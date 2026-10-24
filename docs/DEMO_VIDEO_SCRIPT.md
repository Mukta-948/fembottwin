# FemMetaboTwin — Final spoken demo-video script

**Target recording length: about 18 minutes.** Directions in brackets are for the presenter and are not spoken. The walkthrough uses the isolated fictional participant `SIM-DEMO-FEM-001`. Keep the orange simulated-data banner visible whenever its records are on screen. This is a software demonstration, not a clinical study or patient-care workflow.

## Before recording (not part of the timed script)

In the first terminal, run `cd backend`, activate/install the backend environment as described in the README, then run `uvicorn app.main:app --reload`. In a second terminal, run `cd frontend`, then `npm run dev`. Open `http://localhost:5173`; verify the backend is reachable and the page shows the local workspace. Click **Load simulated demo** once. The expected state is the orange **SIMULATED SCENARIO — NOT REAL PATIENT DATA** banner and three observations. Do not reset or alter the default workspace. The app stores data in local SQLite; the clinician switch is not authentication. Do not show or enter real patient information.

The checked-in source has eight sidebar destinations, but the dashboard sections below the route panel remain on screen as you switch destinations. The forecast and trend blocks on that dashboard are not populated by the demo scenario. Use the route panel for the active page's controls and explain this shared-page behavior instead of implying each navigation item opens a fully separate application.

## 0:00–1:20 — Introduction and motivation

[Show the Patient Overview with the simulated banner visible.]

“Hi, I’m presenting FemMetaboTwin, a research prototype for making an individual’s glucose observations and the evidence behind a forecast easier to inspect. Women and sex-specific biology have not always been represented or analyzed consistently across biomedical research. We’re interested in whether women’s health context, including menstrual-cycle information, could matter for some people with Type 2 diabetes. That is a research question, not an assumption. Individual responses can differ, and findings in one diabetes population do not establish an effect in another.

“The prototype does not diagnose, recommend treatment, or tell anyone to change medication. It is not a medical device or emergency service. Today I’ll show what the software actually does, where its current evidence stops, and what would have to happen before a real-data model could be enabled.”

## 1:20–2:50 — What this Digital Twin means today

[Point to the local profile, baseline and observation cards.]

“Here, ‘Digital Twin’ means a small persistent state for one local workspace. It updates a personal mean and variability from readings entered into the app, stores observations and prediction outcomes, and makes the prediction status explicit. It is not a physiological simulation, a live glucose sensor connection, or a clinical record shared with a care team.

“The stack is React with Vite and custom responsive CSS, a FastAPI service, and SQLite on this device. pandas and scikit-learn are used by the data and model utilities. The browser sends requests to the API; the API stores state, observations, forecasts, and feedback in SQLite. The app does not currently sync records to a clinician.”

## 2:50–4:00 — Navigation and role switch

[Point to the sidebar, then briefly click each item in order: Overview, My Digital Twin, Glucose Forecast, Cycle Insights, What-If Lab, Recommended Actions, Longitudinal Trends, Model & System Audit.]

“These are the eight navigation options. Each selection changes the title and the focused information panel. The shared overview cards and forms remain below it, so I’ll use the focused panel when I need a page-specific interaction.

“The header switch changes between Patient and Clinician preview. Choosing Clinician takes us to Model & System Audit; it is only a presentation role switch. There is no sign-in, authentication, authorization, or patient separation enforced by that role. The small clinician-preview shortcut in the sidebar opens the audit panel too. The **System status** button also opens the audit; **Explore twin**, **See data setup**, and **Review limitations** are shortcuts to their named panels. On a narrow screen, the menu button opens and closes the sidebar. Refresh reloads the overview, observation history, and audit data from the local API.”

## 4:00–5:20 — Load the isolated demonstration

[Return to Overview. If the orange banner is absent, click **Load simulated demo** once.]

“This button calls the demo-scenario endpoint. It clears and reseeds only the dedicated ID `SIM-DEMO-FEM-001` with three fictional readings, at 104, 139, and 121 milligrams per deciliter, recorded about 28, 19, and 4 hours before activation. Each record has a distinct synthetic meal ID, carbohydrate value, and a `synthetic_demo_only` marker. The endpoint also recalculates that ID’s Twin state and disables trained-model inference for this ID.

“The browser switches to this ID and shows the persistent orange warning. These numbers are authored examples, not observations from CGMacros or from a person. Their only purpose is to let us demonstrate the software path. The default `demo-patient` and other IDs are not replaced.”

