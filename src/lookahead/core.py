"""Build a multi-week lookahead from a schedule CSV."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass(frozen=True)
class Activity:
    """One scheduled activity."""

    name: str
    trade: str
    location: str
    start: date
    finish: date


def load(path: str | Path) -> list[Activity]:
    """Read activities from CSV columns activity,trade,location,start,finish."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for col in ("activity", "trade", "location", "start", "finish"):
            if col not in (reader.fieldnames or []):
                raise ValueError(f"missing column: {col}")
        out = []
        for n, row in enumerate(reader, start=2):
            try:
                start = date.fromisoformat(row["start"].strip())
                finish = date.fromisoformat(row["finish"].strip())
            except ValueError as exc:
                raise ValueError(f"line {n}: bad date ({exc})") from exc
            if finish < start:
                raise ValueError(f"line {n}: finish is before start")
            out.append(Activity(row["activity"].strip(), row["trade"].strip(),
                                row["location"].strip(), start, finish))
    return out


def monday(day: date) -> date:
    """The Monday of the week containing day."""
    return day - timedelta(days=day.weekday())


def build(acts: list[Activity], from_date: date, weeks: int = 3) -> list[tuple[date, list[tuple[Activity, str]]]]:
    """Group activities by week. Each entry carries a status: starts, finishes, starts and finishes, or continues."""
    if weeks < 1:
        raise ValueError("weeks must be at least 1")
    first = monday(from_date)
    result = []
    for w in range(weeks):
        week_start = first + timedelta(weeks=w)
        week_end = week_start + timedelta(days=6)
        rows = []
        for a in acts:
            if a.start > week_end or a.finish < week_start:
                continue
            begins = week_start <= a.start <= week_end
            ends = week_start <= a.finish <= week_end
            status = ("starts and finishes" if begins and ends else
                      "starts" if begins else "finishes" if ends else "continues")
            rows.append((a, status))
        rows.sort(key=lambda r: (r[0].trade, r[0].start, r[0].name))
        result.append((week_start, rows))
    return result


def render(weeks: list[tuple[date, list[tuple[Activity, str]]]]) -> str:
    """Format the lookahead as plain text."""
    lines = []
    for week_start, rows in weeks:
        lines.append(f"Week of {week_start.isoformat()} ({len(rows)} activities)")
        if not rows:
            lines.append("  nothing scheduled")
        for a, status in rows:
            lines.append(f"  {a.trade:<16} {a.name:<26} {a.location:<12} {status}")
        lines.append("")
    return "\n".join(lines).rstrip()


def by_trade(weeks: list[tuple[date, list[tuple[Activity, str]]]]) -> dict[str, int]:
    """Count activity-weeks per trade across the lookahead window."""
    counts: dict[str, int] = {}
    for _, rows in weeks:
        for a, _ in rows:
            counts[a.trade] = counts.get(a.trade, 0) + 1
    return dict(sorted(counts.items()))
