from datetime import datetime, timedelta, timezone
from typing import Any
import json
import math
from pathlib import Path
from uuid import uuid4
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .database import connect, get_state, save_state
from .modeling import FEATURES
from .twin import DEFAULT_STATE, match_historical_meals, update_state

app = FastAPI(title="FemMetaboTwin", version="0.1.0", description="Research PoC; not a medical device or treatment recommendation")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "raw" / "cgmacros"
ARTIFACT_ROOT = PROJECT_ROOT / "artifacts"
EXPECTED_ARCHIVE_BYTES = 657187340
EXPECTED_ARCHIVE_SHA256 = "05c8b0e6f1a2757050aced55ce4bf6ab2ac9b30f2fd8ca193056812d9c621d4d"
SYNTHETIC_DEMO_PATIENT_ID = "SIM-DEMO-FEM-001"
SYNTHETIC_DEMO_LABEL = "SIMULATED SCENARIO — NOT REAL PATIENT DATA"


class Observation(BaseModel):
    patient_id: str = "demo-patient"
    glucose: float = Field(gt=20, lt=600)
    observed_at: datetime | None = None
    context: dict[str, Any] = {}
    prediction_id: str | None = None


class PredictionRequest(BaseModel):
    patient_id: str = "demo-patient"
    context: dict[str, Any] = {}


class Feedback(BaseModel):
    patient_id: str = "demo-patient"
    recommendation: str
    response: str


class WhatIfQuery(BaseModel):
    patient_id: str = "demo-patient"
    features: dict[str, float]


def load_trained_baseline():
    """Load only artifacts tied to the locally verified CGMacros release."""
    archive = DATA_ROOT / "CGMacros_dateshifted365.zip"
    marker = DATA_ROOT / "verified.sha256"
    metrics_path = ARTIFACT_ROOT / "baseline_metrics.json"
    model_path = ARTIFACT_ROOT / "baseline.joblib"
    try:
        if not (archive.is_file() and archive.stat().st_size == EXPECTED_ARCHIVE_BYTES and marker.is_file()
                and marker.read_text(encoding="utf-8").strip().lower() == EXPECTED_ARCHIVE_SHA256
                and metrics_path.is_file() and model_path.is_file()):
            return None
        metadata = json.loads(metrics_path.read_text(encoding="utf-8"))
        if metadata.get("archive_sha256") != EXPECTED_ARCHIVE_SHA256 or metadata.get("features") != FEATURES:
            return None
        artifact = joblib.load(model_path)
        if artifact.get("archive_sha256") != EXPECTED_ARCHIVE_SHA256 or artifact.get("features") != FEATURES:
            return None
        if not hasattr(artifact.get("model"), "predict"):
            return None
        metrics = metadata.get("metrics") or {}
        required_metrics = ("mae_mg_dl", "rmse_mg_dl", "test_rows", "held_out_participants", "dataset_label")
        if any(key not in metrics for key in required_metrics):
            return None
        if int(metrics["test_rows"]) < 1 or int(metrics["held_out_participants"]) < 1:
            return None
        if not all(math.isfinite(float(metrics[key])) for key in ("mae_mg_dl", "rmse_mg_dl")):
            return None
        dataset_label = metrics.get("dataset_label")
        if not isinstance(dataset_label, str) or not dataset_label.startswith("CGMacros PhysioNet v1.0.0"):
            return None
        return {"model": artifact["model"], "features": FEATURES, "metrics": metrics, "dataset_label": dataset_label}
    except Exception:
        # Missing, malformed, or unreadable artifacts must fall back safely.
        return None


@app.get("/api/health")
def health():
    artifact = load_trained_baseline()
    return {"status": "ok", "model": "verified CGMacros model available" if artifact else "no provenance-verified CGMacros model available", "cycle_model": "unavailable without cycle-linked T2D data"}


