from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.schemas import SignupRequest
from app.modules.auth.service import signup_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        user, preferences = await signup_user(db, payload)

        return {
            "message": "User registered successfully",
            "user": {
                "id": str(user.id),
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "preferences": {
                    "market": preferences.market,
                    "timezone": preferences.timezone,
                    "currency": preferences.currency,
                    "default_timeframe": preferences.default_timeframe,
                    "theme": preferences.theme,
                    "notifications_enabled": preferences.notifications_enabled
                }
            }
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )