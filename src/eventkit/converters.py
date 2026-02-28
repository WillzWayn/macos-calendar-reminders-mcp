"""Converters between Python types and EventKit/Foundation types."""

import datetime
from typing import Optional

from Foundation import NSDate

# Apple epoch: January 1, 2001 00:00:00 UTC
APPLE_EPOCH = datetime.datetime(2001, 1, 1, tzinfo=datetime.timezone.utc)


def datetime_to_nsdate(dt: datetime.datetime) -> NSDate:
    """Convert a Python datetime to an NSDate.

    Args:
        dt: A timezone-aware or naive datetime. Naive datetimes are assumed UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    delta = dt - APPLE_EPOCH
    return NSDate.dateWithTimeIntervalSinceReferenceDate_(delta.total_seconds())


def nsdate_to_datetime(ns_date: NSDate) -> datetime.datetime:
    """Convert an NSDate to a timezone-aware Python datetime (UTC)."""
    ref_seconds = ns_date.timeIntervalSinceReferenceDate()
    return APPLE_EPOCH + datetime.timedelta(seconds=ref_seconds)


def nsdate_to_local_string(ns_date: NSDate, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Convert an NSDate to a local-time formatted string."""
    dt = nsdate_to_datetime(ns_date).astimezone()
    return dt.strftime(fmt)


def parse_datetime(value: str) -> datetime.datetime:
    """Parse an ISO 8601 datetime string into a timezone-aware datetime.

    Supports formats:
        - 2026-03-01T10:00:00
        - 2026-03-01T10:00:00Z
        - 2026-03-01T10:00:00+03:00
        - 2026-03-01 (date only, midnight UTC)
    """
    value = value.strip()
    if len(value) == 10:
        # Date only
        dt = datetime.datetime.strptime(value, "%Y-%m-%d")
        return dt.replace(tzinfo=datetime.timezone.utc)

    dt = datetime.datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def event_to_dict(event: object) -> dict:
    """Convert an EKEvent to a plain dictionary.

    Args:
        event: An EKEvent instance from EventKit.
    """
    start_dt = nsdate_to_datetime(event.startDate())  # type: ignore[arg-type]
    end_dt = nsdate_to_datetime(event.endDate())  # type: ignore[arg-type]

    result: dict = {
        "event_id": event.eventIdentifier(),  # type: ignore[union-attr]
        "title": event.title() or "(No title)",  # type: ignore[union-attr]
        "start": start_dt.astimezone().isoformat(),
        "end": end_dt.astimezone().isoformat(),
        "is_all_day": bool(event.isAllDay()),  # type: ignore[union-attr]
        "calendar": event.calendar().title() if event.calendar() else None,  # type: ignore[union-attr]
    }

    location = event.location()  # type: ignore[union-attr]
    if location:
        result["location"] = str(location)

    notes = event.notes()  # type: ignore[union-attr]
    if notes:
        result["notes"] = str(notes)

    url = event.URL()  # type: ignore[union-attr]
    if url:
        result["url"] = str(url)

    return result


def reminder_to_dict(reminder: object) -> dict:
    """Convert an EKReminder to a plain dictionary.

    Args:
        reminder: An EKReminder instance from EventKit.
    """
    result: dict = {
        "reminder_id": reminder.calendarItemIdentifier(),  # type: ignore[union-attr]
        "title": reminder.title() or "(No title)",  # type: ignore[union-attr]
        "completed": bool(reminder.isCompleted()),  # type: ignore[union-attr]
        "list": reminder.calendar().title() if reminder.calendar() else None,  # type: ignore[union-attr]
        "priority": int(reminder.priority()),  # type: ignore[union-attr]
    }

    due_date = reminder.dueDateComponents()  # type: ignore[union-attr]
    if due_date:
        year = due_date.year()
        month = due_date.month()
        day = due_date.day()
        if year > 0 and month > 0 and day > 0:
            result["due_date"] = f"{year:04d}-{month:02d}-{day:02d}"

    completion_date = reminder.completionDate()  # type: ignore[union-attr]
    if completion_date:
        result["completion_date"] = nsdate_to_datetime(completion_date).astimezone().isoformat()

    notes = reminder.notes()  # type: ignore[union-attr]
    if notes:
        result["notes"] = str(notes)

    return result
