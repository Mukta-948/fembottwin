# FemMetaboTwin: A Cycle-Aware Women's Glucose Health Digital Twin

FemMetaboTwin is a hackathon research prototype for a personalized glucose-state twin for women with Type 2 diabetes (T2D). Cycle-related glucose patterns are a future research question; the current application has no cycle-aware model and is not a medical device. It does not diagnose, prescribe, or recommend medication changes.

## Team Details

- **Team name:** [Add the actual team name]
- **Member 1 full name:** [Add full name] | **Role:** [Add role] | **Contact:** [Add contact, if required]
- **Member 2 full name:** [Add full name or remove if not applicable] | **Role:** [Add role] | **Contact:** [Add contact, if required]
- **Member 3 full name:** [Add full name or remove if not applicable] | **Role:** [Add role] | **Contact:** [Add contact, if required]
- **Member 4 full name:** [Add full name or remove if not applicable] | **Role:** [Add role] | **Contact:** [Add contact, if required]

Add or remove member rows to match the actual team. No team-member information has been supplied for this repository.

## College / Incubator Information

- **College / institution:** [Confirm the actual team affiliation. Use PDPM IIITDM Jabalpur only if the team is affiliated with it; otherwise enter the correct institution.]
- **Incubator:** [Add the incubator name, or confirm “None” / “Not applicable.”]
- **Official team or incubator details:** [Add only if applicable and verified.]

These fields are intentionally placeholders and do not assert an affiliation.

## Project Title

**FemMetaboTwin: A Cycle-Aware Women's Glucose Health Digital Twin**

## Problem Statement

