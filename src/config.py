"""Application configuration via pydantic-settings."""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Calendar & Reminders MCP"
    server_port: int = 8000
    transport: str = "streamable-http"
    default_event_range_days: int = 7

    model_config = {"env_prefix": "MCP_"}


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Return cached settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
