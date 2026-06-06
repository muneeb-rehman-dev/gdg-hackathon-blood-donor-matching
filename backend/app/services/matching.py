"""
Donor matching — filters donors from the DB by blood group and eligibility (56-day rule).
"""

from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.donor import Donor

ELIGIBILITY_DAYS = 56


async def get_eligible_donors(
    db: AsyncSession,
    blood_group: str,
    limit: int = 200,
) -> list[Donor]:
    """
    Return donors matching blood_group who are eligible to donate today.
    Eligibility: health_status == 'available' AND
                 (last_donation_date is NULL OR last_donation_date <= today - 56 days)
    """
    cutoff = date.today() - timedelta(days=ELIGIBILITY_DAYS)

    result = await db.execute(
        select(Donor).where(
            Donor.blood_group == blood_group,
            Donor.health_status == "available",
        ).limit(limit)
    )
    donors = result.scalars().all()

    eligible = []
    for donor in donors:
        if donor.last_donation_date is None:
            eligible.append(donor)
        elif donor.last_donation_date <= cutoff:
            eligible.append(donor)

    return eligible
