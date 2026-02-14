import uuid
from datetime import datetime

from pydantic import BaseModel


class CareerRecommendationOut(BaseModel):
    id: uuid.UUID
    job_role: str
    match_score: float
    matched_skills: list[str] | None = None
    missing_skills: list[str] | None = None
    is_selected: bool = False

    model_config = {"from_attributes": True}


class SelectRolesRequest(BaseModel):
    role_ids: list[uuid.UUID]
