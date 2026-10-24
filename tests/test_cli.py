import pytest

from conftest import SAMPLE_TEXT, FakeSource
from dota_behavior_tracker.cli import CHART_FILE, HISTORY_FILE, main


@pytest.fixture
def run(tmp_path, capsys):
    """Runs the CLI with a temporary data dir and a fake conduct source; returns (exit code, output)."""
    def _run(*args, source=FakeSource(SAMPLE_TEXT)):
        code = main(["--data-dir", str(tmp_path), *args], source=source)
        return code, capsys.readouterr().out
    return _run


def test_record_is_the_default_command(run, tmp_path):
    code, out = run()

    assert code == 0
    assert "Recorded summary #8759 from 2026-05-2" in out  # 28 or 29 depending on the time zone
    assert "7843 (+105 vs previous)" in out
    assert "Locked: Coaching (needs 10000)." in out
    assert (tmp_path / HISTORY_FILE).exists()


def test_record_twice_reports_no_changes(run):
    run("record")
    code, out = run("record")

    assert code == 0
    assert "No changes (summary #8759 already recorded, score 7843)." in out


def test_record_without_conduct_file(run):
    code, out = run("record", source=FakeSource(None))

    assert code == 1
    assert "Couldn't find latest_conduct_*.txt" in out


def test_show_prints_the_file_and_the_parsed_summary(run):
    code, out = run("show")

    assert code == 0
    assert "File: fake" in out
    assert "Parsed: ConductSummary(seq_num=8759" in out


def test_add(run):
    code, out = run("add", "7500", "--date", "2026-09-01")

    assert code == 0
    assert out.splitlines() == [
        "Added 7500 dated 2026-09-01.",
        "Locked: Coaching (needs 10000).",
    ]


def test_add_with_everything_unlocked(run):
    code, out = run("add", "11000")

    assert code == 0
    assert "Every behavior score feature is unlocked." in out


def test_add_rejects_an_out_of_range_score(run, tmp_path):
    code, out = run("add", "99999")

    assert code == 1
    assert "between 0 and 12000, got 99999" in out
    assert not (tmp_path / HISTORY_FILE).exists()


def test_add_rejects_an_invalid_date(run, capsys):
    with pytest.raises(SystemExit):
        run("add", "7500", "--date", "01/09/2026")
    assert "use YYYY-MM-DD" in capsys.readouterr().err


def test_plot_without_history(run):
    code, out = run("plot", "--no-show")

    assert code == 1
    assert "no behavior score values" in out


def test_plot_saves_the_chart(run, tmp_path, monkeypatch):
    monkeypatch.setenv("MPLBACKEND", "Agg")
    run("add", "7500", "--date", "2026-09-01")
    run("add", "7800", "--date", "2026-10-01")

    code, out = run("plot", "--no-show")

    assert code == 0
    assert (tmp_path / CHART_FILE).exists()
