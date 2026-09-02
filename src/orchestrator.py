"""Orchestration: the analyze_change(change_id) service boundary."""

from dataclasses import dataclass
from typing import Optional

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from src.data_loader import build_graph, get_artifact_records, load_data
from src.llm_assessment import ImpactAnalysisResponse, assess_impact, create_llm_client
from src.retrieval import RetrievalEngine

from openai import OpenAI, OpenAIError
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)


@dataclass
class AnalysisResult:
    """Container for a full change impact analysis result."""

    change_id: str
    requirement_id: str
    old_text: str
    new_text: str
    change_type: str
    reason: str
    candidates: pd.DataFrame
    ranked_candidates: pd.DataFrame
    llm_assessments: Optional[ImpactAnalysisResponse] = None
    error: Optional[str] = None


def _get_downstream_nodes(graph: nx.DiGraph, start_node: str) -> list[str]:
    """Get all downstream descendants excluding stakeholder requirements."""
    try:
        descendants = nx.descendants(graph, start_node)
    except nx.NetworkXError:
        return []

    return [
        node
        for node in descendants
        if graph.nodes[node].get("type") != "stakeholder_requirement"
    ]


def _get_traceability_paths(
    graph: nx.DiGraph, source: str, target: str, cutoff: int = 5
) -> list[list[str]]:
    """Find all simple paths between source and target up to cutoff length."""
    try:
        paths = list(
            nx.all_simple_paths(graph, source=source, target=target, cutoff=cutoff)
        )
        return paths
    except nx.NetworkXNoPath:
        return []


def _graph_distance(graph: nx.DiGraph, source: str, target: str) -> float:
    """Shortest path length between two nodes, or nan if no path."""
    try:
        return nx.shortest_path_length(graph, source, target)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return np.nan


