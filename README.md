# NASAQ - Change Impact Review

NASAQ is an engineering intelligence application for reviewing the impact of
automotive requirement changes. The current product UI is a React/Vite
frontend backed by a FastAPI adapter over the existing Python analysis
pipeline. The original Streamlit application remains available as a fallback.

## Features

- **Hybrid Retrieval Pipeline**: Combines traceability graph traversal,
  FAISS semantic search (Sentence Transformers), and Cross-Encoder reranking
- **Hybrid Ranking**: Weighted combination of reranker (0.45), graph linkage
  (0.35), and semantic similarity (0.20) scores
- **LLM Impact Assessment**: Uses OpenRouter API to classify candidates as
  DIRECT, POTENTIAL, or NO_IMPACT with confidence, reason, and evidence
- **Graph Traceability Visualization**: View traceability paths for selected
  artifacts
- **Missing Traceability Detection**: Highlights GRAPH-UNLINKED artifacts
  retrieved semantically as potential missing traceability signals
- **Evaluation Metrics**: Built-in Recall@k, Precision@k, F1@k evaluation
  against ground truth

## Architecture

```
api.py                  ← FastAPI adapter used by the React frontend
app.py                  ← Streamlit fallback UI
frontend/
├── src/components/     ← NASAQ UI components
├── src/data/           ← Legacy mock data/reference shapes
├── src/api.js          ← Frontend API client
└── src/styles/         ← Global styles
src/
├── data_loader.py      ← CSV loading + traceability graph construction
├── retrieval.py        ← Embedding model + FAISS index + Cross-Encoder
├── llm_assessment.py   ← OpenRouter LLM client + Pydantic schema
├── orchestrator.py     ← analyze_change(change_id) service boundary
└── ...
tests/
├── test_pipeline.py    ← Core logic + baseline evaluation tests
└── test_llm.py         ← LLM module unit tests
```

## Setup

### Prerequisites

- Python 3.9+
- OpenRouter API key (for LLM features)

### Installation

```bash
# Clone or navigate to the project
cd cia-mvp

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Environment variables

```bash
# Windows
copy .env.example .env

# Edit .env and add your OpenRouter API key.
# OPENROUTER_API_KEY=sk-or-...
```

The FastAPI adapter loads `.env` automatically. Do not commit `.env` or
expose the API key in frontend code.

## Running the NASAQ frontend

Start the backend and frontend in separate terminals. Run the backend from the
repository root:

```powershell
python -m uvicorn api:app --host 127.0.0.1 --port 8765
```

Then run the frontend from the `frontend/` directory:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally
`http://localhost:5173/`. The frontend calls:

- `GET http://127.0.0.1:8765/api/change-requests`
- `POST http://127.0.0.1:8765/api/analyze/{change_id}`

The API port is `8765` because some Windows environments reserve port 8000.
Keep both terminals running while using NASAQ. The first analysis after
starting the backend may take longer while the embedding model, FAISS index,
and reranker load. These resources are cached and reused for later analyses in
the same backend process.

## Free website deployment

NASAQ is deployed as two public services: Vercel serves the static React
website, while Render runs the FastAPI analysis API. This keeps the OpenRouter
credential and the ML pipeline on the server instead of exposing either in
browser code.

### 1. Deploy the API to Render

1. Push the repository to GitHub and create a new **Web Service** in Render
   from that repository.
2. Select the Docker runtime. Render will use the root `Dockerfile` (the
   included `render.yaml` can also be used as a Blueprint).
3. Add these environment variables in Render:
   - `OPENROUTER_API_KEY`: your OpenRouter key.
   - `ALLOWED_ORIGINS`: the Vercel URL, for example
     `https://nasaq.vercel.app`. Multiple origins can be comma-separated.
4. Deploy and verify `https://<render-service>.onrender.com/health` returns
   `{"status":"ok"}`. Copy the service URL for the frontend step.

The Render free service can sleep after inactivity, so the first request may
be slow. The first analysis also downloads and loads the embedding and
reranker models. They are cached for the lifetime of the service process.
The ML dependency stack may exceed the memory available on some free
instances; if the service is repeatedly killed or the build fails, use a
larger Render instance or a host with more memory rather than exposing the
OpenRouter key in the frontend.

### 2. Deploy the frontend to Vercel

