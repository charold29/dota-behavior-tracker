"""
Domain: rules about the behavior score itself.
"""
from __future__ import annotations

MIN_SCORE = 0
MAX_SCORE = 12000

# Behavior score needed for each feature, as shown in Dota's Player Behavior
# Summary (checked in-game, October 2026). Chat, voice and tipping depend on the
# communication score instead, which the latest_conduct file doesn't include.
BEHAVIOR_UNLOCKS = {
    3000: "Ranked",
    5000: "Pausing",
    7000: "Post-game drops",
    10000: "Coaching",  # also needs 10000 communication score
}


class InvalidScoreError(ValueError):
    """The score is outside the range Dota uses."""


def validate_score(score: int) -> int:
    if not MIN_SCORE <= score <= MAX_SCORE:
        raise InvalidScoreError(f"The behavior score must be between {MIN_SCORE} and {MAX_SCORE}, got {score}.")
    return score


def locked_features(score: int) -> dict[int, str]:
    """Features this score doesn't unlock yet, as {score needed: feature}."""
    return {needed: feature for needed, feature in BEHAVIOR_UNLOCKS.items() if score < needed}
