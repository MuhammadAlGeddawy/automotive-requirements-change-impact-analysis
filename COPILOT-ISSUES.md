# GitHub Copilot Coding Agent — NASAQ Frontend Rebuild

How to use this file: create one GitHub issue per section below, in order, and assign each to Copilot's coding agent one at a time. Wait for the PR, review it, and merge before assigning the next one — later issues depend on earlier ones existing. Each issue references `DESIGN.md`, which should be committed to the repo root before you assign Issue 1.

All data in this phase is mocked (hardcoded JSON/objects in the frontend) — no backend calls yet. Mock data shapes below are deliberately modeled on the real backend (a hybrid retrieval + LLM impact-assessment pipeline, with an `analyze_change(change_id)` service boundary already implemented in `src/orchestrator.py`) so that wiring up the real API later — see Issue 7 — is closer to a drop-in swap than a redesign.

**Naming:** see the note in `DESIGN.md` — use "NASAQ" in all UI copy even though the underlying repo/README calls the project "ENGYN."

---

## Issue 1: Scaffold the project

**Title:** Scaffold NASAQ frontend with React, Vite, and Tailwind CSS

**Body:**
Set up a new React + Vite + Tailwind CSS project for the NASAQ frontend rebuild, replacing the previous Streamlit implementation.

Tasks:
- Initialize a Vite + React project (JavaScript, not TypeScript) at the repo root or in a `/frontend` directory (your choice — pick whichever fits the existing repo structure, and note your choice in the PR description).
- Install and configure Tailwind CSS.
- Read `DESIGN.md` and extend the Tailwind config's `theme` with the color tokens, border radius, and spacing scale defined there (as custom Tailwind theme values, not just raw CSS variables).
- Install `lucide-react` for icons.
- Create a basic folder structure: `src/components/`, `src/data/` (for mock data files), `src/styles/`.
- Replace the default Vite starter page with a blank page that just renders the text "NASAQ" using the `color-heading` token, to confirm the Tailwind theme is wired up correctly.
- Add a root-level README section (or new `FRONTEND.md`) explaining how to run the dev server.

**Acceptance criteria:**
- `npm install && npm run dev` starts a working dev server with no console errors.
- The page renders "NASAQ" in the correct heading color from the Tailwind theme (not a hardcoded hex in the component).
- Tailwind config contains the color tokens from `DESIGN.md` as named theme colors (e.g. `brand-dark`, `accent`, `bg-cream`, etc.).

---

## Issue 2: Global styles, layout shell, and gradient mesh background

**Title:** Build the app shell — sidebar/content layout and background gradient mesh

**Body:**
Reference `DESIGN.md` for all colors and the glass/gradient-mesh specification.

Tasks:
- Build a two-column app shell: a fixed-width dark green sidebar (`color-brand-dark`, subtle gradient to `color-brand-dark-alt` top-to-bottom) and a main content area on `color-bg-cream`.
- Implement the background gradient mesh described in `DESIGN.md` as a component that renders behind all content. **Critical:** it must have `pointer-events: none` and a z-index below all content — verify by clicking through the full page and confirming every interactive element still works with the mesh present.
- Add a simple top bar in the main content area with placeholder "Deploy" text and an "MVP v0.4" badge/pill (styled per `DESIGN.md`, no functionality needed yet).
- Sidebar and main content should both be empty/placeholder at this stage aside from the top bar — component content comes in later issues.

