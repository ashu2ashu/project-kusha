"""
app.py
FinScan India - Web Application for Fundamental & Forensic Financial Analysis
"""

import streamlit as st
import plotly.graph_objects as go
import json
import os
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

from prompt_template import DEFAULT_ANALYSIS_PROMPT
from analyzer import analyze_document_with_gemini, get_demo_analysis

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="FinScan India | Fundamental & Forensic Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for clean modern look
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .score-card {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .score-number {
        font-size: 3.5rem;
        font-weight: 800;
        line-height: 1;
        margin: 10px 0;
    }
    .pillar-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .badge-clean {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-warning {
        background-color: #FEF08A;
        color: #713F12;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-danger {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR SETTINGS ---
st.sidebar.image("https://img.icons8.com/color/96/bullish.png", width=64)
st.sidebar.title("Configuration")

# API Key handling
default_env_key = os.getenv("GEMINI_API_KEY", "")
api_key = st.sidebar.text_input(
    "Google Gemini API Key (Free)",
    value=default_env_key,
    type="password",
    help="Get a 100% free API key from https://aistudio.google.com"
)

demo_mode = st.sidebar.checkbox(
    "Run in Demo / Preview Mode",
    value=False if api_key else True,
    help="Test the application UI with sample data without needing an API key."
)

if not api_key and not demo_mode:
    st.sidebar.warning("⚠️ Enter your free Gemini API Key or check 'Demo Mode' to test.")

st.sidebar.markdown("---")
with st.sidebar.expander("🛠️ Custom Analysis Prompt", expanded=False):
    st.write("You can paste or edit your prompt model here:")
    custom_prompt = st.text_area(
        "Active Prompt",
        value=DEFAULT_ANALYSIS_PROMPT,
        height=320,
        help="Use {company_name} and {sector} as dynamic placeholders."
    )

st.sidebar.markdown("---")
st.sidebar.markdown("""
**About FinScan India**  
Designed for BSE/NSE listed companies. Evaluates:
1. 📈 Profitability & Growth
2. 🔄 Capital Efficiency (ROCE)
3. 🛡️ Solvency & Leverage
4. 💵 Cash Flow Reality Check
5. 🔍 Forensic Governance & Red Flags
""")

# --- MAIN PAGE HEADER ---
st.markdown('<div class="main-title">🇮🇳 FinScan India — AI Financial Pillar Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Upload an Indian Company Annual Report or Financial PDF to generate an automated forensic scorecard.</div>', unsafe_allow_html=True)

# --- INPUT FORM ---
col_name, col_sector, col_type = st.columns([2, 2, 1.5])

with col_name:
    company_name = st.text_input("Company Name", placeholder="e.g. Tata Consumer Products Ltd, Infosys, Dixon Tech")

with col_sector:
    sector = st.selectbox(
        "Sector / Industry",
        [
            "FMCG / Consumer Goods",
            "Information Technology (IT)",
            "Automobiles & Auto Ancillaries",
            "Pharmaceuticals & Healthcare",
            "Capital Goods & Manufacturing",
            "Chemicals & Specialty Materials",
            "Banking, Financial Services & Insurance (BFSI)",
            "Infrastructure & Real Estate",
            "Energy & Power",
            "Other / Diversified"
        ]
    )

with col_type:
    report_type = st.selectbox("Document Type", ["Annual Report", "Quarterly Results", "Investor Presentation"])

uploaded_file = st.file_uploader(
    "Upload Financial Document (PDF)",
    type=["pdf"],
    help="Upload the annual report (PDF). Even 300+ page Indian reports work seamlessly with Gemini Flash."
)

# Analyze Button
analyze_clicked = st.button("🚀 Run Comprehensive Financial Analysis", type="primary", use_container_width=True)

# Helper function to plot Radar Chart
def build_radar_chart(pillars):
    categories = [p["name"] for p in pillars]
    scores = [p["score"] for p in pillars]
    max_scores = [p["max_score"] for p in pillars]
    
    # Close the loop for radar chart
    categories_closed = categories + [categories[0]]
    scores_closed = scores + [scores[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(59, 130, 246, 0.25)',
        line=dict(color='#2563EB', width=2),
        name='Score (/20)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 20]
            )
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=30, b=30),
        height=320
    )
    return fig

# --- EXECUTION & DISPLAY ---
if analyze_clicked:
    if not uploaded_file and not demo_mode:
        st.error("Please upload an Annual Report PDF or enable 'Demo / Preview Mode' from the left sidebar.")
    else:
        with st.spinner("Analyzing document across 5 pillars using forensic Indian accounting guidelines..."):
            try:
                if demo_mode:
                    result = get_demo_analysis(company_name, sector)
                else:
                    pdf_bytes = uploaded_file.read()
                    result = analyze_document_with_gemini(
                        pdf_bytes=pdf_bytes,
                        company_name=company_name,
                        sector=sector,
                        api_key=api_key,
                        custom_prompt=custom_prompt
                    )
                st.session_state["analysis_result"] = result
                st.success("✅ Analysis completed successfully!")
            except Exception as ex:
                st.error(f"Analysis failed: {str(ex)}")

# Render Results from Session State
if "analysis_result" in st.session_state:
    res = st.session_state["analysis_result"]
    st.markdown("---")

    # --- TOP SCORECARD ROW ---
    score_col, chart_col = st.columns([1.2, 2])

    with score_col:
        st.markdown(f"""
        <div class="score-card">
            <div style="font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px;">Overall Fundamental Score</div>
            <div class="score-number">{res.get('total_score', 0)}<span style="font-size: 1.5rem; opacity: 0.8;">/100</span></div>
            <div style="font-size: 1.2rem; font-weight: 600;">{res.get('verdict_grade', 'N/A')}</div>
            <div style="font-size: 0.9rem; margin-top: 8px; opacity: 0.9;">{res.get('company_name')} • {res.get('financial_year', 'FY24')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        st.write("**Top Strengths:**")
        for s in res.get("top_strengths", []):
            st.markdown(f"🟢 {s}")

    with chart_col:
        st.subheader("Pillar Distribution (Radar Chart)")
        fig = build_radar_chart(res.get("pillars", []))
        st.plotly_chart(fig, use_container_width=True)

    # --- PILLAR MARKS BREAKDOWN ---
    st.markdown("### 📋 Marks Breakdown by Pillar")
    pillar_cols = st.columns(len(res.get("pillars", [])))
    for i, col in enumerate(pillar_cols):
        p = res["pillars"][i]
        with col:
            col.metric(
                label=p["name"],
                value=f"{p['score']} / {p['max_score']}",
                delta=f"{(p['score'] / p['max_score']) * 100:.0f}%"
            )

    st.markdown("---")

    # --- TABBED DETAILED ANALYSIS ---
    tab_pillars, tab_forensics, tab_summary = st.tabs([
        "📊 Pillar Deep Dive",
        "🚨 Indian Market Red Flags",
        "📝 Executive Summary & Verdict"
    ])

    with tab_pillars:
        for p in res.get("pillars", []):
            with st.expander(f"**{p['name']}** — Score: **{p['score']}/{p['max_score']}**", expanded=True):
                st.write(p.get("assessment", ""))
                pos_col, neg_col = st.columns(2)
                with pos_col:
                    st.write("**Key Positives:**")
                    for pos in p.get("key_positives", []):
                        st.markdown(f"✅ {pos}")
                with neg_col:
                    st.write("**Key Concerns / Risks:**")
                    for neg in p.get("key_negatives", []):
                        st.markdown(f"⚠️ {neg}")

    with tab_forensics:
        st.subheader("Forensic Governance Checklist (Ind AS Compliance)")
        red_flags = res.get("indian_red_flags", [])
        if red_flags:
            for rf in red_flags:
                status = rf.get("status", "N/A")
                badge_class = "badge-clean" if "Clean" in status or "Low" in status or "None" in status else (
                    "badge-warning" if "Moderate" in status else "badge-danger"
                )
                st.markdown(f"""
                <div class="pillar-box">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 700; font-size: 1rem;">{rf.get('flag')}</span>
                        <span class="{badge_class}">{status}</span>
                    </div>
                    <div style="color: #475569; font-size: 0.95rem;">{rf.get('detail')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No red flag data found.")

    with tab_summary:
        st.subheader("Executive Summary")
        st.write(res.get("executive_summary", ""))

        st.subheader("Top Key Risks")
        for r in res.get("top_risks", []):
            st.markdown(f"🔴 {r}")

        st.subheader("Final Analyst Recommendation")
        st.info(res.get("final_recommendation", ""))

    # --- EXPORT REPORT ---
    st.markdown("---")
    st.download_button(
        label="📥 Download Structured Analysis Report (JSON)",
        data=json.dumps(res, indent=2),
        file_name=f"{res.get('company_name', 'company')}_analysis.json",
        mime="application/json"
    )
