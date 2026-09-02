"""Tests for the CIA pipeline core logic."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_loader import build_graph, get_artifact_records, load_data
from src.orchestrator import (
    AnalysisResult,
    _get_downstream_nodes,
    _graph_distance,
    analyze_change,
    evaluate_at_k,
    get_ground_truth,
)
from src.retrieval import RetrievalEngine


# Fixtures
@pytest.fixture(scope="module")
def data():
    return load_data()


@pytest.fixture(scope="module")
def graph(data):
    return build_graph(data)


@pytest.fixture(scope="module")
def artifacts(data):
    return get_artifact_records(data)


@pytest.fixture(scope="module")
def engine(artifacts):
    eng = RetrievalEngine()
    eng.build_index(artifacts)
    return eng


# Data Loading Tests
class TestDataLoader:
    def test_load_data_returns_all_files(self, data):
        expected_keys = {
            "stakeholders", "systems", "software", "components",
            "tests", "traceability", "versions", "changes", "expected_impacts",
        }
        assert set(data.keys()) == expected_keys

    def test_stakeholders_loaded(self, data):
        assert len(data["stakeholders"]) >= 5
        assert "id" in data["stakeholders"].columns
        assert "text" in data["stakeholders"].columns

    def test_change_requests_loaded(self, data):
        assert len(data["changes"]) >= 3
        assert "change_id" in data["changes"].columns

    def test_expected_impacts_loaded(self, data):
        assert len(data["expected_impacts"]) > 0
        assert "artifact_id" in data["expected_impacts"].columns


# Graph Tests
class TestGraph:
    def test_graph_has_nodes(self, graph):
        assert graph.number_of_nodes() > 0

    def test_graph_has_edges(self, graph):
        assert graph.number_of_edges() > 0

    def test_node_types_present(self, graph):
        node_types = {graph.nodes[n].get("type") for n in graph.nodes()}
        assert "stakeholder_requirement" in node_types
        assert "system_requirement" in node_types

    def test_downstream_nodes(self, graph):
        downstream = _get_downstream_nodes(graph, "SR-001")
        assert len(downstream) > 0
        for node in downstream:
            assert graph.nodes[node].get("type") != "stakeholder_requirement"

    def test_graph_distance_direct(self, graph):
        dist = _graph_distance(graph, "SR-001", "SYS-001")
        assert dist == 1

    def test_graph_distance_multi_hop(self, graph):
        dist_multi = _graph_distance(graph, "SR-001", "SWR-001")
        assert dist_multi == 2

    def test_graph_distance_no_path(self, graph):
        dist_none = _graph_distance(graph, "SR-001", "NONEXISTENT")
        assert np.isnan(dist_none)


# Retrieval Tests
class TestRetrieval:
    def test_index_built(self, engine):
        assert engine._index is not None
        assert engine._index.ntotal > 0

    def test_semantic_retrieve_returns_results(self, engine):
        results = engine.semantic_retrieve("obstacle detection", top_k=5)
        assert len(results) == 5
        assert "similarity" in results.columns

    def test_semantic_retrieve_relevant(self, engine):
        results = engine.semantic_retrieve("obstacle detection", top_k=5)
        top_text = results.iloc[0]["text"].lower()
        assert "obstacle" in top_text or "detect" in top_text

    def test_rerank(self, engine):
        candidates = engine.semantic_retrieve("headlight activation", top_k=5)
        scores = engine.rerank("headlight activation", candidates)
        assert len(scores) == len(candidates)


# Orchestrator Tests
class TestOrchestrator:
    def test_analyze_change_returns_result(self):
        result = analyze_change("CR-001", skip_llm=True)
        assert isinstance(result, AnalysisResult)
        assert result.change_id == "CR-001"
        assert result.requirement_id == "SR-001"

    def test_analyze_change_has_candidates(self):
        result = analyze_change("CR-001", skip_llm=True)
        assert len(result.candidates) > 0

    def test_analyze_change_ranked_columns(self):
        result = analyze_change("CR-001", skip_llm=True)
        required_cols = {
            "id", "type", "semantic_similarity", "reranker_score",
            "graph_linked", "hybrid_score", "text",
        }
        assert required_cols.issubset(set(result.ranked_candidates.columns))

    def test_analyze_change_graph_candidates_included(self):
        result = analyze_change("CR-001", skip_llm=True)
        graph_linked = result.ranked_candidates[
            result.ranked_candidates["graph_linked"]
        ]
        assert len(graph_linked) > 0

    def test_analyze_change_invalid_id(self):
        result = analyze_change("INVALID-CR", skip_llm=True)
        assert result.error is not None
        assert "not found" in result.error

    def test_evaluate_at_k_perfect(self):
        ranked = ["A", "B", "C", "D", "E"]
        gt = {"A", "B", "C"}
        result = evaluate_at_k(ranked, gt, 3)
        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0

    def test_evaluate_at_k_partial(self):
        ranked = ["A", "X", "Y", "B", "Z"]
        gt = {"A", "B", "C"}
        result = evaluate_at_k(ranked, gt, 3)
        # Top 3 = {A, X, Y}, TP = {A}, precision = 1/3, recall = 1/3
        assert result["precision"] == 1 / 3
        assert result["recall"] == 1 / 3

    def test_evaluate_at_k_empty_ground_truth(self):
        ranked = ["A", "B", "C"]
        result = evaluate_at_k(ranked, set(), 3)
        assert result["recall"] == 0
        assert result["f1"] == 0

    def test_get_ground_truth(self, data):
        gt = get_ground_truth(data, "CR-001")
        assert len(gt) > 0
        assert "SYS-001" in gt
        assert "SWR-001" in gt


# Baseline Evaluation Tests
class TestEvaluationBaseline:
    def test_recall_at_10(self):
        data = load_data()
        ground_truth_ids = get_ground_truth(data, "CR-001")
        result = analyze_change("CR-001", skip_llm=True)
        hybrid_ids = result.ranked_candidates["id"].tolist()
        metrics = evaluate_at_k(hybrid_ids, ground_truth_ids, 10)
        assert metrics["recall"] >= 0.60

    def test_f1_at_10(self):
        data = load_data()
        ground_truth_ids = get_ground_truth(data, "CR-001")
        result = analyze_change("CR-001", skip_llm=True)
        hybrid_ids = result.ranked_candidates["id"].tolist()
        metrics = evaluate_at_k(hybrid_ids, ground_truth_ids, 10)
        assert metrics["f1"] >= 0.50

    def test_recall_improves_with_k(self):
        data = load_data()
        ground_truth_ids = get_ground_truth(data, "CR-001")
        result = analyze_change("CR-001", skip_llm=True)
        hybrid_ids = result.ranked_candidates["id"].tolist()

        r5 = evaluate_at_k(hybrid_ids, ground_truth_ids, 5)["recall"]
        r10 = evaluate_at_k(hybrid_ids, ground_truth_ids, 10)["recall"]
        r15 = evaluate_at_k(hybrid_ids, ground_truth_ids, 15)["recall"]

        assert r10 >= r5
        assert r15 >= r10
