"""HTTP client for the retrieval-only Hugging Face service."""

import json
import os
from dataclasses import dataclass
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd


class RemoteRetrievalError(RuntimeError):
    """Raised when the remote retrieval service cannot return valid results."""


@dataclass(frozen=True)
class RemoteRetriever:
    """Retrieve and rerank candidates through the configured HF service."""

    base_url: str
    token: str
    timeout_seconds: float = 120.0
    max_retries: int = 1

    @classmethod
    def from_environment(cls) -> "RemoteRetriever":
        base_url = os.getenv("RETRIEVAL_SERVICE_URL", "").strip().rstrip("/")
        token = os.getenv("RETRIEVAL_SERVICE_TOKEN", "").strip()
        if not base_url:
            raise RemoteRetrievalError("RETRIEVAL_SERVICE_URL is not configured.")
        if not token:
            raise RemoteRetrievalError("RETRIEVAL_SERVICE_TOKEN is not configured.")
        return cls(
            base_url=base_url,
            token=token,
            timeout_seconds=float(os.getenv("RETRIEVAL_SERVICE_TIMEOUT", "120")),
            max_retries=int(os.getenv("RETRIEVAL_SERVICE_RETRIES", "1")),
        )

    def retrieve_and_rerank(
        self,
        semantic_query: str,
        rerank_query: str,
        semantic_top_k: int,
        rerank_artifact_ids: list[str],
    ) -> pd.DataFrame:
        payload = {
            "semantic_query": semantic_query,
            "rerank_query": rerank_query,
            "semantic_top_k": semantic_top_k,
            "rerank_artifact_ids": list(dict.fromkeys(rerank_artifact_ids)),
        }
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}/retrieve",
            data=body,
            headers={
                "Authorization": "Bearer " + self.token,
                "Content-Type": "application/json",
            },
            method="POST",
        )

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    result = json.loads(response.read().decode("utf-8"))
                return self._validate_response(result)
            except (HTTPError, URLError, TimeoutError, ValueError, OSError) as error:
                last_error = error
                if attempt >= self.max_retries:
                    break

        raise RemoteRetrievalError(
            f"Remote retrieval request failed after {self.max_retries + 1} attempts: "
            f"{last_error}"
        )

    @staticmethod
    def _validate_response(result: Any) -> pd.DataFrame:
        if not isinstance(result, dict) or not isinstance(result.get("results"), list):
            raise RemoteRetrievalError("Remote retrieval response has an invalid shape.")

        rows = []
        for item in result["results"]:
            if not isinstance(item, dict):
                raise RemoteRetrievalError("Remote retrieval result is not an object.")
            required = {"artifact_id", "artifact_type", "text", "similarity", "reranker_score"}
            if not required.issubset(item):
                raise RemoteRetrievalError("Remote retrieval result is missing fields.")
            rows.append(
                {
                    "id": str(item["artifact_id"]),
                    "type": str(item["artifact_type"]),
                    "text": str(item["text"]),
                    "semantic_similarity": float(item["similarity"])
                    if item["similarity"] is not None
                    else float("nan"),
                    "reranker_score": float(item["reranker_score"]),
                }
            )

        return pd.DataFrame(rows)
