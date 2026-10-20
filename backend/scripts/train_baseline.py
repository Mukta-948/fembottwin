"""Train only from a checksum-verified CGMacros extraction under data/raw."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import joblib
import pandas as pd
from app.modeling import prepare_postmeal_examples, train_baseline

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = (PROJECT_ROOT / "data" / "raw" / "cgmacros").resolve()
EXPECTED_SHA256 = "05c8b0e6f1a2757050aced55ce4bf6ab2ac9b30f2fd8ca193056812d9c621d4d"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


p = argparse.ArgumentParser(description=__doc__)
p.add_argument("data", type=Path, help="Verified extracted directory, or a CSV inside it")
p.add_argument("--participant", help="Exact participant-ID column, if the real files contain one")
p.add_argument("--participant-path-regex", help="Explicit capture regex against relative CSV path if IDs are encoded in filenames/folders")
p.add_argument("--timestamp", required=True, help="Exact timestamp column from the observed data dictionary")
p.add_argument("--glucose", required=True, help="Exact CGM column from the observed data dictionary")
p.add_argument("--carbs", required=True, help="Exact carbohydrate column linked to meal timestamp")
p.add_argument("--glucose-unit", required=True, choices=["mg/dL", "mmol/L"], help="Unit verified from the data dictionary")
p.add_argument("--carbs-unit", required=True, choices=["g"], help="Unit verified from the data dictionary")
p.add_argument("--horizon", type=int, default=60)
a = p.parse_args()

verified_archive = RAW_ROOT / "CGMacros_dateshifted365.zip"
verified_marker = RAW_ROOT / "verified.sha256"
if not a.data.resolve().is_relative_to(RAW_ROOT / "extracted"):
    p.error("Training is restricted to the official extracted CGMacros directory; synthetic fixtures are test-only.")
if not verified_archive.is_file() or sha256(verified_archive) != EXPECTED_SHA256:
    p.error("The original CGMacros archive is absent or has not passed the pinned official SHA-256 check.")
if not verified_marker.is_file() or verified_marker.read_text(encoding="utf-8").strip() != EXPECTED_SHA256:
    p.error("No matching verified.sha256 marker; run the official download/extraction script first.")

if a.participant_path_regex:
    participant_pattern = re.compile(a.participant_path_regex)
    if participant_pattern.groups < 1:
        p.error("--participant-path-regex must contain a capture group for the participant identifier.")
else:
    participant_pattern = None

paths = sorted([a.data.resolve()] if a.data.is_file() else a.data.resolve().rglob("*.csv"))
if not paths:
    p.error("No CSV files found under the selected data path.")
examples = []
skipped = []
used_paths = []
for path in paths:
    header = list(pd.read_csv(path, nrows=0).columns)
    absent = [name for name in (a.timestamp, a.glucose, a.carbs) if name not in header]
    has_participant = bool(a.participant and a.participant in header)
    if absent or (not has_participant and participant_pattern is None):
        skipped.append({"path": str(path.relative_to(RAW_ROOT)), "reason": "requested columns or participant mapping absent"})
        continue
    columns = [a.timestamp, a.glucose, a.carbs] + ([a.participant] if has_participant else [])
    frame = pd.read_csv(path, usecols=columns)
    if has_participant:
        participant_column = a.participant
    else:
        match = participant_pattern.search(str(path.relative_to(RAW_ROOT / "extracted")))
        if not match:
            skipped.append({"path": str(path.relative_to(RAW_ROOT)), "reason": "participant path regex did not match"})
            continue
        capture = match.groupdict().get("participant") or match.group(1)
        frame["__mapped_participant_id"] = str(capture)
        participant_column = "__mapped_participant_id"
    prepared = prepare_postmeal_examples(frame, participant=participant_column, timestamp=a.timestamp,
                                        glucose=a.glucose, carbs=a.carbs, glucose_unit=a.glucose_unit,
                                        carbs_unit=a.carbs_unit, horizon_minutes=a.horizon)
    if not prepared.empty:
        examples.append(prepared)
        used_paths.append(path)
    else:
        skipped.append({"path": str(path.relative_to(RAW_ROOT)), "reason": "no linked meal-to-future-CGM events"})
if not examples:
    p.error("No valid post-meal targets were constructed. Check observed mappings, meal timestamp linkage, units, and CGM coverage.")
prepared = pd.concat(examples, ignore_index=True).sort_values(["participant_id", "meal_time"])
result = train_baseline(prepared, dataset_label="CGMacros PhysioNet v1.0.0; verified official archive")
relative_inputs = sorted({str(path.relative_to(RAW_ROOT / "extracted")) for path in used_paths})
metadata = {"metrics": result["metrics"], "features": result["features"], "mapping": {"participant": a.participant or "explicit path regex", "timestamp": a.timestamp, "glucose": a.glucose, "glucose_unit": a.glucose_unit, "carbs": a.carbs, "carbs_unit": a.carbs_unit}, "archive_sha256": EXPECTED_SHA256, "inputs": relative_inputs, "skipped_files": skipped, "seed": 42}
out = PROJECT_ROOT / "artifacts"
out.mkdir(exist_ok=True)
joblib.dump({"model": result["model"], **metadata}, out / "baseline.joblib")
(out / "baseline_metrics.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
print(json.dumps(metadata, indent=2))
