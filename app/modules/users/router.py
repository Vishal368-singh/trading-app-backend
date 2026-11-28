
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.users.models import User
from app.modules.users.schemas import UserProfileUpdate
from app.modules.users.service import update_user_profile


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    preferences = current_user.preferences

    return {
        "id": str(current_user.id),
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "profile_image":current_user.profile_image,
        "age":current_user.age,
        "mobile":current_user.mobile,
        "preferences": (
            {
                "market": preferences.market,
                "timezone": preferences.timezone,
                "currency": preferences.currency,
                "default_timeframe": preferences.default_timeframe,
                "theme": preferences.theme,
                "notifications_enabled": preferences.notifications_enabled,
                "exchanges": preferences.exchanges,
                "segments": preferences.segments,
                "watchlists": preferences.watchlists,
                "alerts": preferences.alerts
            }
            if preferences else None
        ),
    }


@router.patch("/me/profile")
async def update_profile(
    payload: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        user = await update_user_profile(
            db=db,
            user_id=current_user.id,
            payload=payload,
        )

        preferences = user.preferences

        return {
            "message": "Profile updated successfully",
            "user": {
                "id": str(user.id),
                "full_name": user.full_name,
                "email": user.email,
                "mobile": user.mobile,
                "age": user.age,
                "profile_image": user.profile_image,
                "preferences": {
                    "market": preferences.market,
                    "timezone": preferences.timezone,
                    "currency": preferences.currency,
                    "default_timeframe": preferences.default_timeframe,
                    "theme": preferences.theme,
                    "notifications_enabled": preferences.notifications_enabled,
                    "exchanges": preferences.exchanges,
                    "segments": preferences.segments,
                    "watchlists": preferences.watchlists,
                    "alerts": preferences.alerts,
                } if preferences else None,
            },
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )