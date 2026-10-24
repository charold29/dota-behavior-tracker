from datetime import date, datetime, timezone

import pytest

from conftest import NOW, FakeSource
from dota_behavior_tracker.application.tracker import (
    ConductFileNotFoundError,
    add_manual_score,
    record_summary,
    score_timeline,
)
from dota_behavior_tracker.domain.history import HistoryEntry, Source
from dota_behavior_tracker.domain.score import InvalidScoreError
from dota_behavior_tracker.domain.summary import InvalidFormatError


# ------------------------------------------------------- record_summary --

def test_records_a_new_summary(history, sample_source):
    result = record_summary(history, sample_source, now=NOW)

    assert result.recorded
    assert result.summary.seq_num == 8759
    [entry] = history.entries
    assert entry.seq_num == 8759
    assert entry.recorded_at == NOW


def test_does_not_record_the_same_summary_twice(history, sample_source):
    record_summary(history, sample_source, now=NOW)
    result = record_summary(history, sample_source, now=NOW)

    assert not result.recorded
    assert len(history.entries) == 1


def test_a_manual_entry_with_the_same_seq_num_does_not_count(history, sample_source):
    history.append(HistoryEntry(recorded_at=NOW, summary_date=NOW, behavior_score=1,
                                source=Source.MANUAL, seq_num=8759))

    assert record_summary(history, sample_source, now=NOW).recorded


def test_fails_when_there_is_no_conduct_file(history):
    with pytest.raises(ConductFileNotFoundError):
        record_summary(history, FakeSource(None))


def test_an_invalid_file_is_not_recorded(history):
    with pytest.raises(InvalidFormatError):
        record_summary(history, FakeSource("this is not the format"))
    assert history.entries == []


# ----------------------------------------------------- add_manual_score --

def test_adds_a_manual_score_on_the_given_date(history):
    entry = add_manual_score(history, 7500, on=date(2026, 9, 1), now=NOW)

    assert history.entries == [entry]
    assert entry.source is Source.MANUAL
    assert entry.behavior_score == 7500
    assert entry.summary_date.date() == date(2026, 9, 1)


@pytest.mark.parametrize("score", [-1, 12001])
def test_an_out_of_range_manual_score_is_not_stored(history, score):
    with pytest.raises(InvalidScoreError):
        add_manual_score(history, score, now=NOW)
    assert history.entries == []


def test_manual_score_defaults_to_today(history):
    entry = add_manual_score(history, 7800, now=NOW)
    assert entry.summary_date.date() == NOW.date()


# ------------------------------------------------------- score_timeline --

def test_timeline_is_sorted_by_date_mixing_sources(history, sample_source):
    add_manual_score(history, 8000, on=date(2026, 10, 1), now=NOW)
    record_summary(history, sample_source, now=NOW)            # summary from 2026-05-29
    add_manual_score(history, 7500, on=date(2026, 9, 1), now=NOW)

    assert [e.behavior_score for e in score_timeline(history)] == [7843, 7500, 8000]


def test_timeline_is_empty_without_history(history):
    assert score_timeline(history) == []
