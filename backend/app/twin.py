from math import sqrt
from typing import Any
import pandas as pd
from sklearn.preprocessing import StandardScaler

DEFAULT_STATE: dict[str, Any] = {
    "personal_glucose_baseline": None, "glucose_variability_sd": None,
    "meal_response_profiles": {}, "activity_response_profiles": {},
    "prediction_confidence": "insufficient_data", "cycle_confidence": "unavailable",
    "drift": "unknown", "observations": 0, "prediction_outcomes": 0,
    "mean_absolute_prediction_error": None,
}


def match_historical_meals(history: pd.DataFrame, query: dict[str, float], *, minimum_matches: int = 3, limit: int = 5) -> dict[str, Any]:
    """Match only caller-supplied numeric, non-identifying features; no match means no claim."""
    columns = list(query)
    if not columns or any(col not in history.columns for col in columns):
        return {"status": "insufficient_data", "match_count": 0, "matches": [], "reason": "No compatible feature set"}
    frame = history[columns].apply(pd.to_numeric, errors="coerce").dropna()
    if len(frame) < minimum_matches:
        return {"status": "insufficient_data", "match_count": len(frame), "matches": [], "reason": f"Need at least {minimum_matches} complete historical meals"}
    scaler = StandardScaler().fit(frame)
    distances = (((scaler.transform(frame) - scaler.transform(pd.DataFrame([query], columns=columns))[0]) ** 2).sum(axis=1)) ** .5
    chosen = frame.assign(_distance=distances).nsmallest(limit, "_distance")
    return {"status": "matched", "match_count": len(frame), "feature_names": columns,
            "matches": [{"history_index": int(index), "features": {c: float(row[c]) for c in columns}, "distance": float(row["_distance"])} for index, row in chosen.iterrows()]}


def update_state(state: dict[str, Any], glucose: float, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Online mean/variance update; context is retained as evidence, not causal attribution."""
    context = context or {}
    n = int(state.get("observations", 0))
    old_mean = state.get("personal_glucose_baseline")
    mean = glucose if old_mean is None else float(old_mean) + (glucose - float(old_mean)) / (n + 1)
    old_sd = state.get("glucose_variability_sd")
    old_var = 0.0 if old_sd is None else float(old_sd) ** 2
    # Welford update, storing only the sufficient statistic for a compact persistent state.
    m2 = float(state.get("_glucose_m2", old_var * max(n - 1, 0))) + ((glucose - (old_mean if old_mean is not None else glucose)) * (glucose - mean))
    state.update({"personal_glucose_baseline": mean, "observations": n + 1,
                  "_glucose_m2": m2,
                  "glucose_variability_sd": sqrt(m2 / n) if n else 0.0,
                  "prediction_confidence": "low" if n + 1 < 10 else "moderate"})
    for key in ("meal_type", "activity"):
        label = context.get(key)
        if label:
            profiles = state.setdefault("meal_response_profiles" if key == "meal_type" else "activity_response_profiles", {})
            old = profiles.get(str(label), {"count": 0, "mean_glucose": None})
            count = old["count"] + 1
            old_mean_profile = old["mean_glucose"]
            profiles[str(label)] = {"count": count, "mean_glucose": glucose if old_mean_profile is None else old_mean_profile + (glucose - old_mean_profile) / count}
    if context.get("cycle_phase"):
        state["cycle_confidence"] = "observed_label_only"
    return state
