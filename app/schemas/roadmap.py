import uuid
from datetime import date

from pydantic import BaseModel


class RoadmapEntryOut(BaseModel):
    id: uuid.UUID
    date: date
    jobs_to_apply: int
    referrals_to_send: int
    recruiters_to_connect: int
    jobs_applied: int
    referrals_sent: int
    recruiters_connected: int
    daily_tips: dict | None = None
    is_completed: bool

    model_config = {"from_attributes": True}


class UpdateProgress(BaseModel):
    jobs_applied: int | None = None
    referrals_sent: int | None = None
    recruiters_connected: int | None = None


class ReferralMessageRequest(BaseModel):
    job_role: str
    company_name: str


class ReferralMessageOut(BaseModel):
    message: str
    subject_line: str | None = None
