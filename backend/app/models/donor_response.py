import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class DonorResponse(Base):
    __tablename__ = "donor_responses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    wave_id: Mapped[str] = mapped_column(String, ForeignKey("outreach_waves.id"), index=True)
    donor_id: Mapped[str] = mapped_column(String, ForeignKey("donors.id"), index=True)
    request_id: Mapped[str] = mapped_column(String, ForeignKey("blood_requests.id"), index=True)
    intent: Mapped[str] = mapped_column(
        SAEnum("accepted", "rejected", "unavailable", "no_response", name="intent_enum"),
        default="no_response",
    )
    response_text: Mapped[str] = mapped_column(String(500), default="")
    responded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
