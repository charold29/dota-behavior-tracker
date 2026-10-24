# dota-behavior-tracker

Keeps a local history of your **Dota 2 Behavior Score**.

Valve doesn't keep a history of your conduct: every Player Behavior Summary
overwrites the previous one in a local file (`latest_conduct_*.txt`). This
script reads that file and appends each new summary to a CSV, so you can see
how your score changes over time and plot it.

> The code and CLI output are in Spanish.

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
uv run behavior_tracker.py                      # record the current summary (if it's new)
uv run behavior_tracker.py ver                  # show Valve's file and how it was parsed
uv run behavior_tracker.py agregar 7800         # add a value by hand (dated today)
uv run behavior_tracker.py agregar 7500 --fecha 2026-09-01
uv run behavior_tracker.py grafica              # plot your score over time
```

Run it after each new conduct summary (or schedule it with Task Scheduler).
A summary is recorded only once, keyed by its `seq_num`.

### Output

- `behavior_history.csv`: one row per summary, with the score, previous
  score, rating, and every raw field from Valve's file
- `behavior_history.png`: the chart produced by `grafica`

Both files contain your own data and are git-ignored.

## How it works

The script looks for the conduct file in every Steam library:

```
<Steam library>\steamapps\common\dota 2 beta\game\dota\cfg\latest_conduct_<n>.<account_id>.txt
```

The file is a list of `key: value` pairs, usually all on a single line:

```
account_id: 123456789 match_id: 1234567890 seq_num: 8759 ... raw_behavior_score: 7843 old_raw_behavior_score: 7738 ... behavior_rating: k_eBehaviorGood
```

[`conduct_summary.py`](conduct_summary.py) turns that text into a
`ResumenConducta` object. It doesn't depend on Windows or Steam, so it can be
tested anywhere. [`behavior_tracker.py`](behavior_tracker.py) has the Steam lookup, the CSV
writer and the CLI.

| Field | Meaning |
| --- | --- |
| `raw_behavior_score` | Current behavior score (max 12000) |
| `old_raw_behavior_score` | Score in the previous summary |
| `behavior_rating` | `k_eBehaviorGood`, `k_eBehaviorWarning` or `k_eBehaviorBad` |
| `matches_in_report` / `matches_clean` / `matches_reported` / `matches_abandoned` | Matches covered by the summary |
| `reports_count` / `commend_count` | Reports and commends received |
| `date` | When the summary was generated (Unix time) |

Any field Valve adds later is kept in the CSV's `datos` column.

## Tests

```powershell
uv run pytest
```

## Disclaimer

This is a fan project and is not affiliated with Valve. It only reads a file
that Dota 2 already writes to your disk.
