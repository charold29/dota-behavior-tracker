"""
Infrastructure: draws the behavior score chart with matplotlib.

The background of each period is colored with the rating Valve gave in the
summary that starts it. Valve doesn't publish the score ranges of each rating,
so the chart uses the actual ratings instead of guessed thresholds.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from .history import HistoryEntry, Source
from .summary import RATINGS

MAX_SCORE = 12000
RATING_COLORS = {
    RATINGS["k_eBehaviorGood"]: "#2e9d5b",
    RATINGS["k_eBehaviorWarning"]: "#e0a100",
    RATINGS["k_eBehaviorBad"]: "#d64545",
}
NO_RATING_COLOR = "#8a8a8a"  # manual entries and unknown ratings
LINE_COLOR = "#4a4a4a"


def rating_spans(entries: list[HistoryEntry], end: datetime) -> list[tuple[datetime, datetime, str]]:
    """(start, end, rating) periods: each rating lasts until the next summary that has one."""
    rated = [e for e in entries if e.rating in RATING_COLORS]
    spans = []
    for current, following in zip(rated, rated[1:] + [None]):
        stop = following.summary_date if following else end
        spans.append((current.summary_date, stop, current.rating))
    return spans


def last_value_label(entries: list[HistoryEntry]) -> str:
    """'7843 (+105)': the latest score and its change from the previous point in the chart."""
    last = entries[-1]
    if len(entries) < 2:
        return str(last.behavior_score)
    return f"{last.behavior_score} ({last.behavior_score - entries[-2].behavior_score:+d})"


def plot_timeline(entries: list[HistoryEntry], output: Path, show: bool = True) -> None:
    """Saves the chart to `output` and, if `show`, opens it in a window. `entries` must be sorted."""
    x = [_local(e.summary_date) for e in entries]
    y = [e.behavior_score for e in entries]
    colors = [RATING_COLORS.get(e.rating, NO_RATING_COLOR) for e in entries]
    padding = max((x[-1] - x[0]) * 0.04, timedelta(days=3))

    fig, ax = plt.subplots(figsize=(10, 5))

    for start, stop, rating in rating_spans(entries, end=entries[-1].summary_date + padding):
        ax.axvspan(_local(start), _local(stop), color=RATING_COLORS[rating], alpha=0.12, linewidth=0)

    ax.plot(x, y, color=LINE_COLOR, linewidth=1.8, zorder=2)
    for xi, yi, color, entry in zip(x, y, colors, entries):
        manual = entry.source is Source.MANUAL
        ax.scatter(xi, yi, s=42, zorder=3, linewidths=1.6,
                   facecolors="white" if manual else color, edgecolors=color)

    ax.annotate(last_value_label(entries), xy=(x[-1], y[-1]), xytext=(0, 14),
                textcoords="offset points", ha="center", fontsize=10, fontweight="bold",
                bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": colors[-1]})

    ax.set_title("Behavior Score - Dota 2")
    ax.set_ylabel("Points")
    ax.set_ylim(0, MAX_SCORE)
    ax.set_xlim(x[0] - padding, x[-1] + padding)
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.legend(handles=_legend(entries), loc="lower left", fontsize=9, framealpha=0.9)
    fig.autofmt_xdate()
    fig.tight_layout()

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=120)
    if show:
        plt.show()
    plt.close(fig)


def _legend(entries: list[HistoryEntry]) -> list[Line2D]:
    ratings = {e.rating for e in entries}
    handles = [_marker(color, rating) for rating, color in RATING_COLORS.items() if rating in ratings]
    if any(e.source is Source.MANUAL for e in entries):
        handles.append(_marker("white", "Added by hand", edge=NO_RATING_COLOR))
    return handles


def _marker(color: str, label: str, edge: str | None = None) -> Line2D:
    return Line2D([], [], marker="o", linestyle="", markersize=7, label=label,
                  markerfacecolor=color, markeredgecolor=edge or color, markeredgewidth=1.6)


def _local(d: datetime) -> datetime:
    return d.astimezone().replace(tzinfo=None)  # local time, as matplotlib expects
