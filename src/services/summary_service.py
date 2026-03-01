"""Weekly/N-day summary service.

Single Responsibility: Aggregates events and reminders, formats output.
Dependency Inversion: Depends on CalendarService and ReminderService abstractions.
"""

import datetime
from typing import Optional

from src.services.calendar_service import CalendarService
from src.services.reminder_service import ReminderService

PRIORITY_LABELS = {1: "high", 5: "medium", 9: "low"}


class SummaryService:
    """Aggregates calendar events and reminders into a unified summary."""

    def __init__(
        self,
        calendar_service: CalendarService,
        reminder_service: ReminderService,
    ) -> None:
        self._calendar = calendar_service
        self._reminders = reminder_service

    def generate(
        self,
        days: int = 7,
        fmt: str = "ascii",
        start_date: Optional[str] = None,
    ) -> str | dict:
        """Generate a summary for the next N days.

        Args:
            days: Number of days to cover (default 7). Max 365.
            fmt: Output format - 'ascii', 'markdown', or 'json'.
            start_date: Start date ISO 8601 (defaults to today).

        Returns:
            Formatted string (ascii/markdown) or dict (json).
        """
        days = min(max(1, days), 365)  # Prevent DoS from large values

        if start_date:
            start_dt = datetime.datetime.fromisoformat(start_date)
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=datetime.timezone.utc)
        else:
            start_dt = datetime.datetime.now(datetime.timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        end_dt = start_dt + datetime.timedelta(days=days)

        # Fetch all events and reminders in the range
        events = self._calendar.list_events(
            start_dt.isoformat(), end_dt.isoformat()
        )
        reminders = self._reminders.list_reminders(
            include_completed=False,
        )

        # Build per-day buckets
        day_data = self._bucket_by_day(start_dt, days, events, reminders)

        if fmt == "json":
            return self._format_json(start_dt, end_dt, day_data)
        elif fmt == "markdown":
            return self._format_markdown(start_dt, end_dt, day_data)
        else:
            return self._format_ascii(start_dt, end_dt, day_data)

    # ------------------------------------------------------------------
    # Bucketing
    # ------------------------------------------------------------------

    def _bucket_by_day(
        self,
        start_dt: datetime.datetime,
        days: int,
        events: list[dict],
        reminders: list[dict],
    ) -> list[dict]:
        """Organize events and reminders into per-day buckets."""
        buckets: list[dict] = []

        for i in range(days):
            day = start_dt + datetime.timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")

            all_day_events: list[dict] = []
            timed_events: list[dict] = []
            day_reminders: list[dict] = []

            # Classify events
            for ev in events:
                ev_start = ev.get("start", "")
                if not ev_start.startswith(day_str):
                    continue
                if ev.get("is_all_day"):
                    all_day_events.append(ev)
                else:
                    timed_events.append(ev)

            # Filter reminders due on this day (or no due date - show on first day)
            for rem in reminders:
                due = rem.get("due_date")
                if due and due == day_str:
                    day_reminders.append(rem)

            buckets.append({
                "date": day_str,
                "weekday": day.strftime("%a"),
                "day": day.strftime("%d"),
                "month": day.strftime("%b"),
                "all_day_events": all_day_events,
                "timed_events": timed_events,
                "reminders": day_reminders,
            })

        return buckets

    # ------------------------------------------------------------------
    # ASCII formatter
    # ------------------------------------------------------------------

    def _format_ascii(
        self,
        start_dt: datetime.datetime,
        end_dt: datetime.datetime,
        day_data: list[dict],
    ) -> str:
        days_count = len(day_data)
        title = "DAILY SUMMARY" if days_count == 1 else "WEEKLY SUMMARY"
        width = 54
        border = "=" * width
        start_label = start_dt.strftime("%d %b")
        end_label = (end_dt - datetime.timedelta(days=1)).strftime("%d %b %Y")

        lines: list[str] = []
        lines.append(border)
        if days_count == 1:
            lines.append(f"  {title}  |  {start_label} {start_dt.strftime('%Y')}".center(width))
        else:
            lines.append(f"  {title}  |  {start_label} - {end_label}".center(width))
        lines.append(border)

        total_events = 0
        total_reminders = 0

        for bucket in day_data:
            has_content = (
                bucket["all_day_events"]
                or bucket["timed_events"]
                or bucket["reminders"]
            )

            lines.append("")
            day_header = (
                f"-- {bucket['weekday']}, {bucket['day']} {bucket['month']} "
            )
            lines.append(day_header + "-" * (width - len(day_header)))

            if not has_content:
                lines.append("  No events or reminders.")
                continue

            # All-day events
            if bucket["all_day_events"]:
                lines.append("  ALL-DAY")
                for ev in bucket["all_day_events"]:
                    cal = ev.get("calendar", "")
                    lines.append(f"  * {ev['title']}  [{cal}]")
                    if ev.get("location"):
                        lines.append(f"    @ {ev['location']}")
                total_events += len(bucket["all_day_events"])

            # Timed events
            if bucket["timed_events"]:
                if bucket["all_day_events"]:
                    lines.append("")
                lines.append("  EVENTS")
                for ev in bucket["timed_events"]:
                    t_start = self._time_str(ev.get("start", ""))
                    t_end = self._time_str(ev.get("end", ""))
                    cal = ev.get("calendar", "")
                    lines.append(
                        f"  {t_start} - {t_end}  {ev['title']}"
                    )
                    details: list[str] = []
                    if ev.get("location"):
                        details.append(f"@ {ev['location']}")
                    details.append(f"[{cal}]")
                    lines.append(f"                 {' '.join(details)}")
                total_events += len(bucket["timed_events"])

            # Reminders
            if bucket["reminders"]:
                if bucket["timed_events"] or bucket["all_day_events"]:
                    lines.append("")
                lines.append("  REMINDERS")
                for rem in bucket["reminders"]:
                    title = rem.get("title", "")
                    priority = rem.get("priority", 0)
                    p_label = PRIORITY_LABELS.get(priority, "")
                    suffix = f"  ({p_label})" if p_label else ""
                    lines.append(f"  [ ] {title}{suffix}")
                total_reminders += len(bucket["reminders"])

        # Footer
        lines.append("")
        lines.append(border)
        lines.append(
            f"  TOTALS: {total_events} events | "
            f"{total_reminders} reminders pending"
        )
        lines.append(border)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Markdown formatter
    # ------------------------------------------------------------------

    def _format_markdown(
        self,
        start_dt: datetime.datetime,
        end_dt: datetime.datetime,
        day_data: list[dict],
    ) -> str:
        days_count = len(day_data)
        title = "Daily Summary" if days_count == 1 else "Weekly Summary"
        start_label = start_dt.strftime("%d %b")
        end_label = (end_dt - datetime.timedelta(days=1)).strftime("%d %b %Y")

        lines: list[str] = []
        if days_count == 1:
            lines.append(f"# {title}: {start_label} {start_dt.strftime('%Y')}")
        else:
            lines.append(f"# {title}: {start_label} - {end_label}")
        lines.append("")

        total_events = 0
        total_reminders = 0

        for bucket in day_data:
            has_content = (
                bucket["all_day_events"]
                or bucket["timed_events"]
                or bucket["reminders"]
            )

            lines.append(
                f"## {bucket['weekday']}, {bucket['day']} {bucket['month']}"
            )
            lines.append("")

            if not has_content:
                lines.append("_No events or reminders._")
                lines.append("")
                continue

            # All-day events
            if bucket["all_day_events"]:
                lines.append("### All-Day")
                for ev in bucket["all_day_events"]:
                    cal = ev.get("calendar", "")
                    loc = f" - {ev['location']}" if ev.get("location") else ""
                    lines.append(f"- **{ev['title']}**{loc} `{cal}`")
                lines.append("")
                total_events += len(bucket["all_day_events"])

            # Timed events
            if bucket["timed_events"]:
                lines.append("### Events")
                for ev in bucket["timed_events"]:
                    t_start = self._time_str(ev.get("start", ""))
                    t_end = self._time_str(ev.get("end", ""))
                    cal = ev.get("calendar", "")
                    loc = f" - {ev['location']}" if ev.get("location") else ""
                    lines.append(
                        f"- `{t_start}-{t_end}` **{ev['title']}**{loc} `{cal}`"
                    )
                lines.append("")
                total_events += len(bucket["timed_events"])

            # Reminders
            if bucket["reminders"]:
                lines.append("### Reminders")
                for rem in bucket["reminders"]:
                    title = rem.get("title", "")
                    priority = rem.get("priority", 0)
                    p_label = PRIORITY_LABELS.get(priority, "")
                    suffix = f" *({p_label})*" if p_label else ""
                    lines.append(f"- [ ] {title}{suffix}")
                lines.append("")
                total_reminders += len(bucket["reminders"])

        lines.append("---")
        lines.append(
            f"**Totals:** {total_events} events | "
            f"{total_reminders} reminders pending"
        )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # JSON formatter
    # ------------------------------------------------------------------

    def _format_json(
        self,
        start_dt: datetime.datetime,
        end_dt: datetime.datetime,
        day_data: list[dict],
    ) -> dict:
        total_events = sum(
            len(d["all_day_events"]) + len(d["timed_events"])
            for d in day_data
        )
        total_reminders = sum(len(d["reminders"]) for d in day_data)

        return {
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "days": day_data,
            "totals": {
                "events": total_events,
                "reminders": total_reminders,
            },
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _time_str(iso: str) -> str:
        """Extract HH:MM from an ISO 8601 datetime string."""
        try:
            dt = datetime.datetime.fromisoformat(iso)
            return dt.strftime("%H:%M")
        except (ValueError, TypeError):
            return "??:??"
