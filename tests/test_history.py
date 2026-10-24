import json
from datetime import datetime, timezone

import pytest

from conftest import NOW, SAMPLE
from dota_behavior_tracker.history import COLUMNS, HistoryEntry, Source
from dota_behavior_tracker.summary import ConductSummary


@pytest.fixture
def entry() -> HistoryEntry:
    return HistoryEntry.from_summary(ConductSummary.from_file(SAMPLE), recorded_at=NOW)


@pytest.fixture
def manual_entry() -> HistoryEntry:
    return HistoryEntry(
        recorded_at=NOW,
        summary_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
        behavior_score=7500,
        source=Source.MANUAL,
    )


# ------------------------------------------------------------ entries ----

def test_from_summary_copies_the_score_fields(entry):
    assert entry.behavior_score == 7843
    assert entry.previous_score == 7738
    assert entry.rating == "Good"
    assert entry.source is Source.FILE
    assert entry.seq_num == 8759
    assert entry.summary_date == datetime(2026, 5, 29, 0, 19, 23, tzinfo=timezone.utc)


def test_to_row_builds_the_csv_row(entry):
    row = entry.to_row()

    assert list(row) == COLUMNS
    assert row["recorded_at"] == "2026-10-24T13:00:00+00:00"
    assert row["summary_date"] == "2026-05-29T00:19:23+00:00"
    assert row["behavior_score"] == "7843"
    assert row["previous_score"] == "7738"
    assert row["rating"] == "Good"
    assert row["source"] == "file"
    assert row["seq_num"] == "8759"
    assert json.loads(row["data"])["commend_count"] == 8


def test_manual_entry_leaves_optional_columns_empty(manual_entry):
    row = manual_entry.to_row()
    assert row["source"] == "manual"
    assert row["previous_score"] == row["rating"] == row["seq_num"] == row["data"] == ""


@pytest.mark.parametrize("fixture", ["entry", "manual_entry"])
def test_row_round_trip(request, fixture):
    original = request.getfixturevalue(fixture)
    assert HistoryEntry.from_row(original.to_row()) == original


# -------------------------------------------------------------- store ----

def test_read_is_empty_when_the_file_does_not_exist(store):
    assert store.read() == []


def test_append_creates_the_folder_and_writes_the_header_once(store, entry, manual_entry):
    store.append(entry)
    store.append(manual_entry)

    lines = store.path.read_text(encoding="utf-8-sig").splitlines()
    assert lines[0] == ",".join(COLUMNS)
    assert len(lines) == 3
    assert store.read() == [entry, manual_entry]


def test_has_seq_num_only_matches_entries_from_the_file(store, entry, manual_entry):
    store.append(manual_entry)
    assert not store.has_seq_num(8759)

    store.append(entry)
    assert store.has_seq_num(8759)
    assert not store.has_seq_num(1)
