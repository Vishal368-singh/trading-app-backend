from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User, UserPreference
from app.modules.users.schemas import UserProfileUpdate

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password

async def update_user_profile(
    db: AsyncSession,
    user_id,
    payload: UserProfileUpdate,
):
    # Load user and preferences
    result = await db.execute(
        select(User)
        .options(selectinload(User.preferences))
        .where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found")

    data = payload.model_dump(exclude_unset=True)

    # Update basic profile fields
    if "full_name" in data:
        if data["full_name"] is None:
            raise ValueError("Full name cannot be empty")

        user.full_name = data["full_name"].strip()

    if "mobile" in data:
        mobile = data["mobile"]

        if not mobile:
            raise ValueError("Mobile number cannot be empty")

        result = await db.execute(
            select(User).where(
                User.mobile == mobile,
                User.id != user_id,
            )
        )

        if result.scalar_one_or_none():
            raise ValueError("Mobile number already registered")

        user.mobile = mobile

    if "age" in data:
        user.age = data["age"]

    if "profile_image" in data:
        user.profile_image = data["profile_image"]

    # Update preferences without overwriting omitted fields
    preference_data = data.get("preferences")

    if preference_data is not None:
        preferences = user.preferences

        if preferences is None:
            preferences = UserPreference(user_id=user.id)
            db.add(preferences)

        for field, value in preference_data.items():
            if value is not None:
                setattr(preferences, field, value)

    await db.commit()

    # Reload updated data
    result = await db.execute(
        select(User)
        .options(selectinload(User.preferences))
        .where(User.id == user_id)
    )

    return result.scalar_one()



async def delete_user_account(
    db: AsyncSession,
    user: User,
    current_password: str
):
    # Verify current password
    if not verify_password(current_password, user.password_hash):
        raise ValueError("Incorrect password")

    # Permanently delete account
    await db.execute(
        delete(User).where(User.id == user.id)
    )

    await db.commit()

    return {
        "message": "Your account has been permanently deleted."
    }