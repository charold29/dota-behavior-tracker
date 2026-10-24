"""
Application: what the app can do, independent of how it's invoked (CLI, a
scheduled task...). Doesn't print anything; it returns results or raises.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path

from .history import HistoryEntry, HistoryStore, Source
from .summary import ConductSummary


class ConductFileNotFoundError(FileNotFoundError):
    """Dota 2's latest_conduct file couldn't be found."""


@dataclass(frozen=True)
class RecordResult:
    summary: ConductSummary
    recorded: bool  # False when the summary was already in the history


def record_summary(store: HistoryStore, conduct_file: Path | None,
                   now: datetime | None = None) -> RecordResult:
    """Adds the summary in conduct_file to the history, unless it's already there."""
    if conduct_file is None:
        raise ConductFileNotFoundError("Couldn't find latest_conduct_*.txt.")

    summary = ConductSummary.from_file(conduct_file)
    if store.has_seq_num(summary.seq_num):
        return RecordResult(summary, recorded=False)

    store.append(HistoryEntry.from_summary(summary, recorded_at=now or _now()))
    return RecordResult(summary, recorded=True)


def add_manual_score(store: HistoryStore, score: int, on: date | None = None,
                     now: datetime | None = None) -> HistoryEntry:
    """Adds a score by hand, dated `on` (today by default)."""
    now = now or _now()
    entry = HistoryEntry(
        recorded_at=now,
        summary_date=datetime.combine(on or now.date(), time()).astimezone(),
        behavior_score=score,
        source=Source.MANUAL,
    )
    store.append(entry)
    return entry


def score_timeline(store: HistoryStore) -> list[tuple[datetime, int]]:
    """(date, score) pairs sorted by date."""
    return sorted((e.summary_date, e.behavior_score) for e in store.read())


def _now() -> datetime:
    return datetime.now().astimezone()
