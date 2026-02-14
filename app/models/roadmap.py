import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RoadmapEntry(Base):
    __tablename__ = "roadmap_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Daily targets
    jobs_to_apply: Mapped[int] = mapped_column(Integer, default=5)
    referrals_to_send: Mapped[int] = mapped_column(Integer, default=3)
    recruiters_to_connect: Mapped[int] = mapped_column(Integer, default=2)

    # Progress tracking
    jobs_applied: Mapped[int] = mapped_column(Integer, default=0)
    referrals_sent: Mapped[int] = mapped_column(Integer, default=0)
    recruiters_connected: Mapped[int] = mapped_column(Integer, default=0)

    # LLM-generated tips
    daily_tips: Mapped[dict | None] = mapped_column(JSONB)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="roadmap_entries")


from app.models.user import User  # noqa: E402
