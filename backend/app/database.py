import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "femmetabotwin.sqlite3"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE IF NOT EXISTS patient_state (patient_id TEXT PRIMARY KEY, state_json TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    db.execute("CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, patient_id TEXT NOT NULL, recommendation TEXT NOT NULL, response TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    db.execute("CREATE TABLE IF NOT EXISTS observations (id INTEGER PRIMARY KEY, patient_id TEXT NOT NULL, observed_at TEXT NOT NULL, glucose REAL NOT NULL, context_json TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS predictions (prediction_id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, predicted_glucose REAL NOT NULL, source TEXT NOT NULL, context_json TEXT NOT NULL, observed_glucose REAL, absolute_error REAL)")
    columns = {row[1] for row in db.execute("PRAGMA table_info(observations)")}
    if "prediction_id" not in columns:
        db.execute("ALTER TABLE observations ADD COLUMN prediction_id TEXT")
    db.commit()
    return db


def get_state(patient_id: str) -> dict[str, Any] | None:
    with connect() as db:
        row = db.execute("SELECT state_json FROM patient_state WHERE patient_id=?", (patient_id,)).fetchone()
        return json.loads(row[0]) if row else None


def save_state(patient_id: str, state: dict[str, Any]) -> None:
    with connect() as db:
        db.execute("INSERT INTO patient_state(patient_id,state_json) VALUES(?,?) ON CONFLICT(patient_id) DO UPDATE SET state_json=excluded.state_json,updated_at=CURRENT_TIMESTAMP", (patient_id, json.dumps(state)))
        db.commit()
