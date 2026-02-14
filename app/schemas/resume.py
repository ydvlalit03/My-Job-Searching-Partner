import uuid
from datetime import datetime

from pydantic import BaseModel


class ResumeProfileOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    skills: list[str] | None = None
    experience: list[dict] | None = None
    education: list[dict] | None = None
    total_experience_years: float = 0.0
    ats_score: int | None = None
    ats_feedback: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ATSScoreOut(BaseModel):
    score: int
    keyword_score: int
    format_score: int
    achievement_score: int
    missing_keywords: list[str]
    suggestions: list[str]
    action_verbs_found: list[str]
    action_verbs_missing: list[str]
