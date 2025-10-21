from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    debug: bool = Field(default=True)
    app_name: str = Field(default="AI Product Description Generator")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int | None = Field(default=None, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_sender: str | None = Field(default=None, alias="SMTP_SENDER")

    # Cấu hình để đọc file .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