@app.get("/api/overview")
def overview(patient_id: str = "demo-patient"):
    state = get_state(patient_id) or DEFAULT_STATE.copy()
    artifact = load_trained_baseline()
    if artifact:
        forecast_status = "verified_model_ready_when_complete_inputs_are_supplied"
    elif state.get("personal_glucose_baseline") is not None and int(state.get("observations", 0)) >= 2:
        forecast_status = "personal_mean_fallback_available; not_a_trained_model"
    else:
        forecast_status = "unavailable; no_verified_model_or_sufficient_observations"
    return {"patient_id": patient_id, "state": state, "forecast": None, "forecast_status": forecast_status, "cycle_insights": {"status": "unavailable", "reason": "CGMacros has no cycle data; mcPHASES is a separate restricted dataset and is not a T2D cohort"}, "what_if": {"status": "insufficient_data", "match_count": 0}, "recommendations": [{"text": "Review your personal glucose patterns with your care team.", "basis": "General educational guidance; no patient-specific causal evidence.", "medication_change": False}], "alerts": {"simulated": True, "status": "no live signals", "message": "Demo workflow only; not connected to devices or emergency services."}}


@app.post("/api/predictions")
def create_prediction(request: PredictionRequest):
    """Use a provenance-checked model when complete features exist; otherwise label the mean fallback."""
    state = get_state(request.patient_id) or DEFAULT_STATE.copy()
    simulated_demo = request.patient_id == SYNTHETIC_DEMO_PATIENT_ID
    artifact = None if simulated_demo else load_trained_baseline()
    model_features = request.context.get("model_features")
    missing_features: list[str] = []
    numeric_features: dict[str, float] = {}
    model_failure: str | None = None
    if artifact:
        if not isinstance(model_features, dict):
            missing_features = list(artifact["features"])
        else:
            missing_features = [key for key in artifact["features"] if key not in model_features]
            for key in artifact["features"]:
                if key not in model_features:
                    continue
                value = model_features[key]
                try:
                    number = float(value)
                except (TypeError, ValueError):
                    missing_features.append(key)
                    continue
                if isinstance(value, bool) or not math.isfinite(number):
                    missing_features.append(key)
                    continue
                numeric_features[key] = number
        if not missing_features:
            try:
                prediction_value = float(artifact["model"].predict(pd.DataFrame([[numeric_features[key] for key in artifact["features"]]], columns=artifact["features"]))[0])
            except Exception as exc:
                model_failure = f"Verified model inference failed ({type(exc).__name__})."
            if model_failure is None and not math.isfinite(prediction_value):
                model_failure = "Verified model returned a non-finite value."
            if model_failure is None:
                prediction_id = str(uuid4())
                dataset_label = artifact["dataset_label"]
                synthetic_test_only = dataset_label.upper().startswith("SYNTHETIC")
                source = "synthetic_test_only" if synthetic_test_only else "trained_cgmacros_model"
                status = "synthetic_test_only" if synthetic_test_only else "trained_model_prediction"
                with connect() as db:
                    db.execute("INSERT INTO predictions(prediction_id,patient_id,predicted_glucose,source,context_json) VALUES(?,?,?,?,?)",
                               (prediction_id, request.patient_id, prediction_value, source, json.dumps(request.context)))
                    db.commit()
                return {"status": status, "prediction_id": prediction_id, "predicted_glucose": prediction_value,
                        "unit": "mg/dL", "source": source, "confidence": "not_estimated",
                        "dataset_label": dataset_label, "evaluation": artifact["metrics"],
                        "reason": ("Synthetic test double; not a real prediction or validation." if synthetic_test_only
                                   else "Verified CGMacros baseline; uncertainty is not calibrated."),
                        "cycle_fallback": "baseline_only; no cycle data"}
    enough_observations = state.get("personal_glucose_baseline") is not None and int(state.get("observations", 0)) >= 2
    if not enough_observations:
        reason = "Log at least two observations before the personal-mean fallback can be calculated."
        if simulated_demo:
            reason = f"{SYNTHETIC_DEMO_LABEL}. {reason}"
        if artifact:
            if missing_features:
                reason += f" Trained model inputs are missing or invalid: {', '.join(sorted(set(missing_features)))}."
            if model_failure:
                reason += f" {model_failure}"
        else:
            reason += " No provenance-verified trained model is available."
        return {"status": "unavailable", "reason": reason, "source": "no_prediction", "cycle_fallback": "baseline_only; no cycle data"}
    prediction_id = str(uuid4())
    predicted = float(state["personal_glucose_baseline"])
    with connect() as db:
        db.execute("INSERT INTO predictions(prediction_id,patient_id,predicted_glucose,source,context_json) VALUES(?,?,?,?,?)",
                   (prediction_id, request.patient_id, predicted, "personal_baseline_fallback", json.dumps(request.context)))
        db.commit()
    return {"status": "baseline_fallback", "prediction_id": prediction_id, "predicted_glucose": predicted,
            "unit": "mg/dL (user-entered observations assumed)", "source": "personal_baseline_fallback",
            "confidence": "not_estimated",
            "scenario_label": SYNTHETIC_DEMO_LABEL if simulated_demo else None,
            "reason": (f"{SYNTHETIC_DEMO_LABEL}. Illustrative personal-mean estimate; not a real patient estimate."
                       if simulated_demo else f"Trained model inputs unavailable: {', '.join(sorted(set(missing_features)))}; using personal mean."
                       if artifact and missing_features else model_failure + " Using personal mean." if model_failure
                       else "No provenance-verified trained model available; using personal mean."),
            "cycle_fallback": "baseline_only; no cycle data"}


