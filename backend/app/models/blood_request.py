import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class BloodRequest(Base):
    __tablename__ = "blood_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_session_id: Mapped[str] = mapped_column(String(100), index=True)
    blood_group: Mapped[str] = mapped_column(
        SAEnum("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", name="req_blood_group_enum")
    )
    units_needed: Mapped[int] = mapped_column(Integer, default=1)
    hospital_name: Mapped[str] = mapped_column(String(200))
    hospital_area: Mapped[str] = mapped_column(String(100))
    hospital_lat: Mapped[float] = mapped_column(Float)
    hospital_lng: Mapped[float] = mapped_column(Float)
    urgency_level: Mapped[str] = mapped_column(
        SAEnum("critical", "high", "medium", "low", name="urgency_enum"),
        default="high",
    )
    patient_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        SAEnum("pending", "in_progress", "fulfilled", "failed", name="request_status_enum"),
        default="pending",
    )
    confirmed_donors: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
