"""Tests for LLM assessment module (without API calls)."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.llm_assessment import _extract_json, build_llm_context


class TestExtractJson:
    def test_direct_json(self):
        text = '{"key": "value", "num": 42}'
        result = _extract_json(text)
        assert result == {"key": "value", "num": 42}

    def test_json_with_markdown_fence(self):
        text = '```json\n{"key": "value"}\n```'
        result = _extract_json(text)
        assert result == {"key": "value"}

    def test_json_with_plain_fence(self):
        text = '```\n{"key": "value"}\n```'
        result = _extract_json(text)
        assert result == {"key": "value"}

    def test_json_with_surrounding_text(self):
        text = 'Here is the result: {"key": "value"} Done.'
        result = _extract_json(text)
        assert result == {"key": "value"}

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            _extract_json("")

    def test_no_json_raises(self):
        with pytest.raises(ValueError, match="No JSON object"):
            _extract_json("This is just plain text with no JSON")

    def test_nested_json(self):
        text = '{"assessments": [{"id": "SYS-001", "impact_level": "DIRECT"}]}'
        result = _extract_json(text)
        assert "assessments" in result
        assert len(result["assessments"]) == 1


class TestBuildLlmContext:
    def test_builds_context(self):
        import pandas as pd

        candidates = pd.DataFrame([
            {
                "id": "SYS-001",
                "type": "system_requirement",
                "text": "Test text",
                "semantic_similarity": 0.85,
                "reranker_score": 0.92,
                "graph_linked": True,
                "graph_distance": 1.0,
            }
        ])

        context = build_llm_context(
            change_id="CR-001",
            requirement_id="SR-001",
            old_text="Old text",
            new_text="New text",
            ranked_candidates=candidates,
        )

        assert "CR-001" in context
        assert "SR-001" in context
        assert "Old text" in context
        assert "New text" in context
        assert "SYS-001" in context
        assert "Test text" in context
