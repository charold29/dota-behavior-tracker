"""
Adapter: implements the HistoryRepository port with a CSV file.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from ..domain.history import HistoryEntry, Source

COLUMNS = ["recorded_at", "summary_date", "behavior_score", "previous_score",
           "rating", "source", "seq_num", "data"]


class CsvHistoryRepository:
    """The file (and its folder) is created on the first write."""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def read(self) -> list[HistoryEntry]:
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8-sig", newline="") as f:
            return [row_to_entry(row) for row in csv.DictReader(f)]

    def append(self, entry: HistoryEntry) -> None:
        new = not self.path.exists()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            if new:
                w.writeheader()
            w.writerow(entry_to_row(entry))


def entry_to_row(entry: HistoryEntry) -> dict[str, str]:
    return {
        "recorded_at": entry.recorded_at.isoformat(timespec="seconds"),
        "summary_date": entry.summary_date.isoformat(timespec="seconds"),
        "behavior_score": str(entry.behavior_score),
        "previous_score": _str_or_empty(entry.previous_score),
        "rating": entry.rating,
        "source": entry.source.value,
        "seq_num": _str_or_empty(entry.seq_num),
        "data": json.dumps(entry.data, ensure_ascii=False, default=str) if entry.data else "",
    }


def row_to_entry(row: dict[str, str]) -> HistoryEntry:
    return HistoryEntry(
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        summary_date=datetime.fromisoformat(row["summary_date"] or row["recorded_at"]),
        behavior_score=int(row["behavior_score"]),
        source=Source(row["source"]),
        previous_score=_int_or_none(row["previous_score"]),
        rating=row["rating"],
        seq_num=_int_or_none(row["seq_num"]),
        data=json.loads(row["data"]) if row["data"] else {},
    )


def _str_or_empty(value: int | None) -> str:
    return "" if value is None else str(value)


def _int_or_none(text: str) -> int | None:
    return int(text) if text else None
