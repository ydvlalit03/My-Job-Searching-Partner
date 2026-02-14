"""Full onboarding pipeline endpoint — powered by LangGraph."""

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.career import CareerRecommendation
from app.models.resume import ResumeProfile
from app.models.user import User
from app.services.pipeline import run_full_pipeline

settings = get_settings()
router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/onboard")
async def run_onboarding_pipeline(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run the full LangGraph onboarding pipeline in one call.

    Steps executed:
    1. Parse resume (LLM + regex)
    2. Recommend top 5 career roles (LLM)
    3. Search & rank jobs for top role (RapidAPI + scoring)
    4. ATS score the resume for top role (LLM)

    Returns all results in a single response.
    """
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

    # Run the full LangGraph pipeline
    result = await run_full_pipeline(
        user_id=str(user.id),
        resume_file_path=file_path,
        location_preference=user.location_preference,
        remote_preference=user.remote_preference,
    )

    # Persist parsed resume profile
    profile = user.profile
    if profile:
        profile.resume_file_path = file_path
        profile.raw_text = result.get("raw_text", "")
        profile.skills = result.get("skills", [])
        profile.experience = result.get("experience", [])
        profile.education = result.get("education", [])
        profile.total_experience_years = result.get("total_experience_years", 0.0)
    else:
        profile = ResumeProfile(
            user_id=user.id,
            resume_file_path=file_path,
            raw_text=result.get("raw_text", ""),
            skills=result.get("skills", []),
            experience=result.get("experience", []),
            education=result.get("education", []),
            total_experience_years=result.get("total_experience_years", 0.0),
        )
        db.add(profile)

    # Persist ATS score
    ats = result.get("ats_result", {})
    if ats:
        profile.ats_score = ats.get("score", 0)
        profile.ats_feedback = ats

    # Persist career recommendations
    for rec_data in result.get("recommendations", []):
        rec = CareerRecommendation(
            user_id=user.id,
            job_role=rec_data["job_role"],
            match_score=rec_data["match_score"],
            matched_skills=rec_data.get("matched_skills", []),
            missing_skills=rec_data.get("missing_skills", []),
        )
        db.add(rec)

    await db.flush()

    return {
        "status": "completed",
        "skills_extracted": result.get("skills", []),
        "experience_years": result.get("total_experience_years", 0),
        "career_recommendations": result.get("recommendations", []),
        "top_role": result.get("selected_role", ""),
        "matched_jobs": result.get("matched_jobs", [])[:10],  # Top 10 in response
        "ats_score": ats,
        "errors": result.get("errors", []),
    }
