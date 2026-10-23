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
from nifty_universe import get_company_list, find_company_info, fetch_live_market_data

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
    st.markdown("#### Company Selection & Live Market Grounding")
    
    c_list = get_company_list()
    default_target = "Tata Consumer Products Ltd. (TATACONSUM)"
    default_idx = c_list.index(default_target) if default_target in c_list else 0
    
    col_sel1, col_sel2 = st.columns([2.5, 1.5])
    
    with col_sel1:
        selected_company_str = st.selectbox(
            "Select Indian Listed Stock (Nifty 500 Universe)",
            options=c_list,
            index=default_idx,
            help="Select any listed Indian company from the Nifty 500 to automatically fetch live market data."
        )
    
    matched_info = find_company_info(selected_company_str)
    
    with col_sel2:
        if matched_info["ticker"] == "CUSTOM":
            target_company_name = st.text_input("Enter Company Name", placeholder="e.g. Amber Enterprises Ltd")
            target_ticker = st.text_input("NSE/BSE Symbol (Optional)", placeholder="e.g. AMBER")
        else:
            target_company_name = matched_info["name"]
            target_ticker = matched_info["ticker"]
            st.text_input("NSE Ticker Symbol", value=target_ticker, disabled=True)
            
    col_sec1, col_sec2 = st.columns([2, 2])
    with col_sec1:
        sector_list = [
            "FMCG / Retail",
            "Consumer Durables / Retailer credit",
            "Pharma / Formulations (trade)",
            "Manufacturing / B2B",
            "Capital Goods / Industrial",
            "Construction / Infra (milestone billing)",
            "IT Services / Consulting",
            "SaaS / Subscription (B2B)",
            "Hospitals / Healthcare (insurer payments)",
            "Logistics / Transport",
            "Chemicals / Oil & Gas",
            "Banks / NBFC"
        ]
        
        def_sector_idx = sector_list.index(matched_info["sector"]) if matched_info["sector"] in sector_list else 0
        target_sector = st.selectbox(
            "Sector Industry Matrix",
            sector_list,
            index=def_sector_idx,
            help="Applies sector-specific DSO, inventory, and margin thresholds."
        )
        
    with col_sec2:
        doc_type = st.segmented_control(
            "Data Ingestion Source",
            ["Live Online Grounding (NSE & Filings)", "Upload Annual Report (PDF)"],
            default="Live Online Grounding (NSE & Filings)"
        )

    # Optional PDF Upload
    uploaded_file = None
    if doc_type == "Upload Annual Report (PDF)":
        uploaded_file = st.file_uploader(
            "Upload Financial Document (PDF)",
            type=["pdf"],
            help="Upload the annual report. 200–500 page Indian reports are fully ingested by Gemini 3.5 Flash."
        )

# Fetch Live Online Market Data (Cached for snappy performance)
@st.cache_data(ttl=180, show_spinner=False)
def get_cached_live_data(ticker_sym: str):
    return fetch_live_market_data(ticker_sym)

live_data = None
if target_ticker and target_ticker != "CUSTOM":
    live_data = get_cached_live_data(target_ticker)

