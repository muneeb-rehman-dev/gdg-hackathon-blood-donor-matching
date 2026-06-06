import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, Date, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Donor(Base):
    __tablename__ = "donors"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20))
    blood_group: Mapped[str] = mapped_column(
        SAEnum("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", name="blood_group_enum")
    )
    area: Mapped[str] = mapped_column(String(100))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    last_donation_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    health_status: Mapped[str] = mapped_column(
        SAEnum("available", "unavailable", name="health_status_enum"),
        default="available",
    )
    response_rate: Mapped[float] = mapped_column(Float, default=0.7)
    total_donations: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
