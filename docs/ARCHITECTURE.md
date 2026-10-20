# FemMetaboTwin architecture

## Implemented user and prediction flow

```mermaid
flowchart LR
  Patient[Patient input and glucose observations] --> React[React patient workspace]
  React --> API[FastAPI]
  API --> Store[(SQLite observations, history, Twin state, feedback)]
  Store --> State[Patient State Vector update]
  State --> Gate{Provenance, feature, and held-out evidence eligible?}
  Gate -->|yes and complete inputs| Model[Trained-model inference]
  Gate -->|not eligible, enough observations| Mean[Clearly labeled personal-mean fallback]
  Gate -->|not eligible, too little history| None[Unavailable prediction]
  Model --> Result[Status-labeled response; uncertainty not estimated]
  Mean --> Result
  None --> Result
  Result --> PatientView[Patient forecast and history]
  Store --> Trends[Longitudinal trends and What-If matching]
  Trends --> PatientView
  Store --> Clinician[Clinician demo view]
  API --> Audit[Data, model, safeguards, and limitations audit]
  Audit --> Clinician
  Data[Official CGMacros archive] --> Verify[Exact size and pinned SHA-256 verification]
  Verify --> Inspect[Observed schema inventory and explicit mapping]
  Inspect --> Train[Past-only features; future target; participant-held-out evaluation]
  Train -. eligible artifact and actual metrics only .-> Model
  Synthetic[Explicit synthetic demo endpoint] -->|fictional ID only| DemoStore[(Isolated synthetic SQLite rows)]
  DemoStore -->|trained inference disabled| Mean
  Restricted[mcPHASES: restricted, separate cohort] -. not merged; no cycle model .-> Future[Future separately approved research]
```

No verified CGMacros archive, extracted schema, real trained artifact, or held-out metrics are present in the current submission. The trained-model branch describes guarded capability and is inactive here. The deterministic demo is a separate, fictional patient namespace and is never eligible for model inference or training. The patient/clinician role switch is a presentation control, not authentication or access control.

## Diagram export

The submission-ready [architecture PDF](architecture.pdf) is a readable one-page flow diagram. [architecture.svg](architecture.svg) is the standalone vector version. This Markdown file preserves the Mermaid source for editing. Both diagrams describe guarded capability; the trained-model branch is inactive because no real-data artifact is available.
