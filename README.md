# dota-behavior-tracker

Keeps a local history of your **Dota 2 Behavior Score**.

Valve doesn't keep a history of your conduct: every Player Behavior Summary
overwrites the previous one in a local file (`latest_conduct_*.txt`). This
script reads that file and appends each new summary to a CSV, so you can see
how your score changes over time and plot it.

## Requirements

- Windows. The script finds your Steam install through the registry.
- Dota 2 installed through Steam, opened at least once after a conduct summary
- [uv](https://docs.astral.sh/uv/)

## Setup

```powershell
git clone https://github.com/<your-user>/dota-behavior-tracker.git
cd dota-behavior-tracker
uv sync
```

## Usage

```powershell
uv run dota-behavior                    # record the current summary (if it's new)
uv run dota-behavior show               # show Valve's file and how it was parsed
uv run dota-behavior add 7800           # add a value by hand (dated today)
uv run dota-behavior add 7500 --date 2026-09-01
uv run dota-behavior plot               # plot your score over time
uv run dota-behavior plot --no-show     # only save the PNG
```

`python -m dota_behavior_tracker` works too.

Run it after each new conduct summary (or schedule it with Task Scheduler).
A summary is recorded only once, keyed by its `seq_num`.

### Output

Your data is saved in `%LOCALAPPDATA%\dota-behavior-tracker\`:

- `behavior_history.csv`: one row per summary, with the score, previous
  score, rating, and every raw field from Valve's file
- `behavior_history.png`: the chart produced by `plot`. Each period is
  shaded with the rating Valve gave you (Good, Warning, Bad), scores added by
  hand are drawn as hollow points, and the latest value is labeled with its
  change

To use another folder, pass `--data-dir` before the command:

```powershell
uv run dota-behavior --data-dir D:\backups\dota add 7800
```

## How it works

The script looks for the conduct file in every Steam library:

```
<Steam library>\steamapps\common\dota 2 beta\game\dota\cfg\latest_conduct_<n>.<account_id>.txt
```

The file is a list of `key: value` pairs, usually all on a single line:

```
account_id: 123456789 match_id: 1234567890 seq_num: 8759 ... raw_behavior_score: 7843 old_raw_behavior_score: 7738 ... behavior_rating: k_eBehaviorGood
```

| Field | Meaning |
| --- | --- |
| `raw_behavior_score` | Current behavior score (max 12000) |
| `old_raw_behavior_score` | Score in the previous summary |
| `behavior_rating` | `k_eBehaviorGood`, `k_eBehaviorWarning` or `k_eBehaviorBad` |
| `matches_in_report` / `matches_clean` / `matches_reported` / `matches_abandoned` | Matches covered by the summary |
| `reports_count` / `commend_count` | Reports and commends received |
| `date` | When the summary was generated (Unix time) |

Any field Valve adds later is kept in the CSV's `data` column.

### What the score means

Dota's Player Behavior Summary shows two scores, each unlocking features at
its own threshold (checked in-game, October 2026):

| Behavior score | Unlocks |
| --- | --- |
| 3000 | Ranked matchmaking |
| 5000 | In-game pausing |
| 7000 | Post-game drops (treasure chests and sets) |
| 10000 | Coaching (also needs 10000 communication score) |

| Communication score | Unlocks |
| --- | --- |
| 3000 | Unthrottled messages (below it, pings, alerts and chat wheels share a 30 s cooldown) |
| 6000 | Text chat |
| 7000 | In-game tipping |
| 8000 | Voice chat |
| 10000 | Coaching (also needs 10000 behavior score), pinging ally abilities |

The chart draws a dashed line at each behavior score threshold. The
`latest_conduct` file doesn't include the communication score, so it isn't
tracked. The background colors come from the actual rating in each of Valve's
summaries.

## Project structure

A lightweight hexagonal (ports and adapters) architecture:

```
src/dota_behavior_tracker/
├── domain/
│   ├── summary.py          # ConductSummary, its parser, behavior score unlocks
│   └── history.py          # HistoryEntry, Source
├── application/
│   ├── ports.py            # HistoryRepository, ConductSource (Protocols)
│   └── tracker.py          # use cases: record, add, timeline
├── adapters/
│   ├── csv_history.py      # HistoryRepository backed by a CSV file
│   ├── steam_source.py     # ConductSource that finds the file in Steam
│   └── chart.py            # the matplotlib chart
└── cli.py                  # command line + composition root
```

Dependencies point inwards: `adapters` and `cli` → `application` → `domain`.

- **domain** is pure logic and imports nothing outside itself.
- **application** only knows the ports, never a file, Steam or matplotlib.
  The tests run the use cases against in-memory fakes.
- **cli** is the only place that picks the concrete adapters. Storing the
  history somewhere else (SQLite, JSON...) means writing a new
  `HistoryRepository` adapter and changing one line there.

## Tests

```powershell
uv run pytest
```

## Disclaimer

This is a fan project and is not affiliated with Valve. It only reads a file
that Dota 2 already writes to your disk.
