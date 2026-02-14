import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.resume import ResumeProfile
from app.models.user import User
from app.schemas.resume import ATSScoreOut, ResumeProfileOut
from app.services.ats_scorer import score_resume
from app.services.resume_parser import parse_resume_with_llm

settings = get_settings()
router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/upload", response_model=ResumeProfileOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"{user.id}_{uuid.uuid4().hex}.pdf")
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse with LLM (falls back to regex automatically)
    parsed = await parse_resume_with_llm(file_path)

    # Upsert profile
    profile = user.profile
    if profile:
        profile.resume_file_path = file_path
        profile.raw_text = parsed["raw_text"]
        profile.skills = parsed["skills"]
        profile.experience = parsed["experience"]
        profile.education = parsed["education"]
        profile.total_experience_years = parsed["total_experience_years"]
    else:
        profile = ResumeProfile(
            user_id=user.id,
            resume_file_path=file_path,
            raw_text=parsed["raw_text"],
            skills=parsed["skills"],
            experience=parsed["experience"],
            education=parsed["education"],
            total_experience_years=parsed["total_experience_years"],
        )
        db.add(profile)

    await db.flush()
    return ResumeProfileOut.model_validate(profile)


@router.get("/profile", response_model=ResumeProfileOut)
async def get_profile(user: User = Depends(get_current_user)):
    if not user.profile:
        raise HTTPException(status_code=404, detail="No resume uploaded yet")
    return ResumeProfileOut.model_validate(user.profile)


@router.post("/ats-score", response_model=ATSScoreOut)
async def get_ats_score(
    target_role: str | None = None,
    user: User = Depends(get_current_user),
):
    if not user.profile or not user.profile.raw_text:
        raise HTTPException(status_code=404, detail="Upload a resume first")

    result = await score_resume(user.profile.raw_text, target_role)
    return ATSScoreOut(**result)
