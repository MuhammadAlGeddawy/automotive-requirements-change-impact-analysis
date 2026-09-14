"""Lightweight Vercel API for the precomputed NASAQ demo."""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException


SERVICE_DATA_DIR = Path(__file__).resolve().parent / "precomputed_data"
DATA_DIR = (
    SERVICE_DATA_DIR
    if SERVICE_DATA_DIR.exists()
    else Path(__file__).resolve().parent.parent / "precomputed_data"
)
app = FastAPI(title="NASAQ Precomputed Demo API")


def _read_json(path: Path):
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail="Precomputed demo data is not installed. Run scripts/precompute_demo.py.",
        ) from error


def _precomputed_enabled() -> bool:
    return os.getenv("NASAQ_DEMO_MODE", "precomputed").strip().lower() == "precomputed"


@app.get("/health")
@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "precomputed-demo"}


@app.get("/change-requests")
@app.get("/api/change-requests")
@app.get("/svc/api/change-requests")
def change_requests():
    if not _precomputed_enabled():
        raise HTTPException(status_code=503, detail="Precomputed demo mode is disabled.")
    return _read_json(DATA_DIR / "change_requests.json")


@app.post("/analyze/{change_id}")
@app.post("/api/analyze/{change_id}")
@app.post("/svc/api/analyze/{change_id}")
def analyze(change_id: str):
    if not _precomputed_enabled():
        raise HTTPException(status_code=503, detail="Precomputed demo mode is disabled.")
    if not change_id.isalnum() and "-" not in change_id:
        raise HTTPException(status_code=400, detail="Invalid change request ID.")
    result_path = DATA_DIR / "analyses" / f"{change_id}.json"
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Unknown change request ID.")
    return _read_json(result_path)
