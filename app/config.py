from functools import lru_cache

from pydantic import Field, field_validator
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

    default_free_minutes: int = Field(default=30, alias="DEFAULT_FREE_MINUTES")
    friends_package_minutes: int = Field(
        default=300,
        alias="FRIENDS_PACKAGE_MINUTES",
    )
    power_package_minutes: int = Field(
        default=1000,
        alias="POWER_PACKAGE_MINUTES",
    )

    transcription_model: str = Field(
        default="gpt-4o-mini-transcribe",
        alias="TRANSCRIPTION_MODEL",
    )
    text_model: str = Field(default="gpt-5.4-nano", alias="TEXT_MODEL")

    @field_validator("admin_telegram_ids", mode="before")
    @classmethod
    def parse_admin_telegram_ids(cls, value: object) -> object:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        return value

    def is_admin(self, telegram_id: int) -> bool:
        return telegram_id in self.admin_telegram_ids


@lru_cache
def get_settings() -> Settings:
    return Settings()
