from datetime import date

import pytest

from conftest import NOW, SAMPLE
from dota_behavior_tracker.history import Source
from dota_behavior_tracker.summary import InvalidFormatError
from dota_behavior_tracker.tracker import (
    ConductFileNotFoundError,
    add_manual_score,
    record_summary,
    score_timeline,
)


# ------------------------------------------------------- record_summary --

def test_records_a_new_summary(store):
    result = record_summary(store, SAMPLE, now=NOW)

    assert result.recorded
    assert result.summary.seq_num == 8759
    [entry] = store.read()
    assert entry.seq_num == 8759
    assert entry.recorded_at == NOW


def test_does_not_record_the_same_summary_twice(store):
    record_summary(store, SAMPLE, now=NOW)
    result = record_summary(store, SAMPLE, now=NOW)

    assert not result.recorded
    assert len(store.read()) == 1


def test_fails_when_there_is_no_conduct_file(store):
    with pytest.raises(ConductFileNotFoundError):
        record_summary(store, None)


def test_an_invalid_file_is_not_recorded(store, tmp_path):
    bad = tmp_path / "latest_conduct_bad.txt"
    bad.write_text("this is not the format", encoding="utf-8")

    with pytest.raises(InvalidFormatError):
        record_summary(store, bad)
    assert store.read() == []


# ----------------------------------------------------- add_manual_score --

def test_adds_a_manual_score_on_the_given_date(store):
    entry = add_manual_score(store, 7500, on=date(2026, 9, 1), now=NOW)

    assert store.read() == [entry]
    assert entry.source is Source.MANUAL
    assert entry.behavior_score == 7500
    assert entry.summary_date.date() == date(2026, 9, 1)


def test_manual_score_defaults_to_today(store):
    entry = add_manual_score(store, 7800, now=NOW)
    assert entry.summary_date.date() == NOW.date()


# ------------------------------------------------------- score_timeline --

def test_timeline_is_sorted_by_date_mixing_sources(store):
    add_manual_score(store, 8000, on=date(2026, 10, 1), now=NOW)
    record_summary(store, SAMPLE, now=NOW)                      # summary from 2026-05-29
    add_manual_score(store, 7500, on=date(2026, 9, 1), now=NOW)

    assert [e.behavior_score for e in score_timeline(store)] == [7843, 7500, 8000]


def test_timeline_is_empty_without_history(store):
    assert score_timeline(store) == []
