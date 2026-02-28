"""Tests for ReminderService."""

from unittest.mock import MagicMock

from tests.conftest import MockEventKitStore
from src.services.reminder_service import ReminderService


def test_list_reminder_lists_empty(
    reminder_service: ReminderService,
    mock_store: MockEventKitStore,
) -> None:
    """list_reminder_lists returns empty list when no lists exist."""
    result = reminder_service.list_reminder_lists()
    assert result == []


def test_list_reminder_lists_returns_names(
    reminder_service: ReminderService,
    mock_store: MockEventKitStore,
) -> None:
    """list_reminder_lists returns reminder list info dicts."""
    mock_list = MagicMock()
    mock_list.title.return_value = "Groceries"
    mock_list.isSubscribed.return_value = False
    mock_store.get_calendars = lambda entity_type=0: [mock_list]

    result = reminder_service.list_reminder_lists()
    assert len(result) == 1
    assert result[0]["name"] == "Groceries"


def test_list_reminders_unknown_list(
    reminder_service: ReminderService,
    mock_store: MockEventKitStore,
) -> None:
    """list_reminders returns empty when list name doesn't exist."""
    result = reminder_service.list_reminders(list_name="Nonexistent")
    assert result == []


def test_create_reminder_missing_list(
    reminder_service: ReminderService,
    mock_store: MockEventKitStore,
) -> None:
    """create_reminder returns error when target list doesn't exist."""
    mock_store._store.reminderWithEventStore_ = MagicMock
    result = reminder_service.create_reminder({
        "title": "Test Reminder",
        "list_name": "Nonexistent",
    })
    assert "error" in result


def test_complete_reminder_not_found(
    reminder_service: ReminderService,
    mock_store: MockEventKitStore,
) -> None:
    """complete_reminder returns False when reminder doesn't exist."""
    # Mock fetch to return empty list
    mock_store._store.fetchRemindersMatchingPredicate_completion_ = (
        lambda pred, cb: cb(None)
    )
    mock_store._store.predicateForRemindersInCalendars_.return_value = MagicMock()

    result = reminder_service.complete_reminder("fake-id")
    assert result is False


def test_delete_reminder_not_found(
    reminder_service: ReminderService,
    mock_store: MockEventKitStore,
) -> None:
    """delete_reminder returns False when reminder doesn't exist."""
    mock_store._store.fetchRemindersMatchingPredicate_completion_ = (
        lambda pred, cb: cb(None)
    )
    mock_store._store.predicateForRemindersInCalendars_.return_value = MagicMock()

    result = reminder_service.delete_reminder("fake-id")
    assert result is False
