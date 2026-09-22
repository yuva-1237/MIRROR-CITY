"""
Mirror City central configuration (Pydantic Settings).

Wiring contract:
    .env file  ->  Settings (this file)  ->  database/connection.py  ->  services

Rules enforced here, at import time, so nothing "half-runs" with bad config:
  1. JWT_SECRET is required, minimum 32 chars, no fallback. Server fails fast.
  2. DATABASE_MODE=postgis requires POSTGIS_URL.
  3. ENABLE_LIVE_TRAFFIC requires TOMTOM_API_KEY.
  4. LLM_PROVIDER=gemini requires GEMINI_API_KEY. "auto" resolves at runtime.

Usage:
    from configs.config import get_settings, settings
    settings = get_settings()
"""

from functools import lru_cache
import os
import logging
from typing import Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

BANNED_JWT_SECRETS = {
    "change-me",
    "super-secret-key",
    "your-secret-here",
    "changeme",
    "super-secret-key-for-mirror-city-12345",
    "your-cryptographic-secret-key-min-32-chars",
}



class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Core ---
    APP_NAME: str = "Mirror City"
    PROJECT_NAME: str = "MIRROR CITY"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"  # development | staging | production

    # --- Database (dual mode: zero-setup SQLite or production PostGIS) ---
    DATABASE_MODE: str = "sqlite"       # sqlite | postgis
    SQLITE_PATH: str = "./mirror_city.db"
    POSTGIS_URL: str = ""               # e.g. postgresql+psycopg://mc:pass@db:5432/mirrorcity
    DATABASE_URL: str = ""              # backward compat
    DATABASE_PATH: str = "./mirror_city.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # --- Security (no defaults that could ship) ---
    JWT_SECRET: str = Field(default="")
    JWT_ALGORITHM: str = "HS256"
    ALGORITHM: str = "HS256"            # backward compat alias
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    BCRYPT_ROUNDS: int = 12
    FORCE_PASSWORD_RESET_ON_FIRST_LOGIN: bool = True

    # --- LLM ---
    LLM_PROVIDER: str = "auto"          # auto | gemini | openai | mock
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # --- External data sources ---
    OPENWEATHER_API_KEY: str = ""
    WEATHERAPI_API_KEY: str = ""
    TOMTOM_API_KEY: str = ""
    ENABLE_LIVE_TRAFFIC: bool = False   # real corridor ingestion; requires TOMTOM_API_KEY
    TOMTOM_POLL_INTERVAL_MIN: int = 15

    # --- Caching / limits ---
    GEOCODE_CACHE_TTL: int = 600
    ENSO_CACHE_TTL: int = 21600         # 6 hours TTL for NOAA ENSO climate data
    RATE_LIMIT_PER_MINUTE: int = 60

    # --- Graph City Parameters ---
    GRID_SIZE: int = 10
    DEFAULT_CAPACITY: float = 100.0

    # --- Data truthfulness ---
    ALLOW_SIMULATED_DATA: bool = True   # set False in production demos with real keys

    @field_validator("JWT_SECRET")
    @classmethod
    def _jwt_secret_required(cls, v: str) -> str:
        # Refuse well-known placeholder values even if they are long or short.
        if v and (v.strip().lower() in BANNED_JWT_SECRETS or "placeholder" in v.lower() or "change-me" in v.lower() or "secret-key" in v.lower()):
            raise ValueError("JWT_SECRET looks like a placeholder. Set a real secret.")
        if not v or len(v.strip()) < 32:
            raise ValueError(
                "CRITICAL SECURITY ERROR: JWT_SECRET environment variable is required and must be at least 32 characters. "
                "Set it in your .env (see .env.example). No insecure default is provided."
            )
        return v


    @field_validator("DATABASE_MODE")
    @classmethod
    def _db_mode_valid(cls, v: str) -> str:
        if v not in ("sqlite", "postgis"):
            raise ValueError("DATABASE_MODE must be 'sqlite' or 'postgis'")
        return v

    @model_validator(mode="after")
    def _cross_field_consistency(self):
        if self.DATABASE_MODE == "postgis" and not self.POSTGIS_URL:
            raise ValueError("DATABASE_MODE=postgis requires POSTGIS_URL to be set.")
        if self.ENABLE_LIVE_TRAFFIC and not self.TOMTOM_API_KEY:
            raise ValueError("ENABLE_LIVE_TRAFFIC=true requires TOMTOM_API_KEY.")
        
        # Populate backward-compatible DATABASE_URL
        if not self.DATABASE_URL:
            if self.DATABASE_MODE == "postgis":
                self.DATABASE_URL = self.POSTGIS_URL
            else:
                abs_path = os.path.abspath(self.SQLITE_PATH)
                self.DATABASE_PATH = abs_path
                self.DATABASE_URL = f"sqlite:///{abs_path}"

        # LLM validation
        if self.LLM_PROVIDER == "gemini" and not self.GEMINI_API_KEY.strip():
            raise ValueError(
                "CRITICAL CONFIG ERROR: LLM_PROVIDER is set to 'gemini' but GEMINI_API_KEY is empty. "
                "Please configure GEMINI_API_KEY in your .env file or environment."
            )
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY.strip():
            raise ValueError(
                "CRITICAL CONFIG ERROR: LLM_PROVIDER is set to 'openai' but OPENAI_API_KEY is empty. "
                "Please configure OPENAI_API_KEY in your .env file or environment."
            )

        if self.ENVIRONMENT == "production" and self.ALLOW_SIMULATED_DATA:
            logger.warning(
                "ALLOW_SIMULATED_DATA=True in production: simulated telemetry "
                "will be labelled 'simulated' in the UI, never 'live_api'."
            )
        return self

    @property
    def resolved_llm_provider(self) -> str:
        if self.LLM_PROVIDER != "auto":
            return self.LLM_PROVIDER
        return "gemini" if self.GEMINI_API_KEY else "mock"


