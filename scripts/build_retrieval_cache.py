"""Build the offline retrieval cache used by low-memory Render deployments."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_loader import build_graph, get_artifact_records, load_data
from src.orchestrator import _get_downstream_nodes
from src.retrieval import RetrievalEngine


def _queries(change) -> tuple[str, str]:
    old_text, new_text = change["old_text"], change["new_text"]
    change_type, reason = change["change_type"], change["reason"]
    semantic = f"""Changed stakeholder requirement:

OLD:
{old_text}

NEW:
{new_text}

Change type:
{change_type}

Reason:
{reason}

Find engineering artifacts that may be affected by this change.""".strip()
    rerank = f"""A stakeholder requirement changed.

OLD:
{old_text}

NEW:
{new_text}

Change type:
{change_type}

Determine whether the engineering artifact below is relevant
to assessing the impact of this change.""".strip()
    return semantic, rerank


def build_cache(output: Path) -> None:
    data = load_data()
    graph = build_graph(data)
    artifacts = get_artifact_records(data)
    source_engine = RetrievalEngine().build_index(artifacts)
    output.mkdir(parents=True, exist_ok=True)
    np.save(output / "artifact_embeddings.npy", source_engine._index.reconstruct_n(0, len(artifacts)))
    source_engine._artifacts_df.to_json(output / "artifacts.json", orient="records")

    query_embeddings = {}
    reranker_scores = {}
    for _, change in data["changes"].iterrows():
        key = str(change["change_id"])
        semantic_query, rerank_query = _queries(change)
        query_embeddings[key] = source_engine.embedder.encode(
            [semantic_query], normalize_embeddings=True
        )[0]
        graph_ids = _get_downstream_nodes(graph, str(change["requirement_id"]))
        semantic = source_engine.semantic_retrieve(semantic_query, top_k=15)
        candidate_ids = list(dict.fromkeys(graph_ids + semantic["id"].tolist()))
        candidates = source_engine._artifacts_df[
            source_engine._artifacts_df["id"].isin(candidate_ids)
        ]
        scores = source_engine.rerank(rerank_query, candidates)
        reranker_scores[key] = {
            str(artifact_id): float(score)
            for artifact_id, score in zip(candidates["id"], scores)
        }

    np.savez(output / "query_embeddings.npz", **query_embeddings)
    with (output / "reranker_scores.json").open("w", encoding="utf-8") as handle:
        json.dump(reranker_scores, handle, indent=2)
    corpus_bytes = (output / "artifacts.json").read_bytes()
    metadata = {
        "embedding_model": source_engine.embed_model_name,
        "reranker_model": source_engine.reranker_model_name,
        "change_ids": sorted(query_embeddings),
        "artifact_count": len(artifacts),
        "corpus_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
    }
    with (output / "metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
    print(f"Retrieval cache written to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("retrieval_cache"))
    build_cache(parser.parse_args().output)
