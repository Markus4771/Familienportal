from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FAMILIENPORTAL_",
        extra="ignore",
    )

    app_name: str = "Familienportal"
    environment: str = "development"
    debug: bool = False
    database_url: str = "sqlite:///./familienportal.db"
    default_profile: str = "small_family"


@lru_cache
def get_settings() -> Settings:
    return Settings()
