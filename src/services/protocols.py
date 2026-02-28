"""Abstract service protocols - Interface Segregation + Dependency Inversion."""

from typing import Optional, Protocol

from src.models.event import EventCreate, EventUpdate
from src.models.reminder import ReminderCreate, ReminderUpdate


class CalendarServiceProtocol(Protocol):
    """Protocol for calendar event operations."""

    def list_calendars(self) -> list[dict]: ...

    def list_events(
        self,
        start: str,
        end: str,
        calendar_name: Optional[str] = None,
    ) -> list[dict]: ...

    def get_event(self, event_id: str) -> Optional[dict]: ...

    def create_event(self, data: EventCreate) -> dict: ...

    def update_event(self, data: EventUpdate) -> dict: ...

    def delete_event(self, event_id: str) -> bool: ...


class ReminderServiceProtocol(Protocol):
    """Protocol for reminder operations."""

    def list_reminder_lists(self) -> list[dict]: ...

    def list_reminders(
        self,
        list_name: Optional[str] = None,
        include_completed: bool = False,
    ) -> list[dict]: ...

    def create_reminder(self, data: ReminderCreate) -> dict: ...

    def update_reminder(self, data: ReminderUpdate) -> dict: ...

    def complete_reminder(self, reminder_id: str) -> bool: ...

    def delete_reminder(self, reminder_id: str) -> bool: ...
