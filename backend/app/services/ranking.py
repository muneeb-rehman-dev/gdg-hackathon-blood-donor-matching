"""
Multi-factor donor ranking using Haversine distance + eligibility + response rate.
"""

import math
from datetime import date, timedelta
from app.models.donor import Donor
from app.schemas.donor import DonorMatch


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


WEIGHTS = {
    "distance":      0.40,
    "eligibility":   0.25,
    "response_rate": 0.20,
    "availability":  0.10,
    "fatigue":       0.05,
}

MAX_DISTANCE_KM = 30.0
ELIGIBILITY_DAYS = 56


def _eligibility_score(donor: Donor) -> float:
    if donor.last_donation_date is None:
        return 1.0
    cutoff = date.today() - timedelta(days=ELIGIBILITY_DAYS)
    return 1.0 if donor.last_donation_date <= cutoff else 0.0


def _fatigue_score(donor: Donor) -> float:
    # Simple proxy: reduce score if they have many donations recently (total used as stand-in)
    # In a real system you'd query donations in the last 30 days
    penalty = min(donor.total_donations / 30.0, 1.0)
    return max(0.0, 1.0 - penalty)


def rank_donors(
    donors: list[Donor],
    hospital_lat: float,
    hospital_lng: float,
) -> list[DonorMatch]:
    results: list[DonorMatch] = []

    for donor in donors:
        dist = _haversine_km(hospital_lat, hospital_lng, donor.lat, donor.lng)
        dist_score = max(0.0, 1.0 - (dist / MAX_DISTANCE_KM))
        elig_score = _eligibility_score(donor)

        score = (
            WEIGHTS["distance"] * dist_score
            + WEIGHTS["eligibility"] * elig_score
            + WEIGHTS["response_rate"] * donor.response_rate
            + WEIGHTS["availability"] * (1.0 if donor.health_status == "available" else 0.0)
            + WEIGHTS["fatigue"] * _fatigue_score(donor)
        )

        results.append(
            DonorMatch(
                id=donor.id,
                name=donor.name,
                phone=donor.phone,
                blood_group=donor.blood_group,
                area=donor.area,
                lat=donor.lat,
                lng=donor.lng,
                health_status=donor.health_status,
                response_rate=donor.response_rate,
                total_donations=donor.total_donations,
                last_donation_date=donor.last_donation_date,
                created_at=donor.created_at,
                score=round(score, 4),
                distance_km=round(dist, 2),
                is_eligible=elig_score == 1.0,
            )
        )

    results.sort(key=lambda d: d.score, reverse=True)
    return results
