"""LLM Impact Assessment via OpenRouter."""

import json
import os
import re
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class ImpactAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    impact_level: Literal["DIRECT", "POTENTIAL", "NO_IMPACT"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    evidence: list[str]


class ImpactAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assessments: list[ImpactAssessment]


SYSTEM_PROMPT = """
You are an automotive Change Impact Analysis classifier.

Classify every candidate artifact into exactly one:

DIRECT
POTENTIAL
NO_IMPACT

DIRECT:
The artifact explicitly contains or verifies the behavior/parameter
that changed.

POTENTIAL:
The artifact is functionally related to the changed behavior,
but direct impact is not proven.

NO_IMPACT:
There is sufficient evidence that the artifact is unrelated.

Rules:
- Use the artifact text and traceability evidence.
- Do not use semantic similarity alone.
- Do not invent relationships.
- Consider the OLD and NEW requirements.
- Return exactly one result for every candidate.
- Do NOT provide reasoning or analysis outside the JSON.
- Keep the reason to ONE short sentence.
- Keep evidence to ONE short sentence.

Return ONLY valid JSON in this exact format:

{
  "assessments": [
    {
      "artifact_id": "SYS-001",
      "impact_level": "DIRECT",
      "confidence": 0.95,
      "reason": "Short reason.",
      "evidence": ["Short evidence."]
    }
  ]
}
""".strip()


def _safe_value(value):
    """Convert numpy/pandas types to native Python types."""
    import pandas as pd
    import numpy as np

    if pd.isna(value):
        return None
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


def build_llm_context(
    change_id: str,
    requirement_id: str,
    old_text: str,
    new_text: str,
    ranked_candidates,
) -> str:
    """Build the user prompt context string for the LLM."""
    context = f"""
CHANGE REQUEST
-------------
Change ID: {change_id}

Changed Requirement ID:
{requirement_id}

OLD REQUIREMENT:
{old_text}

NEW REQUIREMENT:
{new_text}


CANDIDATE ARTIFACTS
-------------------
"""

    for _, row in ranked_candidates.iterrows():
        artifact_id = _safe_value(row.get("id"))
        artifact_type = _safe_value(row.get("type"))
        artifact_text = _safe_value(row.get("text"))

        semantic_similarity = _safe_value(row.get("semantic_similarity"))
        reranker_score = _safe_value(row.get("reranker"))
        if reranker_score is None:
            reranker_score = _safe_value(row.get("reranker_score"))
        graph_linked = _safe_value(row.get("graph_linked"))
        graph_distance = _safe_value(row.get("graph_distance"))

        context += f"""

----------------------------------------
Artifact ID:
{artifact_id}

Type:
{artifact_type}

Text:
{artifact_text}

Semantic Similarity:
{semantic_similarity}

Reranker Score:
{reranker_score}

Graph Linked:
{graph_linked}

Graph Distance:
{graph_distance}
"""

    return context


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences."""
    if not text:
        raise ValueError("LLM returned an empty response.")

    text = text.strip()

    # Remove markdown code fences
    text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()

    # Try direct JSON parsing first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find the first JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        json_text = text[start:end + 1]
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Found JSON-like content but it is malformed: {json_text}"
            ) from e

    raise ValueError(f"No JSON object found in the LLM response: {text[:200]}")


def create_llm_client() -> OpenAI:
    """Create OpenRouter client from environment variable."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY not set. "
            "Set it as an environment variable or in a .env file."
        )

    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


def assess_impact(
    client: OpenAI,
    model: str,
    change_id: str,
    requirement_id: str,
    old_text: str,
    new_text: str,
    ranked_candidates,
) -> ImpactAnalysisResponse:
    """Call LLM to assess impact of top-K candidates."""
    user_prompt = build_llm_context(
        change_id=change_id,
        requirement_id=requirement_id,
        old_text=old_text,
        new_text=new_text,
        ranked_candidates=ranked_candidates,
    )

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "impact_analysis",
            "description": "Engineering change impact analysis results",
            "schema": ImpactAnalysisResponse.model_json_schema(),
            "strict": True,
        },
    }

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format=response_format,
        temperature=0.0,
        timeout=120,
    )

    raw_output = response.choices[0].message.content
    parsed_output = _extract_json(raw_output)

    return ImpactAnalysisResponse.model_validate(parsed_output)
