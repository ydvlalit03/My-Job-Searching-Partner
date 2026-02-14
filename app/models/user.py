import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Onboarding fields
    degree: Mapped[str | None] = mapped_column(String(255))
    location_preference: Mapped[str | None] = mapped_column(String(255))
    remote_preference: Mapped[str | None] = mapped_column(String(50))  # remote / onsite / hybrid
    salary_expectation: Mapped[str | None] = mapped_column(String(100))

    # Relationships
    profile: Mapped["ResumeProfile"] = relationship(back_populates="user", uselist=False, lazy="selectin")
    recommendations: Mapped[list["CareerRecommendation"]] = relationship(back_populates="user", lazy="selectin")
    saved_jobs: Mapped[list["SavedJob"]] = relationship(back_populates="user", lazy="selectin")
    roadmap_entries: Mapped[list["RoadmapEntry"]] = relationship(back_populates="user", lazy="selectin")


# Resolve forward refs
from app.models.resume import ResumeProfile  # noqa: E402
from app.models.career import CareerRecommendation  # noqa: E402
from app.models.job import SavedJob  # noqa: E402
from app.models.roadmap import RoadmapEntry  # noqa: E402
