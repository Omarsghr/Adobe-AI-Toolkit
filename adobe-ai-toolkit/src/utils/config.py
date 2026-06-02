from pathlib import Path
from typing import Optional

# Try to use pydantic-settings (pydantic v2) when available, fall back to
# pydantic.BaseSettings for environments where the newer package is not
# installed. This makes the module more robust for local development.
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore
    _PD_SETTINGS_AVAILABLE = True
except Exception:  # pragma: no cover - local fallback for dev machines
    from pydantic import BaseSettings  # type: ignore

    BaseSettings = BaseSettings  # type: ignore
    SettingsConfigDict = dict  # type: ignore
    _PD_SETTINGS_AVAILABLE = False


class Settings(BaseSettings):
    """
    Application settings loaded from the environment.

    Uses pydantic-settings when available; otherwise falls back to
    pydantic.BaseSettings. Values can come from environment variables or
    an optional `.env` file.
    """

    # File-system locations
    database_path: Path = Path("src/database/project_memory.db")
    storage_path: Path = Path("outputs")
    persona_dir: Path = Path("personas")

    # API keys (placeholders; populate via environment in your deployment)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    nvidia_api_key: Optional[str] = None

    # Behaviour flags
    allow_cloud_fallback: bool = False

    if _PD_SETTINGS_AVAILABLE:  # pydantic-settings v2 style
        model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    else:  # fallback to pydantic v1-like BaseSettings behaviour
        class Config:  # type: ignore
            env_file = ".env"
            env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Return a Settings instance for the application.

    Call this from your application entry point and pass the resulting
    instance into modules that need configuration. This keeps modules
    easier to test.
    """

    return Settings()
