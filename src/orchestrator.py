"""Orchestration: the analyze_change(change_id) service boundary."""

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
from typing import Optional

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from src.data_loader import build_graph, get_artifact_records, load_data
from src.llm_assessment import ImpactAnalysisResponse, assess_impact, create_llm_client
from src.remote_retrieval import RemoteRetrievalError, RemoteRetriever

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


@lru_cache(maxsize=4)
def _get_pipeline_resources(data_dir_key: str, mode: Optional[str] = None):
    """Load the dataset and build retrieval resources once per API process."""
    data_dir = Path(data_dir_key) if data_dir_key else None
    data = load_data(data_dir)
    graph = build_graph(data)
    engine = None
    mode = mode or _retriever_mode()
    if mode == "local":
        from src.retrieval import RetrievalEngine

        cache_dir = os.getenv("RETRIEVAL_CACHE_DIR", "").strip()
        if cache_dir and Path(cache_dir).is_dir():
            engine = RetrievalEngine.from_cache(cache_dir)
        else:
            engine = RetrievalEngine()
            engine.build_index(get_artifact_records(data))
    return data, graph, engine


def clear_pipeline_cache() -> None:
    """Clear cached models and indexes, primarily for development or data refreshes."""
    _get_pipeline_resources.cache_clear()


def _retriever_mode() -> str:
    return os.getenv("RETRIEVER_MODE", "local").strip().lower()


def _get_remote_retriever() -> RemoteRetriever:
    return RemoteRetriever.from_environment()


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
    top_k_llm: Optional[int] = 10,
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
    6. LLM impact assessment on the selected candidate set
    """
    # Reuse the loaded dataset, embedding model, FAISS index, and reranker.
    data_dir_key = str(Path(data_dir).resolve()) if data_dir else ""
    mode = _retriever_mode()
    if mode not in {"local", "remote"}:
        raise ValueError(f"Unsupported RETRIEVER_MODE: {mode}")
    data, graph, engine = _get_pipeline_resources(data_dir_key, mode)

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

    # Graph candidates
    graph_candidates = _get_downstream_nodes(graph, requirement_id)

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

    if mode == "remote":
        try:
            retrieved = _get_remote_retriever().retrieve_and_rerank(
                semantic_query=change_query,
                rerank_query=rerank_query,
                semantic_top_k=top_k_retrieval,
                rerank_artifact_ids=graph_candidates,
            )
        except RemoteRetrievalError as error:
            return AnalysisResult(
                change_id=change_id,
                requirement_id=requirement_id,
                old_text=old_text,
                new_text=new_text,
                change_type=change_type,
                reason=reason,
                candidates=pd.DataFrame(),
                ranked_candidates=pd.DataFrame(),
                error=f"Remote retrieval unavailable: {error}",
            )
    else:
        if engine is None:
            raise RuntimeError("Local retrieval engine was not initialized.")
        query_key = change_id if engine._precomputed else None
        retrieved = engine.semantic_retrieve(
            change_query, top_k=top_k_retrieval, query_key=query_key
        )

    # Combine candidates (preserve order, deduplicate)
    retrieval_candidates = retrieved["id"].tolist()
    candidate_ids = list(dict.fromkeys(graph_candidates + retrieval_candidates))

    # Build candidate records with metadata
    similarity_column = (
        "semantic_similarity"
        if "semantic_similarity" in retrieved
        else "similarity"
    )
    retrieval_scores = dict(zip(retrieved["id"], retrieved[similarity_column]))
    reranker_scores = (
        dict(zip(retrieved["id"], retrieved["reranker_score"]))
        if "reranker_score" in retrieved
        else {}
    )

    candidate_records = []
    for artifact_id in candidate_ids:
        node_data = graph.nodes.get(artifact_id)
        if node_data is None:
            continue

        paths = _get_traceability_paths(graph, requirement_id, artifact_id)
        path_nodes = [
            [
                {
                    "id": path_node,
                    "type": graph.nodes[path_node].get("type", "engineering_artifact"),
                }
                for path_node in path
            ]
            for path in paths
        ]
        current_graph_distance = _graph_distance(graph, requirement_id, artifact_id)
        current_graph_linked = artifact_id in graph_candidates

        candidate_records.append({
            "id": artifact_id,
            "type": node_data.get("type"),
            "text": node_data.get("text", node_data.get("name", "")),
            "semantic_similarity": retrieval_scores.get(artifact_id, np.nan),
            "reranker_score": reranker_scores.get(artifact_id, np.nan),
            "graph_linked": current_graph_linked,
            "graph_distance": current_graph_distance,
            "paths": paths,
            "path_nodes": path_nodes,
        })

    candidate_df = pd.DataFrame(candidate_records)

    if mode == "local":
        if engine is None:
            raise RuntimeError("Local retrieval engine was not initialized.")
        candidate_df["reranker_score"] = engine.rerank(
            rerank_query, candidate_df, query_key=query_key
        )

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
            # ``None`` assesses every candidate shown in the ranked breakdown.
            llm_candidates = (
                hybrid_ranked.copy()
                if top_k_llm is None
                else hybrid_ranked.head(top_k_llm).copy()
            )

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