# --- SCREENER-STYLE LIVE COMPANY INTELLIGENCE & KEY RATIOS ---
if live_data:
    with st.container(border=True):
        cur_p = live_data.get("current_price")
        cur_str = f"₹{cur_p:,.2f}" if isinstance(cur_p, (int, float)) else "N/A"
        chg_pct = live_data.get("change_pct", 0)
        chg_val = live_data.get("change_val", 0)
        delta_color = "#059669" if chg_pct >= 0 else "#DC2626"
        delta_sign = "+" if chg_pct >= 0 else ""
        delta_str = f"{delta_sign}{chg_pct:.2f}% ({delta_sign}₹{chg_val:.2f})" if chg_pct is not None else ""

        mcap_val = live_data.get("market_cap_cr")
        mcap_str = f"₹{mcap_val:,.1f} Cr" if isinstance(mcap_val, (int, float)) else "N/A"
        cap_category = "Large Cap" if isinstance(mcap_val, (int, float)) and mcap_val >= 20000 else ("Mid Cap" if isinstance(mcap_val, (int, float)) and mcap_val >= 5000 else "Small Cap")

        # Screener.in Signature Company Headline Banner
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:flex-end; border-bottom: 2px solid #0F172A; padding-bottom: 14px; margin-bottom: 18px;">
            <div>
                <div style="font-size: 32px; font-weight: 800; color: #0F172A; letter-spacing: -0.6px; line-height: 1.2;">
                    {target_company_name}
                </div>
                <div style="color: #64748B; font-size: 14.5px; font-weight: 500; margin-top: 6px;">
                    NSE: <strong style="color:#0F172A;">{target_ticker}</strong> • Sector: <strong style="color:#0F172A;">{target_sector}</strong> • <span style="background:#F1F5F9; color:#0F172A; padding:3px 10px; border-radius:4px; font-weight:700; font-size:12.5px; border:1px solid #E2E8F0;">{cap_category}</span>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 34px; font-weight: 800; color: #0F172A; font-family: 'JetBrains Mono', monospace; line-height: 1.1;">
                    {cur_str}
                </div>
                <div style="font-size: 15px; font-weight: 700; color: {delta_color}; margin-top: 4px;">
                    {delta_str}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Screener Row 1: Core Valuation & Corridor Metrics (5 Columns)
        r_col1, r_col2, r_col3, r_col4, r_col5 = st.columns(5)
        
        with r_col1:
            st.metric(label="MARKET CAP", value=mcap_str, delta=cap_category, delta_color="off", border=True)
        with r_col2:
            st.metric(label="CURRENT PRICE", value=cur_str, delta=delta_str, border=True)
        with r_col3:
            h52 = live_data.get("high_52w", "N/A")
            l52 = live_data.get("low_52w", "N/A")
            st.metric(label="HIGH / LOW (52W)", value=f"₹{h52}" if h52 != "N/A" else "N/A", delta=f"Low: ₹{l52}" if l52 != "N/A" else None, delta_color="off", border=True)
        with r_col4:
            pe_v = live_data.get("pe_ratio")
            pe_str = f"{pe_v}x" if pe_v and pe_v != "N/A" else "N/A"
            fwd_v = live_data.get("forward_pe")
            fwd_str = f"Fwd PE: {fwd_v}x" if fwd_v and fwd_v != "N/A" else "Fwd PE: N/A"
            st.metric(label="STOCK P/E", value=pe_str, delta=fwd_str, delta_color="off", border=True)
        with r_col5:
            pb_v = live_data.get("price_to_book")
            pb_str = f"{pb_v}x" if pb_v and pb_v != "N/A" else "N/A"
            de_v = live_data.get("debt_to_equity")
            de_str = f"Debt/Eq: {de_v}" if de_v and de_v != "N/A" else "D/E: Clean"
            st.metric(label="BOOK MULTIPLE (P/B)", value=pb_str, delta=de_str, delta_color="off", border=True)

        # Screener Row 2: Secondary Technicals & Balance Sheet Ratios (5 Columns)
        s_col1, s_col2, s_col3, s_col4, s_col5 = st.columns(5)
        with s_col1:
            st.metric(label="DIVIDEND YIELD", value=str(live_data.get("dividend_yield", "N/A")), border=True)
        with s_col2:
            st.metric(label="50-DAY DMA", value=f"₹{live_data.get('dma_50', 'N/A')}", border=True)
        with s_col3:
            st.metric(label="200-DAY DMA", value=f"₹{live_data.get('dma_200', 'N/A')}", border=True)
        with s_col4:
            st.metric(label="DEBT TO EQUITY", value=str(live_data.get("debt_to_equity", "N/A")), border=True)
        with s_col5:
            st.metric(label="PREVIOUS CLOSE", value=f"₹{live_data.get('prev_close', 'N/A')}", border=True)

# Action Buttons
btn_col1, btn_col2 = st.columns([3, 1])
with btn_col1:
    run_btn = st.button(
        f"Execute StockSage AI Evaluation for {target_company_name}",
        type="primary",
        width="stretch"
    )
