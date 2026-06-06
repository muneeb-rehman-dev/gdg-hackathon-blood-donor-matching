from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


BloodGroup = Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
UrgencyLevel = Literal["critical", "high", "medium", "low"]
RequestStatus = Literal["pending", "in_progress", "fulfilled", "failed"]


class BloodRequestExtraction(BaseModel):
    """Structured output from the NLP extraction agent."""
    blood_group: Optional[str] = None
    units_needed: Optional[int] = None
    hospital_name: Optional[str] = None
    hospital_area: Optional[str] = None
    urgency_level: UrgencyLevel = "high"
    patient_name: Optional[str] = None
    needs_clarification: bool = False
    clarification_questions: list[str] = []
    extracted_successfully: bool = False
    bot_reply: str = ""


class BloodRequestRead(BaseModel):
    id: str
    chat_session_id: str
    blood_group: BloodGroup
    units_needed: int
    hospital_name: str
    hospital_area: str
    hospital_lat: float
    hospital_lng: float
    urgency_level: UrgencyLevel
    patient_name: Optional[str]
    raw_message: str
    status: RequestStatus
    confirmed_donors: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DonorResponseRead(BaseModel):
    id: str
    donor_id: str
    wave_id: str
    request_id: str
    intent: Literal["accepted", "rejected", "unavailable", "no_response"]
    response_text: str
    responded_at: datetime

    model_config = {"from_attributes": True}


class WaveRead(BaseModel):
    id: str
    request_id: str
    wave_number: int
    donor_ids: list[str]
    status: Literal["pending", "in_progress", "completed"]
    started_at: datetime
    completed_at: Optional[datetime]
    responses: list[DonorResponseRead] = []

    model_config = {"from_attributes": True}


class BloodRequestDetail(BloodRequestRead):
    waves: list[WaveRead] = []
