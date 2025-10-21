from functools import lru_cache
import logging
import secrets
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32), alias="JWT_SECRET")
    debug: bool = Field(default=True)
    app_name: str = Field(default="AI Product Description Generator")

    # Load configuration from an optional .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()

    if not settings.gemini_api_key:
        logger.warning(
            "GEMINI_API_KEY is not set; Gemini-powered endpoints will respond with 503 until configured."
        )
    if "jwt_secret" not in settings.model_fields_set:
        logger.warning("JWT_SECRET is not set; using a generated secret for this process.")

    return settings
