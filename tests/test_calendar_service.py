"""Tests for CalendarService."""

from unittest.mock import MagicMock

from tests.conftest import MockEventKitStore
from src.services.calendar_service import CalendarService


def test_list_calendars_empty(
    calendar_service: CalendarService,
    mock_store: MockEventKitStore,
) -> None:
    """list_calendars returns empty list when no calendars exist."""
    result = calendar_service.list_calendars()
    assert result == []


def test_list_calendars_returns_names(
    calendar_service: CalendarService,
    mock_store: MockEventKitStore,
) -> None:
    """list_calendars returns calendar info dicts."""
    mock_cal = MagicMock()
    mock_cal.title.return_value = "Work"
    mock_cal.type.return_value = 1
    mock_cal.isSubscribed.return_value = False
    mock_store.get_calendars = lambda entity_type=0: [mock_cal]

    result = calendar_service.list_calendars()
    assert len(result) == 1
    assert result[0]["name"] == "Work"


def test_list_events_empty_range(
    calendar_service: CalendarService,
    mock_store: MockEventKitStore,
) -> None:
    """list_events returns empty list when no events match."""
    mock_store._store.predicateForEventsWithStartDate_endDate_calendars_.return_value = (
        MagicMock()
    )
    mock_store._store.eventsMatchingPredicate_.return_value = None

    result = calendar_service.list_events(
        "2026-03-01T00:00:00Z", "2026-03-07T23:59:59Z"
    )
    assert result == []


def test_list_events_unknown_calendar(
    calendar_service: CalendarService,
    mock_store: MockEventKitStore,
) -> None:
    """list_events returns empty list when calendar name doesn't exist."""
    result = calendar_service.list_events(
        "2026-03-01", "2026-03-07", calendar_name="Nonexistent"
    )
    assert result == []


def test_get_event_not_found(
    calendar_service: CalendarService,
    mock_store: MockEventKitStore,
) -> None:
    """get_event returns None for unknown event ID."""
    mock_store._store.eventWithIdentifier_.return_value = None
    result = calendar_service.get_event("fake-id")
    assert result is None


def test_create_event_missing_calendar(
    calendar_service: CalendarService,
    mock_store: MockEventKitStore,
) -> None:
    """create_event returns error when target calendar doesn't exist."""
    result = calendar_service.create_event({
        "title": "Test",
        "start": "2026-03-01T10:00:00Z",
        "end": "2026-03-01T11:00:00Z",
        "calendar_name": "Nonexistent",
    })
    assert "error" in result


def test_delete_event_not_found(
    calendar_service: CalendarService,
    mock_store: MockEventKitStore,
) -> None:
    """delete_event returns False when event doesn't exist."""
    mock_store._store.eventWithIdentifier_.return_value = None
    result = calendar_service.delete_event("fake-id")
    assert result is False
