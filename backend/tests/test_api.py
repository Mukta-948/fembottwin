from app import main
from app.main import app, Observation, PredictionRequest, add_observation, audit, create_prediction, health, list_observations, list_predictions
import app.database as database


def test_health_status_discloses_data_blocker(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "CGMacros_dateshifted365.zip.partial").write_bytes(b"partial")
    monkeypatch.setattr(main, "DATA_ROOT", raw)
    monkeypatch.setattr(main, "ARTIFACT_ROOT", tmp_path / "artifacts")
    assert any(route.path == "/api/health" and "GET" in route.methods for route in app.routes)
    result = health()
    assert result["status"] == "ok"
    assert "no provenance-verified CGMacros model" in result["model"]
    audit_result = audit()
    assert audit_result["data_status"] == "partial_archive"
    assert audit_result["archive_bytes"] == 7
    assert not audit_result["archive_sha256_verified"]
    assert "leakage_safeguards" in audit_result
    assert audit_result["evaluation"] is None


def test_prediction_outcome_updates_persisted_twin(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "twin.sqlite3")
    add_observation(Observation(glucose=100))
    add_observation(Observation(glucose=120))
    prediction = create_prediction(PredictionRequest())
    assert prediction["status"] == "baseline_fallback"
    assert prediction["source"] == "personal_baseline_fallback"
    assert prediction["cycle_fallback"] == "baseline_only; no cycle data"
    assert prediction["predicted_glucose"] == 110
    outcome = add_observation(Observation(glucose=130, prediction_id=prediction["prediction_id"]))
    assert outcome["prediction_outcome"]["absolute_error"] == 20
    assert outcome["state"]["prediction_outcomes"] == 1
    saved = list_predictions()
    assert saved["predictions"][0]["observed_glucose"] == 130
    history = list_observations()
    assert [row["glucose"] for row in history["observations"]] == [100, 120, 130]


def test_forecast_fallback_is_unavailable_without_personal_observations(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "empty.sqlite3")
    prediction = create_prediction(PredictionRequest())
    assert prediction["status"] == "unavailable"
    assert "two observations" in prediction["reason"]


def test_overview_forecast_status_requires_observations_for_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "overview-status.sqlite3")
    before = main.overview()["forecast_status"]
    assert before.startswith("unavailable")
    add_observation(Observation(glucose=100))
    add_observation(Observation(glucose=120))
    after = main.overview()["forecast_status"]
    assert after == "personal_mean_fallback_available; not_a_trained_model"


def test_synthetic_model_inference_is_test_labeled_and_persisted(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "model.sqlite3")

    class SyntheticTestModel:
        def predict(self, frame):
            return [132.5]

    label = "SYNTHETIC TEST ONLY — NOT CGMacros VALIDATION"
    monkeypatch.setattr(main, "load_trained_baseline", lambda: {
        "model": SyntheticTestModel(), "features": main.FEATURES,
        "dataset_label": label, "metrics": {"dataset_label": label},
    })
    features = {name: float(i + 1) for i, name in enumerate(main.FEATURES)}
    prediction = create_prediction(PredictionRequest(context={"model_features": features}))
    assert prediction["status"] == "synthetic_test_only"
    assert prediction["source"] == "synthetic_test_only"
    assert prediction["dataset_label"] == label
    assert prediction["confidence"] == "not_estimated"
    assert list_predictions()["predictions"][0]["source"] == "synthetic_test_only"


def test_missing_model_features_use_personal_mean_not_model_prediction(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "missing-features.sqlite3")
    add_observation(Observation(glucose=100))
    add_observation(Observation(glucose=120))

    class SyntheticTestModel:
        def predict(self, frame):
            raise AssertionError("model must not run with incomplete features")

    monkeypatch.setattr(main, "load_trained_baseline", lambda: {
        "model": SyntheticTestModel(), "features": main.FEATURES,
        "dataset_label": "SYNTHETIC TEST ONLY", "metrics": {},
    })
    prediction = create_prediction(PredictionRequest(context={"model_features": {"carbs_g": 30}}))
    assert prediction["status"] == "baseline_fallback"
    assert prediction["source"] == "personal_baseline_fallback"
    assert "inputs unavailable" in prediction["reason"]


def test_unverified_artifact_is_not_loaded_as_a_trained_model(tmp_path, monkeypatch):
    data_root = tmp_path / "raw"
    artifacts = tmp_path / "artifacts"
    data_root.mkdir()
    artifacts.mkdir()
    (artifacts / "baseline.joblib").write_bytes(b"test placeholder")
    (artifacts / "baseline_metrics.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(main, "DATA_ROOT", data_root)
    monkeypatch.setattr(main, "ARTIFACT_ROOT", artifacts)
    assert main.load_trained_baseline() is None


def test_model_inference_error_uses_labeled_personal_mean_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "inference-error.sqlite3")
    add_observation(Observation(glucose=100))
    add_observation(Observation(glucose=120))

    class FailingTestModel:
        def predict(self, frame):
            raise RuntimeError("test-only failure")

    monkeypatch.setattr(main, "load_trained_baseline", lambda: {
        "model": FailingTestModel(), "features": main.FEATURES,
        "dataset_label": "SYNTHETIC TEST ONLY", "metrics": {},
    })
    features = {name: float(i + 1) for i, name in enumerate(main.FEATURES)}
    prediction = create_prediction(PredictionRequest(context={"model_features": features}))
    assert prediction["status"] == "baseline_fallback"
    assert prediction["source"] == "personal_baseline_fallback"
    assert "inference failed" in prediction["reason"]


def test_synthetic_demo_is_separate_labeled_and_resettable(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "demo.sqlite3")

    def trained_model_must_not_load():
        raise AssertionError("synthetic demo must never load a trained artifact")

    monkeypatch.setattr(main, "load_trained_baseline", trained_model_must_not_load)
    add_observation(Observation(patient_id="default-patient", glucose=95))
    seeded = main.activate_synthetic_demo()
    demo_id = seeded["patient_id"]
    assert seeded["trained_model_disabled"] is True
    assert "SIMULATED SCENARIO" in seeded["label"]
    history = list_observations(patient_id=demo_id)["observations"]
    assert len(history) == 3
    assert all(row["context"]["simulation"] == "synthetic_demo_only" for row in history)

    what_if = main.what_if(main.WhatIfQuery(patient_id=demo_id, features={"carbs_g": 30.0}))
    assert what_if["status"] == "matched"
    assert what_if["match_count"] == 3
    assert "causal effects" in what_if["interpretation"]

    prediction = create_prediction(PredictionRequest(patient_id=demo_id))
    assert prediction["status"] == "baseline_fallback"
    assert prediction["source"] == "personal_baseline_fallback"
    assert prediction["scenario_label"] == seeded["label"]
    assert prediction["confidence"] == "not_estimated"

    reset = main.reset_synthetic_demo()
    assert reset["status"] == "reset"
    assert list_observations(patient_id=demo_id)["observations"] == []
    assert [row["glucose"] for row in list_observations(patient_id="default-patient")["observations"]] == [95]
    unavailable = create_prediction(PredictionRequest(patient_id=demo_id))
    assert unavailable["status"] == "unavailable"
    assert "SIMULATED SCENARIO" in unavailable["reason"]
    demo_routes = [route for route in app.routes if route.path == "/api/demo/scenario"]
    assert {method for route in demo_routes for method in route.methods} >= {"POST", "DELETE"}
