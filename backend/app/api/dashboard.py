from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.blood_request import BloodRequest
from app.models.donor import Donor
from app.models.outreach_wave import OutreachWave
from app.schemas.dashboard import DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

ELIGIBILITY_DAYS = 56


@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db)) -> DashboardStats:
    # Blood request counts
    req_result = await db.execute(select(BloodRequest))
    requests = req_result.scalars().all()

    total = len(requests)
    fulfilled = sum(1 for r in requests if r.status == "fulfilled")
    failed = sum(1 for r in requests if r.status == "failed")
    in_progress = sum(1 for r in requests if r.status == "in_progress")
    fulfillment_rate = round(fulfilled / total, 2) if total else 0.0

    # Donor counts
    donor_result = await db.execute(select(Donor))
    donors = donor_result.scalars().all()
    total_donors = len(donors)

    cutoff = date.today() - timedelta(days=ELIGIBILITY_DAYS)
    eligible_donors = sum(
        1 for d in donors
        if d.health_status == "available"
        and (d.last_donation_date is None or d.last_donation_date <= cutoff)
    )

    # Wave stats
    wave_result = await db.execute(select(OutreachWave))
    waves = wave_result.scalars().all()
    total_waves = len(waves)
    avg_waves = round(total_waves / total, 2) if total else 0.0

    # Blood group breakdown
    bg_breakdown: dict[str, int] = {}
    for r in requests:
        bg_breakdown[r.blood_group] = bg_breakdown.get(r.blood_group, 0) + 1

    return DashboardStats(
        total_requests=total,
        fulfilled_requests=fulfilled,
        failed_requests=failed,
        in_progress_requests=in_progress,
        fulfillment_rate=fulfillment_rate,
        total_donors=total_donors,
        eligible_donors=eligible_donors,
        total_waves=total_waves,
        avg_waves_per_request=avg_waves,
        blood_group_breakdown=bg_breakdown,
    )
