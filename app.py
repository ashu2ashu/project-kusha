"""
app.py
FinScan India — IDEX-7.5SC Hybrid Pro (Ashu Elite Edition)
Institutional Fundamental & Forensic Research Platform for Indian Equities
"""

import streamlit as st
import plotly.graph_objects as go
import json
import os
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv(override=True)

from prompt_template import IDEX_ANALYSIS_PROMPT
import importlib
import analyzer
importlib.reload(analyzer)
from analyzer import analyze_document_with_gemini, get_demo_analysis, verify_gemini_api_key

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="IDEX-7.5SC Pro (Ashu Elite Edition) | Indian Equity Research",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Institutional Look
st.markdown("""
<style>
    .report-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.5px;
        margin-bottom: 2px;
    }
    .report-subtitle {
        font-size: 1.0rem;
        color: #475569;
        margin-bottom: 20px;
    }
    .guardrail-clean {
        background-color: #ECFDF5;
        border: 2px solid #10B981;
        border-radius: 10px;
        padding: 16px 20px;
        color: #065F46;
        margin-bottom: 20px;
    }
    .guardrail-alert {
        background-color: #FFFBEB;
        border: 2px solid #F59E0B;
        border-radius: 10px;
        padding: 16px 20px;
        color: #92400E;
        margin-bottom: 20px;
    }
    .guardrail-red {
        background-color: #FEF2F2;
        border: 2px solid #EF4444;
        border-radius: 10px;
        padding: 16px 20px;
        color: #991B1B;
        margin-bottom: 20px;
    }
    .score-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-value-huge {
        font-size: 3.6rem;
        font-weight: 800;
        line-height: 1;
        margin: 8px 0;
        color: #38BDF8;
    }
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
        background-color: #E2E8F0;
        color: #334155;
    }
    .receivable-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR SETTINGS ---
st.sidebar.image("https://img.icons8.com/color/96/shield.png", width=56)
st.sidebar.markdown("### **IDEX-7.5SC Hybrid Pro**")
st.sidebar.caption("Ashu Elite Edition — Locked with Promoter Integrity Guardrails")

# API Key handling
env_key = os.getenv("GEMINI_API_KEY", "").strip()
api_key_input = st.sidebar.text_input(
    "Google Gemini API Key (Free)",
    value=env_key,
    type="password",
    help="Loaded automatically from .env or enter manually."
)

active_api_key = api_key_input.strip() if api_key_input and api_key_input.strip() else env_key

if env_key:
    st.sidebar.caption("🔒 Key auto-detected from .env")

if st.sidebar.button("🔍 Test Key Connection", use_container_width=True):
    with st.sidebar:
        with st.spinner("Testing API key with Gemini..."):
            is_valid, msg = verify_gemini_api_key(active_api_key)
            if is_valid:
                st.success(msg)
            else:
                st.error(msg)

demo_mode = st.sidebar.checkbox(
    "Run in Demo / Preview Mode",
    value=False if active_api_key else True,
    help="Preview complete institutional analysis on sample company without needing an API key."
)

if not active_api_key and not demo_mode:
    st.sidebar.warning("⚠️ Enter your Gemini API Key or check 'Demo Mode' to evaluate.")

st.sidebar.markdown("---")
with st.sidebar.expander("🛠️ View / Edit IDEX Prompt Model", expanded=False):
    custom_prompt = st.text_area(
        "Active Prompt Template",
        value=IDEX_ANALYSIS_PROMPT,
        height=300,
        help="Use {company_name} and {sector} as dynamic placeholders."
    )

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Framework Core Rules:**
- **Core Score:** ≤ 100 Max across 8 Pillars
- **Receivable Layer:** Embedded 4.0 pt subscore
- **PIO Hard Override:** Auto-caps Governance ≤6/20, blocks bonuses, forces `GOV-RED 🔴`
- **Bonuses:** Cumulative cap +10% (COOL++, Trajectory, Resilience)
""")

# --- MAIN PAGE HEADER ---
st.markdown('<div class="report-title">🛡️ IDEX-7.5SC Hybrid Pro (Ashu Elite Edition)</div>', unsafe_allow_html=True)
st.markdown('<div class="report-subtitle">Forensic Equity Research & 8-Pillar Scoring Engine with Promoter Integrity Guardrails & Receivable Health Layer</div>', unsafe_allow_html=True)

# --- INPUT SECTION ---
input_col1, input_col2, input_col3 = st.columns([2.2, 1.8, 1.5])

with input_col1:
    company_name = st.text_input("Company Name", placeholder="e.g. Tata Consumer Products Ltd, Dixon Tech, Titan")

