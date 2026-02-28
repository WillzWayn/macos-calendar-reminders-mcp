"""Concrete calendar service using EventKit.

Single Responsibility: Only handles calendar event CRUD operations.
Liskov Substitution: Implements CalendarServiceProtocol.
"""

import datetime
from typing import Optional

import EventKit

from src.eventkit.converters import (
    datetime_to_nsdate,
    event_to_dict,
    parse_datetime,
)
from src.eventkit.store import EventKitStore


class CalendarService:
    """Calendar event operations backed by EventKit."""

    def __init__(self, store: EventKitStore) -> None:
        self._store = store

    def list_calendars(self) -> list[dict]:
        """List all available calendars."""
        calendars = self._store.get_calendars(EventKit.EKEntityTypeEvent)
        result = []
        for cal in calendars:
            result.append({
                "name": cal.title(),
                "calendar_type": str(cal.type()),
                "is_subscribed": bool(cal.isSubscribed()),
            })
        return result

    def list_events(
        self,
        start: str,
        end: str,
        calendar_name: Optional[str] = None,
    ) -> list[dict]:
        """List calendar events within a date range.

        Args:
            start: Start date/time in ISO 8601 format.
            end: End date/time in ISO 8601 format.
            calendar_name: Filter to a specific calendar (None = all).
        """
        start_dt = parse_datetime(start)
        end_dt = parse_datetime(end)
        start_ns = datetime_to_nsdate(start_dt)
        end_ns = datetime_to_nsdate(end_dt)

        calendars = None
        if calendar_name:
            cal = self._store.get_calendar_by_name(
                calendar_name, EventKit.EKEntityTypeEvent
            )
            if cal:
                calendars = [cal]
            else:
                return []

        predicate = self._store.store.predicateForEventsWithStartDate_endDate_calendars_(
            start_ns, end_ns, calendars
        )
        events = self._store.store.eventsMatchingPredicate_(predicate)

        if not events:
            return []

        # Sort by start date
        sorted_events = sorted(
            events,
            key=lambda e: e.startDate().timeIntervalSinceReferenceDate(),
        )
        return [event_to_dict(e) for e in sorted_events]

    def get_event(self, event_id: str) -> Optional[dict]:
        """Get a single event by its identifier."""
        event = self._store.store.eventWithIdentifier_(event_id)
        if not event:
            return None
        return event_to_dict(event)

    def create_event(self, data: dict) -> dict:
        """Create a new calendar event.

        Args:
            data: Dict with title, start, end, and optional fields.
        """
        try:
            event = EventKit.EKEvent.eventWithEventStore_(self._store.store)
            event.setTitle_(data["title"])
            event.setStartDate_(datetime_to_nsdate(parse_datetime(data["start"])))
            event.setEndDate_(datetime_to_nsdate(parse_datetime(data["end"])))

            if data.get("is_all_day"):
                event.setAllDay_(True)

            if data.get("location"):
                event.setLocation_(data["location"])

            if data.get("notes"):
                event.setNotes_(data["notes"])

            # Set calendar
            calendar_name = data.get("calendar_name")
            if calendar_name:
                cal = self._store.get_calendar_by_name(
                    calendar_name, EventKit.EKEntityTypeEvent
                )
                if cal:
                    event.setCalendar_(cal)
                else:
                    return {"error": f"Calendar '{calendar_name}' not found"}
            else:
                default_cal = self._store.get_default_calendar()
                if default_cal:
                    event.setCalendar_(default_cal)

            success, error = self._store.store.saveEvent_span_error_(
                event, EventKit.EKSpanThisEvent, None
            )
            if not success:
                return {"error": f"Failed to save event: {error}"}

            return event_to_dict(event)
        except Exception as e:
            return {"error": str(e)}

    def update_event(self, data: dict) -> dict:
        """Update an existing calendar event.

        Args:
            data: Dict with event_id and fields to update.
        """
        try:
            event = self._store.store.eventWithIdentifier_(data["event_id"])
            if not event:
                return {"error": f"Event '{data['event_id']}' not found"}

            if data.get("title"):
                event.setTitle_(data["title"])
            if data.get("start"):
                event.setStartDate_(datetime_to_nsdate(parse_datetime(data["start"])))
            if data.get("end"):
                event.setEndDate_(datetime_to_nsdate(parse_datetime(data["end"])))
            if data.get("location") is not None:
                event.setLocation_(data["location"])
            if data.get("notes") is not None:
                event.setNotes_(data["notes"])
            if data.get("is_all_day") is not None:
                event.setAllDay_(data["is_all_day"])

            success, error = self._store.store.saveEvent_span_error_(
                event, EventKit.EKSpanThisEvent, None
            )
            if not success:
                return {"error": f"Failed to update event: {error}"}

            return event_to_dict(event)
        except Exception as e:
            return {"error": str(e)}

    def delete_event(self, event_id: str) -> bool:
        """Delete an event by its identifier."""
        try:
            event = self._store.store.eventWithIdentifier_(event_id)
            if not event:
                return False

            success, error = self._store.store.removeEvent_span_error_(
                event, EventKit.EKSpanThisEvent, None
            )
            return bool(success)
        except Exception:
            return False