## 5:20–7:25 — Twin state, history, and a complete feedback loop

[Click **My Digital Twin**. Point out baseline, variability, count, and recent observations.]

“The Twin panel shows the mean of this workspace’s logged glucose values, its running population standard deviation, the count, and up to five recent readings. The values are descriptive summaries. The state updater uses an online Welford-style calculation, so it can update the mean and variability without rereading the full history. If a context includes a meal type or activity label, it also keeps a simple count and mean for that label. The current entry form does not provide those labels, so those profiles are not demonstrated here. A cycle label, if supplied through the API, is recorded as a label only; it does not change glucose predictions.”

[Click **Glucose Forecast**, then **Generate glucose forecast**. Leave meal carbohydrate blank so this is a clear fallback demonstration.]

“With three observations, the demo can show the personal-mean fallback. It is labeled **PERSONAL-MEAN FALLBACK · SIMULATED**, and its source is `personal_baseline_fallback`. This is not an ML prediction, not a validated estimate, and its uncertainty is explicitly not estimated. The synthetic ID cannot use a trained artifact even if one were present.

[Return to Overview using the sidebar, enter `127` in Glucose reading, and click **Log observation**.]

“Now I’m logging another fictional reading. The API validates the numeric input bounds, persists the observation and context, and updates the state. Because the previous fallback prediction is still active in the form state, this reading is linked to its prediction ID. The API records the absolute prediction error and updates a descriptive mean absolute error summary; it does not retrain any model. The browser clears the input and refreshes the displayed history.”

## 7:25–8:50 — Forecast decision flow and unavailable real model

[Click **Glucose Forecast** again. Point at the displayed source, status, and confidence text.]

“The real-model route is guarded. The backend requires a complete model artifact, the expected feature list, the pinned CGMacros archive verification marker and byte size, matching provenance metadata, and held-out evaluation fields with finite MAE and RMSE and nonzero test rows and held-out participants. It also requires every expected feature to be present and finite at request time. An inference error or incomplete inputs cannot be labeled a trained prediction.

“If those checks fail, at least two logged observations allow a personal-mean fallback. With fewer than two and no eligible model, the response is unavailable. In this checkout there is no verified real dataset, trained real-data artifact, or genuine held-out metric. The app therefore does not have a real-data forecast to show. Uncertainty is not estimated in any current prediction path.”

“The browser can construct model inputs only when the user has entered a positive carbohydrate amount and has an observation from the last fifteen minutes. It derives the premeal value, recent mean and standard deviation, and cyclical time-of-day features. The synthetic observations are hours old, so they do not supply those recent inputs. The current fallback path does not depend on them.”

## 8:50–10:20 — What-If historical matching

[Click **What-If Lab**. Keep the default 30 grams and click **Check historical matches**.]

“This is a historical similarity lookup, not a counterfactual model. The browser sends only the selected carbohydrate feature. The API considers unique meal IDs with a complete-response marker and the same feature fields. It standardizes that feature across the usable history with scikit-learn’s `StandardScaler`, calculates Euclidean distance, and returns up to five nearest records. At least three complete comparable meals are required. The displayed match count is the number of complete comparable records, not a causal estimate or a guarantee that an outcome will repeat.

“The synthetic scenario has three complete meal records, so we expect three matches and their recorded glucose values. The app explicitly calls them historical analogs, not predictions. In an ordinary empty workspace, or when fewer than three complete matching meals exist, the endpoint reports `insufficient_data` and the count; it does not fill in a result.”

## 10:20–11:15 — Longitudinal Trends

[Click **Longitudinal Trends** and point to the chart.]

“This chart plots the locally stored observation timestamps against entered glucose values. It is drawn from the current workspace’s observation history. It is not a cohort result, model evaluation plot, or forecast chart. The trend panel requires at least two readings; otherwise it shows the logged count and says that more readings are needed. As with every demo record, the orange banner remains the reminder that this particular history is fictional.”

## 11:15–12:10 — Cycle Insights and the research boundary

[Click **Cycle Insights**.]

“Cycle Insights is currently an unavailable-state explanation, not a cycle model. The UI says CGMacros does not include cycle information; mcPHASES is a separate restricted dataset and is not a Type 2 diabetes cohort. We keep the sources separate and do not apply a hormonal correction. A self-reported phase label by itself would not validate an effect or show that cycle features improve prediction.

“To investigate this responsibly, we would need suitable authorized longitudinal data that links glucose and meal timing to reliable cycle context in the intended population, with privacy and ethics requirements addressed. We would first inspect the actual files, units, missingness, timing, and participant structure, then decide whether the observations support a target at all.”

