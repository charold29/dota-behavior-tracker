import pytest

from conftest import SAMPLE
from dota_behavior_tracker import steam
from dota_behavior_tracker.cli import CHART_FILE, HISTORY_FILE, main


@pytest.fixture
def run(tmp_path, capsys):
    """Runs the CLI with a temporary data dir and returns (exit code, output)."""
    def _run(*args):
        code = main(["--data-dir", str(tmp_path), *args])
        return code, capsys.readouterr().out
    return _run


@pytest.fixture
def conduct_file(monkeypatch):
    monkeypatch.setattr(steam, "find_conduct_file", lambda: SAMPLE)


def test_record_is_the_default_command(run, conduct_file, tmp_path):
    code, out = run()

    assert code == 0
    assert "Recorded summary #8759 from 2026-05-2" in out  # 28 or 29 depending on the time zone
    assert "7843 (+105 vs previous)" in out
    assert (tmp_path / HISTORY_FILE).exists()


def test_record_twice_reports_no_changes(run, conduct_file):
    run("record")
    code, out = run("record")

    assert code == 0
    assert "No changes (summary #8759 already recorded, score 7843)." in out


def test_record_without_conduct_file(run, monkeypatch):
    monkeypatch.setattr(steam, "find_conduct_file", lambda: None)
    code, out = run("record")

    assert code == 1
    assert "Couldn't find latest_conduct_*.txt" in out


def test_add(run):
    code, out = run("add", "7500", "--date", "2026-09-01")

    assert code == 0
    assert out.strip() == "Added 7500 dated 2026-09-01."


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
