"""
Wave-based outreach simulation.

Each wave contacts WAVE_SIZE donors asynchronously with random delays.
Outcomes: 70% accepted, 20% rejected, 10% unavailable.
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


async def _simulate_response(donor: DonorMatch) -> tuple[str, str]:
    """Simulate one donor's response — no DB access, returns (intent, text)."""
    await asyncio.sleep(random.uniform(1.0, 4.5))
    intent = random.choices(OUTCOME_CHOICES, weights=OUTCOME_WEIGHTS, k=1)[0]
    response_text = random.choice(REPLY_MAP[intent])
    return intent, response_text


async def run_wave(
    db: AsyncSession,
    request: BloodRequest,
    wave_number: int,
    donors: list[DonorMatch],
) -> dict:
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

    # Simulate all donors concurrently — no shared DB session inside tasks
    results = await asyncio.gather(*[_simulate_response(d) for d in wave_donors])

    counts = {"accepted": 0, "rejected": 0, "unavailable": 0}

    # Save responses sequentially (safe session access) and broadcast each one
    for donor, (intent, response_text) in zip(wave_donors, results):
        db.add(DonorResponse(
            id=str(uuid.uuid4()),
            wave_id=wave.id,
            donor_id=donor.id,
            request_id=request.id,
            intent=intent,
            response_text=response_text,
            responded_at=datetime.utcnow(),
        ))
        counts[intent] += 1

        await manager.broadcast({
            "event": "donor_response",
            "request_id": request.id,
            "wave_number": wave_number,
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

    # One commit for all responses + wave completion + confirmed count
    wave.status = "completed"
    wave.completed_at = datetime.utcnow()
    request.confirmed_donors += counts["accepted"]
    await db.commit()

    await manager.broadcast({
        "event": "wave_completed",
        "request_id": request.id,
        "wave_number": wave_number,
        "data": counts,
    })

    return counts
