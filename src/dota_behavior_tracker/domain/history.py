"""
Domain: an entry in the behavior score history.

How entries are stored (CSV today) is the job of an adapter
(adapters/csv_history.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from .summary import ConductSummary


class Source(StrEnum):
    FILE = "file"      # read from Valve's latest_conduct file
    MANUAL = "manual"  # added by hand with the 'add' command


@dataclass(frozen=True)
class HistoryEntry:
    recorded_at: datetime                # when it was added to the history
    summary_date: datetime               # when Valve generated the summary (or the date given by hand)
    behavior_score: int
    source: Source
    previous_score: int | None = None
    rating: str = ""
    seq_num: int | None = None
    data: dict[str, object] = field(default_factory=dict)  # raw fields from Valve's file

    @classmethod
    def from_summary(cls, summary: ConductSummary, recorded_at: datetime) -> HistoryEntry:
        return cls(
            recorded_at=recorded_at,
            summary_date=summary.date,
            behavior_score=summary.raw_behavior_score,
            source=Source.FILE,
            previous_score=summary.old_raw_behavior_score,
            rating=summary.rating_label,
            seq_num=summary.seq_num,
            data=summary.raw_fields(),
        )
