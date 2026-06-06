from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.blood_request import BloodRequest
from app.models.donor_response import DonorResponse
from app.models.outreach_wave import OutreachWave
from app.schemas.blood_request import BloodRequestDetail, BloodRequestRead, DonorResponseRead, WaveRead

router = APIRouter(prefix="/api/requests", tags=["requests"])


@router.get("", response_model=list[BloodRequestRead])
async def list_requests(db: AsyncSession = Depends(get_db)) -> list[BloodRequestRead]:
    result = await db.execute(
        select(BloodRequest).order_by(BloodRequest.created_at.desc()).limit(50)
    )
    return [BloodRequestRead.model_validate(r) for r in result.scalars().all()]


@router.get("/{request_id}", response_model=BloodRequestDetail)
async def get_request(request_id: str, db: AsyncSession = Depends(get_db)) -> BloodRequestDetail:
    req_result = await db.execute(
        select(BloodRequest).where(BloodRequest.id == request_id)
    )
    request = req_result.scalar_one()

    wave_result = await db.execute(
        select(OutreachWave)
        .where(OutreachWave.request_id == request_id)
        .order_by(OutreachWave.wave_number)
    )
    waves = wave_result.scalars().all()

    waves_detail: list[WaveRead] = []
    for wave in waves:
        resp_result = await db.execute(
            select(DonorResponse).where(DonorResponse.wave_id == wave.id)
        )
        responses = [DonorResponseRead.model_validate(r) for r in resp_result.scalars().all()]
        wave_read = WaveRead.model_validate(wave)
        wave_read.responses = responses
        waves_detail.append(wave_read)

    detail = BloodRequestDetail.model_validate(request)
    detail.waves = waves_detail
    return detail
