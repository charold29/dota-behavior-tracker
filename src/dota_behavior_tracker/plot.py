"""
Infrastructure: draws the behavior score chart with matplotlib.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

MAX_SCORE = 12000


def plot_timeline(points: list[tuple[datetime, int]], output: Path, show: bool = True) -> None:
    """Saves the chart to `output` and, if `show`, opens it in a window."""
    x = [d.astimezone().replace(tzinfo=None) for d, _ in points]  # local time, as matplotlib expects
    y = [score for _, score in points]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(x, y, marker="o", linewidth=2)
    ax.set_title("Behavior Score - Dota 2")
    ax.set_ylabel("Points")
    ax.set_ylim(0, MAX_SCORE)
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    fig.tight_layout()

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=120)
    if show:
        plt.show()
    plt.close(fig)
