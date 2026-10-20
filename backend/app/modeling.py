"""Schema-explicit, past-only post-meal glucose forecasting utilities."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

GLUCOSE_TO_MG_DL = {"mg/dL": 1.0, "mmol/L": 18.0182}
FEATURES = ["carbs_g", "premeal_glucose_mg_dl", "premeal_mean_mg_dl", "premeal_sd_mg_dl", "meal_hour_sin", "meal_hour_cos"]


def _csv_inventory(path: Path, root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path.relative_to(root)), "bytes": path.stat().st_size}
    try:
        columns = list(pd.read_csv(path, nrows=0).columns)
        result["columns"] = columns
        result["dtypes"] = {}
        result["missing_counts"] = {str(c): 0 for c in columns}
        id_candidates = [str(c) for c in columns if re.search(r"participant|subject|person|patient|(^|_)id($|_)", str(c), re.I)]
        time_candidates = [str(c) for c in columns if re.search(r"time|date|timestamp", str(c), re.I)]
        glucose_candidates = [str(c) for c in columns if re.search(r"glucose|\bcgm\b|blood.?sugar", str(c), re.I)]
        meal_candidates = [str(c) for c in columns if re.search(r"meal|food|carb|protein|fat|fiber|kcal|calor", str(c), re.I)]
        unique_ids: dict[str, set[str]] = {c: set() for c in id_candidates}
        time_stats = {c: {"valid": 0, "invalid_nonempty": 0, "min": None, "max": None} for c in time_candidates}
        rows = 0
        for chunk in pd.read_csv(path, chunksize=50_000, low_memory=False):
            rows += len(chunk)
            for col in columns:
                result["missing_counts"][str(col)] += int(chunk[col].isna().sum())
                result["dtypes"].setdefault(str(col), set()).add(str(chunk[col].dtype))
            for col in id_candidates:
                unique_ids[col].update(chunk[col].dropna().astype(str).unique().tolist())
            for col in time_candidates:
                values = chunk[col].dropna()
                # Numeric timestamps require dataset-specific units; report candidates without guessing.
                if pd.api.types.is_numeric_dtype(chunk[col]):
                    continue
                parsed = pd.to_datetime(values, errors="coerce", utc=True)
                valid = parsed.dropna()
                stat = time_stats[col]
                stat["valid"] += len(valid)
                stat["invalid_nonempty"] += int(parsed.isna().sum())
                if len(valid):
                    lo, hi = valid.min().isoformat(), valid.max().isoformat()
                    stat["min"] = min(filter(None, [stat["min"], lo]))
                    stat["max"] = max(filter(None, [stat["max"], hi]))
        result.update({"rows": rows, "candidate_identifier_columns": {c: {"unique_count": len(vals)} for c, vals in unique_ids.items()},
                       "candidate_timestamp_columns": time_stats, "candidate_glucose_columns": glucose_candidates,
                       "candidate_meal_columns": meal_candidates,
                       "explicit_units_in_glucose_headers": {c: re.findall(r"(?:mg\s*/\s*dL|mmol\s*/\s*L)", c, flags=re.I) for c in glucose_candidates},
                       "note": "Field-name candidates are not confirmed mappings; check the dataset dictionary. Numeric timestamps and units are not inferred."})
        result["dtypes"] = {k: sorted(v) for k, v in result["dtypes"].items()}
    except Exception as exc:
        result["inspection_error"] = f"{type(exc).__name__}: {exc}"
    return result


def inspect_dataset(root: Path) -> dict[str, Any]:
    root = root.resolve()
    files = sorted(path for path in root.rglob("*") if path.is_file()) if root.exists() else []
    return {"root": str(root), "files": [{"path": str(p.relative_to(root)), "bytes": p.stat().st_size,
                                          "kind": p.suffix.lower().lstrip(".") or "no_extension"} for p in files],
            "csvs": [_csv_inventory(p, root) for p in files if p.suffix.lower() == ".csv"],
            "license_or_provenance_files": [str(p.relative_to(root)) for p in files if re.search(r"license|readme|provenance|terms", p.name, re.I)]}


def inspect_csvs(root: Path) -> dict[str, Any]:
    """Compatibility wrapper retained for the initial inventory script."""
    return inspect_dataset(root)


def prepare_postmeal_examples(
    frame: pd.DataFrame, *, participant: str, timestamp: str, glucose: str, carbs: str,
    glucose_unit: str, carbs_unit: str, horizon_minutes: int = 60, target_tolerance_minutes: int = 5,
    premeal_window_minutes: int = 15, meal_gap_minutes: int = 30,
) -> pd.DataFrame:
    """Link positive-carb meal events to a future CGM point and strictly prior features.

    Column names and glucose units must be mapped from the release's actual dictionary.
    Missing carb values mean no recorded carb event; they are never interpolated.
    """
    if glucose_unit not in GLUCOSE_TO_MG_DL:
        raise ValueError("Set glucose_unit explicitly to 'mg/dL' or 'mmol/L' after verifying the data dictionary")
    if carbs_unit != "g":
        raise ValueError("Set carbs_unit explicitly to 'g' after verifying the data dictionary")
    required = [participant, timestamp, glucose, carbs]
    missing = [col for col in required if col not in frame.columns]
    if missing:
        raise ValueError(f"Required mapped columns absent: {missing}")
    df = frame[required].copy()
    # Numeric timestamps are ambiguous (seconds, milliseconds, Excel serials, etc.).
    # Refuse them until a dataset-specific, documented conversion is implemented.
    if pd.api.types.is_numeric_dtype(df[timestamp]):
        raise ValueError("Numeric timestamps require a verified dataset-specific unit mapping; timestamps are not guessed")
    df[timestamp] = pd.to_datetime(df[timestamp], errors="coerce", utc=True)
    df[glucose] = pd.to_numeric(df[glucose], errors="coerce") * GLUCOSE_TO_MG_DL[glucose_unit]
    df[carbs] = pd.to_numeric(df[carbs], errors="coerce")
    df = df.dropna(subset=[participant, timestamp, glucose]).sort_values([participant, timestamp])
    examples: list[dict[str, Any]] = []
    horizon = pd.Timedelta(minutes=horizon_minutes)
    tolerance = pd.Timedelta(minutes=target_tolerance_minutes)
    prior_window = pd.Timedelta(minutes=premeal_window_minutes)
    meal_gap = pd.Timedelta(minutes=meal_gap_minutes)
    for person, group in df.groupby(participant, sort=False):
        group = group.drop_duplicates(timestamp, keep="last").reset_index(drop=True)
        times = group[timestamp]
        carb_values = group[carbs]
        prev_time = times.shift(1)
        prev_carbs = carb_values.shift(1).fillna(0)
        new_episode = prev_time.isna() | ((times - prev_time) > meal_gap) | (prev_carbs <= 0)
        meal_indices = group.index[(carb_values > 0) & new_episode]
        for idx in meal_indices:
            meal = group.iloc[idx]
            meal_time = meal[timestamp]
            prior = group.loc[(times < meal_time) & (times >= meal_time - prior_window), glucose].dropna()
            if prior.empty:
                continue
            target_time = meal_time + horizon
            target_idx = int(times.searchsorted(target_time, side="right") - 1)
            if target_idx < 0:
                continue
            observed = group.iloc[target_idx]
            observed_time = observed[timestamp]
            if observed_time <= meal_time or target_time - observed_time > tolerance:
                continue
            hour = meal_time.hour + meal_time.minute / 60.0
            examples.append({"participant_id": person, "meal_time": meal_time, "outcome_time": observed_time,
                             "target_glucose_mg_dl": float(observed[glucose]), "carbs_g": float(meal[carbs]),
                             "premeal_glucose_mg_dl": float(prior.iloc[-1]), "premeal_mean_mg_dl": float(prior.mean()),
                             "premeal_sd_mg_dl": float(prior.std(ddof=0)) if len(prior) > 1 else 0.0,
                             "meal_hour_sin": float(np.sin(2 * np.pi * hour / 24)),
                             "meal_hour_cos": float(np.cos(2 * np.pi * hour / 24))})
    return pd.DataFrame(examples, columns=["participant_id", "meal_time", "outcome_time", "target_glucose_mg_dl", *FEATURES])


def train_baseline(examples: pd.DataFrame, *, dataset_label: str, random_state: int = 42) -> dict[str, Any]:
    """Train with a participant-group holdout; all features are prepared from pre-meal data."""
    required = ["participant_id", "meal_time", "outcome_time", "target_glucose_mg_dl", *FEATURES]
    missing = [col for col in required if col not in examples.columns]
    if missing:
        raise ValueError(f"Required prepared fields absent: {missing}")
    if not dataset_label.strip():
        raise ValueError("dataset_label is required so metrics retain their provenance")
    df = examples.dropna(subset=required).copy().sort_values(["participant_id", "meal_time"])
    if (pd.to_datetime(df["outcome_time"]) <= pd.to_datetime(df["meal_time"])).any():
        raise ValueError("Leakage check failed: outcome time must follow the meal time")
    if df["participant_id"].nunique() < 2 or len(df) < 20:
        raise ValueError("Need at least 20 prepared meal events from at least two participants")
    groups = df["participant_id"]
    train_idx, test_idx = next(GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=random_state).split(df[FEATURES], df["target_glucose_mg_dl"], groups=groups))
    train_people = set(groups.iloc[train_idx])
    test_people = set(groups.iloc[test_idx])
    if train_people & test_people:
        raise RuntimeError("Participant leakage detected between training and evaluation sets")
    model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), HistGradientBoostingRegressor(max_iter=100, random_state=random_state))
    model.fit(df.iloc[train_idx][FEATURES], df.iloc[train_idx]["target_glucose_mg_dl"])
    prediction = model.predict(df.iloc[test_idx][FEATURES])
    truth = df.iloc[test_idx]["target_glucose_mg_dl"]
    persistence = df.iloc[test_idx]["premeal_glucose_mg_dl"]
    return {"model": model, "features": FEATURES, "status": "trained", "metrics": {
        "mae_mg_dl": float(mean_absolute_error(truth, prediction)),
        "rmse_mg_dl": float(mean_squared_error(truth, prediction) ** 0.5),
        "persistence_mae_mg_dl": float(mean_absolute_error(truth, persistence)),
        "test_rows": len(test_idx), "held_out_participants": int(len(test_people)),
        "train_participants": int(len(train_people)), "horizon_minutes": int(round((pd.to_datetime(df.iloc[test_idx]["outcome_time"]) - pd.to_datetime(df.iloc[test_idx]["meal_time"])).dt.total_seconds().median() / 60)),
        "split": "one deterministic participant-group holdout", "target_unit": "mg/dL",
        "dataset_label": dataset_label,
        "feature_timing": "at meal time and strictly before meal time; target is future CGM",
    }}
