
import uuid
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from sqlalchemy import String, Boolean, DateTime, func, ForeignKey, Integer, JSON, text
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.auth.models import RefreshToken

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    
    mobile: Mapped[str] = mapped_column(
    String(15),
    unique=True,
    index=True,
    nullable=False,
    )

    age: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(30),
        default="user",
        server_default="user",
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    preferences: Mapped["UserPreference"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
    Uuid(as_uuid=True),
    ForeignKey("users.id", ondelete="CASCADE"),
    unique=True,
    nullable=False,
    )

    market: Mapped[str] = mapped_column(
        String(20),
        default="NSE",
        server_default="NSE",
        nullable=False,
    )

    exchanges: Mapped[list[str]] = mapped_column(
    JSONB,
    default=lambda: ["NSE", "BSE"],
    server_default=text("""'["NSE", "BSE"]'::jsonb"""),
    nullable=False,
    )

    segments: Mapped[list[str]] = mapped_column(
        JSONB,
        default=lambda: ["Cash", "Futures", "Options"],
        server_default=text("""'["Cash", "Futures", "Options"]'::jsonb"""),
        nullable=False,
    )

    watchlists: Mapped[list[str]] = mapped_column(
    JSONB,
    default=lambda: ["Nifty 50", "Bank Nifty"],
    server_default=text("""'["Nifty 50", "Bank Nifty"]'::jsonb"""),
    nullable=False,
    )


    alerts: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {
            "price": True,
            "signal": True,
            "order": True,
        },
        server_default=text("""'{"price": true, "signal": true, "order": true}'::jsonb"""),
        nullable=False,
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        default="Asia/Kolkata",
        server_default="Asia/Kolkata",
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="INR",
        server_default="INR",
        nullable=False,
    )

    default_timeframe: Mapped[str] = mapped_column(
        String(20),
        default="1D",
        server_default="1D",
        nullable=False,
    )

    theme: Mapped[str] = mapped_column(
        String(20),
        default="system",
        server_default="system",
        nullable=False,
    )

    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="preferences",
    )