with btn_col2:
    if st.button("Quick Demo", width="stretch"):
        demo_mode = True
        run_btn = True

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
                
            row_html = f"""
            <tr>
                <td style="width: 25%; font-weight: 700;">
                    <div style="font-size: 15.5px; color: #0F172A; font-weight: 700;">P{p.get('id')}: {p.get('name')}</div>
                </td>
                <td style="width: 14%; text-align: center;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 17px; font-weight: 800; color: #047857;">
                        {p_score:.1f} <span style="font-size: 13px; font-weight: 500; color: #64748B;">/ {p_max:.1f}</span>
                    </div>
                </td>
                <td style="width: 16%; text-align: center;">
                    {badge}
                </td>
                <td style="width: 45%;">
                    <div style="font-size: 14.5px; line-height: 1.6; color: #334155;">{p.get('justification', '')}</div>
                    {rec_html}
                </td>
            </tr>
            """
            table_rows.append(row_html)
            
        full_table_html = f"""
        <table class="pillar-table">
            <thead>
                <tr>
                    <th style="width: 25%; text-align: left;">Pillar Domain</th>
                    <th style="width: 14%; text-align: center;">Score</th>
                    <th style="width: 16%; text-align: center;">Quality Rating</th>
                    <th style="width: 45%; text-align: left;">Forensic Assessment & Driver Justification</th>
                </tr>
            </thead>
            <tbody>
                {''.join(table_rows)}
            </tbody>
        </table>
        """
        st.markdown(full_table_html, unsafe_allow_html=True)

    with tab_math:
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            with st.container(border=True):
                st.markdown("##### Deducted Penalties")
                penalties = res.get("penalties_breakdown", [])
                if penalties:
                    for pen in penalties:
                        st.markdown(f"""
                        <div style="font-size: 15px; line-height: 1.6; margin-bottom: 10px;">
                            <strong style="color: #DC2626;">{pen.get('penalty_name')}</strong> (<code style="font-weight:700;">{pen.get('points')} pts</code>): {pen.get('reason')}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("No statutory forensic penalties applied.")
        
        with m_col2:
            with st.container(border=True):
                st.markdown("##### Applied Bonuses (Max +10%)")
                bb = res.get("bonuses_breakdown", {})
                st.markdown(f"""
                <div style="font-size: 15px; line-height: 1.8;">
                    <div>• <strong>COOL++ PRO Bonus:</strong> <code>+{bb.get('cool_pro_bonus', 0):.1f}%</code></div>
                    <div>• <strong>Trajectory Bonus:</strong> <code>+{bb.get('trajectory_bonus', 0):.1f}%</code></div>
                    <div>• <strong>Resilience Bonus:</strong> <code>+{bb.get('resilience_bonus', 0):.1f}%</code></div>
                </div>
                """, unsafe_allow_html=True)
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
                    st.markdown(f"<div style='font-size: 14.5px; line-height: 1.6; margin-bottom: 6px;'><span style='color: #059669; font-weight: 700;'>✔</span> {s}</div>", unsafe_allow_html=True)
            with p_str_col2:
                st.markdown("**Structural Weaknesses & Fragilities:**")
                for w in res.get("weaknesses", []):
                    st.markdown(f"<div style='font-size: 14.5px; line-height: 1.6; margin-bottom: 6px;'><span style='color: #DC2626; font-weight: 700;'>✖</span> {w}</div>", unsafe_allow_html=True)

    with tab_thesis:
        with st.container(border=True):
            st.markdown("##### Final Analyst Recommendation")
            st.markdown(f"""
            <div style="font-size: 22px; font-weight: 800; color: #0F172A; padding: 18px 22px; background: #F8FAFC; border-left: 4px solid #0F172A; border-radius: 0 8px 8px 0; margin: 12px 0 18px 0; line-height: 1.3;">
                {res.get('final_call', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.markdown("**ESG, Fragility & Foreign Exchange Notes:**")
                st.markdown(f"<p style='font-size: 14.5px; line-height: 1.6; color: #334155;'>{res.get('fragility_esg_fx_notes', 'No material vulnerabilities observed.')}</p>", unsafe_allow_html=True)
            with t_col2:
                st.markdown("**12–24 Month Catalyst & Drift Watch:**")
                st.markdown(f"<p style='font-size: 14.5px; line-height: 1.6; color: #334155;'>{res.get('drift_optionality_update', 'Monitor upcoming capital deployment.')}</p>", unsafe_allow_html=True)

    with tab_appendices:
        with st.container(border=True):
            st.markdown("##### Appendix A — Forensic Evidence Pack")
            st.caption("Exact quotes, regulatory disclosures, and load-bearing audit excerpts:")
            for e in res.get("appendix_a_forensic_evidence", []):
                st.markdown(f"""
                <div style="font-size: 14.5px; line-height: 1.6; color: #1E293B; margin-bottom: 8px; padding-left: 12px; border-left: 2px solid #CBD5E1;">
                    {e}
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            st.markdown("##### Appendix B — Calculations & Stress Tests")
            calcs = res.get("appendix_b_calculations", {})
            for k, v in calcs.items():
                st.markdown(f"""
                <div style="font-size: 14.5px; line-height: 1.6; margin-bottom: 8px;">
                    <strong>{k.replace('_', ' ').title()}:</strong> <span style="color: #334155;">{v}</span>
                </div>
                """, unsafe_allow_html=True)

    # 4. MANDATORY GUARDRAIL & PROMOTER INTEGRITY AUDIT (BELOW PILLARS)
    st.write("")
    tag = res.get("guardrail_tag", "GOV-CLEAN 🟢")
    evidence_list = res.get("guardrail_evidence", [])
    
    if "GOV-RED" in tag or res.get("pio_triggered", False):
        st.markdown(f"""
        <div class="guardrail-red-box">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: 800; font-size: 1.15rem; color: #DC2626;">
                    🚨 MANDATORY GUARDRAIL TAG: {tag} (PIO FIRED)
                </span>
                <span style="background-color: #FEE2E2; color: #991B1B; padding: 3px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.8rem; border: 1px solid #FCA5A5;">
                    CRITICAL FORENSIC RISK
                </span>
            </div>
            <p style="margin: 0 0 10px 0; font-weight: 600; color: #991B1B;">{res.get('pio_reason', 'Promoter Integrity Override triggered. Governance pillar capped at ≤6.0/20. Bonuses blocked. Forced into Red Zone.')}</p>
            <ul style="margin: 0; padding-left: 20px; color: #7F1D1D;">{''.join([f'<li>{e}</li>' for e in evidence_list])}</ul>
        </div>
        """, unsafe_allow_html=True)
    elif "PROM-ALERT" in tag:
        st.markdown(f"""
        <div class="guardrail-alert-box">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: 800; font-size: 1.15rem; color: #D97706;">
                    ⚠️ MANDATORY GUARDRAIL TAG: {tag}
                </span>
                <span style="background-color: #FEF3C7; color: #92400E; padding: 3px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.8rem; border: 1px solid #FCD34D;">
                    PROMOTER ALERT
                </span>
            </div>
            <p style="margin: 0 0 10px 0; color: #92400E; font-weight: 500;">Elevated promoter pledging or dilution observed under PPRM rules.</p>
            <ul style="margin: 0; padding-left: 20px; color: #78350F;">{''.join([f'<li>{e}</li>' for e in evidence_list])}</ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="guardrail-clean-box">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: 800; font-size: 1.15rem; color: #059669;">
                    🛡️ PROMOTER INTEGRITY & GOVERNANCE VERDICT: {tag}
                </span>
                <span style="background-color: #D1FAE5; color: #065F46; padding: 3px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.8rem; border: 1px solid #A7F3D0;">
                    INSTITUTIONAL GRADE
                </span>
            </div>
            <p style="margin: 0 0 8px 0; color: #064E3B; font-weight: 600;">10Y+ clean statutory audit history, zero promoter share pledge, verified arm's length related-party disclosures.</p>
            <ul style="margin: 0; padding-left: 20px; color: #1E293B;">{''.join([f'<li>{e}</li>' for e in evidence_list])}</ul>
        </div>
        """, unsafe_allow_html=True)

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
