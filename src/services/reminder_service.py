"""Concrete reminder service using EventKit.

Single Responsibility: Only handles reminder CRUD operations.
Liskov Substitution: Implements ReminderServiceProtocol.
"""

import threading
from typing import Optional

import EventKit
from Foundation import NSDateComponents

from src.eventkit.converters import reminder_to_dict
from src.eventkit.store import EventKitStore


class ReminderService:
    """Reminder operations backed by EventKit."""

    def __init__(self, store: EventKitStore) -> None:
        self._store = store

    def list_reminder_lists(self) -> list[dict]:
        """List all reminder lists (calendars of type Reminder)."""
        calendars = self._store.get_calendars(EventKit.EKEntityTypeReminder)
        result = []
        for cal in calendars:
            result.append({
                "name": cal.title(),
                "is_subscribed": bool(cal.isSubscribed()),
            })
        return result

    def _fetch_reminders_sync(
        self,
        predicate: object,
    ) -> list:
        """Fetch reminders synchronously using a threading event.

        EventKit's fetchRemindersMatchingPredicate:completion: is async,
        so we block on a threading.Event to collect results.
        """
        event = threading.Event()
        results: list = []

        def callback(reminders: object) -> None:
            if reminders:
                results.extend(list(reminders))
            event.set()

        self._store.store.fetchRemindersMatchingPredicate_completion_(
            predicate, callback
        )
        event.wait(timeout=30)
        return results

    def list_reminders(
        self,
        list_name: Optional[str] = None,
        include_completed: bool = False,
    ) -> list[dict]:
        """List reminders, optionally filtered by list name.

        Args:
            list_name: Filter to a specific reminder list (None = all).
            include_completed: Whether to include completed reminders.
        """
        calendars = None
        if list_name:
            cal = self._store.get_calendar_by_name(
                list_name, EventKit.EKEntityTypeReminder
            )
            if cal:
                calendars = [cal]
            else:
                return []

        if include_completed:
            predicate = self._store.store.predicateForRemindersInCalendars_(calendars)
        else:
            predicate = self._store.store.predicateForIncompleteRemindersWithDueDateStarting_ending_calendars_(
                None, None, calendars
            )

        reminders = self._fetch_reminders_sync(predicate)
        return [reminder_to_dict(r) for r in reminders]

    def create_reminder(self, data: dict) -> dict:
        """Create a new reminder.

        Args:
            data: Dict with title and optional fields.
        """
        try:
            reminder = EventKit.EKReminder.reminderWithEventStore_(self._store.store)
            reminder.setTitle_(data["title"])

            if data.get("priority") is not None:
                reminder.setPriority_(int(data["priority"]))

            if data.get("notes"):
                reminder.setNotes_(data["notes"])

            # Set due date
            if data.get("due_date"):
                parts = data["due_date"].split("-")
                if len(parts) == 3:
                    components = NSDateComponents.alloc().init()
                    components.setYear_(int(parts[0]))
                    components.setMonth_(int(parts[1]))
                    components.setDay_(int(parts[2]))
                    reminder.setDueDateComponents_(components)

            # Set reminder list
            list_name = data.get("list_name")
            if list_name:
                cal = self._store.get_calendar_by_name(
                    list_name, EventKit.EKEntityTypeReminder
                )
                if cal:
                    reminder.setCalendar_(cal)
                else:
                    return {"error": f"Reminder list '{list_name}' not found"}
            else:
                default_list = self._store.get_default_reminder_list()
                if default_list:
                    reminder.setCalendar_(default_list)

            success, error = self._store.store.saveReminder_commit_error_(
                reminder, True, None
            )
            if not success:
                return {"error": f"Failed to save reminder: {error}"}

            return reminder_to_dict(reminder)
        except Exception as e:
            return {"error": str(e)}

    def update_reminder(self, data: dict) -> dict:
        """Update an existing reminder.

        Args:
            data: Dict with reminder_id and fields to update.
        """
        try:
            reminder = self._find_reminder_by_id(data["reminder_id"])
            if not reminder:
                return {"error": f"Reminder '{data['reminder_id']}' not found"}

            if data.get("title"):
                reminder.setTitle_(data["title"])

            if data.get("priority") is not None:
                reminder.setPriority_(int(data["priority"]))

            if data.get("notes") is not None:
                reminder.setNotes_(data["notes"])

            if data.get("completed") is not None:
                reminder.setCompleted_(bool(data["completed"]))

            if data.get("due_date"):
                parts = data["due_date"].split("-")
                if len(parts) == 3:
                    components = NSDateComponents.alloc().init()
                    components.setYear_(int(parts[0]))
                    components.setMonth_(int(parts[1]))
                    components.setDay_(int(parts[2]))
                    reminder.setDueDateComponents_(components)

            success, error = self._store.store.saveReminder_commit_error_(
                reminder, True, None
            )
            if not success:
                return {"error": f"Failed to update reminder: {error}"}

            return reminder_to_dict(reminder)
        except Exception as e:
            return {"error": str(e)}

    def complete_reminder(self, reminder_id: str) -> bool:
        """Mark a reminder as completed."""
        try:
            reminder = self._find_reminder_by_id(reminder_id)
            if not reminder:
                return False

            reminder.setCompleted_(True)
            success, error = self._store.store.saveReminder_commit_error_(
                reminder, True, None
            )
            return bool(success)
        except Exception:
            return False

    def delete_reminder(self, reminder_id: str) -> bool:
        """Delete a reminder by its identifier."""
        try:
            reminder = self._find_reminder_by_id(reminder_id)
            if not reminder:
                return False

            success, error = self._store.store.removeReminder_commit_error_(
                reminder, True, None
            )
            return bool(success)
        except Exception:
            return False

    def _find_reminder_by_id(self, reminder_id: str) -> Optional[object]:
        """Find a reminder by its calendarItemIdentifier.

        EventKit doesn't provide a direct lookup for reminders by ID,
        so we fetch all and filter.
        """
        predicate = self._store.store.predicateForRemindersInCalendars_(None)
        reminders = self._fetch_reminders_sync(predicate)
        for r in reminders:
            if r.calendarItemIdentifier() == reminder_id:
                return r
        return None
