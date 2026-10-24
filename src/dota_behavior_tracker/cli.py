"""
Interface: the command line. Parses arguments and prints results; the logic
lives in tracker.py.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

from . import steam, tracker
from .history import HistoryStore
from .summary import ConductSummary, InvalidFormatError

APP_NAME = "dota-behavior-tracker"
HISTORY_FILE = "behavior_history.csv"
CHART_FILE = "behavior_history.png"


def default_data_dir() -> Path:
    """%LOCALAPPDATA%\\dota-behavior-tracker on Windows, ~/.local/share/... elsewhere."""
    base = os.environ.get("LOCALAPPDATA")
    return Path(base) / APP_NAME if base else Path.home() / ".local" / "share" / APP_NAME


# ---------------------------------------------------------------- commands -

def cmd_record(args) -> int:
    try:
        result = tracker.record_summary(_store(args), steam.find_conduct_file())
    except tracker.ConductFileNotFoundError:
        print("Couldn't find latest_conduct_*.txt. Open Dota 2 at least once "
              "and check that the game is installed through Steam.")
        return 1
    except InvalidFormatError as e:
        print(f"Couldn't read the summary: {e}")
        return 1

    s = result.summary
    if not result.recorded:
        print(f"No changes (summary #{s.seq_num} already recorded, score {s.raw_behavior_score}).")
        return 0

    change = f" ({s.change:+d} vs previous)" if s.change is not None else ""
    print(f"Recorded summary #{s.seq_num} from {s.date.astimezone():%Y-%m-%d}: "
          f"{s.raw_behavior_score}{change}")
    return 0


def cmd_show(_args) -> int:
    path = steam.find_conduct_file()
    if path is None:
        print("Couldn't find the conduct file.")
        return 1
    print(f"File: {path}\n")
    print(path.read_text(encoding="utf-8", errors="ignore"))
    try:
        print("\nParsed:", ConductSummary.from_file(path))
    except InvalidFormatError as e:
        print(f"\nCouldn't parse it: {e}")
    return 0


def cmd_add(args) -> int:
    entry = tracker.add_manual_score(_store(args), args.score, args.date)
    print(f"Added {entry.behavior_score} dated {entry.summary_date:%Y-%m-%d}.")
    return 0


def cmd_plot(args) -> int:
    points = tracker.score_timeline(_store(args))
    if not points:
        print("There are no behavior score values in the history yet.")
        return 1

    from .plot import plot_timeline  # matplotlib is slow to import: only load it when plotting

    output = args.data_dir / CHART_FILE
    plot_timeline(points, output, show=not args.no_show)
    print(f"Chart saved to {output}")
    return 0


# ------------------------------------------------------------------ parser -

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dota-behavior", description="Dota 2 Behavior Score history")
    p.add_argument("--data-dir", type=Path, default=default_data_dir(),
                   help="where the history CSV and the chart are saved (default: %(default)s)")
    p.set_defaults(func=cmd_record)

    sub = p.add_subparsers(title="commands", metavar="COMMAND")
    sub.add_parser("record", help="record the current summary if it's new (default)").set_defaults(func=cmd_record)
    sub.add_parser("show", help="show Valve's file and how it was parsed").set_defaults(func=cmd_show)

    add = sub.add_parser("add", help="add a value by hand")
    add.add_argument("score", type=int)
    add.add_argument("--date", type=_parse_date, help="YYYY-MM-DD (defaults to today)")
    add.set_defaults(func=cmd_add)

    plot = sub.add_parser("plot", help="plot the score over time")
    plot.add_argument("--no-show", action="store_true", help="only save the PNG, don't open a window")
    plot.set_defaults(func=cmd_plot)
    return p


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    return args.func(args)


def _store(args) -> HistoryStore:
    return HistoryStore(args.data_dir / HISTORY_FILE)


def _parse_date(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date '{text}', use YYYY-MM-DD") from None
