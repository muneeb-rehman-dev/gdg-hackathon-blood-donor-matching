from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, Literal


BloodGroup = Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
HealthStatus = Literal["available", "unavailable"]


class DonorBase(BaseModel):
    name: str
    phone: str
    blood_group: BloodGroup
    area: str
    lat: float
    lng: float
    health_status: HealthStatus = "available"
    response_rate: float = 0.7
    total_donations: int = 0
    last_donation_date: Optional[date] = None


class DonorRead(DonorBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DonorMatch(DonorRead):
    score: float
    distance_km: float
    is_eligible: bool