with input_col2:
    sector = st.selectbox(
        "Sector Benchmark",
        [
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
    )

with input_col3:
    doc_type = st.selectbox("Document Type", ["Annual Report", "Investor Presentation", "Audited Financials"])

uploaded_file = st.file_uploader(
    "Upload Financial Report (PDF)",
    type=["pdf"],
    help="Upload the annual report (PDF). 200–500 page Indian reports are fully ingested by Gemini Flash."
)

run_button = st.button("🚀 Execute IDEX-7.5SC Forensic Evaluation", type="primary", use_container_width=True)

# Helper function to plot 8-Pillar Radar Chart
def build_8pillar_radar(pillars):
    names = [f"P{p['id']}: {p['name'][:18]}.." if len(p['name']) > 20 else f"P{p['id']}: {p['name']}" for p in pillars]
    # Normalize score to percentage of max for fair radar visual
    pct_scores = [(p["score"] / p["max_score"]) * 100 for p in pillars]
    
    names_closed = names + [names[0]]
    pct_closed = pct_scores + [pct_scores[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=pct_closed,
        theta=names_closed,
        fill='toself',
        fillcolor='rgba(56, 189, 248, 0.22)',
        line=dict(color='#0284C7', width=2.5),
        name='% of Max Score'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%"
            )
        ),
        showlegend=False,
        margin=dict(l=45, r=45, t=25, b=25),
        height=360
    )
    return fig

# --- EXECUTION ---
if run_button:
    if not uploaded_file and not demo_mode:
        st.error("Please upload an Annual Report PDF or check 'Run in Demo / Preview Mode' in the sidebar.")
    else:
        with st.spinner("Executing IDEX-7.5SC Hybrid Pro with Promoter Integrity Guardrails & Receivable Checks..."):
            try:
                if demo_mode:
                    result = get_demo_analysis(company_name, sector)
                else:
                    pdf_bytes = uploaded_file.read()
                    result = analyze_document_with_gemini(
                        pdf_bytes=pdf_bytes,
                        company_name=company_name,
                        sector=sector,
                        api_key=active_api_key,
                        custom_prompt=custom_prompt
                    )
                st.session_state["idex_result"] = result
                st.success("✅ Evaluation complete! Institutional scorecard generated.")
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")
                with st.expander("🔍 View Technical Details of Error"):
                    st.exception(e)

