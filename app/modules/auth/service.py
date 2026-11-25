from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User, UserPreference
from app.modules.auth.schemas import SignupRequest
from app.core.security import hash_password


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