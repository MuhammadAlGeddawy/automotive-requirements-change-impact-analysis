---
title: NASAQ Retrieval Service
emoji: 🔎
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# NASAQ Retrieval Service

Private retrieval service for NASAQ's change-impact-analysis backend.

The service eagerly loads the fixed embedding model, Cross-Encoder reranker,
artifact corpus, and FAISS index before `/readiness` reports ready.

## Endpoints

- `GET /health` — process health
- `GET /readiness` — model/index readiness and dataset metadata
- `POST /retrieve` — authenticated semantic retrieval plus reranking

`POST /retrieve` requires:

```text
Authorization: Bearer <RETRIEVAL_SERVICE_TOKEN>
```

The service does not own graph traversal, hybrid scoring, OpenRouter calls, or
frontend logic. Render sends graph candidate IDs so the service preserves the
existing semantic-candidate plus graph-candidate reranking behavior.

## Required secret

Configure `RETRIEVAL_SERVICE_TOKEN` in the Space secrets. Model revisions are
pinned in `app.py` and can only be overridden deliberately through Space
variables.
