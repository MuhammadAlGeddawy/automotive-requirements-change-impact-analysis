"""NASAQ - Change Impact Review.

A user-friendly Streamlit app for reviewing change requests and their related
artifacts without exposing low-level technical details.
"""

# Load environment variables before any other imports
import html
import os
from pathlib import Path

# Try to load .env if python-dotenv is available
# This must be at the very top to ensure environment variables are available
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).resolve().parent
    dotenv_path = project_root / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
except ImportError:
    pass

# Now import other modules
import networkx as nx
import pandas as pd
import streamlit as st

from src.data_loader import build_graph, load_data
from src.orchestrator import AnalysisResult, analyze_change, get_ground_truth


# Page config
st.set_page_config(
    page_title="نسق | NASAQ",
    page_icon="▣",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Cached resources
@st.cache_data
def _load_data():
    """Cache loaded dataset across reruns."""
    return load_data()


@st.cache_resource
def _build_graph() -> nx.DiGraph:
    """Cache the traceability graph as a singleton."""
    data = _load_data()
    return build_graph(data)


def _inject_custom_css():
    """Apply the NASAQ brand theme and enterprise UI styling."""
    st.markdown(
        """
        <style>
            :root {
                --nasaq-green: #0B3D32;
                --nasaq-charcoal: #17211F;
                --nasaq-sand: #F5F1E8;
                --nasaq-white: #FFFFFF;
                --nasaq-light: #F8F7F3;
                --nasaq-mist: #EEF4F1;
                --nasaq-sage: #DDE9E5;
                --nasaq-line: rgba(23, 33, 31, 0.12);
                --nasaq-text: #17211F;
                --nasaq-muted: #62726D;
                --nasaq-warn: #C7B38A;
                --nasaq-critical: #A94D32;
            }

            @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');

            html, body, [class*="st"] {
                font-family: 'Cairo', 'Inter', sans-serif;
            }

            .stApp {
                background:
                    linear-gradient(rgba(23, 33, 31, 0.025) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(23, 33, 31, 0.025) 1px, transparent 1px),
                    var(--nasaq-light);
                background-size: 32px 32px;
                color: var(--nasaq-text);
            }

            .block-container {
                padding-top: 1.5rem;
                padding-bottom: 3rem;
                max-width: 1500px;
            }

            .stSidebar > div {
                background: var(--nasaq-green);
                color: var(--nasaq-white);
            }

            .stSidebar .stSelectbox label,
            .stSidebar .stTextInput label,
            .stSidebar .stMarkdown,
            .stSidebar .stCaption,
            .stSidebar p,
            .stSidebar div {
                color: rgba(255,255,255,0.9) !important;
            }

            .stSidebar .nasaq-wordmark {
                color: var(--nasaq-white) !important;
            }

            .stSidebar .stSelectbox div[data-baseweb="select"] > div,
            .stSidebar .stTextInput input {
                background: rgba(255,255,255,0.06);
                color: var(--nasaq-white);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 4px;
            }

            .nasaq-header {
                background: var(--nasaq-white);
                border: 1px solid var(--nasaq-line);
                border-top: 4px solid var(--nasaq-green);
                border-radius: 4px;
                padding: 1.35rem 1.5rem 1.15rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 8px 20px rgba(11, 61, 50, 0.05);
            }

            .nasaq-brand {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                flex-wrap: wrap;
            }

            .nasaq-mark {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 46px;
                height: 46px;
                border-radius: 4px;
                background: var(--nasaq-green);
                color: var(--nasaq-white);
                font-weight: 800;
                font-size: 1.2rem;
                letter-spacing: 0.08em;
            }

            .nasaq-wordmark {
                font-size: clamp(1.7rem, 2.6vw, 2.5rem);
                font-weight: 800;
                letter-spacing: -0.04em;
                color: var(--nasaq-green);
                line-height: 1;
            }

            .nasaq-wordmark .arabic {
                font-size: 1.2em;
                margin-left: 0.2rem;
            }

            .nasaq-tagline {
                margin-top: 0.35rem;
                color: var(--nasaq-muted);
                font-size: 0.98rem;
                font-weight: 500;
            }

            .workflow-strip {
                display: flex;
                align-items: center;
                gap: 0.55rem;
                margin-top: 1rem;
                padding-top: 0.8rem;
                border-top: 1px solid var(--nasaq-line);
                color: var(--nasaq-muted);
                font-size: 0.74rem;
                font-weight: 700;
                letter-spacing: 0.04em;
                text-transform: uppercase;
                overflow-x: auto;
                white-space: nowrap;
            }

            .workflow-step {
                color: var(--nasaq-charcoal);
            }

            .workflow-step.active {
                color: var(--nasaq-green);
            }

            .workflow-arrow {
                color: var(--nasaq-green);
                font-size: 1rem;
            }

            .section-label {
                color: var(--nasaq-green);
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                margin-bottom: 0.5rem;
            }

            .request-panel {
                background: rgba(255,255,255,0.7);
                border: 1px solid var(--nasaq-line);
                border-radius: 4px;
                padding: 1rem 1.1rem;
                box-shadow: 0 8px 18px rgba(11, 61, 50, 0.04);
            }

            .requirement-card {
                border-radius: 4px;
                padding: 1rem 1.15rem;
                margin-top: 0.6rem;
                border: 1px solid var(--nasaq-line);
                background: var(--nasaq-white);
                box-shadow: 0 6px 16px rgba(11, 61, 50, 0.03);
                color: var(--nasaq-text);
                white-space: pre-wrap;
                line-height: 1.7;
            }

            .requirement-card.requirement-old {
                background: var(--nasaq-white);
                border-top: 3px solid #B66B4D;
            }

            .requirement-card.requirement-new {
                background: var(--nasaq-white);
                border-top: 3px solid var(--nasaq-green);
            }

            .requirement-label {
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: var(--nasaq-muted);
                margin-bottom: 0.45rem;
            }

            .requirement-content {
                color: var(--nasaq-text);
                font-size: 1rem;
            }

            .summary-card {
                background: var(--nasaq-white);
                border: 1px solid var(--nasaq-line);
                border-radius: 4px;
                border-top: 3px solid var(--nasaq-green);
                padding: 1rem 1.1rem;
                box-shadow: 0 8px 20px rgba(11, 61, 50, 0.04);
                min-height: 110px;
            }

            .summary-card .label {
                color: var(--nasaq-muted);
                font-size: 0.74rem;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                font-weight: 700;
            }

            .summary-card .value {
                color: var(--nasaq-green);
                font-size: 2rem;
                font-weight: 800;
                line-height: 1.2;
                margin-top: 0.45rem;
            }

            .summary-card .meta {
                color: var(--nasaq-muted);
                font-size: 0.8rem;
                margin-top: 0.4rem;
            }

            .stButton > button {
                background: var(--nasaq-green) !important;
                color: var(--nasaq-white) !important;
                border-radius: 4px !important;
                border: none !important;
                padding: 0.85rem 1.2rem !important;
                font-weight: 700 !important;
                box-shadow: 0 8px 16px rgba(11, 61, 50, 0.18) !important;
            }

            .stButton > button:hover {
                filter: brightness(1.03);
            }

            .info-panel {
                background: var(--nasaq-white);
                border: 1px solid rgba(11, 61, 50, 0.12);
                border-left: 4px solid var(--nasaq-green);
                border-radius: 4px;
                padding: 0.8rem 1rem;
                margin: 0.5rem 0 1rem;
                color: var(--nasaq-charcoal);
            }

            .stAlert,
            .stInfo,
            .stSuccess,
            .stWarning,
            .stException {
                background: var(--nasaq-white) !important;
                color: var(--nasaq-text) !important;
                border: 1px solid rgba(11, 61, 50, 0.12) !important;
                border-left: 4px solid var(--nasaq-green) !important;
                box-shadow: none !important;
            }

            .stAlert p,
            .stInfo p,
            .stSuccess p,
            .stWarning p,
            .stException p,
            .stMarkdown p,
            .stMarkdown li,
            .stMarkdown div,
            .stExpander .streamlit-expanderHeader {
                color: var(--nasaq-text) !important;
            }

            .stExpander {
                background: var(--nasaq-white) !important;
                border: 1px solid rgba(11, 61, 50, 0.12) !important;
                border-top: 3px solid var(--nasaq-green) !important;
                border-radius: 4px !important;
            }

            .stExpander .streamlit-expanderHeader {
                background: var(--nasaq-green) !important;
                color: var(--nasaq-white) !important;
                border: none !important;
            }

            .stExpander .streamlit-expanderHeader p,
            .stExpander .streamlit-expanderHeader span,
            .stExpander .streamlit-expanderHeader div {
                color: var(--nasaq-white) !important;
            }

            .stExpander button > svg,
            .stExpander summary > svg,
            .streamlit-expanderHeader svg,
            [data-testid="stExpander"] svg {
                display: none !important;
            }

            .impact-artifact-text {
                background: var(--nasaq-white);
                color: #000000;
                border: 1px solid var(--nasaq-line);
                border-radius: 3px;
                padding: 0.85rem 1rem;
                margin: 0.35rem 0 1rem;
                white-space: pre-wrap;
                line-height: 1.65;
            }

            .dataframe-container {
                border-radius: 4px;
                overflow: hidden;
                border: 1px solid var(--nasaq-line);
                background: var(--nasaq-white);
            }

            .stDataFrame {
                border-radius: 4px;
            }

            .stTabs [role="tablist"] {
                gap: 0.6rem;
            }

            .stTabs [role="tab"] {
                border-radius: 4px 4px 0 0;
                color: var(--nasaq-charcoal);
                border: 1px solid var(--nasaq-line);
            }

            .stTabs [role="tab"][aria-selected="true"] {
                background: var(--nasaq-green);
                color: var(--nasaq-white);
                border-color: var(--nasaq-green);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# UI helpers
def _render_impact_badge(impact_level: str) -> str:
    """Render impact level as a colored badge."""
    colors = {
        "DIRECT": "red",
        "POTENTIAL": "orange",
        "NO_IMPACT": "green",
    }
    color = colors.get(impact_level, "gray")
    return f":{color}-background[{impact_level}]"


def _render_graph_status_badge(is_linked: bool) -> str:
    """Render graph-linked status badge."""
    if is_linked:
        return ":blue-background[Linked in traceability]"
    else:
        return ":red-background[Needs review]"


def _format_path_badge(path: list[str]) -> str:
    """Format a path list as a readable string with badges."""
    return " → ".join([f"`{node}`" for node in path])


def _render_requirement_card(title: str, requirement_text: str, tone: str):
    """Render requirement text inside a readable card."""
    safe_text = html.escape(requirement_text or "")
    card_class = "requirement-old" if tone == "old" else "requirement-new"
    st.markdown(
        f"""
        <div class="requirement-card {card_class}">
            <div class="requirement-label">{html.escape(title)}</div>
            <div class="requirement-content">{safe_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _initialize_session_state():
    """Initialize session state variables."""
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "selected_change_id" not in st.session_state:
        st.session_state.selected_change_id = None
    if "analysis_run" not in st.session_state:
        st.session_state.analysis_run = False


def _render_summary_cards(total_candidates: int, expected_count: int, linked_count: int, needs_review: int):
    """Render summary cards for the NASAQ review dashboard."""
    cards = st.columns(4)
    card_values = [
        ("Candidates", total_candidates, "Relevant artifacts"),
        ("Expected impact", expected_count, "Ground truth"),
        ("Traceable", linked_count, "Connected via path"),
        ("Needs review", needs_review, "Unlinked candidates"),
    ]

    for col, (label, value, meta) in zip(cards, card_values):
        with col:
            st.markdown(
                f"""
                <div class="summary-card">
                    <div class="label">{label}</div>
                    <div class="value">{value}</div>
                    <div class="meta">{meta}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _run_analysis(change_id: str, llm_model: str):
    """Run analysis and store result in session state."""
    with st.spinner("Reviewing related artifacts and impact..."):
        result = analyze_change(
            change_id=change_id,
            skip_llm=False,
            llm_model=llm_model,
        )
    st.session_state.analysis_result = result
    st.session_state.analysis_run = True


# Main app
def main():
    _inject_custom_css()

    st.markdown(
        """
        <div class="nasaq-header">
            <div class="nasaq-brand">
                <div class="nasaq-mark">نسق</div>
                <div class="nasaq-wordmark"><span class="arabic">نسق</span> | NASAQ</div>
            </div>
            <div class="nasaq-tagline">Change impact review for engineering and product teams</div>
            <div class="workflow-strip">
                <span class="workflow-step">Engineering artifacts</span>
                <span class="workflow-arrow">→</span>
                <span class="workflow-step active">Changed requirement</span>
                <span class="workflow-arrow">→</span>
                <span class="workflow-step active">Impact analysis</span>
                <span class="workflow-arrow">→</span>
                <span class="workflow-step">Affected artifacts</span>
                <span class="workflow-arrow">→</span>
                <span class="workflow-step">Traceability chain</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Initialize session state
    _initialize_session_state()

    # Load data
    data = _load_data()
    changes = data["changes"]

    # Sidebar - Change Request Selection
    st.sidebar.markdown("<div style='padding: 0.5rem 0 1rem;'><div class='nasaq-wordmark' style='font-size:1.5rem;color:#fff;'>نسق | NASAQ</div></div>", unsafe_allow_html=True)
    st.sidebar.caption("Engineering change review")
    st.sidebar.markdown("### Select Change Request")
    change_ids = changes["change_id"].tolist()

    selected_change_id = st.sidebar.selectbox(
        "Change request",
        change_ids,
        index=0,
        help="Choose the request to review",
        key="change_selector",
    )

    change_row = changes[changes["change_id"] == selected_change_id].iloc[0]

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Request Details")
    st.sidebar.markdown(f"**Request:** `{selected_change_id}`")
    st.sidebar.markdown(f"**Type:** {change_row['change_type']}")
    st.sidebar.markdown(f"**Requirement:** `{change_row['requirement_id']}`")
    st.sidebar.markdown(f"**Reason:** {change_row['reason']}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### AI Review")
    llm_model = st.sidebar.text_input(
        "Model",
        value="nvidia/nemotron-3.5-lightning:free",
        help="Choose the AI model used for review",
        key="llm_model_input",
    )

    has_api_key = bool(os.environ.get("OPENROUTER_API_KEY"))
    if has_api_key:
        st.sidebar.caption("AI review ready")
    else:
        st.sidebar.caption("AI review unavailable")

    st.markdown("<div class='section-label'>Change request</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='info-panel'>Review the previous and updated requirement text before running the impact analysis.</div>",
        unsafe_allow_html=True,
    )

    col_old, col_new = st.columns(2)

    with col_old:
        st.markdown("### Previous Requirement")
        st.markdown(f"**ID:** `{change_row['requirement_id']}`")
        _render_requirement_card("Previous requirement", change_row["old_text"], "old")

    with col_new:
        st.markdown("### Updated Requirement")
        st.markdown(f"**ID:** `{change_row['requirement_id']}`")
        _render_requirement_card("Updated requirement", change_row["new_text"], "new")

    st.markdown(f"**Change type:** `{change_row['change_type']}` | **Reason:** {change_row['reason']}")

    st.divider()
    with st.form("analysis_form", enter_to_submit=False):
        analyze_clicked = st.form_submit_button(
            "Analyze Impact",
            type="primary",
            use_container_width=True,
            help="Run the impact review across related artifacts",
        )
        if analyze_clicked:
            _run_analysis(selected_change_id, llm_model)

    if (st.session_state.analysis_result is None and st.session_state.selected_change_id != selected_change_id):
        st.session_state.selected_change_id = selected_change_id
        _run_analysis(selected_change_id, llm_model)

    if st.session_state.analysis_run and st.session_state.analysis_result:
        _render_results(st.session_state.analysis_result, data)


def _render_results(result: AnalysisResult, data: dict):
    """Render analysis results in a clearer, user-friendly layout."""
    st.markdown("<div class='section-label'>Review results</div>", unsafe_allow_html=True)
    st.header("Impact review")

    if result.error:
        st.warning(result.error)

    ground_truth_ids = get_ground_truth(data, result.change_id)
    display_df = result.ranked_candidates[["id", "type", "graph_linked", "text"]].copy()
    display_df["status"] = display_df["graph_linked"].apply(
        lambda x: "Linked" if x else "Needs review",
    )

    linked_count = int(display_df["graph_linked"].sum())
    needs_review = int((display_df["status"] == "Needs review").sum())
    _render_summary_cards(
        total_candidates=len(result.ranked_candidates),
        expected_count=len(ground_truth_ids),
        linked_count=linked_count,
        needs_review=needs_review,
    )

    st.divider()
    col_table, col_detail = st.columns([3, 2])

    with col_table:
        st.subheader("Most relevant artifacts")
        st.dataframe(
            display_df[["id", "type", "status", "text"]],
            column_config={
                "id": st.column_config.TextColumn("Artifact ID", width="small"),
                "type": st.column_config.TextColumn("Type", width="small"),
                "status": st.column_config.TextColumn("Status", width="small"),
                "text": st.column_config.TextColumn("Artifact content", width="large"),
            },
            use_container_width=True,
            height=450,
            key="artifact_table",
        )

    with col_detail:
        st.subheader("Artifact detail")
        artifact_ids = result.ranked_candidates["id"].tolist()
        selected_artifact = st.selectbox(
            "Select an artifact",
            artifact_ids,
            index=0,
            help="Choose an artifact to inspect its details",
            key="artifact_selector",
        )

        if selected_artifact:
            _render_artifact_detail(result, selected_artifact, data)

    st.divider()
    unlinked = display_df[display_df["status"] == "Needs review"]
    if not unlinked.empty:
        st.subheader("Possible missing traceability")
        st.markdown(
            "These artifacts were identified as relevant but do not have a clear traceability path from the request and may require manual review."
        )
        st.dataframe(
            unlinked[["id", "type", "text"]],
            use_container_width=True,
            column_config={
                "id": st.column_config.TextColumn("Artifact ID"),
                "type": st.column_config.TextColumn("Type"),
                "text": st.column_config.TextColumn("Artifact content"),
            },
            key="unlinked_table",
        )

    if result.llm_assessments:
        st.divider()
        st.subheader("AI impact assessment")

        for assessment in result.llm_assessments.assessments:
            impact_badge = _render_impact_badge(assessment.impact_level)
            with st.expander(
                f"{assessment.artifact_id} {impact_badge} (confidence {assessment.confidence:.2f})",
                expanded=True,
            ):
                artifact_row = result.ranked_candidates[
                    result.ranked_candidates["id"] == assessment.artifact_id
                ]
                if not artifact_row.empty:
                    assessed_artifact = artifact_row.iloc[0]
                    st.markdown("**Artifact content:**")
                    st.markdown(
                        f"<div class='impact-artifact-text'>{html.escape(str(assessed_artifact['text'] or ''))}</div>",
                        unsafe_allow_html=True,
                    )

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Why this matters:**")
                    st.markdown(assessment.reason)
                with c2:
                    st.markdown("**Evidence:**")
                    for ev in assessment.evidence:
                        st.markdown(f"- {ev}")

                if not artifact_row.empty:
                    row = artifact_row.iloc[0]
                    st.markdown("---")
                    st.markdown(f"**Traceability status:** {_render_graph_status_badge(row['graph_linked'])}")


@st.fragment
def _render_artifact_detail(result: AnalysisResult, artifact_id: str, data: dict):
    """Render the selected artifact in a readable detail panel."""
    graph = _build_graph()
    artifact_row = result.ranked_candidates[result.ranked_candidates["id"] == artifact_id]

    if artifact_row.empty:
        st.warning(f"Artifact {artifact_id} not found in candidates.")
        return

    row = artifact_row.iloc[0]

    st.markdown(f"### {artifact_id}")
    st.markdown(f"**Type:** `{row['type']}`")

    st.markdown("**Content:**")
    _render_requirement_card("Artifact content", row["text"], "new")

    status_text = "Linked to the request through traceability." if row.get("graph_linked") else "This artifact was found by relevance, but no direct traceability path is visible."
    st.info(status_text)

    st.markdown("**Traceability paths:**")
    try:
        paths = list(
            nx.all_simple_paths(
                graph,
                source=result.requirement_id,
                target=artifact_id,
                cutoff=5,
            )
        )
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        paths = []

    if paths:
        for i, path in enumerate(paths, 1):
            st.markdown(f"{i}. {_format_path_badge(path)}")
    else:
        if row.get("graph_linked"):
            st.info("No direct path found within the current view. This can happen with longer traceability chains.")
        else:
            st.warning("No explicit traceability path exists for this artifact.")

    ground_truth_ids = get_ground_truth(data, result.change_id)
    if artifact_id in ground_truth_ids:
        st.success("This artifact matches the expected impact set.")
    else:
        st.info("This artifact is not part of the expected impact set.")


if __name__ == "__main__":
    main()
