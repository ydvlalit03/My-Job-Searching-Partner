import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CareerRecommendation(Base):
    __tablename__ = "career_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    job_role: Mapped[str] = mapped_column(String(255), nullable=False)
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    matched_skills: Mapped[list | None] = mapped_column(ARRAY(String), default=list)
    missing_skills: Mapped[list | None] = mapped_column(ARRAY(String), default=list)
    is_selected: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="recommendations")


from app.models.user import User  # noqa: E402
