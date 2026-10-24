import json
from datetime import datetime, timezone

import pytest

from conftest import NOW, SAMPLE_TEXT
from dota_behavior_tracker.adapters.csv_history import (
    COLUMNS,
    CsvHistoryRepository,
    entry_to_row,
    row_to_entry,
)
from dota_behavior_tracker.domain.history import HistoryEntry, Source
from dota_behavior_tracker.domain.summary import ConductSummary


@pytest.fixture
def repo(tmp_path) -> CsvHistoryRepository:
    return CsvHistoryRepository(tmp_path / "data" / "behavior_history.csv")


@pytest.fixture
def entry() -> HistoryEntry:
    return HistoryEntry.from_summary(ConductSummary.from_text(SAMPLE_TEXT), recorded_at=NOW)


@pytest.fixture
def manual_entry() -> HistoryEntry:
    return HistoryEntry(
        recorded_at=NOW,
        summary_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
        behavior_score=7500,
        source=Source.MANUAL,
    )


# --------------------------------------------------------------- rows ----

def test_entry_to_row_builds_the_csv_row(entry):
    row = entry_to_row(entry)

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
    row = entry_to_row(manual_entry)
    assert row["source"] == "manual"
    assert row["previous_score"] == row["rating"] == row["seq_num"] == row["data"] == ""


@pytest.mark.parametrize("fixture", ["entry", "manual_entry"])
def test_row_round_trip(request, fixture):
    original = request.getfixturevalue(fixture)
    assert row_to_entry(entry_to_row(original)) == original


# --------------------------------------------------------------- file ----

def test_read_is_empty_when_the_file_does_not_exist(repo):
    assert repo.read() == []


def test_append_creates_the_folder_and_writes_the_header_once(repo, entry, manual_entry):
    repo.append(entry)
    repo.append(manual_entry)

    lines = repo.path.read_text(encoding="utf-8-sig").splitlines()
    assert lines[0] == ",".join(COLUMNS)
    assert len(lines) == 3
    assert repo.read() == [entry, manual_entry]
