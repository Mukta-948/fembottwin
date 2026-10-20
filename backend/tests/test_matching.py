import pandas as pd
from app.twin import match_historical_meals


def test_matching_falls_back_when_history_is_too_small():
    result = match_historical_meals(pd.DataFrame({"carbs": [20, 30]}), {"carbs": 25})
    assert result["status"] == "insufficient_data"
    assert result["match_count"] == 2


def test_matching_uses_standardized_features_and_returns_count():
    history = pd.DataFrame({"carbs": [20, 22, 24, 60], "fat": [4, 5, 3, 20]})
    result = match_historical_meals(history, {"carbs": 23, "fat": 4}, minimum_matches=3)
    assert result["status"] == "matched"
    assert result["match_count"] == 4
    assert len(result["matches"]) == 4
