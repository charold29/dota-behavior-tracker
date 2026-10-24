import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from conduct_summary import ConductSummary, InvalidFormatError

RESOURCES = Path(__file__).parent / "resources"
SAMPLE = RESOURCES / "latest_conduct_sample.txt"


@pytest.fixture
def sample_text() -> str:
    return SAMPLE.read_text(encoding="utf-8")


@pytest.fixture
def summary() -> ConductSummary:
    return ConductSummary.from_file(SAMPLE)


# ---------------------------------------------------------- parsing ok ---

def test_reads_every_field_in_the_file(summary):
    assert summary.account_id == 123456789
    assert summary.match_id == 1234567890
    assert summary.seq_num == 8759
    assert summary.reasons == 1
    assert summary.matches_in_report == 15
    assert summary.matches_clean == 14
    assert summary.matches_reported == 1
    assert summary.matches_abandoned == 0
    assert summary.reports_count == 3
    assert summary.reports_parties == 3
    assert summary.commend_count == 8
    assert summary.raw_behavior_score == 7843
    assert summary.old_raw_behavior_score == 7738
    assert summary.comms_reports == 0
    assert summary.comms_parties == 0
    assert summary.behavior_rating == "k_eBehaviorGood"
    assert summary.extras == {}


def test_converts_epoch_date_to_utc_datetime(summary):
    assert summary.date == datetime(2026, 5, 29, 0, 19, 23, tzinfo=timezone.utc)


def test_from_text_and_from_file_match(sample_text, summary):
    assert ConductSummary.from_text(sample_text) == summary


def test_tolerates_whitespace_and_windows_line_endings(sample_text):
    text = "\r\n".join(f"   {line}   " for line in sample_text.splitlines())
    assert ConductSummary.from_text(text).raw_behavior_score == 7843


def test_reads_the_real_single_line_format(sample_text, summary):
    # this is how Valve writes it: every field on one line, separated by spaces
    text = " ".join(sample_text.split("\n")).strip()
    assert ConductSummary.from_text(text) == summary


# ------------------------------------------------------------ derived ----

def test_change_is_the_difference_from_the_previous_score(summary):
    assert summary.change == 105


def test_change_is_none_without_a_previous_score(sample_text):
    text = _without_field(sample_text, "old_raw_behavior_score")
    assert ConductSummary.from_text(text).change is None


@pytest.mark.parametrize("raw, label", [
    ("k_eBehaviorGood", "Good"),
    ("k_eBehaviorWarning", "Warning"),
    ("k_eBehaviorBad", "Bad"),
    ("k_eBehaviorSomethingNew", "k_eBehaviorSomethingNew"),  # unknown: kept as is
])
def test_rating_label(sample_text, raw, label):
    text = sample_text.replace("k_eBehaviorGood", raw)
    assert ConductSummary.from_text(text).rating_label == label


def test_unknown_fields_go_to_extras(sample_text):
    text = sample_text + "new_valve_field: 42\n"
    s = ConductSummary.from_text(text)
    assert s.extras == {"new_valve_field": "42"}


# ------------------------------------------------------------- errors ----

@pytest.mark.parametrize("required", ["seq_num", "raw_behavior_score", "date"])
def test_fails_when_a_required_field_is_missing(sample_text, required):
    with pytest.raises(InvalidFormatError, match=required):
        ConductSummary.from_text(_without_field(sample_text, required))


def test_fails_when_a_number_is_not_a_number(sample_text):
    text = sample_text.replace("raw_behavior_score: 7843", "raw_behavior_score: abc")
    with pytest.raises(InvalidFormatError, match="raw_behavior_score"):
        ConductSummary.from_text(text)


@pytest.mark.parametrize("text", ["", "   \n\n", "this is not the format"])
def test_fails_with_empty_or_garbage_text(text):
    with pytest.raises(InvalidFormatError):
        ConductSummary.from_text(text)


def test_missing_optional_fields_use_defaults():
    text = "seq_num: 1\nraw_behavior_score: 10000\ndate: 0\n"
    s = ConductSummary.from_text(text)
    assert s.account_id is None
    assert s.commend_count == 0
    assert s.behavior_rating == ""


# ------------------------------------------------------- to_row (CSV) ----

def test_to_row_builds_the_csv_row(summary):
    recorded_at = datetime(2026, 10, 24, 13, 0, tzinfo=timezone.utc)
    row = summary.to_row(recorded_at=recorded_at)

    assert row["recorded_at"] == "2026-10-24T13:00:00+00:00"
    assert row["summary_date"] == "2026-05-29T00:19:23+00:00"
    assert row["behavior_score"] == "7843"
    assert row["previous_score"] == "7738"
    assert row["rating"] == "Good"
    assert row["source"] == "file"
    assert row["seq_num"] == "8759"
    assert json.loads(row["data"])["commend_count"] == 8


# ------------------------------------------------------------ helpers ----

def _without_field(text: str, field: str) -> str:
    return "\n".join(l for l in text.splitlines() if not l.startswith(f"{field}:"))