# --- DISPLAY REPORT ---
if "idex_result" in st.session_state:
    res = st.session_state["idex_result"]
    st.markdown("---")

    # 1. MANDATORY GUARDRAIL TAG BANNER
    tag = res.get("guardrail_tag", "GOV-CLEAN 🟢")
    evidence_list = res.get("guardrail_evidence", [])
    
    if "GOV-RED" in tag or res.get("pio_triggered", False):
        st.markdown(f"""
        <div class="guardrail-red">
            <h3 style="margin:0 0 6px 0; color:#B91C1C;">🚨 MANDATORY GUARDRAIL TAG: {tag} (PIO TRIGGERED)</h3>
            <p style="margin:0 0 8px 0; font-weight:600;">{res.get('pio_reason', 'Promoter Integrity Override fired. Governance capped ≤ 6.0/20. All bonuses blocked. Automatic Red Flag zone.')}</p>
            <ul>{''.join([f'<li>{e}</li>' for e in evidence_list])}</ul>
        </div>
        """, unsafe_allow_html=True)
    elif "PROM-ALERT" in tag:
        st.markdown(f"""
        <div class="guardrail-alert">
            <h3 style="margin:0 0 6px 0; color:#B45309;">⚠️ MANDATORY GUARDRAIL TAG: {tag}</h3>
            <p style="margin:0 0 8px 0;">Elevated promoter pledge or dilution risk detected under PPRM/Stake Trend rules.</p>
            <ul>{''.join([f'<li>{e}</li>' for e in evidence_list])}</ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="guardrail-clean">
            <h3 style="margin:0 0 6px 0; color:#047857;">🛡️ MANDATORY GUARDRAIL TAG: {tag}</h3>
            <p style="margin:0 0 8px 0;">Clean governance track record, zero pledging, stable auditors, aligned promoter incentives.</p>
            <ul>{''.join([f'<li>{e}</li>' for e in evidence_list])}</ul>
        </div>
        """, unsafe_allow_html=True)

    # 2. TOP BANNER: SCORECARD & RADAR
    score_col, radar_col = st.columns([1.3, 2])

    with score_col:
        st.markdown(f"""
        <div class="score-banner">
            <div style="font-size: 0.95rem; text-transform: uppercase; letter-spacing: 1.2px; opacity: 0.85;">Final IDEX-7.5SC Score</div>
            <div class="metric-value-huge">{res.get('final_score', 0):.1f}<span style="font-size: 1.6rem; opacity: 0.7;">/100</span></div>
            <div style="font-size: 1.35rem; font-weight: 700; color: #F8FAFC;">{res.get('verdict', 'N/A')}</div>
            <div style="font-size: 0.95rem; margin-top: 10px; color: #94A3B8;">
                Core: <b>{res.get('core_score', 0):.1f}</b> | Penalties: <b>{res.get('total_penalties', 0):.1f}</b> | Bonus: <b>+{res.get('bonuses_breakdown', {}).get('total_bonus_applied', 0):.1f}%</b>
            </div>
            <div style="margin-top: 14px;">
                <span style="font-size: 0.85rem; color: #E2E8F0;">Suggested Position Sizing:</span><br/>
                <span style="font-size: 1.3rem; font-weight: 800; color: #34D399;">{res.get('position_sizing', '0%')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        st.write("**Active Tags:**")
        tag_html = "".join([f'<span class="badge-pill">{t}</span>' for t in res.get("tags_applied", [])])
        st.markdown(tag_html, unsafe_allow_html=True)

    with radar_col:
        st.subheader("8-Pillar Quality Profile")
        radar_fig = build_8pillar_radar(res.get("pillars", []))
        st.plotly_chart(radar_fig, use_container_width=True)

    # 3. INSERTED RECEIVABLE HEALTH LAYER
    rec_metrics = res.get("receivable_health_metrics", {})
    if rec_metrics:
        st.markdown("### 📥 Sector-Sensitive Receivable Health Layer")
        rcol1, rcol2, rcol3, rcol4, rcol5 = st.columns(5)
        with rcol1:
            st.metric("DSO (Days)", f"{rec_metrics.get('dso_days', 'N/A')} days", help="Days Sales Outstanding")
            st.caption(f"Ideal: {rec_metrics.get('sector_ideal_dso', 'N/A')}")
        with rcol2:
            st.metric("Receivables / Sales", rec_metrics.get("receivables_to_sales_pct", "N/A"))
        with rcol3:
            st.metric(">90 Days Overdue", rec_metrics.get("pct_over_90_days", "N/A"), help="Delinquency threshold")
        with rcol4:
            st.metric("Top Debtor Conc.", rec_metrics.get("top_debtor_concentration_pct", "N/A"))
        with rcol5:
            st.metric("Provision Coverage", rec_metrics.get("provision_coverage_pct", "N/A"))

        st.info(f"**Receivable Health Assessment:** {rec_metrics.get('receivable_verdict', 'Normal')}")

    st.markdown("---")

    # 4. TABBED DETAILED BREAKDOWNS
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Full 8-Pillar Scorecard",
        "⚖️ Penalties & Bonuses",
        "📈 Peer Matrix & Context",
        "🎯 Final Call & Thesis",
        "📁 Appendices (Forensic Pack & DCF)"
    ])

    with tab1:
        st.subheader("Core 8-Pillar Evaluation (Max 100 Points)")
        for p in res.get("pillars", []):
            p_score = p.get("score", 0)
            p_max = p.get("max_score", 1)
            pct = (p_score / p_max) * 100
            
            with st.expander(f"**Pillar {p.get('id', '')}: {p.get('name')}** — **{p_score:.1f} / {p_max:.1f}** ({pct:.0f}%)", expanded=True):
                st.write(p.get("justification", ""))
                if "receivable_subscore" in p:
                    st.markdown(f"**Receivable Subscore (Embedded):** `{p['receivable_subscore']}`")

    with tab2:
        col_pen, col_bon = st.columns(2)
        with col_pen:
            st.subheader("⚠️ Penalties Applied")
            st.write(f"**Total Penalties:** `{res.get('total_penalties', 0):.1f} pts`")
            pen_list = res.get("penalties_breakdown", [])
            if pen_list:
                for item in pen_list:
                    st.markdown(f"- **{item.get('penalty_name')}:** `{item.get('points')} pts` — {item.get('reason')}")
            else:
                st.success("No statutory penalties triggered.")

        with col_bon:
            st.subheader("🌟 Bonuses Applied")
            bb = res.get("bonuses_breakdown", {})
            st.write(f"**Total Bonus Applied:** `+{bb.get('total_bonus_applied', 0):.1f}%` (Max Cap: +10%)")
            st.markdown(f"- **COOL++ PRO Bonus:** `+{bb.get('cool_pro_bonus', 0):.1f}%`")
            st.markdown(f"- **Trajectory Bonus:** `+{bb.get('trajectory_bonus', 0):.1f}%`")
            st.markdown(f"- **Resilience Bonus:** `+{bb.get('resilience_bonus', 0):.1f}%`")

    with tab3:
        st.subheader("Peer Comparison Matrix")
        peers = res.get("peer_matrix", [])
        if peers:
            st.table(peers)
        
        st.markdown("#### Strengths vs Weaknesses")
        scol, wcol = st.columns(2)
        with scol:
            st.write("**Key Structural Strengths:**")
            for s in res.get("strengths", []):
                st.markdown(f"🟢 {s}")
        with wcol:
            st.write("**Key Weaknesses & Vulnerabilities:**")
            for w in res.get("weaknesses", []):
                st.markdown(f"🔴 {w}")

    with tab4:
        st.subheader("📌 Final Analyst Call")
        st.success(f"**{res.get('final_call', 'N/A')}**")

        st.markdown("#### ESG, Fragility & FX Notes")
        st.write(res.get("fragility_esg_fx_notes", "None reported."))

        st.markdown("#### Drift & Optionality Catalyst (12–24 Months)")
        st.write(res.get("drift_optionality_update", "None reported."))

    with tab5:
        st.subheader("Appendix A — Forensic Evidence Pack")
        st.caption("Exact quotes, regulatory disclosures, and load-bearing citations")
        for item in res.get("appendix_a_forensic_evidence", []):
            st.markdown(f"- {item}")

        st.markdown("---")
        st.subheader("Appendix B — Calculations & Stress Tests")
        app_b = res.get("appendix_b_calculations", {})
        for k, v in app_b.items():
            st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")

    # 5. EXPORT OPTIONS
    st.markdown("---")
    down_col1, down_col2 = st.columns(2)

    with down_col1:
        st.download_button(
            label="📥 Download Structured JSON Data",
            data=json.dumps(res, indent=2),
            file_name=f"{res.get('company_name', 'company')}_IDEX_7.5SC.json",
            mime="application/json",
            use_container_width=True
        )

    with down_col2:
        # Build strict 17-section institutional markdown report
        md_report = f"""# {res.get('cover_line', 'IDEX-7.5SC Hybrid Pro Evaluation')}

## 1. Company & Sector
- **Company:** {res.get('company_name')}
- **Sector:** {res.get('sector')}
- **Financial Period:** {res.get('financial_year')}

## 2. Mandatory Guardrail Tag
### {res.get('guardrail_tag')}
{chr(10).join(['- ' + e for e in res.get('guardrail_evidence', [])])}

## 3. Full 8-Pillar Scorecard (Core Max = 100)
{chr(10).join([f"- **Pillar {p.get('id')}: {p.get('name')}**: {p.get('score')}/{p.get('max_score')} ({p.get('justification')})" for p in res.get('pillars', [])])}

**Core Score:** {res.get('core_score')}/100

## 4. Adjusted Score & Penalties
- Total Penalties: {res.get('total_penalties')}
- Adjusted Pre-Bonus Score: {res.get('adjusted_pre_bonus_score')}

## 5. Bonuses Applied
- COOL++ PRO: +{res.get('bonuses_breakdown', {}).get('cool_pro_bonus')}%
- Trajectory: +{res.get('bonuses_breakdown', {}).get('trajectory_bonus')}%
- Resilience: +{res.get('bonuses_breakdown', {}).get('resilience_bonus')}%
- Total Bonus Applied: +{res.get('bonuses_breakdown', {}).get('total_bonus_applied')}%

## 6. Final Score & Verdict
- **Final Score:** {res.get('final_score')} / 100
- **Verdict:** {res.get('verdict')}
- **Position Sizing Suggestion:** {res.get('position_sizing')}

## 7. Active Tags
{', '.join(res.get('tags_applied', []))}

## 8. Receivable Health & Sector Benchmark Layer
- DSO: {rec_metrics.get('dso_days')} days (Sector Ideal: {rec_metrics.get('sector_ideal_dso')})
- Receivables / Sales: {rec_metrics.get('receivables_to_sales_pct')}
- % >90 Days Overdue: {rec_metrics.get('pct_over_90_days')}
- Top Debtor Concentration: {rec_metrics.get('top_debtor_concentration_pct')}
- Provision Coverage: {rec_metrics.get('provision_coverage_pct')}
- Verdict: {rec_metrics.get('receivable_verdict')}

## 9. Final Call
**{res.get('final_call')}**

## 10. Appendix A — Forensic Evidence Pack
{chr(10).join(['- ' + e for e in res.get('appendix_a_forensic_evidence', [])])}

## 11. Appendix B — Calculations
{chr(10).join([f"- **{k.title()}**: {v}" for k, v in app_b.items()])}
"""
        st.download_button(
            label="📄 Download Full Institutional Research Report (.md)",
            data=md_report,
            file_name=f"{res.get('company_name', 'company')}_IDEX_7.5SC_Report.md",
            mime="text/markdown",
            use_container_width=True
        )
