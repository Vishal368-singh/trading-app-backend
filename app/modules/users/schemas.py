from pydantic import BaseModel, Field, ConfigDict


class UserPreferenceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    market: str | None = None
    timezone: str | None = None
    currency: str | None = None
    default_timeframe: str | None = None
    theme: str | None = None
    notifications_enabled: bool | None = None

    exchanges: list[str] | None = None
    segments: list[str] | None = None
    watchlists: list[str] | None = None
    alerts: dict[str, bool] | None = None


class UserProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    mobile: str | None = Field(
        default=None,
        min_length=10,
        max_length=15,
    )

    age: int | None = Field(
        default=None,
        ge=18,
        le=120,
    )

    profile_image: str | None = Field(
        default=None,
        max_length=2_800_000,
    )

    preferences: UserPreferenceUpdate | None = None

class DeleteAccountRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=8, max_length=128)