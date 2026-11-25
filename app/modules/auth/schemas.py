from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Literal


class UserPreferenceCreate(BaseModel):
    market: Literal["NSE", "BSE"] = "NSE"
    timezone: str = "Asia/Kolkata"
    currency: Literal["INR"] = "INR"
    default_timeframe: Literal["1m", "5m", "15m", "1h", "1D"] = "1D"
    theme: Literal["light", "dark", "system"] = "system"
    notifications_enabled: bool = True


class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    preferences: UserPreferenceCreate = Field(
        default_factory=UserPreferenceCreate
    )


class SignupResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str
    preferences: UserPreferenceCreate

    model_config = ConfigDict(from_attributes=True)