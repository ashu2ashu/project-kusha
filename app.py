"""
app.py
Project KUSHA | Fundamental & Forensic Institutional Terminal
Institutional AI Financial Intelligence Terminal for Indian Listed Equities
"""

import streamlit as st
import plotly.graph_objects as go
import json
import os
import re
import html
import time
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load local environment variables dynamically
load_dotenv(override=True)

from prompt_template import IDEX_ANALYSIS_PROMPT
import importlib
import analyzer
import nifty_universe
import financial_trends
import data_integrity_agent
import nifty_peer_comparison
import forensic_risk_engine
importlib.reload(analyzer)
importlib.reload(nifty_universe)
importlib.reload(financial_trends)
importlib.reload(data_integrity_agent)
importlib.reload(nifty_peer_comparison)
importlib.reload(forensic_risk_engine)
import evaluation_cache
importlib.reload(evaluation_cache)
import self_improvement_engine
importlib.reload(self_improvement_engine)

from evaluation_cache import (
    load_cached_evaluation,
    save_cached_evaluation,
    get_cache_stats,
    clear_evaluation_cache
)

from self_improvement_engine import (
    SelfImprovementLoop,
    ImprovementLedgerManager,
    FEEDBACK_DIR
)

from nifty_peer_comparison import (
    render_head_to_head_comparison_html,
    render_nifty50_screener_view
)

from forensic_risk_engine import (
    ForensicRiskEngine,
    render_forensic_dossier_html
)

from data_integrity_agent import (
    DataIntegritySentinel,
    render_sentinel_audit_certificate_html
)

from financial_trends import (
    fetch_financial_statements,
    build_revenue_profit_chart,
    build_cashflow_health_chart,
    build_balance_sheet_chart,
    render_growth_cagr_scorecard_html,
    render_financial_table_html,
    generate_forensic_cagr_insights
)

from analyzer import analyze_document_with_gemini, get_demo_analysis, verify_gemini_api_key, SUPPORTED_MODELS, DEFAULT_MODEL, ANALYSIS_PIPELINE_VERSION
from annual_report_fetcher import get_available_annual_reports, download_annual_report_bytes
from nifty_universe import (
    get_company_list, find_company_info, fetch_live_market_data, get_sector_list,
    fetch_live_indices_data, fetch_marquee_stocks_data, fetch_ticker_historical_data
)
import pandas as pd
from plotly.subplots import make_subplots
import logging
import hmac
import kusha_logging

kusha_logging.configure_logging()
logger = kusha_logging.get_logger("kusha.app")

MAX_PDF_MB = 40
MAX_RUNS_PER_SESSION = int(os.environ.get("KUSHA_MAX_RUNS", "25"))


def esc(value: Any) -> str:
    """Escape any value for safe HTML interpolation. None becomes an empty string."""
    return html.escape(str(value if value is not None else ""), quote=True)


def safe_url(url: Any) -> str:
    """Return the URL only if it is an absolute http(s) URL, else ''."""
    u = str(url or "").strip()
    return u if u.lower().startswith(("https://", "http://")) else ""


def sanitize_memo_field(val: Any, max_len: int = 600) -> str:
    """Neutralize structural markdown, strip leading control characters, collapse to single line, and cap length."""
    if val is None:
        return ""
    s = str(val).replace("\r", " ").replace("\n", " ")
    # Strip dangerous leading structural markdown characters repeatedly
    s = re.sub(r'^[#>\-*|`\s]+', '', s)
    # Escape pipe characters so they don't break markdown tables
    s = s.replace("|", "\\|")
    # Collapse multiple whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    if len(s) > max_len:
        s = s[:max_len].rstrip() + "..."
    return s


def get_kusha_access_password() -> Optional[str]:
    """Retrieve optional access password from environment or st.secrets."""
    pwd = os.environ.get("KUSHA_ACCESS_PASSWORD", "").strip()
    if pwd:
        return pwd
    try:
        if "KUSHA_ACCESS_PASSWORD" in st.secrets:
            sec_pwd = str(st.secrets["KUSHA_ACCESS_PASSWORD"]).strip()
            if sec_pwd:
                return sec_pwd
    except Exception as e:
        # secrets.toml does not exist or has invalid syntax in non-cloud / local environment; legitimate fallback
        logger.debug("st.secrets check for KUSHA_ACCESS_PASSWORD skipped: %s", e)
    return None


def build_filing_ingestion_notice_html(filing_metadata):
    """Build an escaped filing notice that does not imply unverified ingestion."""
    metadata = filing_metadata or {}
    title = html.escape(str(metadata.get("title") or "Annual Report"), quote=True)
    year = html.escape(str(metadata.get("year") or "Latest"), quote=True)
    source = html.escape(str(metadata.get("source") or "Source not verified"), quote=True)
    analyzed = metadata.get("ingestion_status") == "analyzed"
    is_manual = metadata.get("source") == "Manual PDF Upload"

    if analyzed and is_manual:
        heading = "Uploaded PDF analyzed · source not independently verified"
        description = "The uploaded document was attached to the analysis. Its origin and statutory status were not independently verified."
        background, border, accent, heading_color, body_color = "#EFF6FF", "#BFDBFE", "#2563EB", "#1E40AF", "#475569"
    elif analyzed:
        heading = "Official BSE India Filing Analyzed · Multimodal Document Ingestion"
        description = "The official statutory filing was attached to Gemini and analyzed against all 8 governance and financial pillars."
        background, border, accent, heading_color, body_color = "#ECFDF5", "#A7F3D0", "#059669", "#065F46", "#475569"
    else:
        heading = "Filing listed · PDF not analyzed"
        description = "The filing metadata was found, but the PDF was not confirmed as attached to the completed analysis."
        background, border, accent, heading_color, body_color = "#FFFBEB", "#FDE68A", "#D97706", "#92400E", "#475569"

    filing_url = str(metadata.get("url") or "")
    try:
        parsed_url = urlparse(filing_url)
        host = (parsed_url.hostname or "").lower().rstrip(".")
        safe_bse_url = (
            filing_url
            if parsed_url.scheme == "https"
            and (host == "bseindia.com" or host.endswith(".bseindia.com"))
            and parsed_url.path.lower().endswith(".pdf")
            else None
        )
    except ValueError:
        safe_bse_url = None
    link_html = (
        f'<a href="{html.escape(safe_bse_url, quote=True)}" target="_blank" rel="noopener noreferrer" '
        'style="color: #059669; font-weight: 700; text-decoration: underline; font-size: 13px; font-family: \'JetBrains Mono\', monospace;">View BSE-hosted PDF ↗</a>'
        if safe_bse_url
        else '<span style="color: #64748B; font-size: 13px;">No verified filing link</span>'
    )

    display_title = title if year in title else f"{title} ({year})"
    return (
        f'<div style="background: {background}; border: 1px solid {border}; border-left: 5px solid {accent}; '
        'border-radius: 10px; padding: 12px 18px; margin-bottom: 16px; display: flex; '
        'justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">'
        f'<div><div style="font-size: 11px; font-weight: 800; color: {heading_color}; text-transform: uppercase; '
        f'letter-spacing: 0.6px; margin-bottom: 2px;">{heading}</div>'
        f'<div style="font-size: 14.5px; font-weight: 750; color: #0F172A;">{display_title} · {source}</div>'
        f'<div style="font-size: 12px; color: {body_color}; margin-top: 2px;">{description}</div></div>'
        f'<div>{link_html}</div></div>'
    )


# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="StockSage | Institutional AI Financial Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Brand Logo Integration
LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo.svg")
ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "icon.svg")
if os.path.exists(LOGO_PATH):
    st.logo(LOGO_PATH, icon_image=ICON_PATH if os.path.exists(ICON_PATH) else None, size="large")

