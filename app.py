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
        background: #F0FDF4;
        border: 1.5px solid #10B981;
        border-radius: 8px;
        padding: 18px 24px;
        color: #0F172A;
        margin-top: 16px;
        margin-bottom: 20px;
    }
    .guardrail-alert-box {
        background: #FFFBEB;
        border: 1.5px solid #F59E0B;
        border-radius: 8px;
        padding: 18px 24px;
        color: #0F172A;
        margin-top: 16px;
        margin-bottom: 20px;
    }
    .guardrail-red-box {
        background: #FEF2F2;
        border: 2px solid #EF4444;
        border-radius: 8px;
        padding: 18px 24px;
        color: #0F172A;
        margin-top: 16px;
        margin-bottom: 20px;
    }

    /* Screener.in Exact Key Ratio Card & Split About Styling */
    .screener-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 22px 24px;
        margin-top: 14px;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    .screener-header-flex {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding-bottom: 16px;
        margin-bottom: 18px;
        border-bottom: 1.5px solid #F1F5F9;
    }
    .screener-title-area {
        display: flex;
        gap: 16px;
        align-items: center;
    }
    .screener-logo-box {
        width: 46px;
        height: 46px;
        border-radius: 8px;
        background: #F8FAFC;
        border: 1.5px solid #E2E8F0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 18px;
        color: #059669;
        font-family: 'Inter', sans-serif;
    }
    .screener-company-name {
        font-size: 28px;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }
    .screener-price-inline {
        font-size: 22px;
        font-weight: 800;
        color: #0F172A;
        font-family: 'JetBrains Mono', monospace;
        margin-left: 10px;
    }
    .screener-delta-pill {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 700;
        margin-left: 8px;
    }
    .screener-links-bar {
        display: flex;
        gap: 14px;
        align-items: center;
        margin-top: 6px;
        font-size: 13.5px;
        color: #64748B;
        font-weight: 500;
    }
    .screener-links-bar a {
        color: #2563EB;
        text-decoration: none;
        font-weight: 600;
    }
    .screener-links-bar a:hover {
        text-decoration: underline;
    }
    .screener-grid-split {
        display: flex;
        gap: 24px;
        align-items: flex-start;
    }
    .screener-table-container {
        flex: 2.15;
    }
    .screener-about-container {
        flex: 1.0;
        padding-left: 20px;
        border-left: 1px solid #F1F5F9;
    }
    .screener-ratio-table {
        width: 100%;
        border-collapse: collapse;
    }
    .screener-ratio-table tr {
        border-bottom: 1px solid #F1F5F9;
    }
    .screener-ratio-table tr:hover {
        background-color: #F8FAFC;
    }
    .screener-ratio-table td.r-name {
        font-size: 13.5px;
        font-weight: 500;
        color: #64748B;
        padding: 9px 4px 9px 0;
        text-align: left;
        white-space: nowrap;
        width: 17%;
    }
    .screener-ratio-table td.r-val {
        font-size: 14px;
        font-weight: 700;
        color: #0F172A;
        font-family: 'JetBrains Mono', monospace;
        padding: 9px 18px 9px 4px;
        text-align: right;
        white-space: nowrap;
        width: 16%;
    }
    .screener-table-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 14px;
        padding-top: 8px;
    }
    .screener-footer-input {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 4px;
        padding: 6px 12px;
        font-size: 13px;
        color: #475569;
        width: 200px;
        outline: none;
    }
    .screener-footer-btn {
        background: transparent;
        border: none;
        color: #2563EB;
        font-size: 12.5px;
        font-weight: 700;
        cursor: pointer;
        letter-spacing: 0.3px;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### StockSage")
    st.caption("Dalal Street Equity Intelligence • Ashu Elite Edition")
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

st.title("StockSage")
st.caption("Institutional Equity Research & Forensic Intelligence Terminal • Ashu Elite Edition")

# --- INTAKE CONSOLE ---
with st.container(border=True):
    st.markdown("#### Company Search")
    
    c_list = get_company_list()
    
    col_sel1, col_sel2 = st.columns([2.5, 1.5])
    
    with col_sel1:
        selected_company_str = st.selectbox(
            "Company",
            options=c_list,
            index=None,
            placeholder="Search by company name or symbol (e.g. Reliance, HDFC Bank, Infosys, Dixon)...",
            help="Select any listed Indian company from the Nifty 500 to pull live financial data."
        )
    
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
    st.html(
        f'<div style="background: #FFFFFF; border: 1.5px dashed #CBD5E1; border-radius: 12px; padding: 44px 28px; text-align: center; margin-top: 18px; margin-bottom: 24px;">'
        f'<div style="font-size: 38px; margin-bottom: 12px;">📈</div>'
        f'<div style="font-size: 22px; font-weight: 800; color: #0F172A; letter-spacing: -0.4px; margin-bottom: 8px;">Search or Select a Listed Indian Stock</div>'
        f'<div style="font-size: 15px; color: #64748B; max-width: 620px; margin: 0 auto 20px auto; line-height: 1.6;">Select any company from the 501 Nifty 500 universe above (or enter a custom stock) to inspect real-time NSE valuation metrics, 52-week price channels, and launch the 8-pillar institutional quality audit.</div>'
        f'<div style="display: flex; justify-content: center; gap: 10px; flex-wrap: wrap;">'
        f'<span style="background: #F0FDF4; color: #047857; border: 1px solid #A7F3D0; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;">⚡ Real-time Market Cap & P/E</span>'
        f'<span style="background: #F0FDF4; color: #047857; border: 1px solid #A7F3D0; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;">🏛️ Screener 8-Pillar Scorecard</span>'
        f'<span style="background: #F0FDF4; color: #047857; border: 1px solid #A7F3D0; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;">🛡️ Promoter Integrity & Governance</span>'
        f'<span style="background: #F0FDF4; color: #047857; border: 1px solid #A7F3D0; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;">📊 Cash Flow & Forensic Checks</span>'
        f'</div></div>'
    )

# --- SCREENER-STYLE LIVE COMPANY INTELLIGENCE & 27 KEY RATIOS ---
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
    
    logo_initials = "".join([w[0] for w in target_company_name.split()[:2]]).upper() if target_company_name else "SS"

    # 9 rows × 3 columns of Screener metrics matching exact Screener.in presentation
    rows_data = [
        [("Market Cap", sm.get("market_cap", "N/A")), ("Current Price", sm.get("current_price", cur_str)), ("High / Low", sm.get("high_low", "N/A"))],
        [("Stock P/E", sm.get("stock_pe", "N/A")), ("Book Value", sm.get("book_value", "N/A")), ("Dividend Yield", sm.get("dividend_yield", "N/A"))],
        [("ROCE", sm.get("roce", "N/A")), ("ROE", sm.get("roe", "N/A")), ("Face Value", sm.get("face_value", "N/A"))],
        [("Graham Number", sm.get("graham_number", "N/A")), ("Current ratio", sm.get("current_ratio", "N/A")), ("Debt to equity", sm.get("debt_to_equity", "N/A"))],
        [("Market Cap to Sales", sm.get("market_cap_to_sales", "N/A")), ("Asset Turnover", sm.get("asset_turnover", "N/A")), ("Intrinsic Value", sm.get("intrinsic_value", "N/A"))],
        [("Promoter holding", sm.get("promoter_holding", "N/A")), ("Int Coverage", sm.get("int_coverage", "N/A")), ("OPM", sm.get("opm", "N/A"))],
        [("Debt", sm.get("debt", "N/A")), ("Sales growth 5Years", sm.get("sales_growth_5yr", "N/A")), ("ROIC", sm.get("roic", "N/A"))],
        [("NPM last year", sm.get("npm_last_year", "N/A")), ("CMP / FCF", sm.get("cmp_to_fcf", "N/A")), ("Earnings yield", sm.get("earnings_yield", "N/A"))],
        [("Free Cash Flow 5Yrs", sm.get("free_cash_flow_5yr", "N/A")), ("PEG Ratio", sm.get("peg_ratio", "N/A")), ("EVEBITDA", sm.get("evebitda", "N/A"))]
    ]

    table_rows_html = []
    for r in rows_data:
        cells = ""
        for name, val in r:
            cells += f'<td class="r-name">{name}</td><td class="r-val">{val}</td>'
        table_rows_html.append(f'<tr>{cells}</tr>')

    screener_full_html = (
        f'<div class="screener-card">'
        f'<div class="screener-header-flex">'
        f'<div class="screener-title-area">'
        f'<div class="screener-logo-box">{logo_initials}</div>'
        f'<div>'
        f'<div style="display: flex; align-items: baseline; flex-wrap: wrap;">'
        f'<span class="screener-company-name">{target_company_name}</span>'
        f'<span class="screener-price-inline">• {cur_str}</span>'
        f'<span class="screener-delta-pill" style="color: {delta_fg}; background: {delta_bg};">{delta_str}</span>'
        f'<span style="color: #64748B; font-size: 12px; margin-left: 8px;">{price_date}</span>'
        f'</div>'
        f'<div class="screener-links-bar">'
        f'<span>🔗 <a href="{website_url}" target="_blank">{website_display}</a></span>'
        f'<span>• ↗ BSE: {live_data.get("bse_code", target_ticker)}</span>'
        f'<span>• ↗ NSE: {target_ticker}</span>'
        f'<span>• <span style="background: #F1F5F9; color: #334155; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 12px;">{target_sector}</span></span>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div style="display: flex; gap: 10px;">'
        f'<button style="background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; font-size: 13px; font-weight: 700; padding: 7px 14px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; gap: 6px;">📥 EXPORT TO EXCEL</button>'
        f'<button style="background: #5B21B6; border: none; color: #FFFFFF; font-size: 13px; font-weight: 700; padding: 7px 16px; border-radius: 6px; cursor: pointer;">+ FOLLOW ▾</button>'
        f'</div>'
        f'</div>'
        f'<div class="screener-grid-split">'
        f'<div class="screener-table-container">'
        f'<table class="screener-ratio-table">'
        f'<tbody>{"".join(table_rows_html)}</tbody>'
        f'</table>'
        f'<div class="screener-table-footer">'
        f'<div style="display: flex; align-items: center; gap: 12px;">'
        f'<span style="font-size: 13px; font-weight: 600; color: #64748B;">Add ratio to table</span>'
        f'<input class="screener-footer-input" placeholder="eg. Promoter holding" />'
        f'</div>'
        f'<button class="screener-footer-btn">✏️ EDIT RATIOS</button>'
        f'</div>'
        f'</div>'
        f'<div class="screener-about-container">'
        f'<div style="font-size: 12.5px; font-weight: 800; color: #0F172A; letter-spacing: 0.6px; margin-bottom: 8px;">ABOUT</div>'
        f'<div style="font-size: 13px; line-height: 1.6; color: #334155; margin-bottom: 18px; max-height: 185px; overflow-y: auto; padding-right: 4px;">{about_text}</div>'
        f'<div style="font-size: 12.5px; font-weight: 800; color: #0F172A; letter-spacing: 0.6px; margin-bottom: 6px;">KEY POINTS</div>'
        f'<div style="font-size: 13px; line-height: 1.55; color: #334155;">'
        f'<strong>Market Position:</strong> The company is an established flagship {target_sector} constituent listed on NSE/BSE with significant institutional coverage, scale distribution moats, and Ind AS audit compliance.'
        f'</div>'
        f'<div style="margin-top: 10px;"><a style="color: #059669; font-size: 12px; font-weight: 700; text-decoration: none; cursor: pointer;">READ MORE ›</a></div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.html(screener_full_html)

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
        fillcolor='rgba(5, 150, 105, 0.12)',
        line=dict(color='#059669', width=3),
        marker=dict(size=7, color='#059669'),
        name='% of Max Score'
    ))

    fig.update_layout(
        polar=dict(
            bgcolor='rgba(240, 253, 244, 0.4)',
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%",
                gridcolor='#D1FAE5',
                linecolor='#A7F3D0',
                tickfont=dict(color='#047857', size=11, family='Inter', weight=500)
            ),
            angularaxis=dict(
                gridcolor='#E2E8F0',
                linecolor='#CBD5E1',
                tickfont=dict(color='#0F172A', size=12.5, family='Inter', weight=700)
            )
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=50, r=50, t=30, b=30),
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

    # 1. EXECUTIVE SCORE ROW (KPI CARDS)
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
    
    with kpi_col1:
        st.metric(
            label="FINAL SCORE",
            value=f"{res.get('final_score', 0):.1f} / 100",
            delta=res.get("verdict", "").split("—")[0].strip(),
            border=True
        )
    with kpi_col2:
        st.metric(
            label="CORE QUALITY SCORE",
            value=f"{res.get('core_score', 0):.1f}",
            delta_description="Pre-penalties (100 Max)",
            border=True
        )
    with kpi_col3:
        st.metric(
            label="RISK PENALTIES",
            value=f"{res.get('total_penalties', 0):.1f} pts",
            delta="-7.5% Cap",
            delta_color="inverse",
            border=True
        )
    with kpi_col4:
        st.metric(
            label="GROWTH BONUSES",
            value=f"+{res.get('bonuses_breakdown', {}).get('total_bonus_applied', 0):.1f}%",
            delta="+10% Cap",
            border=True
        )
    with kpi_col5:
        st.metric(
            label="ALLOCATION SIZING",
            value=res.get("position_sizing", "0%"),
            delta_description="Portfolio Allocation",
            border=True
        )

    st.write("")

    # 2. RADAR & RECEIVABLE HEALTH SPLIT
    split_col1, split_col2 = st.columns([1.3, 1.7])

    with split_col1:
        with st.container(border=True):
            st.markdown("##### 8-Pillar Quality Profile")
            radar_fig = build_radar_chart(res.get("pillars", []))
            st.plotly_chart(radar_fig, width="stretch", alt="8-Pillar Radar Chart")
            
            # Active Tags Row
            st.caption("Active Forensic Tags:")
            tag_badges = " ".join([f":gray-badge[{t}]" for t in res.get("tags_applied", [])])
            st.markdown(tag_badges)

    with split_col2:
        with st.container(border=True):
            st.markdown("##### Sector Receivable Health Layer")
            st.caption("Forensic Cash Conversion & Liquidity Benchmarking")
            
            rec = res.get("receivable_health_metrics", {})
            
            r_row1, r_row2 = st.columns(2)
            with r_row1:
                st.metric("DSO (Days Sales Outstanding)", f"{rec.get('dso_days', 'N/A')} d", f"Sector Ideal: {rec.get('sector_ideal_dso', 'N/A')}", border=True)
                st.metric("Receivables / Annual Sales", rec.get("receivables_to_sales_pct", "N/A"), border=True)
            with r_row2:
                st.metric(">90 Days Delinquency", rec.get("pct_over_90_days", "N/A"), help="Delinquency threshold", border=True)
                st.metric("Provision Coverage", rec.get("provision_coverage_pct", "N/A"), border=True)
            
            st.info(f"**Assessment:** {rec.get('receivable_verdict', 'Normal')}")

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
            p_score = p.get("score", 0)
            p_max = p.get("max_score", 1)
            pct = (p_score / p_max) * 100
            
            # Screener-style Quality Rating Badge
            if pct >= 85:
                badge = f'<span style="background:#ECFDF5; color:#047857; border:1px solid #A7F3D0; padding:4px 10px; border-radius:9999px; font-weight:700; font-size:12.5px; display:inline-block;">{pct:.0f}% • Pristine</span>'
            elif pct >= 70:
                badge = f'<span style="background:#F0FDF4; color:#059669; border:1px solid #BBF7D0; padding:4px 10px; border-radius:9999px; font-weight:700; font-size:12.5px; display:inline-block;">{pct:.0f}% • Strong</span>'
            elif pct >= 50:
                badge = f'<span style="background:#FFFBEB; color:#D97706; border:1px solid #FDE68A; padding:4px 10px; border-radius:9999px; font-weight:700; font-size:12.5px; display:inline-block;">{pct:.0f}% • Moderate</span>'
            else:
                badge = f'<span style="background:#FEF2F2; color:#DC2626; border:1px solid #FECACA; padding:4px 10px; border-radius:9999px; font-weight:700; font-size:12.5px; display:inline-block;">{pct:.0f}% • Fragile</span>'
                
            rec_html = ""
            if "receivable_subscore" in p:
                rec_html = f'<div style="margin-top: 8px; background: #ECFDF5; border-left: 3px solid #059669; padding: 4px 10px; font-size: 13px; font-weight: 600; color: #065F46; border-radius: 0 4px 4px 0;">Receivable Health Subscore: {p["receivable_subscore"]}</div>'
                
            row_html = (
                f'<tr>'
                f'<td style="width: 25%; font-weight: 700;"><div style="font-size: 15.5px; color: #0F172A; font-weight: 700;">P{p.get("id")}: {p.get("name")}</div></td>'
                f'<td style="width: 14%; text-align: center;"><div style="font-family: \'JetBrains Mono\', monospace; font-size: 17px; font-weight: 800; color: #047857;">{p_score:.1f} <span style="font-size: 13px; font-weight: 500; color: #64748B;">/ {p_max:.1f}</span></div></td>'
                f'<td style="width: 16%; text-align: center;">{badge}</td>'
                f'<td style="width: 45%;"><div style="font-size: 14.5px; line-height: 1.6; color: #334155;">{p.get("justification", "")}</div>{rec_html}</td>'
                f'</tr>'
            )
            table_rows.append(row_html)
            
        full_table_html = (
            f'<table class="pillar-table">'
            f'<thead><tr>'
            f'<th style="width: 25%; text-align: left;">Pillar Domain</th>'
            f'<th style="width: 14%; text-align: center;">Score</th>'
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
                st.markdown("##### Deducted Penalties")
                penalties = res.get("penalties_breakdown", [])
                if penalties:
                    for pen in penalties:
                        st.html(
                            f'<div style="font-size: 15px; line-height: 1.6; margin-bottom: 10px;">'
                            f'<strong style="color: #DC2626;">{pen.get("penalty_name")}</strong> (<code style="font-weight:700;">{pen.get("points")} pts</code>): {pen.get("reason")}'
                            f'</div>'
                        )
                else:
                    st.success("No statutory forensic penalties applied.")
        
        with m_col2:
            with st.container(border=True):
                st.markdown("##### Applied Bonuses (Max +10%)")
                bb = res.get("bonuses_breakdown", {})
                st.html(
                    f'<div style="font-size: 15px; line-height: 1.8;">'
                    f'<div>• <strong>COOL++ PRO Bonus:</strong> <code>+{bb.get("cool_pro_bonus", 0):.1f}%</code></div>'
                    f'<div>• <strong>Trajectory Bonus:</strong> <code>+{bb.get("trajectory_bonus", 0):.1f}%</code></div>'
                    f'<div>• <strong>Resilience Bonus:</strong> <code>+{bb.get("resilience_bonus", 0):.1f}%</code></div>'
                    f'</div>'
                )
                st.divider()
                st.metric("Total Bonus Impact", f"+{bb.get('total_bonus_applied', 0):.1f}%")

    with tab_peers:
        with st.container(border=True):
            st.markdown("##### Peer Relative Matrix")
            peers = res.get("peer_matrix", [])
            if peers:
                st.dataframe(peers, width="stretch", alt="Peer Matrix Table")
            
            p_str_col1, p_str_col2 = st.columns(2)
            with p_str_col1:
                st.markdown("**Key Structural Strengths:**")
                for s in res.get("strengths", []):
                    st.html(f"<div style='font-size: 14.5px; line-height: 1.6; margin-bottom: 6px;'><span style='color: #059669; font-weight: 700;'>✔</span> {s}</div>")
            with p_str_col2:
                st.markdown("**Structural Weaknesses & Fragilities:**")
                for w in res.get("weaknesses", []):
                    st.html(f"<div style='font-size: 14.5px; line-height: 1.6; margin-bottom: 6px;'><span style='color: #DC2626; font-weight: 700;'>✖</span> {w}</div>")

    with tab_thesis:
        with st.container(border=True):
            st.markdown("##### Final Analyst Recommendation")
            st.html(
                f'<div style="font-size: 22px; font-weight: 800; color: #0F172A; padding: 18px 22px; background: #F8FAFC; border-left: 4px solid #0F172A; border-radius: 0 8px 8px 0; margin: 12px 0 18px 0; line-height: 1.3;">'
                f'{res.get("final_call", "N/A")}'
                f'</div>'
            )
            
            st.divider()
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.markdown("**ESG, Fragility & Foreign Exchange Notes:**")
                st.html(f"<p style='font-size: 14.5px; line-height: 1.6; color: #334155;'>{res.get('fragility_esg_fx_notes', 'No material vulnerabilities observed.')}</p>")
            with t_col2:
                st.markdown("**12–24 Month Catalyst & Drift Watch:**")
                st.html(f"<p style='font-size: 14.5px; line-height: 1.6; color: #334155;'>{res.get('drift_optionality_update', 'Monitor upcoming capital deployment.')}</p>")

    with tab_appendices:
        with st.container(border=True):
            st.markdown("##### Appendix A — Forensic Evidence Pack")
            st.caption("Exact quotes, regulatory disclosures, and load-bearing audit excerpts:")
            for e in res.get("appendix_a_forensic_evidence", []):
                st.html(
                    f'<div style="font-size: 14.5px; line-height: 1.6; color: #1E293B; margin-bottom: 8px; padding-left: 12px; border-left: 2px solid #CBD5E1;">'
                    f'{e}'
                    f'</div>'
                )
            
            st.divider()
            st.markdown("##### Appendix B — Calculations & Stress Tests")
            calcs = res.get("appendix_b_calculations", {})
            for k, v in calcs.items():
                st.html(
                    f'<div style="font-size: 14.5px; line-height: 1.6; margin-bottom: 8px;">'
                    f'<strong>{k.replace("_", " ").title()}:</strong> <span style="color: #334155;">{v}</span>'
                    f'</div>'
                )

    # 4. MANDATORY GUARDRAIL & PROMOTER INTEGRITY AUDIT (BELOW PILLARS)
    st.write("")
    tag = res.get("guardrail_tag", "GOV-CLEAN 🟢")
    evidence_list = res.get("guardrail_evidence", [])
    
    if "GOV-RED" in tag or res.get("pio_triggered", False):
        st.html(
            f'<div class="guardrail-red-box">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
            f'<span style="font-weight: 800; font-size: 1.15rem; color: #DC2626;">🚨 MANDATORY GUARDRAIL TAG: {tag} (PIO FIRED)</span>'
            f'<span style="background-color: #FEE2E2; color: #991B1B; padding: 3px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.8rem; border: 1px solid #FCA5A5;">CRITICAL FORENSIC RISK</span>'
            f'</div>'
            f'<p style="margin: 0 0 10px 0; font-weight: 600; color: #991B1B;">{res.get("pio_reason", "Promoter Integrity Override triggered. Governance pillar capped at ≤6.0/20. Bonuses blocked. Forced into Red Zone.")}</p>'
            f'<ul style="margin: 0; padding-left: 20px; color: #7F1D1D;">{"".join([f"<li>{e}</li>" for e in evidence_list])}</ul>'
            f'</div>'
        )
    elif "PROM-ALERT" in tag:
        st.html(
            f'<div class="guardrail-alert-box">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
            f'<span style="font-weight: 800; font-size: 1.15rem; color: #D97706;">⚠️ MANDATORY GUARDRAIL TAG: {tag}</span>'
            f'<span style="background-color: #FEF3C7; color: #92400E; padding: 3px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.8rem; border: 1px solid #FCD34D;">PROMOTER ALERT</span>'
            f'</div>'
            f'<p style="margin: 0 0 10px 0; color: #92400E; font-weight: 500;">Elevated promoter pledging or dilution observed under PPRM rules.</p>'
            f'<ul style="margin: 0; padding-left: 20px; color: #78350F;">{"".join([f"<li>{e}</li>" for e in evidence_list])}</ul>'
            f'</div>'
        )
    else:
        st.html(
            f'<div class="guardrail-clean-box">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
            f'<span style="font-weight: 800; font-size: 1.15rem; color: #059669;">🛡️ PROMOTER INTEGRITY & GOVERNANCE VERDICT: {tag}</span>'
            f'<span style="background-color: #D1FAE5; color: #065F46; padding: 3px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.8rem; border: 1px solid #A7F3D0;">INSTITUTIONAL GRADE</span>'
            f'</div>'
            f'<p style="margin: 0 0 8px 0; color: #064E3B; font-weight: 600;">10Y+ clean statutory audit history, zero promoter share pledge, verified arm\'s length related-party disclosures.</p>'
            f'<ul style="margin: 0; padding-left: 20px; color: #1E293B;">{"".join([f"<li>{e}</li>" for e in evidence_list])}</ul>'
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
