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
    page_title="IDEX-7.5SC Terminal | Ashu Elite Edition",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Ultra-Clean Institutional CSS
st.markdown("""
<style>
    /* Clean font & metrics */
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', -apple-system, BlinkMacSystemFont, monospace;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Guardrail Banners */
    .guardrail-clean-box {
        background: rgba(16, 185, 129, 0.08);
        border: 1.5px solid #10B981;
        border-radius: 8px;
        padding: 16px 20px;
        color: #E2E8F0;
        margin-bottom: 18px;
    }
    .guardrail-alert-box {
        background: rgba(245, 158, 11, 0.08);
        border: 1.5px solid #F59E0B;
        border-radius: 8px;
        padding: 16px 20px;
        color: #E2E8F0;
        margin-bottom: 18px;
    }
    .guardrail-red-box {
        background: rgba(239, 68, 68, 0.12);
        border: 2px solid #EF4444;
        border-radius: 8px;
        padding: 16px 20px;
        color: #FEE2E2;
        margin-bottom: 18px;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### IDEX-7.5SC Terminal")
    st.caption("Ashu Elite Edition • Dalal Street Forensic Engine")
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

st.title("IDEX-7.5SC Terminal")
st.caption("Ashu Elite Edition • Institutional Financial & Forensic Research • Dalal Street Universe")

# --- INTAKE CONSOLE ---
with st.container(border=True):
    st.markdown("#### Company Selection & Live Market Ingestion")
    
    c_list = get_company_list()
    default_idx = 11  # Tata Consumer Products Ltd
    
    col_sel1, col_sel2 = st.columns([2.5, 1.5])
    
    with col_sel1:
        selected_company_str = st.selectbox(
            "Select Listed Indian Company (Nifty 50 / Next 50)",
            options=c_list,
            index=default_idx,
            help="Select any listed Indian company to automatically fetch live market data."
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
            "Sector Benchmark Matrix",
            sector_list,
            index=def_sector_idx,
            help="Applies sector-specific DSO, inventory, and margin thresholds."
        )
        
    with col_sec2:
        doc_type = st.segmented_control(
            "Evaluation Source",
            ["Online Grounding + Knowledge Base", "Upload Annual Report PDF"],
            default="Online Grounding + Knowledge Base"
        )

    # Optional PDF Upload
    uploaded_file = None
    if doc_type == "Upload Annual Report PDF":
        uploaded_file = st.file_uploader(
            "Upload Financial Document (PDF)",
            type=["pdf"],
            help="Upload the annual report. 200–500 page Indian reports are fully ingested by Gemini 3.5 Flash."
        )

# Fetch Live Online Market Data
live_data = None
if target_ticker and target_ticker != "CUSTOM":
    live_data = fetch_live_market_data(target_ticker)

# Action Buttons
btn_col1, btn_col2 = st.columns([3, 1])
with btn_col1:
    run_btn = st.button(
        f"Execute IDEX-7.5SC AI Evaluation for {target_company_name}",
        type="primary",
        width="stretch"
    )
with btn_col2:
    if st.button("Quick Demo", width="stretch"):
        demo_mode = True
        run_btn = True

# Helper to build Plotly 8-Pillar Radar Chart
def build_dark_radar_chart(pillars):
    names = [f"P{p['id']}: {p['name']}" for p in pillars]
    pct_scores = [(p["score"] / p["max_score"]) * 100 for p in pillars]
    
    names_closed = names + [names[0]]
    pct_closed = pct_scores + [pct_scores[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=pct_closed,
        theta=names_closed,
        fill='toself',
        fillcolor='rgba(56, 189, 248, 0.20)',
        line=dict(color='#38BDF8', width=2.5),
        marker=dict(size=6, color='#38BDF8'),
        name='% of Max Score'
    ))

    fig.update_layout(
        polar=dict(
            bgcolor='rgba(15, 23, 42, 0.6)',
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%",
                gridcolor='#334155',
                linecolor='#334155',
                tickfont=dict(color='#94A3B8', size=10)
            ),
            angularaxis=dict(
                gridcolor='#334155',
                linecolor='#334155',
                tickfont=dict(color='#E2E8F0', size=11, family='Inter')
            )
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=45, r=45, t=25, b=25),
        height=370
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

    # 1. MANDATORY GUARDRAIL TAG CALLOUT
    tag = res.get("guardrail_tag", "GOV-CLEAN 🟢")
    evidence_list = res.get("guardrail_evidence", [])
    
    if "GOV-RED" in tag or res.get("pio_triggered", False):
        st.markdown(f"""
        <div class="guardrail-red-box">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: 800; font-size: 1.15rem; color: #F87171;">
                    🚨 MANDATORY GUARDRAIL TAG: {tag} (PIO FIRED)
                </span>
                <span style="background-color: #7F1D1D; color: #FCA5A5; padding: 3px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.8rem;">
                    CRITICAL FORENSIC RISK
                </span>
            </div>
            <p style="margin: 0 0 10px 0; font-weight: 600;">{res.get('pio_reason', 'Promoter Integrity Override triggered. Governance pillar capped at ≤6.0/20. Bonuses blocked. Forced into Red Zone.')}</p>
            <ul style="margin: 0; padding-left: 20px;">{''.join([f'<li>{e}</li>' for e in evidence_list])}</ul>
        </div>
        """, unsafe_allow_html=True)
    elif "PROM-ALERT" in tag:
        st.markdown(f"""
        <div class="guardrail-alert-box">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: 800; font-size: 1.15rem; color: #FBBF24;">
                    ⚠️ MANDATORY GUARDRAIL TAG: {tag}
                </span>
                <span style="background-color: #78350F; color: #FDE68A; padding: 3px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.8rem;">
                    PROMOTER ALERT
                </span>
            </div>
            <p style="margin: 0 0 10px 0;">Elevated promoter pledging or dilution observed under PPRM rules.</p>
            <ul style="margin: 0; padding-left: 20px;">{''.join([f'<li>{e}</li>' for e in evidence_list])}</ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="guardrail-clean-box">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: 800; font-size: 1.15rem; color: #34D399;">
                    🛡️ MANDATORY GUARDRAIL TAG: {tag}
                </span>
                <span style="background-color: #064E3B; color: #A7F3D0; padding: 3px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.8rem;">
                    INSTITUTIONAL GRADE
                </span>
            </div>
            <p style="margin: 0 0 8px 0; color: #CBD5E1;">10Y+ clean auditor records, zero promoter share pledging, fully aligned minority shareholder governance.</p>
            <ul style="margin: 0; padding-left: 20px; color: #94A3B8;">{''.join([f'<li>{e}</li>' for e in evidence_list])}</ul>
        </div>
        """, unsafe_allow_html=True)

    # 2. EXECUTIVE SCORE ROW (KPI CARDS)
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
            label="CORE SCORE",
            value=f"{res.get('core_score', 0):.1f}",
            delta_description="Pre-penalties (100 Max)",
            border=True
        )
    with kpi_col3:
        st.metric(
            label="PENALTIES",
            value=f"{res.get('total_penalties', 0):.1f} pts",
            delta="-7.5% Cap",
            delta_color="inverse",
            border=True
        )
    with kpi_col4:
        st.metric(
            label="BONUS APPLIED",
            value=f"+{res.get('bonuses_breakdown', {}).get('total_bonus_applied', 0):.1f}%",
            delta="+10% Cap",
            border=True
        )
    with kpi_col5:
        st.metric(
            label="POSITION SIZING",
            value=res.get("position_sizing", "0%"),
            delta_description="Portfolio Allocation",
            border=True
        )

    st.write("")

    # 3. RADAR & RECEIVABLE HEALTH SPLIT
    split_col1, split_col2 = st.columns([1.3, 1.7])

    with split_col1:
        with st.container(border=True):
            st.markdown("##### 8-Pillar Quality Profile")
            radar_fig = build_dark_radar_chart(res.get("pillars", []))
            st.plotly_chart(radar_fig, width="stretch", alt="8-Pillar Radar Chart")
            
            # Active Tags Row
            st.caption("Active Forensic Tags:")
            tag_badges = " ".join([f":blue-badge[{t}]" for t in res.get("tags_applied", [])])
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

    # 4. TABBED IN-DEPTH FORENSIC ANALYSIS
    st.write("")
    tab_pillars, tab_math, tab_peers, tab_thesis, tab_appendices = st.tabs([
        "8-Pillar Scorecard",
        "Penalties & Bonuses",
        "Peer Comparison",
        "Final Call & Thesis",
        "Forensic Evidence & Calculations"
    ])

    with tab_pillars:
        st.markdown("#### Full 8-Pillar Evaluation Breakdown")
        
        p_cols = st.columns(2)
        for i, p in enumerate(res.get("pillars", [])):
            col = p_cols[i % 2]
            with col:
                with st.container(border=True):
                    p_score = p.get("score", 0)
                    p_max = p.get("max_score", 1)
                    pct = (p_score / p_max) * 100
                    
                    st.markdown(f"**Pillar {p.get('id')}: {p.get('name')}**")
                    st.progress(pct / 100, text=f"**{p_score:.1f} / {p_max:.1f} pts** ({pct:.0f}%)")
                    st.caption(p.get("justification", ""))
                    if "receivable_subscore" in p:
                        st.markdown(f":blue-badge[Receivable Subscore: {p['receivable_subscore']}]")

    with tab_math:
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            with st.container(border=True):
                st.markdown("##### Deducted Penalties")
                penalties = res.get("penalties_breakdown", [])
                if penalties:
                    for pen in penalties:
                        st.markdown(f"- :red[**{pen.get('penalty_name')}**] (`{pen.get('points')} pts`): {pen.get('reason')}")
                else:
                    st.success("No statutory forensic penalties applied.")
        
        with m_col2:
            with st.container(border=True):
                st.markdown("##### Applied Bonuses (Max +10%)")
                bb = res.get("bonuses_breakdown", {})
                st.markdown(f"- **COOL++ PRO Bonus:** `+{bb.get('cool_pro_bonus', 0):.1f}%`")
                st.markdown(f"- **Trajectory Bonus:** `+{bb.get('trajectory_bonus', 0):.1f}%`")
                st.markdown(f"- **Resilience Bonus:** `+{bb.get('resilience_bonus', 0):.1f}%`")
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
                    st.markdown(f":green[✔] {s}")
            with p_str_col2:
                st.markdown("**Structural Weaknesses & Fragilities:**")
                for w in res.get("weaknesses", []):
                    st.markdown(f":red[✖] {w}")

    with tab_thesis:
        with st.container(border=True):
            st.markdown("##### Final Analyst Recommendation")
            st.markdown(f"### {res.get('final_call', 'N/A')}")
            
            st.divider()
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.markdown("**ESG, Fragility & Foreign Exchange Notes:**")
                st.caption(res.get("fragility_esg_fx_notes", "No material vulnerabilities observed."))
            with t_col2:
                st.markdown("**12–24 Month Catalyst & Drift Watch:**")
                st.caption(res.get("drift_optionality_update", "Monitor upcoming capital deployment."))

    with tab_appendices:
        with st.container(border=True):
            st.markdown("##### Appendix A — Forensic Evidence Pack")
            st.caption("Exact quotes, regulatory disclosures, and load-bearing audit excerpts:")
            for e in res.get("appendix_a_forensic_evidence", []):
                st.markdown(f"- `{e}`")
            
            st.divider()
            st.markdown("##### Appendix B — Calculations & Stress Tests")
            calcs = res.get("appendix_b_calculations", {})
            for k, v in calcs.items():
                st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")

    # 5. EXPORT TOOLBAR
    st.write("")
    st.divider()
    exp_col1, exp_col2, exp_col3 = st.columns([1, 1, 2])
    
    with exp_col1:
        st.download_button(
            label="Export Structured JSON",
            data=json.dumps(res, indent=2),
            file_name=f"{res.get('company_name', 'Company')}_IDEX75SC.json",
            mime="application/json",
            width="stretch"
        )
    with exp_col2:
        md_text = f"""# {res.get('cover_line', 'IDEX-7.5SC Institutional Research')}

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
            label="Export Research Memo (.md)",
            data=md_text,
            file_name=f"{res.get('company_name', 'Company')}_Institutional_Memo.md",
            mime="text/markdown",
            width="stretch"
        )
