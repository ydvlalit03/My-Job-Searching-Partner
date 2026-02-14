import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.career import CareerRecommendation
from app.models.user import User
from app.schemas.career import CareerRecommendationOut, SelectRolesRequest
from app.services.career_recommender import recommend_roles

router = APIRouter(prefix="/career", tags=["career"])


@router.post("/recommend", response_model=list[CareerRecommendationOut])
async def get_recommendations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.profile or not user.profile.skills:
        raise HTTPException(status_code=400, detail="Upload resume first to extract skills")

    # Clear old recommendations
    old = await db.execute(
        select(CareerRecommendation).where(CareerRecommendation.user_id == user.id)
    )
    for rec in old.scalars():
        await db.delete(rec)

    results = await recommend_roles(
        user_skills=user.profile.skills,
        education=user.profile.education,
        experience=user.profile.experience,
    )
    recs: list[CareerRecommendation] = []
    for r in results:
        rec = CareerRecommendation(
            user_id=user.id,
            job_role=r["job_role"],
            match_score=r["match_score"],
            matched_skills=r["matched_skills"],
            missing_skills=r["missing_skills"],
        )
        db.add(rec)
        recs.append(rec)

    await db.flush()
    return [CareerRecommendationOut.model_validate(r) for r in recs]


@router.post("/select-roles")
async def select_roles(
    body: SelectRolesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CareerRecommendation).where(
            CareerRecommendation.user_id == user.id,
            CareerRecommendation.id.in_(body.role_ids),
        )
    )
    recs = result.scalars().all()
    if not recs:
        raise HTTPException(status_code=404, detail="No matching recommendations found")

    for rec in recs:
        rec.is_selected = True

    await db.flush()
    return {"selected": len(recs)}
