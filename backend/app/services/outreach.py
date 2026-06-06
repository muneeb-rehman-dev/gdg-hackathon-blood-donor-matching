"""
Wave-based outreach simulation.

Each wave contacts WAVE_SIZE donors asynchronously with random delays.
Outcomes: 70% accepted, 20% rejected, 10% unavailable.
Results are saved to DB and broadcast via WebSocket.
"""

import asyncio
import random
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.blood_request import BloodRequest
from app.models.donor_response import DonorResponse
from app.models.outreach_wave import OutreachWave
from app.schemas.donor import DonorMatch
from app.services.broadcast import manager

OUTCOME_CHOICES = ["accepted", "rejected", "unavailable"]
OUTCOME_WEIGHTS = [0.70, 0.20, 0.10]

ACCEPTED_REPLIES = [
    "Haan bhai, zaroor. Aa raha hoon.",
    "Yes, I can donate. Please share the address.",
    "Bilkul, main abhi nikal raha hoon.",
    "Of course! On my way.",
    "Haan, ready hoon. Hospital ka naam batao.",
]

REJECTED_REPLIES = [
    "Sorry, main available nahi hoon abhi.",
    "Nahi kar sakta, bahar hoon sheher se.",
    "No, I'm not able to come right now.",
    "Main busy hoon, maafi chahta hoon.",
]

UNAVAILABLE_REPLIES = [
    "Main beemaar hoon, donate nahi kar sakta.",
    "Mujhe fever hai, sorry.",
    "I recently had surgery, cannot donate.",
    "Tabiyat theek nahi hai.",
]

REPLY_MAP = {
    "accepted": ACCEPTED_REPLIES,
    "rejected": REJECTED_REPLIES,
    "unavailable": UNAVAILABLE_REPLIES,
}


async def _simulate_single_donor(
    db: AsyncSession,
    donor: DonorMatch,
    wave: OutreachWave,
    request_id: str,
) -> str:
    """Simulate one donor's response with random delay."""
    await asyncio.sleep(random.uniform(1.0, 4.5))

    intent = random.choices(OUTCOME_CHOICES, weights=OUTCOME_WEIGHTS, k=1)[0]
    response_text = random.choice(REPLY_MAP[intent])

    donor_response = DonorResponse(
        id=str(uuid.uuid4()),
        wave_id=wave.id,
        donor_id=donor.id,
        request_id=request_id,
        intent=intent,
        response_text=response_text,
        responded_at=datetime.utcnow(),
    )
    db.add(donor_response)
    await db.commit()

    await manager.broadcast({
        "event": "donor_response",
        "request_id": request_id,
        "wave_number": wave.wave_number,
        "data": {
            "donor": {
                "id": donor.id,
                "name": donor.name,
                "blood_group": donor.blood_group,
                "area": donor.area,
                "distance_km": donor.distance_km,
                "score": donor.score,
            },
            "intent": intent,
            "response_text": response_text,
        },
    })

    return intent


async def run_wave(
    db: AsyncSession,
    request: BloodRequest,
    wave_number: int,
    donors: list[DonorMatch],
) -> dict:
    """
    Run a single outreach wave for the given donors.
    Returns dict with accepted/rejected/unavailable counts.
    """
    wave_donors = donors[:settings.wave_size]

    wave = OutreachWave(
        id=str(uuid.uuid4()),
        request_id=request.id,
        wave_number=wave_number,
        donor_ids=[d.id for d in wave_donors],
        status="in_progress",
        started_at=datetime.utcnow(),
    )
    db.add(wave)
    await db.commit()
    await db.refresh(wave)

    await manager.broadcast({
        "event": "wave_started",
        "request_id": request.id,
        "wave_number": wave_number,
        "data": {"donor_count": len(wave_donors)},
    })

    # Run all donors concurrently
    tasks = [
        _simulate_single_donor(db, donor, wave, request.id)
        for donor in wave_donors
    ]
    results = await asyncio.gather(*tasks)

    counts = {
        "accepted": results.count("accepted"),
        "rejected": results.count("rejected"),
        "unavailable": results.count("unavailable"),
    }

    wave.status = "completed"
    wave.completed_at = datetime.utcnow()
    await db.commit()

    # Update confirmed donors on the request
    request.confirmed_donors += counts["accepted"]
    await db.commit()

    await manager.broadcast({
        "event": "wave_completed",
        "request_id": request.id,
        "wave_number": wave_number,
        "data": counts,
    })

    return counts