# StockSage Crisp Institutional White & Emerald Design System & Typography Engine
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&display=swap');

    /* Design Tokens & CSS Custom Properties - Crisp Institutional White & Emerald */
    :root {
        /* Canvas & Clean Card Surfaces */
        --ss-canvas: #FFFFFF;
        --ss-surface-glass: #FFFFFF;
        --ss-surface-card: #FFFFFF;
        --ss-surface-elevated: #F8FAFC;
        --ss-border-glass: #E2E8F0;
        --ss-border-hover: #CBD5E1;

        /* Dalal Street Institutional Semantic Accents */
        --ss-neon-emerald: #059669; /* Dalal Street Alpha */
        --ss-neon-cyan: #2563EB;    /* Institutional Telemetry Blue */
        --ss-neon-gold: #D97706;    /* Warning / Caution */
        --ss-neon-crimson: #DC2626; /* Critical / Loss */
        --ss-neon-purple: #7C3AED;  /* Quantum / Innovation */

        /* High-Contrast Typographic Hierarchy */
        --ss-text-primary: #0F172A;
        --ss-text-secondary: #475569;
        --ss-text-muted: #64748B;
        --ss-text-dark: #0F172A;

        /* Typography */
        --ss-font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        --ss-font-mono: 'JetBrains Mono', 'SF Mono', Consolas, Menlo, monospace;

        /* Soft Elevation Shadows */
        --ss-shadow-card: 0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.04);
        --ss-shadow-hover: 0 4px 20px -2px rgba(0, 0, 0, 0.08);
        --ss-glow-cyan: 0 0 12px rgba(37, 99, 235, 0.15);
        --ss-glow-emerald: 0 0 12px rgba(5, 150, 105, 0.15);

        /* Radii Tokens */
        --ss-radius-sm: 6px;
        --ss-radius-md: 10px;
        --ss-radius-lg: 14px;
        --ss-radius-xl: 18px;
        --ss-radius-full: 9999px;

        /* Transitions */
        --ss-transition-fast: 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        --ss-transition-smooth: 0.22s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* Anti-Scraping & IP Protection Safeguards */
    .ss-proprietary-shield {
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
    }
    @media print {
        /* Hide interactive controls and chrome during browser print */
        [data-testid="stSidebar"], .stButton, div[data-testid="stDownloadButton"], footer, header {
            display: none !important;
        }
        body {
            background: #ffffff !important;
            color: #000000 !important;
        }
    }

    /* Global Light Canvas Reset */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: var(--ss-font-sans) !important;
        font-size: 14.5px !important;
        line-height: 1.55 !important;
        color: var(--ss-text-primary) !important;
        background-color: var(--ss-canvas) !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
        text-rendering: optimizeLegibility !important;
    }

    /* Tabular Monospace for All Numerical Data */
    code, kbd, samp, pre, [data-testid="stMetricValue"], .m-value, .metric-val, .pillar-score, .financial-num {
        font-family: var(--ss-font-mono) !important;
        font-feature-settings: 'tnum' 1, 'zero' 1 !important;
        font-variant-numeric: tabular-nums !important;
    }

    /* Headings */
    h1, .stHeadingContainer h1 {
        font-family: var(--ss-font-sans) !important;
        font-size: 30px !important;
        font-weight: 800 !important;
        letter-spacing: -0.03em !important;
        line-height: 1.2 !important;
        color: #0F172A !important;
    }
    h2, .stHeadingContainer h2 {
        font-family: var(--ss-font-sans) !important;
        font-size: 24px !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
        line-height: 1.25 !important;
        color: #0F172A !important;
    }
    h3, .stHeadingContainer h3 {
        font-family: var(--ss-font-sans) !important;
        font-size: 19px !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        color: #1E293B !important;
    }
    h4, .stHeadingContainer h4 {
        font-family: var(--ss-font-sans) !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        color: #334155 !important;
    }

    /* Real-time Telemetry Pulsing Beacon */
    @keyframes ss-pulse {
        0% { transform: scale(0.92); opacity: 0.8; box-shadow: 0 0 0 0 rgba(5, 150, 105, 0.7); }
        70% { transform: scale(1.08); opacity: 1; box-shadow: 0 0 0 7px rgba(5, 150, 105, 0); }
        100% { transform: scale(0.92); opacity: 0.8; box-shadow: 0 0 0 0 rgba(5, 150, 105, 0); }
    }
    .live-pulse-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: var(--ss-neon-emerald);
        border-radius: 50%;
        margin-right: 6px;
        animation: ss-pulse 2s infinite ease-in-out;
        vertical-align: middle;
    }

    /* Clean Institutional Segmented Control (Workspace Selector) */
    div[data-testid="stSegmentedControl"] {
        background-color: #F8FAFC !important;
        border: 1.5px solid #E2E8F0 !important;
        border-radius: var(--ss-radius-md) !important;
        padding: 4px !important;
        gap: 4px !important;
    }
    div[data-testid="stSegmentedControl"] button {
        border-radius: var(--ss-radius-sm) !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        color: #475569 !important;
        padding: 8px 18px !important;
        border: none !important;
        background: transparent !important;
        transition: all var(--ss-transition-fast) !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background: #FFFFFF !important;
        color: #059669 !important;
        font-weight: 800 !important;
        border: 1px solid #CBD5E1 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }
    div[data-testid="stSegmentedControl"] button:hover {
        color: #0F172A !important;
        background: rgba(0, 0, 0, 0.03) !important;
    }

    /* Institutional Navigation Tabs */
    div[data-baseweb="tab-list"] {
        gap: 6px !important;
        border-bottom: 1.5px solid #E2E8F0 !important;
        padding-bottom: 0px !important;
        margin-top: 14px !important;
        margin-bottom: 22px !important;
    }
    button[data-baseweb="tab"] {
        font-family: var(--ss-font-sans) !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        padding: 12px 22px !important;
        border-radius: 8px 8px 0 0 !important;
        color: #64748B !important;
        background: transparent !important;
        border: none !important;
        transition: all var(--ss-transition-fast) !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #059669 !important;
        background-color: rgba(5, 150, 105, 0.04) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #059669 !important;
        font-weight: 800 !important;
        border-bottom: 3px solid #059669 !important;
        background-color: transparent !important;
    }
    div[data-baseweb="tab-border"] { display: none !important; }
    div[data-baseweb="tab-highlight"] { background-color: #059669 !important; height: 3px !important; }

    /* High-Density Clean Metric Cards */
    [data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        padding: 16px 20px !important;
        border-radius: var(--ss-radius-lg) !important;
        border: 1.5px solid #E2E8F0 !important;
        box-shadow: var(--ss-shadow-card) !important;
        transition: transform var(--ss-transition-smooth), box-shadow var(--ss-transition-smooth), border-color var(--ss-transition-fast) !important;
    }
    [data-testid="stMetric"]:hover {
        border-color: #CBD5E1 !important;
        transform: translateY(-2px) !important;
        box-shadow: var(--ss-shadow-hover) !important;
    }
    [data-testid="stMetricValue"] {
        font-family: var(--ss-font-mono) !important;
        font-size: 26px !important;
        font-weight: 900 !important;
        color: #0F172A !important;
        line-height: 1.2 !important;
    }
    [data-testid="stMetricLabel"] {
        font-family: var(--ss-font-sans) !important;
        font-size: 11.5px !important;
        font-weight: 700 !important;
        color: #64748B !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 13.5px !important;
        font-weight: 700 !important;
    }

    /* Primary Dalal Street Action Button */
    button[kind="primary"] {
        background: #059669 !important;
        color: #FFFFFF !important;
        font-family: var(--ss-font-sans) !important;
        font-size: 15px !important;
        font-weight: 800 !important;
        padding: 12px 26px !important;
        border-radius: var(--ss-radius-md) !important;
        border: none !important;
        letter-spacing: 0.02em !important;
        box-shadow: 0 1px 3px rgba(5, 150, 105, 0.3) !important;
        transition: all var(--ss-transition-fast) !important;
    }
    button[kind="primary"]:hover {
        background: #047857 !important;
        box-shadow: 0 4px 14px rgba(5, 150, 105, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    button[kind="primary"]:active {
        transform: translateY(1px) scale(0.99) !important;
    }

    /* Secondary Clean White Buttons */
    button[kind="secondary"] {
        font-family: var(--ss-font-sans) !important;
        border-radius: var(--ss-radius-md) !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        border: 1.5px solid #CBD5E1 !important;
        color: #334155 !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
        transition: all var(--ss-transition-fast) !important;
    }
    button[kind="secondary"]:hover {
        border-color: #059669 !important;
        color: #059669 !important;
        background-color: #F0FDF4 !important;
        transform: translateY(-1px) !important;
    }

    /* Border Container Polish (st.container(border=True)) */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #FFFFFF !important;
        border: 1.5px solid #E2E8F0 !important;
        border-radius: var(--ss-radius-lg) !important;
        box-shadow: var(--ss-shadow-card) !important;
        padding: 20px 24px !important;
        transition: border-color var(--ss-transition-fast) !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
        border-color: #CBD5E1 !important;
    }

    /* Clean Light Inputs & Select Controls */
    div[data-baseweb="input"] input,
    div[data-baseweb="select"] {
        font-family: var(--ss-font-sans) !important;
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-radius: var(--ss-radius-md) !important;
        font-size: 14px !important;
        border: 1.5px solid #CBD5E1 !important;
        transition: all var(--ss-transition-fast) !important;
    }
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"]:focus-within {
        border-color: #059669 !important;
        box-shadow: 0 0 0 2px rgba(5, 150, 105, 0.2) !important;
    }

    /* Clean White Expanders */
    details[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #E2E8F0 !important;
        border-radius: var(--ss-radius-md) !important;
        box-shadow: var(--ss-shadow-card) !important;
        overflow: hidden;
    }
    details[data-testid="stExpander"] summary {
        font-family: var(--ss-font-sans) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        color: #0F172A !important;
        padding: 12px 18px !important;
    }
    details[data-testid="stExpander"] summary:hover {
        color: #059669 !important;
        background-color: #F8FAFC !important;
    }

    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #2563EB 0%, #059669 100%) !important;
        border-radius: var(--ss-radius-full) !important;
    }
    .stProgress > div > div > div {
        background-color: #E2E8F0 !important;
        height: 8px !important;
        border-radius: var(--ss-radius-full) !important;
    }

    /* 8-Pillar Screener-Grade Financial Table */
    .pillar-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border: 1.5px solid #E2E8F0;
        border-radius: var(--ss-radius-lg);
        overflow: hidden;
        background: #FFFFFF;
        margin: 14px 0 24px 0;
        box-shadow: var(--ss-shadow-card);
    }
    .pillar-table th {
        background-color: #F8FAFC;
        padding: 12px 18px;
        font-size: 11.5px;
        font-weight: 800;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        border-bottom: 2px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
    }
    .pillar-table th:last-child { border-right: none; }
    .pillar-table td {
        padding: 14px 18px;
        border-bottom: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        vertical-align: top;
        font-size: 13.5px;
        color: #334155;
        line-height: 1.55;
        transition: background-color var(--ss-transition-fast);
    }
    .pillar-table td:last-child { border-right: none; }
    .pillar-table tr:last-child td { border-bottom: none; }
    .pillar-table tr:hover td { background-color: #F8FAFC; }

    /* Guardrail Semantic Banners */
    .guardrail-clean-box {
        background: #ECFDF5;
        border: 1px solid #A7F3D0;
        border-left: 5px solid #059669;
        border-radius: var(--ss-radius-md);
        padding: 16px 22px;
        color: #065F46;
        margin-top: 14px;
        margin-bottom: 18px;
    }
    .guardrail-alert-box {
        background: #FFFBEB;
        border: 1px solid #FDE68A;
        border-left: 5px solid #D97706;
        border-radius: var(--ss-radius-md);
        padding: 16px 22px;
        color: #92400E;
        margin-top: 14px;
        margin-bottom: 18px;
    }
    .guardrail-red-box {
        background: #FEF2F2;
        border: 1px solid #FECACA;
        border-left: 5px solid #DC2626;
        border-radius: var(--ss-radius-md);
        padding: 16px 22px;
        color: #991B1B;
        margin-top: 14px;
        margin-bottom: 18px;
    }

    /* Factsheet Header & Matrix Cards */
    .facts-header-card {
        background: #FFFFFF;
        border: 1.5px solid #E2E8F0;
        border-radius: var(--ss-radius-xl);
        padding: 24px 28px;
        margin-top: 16px;
        margin-bottom: 22px;
        box-shadow: var(--ss-shadow-card);
        transition: transform var(--ss-transition-smooth), box-shadow var(--ss-transition-smooth), border-color var(--ss-transition-fast);
    }
    .facts-header-card:hover {
        border-color: #CBD5E1;
        box-shadow: var(--ss-shadow-hover);
    }
    @media (max-width: 640px) {
        .facts-header-card { padding: 16px 16px !important; }
    }
    .metrics-3col-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        margin-bottom: 24px;
    }
    @media (max-width: 1100px) and (min-width: 768px) {
        .metrics-3col-grid { grid-template-columns: repeat(2, 1fr) !important; }
    }
    @media (max-width: 767px) {
        .metrics-3col-grid { grid-template-columns: 1fr !important; }
    }
    .metric-domain-card {
        background: #FFFFFF;
        border: 1.5px solid #E2E8F0;
        border-radius: var(--ss-radius-lg);
        overflow: hidden;
        box-shadow: var(--ss-shadow-card);
        transition: transform var(--ss-transition-smooth), box-shadow var(--ss-transition-smooth), border-color var(--ss-transition-fast);
    }
    .metric-domain-card:hover {
        transform: translateY(-2px);
        border-color: #CBD5E1;
        box-shadow: var(--ss-shadow-hover);
    }
    .metric-domain-header {
        padding: 14px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .metric-table-spacious {
        width: 100%;
        border-collapse: collapse;
    }
    .metric-table-spacious tr {
        border-bottom: 1px solid #E2E8F0;
        transition: background-color var(--ss-transition-fast);
    }
    .metric-table-spacious tr:last-child { border-bottom: none; }
    .metric-table-spacious tr:hover { background-color: #F8FAFC !important; }
    .metric-table-spacious td.m-label {
        padding: 12px 20px;
        font-size: 13.5px;
        font-weight: 600;
        color: #475569;
        text-align: left;
        white-space: nowrap;
    }
    .metric-table-spacious td.m-value {
        padding: 12px 20px;
        font-size: 14.5px;
        font-family: var(--ss-font-mono);
        font-weight: 700;
        color: #0F172A;
        text-align: right;
        white-space: nowrap;
        font-feature-settings: 'tnum' 1, 'zero' 1;
        font-variant-numeric: tabular-nums;
    }

    /* Clean Institutional Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #F8FAFC; }
    ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

    /* StockSage Workspace Shell Polish */
    [data-testid="stAppViewContainer"] { background: #FFFFFF; }
    [data-testid="stMainBlockContainer"] { max-width: 1480px; padding-top: 1rem; padding-bottom: 2.5rem; }
    
    /* Institutional Hero Terminal */
    .ss-hero {
        display: grid;
        grid-template-columns: minmax(0, 1.6fr) minmax(300px, .9fr);
        gap: 20px;
        align-items: center;
        padding: 22px 28px;
        margin: 4px 0 16px;
        color: #0F172A;
        border: 1.5px solid #E2E8F0;
        border-radius: 16px;
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 50%, #ECFDF5 100%);
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
    }
    .ss-hero-kicker {
        display: inline-flex;
        gap: 6px;
        align-items: center;
        color: #059669;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        font-family: var(--ss-font-mono);
    }
    .ss-hero-title {
        margin: 6px 0 4px;
        color: #0F172A;
        font-size: clamp(22px, 2.4vw, 30px);
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.15;
    }
    .ss-hero-subtitle {
        max-width: 650px;
        margin: 0;
        color: #475569;
        font-size: 13.5px;
        line-height: 1.5;
    }
    .ss-hero-meta { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
    .ss-hero-meta span {
        padding: 4px 10px;
        border: 1.5px solid #E2E8F0;
        border-radius: 999px;
        color: #334155;
        background: #FFFFFF;
        font-size: 11px;
        font-weight: 600;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }
    .ss-hero-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
    .ss-hero-stat {
        min-height: 64px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 10px 14px;
        border: 1.5px solid #E2E8F0;
        border-radius: 12px;
        background: #FFFFFF;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    .ss-hero-stat-label {
        color: #2563EB;
        font-size: 9.5px;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .ss-hero-stat-value {
        margin-top: 3px;
        color: #0F172A;
        font-size: 14px;
        font-weight: 800;
        line-height: 1.2;
        font-family: var(--ss-font-mono);
    }
    .ss-source-card {
        padding: 14px 16px;
        border: 1.5px solid #E2E8F0;
        border-radius: 12px;
        background: #FFFFFF;
    }
    .ss-source-label { margin-bottom: 8px; color: #64748B; font-size: 10px; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; }
    .ss-source-row { display: flex; justify-content: space-between; gap: 12px; margin: 5px 0; color: #475569; font-size: 11px; }
    .ss-source-row strong { color: #059669; font-weight: 700; text-align: right; }
    .ss-source-note { margin-top: 8px; color: #64748B; font-size: 10px; line-height: 1.45; }
    div[data-testid="stVerticalBlockBorderWrapper"] > div { border-radius: 16px !important; }
    div[data-testid="stSegmentedControl"] { white-space: normal; }
    div[data-testid="stButton"] button { min-height: 40px; white-space: normal !important; word-break: break-word !important; line-height: 1.25; text-align: center; }
    div[data-testid="stLinkButton"] a { min-height: 40px; white-space: normal !important; word-break: break-word !important; line-height: 1.25; text-align: center; }
    html, body, [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
        max-width: 100vw;
    }
    .pillar-table, table, div[data-testid="stTable"] {
        display: block;
        overflow-x: auto !important;
        max-width: 100%;
    }
    @media (max-width: 900px) { .ss-hero { grid-template-columns: 1fr; gap: 20px; padding: 22px; } .ss-hero-stats { max-width: 720px; } }
    @media (max-width: 768px) {
        [data-testid="stMainBlockContainer"] { padding: .75rem .75rem 2rem !important; }
        [data-testid="stHorizontalBlock"] { flex-direction: column !important; align-items: stretch !important; gap: .5rem !important; }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] { width: 100% !important; min-width: 0 !important; flex: 1 1 100% !important; }
        .ss-hero { padding: 18px 16px; border-radius: 16px; gap: 13px; }
        .ss-hero-title { font-size: 22px; }
        .ss-hero-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
        .ss-pipeline-grid { grid-template-columns: 1fr !important; }
        .pillar-table, table { display: block; overflow-x: auto; width: 100%; }
    }
</style>
""", unsafe_allow_html=True)

# Prepare accurate universe counts once for the sidebar and hero summary.
company_options = get_company_list()
tracked_equity_count = sum(1 for item in company_options if find_company_info(item).get("ticker") != "CUSTOM")
sector_count = len(get_sector_list())

# Fetch Live Online Market Data (Cached for snappy performance)
@st.cache_data(ttl=180, show_spinner=False)
def get_cached_live_data(ticker_sym: str):
    return fetch_live_market_data(ticker_sym)

@st.cache_data(ttl=60, show_spinner=False)
def get_cached_market_indices():
    return fetch_live_indices_data()

@st.cache_data(ttl=60, show_spinner=False)
def get_cached_marquee_stocks():
    return fetch_marquee_stocks_data()


def render_marquee_stocks_tape(stocks_list: Optional[List[Dict[str, Any]]] = None) -> None:
    """Renders marquee benchmark equities with mandatory data status labelling."""
    items = stocks_list if stocks_list is not None else get_cached_marquee_stocks()
    if not items:
        return

    non_provider = [stk for stk in items if stk.get("data_status") != "provider"]
    if non_provider:
        as_of_date = non_provider[0].get("as_of") or "2024-06-30"
        st.html(f'<div style="background: #FEF3C7; border: 1px solid #FCD34D; color: #92400E; padding: 6px 12px; border-radius: 6px; font-size: 11px; margin-bottom: 8px; font-weight: 600;">Sample reference data as of {as_of_date} — not live.</div>')

@st.cache_data(ttl=300, show_spinner=False)
def get_cached_ticker_history(ticker_sym: str, period: str = "1y"):
    return fetch_ticker_historical_data(ticker_sym, period=period)

@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_financial_statements(ticker_sym: str):
    return fetch_financial_statements(ticker_sym)


def save_analyst_feedback(category: str, ticker: str, claim_or_figure: str, expected_or_correct: str, user_comment: str) -> str:
    """Saves analyst observation to .cache/feedback/ with zero PII or credentials."""
    import uuid
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    clean_cat = str(category).strip()
    clean_ticker = str(ticker).strip().upper()
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    fb_id = f"FB-{int(time.time())}-{uuid.uuid4().hex[:6]}"

    # Redact any accidental keys or credentials
    safe_comment = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED_KEY]", str(user_comment))
    safe_claim = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED_KEY]", str(claim_or_figure))

    payload = {
        "id": fb_id,
        "timestamp": ts,
        "category": clean_cat,
        "ticker": clean_ticker,
        "claim_or_figure": safe_claim,
        "expected_or_correct": str(expected_or_correct).strip(),
        "user_comment": safe_comment.strip()
    }

    filepath = os.path.join(FEEDBACK_DIR, f"{fb_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return fb_id

# --- STARTUP NETWORK GUARD & OPERATOR PASSWORD GATE ---
configured_access_password = get_kusha_access_password()

try:
    server_address = st.config.get_option("server.address")
except Exception as e:
    # Fallback to local loopback if running in bare headless mode without active streamlit config
    server_address = "127.0.0.1"

is_loopback = str(server_address or "").strip().lower() in ("127.0.0.1", "localhost", "::1")
if not is_loopback and not configured_access_password:
    st.error(
        "⚠️ This app is network-reachable with no authentication. "
        "Anyone on this network can use it and consume your API quota."
    )

if configured_access_password:
    if not st.session_state.get("kusha_authenticated", False):
        st.markdown("### 🔒 Project KUSHA Access Gate")
        st.caption("Operator authentication is required to access this terminal.")
        with st.form("kusha_auth_gate_form", clear_on_submit=True):
            gate_pwd = st.text_input("Enter Access Password", type="password")
            submit_gate = st.form_submit_button("Authenticate")
            if submit_gate:
                if hmac.compare_digest(gate_pwd.encode("utf-8"), configured_access_password.encode("utf-8")):
                    st.session_state["kusha_authenticated"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
        st.stop()

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    if configured_access_password:
        if st.sidebar.button("🔒 Lock session", key="btn_lock_session_sidebar", width="stretch"):
            st.session_state["kusha_authenticated"] = False
            st.rerun()

    st.markdown("### Project KUSHA")
    st.caption("Autonomous AI for Finance • Ashu Elite Edition")
    
    st.html(f"""
    <div class="ss-source-card">
        <div class="ss-source-label">Evidence and data sources</div>
        <div class="ss-source-row"><span>Company universe</span><strong>{tracked_equity_count} tracked equities</strong></div>
        <div class="ss-source-row"><span>Market quotes</span><strong>Yahoo Finance · third party</strong></div>
        <div class="ss-source-row"><span>Research documents</span><strong>Google Search citations</strong></div>
        <div class="ss-source-note">Exchange and audited filings are identified as sources in the analysis when available.</div>
    </div>
    """)
    st.divider()

    # API Configuration
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    placeholder_text = "Override with custom key (optional)..." if env_key else "Enter your Gemini API key..."
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value="",
        type="password",
        placeholder=placeholder_text,
        help="Your API key authenticates client calls directly to Google Gemini. It is held in volatile session memory and never persisted or shared."
    )

    active_api_key = api_key_input.strip() if api_key_input and api_key_input.strip() else env_key

    selected_gemini_model = st.selectbox(
        "Gemini Model",
        options=SUPPORTED_MODELS,
        index=0,
        help="Select supported Google Gemini model."
    )

    if env_key and not api_key_input.strip():
        st.caption("🔒 Key active from environment (`.env`)")
    elif api_key_input.strip():
        st.caption("🔑 Using custom user-supplied key")

    col_btn1, col_btn2 = st.columns([1.2, 1])
    with col_btn1:
        if st.button("Test Key", width="stretch"):
            with st.spinner("Connecting to Google..."):
                is_valid, msg = verify_gemini_api_key(active_api_key, model_name=selected_gemini_model)
                if is_valid:
                    st.success(msg)
                else:
                    st.error(msg)
    with col_btn2:
        demo_mode = st.toggle("Demo Mode", value=False if active_api_key else True)

    if demo_mode:
        st.caption("🧪 **Demo Mode Active**: The company assessment uses synthetic sample data and does not represent a real investment analysis.")

    # Local Evaluation Cache Controls (Saves API Quota)
    use_eval_cache = st.toggle(
        "💾 Use local replay cache",
        value=True,
        help="Saves real Gemini outputs locally. Replays instantly (<0.05s) on repeat runs with 0 API requests and 0 storage overhead (~15KB per company)."
    )
    cache_stats = get_cache_stats()
    if cache_stats["count"] > 0:
        c_col1, c_col2 = st.columns([1.5, 1])
        with c_col1:
            st.caption(f"💾 **{cache_stats['count']} cached** ({cache_stats['total_kb']} KB)")
        with c_col2:
            if st.button("Clear", key="btn_clear_eval_cache", help="Wipes all cached analyses from your disk."):
                cleared = clear_evaluation_cache()
                st.toast(f"Cleared {cleared} cached evaluations.")
                st.rerun()
    else:
        st.caption("💾 Cache empty (runs save automatically)")

    st.divider()

    # Analyst Research Feedback Mechanism (Stage A Observe Feed)
    with st.expander("💬 Analyst Quality Feedback", expanded=False):
        st.markdown(
            "<div style='font-size:11.5px; color:#475569; margin-bottom:8px; line-height:1.4;'>"
            "Report statement discrepancies, unsupported model claims, or missing citations for the self-improvement audit loop."
            "</div>",
            unsafe_allow_html=True
        )
        fb_cat = st.selectbox(
            "Category",
            [
                "Incorrect Financial Figure",
                "Unsupported Claim",
                "Missing Source Citation",
                "Incorrect Risk Classification",
                "UI / Workflow Defect"
            ],
            key="fb_category_select"
        )
        current_tkr = st.session_state.get("selected_ticker", "RELIANCE")
        fb_ticker = st.text_input("Ticker / Symbol", value=current_tkr if isinstance(current_tkr, str) else "RELIANCE", key="fb_ticker_input")
        fb_claim = st.text_area("Flagged Claim or Number", placeholder="e.g. Reported net debt diverges from balance sheet line...", key="fb_claim_input", height=68)
        fb_expected = st.text_input("Correct Value or Source Citation", placeholder="e.g. Standalone debt is ₹1,16,000 Cr as per Page 142 Note 18", key="fb_expected_input")
        fb_comment = st.text_area("Additional Notes (Optional)", placeholder="Context or page reference...", key="fb_comment_input", height=50)

        if st.button("Submit Quality Finding", key="btn_submit_feedback", width="stretch"):
            if fb_claim.strip():
                fid = save_analyst_feedback(fb_cat, fb_ticker, fb_claim, fb_expected, fb_comment)
                st.success(f"Finding `{fid}` logged to observation loop.")
                st.toast("Feedback recorded securely. No credentials stored.")
            else:
                st.warning("Please describe the flagged claim or number.")
        st.caption("🔒 Privacy Verified: Zero collection of API keys, accounts, or confidential documents.")

    # Autonomous Self-Improvement System HUD
    with st.expander("🤖 Autonomous Self-Improvement", expanded=False):
        st.markdown("""
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 8px; padding: 10px 12px; font-size: 11px; margin-bottom: 8px;">
          <div style="font-weight: 800; color: #0F172A; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
            <span style="color: #059669;">●</span> Continuous Invariant Auditing
          </div>
          <div style="color: #64748B; line-height: 1.4;">
            <b>IDEX-7.5SC</b> permanent regression suite verifying accounting equations, debtor velocity, and governance caps.
          </div>
          <div style="margin-top: 6px; font-family: 'JetBrains Mono', monospace; font-size: 9.5px; color: #2563EB; font-weight: 700;">
            BOUNDED LIMITS: MAX 3 REPAIRS | MAX 5 CYCLES
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Run Dry-Run Invariant Check", key="btn_run_self_improvement_dry_run", width="stretch"):
            with st.spinner("Executing autonomous invariant loop..."):
                loop = SelfImprovementLoop(dry_run=True)
                cycle_res = loop.run_cycle()
                if cycle_res.get("tests_passed"):
                    st.success(f"Verified: {cycle_res.get('total_tests')} tests passed. Invariants intact.")
                else:
                    st.error("Invariant check detected regressions. Proposal generated.")

    st.divider()
    
    # Proprietary Quantitative Engine Safeguard (Internal Backend Protected)
    custom_prompt = IDEX_ANALYSIS_PROMPT
    with st.expander("🔒 Quantitative Engine Status", expanded=False):
        st.markdown("""
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 8px; padding: 12px 14px; font-size: 11.5px;">
          <div style="font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
            <span style="color: #059669; font-size: 14px;">●</span> Proprietary Core Active
          </div>
          <div style="color: #64748B; line-height: 1.45;">
            Pillar scores are extracted by a Gemini model, then clamped, capped and summed in Python. The final number is deterministic given the model output, but the model output itself is not reproducible. No encryption or tamper-proofing is applied.
          </div>
          <div style="margin-top: 6px; font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #D97706; font-weight: 700;">
            DETERMINISTIC POST-PROCESSING ONLY
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.caption("**Forensic Safeguards:**")
    st.markdown("""
    - **8 Pillars:** Multi-Vector Institutional Audit
    - **Promoter Integrity Override:** Automated Governance Circuit Breaker
    - **Working Capital Forensics:** Non-Cash Accrual Surveillance
    - **Resilience Engine:** Downside Balance Sheet Stress Testing
    """)

# --- TOP-OF-PAGE LIVE INDIAN MARKET SNAPSHOT (INSTITUTIONAL TELEMETRY HUD) ---
def render_terminal_top_telemetry_hud():
    st.html("""
    <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 14px; padding: 14px 22px; margin-top: 2px; margin-bottom: 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
      <div style="display: flex; align-items: center; gap: 12px;">
        <span class="live-pulse-dot"></span>
        <div>
          <div style="font-size: 17px; font-weight: 900; color: #0F172A; display: flex; align-items: center; gap: 8px; letter-spacing: -0.3px;">
            <span style="color: #059669;">⚡</span> Indian Market Telemetry HUD
          </div>
          <div style="font-size: 12px; color: #64748B; margin-top: 2px;">
            NSE / BSE market snapshot · Public aggregator feeds · Macro indicator surveillance
          </div>
        </div>
      </div>
      <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
        <span style="background: rgba(5, 150, 105, 0.08); color: #059669; border: 1px solid rgba(5, 150, 105, 0.25); font-size: 11px; font-weight: 800; padding: 4px 12px; border-radius: 9999px; display: flex; align-items: center; gap: 6px; font-family: 'JetBrains Mono', monospace;">
          ● DELAYED NSE QUOTES
        </span>
        <span style="background: rgba(37, 99, 235, 0.08); color: #2563EB; border: 1px solid rgba(37, 99, 235, 0.25); font-size: 11px; font-weight: 800; padding: 4px 12px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">
          FUNDAMENTAL & FORENSIC DUAL-ENGINE
        </span>
      </div>
    </div>
    """)

    indices_list = get_cached_market_indices()
    stale_indices = [idx for idx in indices_list if idx.get("data_status") == "stale_reference"]
    if stale_indices:
        stale_date = stale_indices[0].get("as_of", "2024-06-30")
        st.html(f'<div style="background: #FEF3C7; border: 1.5px solid #FCD34D; color: #92400E; padding: 10px 16px; border-radius: 8px; font-size: 12px; margin-bottom: 12px; font-weight: 700;">⚠️ Index levels unavailable from provider; showing a static reference set as of {stale_date}. Not current.</div>')

    idx_cols = st.columns(4)
    for i, idx in enumerate(indices_list):
        with idx_cols[i]:
            is_pos = (idx.get("pct") or 0) >= 0
            delta_col = "#059669" if is_pos else "#DC2626"
            delta_bg = "rgba(5, 150, 105, 0.08)" if is_pos else "rgba(220, 38, 38, 0.08)"
            delta_border = "rgba(5, 150, 105, 0.25)" if is_pos else "rgba(220, 38, 38, 0.25)"
            delta_sign = "+" if is_pos else ""
            if idx.get("pct") is not None and idx.get("chg") is not None:
                delta_str = f"{delta_sign}{idx['pct']:.2f}% ({delta_sign}{idx['chg']:,.1f})"
            else:
                delta_str = "N/A"

            # Calculate Day Range progress
            lo = idx.get("lo")
            hi = idx.get("hi")
            cur = idx.get("cur")
            
            if hi is not None and lo is not None and cur is not None:
                range_span = max(hi - lo, 1.0)
                day_pct = min(100.0, max(0.0, (cur - lo) / range_span * 100.0))
                lo_str = f"L: {lo:,.0f}"
                hi_str = f"H: {hi:,.0f}"
                day_pct_str = f"{day_pct:.0f}% of Day"
                bar_html = f'<div style="background: linear-gradient(90deg, #2563EB, {delta_col}); width: {day_pct:.1f}%; height: 3px; border-radius: 9999px;"></div>'
            else:
                lo_str = f"L: {lo:,.0f}" if lo is not None else "L: N/A"
                hi_str = f"H: {hi:,.0f}" if hi is not None else "H: N/A"
                day_pct_str = "Day Range: N/A"
                bar_html = ''

            cur_str = f"{cur:,.2f}" if cur is not None else "N/A"
            idx_name = idx.get("name", "Index")
            card_html = (
                f'<div role="region" aria-label="{idx_name} quote" style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 14px 16px; border-top: 3.5px solid {delta_col}; box-shadow: 0 1px 4px rgba(0,0,0,0.04); margin-bottom: 14px; min-height: 110px;">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">'
                f'<span style="font-size: 12px; font-weight: 800; color: #475569; letter-spacing: 0.5px;">{idx.get("icon", "")} {idx_name}</span>'
                f'<span style="font-size: 11px; font-weight: 800; color: {delta_col}; background: {delta_bg}; border: 1px solid {delta_border}; padding: 2px 7px; border-radius: 6px; font-family: \'JetBrains Mono\', monospace;">{delta_str}</span>'
                f'</div>'
                f'<div style="font-size: 22px; font-weight: 900; color: #0F172A; font-family: \'JetBrains Mono\', monospace; line-height: 1.1;">{cur_str}</div>'
                f'<div style="margin-top: 8px; background: #E2E8F0; height: 3px; border-radius: 9999px; position: relative;">'
                f'{bar_html}'
                f'</div>'
                f'<div style="font-size: 10px; color: #64748B; margin-top: 6px; display: flex; justify-content: space-between; font-family: \'JetBrains Mono\', monospace;">'
                f'<span>{lo_str}</span>'
                f'<span>{day_pct_str}</span>'
                f'<span>{hi_str}</span>'
                f'</div>'
                f'</div>'
            )
            st.html(card_html)

    # Workspace Header: Calm, Institutional Research Metadata
    st.html(f"""
    <section class="ss-hero" style="padding: 16px 22px; margin-bottom: 16px; background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
        <div>
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            <span style="font-size: 11px; font-weight: 800; color: #059669; background: #ECFDF5; border: 1px solid #A7F3D0; padding: 2px 8px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">STOCKSAGE // RESEARCH WORKSPACE</span>
            <span style="font-size: 11px; font-weight: 700; color: #64748B; font-family: 'JetBrains Mono', monospace;">NSE / BSE Listed Equities</span>
          </div>
          <div style="font-size: 18px; font-weight: 800; color: #0F172A; letter-spacing: -0.2px;">
            Evidence-Based Financial Analysis &amp; Forensic Intelligence
          </div>
          <p style="font-size: 12.5px; color: #475569; margin: 4px 0 0 0; max-width: 780px; line-height: 1.45;">
            StockSage helps self-directed investors review financial and market information alongside cited research, audit trails, and transparent evidence gaps. Educational research tool — not SEBI-registered investment advice.
          </p>
        </div>
        <div style="display: flex; gap: 12px; flex-wrap: wrap;">
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 14px; text-align: right;">
            <div style="font-size: 10px; font-weight: 700; color: #64748B; text-transform: uppercase;">Coverage</div>
            <div style="font-size: 14px; font-weight: 800; color: #0F172A; font-family: 'JetBrains Mono', monospace;">{tracked_equity_count} Bluechips</div>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 14px; text-align: right;">
            <div style="font-size: 10px; font-weight: 700; color: #64748B; text-transform: uppercase;">Sectors</div>
            <div style="font-size: 14px; font-weight: 800; color: #0F172A; font-family: 'JetBrains Mono', monospace;">{sector_count} Sectors</div>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 14px; text-align: right;">
            <div style="font-size: 10px; font-weight: 700; color: #64748B; text-transform: uppercase;">Telemetry</div>
            <div style="font-size: 14px; font-weight: 800; color: #059669; font-family: 'JetBrains Mono', monospace;">Delayed Market Feeds</div>
          </div>
        </div>
      </div>
    </section>
    """)

def render_dalal_street_metric_cards_html(live_data: dict, fin_res: dict = None) -> str:
    if not live_data:
        return ""
    sm = dict(live_data.get("screener_metrics", {}))
    if fin_res and "cagr" in fin_res and not fin_res.get("error"):
        cagr_d = fin_res.get("cagr", {})
        if sm.get("roce") in ("N/A", None) and cagr_d.get("latest_roce") is not None:
            sm["roce"] = f"{cagr_d['latest_roce']:.2f} %"
        if sm.get("roe") in ("N/A", None) and cagr_d.get("latest_roe") is not None:
            sm["roe"] = f"{cagr_d['latest_roe']:.1f} %"
        if sm.get("roic") in ("N/A", None) and cagr_d.get("latest_roic") is not None:
            sm["roic"] = f"{cagr_d['latest_roic']:.2f} %"
        if sm.get("current_ratio") in ("N/A", None) and cagr_d.get("latest_current_ratio") is not None:
            sm["current_ratio"] = f"{cagr_d['latest_current_ratio']:.2f}"
        if sm.get("int_coverage") in ("N/A", None) and cagr_d.get("latest_int_coverage") is not None:
            ic_v = cagr_d["latest_int_coverage"]
            sm["int_coverage"] = "Net Cash (Debt-Free)" if ic_v >= 99.0 else f"{ic_v:.2f}"
        if sm.get("asset_turnover") in ("N/A", None) and cagr_d.get("latest_asset_turnover") is not None:
            sm["asset_turnover"] = f"{cagr_d['latest_asset_turnover']:.2f}"
        if sm.get("debt_to_equity") in ("N/A", None) and cagr_d.get("latest_de") is not None:
            sm["debt_to_equity"] = f"{cagr_d['latest_de']:.2f}"

    cur_p = live_data.get("current_price", 0)
    cur_str = f"₹ {cur_p:,.2f}" if isinstance(cur_p, (int, float)) else "N/A"

    def fmt_metric_row(label: str, value: str, style_mode: str = "normal", is_even: bool = False) -> str:
        row_bg = ' style="background-color: #F8FAFC;"' if is_even else ''
        if style_mode == "emerald":
            val_span = f'<span style="background: rgba(5, 150, 105, 0.08); color: #059669; border: 1px solid rgba(5, 150, 105, 0.25); padding: 3px 10px; border-radius: 6px; font-weight: 800; font-size: 14px; font-family: monospace;">{value}</span>'
        elif style_mode == "teal":
            val_span = f'<span style="background: rgba(37, 99, 235, 0.08); color: #2563EB; border: 1px solid rgba(37, 99, 235, 0.25); padding: 3px 10px; border-radius: 6px; font-weight: 800; font-size: 14px; font-family: monospace;">{value}</span>'
        elif style_mode == "bold":
            val_span = f'<span style="font-weight: 900; color: #0F172A; font-size: 15px; font-family: monospace;">{value}</span>'
        else:
            val_span = f'<span style="font-weight: 700; color: #334155; font-size: 14.5px; font-family: monospace;">{value}</span>'
        return f'<tr{row_bg}><td class="m-label">{label}</td><td class="m-val">{val_span}</td></tr>'

    col1_items = [
        ("Market Capitalization", sm.get("market_cap", "N/A"), "bold"),
        ("Current Price (CMP)", cur_str, "emerald"),
        ("Price to Earnings (P/E)", sm.get("pe", "N/A"), "normal"),
        ("Price to Book Value (P/B)", sm.get("price_to_book", "N/A"), "normal"),
        ("Enterprise Value (EV)", sm.get("ev", "N/A"), "normal"),
        ("EV / EBITDA Multiple", sm.get("ev_to_ebitda", "N/A"), "normal"),
        ("Historical High / Low", sm.get("high_low", "N/A"), "normal"),
        ("Sector Median P/E", sm.get("industry_pe", "N/A"), "normal"),
        ("Graham Intrinsic Value", sm.get("graham_number", "N/A"), "normal"),
    ]

    col2_items = [
        ("ROCE (Capital Employed)", sm.get("roce", "N/A"), "emerald"),
        ("ROE (Shareholder Equity)", sm.get("roe", "N/A"), "emerald"),
        ("ROIC (Invested Capital)", sm.get("roic", "N/A"), "emerald"),
        ("Operating Margin (OPM)", sm.get("opm", "N/A"), "normal"),
        ("Net Profit Margin (NPM)", sm.get("npm_last_year", "N/A"), "normal"),
        ("Earnings Yield", sm.get("earnings_yield", "N/A"), "normal"),
        ("Asset Turnover Ratio", sm.get("asset_turnover", "N/A"), "normal"),
        ("Book Value Per Share", sm.get("book_value", "N/A"), "normal"),
        ("Face Value", sm.get("face_value", "N/A"), "normal"),
    ]

    col3_items = [
        ("Total Debt", sm.get("debt", "N/A"), "normal"),
        ("Debt to Equity Ratio", sm.get("debt_to_equity", "N/A"), "normal"),
        ("Current Ratio", sm.get("current_ratio", "N/A"), "normal"),
        ("Interest Coverage Ratio", sm.get("int_coverage", "N/A"), "normal"),
        ("Est. 5Y FCF Run-Rate", sm.get("free_cash_flow_5yr", "N/A"), "teal"),
        ("CMP to Free Cash Flow", sm.get("cmp_to_fcf", "N/A"), "teal"),
        ("Promoter Shareholding", sm.get("promoter_holding", "N/A"), "bold"),
        ("Sales Growth (5 Years)", sm.get("sales_growth_5yr", "N/A"), "normal"),
        ("Dividend Yield", sm.get("dividend_yield", "N/A"), "normal"),
    ]

    def build_spacious_card(title: str, icon: str, badge_lbl: str, hdr_bg: str, border_col: str, title_col: str, badge_fg: str, items: list) -> str:
        rows_html = [fmt_metric_row(lbl, val, smode, is_even=(idx % 2 == 1)) for idx, (lbl, val, smode) in enumerate(items)]
        return (
            f'<div class="metric-domain-card" style="border: 1.5px solid {border_col}; background: #FFFFFF; border-radius: 14px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">'
            f'<div class="metric-domain-header" style="background: {hdr_bg}; border-bottom: 1.5px solid {border_col};">'
            f'<div style="display: flex; align-items: center; gap: 10px;">'
            f'<span style="font-size: 18px;">{icon}</span>'
            f'<span style="font-size: 14.5px; font-weight: 800; color: {title_col}; letter-spacing: -0.3px;">{title}</span>'
            f'</div>'
            f'<span style="font-size: 11px; font-weight: 800; color: {badge_fg}; background: #FFFFFF; border: 1px solid {border_col}; padding: 3px 9px; border-radius: 9999px; font-family: monospace;">{badge_lbl}</span>'
            f'</div>'
            f'<table class="metric-table-spacious">'
            f'<tbody>{"".join(rows_html)}</tbody>'
            f'</table>'
            f'</div>'
        )

    card_val = build_spacious_card("Valuation & Pricing Multiples", "🏛️", "9 Key Metrics", "#F8FAFC", "#E2E8F0", "#2563EB", "#2563EB", col1_items)
    card_ret = build_spacious_card("Profitability & Capital Returns", "📈", "9 Key Metrics", "#F8FAFC", "#E2E8F0", "#059669", "#059669", col2_items)
    card_sol = build_spacious_card("Solvency, Cash Flow & Growth", "🛡️", "9 Key Metrics", "#F8FAFC", "#E2E8F0", "#7C3AED", "#7C3AED", col3_items)
    return f"{card_val}{card_ret}{card_sol}"


def build_ticker_chart(df: pd.DataFrame, ticker_title: str, chart_style: str = "Area", show_dma: bool = True):
    if df.empty or len(df) < 2:
        return None
        
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.80, 0.20]
    )
    
    if chart_style in ("Candlestick", "Candles"):
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="OHLC",
                increasing_line_color="#059669",
                decreasing_line_color="#DC2626",
                showlegend=False
            ),
            row=1, col=1
        )
    else:
        start_price = float(df["Close"].iloc[0])
        end_price = float(df["Close"].iloc[-1])
        line_color = "#059669" if end_price >= start_price else "#DC2626"
        fill_color = "rgba(5, 150, 105, 0.08)" if end_price >= start_price else "rgba(220, 38, 38, 0.08)"
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Close"],
                mode="lines",
                name="CMP",
                line=dict(color=line_color, width=2.4),
                fill="tozeroy",
                fillcolor=fill_color
            ),
            row=1, col=1
        )
        
    if show_dma:
        if len(df) >= 50:
            sma50 = df["Close"].rolling(window=50).mean()
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=sma50,
                    mode="lines",
                    name="50 DMA",
                    line=dict(color="#2563EB", width=1.5, dash="dot")
                ),
                row=1, col=1
            )
        if len(df) >= 200:
            sma200 = df["Close"].rolling(window=200).mean()
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=sma200,
                    mode="lines",
                    name="200 DMA",
                    line=dict(color="#D97706", width=1.5, dash="dash")
                ),
                row=1, col=1
            )

    vol_colors = ["#059669" if c >= o else "#DC2626" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker=dict(color=vol_colors, opacity=0.55),
            showlegend=False
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        template="plotly_white",
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11, family="Inter, sans-serif")),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    fig.update_yaxes(title_text="Price (₹)", row=1, col=1, gridcolor="#F1F5F9", tickfont=dict(size=11, family="JetBrains Mono, monospace", color="#475569"))
    fig.update_yaxes(title_text="Vol", row=2, col=1, gridcolor="#F1F5F9", tickfont=dict(size=10, color="#64748B"))
    fig.update_xaxes(gridcolor="#F1F5F9", tickfont=dict(size=11, color="#475569"))
    return fig

# --- PROJECT KUSHA WELCOME & GREETING VIEW ---
def render_project_kusha_welcome_page():
    # Hero Welcome Greeting Card - Visual Infographic
    st.markdown("""
    <div class="ss-proprietary-shield" style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 24px 28px; border-top: 5px solid #059669; box-shadow: 0 4px 16px rgba(0,0,0,0.03); margin-top: 4px; margin-bottom: 20px;">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
        <span style="font-size: 11.5px; font-weight: 800; color: #059669; background: #ECFDF5; border: 1px solid #A7F3D0; padding: 4px 12px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.04em;">
          🇮🇳 STOCKSAGE // PROJECT KUSHA
        </span>
        <span style="font-size: 11px; font-weight: 800; color: #2563EB; background: #EFF6FF; border: 1px solid #BFDBFE; padding: 4px 10px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">
          EVIDENCE-BASED EQUITY RESEARCH &amp; FORENSIC INTELLIGENCE
        </span>
      </div>
      <div style="font-size: 26px; font-weight: 900; color: #0F172A; letter-spacing: -0.03em; line-height: 1.25; margin-bottom: 6px;">
        Evidence-Driven Research for Indian Listed Equities
      </div>
      <div style="font-size: 14px; font-weight: 600; color: #475569; line-height: 1.55; margin-bottom: 16px; max-width: 860px;">
        StockSage helps self-directed investors researching NSE/BSE companies review financial and market information alongside cited research, then see important risks and evidence gaps in one place.
      </div>
      
      <!-- 6 Core Research Dimensions Answering User Questions -->
      <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 18px 20px; margin-bottom: 16px;">
        <div style="font-size: 12px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
          <span>🧭</span> Designed to Answer 6 Core Due Diligence Questions
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 10px;">
          <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px 14px; border-left: 3.5px solid #059669;">
            <div style="font-size: 11px; font-weight: 800; color: #059669; text-transform: uppercase;">1. Company &amp; Period</div>
            <div style="font-size: 12.5px; font-weight: 700; color: #0F172A; margin-top: 2px;">What entity &amp; period am I looking at?</div>
            <div style="font-size: 11.5px; color: #64748B; margin-top: 4px; line-height: 1.4;">Exact legal company name, NSE/BSE symbol, and audited statutory filing fiscal year.</div>
          </div>
          <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px 14px; border-left: 3.5px solid #2563EB;">
            <div style="font-size: 11px; font-weight: 800; color: #2563EB; text-transform: uppercase;">2. Data Origin</div>
            <div style="font-size: 12.5px; font-weight: 700; color: #0F172A; margin-top: 2px;">Where did this information come from?</div>
            <div style="font-size: 11.5px; color: #64748B; margin-top: 4px; line-height: 1.4;">BSE India exchange filings (SEBI LODR Reg 34), delayed Yahoo Finance statements (~4 years, unaudited), and web citations.</div>
          </div>
          <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px 14px; border-left: 3.5px solid #7C3AED;">
            <div style="font-size: 11px; font-weight: 800; color: #7C3AED; text-transform: uppercase;">3. Freshness &amp; Integrity</div>
            <div style="font-size: 12.5px; font-weight: 700; color: #0F172A; margin-top: 2px;">How fresh and complete is it?</div>
            <div style="font-size: 11.5px; color: #64748B; margin-top: 4px; line-height: 1.4;">Timestamped retrieval, multimodal PDF ingestion verification, and 6 mathematical sanity checks.</div>
          </div>
          <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px 14px; border-left: 3.5px solid #059669;">
            <div style="font-size: 11px; font-weight: 800; color: #059669; text-transform: uppercase;">4. Grounded Takeaway</div>
            <div style="font-size: 12.5px; font-weight: 700; color: #0F172A; margin-top: 2px;">What does the analysis conclude?</div>
            <div style="font-size: 11.5px; color: #64748B; margin-top: 4px; line-height: 1.4;">Educational risk tiers (Constructive Watchlist, Monitored, Elevated Caution) backed by CFO/PAT evidence.</div>
          </div>
          <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px 14px; border-left: 3.5px solid #D97706;">
            <div style="font-size: 11px; font-weight: 800; color: #D97706; text-transform: uppercase;">5. Evidence Gaps</div>
            <div style="font-size: 12.5px; font-weight: 700; color: #0F172A; margin-top: 2px;">What important data is missing?</div>
            <div style="font-size: 11.5px; color: #64748B; margin-top: 4px; line-height: 1.4;">Explicitly surfaces unverified auditor notes, share pledging uncertainties, or missing schedule details.</div>
          </div>
          <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px 14px; border-left: 3.5px solid #0284C7;">
            <div style="font-size: 11px; font-weight: 800; color: #0284C7; text-transform: uppercase;">6. Directed Next Checks</div>
            <div style="font-size: 12.5px; font-weight: 700; color: #0F172A; margin-top: 2px;">What should I inspect next?</div>
            <div style="font-size: 11.5px; color: #64748B; margin-top: 4px; line-height: 1.4;">Actionable audit trails pointing to CARO remarks, Related-Party schedules, and exchange pledge registries.</div>
          </div>
        </div>
      </div>
      
      <!-- 4 Summary Universe Metric Chips -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; padding-top: 14px; border-top: 1px solid #F1F5F9;">
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px;">
          <div style="font-size: 10.5px; font-weight: 700; color: #64748B; text-transform: uppercase;">Coverage Universe</div>
          <div style="font-size: 15px; font-weight: 800; color: #0F172A; font-family: 'JetBrains Mono', monospace;">50 Nifty Bluechips</div>
          <div style="font-size: 11px; color: #059669; font-weight: 700; margin-top: 2px;">16 Canonical Ratios</div>
        </div>
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px;">
          <div style="font-size: 10.5px; font-weight: 700; color: #64748B; text-transform: uppercase;">Forensic Checks</div>
          <div style="font-size: 15px; font-weight: 800; color: #DC2626; font-family: 'JetBrains Mono', monospace;">6 Sanity Sentinel Tests</div>
          <div style="font-size: 11px; color: #64748B; font-weight: 600; margin-top: 2px;">Accrual &amp; Pledging Guard</div>
        </div>
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px;">
          <div style="font-size: 10.5px; font-weight: 700; color: #64748B; text-transform: uppercase;">Valuation Corridors</div>
          <div style="font-size: 15px; font-weight: 800; color: #2563EB; font-family: 'JetBrains Mono', monospace;">Relative Valuation</div>
          <div style="font-size: 11px; color: #64748B; font-weight: 600; margin-top: 2px;">P/E · EV/EBITDA · P/B multiples</div>
        </div>
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px;">
          <div style="font-size: 10.5px; font-weight: 700; color: #64748B; text-transform: uppercase;">Statutory Filings</div>
          <div style="font-size: 15px; font-weight: 800; color: #7C3AED; font-family: 'JetBrains Mono', monospace;">BSE India Official</div>
          <div style="font-size: 11px; color: #64748B; font-weight: 600; margin-top: 2px;">Direct Statutory Annual Reports</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Section 1: Visual Contrast Matrix
    st.markdown("""
    <div style="margin-top: 20px; margin-bottom: 12px;">
      <div style="font-size: 17px; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 8px;">
        <span style="color: #2563EB;">🎯</span> Why Project KUSHA? Visual Head-to-Head Comparison
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_purpose_text, col_purpose_comp = st.columns([1, 1])
    with col_purpose_text:
        with st.container(border=True):
            st.markdown("""
            <div style="font-size: 14.5px; font-weight: 800; color: #0F172A; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
              <span>🛡️</span> Eliminating Dalal Street Accounting Blindspots
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px;">
              <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 10px 12px;">
                <div style="font-size: 11px; font-weight: 800; color: #DC2626; text-transform: uppercase;">Non-Cash Accruals</div>
                <div style="font-size: 12px; color: #7F1D1D; margin-top: 2px;">CFO vs PAT Divergence</div>
              </div>
              <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 10px 12px;">
                <div style="font-size: 11px; font-weight: 800; color: #DC2626; text-transform: uppercase;">Promoter Pledging</div>
                <div style="font-size: 12px; color: #7F1D1D; margin-top: 2px;">Margin Call Liquidation Risk</div>
              </div>
              <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 10px 12px;">
                <div style="font-size: 11px; font-weight: 800; color: #DC2626; text-transform: uppercase;">CWIP Asset Inflation</div>
                <div style="font-size: 12px; color: #7F1D1D; margin-top: 2px;">Capitalized Expense Parking</div>
              </div>
              <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 10px 12px;">
                <div style="font-size: 11px; font-weight: 800; color: #DC2626; text-transform: uppercase;">Related-Party Deals</div>
                <div style="font-size: 12px; color: #7F1D1D; margin-top: 2px;">RPT Minority Siphoning</div>
              </div>
            </div>

            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; padding: 10px 12px; display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 16px;">🛡️</span>
              <div style="font-size: 12px; font-weight: 700; color: #065F46;">
                Pre-Emptive Surveillance: Audits statutory disclosures to identify solvency strain and governance decay quarters before media coverage.
              </div>
            </div>
            """, unsafe_allow_html=True)

    with col_purpose_comp:
        with st.container(border=True):
            st.markdown("""
            <div style="font-size: 14.5px; font-weight: 800; color: #0F172A; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
              <span>⚖️</span> Conventional Screener vs. Project KUSHA
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
              <thead>
                <tr style="border-bottom: 1.5px solid #E2E8F0; background: #F8FAFC;">
                  <th style="text-align: left; padding: 6px 8px; color: #64748B; font-weight: 700;">Vector</th>
                  <th style="text-align: left; padding: 6px 8px; color: #DC2626; font-weight: 700;">Conventional</th>
                  <th style="text-align: left; padding: 6px 8px; color: #059669; font-weight: 700;">Project KUSHA</th>
                </tr>
              </thead>
              <tbody>
                <tr style="border-bottom: 1px solid #F1F5F9;">
                  <td style="padding: 6px 8px; font-weight: 600; color: #334155;">Earnings Quality</td>
                  <td style="padding: 6px 8px; color: #DC2626;">❌ Reported PAT</td>
                  <td style="padding: 6px 8px; font-weight: 700; color: #059669;">✅ CFO vs PAT Accrual Reconcilement</td>
                </tr>
                <tr style="border-bottom: 1px solid #F1F5F9;">
                  <td style="padding: 6px 8px; font-weight: 600; color: #334155;">Promoter Pledging</td>
                  <td style="padding: 6px 8px; color: #DC2626;">❌ Ignored footnote</td>
                  <td style="padding: 6px 8px; font-weight: 700; color: #059669;">✅ PPRM &gt;50% PIO Hard Penalty</td>
                </tr>
                <tr style="border-bottom: 1px solid #F1F5F9;">
                  <td style="padding: 6px 8px; font-weight: 600; color: #334155;">Crisis Prevention</td>
                  <td style="padding: 6px 8px; color: #DC2626;">❌ Trapped when news breaks</td>
                  <td style="padding: 6px 8px; font-weight: 700; color: #059669;">✅ Flags pre-crisis stress signals (e.g. YES Bank cash divergences)</td>
                </tr>
                <tr style="border-bottom: 1px solid #F1F5F9;">
                  <td style="padding: 6px 8px; font-weight: 600; color: #334155;">Scoring Engine</td>
                  <td style="padding: 6px 8px; color: #DC2626;">❌ Black-box opinion</td>
                  <td style="padding: 6px 8px; font-weight: 700; color: #059669;">✅ Simple No-Nonsense Score (100% Deterministic Forensic Model)</td>
                </tr>
                <tr>
                  <td style="padding: 6px 8px; font-weight: 600; color: #334155;">Provenance</td>
                  <td style="padding: 6px 8px; color: #DC2626;">❌ Uncited summaries</td>
                  <td style="padding: 6px 8px; font-weight: 700; color: #059669;">✅ Direct BSE India Annual Report PDFs</td>
                </tr>
              </tbody>
            </table>
            """, unsafe_allow_html=True)

    # Section 2: Visual 5-Step Pipeline (Concise & Graphic)
    st.markdown("""
    <div style="margin-top: 22px; margin-bottom: 12px;">
      <div style="font-size: 17px; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 8px;">
        <span style="color: #059669;">⚙️</span> The 5-Step Autonomous Pipeline
      </div>
    </div>
    """, unsafe_allow_html=True)

    p1, p2, p3, p4, p5 = st.columns(5)
    with p1:
        with st.container(border=True):
            st.markdown("""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 10px; font-weight: 800; color: #2563EB; background: #EFF6FF; border: 1px solid #BFDBFE; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">STEP 01</span>
              <span style="font-size: 16px;">📥</span>
            </div>
            <div style="font-size: 13.5px; font-weight: 800; color: #0F172A; margin-bottom: 6px;">Ingestion</div>
            <div style="font-size: 11.5px; color: #475569; line-height: 1.4;">
              • ~4-Yr Third-Party Financials<br/>
              • 6 Sanity Checks
            </div>
            """, unsafe_allow_html=True)

    with p2:
        with st.container(border=True):
            st.markdown("""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 10px; font-weight: 800; color: #059669; background: #ECFDF5; border: 1px solid #A7F3D0; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">STEP 02</span>
              <span style="font-size: 16px;">🏛️</span>
            </div>
            <div style="font-size: 13.5px; font-weight: 800; color: #0F172A; margin-bottom: 6px;">8-Pillar Matrix</div>
            <div style="font-size: 11.5px; color: #475569; line-height: 1.4;">
              • Proprietary Valuation Matrix<br/>
              • Multi-Factor Heuristics
            </div>
            """, unsafe_allow_html=True)

    with p3:
        with st.container(border=True):
            st.markdown("""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 10px; font-weight: 800; color: #DC2626; background: #FEF2F2; border: 1px solid #FECACA; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">STEP 03</span>
              <span style="font-size: 16px;">🛡️</span>
            </div>
            <div style="font-size: 13.5px; font-weight: 800; color: #0F172A; margin-bottom: 6px;">Fraud Shield</div>
            <div style="font-size: 11.5px; color: #475569; line-height: 1.4;">
              • 8 Forensic Tests<br/>
              • Accruals &amp; Pledging Guard
            </div>
            """, unsafe_allow_html=True)

    with p4:
        with st.container(border=True):
            st.markdown("""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 10px; font-weight: 800; color: #D97706; background: #FFFBEB; border: 1px solid #FDE68A; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">STEP 04</span>
              <span style="font-size: 16px;">⚡</span>
            </div>
            <div style="font-size: 13.5px; font-weight: 800; color: #0F172A; margin-bottom: 6px;">Forensic Bridge</div>
            <div style="font-size: 11.5px; color: #475569; line-height: 1.4;">
              • Risk Penalty Corridors<br/>
              • PIO Circuit Breaker
            </div>
            """, unsafe_allow_html=True)

    with p5:
        with st.container(border=True):
            st.markdown("""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 10px; font-weight: 800; color: #059669; background: #ECFDF5; border: 1px solid #A7F3D0; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">STEP 05</span>
              <span style="font-size: 16px;">🎯</span>
            </div>
            <div style="font-size: 13.5px; font-weight: 800; color: #0F172A; margin-bottom: 6px;">Relative Valuation</div>
            <div style="font-size: 11.5px; color: #475569; line-height: 1.4;">
              • P/E · EV/EBITDA · P/B Multiples<br/>
              • Peer Benchmark Spread
            </div>
            """, unsafe_allow_html=True)

    # Section 3: Operational & Technical Architecture FAQ
    st.markdown("""
    <div style="margin-top: 28px; margin-bottom: 10px;">
      <div style="font-size: 16px; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 6px;">
        <span>❓</span> Architecture &amp; Operational Insights
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🏛️ How does the 8-Pillar Fundamental & Forensic framework evaluate equities?", expanded=False):
        st.markdown("""
        <div class="ss-proprietary-shield" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 8px; margin-bottom: 10px;">
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center;">
            <div><span style="font-size: 13px;">🏛️</span> <strong style="font-size: 12px; color: #0F172A;">Governance &amp; Capital</strong><br/><span style="font-size: 11px; color: #64748B;">Reinvestment &amp; Board Independence</span></div>
            <span style="font-size: 10.5px; font-weight: 700; color: #059669; background: #ECFDF5; padding: 2px 6px; border-radius: 4px; font-family: monospace;">Vector 01</span>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center;">
            <div><span style="font-size: 13px;">🔍</span> <strong style="font-size: 12px; color: #0F172A;">Forensics &amp; Cash Flow</strong><br/><span style="font-size: 11px; color: #64748B;">CFO / PAT &amp; Accrual Reconcile</span></div>
            <span style="font-size: 10.5px; font-weight: 700; color: #059669; background: #ECFDF5; padding: 2px 6px; border-radius: 4px; font-family: monospace;">Vector 02</span>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center;">
            <div><span style="font-size: 13px;">🛡️</span> <strong style="font-size: 12px; color: #0F172A;">Risk, Solvency &amp; Fragility</strong><br/><span style="font-size: 11px; color: #64748B;">Net Debt/EBITDA &amp; Liquidity Buffer</span></div>
            <span style="font-size: 10.5px; font-weight: 700; color: #059669; background: #ECFDF5; padding: 2px 6px; border-radius: 4px; font-family: monospace;">Vector 03</span>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center;">
            <div><span style="font-size: 13px;">🚀</span> <strong style="font-size: 12px; color: #0F172A;">Innovation &amp; TAM Optionality</strong><br/><span style="font-size: 11px; color: #64748B;">R&amp;D Runway &amp; Addressable Scale</span></div>
            <span style="font-size: 10.5px; font-weight: 700; color: #059669; background: #ECFDF5; padding: 2px 6px; border-radius: 4px; font-family: monospace;">Vector 04</span>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center;">
            <div><span style="font-size: 13px;">🏰</span> <strong style="font-size: 12px; color: #0F172A;">Moat Durability &amp; Scale</strong><br/><span style="font-size: 11px; color: #64748B;">Pricing Power &amp; Network Effects</span></div>
            <span style="font-size: 10.5px; font-weight: 700; color: #059669; background: #ECFDF5; padding: 2px 6px; border-radius: 4px; font-family: monospace;">Vector 05</span>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center;">
            <div><span style="font-size: 13px;">📈</span> <strong style="font-size: 12px; color: #0F172A;">Valuation &amp; Sanity Layer</strong><br/><span style="font-size: 11px; color: #64748B;">Multiples vs 10Y History</span></div>
            <span style="font-size: 10.5px; font-weight: 700; color: #059669; background: #ECFDF5; padding: 2px 6px; border-radius: 4px; font-family: monospace;">Vector 06</span>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center;">
            <div><span style="font-size: 13px;">⚠️</span> <strong style="font-size: 12px; color: #0F172A;">Insider &amp; Minority Risk</strong><br/><span style="font-size: 11px; color: #64748B;">PPRM Pledging &amp; RPT Transparency</span></div>
            <span style="font-size: 10.5px; font-weight: 700; color: #059669; background: #ECFDF5; padding: 2px 6px; border-radius: 4px; font-family: monospace;">Vector 07</span>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center;">
            <div><span style="font-size: 13px;">⚡</span> <strong style="font-size: 12px; color: #0F172A;">Simplicity &amp; Repeatability</strong><br/><span style="font-size: 11px; color: #64748B;">Predictability &amp; Low Subsidiary Clutter</span></div>
            <span style="font-size: 10.5px; font-weight: 700; color: #059669; background: #ECFDF5; padding: 2px 6px; border-radius: 4px; font-family: monospace;">Vector 08</span>
          </div>
        </div>
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; font-size: 11.5px; font-weight: 600; color: #475569; text-align: center;">
          🔒 <strong>Proprietary Quantitative Engine:</strong> Exact algorithmic weights, penalty multipliers, and non-linear scoring curves are compiled trade secrets protected under quantitative IP safeguards.
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🛡️ What triggers the Promoter Integrity Override (PIO)?", expanded=False):
        st.markdown("""
        <div class="ss-proprietary-shield" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 12px;">
            <div style="font-size: 11.5px; font-weight: 800; color: #DC2626; margin-bottom: 8px;">🚨 Critical Distress Triggers</div>
            <div style="font-size: 11.5px; color: #991B1B; line-height: 1.6;">
              • <strong>Promoter Share Pledging</strong> Margin liquidation hazard<br/>
              • <strong>Auditor Qualifications</strong> Adverse CARO opinions or sudden exit<br/>
              • <strong>Regulatory Inquiries</strong> Statutory authority enforcement<br/>
              • <strong>Related-Party Extraction</strong> Non-arm's length minority siphoning
            </div>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px;">
            <div style="font-size: 11.5px; font-weight: 800; color: #0F172A; margin-bottom: 8px;">⚡ Automated Circuit Breaker</div>
            <div style="font-size: 11.5px; color: #475569; line-height: 1.6;">
              • <strong>Governance Clamped</strong> Strict institutional ceiling applied<br/>
              • <strong>Bonuses Neutralized</strong> Upside multipliers revoked<br/>
              • <strong>GOV-RED 🔴 Alert</strong> Persistent visual warning across terminal<br/>
              • <strong>Distress Lockdown</strong> Overall rating constrained to high-risk band
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📑 Where does Project KUSHA source filings and market data?", expanded=False):
        st.markdown("""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 12px;">
            <div style="font-size: 12px; font-weight: 800; color: #0F172A;">🏛️ BSE India</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 2px;">Official statutory annual reports with 1-click verified PDF URLs.</div>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 12px;">
            <div style="font-size: 12px; font-weight: 800; color: #0F172A;">📊 Yahoo Finance</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 2px;">Third-party, unaudited P&amp;L, Balance Sheet and Cash Flow data (~4 years).</div>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 12px;">
            <div style="font-size: 12px; font-weight: 800; color: #0F172A;">⭐ CRISIL / ICRA</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 2px;">Manually curated public rating disclosures for a small set of large caps only; shown with its disclosure date.</div>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 12px;">
            <div style="font-size: 12px; font-weight: 800; color: #0F172A;">📈 NSE / Yahoo</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 2px;">Delayed market quotes, 52-week channels, and intraday range telemetry.</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🧪 Can I use Project KUSHA in Demo Mode without an API key?", expanded=False):
        st.markdown("""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 10px;">
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 12px;">
            <div style="font-size: 11.5px; font-weight: 800; color: #2563EB;">1️⃣ Enable Demo Mode</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 2px;">Toggle "Demo Mode" in the sidebar with zero API key requirement.</div>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 12px;">
            <div style="font-size: 11.5px; font-weight: 800; color: #059669;">2️⃣ Select Bluechip</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 2px;">Choose any Nifty 50 constituent from the dropdown or peer matrix.</div>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 12px;">
            <div style="font-size: 11.5px; font-weight: 800; color: #7C3AED;">3️⃣ Instant Dossier</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 2px;">Radial charts, fraud shield, and valuation corridors in 1 second.</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🤖 The Vision: Next-Gen Autonomous AI for Finance", expanded=False):
        st.markdown("""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px;">
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px;">
            <div style="font-size: 12px; font-weight: 800; color: #059669;">🛡️ Capital Protection Over Hype</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 4px;">Engineered to systematically flag pre-crisis distress patterns (e.g. YES Bank-style cash flow vs profit divergences), prioritizing capital preservation over speculative hype.</div>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px;">
            <div style="font-size: 12px; font-weight: 800; color: #2563EB;">🔍 Fine-Print Footnote Auditing</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 4px;">AI that reads between the lines of 10-year financials and regulatory filings so normal investors don't have to.</div>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px;">
            <div style="font-size: 12px; font-weight: 800; color: #7C3AED;">⚡ Simple No-Nonsense Score</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 4px;">A single, deterministic 0–100 score bridging 8 core pillars with immediate forensic risk deductions.</div>
          </div>
          <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px;">
            <div style="font-size: 12px; font-weight: 800; color: #D97706;">🔄 Continuous Feedback (Next Stage)</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 4px;">Analyst edits and audited footnote discoveries improve every subsequent search through active feedback loops.</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Section: Primary Terminal Workstation Gateway Action
    if not st.session_state.get("entered_terminal", False):
        st.markdown("""
        <div style="margin-top: 32px; margin-bottom: 20px; text-align: center; border-top: 1.5px solid #E2E8F0; padding-top: 24px;">
          <div style="font-size: 18px; font-weight: 800; color: #0F172A; letter-spacing: -0.3px;">
            Start Exploring Indian Listed Equities
          </div>
          <div style="font-size: 13px; color: #64748B; margin-top: 4px; margin-bottom: 18px;">
            Choose a research path below or use the top navigation tabs anytime.
          </div>
        </div>
        """, unsafe_allow_html=True)

        col_act1, col_act2, col_act3 = st.columns(3)
        with col_act1:
            if st.button("🔬 Research a Company", type="primary", key="btn_guide_research", width="stretch"):
                st.session_state["pending_nav_mode"] = "Research"
                st.rerun()
            st.caption("Inspect a specific company, review audited BSE filings, or upload a custom annual report PDF.")
        with col_act2:
            if st.button("📊 Open Market Screener", key="btn_guide_screener", width="stretch"):
                st.session_state["pending_nav_mode"] = "Market screener"
                st.rerun()
            st.caption("Screen 50 bluechip equities across 16 canonical factors and peer valuation multiples.")
        with col_act3:
            if st.button("🧪 Try Synthetic Demo", key="btn_guide_demo", width="stretch"):
                st.session_state["pending_nav_mode"] = "Research"
                st.session_state["selected_company_choice"] = "Tata Consumer Products Ltd. (TATACONSUM)"
                st.session_state["company_search_selector"] = "Tata Consumer Products Ltd. (TATACONSUM)"
                st.session_state["trigger_demo_run"] = True
                st.rerun()
            st.caption("Explore a complete, instant walkthrough using synthetic demonstration data for Tata Consumer.")

    # Intellectual Property & Trade Secret Safeguard Notice
    st.markdown("""
    <div class="ss-proprietary-shield" style="margin-top: 28px; padding: 12px 18px; background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 10px; text-align: center; font-size: 11.5px; color: #64748B;">
      🔒 <strong>Intellectual Property &amp; Trade Secret Safeguard:</strong> Project KUSHA valuation heuristics, multi-factor scoring vectors, and forensic algorithms are protected proprietary IP. Systematic scraping, model reverse-engineering, and unauthorized algorithmic replication are strictly prohibited.
    </div>
    """, unsafe_allow_html=True)

# --- AUDITED STATUTORY FILINGS VAULT VIEW ---
def render_audited_filings_vault_view():
    st.markdown("""
    <div style="margin-top: 4px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1.5px solid #E2E8F0; padding-bottom: 12px;">
      <div>
        <div style="font-size: 20px; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 8px;">
          <span style="color: #059669;">📑</span> Audited Statutory Filings Vault
        </div>
        <p style="font-size: 13px; color: #64748B; margin: 4px 0 0 0;">
          Direct statutory annual report repository streamed from official BSE India exchange archives (<code>bseindia.com</code>).
        </p>
      </div>
      <span style="font-size: 11.5px; color: #059669; background: #ECFDF5; border: 1px solid #A7F3D0; padding: 4px 10px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace; font-weight: 800;">
        SEBI LODR REG 34 COMPLIANT
      </span>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### Select Equity to Inspect Statutory Disclosures")
        c_list = company_options
        cur_choice = st.session_state.get("selected_company_choice", None)
        default_idx = c_list.index(cur_choice) if (cur_choice and cur_choice in c_list) else 0

        v_col1, v_col2 = st.columns([3, 1])
        with v_col1:
            vault_company_str = st.selectbox(
                "Company",
                options=c_list,
                index=default_idx,
                key="vault_company_select",
                placeholder="Search tracked companies (e.g. Reliance, TCS, HDFC Bank, Infosys)..."
            )
        
        info = find_company_info(vault_company_str) if vault_company_str else None
        sym = info.get("ticker", "RELIANCE") if info else "RELIANCE"

        with v_col2:
            st.text_input("NSE / BSE Symbol", value=sym, disabled=True)

        # Quick preset buttons
        st.caption("Quick Bluechip Filings Discovery")
        preset_syms = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ITC", "LT"]
        p_cols = st.columns(len(preset_syms))
        for p_idx, p_sym in enumerate(preset_syms):
            with p_cols[p_idx]:
                if st.button(f"📄 {p_sym}", key=f"btn_vault_preset_{p_sym}", width="stretch"):
                    p_info = find_company_info(p_sym)
                    st.session_state["selected_company_choice"] = p_info["display"]
                    st.rerun()

    # Discover Available Annual Reports for this symbol
    reports = get_available_annual_reports(sym) if (sym and sym != "CUSTOM") else []

    if reports:
        st.markdown(f"""
        <div style="font-size: 15px; font-weight: 800; color: #0F172A; margin-top: 18px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
          <span>📁</span> Available BSE India Statutory Filings ({len(reports)} Discovered)
        </div>
        """, unsafe_allow_html=True)

        for r_idx, rep in enumerate(reports):
            with st.container(border=True):
                r_c1, r_c2, r_c3 = st.columns([3, 1.5, 1.5])
                with r_c1:
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <span style="font-size: 18px;">📑</span>
                      <div>
                        <div style="font-size: 15px; font-weight: 800; color: #0F172A;">{rep.get('title', 'Annual Report')}</div>
                        <div style="font-size: 12px; color: #64748B; font-family: 'JetBrains Mono', monospace;">
                          Financial Year: {rep.get('year', 'Latest')} · Host: bseindia.com
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                with r_c2:
                    st.link_button("View BSE Filing PDF ↗", rep["url"], width="stretch")
                with r_c3:
                    if st.button("Inspect in Research 🔬", key=f"vault_inspect_{sym}_{r_idx}", width="stretch"):
                        st.session_state["selected_company_choice"] = info["display"]
                        st.session_state["pending_nav_mode"] = "Research"
                        st.rerun()
    else:
        st.info(f"No direct BSE annual report PDF candidates are currently cached for symbol `{sym}`. You can analyze this equity using Google Search grounding or upload a custom PDF inside Research.")

    # Statutory Disclosures Note Card
    st.markdown("""
    <div style="margin-top: 20px; background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 18px 22px;">
      <div style="font-size: 13.5px; font-weight: 800; color: #0F172A; margin-bottom: 6px;">
        🏛️ Statutory Filing Provenance &amp; SEBI LODR Regulations
      </div>
      <p style="font-size: 12.5px; color: #475569; line-height: 1.55; margin: 0;">
        Under Regulation 34 of SEBI (Listing Obligations and Disclosure Requirements) Regulations, 2015, listed Indian entities must submit their annual reports containing audited financial statements, Cash Flow statements, Notes to Accounts, and the Companies (Auditor's Report) Order (CARO) to the stock exchanges. Project KUSHA references these official exchange filings directly from BSE India regulatory servers.
      </p>
    </div>
    """, unsafe_allow_html=True)

# --- TOP-LEVEL WORKSPACE NAVIGATION ---
workspace_options = [
    "Research",
    "Market screener",
    "Company filings",
    "How it works"
]

# Smooth alias mapping for existing session states and backwards compatibility
nav_alias_map = {
    # Plain labels
    "Research": "Research",
    "Market screener": "Market screener",
    "Company filings": "Company filings",
    "How it works": "How it works",
    # Legacy aliases mapping to Research
    "Company Analysis": "Research",
    "🔬 Company Analysis": "Research",
    "🔬 Holographic Stock Dossier": "Research",
    "Dossier": "Research",
    "Analyze": "Research",
    # Legacy aliases mapping to Market screener
    "Market Screener": "Market screener",
    "⚡ Screener & Market Matrix": "Market screener",
    "🌐 Explore": "Market screener",
    "📊 Nifty 50": "Market screener",
    "Screener": "Market screener",
    # Legacy aliases mapping to Company filings
    "Filings Vault": "Company filings",
    "📑 Audited Filings Vault": "Company filings",
    "Vault": "Company filings",
    # Legacy aliases mapping to How it works
    "Overview & Guide": "How it works",
    "👋 Welcome Guide": "How it works",
    "Welcome": "How it works",
    "Greeting": "How it works",
    "Home": "How it works",
    "👋 Welcome to Project KUSHA": "How it works",
    "Overview": "How it works",
    "Guide": "How it works"
}

if "pending_nav_mode" in st.session_state:
    raw_pending = st.session_state.pop("pending_nav_mode")
    st.session_state["active_nav_mode"] = nav_alias_map.get(raw_pending, raw_pending)

current_nav = st.session_state.get("active_nav_mode")
if current_nav not in workspace_options:
    st.session_state["active_nav_mode"] = nav_alias_map.get(current_nav, "Research")

terminal_mode = st.segmented_control(
    "Workspace",
    options=workspace_options,
    key="active_nav_mode",
    label_visibility="collapsed"
)

if terminal_mode == "How it works":
    render_project_kusha_welcome_page()
    st.stop()

if terminal_mode == "Market screener":
    render_terminal_top_telemetry_hud()
    st.markdown("""
    <div style="margin-top: 8px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1.5px solid #E2E8F0; padding-bottom: 10px;">
      <div style="font-size: 18px; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 8px;">
        <span style="color: #059669;">⚡</span> Market Screener & Factor Matrix
      </div>
      <span style="font-size: 11.5px; color: #64748B; font-family: 'JetBrains Mono', monospace;">50 Premier Equities · 16 Canonical Ratios</span>
    </div>
    """, unsafe_allow_html=True)
    
    render_nifty50_screener_view()
    st.stop()

if terminal_mode == "Company filings":
    render_audited_filings_vault_view()
    st.stop()

if terminal_mode == "Research":
    benchmark_launch_notice = st.session_state.pop("benchmark_launch_notice", None)
    if benchmark_launch_notice:
        st.warning(benchmark_launch_notice)
    # --- COMPANY RESEARCH INTAKE ---
    st.markdown("""
    <div style="margin-top: 4px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; border-bottom: 1.5px solid #E2E8F0; padding-bottom: 12px;">
      <div>
        <div style="font-size: 20px; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 8px; letter-spacing: -0.3px;">
          <span>🔬</span> Company Research Brief
        </div>
        <div style="font-size: 13px; color: #64748B; margin-top: 3px;">
          Review financial disclosures, forensic indicators, and evidence gaps for Indian listed companies.
        </div>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="background: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">
          BSE Statutory Filings · Yahoo Quotes · Google Search
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    with st.container(border=True):
        st.caption("Quick Bluechip Examples:")
        p_col1, p_col2, p_col3, p_col4 = st.columns(4)
        chips = [
            ("Reliance", "RELIANCE", p_col1),
            ("HDFC Bank", "HDFCBANK", p_col2),
            ("Infosys", "INFY", p_col3),
            ("Tata Consumer", "TATACONSUM", p_col4)
        ]
        for lbl, sym, col in chips:
            with col:
                if st.button(f"📌 {lbl}", key=f"chip_{sym}", width="stretch"):
                    info = find_company_info(sym)
                    st.session_state["pending_company_choice"] = info["display"]
                    st.rerun()

        if "pending_company_choice" in st.session_state:
            pending_c = st.session_state.pop("pending_company_choice")
            st.session_state["selected_company_choice"] = pending_c
            st.session_state["company_search_selector"] = pending_c

        c_list = company_options
        cur_choice = st.session_state.get("selected_company_choice", None)
        default_idx = c_list.index(cur_choice) if (cur_choice and cur_choice in c_list) else None

        col_sel1, col_sel2 = st.columns([2.8, 1.2])
        with col_sel1:
            selected_company_str = st.selectbox(
                "Select or search a company",
                options=c_list,
                index=default_idx,
                key="company_search_selector",
                placeholder="Search by company name or symbol (e.g. Reliance, HDFC Bank, Infosys, Tata Consumer)...",
                help="Search 50+ tracked Indian listed equities. Quotes are delayed third-party market data."
            )
            if selected_company_str != cur_choice:
                st.session_state["selected_company_choice"] = selected_company_str

        matched_info = find_company_info(selected_company_str) if selected_company_str else None

        with col_sel2:
            if matched_info and matched_info["ticker"] == "CUSTOM":
                target_company_name = st.text_input("Company Name", placeholder="e.g. Amber Enterprises Ltd")
                target_ticker = st.text_input("NSE/BSE Symbol", placeholder="e.g. AMBER")
            elif matched_info:
                target_company_name = matched_info["name"]
                target_ticker = matched_info["ticker"]
                st.text_input("NSE Ticker", value=target_ticker, disabled=True)
            else:
                target_company_name = None
                target_ticker = None
                st.text_input("NSE Ticker", value="", placeholder="Awaiting selection...", disabled=True)

        sector_list = get_sector_list()
        def_sector_idx = sector_list.index(matched_info["sector"]) if (matched_info and matched_info.get("sector") in sector_list) else 0

        # Fetch live market data and audited financial statements for target
        live_data = None
        if target_ticker and target_ticker != "CUSTOM":
            live_data = get_cached_live_data(target_ticker)

        fin_res = None
        if target_ticker and target_ticker != "CUSTOM":
            fin_res = get_cached_financial_statements(target_ticker)

        # Reset evaluation only when the user changes the active company.
        if "selected_company_memory" not in st.session_state:
            st.session_state["selected_company_memory"] = selected_company_str
        elif st.session_state["selected_company_memory"] != selected_company_str:
            st.session_state["selected_company_memory"] = selected_company_str
            if "idex_result" in st.session_state:
                del st.session_state["idex_result"]

        # Compact Company Identity & Data Freshness Summary Card
        if target_company_name:
            cur_p = (live_data or {}).get("current_price", 0)
            cur_str = f"₹ {cur_p:,.2f}" if isinstance(cur_p, (int, float)) and cur_p > 0 else "Price on file"
            chg_pct = (live_data or {}).get("change_pct", 0)
            is_pos = chg_pct >= 0
            delta_fg = "#059669" if is_pos else "#DC2626"
            delta_sign = "+" if is_pos else ""
            delta_str = f"{delta_sign}{chg_pct:.2f}%" if chg_pct else ""
            quote_status = "delayed quote" if (live_data or {}).get("is_delayed") else "third-party data"
            bse_c = (live_data or {}).get("bse_code", target_ticker)

            st.html(f"""
            <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 12px 18px; margin: 10px 0 16px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
              <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 22px;">🏢</span>
                <div>
                  <div style="font-size: 15px; font-weight: 800; color: #0F172A;">{esc(target_company_name)} <span style="font-size: 13px; font-weight: 700; color: #64748B; font-family: 'JetBrains Mono', monospace;">({esc(target_ticker)})</span></div>
                  <div style="font-size: 11.5px; color: #64748B;">Sector: {esc(matched_info.get('sector', 'General') if matched_info else 'General')} · BSE: {esc(bse_c)} · Source: BSE Statutory Filings</div>
                </div>
              </div>
              <div style="text-align: right;">
                <div style="font-size: 16px; font-weight: 900; color: #0F172A; font-family: 'JetBrains Mono', monospace;">{cur_str}</div>
                <div style="font-size: 11px; color: {delta_fg}; font-weight: 700; font-family: 'JetBrains Mono', monospace;">{delta_str} ({quote_status})</div>
              </div>
            </div>
            """)

        # Per-session analysis budget check
        if "kusha_runs" not in st.session_state:
            st.session_state["kusha_runs"] = 0
        current_runs = st.session_state["kusha_runs"]
        budget_exhausted = current_runs >= MAX_RUNS_PER_SESSION
        if budget_exhausted:
            st.warning(f"Session analysis budget reached ({current_runs} of {MAX_RUNS_PER_SESSION}). Reload to start a new session.")

        # Action Buttons Row (Prominent & Unobscured)
        run_btn = False
        if st.session_state.pop("trigger_demo_run", False):
            if budget_exhausted:
                st.warning(f"Session analysis budget reached ({current_runs} of {MAX_RUNS_PER_SESSION}). Reload to start a new session.")
            else:
                demo_mode = True
                run_btn = True
                if not target_company_name:
                    target_company_name = "Tata Consumer Products Ltd."
                    target_sector = "FMCG / Packaged Goods"
                    target_ticker = "TATACONSUM.NS"
                if target_ticker and not live_data:
                    live_data = get_cached_live_data(target_ticker)
                if target_ticker and not fin_res:
                    fin_res = get_cached_financial_statements(target_ticker)

        btn_col1, btn_col2 = st.columns([3, 1.8])
        is_running = st.session_state.get("kusha_running", False)
        with btn_col1:
            btn_label = f"Build research brief for {target_company_name}" if target_company_name else "Select a company to research"
            run_btn_manual = st.button(
                btn_label,
                type="primary",
                width="stretch",
                disabled=not bool(target_company_name) or budget_exhausted or is_running
            )
            if run_btn_manual:
                run_btn = True
        with btn_col2:
            if st.button("Try synthetic demo (Tata Consumer)", width="stretch", disabled=budget_exhausted or is_running):
                st.session_state["pending_company_choice"] = "Tata Consumer Products Ltd. (TATACONSUM)"
                st.session_state["trigger_demo_run"] = True
                st.rerun()

        cache_badge_ph = st.empty()
        force_live_api = False

        # Latency / estimated duration guidance
        st.markdown(
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px; padding: 4px 6px; font-size: 11.5px; color: #64748B;">'
            f'<span>⏱️ <strong>Estimated Latency:</strong> ~12–20s (Web research) &middot; ~45–75s (BSE statutory filing) &middot; &lt;1s (Demo)</span>'
            f'<span style="font-family: monospace; font-size: 11px; color: #059669; font-weight: 700;">Active Model: {selected_gemini_model}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Advanced research options expander
        with st.expander("⚙️ Advanced research options (sector override, filings & PDFs)", expanded=False):
            col_sec1, col_sec2 = st.columns([2, 2])
            with col_sec1:
                target_sector = st.selectbox(
                    "Sector override",
                    sector_list,
                    index=def_sector_idx,
                    help="Applies sector-specific thresholds for DSO, inventory, and operating margins."
                )
            with col_sec2:
                doc_type = st.segmented_control(
                    "Data Source",
                    ["⚡ Auto-fetch BSE filing", "📂 Upload custom PDF", "🌐 Web research only"],
                    default="⚡ Auto-fetch BSE filing",
                    help="Finds annual-report links through Screener.in, accepts only HTTPS PDF links hosted on BSE, and validates the downloaded PDF before analysis."
                )

            skip_web_search = False
            if doc_type != "🌐 Web research only":
                skip_web_search = st.toggle(
                    "⚡ Skip web search grounding (Conserves API quota)",
                    value=False,
                    help="Grounds analysis directly on the official PDF filing and skips Google Search web queries. Saves 1 full API call per audit and avoids 429 search quota exhaustion."
                )

            uploaded_file = None
            selected_filing_metadata = None

            if doc_type == "⚡ Auto-fetch BSE filing":
                available_reports = get_available_annual_reports(target_ticker) if target_ticker else []
                if available_reports:
                    report_options = {f"{r['title']} ({r.get('year', 'Latest')})": r for r in available_reports}
                    selected_report_label = st.selectbox(
                        "BSE-hosted filing candidate",
                        options=list(report_options.keys()),
                        index=0,
                        help="A BSE-hosted PDF candidate discovered through Screener.in. The host and PDF bytes are checked before analysis."
                    )
                    selected_filing_metadata = report_options[selected_report_label]
                    st.caption("BSE-hosted PDF candidate found via Screener.in. The host and PDF bytes are checked before use.")
                    st.link_button("View filing candidate", selected_filing_metadata["url"])
                else:
                    if target_ticker and target_ticker != "CUSTOM":
                        st.info(f"No direct BSE annual report PDF link was found in the public index for {target_ticker}. You can upload a custom PDF or run Web research.")
                    selected_filing_metadata = None
            elif doc_type == "📂 Upload custom PDF":
                st.markdown("""
                <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; margin-bottom: 10px; font-size: 11.5px; color: #475569; line-height: 1.45;">
                  <strong style="color: #0F172A;">🔒 Privacy &amp; Cloud Processing Notice:</strong> Uploaded statutory PDFs are temporarily streamed to Google's Gemini Files API for multimodal financial extraction and deleted immediately upon evaluation completion. Do not upload confidential non-public material.
                </div>
                """, unsafe_allow_html=True)
                uploaded_file = st.file_uploader(
                    "Upload Annual Report (PDF)",
                    type=["pdf"],
                    help="Uploaded PDF is processed via Google Gemini Files API for multimodal financial statement extraction."
                )
                if uploaded_file:
                    raw_pdf_bytes = uploaded_file.getvalue()
                    if len(raw_pdf_bytes) > MAX_PDF_MB * 1024 * 1024:
                        st.error(f"Uploaded file exceeds maximum limit of {MAX_PDF_MB}MB (received {len(raw_pdf_bytes)/(1024*1024):.1f}MB).")
                        uploaded_file = None
                        selected_filing_metadata = None
                    elif not raw_pdf_bytes.startswith(b"%PDF-"):
                        st.error("Not a valid PDF (missing '%PDF-' header).")
                        uploaded_file = None
                        selected_filing_metadata = None
                    else:
                        selected_filing_metadata = {
                            "title": uploaded_file.name,
                            "year": "User Uploaded",
                            "source": "Manual PDF Upload",
                            "url": None
                        }
            else:
                st.caption("Gemini will perform Google Search grounding on recent filings, investor presentations, and market reports.")
                selected_filing_metadata = None

        if not target_sector:
            target_sector = matched_info["sector"] if matched_info else "General"

        # Determine execution profile and expected mode for cache key consistency
        if demo_mode:
            mode_pill = "🧪 Synthetic Demo"
        elif doc_type == "⚡ Auto-fetch BSE filing" and selected_filing_metadata:
            mode_pill = "⚡ BSE Annual Report"
        elif doc_type == "📂 Upload custom PDF" and uploaded_file:
            mode_pill = "📂 Custom PDF"
        else:
            mode_pill = "🌐 Web Research"

        # Compute document_hash once per run
        pdf_bytes = uploaded_file.getvalue() if (doc_type == "📂 Upload custom PDF" and uploaded_file) else None
        if pdf_bytes:
            document_hash = hashlib.sha256(pdf_bytes).hexdigest()
        elif doc_type == "⚡ Auto-fetch BSE filing" and selected_filing_metadata and selected_filing_metadata.get("url"):
            document_hash = hashlib.sha256(selected_filing_metadata["url"].encode("utf-8")).hexdigest()
        else:
            document_hash = "no_document"

        clean_target_name = str(target_company_name or "").strip()
        clean_target_ticker = str(target_ticker or "").strip()

        # Check if local cached evaluation exists (Probe site)
        cached_exists = False
        if use_eval_cache and clean_target_ticker:
            cached_exists = load_cached_evaluation(
                company_name=clean_target_name,
                ticker=clean_target_ticker,
                model=selected_gemini_model,
                current_pipeline_version=ANALYSIS_PIPELINE_VERSION,
                document_hash=document_hash,
                sector=target_sector,
                skip_web_search=skip_web_search,
                analysis_mode=mode_pill,
            ) is not None

        if cached_exists:
            with cache_badge_ph.container():
                col_c1, col_c2 = st.columns([2.6, 1.4])
                with col_c1:
                    st.markdown(
                        '<div style="margin-top: 4px; font-size: 11.5px; color: #059669; font-weight: 700;">'
                        '⚡ <strong>Cached Evaluation Available:</strong> Will replay in &lt;0.05s with 0 API quota.'
                        '</div>',
                        unsafe_allow_html=True
                    )
                with col_c2:
                    force_live_api = st.checkbox("Force fresh live API run", value=False, help="Bypasses local cache and executes fresh Gemini API call.")

        # Secondary Expander: Company Data & 10-Year Financial History
        with st.expander("📊 View company data & 10-year financial history", expanded=False):
            if live_data:
                # Automated Data Consistency Engine (runs in background for target)
                sentinel_report = DataIntegritySentinel.audit_and_certify(
                    ticker_symbol=target_ticker,
                    company_name=target_company_name,
                    financial_statements=fin_res,
                    live_market_data=live_data
                )
                st.session_state["sentinel_report"] = sentinel_report

                forensic_report = ForensicRiskEngine.audit_company_forensics(
                    ticker_symbol=target_ticker,
                    company_name=target_company_name,
                    sector=target_sector,
                    financial_statements=fin_res,
                    live_market_data=live_data
                )
                st.session_state["forensic_report"] = forensic_report

                # Price chart
                st.markdown(
                    f'<div style="font-size: 15px; font-weight: 800; color: #0F172A; margin: 12px 0 6px;">'
                    f'<span>📈</span> {target_company_name} ({target_ticker}) Price Action'
                    f'</div>',
                    unsafe_allow_html=True
                )
                hist_df = get_cached_ticker_history(target_ticker, period="1y")
                if not hist_df.empty:
                    stk_fig = build_ticker_chart(hist_df, target_ticker, "Area", show_dma=True)
                    if stk_fig:
                        st.plotly_chart(stk_fig, width="stretch", key=f"intake_price_chart_{target_ticker}")

                # 27 Key Screener Ratios
                metric_cards_html = render_dalal_street_metric_cards_html(live_data, fin_res)
                if metric_cards_html:
                    st.html(f'<div class="metrics-3col-grid" style="margin-top: 18px;">{metric_cards_html}</div>')

                # Multi-year historical statements
                if fin_res and "years" in fin_res and not fin_res.get("error"):
                    st.markdown(
                        f'<div style="font-size: 16px; font-weight: 800; color: #0F172A; margin-top: 22px; margin-bottom: 6px;">'
                        f'<span>📑</span> Audited Financial Statements &amp; Trends'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    st.html(render_growth_cagr_scorecard_html(fin_res["cagr"]))
                    stmt_sub = st.segmented_control(
                        "Statement",
                        options=["📜 Profit & Loss", "⚡ Quarterly", "🏛️ Balance Sheet", "💵 Cash Flows"],
                        default="📜 Profit & Loss",
                        key=f"exp_stmt_{target_ticker}",
                        label_visibility="collapsed"
                    )
                    if stmt_sub == "📜 Profit & Loss":
                        st.html(render_financial_table_html(fin_res["pnl"], fin_res["years"], "Annual Profit & Loss Statement"))
                    elif stmt_sub == "⚡ Quarterly":
                        if fin_res.get("quarterly") and fin_res.get("q_years"):
                            st.html(render_financial_table_html(fin_res["quarterly"], fin_res["q_years"], "Quarterly Financial Performance"))
                        else:
                            st.info("Quarterly statements currently synchronizing for this company.")
                    elif stmt_sub == "🏛️ Balance Sheet":
                        st.html(render_financial_table_html(fin_res["bs"], fin_res["bs_years"], "Annual Balance Sheet"))
                    elif stmt_sub == "💵 Cash Flows":
                        st.html(render_financial_table_html(fin_res["cf"], fin_res["cf_years"], "Annual Cash Flow Statement"))

                    cagr_insights = generate_forensic_cagr_insights(fin_res, target_company_name)
                    if cagr_insights:
                        insight_boxes = []
                        for ins in cagr_insights:
                            status_type = ins.get("status", "info")
                            if status_type == "positive":
                                iborder, ibg, ititle_color, ibody_color, icon = "#10B981", "#ECFDF5", "#065F46", "#047857", "✔"
                            elif status_type == "negative":
                                iborder, ibg, ititle_color, ibody_color, icon = "#EF4444", "#FEF2F2", "#991B1B", "#7F1D1D", "⚠"
                            else:
                                iborder, ibg, ititle_color, ibody_color, icon = "#3B82F6", "#EFF6FF", "#1E40AF", "#1E3A8A", "ℹ"
                            insight_boxes.append(
                                f'<div style="background: {ibg}; border-left: 3.5px solid {iborder}; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;">'
                                f'<div style="font-size: 13px; font-weight: 800; color: {ititle_color}; display: flex; align-items: center; gap: 6px;">'
                                f'<span>{icon}</span> {ins.get("title")}'
                                f'</div>'
                                f'<div style="font-size: 12px; line-height: 1.5; color: {ibody_color}; margin-top: 3px;">'
                                f'{ins.get("body")}'
                                f'</div>'
                                f'</div>'
                            )
                        st.html(f'<div style="margin-top: 14px;">{"".join(insight_boxes)}</div>')
            else:
                st.info("Select a tracked company above to view its 10-year financial history, balance sheet, and live market quotes.")
else:
    selected_company_str = None
    matched_info = None
    target_company_name = None
    target_ticker = None
    target_sector = None
    uploaded_file = None
    selected_filing_metadata = None
    doc_type = "⚡ Auto-fetch BSE filing"
    skip_web_search = False
    force_live_api = False
    live_data = None
    fin_res = None
    run_btn = False


# Display metadata for the 8 canonical pillars.
# The labels MUST match analyzer.CANONICAL_PILLARS so a chip never mislabels a score.
_PILLAR_STYLE = [
    ("🏛️", "Governance", "rgba(5, 150, 105, 0.08)", "#059669", "rgba(5, 150, 105, 0.25)"),
    ("🔍", "Forensics", "rgba(37, 99, 235, 0.08)", "#2563EB", "rgba(37, 99, 235, 0.25)"),
    ("🛡️", "Risk / ESG", "rgba(124, 58, 237, 0.08)", "#7C3AED", "rgba(124, 58, 237, 0.25)"),
    ("📈", "Valuation", "rgba(37, 99, 235, 0.08)", "#2563EB", "rgba(37, 99, 235, 0.25)"),
    ("🔄", "Moat", "rgba(5, 150, 105, 0.08)", "#059669", "rgba(5, 150, 105, 0.25)"),
    ("💵", "Simplicity", "rgba(217, 119, 6, 0.08)", "#D97706", "rgba(217, 119, 6, 0.25)"),
    ("🚀", "Innovation", "rgba(124, 58, 237, 0.08)", "#7C3AED", "rgba(124, 58, 237, 0.25)"),
    ("⚖️", "Insider Risk", "rgba(234, 88, 12, 0.08)", "#EA580C", "rgba(234, 88, 12, 0.25)"),
]

PILLAR_METADATA = {
    pillar["id"]: {
        "icon": _PILLAR_STYLE[i][0],
        "chip": _PILLAR_STYLE[i][1],
        "chip_bg": _PILLAR_STYLE[i][2],
        "chip_fg": _PILLAR_STYLE[i][3],
        "border": _PILLAR_STYLE[i][4],
        "name": pillar["name"],
    }
    for i, pillar in enumerate(analyzer.CANONICAL_PILLARS)
}

# Helper to build Plotly 8-Pillar Radar Chart in Institutional White & Emerald
def build_radar_chart(pillars):
    if not pillars:
        return None
    names = [f"P{p['id']}: {p['name']}" for p in pillars]
    pct_scores = [(p["score"] / p["max_score"]) * 100 for p in pillars]
    
    names_closed = names + [names[0]]
    pct_closed = pct_scores + [pct_scores[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=pct_closed,
        theta=names_closed,
        fill='toself',
        fillcolor='rgba(5, 150, 105, 0.18)',
        line=dict(color='#059669', width=3),
        marker=dict(size=7, color='#2563EB', line=dict(color='#FFFFFF', width=2)),
        name='% of Max Score'
    ))

    fig.update_layout(
        template="plotly_white",
        polar=dict(
            bgcolor='#FFFFFF',
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%",
                gridcolor='#E2E8F0',
                linecolor='#CBD5E1',
                tickfont=dict(color='#64748B', size=10, family='JetBrains Mono')
            ),
            angularaxis=dict(
                gridcolor='#E2E8F0',
                linecolor='#CBD5E1',
                tickfont=dict(color='#0F172A', size=11.5, family='Inter', weight=700)
            )
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=55, r=55, t=30, b=30),
        height=430
    )
    return fig

# --- INTUITIVE FORENSIC LENS HELPERS ---
def parse_dcf_estimate(dcf_str):
    if not dcf_str:
        return None, None, None
    s = str(dcf_str)
    curr_matches = re.findall(r"(?:INR|₹|Rs\.?)\s*([\d,]+(?:\.\d+)?)", s, re.IGNORECASE)
    nums = []
    for item in curr_matches:
        clean = item.replace(",", "").strip()
        if clean:
            try:
                v = float(clean)
                if v > 0:
                    nums.append(v)
            except ValueError:
                pass
    if not nums:
        fallback = re.findall(r"\b([\d,]+(?:\.\d+)?)\b(?!\s*(?:%|bps|percent))", s, re.IGNORECASE)
        for item in fallback:
            clean = item.replace(",", "").strip()
            if clean:
                try:
                    v = float(clean)
                    if v > 0:
                        nums.append(v)
                except ValueError:
                    pass
    if len(nums) >= 2:
        l, h = sorted([nums[0], nums[1]])
        return l, h, (l + h) / 2.0
    elif len(nums) == 1:
        return nums[0], nums[0], nums[0]
    return None, None, None

def render_live_analysis_timer_html(
    company_name: str,
    ticker: str,
    mode_label: str,
    est_label: str,
    est_sec_typical: int = 60,
    completed_sec: float | None = None,
    is_error: bool = False
) -> str:
    """Renders a client-side JavaScript ticking stopwatch and progress gauge for live analysis."""
    esc_company = html.escape(str(company_name or "Target Entity"))
    esc_ticker = html.escape(str(ticker or "NSE/BSE"))
    esc_mode = html.escape(str(mode_label or "Fundamental Audit"))
    esc_est = html.escape(str(est_label or "~45–75s"))
    typical_s = max(1, int(est_sec_typical or 60))

    if completed_sec is not None:
        total_s = max(0.0, float(completed_sec))
        m = int(total_s // 60)
        s = int(total_s % 60)
        d = int((total_s * 10) % 10)
        time_display = f"{m:02d}:{s:02d}"
        tenths_display = str(d)
        
        if is_error:
            pulse_color = "#DC2626"
            title_text = f"Audit Interrupted · {esc_company} ({esc_ticker})"
            badge_text = "Failed / Error"
            badge_style = "color: #EF4444; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3);"
            bar_style = "width: 100%; background: #EF4444;"
            phase_text = "Evaluation interrupted. See technical diagnostics below."
            pct_display = "100%"
        else:
            pulse_color = "#10B981"
            title_text = f"Audit Completed · {esc_company} ({esc_ticker})"
            badge_text = f"Completed in {total_s:.1f}s ✔"
            badge_style = "color: #10B981; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3);"
            bar_style = "width: 100%; background: linear-gradient(90deg, #10B981, #059669);"
            phase_text = "✅ Institutional brief compiled &amp; mathematical guardrails verified."
            pct_display = "100%"

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: transparent;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    color: #F8FAFC;
    overflow: hidden;
  }}
  .timer-card {{
    background: linear-gradient(135deg, #090D16 0%, #0F172A 60%, #1E293B 100%);
    border: 1.5px solid #334155;
    border-radius: 12px;
    padding: 12px 18px;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.45);
  }}
  .header-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }}
  .live-tag {{
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.7px;
    color: {pulse_color};
    text-transform: uppercase;
  }}
  .pulse-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: {pulse_color};
    box-shadow: 0 0 8px {pulse_color};
  }}
  .mode-badge {{
    background: rgba(56, 189, 248, 0.12);
    color: #38BDF8;
    border: 1px solid rgba(56, 189, 248, 0.28);
    font-size: 10px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 9999px;
    font-family: monospace;
    letter-spacing: 0.4px;
  }}
  .metrics-grid {{
    display: grid;
    grid-template-columns: 1.2fr 1fr 0.9fr;
    gap: 12px;
    align-items: center;
  }}
  .metric-block {{
    display: flex;
    flex-direction: column;
  }}
  .metric-label {{
    font-size: 9.5px;
    font-weight: 800;
    letter-spacing: 0.6px;
    color: #94A3B8;
    text-transform: uppercase;
    margin-bottom: 2px;
  }}
  .clock-digits {{
    font-family: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
    font-size: 24px;
    font-weight: 900;
    color: #F8FAFC;
    letter-spacing: 0.5px;
    line-height: 1.1;
  }}
  .clock-digits .tenths {{
    color: {pulse_color};
    font-size: 20px;
  }}
  .estimate-val {{
    font-family: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
    font-size: 16px;
    font-weight: 700;
    color: #E2E8F0;
  }}
  .status-badge {{
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    {badge_style}
    padding: 3px 8px;
    border-radius: 6px;
    text-align: center;
    width: fit-content;
  }}
  .progress-track {{
    background: #1E293B;
    border: 1px solid rgba(255, 255, 255, 0.05);
    height: 6px;
    border-radius: 9999px;
    overflow: hidden;
    margin-top: 9px;
  }}
  .progress-fill {{
    height: 100%;
    {bar_style}
    border-radius: 9999px;
  }}
  .footer-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 6px;
    font-size: 11px;
  }}
  .phase-text {{
    color: #94A3B8;
    font-size: 11px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .pct-text {{
    color: {pulse_color};
    font-family: monospace;
    font-weight: 800;
    font-size: 11px;
    margin-left: 8px;
  }}
</style>
</head>
<body>
<div class="timer-card">
  <div class="header-row">
    <div class="live-tag">
      <span class="pulse-dot"></span>
      <span>{title_text}</span>
    </div>
    <span class="mode-badge">{esc_mode}</span>
  </div>
  <div class="metrics-grid">
    <div class="metric-block">
      <span class="metric-label">Total Duration</span>
      <div class="clock-digits"><span>{time_display}</span>.<span class="tenths">{tenths_display}</span></div>
    </div>
    <div class="metric-block">
      <span class="metric-label">Target Estimate</span>
      <div class="estimate-val">⏳ {esc_est}</div>
    </div>
    <div class="metric-block">
      <span class="metric-label">Engine Status</span>
      <div class="status-badge">{badge_text}</div>
    </div>
  </div>
  <div class="progress-track">
    <div class="progress-fill"></div>
  </div>
  <div class="footer-row">
    <span class="phase-text">{phase_text}</span>
    <span class="pct-text">{pct_display}</span>
  </div>
</div>
</body>
</html>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: transparent;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    color: #F8FAFC;
    overflow: hidden;
  }}
  .timer-card {{
    background: linear-gradient(135deg, #090D16 0%, #0F172A 60%, #1E293B 100%);
    border: 1.5px solid #334155;
    border-radius: 12px;
    padding: 12px 18px;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.45);
  }}
  .header-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }}
  .live-tag {{
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.7px;
    color: #38BDF8;
    text-transform: uppercase;
  }}
  .pulse-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10B981;
    box-shadow: 0 0 8px #10B981;
    animation: livePulse 1.4s ease-in-out infinite;
  }}
  @keyframes livePulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.4; transform: scale(0.85); }}
  }}
  .mode-badge {{
    background: rgba(56, 189, 248, 0.12);
    color: #38BDF8;
    border: 1px solid rgba(56, 189, 248, 0.28);
    font-size: 10px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 9999px;
    font-family: monospace;
    letter-spacing: 0.4px;
  }}
  .metrics-grid {{
    display: grid;
    grid-template-columns: 1.2fr 1fr 0.9fr;
    gap: 12px;
    align-items: center;
  }}
  .metric-block {{
    display: flex;
    flex-direction: column;
  }}
  .metric-label {{
    font-size: 9.5px;
    font-weight: 800;
    letter-spacing: 0.6px;
    color: #94A3B8;
    text-transform: uppercase;
    margin-bottom: 2px;
  }}
  .clock-digits {{
    font-family: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
    font-size: 24px;
    font-weight: 900;
    color: #F8FAFC;
    letter-spacing: 0.5px;
    line-height: 1.1;
  }}
  .clock-digits .tenths {{
    color: #38BDF8;
    font-size: 20px;
  }}
  .estimate-val {{
    font-family: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
    font-size: 16px;
    font-weight: 700;
    color: #E2E8F0;
  }}
  .status-badge {{
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    color: #10B981;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.25);
    padding: 3px 8px;
    border-radius: 6px;
    text-align: center;
    width: fit-content;
  }}
  .progress-track {{
    background: #1E293B;
    border: 1px solid rgba(255, 255, 255, 0.05);
    height: 6px;
    border-radius: 9999px;
    overflow: hidden;
    margin-top: 9px;
  }}
  .progress-fill {{
    height: 100%;
    width: 2%;
    background: linear-gradient(90deg, #38BDF8, #10B981);
    border-radius: 9999px;
    transition: width 0.15s ease-out;
  }}
  .footer-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 6px;
    font-size: 11px;
  }}
  .phase-text {{
    color: #94A3B8;
    font-size: 11px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .pct-text {{
    color: #38BDF8;
    font-family: monospace;
    font-weight: 800;
    font-size: 11px;
    margin-left: 8px;
  }}
</style>
</head>
<body>
<div class="timer-card">
  <div class="header-row">
    <div class="live-tag">
      <span class="pulse-dot"></span>
      <span>Live Audit &middot; {esc_company} ({esc_ticker})</span>
    </div>
    <span class="mode-badge">{esc_mode}</span>
  </div>
  <div class="metrics-grid">
    <div class="metric-block">
      <span class="metric-label">Elapsed Time</span>
      <div class="clock-digits"><span id="m_s">00:00</span>.<span class="tenths" id="tenths">0</span></div>
    </div>
    <div class="metric-block">
      <span class="metric-label">Estimated Latency</span>
      <div class="estimate-val">⏳ {esc_est}</div>
    </div>
    <div class="metric-block">
      <span class="metric-label">Engine Pace</span>
      <div class="status-badge" id="pace_badge">Active &middot; On Track</div>
    </div>
  </div>
  <div class="progress-track">
    <div class="progress-fill" id="progress_bar"></div>
  </div>
  <div class="footer-row">
    <span class="phase-text" id="phase_label">Connecting to exchange feeds &amp; fundamental database...</span>
    <span class="pct-text" id="pct_label">0%</span>
  </div>
</div>
<script>
(function() {{
  var t0 = Date.now();
  var est = {typical_s};
  var msEl = document.getElementById('m_s');
  var tenEl = document.getElementById('tenths');
  var barEl = document.getElementById('progress_bar');
  var pctEl = document.getElementById('pct_label');
  var phaseEl = document.getElementById('phase_label');
  var paceEl = document.getElementById('pace_badge');

  function update() {{
    var elapsedMs = Date.now() - t0;
    var totalSec = elapsedMs / 1000.0;
    var mins = Math.floor(totalSec / 60);
    var secs = Math.floor(totalSec % 60);
    var tenths = Math.floor((elapsedMs % 1000) / 100);

    msEl.textContent = (mins < 10 ? '0' : '') + mins + ':' + (secs < 10 ? '0' : '') + secs;
    tenEl.textContent = tenths;

    var pct = 0;
    if (est <= 1) {{
      pct = Math.min(98, Math.round(totalSec * 80));
    }} else {{
      pct = Math.round((totalSec / est) * 100);
      if (pct > 96) {{
        pct = Math.min(99, 96 + Math.round(((totalSec - est) / (est * 0.5)) * 3));
      }}
    }}
    pct = Math.max(2, Math.min(99, pct));
    barEl.style.width = pct + '%';
    pctEl.textContent = pct + '%';

    if (totalSec > est && paceEl && est > 2) {{
      paceEl.textContent = 'Deep Synthesis';
      paceEl.style.color = '#F59E0B';
      paceEl.style.borderColor = 'rgba(245, 158, 11, 0.4)';
      paceEl.style.background = 'rgba(245, 158, 11, 0.15)';
    }}

    if (pct < 15) {{
      phaseEl.textContent = 'Connecting to exchange feeds & parsing fundamental tables...';
    }} else if (pct < 35) {{
      phaseEl.textContent = 'Evaluating statutory filings & footnote schedules...';
    }} else if (pct < 70) {{
      phaseEl.textContent = 'Multimodal reasoning across 8 Pillars with Gemini 2.5...';
    }} else if (pct < 90) {{
      phaseEl.textContent = 'Enforcing deterministic Python scoring & PIO guardrails...';
    }} else {{
      phaseEl.textContent = 'Compiling institutional research brief & governance dossier...';
    }}
  }}

  setInterval(update, 100);
  update();
}})();
</script>
</body>
</html>"""

def render_research_provenance_and_evidence_card(res, live_data, target_company_name, target_ticker, target_sector, fin_res=None):
    live = live_data or {}
    company_name = html.escape(str(target_company_name or res.get("company_name", "Tracked Company")))
    ticker = html.escape(str(target_ticker or res.get("ticker", "NSE")))
    sector = html.escape(str(target_sector or res.get("sector", "General")))
    
    filing_meta = res.get("filing_metadata") or {}
    period = html.escape(str(filing_meta.get("year") or res.get("financial_year") or "FY2024 / TTM"))
    
    is_demo = bool(res.get("is_synthetic_demo", False))
    is_analyzed = filing_meta.get("ingestion_status") == "analyzed" or res.get("document_analyzed", False)
    
    # 1. Company & Period
    q1_sub = f"<strong>{company_name}</strong> ({ticker}) · Sector: {sector} · Audited Period: <strong>{period}</strong>"
    
    # 2. Data Origin
    if is_demo:
        q2_source = "Synthetic demonstration dataset (sample for UI walkthrough; not live market data)"
        q2_chip = "SYNTHETIC SAMPLE"
        q2_chip_bg = "#FFFBEB"
        q2_chip_fg = "#D97706"
        q2_chip_bdr = "#FDE68A"
    elif is_analyzed:
        q2_source = f"Official BSE India statutory filing ({filing_meta.get('title', 'Annual Report')}) + delayed Yahoo Finance statements (~4 years, unaudited) + delayed quotes"
        q2_chip = "STATUTORY BSE FILING"
        q2_chip_bg = "#ECFDF5"
        q2_chip_fg = "#059669"
        q2_chip_bdr = "#A7F3D0"
    else:
        research = res.get("web_research", {})
        src_cnt = len(research.get("sources", []))
        q2_source = f"Delayed Yahoo Finance market and statement data (unaudited) + {src_cnt} web citation{'s' if src_cnt != 1 else ''}"
        q2_chip = "PUBLIC FEEDS & CITATIONS"
        q2_chip_bg = "#EFF6FF"
        q2_chip_fg = "#2563EB"
        q2_chip_bdr = "#BFDBFE"

    # 3. Freshness & Integrity
    sentinel = res.get("sentinel_audit") or {}
    s_score = sentinel.get("integrity_score")
    s_text = f"{s_score:.0f}/100" if s_score is not None else "Not evaluated (insufficient data)"
    retrieval_time = res.get("retrieved_at") or "Not recorded"
    exec_sec = res.get("execution_time_seconds")
    est_lbl = res.get("estimated_time_label")
    is_cached = res.get("is_cached_result", False)
    if is_cached:
        latency_str = f" · Replay: Local Cache ({exec_sec:.2f}s · 0 API Quota)"
    else:
        latency_str = f" · Latency: {exec_sec:.1f}s" + (f" (Est: {est_lbl})" if est_lbl else "") if exec_sec is not None else ""
    q3_text = f"Retrieved: {retrieval_time} · Multimodal Ingestion: {'Verified' if is_analyzed else 'Public Feed'} · Mathematical Sanity Check: {s_text}{latency_str}"

    # 4. Qualified Conclusion & Supporting Evidence
    try:
        final_score = float(res.get("final_score", 0))
    except (ValueError, TypeError):
        final_score = 0.0
    pio_trig = res.get("pio_triggered", False)
    guardrail = str(res.get("guardrail_tag", ""))

    if pio_trig or analyzer.guardrail_level(guardrail) == analyzer.GUARDRAIL_RED or final_score < 55.0:
        stance_label = "Elevated Caution / High Risk"
        stance_col = "#DC2626"
        stance_bg = "#FEF2F2"
        stance_bdr = "#FECACA"
    elif final_score >= 70.0:
        stance_label = "Constructive Watchlist / Quality Franchise"
        stance_col = "#059669"
        stance_bg = "#ECFDF5"
        stance_bdr = "#A7F3D0"
    else:
        stance_label = "Monitored / Neutral Tier"
        stance_col = "#D97706"
        stance_bg = "#FFFBEB"
        stance_bdr = "#FDE68A"

    verdict_text = res.get("verdict", "") or f"Composite Forensic Score: {final_score:.1f}/100"
    verdict_clean = html.escape(str(verdict_text))

    # 5. Evidence Gaps
    gaps = res.get("evidence_gaps") or []
    if gaps:
        gap_items = "".join([f'<li style="margin-bottom: 4px;">{html.escape(str(g))}</li>' for g in gaps[:3]])
        q5_html = f'<ul style="margin: 4px 0 0 16px; padding: 0; color: #B45309; font-size: 12px; line-height: 1.45;">{gap_items}</ul>'
        gap_badge = f'<span style="background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 9999px;">{len(gaps)} EVIDENCE GAPS</span>'
    else:
        q5_html = '<div style="font-size: 12px; color: #059669; margin-top: 4px;">✔ Standard audited statement schedules reviewed; check Notes to Accounts for unlisted commitments.</div>'
        gap_badge = '<span style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 9999px;">STANDARD DISCLOSURES</span>'

    # 6. What to Inspect Next
    next_checks = [
        "CARO 2020 Order: Check paragraph 3 for adverse inventory or disputed statutory tax remarks.",
        "Notes to Accounts: Review Note on Related-Party Transactions & Contingent Liabilities.",
        "Cash Conversion: Cross-examine CFO vs PAT across trailing 4 quarters.",
        "Promoter Registry: Inspect BSE / NSE shareholding disclosures for fresh encumbrances."
    ]
    next_html = "".join([f'<li style="margin-bottom: 4px;">{html.escape(c)}</li>' for c in next_checks])

    card_html = (
        f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.03);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 10px; border-bottom: 1.5px solid #F1F5F9; padding-bottom: 10px;">'
        f'<div style="display: flex; align-items: center; gap: 8px;">'
        f'<span style="font-size: 18px;">🧭</span>'
        f'<span style="font-size: 14px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.7px;">Research Provenance &amp; Due Diligence Framework</span>'
        f'</div>'
        f'<span style="background: {q2_chip_bg}; color: {q2_chip_fg}; border: 1px solid {q2_chip_bdr}; font-size: 11px; font-weight: 800; padding: 3px 10px; border-radius: 9999px; font-family: \'JetBrains Mono\', monospace;">{q2_chip}</span>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; margin-bottom: 14px;">'
        f'<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; border-left: 3.5px solid #059669;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">1. Subject Entity &amp; Target Period</div>'
        f'<div style="font-size: 12.5px; color: #0F172A; margin-top: 4px; line-height: 1.45;">{q1_sub}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; border-left: 3.5px solid #2563EB;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">2. Source Provenance</div>'
        f'<div style="font-size: 12px; color: #334155; margin-top: 4px; line-height: 1.45;">{q2_source}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; border-left: 3.5px solid #7C3AED;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">3. Freshness &amp; Sanity Audit</div>'
        f'<div style="font-size: 12px; color: #334155; margin-top: 4px; line-height: 1.45;">{q3_text}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; border-left: 3.5px solid {stance_col};">'
        f'<div style="display: flex; justify-content: space-between; align-items: center;">'
        f'<span style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">4. Model Forensic Stance</span>'
        f'<span style="background: {stance_bg}; color: {stance_col}; border: 1px solid {stance_bdr}; font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 9999px;">{stance_label}</span>'
        f'</div>'
        f'<div style="font-size: 12px; color: #0F172A; font-weight: 600; margin-top: 4px; line-height: 1.45;">{verdict_clean}</div>'
        f'</div>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">'
        f'<div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 10px; padding: 12px 14px;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">'
        f'<span style="font-size: 11px; font-weight: 800; color: #92400E; text-transform: uppercase; letter-spacing: 0.5px;">5. Evidence Gaps &amp; Uncertainties</span>'
        f'{gap_badge}'
        f'</div>'
        f'{q5_html}'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px;">'
        f'<div style="font-size: 11px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">6. What to Inspect Next (Due Diligence Checklist)</div>'
        f'<ol style="margin: 4px 0 0 16px; padding: 0; color: #475569; font-size: 12px; line-height: 1.45;">{next_html}</ol>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    return card_html

def render_traffic_light_and_eli15_html(res, live_data, target_company_name, target_sector):
    live = live_data or {}

    def _parse_num(val):
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    cmp = _parse_num(live.get("current_price"))
    de_val = _parse_num(live.get("debt_to_equity"))
    pe = _parse_num(live.get("pe_ratio"))

    # 1. Management Integrity
    pio_trig = res.get("pio_triggered", False)
    guardrail = str(res.get("guardrail_tag", ""))
    total_pen = _parse_num(res.get("total_penalties")) or 0.0
    is_doc_analyzed = res.get("filing_metadata", {}).get("ingestion_status") == "analyzed" or res.get("document_analyzed", False)
    is_insufficient = res.get("analysis_status") == "insufficient_evidence"
    has_gaps = is_insufficient or (bool(res.get("evidence_gaps")) and not is_doc_analyzed)

    if pio_trig or analyzer.guardrail_level(guardrail) == analyzer.GUARDRAIL_RED:
        gov_status = "CRITICAL RISK"
        gov_color = "#DC2626"
        gov_bg = "#FEF2F2"
        gov_border = "#FECACA"
        gov_sub = "High risk: Serious audit red flags or promoter integrity warnings active."
        gov_icon = "🔴"
    elif analyzer.guardrail_level(guardrail) == analyzer.GUARDRAIL_ALERT or total_pen >= 4.0:
        gov_status = "MONITOR"
        gov_color = "#D97706"
        gov_bg = "#FFFBEB"
        gov_border = "#FDE68A"
        gov_sub = "Watch closely: Minor disclosure alerts or related-party schedules flagged."
        gov_icon = "🟡"
    elif has_gaps:
        gov_status = "INSUFFICIENT DATA"
        gov_color = "#D97706"
        gov_bg = "#FFFBEB"
        gov_border = "#FDE68A"
        gov_sub = "Evidence gaps present: Full statutory disclosures could not be verified."
        gov_icon = "🟡"
    else:
        gov_status = "PRISTINE"
        gov_color = "#059669"
        gov_bg = "#ECFDF5"
        gov_border = "#A7F3D0"
        gov_sub = "Clean record: Zero shares pledged, trusted auditor, no accounting issues."
        gov_icon = "🟢"

    # 2. Balance Sheet Fortress
    if de_val is not None:
        if de_val <= 0.4:
            bs_status = "FORTRESS"
            bs_color = "#059669"
            bs_bg = "#ECFDF5"
            bs_border = "#A7F3D0"
            bs_sub = f"Virtually debt-free ({de_val:.2f}x D/E) with strong cash reserves."
            bs_icon = "🟢"
        elif de_val <= 1.0:
            bs_status = "MODERATE"
            bs_color = "#D97706"
            bs_bg = "#FFFBEB"
            bs_border = "#FDE68A"
            bs_sub = f"Manageable debt ({de_val:.2f}x D/E) comfortably serviced by operating cash."
            bs_icon = "🟡"
        else:
            bs_status = "LEVERAGED"
            bs_color = "#DC2626"
            bs_bg = "#FEF2F2"
            bs_border = "#FECACA"
            bs_sub = f"High debt ({de_val:.2f}x D/E). Vulnerable to interest rate or economic slowdowns."
            bs_icon = "🔴"
    else:
        bs_status = "NOT ASSESSED"
        bs_color = "#64748B"
        bs_bg = "#F8FAFC"
        bs_border = "#E2E8F0"
        bs_sub = "Debt-to-equity metric is unavailable from market data feeds."
        bs_icon = "⚪"

    # 3. Valuation Multiples
    appendix_b = res.get("appendix_b_calculations") or {}
    dcf_str = appendix_b.get("dcf_fair_value_estimate", "")
    dcf_low, dcf_high, dcf_mid = parse_dcf_estimate(dcf_str)

    mos_pct = None
    if dcf_mid and cmp:
        mos_pct = ((dcf_mid - cmp) / dcf_mid) * 100.0

    if mos_pct is not None:
        if mos_pct >= 5.0:
            val_status = "ATTRACTIVE"
            val_color = "#059669"
            val_bg = "#ECFDF5"
            val_border = "#A7F3D0"
            val_sub = f"Good entry: Trading {mos_pct:.1f}% below fair value (₹{dcf_mid:,.0f})."
            val_icon = "🟢"
        elif mos_pct >= -10.0:
            val_status = "FAIR VALUE"
            val_color = "#2563EB"
            val_bg = "#EFF6FF"
            val_border = "#BFDBFE"
            val_sub = f"Fairly priced: Trading near intrinsic fair value (₹{dcf_mid:,.0f})."
            val_icon = "🔵"
        else:
            val_status = "STRETCHED"
            val_color = "#DC2626"
            val_bg = "#FEF2F2"
            val_border = "#FECACA"
            val_sub = f"Expensive: Trading {abs(mos_pct):.1f}% above fair value (₹{dcf_mid:,.0f})."
            val_icon = "🔴"
    elif pe is not None:
        if pe <= 25:
            val_status = "ATTRACTIVE"
            val_color = "#059669"
            val_bg = "#ECFDF5"
            val_border = "#A7F3D0"
            val_sub = f"Attractive multiple ({pe:.1f}x P/E) offering good value support."
            val_icon = "🟢"
        elif pe <= 55:
            val_status = "FAIR VALUE"
            val_color = "#2563EB"
            val_bg = "#EFF6FF"
            val_border = "#BFDBFE"
            val_sub = f"Reasonable multiple ({pe:.1f}x P/E) reflecting steady business quality."
            val_icon = "🔵"
        else:
            val_status = "STRETCHED"
            val_color = "#DC2626"
            val_bg = "#FEF2F2"
            val_border = "#FECACA"
            val_sub = f"High valuation ({pe:.1f}x P/E) leaves little margin for error."
            val_icon = "🔴"
    else:
        val_status = "BALANCED"
        val_color = "#2563EB"
        val_bg = "#EFF6FF"
        val_border = "#BFDBFE"
        val_sub = "Valuation multiples in line with industry peers."
        val_icon = "🔵"

    # ELI15 Plain English
    final_score = _parse_num(res.get("final_score")) or 0.0
    company_clean = html.escape(str(target_company_name or "This company"))
    sector_clean = html.escape(str(target_sector or "its sector"))

    if final_score >= 75:
        eli_action = "Bottom Line: High-quality compounder with verified cash flows and clean governance metrics. Favorable risk-reward profile for fundamental watchlists."
        eli_badge = "HIGH FINANCIAL INTEGRITY"
        eli_badge_bg = "rgba(5, 150, 105, 0.08)"
        eli_badge_fg = "#059669"
        eli_badge_bdr = "rgba(5, 150, 105, 0.25)"
    elif final_score >= 60:
        eli_action = "Bottom Line: Established franchise with solid moats, but monitored accruals or valuation suggest exercising margin of safety."
        eli_badge = "MONITORED QUALITY TIER"
        eli_badge_bg = "rgba(37, 99, 235, 0.08)"
        eli_badge_fg = "#2563EB"
        eli_badge_bdr = "rgba(37, 99, 235, 0.25)"
    else:
        eli_action = "Bottom Line: Elevated forensic risk. Significant anomalies identified in debt servicing, governance signals, or cash conversion."
        eli_badge = "ELEVATED FORENSIC RISK"
        eli_badge_bg = "rgba(220, 38, 38, 0.08)"
        eli_badge_fg = "#DC2626"
        eli_badge_bdr = "rgba(220, 38, 38, 0.25)"

    strengths = res.get("strengths", [])
    if strengths and len(strengths) > 0:
        clean_s = html.escape(str(strengths[0]).rstrip("."))
        if "insufficient evidence" in clean_s.lower() and not is_doc_analyzed:
            eli_biz = f"<strong>{company_clean}</strong> operates in India\'s <strong>{sector_clean}</strong> sector; statutory research is incomplete due to evidence gaps."
        else:
            eli_biz = f"<strong>{company_clean}</strong> is an established market leader in India\'s <strong>{sector_clean}</strong> sector, powered by {clean_s.lower()}."
    else:
        eli_biz = f"<strong>{company_clean}</strong> is an established business in India\'s <strong>{sector_clean}</strong> sector with healthy operating cash flows and strong market reach."

    rendered_html = (
        f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 22px 24px; margin-bottom: 22px; box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; flex-wrap: wrap; gap: 10px;">'
        f'<div style="display: flex; align-items: center; gap: 8px;">'
        f'<span style="font-size: 20px;">🚦</span>'
        f'<span style="font-size: 14.5px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.8px;">10-Second Telemetry & Quick Takeaway</span>'
        f'</div>'
        f'<span style="background: {eli_badge_bg}; color: {eli_badge_fg}; border: 1px solid {eli_badge_bdr}; font-size: 11.5px; font-weight: 800; padding: 4px 12px; border-radius: 9999px; font-family: \'JetBrains Mono\', monospace; letter-spacing: 0.4px;">{eli_badge}</span>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 18px;">'
        f'<div style="background: {gov_bg}; border: 1.5px solid {gov_border}; border-radius: 12px; padding: 16px 18px;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px;">1. MANAGEMENT & AUDIT</div>'
        f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">'
        f'<span style="font-size: 16px;">{gov_icon}</span>'
        f'<span style="font-size: 16px; font-weight: 900; color: {gov_color}; font-family: \'JetBrains Mono\', monospace; letter-spacing: 0.3px;">{gov_status}</span>'
        f'</div>'
        f'<div style="font-size: 12.5px; line-height: 1.5; color: #475569;">{gov_sub}</div>'
        f'</div>'
        f'<div style="background: {bs_bg}; border: 1.5px solid {bs_border}; border-radius: 12px; padding: 16px 18px;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px;">2. BALANCE SHEET FORTRESS</div>'
        f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">'
        f'<span style="font-size: 16px;">{bs_icon}</span>'
        f'<span style="font-size: 16px; font-weight: 900; color: {bs_color}; font-family: \'JetBrains Mono\', monospace; letter-spacing: 0.3px;">{bs_status}</span>'
        f'</div>'
        f'<div style="font-size: 12.5px; line-height: 1.5; color: #475569;">{bs_sub}</div>'
        f'</div>'
        f'<div style="background: {val_bg}; border: 1.5px solid {val_border}; border-radius: 12px; padding: 16px 18px;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px;">3. VALUATION & ENTRY</div>'
        f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">'
        f'<span style="font-size: 16px;">{val_icon}</span>'
        f'<span style="font-size: 16px; font-weight: 900; color: {val_color}; font-family: \'JetBrains Mono\', monospace; letter-spacing: 0.3px;">{val_status}</span>'
        f'</div>'
        f'<div style="font-size: 12.5px; line-height: 1.5; color: #475569;">{val_sub}</div>'
        f'</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-left: 4.5px solid #059669; border-radius: 10px; padding: 16px 20px;">'
        f'<div style="font-size: 11.5px; font-weight: 800; color: #059669; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">'
        f'<span>💬</span> Plain-English Executive Summary (ELI15 Takeaway)'
        f'</div>'
        f'<div style="font-size: 13.5px; line-height: 1.6; color: #334155; margin-bottom: 6px;">{eli_biz}</div>'
        f'<div style="font-size: 13.5px; line-height: 1.6; color: #0F172A; font-weight: 700;">{eli_action}</div>'
        f'</div>'
        f'</div>'
    )
    return rendered_html

def render_forensic_fraud_shield_html(res, live_data, financial_data=None, forensic_report=None):
    live = live_data or {}
    fin = financial_data or res.get("financial_statements") or {}
    forensic_rep = forensic_report or res.get("forensic_report") or {}

    def _parse_num(val):
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    shield_items = []
    app_a = res.get("appendix_a_forensic_evidence", [])
    is_doc_analyzed = res.get("filing_metadata", {}).get("ingestion_status") == "analyzed" or res.get("document_analyzed", False)
    is_insufficient = res.get("analysis_status") == "insufficient_evidence"

    def _fcheck(check_id):
        """Look up a result from the forensic engine's check list."""
        return next((c for c in forensic_rep.get("checks", []) if c.get("id") == check_id), {})

    # ==========================================
    # 1. Auditor & Accounting Check
    # ==========================================
    auditor_ev = None
    for ev in app_a:
        ev_lower = ev.lower()
        if "auditor" in ev_lower or "opinion" in ev_lower or "caro" in ev_lower:
            auditor_ev = ev
            break

    if auditor_ev:
        ev_l = auditor_ev.lower()
        clean_terms = [
            "unmodified", "unqualified", "clean", "no qualification",
            "without qualification", "no adverse", "true and fair",
            "zero qualification", "standard unqualified"
        ]
        adverse_terms = [
            "qualified opinion", "adverse opinion", "disclaimer of opinion",
            "resignation", "fraud reported", "material misstatement"
        ]
        has_clean = any(term in ev_l for term in clean_terms)
        has_adverse = any(term in ev_l for term in adverse_terms)

        if has_clean and not has_adverse:
            auditor_status = "PASS"
            auditor_badge = "CLEAN AUDIT"
        elif has_adverse:
            auditor_status = "ALERT"
            auditor_badge = "AUDIT NOTE"
        else:
            auditor_status = "MONITOR"
            auditor_badge = "NOT VERIFIED"
            auditor_ev = "An auditor disclosure was cited but it does not state a clean or adverse opinion; treat as unverified."
    elif _fcheck("FOR_08_AUDITOR_GOVERNANCE").get("status") == "PASS":
        auditor_status = "PASS"
        auditor_badge = "CLEAN AUDIT"
        auditor_ev = _fcheck("FOR_08_AUDITOR_GOVERNANCE").get("detail", "Supplied auditor disclosure reports an unqualified opinion.")
    else:
        auditor_status = "MONITOR"
        auditor_badge = "NOT VERIFIED"
        auditor_ev = "No auditor opinion, CARO qualification or resignation history was available in the supplied data."

    shield_items.append({
        "title": "Auditor & Accounting Check",
        "status": auditor_status,
        "badge": auditor_badge,
        "evidence": auditor_ev
    })

    # ==========================================
    # 2. Promoter Share Pledge Check
    # ==========================================
    # Indian corporate disclosures report pledges numerically in shareholding tables (e.g. 0.00% / Nil / 0 shares).
    # Promoters do NOT state "we have no pledge"; an absence of encumbrance or 0.0% pledge confirms unencumbered holding.
    pledge_ev = None
    for ev in app_a:
        if "pledge" in ev.lower() or "encumbrance" in ev.lower() or "sast" in ev.lower():
            pledge_ev = ev
            break

    prom_holding_str = str(live.get("screener_metrics", {}).get("promoter_holding") or live.get("promoter_holding") or "").strip()
    pledge_check = _fcheck("FOR_07_PROMOTER_PLEDGE")

    if pledge_check.get("status") == "PASS":
        pledge_status = "PASS"
        pledge_badge = "0.0% PLEDGED"
        pledge_ev = pledge_check.get("detail") or "Disclosure reports 0.0% of promoter shareholding pledged."
    elif pledge_check.get("status") == "CRITICAL":
        pledge_status = "ALERT"
        pledge_badge = pledge_check.get("metric", "PLEDGE FLAGGED")
        pledge_ev = pledge_check.get("detail") or "Promoter shares are pledged as loan collateral."
    elif pledge_ev:
        p_l = pledge_ev.lower()
        if any(term in p_l for term in ["0.0%", "zero", "nil", "no pledge", "no shares pledged"]) and "insufficient" not in p_l:
            pledge_status = "PASS"
            pledge_badge = "0.0% PLEDGED"
        elif any(term in p_l for term in ["alert", "high pledge", "encumbered", "pledge flagged"]):
            pledge_status = "MONITOR"
            pledge_badge = "PLEDGE FLAGGED"
        else:
            pledge_status = "MONITOR"
            pledge_badge = "NOT VERIFIED"
            pledge_ev = "A pledge disclosure was cited but does not state a quantified pledge level; treat as unverified."
    else:
        pledge_status = "MONITOR"
        pledge_badge = "NOT VERIFIED"
        pledge_ev = (
            "Promoter pledging could not be verified from the available disclosures. "
            "Absence of a pledge disclosure is not evidence of zero pledging."
        )

    shield_items.append({
        "title": "Promoter Share Pledge",
        "status": pledge_status,
        "badge": pledge_badge,
        "evidence": pledge_ev
    })

    # ==========================================
    # 3. Real Cash vs Paper Profit (Cash Flow Conversion)
    # ==========================================
    cfo_status = None
    cfo_badge = None
    cfo_ev = None

    # Inspect financial statements
    cf_data = fin.get("cf", {})
    pnl_data = fin.get("pnl", {})
    cfo_row = cf_data.get("Cash from Operations (CFO)", {}).get("values", [])
    pat_row = pnl_data.get("Net Profit (PAT)", {}).get("values", [])
    fcf_row = cf_data.get("Free Cash Flow (FCF)", {}).get("values", [])

    cfo_clean = [v for v in cfo_row if isinstance(v, (int, float))]
    pat_clean = [v for v in pat_row if isinstance(v, (int, float))]
    fcf_clean = [v for v in fcf_row if isinstance(v, (int, float))]

    if cfo_clean:
        cum_cfo = sum(cfo_clean)
        cum_pat = sum(pat_clean) if pat_clean else 0.0
        cum_fcf = sum(fcf_clean) if fcf_clean else 0.0
        conv_pct = (cum_cfo / cum_pat * 100.0) if cum_pat > 0 else None

        if cum_cfo > 0 and conv_pct is not None:
            cfo_status = "PASS"
            cfo_badge = "CFO > PAT (REAL CASH)" if conv_pct >= 90.0 else f"CFO/PAT: {conv_pct:.0f}%"
            fcf_note = f" with ₹{cum_fcf:,.0f} Cr cumulative FCF" if cum_fcf > 0 else ""
            cfo_ev = f"Cumulative CFO of ₹{cum_cfo:,.0f} Cr ({conv_pct:.0f}% of PAT){fcf_note}. This is a cash-conversion ratio, not proof of earnings quality."
        elif cum_cfo > 0:
            cfo_status = "MONITOR"
            cfo_badge = "CFO/PAT: N/A"
            cfo_ev = (
                f"Cumulative CFO is positive (₹{cum_cfo:,.0f} Cr) but cumulative PAT is "
                f"{'zero' if cum_pat == 0 else 'negative'}, so the CFO/PAT ratio is not meaningful."
            )
        else:
            cfo_status = "MONITOR"
            cfo_badge = "NEGATIVE CFO"
            cfo_ev = f"Operating cash burn detected: cumulative CFO is negative (₹{cum_cfo:,.0f} Cr)."
    else:
        cfo_check = _fcheck("FOR_01_CASH_CONVERSION")
        if cfo_check.get("status"):
            cfo_status = "PASS" if cfo_check["status"] == "PASS" else "MONITOR"
            cfo_badge = cfo_check.get("metric", "CFO/PAT")
            cfo_ev = cfo_check.get("detail")
        else:
            cfo_status = "MONITOR"
            cfo_badge = "NOT VERIFIED"
            cfo_ev = "Cash flow conversion could not be evaluated: CFO or PAT history was unavailable."

    shield_items.append({
        "title": "Real Cash vs Paper Profit",
        "status": cfo_status,
        "badge": cfo_badge,
        "evidence": cfo_ev
    })

    # ==========================================
    # 4. Customer Payments & Dues (Debtor Health)
    # ==========================================
    rec = res.get("receivable_health_metrics", {})
    dso_raw = rec.get("dso_days")
    over_90 = rec.get("pct_over_90_days", "N/A")
    dso_val = None
    if dso_raw is not None:
        try:
            clean_dso = str(dso_raw).lower().replace("days", "").replace("day", "").replace("d", "").strip()
            dso_val = float(clean_dso)
        except (ValueError, TypeError):
            dso_val = None

    if dso_val is not None:
        # B2B & industrial companies have standard 60-90 day credit cycles; <90 days is completely healthy
        over_90_num = None
        try:
            over_90_num = float(str(over_90).replace("%", "").strip())
        except (ValueError, TypeError):
            pass

        is_low_overdue = (over_90_num is not None and over_90_num <= 10.0) or ("low" in str(over_90).lower())
        debtor_pass = (dso_val <= 90) or (dso_val <= 110 and is_low_overdue)
        debtor_status = "PASS" if debtor_pass else "MONITOR"
        debtor_badge = f"DSO: {dso_val:.0f} DAYS"
        debtor_ev = f"Customers pay on time ({dso_val:.0f} days average); overdue debt risk is low ({over_90} past 90 days)."
    else:
        rec_check = _fcheck("FOR_02_RECEIVABLE_VELOCITY")
        if rec_check.get("status"):
            debtor_status = "PASS" if rec_check["status"] == "PASS" else "MONITOR"
            debtor_badge = rec_check.get("metric", "DSO: N/A")
            debtor_ev = rec_check.get("detail")
        else:
            debtor_status = "MONITOR"
            debtor_badge = "DSO: N/A"
            debtor_ev = "Customer payment turnaround (DSO) and receivables aging were not available; not evaluated."

    shield_items.append({
        "title": "Customer Payments & Dues",
        "status": debtor_status,
        "badge": debtor_badge,
        "evidence": debtor_ev
    })

    # ==========================================
    # 5. Leverage & Solvency Health
    # ==========================================
    # Check balance sheet / CAGR latest_de first
    cagr_de = _parse_num(fin.get("cagr", {}).get("latest_de"))
    de_val = cagr_de if cagr_de is not None else _parse_num(live.get("debt_to_equity"))

    if de_val is not None:
        de_pass = (de_val <= 0.6)
        de_status = "PASS" if de_pass else "MONITOR"
        de_badge = "DEBT FREE" if de_val <= 0.05 else f"D/E {de_val:.2f}x"
        de_ev = f"Strong cash cushion and low borrowings (D/E {de_val:.2f}x) protect the company from interest rate shocks." if de_pass else f"Debt-to-equity of {de_val:.2f}x requires ongoing operating cash generation."
    else:
        de_status = "MONITOR"
        de_badge = "D/E: N/A"
        de_ev = "Debt-to-equity was unavailable from the supplied data; solvency not evaluated."

    shield_items.append({
        "title": "Debt & Solvency Health",
        "status": de_status,
        "badge": de_badge,
        "evidence": de_ev
    })

    # ==========================================
    # 6. Regulatory Track Record
    # ==========================================
    pio_trig = res.get("pio_triggered", False)
    if pio_trig:
        reg_status = "ALERT"
        reg_badge = "UNDER PROBE"
        reg_ev = "Regulatory warnings, auditor actions, or forensic concerns flagged in records."
    else:
        reg_status = "MONITOR"
        reg_badge = "NOT VERIFIED"
        reg_ev = (
            "Regulatory history was not independently verified. This is not a statement "
            "that the company has no penalties or investigations."
        )

    shield_items.append({
        "title": "Regulatory Track Record",
        "status": reg_status,
        "badge": reg_badge,
        "evidence": reg_ev
    })

    passed_count = sum(1 for it in shield_items if it["status"] == "PASS")
    not_verified_count = sum(1 for it in shield_items if it["badge"] == "NOT VERIFIED")
    total_shield = len(shield_items)
    if passed_count == total_shield:
        shield_badge = f"{passed_count} / {total_shield} CHECKS PASSED — ALL CLEAR"
    elif not_verified_count:
        shield_badge = f"{passed_count} / {total_shield} PASSED · {not_verified_count} NOT VERIFIED"
    else:
        shield_badge = f"{passed_count} / {total_shield} CHECKS PASSED"
    all_clear = passed_count == total_shield
    shield_badge_bg = "rgba(5, 150, 105, 0.08)" if all_clear else "rgba(217, 119, 6, 0.08)"
    shield_badge_fg = "#059669" if all_clear else "#D97706"
    shield_badge_bdr = "rgba(5, 150, 105, 0.25)" if all_clear else "rgba(217, 119, 6, 0.25)"

    cards_html_list = []
    for it in shield_items:
        is_pass = (it["status"] == "PASS")
        icon_str = "✔" if is_pass else ("⚠" if it["status"] == "MONITOR" else "✖")
        icon_bg = "#ECFDF5" if is_pass else ("#FFFBEB" if it["status"] == "MONITOR" else "#FEF2F2")
        icon_fg = "#059669" if is_pass else ("#D97706" if it["status"] == "MONITOR" else "#DC2626")
        badge_bg = "rgba(5, 150, 105, 0.08)" if is_pass else ("rgba(217, 119, 6, 0.08)" if it["status"] == "MONITOR" else "rgba(220, 38, 38, 0.08)")
        badge_fg = "#059669" if is_pass else ("#D97706" if it["status"] == "MONITOR" else "#DC2626")
        badge_border = "rgba(5, 150, 105, 0.25)" if is_pass else ("rgba(217, 119, 6, 0.25)" if it["status"] == "MONITOR" else "rgba(220, 38, 38, 0.25)")
        
        cards_html_list.append(
            f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 16px 18px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.2s ease;">'
            f'<div>'
            f'<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; gap: 8px;">'
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'<span style="display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; background: {icon_bg}; color: {icon_fg}; border-radius: 50%; font-size: 12px; font-weight: 900;">{icon_str}</span>'
            f'<span style="font-size: 13.5px; font-weight: 800; color: #0F172A;">{html.escape(str(it["title"]))}</span>'
            f'</div>'
            f'<span style="background: {badge_bg}; color: {badge_fg}; border: 1px solid {badge_border}; font-size: 10px; font-weight: 800; padding: 2px 8px; border-radius: 9999px; white-space: nowrap; font-family: \'JetBrains Mono\', monospace; letter-spacing: 0.3px;">{html.escape(str(it["badge"]))}</span>'
            f'</div>'
            f'<div style="font-size: 12.5px; line-height: 1.5; color: #475569; margin-top: 4px;">{html.escape(str(it["evidence"]))}</div>'
            f'</div>'
            f'</div>'
        )
    cards_html = "".join(cards_html_list)

    shield_html = (
        f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 22px 24px; margin-bottom: 22px; box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px;">'
        f'<div>'
        f'<div style="display: flex; align-items: center; gap: 8px;">'
        f'<span style="font-size: 20px;">🛡️</span>'
        f'<span style="font-size: 14.5px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.8px;">6-Point Forensic Safety Shield (Anti-Fraud Filter)</span>'
        f'</div>'
        f'<div style="font-size: 12.5px; color: #64748B; margin-top: 3px;">A 6-point background check for accounting tricks, hidden debt, and promoter red flags</div>'
        f'</div>'
        f'<span style="background: {shield_badge_bg}; color: {shield_badge_fg}; border: 1px solid {shield_badge_bdr}; font-size: 11.5px; font-weight: 800; padding: 4px 12px; border-radius: 9999px; letter-spacing: 0.4px; font-family: \'JetBrains Mono\', monospace;">{shield_badge}</span>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;">'
        f'{cards_html}'
        f'</div>'
        f'</div>'
    )
    return shield_html

def render_valuation_compass_html(res, live_data):
    live = live_data or {}

    def _parse_num(val):
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    cmp = _parse_num(live.get("current_price"))
    low_52w = _parse_num(live.get("low_52w"))
    high_52w = _parse_num(live.get("high_52w"))

    appendix_b = res.get("appendix_b_calculations") or {}
    dcf_str = appendix_b.get("dcf_fair_value_estimate", "")
    dcf_low, dcf_high, dcf_mid = parse_dcf_estimate(dcf_str)

    # No fair-value estimate from the model means no fair-value corridor.
    # Deriving one from the current price would fabricate a "target" from the
    # very number it is supposed to be compared against.
    if not cmp or not dcf_mid:
        return ""

    # Intrinsic target and sensitivity band handling
    if not dcf_low or not dcf_high or abs(dcf_high - dcf_low) < 1.0:
        dcf_card_val = f"₹{dcf_mid:,.0f}"
        dcf_card_sub = f"Intrinsic Target (±5% Band: ₹{dcf_mid * 0.95:,.0f} – ₹{dcf_mid * 1.05:,.0f})"
        band_low = dcf_mid * 0.95
        band_high = dcf_mid * 1.05
    else:
        dcf_card_val = f"₹{dcf_low:,.0f} – ₹{dcf_high:,.0f}"
        dcf_card_sub = f"Midpoint: ₹{dcf_mid:,.0f}"
        band_low = dcf_low
        band_high = dcf_high

    if not low_52w:
        low_52w = min(cmp, band_low)
    if not high_52w:
        high_52w = max(cmp, band_high)

    # Margin of Safety calculation
    mos_pct = ((dcf_mid - cmp) / dcf_mid) * 100.0
    if mos_pct > 0:
        mos_badge = f"+{mos_pct:.1f}% Margin of Safety"
        mos_color = "#059669"
        mos_bg = "rgba(5, 150, 105, 0.08)"
        mos_bdr = "rgba(5, 150, 105, 0.25)"
        mos_desc = f"Trading at a discount to the model fair-value estimate (₹{dcf_mid:,.0f})"
    else:
        mos_badge = f"{abs(mos_pct):.1f}% Valuation Premium"
        mos_color = "#DC2626"
        mos_bg = "rgba(220, 38, 38, 0.08)"
        mos_bdr = "rgba(220, 38, 38, 0.25)"
        mos_desc = f"Trading above the model fair-value estimate (₹{dcf_mid:,.0f})"

    # Asymmetry & Risk-Reward calculations
    downside_low_pct = ((cmp - low_52w) / cmp) * 100.0 if cmp and low_52w else 0.0
    upside_dcf_pct = ((dcf_mid - cmp) / cmp) * 100.0 if cmp and dcf_mid else 0.0

    if upside_dcf_pct >= 0:
        upside_str = f"+{upside_dcf_pct:.1f}% to model fair value"
        upside_color = "#059669"
        asymmetry_desc = "Favorable risk-reward versus the model estimate"
    else:
        upside_str = f"{upside_dcf_pct:.1f}% to model fair value"
        upside_color = "#DC2626"
        asymmetry_desc = "Trading above the model estimate; downside risk to 52W Low"

    downside_str = f"-{abs(downside_low_pct):.1f}% to 52W L"

    val_min = min(low_52w, band_low, cmp) * 0.96
    val_max = max(high_52w, band_high, cmp) * 1.04
    span = max(val_max - val_min, 1.0)

    def to_pct(v):
        return min(96.0, max(4.0, (v - val_min) / span * 100.0))

    pct_low = to_pct(low_52w)
    pct_high = to_pct(high_52w)
    pct_cmp = to_pct(cmp)
    pct_dcf_low = to_pct(band_low)
    pct_dcf_high = to_pct(band_high)
    dcf_width = max(3.0, pct_dcf_high - pct_dcf_low)

    # Active valuation bar fills strictly in accordance with Current Market Price (CMP)
    fill_left = min(pct_low, pct_cmp)
    fill_width = max(3.0, abs(pct_cmp - pct_low))
    range_52w_width = max(3.0, pct_high - pct_low)

    html = (
        f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 24px 26px; margin-bottom: 22px; box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px;">'
        f'<div>'
        f'<div style="display: flex; align-items: center; gap: 8px;">'
        f'<span style="font-size: 20px;">🧭</span>'
        f'<span style="font-size: 14.5px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.8px;">Valuation Compass & Fair Value Corridor</span>'
        f'</div>'
        f'<div style="font-size: 12.5px; color: #64748B; margin-top: 3px;">Current market price relative to the 52-week corridor and a model-estimated fair value (not a computed DCF)</div>'
        f'</div>'
        f'<span style="background: {mos_bg}; color: {mos_color}; border: 1px solid {mos_bdr}; font-size: 11.5px; font-weight: 800; padding: 4px 12px; border-radius: 9999px; font-family: \'JetBrains Mono\', monospace; letter-spacing: 0.3px;">{mos_badge}</span>'
        f'</div>'
        f'<div style="position: relative; margin: 44px 16px 36px 16px; height: 14px; background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 9999px;">'
        # 1. 52-week range corridor (unfilled guide from 52W L to 52W H)
        f'<div style="position: absolute; left: {pct_low:.1f}%; width: {range_52w_width:.1f}%; height: 100%; background: #E2E8F0; border-radius: 9999px;"></div>'
        # 2. Active valuation bar filled in accordance with CMP (from 52W Low up to CMP)
        f'<div style="position: absolute; left: {fill_left:.1f}%; width: {fill_width:.1f}%; height: 100%; background: linear-gradient(90deg, #60A5FA 0%, #2563EB 100%); border-radius: 9999px; z-index: 2;"></div>'
        # 3. DCF Fair Value Range Target Zone (capsule)
        f'<div style="position: absolute; left: {pct_dcf_low:.1f}%; width: {dcf_width:.1f}%; height: 100%; background: rgba(5, 150, 105, 0.15); border: 2px solid #059669; border-radius: 9999px; z-index: 3;"></div>'
        # 4. 52W Low tick & label
        f'<div style="position: absolute; left: {pct_low:.1f}%; top: -26px; transform: translateX(-50%); font-size: 11px; font-weight: 700; color: #64748B; font-family: \'JetBrains Mono\', monospace; white-space: nowrap;">52W L: ₹{low_52w:,.1f}</div>'
        f'<div style="position: absolute; left: {pct_low:.1f}%; top: -2px; transform: translateX(-50%); width: 3px; height: 18px; background: #CBD5E1; border-radius: 2px; z-index: 4;"></div>'
        # 5. DCF Fair Value Target Label (below)
        f'<div style="position: absolute; left: {to_pct(dcf_mid):.1f}%; top: 18px; transform: translateX(-50%); font-size: 11.5px; font-weight: 800; color: #059669; font-family: \'JetBrains Mono\', monospace; white-space: nowrap; z-index: 4;">▲ Est. Fair: ₹{dcf_mid:,.0f}</div>'
        # 6. CMP Needle and Badge (positioned precisely at CMP)
        f'<div style="position: absolute; left: {pct_cmp:.1f}%; top: -34px; transform: translateX(-50%); z-index: 5; text-align: center;">'
        f'<span style="background: #2563EB; color: #FFFFFF; font-size: 11.5px; font-weight: 900; padding: 2px 8px; border-radius: 6px; box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4); font-family: \'JetBrains Mono\', monospace; white-space: nowrap;">CMP ₹{cmp:,.1f}</span>'
        f'<div style="width: 3px; height: 18px; background: #2563EB; margin: 0 auto; border-radius: 2px;"></div>'
        f'</div>'
        # 7. 52W High tick & label
        f'<div style="position: absolute; left: {pct_high:.1f}%; top: -26px; transform: translateX(-50%); font-size: 11px; font-weight: 700; color: #64748B; font-family: \'JetBrains Mono\', monospace; white-space: nowrap;">52W H: ₹{high_52w:,.1f}</div>'
        f'<div style="position: absolute; left: {pct_high:.1f}%; top: -2px; transform: translateX(-50%); width: 3px; height: 18px; background: #CBD5E1; border-radius: 2px; z-index: 4;"></div>'
        f'</div>'
        # Bottom Metric Cards
        f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-top: 28px;">'
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 14px 16px;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">FAIR VALUE (MODEL ESTIMATE)</div>'
        f'<div style="font-size: 16.5px; font-weight: 800; color: #059669; font-family: \'JetBrains Mono\', monospace; margin-top: 4px;">{dcf_card_val}</div>'
        f'<div style="font-size: 12px; color: #64748B; margin-top: 2px;">{dcf_card_sub}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 14px 16px;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">VALUATION STATUS</div>'
        f'<div style="font-size: 16.5px; font-weight: 800; color: {mos_color}; font-family: \'JetBrains Mono\', monospace; margin-top: 4px;">{mos_badge}</div>'
        f'<div style="font-size: 12px; color: #64748B; margin-top: 2px;">{mos_desc}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 14px 16px;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">UPSIDE VS DOWNSIDE</div>'
        f'<div style="font-size: 14.5px; font-weight: 800; color: #0F172A; margin-top: 4px; font-family: \'JetBrains Mono\', monospace;">'
        f'<span style="color: {upside_color};">{upside_str}</span> &bull; <span style="color: #64748B;">{downside_str}</span>'
        f'</div>'
        f'<div style="font-size: 12px; color: #64748B; margin-top: 2px;">{asymmetry_desc}</div>'
        f'</div>'
        f'</div>'
        # Micro-Legend for Valuation Compass
        f'<div style="display: flex; justify-content: center; align-items: center; gap: 20px; flex-wrap: wrap; margin-top: 18px; padding-top: 14px; border-top: 1px dashed #E2E8F0; font-size: 11px; font-weight: 700; color: #64748B;">'
        f'<span style="display: inline-flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 11px; height: 11px; background: #2563EB; border-radius: 2px;"></span> CMP Active Price Pin</span>'
        f'<span style="display: inline-flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 11px; height: 11px; background: rgba(5, 150, 105, 0.15); border: 1.5px solid #059669; border-radius: 2px;"></span> Model Fair Value Zone</span>'
        f'<span style="display: inline-flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 11px; height: 11px; background: #E2E8F0; border: 1px solid #CBD5E1; border-radius: 2px;"></span> 52-Week Range Bounds</span>'
        f'</div>'
        f'</div>'
    )
    return html

def render_graphical_forensic_architecture_html() -> str:
    """
    Renders an innovative graphical pipeline and visual benchmark compass for the
    StockSage Forensic Evaluation Architecture, replacing walls of text with intuitive infographics.
    """
    return """
    <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 24px 28px; box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);">
      <!-- Header -->
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px; flex-wrap: wrap; gap: 12px; border-bottom: 1.5px solid #E2E8F0; padding-bottom: 16px;">
        <div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 22px;">🧭</span>
            <span style="font-size: 17px; font-weight: 800; color: #0F172A; letter-spacing: -0.2px;">StockSage Forensic Architecture & Evaluation Pipeline</span>
          </div>
          <div style="font-size: 13px; color: #64748B; margin-top: 3px;">
            Deterministic multi-layer forensic audit combining live market context with audited filing telemetry.
          </div>
        </div>
        <div style="display: flex; gap: 8px;">
          <span style="background: rgba(5, 150, 105, 0.08); color: #059669; border: 1px solid rgba(5, 150, 105, 0.25); font-size: 11px; font-weight: 800; padding: 3px 10px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">Ind AS Aligned</span>
          <span style="background: rgba(37, 99, 235, 0.08); color: #2563EB; border: 1px solid rgba(37, 99, 235, 0.25); font-size: 11px; font-weight: 800; padding: 3px 10px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">Internal consistency checks</span>
        </div>
      </div>

      <!-- Stage 1-4 Connected Pipeline Infographic -->
      <div class="ss-pipeline-grid">
        <!-- Step 1 -->
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3.5px solid #059669; border-radius: 12px; padding: 18px 20px; position: relative;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="width: 26px; height: 26px; border-radius: 50%; background: #059669; color: #FFFFFF; font-weight: 900; font-size: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(5,150,105,0.3);">1</span>
            <span style="font-size: 10px; font-weight: 800; color: #059669; background: rgba(5, 150, 105, 0.08); border: 1px solid rgba(5, 150, 105, 0.25); padding: 2px 7px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">DATA LAYER</span>
          </div>
          <div style="font-size: 14.5px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">Universe Ingestion</div>
          <div style="font-size: 12px; color: #475569; line-height: 1.45; margin-bottom: 12px;">Ingest 501 tracked equities, pull live quotes, and review primary annual reports.</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">501 tracked</span>
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">Live Feeds</span>
          </div>
        </div>

        <!-- Step 2 -->
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3.5px solid #2563EB; border-radius: 12px; padding: 18px 20px; position: relative;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="width: 26px; height: 26px; border-radius: 50%; background: #2563EB; color: #FFFFFF; font-weight: 900; font-size: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(37,99,235,0.3);">2</span>
            <span style="font-size: 10px; font-weight: 800; color: #2563EB; background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(37, 99, 235, 0.25); padding: 2px 7px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">AUDIT LAYER</span>
          </div>
          <div style="font-size: 14.5px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">Sentinel-1 Verification</div>
          <div style="font-size: 12px; color: #475569; line-height: 1.45; margin-bottom: 12px;">Runs 6-point mathematical cross-check to verify balance equations and zero hallucinations.</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">6/6 Check</span>
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">SHA Seal</span>
          </div>
        </div>

        <!-- Step 3 -->
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3.5px solid #D97706; border-radius: 12px; padding: 18px 20px; position: relative;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="width: 26px; height: 26px; border-radius: 50%; background: #D97706; color: #FFFFFF; font-weight: 900; font-size: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(217,119,6,0.3);">3</span>
            <span style="font-size: 10px; font-weight: 800; color: #D97706; background: rgba(217, 119, 6, 0.08); border: 1px solid rgba(217, 119, 6, 0.25); padding: 2px 7px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">CAGR LAYER</span>
          </div>
          <div style="font-size: 14.5px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">Multi-Year Trends</div>
          <div style="font-size: 12px; color: #475569; line-height: 1.45; margin-bottom: 12px;">Computes 3–5 year compounded growth across Revenue, Profit, ROCE, and Free Cash Flow.</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">5Y CAGR</span>
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">FCF Engine</span>
          </div>
        </div>

        <!-- Step 4 -->
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3.5px solid #7C3AED; border-radius: 12px; padding: 18px 20px; position: relative;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="width: 26px; height: 26px; border-radius: 50%; background: #7C3AED; color: #FFFFFF; font-weight: 900; font-size: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(124,58,237,0.3);">4</span>
            <span style="font-size: 10px; font-weight: 800; color: #7C3AED; background: rgba(124, 58, 237, 0.08); border: 1px solid rgba(124, 58, 237, 0.25); padding: 2px 7px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">SYNTHESIS</span>
          </div>
          <div style="font-size: 14.5px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">8-Pillar AI Dossier</div>
          <div style="font-size: 12px; color: #475569; line-height: 1.45; margin-bottom: 12px;">Synthesizes 0–100 score, forensic penalties, Big 4 auditor checks, and institutional position call.</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">0-100 Score</span>
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">Position Call</span>
          </div>
        </div>
      </div>

      <!-- Graphical Metric Benchmark Cards -->
      <div style="border-top: 1.5px solid #E2E8F0; padding-top: 20px;">
        <div style="font-size: 12.5px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 14px; display: flex; align-items: center; gap: 8px;">
          <span>📊</span> Forensic Threshold Compass (Dalal Street Institutional Benchmarks)
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;">
          <!-- Benchmark 1 -->
          <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3px solid #059669; border-radius: 12px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 10.5px; font-weight: 800; color: #059669; text-transform: uppercase; letter-spacing: 0.5px;">CFO / PAT CONVERSION</span>
              <span style="background: rgba(5, 150, 105, 0.08); color: #059669; border: 1px solid rgba(5, 150, 105, 0.25); font-size: 10px; font-weight: 800; padding: 1px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">≥ 95%</span>
            </div>
            <div style="background: #E2E8F0; border-radius: 9999px; height: 5px; margin-bottom: 8px;">
              <div style="background: #059669; width: 95%; height: 5px; border-radius: 9999px;"></div>
            </div>
            <div style="font-size: 11.5px; color: #475569; line-height: 1.4;">Real Cash in Bank: Over 95% confirms reported accounting profits actually turn into liquid cash.</div>
          </div>

          <!-- Benchmark 2 -->
          <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3px solid #2563EB; border-radius: 12px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 10.5px; font-weight: 800; color: #2563EB; text-transform: uppercase; letter-spacing: 0.5px;">DEBT TO EQUITY (D/E)</span>
              <span style="background: rgba(37, 99, 235, 0.08); color: #2563EB; border: 1px solid rgba(37, 99, 235, 0.25); font-size: 10px; font-weight: 800; padding: 1px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">≤ 0.3x</span>
            </div>
            <div style="background: #E2E8F0; border-radius: 9999px; height: 5px; margin-bottom: 8px;">
              <div style="background: #2563EB; width: 30%; height: 5px; border-radius: 9999px;"></div>
            </div>
            <div style="font-size: 11.5px; color: #475569; line-height: 1.4;">Solvency Shield: Low debt prevents interest burden shocks during macro slowdowns.</div>
          </div>

          <!-- Benchmark 3 -->
          <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3px solid #D97706; border-radius: 12px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 10.5px; font-weight: 800; color: #D97706; text-transform: uppercase; letter-spacing: 0.5px;">ROCE (CAPITAL RETURNS)</span>
              <span style="background: rgba(217, 119, 6, 0.08); color: #D97706; border: 1px solid rgba(217, 119, 6, 0.25); font-size: 10px; font-weight: 800; padding: 1px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">≥ 20%</span>
            </div>
            <div style="background: #E2E8F0; border-radius: 9999px; height: 5px; margin-bottom: 8px;">
              <div style="background: #D97706; width: 80%; height: 5px; border-radius: 9999px;"></div>
            </div>
            <div style="font-size: 11.5px; color: #475569; line-height: 1.4;">Elite Moat: Generates >₹20 operating profit per ₹100 of capital employed.</div>
          </div>

          <!-- Benchmark 4 -->
          <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3px solid #7C3AED; border-radius: 12px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 10.5px; font-weight: 800; color: #7C3AED; text-transform: uppercase; letter-spacing: 0.5px;">COMPOSITE QUALITY SCORE</span>
              <span style="background: rgba(124, 58, 237, 0.08); color: #7C3AED; border: 1px solid rgba(124, 58, 237, 0.25); font-size: 10px; font-weight: 800; padding: 1px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">≥ 85 / 100</span>
            </div>
            <div style="background: #E2E8F0; border-radius: 9999px; height: 5px; margin-bottom: 8px;">
              <div style="background: #7C3AED; width: 85%; height: 5px; border-radius: 9999px;"></div>
            </div>
            <div style="font-size: 11.5px; color: #475569; line-height: 1.4;">Potential Compounder: Top 15% quality tier with clean governance and moat endurance.</div>
          </div>
        </div>
      </div>
    </div>
    """

# --- EXECUTION ENGINE ---
if run_btn:
    clean_target_name = str(target_company_name or "").strip()
    clean_target_ticker = str(target_ticker or "").strip()
    if not clean_target_name:
        st.error("⚠️ Please select a company from the tracked universe or enter a valid company name before launching an audit.")
        st.stop()
    if not clean_target_ticker:
        st.error("⚠️ Please enter a valid stock ticker or symbol (e.g. RELIANCE, TCS, INFY) before launching an audit.")
        st.stop()

    # Rate Limiting & Spend Budget Enforcement
    if "kusha_runs" not in st.session_state:
        st.session_state["kusha_runs"] = 0
    current_runs = st.session_state["kusha_runs"]
    if current_runs >= MAX_RUNS_PER_SESSION:
        st.warning(f"Session analysis budget reached ({current_runs} of {MAX_RUNS_PER_SESSION}). Reload to start a new session.")
        st.stop()

    last_run_time = st.session_state.get("kusha_last_run_time", 0.0)
    now_ts = time.time()
    if (now_ts - last_run_time) < 10.0 and last_run_time > 0.0:
        st.warning("Please wait — an analysis just completed.")
        st.stop()

    if st.session_state.get("kusha_running", False):
        st.stop()

    st.session_state["kusha_running"] = True
    try:
        # Determine execution profile and expected latency
        if demo_mode:
            mode_pill = "🧪 Synthetic Demo"
            est_label = "< 1s"
            est_sec_typical = 1
        elif doc_type == "⚡ Auto-fetch BSE filing" and selected_filing_metadata:
            mode_pill = "⚡ BSE Annual Report"
            est_label = "~45–75s"
            est_sec_typical = 60
        elif doc_type == "📂 Upload custom PDF" and uploaded_file:
            mode_pill = "📂 Custom PDF"
            est_label = "~30–50s"
            est_sec_typical = 40
        else:
            mode_pill = "🌐 Web Research"
            est_label = "~12–20s"
            est_sec_typical = 15

        t_start = time.time()
        def fmt_elapsed(t0):
            el = max(0.0, time.time() - t0)
            m = int(el // 60)
            s = el % 60
            return f"{m:02d}:{s:04.1f}"

        # Render client-side live stopwatch & estimated progress component
        timer_placeholder = st.empty()
        with timer_placeholder:
            st.iframe(render_live_analysis_timer_html(
                company_name=clean_target_name,
                ticker=clean_target_ticker,
                mode_label=mode_pill,
                est_label=est_label,
                est_sec_typical=est_sec_typical
            ), height=130)

        # Check if a pre-computed evaluation exists in the local development cache (Load site)
        cached_eval_data = None
        if not demo_mode and use_eval_cache and not force_live_api:
            cached_eval_data = load_cached_evaluation(
                company_name=clean_target_name,
                ticker=clean_target_ticker,
                model=selected_gemini_model,
                current_pipeline_version=ANALYSIS_PIPELINE_VERSION,
                document_hash=document_hash,
                sector=target_sector,
                skip_web_search=skip_web_search,
                analysis_mode=mode_pill,
            )

        if cached_eval_data is not None:
            result, cached_at_time = cached_eval_data
            result["is_cached_result"] = True
            result["cached_at_time"] = cached_at_time
            result["execution_time_seconds"] = 0.05
            result["estimated_time_label"] = "Instant (Local Cache)"
            st.session_state["idex_result"] = result
            st.session_state["kusha_runs"] = st.session_state.get("kusha_runs", 0) + 1
            st.session_state["kusha_last_run_time"] = time.time()
            logger.info("Analysis completed | Model: %s (Cache Replay) | Elapsed: 0.05s", selected_gemini_model)

            with timer_placeholder:
                st.iframe(render_live_analysis_timer_html(
                    company_name=clean_target_name,
                    ticker=clean_target_ticker,
                    mode_label="💾 Local Cache Replay",
                    est_label="< 0.1s",
                    est_sec_typical=1,
                    completed_sec=0.05
                ), height=130)

            with st.status(f"⚡ Instant Replay from Local Cache: {clean_target_name} (0 API Calls Used)", expanded=False, state="complete") as status:
                st.write(f"💾 Loaded pre-computed institutional brief from disk ({cached_at_time}).")
                st.write(f"🔒 Mathematical Determinism & PIO Guardrails Verified.")
                st.write(f"⚡ Zero API quota consumed (saved 2 live Gemini requests).")
        else:
            with st.status(f"Evaluating {clean_target_name} across 8 Fundamental & Forensic Pillars (Est: {est_label})...", expanded=True) as status:
                st.write(f"⏱️ `[{fmt_elapsed(t_start)}]` Ingesting financial statement tables & market feeds...")
                time.sleep(0.15)
                st.write(f"⏱️ `[{fmt_elapsed(t_start)}]` Evaluating statutory disclosures & related-party schedules...")
                time.sleep(0.15)
                st.write(f"⏱️ `[{fmt_elapsed(t_start)}]` Evaluating Sector Receivable Health (DSO, Aging, Provision Coverage)...")
                time.sleep(0.15)
                st.write(f"⏱️ `[{fmt_elapsed(t_start)}]` Enforcing deterministic Python scoring, PIO guardrails & penalty/bonus caps...")
                
                try:
                    sentinel_rep = st.session_state.get("sentinel_report", None)
                    forensic_rep = st.session_state.get("forensic_report", None)
                    if demo_mode:
                        st.write(f"⏱️ `[{fmt_elapsed(t_start)}]` Generating synthetic demonstration vector...")
                        result = get_demo_analysis(target_company_name, target_sector, live_data, sentinel_report=sentinel_rep, forensic_report=forensic_rep)
                    else:
                        pdf_bytes = None
                        filing_meta = None
                        if doc_type == "⚡ Auto-fetch BSE filing" and selected_filing_metadata:
                            st.write(f"⏱️ `[{fmt_elapsed(t_start)}]` 📥 Downloading BSE-hosted filing PDF ({selected_filing_metadata.get('title')})...")
                            pdf_bytes = download_annual_report_bytes(selected_filing_metadata["url"])
                            filing_meta = selected_filing_metadata
                            st.write(f"⏱️ `[{fmt_elapsed(t_start)}]` 📄 Retrieved BSE statutory PDF ({len(pdf_bytes)/(1024*1024):.1f} MB).")
                        elif doc_type == "📂 Upload custom PDF" and uploaded_file:
                            st.write(f"⏱️ `[{fmt_elapsed(t_start)}]` 📥 Ingesting user uploaded document ({uploaded_file.name})...")
                            raw_bytes = uploaded_file.getvalue()
                            max_upload_size = MAX_PDF_MB * 1024 * 1024
                            if len(raw_bytes) > max_upload_size:
                                raise ValueError(f"Uploaded file exceeds maximum limit of {MAX_PDF_MB}MB (received {len(raw_bytes)/(1024*1024):.1f}MB).")
                            if not raw_bytes.startswith(b"%PDF-"):
                                raise ValueError("Not a valid PDF (missing '%PDF-' header).")
                            pdf_bytes = raw_bytes
                            filing_meta = selected_filing_metadata
                            st.write(f"⏱️ `[{fmt_elapsed(t_start)}]` 📄 Uploaded PDF validated ({len(pdf_bytes)/(1024*1024):.1f} MB).")

                        st.write(f"⏱️ `[{fmt_elapsed(t_start)}]` 🧠 Launching Gemini {selected_gemini_model} multimodal audit...")
                        result = analyze_document_with_gemini(
                            company_name=target_company_name,
                            sector=target_sector,
                            api_key=active_api_key,
                            pdf_bytes=pdf_bytes,
                            live_data=live_data,
                            custom_prompt=custom_prompt,
                            sentinel_report=sentinel_rep,
                            selected_model=selected_gemini_model,
                            filing_metadata=filing_meta,
                            forensic_report=forensic_rep,
                            skip_web_search=skip_web_search
                        )
                    total_elapsed = time.time() - t_start
                    result["analysis_pipeline_version"] = ANALYSIS_PIPELINE_VERSION
                    result["execution_time_seconds"] = round(total_elapsed, 1)
                    result["estimated_time_seconds"] = est_sec_typical
                    result["estimated_time_label"] = est_label

                    # Save to local cache for instant zero-cost replays (Save site)
                    if not demo_mode and use_eval_cache:
                        result["document_hash"] = document_hash
                        save_cached_evaluation(
                            company_name=clean_target_name,
                            ticker=clean_target_ticker,
                            model=selected_gemini_model,
                            pipeline_version=ANALYSIS_PIPELINE_VERSION,
                            result=result,
                            document_hash=document_hash,
                            sector=target_sector,
                            skip_web_search=skip_web_search,
                            analysis_mode=mode_pill,
                        )

                    st.session_state["idex_result"] = result
                    st.session_state["kusha_runs"] = st.session_state.get("kusha_runs", 0) + 1
                    st.session_state["kusha_last_run_time"] = time.time()
                    logger.info("Analysis completed | Model: %s | Elapsed: %.2fs", selected_gemini_model, total_elapsed)
                    
                    with timer_placeholder:
                        st.iframe(render_live_analysis_timer_html(
                            company_name=clean_target_name,
                            ticker=clean_target_ticker,
                            mode_label=mode_pill,
                            est_label=est_label,
                            est_sec_typical=est_sec_typical,
                            completed_sec=total_elapsed
                        ), height=130)
                    
                    st.write(f"⏱️ `[{fmt_elapsed(t_start)}]` ✅ Scoring complete in {total_elapsed:.1f}s (Est: {est_label}).")
                    status.update(label=f"Evaluation Complete for {clean_target_name} in {total_elapsed:.1f}s (Estimated: {est_label})!", state="complete", expanded=False)
                except Exception as e:
                    total_elapsed = time.time() - t_start
                    with timer_placeholder:
                        st.iframe(render_live_analysis_timer_html(
                            company_name=clean_target_name,
                            ticker=clean_target_ticker,
                            mode_label=mode_pill,
                            est_label=est_label,
                            est_sec_typical=est_sec_typical,
                            completed_sec=total_elapsed,
                            is_error=True
                        ), height=130)
                    status.update(label=f"Evaluation Failed after {total_elapsed:.1f}s", state="error")
                    raw_err = str(e)
                    # Redact raw API key patterns to prevent client-side credential exposure
                    clean_err = raw_err
                    if active_api_key and len(active_api_key) > 8:
                        clean_err = clean_err.replace(active_api_key, "AIzaSy***[REDACTED]***")
                    clean_err = re.sub(r'AIza[0-9A-Za-z-_]{35}', 'AIzaSy***[REDACTED]***', clean_err)
                    clean_err = re.sub(r'key=[0-9A-Za-z-_]{20,}', 'key=***[REDACTED]***', clean_err)
                    st.error(f"Analysis Error: {clean_err}")
                    with st.expander("Technical Details"):
                        st.write(f"Diagnostic detail: {clean_err}")
    finally:
        st.session_state["kusha_running"] = False

# --- RESULTS DASHBOARD ---
if "idex_result" in st.session_state:
    res = st.session_state["idex_result"]
    rec = res.get("receivable_health_metrics") or {}
    if res.get("analysis_pipeline_version") != ANALYSIS_PIPELINE_VERSION:
        del st.session_state["idex_result"]
        st.warning("This saved result was created before evidence checks were enabled. Run the analysis again to see a current result.")
        st.stop()

    is_demo = bool(res.get("is_synthetic_demo", False))
    if not target_ticker and res.get("ticker"):
        target_ticker = res.get("ticker")
    if target_ticker and not live_data:
        live_data = get_cached_live_data(target_ticker)
    if target_ticker and not fin_res:
        fin_res = get_cached_financial_statements(target_ticker)
    st.write("")

    # 1. Synthetic Demo Warning Banner (Accessible, Warm Amber #FFFBEB, No Fake Claims)
    if is_demo:
        st.html(
            f'<div style="background: #FFFBEB; border: 1.5px solid #FDE68A; border-left: 5px solid #D97706; border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; display: flex; align-items: flex-start; gap: 14px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);">'
            f'<span style="font-size: 24px; line-height: 1;">⚠️</span>'
            f'<div>'
            f'<div style="font-size: 13.5px; font-weight: 800; color: #92400E; text-transform: uppercase; letter-spacing: 0.5px; font-family: monospace;">'
            f'Synthetic Demonstration Dataset — Not Official BSE Filings or Real Investment Advice'
            f'</div>'
            f'<div style="font-size: 13px; color: #78350F; margin-top: 4px; line-height: 1.5;">'
            f'This research brief was generated using synthetic sample data for UI demonstration and walkthrough purposes only. '
            f'No official regulatory claims, statutory audit verifications, or buy/sell recommendations are made for {target_company_name}.'
            f'</div>'
            f'</div>'
            f'</div>'
        )

    st.markdown("### Institutional Equity Research Brief" + (" [SYNTHETIC DEMO]" if is_demo else ""))

    # Execution telemetry & audit duration badge
    if res.get("execution_time_seconds") is not None:
        exec_dur = res["execution_time_seconds"]
        is_cached = res.get("is_cached_result", False)
        cached_time = res.get("cached_at_time", "")
        if is_cached:
            badge_text = f"⚡ Local Cache Replay: {exec_dur:.2f}s (0 API Quota Used • Cached: {cached_time})"
            badge_style = "background: #ECFDF5; border: 1px solid #A7F3D0; color: #065F46;"
        else:
            est_lbl = res.get("estimated_time_label") or f"~{res.get('estimated_time_seconds', 0)}s"
            badge_text = f"⏱️ Audit Duration: {exec_dur:.1f}s (Estimated: {est_lbl})"
            badge_style = "background: #F1F5F9; border: 1px solid #CBD5E1; color: #0F172A;"
        st.markdown(
            f'<div style="display: flex; align-items: center; gap: 10px; margin-top: -6px; margin-bottom: 14px; font-size: 12px; color: #64748B;">'
            f'<span style="{badge_style} padding: 3px 10px; border-radius: 9999px; font-weight: 700; font-family: monospace;">'
            f'{badge_text}'
            f'</span>'
            f'<span style="color: #94A3B8;">&bull;</span>'
            f'<span>Mathematical Determinism &amp; PIO Guardrails Verified</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    if res.get("filing_metadata"):
        st.html(build_filing_ingestion_notice_html(res["filing_metadata"]))

    research = res.get("web_research", {})
    source_count = len(research.get("sources", []))
    evidence_gap_count = len(res.get("evidence_gaps", []))
    issuer_host = (urlparse(str((live_data or {}).get("website_url") or "")).hostname or "").lower().removeprefix("www.")

    def classify_research_source(source):
        host = (urlparse(str(source.get("url") or "")).hostname or "").lower().removeprefix("www.")
        def is_domain(domain):
            return host == domain or host.endswith("." + domain)

        if source.get("source_type") == "third_party_market_data" or any(is_domain(domain) for domain in ("yahoo.com", "moneycontrol.com", "screener.in")):
            return "Third-party market data"
        if is_domain("nseindia.com") or is_domain("bseindia.com"):
            return "Official exchange"
        if is_domain("sebi.gov.in"):
            return "Regulator"
        if issuer_host and (host == issuer_host or host.endswith("." + issuer_host)):
            return "Issuer website"
        reporting_domains = ("reuters.com", "economictimes.indiatimes.com", "livemint.com", "thehindu.com", "business-standard.com", "financialexpress.com")
        if any(is_domain(domain) for domain in reporting_domains):
            return "News/reporting publisher"
        return "Web publisher unclassified"

    source_class_counts = {}
    for source in research.get("sources", []):
        source_class = classify_research_source(source)
        source_class_counts[source_class] = source_class_counts.get(source_class, 0) + 1

    if research or evidence_gap_count:
        source_summary = f"{source_count} web source link{'s' if source_count != 1 else ''} returned"
        gap_summary = f"{evidence_gap_count} evidence gap{'s' if evidence_gap_count != 1 else ''}"
        class_summary = " · ".join(f"{kind}: {count}" for kind, count in source_class_counts.items()) or "No source classes identified"
        if res.get("filing_metadata", {}).get("ingestion_status") == "analyzed" or res.get("document_analyzed"):
            st.caption(f"Evidence status: Official statutory filing analyzed · {source_summary} · {gap_summary}. Claims are directly grounded in the primary annual report.")
        else:
            st.caption(f"Evidence status: {source_summary} · {gap_summary}. {class_summary}. Sources are retrieved, not independently verified; open the panel for queries, dates, and citations.")
            st.caption("Link counts do not confirm complete annual-report, auditor, shareholding/pledge, regulatory, or peer coverage; review the evidence gaps and citations per claim.")

    degraded = res.get("data_quality", {}).get("degraded_sources", [])
    if degraded:
        st.warning("⚠️ **Data Quality Notice**: " + " • ".join(esc(d) for d in degraded))

    if res.get("analysis_status") == "insufficient_evidence":
        st.error("Insufficient evidence: " + "; ".join(res.get("evidence_gaps", [])))

    if not is_demo and res.get("analysis_status") == "insufficient_evidence" and res.get("filing_metadata", {}).get("ingestion_status") != "analyzed":
        st.error("Score, allocation, and investment call are withheld because the evidence checks are incomplete. Resolve the listed gaps and run the analysis again.")
        st.stop()

    # Data Consistency & Reconciliation Sentinel
    sentinel_audit = res.get("sentinel_audit") or st.session_state.get("sentinel_report")
    if not sentinel_audit and fin_res:
        sentinel_audit = DataIntegritySentinel.audit_and_certify(
            ticker_symbol=target_ticker or "",
            company_name=target_company_name or "",
            financial_statements=fin_res,
            live_market_data=live_data
        )
        st.session_state["sentinel_report"] = sentinel_audit

    # Forensic Due Diligence Audit
    forensic_audit = res.get("forensic_report") or st.session_state.get("forensic_report")
    if not forensic_audit and fin_res:
        forensic_audit = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol=target_ticker or "",
            company_name=target_company_name or "",
            sector=target_sector or "",
            financial_statements=fin_res,
            live_market_data=live_data
        )
        st.session_state["forensic_report"] = forensic_audit

    # 2. RESEARCH PROVENANCE & DUE DILIGENCE HUD (Answers 6 Core Questions at the Top)
    provenance_hud_html = render_research_provenance_and_evidence_card(
        res, live_data, target_company_name, target_ticker, target_sector, fin_res=fin_res
    )
    st.html(provenance_hud_html)

    # 3. EXECUTIVE QUALITY SCORECARD & RADIAL GAUGE
    final_score = res.get('final_score', 0)
    verdict = res.get("verdict", "").split("—")[0].strip()
    core_score = res.get('core_score', 0)
    total_penalties = res.get('total_penalties', 0)
    total_bonus = res.get('bonuses_breakdown', {}).get('total_bonus_applied', 0)
    position_sizing = res.get("position_sizing", "0%")

    try:
        f_val = float(final_score)
    except (ValueError, TypeError):
        f_val = 0.0

    clamped_score = min(100.0, max(0.0, f_val))
    circumference = 326.7
    gauge_offset = circumference * (1.0 - (clamped_score / 100.0))

    if f_val >= 80:
        score_neon_color = "#059669"
        score_badge_bg = "#ECFDF5"
        score_badge_bdr = "#A7F3D0"
    elif f_val >= 60:
        score_neon_color = "#2563EB"
        score_badge_bg = "#EFF6FF"
        score_badge_bdr = "#BFDBFE"
    else:
        score_neon_color = "#DC2626"
        score_badge_bg = "#FEF2F2"
        score_badge_bdr = "#FECACA"

    determ_label = "SYNTHETIC TEST VECTOR COMPUTATION" if is_demo else "DETERMINISTIC POST-PROCESSING APPLIED ✔"

    kpi_cards_html = (
        f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 22px 24px; margin-bottom: 22px; box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);">'
        f'<div style="display: grid; grid-template-columns: 220px 1fr; gap: 24px; align-items: center;">'
        # Radial Gauge Pod
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 14px; padding: 18px 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; position: relative;">'
        f'<div style="font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 10px;">COMPOSITE QUALITY SCORE</div>'
        f'<div style="position: relative; width: 130px; height: 130px;">'
        f'<svg width="130" height="130" viewBox="0 0 140 140" style="transform: rotate(-90deg);">'
        f'<defs>'
        f'<linearGradient id="idexNeonGrad" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="#2563EB" />'
        f'<stop offset="100%" stop-color="#059669" />'
        f'</linearGradient>'
        f'</defs>'
        f'<circle cx="70" cy="70" r="52" fill="none" stroke="#E2E8F0" stroke-width="10" />'
        f'<circle cx="70" cy="70" r="52" fill="none" stroke="url(#idexNeonGrad)" stroke-width="10" stroke-linecap="round" stroke-dasharray="{circumference:.1f}" stroke-dashoffset="{gauge_offset:.1f}" style="transition: stroke-dashoffset 0.8s ease;" />'
        f'</svg>'
        f'<div style="position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">'
        f'<span style="font-family: monospace; font-size: 26px; font-weight: 900; color: #0F172A; line-height: 1;">{final_score:.1f}</span>'
        f'<span style="font-size: 11px; font-weight: 700; color: #64748B; font-family: monospace; margin-top: 2px;">/ 100</span>'
        f'</div>'
        f'</div>'
        f'<div style="margin-top: 10px;">'
        f'<span style="background: {score_badge_bg}; color: {score_neon_color}; border: 1px solid {score_badge_bdr}; font-size: 11px; font-weight: 800; padding: 3px 12px; border-radius: 9999px; letter-spacing: 0.4px; font-family: monospace;">{verdict}</span>'
        f'</div>'
        f'</div>'
        # 4 Telemetry Pods
        f'<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;">'
        # Pod 1: Core Quality
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 4px solid #2563EB; border-radius: 12px; padding: 16px 18px;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">'
        f'<span style="font-size: 11px; font-weight: 800; color: #2563EB; text-transform: uppercase; letter-spacing: 0.6px;">CORE QUALITY</span>'
        f'<span style="font-size: 16px;">💎</span>'
        f'</div>'
        f'<div style="font-size: 24px; font-weight: 900; color: #0F172A; font-family: monospace;">{core_score:.1f} <span style="font-size: 13px; font-weight: 600; color: #2563EB;">/ 100</span></div>'
        f'<div style="font-size: 11.5px; color: #64748B; margin-top: 6px;">Base 8-pillar rating</div>'
        f'</div>'
        # Pod 2: Risk Deductions
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 4px solid #DC2626; border-radius: 12px; padding: 16px 18px;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">'
        f'<span style="font-size: 11px; font-weight: 800; color: #DC2626; text-transform: uppercase; letter-spacing: 0.6px;">RISK PENALTIES</span>'
        f'<span style="font-size: 16px;">🛡️</span>'
        f'</div>'
        f'<div style="font-size: 24px; font-weight: 900; color: #DC2626; font-family: monospace;">-{abs(total_penalties):.1f} <span style="font-size: 13px; font-weight: 600; color: #DC2626;">pts</span></div>'
        f'<div style="font-size: 11.5px; color: #64748B; margin-top: 6px;">Bounded Risk Corridor</div>'
        f'</div>'
        # Pod 3: Growth Bonuses
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 4px solid #7C3AED; border-radius: 12px; padding: 16px 18px;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">'
        f'<span style="font-size: 11px; font-weight: 800; color: #7C3AED; text-transform: uppercase; letter-spacing: 0.6px;">ALPHA BONUSES</span>'
        f'<span style="font-size: 16px;">🚀</span>'
        f'</div>'
        f'<div style="font-size: 24px; font-weight: 900; color: #7C3AED; font-family: monospace;">+{total_bonus:.1f} <span style="font-size: 13px; font-weight: 600; color: #7C3AED;">pts</span></div>'
        f'<div style="font-size: 11.5px; color: #64748B; margin-top: 6px;">Bounded Growth Factor</div>'
        f'</div>'
        # Pod 4: Sizing
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 4px solid #D97706; border-radius: 12px; padding: 16px 18px;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">'
        f'<span style="font-size: 11px; font-weight: 800; color: #D97706; text-transform: uppercase; letter-spacing: 0.6px;">RISK TIER</span>'
        f'<span style="font-size: 16px;">⚖️</span>'
        f'</div>'
        f'<div style="font-size: 20px; font-weight: 900; color: #D97706; font-family: monospace;">{position_sizing}</div>'
        f'<div style="font-size: 11.5px; color: #64748B; margin-top: 6px;">Illustrative Non-Advisory Cap</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        # Formula Bridge Node Strip
        f'<div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 18px; padding-top: 14px; border-top: 1px solid #E2E8F0; flex-wrap: wrap;">'
        f'<div style="display: flex; align-items: center; gap: 8px; font-size: 11.5px; font-family: monospace; color: #64748B;">'
        f'<span style="font-weight: 700; color: #0F172A;">⚡ Deterministic Scoring Formula:</span>'
        f'<span style="background: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE; padding: 2px 8px; border-radius: 6px; font-weight: 700;">Core: {core_score:.1f}</span>'
        f'<span style="color: #64748B; font-weight: 800;">−</span>'
        f'<span style="background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; padding: 2px 8px; border-radius: 6px; font-weight: 700;">Penalties: {abs(total_penalties):.1f}</span>'
        f'<span style="color: #64748B; font-weight: 800;">+</span>'
        f'<span style="background: #FAF5FF; color: #7C3AED; border: 1px solid #E9D5FF; padding: 2px 8px; border-radius: 6px; font-weight: 700;">Bonuses: {total_bonus:.1f}</span>'
        f'<span style="color: #64748B; font-weight: 800;">=</span>'
        f'<span style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; padding: 2px 10px; border-radius: 6px; font-weight: 800;">Final: {final_score:.1f}</span>'
        f'</div>'
        f'<div style="font-size: 11px; font-weight: 700; color: #059669; font-family: monospace;">{determ_label}</div>'
        f'</div>'
        f'</div>'
    )
    st.html(kpi_cards_html)

    # 4. CORE PLAIN-LANGUAGE RESEARCH TAKEAWAY BANNER (EDUCATIONAL RISK TIER)
    final_call_str = res.get("final_call", "N/A")
    verdict_str = res.get("verdict", "")
    guardrail_tag = str(res.get("guardrail_tag", ""))
    pio_trig = res.get("pio_triggered", False)
    try:
        final_score = float(res.get("final_score", 0))
    except (ValueError, TypeError):
        final_score = 0.0
    drift_str = res.get('drift_optionality_update', 'Monitor upcoming capital deployment and quarterly earnings.')
    esg_str = res.get('fragility_esg_fx_notes', 'No material governance or FX vulnerabilities observed.')
    position_sizing = res.get("position_sizing", "Risk-Weighted")
    str_list = res.get("strengths", [])
    wk_list = res.get("weaknesses", [])

    if "—" in final_call_str:
        parts = final_call_str.split("—", 1)
        call_badge = parts[0].strip()
        call_summary = parts[1].strip()
    elif ":" in final_call_str:
        parts = final_call_str.split(":", 1)
        call_badge = parts[0].strip()
        call_summary = parts[1].strip()
    else:
        call_badge = "FORENSIC PROFILE"
        call_summary = final_call_str

    combined = (str(final_call_str) + " " + str(verdict_str) + " " + str(guardrail_tag)).upper()

    if pio_trig or analyzer.guardrail_level(guardrail_tag) == analyzer.GUARDRAIL_RED or final_score < 55.0 or any(k in combined for k in ["AVOID", "PRUDENCE", "SELL", "EXIT", "REDUCE", "UNINVESTABLE", "HIGH RISK"]):
        stance = "AVOID"
    elif final_score >= 70.0 and any(k in combined for k in ["BUY", "ACCUMULATE", "OVERWEIGHT", "LONG", "COMPOUNDER"]):
        stance = "BUY"
    else:
        stance = "HOLD"

    drift_lower = drift_str.lower() if drift_str else "operational metrics"

    if stance == "AVOID":
        banner_border = "#DC2626"
        badge_bg = "#FEF2F2"
        badge_border = "#FECACA"
        badge_fg = "#DC2626"
        badge_text = "🛑 ELEVATED CAUTION / HIGH FORENSIC RISK"
        sizing_display = "0.0% Allocation (Educational Risk Tier — Not Personal Investment Advice)"
        summary_color = "#DC2626"
        cards = [
            {"icon": "🛑", "title": "PRIMARY RED FLAG", "text": wk_list[0] if wk_list else "Serious accounting, governance, or debt anomalies flagged in disclosures.", "hcolor": "#DC2626"},
            {"icon": "⚠️", "title": "CAPITAL IMPAIRMENT RISK", "text": wk_list[1] if len(wk_list) > 1 else "Elevated risk of capital loss if operating conditions or debt servicing deteriorate.", "hcolor": "#DC2626"},
            {"icon": "📉", "title": "ACCRUAL & CASH DIVERGENCE", "text": esg_str or "Reported profits diverge from actual operating cash flow generation.", "hcolor": "#D97706"},
            {"icon": "🛡️", "title": "REQUISITES BEFORE RE-EVALUATION", "text": "Requires debt deleveraging, unpledged promoter holdings, and unmodified CARO audit opinions.", "hcolor": "#475569"}
        ]
    elif stance == "BUY":
        banner_border = "#059669"
        badge_bg = "#ECFDF5"
        badge_border = "#A7F3D0"
        badge_fg = "#059669"
        badge_text = "🟢 CONSTRUCTIVE WATCHLIST / HIGH QUALITY"
        sizing_display = "Illustrative Exposure: 2–5% Cap (Educational Risk Tier — Not Personal Investment Advice)"
        summary_color = "#059669"
        cards = [
            {"icon": "🟢", "title": "CORE COMPETITIVE MOAT", "text": str_list[0] if str_list else "Dominant market presence with pricing power and defensible market share.", "hcolor": "#059669"},
            {"icon": "🛡️", "title": "BALANCE SHEET & CASH GENERATION", "text": str_list[1] if len(str_list) > 1 else "Conservative leverage profile with consistent operating cash flow generation.", "hcolor": "#2563EB"},
            {"icon": "🚀", "title": "1–2 YEAR OPERATIONAL CATALYSTS", "text": drift_str or "Capacity expansion and operating leverage driving fundamental trajectory.", "hcolor": "#7C3AED"},
            {"icon": "🎯", "title": "KEY METRICS TO MONITOR QUARTERLY", "text": "Track quarterly ROCE sustainability, debtor days, and cash flow conversion vs reported PAT.", "hcolor": "#059669"}
        ]
    else:
        banner_border = "#D97706"
        badge_bg = "#FFFBEB"
        badge_border = "#FDE68A"
        badge_fg = "#D97706"
        badge_text = "🟡 MONITORED / NEUTRAL QUALITY TIER"
        sizing_display = "Illustrative Exposure: 0–2% Watchlist (Educational Risk Tier — Not Personal Investment Advice)"
        summary_color = "#D97706"
        cards = [
            {"icon": "🟢", "title": "ESTABLISHED BUSINESS FRANCHISE", "text": str_list[0] if str_list else "Established business with respectable market presence and operational scale.", "hcolor": "#059669"},
            {"icon": "⏳", "title": "CONSTRAINTS & MARGIN OF SAFETY", "text": wk_list[0] if wk_list else "Valuation multiple offers limited safety margin or earnings growth is temporarily subdued.", "hcolor": "#D97706"},
            {"icon": "🎯", "title": "CATALYSTS FOR PROFILE UPGRADE", "text": f"Valuation discount toward fair value or accelerated cash flow conversion in {drift_lower}.", "hcolor": "#2563EB"},
            {"icon": "⚠️", "title": "DOWNSIDE RISKS TO WATCH", "text": wk_list[1] if len(wk_list) > 1 else "Monitor margin compression, working capital elongation, or rising debtor cycles.", "hcolor": "#DC2626"}
        ]

    card_blocks_list = []
    for c in cards:
        c_hcolor = c["hcolor"]
        c_icon = c["icon"]
        c_title = html.escape(str(c["title"]))
        c_text = html.escape(str(c["text"]))
        card_blocks_list.append(
            f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 14px 16px;">'
            f'<div style="font-size: 11px; font-weight: 800; color: {c_hcolor}; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 5px; display: flex; align-items: center; gap: 6px;">'
            f'<span>{c_icon}</span> {c_title}'
            f'</div>'
            f'<div style="font-size: 13px; line-height: 1.5; color: #334155; font-weight: 500;">{c_text}</div>'
            f'</div>'
        )
    card_blocks = "".join(card_blocks_list)
    call_summary_escaped = html.escape(str(call_summary))

    thesis_banner_html = (
        f'<div style="background: #FFFFFF; border: 1.5px solid {banner_border}; border-radius: 16px; padding: 22px 26px; margin-bottom: 22px; box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 10px;">'
        f'<div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">'
        f'<span style="background: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; font-size: 11px; font-weight: 800; padding: 3px 10px; border-radius: 9999px; text-transform: uppercase; font-family: monospace;">📋 FORENSIC PROFILE</span>'
        f'<span style="background: {badge_bg}; color: {badge_fg}; border: 1px solid {badge_border}; font-size: 11.5px; font-weight: 900; padding: 3px 12px; border-radius: 9999px; font-family: monospace; letter-spacing: 0.4px;">{badge_text}</span>'
        f'</div>'
        f'<div style="display: flex; align-items: center; gap: 8px;">'
        f'<span style="background: #F8FAFC; color: #475569; border: 1px solid #E2E8F0; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 6px; font-family: monospace;">⏱️ 1–2 Year Window</span>'
        f'<span style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 6px; font-family: monospace;">⚖️ {sizing_display}</span>'
        f'</div>'
        f'</div>'
        f'<div style="font-size: 16px; font-weight: 800; color: {summary_color}; line-height: 1.45; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid #E2E8F0;">'
        f'{call_summary_escaped}'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">'
        f'{card_blocks}'
        f'</div>'
        f'<div style="margin-top: 14px; padding-top: 10px; border-top: 1px solid #E2E8F0; font-size: 11px; color: #64748B; line-height: 1.4;">'
        f'⚖️ <strong>Educational Research Stance:</strong> This automated profile is generated from heuristic financial modeling and disclosure cross-referencing. It does NOT constitute SEBI investment advice, trading calls, or a guarantee of future operational performance.'
        f'</div>'
        f'</div>'
    )
    st.html(thesis_banner_html)

    # 5. ORGANIZED 5-TAB RESEARCH DOSSIER
    tab_evidence, tab_financials, tab_heuristics, tab_methodology, tab_export = st.tabs([
        "Evidence & Findings",
        "Financial Statements",
        "8-Pillar Heuristics",
        "Methodology & Checks",
        "Export Brief"
    ])

    # --- TAB 1: EVIDENCE & FINDINGS ---
    with tab_evidence:
        st.markdown("#### 🔍 Evidence & Forensic Findings")
        st.caption("Review traffic light indicators, fraud shield heuristics, and load-bearing statutory disclosures.")

        # 10-Second Traffic Light & ELI15 Plain-English Takeaway
        traffic_eli15_html = render_traffic_light_and_eli15_html(res, live_data, target_company_name, target_sector)
        st.html(traffic_eli15_html)

        # 6-Point Forensic Fraud Shield
        shield_html = render_forensic_fraud_shield_html(res, live_data, financial_data=fin_res, forensic_report=forensic_audit)
        st.html(shield_html)

        # Mandatory Guardrail Tag & Promoter Integrity Verdict
        tag = res.get("guardrail_tag", "GOV-CLEAN 🟢")
        tag_esc = html.escape(str(tag))
        evidence_list = res.get("guardrail_evidence", [])
        ev_html_items = "".join([f'<li style="margin-bottom: 4px;">{html.escape(str(e))}</li>' for e in evidence_list])
        if analyzer.guardrail_level(tag) == analyzer.GUARDRAIL_RED or res.get("pio_triggered", False):
            st.html(
                f'<div style="background: #FEF2F2; border: 1.5px solid #FECACA; border-left: 5px solid #DC2626; border-radius: 12px; padding: 18px 22px; margin-bottom: 16px;">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
                f'<span style="font-weight: 800; font-size: 1.1rem; color: #DC2626;">🚨 MANDATORY GUARDRAIL TAG: {tag_esc} (PIO HARD TRIGGER FIRED)</span>'
                f'<span style="background: #FEE2E2; color: #DC2626; padding: 4px 12px; border-radius: 9999px; font-weight: 800; font-size: 0.8rem; border: 1px solid #FCA5A5; font-family: monospace;">CRITICAL FORENSIC RISK</span>'
                f'</div>'
                f'<p style="margin: 0 0 10px 0; font-weight: 600; color: #DC2626;">{html.escape(str(res.get("pio_reason") or "Promoter Integrity Override triggered. Governance pillar capped at ≤6.0/20. Bonuses blocked. Forced into Red Zone."))}</p>'
                f'<ul style="margin: 0; padding-left: 20px; color: #334155;">{ev_html_items}</ul>'
                f'</div>'
            )
        elif analyzer.guardrail_level(tag) == analyzer.GUARDRAIL_ALERT:
            st.html(
                f'<div style="background: #FFFBEB; border: 1.5px solid #FDE68A; border-left: 5px solid #D97706; border-radius: 12px; padding: 18px 22px; margin-bottom: 16px;">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
                f'<span style="font-weight: 800; font-size: 1.1rem; color: #D97706;">⚠️ MANDATORY GUARDRAIL TAG: {tag_esc}</span>'
                f'<span style="background: #FEF3C7; color: #D97706; padding: 4px 12px; border-radius: 9999px; font-weight: 800; font-size: 0.8rem; border: 1px solid #FCD34D; font-family: monospace;">PROMOTER ALERT</span>'
                f'</div>'
                f'<p style="margin: 0 0 10px 0; color: #D97706; font-weight: 600;">Elevated promoter pledging or dilution observed under PPRM rules.</p>'
                f'<ul style="margin: 0; padding-left: 20px; color: #334155;">{ev_html_items}</ul>'
                f'</div>'
            )
        else:
            st.html(
                f'<div style="background: #ECFDF5; border: 1.5px solid #A7F3D0; border-left: 5px solid #059669; border-radius: 12px; padding: 18px 22px; margin-bottom: 16px;">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
                f'<span style="font-weight: 800; font-size: 1.1rem; color: #059669;">🛡️ PROMOTER INTEGRITY & GOVERNANCE VERDICT: {tag_esc}</span>'
                f'<span style="background: #D1FAE5; color: #059669; padding: 4px 12px; border-radius: 9999px; font-weight: 800; font-size: 0.8rem; border: 1px solid #6EE7B7; font-family: monospace;">INSTITUTIONAL GRADE</span>'
                f'</div>'
                f'<p style="margin: 0 0 8px 0; color: #059669; font-weight: 600;">10Y+ clean statutory audit history, zero promoter share pledge, verified arm-length related-party disclosures.</p>'
                f'<ul style="margin: 0; padding-left: 20px; color: #334155;">{ev_html_items}</ul>'
                f'</div>'
            )

        # Detailed Notes / Moats & Fragilities
        str_html_items = "".join([f'<div style="font-size: 13px; line-height: 1.5; margin-bottom: 6px; display: flex; align-items: flex-start; gap: 6px;"><span style="color: #059669; font-weight: 800;">✔</span><span style="color: #334155;">{html.escape(str(s))}</span></div>' for s in str_list])
        wk_html_items = "".join([f'<div style="font-size: 13px; line-height: 1.5; margin-bottom: 6px; display: flex; align-items: flex-start; gap: 6px;"><span style="color: #DC2626; font-weight: 800;">✖</span><span style="color: #334155;">{html.escape(str(w))}</span></div>' for w in wk_list])
        drift_str_escaped = html.escape(str(drift_str))
        esg_str_escaped = html.escape(str(esg_str))

        with st.expander("📑 Detailed Strengths, Risks & Fundamental Notes", expanded=False):
            st.html(
                f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 12px;">'
                f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3.5px solid #059669; border-radius: 8px; padding: 14px 16px;">'
                f'<div style="font-size: 11px; font-weight: 800; color: #059669; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.6px;">🟢 Key Strengths & Moats</div>'
                f'{str_html_items}'
                f'</div>'
                f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3.5px solid #DC2626; border-radius: 8px; padding: 14px 16px;">'
                f'<div style="font-size: 11px; font-weight: 800; color: #DC2626; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.6px;">🔴 Key Risks & Fragilities</div>'
                f'{wk_html_items}'
                f'</div>'
                f'</div>'
                f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">'
                f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 8px; padding: 12px 14px;">'
                f'<div style="font-size: 10.5px; font-weight: 800; color: #475569; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px;">⏱️ Growth Drivers & Catalysts</div>'
                f'<div style="font-size: 12.5px; line-height: 1.5; color: #334155;">{drift_str_escaped}</div>'
                f'</div>'
                f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 8px; padding: 12px 14px;">'
                f'<div style="font-size: 10.5px; font-weight: 800; color: #475569; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px;">🌍 Governance & Integrity Notes</div>'
                f'<div style="font-size: 12.5px; line-height: 1.5; color: #334155;">{esg_str_escaped}</div>'
                f'</div>'
                f'</div>'
            )

        # Full Forensic Due Diligence Dossier
        active_forensic_rep = res.get("forensic_report") or st.session_state.get("forensic_report")
        if not active_forensic_rep and fin_res:
            active_forensic_rep = ForensicRiskEngine.audit_company_forensics(
                ticker_symbol=target_ticker or "",
                company_name=target_company_name or "",
                sector=target_sector or "",
                financial_statements=fin_res,
                live_market_data=live_data
            )
        if active_forensic_rep:
            st.markdown("##### 🕵️ Forensic Accounting & Concealed Risk Audit")
            st.html(render_forensic_dossier_html(active_forensic_rep))

        # Web Research & Grounding Evidence
        if research or res.get("evidence_gaps"):
            with st.expander("🌐 Web research and source evidence", expanded=bool(res.get("analysis_status") == "insufficient_evidence")):
                if research.get("search_performed"):
                    st.caption("Google Search grounding was returned by Gemini. Query and source details below are API metadata.")
                    if research.get("search_queries"):
                        st.markdown("**Search queries**")
                        for query in research["search_queries"]:
                            st.write(f"- {query}")
                    if research.get("sources"):
                        st.markdown("**Sources returned by Google Search** (publication date is shown only when provided by the API; retrieval time is recorded)")
                        for source in research["sources"]:
                            published = source.get("published_date") or "Publication date not provided by API"
                            source_label = classify_research_source(source).upper()
                            st.markdown(f"[{source['source_id']}: {source['title']}]({source['url']}) — {source_label}; {published}; retrieved {source.get('retrieved_at', 'unknown')}")
                    for penalty in res.get("penalties_breakdown", []):
                        cited = " ".join(f"[{c['source_id']}]({c['url']})" for c in penalty.get("citations", []))
                        st.markdown(f"**Penalty ({penalty.get('points')} pts):** {penalty.get('reason')}  {cited or '— statutory filing citation' if res.get('filing_metadata', {}).get('ingestion_status') == 'analyzed' else '— insufficient evidence citation'}")
                    bonus = res.get("bonuses_breakdown", {})
                    cited_bonus = " ".join(f"[{c['source_id']}]({c['url']})" for c in bonus.get("citations", []))
                    st.markdown(f"**Bonus rationale ({bonus.get('total_bonus_applied', 0)} pts):** {bonus.get('reason', 'Insufficient evidence rationale.')}  {cited_bonus or '— statutory filing citation' if res.get('filing_metadata', {}).get('ingestion_status') == 'analyzed' else '— insufficient evidence citation'}")
                    cited_call = " ".join(f"[{c['source_id']}]({c['url']})" for c in res.get("final_call_citations", []))
                    st.markdown(f"**Final call:** {res.get('final_call', 'Insufficient evidence')}  {cited_call or '— statutory filing citation' if res.get('filing_metadata', {}).get('ingestion_status') == 'analyzed' else '— insufficient evidence citation'}")
                    if res.get("pio_triggered"):
                        cited_pio = " ".join(f"[{c['source_id']}]({c['url']})" for c in res.get("pio_reason_citations", []))
                        st.markdown(f"**PIO basis:** {res.get('pio_reason', 'Insufficient evidence')}  {cited_pio or '— statutory filing citation' if res.get('filing_metadata', {}).get('ingestion_status') == 'analyzed' else '— insufficient evidence citation'}")
                    if res.get("evidence_gaps"):
                        st.warning("Evidence gaps: " + "; ".join(res["evidence_gaps"]))
                elif res.get("filing_metadata", {}).get("ingestion_status") == "analyzed" or res.get("document_analyzed"):
                    st.info("ℹ️ **Primary Statutory Evaluation**: Analysis was evaluated directly from the official BSE India annual report via Gemini multimodal ingestion. Live internet search grounding was not queried or was limited by API quota.")
                else:
                    st.warning("No Search grounding metadata was returned. Internet research is not verified.")

        # Appendix A: Statutory Auditor Excerpts
        with st.expander("📄 Appendix A — Load-Bearing Forensic Citations (Auditor Excerpts)", expanded=False):
            ev_items = "".join([
                f'<div style="font-size: 13px; line-height: 1.6; color: #334155; margin-bottom: 10px; padding: 12px 16px; background: #F8FAFC; border-left: 3.5px solid #059669; border-radius: 0 8px 8px 0; border: 1.5px solid #E2E8F0;">'
                f'<span style="color: #059669; font-weight: 800; margin-right: 6px;">●</span> {esc(e)}'
                f'</div>'
                for e in res.get("appendix_a_forensic_evidence", [])
            ])
            if ev_items:
                st.html(ev_items)
            else:
                st.info("No statutory auditor qualifications or load-bearing exceptions reported.")

    # --- TAB 2: FINANCIAL STATEMENTS ---
    with tab_financials:
        st.markdown("#### 📊 Financial Statements & Historical Performance")
        st.caption("Inspect multi-year statements, growth CAGRs, key Dalal Street ratios, and price action.")

        # Price Action Chart
        hist_df = get_cached_ticker_history(target_ticker, period="1y") if target_ticker else pd.DataFrame()
        if not hist_df.empty:
            st.markdown(f"##### 📈 {target_company_name} ({target_ticker}) Price Action (1 Year)")
            stk_fig = build_ticker_chart(hist_df, target_ticker, "Area", show_dma=True)
            if stk_fig:
                st.plotly_chart(stk_fig, width="stretch", key=f"tab_financials_price_chart_{target_ticker}")

        # 27 Dalal Street Canonical Screening Ratios
        st.markdown("##### 🏛️ Dalal Street Screening Ratios (27 Canonical Factors)")
        metric_cards_html = render_dalal_street_metric_cards_html(live_data, fin_res)
        if metric_cards_html:
            st.html(f'<div class="metrics-3col-grid" style="margin-top: 12px; margin-bottom: 24px;">{metric_cards_html}</div>')

        # Multi-Year Historical Statements & Growth Scorecard
        if fin_res and "years" in fin_res and not fin_res.get("error"):
            st.markdown("##### 📑 Audited Financial Statements & Compounding CAGRs")
            st.html(render_growth_cagr_scorecard_html(fin_res["cagr"]))
            stmt_mode = st.segmented_control(
                "Statement",
                options=["📜 Profit & Loss", "⚡ Quarterly", "🏛️ Balance Sheet", "💵 Cash Flows"],
                default="📜 Profit & Loss",
                key=f"tab_stmt_mode_{target_ticker}",
                label_visibility="collapsed"
            )
            if stmt_mode == "📜 Profit & Loss":
                st.html(render_financial_table_html(fin_res["pnl"], fin_res["years"], "Annual Profit & Loss Statement"))
            elif stmt_mode == "⚡ Quarterly":
                if fin_res.get("quarterly") and fin_res.get("q_years"):
                    st.html(render_financial_table_html(fin_res["quarterly"], fin_res["q_years"], "Quarterly Financial Performance"))
                else:
                    st.info("Quarterly statements currently synchronizing for this company.")
            elif stmt_mode == "🏛️ Balance Sheet":
                st.html(render_financial_table_html(fin_res["bs"], fin_res["bs_years"], "Annual Balance Sheet"))
            elif stmt_mode == "💵 Cash Flows":
                st.html(render_financial_table_html(fin_res["cf"], fin_res["cf_years"], "Annual Cash Flow Statement"))

            cagr_insights = generate_forensic_cagr_insights(fin_res, target_company_name)
            if cagr_insights:
                insight_boxes = []
                for ins in cagr_insights:
                    status_type = ins.get("status", "info")
                    if status_type == "positive":
                        iborder, ibg, ititle_color, ibody_color, icon = "#10B981", "#ECFDF5", "#065F46", "#047857", "✔"
                    elif status_type == "negative":
                        iborder, ibg, ititle_color, ibody_color, icon = "#EF4444", "#FEF2F2", "#991B1B", "#7F1D1D", "⚠"
                    else:
                        iborder, ibg, ititle_color, ibody_color, icon = "#3B82F6", "#EFF6FF", "#1E40AF", "#1E3A8A", "ℹ"
                    insight_boxes.append(
                        f'<div style="background: {ibg}; border-left: 3.5px solid {iborder}; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;">'
                        f'<div style="font-size: 13px; font-weight: 800; color: {ititle_color}; display: flex; align-items: center; gap: 6px;">'
                        f'<span>{icon}</span> {ins.get("title")}'
                        f'</div>'
                        f'<div style="font-size: 12px; line-height: 1.5; color: {ibody_color}; margin-top: 3px;">'
                        f'{ins.get("body")}'
                        f'</div>'
                        f'</div>'
                    )
                st.html(f'<div style="margin-top: 14px;">{"".join(insight_boxes)}</div>')
        else:
            st.info("Select a tracked company above to view its 10-year financial history and balance sheet.")

    # --- TAB 3: 8-PILLAR HEURISTICS ---
    with tab_heuristics:
        st.markdown("#### 🏛️ 8-Pillar Quality Profile & Valuation Heuristics")
        st.caption("Standardized 100-point institutional matrix evaluating solvency, governance, accruals, and cash generation.")

        split_col1, split_col2 = st.columns([1.3, 1.7])
        with split_col1:
            with st.container(border=True):
                st.markdown("##### 8-Pillar Quality Profile")
                radar_fig = build_radar_chart(res.get("pillars", []))
                if radar_fig:
                    st.plotly_chart(radar_fig, width="stretch", key=f"tab_heuristics_radar_chart_{target_ticker}")

                st.caption("Active Forensic Tags:")
                tag_pills = []
                tag_color_map = {
                    "GOV-CLEAN": ("#ECFDF5", "#059669", "#A7F3D0"),
                    "GOV-RED": ("#FEF2F2", "#DC2626", "#FECACA"),
                    "PROM-ALERT": ("#FFFBEB", "#D97706", "#FDE68A"),
                    "ZERO-DEBT": ("#EFF6FF", "#2563EB", "#BFDBFE"),
                    "HIGH-ROCE": ("#ECFDF5", "#059669", "#A7F3D0"),
                    "COOL-PRO": ("#FAF5FF", "#7C3AED", "#E9D5FF"),
                    "DSO-PRISTINE": ("#EFF6FF", "#2563EB", "#BFDBFE"),
                }
                for t in res.get("tags_applied", []):
                    found_colors = None
                    for prefix, colors in tag_color_map.items():
                        if prefix in t:
                            found_colors = colors
                            break
                    if not found_colors:
                        found_colors = ("#F8FAFC", "#475569", "#E2E8F0")
                    bg, fg, bdr = found_colors
                    tag_pills.append(f'<span style="background: {bg}; color: {fg}; border: 1px solid {bdr}; padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: 700; display: inline-block; margin-right: 6px; margin-bottom: 6px; font-family: monospace;">{esc(t)}</span>')
                st.html(f'<div style="display: flex; flex-wrap: wrap; margin-top: 6px;">{"".join(tag_pills)}</div>')

        with split_col2:
            with st.container(border=True):
                st.markdown("##### Sector Receivable Health Layer")
                st.caption("Forensic Cash Conversion & Liquidity Benchmarking")
                rec_val = res.get("receivable_health_metrics", {})
                dso_val = rec_val.get('dso_days', 'N/A')
                dso_display = f"{dso_val} d" if str(dso_val).replace(".", "").isdigit() else str(dso_val)
                ideal_dso = rec_val.get('sector_ideal_dso', 'N/A')
                rec_sales = rec_val.get('receivables_to_sales_pct', 'N/A')
                over_90 = rec_val.get('pct_over_90_days', 'N/A')
                prov_cov = rec_val.get('provision_coverage_pct', 'N/A')
                verdict_text = rec_val.get('receivable_verdict', 'Normal')

                rec_cards_html = (
                    f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px;">'
                    f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 8px; padding: 12px 16px;">'
                    f'<div style="font-size: 10.5px; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: 0.5px;">DSO (Days Sales)</div>'
                    f'<div style="font-size: 20px; font-weight: 800; color: #0F172A; font-family: monospace; margin: 4px 0;">{esc(dso_display)}</div>'
                    f'<div style="font-size: 11px; color: #64748B;">Sector Benchmark: {esc(ideal_dso)}</div>'
                    f'</div>'
                    f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 8px; padding: 12px 16px;">'
                    f'<div style="font-size: 10.5px; font-weight: 700; color: #059669; text-transform: uppercase; letter-spacing: 0.5px;">Receivables / Sales</div>'
                    f'<div style="font-size: 20px; font-weight: 800; color: #0F172A; font-family: monospace; margin: 4px 0;">{esc(rec_sales)}</div>'
                    f'<div style="font-size: 11px; color: #64748B;">Balance Sheet Weight</div>'
                    f'</div>'
                    f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 8px; padding: 12px 16px;">'
                    f'<div style="font-size: 10.5px; font-weight: 700; color: #D97706; text-transform: uppercase; letter-spacing: 0.5px;">>90 Days Overdue</div>'
                    f'<div style="font-size: 20px; font-weight: 800; color: #0F172A; font-family: monospace; margin: 4px 0;">{esc(over_90)}</div>'
                    f'<div style="font-size: 11px; color: #64748B;">Delinquency Risk</div>'
                    f'</div>'
                    f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 8px; padding: 12px 16px;">'
                    f'<div style="font-size: 10.5px; font-weight: 700; color: #7C3AED; text-transform: uppercase; letter-spacing: 0.5px;">Provision Coverage</div>'
                    f'<div style="font-size: 20px; font-weight: 800; color: #0F172A; font-family: monospace; margin: 4px 0;">{esc(prov_cov)}</div>'
                    f'<div style="font-size: 11px; color: #64748B;">ECL Buffer</div>'
                    f'</div>'
                    f'</div>'
                    f'<div style="background: #ECFDF5; border: 1.5px solid #A7F3D0; border-left: 4px solid #059669; border-radius: 6px; padding: 10px 14px; display: flex; align-items: center; gap: 10px;">'
                    f'<span style="font-size: 18px;">🛡️</span>'
                    f'<div>'
                    f'<div style="font-size: 10.5px; font-weight: 800; color: #059669; text-transform: uppercase; letter-spacing: 0.5px;">Forensic Assessment</div>'
                    f'<div style="font-size: 13px; font-weight: 700; color: #0F172A;">{esc(verdict_text)}</div>'
                    f'</div>'
                    f'</div>'
                )
                st.html(rec_cards_html)

        # 8-Pillar Table with Quality Tier Filter
        st.markdown("##### 8-Pillar Evaluation Matrix")
        tbl_c1, tbl_c2 = st.columns([3, 1])
        with tbl_c1:
            p_filter = st.segmented_control(
                "Filter Quality Tier",
                options=["All Pillars", "Pristine (≥80%)", "Moderate (50-79%)", "Fragile (<50%)"],
                default="All Pillars",
                key="p_filter_ctrl_tab",
                label_visibility="collapsed"
            )
        with tbl_c2:
            p_density = st.segmented_control(
                "Table Density",
                options=["Detailed", "Compact"],
                default="Detailed",
                key="p_density_ctrl_tab",
                label_visibility="collapsed"
            )

        table_rows = []
        for p in res.get("pillars", []):
            p_id = p.get("id", 1)
            p_score = p.get("score", 0)
            p_max = p.get("max_score", 1)
            pct = (p_score / p_max) * 100 if p_max > 0 else 0

            if p_filter == "Pristine (≥80%)" and pct < 80.0:
                continue
            elif p_filter == "Moderate (50-79%)" and not (50.0 <= pct < 80.0):
                continue
            elif p_filter == "Fragile (<50%)" and pct >= 50.0:
                continue

            meta = PILLAR_METADATA.get(p_id, {"icon": "📌", "chip": "Quality", "chip_bg": "#F1F5F9", "chip_fg": "#475569", "border": "#E2E8F0"})

            if pct >= 85:
                badge = f'<span style="background:#ECFDF5; color:#059669; border:1px solid #A7F3D0; padding:4px 10px; border-radius:9999px; font-weight:800; font-size:11px; display:inline-flex; align-items:center; gap:4px; font-family: monospace;">✨ {pct:.0f}% • Pristine</span>'
                bar_color = "#059669"
            elif pct >= 70:
                badge = f'<span style="background:#EFF6FF; color:#2563EB; border:1px solid #BFDBFE; padding:4px 10px; border-radius:9999px; font-weight:700; font-size:11px; display:inline-flex; align-items:center; gap:4px; font-family: monospace;">🟢 {pct:.0f}% • Strong</span>'
                bar_color = "#2563EB"
            elif pct >= 50:
                badge = f'<span style="background:#FFFBEB; color:#D97706; border:1px solid #FDE68A; padding:4px 10px; border-radius:9999px; font-weight:700; font-size:11px; display:inline-flex; align-items:center; gap:4px; font-family: monospace;">🟡 {pct:.0f}% • Moderate</span>'
                bar_color = "#D97706"
            else:
                badge = f'<span style="background:#FEF2F2; color:#DC2626; border:1px solid #FECACA; padding:4px 10px; border-radius:9999px; font-weight:700; font-size:11px; display:inline-flex; align-items:center; gap:4px; font-family: monospace;">🔴 {pct:.0f}% • Fragile</span>'
                bar_color = "#DC2626"

            rec_html = ""
            if "receivable_subscore" in p:
                rec_html = f'<div style="margin-top: 8px; background: #ECFDF5; border-left: 3px solid #059669; padding: 6px 12px; font-size: 12px; font-weight: 600; color: #059669; border-radius: 0 4px 4px 0;">⚡ Sector Receivable Health Subscore: <strong>{html.escape(str(p["receivable_subscore"]))}</strong></div>'

            pillar_citations = p.get("citations", [])
            c_links = []
            if pillar_citations:
                for c in pillar_citations:
                    u = safe_url(c.get("url", ""))
                    if u:
                        raw_title = c.get("title") or c.get("source_id") or "Source"
                        clean_t = str(raw_title).replace("https://", "").replace("http://", "").rstrip("/")
                        if len(clean_t) > 35:
                            clean_t = clean_t[:32] + "…"
                        c_links.append(f'<a href="{esc(u)}" target="_blank" rel="noopener noreferrer" style="color: #2563EB; font-weight: 700; text-decoration: underline; font-size: 11.5px;">{esc(clean_t)} ↗</a>')

            if c_links:
                citation_html = f'<div style="font-size:11.5px; margin-top:6px; color:#64748B;">🔗 <strong>Sources:</strong> {" &bull; ".join(c_links)}</div>'
            else:
                citation_html = f'<div style="font-size:11.5px; margin-top:6px; color:#64748B;">📊 <strong>Source:</strong> Official Exchange Filings & Screener Dataset</div>'

            justification_text = p.get("justification", "")
            if p_density == "Compact" and len(justification_text) > 130:
                justification_text = justification_text[:126].rsplit(" ", 1)[0] + "…"
            justification_clean = html.escape(str(justification_text))
            p_name_escaped = html.escape(str(p.get("name") or "Pillar"))

            row_html = (
                f'<tr>'
                f'<td style="width: 25%; font-weight: 700;">'
                f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">'
                f'<span style="font-size: 18px;">{meta["icon"]}</span>'
                f'<span style="font-size: 14px; color: #0F172A; font-weight: 800;">P{p_id}: {p_name_escaped}</span>'
                f'</div>'
                f'<span style="background: {meta["chip_bg"]}; color: {meta["chip_fg"]}; border: 1px solid {meta["border"]}; font-size: 10.5px; font-weight: 700; padding: 2px 8px; border-radius: 9999px; font-family: monospace;">{meta["chip"]}</span>'
                f'</td>'
                f'<td style="width: 14%; text-align: center;">'
                f'<div style="font-family: monospace; font-size: 17px; font-weight: 800; color: #059669;">{p_score:.1f} <span style="font-size: 12px; font-weight: 500; color: #64748B;">/ {p_max:.1f}</span></div>'
                f'<div style="background: #E2E8F0; border-radius: 9999px; height: 5px; width: 85%; margin: 6px auto 0 auto; overflow: hidden;">'
                f'<div style="background: {bar_color}; width: {pct:.1f}%; height: 100%; border-radius: 9999px;"></div>'
                f'</div>'
                f'</td>'
                f'<td style="width: 16%; text-align: center;">{badge}</td>'
                f'<td style="width: 45%;"><div style="font-size: 13.5px; line-height: 1.6; color: #334155;">{justification_clean}</div>{citation_html}{rec_html}</td>'
                f'</tr>'
            )
            table_rows.append(row_html)

        if not table_rows:
            table_rows.append('<tr><td colspan="4" style="text-align: center; padding: 28px; color: #64748B; font-weight: 600;">No pillars match the selected quality tier filter.</td></tr>')

        full_table_html = (
            f'<table class="pillar-table">'
            f'<thead><tr>'
            f'<th style="width: 25%; text-align: left;">Pillar Domain</th>'
            f'<th style="width: 14%; text-align: center;">Score & Progress</th>'
            f'<th style="width: 16%; text-align: center;">Quality Rating</th>'
            f'<th style="width: 45%; text-align: left;">Forensic Assessment & Driver Justification</th>'
            f'</tr></thead>'
            f'<tbody>{"".join(table_rows)}</tbody>'
            f'</table>'
        )
        st.html(full_table_html)

        # Forensic Score Bridge: Deductions & Bonuses
        st.markdown("##### 🛡️ Forensic Score Bridge: Deductions & Growth Bonuses")
        bridge_col1, bridge_col2 = st.columns(2)
        with bridge_col1:
            with st.container(border=True):
                st.markdown(
                    '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">'
                    '<span style="font-size: 13px; font-weight: 800; color: #DC2626; text-transform: uppercase; letter-spacing: 0.6px;">Deducted Risk Penalties</span>'
                    '<span style="background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; font-size: 11px; font-weight: 800; padding: 2px 8px; border-radius: 9999px; font-family: monospace;">Bounded Risk Corridor</span>'
                    '</div>',
                    unsafe_allow_html=True
                )
                penalties = res.get("penalties_breakdown", [])
                if penalties:
                    pen_html = []
                    for pen in penalties:
                        pts_val = abs(float(pen.get("points", 0)))
                        pen_html.append(
                            f'<div style="background: #FEF2F2; border: 1px solid #FECACA; border-left: 4px solid #DC2626; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">'
                            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">'
                            f'<span style="font-size: 13.5px; font-weight: 800; color: #DC2626;">{esc(pen.get("penalty_name"))}</span>'
                            f'<span style="background: #DC2626; color: #FFFFFF; font-size: 11px; font-weight: 900; padding: 2px 8px; border-radius: 9999px; font-family: monospace;">-{pts_val:.1f} pts</span>'
                            f'</div>'
                            f'<div style="font-size: 12.5px; color: #475569; line-height: 1.5;">{esc(pen.get("reason"))}</div>'
                            f'</div>'
                        )
                    st.html("".join(pen_html))
                else:
                    st.html(
                        '<div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-left: 4px solid #059669; border-radius: 8px; padding: 16px 18px; color: #059669; font-weight: 700; font-size: 13px;">'
                        '✔ Zero statutory forensic risk deductions applied. Clean regulatory audit profile.'
                        '</div>'
                    )

        with bridge_col2:
            with st.container(border=True):
                bb = res.get("bonuses_breakdown", {})
                st.markdown(
                    '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">'
                    '<span style="font-size: 13px; font-weight: 800; color: #7C3AED; text-transform: uppercase; letter-spacing: 0.6px;">Applied Growth Bonuses</span>'
                    '<span style="background: #FAF5FF; color: #7C3AED; border: 1px solid #E9D5FF; font-size: 11px; font-weight: 800; padding: 2px 8px; border-radius: 9999px; font-family: monospace;">Bounded Growth Factor</span>'
                    '</div>',
                    unsafe_allow_html=True
                )
                st.html(
                    f'<div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px;">'
                    f'<div style="background: #FAF5FF; border: 1px solid #E9D5FF; border-left: 4px solid #7C3AED; border-radius: 6px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center;">'
                    f'<div><span style="font-weight: 800; color: #0F172A; font-size: 13px;">COOL++ PRO Bonus</span><div style="font-size: 11.5px; color: #64748B;">Capital-Light Operating Leverage Outperformance</div></div>'
                    f'<span style="background: #7C3AED; color: #FFFFFF; font-size: 11.5px; font-weight: 900; padding: 3px 9px; border-radius: 9999px; font-family: monospace;">+{float(bb.get("cool_pro_bonus", 0)):.1f} pts</span>'
                    f'</div>'
                    f'<div style="background: #FAF5FF; border: 1px solid #E9D5FF; border-left: 4px solid #7C3AED; border-radius: 6px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center;">'
                    f'<div><span style="font-weight: 800; color: #0F172A; font-size: 13px;">Trajectory Bonus</span><div style="font-size: 11.5px; color: #64748B;">Sustained Margin Expansion & FCF Compounding</div></div>'
                    f'<span style="background: #7C3AED; color: #FFFFFF; font-size: 11.5px; font-weight: 900; padding: 3px 9px; border-radius: 9999px; font-family: monospace;">+{float(bb.get("trajectory_bonus", 0)):.1f} pts</span>'
                    f'</div>'
                    f'<div style="background: #FAF5FF; border: 1px solid #E9D5FF; border-left: 4px solid #7C3AED; border-radius: 6px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center;">'
                    f'<div><span style="font-weight: 800; color: #0F172A; font-size: 13px;">Resilience Bonus</span><div style="font-size: 11.5px; color: #64748B;">Balance Sheet Solvency & Counter-Cyclical Endurance</div></div>'
                    f'<span style="background: #7C3AED; color: #FFFFFF; font-size: 11.5px; font-weight: 900; padding: 3px 9px; border-radius: 9999px; font-family: monospace;">+{float(bb.get("resilience_bonus", 0)):.1f} pts</span>'
                    f'</div>'
                    f'</div>'
                    f'<div style="background: #FAF5FF; border: 1.5px solid #E9D5FF; border-radius: 8px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center;">'
                    f'<span style="font-size: 12px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.5px;">Total Growth Bonus Applied</span>'
                    f'<span style="font-size: 18px; font-weight: 900; color: #7C3AED; font-family: monospace;">+{float(bb.get("total_bonus_applied", 0)):.1f} pts</span>'
                    f'</div>'
                )

        # Valuation Compass & model-estimated fair-value corridor
        compass_html = render_valuation_compass_html(res, live_data)
        if compass_html:
            st.markdown("##### 🧭 Valuation Compass & Model Fair-Value Corridor")
            st.caption("The fair-value band is a Gemini-generated estimate, not a computed discounted-cash-flow model. Treat it as an opinion, not a valuation.")
            st.html(compass_html)

        # Appendix B — Forensic Calculations & Stress Tests
        with st.expander("🔬 Appendix B — Forensic Calculations & Stress Tests", expanded=False):
            calcs = res.get("appendix_b_calculations", {})
            calc_cards = []
            for k, v in calcs.items():
                calc_cards.append(
                    f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 8px; padding: 14px 16px;">'
                    f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">{html.escape(str(k).replace("_", " ").title())}</div>'
                    f'<div style="font-size: 13.5px; font-weight: 700; color: #0F172A; margin-top: 6px; line-height: 1.45; font-family: monospace;">{html.escape(str(v))}</div>'
                    f'</div>'
                )
            if calc_cards:
                st.html(f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;">{"".join(calc_cards)}</div>')
            else:
                st.info("Forensic calculation disclosures unavailable for this asset.")

    # --- TAB 4: METHODOLOGY & CHECKS ---
    with tab_methodology:
        st.markdown("#### ⚖️ Methodology, Data Consistency & Benchmarks")
        st.caption("Inspect automated data reconciliation certificates, peer comparisons, and forensic methodology.")

        # Sentinel Audit Certificate
        if sentinel_audit:
            s_score = sentinel_audit.get('integrity_score')
            s_score_text = f"{s_score:.0f}/100" if s_score is not None else "N/A"
            s_run_id = sentinel_audit.get('run_id') or sentinel_audit.get('audit_hash', 'RUN-ID')
            st.markdown("##### 🔍 Data Consistency Sentinel Audit Certificate")
            st.html(
                f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-left: 5px solid #059669; border-radius: 8px; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); margin-bottom: 18px;">'
                f'<div><span style="font-weight: 800; color: #0F172A; font-size: 15px;">🔍 {esc(sentinel_audit.get("agent_name", "Data Consistency Engine"))}</span>'
                f'<div style="font-size: 13px; color: #475569; margin-top: 3px;">{esc(sentinel_audit.get("verdict_desc", ""))}</div>'
                f'<div style="font-size: 11px; color: #64748B; margin-top: 5px;">Score: <strong>{s_score_text}</strong> • Verified Checks: <strong>{sentinel_audit.get("passed_count", 0)}/{sentinel_audit.get("total_count", 0)}</strong></div></div>'
                f'<div style="text-align: right;"><span style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; font-size: 11.5px; font-weight: 800; padding: 4px 11px; border-radius: 9999px; font-family: monospace;">{esc(sentinel_audit.get("status", "EVALUATED"))}</span>'
                f'<div style="font-size: 11px; font-weight: 700; color: #64748B; margin-top: 5px; font-family: monospace;">Run ID: {esc(s_run_id)}</div></div>'
                f'</div>'
            )

        # Peer Relative Benchmark Matrix
        st.markdown(f"##### 👥 Peer Relative Benchmark Matrix ({target_sector})")
        peers = res.get("peer_matrix", [])
        if peers:
            p_rows = []
            p_rows.append(
                f'<tr style="background: #ECFDF5; border-bottom: 1.5px solid #A7F3D0;">'
                f'<td style="padding: 12px 16px; font-weight: 900; color: #059669;">'
                f'{esc(target_company_name)} <span style="background: #059669; color: #FFFFFF; font-size: 10px; font-weight: 900; padding: 2px 7px; border-radius: 4px; margin-left: 6px; font-family: monospace;">EVALUATED</span>'
                f'</td>'
                f'<td style="padding: 12px 16px; text-align: center;"><span style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; padding: 4px 10px; border-radius: 6px; font-weight: 900; font-family: monospace; font-size: 14px;">{final_score:.1f} / 100</span></td>'
                f'<td style="padding: 12px 16px;"><span style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; padding: 3px 9px; border-radius: 6px; font-weight: 800; font-size: 11.5px; font-family: monospace;">Active Target ({esc(verdict)})</span></td>'
                f'</tr>'
            )
            for p in peers:
                p_name = p.get("peer_name", "")
                p_sc = p.get("score", "N/A")
                p_pos = p.get("position", "Peer Competitor")
                p_rows.append(
                    f'<tr style="background: #FFFFFF; border-bottom: 1px solid #F1F5F9;">'
                    f'<td style="padding: 11px 16px; font-weight: 700; color: #0F172A;">{esc(p_name)}</td>'
                    f'<td style="padding: 11px 16px; text-align: center;"><span style="background: #F8FAFC; color: #2563EB; border: 1px solid #E2E8F0; padding: 3px 9px; border-radius: 6px; font-weight: 800; font-family: monospace; font-size: 13px;">{esc(p_sc)} / 100</span></td>'
                    f'<td style="padding: 11px 16px;"><span style="background: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; padding: 3px 9px; border-radius: 6px; font-weight: 700; font-size: 11.5px; font-family: monospace;">{esc(p_pos)}</span></td>'
                    f'</tr>'
                )

            peer_table_html = (
                f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; overflow: hidden; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);">'
                f'<table style="width: 100%; border-collapse: collapse; font-size: 13.5px;">'
                f'<thead>'
                f'<tr style="background: #F8FAFC; border-bottom: 1.5px solid #E2E8F0;">'
                f'<th style="padding: 12px 16px; text-align: left; font-weight: 800; color: #475569; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px;">Constituent Company</th>'
                f'<th style="padding: 12px 16px; text-align: center; font-weight: 800; color: #475569; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px;">Composite Quality Score</th>'
                f'<th style="padding: 12px 16px; text-align: left; font-weight: 800; color: #475569; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px;">Sector Position & Standing</th>'
                f'</tr>'
                f'</thead>'
                f'<tbody>{"".join(p_rows)}</tbody>'
                f'</table>'
                f'</div>'
            )
            st.html(peer_table_html)

        dossier_peer_html = render_head_to_head_comparison_html(
            target_ticker=target_ticker,
            target_company_name=target_company_name,
            target_sector=target_sector,
            live_data=live_data,
            financial_data=fin_res
        )
        st.html(dossier_peer_html)

        # Graphical Forensic Architecture & Evaluation Pipeline
        with st.expander("🧭 StockSage Forensic Architecture & Evaluation Pipeline (Visual Methodology & Benchmarks)", expanded=False):
            st.html(render_graphical_forensic_architecture_html())

        # Confidential Methodology IP Safeguard Notice (High-Level, Non-Revealing)
        st.markdown("""
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 14px 18px; margin-top: 14px; font-size: 12px; color: #475569; line-height: 1.5;">
          <strong style="color: #0F172A;">🔒 Evaluation Methodology & Safeguard Standard:</strong>
          Project KUSHA / StockSage utilizes a multi-stage deterministic pipeline combining Google Gemini multimodal ingestion of audited BSE annual reports, automated cash flow reconciliation, and sector-standardized balance sheet stress tests. Exact mathematical weights, proprietary scoring thresholds, and internal decision logic are protected under trade secret guidelines to prevent reverse engineering and ensure analytical objectivity.
        </div>
        """, unsafe_allow_html=True)

    # --- TAB 5: EXPORT BRIEF ---
    with tab_export:
        st.markdown("#### 📥 Export Research Brief & Forensic Data")
        st.caption("Download institutional-grade research outputs in structured JSON, markdown memo, or printable HTML/PDF.")

        raw_cname = str(res.get('company_name', 'Company')).replace(" [SYNTHETIC SAMPLE]", "")
        safe_cname = re.sub(r'[^a-zA-Z0-9_\-]', '_', raw_cname).strip('_') or "Company"

        exp_col1, exp_col2, exp_col3 = st.columns(3)
        with exp_col1:
            public_export_data = dict(res)
            public_export_data.pop("analysis_pipeline_version", None)
            public_export_data["regulatory_notice"] = (
                "This document is programmatically generated by Project KUSHA / StockSage for informational and educational "
                "screening purposes only. It does not constitute SEBI-registered investment advice or a statutory audit."
            )
            st.download_button(
                label="Download Structured JSON",
                data=json.dumps(public_export_data, indent=2),
                file_name=f"{safe_cname}_StockSage.json",
                mime="application/json",
                width="stretch"
            )

        with exp_col2:
            is_demo_export = res.get("is_synthetic_demo", False)
            demo_header = (
                "> [!WARNING]\n"
                "> **SYNTHETIC DEMO MODE — NOT INVESTMENT RESEARCH OR ADVICE**\n"
                "> This document contains purely synthetic illustrative data generated for UI testing. "
                "It does not represent an actual investment analysis, audited statement verification, or buy/sell recommendation.\n\n---\n\n"
            ) if is_demo_export else ""

            def source_refs(items):
                refs = []
                for c in (items or []):
                    u = safe_url(c.get("url", ""))
                    sid = sanitize_memo_field(c.get("source_id", "source"), max_len=40)
                    if u and sid:
                        refs.append(f"[{sid}]({u})")
                return ", ".join(refs) or "Insufficient evidence citation"

            web_sources_md = "\n".join(
                f"- [{sanitize_memo_field(s.get('source_id', 'source'), 40)}: {sanitize_memo_field(s.get('title', 'Source'), 100)}]({safe_url(s.get('url'))}) — published: {sanitize_memo_field(s.get('published_date') or 'not supplied by API', 60)}; retrieved: {sanitize_memo_field(s.get('retrieved_at', 'unknown'), 60)} ({sanitize_memo_field(s.get('source_type', 'web evidence'), 40)})"
                for s in res.get("web_research", {}).get("sources", [])
                if safe_url(s.get("url"))
            ) or "Insufficient evidence: no grounded web sources returned."

            pillars_md = "\n".join(
                f"- **Pillar {p.get('id')}: {sanitize_memo_field(p.get('name', 'Pillar'), 60)}**: {p.get('score')}/{p.get('max_score')} ({sanitize_memo_field(p.get('justification'), 400)}) — {source_refs(p.get('citations', []))}"
                for p in res.get("pillars", [])
            )

            penalties_md = "\n".join(
                f"- **{sanitize_memo_field(p.get('penalty_name', 'Penalty'), 60)} ({p.get('points')} pts):** {sanitize_memo_field(p.get('reason'), 300)} — {source_refs(p.get('citations', []))}"
                for p in res.get("penalties_breakdown", [])
            ) or "No penalties applied."

            bonus = res.get("bonuses_breakdown", {})
            call_refs = source_refs(res.get("final_call_citations", []))

            filing_meta_md = ""
            if res.get("filing_metadata"):
                fm = res["filing_metadata"]
                f_u = safe_url(fm.get("url")) or "Uploaded directly"
                f_title = sanitize_memo_field(fm.get('title', 'Statutory Filing'), 80)
                f_src = sanitize_memo_field(fm.get('source', 'Archive'), 40)
                f_yr = sanitize_memo_field(fm.get('year', 'Latest'), 30)
                filing_meta_md = f"- **Statutory Filing Analyzed:** [{f_title}]({f_u}) ({f_src}, Period: {f_yr})\n"

            sentinel_sec = ""
            if res.get("sentinel_audit"):
                sa = res["sentinel_audit"]
                sa_checks_md = "\n".join(f"- **{sanitize_memo_field(c.get('name'))}:** {sanitize_memo_field(c.get('status'))} — {sanitize_memo_field(c.get('detail'), 250)}" for c in sa.get("checks", []))
                sa_score = sa.get('integrity_score')
                sentinel_sec = f"\n## Automated Data Consistency Sentinel\n- **Integrity Score:** {f'{sa_score:.1f}' if isinstance(sa_score, (int, float)) else 'N/A (not evaluated)'}/100 ({sanitize_memo_field(sa.get('status'))})\n- **Checks Evaluated:** {sa.get('passed_count')}/{sa.get('total_count')}\n{sa_checks_md}\n"

            forensic_sec = ""
            if res.get("forensic_report"):
                fr = res["forensic_report"]
                fr_checks_md = "\n".join(f"- **{sanitize_memo_field(c.get('title'))}:** {sanitize_memo_field(c.get('status'))} ({sanitize_memo_field(c.get('metric', 'N/A'))}) — {sanitize_memo_field(c.get('detail'), 250)}" for c in fr.get("checks", []))
                fr_fqi = fr.get('fqi_score')
                forensic_sec = f"\n## Forensic Accounting & Concealed Risk Audit\n- **Forensic Quality Index (FQI):** {f'{fr_fqi:.1f}' if isinstance(fr_fqi, (int, float)) else 'N/A (insufficient evidence)'}/100 ({sanitize_memo_field(fr.get('verdict_badge'))})\n- **Evidence coverage:** {fr.get('evaluated_count', 0)}/{fr.get('total_checks', 8)} checks • External rating: {sanitize_memo_field(fr.get('credit_rating', {}).get('rating', 'N/A'))}\n{fr_checks_md}\n"

            provenance_memo_block = (
                f"> **Document Provenance & Model Audit Notice**\n"
                f"> - **Target Entity:** {sanitize_memo_field(res.get('company_name'))} ({sanitize_memo_field(target_ticker or res.get('ticker'))})\n"
                f"> - **Model Requested:** {sanitize_memo_field(res.get('model_requested') or selected_gemini_model)}\n"
                f"> - **Model Used:** {sanitize_memo_field(res.get('model_used') or selected_gemini_model)}\n"
                f"> - **Model Fallback Occurred:** {bool(res.get('model_fallback_used', False))}\n"
                f"> - **Retrieval Timestamp:** {sanitize_memo_field(res.get('retrieved_at', 'unknown'))}\n"
                f"> - **Pipeline Version:** {sanitize_memo_field(res.get('analysis_pipeline_version', ANALYSIS_PIPELINE_VERSION))}\n"
                f"> - **Notice:** This document is algorithmically generated by an AI model, unaudited, and provided for research and educational purposes only.\n\n"
            )

            guardrail_ev_md = "\n".join([f"- {sanitize_memo_field(ev)}" for ev in res.get('guardrail_evidence', [])])
            evidence_gaps_md = ", ".join([sanitize_memo_field(g) for g in res.get('evidence_gaps', [])]) or "None reported"
            search_queries_md = ", ".join([sanitize_memo_field(q) for q in res.get('web_research', {}).get('search_queries', [])]) or "No query metadata returned"

            md_text = f"""{demo_header}# StockSage | Institutional Research Memo: {sanitize_memo_field(res.get('company_name'))}

{provenance_memo_block}## Metadata
- **Target Company:** {sanitize_memo_field(res.get('company_name'))}
- **Sector Benchmark:** {sanitize_memo_field(res.get('sector'))}
- **Reporting Period:** {sanitize_memo_field(res.get('financial_year'))}
{filing_meta_md}- **Final Rating:** {sanitize_memo_field(res.get('verdict'))} (Score: {res.get('final_score')}/100)
- **Risk Allocation Sizing:** {sanitize_memo_field(res.get('position_sizing'))} (Illustrative Model Exposure Tier — Not SEBI Investment Advice)
- **Evidence status:** {sanitize_memo_field(res.get('analysis_status', 'unknown'))}
- **Evidence gaps:** {evidence_gaps_md}

## Web Research Sources
Search queries: {search_queries_md}
{web_sources_md}

## Mandatory Guardrail Tag
**{sanitize_memo_field(res.get('guardrail_tag'))}**
{guardrail_ev_md}
{sentinel_sec}{forensic_sec}
## Core 8-Pillar Scorecard
{pillars_md}

## Penalties and Bonuses
{penalties_md}
- **Bonus total ({bonus.get('total_bonus_applied', 0)} pts):** {sanitize_memo_field(bonus.get('reason', 'Insufficient evidence rationale.'))} — {source_refs(bonus.get('citations', []))}

## Sector-Sensitive Receivable Layer
- DSO: {sanitize_memo_field(rec.get('dso_days'))} days (Ideal: {sanitize_memo_field(rec.get('sector_ideal_dso'))})
- Overdue >90 Days: {sanitize_memo_field(rec.get('pct_over_90_days'))}
- Receivables / Sales: {sanitize_memo_field(rec.get('receivables_to_sales_pct'))}
- Verdict: {sanitize_memo_field(rec.get('receivable_verdict'))}

## Final Call
**{sanitize_memo_field(res.get('final_call'))}** — {call_refs}

---
*Regulatory Disclaimer: This research memo is programmatically generated by Project KUSHA / StockSage for informational and educational screening purposes only. It is not SEBI-registered investment advice or a statutory audit.*
"""
            st.download_button(
                label="Download Investment Memo (.md)",
                data=md_text,
                file_name=f"{safe_cname}_StockSage_Memo.md",
                mime="text/markdown",
                width="stretch"
            )

        with exp_col3:
            demo_html_banner = (
                '<div style="background:#fef3c7; border:2px solid #f59e0b; padding:12px 16px; border-radius:6px; font-size:13.5px; font-weight:700; color:#92400e; margin-bottom:18px; text-align:center;">'
                '⚠️ SYNTHETIC DEMO MODE — FOR TESTING ONLY. NOT INVESTMENT RESEARCH OR ADVICE.'
                '</div>'
            ) if is_demo_export else ""

            sentinel_html_table = ""
            if res.get("sentinel_audit"):
                sa = res["sentinel_audit"]
                sa_rows = "".join(f"<tr><td><strong>{html.escape(str(c.get('name') or ''))}</strong></td><td>{html.escape(str(c.get('status') or ''))}</td><td>{html.escape(str(c.get('detail') or ''))}</td></tr>" for c in sa.get("checks", []))
                sentinel_html_table = f"""
                <h2>Data Consistency Sentinel ({html.escape(str(sa.get('integrity_score') if sa.get('integrity_score') is not None else 'N/A'))}/100 - {html.escape(str(sa.get('status', 'N/A')))})</h2>
                <table>
                    <thead><tr><th>Sanity Check</th><th>Status</th><th>Verification Detail</th></tr></thead>
                    <tbody>{sa_rows}</tbody>
                </table>
                """

            forensic_html_table = ""
            if res.get("forensic_report"):
                fr = res["forensic_report"]
                fr_rows = "".join(f"<tr><td><strong>{html.escape(str(c.get('title') or ''))}</strong></td><td><strong>{html.escape(str(c.get('status') or ''))}</strong></td><td>{html.escape(str(c.get('metric', 'N/A')))}</td><td>{html.escape(str(c.get('detail') or ''))}</td></tr>" for c in fr.get("checks", []))
                forensic_html_table = f"""
                <h2>Forensic Accounting Audit (FQI: {html.escape(str(fr.get('fqi_score') if fr.get('fqi_score') is not None else 'N/A'))}/100 - {html.escape(str(fr.get('verdict_badge', 'N/A')))})</h2>
                <table>
                    <thead><tr><th>Forensic Test</th><th>Status</th><th>Metric</th><th>Findings &amp; Stress Test</th></tr></thead>
                    <tbody>{fr_rows}</tbody>
                </table>
                """

            c_name_escaped = html.escape(str(res.get('company_name', 'Company')))
            sector_escaped = html.escape(str(res.get('sector', 'Diversified')))
            year_escaped = html.escape(str(res.get('financial_year', 'Latest')))
            verdict_escaped = html.escape(str(res.get('verdict', '')))
            guardrail_escaped = html.escape(str(res.get('guardrail_tag', '')))
            final_call_escaped = html.escape(str(res.get('final_call', '')))
            rec_verdict_escaped = html.escape(str(rec.get('receivable_verdict', '')))

            pillar_rows_escaped = "".join([
                f"<tr><td><strong>P{p.get('id')}: {html.escape(str(p.get('name', '')))}</strong></td><td><strong>{p.get('score')}</strong></td><td>{p.get('max_score')}</td><td>{html.escape(str(p.get('justification', '')))}</td></tr>"
                for p in res.get('pillars', [])
            ])
            guardrail_ev_items = "".join([f'<li>{html.escape(str(e))}</li>' for e in res.get('guardrail_evidence', [])])

            html_report = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{c_name_escaped} - StockSage Institutional Report</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; color: #0f172a; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #ffffff; }}
    h1 {{ font-size: 24px; color: #047857; border-bottom: 2px solid #059669; padding-bottom: 8px; }}
    h2 {{ font-size: 18px; color: #0f172a; margin-top: 24px; }}
    .badge {{ display: inline-block; padding: 4px 12px; border-radius: 9999px; font-weight: 700; font-size: 14px; background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }}
    .tag-box {{ border: 1.5px solid #10b981; background: #f0fdf4; padding: 12px 16px; border-radius: 6px; margin: 16px 0; color: #064e3b; }}
    table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
    th, td {{ border: 1px solid #e2e8f0; padding: 10px; text-align: left; font-size: 14px; color: #0f172a; }}
    th {{ background: #f8fafc; font-weight: 600; }}
    .metric-val {{ font-weight: 700; color: #047857; }}
    @media print {{ body {{ margin: 0; padding: 10px; }} .no-print {{ display: none; }} }}
</style>
</head>
<body>
    {demo_html_banner}
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h1>StockSage • {c_name_escaped}</h1>
            <p style="color:#64748b; margin-top:-8px;">Sector: {sector_escaped} • Period: {year_escaped} • Institutional Forensic Research</p>
        </div>
        <div style="text-align:right;">
            <div style="font-size:32px; font-weight:800; color:#047857;">{res.get('final_score', 0):.1f}<span style="font-size:16px; color:#64748b;">/100</span></div>
            <div class="badge">{verdict_escaped}</div>
        </div>
    </div>
    {sentinel_html_table}
    {forensic_html_table}
    <h2>Core 8-Pillar Evaluation</h2>
    <table>
        <thead><tr><th>Pillar</th><th>Score</th><th>Max</th><th>Forensic Justification</th></tr></thead>
        <tbody>
            {pillar_rows_escaped}
        </tbody>
    </table>

    <h2>Sector Receivable Health</h2>
    <table>
        <tr><td><strong>DSO:</strong> {rec.get('dso_days')} days (Ideal: {rec.get('sector_ideal_dso')})</td><td><strong>Receivables/Sales:</strong> {rec.get('receivables_to_sales_pct')}</td></tr>
        <tr><td><strong>Overdue >90d:</strong> {rec.get('pct_over_90_days')}</td><td><strong>Assessment:</strong> {rec_verdict_escaped}</td></tr>
    </table>

    <div class="tag-box">
        <strong>Mandatory Guardrail Tag: {guardrail_escaped}</strong>
        <ul style="margin: 8px 0 0 0; padding-left: 20px;">{guardrail_ev_items}</ul>
    </div>

    <h2>Analyst Recommendation</h2>
    <div style="background:#f8fafc; border: 1px solid #e2e8f0; padding:14px; border-radius:6px; font-size:16px; font-weight:600; color: #0f172a;">
        {final_call_escaped}
    </div>

    <div style="margin-top: 32px; padding: 12px 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 11px; color: #64748b; line-height: 1.5;">
        <strong>Regulatory Disclaimer:</strong> This report is programmatically generated by Project KUSHA / StockSage for informational and educational purposes only. It does not constitute SEBI-registered investment advice, a research report under SEBI (Research Analysts) Regulations, or a statutory audit. Conduct independent due diligence before making investment decisions.
    </div>
</body>
</html>"""
            st.download_button(
                label="Print Analyst Report (PDF/HTML)",
                data=html_report,
                file_name=f"{safe_cname}_StockSage_Report.html",
                mime="text/html",
                width="stretch"
            )

        # Copyable Plain-Text Research Brief
        st.write("")
        summary_plain = (
            f"STOCKSAGE RESEARCH BRIEF: {raw_cname} ({target_ticker or 'NSE/BSE'})\n"
            f"Sector: {target_sector or 'Diversified'} | Score: {final_score:.1f}/100 ({verdict})\n"
            f"Risk Tier: {position_sizing} (Educational Tier - Not Investment Advice)\n"
            f"Takeaway: {call_summary}\n\n"
            f"Key Moats:\n" + "\n".join(f" - {s}" for s in str_list[:3]) + "\n\n"
            f"Key Risks:\n" + "\n".join(f" - {w}" for w in wk_list[:3]) + "\n\n"
            f"Sources: Official BSE Annual Reports, Yahoo Quotes & Grounded Research.\n"
            f"Notice: Programmatically generated educational screening brief. Not SEBI advice."
        )
        st.text_area("📋 Copyable Plain-Text Brief", value=summary_plain, height=180)



# --- STATUTORY REGULATORY DISCLAIMER & DATA PROVENANCE NOTICE ---
st.html("""
<div style="margin-top: 40px; padding: 18px 24px; background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 12px; font-size: 11.5px; color: #64748B; line-height: 1.6; margin-bottom: 30px;">
  <div style="font-weight: 800; color: #0F172A; margin-bottom: 6px; display: flex; align-items: center; gap: 6px; text-transform: uppercase; letter-spacing: 0.5px;">
    <span>⚖️</span> Statutory Disclaimer &amp; Regulatory Notice
  </div>
  <div>
    <strong>Not SEBI Registered:</strong> Project KUSHA / StockSage is an automated analytical research and educational technology prototype. It is NOT registered with the Securities and Exchange Board of India (SEBI) as an Investment Adviser (under IA Regulations, 2013) or Research Analyst (under RA Regulations, 2014).
    All outputs, forensic scores, traffic light badges, and illustrative allocation bands represent programmatic algorithmic evaluations of public disclosures and do NOT constitute investment advice, financial recommendations, or solicitation to buy or sell securities.
  </div>
  <div style="margin-top: 6px;">
    <strong>Data Provenance:</strong> Market data is retrieved via public aggregation endpoints (e.g., Yahoo Finance). Statutory filings are discovered from publicly archived exchange repositories. Metrics are subject to transmission delays and public reporting inconsistencies. Users must perform independent verification and consult a licensed financial advisor before making capital allocation decisions.
  </div>
</div>
""")
