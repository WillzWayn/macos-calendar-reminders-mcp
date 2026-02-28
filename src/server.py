"""FastMCP server with tool registrations.

Single Responsibility: Only registers MCP tools and wires up dependencies.
Tool handlers are thin - they delegate to the service layer.
"""

import datetime
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Optional

from mcp.server.fastmcp import Context, FastMCP

from src.config import get_settings
from src.eventkit.store import EventKitStore
from src.services.calendar_service import CalendarService
from src.services.reminder_service import ReminderService


@dataclass
class AppContext:
    """Dependency injection container passed via lifespan."""

    event_store: EventKitStore
    calendar_service: CalendarService
    reminder_service: ReminderService


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Composition root: create services and inject into AppContext."""
    store = EventKitStore()

    cal_granted, rem_granted = store.request_all_access()
    if not cal_granted:
        print("WARNING: Calendar access not granted")
    if not rem_granted:
        print("WARNING: Reminder access not granted")

    calendar_service = CalendarService(store)
    reminder_service = ReminderService(store)

    yield AppContext(
        event_store=store,
        calendar_service=calendar_service,
        reminder_service=reminder_service,
    )


mcp = FastMCP(
    "Calendar & Reminders MCP",
    lifespan=app_lifespan,
    json_response=True,
)


# ---------------------------------------------------------------------------
# Calendar tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_calendars(ctx: Context) -> list[dict]:
    """List all available calendars on this Mac."""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        return app_ctx.calendar_service.list_calendars()
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
async def list_events(
    ctx: Context,
    start: Optional[str] = None,
    end: Optional[str] = None,
    calendar_name: Optional[str] = None,
) -> list[dict]:
    """List calendar events within a date range.

    Args:
        start: Start date in ISO 8601 (defaults to today).
        end: End date in ISO 8601 (defaults to 7 days from start).
        calendar_name: Filter to a specific calendar name.
    """
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        settings = get_settings()

        if not start:
            now = datetime.datetime.now(datetime.timezone.utc)
            start = now.replace(hour=0, minute=0, second=0).isoformat()
        if not end:
            start_dt = datetime.datetime.fromisoformat(start)
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=datetime.timezone.utc)
            end_dt = start_dt + datetime.timedelta(days=settings.default_event_range_days)
            end = end_dt.isoformat()

        return app_ctx.calendar_service.list_events(start, end, calendar_name)
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
async def get_event(ctx: Context, event_id: str) -> dict:
    """Get details of a specific calendar event by its ID."""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        result = app_ctx.calendar_service.get_event(event_id)
        if not result:
            return {"error": f"Event '{event_id}' not found"}
        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def create_event(
    ctx: Context,
    title: str,
    start: str,
    end: str,
    calendar_name: Optional[str] = None,
    is_all_day: bool = False,
    location: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """Create a new calendar event.

    Args:
        title: Event title.
        start: Start date/time in ISO 8601.
        end: End date/time in ISO 8601.
        calendar_name: Target calendar (uses default if omitted).
        is_all_day: Whether this is an all-day event.
        location: Event location.
        notes: Event notes.
    """
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        return app_ctx.calendar_service.create_event({
            "title": title,
            "start": start,
            "end": end,
            "calendar_name": calendar_name,
            "is_all_day": is_all_day,
            "location": location,
            "notes": notes,
        })
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def update_event(
    ctx: Context,
    event_id: str,
    title: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    location: Optional[str] = None,
    notes: Optional[str] = None,
    is_all_day: Optional[bool] = None,
) -> dict:
    """Update an existing calendar event.

    Args:
        event_id: The event identifier to update.
        title: New title (omit to keep current).
        start: New start date/time ISO 8601.
        end: New end date/time ISO 8601.
        location: New location.
        notes: New notes.
        is_all_day: Set all-day flag.
    """
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        return app_ctx.calendar_service.update_event({
            "event_id": event_id,
            "title": title,
            "start": start,
            "end": end,
            "location": location,
            "notes": notes,
            "is_all_day": is_all_day,
        })
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def delete_event(ctx: Context, event_id: str) -> dict:
    """Delete a calendar event by its ID."""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        success = app_ctx.calendar_service.delete_event(event_id)
        if success:
            return {"status": "deleted", "event_id": event_id}
        return {"error": f"Failed to delete event '{event_id}'"}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Reminder tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_reminder_lists(ctx: Context) -> list[dict]:
    """List all reminder lists on this Mac."""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        return app_ctx.reminder_service.list_reminder_lists()
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
async def list_reminders(
    ctx: Context,
    list_name: Optional[str] = None,
    include_completed: bool = False,
) -> list[dict]:
    """List reminders, optionally filtered by list name.

    Args:
        list_name: Filter to a specific reminder list.
        include_completed: Include completed reminders (default: False).
    """
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        return app_ctx.reminder_service.list_reminders(list_name, include_completed)
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
async def create_reminder(
    ctx: Context,
    title: str,
    list_name: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: int = 0,
    notes: Optional[str] = None,
) -> dict:
    """Create a new reminder.

    Args:
        title: Reminder title.
        list_name: Target reminder list (uses default if omitted).
        due_date: Due date in YYYY-MM-DD format.
        priority: Priority (0=none, 1=high, 5=medium, 9=low).
        notes: Reminder notes.
    """
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        return app_ctx.reminder_service.create_reminder({
            "title": title,
            "list_name": list_name,
            "due_date": due_date,
            "priority": priority,
            "notes": notes,
        })
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def update_reminder(
    ctx: Context,
    reminder_id: str,
    title: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[int] = None,
    notes: Optional[str] = None,
    completed: Optional[bool] = None,
) -> dict:
    """Update an existing reminder.

    Args:
        reminder_id: The reminder identifier to update.
        title: New title.
        due_date: New due date YYYY-MM-DD.
        priority: New priority (0=none, 1=high, 5=medium, 9=low).
        notes: New notes.
        completed: Mark as completed/incomplete.
    """
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        return app_ctx.reminder_service.update_reminder({
            "reminder_id": reminder_id,
            "title": title,
            "due_date": due_date,
            "priority": priority,
            "notes": notes,
            "completed": completed,
        })
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def complete_reminder(ctx: Context, reminder_id: str) -> dict:
    """Mark a reminder as completed."""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        success = app_ctx.reminder_service.complete_reminder(reminder_id)
        if success:
            return {"status": "completed", "reminder_id": reminder_id}
        return {"error": f"Failed to complete reminder '{reminder_id}'"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def delete_reminder(ctx: Context, reminder_id: str) -> dict:
    """Delete a reminder by its ID."""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        success = app_ctx.reminder_service.delete_reminder(reminder_id)
        if success:
            return {"status": "deleted", "reminder_id": reminder_id}
        return {"error": f"Failed to delete reminder '{reminder_id}'"}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the MCP server."""
    settings = get_settings()
    transport = "stdio" if "--stdio" in sys.argv else settings.transport
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
