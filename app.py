"""
app.py
FinScan India | IDEX-7.5SC Hybrid Pro (Ashu Elite Edition)
Institutional AI Financial Intelligence Terminal for Indian Listed Equities
"""

import streamlit as st
import plotly.graph_objects as go
import json
import os
import time
from dotenv import load_dotenv

# Load local environment variables dynamically
load_dotenv(override=True)

from prompt_template import IDEX_ANALYSIS_PROMPT
import importlib
import analyzer
import nifty_universe
importlib.reload(analyzer)
importlib.reload(nifty_universe)

from analyzer import analyze_document_with_gemini, get_demo_analysis, verify_gemini_api_key
from nifty_universe import get_company_list, find_company_info, fetch_live_market_data, get_sector_list

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

# Screener.in Inspired Green & White Institutional CSS
st.markdown("""
<style>
    /* Global Screener-grade Typography */
    html, body, [class*="css"] {
        font-size: 15px;
    }
    
    /* Screener-Style Main Headings */
    h1, .stHeadingContainer h1 {
        font-size: 32px !important;
        font-weight: 800 !important;
        letter-spacing: -0.6px !important;
        color: #0F172A !important;
    }
    h2, .stHeadingContainer h2 {
        font-size: 24px !important;
        font-weight: 700 !important;
        letter-spacing: -0.4px !important;
        color: #0F172A !important;
    }
    h3, .stHeadingContainer h3 {
        font-size: 20px !important;
        font-weight: 700 !important;
        color: #0F172A !important;
    }
    h4, .stHeadingContainer h4 {
        font-size: 17px !important;
        font-weight: 600 !important;
        color: #0F172A !important;
    }

    /* Screener.in Iconic Tabs: Big, Bold, Clean Green Underline */
    div[data-baseweb="tab-list"] {
        gap: 8px !important;
        border-bottom: 2px solid #E2E8F0 !important;
        padding-bottom: 0px !important;
        margin-top: 14px !important;
        margin-bottom: 24px !important;
    }
    button[data-baseweb="tab"] {
        font-size: 16.5px !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        border-radius: 6px 6px 0 0 !important;
        color: #64748B !important;
        background: transparent !important;
        border: none !important;
        letter-spacing: -0.2px !important;
        transition: all 0.15s ease-in-out !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #059669 !important;
        background-color: #F0FDF4 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #047857 !important;
        font-weight: 700 !important;
        border-bottom: 3.5px solid #059669 !important;
        background-color: transparent !important;
    }
    div[data-baseweb="tab-border"] {
        display: none !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: #059669 !important;
        height: 3.5px !important;
    }

    /* Screener-Style Key Ratio Metric Cards: Big, Crisp & Legible */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 16px 20px !important;
        border-radius: 8px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
        transition: border-color 0.15s ease !important;
    }
    [data-testid="stMetric"]:hover {
        border-color: #A7F3D0 !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', -apple-system, BlinkMacSystemFont, monospace !important;
        font-size: 28px !important;
        font-weight: 700 !important;
        letter-spacing: -0.6px !important;
        color: #0F172A !important;
        line-height: 1.25 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #64748B !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 14px !important;
        font-weight: 600 !important;
    }

    /* Screener-Style Institutional Emerald Primary Button */
    button[kind="primary"] {
        background-color: #059669 !important;
        color: #FFFFFF !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 14px 28px !important;
        border-radius: 8px !important;
        border: 1px solid #047857 !important;
        letter-spacing: -0.2px !important;
        transition: all 0.2s ease !important;
    }
    button[kind="primary"]:hover {
        background-color: #047857 !important;
        opacity: 0.95 !important;
        transform: translateY(-1px) !important;
    }

    /* Progress Bar (Screener Green Style) */
    .stProgress > div > div > div > div {
        background-color: #059669 !important;
        border-radius: 6px !important;
    }
    .stProgress > div > div > div {
        background-color: #E2E8F0 !important;
        height: 10px !important;
        border-radius: 6px !important;
    }

    /* 8-Pillar Screener-Grade Financial Table */
    .pillar-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        overflow: hidden;
        background: #FFFFFF;
        margin: 14px 0 24px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .pillar-table th {
        background-color: #F8FAFC;
        padding: 14px 18px;
        font-size: 13px;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 2px solid #E2E8F0;
        border-right: 1px solid #F1F5F9;
    }
    .pillar-table th:last-child {
        border-right: none;
    }
    .pillar-table td {
        padding: 16px 18px;
        border-bottom: 1px solid #F1F5F9;
        border-right: 1px solid #F1F5F9;
        vertical-align: top;
        font-size: 14.5px;
        color: #1E293B;
        line-height: 1.55;
    }
    .pillar-table td:last-child {
        border-right: none;
    }
    .pillar-table tr:last-child td {
        border-bottom: none;
    }
    .pillar-table tr:hover td {
        background-color: #F0FDF4;
    }

    /* Guardrail Banners - Refined Green & White with subtle semantic borders */
    .guardrail-clean-box {
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
        border: 1.5px solid #10B981;
        border-left: 5px solid #059669;
        border-radius: 8px;
        padding: 18px 24px;
        color: #0F172A;
        margin-top: 16px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(16, 185, 129, 0.06);
    }
    .guardrail-alert-box {
        background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
        border: 1.5px solid #F59E0B;
        border-left: 5px solid #D97706;
        border-radius: 8px;
        padding: 18px 24px;
        color: #0F172A;
        margin-top: 16px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(245, 158, 11, 0.06);
    }
    .guardrail-red-box {
        background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
        border: 2px solid #EF4444;
        border-left: 5px solid #DC2626;
        border-radius: 8px;
        padding: 18px 24px;
        color: #0F172A;
        margin-top: 16px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(239, 68, 68, 0.06);
    }

    /* Preset Benchmark Chips */
    button[kind="secondary"] {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.15s ease !important;
    }
    button[kind="secondary"]:hover {
        border-color: #059669 !important;
        color: #047857 !important;
        background-color: #F0FDF4 !important;
        transform: translateY(-1px) !important;
    }

    /* StockSage Bespoke Financial Factsheet & 3-Column Matrix */
    .facts-header-card {
        background: #FFFFFF;
        border: 1.5px solid #E2E8F0;
        border-radius: 14px;
        padding: 26px 30px;
        margin-top: 16px;
        margin-bottom: 22px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    }
    .metrics-3col-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 22px;
        margin-bottom: 26px;
    }
    @media (max-width: 1100px) {
        .metrics-3col-grid {
            grid-template-columns: 1fr;
        }
    }
    .metric-domain-card {
        background: #FFFFFF;
        border: 1.5px solid #E2E8F0;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-domain-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
    }
    .metric-table-spacious {
        width: 100%;
        border-collapse: collapse;
    }
    .metric-table-spacious tr {
        border-bottom: 1px solid #F1F5F9;
        transition: background-color 0.12s ease;
    }
    .metric-table-spacious tr:last-child {
        border-bottom: none;
    }
    .metric-table-spacious tr:hover {
        background-color: #F0FDF4 !important;
    }
    .metric-table-spacious td.m-label {
        padding: 12px 18px;
        font-size: 14px;
        font-weight: 600;
        color: #475569;
        text-align: left;
        white-space: nowrap;
    }
    .metric-table-spacious td.m-value {
        padding: 12px 18px;
        font-size: 14.5px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        color: #0F172A;
        text-align: right;
        white-space: nowrap;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### StockSage")
    st.caption("Dalal Street Equity Intelligence • Ashu Elite Edition")
    
    st.html("""
    <div style="background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border: 1.5px solid #86EFAC; border-radius: 8px; padding: 10px 14px; margin-top: 8px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(5,150,105,0.08);">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span style="font-size: 11.5px; font-weight: 800; color: #065F46; letter-spacing: 0.3px;">NSE / BSE GROUNDING</span>
            <span style="background: #059669; color: #FFFFFF; font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 9999px;">● LIVE</span>
        </div>
        <div style="font-size: 11px; color: #047857; margin-top: 4px; font-weight: 600;">501 Nifty Equities • 24 Sectors</div>
    </div>
    """)
    st.divider()

    # API Configuration
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=env_key,
        type="password",
        help="Free key with 15 RPM & 1M context from Google AI Studio."
    )

    active_api_key = api_key_input.strip() if api_key_input and api_key_input.strip() else env_key

    if env_key:
        st.caption("Key auto-loaded from .env")

    col_btn1, col_btn2 = st.columns([1.2, 1])
    with col_btn1:
        if st.button("Test Key", width="stretch"):
            with st.spinner("Connecting to Google..."):
                is_valid, msg = verify_gemini_api_key(active_api_key)
                if is_valid:
                    st.success(msg)
                else:
                    st.error(msg)
    with col_btn2:
        demo_mode = st.toggle("Demo Mode", value=False if active_api_key else True)

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

# Top Hero Brand Navigation Banner
st.html("""
<div style="background: linear-gradient(135deg, #064E3B 0%, #065F46 45%, #047857 75%, #0F172A 100%); padding: 22px 28px; border-radius: 12px; margin-bottom: 20px; color: #FFFFFF; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 15px rgba(5, 150, 105, 0.16);">
  <div>
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 6px;">
      <span style="font-size: 26px; font-weight: 900; letter-spacing: -0.6px; color: #FFFFFF;">Stock<span style="color: #34D399;">Sage</span></span>
      <span style="background: #10B981; color: #022C22; font-size: 10.5px; font-weight: 800; padding: 3px 9px; border-radius: 9999px; letter-spacing: 0.5px;">PRO EDITION</span>
      <span style="background: rgba(255,255,255,0.15); color: #E2E8F0; font-size: 11px; font-weight: 600; padding: 3px 9px; border-radius: 9999px;">IDEX-7.5SC HYBRID</span>
    </div>
    <div style="font-size: 13.5px; color: #D1FAE5; font-weight: 400; max-width: 680px; line-height: 1.5;">
      Institutional Equity Intelligence & Forensic Audit Terminal • Real-Time NSE/BSE Market Grounding & 501 Nifty 500 Constituents
    </div>
  </div>
  <div style="display: flex; gap: 8px; flex-wrap: wrap;">
    <div style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 6px 14px; text-align: center;">
      <div style="font-size: 10.5px; color: #A7F3D0; font-weight: 600; text-transform: uppercase;">Universe</div>
      <div style="font-size: 15px; font-weight: 800; color: #FFFFFF;">501 Stocks</div>
    </div>
    <div style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 6px 14px; text-align: center;">
      <div style="font-size: 10.5px; color: #A7F3D0; font-weight: 600; text-transform: uppercase;">Taxonomy</div>
      <div style="font-size: 15px; font-weight: 800; color: #FFFFFF;">24 Sectors</div>
    </div>
    <div style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 6px 14px; text-align: center;">
      <div style="font-size: 10.5px; color: #A7F3D0; font-weight: 600; text-transform: uppercase;">Feed</div>
      <div style="font-size: 15px; font-weight: 800; color: #34D399;">● LIVE</div>
    </div>
  </div>
</div>
""")

# --- INTAKE CONSOLE ---
with st.container(border=True):
    st.markdown("#### Company Search")
    
    # Fast Preset Benchmark Chips
    st.caption("⚡ **Dalal Street Benchmarks (1-Click Instant Load):**")
    preset_cols = st.columns(6)
    presets = [
        ("Reliance", "RELIANCE", "🔵"),
        ("HDFC Bank", "HDFCBANK", "🟢"),
        ("Tata Consumer", "TATACONSUM", "🟠"),
        ("TCS", "TCS", "🟣"),
        ("Dixon Tech", "DIXON", "🔷"),
        ("HDFC Life", "HDFCLIFE", "🔴"),
    ]
    for idx, (label, sym, emoji) in enumerate(presets):
        with preset_cols[idx]:
            if st.button(f"{emoji} {label}", key=f"btn_preset_{sym}", width="stretch"):
                info = find_company_info(sym)
                st.session_state["selected_company_choice"] = info["display"]
                st.rerun()

    c_list = get_company_list()
    cur_choice = st.session_state.get("selected_company_choice", None)
    default_idx = c_list.index(cur_choice) if (cur_choice and cur_choice in c_list) else None

    col_sel1, col_sel2 = st.columns([2.5, 1.5])
    
    with col_sel1:
        selected_company_str = st.selectbox(
            "Company",
            options=c_list,
            index=default_idx,
            placeholder="Search by company name or symbol (e.g. Reliance, HDFC Bank, Infosys, Dixon)...",
            help="Select any listed Indian company from the Nifty 500 to pull live financial data."
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
            ["Live Market & Filings", "Upload Annual Report (PDF)"],
            default="Live Market & Filings"
        )

    # Optional PDF Upload
    uploaded_file = None
    if doc_type == "Upload Annual Report (PDF)":
        uploaded_file = st.file_uploader(
            "Upload Annual Report (PDF)",
            type=["pdf"],
            help="Upload the annual report. 200–500 page Indian reports are fully ingested by Gemini 3.5 Flash."
        )

# Reset evaluation if user cleared or switched selected company
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

live_data = None
if target_ticker and target_ticker != "CUSTOM":
    live_data = get_cached_live_data(target_ticker)

# Screener-grade Welcome / Empty State (When no company is selected)
if not selected_company_str:
    st.html("""
    <div style="background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%); border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 36px 32px; text-align: center; margin-top: 18px; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 64px; height: 64px; border-radius: 16px; background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%); border: 1.5px solid #A7F3D0; margin-bottom: 16px; font-size: 30px;">
            📈
        </div>
        <div style="font-size: 24px; font-weight: 800; color: #0F172A; letter-spacing: -0.5px; margin-bottom: 8px;">
            Dalal Street Institutional Intelligence Terminal
        </div>
        <div style="font-size: 14.5px; color: #64748B; max-width: 680px; margin: 0 auto 24px auto; line-height: 1.6;">
            Select any constituent from the <strong>501 Nifty 500 universe</strong> above or click a benchmark chip to inspect real-time NSE market valuations, 27 Screener ratios, and initiate the comprehensive 8-pillar forensic audit.
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; text-align: left; max-width: 920px; margin: 0 auto 16px auto;">
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px 16px; border-top: 3.5px solid #059669; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="font-size: 13px; font-weight: 800; color: #065F46; margin-bottom: 4px;">⚡ 27 SCREENER RATIOS</div>
                <div style="font-size: 12px; color: #64748B; line-height: 1.5;">Real-time Market Cap, P/E, ROCE, ROE, FCF & Graham Number calculated directly from NSE/BSE feeds.</div>
            </div>
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px 16px; border-top: 3.5px solid #2563EB; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="font-size: 13px; font-weight: 800; color: #1E40AF; margin-bottom: 4px;">🏛️ 8-PILLAR AUDIT</div>
                <div style="font-size: 12px; color: #64748B; line-height: 1.5;">Standardized 100-point forensic matrix across Governance, Accounting Forensics, FCF, and Moat durability.</div>
            </div>
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px 16px; border-top: 3.5px solid #DC2626; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="font-size: 13px; font-weight: 800; color: #991B1B; margin-bottom: 4px;">🛡️ PROMOTER INTEGRITY</div>
                <div style="font-size: 12px; color: #64748B; line-height: 1.5;">Hardwired PIO overrides, share pledge thresholds, and regulatory qualification tracking.</div>
            </div>
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px 16px; border-top: 3.5px solid #D97706; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="font-size: 13px; font-weight: 800; color: #92400E; margin-bottom: 4px;">📊 24 SECTOR BENCHMARKS</div>
                <div style="font-size: 12px; color: #64748B; line-height: 1.5;">Granular sector classification ensuring Insurance, Banks, AMCs, and NBFCs are properly evaluated.</div>
            </div>
        </div>
    </div>
    """)
    
    col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)
    with col_exp1:
        if st.button("🏢 Explore Reliance Industries", width="stretch", key="welc_rel"):
            st.session_state["selected_company_choice"] = find_company_info("RELIANCE")["display"]
            st.rerun()
    with col_exp2:
        if st.button("🏦 Explore HDFC Bank", width="stretch", key="welc_hdfc"):
            st.session_state["selected_company_choice"] = find_company_info("HDFCBANK")["display"]
            st.rerun()
    with col_exp3:
        if st.button("🛒 Explore Tata Consumer", width="stretch", key="welc_tataconsum"):
            st.session_state["selected_company_choice"] = find_company_info("TATACONSUM")["display"]
            st.rerun()
    with col_exp4:
        if st.button("💻 Explore TCS", width="stretch", key="welc_tcs"):
            st.session_state["selected_company_choice"] = find_company_info("TCS")["display"]
            st.rerun()

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
            val_span = f'<span style="background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; padding: 3px 9px; border-radius: 6px; font-weight: 800; font-size: 13.5px;">{value}</span>'
        elif style_mode == "teal":
            val_span = f'<span style="background: #F0FDFA; color: #0F766E; border: 1px solid #99F6E4; padding: 3px 9px; border-radius: 6px; font-weight: 700; font-size: 13.5px;">{value}</span>'
        elif style_mode == "bold":
            val_span = f'<span style="font-weight: 800; color: #0F172A; font-size: 14.5px;">{value}</span>'
        else:
            val_span = f'<span style="font-weight: 700; color: #1E293B; font-size: 14px;">{value}</span>'
            
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
        f'<span>• Ind AS Audited Statutory Disclosures</span>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div style="text-align: right; min-width: 220px;">'
        f'<div style="display: flex; align-items: baseline; justify-content: flex-end; gap: 10px;">'
        f'<span style="font-size: 32px; font-weight: 900; color: #0F172A; font-family: \'JetBrains Mono\', monospace; line-height: 1;">{cur_str}</span>'
        f'<span style="color: {delta_fg}; background: {delta_bg}; border: 1px solid {delta_fg}40; padding: 4px 12px; border-radius: 6px; font-size: 14px; font-weight: 800;">{delta_str}</span>'
        f'</div>'
        f'<div style="font-size: 12px; color: #64748B; margin-top: 6px;">Real-Time NSE/BSE Quote • {price_date}</div>'
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
        f'<div style="font-size: 12.5px; font-weight: 800; color: #0F172A; letter-spacing: 0.6px; text-transform: uppercase; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">'
        f'<span>🏢</span> Corporate Operations & Business Model'
        f'</div>'
        f'<div style="font-size: 14px; line-height: 1.65; color: #334155;">{about_text}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 18px 22px; display: flex; flex-direction: column; justify-content: space-between;">'
        f'<div>'
        f'<div style="font-size: 12.5px; font-weight: 800; color: #0F172A; letter-spacing: 0.6px; text-transform: uppercase; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">'
        f'<span>🔑</span> Institutional Market Position'
        f'</div>'
        f'<div style="font-size: 13.5px; line-height: 1.6; color: #334155;">'
        f'Established constituent of the <strong>{target_sector}</strong> benchmark on the National Stock Exchange of India (NSE). Operates under verified Ind AS statutory reporting and broad institutional coverage.'
        f'</div>'
        f'</div>'
        f'<div style="margin-top: 14px; display: flex; gap: 8px; flex-wrap: wrap;">'
        f'<span style="background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; font-size: 11.5px; font-weight: 700; padding: 3px 9px; border-radius: 6px;">✔ Ind AS Audit Tracking</span>'
        f'<span style="background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; font-size: 11.5px; font-weight: 700; padding: 3px 9px; border-radius: 6px;">✔ Nifty 500 Constituent</span>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div class="metrics-3col-grid">'
        f'{card_val}{card_ret}{card_sol}'
        f'</div>'
    )
    st.html(facts_full_html)

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

# --- EXECUTION ENGINE ---
if run_btn:
    with st.status(f"Auditing {target_company_name} with IDEX-7.5SC...", expanded=True) as status:
        st.write("Ingesting verified audited Ind AS financial tables & live market feeds...")
        time.sleep(0.3)
        st.write("Auditing statutory auditor qualifications & related-party schedules...")
        time.sleep(0.3)
        st.write("Testing Sector Receivable Health (DSO, Aging, Provision Coverage)...")
        time.sleep(0.3)
        st.write("Enforcing Promoter Integrity Override (PIO) & PPRM Guardrails...")
        
        try:
            if demo_mode:
                result = get_demo_analysis(target_company_name, target_sector, live_data)
            else:
                pdf_bytes = uploaded_file.read() if uploaded_file else None
                result = analyze_document_with_gemini(
                    company_name=target_company_name,
                    sector=target_sector,
                    api_key=active_api_key,
                    pdf_bytes=pdf_bytes,
                    live_data=live_data,
                    custom_prompt=custom_prompt
                )
            st.session_state["idex_result"] = result
            status.update(label=f"Evaluation Complete for {target_company_name}!", state="complete", expanded=False)
        except Exception as e:
            status.update(label="Evaluation Failed", state="error")
            st.error(f"Analysis Error: {str(e)}")
            with st.expander("Technical Traceback"):
                st.exception(e)

# --- RESULTS DASHBOARD ---
if "idex_result" in st.session_state:
    res = st.session_state["idex_result"]
    st.write("")
    st.markdown("### Institutional Equity Research Scorecard")

    # 1. EXECUTIVE SCORE ROW (Vibrant Gradient KPI Cards)
    final_score = res.get('final_score', 0)
    verdict = res.get("verdict", "").split("—")[0].strip()
    core_score = res.get('core_score', 0)
    total_penalties = res.get('total_penalties', 0)
    total_bonus = res.get('bonuses_breakdown', {}).get('total_bonus_applied', 0)
    position_sizing = res.get("position_sizing", "0%")

    kpi_cards_html = (
        f'<div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 24px;">'
        f'<div style="background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%); border: 1.5px solid #10B981; border-radius: 10px; padding: 18px 20px; box-shadow: 0 2px 5px rgba(16, 185, 129, 0.08);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        f'<span style="font-size: 11.5px; font-weight: 800; letter-spacing: 0.8px; color: #065F46; text-transform: uppercase;">FINAL IDEX SCORE</span>'
        f'<span style="font-size: 18px;">🏆</span>'
        f'</div>'
        f'<div style="font-size: 28px; font-weight: 900; color: #064E3B; font-family: \'JetBrains Mono\', monospace; line-height: 1.1;">'
        f'{final_score:.1f} <span style="font-size: 14px; font-weight: 600; color: #047857;">/ 100</span>'
        f'</div>'
        f'<div style="margin-top: 10px;">'
        f'<span style="background: #059669; color: #FFFFFF; font-size: 11px; font-weight: 800; padding: 3px 9px; border-radius: 9999px; letter-spacing: 0.3px; display: inline-block;">{verdict}</span>'
        f'</div>'
        f'</div>'
        f'<div style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border: 1.5px solid #60A5FA; border-radius: 10px; padding: 18px 20px; box-shadow: 0 2px 5px rgba(59, 130, 246, 0.08);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        f'<span style="font-size: 11.5px; font-weight: 800; letter-spacing: 0.8px; color: #1E40AF; text-transform: uppercase;">CORE QUALITY</span>'
        f'<span style="font-size: 18px;">💎</span>'
        f'</div>'
        f'<div style="font-size: 28px; font-weight: 900; color: #1E3A8A; font-family: \'JetBrains Mono\', monospace; line-height: 1.1;">'
        f'{core_score:.1f} <span style="font-size: 14px; font-weight: 600; color: #2563EB;">/ 100</span>'
        f'</div>'
        f'<div style="margin-top: 10px; font-size: 12px; font-weight: 600; color: #1D4ED8;">'
        f'Pre-penalties baseline'
        f'</div>'
        f'</div>'
        f'<div style="background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%); border: 1.5px solid #F87171; border-radius: 10px; padding: 18px 20px; box-shadow: 0 2px 5px rgba(239, 68, 68, 0.08);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        f'<span style="font-size: 11.5px; font-weight: 800; letter-spacing: 0.8px; color: #991B1B; text-transform: uppercase;">RISK PENALTIES</span>'
        f'<span style="font-size: 18px;">🛡️</span>'
        f'</div>'
        f'<div style="font-size: 28px; font-weight: 900; color: #7F1D1D; font-family: \'JetBrains Mono\', monospace; line-height: 1.1;">'
        f'-{total_penalties:.1f} <span style="font-size: 14px; font-weight: 600; color: #B91C1C;">pts</span>'
        f'</div>'
        f'<div style="margin-top: 10px;">'
        f'<span style="background: #DC2626; color: #FFFFFF; font-size: 11px; font-weight: 800; padding: 3px 9px; border-radius: 9999px;">-7.5% Hard Cap</span>'
        f'</div>'
        f'</div>'
        f'<div style="background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%); border: 1.5px solid #A78BFA; border-radius: 10px; padding: 18px 20px; box-shadow: 0 2px 5px rgba(139, 92, 246, 0.08);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        f'<span style="font-size: 11.5px; font-weight: 800; letter-spacing: 0.8px; color: #5B21B6; text-transform: uppercase;">GROWTH BONUSES</span>'
        f'<span style="font-size: 18px;">🚀</span>'
        f'</div>'
        f'<div style="font-size: 28px; font-weight: 900; color: #4C1D95; font-family: \'JetBrains Mono\', monospace; line-height: 1.1;">'
        f'+{total_bonus:.1f}%'
        f'</div>'
        f'<div style="margin-top: 10px;">'
        f'<span style="background: #7C3AED; color: #FFFFFF; font-size: 11px; font-weight: 800; padding: 3px 9px; border-radius: 9999px;">+10% Max Cap</span>'
        f'</div>'
        f'</div>'
        f'<div style="background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%); border: 1.5px solid #FBBF24; border-radius: 10px; padding: 18px 20px; box-shadow: 0 2px 5px rgba(245, 158, 11, 0.08);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        f'<span style="font-size: 11.5px; font-weight: 800; letter-spacing: 0.8px; color: #92400E; text-transform: uppercase;">PORTFOLIO WEIGHT</span>'
        f'<span style="font-size: 18px;">⚖️</span>'
        f'</div>'
        f'<div style="font-size: 26px; font-weight: 900; color: #78350F; font-family: \'JetBrains Mono\', monospace; line-height: 1.1;">'
        f'{position_sizing}'
        f'</div>'
        f'<div style="margin-top: 10px; font-size: 12px; font-weight: 600; color: #B45309;">'
        f'Risk-Weighted Sizing'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.html(kpi_cards_html)

    st.write("")

    # 2. RADAR & RECEIVABLE HEALTH SPLIT
    split_col1, split_col2 = st.columns([1.3, 1.7])

    with split_col1:
        with st.container(border=True):
            st.markdown("##### 8-Pillar Quality Profile")
            radar_fig = build_radar_chart(res.get("pillars", []))
            st.plotly_chart(radar_fig, width="stretch", alt="8-Pillar Radar Chart")
            
            # Active Tags Row with Vibrant Semantic Pills
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
            ideal_dso = rec.get('sector_ideal_dso', 'N/A')
            rec_sales = rec.get('receivables_to_sales_pct', 'N/A')
            over_90 = rec.get('pct_over_90_days', 'N/A')
            prov_cov = rec.get('provision_coverage_pct', 'N/A')
            verdict_text = rec.get('receivable_verdict', 'Normal')

            rec_cards_html = (
                f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px;">'
                f'<div style="background: #F0FDFA; border: 1px solid #99F6E4; border-radius: 8px; padding: 12px 16px;">'
                f'<div style="font-size: 11.5px; font-weight: 700; color: #0F766E; text-transform: uppercase;">DSO (Days Sales)</div>'
                f'<div style="font-size: 22px; font-weight: 800; color: #115E59; font-family: \'JetBrains Mono\', monospace; margin: 4px 0;">{dso_val} d</div>'
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

    # 3. TABBED IN-DEPTH FORENSIC ANALYSIS
    st.write("")
    tab_pillars, tab_math, tab_peers, tab_thesis, tab_appendices = st.tabs([
        "8-Pillar Scorecard",
        "Risk Deductions & Bonuses",
        "Peer Relative Matrix",
        "Investment Thesis & Final Call",
        "Auditor Evidence & Valuation Math"
    ])

    with tab_pillars:
        st.markdown("#### Comprehensive 8-Pillar Quality Table")
        st.caption("Standardized Dalal Street Evaluation Matrix across Governance, Forensics, Capital Allocation & Durability")
        
        table_rows = []
        for p in res.get("pillars", []):
            p_id = p.get("id", 1)
            p_score = p.get("score", 0)
            p_max = p.get("max_score", 1)
            pct = (p_score / p_max) * 100 if p_max > 0 else 0
            
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
                f'<td style="width: 45%;"><div style="font-size: 14.5px; line-height: 1.6; color: #334155;">{p.get("justification", "")}</div>{rec_html}</td>'
                f'</tr>'
            )
            table_rows.append(row_html)
            
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

    with tab_math:
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            with st.container(border=True):
                st.markdown("##### Deducted Risk Penalties")
                penalties = res.get("penalties_breakdown", [])
                if penalties:
                    pen_html = []
                    for pen in penalties:
                        pen_html.append(
                            f'<div style="background: #FEF2F2; border: 1px solid #FECACA; border-left: 4px solid #DC2626; border-radius: 6px; padding: 12px 16px; margin-bottom: 12px;">'
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
                        '<div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 4px solid #10B981; border-radius: 6px; padding: 14px 18px; color: #064E3B; font-weight: 600; font-size: 14px;">'
                        '✔ Zero statutory forensic risk deductions applied. Clean regulatory profile.'
                        '</div>'
                    )
        
        with m_col2:
            with st.container(border=True):
                st.markdown("##### Applied Growth Bonuses (Max +10%)")
                bb = res.get("bonuses_breakdown", {})
                st.html(
                    f'<div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px;">'
                    f'<div style="background: #F5F3FF; border: 1px solid #DDD6FE; border-left: 4px solid #7C3AED; border-radius: 6px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center;">'
                    f'<div><span style="font-weight: 700; color: #4C1D95; font-size: 14px;">COOL++ PRO Bonus</span><div style="font-size: 12px; color: #6D28D9;">Capital-Light Operating Leverage Outperformance</div></div>'
                    f'<span style="background: #7C3AED; color: #FFFFFF; font-size: 13px; font-weight: 800; padding: 3px 10px; border-radius: 9999px;">+{bb.get("cool_pro_bonus", 0):.1f}%</span>'
                    f'</div>'
                    f'<div style="background: #F5F3FF; border: 1px solid #DDD6FE; border-left: 4px solid #7C3AED; border-radius: 6px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center;">'
                    f'<div><span style="font-weight: 700; color: #4C1D95; font-size: 14px;">Trajectory Bonus</span><div style="font-size: 12px; color: #6D28D9;">Sustained Margin Expansion & FCF Compounding</div></div>'
                    f'<span style="background: #7C3AED; color: #FFFFFF; font-size: 13px; font-weight: 800; padding: 3px 10px; border-radius: 9999px;">+{bb.get("trajectory_bonus", 0):.1f}%</span>'
                    f'</div>'
                    f'<div style="background: #F5F3FF; border: 1px solid #DDD6FE; border-left: 4px solid #7C3AED; border-radius: 6px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center;">'
                    f'<div><span style="font-weight: 700; color: #4C1D95; font-size: 14px;">Resilience Bonus</span><div style="font-size: 12px; color: #6D28D9;">Balance Sheet Solvency & Counter-Cyclical Endurance</div></div>'
                    f'<span style="background: #7C3AED; color: #FFFFFF; font-size: 13px; font-weight: 800; padding: 3px 10px; border-radius: 9999px;">+{bb.get("resilience_bonus", 0):.1f}%</span>'
                    f'</div>'
                    f'</div>'
                    f'<div style="background: #EDE9FE; border: 1.5px solid #A78BFA; border-radius: 8px; padding: 14px 18px; display: flex; justify-content: space-between; align-items: center;">'
                    f'<span style="font-size: 13.5px; font-weight: 800; color: #4C1D95; text-transform: uppercase;">Total Growth Bonus Applied</span>'
                    f'<span style="font-size: 22px; font-weight: 900; color: #4C1D95; font-family: \'JetBrains Mono\', monospace;">+{bb.get("total_bonus_applied", 0):.1f}%</span>'
                    f'</div>'
                )

    with tab_peers:
        with st.container(border=True):
            st.markdown("##### Peer Relative Matrix")
            peers = res.get("peer_matrix", [])
            if peers:
                st.dataframe(peers, width="stretch", alt="Peer Matrix Table")
            
            p_str_col1, p_str_col2 = st.columns(2)
            with p_str_col1:
                st.markdown("##### Key Structural Strengths")
                str_items = "".join([f'<div style="font-size: 13.5px; line-height: 1.55; margin-bottom: 8px; display: flex; align-items: flex-start; gap: 8px;"><span style="color: #059669; font-weight: 800; font-size: 15px;">✔</span> <span style="color: #064E3B;">{s}</span></div>' for s in res.get("strengths", [])])
                st.html(f'<div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 14px 16px;">{str_items}</div>')
            with p_str_col2:
                st.markdown("##### Structural Fragilities & Cautions")
                wk_items = "".join([f'<div style="font-size: 13.5px; line-height: 1.55; margin-bottom: 8px; display: flex; align-items: flex-start; gap: 8px;"><span style="color: #DC2626; font-weight: 800; font-size: 15px;">✖</span> <span style="color: #7F1D1D;">{w}</span></div>' for w in res.get("weaknesses", [])])
                st.html(f'<div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 14px 16px;">{wk_items}</div>')

    with tab_thesis:
        with st.container(border=True):
            st.markdown("##### Final Analyst Recommendation")
            st.html(
                f'<div style="font-size: 20px; font-weight: 800; color: #0F172A; padding: 18px 22px; background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%); border: 1.5px solid #CBD5E1; border-left: 5px solid #059669; border-radius: 0 8px 8px 0; margin: 12px 0 18px 0; line-height: 1.4;">'
                f'<div style="font-size: 11.5px; font-weight: 800; color: #059669; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px;">DALAL STREET POSITION CALL</div>'
                f'{res.get("final_call", "N/A")}'
                f'</div>'
            )
            
            st.divider()
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.markdown("**ESG, Governance & FX Sensitivity:**")
                st.html(f"<div style='background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px 16px; font-size: 13.5px; line-height: 1.6; color: #334155;'>{res.get('fragility_esg_fx_notes', 'No material vulnerabilities observed.')}</div>")
            with t_col2:
                st.markdown("**12–24 Month Catalyst & Forensic Drift Watch:**")
                st.html(f"<div style='background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px 16px; font-size: 13.5px; line-height: 1.6; color: #334155;'>{res.get('drift_optionality_update', 'Monitor upcoming capital deployment.')}</div>")

    with tab_appendices:
        with st.container(border=True):
            st.markdown("##### Appendix A — Forensic Evidence Pack")
            st.caption("Exact quotes, regulatory disclosures, and load-bearing audit excerpts:")
            ev_items = "".join([f'<div style="font-size: 13.5px; line-height: 1.6; color: #1E293B; margin-bottom: 10px; padding: 10px 14px; background: #F8FAFC; border-left: 3px solid #059669; border-radius: 0 6px 6px 0;">{e}</div>' for e in res.get("appendix_a_forensic_evidence", [])])
            st.html(ev_items)
            
            st.divider()
            st.markdown("##### Appendix B — Forensic Calculations & Stress Tests")
            calcs = res.get("appendix_b_calculations", {})
            calc_cards = []
            for k, v in calcs.items():
                calc_cards.append(
                    f'<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px 14px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">'
                    f'<div style="font-size: 11.5px; font-weight: 700; color: #64748B; text-transform: uppercase;">{k.replace("_", " ").title()}</div>'
                    f'<div style="font-size: 14.5px; font-weight: 700; color: #0F172A; margin-top: 4px;">{v}</div>'
                    f'</div>'
                )
            st.html(f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">{"".join(calc_cards)}</div>')

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
        md_text = f"""# StockSage | Institutional Research Memo: {res.get('company_name')}

## Metadata
- **Target Company:** {res.get('company_name')}
- **Sector Benchmark:** {res.get('sector')}
- **Reporting Period:** {res.get('financial_year')}
- **Final Rating:** {res.get('verdict')} (Score: {res.get('final_score')}/100)
- **Position Sizing:** {res.get('position_sizing')}

## Mandatory Guardrail Tag
**{res.get('guardrail_tag')}**
{chr(10).join(['- ' + ev for ev in res.get('guardrail_evidence', [])])}

## Core 8-Pillar Scorecard
{chr(10).join([f"- **Pillar {p.get('id')}: {p.get('name')}**: {p.get('score')}/{p.get('max_score')} ({p.get('justification')})" for p in res.get('pillars', [])])}

## Sector-Sensitive Receivable Layer
- DSO: {rec.get('dso_days')} days (Ideal: {rec.get('sector_ideal_dso')})
- Overdue >90 Days: {rec.get('pct_over_90_days')}
- Receivables / Sales: {rec.get('receivables_to_sales_pct')}
- Verdict: {rec.get('receivable_verdict')}

## Final Call
**{res.get('final_call')}**
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
