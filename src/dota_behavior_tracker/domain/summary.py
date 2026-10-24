"""
Domain: the Dota 2 Player Behavior Summary (latest_conduct_*.txt file).

Pure logic: it only turns text into an object. Reading the file from disk is
the job of an adapter (adapters/steam_source.py).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone

RATINGS = {
    "k_eBehaviorGood": "Good",
    "k_eBehaviorWarning": "Warning",
    "k_eBehaviorBad": "Bad",
}

# Behavior score needed for each feature, as shown in Dota's Player Behavior
# Summary (checked in-game, October 2026). Chat, voice and tipping depend on the
# communication score instead, which the latest_conduct file doesn't include.
BEHAVIOR_UNLOCKS = {
    3000: "Ranked",
    5000: "Pausing",
    7000: "Post-game drops",
    10000: "Coaching",  # also needs 10000 communication score
}

# 'key: value' pairs separated by newlines or spaces: Valve's real file comes
# all on a single line. Values never contain spaces.
_PAIR = re.compile(r"(?<!\S)([A-Za-z_]\w*)\s*:\s*(\S+)")


class InvalidFormatError(ValueError):
    """The text doesn't have the expected format or is missing a required field."""


@dataclass(frozen=True)
class ConductSummary:
    seq_num: int
    raw_behavior_score: int
    date: datetime                       # 'date' field (epoch) converted to UTC
    account_id: int | None = None
    match_id: int | None = None
    old_raw_behavior_score: int | None = None
    behavior_rating: str = ""
    reasons: int = 0
    matches_in_report: int = 0
    matches_clean: int = 0
    matches_reported: int = 0
    matches_abandoned: int = 0
    reports_count: int = 0
    reports_parties: int = 0
    commend_count: int = 0
    comms_reports: int = 0
    comms_parties: int = 0
    extras: dict[str, str] = field(default_factory=dict, compare=False)  # new fields Valve may add

    # ----------------------------------------------------------- parsing --

    @classmethod
    def from_text(cls, text: str) -> "ConductSummary":
        raw = dict(_PAIR.findall(text))
        if not raw:
            raise InvalidFormatError("The text has no 'key: value' pairs.")

        for required in ("seq_num", "raw_behavior_score", "date"):
            if required not in raw:
                raise InvalidFormatError(f"Missing required field '{required}'.")

        known = {f.name for f in fields(cls)} - {"date", "extras"}
        values: dict = {}
        for name in known:
            if name in raw:
                values[name] = raw[name] if name == "behavior_rating" else _to_int(name, raw[name])

        values["date"] = datetime.fromtimestamp(_to_int("date", raw["date"]), tz=timezone.utc)
        values["extras"] = {k: v for k, v in raw.items() if k not in known and k != "date"}
        return cls(**values)

    # ----------------------------------------------------------- derived --

    @property
    def change(self) -> int | None:
        if self.old_raw_behavior_score is None:
            return None
        return self.raw_behavior_score - self.old_raw_behavior_score

    @property
    def rating_label(self) -> str:
        return RATINGS.get(self.behavior_rating, self.behavior_rating)

    def raw_fields(self) -> dict[str, object]:
        """Every field as Valve wrote it (except 'date'), including unknown ones."""
        data = {f.name: getattr(self, f.name) for f in fields(self) if f.name not in ("date", "extras")}
        data.update(self.extras)
        return data


def _to_int(name: str, value: str) -> int:
    try:
        return int(value)
    except ValueError:
        raise InvalidFormatError(f"Field '{name}' should be a number but got '{value}'.") from None
