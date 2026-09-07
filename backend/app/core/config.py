"""
StockSense AI — Application Configuration

All configuration is loaded from environment variables.
Never hard-code credentials or API keys.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_db_url(url: str) -> str:
    """Ensure relative SQLite database paths resolve to the backend directory."""
    if url and "sqlite" in url.lower() and ":///" in url:
        prefix, path_part = url.split(":///", 1)
        p = Path(path_part)
        if not p.is_absolute():
            backend_dir = Path(__file__).resolve().parent.parent.parent
            resolved_path = (backend_dir / p).resolve().as_posix()
            return f"{prefix}:///{resolved_path}"
    return url


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    app_name: str = "StockSense AI"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "CHANGE_ME_TO_A_RANDOM_64_CHAR_STRING"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:3000"
    cors_origins: List[str] = ["http://localhost:3000"]

    # ---- Database ----
    postgres_user: str = "stocksense"
    postgres_password: str = "stocksense_dev_password"
    postgres_db: str = "stocksense"
    postgres_host: str = "db"
    postgres_port: int = 5432
    database_url: str = ""
    database_url_sync: str = ""
    sync_database_url: str = ""

    # ---- Redis ----
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_url: str = ""

    # ---- Celery ----
    celery_broker_url: str = ""
    celery_result_backend: str = ""

    # ---- Data Provider API Keys ----
    alpha_vantage_api_key: str = ""
    fmp_api_key: str = ""
    finnhub_api_key: str = ""
    fred_api_key: str = ""
    sec_user_agent: str = "StockSenseAI admin@example.com"
    sec_edgar_user_agent: str = ""
    grok_api_key: str = ""

    # ---- JWT Auth ----
    jwt_secret_key: str = "CHANGE_ME_TO_ANOTHER_RANDOM_STRING"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # ---- Rate Limiting ----
    rate_limit_per_minute: int = 60
    analysis_rate_limit_per_day: int = 100

    # ---- Logging ----
    log_level: str = "INFO"
    log_format: str = "json"

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str, info) -> str:
        if v:
            return _normalize_db_url(v)
        values = info.data
        user = values.get("postgres_user", "stocksense")
        password = values.get("postgres_password", "stocksense_dev_password")
        host = values.get("postgres_host", "db")
        port = values.get("postgres_port", 5432)
        db = values.get("postgres_db", "stocksense")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    @field_validator("database_url_sync", mode="before")
    @classmethod
    def assemble_db_url_sync(cls, v: str, info) -> str:
        if v:
            return _normalize_db_url(v)
        values = info.data
        if values.get("sync_database_url"):
            return _normalize_db_url(values.get("sync_database_url"))
        user = values.get("postgres_user", "stocksense")
        password = values.get("postgres_password", "stocksense_dev_password")
        host = values.get("postgres_host", "db")
        port = values.get("postgres_port", 5432)
        db = values.get("postgres_db", "stocksense")
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"

    @field_validator("redis_url", mode="before")
    @classmethod
    def assemble_redis_url(cls, v: str, info) -> str:
        if v:
            return v
        values = info.data
        host = values.get("redis_host", "redis")
        port = values.get("redis_port", 6379)
        return f"redis://{host}:{port}/0"

    @field_validator("celery_broker_url", mode="before")
    @classmethod
    def assemble_celery_broker(cls, v: str, info) -> str:
        if v:
            return v
        values = info.data
        host = values.get("redis_host", "redis")
        port = values.get("redis_port", 6379)
        return f"redis://{host}:{port}/1"

    @field_validator("celery_result_backend", mode="before")
    @classmethod
    def assemble_celery_backend(cls, v: str, info) -> str:
        if v:
            return v
        values = info.data
        host = values.get("redis_host", "redis")
        port = values.get("redis_port", 6379)
        return f"redis://{host}:{port}/2"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


# Singleton instance
settings = Settings()
