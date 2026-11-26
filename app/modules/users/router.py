
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.modules.users.models import User


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
        "preferences": (
            {
                "market": preferences.market,
                "timezone": preferences.timezone,
                "currency": preferences.currency,
                "default_timeframe": preferences.default_timeframe,
                "theme": preferences.theme,
                "notifications_enabled": preferences.notifications_enabled,
            }
            if preferences else None
        ),
    }
