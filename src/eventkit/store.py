"""EventKit store wrapper - manages EKEventStore lifecycle and permissions."""

import threading
from typing import Optional

import EventKit


class EventKitStore:
    """Wraps EKEventStore with permission handling and lifecycle management.

    Single Responsibility: Only manages the EventKit store instance and permissions.
    """

    def __init__(self) -> None:
        self._store: EventKit.EKEventStore = EventKit.EKEventStore.alloc().init()
        self._calendar_access_granted: bool = False
        self._reminder_access_granted: bool = False

    @property
    def store(self) -> EventKit.EKEventStore:
        """Return the underlying EKEventStore instance."""
        return self._store

    @property
    def has_calendar_access(self) -> bool:
        return self._calendar_access_granted

    @property
    def has_reminder_access(self) -> bool:
        return self._reminder_access_granted

    def request_calendar_access(self) -> bool:
        """Request access to calendar events. Blocks until user responds."""
        if self._calendar_access_granted:
            return True

        event = threading.Event()
        result = [False]

        def callback(granted: bool, error: object) -> None:
            result[0] = granted
            if error:
                print(f"Calendar access error: {error}")
            event.set()

        self._store.requestAccessToEntityType_completion_(
            EventKit.EKEntityTypeEvent, callback
        )
        event.wait(timeout=30)
        self._calendar_access_granted = result[0]
        return self._calendar_access_granted

    def request_reminder_access(self) -> bool:
        """Request access to reminders. Blocks until user responds."""
        if self._reminder_access_granted:
            return True

        event = threading.Event()
        result = [False]

        def callback(granted: bool, error: object) -> None:
            result[0] = granted
            if error:
                print(f"Reminder access error: {error}")
            event.set()

        self._store.requestAccessToEntityType_completion_(
            EventKit.EKEntityTypeReminder, callback
        )
        event.wait(timeout=30)
        self._reminder_access_granted = result[0]
        return self._reminder_access_granted

    def request_all_access(self) -> tuple[bool, bool]:
        """Request access to both calendars and reminders.

        Returns:
            Tuple of (calendar_granted, reminder_granted).
        """
        cal = self.request_calendar_access()
        rem = self.request_reminder_access()
        return cal, rem

    def get_calendars(
        self, entity_type: int = EventKit.EKEntityTypeEvent
    ) -> list:
        """Return all calendars for the given entity type."""
        return list(self._store.calendarsForEntityType_(entity_type) or [])

    def get_calendar_by_name(
        self,
        name: str,
        entity_type: int = EventKit.EKEntityTypeEvent,
    ) -> Optional[object]:
        """Find a calendar by its display name."""
        for cal in self.get_calendars(entity_type):
            if cal.title() == name:
                return cal
        return None

    def get_default_calendar(self) -> Optional[object]:
        """Return the default calendar for new events."""
        return self._store.defaultCalendarForNewEvents()

    def get_default_reminder_list(self) -> Optional[object]:
        """Return the default reminder list."""
        return self._store.defaultCalendarForNewReminders()

    def commit(self) -> bool:
        """Commit pending changes to the event store.

        Returns:
            True if commit succeeded, False otherwise.
        """
        success, error = self._store.commit_(None)
        if error:
            print(f"EventKit commit error: {error}")
        return bool(success)
