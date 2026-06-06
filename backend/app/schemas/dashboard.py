from pydantic import BaseModel
from typing import Any, Literal, Optional


class WSEvent(BaseModel):
    event: Literal[
        "wave_started",
        "donor_response",
        "wave_completed",
        "request_fulfilled",
        "request_failed",
        "status_update",
    ]
    request_id: str
    wave_number: Optional[int] = None
    data: dict[str, Any] = {}


class DashboardStats(BaseModel):
    total_requests: int
    fulfilled_requests: int
    failed_requests: int
    in_progress_requests: int
    fulfillment_rate: float
    total_donors: int
    eligible_donors: int
    total_waves: int
    avg_waves_per_request: float
    blood_group_breakdown: dict[str, int]
