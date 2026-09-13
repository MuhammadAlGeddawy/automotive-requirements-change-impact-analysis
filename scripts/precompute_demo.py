"""Generate the complete offline NASAQ demo payload."""

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")
secrets_path = PROJECT_ROOT / ".streamlit" / "secrets.toml"
if not os.getenv("OPENROUTER_API_KEY") and secrets_path.exists():
    secrets_text = secrets_path.read_text(encoding="utf-8")
    match = re.search(
        r"OPENROUTER_API_KEY\s*=\s*[\"']?([^\"'\s]+)",
        secrets_text,
    )
    secret_key = match.group(1) if match else None
    if secret_key:
        os.environ["OPENROUTER_API_KEY"] = str(secret_key)

from api import _analysis_payload, _change_request_payload
from src.data_loader import build_graph, load_data
from src.orchestrator import _get_pipeline_resources, analyze_change


def precompute(output_dir: Path, skip_llm: bool = False) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = load_data()
    graph = build_graph(data)

    requests = [
        _change_request_payload(row)
        for _, row in data["changes"].iterrows()
    ]
    with (output_dir / "change_requests.json").open("w", encoding="utf-8") as handle:
        json.dump(requests, handle, indent=2)

    graph_payload = {
        "nodes": [
            {"id": str(node_id), **{key: str(value) for key, value in attrs.items()}}
            for node_id, attrs in graph.nodes(data=True)
        ],
        "edges": [
            {"source": str(source), "target": str(target), **{
                key: str(value) for key, value in attrs.items()
            }}
            for source, target, attrs in graph.edges(data=True)
        ],
    }
    with (output_dir / "traceability_graph.json").open("w", encoding="utf-8") as handle:
        json.dump(graph_payload, handle, indent=2)

    retrieval_cache = output_dir / "retrieval_cache"
    from scripts.build_retrieval_cache import build_cache

    build_cache(retrieval_cache)
    os.environ["RETRIEVAL_CACHE_DIR"] = str(retrieval_cache)
    from src.orchestrator import clear_pipeline_cache

    clear_pipeline_cache()

    analyses_dir = output_dir / "analyses"
    analyses_dir.mkdir(exist_ok=True)
    for request in requests:
        change_id = request["id"]
        result = None
        for attempt in range(3):
            result = analyze_change(change_id, skip_llm=skip_llm)
            if not result.error or skip_llm:
                break
            if attempt < 2:
                print(
                    f"{change_id} assessment failed; retrying "
                    f"({attempt + 1}/2): {result.error}"
                )
                time.sleep(2)
        if result.error and result.llm_assessments is None:
            raise RuntimeError(f"{change_id} precomputation failed: {result.error}")
        payload = {
            "changeId": result.change_id,
            "requirementId": result.requirement_id,
            **_analysis_payload(result),
        }
        with (analyses_dir / f"{change_id}.json").open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=str)

    manifest = {
        "mode": "precomputed-demo",
        "llm_precomputed": not skip_llm,
        "change_request_ids": [request["id"] for request in requests],
        "analysis_count": len(requests),
        "includes": [
            "change_requests.json",
            "traceability_graph.json",
            "retrieval_cache",
            "analyses",
        ],
    }
    with (output_dir / "manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
    print(f"Precomputed {len(requests)} demo analyses in {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "precomputed_data")
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Generate retrieval-only fixtures for local validation; not production demo data.",
    )
    args = parser.parse_args()
    if args.output.exists():
        shutil.rmtree(args.output)
    precompute(args.output, skip_llm=args.skip_llm)
