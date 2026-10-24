from datetime import datetime, timedelta, timezone

import pytest

from conftest import NOW
from dota_behavior_tracker.adapters.chart import last_value_label, plot_timeline, rating_spans
from dota_behavior_tracker.domain.history import HistoryEntry, Source

START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _entry(day: int, score: int, rating: str = "", source: Source = Source.FILE) -> HistoryEntry:
    return HistoryEntry(recorded_at=NOW, summary_date=START + timedelta(days=day),
                        behavior_score=score, source=source, rating=rating)


def test_each_rating_lasts_until_the_next_rated_summary():
    entries = [_entry(0, 8000, "Good"), _entry(10, 7000, "Warning"), _entry(20, 7500, "Good")]
    end = START + timedelta(days=25)

    assert rating_spans(entries, end) == [
        (START, START + timedelta(days=10), "Good"),
        (START + timedelta(days=10), START + timedelta(days=20), "Warning"),
        (START + timedelta(days=20), end, "Good"),
    ]


def test_manual_entries_do_not_break_a_rating_span():
    entries = [_entry(0, 8000, "Good"), _entry(5, 7900, source=Source.MANUAL), _entry(10, 7000, "Warning")]
    spans = rating_spans(entries, end=START + timedelta(days=12))

    assert [(s.day, e.day, r) for s, e, r in spans] == [(1, 11, "Good"), (11, 13, "Warning")]


def test_no_spans_without_ratings():
    assert rating_spans([_entry(0, 7500, source=Source.MANUAL)], end=START) == []


@pytest.mark.parametrize("scores, label", [
    ([7843], "7843"),
    ([7738, 7843], "7843 (+105)"),
    ([8000, 7500], "7500 (-500)"),
])
def test_last_value_label(scores, label):
    assert last_value_label([_entry(i, s) for i, s in enumerate(scores)]) == label


def test_plot_timeline_saves_a_png(tmp_path, monkeypatch):
    monkeypatch.setenv("MPLBACKEND", "Agg")
    entries = [_entry(0, 8000, "Good"), _entry(5, 7900, source=Source.MANUAL), _entry(10, 6500, "Warning")]
    output = tmp_path / "chart" / "behavior_history.png"

    plot_timeline(entries, output, show=False)

    assert output.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
