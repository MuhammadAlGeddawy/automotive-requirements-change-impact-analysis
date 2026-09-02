# NASAQ - Change Impact Review (Local Streamlit MVP)

A user-friendly local Streamlit application for reviewing the impact of
change requests on automotive engineering artifacts using hybrid retrieval
(graph + semantic + cross-encoder reranking) and AI-based impact assessment.

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
app.py                  ← Streamlit UI (single page)
src/
├── data_loader.py      ← CSV loading + traceability graph construction
├── retrieval.py        ← Embedding model + FAISS index + Cross-Encoder
├── llm_assessment.py   ← OpenRouter LLM client + Pydantic schema
├── orchestrator.py     ← analyze_change(change_id) service boundary
└── evaluation.py       ← (in orchestrator) metrics computation
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

### Environment Variables

```bash
# Copy the example
copy .env.example .env

# Edit .env and add your OpenRouter API key
# OPENROUTER_API_KEY=sk-or-...
```

The `.env` file is loaded automatically by the app (via `python-dotenv`
if available, or set the variable in your shell).

## Running the App

```bash
# Option 1: Direct streamlit command
streamlit run app.py

# Option 2: Using the run.py wrapper (loads .env automatically)
python run.py
```

The app will open in your browser at `http://localhost:8501`.

### Usage

1. **Select a Change Request** from the sidebar (CR-001 through CR-005)
2. Review the OLD and NEW requirement texts (color-coded: red=old, green=new)
3. Click **"Analyze Change Impact"** to run the full pipeline (retrieval + LLM)
4. View the **ranked candidate artifacts** table with hybrid scores
5. Check the **evaluation metrics** (Recall@k, F1@k)
6. Select an artifact in the detail panel to view its **full content and traceability paths**
7. Review **LLM Impact Assessment** for each candidate (DIRECT/POTENTIAL/NO_IMPACT)
8. Examine **GRAPH-UNLINKED** artifacts for potential missing traceability

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
