from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Literal


class UserPreferenceCreate(BaseModel):
    market: Literal["NSE", "BSE"] = "NSE"
    timezone: str = "Asia/Kolkata"
    currency: Literal["INR"] = "INR"
    default_timeframe: Literal["1m", "5m", "15m", "1h", "1D"] = "1D"
    theme: Literal["light", "dark", "system"] = "system"
    notifications_enabled: bool = True
    exchanges: list[str] = Field(
        default_factory=lambda: ["NSE", "BSE"]
    )
    segments: list[str] = Field(
        default_factory=lambda: ["Cash", "Futures", "Options"]
    )
    watchlists: list[str] = Field(
        default_factory=lambda: ["Nifty 50", "Bank Nifty"]
    )
    alerts: dict[str, bool] = Field(
        default_factory=lambda: {
            "price": True,
            "signal": True,
            "order": True,
        }
    )


class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    mobile: str = Field(min_length=10, max_length=15)
    age: int | None = Field(default=None, ge=10, le=120)
    password: str = Field(min_length=8, max_length=128)
    preferences: UserPreferenceCreate = Field(
        default_factory=UserPreferenceCreate
    )


class SignupResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str
    age: int
    mobile: str
    preferences: UserPreferenceCreate

    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    identifier: str = Field(
        min_length=3,
        max_length=254,
        description="Email address or mobile number"
    )
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int