import uuid
from datetime import datetime

from pydantic import BaseModel


class JobOut(BaseModel):
    id: uuid.UUID | None = None
    external_job_id: str | None = None
    title: str
    company: str
    location: str | None = None
    is_remote: bool = False
    apply_url: str | None = None
    description: str | None = None
    salary_range: str | None = None
    match_score: float = 0.0
    match_details: dict | None = None
    status: str = "matched"

    model_config = {"from_attributes": True}


class JobSearchParams(BaseModel):
    query: str
    location: str | None = None
    remote_only: bool = False
    page: int = 1
    num_pages: int = 1


class UpdateJobStatus(BaseModel):
    status: str  # applied / interview / rejected / offered
