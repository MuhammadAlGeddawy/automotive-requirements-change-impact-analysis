"""NASAQ Change Impact Analysis workspace.

This module owns presentation only. The retrieval, graph, and assessment
pipeline remain in ``src`` and are called through the existing service API.
"""

from __future__ import annotations

import html
import os
import sys
from typing import TYPE_CHECKING
from difflib import SequenceMatcher
from pathlib import Path

import networkx as nx
import pandas as pd
import streamlit as st

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data_loader import build_graph, load_data

if TYPE_CHECKING:
    from src.orchestrator import AnalysisResult


st.set_page_config(
    page_title="NASAQ | Change Impact Analysis",
    page_icon="▣",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def get_data() -> dict:
    """Load the engineering dataset once per session."""
    return load_data()


@st.cache_resource
def get_graph() -> nx.DiGraph:
    """Build the traceability graph once per process."""
    return build_graph(get_data())


def has_openrouter_api_key() -> bool:
    """Check whether an OpenRouter key is available to the Streamlit app."""
    if os.environ.get("OPENROUTER_API_KEY"):
        return True
    try:
        if st.secrets.get("OPENROUTER_API_KEY"):
            return True
        openrouter = st.secrets.get("openrouter", {})
        return bool(
            openrouter.get("api_key") or openrouter.get("OPENROUTER_API_KEY")
        )
    except (FileNotFoundError, KeyError, TypeError, AttributeError):
        return False


def inject_css() -> None:
    """Install the NASAQ design tokens and scoped Streamlit overrides."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600;700&display=swap');

        :root {
            --nasaq-green: #0B3D32;
            --nasaq-green-2: #145746;
            --nasaq-charcoal: #17211F;
            --nasaq-sand: #F5F1E8;
            --nasaq-white: #FFFFFF;
            --nasaq-light: #F8F7F3;
            --nasaq-line: #D9DED7;
            --nasaq-muted: #61706A;
            --nasaq-high: #9E2A2B;
            --nasaq-medium: #D97706;
            --nasaq-low: #059669;
        }

        html, body, [class*="st-"], .stMarkdown, .stText {
            font-family: "IBM Plex Sans", sans-serif;
            color: var(--nasaq-charcoal);
        }
        code, .mono, [data-testid="stCode"] {
            font-family: "JetBrains Mono", monospace !important;
        }
        .stApp { background: var(--nasaq-sand); }
        .block-container {
            max-width: 1500px;
            padding: 2.2rem 3.2rem 4rem;
        }
        header[data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] > div {
            background: var(--nasaq-green);
            border-right: 1px solid rgba(245,241,232,.18);
        }
        [data-testid="stSidebar"] * { color: var(--nasaq-sand) !important; }
        [data-testid="stSidebar"] hr {
            border-color: rgba(245,241,232,.18) !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] input {
            background: rgba(255,255,255,.08) !important;
            border: 1px solid rgba(245,241,232,.32) !important;
            color: var(--nasaq-sand) !important;
        }
        [data-testid="stSidebar"] [role="listbox"],
        [data-testid="stSidebar"] [role="option"] {
            background: var(--nasaq-charcoal) !important;
            color: var(--nasaq-sand) !important;
        }
        [data-testid="stSidebar"] .stExpander {
            background: rgba(255,255,255,.055) !important;
            border: 1px solid rgba(245,241,232,.2) !important;
        }
        [data-testid="stSidebar"] .stExpander details,
        [data-testid="stSidebar"] .stExpander summary {
            background: transparent !important;
        }
        .sidebar-brand {
            display: flex; align-items: center; gap: .65rem;
            padding: .25rem 0 1.8rem;
        }
        .brand-mark {
            display: grid; place-items: center; width: 30px; height: 30px;
            border: 1px solid rgba(245,241,232,.55); color: var(--nasaq-sand);
            font: 700 .75rem "JetBrains Mono", monospace; letter-spacing: -.1em;
        }
        .sidebar-brand-name {
            color: var(--nasaq-sand); font-size: 1.25rem; font-weight: 700;
            letter-spacing: .08em;
        }
        .sidebar-kicker {
            color: rgba(245,241,232,.7); font-size: .72rem;
            letter-spacing: .12em; text-transform: uppercase;
        }
        .sidebar-section {
            margin: 1.35rem 0 .5rem; color: var(--nasaq-sand);
            font-size: .72rem; font-weight: 700; letter-spacing: .12em;
            text-transform: uppercase;
        }
        .upload-label {
            margin: .35rem 0 .25rem; color: var(--nasaq-sand);
            font-size: .82rem; font-weight: 600;
        }
        /* Hide Streamlit's internal upload copy/icons; the app supplies its own label. */
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"],
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] svg,
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small {
            display: none !important;
        }
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
            min-height: 48px !important; padding: .55rem !important;
            background: rgba(255,255,255,.07) !important;
            border: 1px dashed rgba(245,241,232,.45) !important;
            border-radius: 3px !important;
        }
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
            width: 100% !important; color: var(--nasaq-sand) !important;
            background: transparent !important; border: 0 !important;
            font-size: .8rem !important;
        }
        .app-header {
            display: flex; align-items: flex-start; justify-content: space-between;
            gap: 1rem; padding-bottom: 1.35rem; margin-bottom: 2rem;
            border-bottom: 1px solid var(--nasaq-line);
        }
        .brand-name {
            color: var(--nasaq-green); font-size: clamp(2rem, 3vw, 3rem);
            font-weight: 700; letter-spacing: .08em; line-height: 1;
        }
        .brand-subtitle {
            margin-top: .6rem; color: var(--nasaq-muted); font-size: .95rem;
        }
        .version-badge {
            padding: .35rem .65rem; border: 1px solid var(--nasaq-green);
            color: var(--nasaq-green); font: 700 .7rem "JetBrains Mono", monospace;
            letter-spacing: .08em; white-space: nowrap;
        }
        .eyebrow {
            margin-bottom: .4rem; color: var(--nasaq-green);
            font-size: .72rem; font-weight: 700; letter-spacing: .14em;
            text-transform: uppercase;
        }
        .page-title {
            margin: 0 0 1.25rem; color: var(--nasaq-charcoal);
            font-size: 1.65rem; font-weight: 700;
        }
        .section-title {
            margin: 2rem 0 .8rem; color: var(--nasaq-green);
            font-size: 1.05rem; font-weight: 700; letter-spacing: .01em;
        }
        .panel {
            background: var(--nasaq-white); border: 1px solid var(--nasaq-line);
            border-radius: 3px; padding: 1.15rem 1.25rem;
        }
        .delta-panel { min-height: 145px; }
        .delta-previous { border-left: 4px solid var(--nasaq-high); }
        .delta-updated { border-left: 4px solid var(--nasaq-low); }
        .panel-label {
            margin-bottom: .7rem; color: var(--nasaq-muted); font-size: .7rem;
            font-weight: 700; letter-spacing: .1em; text-transform: uppercase;
        }
        .requirement-text { color: var(--nasaq-charcoal); line-height: 1.7; }
        .meta-line { margin-top: .75rem; color: var(--nasaq-muted); font-size: .84rem; }
        .kpi {
            min-height: 108px; border-top: 3px solid var(--nasaq-green);
        }
        .kpi-high { border-top-color: var(--nasaq-high); }
        .kpi-medium { border-top-color: var(--nasaq-medium); }
        .kpi-low { border-top-color: var(--nasaq-low); }
        .kpi-label {
            color: var(--nasaq-muted); font-size: .7rem; font-weight: 700;
            letter-spacing: .1em; text-transform: uppercase;
        }
        .kpi-value { margin-top: .35rem; color: var(--nasaq-charcoal);
            font-size: 2rem; font-weight: 700; line-height: 1; }
        .kpi-meta { margin-top: .45rem; color: var(--nasaq-muted); font-size: .78rem; }
        .trace-shell { overflow-x: auto; }
        .trace-flow { display: flex; align-items: center; gap: .5rem; min-width: max-content; }
        .trace-node {
            min-width: 140px; padding: .8rem; background: var(--nasaq-light);
            border: 1px solid var(--nasaq-line); border-top: 3px solid var(--nasaq-green);
        }
        .trace-id { color: var(--nasaq-green); font: 700 .8rem "JetBrains Mono", monospace; }
        .trace-type { margin-top: .25rem; color: var(--nasaq-muted); font-size: .72rem; }
        .trace-arrow { color: var(--nasaq-green); font-size: 1.2rem; }
        .stButton > button {
            min-height: 2.7rem; background: var(--nasaq-green) !important;
            color: var(--nasaq-white) !important; border: 0 !important;
            border-radius: 3px !important; font-weight: 700 !important;
        }
        .stButton > button:hover { background: var(--nasaq-green-2) !important; }
        .stButton > button:focus { box-shadow: 0 0 0 2px var(--nasaq-sand),
            0 0 0 4px var(--nasaq-green) !important; }
        .stTextInput input, [data-baseweb="select"] > div {
            border-radius: 3px !important;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--nasaq-line); border-radius: 3px;
            overflow: hidden;
        }
        [data-testid="stExpander"] {
            border: 1px solid var(--nasaq-line) !important;
            border-radius: 3px !important; background: var(--nasaq-white) !important;
        }
        .stAlert, .stInfo, .stWarning, .stSuccess {
            border-radius: 3px !important; box-shadow: none !important;
        }
        @media (max-width: 800px) {
            .block-container { padding: 1.2rem 1rem 3rem; }
            .app-header { flex-direction: column; }
        }

        /* NASAQ visual system: keep component styling consistent across screens. */
        :root {
            --nasaq-green-deep: #072D26;
            --nasaq-cta: #168A5B;
            --nasaq-cta-hover: #0F7049;
            --nasaq-cream: #F5F1E8;
            --nasaq-card: #FFFFFF;
            --nasaq-soft: #F8F7F3;
            --nasaq-border: #D9DED7;
            --nasaq-red-soft: #FDF2F1;
            --nasaq-red-border: #B94A48;
            --nasaq-green-soft: #F1F8F4;
            --nasaq-green-border: #23805A;
            --nasaq-shadow: 0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.06);
            --nasaq-radius: 14px;
            --nasaq-transition: 180ms ease;
        }
        .stApp { background: var(--nasaq-cream); }
        [data-testid="stSidebar"] > div {
            background: linear-gradient(180deg, var(--nasaq-green-deep) 0%, var(--nasaq-green) 55%, #0D493B 100%);
        }
        .block-container { padding-top: 2rem; }
        .sidebar-section {
            padding-top: .9rem; border-top: 1px solid rgba(245,241,232,.18);
        }
        .sidebar-section:first-of-type { border-top: 0; }
        .brand-mark { border-radius: 9px; background: rgba(245,241,232,.08); }
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
            min-height: 72px !important; padding: .7rem !important;
            border-radius: var(--nasaq-radius) !important;
            transition: background var(--nasaq-transition), border-color var(--nasaq-transition);
        }
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover {
            background: rgba(255,255,255,.13) !important;
            border-color: var(--nasaq-sand) !important;
        }
        .upload-zone-icon {
            display: block; margin-bottom: .15rem; color: var(--nasaq-sand);
            font-size: 1.2rem; text-align: center;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] input {
            border-radius: 10px !important; transition: border-color var(--nasaq-transition),
            background var(--nasaq-transition), box-shadow var(--nasaq-transition);
        }
        [data-testid="stSidebar"] [data-baseweb="select"] > div:hover,
        [data-testid="stSidebar"] input:hover {
            border-color: rgba(245,241,232,.72) !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] svg { fill: var(--nasaq-sand) !important; }
        [data-testid="stSidebar"] .stExpander {
            margin-top: .3rem; padding: .2rem .25rem;
            border-radius: var(--nasaq-radius) !important;
            background: rgba(0,0,0,.13) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.04);
        }
        .app-header {
            align-items: center; padding: 1rem 1.2rem 1.2rem;
            margin-bottom: 1.3rem; border: 1px solid var(--nasaq-border);
            border-radius: var(--nasaq-radius); background: rgba(255,255,255,.48);
            box-shadow: var(--nasaq-shadow);
        }
        .version-badge, .deploy-pill {
            border: 1px solid rgba(11,61,50,.24); border-radius: 999px;
            background: rgba(11,61,50,.08); color: var(--nasaq-green);
            padding: .45rem .75rem; font-size: .68rem;
        }
        .top-actions { display: flex; align-items: center; gap: .55rem; }
        .deploy-pill { background: var(--nasaq-green); color: var(--nasaq-sand); }
        .workflow-stepper {
            display: flex; align-items: center; gap: .65rem; margin: 0 0 1.8rem;
            padding: .7rem .9rem; border: 1px solid var(--nasaq-border);
            border-radius: var(--nasaq-radius); background: rgba(255,255,255,.62);
            box-shadow: var(--nasaq-shadow); overflow-x: auto;
        }
        .workflow-step {
            display: flex; align-items: center; gap: .45rem; white-space: nowrap;
            color: var(--nasaq-muted); font-size: .76rem; font-weight: 600;
        }
        .workflow-step strong {
            display: grid; place-items: center; width: 1.45rem; height: 1.45rem;
            border-radius: 50%; background: var(--nasaq-border); color: var(--nasaq-charcoal);
            font: 700 .7rem "JetBrains Mono", monospace;
        }
        .workflow-step.current { color: var(--nasaq-green); }
        .workflow-step.current strong { background: var(--nasaq-cta); color: white; }
        .workflow-connector { flex: 1; min-width: 2rem; height: 1px; background: var(--nasaq-border); }
        .panel, [data-testid="stDataFrame"], [data-testid="stExpander"] {
            border-radius: var(--nasaq-radius) !important; box-shadow: var(--nasaq-shadow);
        }
        .panel { background: var(--nasaq-card); border-color: var(--nasaq-border); }
        .delta-panel { min-height: 145px; transition: transform var(--nasaq-transition), box-shadow var(--nasaq-transition); }
        .delta-panel:hover { transform: translateY(-2px); box-shadow: 0 5px 14px rgba(0,0,0,.09); }
        .delta-previous { background: var(--nasaq-red-soft); border-left: 5px solid var(--nasaq-red-border); }
        .delta-updated { background: var(--nasaq-green-soft); border-left: 5px solid var(--nasaq-green-border); }
        .delta-token {
            padding: .08rem .28rem; border-radius: 5px; font-weight: 700;
            box-decoration-break: clone; -webkit-box-decoration-break: clone;
        }
        .delta-previous .delta-token { background: rgba(185,74,72,.14); color: #7D2929; }
        .delta-updated .delta-token { background: rgba(35,128,90,.15); color: #145B40; }
        .comparison-arrow {
            display: grid; place-items: center; height: 100%; color: var(--nasaq-cta);
            font-size: 1.5rem; font-weight: 700;
        }
        .stButton > button {
            min-height: 3rem; border-radius: var(--nasaq-radius) !important;
            background: var(--nasaq-cta) !important;
            box-shadow: 0 3px 8px rgba(22,138,91,.22);
            transition: transform var(--nasaq-transition), background var(--nasaq-transition),
            box-shadow var(--nasaq-transition), opacity var(--nasaq-transition);
        }
        .stButton > button:hover {
            background: var(--nasaq-cta-hover) !important; transform: translateY(-1px);
            box-shadow: 0 5px 12px rgba(22,138,91,.28);
        }
        .stButton > button:active { transform: translateY(0); }
        .stButton > button:disabled { background: #AAB5AF !important; opacity: .58; cursor: not-allowed; box-shadow: none; }
        .stButton > button:focus-visible, input:focus-visible,
        [data-baseweb="select"] > div:focus-within {
            box-shadow: 0 0 0 3px rgba(22,138,91,.22) !important;
        }
        .empty-state {
            display: flex; align-items: center; gap: .8rem; margin-top: 1.4rem;
            padding: 1rem 1.15rem; border: 1px solid var(--nasaq-border);
            border-radius: var(--nasaq-radius); background: var(--nasaq-soft);
            color: var(--nasaq-muted); box-shadow: var(--nasaq-shadow);
        }
        .empty-state-icon { color: var(--nasaq-cta); font-size: 1.2rem; }
        @media (max-width: 800px) {
            .workflow-stepper { align-items: flex-start; }
            .comparison-arrow { height: 2rem; transform: rotate(90deg); }
            .top-actions { align-self: flex-start; }
        }

        /* Round two: selective glass surfaces and resilient icon treatment. */
        :root {
            --nasaq-heading: #14261F;
            --nasaq-body: #3E4C46;
            --nasaq-muted-aa: #52625A;
            --nasaq-sidebar-muted: #B9CBBF;
            --nasaq-glass: rgba(255,255,255,.55);
            --nasaq-glass-border: rgba(255,255,255,.4);
            --nasaq-glass-shadow: 0 8px 32px rgba(20,60,45,.12);
            --nasaq-badge-high: #B91C1C;
            --nasaq-badge-medium: #9A5300;
            --nasaq-badge-low: #15803D;
        }
        html, body, .stApp {
            color: var(--nasaq-body);
        }
        .stApp {
            position: relative;
            background: var(--nasaq-cream);
            isolation: isolate;
        }
        .stApp::before, .stApp::after {
            position: fixed; z-index: 0; content: ""; pointer-events: none;
            width: 34rem; height: 34rem; border-radius: 50%;
            filter: blur(70px); opacity: .12;
        }
        .stApp::before {
            top: -12rem; right: -8rem;
            background: radial-gradient(circle, #8CB7A1 0%, transparent 68%);
        }
        .stApp::after {
            bottom: -16rem; left: 16%;
            background: radial-gradient(circle, #D6B86A 0%, transparent 68%);
        }
        .stApp > div {
            position: relative;
            z-index: 1;
        }
        .page-title, .kpi-value { color: var(--nasaq-heading); }
        .requirement-text { color: var(--nasaq-body); }
        .eyebrow, .section-title { color: var(--nasaq-green); }
        .meta-line, .kpi-meta, .trace-type { color: var(--nasaq-muted-aa); }
        .sidebar-kicker, [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: var(--nasaq-sidebar-muted) !important;
        }
        [data-testid="stSidebar"] .stExpander summary,
        [data-testid="stSidebar"] .stExpander summary span {
            color: var(--nasaq-sand) !important;
        }
        .kpi, .trace-shell {
            background: var(--nasaq-glass) !important;
            border: 1px solid var(--nasaq-glass-border) !important;
            backdrop-filter: blur(16px) saturate(160%);
            -webkit-backdrop-filter: blur(16px) saturate(160%);
            box-shadow: var(--nasaq-glass-shadow) !important;
            border-radius: 16px !important;
        }
        .trace-node {
            background: rgba(255,255,255,.38);
            border-color: rgba(255,255,255,.5);
            border-radius: 12px;
        }
        /* Keep the dense data surface opaque and readable. */
        [data-testid="stDataFrame"] {
            background: var(--nasaq-card) !important;
            border: 1px solid var(--nasaq-border) !important;
            border-radius: var(--nasaq-radius) !important;
            box-shadow: var(--nasaq-shadow) !important;
            overflow-x: auto !important;
        }
        [data-testid="stDataFrame"] > div { background: var(--nasaq-card) !important; }
        [data-testid="stDataFrame"] iframe { border-radius: var(--nasaq-radius); }
        /* Streamlit/BaseWeb popovers render outside the sidebar DOM. */
        [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] {
            z-index: 1000 !important;
            background: var(--nasaq-glass) !important;
            color: var(--nasaq-body) !important;
            border: 1px solid var(--nasaq-glass-border) !important;
            border-radius: 16px !important;
            backdrop-filter: blur(16px) saturate(160%);
            -webkit-backdrop-filter: blur(16px) saturate(160%);
            box-shadow: var(--nasaq-glass-shadow) !important;
            overflow: hidden;
        }
        [data-baseweb="popover"] [role="option"],
        [data-baseweb="menu"] [role="option"],
        [role="listbox"] [role="option"] {
            min-height: 2.8rem; padding: .65rem .8rem !important;
            color: var(--nasaq-body) !important;
            background: transparent !important;
            border-left: 3px solid transparent;
        }
        [data-baseweb="popover"] [role="option"]:hover,
        [data-baseweb="menu"] [role="option"]:hover,
        [role="listbox"] [role="option"]:hover {
            background: rgba(255,255,255,.58) !important;
        }
        [data-baseweb="popover"] [aria-selected="true"],
        [data-baseweb="menu"] [aria-selected="true"],
        [role="listbox"] [aria-selected="true"] {
            border-left-color: var(--nasaq-cta);
            font-weight: 700;
        }
        /* Prevent failed icon-font ligatures from ever becoming visible text. */
        [data-testid="stSidebarCollapseButton"] span,
        [data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"] {
            font-size: 0 !important; color: transparent !important;
        }
        [data-testid="stSidebarCollapseButton"] svg { display: block !important; }
        .impact-badge {
            display: inline-flex; align-items: center; gap: .35rem;
            padding: .22rem .5rem; border-radius: 999px;
            font-size: .72rem; font-weight: 700; white-space: nowrap;
        }
        .impact-high { color: var(--nasaq-badge-high); background: #FEE2E2; }
        .impact-medium { color: var(--nasaq-badge-medium); background: #FEF3C7; }
        .impact-low { color: var(--nasaq-badge-low); background: #DCFCE7; }
        .impact-unassessed { color: var(--nasaq-muted-aa); background: #E8EDE9; }
        .nasaq-icon {
            width: 1em; height: 1em; flex: 0 0 auto; vertical-align: -.15em;
            fill: none; stroke: currentColor; stroke-width: 1.8;
            stroke-linecap: round; stroke-linejoin: round;
        }
        .upload-label, .sidebar-detail-label {
            display: flex; align-items: center; gap: .4rem;
        }
        .upload-label .nasaq-icon, .sidebar-detail-label .nasaq-icon { font-size: 1rem; }
        .confidence-meter {
            display: inline-flex; align-items: center; gap: .45rem; min-width: 7rem;
        }
        .confidence-meter > span:first-child {
            width: 4.2rem; height: .35rem; overflow: hidden; border-radius: 999px;
            background: var(--nasaq-border);
        }
        .confidence-meter > span:first-child > span {
            display: block; height: 100%; border-radius: inherit; background: var(--nasaq-cta);
        }
        @media (max-width: 800px) {
            .kpi { min-width: 0; }
            [data-testid="stDataFrame"] { overflow-x: scroll !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def esc(value: object) -> str:
    """Escape dynamic values before placing them in HTML."""
    return html.escape(str(value or ""))


def icon(name: str, label: str = "") -> str:
    """Return a small inline SVG so icons never depend on ligature fonts."""
    paths = {
        "upload": '<path d="M12 16V4m0 0L7 9m5-5 5 5"/><path d="M5 15v4h14v-4"/>',
        "request": '<rect x="5" y="4" width="14" height="16" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
        "requirement": '<path d="M6 4h12v16H6z"/><path d="M9 8h6M9 12h6M9 16h4"/>',
        "change": '<path d="M5 7h10"/><path d="m12 4 3 3-3 3"/><path d="M19 17H9"/><path d="m12 14-3 3 3 3"/>',
    }
    return (
        f'<svg class="nasaq-icon" viewBox="0 0 24 24" aria-hidden="true"'
        f' role="img" focusable="false"><title>{esc(label)}</title>{paths[name]}</svg>'
    )


def highlight_delta(previous: object, updated: object) -> tuple[str, str]:
    """Highlight changed word groups while preserving the existing requirement copy."""
    old_tokens = str(previous or "").split()
    new_tokens = str(updated or "").split()
    matcher = SequenceMatcher(None, old_tokens, new_tokens)

    def render(tokens: list[str], changed_ranges: list[tuple[int, int]]) -> str:
        changed = {index for start, end in changed_ranges for index in range(start, end)}
        return " ".join(
            f'<span class="delta-token">{esc(token)}</span>' if index in changed else esc(token)
            for index, token in enumerate(tokens)
        )

    old_ranges: list[tuple[int, int]] = []
    new_ranges: list[tuple[int, int]] = []
    for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if tag != "equal":
            old_ranges.append((old_start, old_end))
            new_ranges.append((new_start, new_end))
    return render(old_tokens, old_ranges), render(new_tokens, new_ranges)


def render_header() -> None:
    st.markdown(
        """
        <div class="app-header">
          <div>
            <div class="brand-name">NASAQ</div>
            <div class="brand-subtitle">Engineering Intelligence · Change Impact Analysis</div>
          </div>
          <div class="top-actions">
            <div class="deploy-pill">Deploy</div>
            <div class="version-badge">MVP v0.4</div>
          </div>
        </div>
        <div class="workflow-stepper" aria-label="Review workflow">
          <div class="workflow-step current"><strong>01</strong><span>Select Change</span></div>
          <div class="workflow-connector"></div>
          <div class="workflow-step"><strong>02</strong><span>Analyze Impact</span></div>
          <div class="workflow-connector"></div>
          <div class="workflow-step"><strong>03</strong><span>Review Results</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(changes: pd.DataFrame) -> tuple[str, str]:
    """Render the workspace controls without exposing internal widget copy."""
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
          <div class="brand-mark">NQ</div>
          <div class="sidebar-brand-name">NASAQ</div>
        </div>
        <div class="sidebar-kicker">Engineering Intelligence</div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown('<div class="sidebar-section">Engineering Artifacts</div>',
                        unsafe_allow_html=True)
    st.sidebar.markdown(
        f'<div class="upload-label">{icon("upload", "Upload artifact")} Artifact file</div>',
                        unsafe_allow_html=True)
    uploaded = st.sidebar.file_uploader(
        "Artifact file",
        type=["csv", "json", "xlsx"],
        label_visibility="collapsed",
        help="Optional artifact export for this review workspace.",
    )
    if uploaded:
        st.sidebar.caption(f"Loaded: {uploaded.name}")

    st.sidebar.markdown('<div class="sidebar-section">Change Request</div>',
                        unsafe_allow_html=True)
    change_id = st.sidebar.selectbox(
        "Change request",
        changes["change_id"].tolist(),
        label_visibility="collapsed",
    )
    row = changes.loc[changes["change_id"] == change_id].iloc[0]

    with st.sidebar.expander("Request Details", expanded=True):
        st.markdown(
            f'<div class="sidebar-detail-label">{icon("request", "Request")} '
            f'<strong>Request</strong>&nbsp; <code>{esc(change_id)}</code></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="sidebar-detail-label">{icon("requirement", "Requirement")} '
            f'<strong>Requirement</strong>&nbsp; <code>{esc(row["requirement_id"])}</code></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="sidebar-detail-label">{icon("change", "Change type")} '
            f'<strong>Change type</strong>&nbsp; {esc(row["change_type"])}</div>',
            unsafe_allow_html=True,
        )
        st.caption(row["reason"])

    st.sidebar.markdown('<div class="sidebar-section">Assessment Engine</div>',
                        unsafe_allow_html=True)
    model = st.sidebar.text_input(
        "Assessment model",
        value="nvidia/nemotron-3.5-lightning:free",
        label_visibility="collapsed",
    )
    status = "Review engine ready" if has_openrouter_api_key() else "Retrieval mode · API key unavailable"
    st.sidebar.caption(status)
    return change_id, model


def render_delta(change: pd.Series) -> None:
    st.markdown('<div class="eyebrow">Changed Requirement</div>',
                unsafe_allow_html=True)
    st.markdown('<h1 class="page-title">Change Request Review</h1>',
                unsafe_allow_html=True)
    previous, arrow, updated = st.columns([10, 1, 10], gap="medium")
    previous_text, updated_text = highlight_delta(change["old_text"], change["new_text"])
    cards = (
        (previous, "Previous Requirement", "old_text", "delta-previous"),
        (updated, "Updated Requirement", "new_text", "delta-updated"),
    )
    for column, title, key, tone in cards:
        with column:
            st.markdown(
                f'<div class="panel delta-panel {tone}">'
                f'<div class="panel-label">{title} · '
                f'<span class="mono">{esc(change["requirement_id"])}</span></div>'
                f'<div class="requirement-text">'
                f'{previous_text if key == "old_text" else updated_text}</div></div>',
                unsafe_allow_html=True,
            )
    with arrow:
        st.markdown('<div class="comparison-arrow" aria-hidden="true">→</div>',
                    unsafe_allow_html=True)
    st.markdown(
        f'<div class="meta-line">Change type: <span class="mono">{esc(change["change_type"])}</span>'
        f' &nbsp;·&nbsp; {esc(change["reason"])}</div>',
        unsafe_allow_html=True,
    )


def render_kpis(result: AnalysisResult) -> None:
    assessments = result.llm_assessments.assessments if result.llm_assessments else []
    counts = {"DIRECT": 0, "POTENTIAL": 0, "NO_IMPACT": 0}
    for assessment in assessments:
        counts[assessment.impact_level] = counts.get(assessment.impact_level, 0) + 1
    cards = (
        ("High Impact", counts["DIRECT"], "Directly affected", "kpi-high"),
        ("Medium Impact", counts["POTENTIAL"], "Requires review", "kpi-medium"),
        ("Low Impact", counts["NO_IMPACT"], "No impact identified", "kpi-low"),
        ("Total Affected", len(result.ranked_candidates), "Ranked artifacts", ""),
    )
    st.markdown('<div class="section-title">Impact Analysis</div>',
                unsafe_allow_html=True)
    columns = st.columns(4, gap="medium")
    for column, (label, value, meta, tone) in zip(columns, cards):
        with column:
            st.markdown(
                f'<div class="panel kpi {tone}"><div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div><div class="kpi-meta">{meta}</div></div>',
                unsafe_allow_html=True,
            )


def trace_chain(result: AnalysisResult) -> list[str]:
    graph = get_graph()
    chain = [result.requirement_id]
    current = result.requirement_id
    for artifact_type in ("system_requirement", "software_requirement", "test_case"):
        next_nodes = [
            node for node in graph.successors(current)
            if graph.nodes[node].get("type") == artifact_type
        ]
        if not next_nodes:
            break
        current = next_nodes[0]
        chain.append(current)
    return chain


def render_traceability(result: AnalysisResult) -> None:
    graph = get_graph()
    nodes = []
    chain = trace_chain(result)
    for index, node in enumerate(chain):
        node_type = graph.nodes[node].get("type", "").replace("_", " ")
        nodes.append(
            f'<div class="trace-node"><div class="trace-id">{esc(node)}</div>'
            f'<div class="trace-type">{esc(node_type)}</div></div>'
        )
        if index < len(chain) - 1:
            nodes.append('<div class="trace-arrow">→</div>')
    st.markdown('<div class="section-title">Impact Chain</div>',
                unsafe_allow_html=True)
    st.markdown(
        f'<div class="panel trace-shell"><div class="trace-flow">{"".join(nodes)}</div></div>',
        unsafe_allow_html=True,
    )


def render_breakdown(result: AnalysisResult) -> None:
    table = result.ranked_candidates.copy()
    assessments = {}
    if result.llm_assessments:
        assessments = {item.artifact_id: item for item in result.llm_assessments.assessments}
    table["Impact Level"] = table["id"].map(
        lambda artifact_id: {
            "DIRECT": "HIGH · DIRECT",
            "POTENTIAL": "MEDIUM · POTENTIAL",
            "NO_IMPACT": "LOW · NO IMPACT",
        }.get(getattr(assessments.get(artifact_id), "impact_level", ""), "UNASSESSED")
    )
    table["Confidence"] = table["id"].map(
        lambda artifact_id: getattr(assessments.get(artifact_id), "confidence", 0.0)
    )
    table["Traceability"] = table["graph_linked"].map(
        lambda linked: "Linked" if linked else "Needs review"
    )
    display = table[["id", "type", "Impact Level", "Confidence", "Traceability", "text"]]
    colors = {
        "HIGH · DIRECT": ("#F8DEDE", "#9E2A2B"),
        "MEDIUM · POTENTIAL": ("#FCE8C8", "#9A5300"),
        "LOW · NO IMPACT": ("#DDF4EA", "#056B4A"),
        "UNASSESSED": ("#E9EDE9", "#4D5C56"),
    }

    def style_impact(value: str) -> str:
        background, foreground = colors.get(value, colors["UNASSESSED"])
        return (
            f"background-color: {background}; color: {foreground}; font-weight: 700;"
            " border-radius: 999px; padding: 5px 9px; "
            "border-top: 4px solid transparent; border-bottom: 4px solid transparent;"
        )

    st.markdown('<div class="section-title">Impacted Artifacts</div>',
                unsafe_allow_html=True)
    st.dataframe(
        display.style.map(style_impact, subset=["Impact Level"]),
        use_container_width=True,
        hide_index=True,
        height=430,
        column_config={
            "id": st.column_config.TextColumn("Artifact ID", width="small"),
            "type": st.column_config.TextColumn("Artifact type", width="small"),
            "Impact Level": st.column_config.TextColumn("Impact level", width="medium"),
            "Confidence": st.column_config.ProgressColumn(
                "Confidence", min_value=0, max_value=1, format="%.0%%"
            ),
            "Traceability": st.column_config.TextColumn("Traceability", width="small"),
            "text": st.column_config.TextColumn("Engineering content", width="large"),
        },
    )


def render_detail(result: AnalysisResult) -> None:
    """Render one ranked artifact and its available traceability paths."""
    ids = result.ranked_candidates["id"].tolist()
    if not ids:
        return
    selected = st.selectbox("Artifact", ids, label_visibility="collapsed")
    row = result.ranked_candidates.loc[
        result.ranked_candidates["id"] == selected
    ].iloc[0]
    st.markdown(
        f'<div class="panel"><div class="panel-label">Artifact · '
        f'<span class="mono">{esc(selected)}</span></div>'
        f'<div class="requirement-text">{esc(row["text"])}</div></div>',
        unsafe_allow_html=True,
    )
    paths = row.get("paths") or []
    st.caption(
        " · ".join(" → ".join(path) for path in paths[:3])
        if paths else "No explicit traceability path found."
    )


def run_analysis(change_id: str, model: str) -> None:
    from src.orchestrator import analyze_change

    with st.spinner("Analyzing engineering impact..."):
        st.session_state.analysis_result = analyze_change(
            change_id=change_id,
            llm_model=model,
            skip_llm=False,
            top_k_llm=None,
        )


def main() -> None:
    inject_css()
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None

    data = get_data()
    change_id, model = render_sidebar(data["changes"])
    change = data["changes"].loc[data["changes"]["change_id"] == change_id].iloc[0]
    render_header()
    render_delta(change)

    if st.button("Analyze Impact", type="primary", use_container_width=True):
        run_analysis(change_id, model)

    result = st.session_state.analysis_result
    if result is not None and result.change_id == change_id:
        if result.error:
            st.warning(result.error)
        render_kpis(result)
        render_traceability(result)
        render_breakdown(result)
        with st.expander("View Details", expanded=False):
            render_detail(result)
    else:
        st.markdown(
            '<div class="empty-state"><span class="empty-state-icon" aria-hidden="true">→</span>'
            '<span>Select a change request and choose <strong>Analyze Impact</strong> to begin.</span></div>',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
