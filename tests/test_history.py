from datetime import datetime, timezone

from conftest import NOW, SAMPLE_TEXT
from dota_behavior_tracker.domain.history import HistoryEntry, Source
from dota_behavior_tracker.domain.summary import ConductSummary


def test_from_summary_copies_the_score_fields():
    entry = HistoryEntry.from_summary(ConductSummary.from_text(SAMPLE_TEXT), recorded_at=NOW)

    assert entry.recorded_at == NOW
    assert entry.summary_date == datetime(2026, 5, 29, 0, 19, 23, tzinfo=timezone.utc)
    assert entry.behavior_score == 7843
    assert entry.previous_score == 7738
    assert entry.rating == "Good"
    assert entry.source is Source.FILE
    assert entry.seq_num == 8759
    assert entry.data["commend_count"] == 8
