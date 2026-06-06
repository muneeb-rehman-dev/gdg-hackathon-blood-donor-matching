"""
POST /api/chat — main chat endpoint.

Flow:
1. Extract blood request via Claude NLP agent
2. If needs clarification → return bot reply with questions
3. If extracted successfully → save BloodRequest to DB, spawn orchestrator as background task
4. Return immediately with request_id so frontend can connect to WebSocket
"""

import asyncio
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import run_matching_orchestrator
from app.agents.request_extractor import extract_blood_request
from app.database import get_db
from app.models.blood_request import BloodRequest
from app.schemas.chat import ChatMessage, ChatResponse

# Hardcoded hospital lat/lng map for Karachi areas (MVP)
AREA_COORDINATES: dict[str, tuple[float, float]] = {
    "Clifton":          (24.8100, 67.0300),
    "DHA":              (24.8100, 67.0750),
    "Gulshan-e-Iqbal":  (24.9350, 67.1050),
    "Nazimabad":        (24.9150, 67.0350),
    "North Karachi":    (24.9650, 67.0650),
    "Saddar":           (24.8700, 67.0100),
    "Korangi":          (24.8450, 67.1150),
    "Malir":            (24.8900, 67.1950),
    "Lyari":            (24.8750, 66.9950),
}

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Simple in-memory session store for conversation history (MVP)
_sessions: dict[str, list[dict]] = {}


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatMessage,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    session_id = body.session_id
    history = _sessions.get(session_id, [])

    # Append user message to history
    history.append({"role": "user", "content": body.message})

    # Run extraction agent
    extraction = await extract_blood_request(
        message=body.message,
        conversation_history=history[:-1],  # history without current message
    )

    # Append assistant reply to history
    history.append({"role": "assistant", "content": extraction.bot_reply})
    _sessions[session_id] = history[-20:]  # Keep last 20 turns

    if extraction.needs_clarification or not extraction.extracted_successfully:
        return ChatResponse(
            session_id=session_id,
            bot_reply=extraction.bot_reply,
            needs_clarification=True,
            clarification_questions=extraction.clarification_questions,
            status="clarification_needed",
        )

    # Resolve hospital lat/lng from area name
    area_key = _find_area(extraction.hospital_area or "")
    if area_key:
        lat, lng = AREA_COORDINATES[area_key]
        hospital_area = area_key
    else:
        # Default to Saddar if area not recognised
        lat, lng = AREA_COORDINATES["Saddar"]
        hospital_area = extraction.hospital_area or "Saddar"

    request = BloodRequest(
        id=str(uuid.uuid4()),
        chat_session_id=session_id,
        blood_group=extraction.blood_group,
        units_needed=extraction.units_needed or 1,
        hospital_name=extraction.hospital_name or "Unknown Hospital",
        hospital_area=hospital_area,
        hospital_lat=lat,
        hospital_lng=lng,
        urgency_level=extraction.urgency_level,
        patient_name=extraction.patient_name,
        raw_message=body.message,
        status="pending",
        confirmed_donors=0,
        created_at=datetime.utcnow(),
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)

    # Launch orchestrator in background — WebSocket delivers progress
    background_tasks.add_task(
        _run_orchestrator_background,
        request.id,
        extraction,
    )

    return ChatResponse(
        session_id=session_id,
        bot_reply=extraction.bot_reply,
        request_id=request.id,
        needs_clarification=False,
        status="outreach_started",
    )


def _find_area(area_input: str) -> str | None:
    normalized = area_input.strip().lower()
    for key in AREA_COORDINATES:
        if key.lower() in normalized or normalized in key.lower():
            return key
    return None


async def _run_orchestrator_background(request_id: str, extraction) -> None:
    """Creates a fresh DB session for the background orchestrator task."""
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(
            select(BloodRequest).where(BloodRequest.id == request_id)
        )
        request = result.scalar_one()
        await run_matching_orchestrator(db, request, extraction)
