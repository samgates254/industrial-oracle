"""Core application configuration using Pydantic Settings."""

import secrets
from typing import List

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Project Information
    PROJECT_NAME: str = "Industrial Oracle"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Observability & Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "text"

    # Database Configuration (PostgreSQL with asyncpg)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/industrial_oracle"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & Tokens
    JWT_SECRET: str = Field(default="", repr=False)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Cross-Origin Resource Sharing & Rate Limiting
    CORS_ORIGINS: List[str] = ["*"]
    RATE_LIMIT_PER_MINUTE: int = 60

    # Background Worker & Scheduler
    WORKER_CONCURRENCY: int = 4
    OPTIMIZATION_TIMEOUT_SECONDS: int = 300

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    @model_validator(mode="after")
    def validate_jwt_secret(self) -> "Settings":
        """Require a deployment secret; generate only an ephemeral development key."""
        secret = self.JWT_SECRET
        normalized_secret = secret.casefold()

        if (
            not secret
            or len(secret.encode("utf-8")) < 32
            or len(set(secret)) < 12
            or "change-in-production" in normalized_secret
            or normalized_secret in {"secret", "changeme", "change-me", "development-secret"}
        ):
            if self.ENVIRONMENT.casefold() == "development" and not secret:
                self.JWT_SECRET = secrets.token_urlsafe(48)
                return self
            raise ValueError(
                "JWT_SECRET must be at least 32 bytes, contain sufficient variation, "
                "and not be a known placeholder."
            )

        return self


# Singleton settings instance
settings = Settings()
