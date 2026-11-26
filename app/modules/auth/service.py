from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User, UserPreference
from app.modules.auth.schemas import SignupRequest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)


async def signup_user(
    db: AsyncSession,
    payload: SignupRequest
):
    email = str(payload.email).lower().strip()

    # Check existing user
    result = await db.execute(
        select(User).where(User.email == email)
    )

    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise ValueError("Email already registered")

    # Create user
    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role="user",
        is_active=True,
        is_verified=False
    )

    db.add(user)
    await db.flush()

    # Create preferences
    preferences = UserPreference(
        user_id=user.id,
        **payload.preferences.model_dump()
    )

    db.add(preferences)

    await db.commit()
    await db.refresh(user)
    await db.refresh(preferences)

    return user, preferences

async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> dict:

    normalized_email = email.strip().lower()

    result = await db.execute(
        select(User).where(User.email == normalized_email)
    )

    user = result.scalar_one_or_none()

    # Generic error: do not reveal whether the email exists
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")

    if not user.is_active:
        raise ValueError("Account is inactive")

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 900,
    }