@app.post("/api/observations")
def add_observation(obs: Observation):
    state = get_state(obs.patient_id) or DEFAULT_STATE.copy()
    old_baseline = state.get("personal_glucose_baseline")
    old_count = int(state.get("observations", 0))
    old_sd = state.get("glucose_variability_sd")
    prediction_outcome = None
    if obs.prediction_id:
        with connect() as db:
            prediction = db.execute("SELECT predicted_glucose FROM predictions WHERE prediction_id=? AND patient_id=?", (obs.prediction_id, obs.patient_id)).fetchone()
            if prediction is None:
                raise HTTPException(status_code=404, detail="Prediction not found for this patient")
            predicted = float(prediction[0])
            absolute_error = abs(float(obs.glucose) - predicted)
            db.execute("UPDATE predictions SET observed_glucose=?,absolute_error=? WHERE prediction_id=?", (float(obs.glucose), absolute_error, obs.prediction_id))
            prediction_outcome = {"prediction_id": obs.prediction_id, "predicted_glucose": predicted, "observed_glucose": float(obs.glucose), "absolute_error": absolute_error}
    state = update_state(state, obs.glucose, obs.context)
    if old_count < 5 or old_baseline is None or old_sd is None or float(old_sd) <= 0:
        state["drift"] = "insufficient_history"
    else:
        state["drift"] = "review_pattern" if abs(float(obs.glucose) - float(old_baseline)) > 2 * float(old_sd) else "within_personal_variability"
    if prediction_outcome:
        outcome_count = int(state.get("prediction_outcomes", 0))
        previous_mae = state.get("mean_absolute_prediction_error")
        state["prediction_outcomes"] = outcome_count + 1
        state["mean_absolute_prediction_error"] = prediction_outcome["absolute_error"] if previous_mae is None else float(previous_mae) + (prediction_outcome["absolute_error"] - float(previous_mae)) / (outcome_count + 1)
    save_state(obs.patient_id, state)
    with connect() as db:
        db.execute("INSERT INTO observations(patient_id,observed_at,glucose,context_json,prediction_id) VALUES(?,?,?,?,?)", (obs.patient_id, (obs.observed_at or datetime.now(timezone.utc)).isoformat(), obs.glucose, json.dumps(obs.context), obs.prediction_id))
        db.commit()
    return {"state": state, "status": "updated", "prediction_outcome": prediction_outcome}


