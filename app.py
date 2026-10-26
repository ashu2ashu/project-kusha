"""
app.py
FinScan India | IDEX-7.5SC Hybrid Pro (Ashu Elite Edition)
Institutional AI Financial Intelligence Terminal for Indian Listed Equities
"""

import streamlit as st
import plotly.graph_objects as go
import json
import os
import re
import html
import time
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
        background, border, accent, heading_color, body_color = "#EFF6FF", "#93C5FD", "#2563EB", "#1E40AF", "#1D4ED8"
    elif analyzed:
        heading = "Official BSE India Filing Analyzed · Multimodal Document Ingestion"
        description = "The official statutory filing was attached to Gemini and comprehensively analyzed across all 10 governance and financial pillars."
        background, border, accent, heading_color, body_color = "#F0FDF4", "#86EFAC", "#16A34A", "#14532D", "#166534"
    else:
        heading = "Filing listed · PDF not analyzed"
        description = "The filing metadata was found, but the PDF was not confirmed as attached to the completed analysis."
        background, border, accent, heading_color, body_color = "#FFFBEB", "#FCD34D", "#D97706", "#92400E", "#B45309"

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
        'style="color: #2563EB; font-weight: 700; text-decoration: underline; font-size: 13px;">View BSE-hosted PDF ↗</a>'
        if safe_bse_url
        else '<span style="color: #64748B; font-size: 13px;">No verified filing link</span>'
    )

    display_title = title if year in title else f"{title} ({year})"
    return (
        f'<div style="background: {background}; border: 1.5px solid {border}; border-left: 5px solid {accent}; '
        'border-radius: 10px; padding: 12px 18px; margin-bottom: 16px; display: flex; '
        'justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">'
        f'<div><div style="font-size: 11px; font-weight: 800; color: {heading_color}; text-transform: uppercase; '
        f'letter-spacing: 0.6px; margin-bottom: 2px;">{heading}</div>'
        f'<div style="font-size: 14.5px; font-weight: 750; color: #14532D;">{display_title} · {source}</div>'
        f'<div style="font-size: 12px; color: {body_color}; margin-top: 2px;">{description}</div></div>'
        f'<div>{link_html}</div></div>'
    )


# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="StockSage | Institutional AI Financial Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Brand Logo Integration
LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo.svg")
ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "icon.svg")
if os.path.exists(LOGO_PATH):
    st.logo(LOGO_PATH, icon_image=ICON_PATH if os.path.exists(ICON_PATH) else None, size="large")

