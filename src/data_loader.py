"""Data loading and traceability graph construction."""

from pathlib import Path
from typing import Optional

import networkx as nx
import pandas as pd


DATASET_DIR = Path(__file__).resolve().parent.parent / "dataset"


def load_data(data_dir: Optional[Path] = None):
    """Load all CSV files from the dataset directory."""
    data_dir = data_dir or DATASET_DIR

    stakeholders = pd.read_csv(data_dir / "stakeholder_requirements.csv")
    systems = pd.read_csv(data_dir / "system_requirements.csv")
    software = pd.read_csv(data_dir / "software_requirements.csv")
    components = pd.read_csv(data_dir / "components.csv")
    tests = pd.read_csv(data_dir / "test_cases.csv")
    traceability = pd.read_csv(data_dir / "traceability.csv")
    versions = pd.read_csv(data_dir / "requirement_versions.csv")
    changes = pd.read_csv(data_dir / "change_requests.csv")
    expected_impacts = pd.read_csv(data_dir / "expected_impacts.csv")

    return {
        "stakeholders": stakeholders,
        "systems": systems,
        "software": software,
        "components": components,
        "tests": tests,
        "traceability": traceability,
        "versions": versions,
        "changes": changes,
        "expected_impacts": expected_impacts,
    }


def build_graph(data: dict) -> nx.DiGraph:
    """Build a directed traceability graph from loaded data."""
    G = nx.DiGraph()

    # Add nodes
    for _, row in data["stakeholders"].iterrows():
        G.add_node(
            row["id"],
            type=row["type"],
            text=row["text"],
            domain=row.get("domain"),
            feature=row.get("feature"),
            priority=row.get("priority"),
            status=row.get("status"),
            version=row.get("version"),
        )

    for _, row in data["systems"].iterrows():
        G.add_node(
            row["id"],
            type=row["type"],
            text=row["text"],
            parent_sr=row.get("parent_sr"),
            status=row.get("status"),
            version=row.get("version"),
        )

    for _, row in data["software"].iterrows():
        G.add_node(
            row["id"],
            type=row["type"],
            text=row["text"],
            parent_sys=row.get("parent_sys"),
            status=row.get("status"),
            version=row.get("version"),
        )

    for _, row in data["components"].iterrows():
        G.add_node(
            row["id"],
            type=row["type"],
            text=row["description"],
            name=row["name"],
        )

    for _, row in data["tests"].iterrows():
        G.add_node(
            row["id"],
            type=row["type"],
            text=row["text"],
            verifies=row.get("verifies"),
        )

    # Add edges
    for _, row in data["traceability"].iterrows():
        G.add_edge(
            row["source"],
            row["target"],
            relation=row["relation"],
            confidence=row["confidence"],
            status=row["status"],
            note=row.get("note"),
        )

    return G


def get_artifact_records(data: dict) -> list[dict]:
    """Build a flat list of all searchable artifacts."""
    records = []

    for _, row in data["systems"].iterrows():
        records.append({
            "id": row["id"],
            "type": row["type"],
            "text": row["text"],
        })

    for _, row in data["software"].iterrows():
        records.append({
            "id": row["id"],
            "type": row["type"],
            "text": row["text"],
        })

    for _, row in data["components"].iterrows():
        records.append({
            "id": row["id"],
            "type": row["type"],
            "text": row["description"],
        })

    for _, row in data["tests"].iterrows():
        records.append({
            "id": row["id"],
            "type": row["type"],
            "text": row["text"],
        })

    return records
