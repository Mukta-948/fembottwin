from pathlib import Path
import pandas as pd
from app.twin import DEFAULT_STATE, update_state


def test_state_updates_mean_variability_and_context():
    state = update_state(DEFAULT_STATE.copy(), 100, {"meal_type": "breakfast", "cycle_phase": "user_reported_luteal"})
    state = update_state(state, 120, {"meal_type": "breakfast"})
    assert state["personal_glucose_baseline"] == 110
    assert state["observations"] == 2
    assert state["meal_response_profiles"]["breakfast"]["count"] == 2
    assert state["cycle_confidence"] == "observed_label_only"


def test_synthetic_fixture_can_drive_patient_state_update():
    fixture = Path(__file__).parent / "fixtures" / "synthetic_cgmacros.csv"
    rows = pd.read_csv(fixture).head(2)
    state = DEFAULT_STATE.copy()
    for _, row in rows.iterrows():
        state = update_state(state, float(row.glucose_mg_dl), {"source": "synthetic_test_fixture_only"})
    assert state["observations"] == 2
    assert state["prediction_confidence"] == "low"
