from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserOnboard, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.patch("/me/onboard", response_model=UserOut)
async def onboard(
    body: UserOnboard,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.degree is not None:
        user.degree = body.degree
    if body.location_preference is not None:
        user.location_preference = body.location_preference
    if body.remote_preference is not None:
        user.remote_preference = body.remote_preference
    if body.salary_expectation is not None:
        user.salary_expectation = body.salary_expectation
    await db.flush()
    return UserOut.model_validate(user)
