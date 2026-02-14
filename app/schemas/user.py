import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOnboard(BaseModel):
    skills: list[str] | None = None
    degree: str | None = None
    location_preference: str | None = None
    remote_preference: str | None = None  # remote / onsite / hybrid
    salary_expectation: str | None = None


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    degree: str | None = None
    location_preference: str | None = None
    remote_preference: str | None = None
    salary_expectation: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
