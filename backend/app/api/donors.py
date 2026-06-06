from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.donor import Donor
from app.schemas.donor import DonorRead

router = APIRouter(prefix="/api/donors", tags=["donors"])


@router.get("", response_model=list[DonorRead])
async def list_donors(
    blood_group: str | None = Query(None, description="Filter by blood group, e.g. O+"),
    area: str | None = Query(None, description="Filter by Karachi area"),
    health_status: str | None = Query(None, description="available or unavailable"),
    limit: int = Query(100, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
) -> list[DonorRead]:
    q = select(Donor)
    if blood_group:
        q = q.where(Donor.blood_group == blood_group)
    if area:
        q = q.where(Donor.area == area)
    if health_status:
        q = q.where(Donor.health_status == health_status)
    q = q.offset(offset).limit(limit)

    result = await db.execute(q)
    donors = result.scalars().all()
    return [DonorRead.model_validate(d) for d in donors]


@router.get("/{donor_id}", response_model=DonorRead)
async def get_donor(donor_id: str, db: AsyncSession = Depends(get_db)) -> DonorRead:
    result = await db.execute(select(Donor).where(Donor.id == donor_id))
    donor = result.scalar_one()
    return DonorRead.model_validate(donor)
