"""Calendar event Pydantic models / DTOs."""

from typing import Optional

from pydantic import BaseModel, Field


class CalendarInfo(BaseModel):
    """Represents a calendar (read-only info)."""

    name: str = Field(description="Calendar display name")
    calendar_type: str = Field(default="unknown", description="Calendar type")
    color: Optional[str] = Field(default=None, description="Calendar color hex")
    is_subscribed: bool = Field(default=False, description="Whether calendar is subscribed/read-only")


class EventCreate(BaseModel):
    """Input model for creating a calendar event."""

    title: str = Field(..., min_length=1, max_length=500, description="Event title")
    start: str = Field(..., description="Start date/time in ISO 8601 format")
    end: str = Field(..., description="End date/time in ISO 8601 format")
    calendar_name: Optional[str] = Field(default=None, description="Target calendar name (default calendar if omitted)")
    is_all_day: bool = Field(default=False, description="Whether this is an all-day event")
    location: Optional[str] = Field(default=None, description="Event location")
    notes: Optional[str] = Field(default=None, description="Event notes")
    url: Optional[str] = Field(default=None, description="Associated URL")


class EventUpdate(BaseModel):
    """Input model for updating a calendar event."""

    event_id: str = Field(..., description="Event identifier to update")
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    start: Optional[str] = Field(default=None, description="New start date/time ISO 8601")
    end: Optional[str] = Field(default=None, description="New end date/time ISO 8601")
    location: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    is_all_day: Optional[bool] = Field(default=None)
