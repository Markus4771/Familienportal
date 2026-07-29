from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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

    public_url: str = "http://localhost:8000"
    bind_host: str = "127.0.0.1"
    bind_port: int = 8000
    trusted_hosts: Annotated[list[str], NoDecode] = ["localhost", "127.0.0.1"]
    trusted_proxies: Annotated[list[str], NoDecode] = ["127.0.0.1"]
    secure_cookies: bool = False
    session_secret_key: str = "development-only-change-me"

    @field_validator("trusted_hosts", "trusted_proxies", mode="before")
    @classmethod
    def split_comma_separated_values(cls, value: object) -> object:
        """Accept comma-separated lists from systemd environment files."""

        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("public_url")
    @classmethod
    def normalize_public_url(cls, value: str) -> str:
        return value.rstrip("/")

    @property
    def forwarded_allow_ips(self) -> str:
        """Return the Uvicorn-compatible trusted proxy list."""

        return ",".join(self.trusted_proxies)


@lru_cache
def get_settings() -> Settings:
    return Settings()
