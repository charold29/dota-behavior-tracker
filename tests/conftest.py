from datetime import datetime, timezone
from pathlib import Path

import pytest

from dota_behavior_tracker.application.ports import ConductFile
from dota_behavior_tracker.domain.history import HistoryEntry

SAMPLE = Path(__file__).parent / "resources" / "latest_conduct_sample.txt"
SAMPLE_TEXT = SAMPLE.read_text(encoding="utf-8")
NOW = datetime(2026, 10, 24, 13, 0, tzinfo=timezone.utc)


# ---------------------------------------------- in-memory port fakes ---

class InMemoryHistory:
    """HistoryRepository kept in a list."""

    def __init__(self):
        self.entries: list[HistoryEntry] = []

    def read(self) -> list[HistoryEntry]:
        return list(self.entries)

    def append(self, entry: HistoryEntry) -> None:
        self.entries.append(entry)


class FakeSource:
    """ConductSource that returns a fixed text (or nothing)."""

    def __init__(self, text: str | None):
        self.text = text

    def latest(self) -> ConductFile | None:
        return None if self.text is None else ConductFile(location="fake", text=self.text)


@pytest.fixture
def history() -> InMemoryHistory:
    return InMemoryHistory()


@pytest.fixture
def sample_source() -> FakeSource:
    return FakeSource(SAMPLE_TEXT)
