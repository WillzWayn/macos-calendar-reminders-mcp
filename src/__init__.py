"""Calendar & Reminders MCP Server package."""

from src.config import Settings, get_settings
from src.server import main, mcp

__all__ = ["Settings", "get_settings", "main", "mcp"]
