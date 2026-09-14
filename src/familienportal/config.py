from functools import lru_cache
from typing import Annotated
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
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
    session_max_age_seconds: int = 43200

    security_encryption_key: str = "development-only-change-security-key"
    password_reset_ttl_minutes: int = 30
    mfa_issuer: str = "Familienportal"
    require_admin_mfa: bool = False
    login_max_failures: int = 5
    login_window_minutes: int = 15
    login_lock_minutes: int = 15
    webauthn_rp_id: str | None = None
    webauthn_rp_name: str = "Familienportal"
    webauthn_origin: str | None = None

    worker_interval_seconds: int = 60
    calendar_sync_interval_minutes: int = 5

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_starttls: bool = True

    @field_validator("trusted_hosts", "trusted_proxies", mode="before")
    @classmethod
    def split_comma_separated_values(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("public_url")
    @classmethod
    def normalize_public_url(cls, value: str) -> str:
        return value.rstrip("/")

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.environment.lower() == "production":
            if self.session_secret_key == "development-only-change-me":
                raise ValueError("FAMILIENPORTAL_SESSION_SECRET_KEY muss in Produktion gesetzt sein")
            if self.security_encryption_key == "development-only-change-security-key":
                raise ValueError("FAMILIENPORTAL_SECURITY_ENCRYPTION_KEY muss in Produktion gesetzt sein")
            if not self.secure_cookies:
                raise ValueError("FAMILIENPORTAL_SECURE_COOKIES muss in Produktion true sein")
        return self

    @property
    def effective_webauthn_origin(self) -> str:
        return (self.webauthn_origin or self.public_url).rstrip("/")

    @property
    def effective_webauthn_rp_id(self) -> str:
        if self.webauthn_rp_id:
            return self.webauthn_rp_id
        hostname = urlparse(self.public_url).hostname
        return hostname or "localhost"

    @property
    def forwarded_allow_ips(self) -> str:
        return ",".join(self.trusted_proxies)

    @property
    def database_backend(self) -> str:
        return self.database_url.split(":", 1)[0]


@lru_cache
def get_settings() -> Settings:
    return Settings()