## 12:10–13:05 — Recommended Actions and safety

[Click **Recommended Actions**. Point to the general guidance and the feedback control lower on the page.]

“The recommendation is fixed, general educational guidance: review personal patterns with a care team. It is not generated from a clinical guideline or causal analysis. The **Yes, helpful** control stores a feedback row for the current local ID; the API explicitly reports that feedback is not used to update the model. There is no medication-adjustment advice.

“The API response includes a simulated safety-status field, but this frontend does not render an operational alert workflow. There is no device integration, signal monitoring, escalation, or emergency service. The visible research-prototype notice is the safety boundary.”

## 13:05–15:20 — Clinician preview and Model & System Audit

[Click the Patient view role switch to enter Clinician view. It should open Model & System Audit.]

“The clinician preview focuses on the audit. It does not expose a separate clinical record or access-controlled clinician account. The audit reports local dataset status, detected CSV count, archive size versus expected size, checksum-marker status, model status, evaluation fields when an eligible artifact exists, interval and SHAP availability, leakage safeguards, provenance, cycle limitations, and synthetic-scenario boundaries.

“For this project, the official CGMacros ZIP is expected to be 657,187,340 bytes and must match the SHA-256 recorded in the provenance document before extraction. The repository’s partial archive is incomplete, and no local schema has been confirmed. The audit is based on files and a verification marker in this checkout; it does not independently re-hash the whole archive each time it loads. The download script performs the pinned checksum validation before extraction.

“The audit therefore has no real-data evaluation metrics to show. The repository contains only an incomplete 2,150,024-byte partial archive; it has not been checksum-verified or extracted, and no local CSV schema has been observed. The code has a schema inspection utility and a training pipeline, but the training script requires exact participant, timestamp, glucose, and carbohydrate mappings supplied only after checking the actual dataset dictionary. It refuses to guess numeric timestamp units, refuses paths outside the verified extraction, and does not train on the synthetic test fixture.”

## 15:20–16:55 — Intended pipeline and validation

[Leave the audit open; optionally show `docs/ARCHITECTURE.md` and `docs/DATA_PROVENANCE.md` in another tab.]

“The current pipeline is prepared for an exploratory post-meal target, not trained on observed CGMacros files. It identifies a positive-carbohydrate meal event, uses glucose readings strictly before that event in a fifteen-minute premeal window, and seeks a future CGM reading around sixty minutes after the meal. The target must be after the meal and within the configured five-minute tolerance. Glucose and carbohydrate units must be explicitly mapped from the real documentation.

“The training utility requires at least twenty constructed examples and at least two participants. It uses a participant-group holdout, checks that participant IDs do not overlap, and reports MAE and RMSE alongside a premeal-glucose persistence comparator. That code path is not evidence that the source dataset actually supports the target. We still need to confirm meal linkage, timestamps, coverage, and sample counts from the real files before choosing mappings or running it.

“If the target is supportable, the next steps are a reproducible real-data run, held-out baseline comparisons, review of exclusions and leakage, then artifact integration and independent checks. Prediction intervals would need their own calibration evaluation. Any question about whether cycle context adds value would need a separate, appropriately designed analysis. Downloading a file alone does not make a validated model.”

## 16:55–18:00 — Reset and close

[Return to Overview. Click **Reset simulated demo** and accept the confirmation.]

“The reset endpoint deletes only observations, predictions, feedback, and Twin state for `SIM-DEMO-FEM-001`. It preserves the default workspace and every other patient ID. The browser clears the saved synthetic ID, selects `demo-patient`, and clears the displayed forecast. After reset, this simulated ID has no observations and a forecast request is unavailable until observations are seeded again.

“What works today is local observation entry, persistent descriptive Twin updates, labeled fallback and unavailable states, history, trend display, historical meal matching, feedback storage, and a local model audit. What is not available is a real-data-trained forecast, calibrated uncertainty, or cycle-aware prediction. The next evidence step is to obtain and verify the authorized source data, inspect its real schema, and only then decide whether a defensible evaluation can be built. Thanks for watching.”

## Recording contingency

If the API is unavailable, do not type in substitute values and imply the interaction succeeded. Show the unavailable message or stop and fix the local runtime. If the demo banner is missing, reload the scenario before showing its data. If the page appears visually unchanged after a sidebar click, scroll to the route panel near the top; the lower overview cards intentionally remain visible. No live browser recording was performed while preparing this script; click outcomes above are based on the implementation and backend tests.
