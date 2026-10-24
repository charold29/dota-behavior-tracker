"""
Application: what the app can do, independent of how it's invoked (CLI, a
scheduled task...). Only knows the ports, never a concrete file or library.
Doesn't print anything; it returns results or raises.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from ..domain.history import HistoryEntry, Source
from ..domain.score import validate_score
from ..domain.summary import ConductSummary
from .ports import ConductSource, HistoryRepository


class ConductFileNotFoundError(FileNotFoundError):
    """There is no conduct summary to read."""


@dataclass(frozen=True)
class RecordResult:
    summary: ConductSummary
    recorded: bool  # False when the summary was already in the history


def record_summary(history: HistoryRepository, source: ConductSource,
                   now: datetime | None = None) -> RecordResult:
    """Adds the latest summary to the history, unless it's already there."""
    conduct_file = source.latest()
    if conduct_file is None:
        raise ConductFileNotFoundError("Couldn't find latest_conduct_*.txt.")

    summary = ConductSummary.from_text(conduct_file.text)
    if _already_recorded(history, summary.seq_num):
        return RecordResult(summary, recorded=False)

    history.append(HistoryEntry.from_summary(summary, recorded_at=now or _now()))
    return RecordResult(summary, recorded=True)


def add_manual_score(history: HistoryRepository, score: int, on: date | None = None,
                     now: datetime | None = None) -> HistoryEntry:
    """Adds a score by hand, dated `on` (today by default). Raises InvalidScoreError if out of range."""
    now = now or _now()
    entry = HistoryEntry(
        recorded_at=now,
        summary_date=datetime.combine(on or now.date(), time()).astimezone(),
        behavior_score=validate_score(score),
        source=Source.MANUAL,
    )
    history.append(entry)
    return entry


def score_timeline(history: HistoryRepository) -> list[HistoryEntry]:
    """Every history entry, sorted by summary date."""
    return sorted(history.read(), key=lambda e: e.summary_date)


def _already_recorded(history: HistoryRepository, seq_num: int) -> bool:
    return any(e.source is Source.FILE and e.seq_num == seq_num for e in history.read())


def _now() -> datetime:
    return datetime.now().astimezone()
