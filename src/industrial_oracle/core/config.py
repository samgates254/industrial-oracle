"""Core application configuration using Pydantic Settings."""

import os
from typing import List, Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


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

    # Database Configuration (PostgreSQL with asyncpg and psycopg2)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/industrial_oracle"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/industrial_oracle"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & Tokens
    JWT_SECRET: str = "industrial-oracle-super-secret-key-change-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Cross-Origin Resource Sharing & Rate Limiting
    CORS_ORIGINS: List[str] = ["*"]
    RATE_LIMIT_PER_MINUTE: int = 60

    # Background Worker & Scheduler
    WORKER_CONCURRENCY: int = 4
    OPTIMIZATION_TIMEOUT_SECONDS: int = 300

    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton settings instance
settings = Settings()