1. Import the same GitHub repository into Vercel.
2. Keep the repository root as the project root; `vercel.json` configures the
   `frontend/` build automatically.
3. Add the environment variable
   `VITE_API_BASE_URL=https://<render-service>.onrender.com`.
4. Deploy, then add the resulting Vercel URL to Render's `ALLOWED_ORIGINS` and
   redeploy the API if needed.

The frontend can also be deployed with the Vercel CLI from the repository
root:

```powershell
vercel
```

Never put `OPENROUTER_API_KEY` in `frontend/.env`, `VITE_*` variables, or
committed files. Vite bundles `VITE_*` values into public JavaScript.

### Running the Streamlit fallback

The original Streamlit interface remains available independently:

```bash
streamlit run app.py
# Or use the wrapper, which also loads .env:
python run.py
```

It opens at `http://localhost:8501`.

### Frontend usage

1. **Select a Change Request** from the sidebar (CR-001 through CR-005)
2. Review the previous and updated requirement text.
3. Click **Analyze Impact** to run the real retrieval and LLM pipeline.
4. Review KPI totals, compound impact labels, confidence, and traceability flags.
5. Select an artifact in the Impact Chain section to view its full graph path.
6. Double-click engineering content in the table to expand or collapse it.

If the frontend reports `Failed to fetch`, confirm that the FastAPI terminal is
still running and that `http://127.0.0.1:8765/api/change-requests` returns JSON.
If analysis fails because the OpenRouter key is missing or invalid, verify
`OPENROUTER_API_KEY` in `.env` and restart the backend.

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src

# Run only evaluation baseline tests
pytest tests/test_pipeline.py::TestEvaluationBaseline -v
```

## Evaluation Baseline

The pipeline is expected to achieve the following metrics on CR-001:

| Metric   | Baseline | Target |
|----------|----------|--------|
| Recall@10 | ~0.75   | >=0.60 |
| F1@10    | ~0.67   | >=0.50 |

Run the baseline tests to verify:

```bash
pytest tests/test_pipeline.py::TestEvaluationBaseline -v
```

## Pipeline Details

### 1. Data Loading
Loads CSV files from `dataset/` and builds a NetworkX directed graph
representing traceability relationships between artifacts.

### 2. Retrieval
- Embeds all artifacts using `all-MiniLM-L6-v2` Sentence Transformer
- Builds a FAISS Inner Product index for fast semantic search
- Retrieves top-K candidates using a change query constructed from
  the OLD/NEW requirement texts

### 3. Graph Candidates
Performs graph traversal from the changed stakeholder requirement to
find all downstream descendants (excluding stakeholder requirements).

### 4. Reranking
Uses `cross-encoder/ms-marco-MiniLM-L-6-v2` to rerank the combined
candidate pool.

### 5. Hybrid Ranking
Combines normalized scores:
- 45% Cross-Encoder reranker score
- 35% Graph linkage (binary)
- 20% Semantic similarity

### 6. LLM Assessment
Sends top-10 candidates to OpenRouter API with a structured prompt
requesting Pydantic-validated JSON output.

## Dataset

The `dataset/` directory contains synthetic automotive engineering artifacts:

| File | Description |
|------|-------------|
| stakeholder_requirements.csv | Top-level stakeholder needs |
| system_requirements.csv | System-level requirements |
| software_requirements.csv | Software requirements |
| components.csv | Software components |
| test_cases.csv | Test cases |
| traceability.csv | Traceability links between artifacts |
| requirement_versions.csv | Version history |
| change_requests.csv | Change requests with OLD/NEW texts |
| expected_impacts.csv | Ground truth impact labels |

The dataset intentionally includes invalid and missing traceability links
to test the system's ability to recover missing traces semantically.

## Known Limitations

- LLM features require an active OpenRouter API key and internet connection.
  The LLM is always run as part of the pipeline (as in the original notebook).
  If no API key is set, a warning is shown but retrieval results are still displayed.
- The embedding and reranker models require ~500MB download on first run
- The synthetic dataset is small; real-world performance may vary
- Graph visualization is limited to path display (no full graph rendering)
- No persistent storage of analysis results
- Streamlit reruns on widget interaction; analysis results are cached in
  session state to avoid redundant computation

## License

Synthetic data for experimentation only. Not an actual OEM project.
