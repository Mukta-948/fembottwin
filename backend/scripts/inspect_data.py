from pathlib import Path
import json
from app.modeling import inspect_dataset

root = Path(__file__).resolve().parents[2] / "data" / "raw"
inventory = inspect_dataset(root)
out = Path(__file__).resolve().parents[2] / "artifacts" / "data_inventory.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
print(json.dumps(inventory, indent=2))
print(f"Inventory saved to {out}")
