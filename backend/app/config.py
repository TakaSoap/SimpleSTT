from functools import lru_cache
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: Literal["development", "production", "test"] = "development"
    app_name: str = "audio-transcription"
    app_version: str = "0.1.0"

    # Authentication
    app_username: str = "admin"
    app_password: str = "changeme"

    # Storage settings
    storage_dir: Path = Path("./storage")
    storage_ttl_seconds: int = 6 * 60 * 60  # 6 hours

    # Provider defaults exposed to the frontend
    default_provider: Literal["openai", "azure"] = "openai"
    default_model: str = "gpt-4o-transcribe"
    default_language: str = ""
    default_stream_enabled: bool = True
    default_azure_endpoint: Optional[HttpUrl] = None
    default_azure_deployment_id: str = "gpt-4o-transcribe"
    default_azure_api_version: str = "2025-04-01-preview"
    default_openai_api_key: Optional[str] = None
    default_azure_api_key: Optional[str] = None

    # Currency conversion
    usd_to_cny_rate: float = 7.3
    usd_to_hkd_rate: float = 7.8

    cors_allow_origins: List[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("default_azure_endpoint", mode="before")
    @classmethod
    def _empty_url_to_none(cls, value: Optional[str]):
        if value is None:
            return value
        if isinstance(value, str) and value.strip() == "":
            return None
        return value


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    return settings