**Acceptance criteria:**
- Layout renders correctly with sidebar fixed on the left, content area filling the rest.
- The gradient mesh is visible but subtle, and does not block clicks on any element in front of it (test by adding a temporary button and confirming it's clickable).
- Resizing the browser window narrower doesn't break the layout (sidebar can remain fixed-width for now; full responsive behavior comes in a later issue).

---

## Issue 3: Sidebar components with mock data

**Title:** Build sidebar sections — upload, change request selector, request details, assessment engine

**Body:**
Reference `DESIGN.md` for the sidebar component spec and glass dropdown styling.

Create a mock data file at `src/data/changeRequests.js` with an array of 5 mock change requests (CR-001 through CR-005). Field names below mirror the real dataset's `change_requests.csv` + `requirement_versions.csv` columns (adapted to camelCase) so this file is easy to delete wholesale once Issue 7 wires up the real API: `id` (e.g. "CR-001"), `requirementId` (e.g. "SR-001", the stakeholder requirement being changed), `changeType` (e.g. "parameter_change"), `description` (the human-readable rationale, e.g. "Customer increased obstacle detection range"), `oldText` (the previous requirement wording), `newText` (the updated wording), `changedValueOld` / `changedValueNew` (the specific token that differs between `oldText` and `newText`, for the inline highlight — this pair is a frontend-only convenience derived from diffing `oldText`/`newText`, not a real dataset column, so note that clearly in a code comment).

Tasks:
- **Upload section:** a dashed-border dropzone with an upload icon (Lucide, not an icon font) and label text — no real file upload logic needed yet, just the visual component and an `onDrop`/`onClick` handler that logs to console.
- **Change Request selector:** a dropdown showing the mock change requests. When open, the option list must use the glass surface recipe from `DESIGN.md`, with proper hover states, a visible selected-state indicator, and correct z-index so it never overlaps or gets overlapped by other content.
- **Request Details card:** a nested card (visually distinct background from the sidebar) showing the currently selected change request's Request ID, Requirement ID, Change type, and description, each with a small Lucide icon.
- **Assessment Engine field:** a read-only field showing a model identifier string (e.g. "nvidia/nemotron-3.5-lightning:free") and a status line below it (e.g. "Review engine ready"). This mirrors a real config value (the OpenRouter model used for LLM impact assessment in `src/llm_assessment.py`), not decorative text — keep it as an easily-swappable constant/prop rather than burying it inline, since Issue 7 will make it dynamic.

**Acceptance criteria:**
- Selecting a different change request in the dropdown updates the Request Details card below it.
- The dropdown list is fully readable (no low-contrast text), doesn't visually overlap the description text beneath it, and closes when clicking outside it.
- No icon-font ligature text is visible anywhere (all icons are Lucide SVG components).

---

## Issue 4: Change Request Review — stepper and comparison cards

**Title:** Build the stepper and requirement diff comparison cards

**Body:**
Reference `DESIGN.md` for stepper and comparison card specs.

Tasks:
- **Stepper:** horizontal 3-step indicator (Select Change → Analyze Impact → Review Results) at the top of the main content area, below the top bar. Accept a `currentStep` prop (1, 2, or 3) and highlight that step in `color-accent`; completed steps get a checkmark, upcoming steps are muted.
- **Comparison cards:** two side-by-side cards using the currently selected mock change request's `oldText`/`newText`. Previous card uses `color-diff-prev-bg`/`color-diff-prev-border`; updated card uses `color-diff-next-bg`/`color-diff-next-border`. Within each card's text, the specific changed value (`changedValueOld` / `changedValueNew`) must be visually highlighted (bold + a subtle background pill), not just present in the full sentence.
- Add a small arrow icon between the two cards (visible on wider screens, can stack/hide on narrow ones).
- Below the cards, show the change type and description as plain text (small, muted, per `DESIGN.md` typography).

**Acceptance criteria:**
- Changing the selected change request in the sidebar (Issue 3) updates the comparison cards' content.
- The specific changed value is visually distinguishable from the rest of the sentence at a glance, without reading the full text.
- Stepper accurately reflects a `currentStep` value passed to it (test by hardcoding different values temporarily).

---

## Issue 5: Analyze Impact button and KPI stat cards

**Title:** Build the Analyze Impact CTA and glass KPI stat cards with mock results

**Body:**
Create a mock data file at `src/data/impactResults.js` with a mock result object: `{ highImpact: 4, mediumImpact: 1, lowImpact: 17, totalAffected: 23 }`. Note: Issue 6 will extend this same file with the full `artifacts` array (by `impactTier`) — when that happens, these counts should actually match the `impactTier` distribution in that array rather than being independent numbers, so keep that in mind if you adjust either later.

Tasks:
- **Analyze Impact button:** solid `color-accent` button below the comparison cards, full-width, with distinct hover/active states. Clicking it should trigger a mock "loading" state (a spinner or pulsing bar, ~1.5s simulated delay via `setTimeout`) and then reveal the KPI stat cards section below. Add a disabled state (grayed, `not-allowed` cursor) for when no change request is selected.
- **KPI stat cards:** 4 cards in a row (High Impact, Medium Impact, Low Impact, Total Affected) using the glass surface recipe from `DESIGN.md`, each showing the number prominently and a short caption beneath (e.g. "Directly affected", "Requires review", "No impact identified", "Ranked artifacts").
- Cards should be hidden until the mock analysis "completes," then animate/fade in.

**Acceptance criteria:**
- Clicking Analyze Impact with a change request selected shows the loading state, then reveals correctly populated KPI cards after the simulated delay.
- Clicking Analyze Impact with nothing selected does nothing (button is visibly disabled).
- KPI cards visibly use the glass effect (translucent + blurred) against the gradient mesh background from Issue 2 — take a screenshot in the PR description showing this.

---

## Issue 6: Impact Chain and Impacted Artifacts table

**Title:** Build the Impact Chain visualization and the Impacted Artifacts data table

**Body:**
Extend `src/data/impactResults.js` with:
- `impactChain`: array of `{ id, type }`, e.g. `[{id: "SR-001", type: "stakeholder requirement"}, {id: "SYS-001", type: "system requirement"}, {id: "SWR-001", type: "software requirement"}, {id: "TC-001", type: "test case"}]`
- `artifacts`: array of ~10 mock rows. **This is the important part to get right** — the real pipeline classifies each artifact along two independent dimensions, and the table needs to show both, not one collapsed value. Fields: `artifactId` (e.g. "SYS-001"), `artifactType` (e.g. "system_requirement"), `impactTier` ("high" | "medium" | "low" — an aggregate severity bucket), `llmLabel` ("DIRECT" | "POTENTIAL" | "NO_IMPACT" — the LLM's own classification), `confidence` (0–1), `traceability` ("linked" | "graph_unlinked" — most rows should be "linked"; include at least 2 mock rows as "graph_unlinked" to exercise that state), `engineeringContent` (a full sentence, some long enough to require truncation).
  - Make sure your mock values are internally consistent with real-world expectations: rows with `llmLabel: "DIRECT"` should generally have `impactTier: "high"` and higher `confidence` (e.g. ~0.9+); `"NO_IMPACT"` rows should generally be `impactTier: "low"` with lower confidence (e.g. ~0.5). This mirrors the real hybrid ranking + LLM assessment output and keeps the mock believable.

Tasks:
- **Impact Chain:** row of glass-surface boxes (per `DESIGN.md`) connected by arrow icons, showing each artifact ID (monospace) and its type.
- **Impacted Artifacts table:** solid card container (not glass) with:
  - Sticky/distinct header row.
  - **Impact column is a compound badge**, per `DESIGN.md`: one pill combining `impactTier` (drives color, via the badge tokens) and `llmLabel` (shown after a middot, e.g. "HIGH · DIRECT", "LOW · NO_IMPACT") — not two separate columns, not a single flattened value.
  - **Traceability column:** normal rows show a plain "Linked" label; `graph_unlinked` rows render using the `flag-unlinked` tokens from `DESIGN.md` (dashed amber border, warning icon, "GRAPH-UNLINKED" text) so they visually stand out as needing review.
  - Confidence column: the number plus a small horizontal bar indicator reflecting its value, right-aligned.
  - Artifact ID column in monospace.
  - Engineering Content column: truncate with an ellipsis at a reasonable character limit, with the full text available via a `title` attribute (native tooltip) on hover.
  - Row hover highlight.
  - If the table's content width exceeds its container, it should scroll horizontally with a visible scrollbar rather than compressing columns unreadably.
- Both sections only render after the mock "analysis" from Issue 5 completes (reuse that state).

**Acceptance criteria:**
- Table renders all mock rows with correctly styled compound impact badges (tier color + LLM label text together in one pill).
- The `graph_unlinked` mock rows are visually distinct from normal "Linked" rows at a glance, not just via different text.
- Long engineering content text truncates cleanly (no mid-word cutoff) and shows the full text on hover.
- Table remains usable (readable, scrollable, no broken layout) at a narrow viewport width (~375px) — check this in the PR description with a screenshot.

---

## Issue 7 (later — do not assign yet): Wire up the real backend

Hold this until the mocked frontend (Issues 1–6) is reviewed and you're ready to connect it for real. Included here now, in detail, because the backend already has a clean shape that makes this easier than it might sound:

**What already exists** (per the project's README): `src/orchestrator.py` exposes `analyze_change(change_id)` as a service boundary — it already runs the full pipeline (graph traversal + FAISS semantic search + cross-encoder reranking + hybrid scoring + OpenRouter LLM assessment) and returns a result for one change request. This means the backend work is mostly a thin API wrapper, not new pipeline logic.

**Body (for when you create this issue):**

Tasks:
- Add a FastAPI app (e.g. `api.py` at the repo root, separate from the Streamlit `app.py` — don't delete or modify the Streamlit app in this issue, keep it as a fallback until the new frontend is confirmed working end-to-end).
- `GET /api/change-requests` — reads `change_requests.csv` / `requirement_versions.csv` via the existing `src/data_loader.py` and returns an array matching the shape of the current `src/data/changeRequests.js` mock (same field names) so the frontend swap requires minimal changes.
- `POST /api/analyze/{change_id}` — calls `analyze_change(change_id)` from `src/orchestrator.py` and shapes its return value to match the current `src/data/impactResults.js` mock structure (`highImpact`/`mediumImpact`/`lowImpact`/`totalAffected`, `impactChain`, `artifacts` with `impactTier`/`llmLabel`/`confidence`/`traceability`/`engineeringContent`). Map the pipeline's DIRECT/POTENTIAL/NO_IMPACT LLM output to `llmLabel` directly, and derive `impactTier` from whatever severity bucketing the existing pipeline already uses (check `src/orchestrator.py` and `src/evaluation.py` for how High/Medium/Low is currently determined before inventing new bucketing logic).
- Add CORS middleware allowing the Vite dev server's origin (default `http://localhost:5173`) to call the FastAPI server (likely `http://localhost:8000`) during local development.
- On the frontend: replace the static imports from `src/data/changeRequests.js` and `src/data/impactResults.js` with `fetch` calls to the new endpoints, keeping the same component props/shapes so components themselves don't need rewriting — this is the payoff of having matched the mock shapes to the real pipeline earlier.
- Real analysis will take longer than the mocked 1.5s delay (LLM calls over the network) — verify the existing loading state from Issue 5 handles arbitrary duration gracefully, and add a reasonable timeout + error state (e.g. "Analysis failed — check your OpenRouter API key" per the README's known limitations) if the request fails or the API key is missing.

**Acceptance criteria:**
- Selecting a real change request (CR-001–CR-005) and clicking Analyze Impact returns real pipeline results, not mock data.
- The Streamlit app (`app.py`) still runs independently and is unaffected by this change.
- If `OPENROUTER_API_KEY` is missing or invalid, the frontend shows a clear error state instead of hanging indefinitely or crashing.
