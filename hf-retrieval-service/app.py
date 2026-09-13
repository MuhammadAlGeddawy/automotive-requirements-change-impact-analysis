"""Retrieval-only FastAPI service for the Hugging Face Docker Space."""

import hashlib
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import faiss
import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from sentence_transformers import CrossEncoder, SentenceTransformer


SERVICE_ROOT = Path(__file__).resolve().parent
CORPUS_PATH = SERVICE_ROOT / "dataset" / "artifacts.csv"
SERVICE_TOKEN = os.getenv("RETRIEVAL_SERVICE_TOKEN", "").strip()
EMBED_MODEL = "all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
EMBED_REVISION = os.getenv(
    "EMBED_MODEL_REVISION",
    "1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
).strip()
RERANKER_REVISION = os.getenv(
    "RERANKER_MODEL_REVISION",
    "233902d25c440f23af6f7d6e94d2946bac0bee0a",
).strip()


class RetrieveRequest(BaseModel):
    semantic_query: str = Field(min_length=1, max_length=12000)
    rerank_query: str = Field(min_length=1, max_length=12000)
    semantic_top_k: int = Field(default=15, ge=1, le=100)
    rerank_artifact_ids: list[str] = Field(default_factory=list, max_length=500)


class RetrievalService:
    def __init__(self) -> None:
        self.corpus = pd.read_csv(CORPUS_PATH)
        self.embedder = SentenceTransformer(EMBED_MODEL, revision=EMBED_REVISION)
        self.reranker = CrossEncoder(RERANKER_MODEL, revision=RERANKER_REVISION)
        embeddings = self.embedder.encode(
            self.corpus["text"].tolist(),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        self.index = faiss.IndexFlatIP(embeddings.shape[1])
        self.index.add(np.asarray(embeddings, dtype="float32"))
        self.dataset_version = self._dataset_version()

    def _dataset_version(self) -> str:
        digest = hashlib.sha256(CORPUS_PATH.read_bytes()).hexdigest()
        return f"sha256:{digest}"

    def retrieve(self, request: RetrieveRequest) -> list[dict[str, Any]]:
        query_embedding = self.embedder.encode(
            [request.semantic_query],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        scores, indices = self.index.search(
            np.asarray(query_embedding, dtype="float32"),
            request.semantic_top_k,
        )

        semantic_scores = {
            str(self.corpus.iloc[index]["id"]): float(score)
            for index, score in zip(indices[0], scores[0])
        }
        candidate_ids = list(
            dict.fromkeys(
                list(semantic_scores) + request.rerank_artifact_ids
            )
        )
        candidates = (
            self.corpus.set_index("id")
            .loc[[artifact_id for artifact_id in candidate_ids]]
            .reset_index()
        )
        pairs = [(request.rerank_query, text) for text in candidates["text"].tolist()]
        reranker_scores = self.reranker.predict(pairs, show_progress_bar=False)
        candidates["reranker_score"] = reranker_scores
        candidates["similarity"] = candidates["id"].map(semantic_scores)
        return [
            {
                "artifact_id": str(row["id"]),
                "artifact_type": str(row["type"]),
                "text": str(row["text"]),
                "similarity": None if pd.isna(row["similarity"]) else float(row["similarity"]),
                "reranker_score": float(row["reranker_score"]),
            }
            for _, row in candidates.iterrows()
        ]


service: RetrievalService | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global service
    service = RetrievalService()
    yield
    service = None


app = FastAPI(title="NASAQ Retrieval Service", lifespan=lifespan)


def require_token(authorization: str | None = Header(default=None)) -> None:
    if not SERVICE_TOKEN or authorization != "Bearer " + SERVICE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid retrieval service token.")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readiness")
def readiness() -> dict[str, Any]:
    if service is None:
        raise HTTPException(status_code=503, detail="Retrieval service is initializing.")
    return {
        "status": "ready",
        "dataset_version": service.dataset_version,
        "embedding_model": EMBED_MODEL,
        "embedding_revision": EMBED_REVISION,
        "reranker_model": RERANKER_MODEL,
        "reranker_revision": RERANKER_REVISION,
        "artifact_count": len(service.corpus),
    }


@app.post("/retrieve", dependencies=[Depends(require_token)])
def retrieve(request: RetrieveRequest) -> dict[str, Any]:
    if service is None:
        raise HTTPException(status_code=503, detail="Retrieval service is not ready.")
    unknown_ids = set(request.rerank_artifact_ids) - set(service.corpus["id"])
    if unknown_ids:
        raise HTTPException(status_code=422, detail="Unknown artifact ID supplied.")
    return {
        "dataset_version": service.dataset_version,
        "embedding_model": EMBED_MODEL,
        "embedding_revision": EMBED_REVISION,
        "reranker_model": RERANKER_MODEL,
        "reranker_revision": RERANKER_REVISION,
        "results": service.retrieve(request),
    }
