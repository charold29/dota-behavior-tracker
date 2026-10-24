"""
Infrastructure: the behavior score history, stored as a CSV file.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from .summary import ConductSummary

COLUMNS = ["recorded_at", "summary_date", "behavior_score", "previous_score",
           "rating", "source", "seq_num", "data"]


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
    def from_summary(cls, summary: ConductSummary, recorded_at: datetime) -> "HistoryEntry":
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

    # -------------------------------------------------------- CSV rows --

    def to_row(self) -> dict[str, str]:
        return {
            "recorded_at": self.recorded_at.isoformat(timespec="seconds"),
            "summary_date": self.summary_date.isoformat(timespec="seconds"),
            "behavior_score": str(self.behavior_score),
            "previous_score": _str_or_empty(self.previous_score),
            "rating": self.rating,
            "source": self.source.value,
            "seq_num": _str_or_empty(self.seq_num),
            "data": json.dumps(self.data, ensure_ascii=False, default=str) if self.data else "",
        }

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "HistoryEntry":
        return cls(
            recorded_at=datetime.fromisoformat(row["recorded_at"]),
            summary_date=datetime.fromisoformat(row["summary_date"] or row["recorded_at"]),
            behavior_score=int(row["behavior_score"]),
            source=Source(row["source"]),
            previous_score=_int_or_none(row["previous_score"]),
            rating=row["rating"],
            seq_num=_int_or_none(row["seq_num"]),
            data=json.loads(row["data"]) if row["data"] else {},
        )


class HistoryStore:
    """Reads and appends history entries. The file (and its folder) is created on the first write."""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def read(self) -> list[HistoryEntry]:
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8-sig", newline="") as f:
            return [HistoryEntry.from_row(row) for row in csv.DictReader(f)]

    def append(self, entry: HistoryEntry) -> None:
        new = not self.path.exists()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            if new:
                w.writeheader()
            w.writerow(entry.to_row())

    def has_seq_num(self, seq_num: int) -> bool:
        return any(e.source is Source.FILE and e.seq_num == seq_num for e in self.read())


def _str_or_empty(value: int | None) -> str:
    return "" if value is None else str(value)


def _int_or_none(text: str) -> int | None:
    return int(text) if text else None