@app.get("/api/predictions")
def list_predictions(patient_id: str = "demo-patient", limit: int = 100):
    with connect() as db:
        rows = db.execute("SELECT prediction_id,created_at,predicted_glucose,source,observed_glucose,absolute_error FROM predictions WHERE patient_id=? ORDER BY created_at DESC LIMIT ?", (patient_id, min(max(limit, 1), 500))).fetchall()
    return {"predictions": [dict(row) for row in rows]}


@app.get("/api/observations")
def list_observations(patient_id: str = "demo-patient", limit: int = 100):
    with connect() as db:
        rows = db.execute("SELECT observed_at,glucose,context_json FROM observations WHERE patient_id=? ORDER BY observed_at DESC LIMIT ?", (patient_id, min(max(limit, 1), 500))).fetchall()
    return {"observations": [{"observed_at": row[0], "glucose": row[1], "context": __import__("json").loads(row[2])} for row in reversed(rows)]}


@app.post("/api/feedback")
def add_feedback(feedback: Feedback):
    with connect() as db:
        db.execute("INSERT INTO feedback(patient_id,recommendation,response) VALUES(?,?,?)", (feedback.patient_id, feedback.recommendation, feedback.response))
        db.commit()
    return {"status": "recorded", "used_for_model_update": False}


@app.post("/api/demo/scenario")
def activate_synthetic_demo():
    """Reset and seed only the isolated, fictional synthetic demo patient."""
    patient_id = SYNTHETIC_DEMO_PATIENT_ID
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    samples = [
        (now - timedelta(hours=28), 104.0, "SIM-MEAL-01", 28.0),
        (now - timedelta(hours=19), 139.0, "SIM-MEAL-02", 42.0),
        (now - timedelta(hours=4), 121.0, "SIM-MEAL-03", 35.0),
    ]
    state = DEFAULT_STATE.copy()
    with connect() as db:
        for table in ("observations", "predictions", "feedback", "patient_state"):
            db.execute(f"DELETE FROM {table} WHERE patient_id=?", (patient_id,))
        for observed_at, glucose, meal_id, carbs in samples:
            context = {"simulation": "synthetic_demo_only", "meal_id": meal_id,
                       "meal_features": {"carbs_g": carbs}, "meal_response_complete": True}
            state = update_state(state, glucose, context)
            db.execute("INSERT INTO observations(patient_id,observed_at,glucose,context_json) VALUES(?,?,?,?)",
                       (patient_id, observed_at.isoformat(), glucose, json.dumps(context)))
        db.commit()
    save_state(patient_id, state)
    return {"status": "seeded", "patient_id": patient_id, "label": SYNTHETIC_DEMO_LABEL,
            "observation_count": len(samples), "trained_model_disabled": True}


@app.delete("/api/demo/scenario")
def reset_synthetic_demo():
    """Clear only demo-owned rows; genuine/default workspace rows are preserved."""
    with connect() as db:
        for table in ("observations", "predictions", "feedback", "patient_state"):
            db.execute(f"DELETE FROM {table} WHERE patient_id=?", (SYNTHETIC_DEMO_PATIENT_ID,))
        db.commit()
    return {"status": "reset", "patient_id": SYNTHETIC_DEMO_PATIENT_ID,
            "label": SYNTHETIC_DEMO_LABEL}


