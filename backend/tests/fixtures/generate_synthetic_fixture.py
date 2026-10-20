"""Regenerate an explicitly synthetic, deterministic fixture used only by tests."""
from datetime import datetime, timedelta, timezone
import csv
from pathlib import Path

OUTPUT = Path(__file__).with_name("synthetic_cgmacros.csv")
FIELDS = ["participant_id", "timestamp", "glucose_mg_dl", "carbs_g"]
rows = []
origin = datetime(2030, 1, 1, tzinfo=timezone.utc)
for person in range(4):
    for meal in range(6):
        at = origin + timedelta(hours=meal * 2 + 7)
        baseline = 96 + person * 5 + meal * 2
        carbs = 24 + person * 3 + meal * 4
        samples = [(-15, baseline - 1, ""), (0, baseline, carbs), (15, baseline + 10 + carbs * .20, ""),
                   (30, baseline + 12 + carbs * .25, ""), (45, baseline + 9 + carbs * .30, ""),
                   (60, baseline + 7 + carbs * .28, "")]
        for offset, glucose, carb_value in samples:
            rows.append({"participant_id": f"SYNTHETIC-P{person + 1:02d}",
                         "timestamp": (at + timedelta(minutes=offset)).isoformat(),
                         "glucose_mg_dl": round(glucose, 2), "carbs_g": carb_value})
rows.sort(key=lambda row: (row["participant_id"], row["timestamp"]))
with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
print(f"Wrote SYNTHETIC TEST FIXTURE ONLY: {OUTPUT} ({len(rows)} rows)")
