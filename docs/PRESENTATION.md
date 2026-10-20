# FemMetaboTwin — 10-slide presentation source

Copy each numbered block into a slide. No team names are listed because none were supplied. All demo values below are synthetic and do not represent a participant or a trained model.

## 1. FemMetaboTwin

**A cycle-aware personalized Digital Twin research prototype for Type 2 diabetes**

Track personal glucose observations, make prediction evidence visible, and treat cycle effects as a question requiring suitable data.

*Speaker note:* Research prototype only; no clinical claims or medication recommendations.

## 2. The problem

- Glucose responses vary between people and across daily contexts.
- Menstrual-cycle effects in women with Type 2 diabetes require direct evidence.
- A trustworthy prototype must expose missing evidence rather than fill it with assumptions.

## 3. What is implemented

- Local patient observations and persistent Patient State Vector.
- History, longitudinal trends, forecast statuses, meal analog matching, feedback, and clinician/demo audit.
- Explicit trained-model eligibility gate, personal-mean fallback, and unavailable state.
- Separate, clearly labeled synthetic walkthrough with safe reset.

## 4. Architecture

Patient input → React/Vite → FastAPI → SQLite/Twin state → evidence gate → trained inference (only if eligible), personal-mean fallback, or unavailable → patient and clinician demo views.

**Visual:** use `docs/architecture.svg`.

## 5. Data provenance

- CGMacros is an open PhysioNet dataset under CC BY-NC-SA 4.0.
- The 657,187,340-byte archive is incomplete in this environment; no extraction or real schema inspection has occurred.
- mcPHASES is restricted, separate, and not a Type 2 diabetes cohort. The datasets are not merged.

## 6. Prediction and evaluation plan

- Inspect real headers and data dictionary before mapping participants, timestamps, glucose, or meals.
- Construct past-only inputs and a later glucose target only if actual linkage supports it.
- Hold out participant groups, preserve chronology, and report held-out metrics only after real training.
- **Current result:** no verified archive, model, held-out MAE/RMSE, or uncertainty calibration.

## 7. Patient workflow

- Log readings and optional meal context.
- View baseline, variability, observation history, and trend chart.
- See trained prediction only with eligible evidence; otherwise a labeled mean fallback or unavailable response.
- Forecast uncertainty is **not estimated**.

## 8. What-If and clinician review

- Standardized historical meal matching reports actual comparable count.
- Fewer than three complete comparables returns insufficient data.
- Similarity is descriptive, not causal.
- Clinician role switch displays audit and trends but is not authentication or access control.

## 9. Safety, privacy, and limits

- Synthetic walkthrough uses fictional `SIM-DEMO-FEM-001`, persists separately, cannot invoke trained inference, and resets only its own records.
- Local SQLite; not a production privacy/security system.
- No medication changes, live device integration, emergency alerting, calibrated intervals, SHAP, or cycle corrections.
- No clinical validation.

## 10. Verified status and roadmap

- Backend software tests and frontend production build are the verification targets; they do not establish clinical performance.
- **Real-data model:** not trained; metrics unavailable.
- Next: complete and verify the official archive, inspect its actual schemas and cohort linkage, then decide whether the target and participant-held-out evaluation are defensible.
- Only after valid real-data evaluation should model outputs appear as trained predictions.
