from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.auth.schemas import LoginRequest, LogoutRequest, SignupRequest, TokenResponse, RefreshRequest
from app.modules.auth.service import login_user, signup_user, logout_user ,refresh_access_token


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
                "mobile": user.mobile,
                "age": user.age,
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
                }
            }
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await login_user(
            db=db,
            identifier=payload.identifier,
            password=payload.password,
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        await logout_user(
            db=db,
            user_id=current_user.id,
            refresh_token=payload.refresh_token,
        )

        return {
            "message": "Successfully logged out"
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

@router.post("/refresh")
async def refresh_token(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await refresh_access_token(
            db=db,
            refresh_token=payload.refresh_token,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        )