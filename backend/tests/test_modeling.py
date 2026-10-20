from pathlib import Path
import pandas as pd
import pytest
from app.modeling import FEATURES, inspect_dataset, prepare_postmeal_examples, train_baseline

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_cgmacros.csv"
SYNTHETIC_LABEL = "SYNTHETIC TEST FIXTURE ONLY — NOT REAL-DATA VALIDATION"


def prepare_fixture():
    frame = pd.read_csv(FIXTURE)
    return frame, prepare_postmeal_examples(frame, participant="participant_id", timestamp="timestamp",
        glucose="glucose_mg_dl", carbs="carbs_g", glucose_unit="mg/dL", carbs_unit="g")


def test_synthetic_fixture_preprocessing_is_past_only_and_links_future_target():
    raw, prepared = prepare_fixture()
    assert len(prepared) == 24
    assert (prepared["outcome_time"] > prepared["meal_time"]).all()
    assert set(FEATURES).issubset(prepared.columns)
    first = prepared.iloc[0]
    person_rows = raw[raw.participant_id == first.participant_id].copy()
    person_rows["timestamp"] = pd.to_datetime(person_rows.timestamp, utc=True)
    prior = person_rows.loc[(person_rows.timestamp < first.meal_time) & (person_rows.timestamp >= first.meal_time - pd.Timedelta(minutes=15)), "glucose_mg_dl"]
    assert first.premeal_glucose_mg_dl == prior.iloc[-1]


def test_training_interface_tags_synthetic_results_and_holds_out_people():
    _, prepared = prepare_fixture()
    result = train_baseline(prepared, dataset_label=SYNTHETIC_LABEL)
    assert result["status"] == "trained"
    assert result["metrics"]["dataset_label"] == SYNTHETIC_LABEL
    assert result["metrics"]["held_out_participants"] == 1
    assert result["metrics"]["train_participants"] == 3
    prediction = result["model"].predict(prepared[result["features"]].iloc[:2])
    assert prediction.shape == (2,)
    assert pd.Series(prediction).notna().all()


def test_missing_real_column_mapping_is_rejected():
    raw = pd.read_csv(FIXTURE)
    with pytest.raises(ValueError, match="Required mapped columns absent"):
        prepare_postmeal_examples(raw, participant="unknown_id", timestamp="timestamp", glucose="glucose_mg_dl",
                                  carbs="carbs_g", glucose_unit="mg/dL", carbs_unit="g")


def test_unknown_glucose_unit_is_rejected_instead_of_guessed():
    raw = pd.read_csv(FIXTURE)
    with pytest.raises(ValueError, match="Set glucose_unit explicitly"):
        prepare_postmeal_examples(raw, participant="participant_id", timestamp="timestamp", glucose="glucose_mg_dl",
                                  carbs="carbs_g", glucose_unit="unknown", carbs_unit="g")


def test_alternate_observed_mappings_missing_values_and_people_remain_separate():
    rows = []
    base = pd.Timestamp("2024-01-01T00:00:00Z")
    for person, values in (("a", [5.0] * 19), ("b", [10.0] * 19)):
        for i, glucose in enumerate(values):
            rows.append({"person": person, "recorded_at": (base + pd.Timedelta(minutes=5 * i)).isoformat(),
                         "Libre reading": glucose, "meal_carbohydrate": 0 if i != 6 else 30})
    rows[0]["Libre reading"] = None  # Missing glucose must not create or contaminate an event.
    rows[7]["meal_carbohydrate"] = None
    raw = pd.DataFrame(rows)
    prepared = prepare_postmeal_examples(raw, participant="person", timestamp="recorded_at", glucose="Libre reading",
        carbs="meal_carbohydrate", glucose_unit="mmol/L", carbs_unit="g")
    assert set(prepared.participant_id) == {"a", "b"}
    assert len(prepared) == 2
    assert prepared.loc[prepared.participant_id == "a", "target_glucose_mg_dl"].iloc[0] == pytest.approx(90.091)


def test_numeric_timestamps_are_not_silently_interpreted_as_nanoseconds():
    raw, _ = prepare_fixture()
    raw["timestamp"] = range(len(raw))
    with pytest.raises(ValueError, match="Numeric timestamps require a verified"):
        prepare_postmeal_examples(raw, participant="participant_id", timestamp="timestamp", glucose="glucose_mg_dl",
                                  carbs="carbs_g", glucose_unit="mg/dL", carbs_unit="g")


def test_inventory_reports_missing_values_for_synthetic_fixture_only():
    inventory = inspect_dataset(FIXTURE.parent)
    fixture = next(item for item in inventory["csvs"] if item["path"] == FIXTURE.name)
    assert fixture["rows"] > 0
    assert "participant_id" in fixture["columns"]
    assert fixture["missing_counts"]["carbs_g"] > 0
