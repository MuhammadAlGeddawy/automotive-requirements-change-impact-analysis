"""FastAPI adapter for the existing change impact analysis pipeline."""

from difflib import SequenceMatcher
import os
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.data_loader import load_data


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

app = FastAPI(title="NASAQ Change Impact API")

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LABEL_TO_TIER = {
    "DIRECT": "high",
    "POTENTIAL": "medium",
    "NO_IMPACT": "low",
}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _changed_value(old_text: str, new_text: str) -> tuple[str, str]:
    """Find the smallest changed word span for the comparison cards."""
    value_pattern = re.compile(
        r"\b\d+(?:\.\d+)?\s+(?:meters?|lux|milliseconds?|mV|km/h)\b",
        re.IGNORECASE,
    )
    old_value = value_pattern.search(old_text)
    new_value = value_pattern.search(new_text)
    if old_value and new_value and old_value.group() != new_value.group():
        return old_value.group(), new_value.group()

    old_words = old_text.split()
    new_words = new_text.split()
    matcher = SequenceMatcher(a=old_words, b=new_words)
    for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if tag != "equal":
            return (
                " ".join(old_words[old_start:old_end]).rstrip("."),
                " ".join(new_words[new_start:new_end]).rstrip("."),
            )
    return old_text, new_text


def _change_request_payload(row: Any) -> dict[str, str]:
    old_text = str(row["old_text"])
    new_text = str(row["new_text"])
    changed_old, changed_new = _changed_value(old_text, new_text)
    return {
        "id": str(row["change_id"]),
        "requirementId": str(row["requirement_id"]),
        "changeType": str(row["change_type"]),
        "description": str(row["reason"]),
        "oldText": old_text,
        "newText": new_text,
        "changedValueOld": changed_old,
        "changedValueNew": changed_new,
    }


def _json_value(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _display_type(value: str) -> str:
    return value.replace("_", " ")


def _traceability_paths(row: Any) -> list[list[dict[str, str]]]:
    return [
        [
            {"id": str(node["id"]), "type": _display_type(str(node["type"]))}
            for node in path
        ]
        for path in (row.get("path_nodes") or [])
    ]


def _impact_chain(result: Any) -> list[dict[str, str]]:
    """Return the shortest available traceability path for the result."""
    if result.ranked_candidates.empty:
        return [{"id": result.requirement_id, "type": "stakeholder requirement"}]

    for _, row in result.ranked_candidates.iterrows():
        paths = row.get("paths", [])
        if paths:
            path = min(paths, key=len)
            path_nodes = row.get("path_nodes", [])
            if path_nodes:
                return [
                    {"id": str(node["id"]), "type": _display_type(str(node["type"]))}
                    for node in path_nodes[0]
                ]

    return [
        {"id": result.requirement_id, "type": "stakeholder requirement"},
        {
            "id": str(result.ranked_candidates.iloc[0]["id"]),
            "type": str(result.ranked_candidates.iloc[0]["type"]).replace("_", " "),
        },
    ]


def _analysis_payload(result: Any) -> dict[str, Any]:
    if result.error and result.llm_assessments is None:
        raise HTTPException(status_code=502, detail=result.error)

    assessments = {
        assessment.artifact_id: assessment
        for assessment in (result.llm_assessments.assessments if result.llm_assessments else [])
    }
    artifacts = []
    for _, row in result.ranked_candidates.head(10).iterrows():
        artifact_id = str(row["id"])
        assessment = assessments.get(artifact_id)
        label = assessment.impact_level if assessment else "POTENTIAL"
        confidence = assessment.confidence if assessment else 0.0
        artifacts.append(
            {
                "artifactId": artifact_id,
                "artifactType": str(row["type"]),
                "impactTier": LABEL_TO_TIER[label],
                "llmLabel": label,
                "confidence": _json_value(confidence),
                "traceability": "linked" if bool(row["graph_linked"]) else "graph_unlinked",
                "traceabilityPaths": _traceability_paths(row),
                "engineeringContent": str(row["text"]),
            }
        )

    counts = {
        "highImpact": sum(item["impactTier"] == "high" for item in artifacts),
        "mediumImpact": sum(item["impactTier"] == "medium" for item in artifacts),
        "lowImpact": sum(item["impactTier"] == "low" for item in artifacts),
        "totalAffected": len(artifacts),
    }
    return {
        **counts,
        "impactChain": _impact_chain(result),
        "artifacts": artifacts,
    }


@app.get("/api/change-requests")
def get_change_requests() -> list[dict[str, str]]:
    data = load_data()
    return [_change_request_payload(row) for _, row in data["changes"].iterrows()]


@app.post("/api/analyze/{change_id}")
def analyze(change_id: str) -> dict[str, Any]:
    # Load the ML stack only when analysis is requested so the API can start
    # and serve lightweight change-request metadata immediately.
    from src.orchestrator import analyze_change

    result = analyze_change(change_id)
    if result.error and result.ranked_candidates.empty:
        raise HTTPException(status_code=404, detail=result.error)
    return {
        "changeId": result.change_id,
        "requirementId": result.requirement_id,
        **_analysis_payload(result),
    }
