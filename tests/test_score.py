import pytest

from dota_behavior_tracker.domain.score import InvalidScoreError, locked_features, validate_score


# -------------------------------------------------------- validate_score --

@pytest.mark.parametrize("score", [0, 7843, 12000])
def test_scores_in_range_are_valid(score):
    assert validate_score(score) == score


@pytest.mark.parametrize("score", [-1, 12001, 99999])
def test_scores_out_of_range_are_rejected(score):
    with pytest.raises(InvalidScoreError, match="between 0 and 12000"):
        validate_score(score)


# ------------------------------------------------------- locked_features --

@pytest.mark.parametrize("score, locked", [
    (0, ["Ranked", "Pausing", "Post-game drops", "Coaching"]),
    (2999, ["Ranked", "Pausing", "Post-game drops", "Coaching"]),
    (3000, ["Pausing", "Post-game drops", "Coaching"]),   # the threshold itself unlocks it
    (5000, ["Post-game drops", "Coaching"]),
    (7843, ["Coaching"]),
    (9999, ["Coaching"]),
    (10000, []),
    (12000, []),
])
def test_locked_features(score, locked):
    assert list(locked_features(score).values()) == locked


def test_locked_features_include_the_score_needed():
    assert locked_features(7843) == {10000: "Coaching"}
