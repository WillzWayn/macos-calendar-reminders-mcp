# macOS Calendar & Reminders MCP Server

A Python-based [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that allows AI assistants (like Claude, Cursor, or IDEs) to interact with your macOS Calendar and Reminders.

Built with performance and security in mind using Apple's native `EventKit` framework via `PyObjC`.

## 🚀 Features

- **📅 Calendar Management**
  - List events within specific date ranges.
  - Create, update, and delete events.
  - Support for multiple calendars (iCloud, Google, etc. synced to macOS).
  - All-day event support.
- **✅ Reminders Management**
  - List active or completed reminders.
  - Create, update, and delete reminders.
  - Set priorities and due dates.
  - Mark reminders as completed.
- **🔒 Privacy First**
  - Runs locally on your machine.
  - Uses native macOS permissions for data access.
  - No third-party API keys required (uses your existing system accounts).

## 🛠️ Requirements

- **macOS**: 10.15 (Catalina) or newer.
- **Python**: 3.12 or newer.
- **Package Manager**: [uv](https://github.com/astral-sh/uv) recommended.

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/WillzWayn/macbook-reminders-calendar-mcp.git
   cd macbook-reminders-calendar-mcp
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

## ⚙️ Configuration

### Claude Desktop

Add the following to your `claude_desktop_config.json` (usually found in `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "macos-calendar-reminders": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/macbook-reminders-calendar-mcp",
        "run",
        "python",
        "-m",
        "src.server",
        "--stdio"
      ]
    }
  }
}
```

### OpenCode

Add the following to your `opencode.json` (usually found in `~/.config/opencode/opencode.json`):

```json
{
    "macos-calendar-reminders": {
      "type": "local",
      "command": [
        "uv",
        "run",
        "--directory",
        "/absolute/path/to/macbook-reminders-calendar-mcp",
        "python",
        "-m",
        "src.server",
        "--stdio"
      ],
      "enabled": true
  }
}
```

### Cursor / Other IDEs

Use the same configuration as above in your MCP settings, ensuring you provide the **absolute path** to the project directory.

## 🔑 Permissions

When you first run the server, macOS will prompt you for permission to access your **Calendar** and **Reminders**. You must grant these for the server to function.

If you miss the prompt, you can enable it manually in:
`System Settings > Privacy & Security > Calendar / Reminders`.

## 🧪 Development

### Running tests
```bash
uv run pytest
```

### Linting & Formatting
```bash
uv run ruff check src/
uv run ruff format src/
```

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.
