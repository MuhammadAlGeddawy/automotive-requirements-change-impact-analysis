"""Retrieval: embedding model, FAISS index, cross-encoder reranking."""

from typing import Optional

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import CrossEncoder, SentenceTransformer


EMBED_MODEL = "all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class RetrievalEngine:
    """Hybrid retrieval engine with Sentence Transformer embeddings, FAISS index,
    and Cross-Encoder reranking."""

    def __init__(
        self,
        embed_model: str = EMBED_MODEL,
        reranker_model: str = RERANKER_MODEL,
    ):
        self.embed_model_name = embed_model
        self.reranker_model_name = reranker_model
        self._embedder: Optional[SentenceTransformer] = None
        self._reranker: Optional[CrossEncoder] = None
        self._index: Optional[faiss.IndexFlatIP] = None
        self._artifacts_df: Optional[pd.DataFrame] = None

    @property
    def embedder(self) -> SentenceTransformer:
        if self._embedder is None:
            self._embedder = SentenceTransformer(self.embed_model_name)
        return self._embedder

    @property
    def reranker(self) -> CrossEncoder:
        if self._reranker is None:
            self._reranker = CrossEncoder(self.reranker_model_name)
        return self._reranker

    def build_index(self, artifacts: list[dict]) -> "RetrievalEngine":
        """Build FAISS index from artifact records."""
        self._artifacts_df = pd.DataFrame(artifacts)

        embeddings = self.embedder.encode(
            self._artifacts_df["text"].tolist(),
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        dimension = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dimension)
        self._index.add(np.asarray(embeddings, dtype="float32"))

        return self

    def semantic_retrieve(self, query: str, top_k: int = 15) -> pd.DataFrame:
        """Retrieve top-k candidates using FAISS semantic search."""
        if self._index is None or self._artifacts_df is None:
            raise RuntimeError("Index not built. Call build_index() first.")

        query_embedding = self.embedder.encode(
            [query],
            normalize_embeddings=True,
        )

        scores, indices = self._index.search(
            np.asarray(query_embedding, dtype="float32"),
            top_k,
        )

        results = self._artifacts_df.iloc[indices[0]].copy()
        results["similarity"] = scores[0]
        return results.reset_index(drop=True)

    def rerank(
        self,
        query: str,
        candidates_df: pd.DataFrame,
    ) -> pd.Series:
        """Rerank candidates using cross-encoder."""
        pairs = [
            (query, text)
            for text in candidates_df["text"].tolist()
        ]
        scores = self.reranker.predict(pairs, show_progress_bar=False)
        return pd.Series(scores, index=candidates_df.index)
