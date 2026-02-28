"""Reminder Pydantic models / DTOs."""

from enum import IntEnum
from typing import Optional

from pydantic import BaseModel, Field


class ReminderPriority(IntEnum):
    """EventKit priority values (0=none, 1=high, 5=medium, 9=low)."""

    NONE = 0
    HIGH = 1
    MEDIUM = 5
    LOW = 9


class ReminderCreate(BaseModel):
    """Input model for creating a reminder."""

    title: str = Field(..., min_length=1, max_length=500, description="Reminder title")
    list_name: Optional[str] = Field(default=None, description="Reminder list name (default list if omitted)")
    due_date: Optional[str] = Field(default=None, description="Due date in YYYY-MM-DD format")
    priority: ReminderPriority = Field(default=ReminderPriority.NONE, description="Priority: 0=none, 1=high, 5=medium, 9=low")
    notes: Optional[str] = Field(default=None, description="Reminder notes")


class ReminderUpdate(BaseModel):
    """Input model for updating a reminder."""

    reminder_id: str = Field(..., description="Reminder identifier to update")
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    due_date: Optional[str] = Field(default=None, description="New due date YYYY-MM-DD")
    priority: Optional[ReminderPriority] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    completed: Optional[bool] = Field(default=None, description="Mark as completed or incomplete")
