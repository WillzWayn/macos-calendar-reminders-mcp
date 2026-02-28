"""Shared test fixtures with mock EventKit store."""

from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from src.eventkit.store import EventKitStore
from src.services.calendar_service import CalendarService
from src.services.reminder_service import ReminderService


class MockEventKitStore:
    """Mock EventKitStore that doesn't require macOS EventKit access.

    Use this in tests to avoid requiring actual calendar/reminder permissions.
    """

    def __init__(self) -> None:
        self._store = MagicMock()
        self._calendar_access_granted = True
        self._reminder_access_granted = True

    @property
    def store(self) -> MagicMock:
        return self._store

    @property
    def has_calendar_access(self) -> bool:
        return self._calendar_access_granted

    @property
    def has_reminder_access(self) -> bool:
        return self._reminder_access_granted

    def request_calendar_access(self) -> bool:
        return True

    def request_reminder_access(self) -> bool:
        return True

    def request_all_access(self) -> tuple[bool, bool]:
        return True, True

    def get_calendars(self, entity_type: int = 0) -> list:
        return []

    def get_calendar_by_name(
        self, name: str, entity_type: int = 0
    ) -> Optional[MagicMock]:
        return None

    def get_default_calendar(self) -> Optional[MagicMock]:
        return MagicMock()

    def get_default_reminder_list(self) -> Optional[MagicMock]:
        return MagicMock()

    def commit(self) -> bool:
        return True


@pytest.fixture
def mock_store() -> MockEventKitStore:
    """Provide a mock EventKit store for testing."""
    return MockEventKitStore()


@pytest.fixture
def calendar_service(mock_store: MockEventKitStore) -> CalendarService:
    """Provide a CalendarService backed by a mock store."""
    return CalendarService(mock_store)  # type: ignore[arg-type]


@pytest.fixture
def reminder_service(mock_store: MockEventKitStore) -> ReminderService:
    """Provide a ReminderService backed by a mock store."""
    return ReminderService(mock_store)  # type: ignore[arg-type]
