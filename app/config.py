from functools import lru_cache
from decimal import Decimal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        enable_decoding=False,
        extra="ignore",
    )

    bot_token: str = Field(default="", alias="BOT_TOKEN")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    database_url: str = Field(default="", alias="DATABASE_URL")
    admin_telegram_ids: list[int] = Field(
        default_factory=list,
        alias="ADMIN_TELEGRAM_IDS",
    )

    sbp_phone: str = Field(default="", alias="SBP_PHONE")
    sbp_bank_name: str = Field(default="", alias="SBP_BANK_NAME")
    sbp_recipient_name: str = Field(default="", alias="SBP_RECIPIENT_NAME")
    sbp_payment_comment: str = Field(default="", alias="SBP_PAYMENT_COMMENT")
    support_contact_username: str = Field(
        default="@raugestalt",
        alias="SUPPORT_CONTACT_USERNAME",
    )
    max_audio_file_size_mb: int = Field(default=25, alias="MAX_AUDIO_FILE_SIZE_MB")

    default_free_minutes: int = Field(default=30, alias="DEFAULT_FREE_MINUTES")
    friends_package_minutes: int = Field(
        default=300,
        alias="FRIENDS_PACKAGE_MINUTES",
    )
    power_package_minutes: int = Field(
        default=1000,
        alias="POWER_PACKAGE_MINUTES",
    )
    friends_package_price: Decimal = Field(
        default=Decimal("0"),
        alias="FRIENDS_PACKAGE_PRICE",
    )
    power_package_price: Decimal = Field(
        default=Decimal("0"),
        alias="POWER_PACKAGE_PRICE",
    )

    transcription_model: str = Field(
        default="gpt-4o-mini-transcribe",
        alias="TRANSCRIPTION_MODEL",
    )
    transcription_model_fast: str = Field(
        default="gpt-4o-mini-transcribe",
        alias="TRANSCRIPTION_MODEL_FAST",
    )
    transcription_model_premium: str = Field(
        default="gpt-4o-transcribe",
        alias="TRANSCRIPTION_MODEL_PREMIUM",
    )
    text_model: str = Field(default="gpt-5.4-mini", alias="TEXT_MODEL")
    text_model_free: str = Field(default="gpt-5.4-mini", alias="TEXT_MODEL_FREE")
    text_model_paid: str = Field(default="gpt-5.4-mini", alias="TEXT_MODEL_PAID")
    text_model_hr: str = Field(default="gpt-5.4", alias="TEXT_MODEL_HR")
    text_model_legacy: str = Field(default="gpt-5.4-mini", alias="TEXT_MODEL_LEGACY")

    @field_validator("admin_telegram_ids", mode="before")
    @classmethod
    def parse_admin_telegram_ids(cls, value: object) -> object:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def set_model_fallbacks(self) -> "Settings":
        if not self.transcription_model_fast.strip():
            self.transcription_model_fast = (
                self.transcription_model.strip() or "gpt-4o-mini-transcribe"
            )
        if not self.transcription_model_premium.strip():
            self.transcription_model_premium = "gpt-4o-transcribe"
        if not self.text_model.strip():
            self.text_model = self.text_model_paid.strip() or "gpt-5.4-mini"
        if not self.text_model_free.strip():
            self.text_model_free = self.text_model.strip() or "gpt-5.4-mini"
        if not self.text_model_paid.strip():
            self.text_model_paid = self.text_model.strip() or "gpt-5.4-mini"
        if not self.text_model_hr.strip():
            self.text_model_hr = self.text_model_paid.strip() or "gpt-5.4"
        if not self.text_model_legacy.strip():
            self.text_model_legacy = self.text_model_paid.strip() or "gpt-5.4-mini"
        return self

    def is_admin(self, telegram_id: int) -> bool:
        return telegram_id in self.admin_telegram_ids


@lru_cache
def get_settings() -> Settings:
    return Settings()
