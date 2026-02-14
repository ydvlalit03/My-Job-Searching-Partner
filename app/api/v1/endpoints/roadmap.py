import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.career import CareerRecommendation
from app.models.roadmap import RoadmapEntry
from app.models.user import User
from app.schemas.roadmap import ReferralMessageOut, ReferralMessageRequest, RoadmapEntryOut, UpdateProgress
from app.services.llm_client import generate_referral_message
from app.services.roadmap_generator import generate_daily_roadmap

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


@router.post("/generate", response_model=list[RoadmapEntryOut])
async def generate_roadmap(
    days: int = 7,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Find selected role
    result = await db.execute(
        select(CareerRecommendation).where(
            CareerRecommendation.user_id == user.id,
            CareerRecommendation.is_selected.is_(True),
        )
    )
    selected = result.scalars().first()
    target_role = selected.job_role if selected else "Software Developer"

    # Get user skills for personalized roadmap
    skills = user.profile.skills if user.profile else []
    exp_years = user.profile.total_experience_years if user.profile else 0.0

    plan = await generate_daily_roadmap(
        target_role=target_role,
        skills=skills,
        experience_years=exp_years,
        total_days=days,
    )

    entries: list[RoadmapEntry] = []
    for item in plan:
        entry = RoadmapEntry(
            user_id=user.id,
            date=date.fromisoformat(item["date"]),
            jobs_to_apply=item["jobs_to_apply"],
            referrals_to_send=item["referrals_to_send"],
            recruiters_to_connect=item["recruiters_to_connect"],
            daily_tips=item["daily_tips"],
        )
        db.add(entry)
        entries.append(entry)

    await db.flush()
    return [RoadmapEntryOut.model_validate(e) for e in entries]


@router.get("/today", response_model=RoadmapEntryOut | None)
async def get_today(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RoadmapEntry).where(
            RoadmapEntry.user_id == user.id,
            RoadmapEntry.date == date.today(),
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        return None
    return RoadmapEntryOut.model_validate(entry)


@router.patch("/{entry_id}/progress", response_model=RoadmapEntryOut)
async def update_progress(
    entry_id: uuid.UUID,
    body: UpdateProgress,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RoadmapEntry).where(RoadmapEntry.id == entry_id, RoadmapEntry.user_id == user.id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Roadmap entry not found")

    if body.jobs_applied is not None:
        entry.jobs_applied = body.jobs_applied
    if body.referrals_sent is not None:
        entry.referrals_sent = body.referrals_sent
    if body.recruiters_connected is not None:
        entry.recruiters_connected = body.recruiters_connected

    # Auto-complete check
    entry.is_completed = (
        entry.jobs_applied >= entry.jobs_to_apply
        and entry.referrals_sent >= entry.referrals_to_send
        and entry.recruiters_connected >= entry.recruiters_to_connect
    )

    await db.flush()
    return RoadmapEntryOut.model_validate(entry)


@router.post("/referral-message", response_model=ReferralMessageOut)
async def get_referral_message(
    body: ReferralMessageRequest,
    user: User = Depends(get_current_user),
):
    background = f"{user.full_name}"
    if user.profile and user.profile.skills:
        background += f", skilled in {', '.join(user.profile.skills[:5])}"
    if user.degree:
        background += f", {user.degree}"

    result = await generate_referral_message(body.job_role, body.company_name, background)
    return ReferralMessageOut(**result)
