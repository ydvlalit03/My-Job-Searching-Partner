import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.career import CareerRecommendation
from app.models.job import SavedJob
from app.models.user import User
from app.schemas.job import JobOut, UpdateJobStatus
from app.services.job_search import rank_jobs, search_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/search", response_model=list[JobOut])
async def search_and_match(
    role: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search for jobs matching the user's profile.

    If no role is provided, uses the user's selected career recommendation.
    """
    query = role
    if not query:
        result = await db.execute(
            select(CareerRecommendation).where(
                CareerRecommendation.user_id == user.id,
                CareerRecommendation.is_selected.is_(True),
            )
        )
        selected = result.scalars().first()
        if not selected:
            raise HTTPException(status_code=400, detail="Select a career role first or provide ?role= param")
        query = selected.job_role

    user_skills = user.profile.skills if user.profile else []
    location = user.location_preference
    remote = user.remote_preference == "remote"

    raw_jobs = await search_jobs(
        query=f"{query} fresher entry level",
        location=location,
        remote_only=remote,
    )

    ranked = rank_jobs(raw_jobs, user_skills, location)
    return [JobOut(**j) for j in ranked]


@router.post("/save/{job_index}", response_model=JobOut)
async def save_job(
    job_index: int,
    role: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save a job from search results by its index."""
    # Re-run search to get the job (stateless design)
    query = role
    if not query:
        result = await db.execute(
            select(CareerRecommendation).where(
                CareerRecommendation.user_id == user.id,
                CareerRecommendation.is_selected.is_(True),
            )
        )
        selected = result.scalars().first()
        if not selected:
            raise HTTPException(status_code=400, detail="Select a career role first")
        query = selected.job_role

    user_skills = user.profile.skills if user.profile else []
    raw_jobs = await search_jobs(query=f"{query} fresher entry level")
    ranked = rank_jobs(raw_jobs, user_skills, user.location_preference)

    if job_index < 0 or job_index >= len(ranked):
        raise HTTPException(status_code=404, detail="Invalid job index")

    job_data = ranked[job_index]
    saved = SavedJob(
        user_id=user.id,
        external_job_id=job_data.get("external_job_id"),
        title=job_data["title"],
        company=job_data["company"],
        location=job_data.get("location"),
        is_remote=job_data.get("is_remote", False),
        apply_url=job_data.get("apply_url"),
        description=job_data.get("description"),
        salary_range=job_data.get("salary_range"),
        match_score=job_data.get("match_score", 0),
        match_details=job_data.get("match_details"),
    )
    db.add(saved)
    await db.flush()
    return JobOut.model_validate(saved)


@router.get("/saved", response_model=list[JobOut])
async def get_saved_jobs(user: User = Depends(get_current_user)):
    return [JobOut.model_validate(j) for j in user.saved_jobs]


@router.patch("/saved/{job_id}/status", response_model=JobOut)
async def update_job_status(
    job_id: uuid.UUID,
    body: UpdateJobStatus,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavedJob).where(SavedJob.id == job_id, SavedJob.user_id == user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = body.status
    await db.flush()
    return JobOut.model_validate(job)
