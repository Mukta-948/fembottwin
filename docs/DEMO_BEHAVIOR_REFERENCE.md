# FemMetaboTwin demo behavior reference

This is a source-based guide for the screen recording. It records expected behavior from the current checkout; it does not claim browser interactions were manually exercised. Backend tests call the relevant functions and use temporary SQLite files. Run the app separately to confirm local runtime and browser connectivity.

## Navigation and visible controls

| UI item / action | Frontend behavior | API / backend path | Data effect and expected result | Limitation |
|---|---|---|---|---|
| Sidebar: **Overview** | Sets `view` to Overview. | On mount/ID change, `load()` requests `/api/overview`, `/api/observations`, and `/api/audit`. | Displays local state cards and shared dashboard sections. | Lower dashboard sections remain rendered when other nav options are selected. |
| **My Digital Twin** | Shows Twin route panel and recent-history list. | `GET /api/overview`, `GET /api/observations`; `overview()`, `list_observations()`. | Shows baseline, variability, count, and up to five most recent observations (history is ordered for display). | Descriptive local entries, not verified clinical history. |
| **Glucose Forecast** / **Generate glucose forecast** | `requestForecast()` posts current ID and context to predictions; renders status, value when available, reason, confidence/source. | `POST /api/predictions`; `create_prediction()`, `load_trained_baseline()`. | Trained inference only if eligible artifact and all expected finite features exist; otherwise personal-mean fallback or unavailable. A returned prediction is persisted. | Browser includes model features only with positive entered carbs and readings from the last 15 minutes. The current repo has no eligible real-data model. Uncertainty always says not estimated. |
| **Cycle Insights** | Shows the unavailable-state explanation. | `GET /api/overview`; response reports no cycle-linked T2D cohort. | No cycle prediction is produced. | No cycle-specific model or hormonal correction. mcPHASES remains separate and restricted. |
| **What-If Lab** / **Check historical matches** | Sends the entered carbohydrate value as the query feature. Displays status, complete match count, and returned analogs. | `POST /api/what-if`; `what_if()` → `match_historical_meals()`. | Uses unique complete meal responses for this patient ID; standardizes query/history numeric features with `StandardScaler`, ranks Euclidean distances, returns up to five closest records. Requires at least three complete matches. | Only historical similarity; not a predicted response, causal effect, or intervention comparison. UI currently exposes carbs only. |
| **Recommended Actions** | Focus panel explains guidance; the shared action card contains **Yes, helpful**. | `POST /api/feedback`; `add_feedback()`. | Stores fixed recommendation text and `helpful` response for current ID in SQLite; API returns `used_for_model_update: false`. | General educational prompt only. No medication advice, adaptive recommendation engine, or model update. |
| **Longitudinal Trends** | Renders `TrendChart` if at least two observations; otherwise shows count and requirement. | `GET /api/observations`; history is supplied to `TrendChart`. | Recharts area chart plots observed timestamps and entered glucose. | Local workspace records only; not cohort data or a forecast. |
| **Model & System Audit** | Shows dataset, archive, checksum, model/evaluation, interval/SHAP, safeguards, provenance, and limitations. | `GET /api/audit`; `audit()` checks local raw/artifact paths and metadata. | The current state should show no verified data/model metrics. | Audit checks the verification marker plus archive size; it does not re-hash the archive on every request. It is not an independent security audit. |
| Header **Patient / Clinician view** switch | Toggles role label; switching to Clinician also selects Model & System Audit. Switching back changes the label but leaves the current page selected. | No API call. | UI-only preview role. | No authentication, authorization, or access boundary. |
| Sidebar **Clinician preview** shortcut | Selects Model & System Audit; does not itself change the role label. | No API call. | Opens the audit panel. | Presentation shortcut only. |
| Header **Refresh** | Calls `load()`. | Same three GET calls as Overview. | Refreshes overview, history, and audit. | Failed requests set overview data to null; no detailed per-request error is rendered. |
| **System status**, **Explore twin**, **See data setup**, **Review limitations** | Selects Model & System Audit, My Digital Twin, Model & System Audit, or Cycle Insights respectively. | No API call at click time. | Navigational shortcuts to the matching panel. | They do not perform data setup or change model status. |
| Mobile menu | Toggles sidebar's `open` class; navigation closes it after selection. | None. | Responsive navigation only. | No data effect. |

## Observation entry and Twin update

The shared **Update your twin** form accepts glucose in mg/dL, optional meal ID, optional carbohydrate amount, and a **Mark complete meal response** checkbox. On submit, `submit()` sends `POST /api/observations` with the current patient ID, glucose, context and—if the last forecast returned a prediction ID—that prediction ID. Meal context is included only when meal ID, carbs, and the completion checkbox are all present. Otherwise the synthetic ID gets only the `synthetic_demo_only` marker; ordinary IDs receive an empty context.

`Observation.glucose` is constrained by Pydantic to strictly greater than 20 and strictly less than 600. The frontend's HTML min/max do not change those strict server bounds. `add_observation()` optionally links the reading to an existing prediction for the same ID, computes absolute error, updates the descriptive mean absolute prediction error, calls `update_state()`, persists state, and inserts the observation. If a supplied prediction ID does not belong to that ID, it returns 404. After success the frontend clears glucose, active prediction, and displayed forecast, shows a saved/outcome message, and reloads data.