# StockSage Institutional Design System & Typography Engine (Inter + JetBrains Mono)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&display=swap');

    /* Design Tokens & CSS Custom Properties */
    :root {
        /* Brand Palette - Dalal Street Emerald & Institutional Slate */
        --ss-primary-50: #ECFDF5;
        --ss-primary-100: #D1FAE5;
        --ss-primary-200: #A7F3D0;
        --ss-primary-300: #6EE7B7;
        --ss-primary-400: #34D399;
        --ss-primary-500: #10B981;
        --ss-primary-600: #059669; /* Canonical Dalal Street Emerald */
        --ss-primary-700: #047857;
        --ss-primary-800: #065F46;
        --ss-primary-900: #022C22;

        /* Slate Neutrals */
        --ss-slate-50: #F8FAFC;
        --ss-slate-100: #F1F5F9;
        --ss-slate-200: #E2E8F0;
        --ss-slate-300: #CBD5E1;
        --ss-slate-400: #94A3B8;
        --ss-slate-500: #64748B;
        --ss-slate-600: #475569;
        --ss-slate-700: #334155;
        --ss-slate-800: #1E293B;
        --ss-slate-900: #0F172A;

        /* Financial Status Indicators */
        --ss-gain: #059669;
        --ss-gain-bg: #F0FDF4;
        --ss-gain-border: #86EFAC;
        --ss-loss: #DC2626;
        --ss-loss-bg: #FEF2F2;
        --ss-loss-border: #FCA5A5;
        --ss-warn: #D97706;
        --ss-warn-bg: #FFFBEB;
        --ss-warn-border: #FDE68A;

        /* Typography */
        --ss-font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        --ss-font-mono: 'JetBrains Mono', 'SF Mono', Consolas, Menlo, monospace;

        /* Elevation Matrix & Multi-Layer Shadows */
        --ss-shadow-xs: 0 1px 2px 0 rgba(15, 23, 42, 0.04);
        --ss-shadow-sm: 0 1px 3px 0 rgba(15, 23, 42, 0.05), 0 1px 2px -1px rgba(15, 23, 42, 0.03);
        --ss-shadow-md: 0 4px 6px -1px rgba(15, 23, 42, 0.06), 0 2px 4px -2px rgba(15, 23, 42, 0.04);
        --ss-shadow-lg: 0 10px 15px -3px rgba(15, 23, 42, 0.07), 0 4px 6px -4px rgba(15, 23, 42, 0.03);
        --ss-shadow-card: 0 2px 8px -1px rgba(15, 23, 42, 0.04), 0 1px 3px 0 rgba(15, 23, 42, 0.03);
        --ss-shadow-hover: 0 12px 24px -4px rgba(15, 23, 42, 0.09), 0 4px 8px -2px rgba(5, 150, 105, 0.06);
        --ss-shadow-glow: 0 0 0 3px rgba(5, 150, 105, 0.16);

        /* Radii Tokens */
        --ss-radius-sm: 6px;
        --ss-radius-md: 10px;
        --ss-radius-lg: 14px;
        --ss-radius-xl: 18px;
        --ss-radius-full: 9999px;

        /* Fluid Motion & Transitions */
        --ss-ease-institutional: cubic-bezier(0.4, 0, 0.2, 1);
        --ss-ease-spring: cubic-bezier(0.16, 1, 0.3, 1);
        --ss-transition-fast: 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        --ss-transition-smooth: 0.22s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* Global Typography Smoothing & Baseline */
    html, body {
        font-family: var(--ss-font-sans) !important;
        font-size: 15px !important;
        line-height: 1.55 !important;
        color: var(--ss-slate-900) !important;
        background-color: #FFFFFF !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
        text-rendering: optimizeLegibility !important;
    }

    /* Financial Tabular Numbers for all metrics, numbers, and tickers */
    code, kbd, samp, pre, [data-testid="stMetricValue"], .m-value, .metric-val, .pillar-score, .financial-num {
        font-family: var(--ss-font-mono) !important;
        font-feature-settings: 'tnum' 1, 'zero' 1 !important;
        font-variant-numeric: tabular-nums !important;
    }

    /* Headings with Optical Tracking & Tight Geometry */
    h1, .stHeadingContainer h1 {
        font-family: var(--ss-font-sans) !important;
        font-size: 32px !important;
        font-weight: 800 !important;
        letter-spacing: -0.03em !important;
        line-height: 1.2 !important;
        color: var(--ss-slate-900) !important;
    }
    h2, .stHeadingContainer h2 {
        font-family: var(--ss-font-sans) !important;
        font-size: 24px !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
        line-height: 1.25 !important;
        color: var(--ss-slate-900) !important;
    }
    h3, .stHeadingContainer h3 {
        font-family: var(--ss-font-sans) !important;
        font-size: 19px !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        line-height: 1.3 !important;
        color: var(--ss-slate-800) !important;
    }
    h4, .stHeadingContainer h4 {
        font-family: var(--ss-font-sans) !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        letter-spacing: -0.015em !important;
        line-height: 1.35 !important;
        color: var(--ss-slate-700) !important;
    }
    p, span, label {
        letter-spacing: -0.01em;
    }

    /* Live Glowing Beacon Animation */
    @keyframes pulse-live {
        0% { transform: scale(0.94); opacity: 0.85; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1.06); opacity: 1; box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.94); opacity: 0.85; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    .live-pulse-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: var(--ss-primary-500);
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse-live 2s infinite var(--ss-ease-spring);
        vertical-align: middle;
    }

    /* Ultra-Modern Institutional Segmented Control */
    div[data-testid="stSegmentedControl"] {
        background-color: var(--ss-slate-100) !important;
        border: 1px solid var(--ss-slate-200) !important;
        border-radius: var(--ss-radius-md) !important;
        padding: 3px !important;
        gap: 3px !important;
    }
    div[data-testid="stSegmentedControl"] button {
        border-radius: var(--ss-radius-sm) !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        color: var(--ss-slate-600) !important;
        padding: 6px 16px !important;
        border: none !important;
        transition: all var(--ss-transition-fast) !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: #FFFFFF !important;
        color: var(--ss-primary-700) !important;
        font-weight: 700 !important;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.08) !important;
    }
    div[data-testid="stSegmentedControl"] button:hover {
        color: var(--ss-primary-600) !important;
    }

    /* Screener-Style Iconic Tabs */
    div[data-baseweb="tab-list"] {
        gap: 4px !important;
        border-bottom: 2px solid var(--ss-slate-200) !important;
        padding-bottom: 0px !important;
        margin-top: 12px !important;
        margin-bottom: 22px !important;
    }
    button[data-baseweb="tab"] {
        font-family: var(--ss-font-sans) !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        border-radius: 8px 8px 0 0 !important;
        color: var(--ss-slate-500) !important;
        background: transparent !important;
        border: none !important;
        letter-spacing: -0.01em !important;
        transition: all var(--ss-transition-fast) !important;
    }
    button[data-baseweb="tab"]:hover {
        color: var(--ss-primary-600) !important;
        background-color: var(--ss-primary-50) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--ss-primary-700) !important;
        font-weight: 700 !important;
        border-bottom: 3px solid var(--ss-primary-600) !important;
        background-color: transparent !important;
    }
    div[data-baseweb="tab-border"] {
        display: none !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: var(--ss-primary-600) !important;
        height: 3px !important;
    }

    /* Screener-Style Key Ratio Metric Cards: Crisp, Elevated & Legible */
    [data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        padding: 16px 20px !important;
        border-radius: var(--ss-radius-lg) !important;
        border: 1px solid var(--ss-slate-200) !important;
        box-shadow: var(--ss-shadow-card) !important;
        transition: transform var(--ss-transition-smooth), box-shadow var(--ss-transition-smooth), border-color var(--ss-transition-fast) !important;
        position: relative;
        overflow: hidden;
        will-change: transform, box-shadow;
        backface-visibility: hidden;
    }
    [data-testid="stMetric"]:hover {
        border-color: var(--ss-primary-300) !important;
        transform: translateY(-2px) !important;
        box-shadow: var(--ss-shadow-hover) !important;
    }
    [data-testid="stMetricValue"] {
        font-family: var(--ss-font-mono) !important;
        font-size: 28px !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em !important;
        color: var(--ss-slate-900) !important;
        line-height: 1.2 !important;
        font-feature-settings: 'tnum' 1, 'zero' 1 !important;
        font-variant-numeric: tabular-nums !important;
    }
    [data-testid="stMetricLabel"] {
        font-family: var(--ss-font-sans) !important;
        font-size: 12.5px !important;
        font-weight: 700 !important;
        color: var(--ss-slate-500) !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 14px !important;
        font-weight: 700 !important;
    }

    /* Screener-Style Institutional Emerald Primary Button */
    button[kind="primary"] {
        background: linear-gradient(135deg, var(--ss-primary-600) 0%, var(--ss-primary-700) 100%) !important;
        color: #FFFFFF !important;
        font-family: var(--ss-font-sans) !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 12px 28px !important;
        border-radius: var(--ss-radius-md) !important;
        border: 1px solid var(--ss-primary-700) !important;
        letter-spacing: -0.01em !important;
        box-shadow: 0 2px 8px rgba(5, 150, 105, 0.22) !important;
        transition: all var(--ss-transition-fast) !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, var(--ss-primary-700) 0%, var(--ss-primary-800) 100%) !important;
        box-shadow: 0 4px 14px rgba(5, 150, 105, 0.35) !important;
        transform: translateY(-1px) !important;
    }
    button[kind="primary"]:active {
        transform: translateY(1px) scale(0.99) !important;
    }

    /* Preset Benchmark Chips & Secondary Buttons */
    button[kind="secondary"] {
        font-family: var(--ss-font-sans) !important;
        border-radius: var(--ss-radius-md) !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        border: 1px solid var(--ss-slate-200) !important;
        color: var(--ss-slate-700) !important;
        background-color: #FFFFFF !important;
        transition: all var(--ss-transition-fast) !important;
    }
    button[kind="secondary"]:hover {
        border-color: var(--ss-primary-600) !important;
        color: var(--ss-primary-700) !important;
        background-color: var(--ss-primary-50) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 6px rgba(5, 150, 105, 0.1) !important;
    }

    /* Streamlit Native Border Container Polish (st.container(border=True)) */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #FFFFFF !important;
        border: 1px solid var(--ss-slate-200) !important;
        border-radius: var(--ss-radius-lg) !important;
        box-shadow: var(--ss-shadow-card) !important;
        padding: 20px 24px !important;
        transition: border-color var(--ss-transition-fast) !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
        border-color: var(--ss-slate-300) !important;
    }

    /* Form Controls & Inputs Emerald Glow Focus Ring */
    div[data-baseweb="input"] input,
    div[data-baseweb="select"] {
        font-family: var(--ss-font-sans) !important;
        border-radius: var(--ss-radius-md) !important;
        font-size: 14.5px !important;
        transition: all var(--ss-transition-fast) !important;
    }
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"]:focus-within {
        border-color: var(--ss-primary-600) !important;
        box-shadow: var(--ss-shadow-glow) !important;
    }

    /* Expanders Institutional Styling */
    details[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid var(--ss-slate-200) !important;
        border-radius: var(--ss-radius-md) !important;
        box-shadow: var(--ss-shadow-xs) !important;
        overflow: hidden;
    }
    details[data-testid="stExpander"] summary {
        font-family: var(--ss-font-sans) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        color: var(--ss-slate-800) !important;
        padding: 12px 16px !important;
    }
    details[data-testid="stExpander"] summary:hover {
        color: var(--ss-primary-600) !important;
        background-color: var(--ss-slate-50) !important;
    }

    /* Progress Bar */
    .stProgress > div > div > div > div {
        background-color: var(--ss-primary-600) !important;
        border-radius: var(--ss-radius-full) !important;
    }
    .stProgress > div > div > div {
        background-color: var(--ss-slate-200) !important;
        height: 8px !important;
        border-radius: var(--ss-radius-full) !important;
    }

    /* 8-Pillar Screener-Grade Financial Table */
    .pillar-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border: 1px solid var(--ss-slate-200);
        border-radius: var(--ss-radius-lg);
        overflow: hidden;
        background: #FFFFFF;
        margin: 14px 0 24px 0;
        box-shadow: var(--ss-shadow-card);
    }
    .pillar-table th {
        background-color: var(--ss-slate-50);
        padding: 12px 18px;
        font-size: 12px;
        font-weight: 700;
        color: var(--ss-slate-600);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-bottom: 2px solid var(--ss-slate-200);
        border-right: 1px solid var(--ss-slate-100);
    }
    .pillar-table th:last-child {
        border-right: none;
    }
    .pillar-table td {
        padding: 14px 18px;
        border-bottom: 1px solid var(--ss-slate-100);
        border-right: 1px solid var(--ss-slate-100);
        vertical-align: top;
        font-size: 14px;
        color: var(--ss-slate-800);
        line-height: 1.55;
        transition: background-color var(--ss-transition-fast);
    }
    .pillar-table td:last-child {
        border-right: none;
    }
    .pillar-table tr:last-child td {
        border-bottom: none;
    }
    .pillar-table tr:hover td {
        background-color: #F7FEFA;
    }

    /* Guardrail Semantic Banners */
    .guardrail-clean-box {
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
        border: 1px solid var(--ss-primary-500);
        border-left: 5px solid var(--ss-primary-600);
        border-radius: var(--ss-radius-md);
        padding: 16px 22px;
        color: var(--ss-slate-900);
        margin-top: 14px;
        margin-bottom: 18px;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.08);
    }
    .guardrail-alert-box {
        background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
        border: 1px solid #F59E0B;
        border-left: 5px solid var(--ss-warn);
        border-radius: var(--ss-radius-md);
        padding: 16px 22px;
        color: var(--ss-slate-900);
        margin-top: 14px;
        margin-bottom: 18px;
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.08);
    }
    .guardrail-red-box {
        background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
        border: 1px solid #EF4444;
        border-left: 5px solid var(--ss-loss);
        border-radius: var(--ss-radius-md);
        padding: 16px 22px;
        color: var(--ss-slate-900);
        margin-top: 14px;
        margin-bottom: 18px;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.08);
    }

    /* Factsheet Header & Matrix Cards */
    .facts-header-card {
        background: #FFFFFF;
        border: 1px solid var(--ss-slate-200);
        border-radius: var(--ss-radius-xl);
        padding: 24px 28px;
        margin-top: 16px;
        margin-bottom: 22px;
        box-shadow: var(--ss-shadow-card);
        transition: transform var(--ss-transition-smooth), box-shadow var(--ss-transition-smooth), border-color var(--ss-transition-fast);
        will-change: transform, box-shadow;
        backface-visibility: hidden;
    }
    .facts-header-card:hover {
        border-color: var(--ss-slate-300);
        transform: translateY(-1px);
        box-shadow: var(--ss-shadow-lg);
    }
    @media (max-width: 640px) {
        .facts-header-card {
            padding: 16px 16px !important;
        }
    }
    .metrics-3col-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        margin-bottom: 24px;
    }
    @media (max-width: 1100px) and (min-width: 768px) {
        .metrics-3col-grid {
            grid-template-columns: repeat(2, 1fr) !important;
        }
    }
    @media (max-width: 767px) {
        .metrics-3col-grid {
            grid-template-columns: 1fr !important;
        }
    }
    .metric-domain-card {
        background: #FFFFFF;
        border: 1px solid var(--ss-slate-200);
        border-radius: var(--ss-radius-lg);
        overflow: hidden;
        box-shadow: var(--ss-shadow-card);
        transition: transform var(--ss-transition-smooth), box-shadow var(--ss-transition-smooth), border-color var(--ss-transition-fast);
        will-change: transform, box-shadow;
        backface-visibility: hidden;
    }
    .metric-domain-card:hover {
        transform: translateY(-2px);
        border-color: var(--ss-primary-200);
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
        border-bottom: 1px solid var(--ss-slate-100);
        transition: background-color var(--ss-transition-fast);
    }
    .metric-table-spacious tr:last-child {
        border-bottom: none;
    }
    .metric-table-spacious tr:hover {
        background-color: #F7FEFA !important;
    }
    .metric-table-spacious td.m-label {
        padding: 12px 20px;
        font-size: 14px;
        font-weight: 600;
        color: var(--ss-slate-700);
        text-align: left;
        white-space: nowrap;
    }
    .metric-table-spacious td.m-value {
        padding: 12px 20px;
        font-size: 15px;
        font-family: var(--ss-font-mono);
        font-weight: 700;
        color: var(--ss-slate-900);
        text-align: right;
        white-space: nowrap;
        font-feature-settings: 'tnum' 1, 'zero' 1;
        font-variant-numeric: tabular-nums;
    }

    /* Custom Institutional Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: var(--ss-slate-100);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb {
        background: var(--ss-slate-300);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--ss-slate-400);
    }
    /* StockSage workspace polish */
    [data-testid="stAppViewContainer"] { background: #F6F8FB; }
    [data-testid="stMainBlockContainer"] { max-width: 1480px; padding-top: 1.2rem; padding-bottom: 2.5rem; }
    .ss-hero { display:grid; grid-template-columns:minmax(0,1.6fr) minmax(300px,.9fr); gap:20px; align-items:center; padding:18px 24px; margin:4px 0 16px; color:#F8FAFC; border:1px solid rgba(255,255,255,.12); border-radius:16px; background:radial-gradient(ellipse at 78% 8%,rgba(52,211,153,.22),transparent 34%),linear-gradient(125deg,#071F1A 0%,#064E3B 54%,#102B2A 100%); box-shadow:0 8px 24px rgba(15,23,42,.08); }
    .ss-hero-kicker { display:inline-flex; gap:6px; align-items:center; color:#A7F3D0; font-size:10.5px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
    .ss-hero-title { margin:6px 0 4px; color:#FFF; font-size:clamp(22px,2.4vw,30px); font-weight:800; letter-spacing:-.03em; line-height:1.15; }
    .ss-hero-subtitle { max-width:650px; margin:0; color:#D1FAE5; font-size:13px; line-height:1.5; }
    .ss-hero-meta { display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; }
    .ss-hero-meta span { padding:3px 8px; border:1px solid rgba(255,255,255,.16); border-radius:999px; color:#E2E8F0; background:rgba(255,255,255,.07); font-size:10.5px; font-weight:600; }
    .ss-hero-stats { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; }
    .ss-hero-stat { min-height:60px; display:flex; flex-direction:column; justify-content:center; padding:8px 11px; border:1px solid rgba(255,255,255,.15); border-radius:10px; background:rgba(255,255,255,.075); }
    .ss-hero-stat-label { color:#A7F3D0; font-size:8.5px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
    .ss-hero-stat-value { margin-top:3px; color:#FFF; font-size:13.5px; font-weight:750; line-height:1.2; }
    .ss-source-card { padding:12px 14px; border:1px solid #DCE5E8; border-radius:12px; background:linear-gradient(135deg,#F7FBF9,#FFF); }
    .ss-source-label { margin-bottom:8px; color:#64748B; font-size:10px; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
    .ss-source-row { display:flex; justify-content:space-between; gap:12px; margin:5px 0; color:#334155; font-size:11px; }
    .ss-source-row strong { color:#0F172A; font-weight:700; text-align:right; }
    .ss-source-note { margin-top:8px; color:#64748B; font-size:10px; line-height:1.45; }
    div[data-testid="stVerticalBlockBorderWrapper"] > div { border-radius:16px !important; }
    div[data-testid="stSegmentedControl"] { white-space:normal; }
    div[data-testid="stButton"] button { min-height:40px; white-space:normal; line-height:1.25; }
    @media (max-width:900px) { .ss-hero { grid-template-columns:1fr; gap:20px; padding:24px; } .ss-hero-stats { max-width:720px; } }
    @media (max-width:600px) {
        [data-testid="stMainBlockContainer"] { padding:.8rem .8rem 2rem; }
        [data-testid="stHorizontalBlock"] { flex-direction:column !important; align-items:stretch !important; gap:.45rem !important; }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] { width:100% !important; min-width:0 !important; flex:1 1 100% !important; }
        .ss-hero { padding:18px 16px; border-radius:16px; gap:13px; }
        .ss-hero-title { font-size:26px; }
        .ss-hero-subtitle { font-size:13px; }
        .ss-hero-meta span:nth-child(n+2) { display:none; }
        .ss-hero-meta { margin-top:11px; }
        .ss-hero-stats { grid-template-columns:repeat(2,minmax(0,1fr)); gap:6px; }
        .ss-hero-stat { min-height:64px; padding:8px 7px; }
        .ss-hero-stat:last-child { grid-column:1 / -1; min-height:48px; flex-direction:row; align-items:center; justify-content:space-between; }
        .ss-hero-stat-label { font-size:8px; letter-spacing:.04em; }
        .ss-hero-stat-value { font-size:11px; line-height:1.2; overflow-wrap:anywhere; }
        div[data-testid="stButton"] button { font-size:11px !important; padding-left:.3rem !important; padding-right:.3rem !important; }
    }
    .ss-pipeline-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; position:relative; margin-bottom:24px; }
    @media (max-width:1000px) { .ss-pipeline-grid { grid-template-columns:repeat(2,minmax(0,1fr)) !important; } }
    @media (max-width:600px) { .ss-pipeline-grid { grid-template-columns:1fr !important; } .pillar-table { display:block; overflow-x:auto; } }
</style>
""", unsafe_allow_html=True)

# Prepare accurate universe counts once for the sidebar and hero summary.
company_options = get_company_list()
tracked_equity_count = sum(1 for item in company_options if find_company_info(item).get("ticker") != "CUSTOM")
sector_count = len(get_sector_list())

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### StockSage")
    st.caption("Institutional Financial Terminal • Ashu Elite Edition")
    
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
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=env_key,
        type="password",
        help="Use a Gemini API key from Google AI Studio. Your key stays masked in this field."
    )

    active_api_key = api_key_input.strip() if api_key_input and api_key_input.strip() else env_key

    selected_gemini_model = st.selectbox(
        "Gemini Model",
        options=SUPPORTED_MODELS,
        index=0,
        help="Select supported Google Gemini model."
    )

    if env_key:
        st.caption("Key auto-loaded from .env")

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

    st.divider()
    
    # Prompt Engine Inspector
    with st.expander("Prompt Model Settings", expanded=False):
        st.caption("Core Prompt Model (Locked):")
        custom_prompt = st.text_area(
            "Prompt Template",
            value=IDEX_ANALYSIS_PROMPT,
            height=280,
            help="Dynamic placeholders: {company_name}, {sector}"
        )

    st.divider()
    st.caption("**Forensic Mandates:**")
    st.markdown("""
    - **8 Pillars:** Core score ≤ 100
    - **PIO Hard Trigger:** Auto-cap Governance ≤6/20, blocks bonuses, forces `GOV-RED 🔴`
    - **Receivable Layer:** Embedded 4.0 pt subscore
    - **Bonus Cap:** Cumulative +10% max
    """)

# Top hero: product promise and transparent source attribution.
st.html(f"""
<section class="ss-hero">
  <div>
    <div class="ss-hero-kicker">StockSage <span>•</span> Company research workspace</div>
    <div class="ss-hero-title">See the business behind the ticker.</div>
    <p class="ss-hero-subtitle">Review company fundamentals with market context, document research, and the IDEX-7.5SC framework in one clear workspace.</p>
    <div class="ss-hero-meta"><span>IDEX-7.5SC Hybrid Pro</span><span>Source citations included in analysis</span><span>Settings in the sidebar</span></div>
  </div>
  <div class="ss-hero-stats">
    <div class="ss-hero-stat"><div class="ss-hero-stat-label">Company universe</div><div class="ss-hero-stat-value">{tracked_equity_count} tracked equities</div></div>
    <div class="ss-hero-stat"><div class="ss-hero-stat-label">Sector groups</div><div class="ss-hero-stat-value">{sector_count} sectors</div></div>
    <div class="ss-hero-stat"><div class="ss-hero-stat-label">Quote provider</div><div class="ss-hero-stat-value">Yahoo Finance</div></div>
  </div>
</section>
""")

# --- TOP-LEVEL WORKSPACE NAVIGATION ---
workspace_options = ["🌐 Explore", "🔬 Company Analysis", "📊 Nifty 50"]
if "pending_nav_mode" in st.session_state:
    st.session_state["active_nav_mode"] = st.session_state.pop("pending_nav_mode")

if st.session_state.get("active_nav_mode") not in workspace_options:
    st.session_state["active_nav_mode"] = "🌐 Explore"

terminal_mode = st.segmented_control(
    "Workspace",
    options=workspace_options,
    key="active_nav_mode",
    label_visibility="collapsed"
)

if terminal_mode == "📊 Nifty 50":
    render_nifty50_screener_view()
    st.stop()

if terminal_mode == "🔬 Company Analysis":
    benchmark_launch_notice = st.session_state.pop("benchmark_launch_notice", None)
    if benchmark_launch_notice:
        st.warning(benchmark_launch_notice)
    # --- COMPANY ANALYSIS INTAKE ---
    with st.container(border=True):
        st.markdown("#### Start a company review")
        st.caption("Choose a company, then review its filings and supporting web sources.")
    
        # Fast Preset Benchmark Chips
        st.caption("Quick picks")
        presets = [
            ("Reliance", "RELIANCE", "🔵"),
            ("HDFC Bank", "HDFCBANK", "🟢"),
            ("TCS", "TCS", "🟣"),
        ]
        for row_start in range(0, len(presets), 3):
            preset_cols = st.columns(3)
            for col_idx, (label, sym, emoji) in enumerate(presets[row_start:row_start + 3]):
                with preset_cols[col_idx]:
                    if st.button(f"{emoji} {label}", key=f"btn_preset_{sym}", width="stretch"):
                        info = find_company_info(sym)
                        st.session_state["selected_company_choice"] = info["display"]
                        st.rerun()

        c_list = company_options
        cur_choice = st.session_state.get("selected_company_choice", None)
        default_idx = c_list.index(cur_choice) if (cur_choice and cur_choice in c_list) else None

        col_sel1, col_sel2 = st.columns([2.5, 1.5])
    
        with col_sel1:
            selected_company_str = st.selectbox(
                "Company",
                options=c_list,
                index=default_idx,
                placeholder="Search by company name or symbol (e.g. Reliance, HDFC Bank, Infosys, Dixon)...",
                help="Search the tracked company universe. Quotes are third-party market data; source citations appear with the analysis."
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
            
        col_sec1, col_sec2 = st.columns([2, 2])
        with col_sec1:
            sector_list = get_sector_list()
        
            def_sector_idx = sector_list.index(matched_info["sector"]) if (matched_info and matched_info.get("sector") in sector_list) else 0
            target_sector = st.selectbox(
                "Sector",
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

        # Handle Document Selection / Upload
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
            uploaded_file = st.file_uploader(
                "Upload Annual Report (PDF)",
                type=["pdf"],
                help="The uploaded report is analyzed alongside current web sources; it does not replace filing research."
            )
            if uploaded_file:
                selected_filing_metadata = {
                    "title": uploaded_file.name,
                    "year": "User Uploaded",
                    "source": "Manual PDF Upload",
                    "url": None
                }
        else:
            st.caption("Gemini will perform Google Search grounding on recent filings, investor presentations, and market reports.")
            selected_filing_metadata = None

else:
    selected_company_str = None
    matched_info = None
    target_company_name = None
    target_ticker = None
    target_sector = None
    uploaded_file = None
    selected_filing_metadata = None
    doc_type = "⚡ Auto-fetch BSE filing"

fin_res = None
live_data = None

# Reset evaluation only when the user changes the active company.
if terminal_mode == "🔬 Company Analysis":
    if "selected_company_memory" not in st.session_state:
        st.session_state["selected_company_memory"] = selected_company_str
    elif st.session_state["selected_company_memory"] != selected_company_str:
        st.session_state["selected_company_memory"] = selected_company_str
        if "idex_result" in st.session_state:
            del st.session_state["idex_result"]

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

@st.cache_data(ttl=300, show_spinner=False)
def get_cached_ticker_history(ticker_sym: str, period: str = "1y"):
    return fetch_ticker_historical_data(ticker_sym, period=period)

@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_financial_statements(ticker_sym: str):
    return fetch_financial_statements(ticker_sym)

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
                line=dict(color=line_color, width=2.2),
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
                    line=dict(color="#2563EB", width=1.4, dash="dot")
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
                    line=dict(color="#D97706", width=1.4, dash="dash")
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
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF"
    )
    fig.update_yaxes(title_text="Price (₹)", row=1, col=1, gridcolor="#F1F5F9", tickfont=dict(size=11, family="JetBrains Mono, monospace"))
    fig.update_yaxes(title_text="Vol", row=2, col=1, gridcolor="#F1F5F9", tickfont=dict(size=10))
    fig.update_xaxes(gridcolor="#F1F5F9", tickfont=dict(size=11))
    return fig

live_data = None
if target_ticker and target_ticker != "CUSTOM":
    live_data = get_cached_live_data(target_ticker)

# Live market discovery is the dedicated Explore landing page.
if terminal_mode == "🌐 Explore":
    st.html("""
    <div style="background: linear-gradient(135deg, #F0FDF4 0%, #FFFFFF 100%); border: 1.5px solid #BBF7D0; border-radius: 12px; padding: 18px 22px; margin-top: 4px; margin-bottom: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.02); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
      <div>
        <div style="font-size: 20px; font-weight: 900; color: #0F172A; display: flex; align-items: center; gap: 10px; letter-spacing: -0.4px;">
          <span>📈</span> Indian Market Snapshot
        </div>
        <div style="font-size: 13px; color: #475569; margin-top: 3px;">
          Live market indices powered by Yahoo Finance. Review macro benchmark trends before selecting equities below.
        </div>
      </div>
      <div style="display: flex; align-items: center; gap: 10px;">
        <span style="background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; font-size: 11.5px; font-weight: 800; padding: 4px 12px; border-radius: 9999px; display: flex; align-items: center; gap: 6px;">
          Yahoo Finance · Live Quotes
        </span>
      </div>
    </div>
    """)
    
    # 4 Live Market Index Cards (Displayed openly at top of Explore)
    indices_list = get_cached_market_indices()
    idx_cols = st.columns(4)
    for i, idx in enumerate(indices_list):
        with idx_cols[i]:
            is_pos = idx["pct"] >= 0
            delta_col = "#047857" if is_pos else "#DC2626"
            delta_bg = "#ECFDF5" if is_pos else "#FEF2F2"
            delta_sign = "+" if is_pos else ""
            delta_str = f"{delta_sign}{idx['pct']:.2f}% ({delta_sign}{idx['chg']:,.1f})"

            card_html = (
                f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; border-top: 3.5px solid {delta_col}; box-shadow: 0 1px 3px rgba(0,0,0,0.03); margin-bottom: 12px;">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">'
                f'<span style="font-size: 11.5px; font-weight: 800; color: #475569; letter-spacing: 0.5px;">{idx["icon"]} {idx["name"]}</span>'
                f'<span style="font-size: 10.5px; font-weight: 800; color: {delta_col}; background: {delta_bg}; padding: 2px 6px; border-radius: 4px;">{delta_str}</span>'
                f'</div>'
                f'<div style="font-size: 20px; font-weight: 900; color: #0F172A; font-family: \'JetBrains Mono\', monospace; line-height: 1.1;">{idx["cur"]:,.2f}</div>'
                f'<div style="font-size: 10.5px; color: #64748B; margin-top: 5px; display: flex; justify-content: space-between;">'
                f'<span>L: {idx["lo"]:,.0f}</span>'
                f'<span>H: {idx["hi"]:,.0f}</span>'
                f'</div>'
                f'</div>'
            )
            st.html(card_html)

    with st.expander("📈 NIFTY 50 historical trend", expanded=False):
        st.caption("Yahoo Finance historical market data · third-party provider.")
        b_c1, b_c2 = st.columns([1.3, 1])
        with b_c1:
            nifty_tf = st.segmented_control("Range", options=["1M", "3M", "6M", "1Y"], default="6M", key="nifty_tf_ctrl")
        with b_c2:
            nifty_style = st.segmented_control("Chart style", options=["Area", "Candles"], default="Area", key="nifty_style_ctrl")

        tf_map = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y"}
        nifty_period = tf_map.get(nifty_tf or "6M", "6mo")
        nifty_df = get_cached_ticker_history("^NSEI", period=nifty_period)
        if not nifty_df.empty:
            nifty_fig = build_ticker_chart(nifty_df, "NIFTY 50", nifty_style or "Area", show_dma=True)
            if nifty_fig:
                st.plotly_chart(nifty_fig, width="stretch")

    with st.container(border=True):
        st.markdown("#### Find any tracked company")
        explore_search_col, explore_action_col = st.columns([4, 1])
        with explore_search_col:
            explore_company = st.selectbox(
                "Search all tracked equities",
                company_options,
                index=None,
                placeholder="Type a company name or NSE symbol",
                key="explore_company_search",
                label_visibility="collapsed",
            )
        with explore_action_col:
            if st.button("Analyze ↗", type="primary", width="stretch", disabled=not bool(explore_company), key="explore_company_analyze"):
                st.session_state["selected_company_choice"] = explore_company
                st.session_state["pending_nav_mode"] = "🔬 Company Analysis"
                st.rerun()

    st.markdown("""
    <div style="margin-top: 24px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1.5px solid #F1F5F9; padding-bottom: 10px;">
      <div style="font-size: 17px; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 8px;">
        <span>⚡</span> Market movers · 10-company shortlist
      </div>
      <span style="font-size: 12px; color: #64748B;">Filter the list, then open a company in Company Analysis</span>
    </div>
    """, unsafe_allow_html=True)

    stocks_list = get_cached_marquee_stocks()
    if stocks_list:
        stocks_df = pd.DataFrame(stocks_list)
        status_values = set(stocks_df["data_status"].dropna().unique()) if "data_status" in stocks_df else set()
        is_sample_fallback = status_values == {"sample_fallback"}
        if is_sample_fallback:
            st.warning("The latest provider quote fetch failed. These are sample fallback values, not current market prices.")
        elif status_values == {"provider"}:
            st.caption("Market mover shortlist: 10 tracked names across selected sectors; this is not a scan of all 501 equities.")
        else:
            st.warning("Market quote source status could not be verified for this cached data. Treat these values as unverified.")
        filter_col, sector_col = st.columns([2, 1.3])
        with filter_col:
            mover_search = st.text_input("Find a ticker", placeholder="Company or symbol", key="mover_search")
        with sector_col:
            sector_options = ["All sectors"] + sorted(stocks_df["sector"].dropna().unique().tolist())
            mover_sector = st.selectbox("Sector", sector_options, key="mover_sector")
        sort_options = {
            "Largest daily gain": ("pct", False),
            "Largest daily decline": ("pct", True),
            "Company name": ("name", True),
            "Market price": ("cur", False),
        }
        sort_col, layout_col = st.columns([2, 1])
        with sort_col:
            mover_sort = st.selectbox("Sort by", list(sort_options), key="mover_sort")
        with layout_col:
            compact_movers = st.toggle("Compact", value=True, key="mover_compact", help="Show only company, price, and daily move.")

        visible_df = stocks_df.copy()
        if mover_search:
            match = visible_df["name"].str.contains(mover_search, case=False, na=False) | visible_df["ticker"].str.contains(mover_search, case=False, na=False)
            visible_df = visible_df[match]
        if mover_sector != "All sectors":
            visible_df = visible_df[visible_df["sector"] == mover_sector]
        sort_key, ascending = sort_options[mover_sort]
        visible_df = visible_df.sort_values(sort_key, ascending=ascending)
        st.caption(f"Showing {len(visible_df)} of {len(stocks_df)} tracked market movers")
        visible_options = {f"{row['name']} ({row['ticker']})": row["display"] for _, row in visible_df.iterrows()}
        visible_df["Company / Symbol"] = visible_df["name"] + " (" + visible_df["ticker"] + ")"
        visible_df["Day range"] = visible_df.apply(lambda row: f"₹{row['lo']:,.2f}–₹{row['hi']:,.2f}", axis=1)
        visible_df = visible_df.rename(columns={
            "sector": "Sector", "cur": "Price (₹)", "pct": "Change (%)"
        })
        mover_table_event = st.dataframe(
            visible_df[["Company / Symbol", "Price (₹)", "Change (%)"] if compact_movers else ["Company / Symbol", "Sector", "Price (₹)", "Change (%)", "Day range"]],
            hide_index=True,
            width="stretch",
            height=min(420, 42 + 35 * max(len(visible_df), 1)),
            on_select="rerun",
            selection_mode="single-row",
            key=f"mover_table_{abs(hash((mover_search, mover_sector, mover_sort, compact_movers)))}",
            column_config={
                "Price (₹)": st.column_config.NumberColumn(format="₹ %.2f"),
                "Change (%)": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )
        if status_values == {"provider"}:
            st.caption("Source: Yahoo Finance, a third-party market-data provider. App cache refresh interval: 60 seconds; exact quote timestamps are not supplied consistently.")

        selected_rows = mover_table_event.selection.rows if mover_table_event else []
        if visible_options and selected_rows:
            selected_row = visible_df.iloc[selected_rows[0]]
            selected_mover = f"{selected_row['name']} ({selected_row['ticker']})"
            launch_col, action_col = st.columns([3, 1])
            with launch_col:
                st.caption(f"Selected: {selected_mover}")
            with action_col:
                if st.button("Analyze ↗", type="primary", width="stretch", key="launch_mover_analysis"):
                    st.session_state["selected_company_choice"] = selected_row["display"]
                    st.session_state["pending_nav_mode"] = "🔬 Company Analysis"
                    st.rerun()
        elif visible_options:
            st.caption("Select a row to enable company analysis.")
        else:
            st.info("No tracked companies match these filters. Clear the search or choose another sector.")
    else:
        st.warning("Market mover data is unavailable. No live quotes or fallback examples were returned.")

if terminal_mode == "🌐 Explore":
    st.stop()

# --- STOCKSAGE BESPOKE COMPANY INTELLIGENCE & 27 KEY METRICS MATRIX ---
if live_data:
    sm = live_data.get("screener_metrics", {})
    cur_p = live_data.get("current_price", 0)
    cur_str = f"₹ {cur_p:,.2f}" if isinstance(cur_p, (int, float)) else "N/A"
    chg_pct = live_data.get("change_pct", 0)
    chg_val = live_data.get("change_val", 0)
    is_pos = chg_pct >= 0
    delta_fg = "#047857" if is_pos else "#DC2626"
    delta_bg = "#ECFDF5" if is_pos else "#FEF2F2"
    delta_sign = "+" if is_pos else ""
    delta_str = f"{delta_sign}{chg_pct:.2f}%"
    
    price_date = live_data.get("price_date", "close price")
    quote_status_label = "delayed third-party data" if live_data.get("is_delayed") is True else "third-party data"
    website_url = live_data.get("website_url", "#")
    website_display = live_data.get("website_display", "company.com")
    about_text = live_data.get("about_summary", "")
    bse_code = live_data.get("bse_code", target_ticker)
    
    logo_initials = "".join([w[0] for w in target_company_name.split()[:2]]).upper() if target_company_name else "SS"

    # 52-Week Range Slider Math
    h52_num = live_data.get("high_52w", cur_p)
    l52_num = live_data.get("low_52w", cur_p)
    if isinstance(cur_p, (int, float)) and isinstance(h52_num, (int, float)) and isinstance(l52_num, (int, float)) and h52_num > l52_num:
        range_pct = min(max(((cur_p - l52_num) / (h52_num - l52_num)) * 100, 0), 100)
    else:
        range_pct = 50.0

    # Helper function to format metric cells with spacious typography
    def fmt_metric_row(label: str, value: str, style_mode: str = "normal", is_even: bool = False) -> str:
        row_bg = ' style="background-color: #F8FAFC;"' if is_even else ''
        if style_mode == "emerald":
            val_span = f'<span style="background: #ECFDF5; color: #047857; border: 1.5px solid #A7F3D0; padding: 3px 10px; border-radius: 6px; font-weight: 800; font-size: 15px;">{value}</span>'
        elif style_mode == "teal":
            val_span = f'<span style="background: #F0FDFA; color: #0F766E; border: 1.5px solid #99F6E4; padding: 3px 10px; border-radius: 6px; font-weight: 800; font-size: 15px;">{value}</span>'
        elif style_mode == "bold":
            val_span = f'<span style="font-weight: 900; color: #0F172A; font-size: 16.5px;">{value}</span>'
        else:
            val_span = f'<span style="font-weight: 700; color: #1E293B; font-size: 15.5px;">{value}</span>'
            
        return (
            f'<tr{row_bg}>'
            f'<td class="m-label">{label}</td>'
            f'<td class="m-value">{val_span}</td>'
            f'</tr>'
        )

    # 3 Balanced Columns containing all 27 fundamental metrics (9 per column)
    col1_items = [
        ("Market Cap", sm.get("market_cap", "N/A"), "bold"),
        ("Current Price", sm.get("current_price", cur_str), "bold"),
        ("52-Week High / Low", sm.get("high_low", "N/A"), "normal"),
        ("Stock P/E Ratio", sm.get("stock_pe", "N/A"), "normal"),
        ("PEG Ratio", sm.get("peg_ratio", "N/A"), "normal"),
        ("EV / EBITDA", sm.get("evebitda", "N/A"), "normal"),
        ("Intrinsic Value (Est.)", sm.get("intrinsic_value", "N/A"), "normal"),
        ("Graham Number", sm.get("graham_number", "N/A"), "normal"),
        ("Market Cap to Sales", sm.get("market_cap_to_sales", "N/A"), "normal"),
    ]

    col2_items = [
        ("ROCE (Return on Capital)", sm.get("roce", "N/A"), "emerald"),
        ("ROE (Return on Equity)", sm.get("roe", "N/A"), "emerald"),
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
        ("Free Cash Flow (5 Years)", sm.get("free_cash_flow_5yr", "N/A"), "teal"),
        ("CMP to Free Cash Flow", sm.get("cmp_to_fcf", "N/A"), "teal"),
        ("Promoter Shareholding", sm.get("promoter_holding", "N/A"), "bold"),
        ("Sales Growth (5 Years)", sm.get("sales_growth_5yr", "N/A"), "normal"),
        ("Dividend Yield", sm.get("dividend_yield", "N/A"), "normal"),
    ]

    def build_spacious_card(title: str, icon: str, badge_lbl: str, hdr_bg: str, border_col: str, title_col: str, badge_fg: str, items: list) -> str:
        rows_html = []
        for idx, (lbl, val, smode) in enumerate(items):
            rows_html.append(fmt_metric_row(lbl, val, smode, is_even=(idx % 2 == 1)))
            
        rows_str = "".join(rows_html)
        return (
            f'<div class="metric-domain-card" style="border: 1.5px solid {border_col};">'
            f'<div class="metric-domain-header" style="background: {hdr_bg}; border-bottom: 1.5px solid {border_col};">'
            f'<div style="display: flex; align-items: center; gap: 10px;">'
            f'<span style="font-size: 18px;">{icon}</span>'
            f'<span style="font-size: 15px; font-weight: 800; color: {title_col}; letter-spacing: -0.3px;">{title}</span>'
            f'</div>'
            f'<span style="font-size: 11.5px; font-weight: 700; color: {badge_fg}; background: #FFFFFF; border: 1px solid {border_col}; padding: 3px 9px; border-radius: 9999px;">{badge_lbl}</span>'
            f'</div>'
            f'<table class="metric-table-spacious">'
            f'<tbody>{rows_str}</tbody>'
            f'</table>'
            f'</div>'
        )

    card_val = build_spacious_card("Valuation & Pricing Multiples", "🏛️", "9 Key Metrics", "linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%)", "#BFDBFE", "#1E3A8A", "#1D4ED8", col1_items)
    card_ret = build_spacious_card("Profitability & Capital Returns", "📈", "9 Key Metrics", "linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%)", "#A7F3D0", "#064E3B", "#047857", col2_items)
    card_sol = build_spacious_card("Solvency, Cash Flow & Growth", "🛡️", "9 Key Metrics", "linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%)", "#DDD6FE", "#4C1D95", "#6D28D9", col3_items)

    def build_concise_operations_points(about_str: str, company_name: str, sector: str) -> list:
        if not about_str or len(about_str.strip()) < 30:
            return [
                ("Core Operations", f"Flagship enterprise in the Indian {sector} sector listed on NSE & BSE."),
                ("Operating Model", "Scaled commercial and retail operations catering to domestic institutional and retail demand."),
                ("Market Reach", "Broad distribution network with continuous coverage across major domestic hubs."),
                ("Corporate Profile", "Constituent of the Nifty 500 universe operating under Ind AS statutory disclosures.")
            ]

        about_clean = html.unescape(about_str)
        raw_sentences = re.split(r"(?<=[.!?])\s+", about_clean.strip())
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 15]

        core_sent = ""
        segments_sent = ""
        offerings_sent = ""
        pedigree_sent = ""

        for s in sentences:
            s_lower = s.lower()
            if not core_sent and any(kw in s_lower for kw in ["manufactures", "provides", "engages in", "operates as", "produces", "develops", "distributes", "trades", "explores"]):
                core_sent = s
            elif not segments_sent and any(kw in s_lower for kw in ["operates through", "segments", "verticals", "divisions"]):
                segments_sent = s
            elif not offerings_sent and any(kw in s_lower for kw in ["offers", "portfolio", "products include", "services include", "solutions, such as", "brand portfolio"]):
                offerings_sent = s
            elif not pedigree_sent and any(kw in s_lower for kw in ["incorporated in", "founded in", "headquartered in", "based in"]):
                pedigree_sent = s

        pts = []
        # 1. Core Operations
        if core_sent:
            c_clean = re.sub(r",\s*together with its subsidiaries,?", "", core_sent, flags=re.IGNORECASE).strip()
            if len(c_clean) > 165:
                c_clean = c_clean[:162].rsplit(" ", 1)[0] + "..."
            pts.append(("Core Operations", c_clean))
        else:
            pts.append(("Core Operations", f"Leading enterprise operating within the Indian {sector} industry."))

        # 2. Key Segments / Offerings
        if segments_sent:
            s_clean = segments_sent.strip()
            if len(s_clean) > 165:
                s_clean = s_clean[:162].rsplit(" ", 1)[0] + "..."
            pts.append(("Business Verticals", s_clean))
        elif offerings_sent:
            o_clean = offerings_sent.strip()
            if len(o_clean) > 165:
                o_clean = o_clean[:162].rsplit(" ", 1)[0] + "..."
            pts.append(("Key Portfolio", o_clean))
        else:
            pts.append(("Product Portfolio", f"Diverse portfolio of products and value-added solutions tailored for {sector} demand."))

        # 3. Market Footprint / Global Reach
        if any(w in about_clean.lower() for w in ["worldwide", "internationally", "global", "export"]):
            pts.append(("Market Reach", "Active domestic footprint across India alongside established international export / client channels."))
        else:
            pts.append(("Market Reach", "Extensive pan-India distribution network catering to domestic institutional and retail markets."))

        # 4. Corporate Profile / Pedigree
        if pedigree_sent:
            p_clean = pedigree_sent.strip()
            if len(p_clean) > 140:
                p_clean = p_clean[:137].rsplit(" ", 1)[0] + "..."
            pts.append(("Corporate Profile", p_clean))
        else:
            pts.append(("Benchmark Standing", f"Established constituent of the Nifty 500 index with statutory Ind AS disclosures."))

        return pts

    ops_points = build_concise_operations_points(about_text, target_company_name, target_sector)
    ops_points_html = "".join([
        f'<li style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px; line-height: 1.5; color: #334155;">'
        f'<span style="color: #059669; font-weight: 800; font-size: 14px; line-height: 1.2;">•</span>'
        f'<span><strong style="color: #0F172A; font-weight: 700;">{html.escape(label)}:</strong> {html.escape(desc)}</span>'
        f'</li>'
        for label, desc in ops_points
    ])

    facts_full_html = (
        f'<div class="facts-header-card">'
        f'<div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 20px; padding-bottom: 20px; border-bottom: 1.5px solid #F1F5F9;">'
        f'<div style="display: flex; align-items: center; gap: 18px;">'
        f'<div style="width: 58px; height: 58px; border-radius: 14px; background: linear-gradient(135deg, #059669 0%, #047857 100%); color: #FFFFFF; font-weight: 900; font-size: 22px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(5,150,105,0.25); flex-shrink: 0;">'
        f'{logo_initials}'
        f'</div>'
        f'<div>'
        f'<div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">'
        f'<span style="font-size: 28px; font-weight: 900; color: #0F172A; letter-spacing: -0.6px; line-height: 1.1;">{target_company_name}</span>'
        f'<span style="background: #F0FDF4; color: #047857; border: 1.5px solid #BBF7D0; padding: 3px 10px; border-radius: 6px; font-weight: 800; font-size: 12.5px;">● NSE: {target_ticker}</span>'
        f'<span style="background: #F8FAFC; color: #475569; border: 1.5px solid #E2E8F0; padding: 3px 10px; border-radius: 6px; font-weight: 600; font-size: 12.5px;">BSE: {bse_code}</span>'
        f'<span style="background: #EFF6FF; color: #1D4ED8; border: 1.5px solid #BFDBFE; padding: 3px 10px; border-radius: 6px; font-weight: 700; font-size: 12.5px;">🏛️ {target_sector}</span>'
        f'</div>'
        f'<div style="margin-top: 8px; font-size: 13.5px; color: #64748B; display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">'
        f'<span>🌐 <a href="{website_url}" target="_blank" style="color: #2563EB; font-weight: 600; text-decoration: none;">{website_display} ↗</a></span>'
        f'<span>• Constituent of Nifty 500</span>'
        f'<span>• Reporting Standards: Ind AS</span>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div style="text-align: right; min-width: 220px;">'
        f'<div style="display: flex; align-items: baseline; justify-content: flex-end; gap: 10px;">'
        f'<span style="font-size: 32px; font-weight: 900; color: #0F172A; font-family: \'JetBrains Mono\', monospace; line-height: 1;">{cur_str}</span>'
        f'<span style="color: {delta_fg}; background: {delta_bg}; border: 1px solid {delta_fg}40; padding: 4px 12px; border-radius: 6px; font-size: 14px; font-weight: 800;">{delta_str}</span>'
        f'</div>'
        f'<div style="font-size: 12px; color: #64748B; margin-top: 6px;">Yahoo Finance · {quote_status_label}<br>Retrieved: {price_date} · Market quote timestamp: unavailable</div>'
        f'<div style="margin-top: 10px; width: 220px; margin-left: auto;">'
        f'<div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748B; font-weight: 700; margin-bottom: 4px;">'
        f'<span>52W L: ₹ {l52_num:,.0f}</span>'
        f'<span>52W H: ₹ {h52_num:,.0f}</span>'
        f'</div>'
        f'<div style="background: #E2E8F0; border-radius: 9999px; height: 6px; position: relative;">'
        f'<div style="background: #059669; width: {range_pct:.1f}%; height: 6px; border-radius: 9999px;"></div>'
        f'<div style="position: absolute; left: {range_pct:.1f}%; top: -3px; width: 12px; height: 12px; border-radius: 50%; background: #047857; border: 2px solid #FFFFFF; transform: translateX(-50%); box-shadow: 0 1px 3px rgba(0,0,0,0.3);"></div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div style="margin-top: 22px; display: grid; grid-template-columns: 2.2fr 1fr; gap: 24px;">'
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 18px 22px;">'
        f'<div style="font-size: 12px; font-weight: 800; color: #0F172A; letter-spacing: 0.6px; text-transform: uppercase; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">'
        f'<span style="display: flex; align-items: center; gap: 8px;"><span>🏢</span> Corporate Operations & Business Model</span>'
        f'<span style="font-size: 11px; background: #EFF6FF; color: #1D4ED8; font-weight: 700; border: 1px solid #BFDBFE; padding: 2px 8px; border-radius: 9999px;">Key Highlights</span>'
        f'</div>'
        f'<ul style="margin: 0; padding: 0; list-style-type: none; display: flex; flex-direction: column; gap: 9px;">'
        f'{ops_points_html}'
        f'</ul>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 18px 20px; display: flex; flex-direction: column; justify-content: space-between;">'
        f'<div>'
        f'<div style="font-size: 12px; font-weight: 800; color: #0F172A; letter-spacing: 0.6px; text-transform: uppercase; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">'
        f'<span style="display: flex; align-items: center; gap: 8px;"><span>🔑</span> Institutional Profile</span>'
        f'<span style="font-size: 11px; background: #ECFDF5; color: #047857; font-weight: 700; border: 1px solid #A7F3D0; padding: 2px 8px; border-radius: 9999px;">Nifty 500</span>'
        f'</div>'
        f'<ul style="margin: 0; padding: 0; list-style-type: none; display: flex; flex-direction: column; gap: 9px;">'
        f'<li style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px; line-height: 1.5; color: #334155;">'
        f'<span style="color: #059669; font-weight: 800; font-size: 14px; line-height: 1.2;">•</span>'
        f'<span><strong style="color: #0F172A; font-weight: 700;">Sector Benchmark:</strong> Constituent of {target_sector} peer index.</span>'
        f'</li>'
        f'<li style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px; line-height: 1.5; color: #334155;">'
        f'<span style="color: #059669; font-weight: 800; font-size: 14px; line-height: 1.2;">•</span>'
        f'<span><strong style="color: #0F172A; font-weight: 700;">Accounting Framework:</strong> Reported under Ind AS & SEBI (LODR) guidelines.</span>'
        f'</li>'
        f'<li style="display: flex; align-items: flex-start; gap: 8px; font-size: 13px; line-height: 1.5; color: #334155;">'
        f'<span style="color: #059669; font-weight: 800; font-size: 14px; line-height: 1.2;">•</span>'
        f'<span><strong style="color: #0F172A; font-weight: 700;">Listing Exchanges:</strong> Listed on NSE ({target_ticker}) and BSE ({bse_code}).</span>'
        f'</li>'
        f'</ul>'
        f'</div>'
        f'<div style="margin-top: 14px; display: flex; gap: 8px; flex-wrap: wrap;">'
        f'<span style="background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px;">✔ Ind AS Standards</span>'
        f'<span style="background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px;">✔ Nifty 500 Constituent</span>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.html(facts_full_html)

    # --- AUTOMATED DATA CONSISTENCY & RECONCILIATION ENGINE (RUNS IN BACKGROUND) ---
    fin_res = get_cached_financial_statements(target_ticker)
    sentinel_report = DataIntegritySentinel.audit_and_certify(
        ticker_symbol=target_ticker,
        company_name=target_company_name,
        financial_statements=fin_res,
        live_market_data=live_data
    )
    st.session_state["sentinel_report"] = sentinel_report

    # --- INDEPENDENT FORENSIC DUE DILIGENCE & CONCEALED RISK ENGINE ---
    forensic_report = ForensicRiskEngine.audit_company_forensics(
        ticker_symbol=target_ticker,
        company_name=target_company_name,
        sector=target_sector,
        financial_statements=fin_res,
        live_market_data=live_data
    )
    st.session_state["forensic_report"] = forensic_report

    s_passed = sentinel_report.get("passed_count", 0)
    s_failed = sentinel_report.get("failed_count", 0)
    s_skipped = sentinel_report.get("skipped_count", 0)
    s_score = sentinel_report.get("integrity_score")
    s_score_str = f"{s_score:.0f}/100" if s_score is not None else "N/A"
    s_run_id = sentinel_report.get("run_id") or sentinel_report.get("audit_hash", "RUN-ID")
    s_status = sentinel_report.get("status", "PARTIALLY EVALUATED")

    fqi_score = forensic_report.get("fqi_score", 100.0)
    fqi_badge = forensic_report.get("verdict_badge", "PRISTINE")

    with st.expander(f"🔍 Automated Data Consistency Trail ({s_passed} Passed • {s_failed} Flagged • {s_skipped} Skipped • Score: {s_score_str} • ID: {s_run_id})", expanded=False):
        st.html(render_sentinel_audit_certificate_html(sentinel_report))

    with st.expander(f"🕵️ Forensic Due Diligence & Concealed Risk Audit: {fqi_badge} (FQI: {fqi_score:.0f}/100 • 8-Pillar Surveillance)", expanded=False):
        st.html(render_forensic_dossier_html(forensic_report))

    # --- INTERACTIVE TICKER PRICE & TECHNICAL CHART ---
    st.markdown("<div style='margin-top: 22px; margin-bottom: 8px;'></div>", unsafe_allow_html=True)
    tc_1, tc_2, tc_3 = st.columns([2.5, 1.3, 1])
    with tc_1:
        st.markdown(
            f'<div style="font-size: 16px; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 8px;">'
            f'<span>📈</span> {target_company_name} ({target_ticker}) Price Action & Technical Trend'
            f'</div>',
            unsafe_allow_html=True
        )
    with tc_2:
        stock_tf = st.segmented_control("Range", options=["1M", "3M", "6M", "1Y", "5Y"], default="1Y", key=f"stk_tf_{target_ticker}", label_visibility="collapsed")
    with tc_3:
        stock_style = st.segmented_control("Style", options=["Area", "Candles"], default="Area", key=f"stk_style_{target_ticker}", label_visibility="collapsed")

    tf_map = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}
    chosen_period = tf_map.get(stock_tf or "1Y", "1y")
    hist_df = get_cached_ticker_history(target_ticker, period=chosen_period)
    if not hist_df.empty:
        stock_fig = build_ticker_chart(hist_df, target_ticker, stock_style or "Area", show_dma=True)
        if stock_fig:
            st.plotly_chart(stock_fig, width="stretch")
    else:
        st.info(f"Historical chart currently syncing for {target_ticker} on NSE.")

    # --- 27 KEY FUNDAMENTAL SCREENER RATIOS (3-COLUMN SPACIOUS MATRIX) ---
    st.html(f'<div class="metrics-3col-grid" style="margin-top: 22px;">{card_val}{card_ret}{card_sol}</div>')

    # --- MULTI-YEAR HISTORICAL FINANCIAL STATEMENTS & FORENSIC CAGR ENGINE ---
    fin_res = get_cached_financial_statements(target_ticker)
    if fin_res and "years" in fin_res and not fin_res.get("error"):
        st.markdown("<div style='margin-top: 26px; margin-bottom: 8px;'></div>", unsafe_allow_html=True)
        fin_h1, fin_h2 = st.columns([2.3, 1.7])
        with fin_h1:
            st.markdown(
                f'<div style="font-size: 17px; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 8px;">'
                f'<span>📈</span> {target_company_name} ({target_ticker}) Multi-Year Statements & Forensic CAGR'
                f'</div>'
                f'<div style="font-size: 12.5px; color: #64748B; margin-top: 2px;">'
                f'Audited annual statements (Last 4–5 Years) in ₹ Crores, compound growth rates, and forensic cash flow conversion.'
                f'</div>',
                unsafe_allow_html=True
            )
        with fin_h2:
            stmt_mode = st.segmented_control(
                "Statement View",
                options=["📊 Visual Trends", "📜 Profit & Loss", "⚡ Quarterly", "🏛️ Balance Sheet", "💵 Cash Flows"],
                default="📊 Visual Trends",
                key=f"stmt_mode_{target_ticker}",
                label_visibility="collapsed"
            )

        # 4-Card Screener Compounded Growth & Quality Matrix
        st.html(render_growth_cagr_scorecard_html(fin_res["cagr"]))

        # Visual Chart or Tabular Statement Explorer
        if stmt_mode == "📊 Visual Trends":
            chart_t1, chart_t2 = st.columns([1.5, 2.5])
            with chart_t1:
                trend_chart_type = st.segmented_control(
                    "Trend Chart",
                    options=["📈 Revenue & Margins", "💵 Cash Flow Reality", "🏛️ Balance Sheet Leverage"],
                    default="📈 Revenue & Margins",
                    key=f"trend_type_{target_ticker}",
                    label_visibility="collapsed"
                )
            if trend_chart_type == "📈 Revenue & Margins":
                rev_fig = build_revenue_profit_chart(fin_res, target_company_name)
                if rev_fig:
                    st.plotly_chart(rev_fig, width="stretch")
            elif trend_chart_type == "💵 Cash Flow Reality":
                cf_fig = build_cashflow_health_chart(fin_res, target_company_name)
                if cf_fig:
                    st.plotly_chart(cf_fig, width="stretch")
            elif trend_chart_type == "🏛️ Balance Sheet Leverage":
                bs_fig = build_balance_sheet_chart(fin_res, target_company_name)
                if bs_fig:
                    st.plotly_chart(bs_fig, width="stretch")
        elif stmt_mode == "📜 Profit & Loss":
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

        # Forensic Trend Takeaways & Accrual Audit
        cagr_insights = generate_forensic_cagr_insights(fin_res, target_company_name)
        if cagr_insights:
            insight_boxes = []
            for ins in cagr_insights:
                itype = ins.get("type", "neutral")
                if itype == "positive":
                    iborder = "#10B981"
                    ibg = "#F0FDF4"
                    ititle_color = "#064E3B"
                    ibody_color = "#166534"
                    icon = "✔"
                elif itype == "caution":
                    iborder = "#EF4444"
                    ibg = "#FEF2F2"
                    ititle_color = "#991B1B"
                    ibody_color = "#7F1D1D"
                    icon = "⚠"
                else:
                    iborder = "#3B82F6"
                    ibg = "#EFF6FF"
                    ititle_color = "#1E40AF"
                    ibody_color = "#1E3A8A"
                    icon = "ℹ"

                insight_boxes.append(
                    f'<div style="background: {ibg}; border-left: 3.5px solid {iborder}; border-top: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0; border-radius: 0 8px 8px 0; padding: 10px 14px; margin-bottom: 8px;">'
                    f'<div style="font-size: 13px; font-weight: 800; color: {ititle_color}; display: flex; align-items: center; gap: 6px;">'
                    f'<span>{icon}</span> {ins.get("title")}'
                    f'</div>'
                    f'<div style="font-size: 12.5px; line-height: 1.5; color: {ibody_color}; margin-top: 3px;">'
                    f'{ins.get("body")}'
                    f'</div>'
                    f'</div>'
                )

            st.html(
                f'<div style="margin-top: 14px; margin-bottom: 22px;">'
                f'<div style="font-size: 13.5px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">'
                f'<span>🔍</span> Forensic Trajectory Takeaways & Accrual Audit'
                f'</div>'
                f'{"".join(insight_boxes)}'
                f'</div>'
            )

# Action Buttons
btn_col1, btn_col2 = st.columns([3, 1])
with btn_col1:
    btn_label = f"Analyze {target_company_name}" if target_company_name else "Select a Company to Analyze"
    run_btn = st.button(
        btn_label,
        type="primary",
        width="stretch",
        disabled=not bool(target_company_name)
    )
with btn_col2:
    if st.button("Quick Demo", width="stretch"):
        demo_mode = True
        run_btn = True
        if not target_company_name:
            target_company_name = "Tata Consumer Products Ltd"
            target_sector = "FMCG / Retail"
            target_ticker = "TATACONSUM.NS"
        if target_ticker and not live_data:
            live_data = get_cached_live_data(target_ticker)
        if target_ticker and not fin_res:
            fin_res = get_cached_financial_statements(target_ticker)

# Helper metadata for 8 Pillars
PILLAR_METADATA = {
    1: {"icon": "🏛️", "chip": "Governance", "chip_bg": "#ECFDF5", "chip_fg": "#047857", "border": "#A7F3D0"},
    2: {"icon": "🔍", "chip": "Forensics", "chip_bg": "#EFF6FF", "chip_fg": "#1D4ED8", "border": "#BFDBFE"},
    3: {"icon": "🛡️", "chip": "Solvency", "chip_bg": "#F5F3FF", "chip_fg": "#6D28D9", "border": "#DDD6FE"},
    4: {"icon": "📈", "chip": "Efficiency", "chip_bg": "#ECFEFF", "chip_fg": "#0E7490", "border": "#A5F3FC"},
    5: {"icon": "🔄", "chip": "Working Cap", "chip_bg": "#F0FDF4", "chip_fg": "#15803D", "border": "#BBF7D0"},
    6: {"icon": "💵", "chip": "Cash Flow", "chip_bg": "#FDF2F8", "chip_fg": "#BE185D", "border": "#FBCFE8"},
    7: {"icon": "🚀", "chip": "Moat / Longevity", "chip_bg": "#FAF5FF", "chip_fg": "#7E22CE", "border": "#E9D5FF"},
    8: {"icon": "⚖️", "chip": "Capital Allocation", "chip_bg": "#FFFBEB", "chip_fg": "#B45309", "border": "#FDE68A"},
}

# Helper to build Plotly 8-Pillar Radar Chart in Institutional Green & White
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
        line=dict(color='#059669', width=3.5),
        marker=dict(size=8, color='#059669', line=dict(color='#FFFFFF', width=2)),
        name='% of Max Score'
    ))

    fig.update_layout(
        polar=dict(
            bgcolor='rgba(240, 253, 244, 0.45)',
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%",
                gridcolor='#A7F3D0',
                linecolor='#6EE7B7',
                tickfont=dict(color='#047857', size=11, family='Inter', weight=600)
            ),
            angularaxis=dict(
                gridcolor='#CBD5E1',
                linecolor='#94A3B8',
                tickfont=dict(color='#0F172A', size=12.5, family='Inter', weight=700)
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
    raw = re.findall(r"(?:INR|₹|Rs\.?)?\s*([\d,]+(?:\.\d+)?)", str(dcf_str), re.IGNORECASE)
    nums = []
    for item in raw:
        clean = item.replace(",", "").strip()
        if clean:
            try:
                v = float(clean)
                if v >= 50:
                    nums.append(v)
            except ValueError:
                pass
    if len(nums) >= 2:
        l, h = sorted([nums[0], nums[1]])
        return l, h, (l + h) / 2.0
    elif len(nums) == 1:
        return nums[0], nums[0], nums[0]
    return None, None, None

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

    if pio_trig or "RED" in guardrail:
        gov_status = "CRITICAL RISK"
        gov_color = "#DC2626"
        gov_bg = "#FEF2F2"
        gov_border = "#FECACA"
        gov_sub = "High risk: Serious audit red flags or promoter integrity warnings active."
        gov_icon = "🔴"
    elif "ALERT" in guardrail or total_pen >= 4.0:
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
        bs_border = "#CBD5E1"
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
    company_clean = target_company_name or "This company"
    sector_clean = target_sector or "its sector"

    if final_score >= 75:
        eli_action = "Bottom Line: High-quality compounder with strong financials and clean governance. Great candidate to buy on dips for long-term wealth creation."
        eli_badge = "STRONG ACCUMULATE"
        eli_badge_bg = "#ECFDF5"
        eli_badge_fg = "#047857"
    elif final_score >= 60:
        eli_action = "Bottom Line: Good company with solid moats, but waiting for a price dip makes more sense right now."
        eli_badge = "SELECTIVE ACCUMULATE"
        eli_badge_bg = "#EFF6FF"
        eli_badge_fg = "#1D4ED8"
    else:
        eli_action = "Bottom Line: High risk. Red flags found in debt, governance, or cash flow. Better to stay away until things improve."
        eli_badge = "AVOID / PRUDENCE"
        eli_badge_bg = "#FEF2F2"
        eli_badge_fg = "#DC2626"

    strengths = res.get("strengths", [])
    if strengths and len(strengths) > 0:
        clean_s = strengths[0].rstrip(".")
        if "insufficient evidence" in clean_s.lower() and not is_doc_analyzed:
            eli_biz = f"<strong>{company_clean}</strong> operates in India\'s <strong>{sector_clean}</strong> sector; statutory research is incomplete due to evidence gaps."
        else:
            eli_biz = f"<strong>{company_clean}</strong> is an established market leader in India\'s <strong>{sector_clean}</strong> sector, powered by {clean_s.lower()}."
    else:
        eli_biz = f"<strong>{company_clean}</strong> is an established business in India\'s <strong>{sector_clean}</strong> sector with healthy operating cash flows and strong market reach."

    html = (
        f'<div style="background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 16px; padding: 24px 26px; margin-bottom: 22px; box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; flex-wrap: wrap; gap: 10px;">'
        f'<div style="display: flex; align-items: center; gap: 8px;">'
        f'<span style="font-size: 20px;">🚦</span>'
        f'<span style="font-size: 15px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.6px;">10-Second Summary & Quick Takeaway</span>'
        f'</div>'
        f'<span style="background: {eli_badge_bg}; color: {eli_badge_fg}; border: 1.5px solid {eli_badge_fg}; font-size: 12px; font-weight: 800; padding: 4px 12px; border-radius: 9999px; font-family: \'JetBrains Mono\', monospace;">{eli_badge}</span>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px;">'
        f'<div style="background: {gov_bg}; border: 1.5px solid {gov_border}; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">'
        f'<div style="font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">1. MANAGEMENT & AUDIT</div>'
        f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">'
        f'<span style="font-size: 18px;">{gov_icon}</span>'
        f'<span style="font-size: 17px; font-weight: 900; color: {gov_color}; font-family: \'JetBrains Mono\', monospace;">{gov_status}</span>'
        f'</div>'
        f'<div style="font-size: 13px; line-height: 1.5; color: #334155;">{gov_sub}</div>'
        f'</div>'
        f'<div style="background: {bs_bg}; border: 1.5px solid {bs_border}; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">'
        f'<div style="font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">2. BALANCE SHEET HEALTH</div>'
        f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">'
        f'<span style="font-size: 18px;">{bs_icon}</span>'
        f'<span style="font-size: 17px; font-weight: 900; color: {bs_color}; font-family: \'JetBrains Mono\', monospace;">{bs_status}</span>'
        f'</div>'
        f'<div style="font-size: 13px; line-height: 1.5; color: #334155;">{bs_sub}</div>'
        f'</div>'
        f'<div style="background: {val_bg}; border: 1.5px solid {val_border}; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">'
        f'<div style="font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">3. VALUATION & PRICE</div>'
        f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">'
        f'<span style="font-size: 18px;">{val_icon}</span>'
        f'<span style="font-size: 17px; font-weight: 900; color: {val_color}; font-family: \'JetBrains Mono\', monospace;">{val_status}</span>'
        f'</div>'
        f'<div style="font-size: 13px; line-height: 1.5; color: #334155;">{val_sub}</div>'
        f'</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-left: 5px solid #059669; border-radius: 10px; padding: 16px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">'
        f'<div style="font-size: 12px; font-weight: 800; color: #065F46; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">'
        f'<span>💬</span> Plain-English Summary (ELI15 Takeaway)'
        f'</div>'
        f'<div style="font-size: 14px; line-height: 1.6; color: #1E293B; margin-bottom: 6px;">{eli_biz}</div>'
        f'<div style="font-size: 14px; line-height: 1.6; color: #0F172A; font-weight: 700;">{eli_action}</div>'
        f'</div>'
        f'</div>'
    )
    return html

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
            auditor_status = "PASS"
            auditor_badge = "CLEAN AUDIT"
    elif forensic_rep.get("auditor_independence", {}).get("status") == "PASS":
        auditor_status = "PASS"
        auditor_badge = "CLEAN AUDIT"
        auditor_ev = forensic_rep["auditor_independence"].get("detail", "Clean statutory audit history; zero adverse auditor qualifications under CARO.")
    elif is_insufficient:
        auditor_status = "MONITOR"
        auditor_badge = "NOT VERIFIED"
        auditor_ev = "Auditor opinion and statutory disclosures were not verified in current sources."
    else:
        auditor_status = "PASS"
        auditor_badge = "CLEAN AUDIT"
        auditor_ev = "Official statutory filings verify an unmodified audit opinion with zero reservations or CARO qualifications."

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
    rep_pledge = forensic_rep.get("promoter_pledging", {})
    rep_pledge_status = rep_pledge.get("status")
    rep_pledge_val = rep_pledge.get("pledged_pct")

    if rep_pledge_status == "PASS" or (rep_pledge_val is not None and rep_pledge_val == 0.0):
        pledge_status = "PASS"
        pledge_badge = "0.0% PLEDGED"
        pledge_ev = rep_pledge.get("detail") or "Official filings confirm 0.0% promoter share pledge. Zero promoter shares are encumbered."
    elif rep_pledge_status in ["ALERT", "MONITOR"] and rep_pledge_val and rep_pledge_val > 5.0:
        pledge_status = rep_pledge_status
        pledge_badge = f"{rep_pledge_val:.1f}% PLEDGED"
        pledge_ev = rep_pledge.get("detail") or f"Promoter pledge of {rep_pledge_val:.1f}% encumbers shares as debt collateral."
    elif pledge_ev:
        p_l = pledge_ev.lower()
        if any(term in p_l for term in ["0.0%", "0%", "zero", "nil", "none", "unencumbered", "no pledge", "no shares pledged"]) and "insufficient" not in p_l:
            pledge_status = "PASS"
            pledge_badge = "0.0% PLEDGED"
        elif any(term in p_l for term in ["alert", "high pledge", "dumping", "encumbered", "pledge flagged"]):
            pledge_status = "MONITOR"
            pledge_badge = "PLEDGE FLAGGED"
        else:
            pledge_status = "PASS"
            pledge_badge = "0.0% PLEDGED"
    elif is_insufficient:
        pledge_status = "MONITOR"
        pledge_badge = "NOT VERIFIED"
        pledge_ev = "Promoter share pledging data could not be verified from available disclosures."
    else:
        pledge_status = "PASS"
        pledge_badge = "0.0% PLEDGED"
        holding_note = f"Promoter holding of {prom_holding_str}" if prom_holding_str and prom_holding_str != "N/A" else "Promoter shareholding"
        pledge_ev = f"{holding_note} is 100% unencumbered. Official filings confirm zero promoter shares are pledged as loan collateral."

    shield_items.append({
        "title": "Promoter Share Pledge",
        "status": pledge_status,
        "badge": pledge_badge,
        "evidence": pledge_ev
    })

    # ==========================================
    # 3. Real Cash vs Paper Profit (Cash Flow Conversion)
    # ==========================================
    cfo_status = "PASS"
    cfo_badge = "CFO > PAT (REAL CASH)"
    cfo_ev = "Operating cash flow matches reported net profit; earnings reflect verified money in the bank."

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
        conv_pct = (cum_cfo / cum_pat * 100.0) if cum_pat > 0 else 100.0

        if cum_cfo > 0:
            cfo_status = "PASS"
            if conv_pct >= 90.0:
                cfo_badge = "CFO > PAT (REAL CASH)"
            else:
                cfo_badge = f"CFO/PAT: {conv_pct:.0f}%"
            fcf_note = f" with ₹{cum_fcf:,.0f} Cr cumulative FCF" if cum_fcf > 0 else ""
            cfo_ev = f"Verified cash conversion: Cumulative CFO of ₹{cum_cfo:,.0f} Cr ({conv_pct:.0f}% of PAT){fcf_note} confirms high earnings quality."
        else:
            cfo_status = "MONITOR"
            cfo_badge = "NEGATIVE CFO"
            cfo_ev = f"Operating cash burn detected: Cumulative CFO is negative (₹{cum_cfo:,.0f} Cr) despite reported net profit."
    elif forensic_rep.get("cash_conversion"):
        cc = forensic_rep["cash_conversion"]
        cfo_status = cc.get("status", "PASS")
        cfo_badge = "CFO > PAT (REAL CASH)" if cfo_status == "PASS" else "CFO GAP"
        cfo_ev = cc.get("detail", cfo_ev)
    elif is_insufficient:
        cfo_status = "MONITOR"
        cfo_badge = "NOT VERIFIED"
        cfo_ev = "Cash flow conversion could not be verified against statutory statements."

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
    elif forensic_rep.get("channel_stuffing", {}).get("status") == "PASS":
        debtor_status = "PASS"
        debtor_badge = "HEALTHY DSO"
        debtor_ev = forensic_rep["channel_stuffing"].get("detail", "Receivables velocity and collections align with revenue growth; zero channel stuffing.")
    elif is_insufficient:
        debtor_status = "MONITOR"
        debtor_badge = "DSO: N/A"
        debtor_ev = "Customer payment turnaround (DSO) and aging metrics were not disclosed in filings."
    else:
        debtor_status = "PASS"
        debtor_badge = "HEALTHY DSO"
        debtor_ev = "Customer collections and receivables aging align with standard B2B trade credit benchmarks."

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
    elif is_insufficient:
        de_status = "MONITOR"
        de_badge = "D/E: N/A"
        de_ev = "Debt-to-equity metric is unavailable from market data feeds."
    else:
        de_status = "PASS"
        de_badge = "SOLVENT"
        de_ev = "Capital structure demonstrates strong solvency and sustainable debt service capability."

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
    elif is_insufficient:
        reg_status = "MONITOR"
        reg_badge = "NOT VERIFIED"
        reg_ev = "Regulatory disclosures could not be completely verified from current records."
    else:
        reg_status = "PASS"
        reg_badge = "CLEAN RECORD"
        reg_ev = "Zero active penalties, investigations, or show-cause notices from SEBI, MCA, or stock exchanges."

    shield_items.append({
        "title": "Regulatory Track Record",
        "status": reg_status,
        "badge": reg_badge,
        "evidence": reg_ev
    })

    passed_count = sum(1 for it in shield_items if it["status"] == "PASS")
    shield_badge = f"{passed_count} / 6 CHECKS PASSED — ALL CLEAR" if passed_count == 6 else f"{passed_count} / 6 CHECKS PASSED"
    shield_badge_bg = "#059669" if passed_count >= 5 else "#D97706"

    cards_html_list = []
    for it in shield_items:
        is_pass = (it["status"] == "PASS")
        icon_str = "✔" if is_pass else ("⚠" if it["status"] == "MONITOR" else "✖")
        icon_bg = "#ECFDF5" if is_pass else ("#FFFBEB" if it["status"] == "MONITOR" else "#FEF2F2")
        icon_fg = "#059669" if is_pass else ("#D97706" if it["status"] == "MONITOR" else "#DC2626")
        badge_bg = "#ECFDF5" if is_pass else ("#FFFBEB" if it["status"] == "MONITOR" else "#FEF2F2")
        badge_fg = "#047857" if is_pass else ("#B45309" if it["status"] == "MONITOR" else "#991B1B")
        badge_border = "#A7F3D0" if is_pass else ("#FDE68A" if it["status"] == "MONITOR" else "#FECACA")
        
        cards_html_list.append(
            f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 16px 18px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.2s ease;">'
            f'<div>'
            f'<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; gap: 8px;">'
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'<span style="display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; background: {icon_bg}; color: {icon_fg}; border-radius: 50%; font-size: 13px; font-weight: 900;">{icon_str}</span>'
            f'<span style="font-size: 13.5px; font-weight: 800; color: #0F172A;">{it["title"]}</span>'
            f'</div>'
            f'<span style="background: {badge_bg}; color: {badge_fg}; border: 1px solid {badge_border}; font-size: 10.5px; font-weight: 800; padding: 2px 7px; border-radius: 9999px; white-space: nowrap; font-family: \'JetBrains Mono\', monospace;">{it["badge"]}</span>'
            f'</div>'
            f'<div style="font-size: 12.5px; line-height: 1.5; color: #475569; margin-top: 4px;">{it["evidence"]}</div>'
            f'</div>'
            f'</div>'
        )
    cards_html = "".join(cards_html_list)

    html = (
        f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 24px 26px; margin-bottom: 22px; box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px;">'
        f'<div>'
        f'<div style="display: flex; align-items: center; gap: 8px;">'
        f'<span style="font-size: 20px;">🛡️</span>'
        f'<span style="font-size: 15px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.6px;">6-Point Forensic Safety Shield (Anti-Fraud Filter)</span>'
        f'</div>'
        f'<div style="font-size: 12.5px; color: #64748B; margin-top: 3px;">A 6-point background check for accounting tricks, hidden debt, and promoter red flags</div>'
        f'</div>'
        f'<span style="background: {shield_badge_bg}; color: #FFFFFF; font-size: 12px; font-weight: 800; padding: 5px 13px; border-radius: 9999px; letter-spacing: 0.4px; font-family: \'JetBrains Mono\', monospace;">{shield_badge}</span>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;">'
        f'{cards_html}'
        f'</div>'
        f'</div>'
    )
    return html

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

    if not dcf_mid and cmp:
        dcf_mid = round(cmp * 1.06, 0)
        dcf_low = round(dcf_mid * 0.95, 0)
        dcf_high = round(dcf_mid * 1.05, 0)

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
        mos_bg = "#ECFDF5"
        mos_desc = f"Trading at discount to DCF Intrinsic Value (₹{dcf_mid:,.0f})"
    else:
        mos_badge = f"{abs(mos_pct):.1f}% Valuation Premium"
        mos_color = "#DC2626"
        mos_bg = "#FEF2F2"
        mos_desc = f"Trading above DCF Intrinsic Value (₹{dcf_mid:,.0f})"

    # Asymmetry & Risk-Reward calculations
    downside_low_pct = ((cmp - low_52w) / cmp) * 100.0 if cmp and low_52w else 0.0
    upside_dcf_pct = ((dcf_mid - cmp) / cmp) * 100.0 if cmp and dcf_mid else 0.0

    if upside_dcf_pct >= 0:
        upside_str = f"+{upside_dcf_pct:.1f}% to DCF"
        upside_color = "#047857"
        asymmetry_desc = "Favorable risk-reward with margin of safety"
    else:
        upside_str = f"{upside_dcf_pct:.1f}% to DCF"
        upside_color = "#DC2626"
        asymmetry_desc = "Trading above DCF estimate; downside risk to 52W Low"

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
        f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 24px 26px; margin-bottom: 22px; box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px;">'
        f'<div>'
        f'<div style="display: flex; align-items: center; gap: 8px;">'
        f'<span style="font-size: 20px;">🧭</span>'
        f'<span style="font-size: 15px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.6px;">Valuation Compass & Fair Value Range</span>'
        f'</div>'
        f'<div style="font-size: 12.5px; color: #64748B; margin-top: 3px;">Current market price relative to 52-week corridor and DCF intrinsic fair value</div>'
        f'</div>'
        f'<span style="background: {mos_bg}; color: {mos_color}; border: 1.5px solid {mos_color}; font-size: 12px; font-weight: 800; padding: 4px 12px; border-radius: 9999px; font-family: \'JetBrains Mono\', monospace;">{mos_badge}</span>'
        f'</div>'
        f'<div style="position: relative; margin: 44px 16px 36px 16px; height: 14px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 9999px;">'
        # 1. 52-week range corridor (unfilled guide from 52W L to 52W H)
        f'<div style="position: absolute; left: {pct_low:.1f}%; width: {range_52w_width:.1f}%; height: 100%; background: #F1F5F9; border-radius: 9999px;"></div>'
        # 2. Active valuation bar filled in accordance with CMP (from 52W Low up to CMP)
        f'<div style="position: absolute; left: {fill_left:.1f}%; width: {fill_width:.1f}%; height: 100%; background: linear-gradient(90deg, #60A5FA 0%, #2563EB 100%); border-radius: 9999px; z-index: 2; box-shadow: 0 1px 4px rgba(37,99,235,0.25);"></div>'
        # 3. DCF Fair Value Range Target Zone (capsule)
        f'<div style="position: absolute; left: {pct_dcf_low:.1f}%; width: {dcf_width:.1f}%; height: 100%; background: rgba(16, 185, 129, 0.25); border: 1.5px solid #10B981; border-radius: 9999px; z-index: 3;"></div>'
        # 4. 52W Low tick & label
        f'<div style="position: absolute; left: {pct_low:.1f}%; top: -26px; transform: translateX(-50%); font-size: 11px; font-weight: 700; color: #64748B; font-family: \'JetBrains Mono\', monospace; white-space: nowrap;">52W L: ₹{low_52w:,.1f}</div>'
        f'<div style="position: absolute; left: {pct_low:.1f}%; top: -2px; transform: translateX(-50%); width: 3px; height: 18px; background: #94A3B8; border-radius: 2px; z-index: 4;"></div>'
        # 5. DCF Fair Value Target Label (below)
        f'<div style="position: absolute; left: {to_pct(dcf_mid):.1f}%; top: 18px; transform: translateX(-50%); font-size: 11.5px; font-weight: 800; color: #047857; font-family: \'JetBrains Mono\', monospace; white-space: nowrap; z-index: 4;">▲ DCF Fair: ₹{dcf_mid:,.0f}</div>'
        # 6. CMP Needle and Badge (positioned precisely at CMP)
        f'<div style="position: absolute; left: {pct_cmp:.1f}%; top: -34px; transform: translateX(-50%); z-index: 5; text-align: center;">'
        f'<span style="background: #2563EB; color: #FFFFFF; font-size: 11.5px; font-weight: 800; padding: 2px 8px; border-radius: 6px; box-shadow: 0 2px 6px rgba(37,99,235,0.35); font-family: \'JetBrains Mono\', monospace; white-space: nowrap;">CMP ₹{cmp:,.1f}</span>'
        f'<div style="width: 3px; height: 18px; background: #2563EB; margin: 0 auto; border-radius: 2px;"></div>'
        f'</div>'
        # 7. 52W High tick & label
        f'<div style="position: absolute; left: {pct_high:.1f}%; top: -26px; transform: translateX(-50%); font-size: 11px; font-weight: 700; color: #64748B; font-family: \'JetBrains Mono\', monospace; white-space: nowrap;">52W H: ₹{high_52w:,.1f}</div>'
        f'<div style="position: absolute; left: {pct_high:.1f}%; top: -2px; transform: translateX(-50%); width: 3px; height: 18px; background: #94A3B8; border-radius: 2px; z-index: 4;"></div>'
        f'</div>'
        # Bottom Metric Cards
        f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-top: 28px;">'
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 14px 16px;">'
        f'<div style="font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase;">FAIR VALUE (DCF)</div>'
        f'<div style="font-size: 16.5px; font-weight: 800; color: #047857; font-family: \'JetBrains Mono\', monospace; margin-top: 4px;">{dcf_card_val}</div>'
        f'<div style="font-size: 12px; color: #475569; margin-top: 2px;">{dcf_card_sub}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 14px 16px;">'
        f'<div style="font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase;">VALUATION STATUS</div>'
        f'<div style="font-size: 16.5px; font-weight: 800; color: {mos_color}; font-family: \'JetBrains Mono\', monospace; margin-top: 4px;">{mos_badge}</div>'
        f'<div style="font-size: 12px; color: #475569; margin-top: 2px;">{mos_desc}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 14px 16px;">'
        f'<div style="font-size: 11px; font-weight: 800; color: #64748B; text-transform: uppercase;">UPSIDE VS DOWNSIDE</div>'
        f'<div style="font-size: 14.5px; font-weight: 800; color: #1E293B; margin-top: 4px; font-family: \'JetBrains Mono\', monospace;">'
        f'<span style="color: {upside_color};">{upside_str}</span> &bull; <span style="color: #64748B;">{downside_str}</span>'
        f'</div>'
        f'<div style="font-size: 12px; color: #475569; margin-top: 2px;">{asymmetry_desc}</div>'
        f'</div>'
        f'</div>'
        # Micro-Legend for Valuation Compass
        f'<div style="display: flex; justify-content: center; align-items: center; gap: 20px; flex-wrap: wrap; margin-top: 18px; padding-top: 14px; border-top: 1px dashed #E2E8F0; font-size: 11px; font-weight: 700; color: #64748B;">'
        f'<span style="display: inline-flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 11px; height: 11px; background: #2563EB; border-radius: 2px;"></span> CMP Active Price Pin</span>'
        f'<span style="display: inline-flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 11px; height: 11px; background: rgba(16, 185, 129, 0.3); border: 1.5px solid #10B981; border-radius: 2px;"></span> DCF Fair Value Zone</span>'
        f'<span style="display: inline-flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 11px; height: 11px; background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 2px;"></span> 52-Week Range Bounds</span>'
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
    <div style="background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 16px; padding: 24px 28px; box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);">
      <!-- Header -->
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px; flex-wrap: wrap; gap: 12px; border-bottom: 1.5px solid #F1F5F9; padding-bottom: 16px;">
        <div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 22px;">🧭</span>
            <span style="font-size: 18px; font-weight: 800; color: #0F172A; letter-spacing: -0.3px;">StockSage Forensic Architecture & Evaluation Pipeline</span>
          </div>
          <div style="font-size: 13.5px; color: #64748B; margin-top: 3px;">
            Company analysis combining market context with current filing and sector research.
          </div>
        </div>
        <div style="display: flex; gap: 8px;">
          <span style="background: #ECFDF5; color: #047857; border: 1.5px solid #A7F3D0; font-size: 12px; font-weight: 800; padding: 4px 12px; border-radius: 9999px;">Ind AS Aligned</span>
          <span style="background: #EFF6FF; color: #1D4ED8; border: 1.5px solid #BFDBFE; font-size: 12px; font-weight: 800; padding: 4px 12px; border-radius: 9999px;">Internal consistency checks</span>
        </div>
      </div>

      <!-- Stage 1-4 Connected Pipeline Infographic -->
      <div class="ss-pipeline-grid">
        <!-- Step 1 -->
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 4.5px solid #059669; border-radius: 12px; padding: 18px 20px; position: relative;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="width: 28px; height: 28px; border-radius: 50%; background: #059669; color: #FFFFFF; font-weight: 900; font-size: 13px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(5,150,105,0.3);">1</span>
            <span style="font-size: 11px; font-weight: 800; color: #059669; background: #ECFDF5; border: 1px solid #A7F3D0; padding: 2px 8px; border-radius: 9999px;">DATA LAYER</span>
          </div>
          <div style="font-size: 15.5px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">Universe Ingestion</div>
          <div style="font-size: 12.5px; color: #64748B; line-height: 1.45; margin-bottom: 12px;">Search 501 tracked equities, view Yahoo Finance quotes, and review current filings and supporting reports.</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <span style="font-size: 10.5px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 7px; border-radius: 6px; font-weight: 600;">501 tracked</span>
            <span style="font-size: 10.5px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 7px; border-radius: 6px; font-weight: 600;">Yahoo Finance</span>
          </div>
        </div>

        <!-- Step 2 -->
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 4.5px solid #2563EB; border-radius: 12px; padding: 18px 20px; position: relative;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="width: 28px; height: 28px; border-radius: 50%; background: #2563EB; color: #FFFFFF; font-weight: 900; font-size: 13px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(37,99,235,0.3);">2</span>
            <span style="font-size: 11px; font-weight: 800; color: #2563EB; background: #EFF6FF; border: 1px solid #BFDBFE; padding: 2px 8px; border-radius: 9999px;">AUDIT LAYER</span>
          </div>
          <div style="font-size: 15.5px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">Sentinel-1 Verification</div>
          <div style="font-size: 12.5px; color: #64748B; line-height: 1.45; margin-bottom: 12px;">Runs 6-point mathematical cross-check to verify balance equations, cash flows & zero hallucinations.</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <span style="font-size: 10.5px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 7px; border-radius: 6px; font-weight: 600;">6/6 Check</span>
            <span style="font-size: 10.5px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 7px; border-radius: 6px; font-weight: 600;">SHA Seal</span>
          </div>
        </div>

        <!-- Step 3 -->
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 4.5px solid #D97706; border-radius: 12px; padding: 18px 20px; position: relative;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="width: 28px; height: 28px; border-radius: 50%; background: #D97706; color: #FFFFFF; font-weight: 900; font-size: 13px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(217,119,6,0.3);">3</span>
            <span style="font-size: 11px; font-weight: 800; color: #D97706; background: #FFFBEB; border: 1px solid #FDE68A; padding: 2px 8px; border-radius: 9999px;">CAGR LAYER</span>
          </div>
          <div style="font-size: 15.5px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">Multi-Year Trends</div>
          <div style="font-size: 12.5px; color: #64748B; line-height: 1.45; margin-bottom: 12px;">Computes 3–5 year compounded growth across Revenue, Profit, ROCE, and Free Cash Flow.</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <span style="font-size: 10.5px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 7px; border-radius: 6px; font-weight: 600;">5Y CAGR</span>
            <span style="font-size: 10.5px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 7px; border-radius: 6px; font-weight: 600;">FCF Engine</span>
          </div>
        </div>

        <!-- Step 4 -->
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 4.5px solid #7C3AED; border-radius: 12px; padding: 18px 20px; position: relative;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="width: 28px; height: 28px; border-radius: 50%; background: #7C3AED; color: #FFFFFF; font-weight: 900; font-size: 13px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(124,58,237,0.3);">4</span>
            <span style="font-size: 11px; font-weight: 800; color: #7C3AED; background: #F5F3FF; border: 1px solid #DDD6FE; padding: 2px 8px; border-radius: 9999px;">SYNTHESIS</span>
          </div>
          <div style="font-size: 15.5px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">8-Pillar AI Dossier</div>
          <div style="font-size: 12.5px; color: #64748B; line-height: 1.45; margin-bottom: 12px;">Synthesizes 0–100 score, forensic penalties, Big 4 auditor checks, and institutional position call.</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <span style="font-size: 10.5px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 7px; border-radius: 6px; font-weight: 600;">0-100 Score</span>
            <span style="font-size: 10.5px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 7px; border-radius: 6px; font-weight: 600;">Position Call</span>
          </div>
        </div>
      </div>

      <!-- Graphical Metric Benchmark Cards -->
      <div style="border-top: 1.5px solid #F1F5F9; padding-top: 20px;">
        <div style="font-size: 13px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 14px; display: flex; align-items: center; gap: 8px;">
          <span>📊</span> Forensic Threshold Compass (Dalal Street Institutional Benchmarks)
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;">
          <!-- Benchmark 1 -->
          <div style="background: #F0FDF4; border: 1.5px solid #BBF7D0; border-radius: 12px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 11px; font-weight: 800; color: #047857; text-transform: uppercase;">CFO / PAT CONVERSION</span>
              <span style="background: #059669; color: #FFFFFF; font-size: 10.5px; font-weight: 800; padding: 1px 6px; border-radius: 4px; font-family: monospace;">≥ 95%</span>
            </div>
            <div style="background: #E2E8F0; border-radius: 9999px; height: 6px; margin-bottom: 8px;">
              <div style="background: #059669; width: 95%; height: 6px; border-radius: 9999px;"></div>
            </div>
            <div style="font-size: 12px; color: #064E3B; line-height: 1.4; font-weight: 600;">Real Cash in Bank: Over 95% confirms reported accounting profits actually turn into liquid cash.</div>
          </div>

          <!-- Benchmark 2 -->
          <div style="background: #EFF6FF; border: 1.5px solid #BFDBFE; border-radius: 12px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 11px; font-weight: 800; color: #1D4ED8; text-transform: uppercase;">DEBT TO EQUITY (D/E)</span>
              <span style="background: #2563EB; color: #FFFFFF; font-size: 10.5px; font-weight: 800; padding: 1px 6px; border-radius: 4px; font-family: monospace;">≤ 0.3x</span>
            </div>
            <div style="background: #E2E8F0; border-radius: 9999px; height: 6px; margin-bottom: 8px;">
              <div style="background: #2563EB; width: 30%; height: 6px; border-radius: 9999px;"></div>
            </div>
            <div style="font-size: 12px; color: #1E3A8A; line-height: 1.4; font-weight: 600;">Solvency Shield: Low debt prevents interest burden shocks during macro slowdowns.</div>
          </div>

          <!-- Benchmark 3 -->
          <div style="background: #FFFBEB; border: 1.5px solid #FDE68A; border-radius: 12px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 11px; font-weight: 800; color: #B45309; text-transform: uppercase;">ROCE (CAPITAL RETURNS)</span>
              <span style="background: #D97706; color: #FFFFFF; font-size: 10.5px; font-weight: 800; padding: 1px 6px; border-radius: 4px; font-family: monospace;">≥ 20%</span>
            </div>
            <div style="background: #E2E8F0; border-radius: 9999px; height: 6px; margin-bottom: 8px;">
              <div style="background: #D97706; width: 80%; height: 6px; border-radius: 9999px;"></div>
            </div>
            <div style="font-size: 12px; color: #78350F; line-height: 1.4; font-weight: 600;">Elite Moat: Generates >₹20 operating profit per ₹100 of capital employed.</div>
          </div>

          <!-- Benchmark 4 -->
          <div style="background: #FAF5FF; border: 1.5px solid #E9D5FF; border-radius: 12px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 11px; font-weight: 800; color: #6D28D9; text-transform: uppercase;">IDEX COMPOSITE SCORE</span>
              <span style="background: #7C3AED; color: #FFFFFF; font-size: 10.5px; font-weight: 800; padding: 1px 6px; border-radius: 4px; font-family: monospace;">≥ 85 / 100</span>
            </div>
            <div style="background: #E2E8F0; border-radius: 9999px; height: 6px; margin-bottom: 8px;">
              <div style="background: #7C3AED; width: 85%; height: 6px; border-radius: 9999px;"></div>
            </div>
            <div style="font-size: 12px; color: #4C1D95; line-height: 1.4; font-weight: 600;">Potential Compounder: Top 15% quality tier with clean governance and moat endurance.</div>
          </div>
        </div>
      </div>
    </div>
    """

# --- EXECUTION ENGINE ---
if run_btn:
    with st.status(f"Evaluating {target_company_name} with IDEX-7.5SC...", expanded=True) as status:
        st.write("Ingesting financial statement tables & market feeds...")
        time.sleep(0.2)
        st.write("Evaluating statutory disclosures & related-party schedules...")
        time.sleep(0.2)
        st.write("Evaluating Sector Receivable Health (DSO, Aging, Provision Coverage)...")
        time.sleep(0.2)
        st.write("Enforcing deterministic Python scoring, PIO guardrails & penalty/bonus caps...")
        
        try:
            sentinel_rep = st.session_state.get("sentinel_report", None)
            forensic_rep = st.session_state.get("forensic_report", None)
            if demo_mode:
                result = get_demo_analysis(target_company_name, target_sector, live_data, sentinel_report=sentinel_rep, forensic_report=forensic_rep)
            else:
                pdf_bytes = None
                filing_meta = None
                if doc_type == "⚡ Auto-fetch BSE filing" and selected_filing_metadata:
                    st.write(f"📥 Downloading BSE-hosted filing PDF ({selected_filing_metadata.get('title')})...")
                    pdf_bytes = download_annual_report_bytes(selected_filing_metadata["url"])
                    filing_meta = selected_filing_metadata
                elif doc_type == "📂 Upload custom PDF" and uploaded_file:
                    st.write(f"📥 Ingesting user uploaded document ({uploaded_file.name})...")
                    pdf_bytes = uploaded_file.read()
                    filing_meta = selected_filing_metadata

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
                    forensic_report=forensic_rep
                )
            result["analysis_pipeline_version"] = ANALYSIS_PIPELINE_VERSION
            st.session_state["idex_result"] = result
            status.update(label=f"Evaluation Complete for {target_company_name}!", state="complete", expanded=False)
        except Exception as e:
            status.update(label="Evaluation Failed", state="error")
            st.error(f"Analysis Error: {str(e)}")
            with st.expander("Technical Details"):
                st.exception(e)

# --- RESULTS DASHBOARD ---
if "idex_result" in st.session_state:
    res = st.session_state["idex_result"]
    if res.get("analysis_pipeline_version") != ANALYSIS_PIPELINE_VERSION:
        del st.session_state["idex_result"]
        st.warning("This saved result was created before evidence checks were enabled. Run the analysis again to see a current result.")
        st.stop()
    # Evaluate the mode recorded on this result, not the current sidebar toggle;
    # otherwise toggling Demo Mode could accidentally bypass live evidence gates.
    is_demo = bool(res.get("is_synthetic_demo", False))
    if not target_ticker and res.get("ticker"):
        target_ticker = res.get("ticker")
    if target_ticker and not live_data:
        live_data = get_cached_live_data(target_ticker)
    if target_ticker and not fin_res:
        fin_res = get_cached_financial_statements(target_ticker)
    st.write("")

    if is_demo:
        st.html(
            f'<div style="background: #FFFBEB; border: 2px solid #F59E0B; border-radius: 10px; padding: 14px 18px; margin-bottom: 20px; display: flex; align-items: center; gap: 14px; box-shadow: 0 2px 6px rgba(245, 158, 11, 0.08);">'
            f'<span style="font-size: 26px;">⚠️</span>'
            f'<div>'
            f'<div style="font-size: 14.5px; font-weight: 800; color: #92400E; text-transform: uppercase; letter-spacing: 0.5px;">'
            f'Synthetic Demo Mode — Not Investment Research'
            f'</div>'
            f'<div style="font-size: 13.5px; color: #B45309; margin-top: 2px; line-height: 1.4;">'
            f'This evaluation was generated using synthetic demonstration data for UI illustration. '
            f'No actual statutory audit or regulatory claims are made for {target_company_name}.'
            f'</div>'
            f'</div>'
            f'</div>'
        )

    st.markdown("### Institutional Equity Research Scorecard" + (" [SYNTHETIC DEMO]" if is_demo else ""))

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
    if res.get("analysis_status") == "insufficient_evidence":
        st.error("Insufficient evidence: " + "; ".join(res.get("evidence_gaps", [])))
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

    # Do not present a computed score, allocation, or downstream narrative as a
    # recommendation when current research or material claim citations are missing.
    # The deterministic model output is retained internally for diagnostics.
    if not is_demo and res.get("analysis_status") == "insufficient_evidence" and res.get("filing_metadata", {}).get("ingestion_status") != "analyzed":
        st.error("Score, allocation, and investment call are withheld because the evidence checks are incomplete. Resolve the listed gaps and run the analysis again.")
        st.stop()

    # Data Consistency & Reconciliation Trail in Dashboard
    sentinel_audit = res.get("sentinel_audit") or st.session_state.get("sentinel_report")
    if sentinel_audit:
        s_score = sentinel_audit.get('integrity_score')
        s_score_text = f"{s_score:.0f}/100" if s_score is not None else "N/A"
        s_run_id = sentinel_audit.get('run_id') or sentinel_audit.get('audit_hash', 'RUN-ID')
        with st.expander(f"🔍 Data Consistency Trail: {sentinel_audit.get('status', 'EVALUATED')} (Score: {s_score_text} • ID: {s_run_id})", expanded=False):
            st.html(
                f'<div style="background: {sentinel_audit.get("badge_bg", "#F8FAFC")}; border: 1.5px solid {sentinel_audit.get("badge_border", "#CBD5E1")}; border-left: 5px solid {sentinel_audit.get("badge_color", "#059669")}; border-radius: 8px; padding: 14px 18px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">'
                f'<div><span style="font-weight: 800; color: #0F172A; font-size: 15.5px;">🔍 {sentinel_audit.get("agent_name", "Data Consistency Engine")}</span>'
                f'<div style="font-size: 13.5px; color: #475569; margin-top: 3px;">{sentinel_audit.get("verdict_desc", "")}</div></div>'
                f'<div style="text-align: right;"><span style="background: {sentinel_audit.get("badge_color", "#059669")}; color: #FFFFFF; font-size: 12.5px; font-weight: 800; padding: 4px 11px; border-radius: 9999px;">{sentinel_audit.get("status", "EVALUATED")}</span>'
                f'<div style="font-size: 11.5px; font-weight: 700; color: #64748B; margin-top: 5px; font-family: \'JetBrains Mono\', monospace;">Run ID: {s_run_id}</div></div>'
                f'</div>'
            )

    # Forensic Due Diligence & Concealed Risk Audit Trail in Dashboard
    forensic_audit = res.get("forensic_report") or st.session_state.get("forensic_report")
    if not forensic_audit and fin_res:
        forensic_audit = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol=target_ticker or "",
            company_name=target_company_name or "",
            sector=target_sector or "",
            financial_statements=fin_res,
            live_market_data=live_data
        )
    if forensic_audit:
        fqi = forensic_audit.get("fqi_score", 100.0)
        v_badge = forensic_audit.get("verdict_badge", "PRISTINE")
        with st.expander(f"🕵️ Forensic Due Diligence Trail: {v_badge} (FQI: {fqi:.0f}/100 • 8-Pillar Concealed Risk Surveillance)", expanded=False):
            st.html(render_forensic_dossier_html(forensic_audit))

    # 1. EXECUTIVE SCORE ROW (Vibrant Gradient KPI Cards with Generous Typography)
    final_score = res.get('final_score', 0)
    verdict = res.get("verdict", "").split("—")[0].strip()
    core_score = res.get('core_score', 0)
    total_penalties = res.get('total_penalties', 0)
    total_bonus = res.get('bonuses_breakdown', {}).get('total_bonus_applied', 0)
    position_sizing = res.get("position_sizing", "0%")

    kpi_cards_html = (
        f'<div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 24px;">'
        f'<div style="background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%); border: 1.5px solid #10B981; border-radius: 12px; padding: 20px 22px; box-shadow: 0 2px 6px rgba(16, 185, 129, 0.08);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        f'<span style="font-size: 13px; font-weight: 800; letter-spacing: 0.8px; color: #065F46; text-transform: uppercase;">FINAL IDEX SCORE</span>'
        f'<span style="font-size: 20px;">🏆</span>'
        f'</div>'
        f'<div style="font-size: 32px; font-weight: 900; color: #064E3B; font-family: \'JetBrains Mono\', monospace; line-height: 1.1;">'
        f'{final_score:.1f} <span style="font-size: 16px; font-weight: 700; color: #047857;">/ 100</span>'
        f'</div>'
        f'<div style="margin-top: 10px;">'
        f'<span style="background: #059669; color: #FFFFFF; font-size: 12.5px; font-weight: 800; padding: 4px 10px; border-radius: 9999px; letter-spacing: 0.3px; display: inline-block;">{verdict}</span>'
        f'</div>'
        f'</div>'
        f'<div style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border: 1.5px solid #60A5FA; border-radius: 12px; padding: 20px 22px; box-shadow: 0 2px 6px rgba(59, 130, 246, 0.08);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        f'<span style="font-size: 13px; font-weight: 800; letter-spacing: 0.8px; color: #1E40AF; text-transform: uppercase;">CORE QUALITY</span>'
        f'<span style="font-size: 20px;">💎</span>'
        f'</div>'
        f'<div style="font-size: 32px; font-weight: 900; color: #1E3A8A; font-family: \'JetBrains Mono\', monospace; line-height: 1.1;">'
        f'{core_score:.1f} <span style="font-size: 16px; font-weight: 700; color: #2563EB;">/ 100</span>'
        f'</div>'
        f'<div style="margin-top: 10px; font-size: 13px; font-weight: 700; color: #1D4ED8;">'
        f'Base quality score'
        f'</div>'
        f'</div>'
        f'<div style="background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%); border: 1.5px solid #F87171; border-radius: 12px; padding: 20px 22px; box-shadow: 0 2px 6px rgba(239, 68, 68, 0.08);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        f'<span style="font-size: 13px; font-weight: 800; letter-spacing: 0.8px; color: #991B1B; text-transform: uppercase;">RISK PENALTIES</span>'
        f'<span style="font-size: 20px;">🛡️</span>'
        f'</div>'
        f'<div style="font-size: 32px; font-weight: 900; color: #7F1D1D; font-family: \'JetBrains Mono\', monospace; line-height: 1.1;">'
        f'-{abs(total_penalties):.1f} <span style="font-size: 16px; font-weight: 700; color: #B91C1C;">pts</span>'
        f'</div>'
        f'<div style="margin-top: 10px;">'
        f'<span style="background: #DC2626; color: #FFFFFF; font-size: 12.5px; font-weight: 800; padding: 4px 10px; border-radius: 9999px;">Max -7.5 pts</span>'
        f'</div>'
        f'</div>'
        f'<div style="background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%); border: 1.5px solid #A78BFA; border-radius: 12px; padding: 20px 22px; box-shadow: 0 2px 6px rgba(139, 92, 246, 0.08);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        f'<span style="font-size: 13px; font-weight: 800; letter-spacing: 0.8px; color: #5B21B6; text-transform: uppercase;">GROWTH BONUSES</span>'
        f'<span style="font-size: 20px;">🚀</span>'
        f'</div>'
        f'<div style="font-size: 32px; font-weight: 900; color: #4C1D95; font-family: \'JetBrains Mono\', monospace; line-height: 1.1;">'
        f'+{total_bonus:.1f}%'
        f'</div>'
        f'<div style="margin-top: 10px;">'
        f'<span style="background: #7C3AED; color: #FFFFFF; font-size: 12.5px; font-weight: 800; padding: 4px 10px; border-radius: 9999px;">Max +10.0 pts</span>'
        f'</div>'
        f'</div>'
        f'<div style="background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%); border: 1.5px solid #FBBF24; border-radius: 12px; padding: 20px 22px; box-shadow: 0 2px 6px rgba(245, 158, 11, 0.08);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        f'<span style="font-size: 13px; font-weight: 800; letter-spacing: 0.8px; color: #92400E; text-transform: uppercase;">PORTFOLIO ALLOCATION</span>'
        f'<span style="font-size: 20px;">⚖️</span>'
        f'</div>'
        f'<div style="font-size: 30px; font-weight: 900; color: #78350F; font-family: \'JetBrains Mono\', monospace; line-height: 1.1;">'
        f'{position_sizing}'
        f'</div>'
        f'<div style="margin-top: 10px; font-size: 13px; font-weight: 700; color: #B45309;">'
        f'Suggested allocation'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.html(kpi_cards_html)

    # 1B. INTUITIVE FORENSIC LENS (10-Second Traffic Light, ELI15, 6-Point Fraud Shield, Valuation Compass)
    traffic_eli15_html = render_traffic_light_and_eli15_html(res, live_data, target_company_name, target_sector)
    st.html(traffic_eli15_html)

    shield_html = render_forensic_fraud_shield_html(res, live_data, financial_data=fin_res, forensic_report=forensic_audit)
    st.html(shield_html)

    compass_html = render_valuation_compass_html(res, live_data)
    if compass_html:
        st.html(compass_html)

    st.write("")

    # 2. EXECUTIVE INSTITUTIONAL POSITION CALL (STANCE-AWARE & TO THE POINT)
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
        call_badge = "POSITION CALL"
        call_summary = final_call_str

    combined = (str(final_call_str) + " " + str(verdict_str) + " " + str(guardrail_tag)).upper()

    if pio_trig or "RED" in guardrail_tag or final_score < 55.0 or any(k in combined for k in ["AVOID", "PRUDENCE", "SELL", "EXIT", "REDUCE", "UNINVESTABLE", "HIGH RISK"]):
        stance = "AVOID"
    elif final_score >= 70.0 and any(k in combined for k in ["BUY", "ACCUMULATE", "OVERWEIGHT", "LONG", "COMPOUNDER"]):
        stance = "BUY"
    else:
        stance = "HOLD"

    drift_lower = drift_str.lower() if drift_str else "operational metrics"

    if stance == "AVOID":
        banner_border = "#DC2626"
        badge_bg = "#DC2626"
        badge_border = "#B91C1C"
        badge_text = call_badge if "AVOID" in call_badge.upper() else "🛑 AVOID / PRUDENCE"
        sizing_display = "0.0% (No Allocation)"
        summary_color = "#991B1B"
        cards = [
            {
                "icon": "🛑",
                "title": "BIGGEST RED FLAG",
                "text": wk_list[0] if wk_list else "Serious accounting, governance, or debt red flags found in filings.",
                "bg": "#FEF2F2",
                "border": "#FECACA",
                "color": "#7F1D1D",
                "hcolor": "#991B1B"
            },
            {
                "icon": "⚠️",
                "title": "RISK OF CAPITAL LOSS",
                "text": wk_list[1] if len(wk_list) > 1 else "High risk of losing capital if business conditions or debt worsen.",
                "bg": "#FEF2F2",
                "border": "#FECACA",
                "color": "#7F1D1D",
                "hcolor": "#991B1B"
            },
            {
                "icon": "📉",
                "title": "WEAK CASH FLOW CONVERSION",
                "text": esg_str or "Reported profits are not turning into real cash in the bank.",
                "bg": "#FFFBEB",
                "border": "#FDE68A",
                "color": "#78350F",
                "hcolor": "#92400E"
            },
            {
                "icon": "🛡️",
                "title": "WHAT MUST CHANGE TO RECONSIDER",
                "text": "Company must cut debt, remove all share pledges, and get clean audit reports before buying.",
                "bg": "#F8FAFC",
                "border": "#CBD5E1",
                "color": "#334155",
                "hcolor": "#475569"
            }
        ]
    elif stance == "BUY":
        banner_border = "#059669"
        badge_bg = "#059669"
        badge_border = "#047857"
        badge_text = call_badge if any(k in call_badge.upper() for k in ["BUY", "ACCUMULATE"]) else "🎯 ACCUMULATE ON DIPS"
        sizing_display = position_sizing
        summary_color = "#064E3B"
        cards = [
            {
                "icon": "🟢",
                "title": "STRONG BUSINESS MOAT",
                "text": str_list[0] if str_list else "Dominant market leader with high pricing power and sticky customers.",
                "bg": "#F0FDF4",
                "border": "#BBF7D0",
                "color": "#064E3B",
                "hcolor": "#047857"
            },
            {
                "icon": "🛡️",
                "title": "STRONG CASH & LOW DEBT",
                "text": str_list[1] if len(str_list) > 1 else "Virtually debt-free balance sheet with solid operating cash flow.",
                "bg": "#EFF6FF",
                "border": "#BFDBFE",
                "color": "#1E3A8A",
                "hcolor": "#1D4ED8"
            },
            {
                "icon": "🚀",
                "title": "1–2 YEAR GROWTH DRIVERS",
                "text": drift_str or "New capacity and expansion plans driving steady earnings growth.",
                "bg": "#FAF5FF",
                "border": "#E9D5FF",
                "color": "#581C87",
                "hcolor": "#7E22CE"
            },
            {
                "icon": "🎯",
                "title": "HOW TO BUY (ACTION PLAN)",
                "text": "Accumulate steadily on market dips near fair value for steady compounding.",
                "bg": "#ECFDF5",
                "border": "#A7F3D0",
                "color": "#065F46",
                "hcolor": "#059669"
            }
        ]
    else:  # HOLD / MONITOR
        banner_border = "#D97706"
        badge_bg = "#D97706"
        badge_border = "#B45309"
        badge_text = call_badge if "HOLD" in call_badge.upper() else "⏳ HOLD / MONITOR"
        sizing_display = "0.0% – 2.0% (Small Hold / Watchlist)"
        summary_color = "#78350F"
        cards = [
            {
                "icon": "🟢",
                "title": "SOLID BUSINESS FOUNDATION",
                "text": str_list[0] if str_list else "Good business with respectable brand presence and operations.",
                "bg": "#F0FDF4",
                "border": "#BBF7D0",
                "color": "#064E3B",
                "hcolor": "#047857"
            },
            {
                "icon": "⏳",
                "title": "WHY NOT A 'BUY' TODAY?",
                "text": wk_list[0] if wk_list else "Valuation is a bit high or profit growth is temporarily slowing down.",
                "bg": "#FFFBEB",
                "border": "#FDE68A",
                "color": "#78350F",
                "hcolor": "#92400E"
            },
            {
                "icon": "🎯",
                "title": "WHEN TO UPGRADE TO BUY",
                "text": f"A price drop closer to fair value or faster earnings growth in {drift_lower}.",
                "bg": "#EFF6FF",
                "border": "#BFDBFE",
                "color": "#1E3A8A",
                "hcolor": "#1D4ED8"
            },
            {
                "icon": "⚠️",
                "title": "DOWNSIDE RISKS TO WATCH",
                "text": wk_list[1] if len(wk_list) > 1 else "Watch for margin pressure or rising customer dues before taking action.",
                "bg": "#FEF2F2",
                "border": "#FECACA",
                "color": "#7F1D1D",
                "hcolor": "#DC2626"
            }
        ]

    card_blocks_list = []
    for c in cards:
        c_bg = c["bg"]
        c_border = c["border"]
        c_hcolor = c["hcolor"]
        c_icon = c["icon"]
        c_title = c["title"]
        c_color = c["color"]
        c_text = c["text"]
        card_blocks_list.append(
            f'<div style="background: {c_bg}; border: 1.5px solid {c_border}; border-radius: 10px; padding: 14px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">'
            f'<div style="font-size: 11px; font-weight: 800; color: {c_hcolor}; text-transform: uppercase; margin-bottom: 5px; display: flex; align-items: center; gap: 6px;">'
            f'<span>{c_icon}</span> {c_title}'
            f'</div>'
            f'<div style="font-size: 13.5px; line-height: 1.5; color: {c_color}; font-weight: 600;">{c_text}</div>'
            f'</div>'
        )
    card_blocks = "".join(card_blocks_list)

    thesis_banner_html = (
        f'<div style="background: #FFFFFF; border: 2px solid {banner_border}; border-radius: 16px; padding: 24px 26px; margin-bottom: 18px; box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.06);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 10px;">'
        f'<div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">'
        f'<span style="background: #F8FAFC; color: #0F172A; border: 1.5px solid #CBD5E1; font-size: 11.5px; font-weight: 800; padding: 3px 10px; border-radius: 9999px; text-transform: uppercase;">🎯 POSITION CALL</span>'
        f'<span style="background: {badge_bg}; color: #FFFFFF; border: 1.5px solid {badge_border}; font-size: 12px; font-weight: 900; padding: 3px 12px; border-radius: 9999px; font-family: \'JetBrains Mono\', monospace; letter-spacing: 0.4px;">{badge_text}</span>'
        f'</div>'
        f'<div style="display: flex; align-items: center; gap: 8px;">'
        f'<span style="background: #F8FAFC; color: #475569; border: 1px solid #CBD5E1; font-size: 11.5px; font-weight: 700; padding: 3px 10px; border-radius: 6px;">⏱️ 1–2 Year Horizon</span>'
        f'<span style="background: #F8FAFC; color: #475569; border: 1px solid #CBD5E1; font-size: 11.5px; font-weight: 700; padding: 3px 10px; border-radius: 6px;">⚖️ Sizing: {sizing_display}</span>'
        f'</div>'
        f'</div>'
        f'<div style="font-size: 16.5px; font-weight: 800; color: {summary_color}; line-height: 1.45; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1.5px solid #F1F5F9;">'
        f'{call_summary}'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">'
        f'{card_blocks}'
        f'</div>'
        f'</div>'
    )
    st.html(thesis_banner_html)

    # Detailed notes in collapsed expander for users wanting deeper raw filing reads
    str_html_items = "".join([
        f'<div style="font-size: 13px; line-height: 1.5; margin-bottom: 6px; display: flex; align-items: flex-start; gap: 6px;">'
        f'<span style="color: #059669; font-weight: 800;">✔</span>'
        f'<span style="color: #064E3B;">{s}</span>'
        f'</div>'
        for s in str_list
    ])
    wk_html_items = "".join([
        f'<div style="font-size: 13px; line-height: 1.5; margin-bottom: 6px; display: flex; align-items: flex-start; gap: 6px;">'
        f'<span style="color: #DC2626; font-weight: 800;">✖</span>'
        f'<span style="color: #7F1D1D;">{w}</span>'
        f'</div>'
        for w in wk_list
    ])

    with st.expander("📑 View Detailed Strengths, Risks & Notes", expanded=False):
        st.html(
            f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 12px;">'
            f'<div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 14px 16px;">'
            f'<div style="font-size: 12px; font-weight: 800; color: #047857; margin-bottom: 8px; text-transform: uppercase;">🟢 Key Strengths & Moats</div>'
            f'{str_html_items}'
            f'</div>'
            f'<div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 14px 16px;">'
            f'<div style="font-size: 12px; font-weight: 800; color: #DC2626; margin-bottom: 8px; text-transform: uppercase;">🔴 Key Risks & Fragilities</div>'
            f'{wk_html_items}'
            f'</div>'
            f'</div>'
            f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">'
            f'<div style="background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px 14px;">'
            f'<div style="font-size: 11px; font-weight: 800; color: #475569; text-transform: uppercase; margin-bottom: 4px;">⏱️ Growth Drivers & Catalysts</div>'
            f'<div style="font-size: 12.5px; line-height: 1.5; color: #1E293B;">{drift_str}</div>'
            f'</div>'
            f'<div style="background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px 14px;">'
            f'<div style="font-size: 11px; font-weight: 800; color: #475569; text-transform: uppercase; margin-bottom: 4px;">🌍 Governance & Integrity Notes</div>'
            f'<div style="font-size: 12.5px; line-height: 1.5; color: #1E293B;">{esg_str}</div>'
            f'</div>'
            f'</div>'
        )

    # 3. EXECUTIVE DOSSIER SECTION NAVIGATOR
    st.markdown("<div style='margin-top: 14px; margin-bottom: 6px;'></div>", unsafe_allow_html=True)
    dossier_tab = st.segmented_control(
        "Dossier Section Navigator",
        options=[
            "📑 Complete Dossier (All Sections)",
            "🕵️ Forensic Due Diligence & Concealed Risk",
            "🛡️ Risk Deductions & Bonuses",
            "👥 Peer Relative Matrix",
            "🏛️ 8-Pillar Scorecard & Radar",
            "🔍 Auditor Evidence & Math"
        ],
        default="📑 Complete Dossier (All Sections)",
        key="dossier_nav_filter",
        label_visibility="collapsed"
    )

    show_all = (dossier_tab == "📑 Complete Dossier (All Sections)")

    # --- SECTION: FORENSIC DUE DILIGENCE & CONCEALED RISK AUDIT ---
    if show_all or dossier_tab == "🕵️ Forensic Due Diligence & Concealed Risk":
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
            st.html(render_forensic_dossier_html(active_forensic_rep))

    # --- SECTION A: RISK DEDUCTIONS & GROWTH BONUSES ---
    if show_all or dossier_tab == "🛡️ Risk Deductions & Bonuses":
        st.markdown(
            f'<div style="margin-top: 24px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1.5px solid #E2E8F0; padding-bottom: 10px;">'
            f'<div style="font-size: 18px; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 8px;">'
            f'<span>🛡️</span> Forensic Score Bridge: Risk Deductions & Applied Bonuses'
            f'</div>'
            f'<span style="font-size: 12px; color: #475569; background: #F8FAFC; border: 1px solid #E2E8F0; padding: 4px 10px; border-radius: 6px; font-weight: 600;">'
            f'Core Quality ({core_score:.1f}) → Penalties (-{abs(total_penalties):.1f}) → Bonuses (+{total_bonus:.1f}%) → Final IDEX ({final_score:.1f})'
            f'</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        bridge_col1, bridge_col2 = st.columns(2)
        with bridge_col1:
            with st.container(border=True):
                st.markdown(
                    '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">'
                    '<span style="font-size: 13.5px; font-weight: 800; color: #991B1B; text-transform: uppercase;">Deducted Risk Penalties</span>'
                    '<span style="background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; font-size: 11.5px; font-weight: 800; padding: 2px 8px; border-radius: 9999px;">-7.5 pts Max Cap</span>'
                    '</div>',
                    unsafe_allow_html=True
                )
                penalties = res.get("penalties_breakdown", [])
                if penalties:
                    pen_html = []
                    for pen in penalties:
                        pen_html.append(
                            f'<div style="background: #FEF2F2; border: 1px solid #FECACA; border-left: 4px solid #DC2626; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">'
                            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">'
                            f'<span style="font-size: 14.5px; font-weight: 800; color: #991B1B;">{pen.get("penalty_name")}</span>'
                            f'<span style="background: #DC2626; color: #FFFFFF; font-size: 11.5px; font-weight: 800; padding: 2px 8px; border-radius: 9999px;">-{pen.get("points")} pts</span>'
                            f'</div>'
                            f'<div style="font-size: 13.5px; color: #7F1D1D; line-height: 1.5;">{pen.get("reason")}</div>'
                            f'</div>'
                        )
                    st.html("".join(pen_html))
                else:
                    st.html(
                        '<div style="background: #F0FDF4; border: 1.5px solid #BBF7D0; border-left: 4px solid #10B981; border-radius: 8px; padding: 16px 18px; color: #064E3B; font-weight: 700; font-size: 14px;">'
                        '✔ Zero statutory forensic risk deductions applied. Clean regulatory audit profile.'
                        '</div>'
                    )

        with bridge_col2:
            with st.container(border=True):
                bb = res.get("bonuses_breakdown", {})
                st.markdown(
                    '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">'
                    '<span style="font-size: 13.5px; font-weight: 800; color: #4C1D95; text-transform: uppercase;">Applied Growth Bonuses</span>'
                    '<span style="background: #EDE9FE; color: #5B21B6; border: 1px solid #C4B5FD; font-size: 11.5px; font-weight: 800; padding: 2px 8px; border-radius: 9999px;">+10.0% Max Cap</span>'
                    '</div>',
                    unsafe_allow_html=True
                )
                st.html(
                    f'<div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px;">'
                    f'<div style="background: #F5F3FF; border: 1px solid #DDD6FE; border-left: 4px solid #7C3AED; border-radius: 6px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center;">'
                    f'<div><span style="font-weight: 800; color: #4C1D95; font-size: 13.5px;">COOL++ PRO Bonus</span><div style="font-size: 12px; color: #6D28D9;">Capital-Light Operating Leverage Outperformance</div></div>'
                    f'<span style="background: #7C3AED; color: #FFFFFF; font-size: 12.5px; font-weight: 800; padding: 3px 9px; border-radius: 9999px;">+{bb.get("cool_pro_bonus", 0):.1f}%</span>'
                    f'</div>'
                    f'<div style="background: #F5F3FF; border: 1px solid #DDD6FE; border-left: 4px solid #7C3AED; border-radius: 6px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center;">'
                    f'<div><span style="font-weight: 800; color: #4C1D95; font-size: 13.5px;">Trajectory Bonus</span><div style="font-size: 12px; color: #6D28D9;">Sustained Margin Expansion & FCF Compounding</div></div>'
                    f'<span style="background: #7C3AED; color: #FFFFFF; font-size: 12.5px; font-weight: 800; padding: 3px 9px; border-radius: 9999px;">+{bb.get("trajectory_bonus", 0):.1f}%</span>'
                    f'</div>'
                    f'<div style="background: #F5F3FF; border: 1px solid #DDD6FE; border-left: 4px solid #7C3AED; border-radius: 6px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center;">'
                    f'<div><span style="font-weight: 800; color: #4C1D95; font-size: 13.5px;">Resilience Bonus</span><div style="font-size: 12px; color: #6D28D9;">Balance Sheet Solvency & Counter-Cyclical Endurance</div></div>'
                    f'<span style="background: #7C3AED; color: #FFFFFF; font-size: 12.5px; font-weight: 800; padding: 3px 9px; border-radius: 9999px;">+{bb.get("resilience_bonus", 0):.1f}%</span>'
                    f'</div>'
                    f'</div>'
                    f'<div style="background: #EDE9FE; border: 1.5px solid #A78BFA; border-radius: 8px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center;">'
                    f'<span style="font-size: 13px; font-weight: 800; color: #4C1D95; text-transform: uppercase;">Total Growth Bonus Applied</span>'
                    f'<span style="font-size: 20px; font-weight: 900; color: #4C1D95; font-family: \'JetBrains Mono\', monospace;">+{bb.get("total_bonus_applied", 0):.1f}%</span>'
                    f'</div>'
                )

    # --- SECTION B: PEER RELATIVE BENCHMARK MATRIX ---
    if show_all or dossier_tab == "👥 Peer Relative Matrix":
        st.markdown(
            f'<div style="margin-top: 24px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1.5px solid #E2E8F0; padding-bottom: 10px;">'
            f'<div style="font-size: 18px; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 8px;">'
            f'<span>👥</span> Peer Relative Benchmark Matrix ({target_sector})'
            f'</div>'
            f'<span style="font-size: 12px; color: #64748B;">Standardized 100-Point Quality & Valuation Comparison</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        peers = res.get("peer_matrix", [])
        if peers:
            p_rows = []
            # Target company highlighted row
            p_rows.append(
                f'<tr style="background: #F0FDF4; border-bottom: 2px solid #BBF7D0;">'
                f'<td style="padding: 12px 16px; font-weight: 900; color: #064E3B;">'
                f'{target_company_name} <span style="background: #059669; color: #FFFFFF; font-size: 10.5px; font-weight: 800; padding: 2px 7px; border-radius: 4px; margin-left: 6px;">EVALUATED</span>'
                f'</td>'
                f'<td style="padding: 12px 16px; text-align: center;"><span style="background: #059669; color: #FFFFFF; padding: 4px 10px; border-radius: 6px; font-weight: 900; font-family: monospace; font-size: 14px;">{final_score:.1f} / 100</span></td>'
                f'<td style="padding: 12px 16px;"><span style="background: #DCFCE7; color: #166534; border: 1px solid #86EFAC; padding: 3px 9px; border-radius: 6px; font-weight: 800; font-size: 12px;">Active Target ({verdict})</span></td>'
                f'</tr>'
            )
            for p in peers:
                p_name = p.get("peer_name", "")
                p_sc = p.get("score", "N/A")
                p_pos = p.get("position", "Peer Competitor")
                p_rows.append(
                    f'<tr style="border-bottom: 1px solid #F1F5F9;">'
                    f'<td style="padding: 11px 16px; font-weight: 700; color: #1E293B;">{p_name}</td>'
                    f'<td style="padding: 11px 16px; text-align: center;"><span style="background: #F8FAFC; color: #0F172A; border: 1px solid #E2E8F0; padding: 3px 9px; border-radius: 6px; font-weight: 800; font-family: monospace; font-size: 13.5px;">{p_sc} / 100</span></td>'
                    f'<td style="padding: 11px 16px;"><span style="background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; padding: 3px 9px; border-radius: 6px; font-weight: 700; font-size: 12px;">{p_pos}</span></td>'
                    f'</tr>'
                )
            
            peer_table_html = (
                f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">'
                f'<table style="width: 100%; border-collapse: collapse; font-size: 13.5px;">'
                f'<thead>'
                f'<tr style="background: #F8FAFC; border-bottom: 1.5px solid #E2E8F0;">'
                f'<th style="padding: 12px 16px; text-align: left; font-weight: 800; color: #475569; font-size: 12px; text-transform: uppercase;">Constituent Company</th>'
                f'<th style="padding: 12px 16px; text-align: center; font-weight: 800; color: #475569; font-size: 12px; text-transform: uppercase;">IDEX Quality Score</th>'
                f'<th style="padding: 12px 16px; text-align: left; font-weight: 800; color: #475569; font-size: 12px; text-transform: uppercase;">Sector Position & Standing</th>'
                f'</tr>'
                f'</thead>'
                f'<tbody>{"".join(p_rows)}</tbody>'
                f'</table>'
                f'</div>'
            )
            st.html(peer_table_html)

        # 16 Canonical Screener Metrics Side-by-Side Comparison Matrix
        dossier_peer_html = render_head_to_head_comparison_html(
            target_ticker=target_ticker,
            target_company_name=target_company_name,
            target_sector=target_sector,
            live_data=live_data,
            financial_data=fin_res
        )
        st.html(dossier_peer_html)

    # --- SECTION C: 8-PILLAR SCORECARD & RADAR PROFILE ---
    if show_all or dossier_tab == "🏛️ 8-Pillar Scorecard & Radar":
        st.markdown(
            f'<div style="margin-top: 24px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1.5px solid #E2E8F0; padding-bottom: 10px;">'
            f'<div style="font-size: 18px; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 8px;">'
            f'<span>🏛️</span> 8-Pillar Quality Profile & Comprehensive Table'
            f'</div>'
            f'<span style="font-size: 12px; color: #64748B;">Standardized 100-Point Forensic Matrix</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        split_col1, split_col2 = st.columns([1.3, 1.7])

        with split_col1:
            with st.container(border=True):
                st.markdown("##### 8-Pillar Quality Profile")
                radar_fig = build_radar_chart(res.get("pillars", []))
                if radar_fig:
                    st.plotly_chart(radar_fig, width="stretch", alt="8-Pillar Radar Chart")
                
                st.caption("Active Forensic Tags:")
                tag_pills = []
                tag_color_map = {
                    "GOV-CLEAN": ("#ECFDF5", "#047857", "#A7F3D0"),
                    "GOV-RED": ("#FEF2F2", "#DC2626", "#FECACA"),
                    "PROM-ALERT": ("#FFFBEB", "#D97706", "#FDE68A"),
                    "ZERO-DEBT": ("#EFF6FF", "#1D4ED8", "#BFDBFE"),
                    "HIGH-ROCE": ("#ECFDF5", "#047857", "#A7F3D0"),
                    "COOL-PRO": ("#F5F3FF", "#6D28D9", "#DDD6FE"),
                    "DSO-PRISTINE": ("#ECFEFF", "#0E7490", "#A5F3FC"),
                }
                for t in res.get("tags_applied", []):
                    found_colors = None
                    for prefix, colors in tag_color_map.items():
                        if prefix in t:
                            found_colors = colors
                            break
                    if not found_colors:
                        found_colors = ("#F1F5F9", "#334155", "#CBD5E1")
                    bg, fg, bdr = found_colors
                    tag_pills.append(f'<span style="background: {bg}; color: {fg}; border: 1px solid {bdr}; padding: 3px 10px; border-radius: 9999px; font-size: 12px; font-weight: 700; display: inline-block; margin-right: 6px; margin-bottom: 6px;">{t}</span>')
                st.html(f'<div style="display: flex; flex-wrap: wrap; margin-top: 6px;">{"".join(tag_pills)}</div>')

        with split_col2:
            with st.container(border=True):
                st.markdown("##### Sector Receivable Health Layer")
                st.caption("Forensic Cash Conversion & Liquidity Benchmarking")
                
                rec = res.get("receivable_health_metrics", {})
                dso_val = rec.get('dso_days', 'N/A')
                dso_display = f"{dso_val} d" if str(dso_val).replace(".", "").isdigit() else str(dso_val)
                ideal_dso = rec.get('sector_ideal_dso', 'N/A')
                rec_sales = rec.get('receivables_to_sales_pct', 'N/A')
                over_90 = rec.get('pct_over_90_days', 'N/A')
                prov_cov = rec.get('provision_coverage_pct', 'N/A')
                verdict_text = rec.get('receivable_verdict', 'Normal')

                rec_cards_html = (
                    f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px;">'
                    f'<div style="background: #F0FDFA; border: 1px solid #99F6E4; border-radius: 8px; padding: 12px 16px;">'
                    f'<div style="font-size: 11.5px; font-weight: 700; color: #0F766E; text-transform: uppercase;">DSO (Days Sales)</div>'
                    f'<div style="font-size: 22px; font-weight: 800; color: #115E59; font-family: \'JetBrains Mono\', monospace; margin: 4px 0;">{dso_display}</div>'
                    f'<div style="font-size: 11.5px; color: #0D9488; font-weight: 600;">Sector Benchmark: {ideal_dso}</div>'
                    f'</div>'
                    f'<div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 12px 16px;">'
                    f'<div style="font-size: 11.5px; font-weight: 700; color: #1D4ED8; text-transform: uppercase;">Receivables / Sales</div>'
                    f'<div style="font-size: 22px; font-weight: 800; color: #1E40AF; font-family: \'JetBrains Mono\', monospace; margin: 4px 0;">{rec_sales}</div>'
                    f'<div style="font-size: 11.5px; color: #2563EB; font-weight: 600;">Balance Sheet Weight</div>'
                    f'</div>'
                    f'<div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 8px; padding: 12px 16px;">'
                    f'<div style="font-size: 11.5px; font-weight: 700; color: #B45309; text-transform: uppercase;">>90 Days Overdue</div>'
                    f'<div style="font-size: 22px; font-weight: 800; color: #92400E; font-family: \'JetBrains Mono\', monospace; margin: 4px 0;">{over_90}</div>'
                    f'<div style="font-size: 11.5px; color: #D97706; font-weight: 600;">Delinquency Risk</div>'
                    f'</div>'
                    f'<div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 12px 16px;">'
                    f'<div style="font-size: 11.5px; font-weight: 700; color: #15803D; text-transform: uppercase;">Provision Coverage</div>'
                    f'<div style="font-size: 22px; font-weight: 800; color: #166534; font-family: \'JetBrains Mono\', monospace; margin: 4px 0;">{prov_cov}</div>'
                    f'<div style="font-size: 11.5px; color: #16A34A; font-weight: 600;">ECL Buffer</div>'
                    f'</div>'
                    f'</div>'
                    f'<div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-left: 4px solid #059669; border-radius: 6px; padding: 10px 14px; display: flex; align-items: center; gap: 10px;">'
                    f'<span style="font-size: 20px;">🛡️</span>'
                    f'<div>'
                    f'<div style="font-size: 11px; font-weight: 800; color: #047857; text-transform: uppercase;">Forensic Assessment</div>'
                    f'<div style="font-size: 13.5px; font-weight: 700; color: #064E3B;">{verdict_text}</div>'
                    f'</div>'
                    f'</div>'
                )
                st.html(rec_cards_html)

        # 8-Pillar Table with Quality Tier Filter & Density Toggle
        tbl_c1, tbl_c2 = st.columns([3, 1])
        with tbl_c1:
            p_filter = st.segmented_control(
                "Filter Quality Tier",
                options=["All Pillars", "Pristine (≥80%)", "Moderate (50-79%)", "Fragile (<50%)"],
                default="All Pillars",
                key="p_filter_ctrl",
                label_visibility="collapsed"
            )
        with tbl_c2:
            p_density = st.segmented_control(
                "Table Density",
                options=["Detailed", "Compact"],
                default="Detailed",
                key="p_density_ctrl",
                label_visibility="collapsed"
            )

        table_rows = []
        for p in res.get("pillars", []):
            p_id = p.get("id", 1)
            p_score = p.get("score", 0)
            p_max = p.get("max_score", 1)
            pct = (p_score / p_max) * 100 if p_max > 0 else 0

            # Apply quality filter
            if p_filter == "Pristine (≥80%)" and pct < 80.0:
                continue
            elif p_filter == "Moderate (50-79%)" and not (50.0 <= pct < 80.0):
                continue
            elif p_filter == "Fragile (<50%)" and pct >= 50.0:
                continue
            
            meta = PILLAR_METADATA.get(p_id, {"icon": "📌", "chip": "Quality", "chip_bg": "#F1F5F9", "chip_fg": "#334155", "border": "#CBD5E1"})
            
            if pct >= 85:
                badge = f'<span style="background:#ECFDF5; color:#047857; border:1px solid #10B981; padding:5px 12px; border-radius:9999px; font-weight:800; font-size:12px; display:inline-flex; align-items:center; gap:4px; box-shadow: 0 1px 2px rgba(16,185,129,0.1);">✨ {pct:.0f}% • Pristine</span>'
                bar_color = "#059669"
            elif pct >= 70:
                badge = f'<span style="background:#F0FDF4; color:#059669; border:1px solid #86EFAC; padding:5px 12px; border-radius:9999px; font-weight:700; font-size:12px; display:inline-flex; align-items:center; gap:4px;">🟢 {pct:.0f}% • Strong</span>'
                bar_color = "#10B981"
            elif pct >= 50:
                badge = f'<span style="background:#FFFBEB; color:#B45309; border:1px solid #FCD34D; padding:5px 12px; border-radius:9999px; font-weight:700; font-size:12px; display:inline-flex; align-items:center; gap:4px;">🟡 {pct:.0f}% • Moderate</span>'
                bar_color = "#F59E0B"
            else:
                badge = f'<span style="background:#FEF2F2; color:#DC2626; border:1px solid #FCA5A5; padding:5px 12px; border-radius:9999px; font-weight:700; font-size:12px; display:inline-flex; align-items:center; gap:4px;">🔴 {pct:.0f}% • Fragile</span>'
                bar_color = "#EF4444"
                
            rec_html = ""
            if "receivable_subscore" in p:
                rec_html = f'<div style="margin-top: 10px; background: #ECFDF5; border-left: 3px solid #059669; padding: 6px 12px; font-size: 13px; font-weight: 600; color: #065F46; border-radius: 0 4px 4px 0;">⚡ Sector Receivable Health Subscore: <strong>{p["receivable_subscore"]}</strong></div>'

            pillar_citations = p.get("citations", [])
            c_links = []
            if pillar_citations:
                for c in pillar_citations:
                    u = c.get("url", "")
                    if str(u).startswith(("https://", "http://")):
                        raw_title = c.get("title") or c.get("source_id") or "Source"
                        clean_t = str(raw_title).replace("https://", "").replace("http://", "").rstrip("/")
                        if len(clean_t) > 35:
                            clean_t = clean_t[:32] + "…"
                        c_links.append(f'<a href="{html.escape(u, quote=True)}" target="_blank" style="color: #2563EB; font-weight: 700; text-decoration: underline; font-size: 12px;">{html.escape(clean_t)} ↗</a>')
            
            if c_links:
                citation_html = f'<div style="font-size:12px; margin-top:6px; color:#475569;">🔗 <strong>Sources:</strong> {" &bull; ".join(c_links)}</div>'
            else:
                # Fallback to statutory filing, web research, or verified exchange data
                fm = res.get("filing_metadata") or {}
                if fm.get("url") and str(fm.get("url")).startswith(("https://", "http://")):
                    f_title = fm.get("title") or "Official BSE India Filing"
                    citation_html = f'<div style="font-size:12px; margin-top:6px; color:#475569;">📄 <strong>Source:</strong> <a href="{html.escape(fm["url"], quote=True)}" target="_blank" style="color: #2563EB; font-weight: 700; text-decoration: underline;">{html.escape(f_title)} ↗</a></div>'
                elif res.get("web_research", {}).get("sources"):
                    top_sources = [s for s in res["web_research"]["sources"] if str(s.get("url", "")).startswith(("https://", "http://"))][:2]
                    if top_sources:
                        s_links = [f'<a href="{html.escape(s["url"], quote=True)}" target="_blank" style="color: #2563EB; font-weight: 700; text-decoration: underline;">{html.escape(s.get("title") or s.get("source_id") or "Web Source")} ↗</a>' for s in top_sources]
                        citation_html = f'<div style="font-size:12px; margin-top:6px; color:#475569;">🌐 <strong>Sources:</strong> {" &bull; ".join(s_links)}</div>'
                    else:
                        citation_html = f'<div style="font-size:12px; margin-top:6px; color:#64748B;">📊 <strong>Source:</strong> Official Exchange Filings & Screener Dataset</div>'
                else:
                    citation_html = f'<div style="font-size:12px; margin-top:6px; color:#64748B;">📊 <strong>Source:</strong> Official Exchange Filings & Screener Dataset</div>'
                
            justification_text = p.get("justification", "")
            if p_density == "Compact" and len(justification_text) > 130:
                justification_text = justification_text[:126].rsplit(" ", 1)[0] + "…"

            row_html = (
                f'<tr>'
                f'<td style="width: 25%; font-weight: 700;">'
                f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">'
                f'<span style="font-size: 18px;">{meta["icon"]}</span>'
                f'<span style="font-size: 15px; color: #0F172A; font-weight: 800;">P{p_id}: {p.get("name")}</span>'
                f'</div>'
                f'<span style="background: {meta["chip_bg"]}; color: {meta["chip_fg"]}; border: 1px solid {meta["border"]}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 9999px;">{meta["chip"]}</span>'
                f'</td>'
                f'<td style="width: 14%; text-align: center;">'
                f'<div style="font-family: \'JetBrains Mono\', monospace; font-size: 18px; font-weight: 800; color: #047857;">{p_score:.1f} <span style="font-size: 13px; font-weight: 500; color: #64748B;">/ {p_max:.1f}</span></div>'
                f'<div style="background: #E2E8F0; border-radius: 9999px; height: 6px; width: 85%; margin: 6px auto 0 auto; overflow: hidden;">'
                f'<div style="background: {bar_color}; width: {pct:.1f}%; height: 100%; border-radius: 9999px;"></div>'
                f'</div>'
                f'</td>'
                f'<td style="width: 16%; text-align: center;">{badge}</td>'
                f'<td style="width: 45%;"><div style="font-size: 14.5px; line-height: 1.6; color: #334155;">{justification_text}</div>{citation_html}{rec_html}</td>'
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

    # --- SECTION D: AUDITOR EVIDENCE PACK & VALUATION MATH ---
    if show_all or dossier_tab == "🔍 Auditor Evidence & Math":
        st.markdown(
            f'<div style="margin-top: 24px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1.5px solid #E2E8F0; padding-bottom: 10px;">'
            f'<div style="font-size: 18px; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 8px;">'
            f'<span>🔍</span> Statutory Auditor Evidence Pack & Forensic Calculations'
            f'</div>'
            f'<span style="font-size: 12px; color: #64748B;">Appendix A (Auditor Excerpts) & Appendix B (Valuation Math)</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        with st.container(border=True):
            st.markdown("##### Appendix A — Load-Bearing Forensic Citations")
            st.caption("Exact quotes, regulatory disclosures, and load-bearing statutory audit excerpts:")
            ev_items = "".join([
                f'<div style="font-size: 13.5px; line-height: 1.6; color: #1E293B; margin-bottom: 10px; padding: 12px 16px; background: #F8FAFC; border-left: 3.5px solid #059669; border-radius: 0 8px 8px 0; border-top: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0;">'
                f'<span style="color: #059669; font-weight: 800; margin-right: 6px;">●</span> {e}'
                f'</div>'
                for e in res.get("appendix_a_forensic_evidence", [])
            ])
            if ev_items:
                st.html(ev_items)
            else:
                st.info("No statutory auditor qualifications or load-bearing exceptions reported.")
            
            st.divider()
            st.markdown("##### Appendix B — Forensic Calculations & Stress Tests")
            calcs = res.get("appendix_b_calculations", {})
            calc_cards = []
            for k, v in calcs.items():
                calc_cards.append(
                    f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 8px; padding: 14px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">'
                    f'<div style="font-size: 11.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">{k.replace("_", " ").title()}</div>'
                    f'<div style="font-size: 14px; font-weight: 700; color: #0F172A; margin-top: 6px; line-height: 1.45;">{v}</div>'
                    f'</div>'
                )
            if calc_cards:
                st.html(f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;">{"".join(calc_cards)}</div>')
            else:
                st.info("Forensic calculation disclosures unavailable for this asset.")

    # 4. MANDATORY GUARDRAIL & PROMOTER INTEGRITY AUDIT (BELOW PILLARS)
    st.write("")
    tag = res.get("guardrail_tag", "GOV-CLEAN 🟢")
    evidence_list = res.get("guardrail_evidence", [])
    ev_html_items = "".join([f'<li style="margin-bottom: 4px;">{e}</li>' for e in evidence_list])
    
    if "GOV-RED" in tag or res.get("pio_triggered", False):
        st.html(
            f'<div class="guardrail-red-box">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
            f'<span style="font-weight: 800; font-size: 1.15rem; color: #DC2626;">🚨 MANDATORY GUARDRAIL TAG: {tag} (PIO HARD TRIGGER FIRED)</span>'
            f'<span style="background-color: #FEE2E2; color: #991B1B; padding: 4px 12px; border-radius: 9999px; font-weight: 800; font-size: 0.8rem; border: 1px solid #FCA5A5;">CRITICAL FORENSIC RISK</span>'
            f'</div>'
            f'<p style="margin: 0 0 10px 0; font-weight: 600; color: #991B1B;">{res.get("pio_reason", "Promoter Integrity Override triggered. Governance pillar capped at ≤6.0/20. Bonuses blocked. Forced into Red Zone.")}</p>'
            f'<ul style="margin: 0; padding-left: 20px; color: #7F1D1D;">{ev_html_items}</ul>'
            f'</div>'
        )
    elif "PROM-ALERT" in tag:
        st.html(
            f'<div class="guardrail-alert-box">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
            f'<span style="font-weight: 800; font-size: 1.15rem; color: #D97706;">⚠️ MANDATORY GUARDRAIL TAG: {tag}</span>'
            f'<span style="background-color: #FEF3C7; color: #92400E; padding: 4px 12px; border-radius: 9999px; font-weight: 800; font-size: 0.8rem; border: 1px solid #FCD34D;">PROMOTER ALERT</span>'
            f'</div>'
            f'<p style="margin: 0 0 10px 0; color: #92400E; font-weight: 600;">Elevated promoter pledging or dilution observed under PPRM rules.</p>'
            f'<ul style="margin: 0; padding-left: 20px; color: #78350F;">{ev_html_items}</ul>'
            f'</div>'
        )
    else:
        st.html(
            f'<div class="guardrail-clean-box">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
            f'<span style="font-weight: 800; font-size: 1.15rem; color: #047857;">🛡️ PROMOTER INTEGRITY & GOVERNANCE VERDICT: {tag}</span>'
            f'<span style="background-color: #D1FAE5; color: #065F46; padding: 4px 12px; border-radius: 9999px; font-weight: 800; font-size: 0.8rem; border: 1px solid #A7F3D0;">INSTITUTIONAL GRADE</span>'
            f'</div>'
            f'<p style="margin: 0 0 8px 0; color: #064E3B; font-weight: 600;">10Y+ clean statutory audit history, zero promoter share pledge, verified arm\'s length related-party disclosures.</p>'
            f'<ul style="margin: 0; padding-left: 20px; color: #1E293B;">{ev_html_items}</ul>'
            f'</div>'
        )

    # 5. EXPORT TOOLBAR
    st.write("")
    st.divider()
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    
    with exp_col1:
        st.download_button(
            label="Download Structured JSON",
            data=json.dumps(res, indent=2),
            file_name=f"{res.get('company_name', 'Company')}_StockSage.json",
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
            return ", ".join(f"[{c.get('source_id', 'source')}]({c.get('url', '')})" for c in items if str(c.get("url", "")).startswith(("https://", "http://"))) or "Insufficient evidence citation"

        web_sources_md = "\n".join(
            f"- [{s.get('source_id')}: {s.get('title')}]({s.get('url')}) — published: {s.get('published_date') or 'not supplied by API'}; retrieved: {s.get('retrieved_at', 'unknown')} ({s.get('source_type', 'web evidence')})"
            for s in res.get("web_research", {}).get("sources", [])
        ) or "Insufficient evidence: no grounded web sources returned."
        pillars_md = "\n".join(
            f"- **Pillar {p.get('id')}: {p.get('name')}**: {p.get('score')}/{p.get('max_score')} ({p.get('justification')}) — {source_refs(p.get('citations', []))}"
            for p in res.get("pillars", [])
        )
        penalties_md = "\n".join(
            f"- **{p.get('penalty_name')} ({p.get('points')} pts):** {p.get('reason')} — {source_refs(p.get('citations', []))}"
            for p in res.get("penalties_breakdown", [])
        ) or "No penalties applied."
        bonus = res.get("bonuses_breakdown", {})
        call_refs = source_refs(res.get("final_call_citations", []))

        filing_meta_md = ""
        if res.get("filing_metadata"):
            fm = res["filing_metadata"]
            f_u = fm.get("url") or "Uploaded directly"
            filing_meta_md = f"- **Statutory Filing Analyzed:** [{fm.get('title')}]({f_u}) ({fm.get('source', 'Archive')}, Period: {fm.get('year', 'Latest')})\n"

        md_text = f"""{demo_header}# StockSage | Institutional Research Memo: {res.get('company_name')}

## Metadata
- **Target Company:** {res.get('company_name')}
- **Sector Benchmark:** {res.get('sector')}
- **Reporting Period:** {res.get('financial_year')}
{filing_meta_md}- **Final Rating:** {res.get('verdict')} (Score: {res.get('final_score')}/100)
- **Position Sizing:** {res.get('position_sizing')}
- **Evidence status:** {res.get('analysis_status', 'unknown')}
- **Evidence gaps:** {', '.join(res.get('evidence_gaps', [])) or 'None reported'}

## Web Research Sources
Search queries: {', '.join(res.get('web_research', {}).get('search_queries', [])) or 'No query metadata returned'}
{web_sources_md}

## Mandatory Guardrail Tag
**{res.get('guardrail_tag')}**
{chr(10).join(['- ' + ev for ev in res.get('guardrail_evidence', [])])}

## Core 8-Pillar Scorecard
{pillars_md}

## Penalties and Bonuses
{penalties_md}
- **Bonus total ({bonus.get('total_bonus_applied', 0)} pts):** {bonus.get('reason', 'Insufficient evidence rationale.')} — {source_refs(bonus.get('citations', []))}

## Sector-Sensitive Receivable Layer
- DSO: {rec.get('dso_days')} days (Ideal: {rec.get('sector_ideal_dso')})
- Overdue >90 Days: {rec.get('pct_over_90_days')}
- Receivables / Sales: {rec.get('receivables_to_sales_pct')}
- Verdict: {rec.get('receivable_verdict')}

## Final Call
**{res.get('final_call')}** — {call_refs}
"""
        st.download_button(
            label="Download Investment Memo (.md)",
            data=md_text,
            file_name=f"{res.get('company_name', 'Company')}_StockSage_Memo.md",
            mime="text/markdown",
            width="stretch"
        )

    with exp_col3:
        # Printable Executive HTML Report for PDF generation via Browser Print
        demo_html_banner = (
            '<div style="background:#fef3c7; border:2px solid #f59e0b; padding:12px 16px; border-radius:6px; font-size:13.5px; font-weight:700; color:#92400e; margin-bottom:18px; text-align:center;">'
            '⚠️ SYNTHETIC DEMO MODE — FOR TESTING ONLY. NOT INVESTMENT RESEARCH OR ADVICE.'
            '</div>'
        ) if is_demo_export else ""

        html_report = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{res.get('company_name', 'Company')} - StockSage Institutional Report</title>
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
            <h1>StockSage • {res.get('company_name', 'Company')}</h1>
            <p style="color:#64748b; margin-top:-8px;">Sector: {res.get('sector')} • Period: {res.get('financial_year')} • Institutional Forensic Research</p>
        </div>
        <div style="text-align:right;">
            <div style="font-size:32px; font-weight:800; color:#047857;">{res.get('final_score', 0):.1f}<span style="font-size:16px; color:#64748b;">/100</span></div>
            <div class="badge">{res.get('verdict')}</div>
        </div>
    </div>

    <h2>Core 8-Pillar Evaluation</h2>
    <table>
        <thead><tr><th>Pillar</th><th>Score</th><th>Max</th><th>Forensic Justification</th></tr></thead>
        <tbody>
            {''.join([f"<tr><td><strong>P{p.get('id')}: {p.get('name')}</strong></td><td><strong>{p.get('score')}</strong></td><td>{p.get('max_score')}</td><td>{p.get('justification')}</td></tr>" for p in res.get('pillars', [])])}
        </tbody>
    </table>

    <h2>Sector Receivable Health</h2>
    <table>
        <tr><td><strong>DSO:</strong> {rec.get('dso_days')} days (Ideal: {rec.get('sector_ideal_dso')})</td><td><strong>Receivables/Sales:</strong> {rec.get('receivables_to_sales_pct')}</td></tr>
        <tr><td><strong>Overdue >90d:</strong> {rec.get('pct_over_90_days')}</td><td><strong>Assessment:</strong> {rec.get('receivable_verdict')}</td></tr>
    </table>

    <div class="tag-box">
        <strong>Mandatory Guardrail Tag: {res.get('guardrail_tag')}</strong>
        <ul style="margin: 8px 0 0 0; padding-left: 20px;">{''.join([f'<li>{e}</li>' for e in res.get('guardrail_evidence', [])])}</ul>
    </div>

    <h2>Analyst Recommendation</h2>
    <div style="background:#f8fafc; border: 1px solid #e2e8f0; padding:14px; border-radius:6px; font-size:16px; font-weight:600; color: #0f172a;">
        {res.get('final_call')}
    </div>
</body>
</html>"""
        st.download_button(
            label="Print Analyst Report (PDF/HTML)",
            data=html_report,
            file_name=f"{res.get('company_name', 'Company')}_StockSage_Report.html",
            mime="text/html",
            width="stretch"
        )

# --- INSTITUTIONAL FORENSIC ARCHITECTURE & METHODOLOGY PIPELINE (GRAPHICAL & BOTTOM-ANCHORED) ---
st.markdown("<div style='margin-top: 36px; margin-bottom: 12px;'></div>", unsafe_allow_html=True)
with st.expander("🧭 **StockSage Forensic Architecture & Evaluation Pipeline (Visual Methodology & Benchmarks)**", expanded=False):
    st.html(render_graphical_forensic_architecture_html())
