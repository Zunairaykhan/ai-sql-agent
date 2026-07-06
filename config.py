"""
config.py
Centralized application configuration loaded from environment variables.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def _get_env(name: str, default: Optional[str] = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Please set it in your .env file (see .env.example)."
        )
    return value


class Settings:
    """Application settings loaded once at import time."""

    # --- Groq API ---
    GROQ_API_KEY: str = _get_env("GROQ_API_KEY", required=True)
    GROQ_MODEL: str = _get_env("GROQ_MODEL", default="llama-3.3-70b-versatile")

    # --- PostgreSQL ---
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    PG_HOST: str = _get_env("PG_HOST", default="localhost")
    PG_PORT: str = _get_env("PG_PORT", default="5432")
    PG_DATABASE: str = _get_env("PG_DATABASE", default="postgres")
    PG_USER: str = _get_env("PG_USER", default="postgres")
    PG_PASSWORD: str = _get_env("PG_PASSWORD", default="")
    PG_SCHEMA: str = _get_env("PG_SCHEMA", default="public")

    # --- App ---
    APP_HOST: str = _get_env("APP_HOST", default="0.0.0.0")
    APP_PORT: int = int(_get_env("APP_PORT", default="8000"))
    CORS_ORIGINS: list = _get_env("CORS_ORIGINS", default="*").split(",")
    LOG_LEVEL: str = _get_env("LOG_LEVEL", default="INFO")

    # --- Query safety ---
    MAX_ROWS_RETURNED: int = int(_get_env("MAX_ROWS_RETURNED", default="200"))
    QUERY_TIMEOUT_SECONDS: int = int(_get_env("QUERY_TIMEOUT_SECONDS", default="15"))


settings = Settings()


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