@app.get("/api/audit")
def audit():
    archive = DATA_ROOT / "CGMacros_dateshifted365.zip"
    partial = DATA_ROOT / "CGMacros_dateshifted365.zip.partial"
    extracted = DATA_ROOT / "extracted"
    marker = DATA_ROOT / "verified.sha256"
    csv_files = list(extracted.rglob("*.csv")) if extracted.is_dir() else []
    checksum_verified = marker.is_file() and marker.read_text(encoding="utf-8").strip().lower() == EXPECTED_ARCHIVE_SHA256 and archive.is_file() and archive.stat().st_size == EXPECTED_ARCHIVE_BYTES
    if csv_files and checksum_verified:
        data_status = "extracted"
    elif csv_files:
        data_status = "extracted_unverified"
    elif checksum_verified:
        data_status = "archive_verified_not_extracted"
    elif partial.is_file():
        data_status = "partial_archive"
    elif archive.is_file():
        data_status = "archive_unverified"
    else:
        data_status = "not_installed"

    metrics_path = ARTIFACT_ROOT / "baseline_metrics.json"
    model_path = ARTIFACT_ROOT / "baseline.joblib"
    archive_for_size = archive if archive.is_file() else partial
    evaluation = None
    model_status = "not_trained"
    if model_path.is_file() or metrics_path.is_file():
        artifact = load_trained_baseline()
        if artifact:
            evaluation = artifact["metrics"]
            model_status = "trained_artifact"
        else:
            model_status = "artifact_unverified_or_incomplete"
    return {
        "data_status": data_status,
        "archive_bytes": archive_for_size.stat().st_size if archive_for_size.is_file() else 0,
        "expected_archive_bytes": EXPECTED_ARCHIVE_BYTES,
        "archive_sha256_verified": checksum_verified,
        "extracted_csv_count": len(csv_files),
        "model_status": model_status,
        "evaluation": evaluation,
        "quantiles": "not available; no calibrated interval model",
        "shap": "not available; no explanation artifact",
        "leakage_safeguards": ["explicit column and unit mappings required", "feature windows end before meal time", "target reading must follow the meal and meet horizon tolerance", "participant groups are held out and checked for overlap"],
        "cycle_component": "unavailable; no cycle-linked T2D cohort",
        "synthetic_scenarios": "isolated demo available; labeled synthetic data is barred from model inference and training",
        "provenance": "docs/DATA_PROVENANCE.md; official PhysioNet CGMacros v1.0.0",
        "limitations": ["not clinical validation", "no mcPHASES pooling", "no medication recommendations", "user-entered glucose unit is assumed mg/dL in the local Twin"],
    }


@app.post("/api/what-if")
def what_if(query: WhatIfQuery):
    with connect() as db:
        rows = db.execute("SELECT observed_at,glucose,context_json FROM observations WHERE patient_id=? ORDER BY observed_at DESC", (query.patient_id,)).fetchall()
    history = []
    seen_meals = set()
    for row in rows:
        context = json.loads(row["context_json"])
        meal_id = context.get("meal_id")
        meal_features = context.get("meal_features")
        if not meal_id or context.get("meal_response_complete") is not True or not isinstance(meal_features, dict) or meal_id in seen_meals:
            continue
        if not set(query.features).issubset(meal_features):
            continue
        try:
            features = {key: float(meal_features[key]) for key in query.features}
        except (TypeError, ValueError):
            continue
        history.append({"meal_id": str(meal_id), "observed_at": row["observed_at"], "observed_glucose": float(row["glucose"]), **features})
        seen_meals.add(meal_id)
    if not history:
        return {"status": "insufficient_data", "match_count": 0, "matches": [], "reason": "No complete historical meal responses with matching feature fields are logged."}
    frame = pd.DataFrame(history)
    result = match_historical_meals(frame, query.features)
    if result["status"] != "matched":
        return result
    enriched = []
    for match in result["matches"]:
        old = frame.iloc[match.pop("history_index")]
        enriched.append({**match, "meal_id": old["meal_id"], "observed_at": old["observed_at"], "observed_glucose_mg_dl": old["observed_glucose"]})
    result["matches"] = enriched
    result["interpretation"] = "Historical analogs only; observed values are not predicted outcomes or causal effects."
    return result
