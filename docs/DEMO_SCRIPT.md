# FemMetaboTwin: 21½-minute submission demonstration

This script uses the app’s deterministic isolated synthetic scenario. It contains **no real participant records**. Do not imply that the scenario or tests validate clinical performance. If a control is unavailable during the live run, state that and show the corresponding audit or test evidence; do not invent results.

## Before the room (not part of the 21½ minutes)

Start the backend and Vite frontend using README instructions. Open http://localhost:5173 and confirm the API is reachable. Click **Load simulated demo** once. Verify the persistent orange `SIMULATED SCENARIO — NOT REAL PATIENT DATA` banner, fictional ID `SIM-DEMO-FEM-001`, and three observations. If the scenario is not active, load it now. Keep the banner visible whenever displaying its records. Do not clear the scenario until the end.

## Timed script

### 0:00–1:30 — Introduce the problem

“Glucose patterns differ between individuals, and daily context may matter. For women with Type 2 diabetes, whether menstrual-cycle context adds useful predictive information is an important research question. We should not assume an effect or ship a hormonal correction without joint-cohort evidence. FemMetaboTwin is a small research prototype for tracking a person’s observations and making the evidence behind any output visible.”

“It is not medical advice, a medical device, or an emergency service. It never recommends medication changes.”

### 1:30–3:30 — Who it is for and what works today

Point to the Patient workspace and the role switch. “The patient view can log glucose observations and optional meal context. The Twin state, history, forecast status, historical matcher, and trend chart are backed by FastAPI and local SQLite. The Clinician view is a demonstration view over the same local workspace; the role switch is not authentication or a privacy boundary.”

“The available prediction paths are deliberately explicit: a verified trained-model prediction only when provenance and held-out evidence are present and all expected features are supplied; a personal-mean fallback after enough observations; or unavailable. This checkout has no verified real-data model. In all cases, uncertainty is not estimated.”

### 3:30–5:30 — Architecture and data flow

Open `docs/ARCHITECTURE.md` or `docs/architecture.svg`. Trace patient entry → React → FastAPI → SQLite → Twin state → prediction eligibility → patient result and audit. Point out the separate synthetic demonstration branch and the real-data path: checksum verification, schema inspection, explicit mapping, past-only features, a future glucose target, and participant-held-out evaluation.

“The model branch in this diagram describes guarded capability. It is inactive in this checkout. We have not replaced missing CGMacros observations with fabricated training data.”

### 5:30–7:30 — Provenance and limits

Open `docs/DATA_PROVENANCE.md`. “CGMacros is an open PhysioNet resource under CC BY-NC-SA 4.0. The archive is 657,187,340 bytes. The known BITS job is suspended at 884,736 bytes, and a different repository partial is 2,150,024 bytes. Neither is complete or verified; neither was extracted. Consequently, we have no observed local CSV schema, no real training run, and no genuine held-out metrics.”

“mcPHASES is a separate restricted dataset, not a Type 2 diabetes cohort. We do not merge its participants with CGMacros and we make no cycle-aware clinical validation claim.”

### 7:30–9:30 — Activate and inspect the synthetic patient flow

Return to the app and point to the orange scenario banner and fictional ID. “The Load simulated demo button seeds three illustrative observations under a dedicated patient ID. It does not replace the default workspace. The banner persists across views so these records cannot be mistaken for patient evidence.”

Show the three glucose entries and their meal IDs/carbohydrate fields in the Twin history. Explain that the illustrative values were authored for a software walkthrough, not sampled from CGMacros. “Their only purpose is to make the UI path visible.”

### 9:30–11:30 — Patient overview and state update

Point to personal baseline, variability, observation count, and uncertainty. “The API updates the mean and running variability when observations are logged. The state is persisted in SQLite. Prediction-outcome feedback is linked to the prediction ID and updates a descriptive error summary; it does not retrain a model.”

Optionally submit another clearly synthetic reading while the banner is visible. Point out that the workspace label stays present. “Any extra entry in this scenario is also isolated under the synthetic ID and is excluded from model training.”

### 11:30–13:30 — Forecast and honest fallback

Open Glucose Forecast and click **Generate glucose forecast**. “There is no verified model artifact here, and the synthetic ID is additionally barred from trained inference. With these observations, the app returns a personal-mean fallback, labels it as an illustrative simulated fallback, and reports uncertainty as not estimated. This number is not an ML forecast, a validated estimate, or clinical guidance.”

Explain that if the workspace had fewer than two observations and no eligible trained artifact, the API would return unavailable rather than inventing a number. Point out that logging an outcome can record prediction error but does not convert a fallback into a model result.

### 13:30–15:30 — What-If matching

Open What-If Lab and request matches for a carbohydrate amount. “The matcher standardizes the selected numeric feature and counts complete historical meal responses with matching fields. Three illustrative meal records are present in this scenario, so it can display historical analogs. The UI explicitly says these are not predicted outcomes or causal effects. In an empty workspace or with fewer than three comparable meals, it returns an insufficient-data status and the match count.”

### 15:30–17:00 — Longitudinal view and cycle limitation

Open Longitudinal Trends and point out that the chart uses the local observations currently selected. “It is a view of entered values, not a CGMacros cohort analysis.” Open Cycle Insights. “There is no cycle-linked prediction here. A cycle label or a separate cohort cannot establish cycle effects in women with Type 2 diabetes. No hormonal adjustment is hardcoded.”

### 17:00–18:30 — Recommendations and safety

Show Recommended Actions and the feedback control. “The action is general educational guidance to review patterns with a care team. Feedback is stored locally and is not a model update. Medication changes are out of scope.”

Point to the prototype/safety notice. “Any alert behavior is simulated and unconnected to devices or emergency services. This must not be used for urgent care.”

### 18:30–20:00 — Clinician and audit view

Switch to Clinician view and open Model & System Audit. Show dataset status, archive byte count, checksum status, model status, evaluation metrics field, leakage safeguards, provenance, and limitations. “The current state is partial/unverified data, not trained, with metrics unavailable. No interval calibration or SHAP artifact is present. The synthetic scenario label remains visible.”

### 20:00–21:00 — Tests and engineering boundaries

Explain that the backend tests cover state update, API labeling, synthetic isolation/reset, model eligibility/fallback, inference failure, matching, and temporal feature preparation. The production frontend build is also run. “These are software checks; they are not clinical validation or model performance metrics.”

### 21:00–21:30 — Reset and close

Click **Reset simulated demo** and confirm. The app clears only rows for `SIM-DEMO-FEM-001` and returns to the default workspace. “Our next evidence-producing step is to obtain the complete authorized archive, verify exact size and SHA-256, inspect real schemas, then decide whether a defensible target and participant-held-out evaluation are possible. Until then the real-data model remains unavailable.”

## Contingency

If the backend or simulation endpoint is unavailable, do not hand-enter the synthetic values as if they came from a real patient. Show the empty/unavailable state and report the runtime issue. If the synthetic banner is absent, stop displaying those records until the scenario is loaded and labeled. Do not show hypothetical model metrics or claim cycle-aware validation.
