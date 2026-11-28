from datetime import datetime, timezone, timedelta
import hashlib
import uuid

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User, UserPreference
from app.modules.auth.models import RefreshToken
from app.modules.auth.schemas import SignupRequest
from app.core.config import settings
from app.modules.auth.otp_models import PasswordResetOTP
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
import secrets
import hmac

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

async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
) -> dict:

    # 1. Decode and validate JWT
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise ValueError("Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise ValueError("Invalid refresh token")

    try:
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, KeyError, TypeError):
        raise ValueError("Invalid refresh token")

    # 2. Hash incoming refresh token
    token_hash = hashlib.sha256(
        refresh_token.encode()
    ).hexdigest()

    # 3. Find stored token and lock its row
    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id,
        )
        .with_for_update()
    )

    old_token = result.scalar_one_or_none()

    if not old_token or old_token.revoked:
        raise ValueError("Refresh token revoked or not found")

    if old_token.expires_at <= datetime.now(timezone.utc):
        raise ValueError("Refresh token expired")

    # 4. Check user account
    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise ValueError("User account is inactive or not found")

    # 5. Revoke old refresh token
    old_token.revoked = True

    # 6. Generate new tokens
    new_access_token = create_access_token(str(user.id))
    new_refresh_token = create_refresh_token(str(user.id))

    new_payload = decode_token(new_refresh_token)

    new_expires_at = datetime.fromtimestamp(
        new_payload["exp"],
        tz=timezone.utc,
    )

    new_token_hash = hashlib.sha256(
        new_refresh_token.encode()
    ).hexdigest()

    # 7. Save new refresh token
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
            revoked=False,
        )
    )

    await db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": 900,
    }

async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
) -> dict:

    # 1. Decode and validate JWT
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise ValueError("Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise ValueError("Invalid refresh token")

    try:
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, KeyError, TypeError):
        raise ValueError("Invalid refresh token")

    # 2. Hash incoming refresh token
    token_hash = hashlib.sha256(
        refresh_token.encode()
    ).hexdigest()

    # 3. Find stored token and lock its row
    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id,
        )
        .with_for_update()
    )

    old_token = result.scalar_one_or_none()

    if not old_token or old_token.revoked:
        raise ValueError("Refresh token revoked or not found")

    if old_token.expires_at <= datetime.now(timezone.utc):
        raise ValueError("Refresh token expired")

    # 4. Check user account
    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise ValueError("User account is inactive or not found")

    # 5. Revoke old refresh token
    old_token.revoked = True

    # 6. Generate new tokens
    new_access_token = create_access_token(str(user.id))
    new_refresh_token = create_refresh_token(str(user.id))

    new_payload = decode_token(new_refresh_token)

    new_expires_at = datetime.fromtimestamp(
        new_payload["exp"],
        tz=timezone.utc,
    )

    new_token_hash = hashlib.sha256(
        new_refresh_token.encode()
    ).hexdigest()

    # 7. Save new refresh token
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
            revoked=False,
        )
    )

    await db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": 900,
    }

def hash_otp(otp: str) -> str:
    return hmac.new(
        settings.JWT_SECRET_KEY.encode(),
        otp.encode(),
        hashlib.sha256,
    ).hexdigest()


async def request_password_otp(
    db: AsyncSession,
    identifier: str,
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
            select(User).where(
                User.mobile == identifier
            )
        )

    user = result.scalar_one_or_none()

    # Generic response prevents account enumeration
    if not user:
        return {
            "message": "If the account exists, an OTP has been generated."
        }

    otp = f"{secrets.randbelow(1_000_000):06d}"

    otp_record = PasswordResetOTP(
        user_id=user.id,
        otp_hash=hash_otp(otp),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )

    db.add(otp_record)
    await db.commit()

    # MOCK ONLY: remove this OTP from the response before production.
    return {
        "message": "Mock OTP generated successfully",
        "mock_otp": otp,
    }


async def verify_password_otp(
    db: AsyncSession,
    identifier: str,
    otp: str,
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
            select(User).where(
                User.mobile == identifier
            )
        )

    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("Invalid or expired OTP")

    # Lock the latest OTP record to prevent concurrent verification.
    result = await db.execute(
        select(PasswordResetOTP)
        .where(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.used.is_(False),
        )
        .order_by(PasswordResetOTP.created_at.desc())
        .limit(1)
        .with_for_update()
    )

    otp_record = result.scalar_one_or_none()

    if not otp_record or otp_record.verified:
        raise ValueError("Invalid or expired OTP")

    now = datetime.now(timezone.utc)

    if otp_record.expires_at <= now:
        raise ValueError("OTP expired")

    if otp_record.attempts >= 5:
        raise ValueError("Maximum OTP attempts exceeded")

    otp_record.attempts += 1

    if not hmac.compare_digest(
        otp_record.otp_hash,
        hash_otp(otp),
    ):
        await db.commit()
        raise ValueError("Invalid OTP")

    otp_record.verified = True

    reset_expiry = now + timedelta(minutes=10)

    reset_token = jwt.encode(
        {
            "sub": str(user.id),
            "type": "password_reset",
            "otp_id": str(otp_record.id),
            "exp": reset_expiry,
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    await db.commit()

    return {
        "message": "OTP verified successfully",
        "reset_token": reset_token,
        "expires_in": 600,
    }


async def reset_user_password(
    db: AsyncSession,
    reset_token: str,
    new_password: str,
) -> dict:

    try:
        payload = jwt.decode(
            reset_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise ValueError("Invalid or expired reset token")

    if payload.get("type") != "password_reset":
        raise ValueError("Invalid reset token")

    try:
        user_id = uuid.UUID(payload["sub"])
        otp_id = uuid.UUID(payload["otp_id"])
    except (ValueError, KeyError, TypeError):
        raise ValueError("Invalid reset token")

    result = await db.execute(
        select(PasswordResetOTP)
        .where(
            PasswordResetOTP.id == otp_id,
            PasswordResetOTP.user_id == user_id,
        )
        .with_for_update()
    )

    otp_record = result.scalar_one_or_none()

    if (
        not otp_record
        or not otp_record.verified
        or otp_record.used
        or otp_record.expires_at <= datetime.now(timezone.utc)
    ):
        raise ValueError("OTP verification expired or already used")

    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise ValueError("User not found or inactive")

    user.password_hash = hash_password(new_password)
    otp_record.used = True

    # Revoke all existing refresh tokens
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked.is_(False),
        )
    )

    for token in result.scalars().all():
        token.revoked = True

    await db.commit()

    return {
        "message": "Password reset successfully. Please log in again."
    }