Biomedical research has not consistently represented or analyzed sex-specific biology across every field and study; NIH policy now calls for considering sex as a biological variable where applicable. Findings about glucose and menstrual-cycle context are still limited and heterogeneous. A systematic review of studies in Type 1 diabetes (T1D) found varied methods and no conclusive overall evidence, with possible patterns in a subset of people. These T1D findings do not establish cycle effects in T2D. Individual responses may differ, so a cycle effect must be measured rather than assumed. [NIH Office of Research on Women's Health](https://orwh.od.nih.gov/sex-as-biological-variable) · [Systematic review in T1D](https://pubmed.ncbi.nlm.nih.gov/36836608/)

FemMetaboTwin explores whether a longitudinal, personal record can help make glucose observations and their evidence status easier to review. The prototype does not establish that cycle information improves prediction or care.

## Healthcare Use Case

The **intended research population** is women with T2D who may wish to track glucose and relevant daily context over time. The current PoC supports a patient-style workflow to enter glucose observations and optional meal details, review personal history and trends, update a persistent Twin state, inspect a forecast status, and compare a query with historical meal responses. A clinician-style demo view exposes longitudinal records and system/model audit information.

Potential value is making an individual's entered observations and the basis or absence of a forecast visible for discussion with a care team. The application has not been clinically evaluated and must not be used to make care decisions. The clinician view is a local demonstration role switch, not authentication or an access-control boundary. Data is stored locally in SQLite; it does not sync to a clinician.

## Technical Stack

Verified from the project manifests and source:

- **Frontend:** React 18, Vite, JavaScript, custom responsive CSS, Recharts, and Lucide icons. This repository does not use Tailwind.
- **Backend:** Python, FastAPI, Pydantic, pandas, scikit-learn, and joblib.
- **Persistence:** SQLite via Python's built-in `sqlite3` module.
- **Checks:** pytest for backend tests; Vite production build for frontend verification.

See [backend requirements](backend/requirements.txt) and [frontend package manifest](frontend/package.json).

## AI / ML Model and Framework Details

**There is currently no real-data-trained or independently evaluated glucose model available.** CGMacros has not been downloaded as a complete verified archive or schema-inspected in this checkout; no real-data model artifact or genuine held-out metrics exist. No accuracy, MAE, RMSE, calibration, or clinical validation result is claimed.

The implemented forecast router applies these explicit paths:

1. **Trained-model path:** only an artifact that passes provenance, expected-feature, and held-out-evaluation eligibility checks can be served, and all required inputs must be present. There is no such eligible real-data artifact in this project state.
2. **Personal-mean fallback:** after at least two user-entered observations, the app may return that person's arithmetic mean. It is explicitly labeled as a fallback estimate, not an ML prediction; uncertainty is **not estimated**.
3. **Unavailable:** when neither an eligible model nor enough observations exist, no numeric forecast is returned.

What-If uses standardized numeric features to find similar **historical** meal responses. It shows the number of matches and reports insufficient data when there are too few complete comparable records. Similarity is not a causal estimate or a prediction of what will happen after a meal.

The planned research hypothesis is that reliable cycle context might add useful information for some individuals after a suitable joint cohort and evaluation exist. It is **not implemented**: CGMacros has no cycle measurements; mcPHASES is separate, restricted, and not a T2D validation cohort. The cohorts are not merged, no hormonal adjustment is hardcoded, and no cycle-aware T2D validation is claimed. A deterministic, clearly labeled synthetic scenario exists for software demonstrations and tests only; it is not participant data, training data, or validation.

## 15–20 Minute Demo Video

**Video link:** [ADD UNLISTED YOUTUBE DEMO LINK BEFORE SUBMISSION]

The video has not been recorded or uploaded. The detailed live walkthrough is in [the 21–22 minute demo script](docs/DEMO_SCRIPT.md); shorten it to 15–20 minutes for the submission video.

## Open-Source License Details

The project source code is licensed under the [MIT License](LICENSE). MIT permits use, modification, distribution, sublicensing, and sale, provided the copyright and permission notice are included; it is supplied without warranty. This code license does not change third-party data terms. CGMacros has its own CC BY-NC-SA 4.0 terms, and mcPHASES has separate restricted-access terms; see [data provenance](docs/DATA_PROVENANCE.md).

## Architecture Diagram (PDF / SVG)

- [Architecture diagram PDF](docs/architecture.pdf)
- [Architecture diagram SVG](docs/architecture.svg)
- [Editable architecture source and explanation](docs/ARCHITECTURE.md)

The PDF reflects the implemented flows and was rendered and visually checked during this update; review it again if the architecture changes.

## Final Presentation (PDF / PPT)

- **Final presentation PDF:** an 11-page FemMetaboTwin deck was found in Downloads under the generic filename `Untitled presentation.pdf` and copied to [docs/FemMetaboTwin-Presentation.pdf](docs/FemMetaboTwin-Presentation.pdf). Its test/build slide now reflects this verified run (20 backend tests passed; frontend production build passed). The cover's team name remains a placeholder; confirm this is the intended final deck before submission.
- **PowerPoint:** [ADD FINAL `.pptx` HERE IF REQUIRED; no `.pptx` supplied.]
- **Editable presentation outline:** [docs/PRESENTATION.md](docs/PRESENTATION.md) (source outline; it is not the final PDF or PPT).

The final PDF is a copy of the FemMetaboTwin deck identified in Downloads by its project-specific title and content. Review it and confirm that it is the intended final deck before submission.

## Public Repository and Asset Accessibility

**GitHub repository:** [https://github.com/Mukta-948/fembottwin](https://github.com/Mukta-948/fembottwin)

For submission, the repository must be public and every required linked asset (including this README, architecture PDF, presentation PDF, and demo video) must open without sign-in, special permissions, or private-drive access. Verify the links in a signed-out browser before submitting. Do not publish local records, credentials, restricted data, or the CGMacros raw archive.

## Project Overview and Features

- Persistent observation history and Patient State Vector updates in local SQLite (personal mean, variability, observation count, and prediction-outcome feedback).
- Patient Overview, Twin history, forecast status, longitudinal trends, historical meal matching, general non-medication guidance, and clinician/demo audit view.
- Model audit includes dataset/training/evaluation status, provenance, leakage safeguards, and limitations.
- Explicit trained-model eligibility, personal-mean fallback, and unavailable paths; uncertainty is not estimated.
- Isolated fictional synthetic scenario `SIM-DEMO-FEM-001`, with a persistent **SIMULATED SCENARIO — NOT REAL PATIENT DATA** label.
- What-If historical matching shows match counts and does not claim causal effects.
- No device integration, emergency response, authentication, medication guidance, or cycle correction.

## Setup and Run (Windows PowerShell)

Run these commands in two PowerShell terminals from the project root. Node.js/npm and Python must already be installed.

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

Open http://localhost:5173. The frontend sends API requests to the local FastAPI service at http://127.0.0.1:8000. SQLite records are stored locally under `artifacts/` and are gitignored.

**Run checks:**

```powershell
# From backend/
python -m pytest tests -q

# From frontend/
npm run build
```

## How to Use the Simulated Demo

1. Start both services and open the app.
2. Select **Load simulated demo**. This seeds three deterministic illustrative observations for fictional ID `SIM-DEMO-FEM-001` in its separate SQLite namespace.
3. Keep the persistent **SIMULATED SCENARIO — NOT REAL PATIENT DATA** banner visible. Show Patient Overview, Twin history, forecast, What-If Lab, Longitudinal Trends, then the Clinician view and Model & System Audit.
4. Generate a forecast. The synthetic ID cannot use a trained artifact; with enough readings the app shows the clearly labeled personal-mean fallback. Uncertainty remains “not estimated.” The meal matches are historical analogs only.
5. Select **Reset simulated demo** and confirm. Only the synthetic ID's rows are cleared; the default workspace is preserved.

Do not describe synthetic values as participant evidence, training data, validation, clinical performance, or a recommendation. See the [detailed demo script](docs/DEMO_SCRIPT.md).

## Data Provenance, Limitations, and Future Work

No complete verified CGMacros archive, extracted schema, real-data model, or genuine held-out metrics are present in this checkout. The official PhysioNet CGMacros release is licensed CC BY-NC-SA 4.0. Do not extract the partial archive; verify the expected size and official SHA-256 before extraction. mcPHASES is a separate restricted cohort and must not be merged with CGMacros. See [data provenance and download instructions](docs/DATA_PROVENANCE.md).

The app's personal mean is a simple descriptive fallback, not a validated model; uncertainty is not estimated. No cycle-aware prediction, hormonal correction, interval calibration, or clinical validation is implemented. What-If matches are not causal effects. The clinician role switch is not authentication. Simulated alert behavior is not connected to devices or emergency services. Recommendations are general educational language and never advise medication changes.

Future work requires a verified authorized dataset, observed-schema inventory, target and exclusion review, participant-aware/time-safe evaluation on real data, appropriate validation, and privacy/security review. The data inventory and training commands are documented in [data provenance](docs/DATA_PROVENANCE.md); they must not be run against synthetic fixtures as real validation.

## Submission Deliverables Checklist

| Required README item | Status |
|---|---|
| Team details | Placeholders; team information required |
| College / incubator | Placeholder; confirm affiliation/details |
| Project title | Included |
| Problem statement | Included with qualified research context and sources |
| Healthcare use case | Included; prototype limitations stated |
| Technical stack | Included from project manifests/source |
| AI/ML details | Implemented paths and unavailable real-model status stated |
| 15–20 minute demo video | Placeholder; record and upload video |
| Open-source license | MIT identified and summarized |
| Architecture diagram PDF/PPT | PDF and SVG linked; PDF rendered and checked |
| Final presentation PDF/PPT | FemMetaboTwin PDF linked; confirm it is the intended final deck; PPTX not supplied |
| Public accessibility | Repository URL included; verify public visibility and signed-out asset access |
