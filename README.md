# FemMetaboTwin

FemMetaboTwin is a hackathon research prototype exploring a personalized glucose-state twin for people with Type 2 diabetes, with menstrual-cycle effects treated as an open research question. It is not a medical device and does not provide diagnosis, treatment, or medication advice.

## Intended users and implemented features

The prototype is for patient-facing self-observation demonstrations and clinician-facing review of the same local workspace. It includes:

- Persistent glucose observations and Patient State Vector updates in local SQLite (personal mean, variability, observation count, and prediction outcome feedback).
- Patient overview, Twin history, longitudinal chart, forecast status, historical meal matching, general non-medication guidance, and a clinician/demo audit view.
- A trained-model eligibility gate requiring the pinned CGMacros archive provenance, matching feature metadata, and recorded held-out evaluation evidence. No such real-data model exists in this checkout.
- Honest prediction outcomes: a trained prediction only when an eligible artifact and complete inputs are present; a labeled personal-mean estimate after at least two readings; otherwise unavailable. Uncertainty is **not estimated**.
- A deterministic synthetic demonstration under a separate fictional ID. It is labeled in the UI, stored separately, excluded from training, and never sent to a trained model.
- What-If matching against at least three complete historical meal responses. Matches are historical analogs, not causal effects.

## Verified stack and data flow

React 18, Vite, custom responsive CSS, Recharts, FastAPI, Pydantic, pandas, scikit-learn, joblib, and SQLite. Patient-entered observations flow through React to FastAPI and SQLite; the API updates the Twin and selects only an evidence-eligible model, personal-mean fallback, or unavailable result. Clinician view is a demo role switch, not authentication or access control. See [architecture source](docs/ARCHITECTURE.md) and [SVG diagram](docs/architecture.svg).

## Run locally

Use two PowerShell terminals from the project root.

**Terminal 1 — backend:**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Terminal 2 — frontend:**

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. SQLite is created under `artifacts/` and remains local. To verify the backend, run `cd backend; .\.venv\Scripts\Activate.ps1; pytest`. To build the frontend, run `cd frontend; npm run build`.

## Demonstrate the synthetic scenario

1. Start both services and open the site.
2. Select **Load simulated demo**. The app seeds three deterministic illustrative observations for fictional ID `SIM-DEMO-FEM-001` in a separate SQLite namespace.
3. Keep the persistent **SIMULATED SCENARIO — NOT REAL PATIENT DATA** banner visible. Show the overview, Twin history, forecast page, What-If Lab, Longitudinal Trends, then toggle to Clinician view and open Model & System Audit.
4. Generate a forecast: because the demo cannot use a trained artifact, it shows an explicitly simulated personal-mean fallback. Uncertainty remains “not estimated.” The three complete meal records support an illustrative historical-match display only.
5. Choose **Reset simulated demo** and confirm. Only the synthetic ID’s observations, predictions, feedback, and state are cleared; the default workspace is preserved.

Do not describe this scenario as patient evidence, training data, model validation, or clinical performance. Manual observations are local user entries; identify them as demo input if used in a presentation.

## Data provenance and licensing

No complete verified CGMacros archive, extracted data, real schema inventory, trained real-data model, or held-out metrics are present. The official PhysioNet CGMacros release is CC BY-NC-SA 4.0; follow its attribution, non-commercial, and share-alike terms. The partial archive is not data and must not be extracted. See [data provenance](docs/DATA_PROVENANCE.md). mcPHASES is restricted, is a separate cohort, and is not pooled with CGMacros.

The code is under the [MIT License](LICENSE). The code license does not change the separate terms for third-party datasets.

## Reproducible data pipeline (blocked pending verified data)

Only after obtaining the official archive through the documented procedure, verifying its exact size and SHA-256, and extracting it with the repository script, inventory the actual files:

```powershell
cd backend
$env:PYTHONPATH = (Get-Location).Path
python scripts/inspect_data.py
```

Inspect the resulting inventory and data dictionary before selecting exact participant, timestamp, glucose, and meal-carbohydrate mappings. Then use `python scripts/train_baseline.py --help` and pass only observed columns and verified units. The CLI refuses paths outside the verified CGMacros extraction. Evaluation holds out participant groups and uses future glucose only as target. Never pass synthetic fixtures or mix cohorts. No results can be reproduced until authorized real observations are available.

## Limitations and future work

- No real-data training, genuine held-out MAE/RMSE, or clinical validation; no actual local CGMacros schema has been observed.
- The personal mean is a simple fallback, not a trained prediction. Prediction confidence/uncertainty is not estimated; there are no calibrated quantiles or SHAP artifacts.
- CGMacros has no menstrual-cycle measurements. mcPHASES requires restricted access and is not a Type 2 diabetes validation cohort. No cycle correction or cycle-aware prediction is implemented.
- Local role switching is not authentication. There is no device integration, emergency response, production privacy/security review, or operational alerting. Alert behavior is labeled simulated/unconnected.
- What-If results are historical similarity matches, not causal effects. Recommendations are general education; medication changes are out of scope.

Future work: obtain authorized data, inspect actual schemas, pre-register the target and exclusions, train only on real data with participant-aware/time-safe evaluation, evaluate calibration, and seek appropriate clinical and privacy review before any care-facing use.

## Submission materials

- Team details: **[Add team name, contributor names and roles, and contact details; not supplied yet]**

- [Architecture and data flow](docs/ARCHITECTURE.md) plus [exportable SVG](docs/architecture.svg)
- [10-slide presentation outline](docs/PRESENTATION.md)
- [21–22 minute demo script](docs/DEMO_SCRIPT.md)
- [Data provenance and access restrictions](docs/DATA_PROVENANCE.md)
