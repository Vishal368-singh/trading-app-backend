from datetime import datetime, timezone
import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User, UserPreference
from app.modules.auth.models import RefreshToken
from app.modules.auth.schemas import SignupRequest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
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
        mobile=payload.mobile,
        age=payload.age,
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
    identifier: str,
    password: str,
) -> dict:

    identifier = identifier.strip()

    if "@" in identifier:
        result = await db.execute(
            select(User).where(
                User.email == identifier.lower()
            )
        )
    else:
        result = await db.execute(
            select(User).where(User.mobile == identifier)
        )

    user = result.scalar_one_or_none()

    if not user or not verify_password(
        password,
        user.password_hash
    ):
        raise ValueError("Invalid email/mobile or password")

    if not user.is_active:
        raise ValueError("Account is inactive")

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    # Decode refresh token to get its expiry
    token_payload = decode_token(refresh_token)

    expires_at = datetime.fromtimestamp(
    token_payload["exp"],
    tz=timezone.utc
    )
    
    # Hash refresh token before storing it
    token_hash = hashlib.sha256(
        refresh_token.encode()
    ).hexdigest()

    db_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        revoked=False,
    )

    db.add(db_token)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 900,
    }


async def logout_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    refresh_token: str,
):
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise ValueError("Invalid or expired refresh token")

    # Verify token type
    if payload.get("type") != "refresh":
        raise ValueError("Invalid refresh token")

    # Verify token ownership
    if payload.get("sub") != str(user_id):
        raise ValueError("Invalid refresh token")

    # Hash incoming token
    token_hash = hashlib.sha256(
        refresh_token.encode()
    ).hexdigest()

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id,
        )
    )

    db_token = result.scalar_one_or_none()

    if not db_token or db_token.revoked:
        raise ValueError("Refresh token already revoked or not found")

    if db_token.expires_at <= datetime.now(timezone.utc):
        raise ValueError("Refresh token has expired")

    # Revoke token
    db_token.revoked = True

    await db.commit()

    return True