def validate_settings(s: Settings) -> None:
    """Manual validator hook to verify runtime settings or test configurations."""
    if not s.JWT_SECRET or len(s.JWT_SECRET.strip()) < 32:
        raise ValueError(
            "CRITICAL SECURITY ERROR: JWT_SECRET environment variable is required and must be at least 32 characters. "
            "Configure a cryptographically secure JWT_SECRET in your .env file or environment."
        )
    if s.JWT_SECRET.strip().lower() in BANNED_JWT_SECRETS:
        raise ValueError(
            "Insecure legacy development secret detected in JWT_SECRET. "
            "You MUST configure a secure, unique JWT_SECRET in your environment."
        )
    if s.DATABASE_MODE == "postgis" and not s.POSTGIS_URL:
        raise ValueError("DATABASE_MODE=postgis requires POSTGIS_URL to be set.")
    if s.ENABLE_LIVE_TRAFFIC and not s.TOMTOM_API_KEY:
        raise ValueError("ENABLE_LIVE_TRAFFIC=true requires TOMTOM_API_KEY.")
    if s.LLM_PROVIDER == "gemini" and not s.GEMINI_API_KEY.strip():
        raise ValueError(
            "CRITICAL CONFIG ERROR: LLM_PROVIDER is set to 'gemini' but GEMINI_API_KEY is empty. "
            "Please configure GEMINI_API_KEY in your .env file or environment."
        )
    if s.LLM_PROVIDER == "openai" and not s.OPENAI_API_KEY.strip():
        raise ValueError(
            "CRITICAL CONFIG ERROR: LLM_PROVIDER is set to 'openai' but OPENAI_API_KEY is empty. "
            "Please configure OPENAI_API_KEY in your .env file or environment."
        )


@lru_cache
def get_settings() -> Settings:
    """Cached so env is parsed once and every module sees identical settings."""
    return Settings()


# Singleton export for direct imports: from configs.config import settings
settings = get_settings()