def analyze_change(
    change_id: str,
    data_dir: Optional[str] = None,
    top_k_retrieval: int = 15,
    top_k_llm: int = 10,
    llm_model: str = "nvidia/nemotron-3.5-lightning:free",
    skip_llm: bool = False,
) -> AnalysisResult:
    """Run the full change impact analysis pipeline for a given change_id.

    Pipeline:
    1. Load data and build traceability graph
    2. Build FAISS index from artifacts
    3. Generate candidates via graph traversal + semantic retrieval
    4. Rerank with Cross-Encoder
    5. Hybrid ranking (reranker + graph + semantic)
    6. LLM impact assessment on top-K
    """
    # Load data
    data = load_data()
    graph = build_graph(data)
    artifacts = get_artifact_records(data)

    # Get change request
    changes_df = data["changes"]
    change_row = changes_df[changes_df["change_id"] == change_id]

    if change_row.empty:
        return AnalysisResult(
            change_id=change_id,
            requirement_id="",
            old_text="",
            new_text="",
            change_type="",
            reason="",
            candidates=pd.DataFrame(),
            ranked_candidates=pd.DataFrame(),
            error=f"Change request '{change_id}' not found.",
        )

    change = change_row.iloc[0]
    requirement_id = change["requirement_id"]
    old_text = change["old_text"]
    new_text = change["new_text"]
    change_type = change["change_type"]
    reason = change["reason"]

    # Build retrieval engine and index
    engine = RetrievalEngine()
    engine.build_index(artifacts)

    # Build change query
    change_query = f"""
Changed stakeholder requirement:

OLD:
{old_text}

NEW:
{new_text}

Change type:
{change_type}

Reason:
{reason}

Find engineering artifacts that may be affected by this change.
""".strip()

    # Semantic retrieval
    retrieved = engine.semantic_retrieve(change_query, top_k=top_k_retrieval)

    # Graph candidates
    graph_candidates = _get_downstream_nodes(graph, requirement_id)

    # Combine candidates (preserve order, deduplicate)
    retrieval_candidates = retrieved["id"].tolist()
    candidate_ids = list(dict.fromkeys(graph_candidates + retrieval_candidates))

    # Build candidate records with metadata
    retrieval_scores = dict(zip(retrieved["id"], retrieved["similarity"]))

    candidate_records = []
    for artifact_id in candidate_ids:
        node_data = graph.nodes.get(artifact_id)
        if node_data is None:
            continue

        paths = _get_traceability_paths(graph, requirement_id, artifact_id)
        current_graph_distance = _graph_distance(graph, requirement_id, artifact_id)
        current_graph_linked = artifact_id in graph_candidates

        candidate_records.append({
            "id": artifact_id,
            "type": node_data.get("type"),
            "text": node_data.get("text", node_data.get("name", "")),
            "semantic_similarity": retrieval_scores.get(artifact_id, np.nan),
            "graph_linked": current_graph_linked,
            "graph_distance": current_graph_distance,
            "paths": paths,
        })

    candidate_df = pd.DataFrame(candidate_records)

    # Rerank with cross-encoder
    rerank_query = f"""
A stakeholder requirement changed.

OLD:
{old_text}

NEW:
{new_text}

Change type:
{change_type}

Determine whether the engineering artifact below is relevant
to assessing the impact of this change.
""".strip()

    candidate_df["reranker_score"] = engine.rerank(rerank_query, candidate_df)

    # Normalize scores for hybrid ranking
    semantic_scaler = MinMaxScaler()
    reranker_scaler = MinMaxScaler()

    candidate_df["semantic_score_norm"] = semantic_scaler.fit_transform(
        candidate_df[["semantic_similarity"]]
    ).ravel()

    candidate_df["reranker_score_norm"] = reranker_scaler.fit_transform(
        candidate_df[["reranker_score"]]
    ).ravel()

    candidate_df["graph_linked_numeric"] = candidate_df["graph_linked"].astype(int)

    # Hybrid score
    candidate_df["hybrid_score"] = (
        0.45 * candidate_df["reranker_score_norm"]
        + 0.35 * candidate_df["graph_linked_numeric"]
        + 0.20 * candidate_df["semantic_score_norm"]
    )

    hybrid_ranked = (
        candidate_df
        .sort_values("hybrid_score", ascending=False)
        .reset_index(drop=True)
    )

    # LLM assessment on top-K
    llm_assessments = None
    error = None

    if not skip_llm:
        try:
            client = create_llm_client()
            llm_candidates = hybrid_ranked.head(top_k_llm).copy()

            llm_assessments = assess_impact(
                client=client,
                model=llm_model,
                change_id=change_id,
                requirement_id=requirement_id,
                old_text=old_text,
                new_text=new_text,
                ranked_candidates=llm_candidates,
            )
        except EnvironmentError as e:
            # Missing API key - non-fatal, can still show retrieval results
            error = f"LLM skipped: {str(e)}"
        except (
            APIConnectionError,
            APITimeoutError,
            RateLimitError,
            AuthenticationError,
            OpenAIError,
        ) as e:
            error = f"LLM API error: {type(e).__name__}: {str(e)}"
        except (ValueError, Exception) as e:
            error = f"LLM parsing error: {str(e)}"

    return AnalysisResult(
        change_id=change_id,
        requirement_id=requirement_id,
        old_text=old_text,
        new_text=new_text,
        change_type=change_type,
        reason=reason,
        candidates=candidate_df,
        ranked_candidates=hybrid_ranked,
        llm_assessments=llm_assessments,
        error=error,
    )


def evaluate_at_k(
    ranked_ids: list[str],
    ground_truth_ids: set[str],
    k: int,
) -> dict:
    """Evaluate precision, recall, and F1 for top-k retrieval."""
    retrieved = set(ranked_ids[:k])
    tp = len(retrieved & ground_truth_ids)

    precision = tp / k if k > 0 else 0
    recall = tp / len(ground_truth_ids) if ground_truth_ids else 0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    return {
        "k": k,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def get_ground_truth(data: dict, change_id: str) -> set[str]:
    """Get ground truth artifact IDs for a change request."""
    expected_impacts = data["expected_impacts"]
    cr_ground_truth = expected_impacts[
        expected_impacts["change_id"] == change_id
    ]
    return set(cr_ground_truth["artifact_id"])
