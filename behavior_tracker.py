"""
behavior_tracker.py - Keeps a history of your Dota 2 Behavior Score.

Valve doesn't keep a history: it only leaves the latest summary in a local file
(latest_conduct_*.txt). This script reads it and appends each new summary to a CSV.

Usage:
  python behavior_tracker.py                  record the current summary (if it's new)
  python behavior_tracker.py show             show Valve's file and how it was parsed
  python behavior_tracker.py add 7800         add a value by hand (dated today)
  python behavior_tracker.py add 7500 --date 2026-09-01
  python behavior_tracker.py plot             plot the score over time (requires matplotlib)
"""
import argparse
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

from conduct_summary import ConductSummary, InvalidFormatError

BASE = Path(__file__).resolve().parent
CSV_PATH = BASE / "behavior_history.csv"
PNG_PATH = BASE / "behavior_history.png"
COLUMNS = ["recorded_at", "summary_date", "behavior_score", "previous_score",
           "rating", "source", "seq_num", "data"]
CFG_PATH = Path("steamapps") / "common" / "dota 2 beta" / "game" / "dota" / "cfg"


# ---------------------------------------------------------------- Steam ----

def steam_folders():
    """Main Steam folder + extra libraries (other drives/folders)."""
    import winreg  # only exists on Windows; imported here so the tests don't break

    paths = []
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
            paths.append(Path(winreg.QueryValueEx(k, "SteamPath")[0]))
    except OSError:
        pass
    paths += [Path(r"C:\Program Files (x86)\Steam"), Path(r"C:\Program Files\Steam")]

    extra = []
    for p in paths:
        vdf = p / "steamapps" / "libraryfolders.vdf"
        if vdf.exists():
            text = vdf.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r'"path"\s+"([^"]+)"', text):
                extra.append(Path(m.group(1).replace("\\\\", "\\")))

    seen, unique = set(), []
    for p in paths + extra:
        key = str(p).lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def find_conduct_file():
    candidates = []
    for steam in steam_folders():
        cfg = steam / CFG_PATH
        if cfg.is_dir():
            candidates += list(cfg.glob("latest_conduct_*.txt"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


# ---------------------------------------------------------------- CSV ------

def read_history():
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def append_row(row):
    new = not CSV_PATH.exists()
    with CSV_PATH.open("a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if new:
            w.writeheader()
        w.writerow(row)


# ---------------------------------------------------------------- commands -

def cmd_record(_args):
    path = find_conduct_file()
    if path is None:
        print("Couldn't find latest_conduct_*.txt. Open Dota 2 at least once "
              "and check that the game is installed through Steam.")
        return 1

    try:
        summary = ConductSummary.from_file(path)
    except InvalidFormatError as e:
        print(f"Couldn't read the summary: {e}")
        return 1

    already_recorded = {r["seq_num"] for r in read_history() if r["source"] == "file"}
    if str(summary.seq_num) in already_recorded:
        print(f"No changes (summary #{summary.seq_num} already recorded, score {summary.raw_behavior_score}).")
        return 0

    append_row(summary.to_row(recorded_at=datetime.now().astimezone()))
    change = f" ({summary.change:+d} vs previous)" if summary.change is not None else ""
    local_date = summary.date.astimezone()
    print(f"Recorded summary #{summary.seq_num} from {local_date:%Y-%m-%d}: "
          f"{summary.raw_behavior_score}{change}")
    return 0


def cmd_show(_args):
    path = find_conduct_file()
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


def cmd_add(args):
    date = args.date or datetime.now().strftime("%Y-%m-%d")
    try:
        date_dt = datetime.strptime(date, "%Y-%m-%d").astimezone()
    except ValueError:
        print("Invalid date, use the YYYY-MM-DD format.")
        return 1
    append_row({
        "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "summary_date": date_dt.isoformat(timespec="seconds"),
        "behavior_score": str(args.score),
        "previous_score": "",
        "rating": "",
        "source": "manual",
        "seq_num": "",
        "data": "",
    })
    print(f"Added {args.score} dated {date}.")
    return 0


def _local_date(text):
    date = datetime.fromisoformat(text)
    return date.astimezone()  # converts to local time (and makes naive dates "aware")


def cmd_plot(_args):
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("matplotlib is missing. Install it with: uv sync")
        return 1

    points = []
    for r in read_history():
        if r["behavior_score"]:
            date = _local_date(r["summary_date"] or r["recorded_at"])
            points.append((date.replace(tzinfo=None), float(r["behavior_score"])))
    if not points:
        print("There are no behavior score values in the history yet.")
        return 1
    points.sort()
    x, y = zip(*points)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(x, y, marker="o", linewidth=2)
    ax.set_title("Behavior Score - Dota 2")
    ax.set_ylabel("Points")
    ax.set_ylim(0, 12000)
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(PNG_PATH, dpi=120)
    print(f"Chart saved to {PNG_PATH}")
    plt.show()
    return 0


def main():
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    p = argparse.ArgumentParser(description="Dota 2 Behavior Score history")
    sub = p.add_subparsers(dest="command")
    sub.add_parser("show", help="show Valve's file and how it was parsed")
    sub.add_parser("plot", help="plot the score over time")
    a = sub.add_parser("add", help="add a value by hand")
    a.add_argument("score", type=int)
    a.add_argument("--date", help="YYYY-MM-DD (defaults to today)")

    args = p.parse_args()
    actions = {None: cmd_record, "show": cmd_show, "add": cmd_add, "plot": cmd_plot}
    return actions[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