`update_state()` maintains the arithmetic mean, Welford population standard deviation, observation count, and descriptive confidence label (`low` before ten records, `moderate` from ten). That confidence label is not prediction uncertainty. Drift becomes `review_pattern` when a new reading is more than two prior standard deviations from baseline, otherwise `within_personal_variability`; before five prior observations or usable variability, it is `insufficient_history`. Meal/activity profiles update only if those labels are in API context; the present form does not collect them. A supplied cycle label changes only the state label to `observed_label_only`.

## Synthetic demo load and reset semantics

**Load simulated demo** calls `POST /api/demo/scenario`. The backend uses the fixed ID `SIM-DEMO-FEM-001`, deletes this ID's existing rows from `observations`, `predictions`, `feedback`, and `patient_state`, then seeds exactly three observations:

| Relative time at activation | Glucose | Meal ID | Carbohydrates |
|---|---:|---|---:|
| about 28 hours earlier | 104.0 mg/dL | `SIM-MEAL-01` | 28 g |
| about 19 hours earlier | 139.0 mg/dL | `SIM-MEAL-02` | 42 g |
| about 4 hours earlier | 121.0 mg/dL | `SIM-MEAL-03` | 35 g |

Each context is marked `synthetic_demo_only` and `meal_response_complete: true`. The endpoint recomputes and persists Twin state. Frontend stores the synthetic ID in localStorage, selects it, clears prior forecast state, and shows the orange warning banner. The ID is explicitly barred from trained inference. Loading again is destructive only to prior records for this fixed synthetic ID; other IDs are preserved.

**Reset simulated demo** first asks for browser confirmation, then calls `DELETE /api/demo/scenario`. The backend deletes only the four table row groups listed above for `SIM-DEMO-FEM-001`. It preserves `demo-patient` and all other IDs. The frontend removes its saved synthetic ID, switches to `demo-patient`, clears forecast state, and displays a success message. A reset scenario has no observations, so prediction is unavailable until observations are added or the scenario is loaded again. Tests use temporary databases to confirm ID isolation; do not use reset on the default workspace.

## Prediction decision flow

1. `load_trained_baseline()` checks the archive's expected exact byte count, the `verified.sha256` marker, model and metrics files, matching pinned archive hash and expected feature names, a predict-capable model, a CGMacros dataset label, required metric fields, nonzero test rows and held-out participants, and finite MAE/RMSE. Failure or malformed artifacts return no model. The loader trusts the marker rather than recomputing the archive hash on each request; the download/extraction script is responsible for checksum verification.
2. `create_prediction()` disables the artifact path for `SIM-DEMO-FEM-001`. For other IDs it attempts trained inference only if every expected feature is supplied, numeric, finite, and not boolean. An inference exception or non-finite output cannot be returned as a trained prediction.
3. Successful eligible inference is stored with source `trained_cgmacros_model`, status `trained_model_prediction`, and `confidence: not_estimated`. Test doubles with a `SYNTHETIC` dataset label are returned as `synthetic_test_only`, never as real validation.
4. If trained inference cannot be served and the Twin has a baseline plus at least two observations, the API stores and returns `baseline_fallback` / `personal_baseline_fallback`. The UI labels it **PERSONAL-MEAN FALLBACK**, adds **SIMULATED** for the dedicated demo ID, and displays its reason. It is never labeled a trained prediction.
5. With neither a usable trained prediction nor two observations, the API returns `unavailable`, no numeric value, source `no_prediction`. Prediction uncertainty is not estimated for any current path.

## Data and model pipeline boundaries

The downloader pins the official CGMacros archive size and SHA-256, validates the ZIP, and extracts only after verification. The inventory utility reports observed files and candidate schemas; it does not make speculative mappings. Training requires explicit mapped participant, timestamp, glucose, and carbohydrate columns plus verified units and a path under the verified extraction. The feature builder forms a positive-carb meal event, uses strictly pre-meal observations in a 15-minute window, and seeks a future CGM target at 60 minutes within the configured 5-minute tolerance. The baseline trainer requires at least 20 examples and two participants, performs a deterministic 25% participant-group holdout with no participant overlap, and reports held-out MAE/RMSE plus premeal-glucose persistence MAE. This code is not evidence that data was downloaded, schema-inspected, or trained.

The app currently has no cycle model, calibrated intervals, SHAP explanation artifact, live signal integration, or clinical validation. The API returns a simulated-alert status field, but the current React screen does not display an operational alert workflow. Recommendations are fixed general guidance, and feedback does not train a model.

## Verification coverage and demo prerequisites

Backend tests cover direct API-function behavior including synthetic ID isolation and reset using temporary SQLite storage, state and outcome updates, forecast status/fallback, artifact eligibility/failure, and matching/pipeline safeguards. They are not browser end-to-end tests and do not validate clinical performance. The frontend production build verifies compilation, not runtime network connectivity. A live recording requires the local FastAPI and Vite servers, a reachable API at `127.0.0.1:8000`, and a browser at the Vite address. If the backend is stopped, interactions show an API-unavailable message; do not describe them as successful.
