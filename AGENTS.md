# AGENTS.md - macOS Calendar & Reminders MCP Server

## Project Overview

Python MCP server for macOS Calendar and Reminders using Apple's EventKit framework via PyObjC. Follows SOLID principles with a clean service layer abstracting EventKit from MCP tool handlers.

## Development Environment

- **Python**: 3.12+
- **Package Manager**: uv
- **Build Backend**: hatchling
- **MCP SDK**: `mcp[cli]>=1.0.0` (FastMCP)
- **EventKit Bridge**: `pyobjc-framework-EventKit`
- **Data Validation**: Pydantic v2 + pydantic-settings
- **Platform**: macOS only (EventKit is an Apple framework)

## Build, Lint, and Test Commands

### Dependency Management

```bash
uv sync                    # Install all dependencies
uv sync --refresh          # Refresh lock file and reinstall
uv add <package>           # Add a runtime dependency
uv add --dev <package>     # Add a dev dependency
```

### Running the MCP Server

```bash
uv run python -m src.server            # HTTP transport (streamable-http)
uv run python -m src.server --stdio    # stdio transport (for Claude Desktop/Cursor/OpenCode)
```

### Code Quality

```bash
uv run ruff check src/                 # Lint
uv run ruff format src/                # Format
uv run mypy src/                       # Type check
```

### Testing

```bash
uv run pytest                                    # Run all tests
uv run pytest tests/test_calendar_service.py     # Run a single test file
uv run pytest tests/test_calendar_service.py::test_list_events  # Run a single test
uv run pytest -k "test_reminder"                 # Run tests matching a pattern
uv run pytest -v                                 # Verbose output
uv run pytest --tb=short                         # Short tracebacks
```

### MCP Development Tools

```bash
uv run mcp dev src/server.py                           # Dev mode with inspector
npx -y @modelcontextprotocol/inspector                 # Launch MCP Inspector
```

## Project Structure

```
src/
├── __init__.py              # Package root; re-exports key symbols
├── __main__.py              # Entry point: python -m src
├── config.py                # pydantic-settings Settings class
├── server.py                # FastMCP server + tool registrations (thin handlers)
├── models/
│   ├── __init__.py          # Re-exports all models with __all__
│   ├── event.py             # Calendar event Pydantic models / DTOs
│   └── reminder.py          # Reminder Pydantic models / DTOs
├── services/
│   ├── __init__.py          # Re-exports services with __all__
│   ├── protocols.py         # Abstract interfaces (CalendarServiceProtocol, ReminderServiceProtocol)
│   ├── calendar_service.py  # Concrete EventKit calendar implementation
│   └── reminder_service.py  # Concrete EventKit reminder implementation
└── eventkit/
    ├── __init__.py
    ├── store.py             # EKEventStore wrapper (permission handling, lifecycle)
    └── converters.py        # NSDate <-> datetime, EKEvent <-> Pydantic model converters
tests/
├── conftest.py              # Shared fixtures, mock EventKit store
├── test_calendar_service.py
└── test_reminder_service.py
```

## SOLID Principles

- **Single Responsibility**: Each class has one purpose - `CalendarService` handles events, `ReminderService` handles reminders, `EventKitStore` manages the store lifecycle, `server.py` only registers tools.
- **Open/Closed**: New calendar backends can be added by implementing the protocol without modifying existing code.
- **Liskov Substitution**: Service implementations are interchangeable via their protocol interfaces.
- **Interface Segregation**: Separate protocols for calendar vs reminder operations. MCP tools only depend on the service they need.
- **Dependency Inversion**: Tool handlers depend on abstract protocols, not concrete EventKit classes. Concrete services are injected via the lifespan context.

## Code Style Guidelines

### Imports

- Group in order: stdlib, third-party, local (separated by blank lines)
- Use absolute imports from package root: `from src.services import CalendarService`
- Use `__init__.py` with explicit `__all__` for clean public APIs
- Use `collections.abc` for abstract types: `from collections.abc import AsyncIterator`

### Type Hints

- Always annotate function parameters and return values
- Use `Optional[X]` from typing for nullable types
- Use Pydantic models for structured input/output
- Use type aliases for complex types

### Naming Conventions

- **Classes**: `PascalCase` (`CalendarService`, `EventKitStore`)
- **Functions/methods**: `snake_case` (`list_events`, `create_reminder`)
- **Variables**: `snake_case` (`event_id`, `calendar_list`)
- **Constants**: `UPPER_SNAKE_CASE` (`DEFAULT_CALENDAR_NAME`)
- **Private members**: Leading underscore (`_store`, `_fetch_calendars`)
- **Protocols/ABCs**: Suffix with `Protocol` (`CalendarServiceProtocol`)

### Error Handling

- MCP tool layer: return error dicts `{"error": "message"}`, never raise
- Service layer: return `None` or `bool` for soft failures, raise for critical errors
- EventKit layer: check `NSError` output parameters from PyObjC calls
- Use try/except around all EventKit operations

```python
@mcp.tool()
async def list_events(ctx: Context, calendar_name: Optional[str] = None) -> list[dict]:
    """List calendar events."""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        events = app_ctx.calendar_service.list_events(calendar_name)
        return [e.model_dump() for e in events]
    except Exception as e:
        return {"error": str(e)}
```

### Pydantic Models

- Use `BaseModel` for all DTOs
- Use `Field` for validation constraints and descriptions
- Use `Enum` for fixed choices (e.g., `ReminderPriority`, `RecurrenceFrequency`)
- Implement `to_eventkit()` / `from_eventkit()` class methods for conversion

### MCP Server Patterns

- Use `@mcp.tool()` decorator for all tools
- First parameter is always `ctx: Context` for dependency access
- Tool handlers must be thin: delegate to service layer, convert types, return results
- Do NOT pass `Context` into the service layer - extract what you need
- Return `dict` or `list[dict]` (JSON-serializable)
- Use `@asynccontextmanager` lifespan for DI composition root

### EventKit / PyObjC Patterns

- Access properties via methods: `event.title()` not `event.title`
- Set properties via setter: `event.setTitle_("value")`
- Create ObjC objects with: `ClassName.alloc().init()`
- Request permissions separately for `EKEntityTypeEvent` and `EKEntityTypeReminder`
- Convert `NSDate` carefully (epoch is Jan 1, 2001, not 1970)
- Use `predicateForEventsWithStartDate_endDate_calendars_()` for event queries
- Reminders use async fetch: `fetchRemindersMatchingPredicate_completion_()`

### Formatting

- Follow PEP 8
- 4 spaces indentation
- Max line length: 100 characters (soft limit)
- Use ruff for formatting and linting
- Blank lines to separate logical sections sparingly

### Comments and Docstrings

- Code should be self-explanatory; avoid unnecessary comments
- Use Google-style docstrings for public APIs
- Tool docstrings are shown to the LLM - make them clear and actionable

## macOS Permissions

The terminal app running this server (Terminal.app, iTerm, etc.) must have Calendar and Reminders access granted in **System Preferences > Privacy & Security**. The first run will trigger a macOS permission prompt.
