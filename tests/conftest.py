from datetime import datetime, timezone
from pathlib import Path

import pytest

from dota_behavior_tracker.history import HistoryStore

SAMPLE = Path(__file__).parent / "resources" / "latest_conduct_sample.txt"
NOW = datetime(2026, 10, 24, 13, 0, tzinfo=timezone.utc)


@pytest.fixture
def store(tmp_path) -> HistoryStore:
    return HistoryStore(tmp_path / "data" / "behavior_history.csv")
