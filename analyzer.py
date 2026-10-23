"""
analyzer.py
Engine for IDEX-7.5SC Hybrid Pro (Ashu Elite Edition).
Handles PDF ingestion, communication with Gemini Flash, and full 8-pillar parsing.
"""

import json
import os
import tempfile
from typing import Dict, Any, Optional
from prompt_template import IDEX_SYSTEM_INSTRUCTION, IDEX_ANALYSIS_PROMPT

# Models ordered by current availability & performance
SUPPORTED_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.8-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest"
]

def verify_gemini_api_key(api_key: str) -> tuple[bool, str]:
    """Tests if the provided Gemini API key is valid by making a quick ping."""
    key = api_key.strip().strip("'").strip('"').strip() if api_key else ""
    if not key:
        return False, "API key field is empty. Please paste your key."
    
    try:
        from google import genai
        client = genai.Client(api_key=key)
        
        # Try available models in order
        last_error = None
        for model_name in SUPPORTED_MODELS:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents="ping",
                )
                if resp and resp.text:
                    return True, f"✅ API Key is 100% valid & connected to Google Gemini ({model_name})!"
            except Exception as me:
                last_error = me
                continue

        if last_error:
            raise last_error

        return False, "Received empty response from Gemini."
    except Exception as e:
        err = str(e)
        if "API_KEY_INVALID" in err or "400" in err:
            return False, "❌ Invalid API Key. Please re-copy the key from https://aistudio.google.com"
        if "PERMISSION_DENIED" in err or "403" in err:
            return False, "❌ Permission Denied: Generative Language API is not enabled for this project."
        if "RESOURCE_EXHAUSTED" in err or "429" in err:
            return False, "⚠️ Rate limit reached (15 requests/min). Please wait 30 seconds and try again."
        return False, f"Verification failed: {err}"

def get_demo_analysis(company_name: str, sector: str) -> Dict[str, Any]:
    """Returns a realistic, high-grade institutional IDEX-7.5SC analysis."""
    c_name = company_name.strip() if company_name and company_name.strip() else "Tata Consumer Products Ltd"
    c_sec = sector.strip() if sector and sector.strip() else "FMCG / Retail"

    return {
        "cover_line": f"Evaluate {c_name} in {c_sec} using IDEX-7.5SC Hybrid Pro (Ashu Elite Edition) — Updated with Promoter Integrity Guardrails",
        "company_name": c_name,
        "sector": c_sec,
        "financial_year": "FY24",
        "guardrail_tag": "GOV-CLEAN 🟢",
        "guardrail_evidence": [
            "Pristine 10Y+ audit history under Big 4 statutory auditor with unmodified opinion",
            "0.0% promoter share pledging with stable promoter ownership (33.5%)",
            "Zero SEBI, ED, or regulatory show-cause notices or ongoing fraud investigations"
        ],
        "pio_triggered": False,
        "pio_reason": None,
        "core_score": 83.0,
        "total_penalties": -1.5,
        "penalties_breakdown": [
            {
                "penalty_name": "Valuation Distortion",
                "points": -1.5,
                "reason": "Trailing P/E of ~75x is elevated; requires sustained 18%+ earnings compounding to justify."
            }
        ],
        "adjusted_pre_bonus_score": 81.5,
        "bonuses_breakdown": {
            "cool_pro_bonus": 3.0,
            "trajectory_bonus": 1.0,
            "resilience_bonus": 1.5,
            "total_bonus_applied": 5.5
        },
        "final_score": 87.0,
        "verdict": "PCGC (85–89) — Potential Compounder",
        "position_sizing": "5–10%",
        "tags_applied": ["GOV-CLEAN 🟢", "COOL++", "Trajectory", "OCP"],
        "pillars": [
            {
                "id": 1,
                "name": "Governance & Capital Allocation",
                "score": 18.0,
                "max_score": 20.0,
                "justification": "Exemplary board independence, Tata governance code compliance, zero promoter dilution, disciplined M&A integration."
            },
            {
                "id": 2,
                "name": "Forensic Accounting & Cash Flow",
                "score": 16.5,
                "max_score": 20.0,
                "receivable_subscore": "3.6 / 4.0 (DSO at 28d vs FMCG sector ideal 15–30d; >90d = 1.4%)",
                "justification": "CFO/PAT conversion at 89%, high earnings quality, no aggressive revenue recognition, receivables well contained."
            },
            {
                "id": 3,
                "name": "Risk, ESG & Fragility",
                "score": 10.5,
                "max_score": 12.0,
                "justification": "Net Debt/EBITDA is negative (net cash balance sheet). Strong CRISIL AAA rating with minimal environmental risks."
            },
            {
                "id": 4,
                "name": "Valuation & Sanity Layer",
                "score": 3.0,
                "max_score": 6.0,
                "justification": "Multiples trade at a premium to historical median. DCF fair value implies modest margin of safety at current levels."
            },
            {
                "id": 5,
                "name": "Moat Durability & Scalability",
                "score": 11.5,
                "max_score": 13.0,
                "justification": "Formidable distribution reach across 4M+ outlets in India; high pricing power in salt and branded tea."
            },
            {
                "id": 6,
                "name": "Simplicity & Repeatability",
                "score": 4.5,
                "max_score": 5.0,
                "justification": "Straightforward FMCG business model with transparent reporting across India beverages and food verticals."
            },
            {
                "id": 7,
                "name": "Innovation & TAM Optionality",
                "score": 14.0,
                "max_score": 18.0,
                "justification": "Rapid rollout into Sampann pulses/spices, Soulfull cereals, and premium organic RTD segments expanding addressable TAM."
            },
            {
                "id": 8,
                "name": "Insider & Minority Shareholder Risk",
                "score": 5.0,
                "max_score": 6.0,
                "justification": "Zero promoter pledging, equitable treatment of minority shareholders, transparent arm's length RPT disclosures."
            }
        ],
        "receivable_health_metrics": {
            "dso_days": 28,
            "sector_ideal_dso": "15–30 days",
            "receivables_to_sales_pct": "6.8%",
            "pct_over_90_days": "1.4%",
            "top_debtor_concentration_pct": "6.2%",
            "provision_coverage_pct": "3.5%",
            "receivable_verdict": "Ideal — well inside sector benchmark limits with negligible delinquency risk"
        },
        "peer_matrix": [
            {"peer_name": "Hindustan Unilever Ltd", "score": "88.5", "position": "Benchmark Leader"},
            {"peer_name": "Nestle India Ltd", "score": "86.0", "position": "High Quality Peer"},
            {"peer_name": "Marico Ltd", "score": "82.5", "position": "Quality Tracker"}
        ],
        "strengths": [
            "Dominant market share in Tata Salt and Branded Tea with resilient pricing power",
            "Virtually debt-free balance sheet providing strategic M&A flexibility",
            "Strong corporate governance backing with zero promoter share pledging"
        ],
        "weaknesses": [
            "Elevated valuation leaving minimal room for execution missteps",
            "Sensitivity of gross margins to raw tea and coffee commodity price cycles"
        ],
        "fragility_esg_fx_notes": "Negligible environmental litigation. Minor FX exposure from international tea operations hedged via forward contracts.",
        "drift_optionality_update": "Integration of recently acquired Capital Foods (Ching's Secret) and Organic India to drive margin expansion in FY25-26.",
        "final_call": "BUY ON DIPS — High-quality compounder with fortress governance and runway for growth; accumulate during market pullbacks.",
        "appendix_a_forensic_evidence": [
            "Statutory Auditor's Report (Annual Report FY24): Unmodified opinion issued by Walker Chandiok & Co LLP.",
            "Promoter Pledge Disclosure: BSE filing confirms 0.0% promoter shareholding pledged.",
            "Ind AS 24 Related Party Disclosures: Transactions with Tata Sons and group affiliates are routine operational services on an arm's length basis."
        ],
        "appendix_b_calculations": {
            "dcf_fair_value_estimate": "INR 1,020 - 1,080 (WACC 10.8%, Terminal Growth 5.5%)",
            "stress_test_20pct_revenue_drop": "EBITDA margin compresses from 15.1% to 12.8%; ROCE remains above 10%; Net Cash position prevents financial distress.",
            "working_capital_math": "Cash Conversion Cycle: Inventory (45d) + DSO (28d) - DPO (48d) = 25 days net cycle."
        }
    }

def analyze_document_with_gemini(
    pdf_bytes: bytes,
    company_name: str,
    sector: str,
    api_key: str,
    custom_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes IDEX-7.5SC Hybrid Pro evaluation on the uploaded PDF using Gemini Flash.
    """
    clean_key = api_key.strip().strip("'").strip('"').strip() if api_key else ""
    if not clean_key:
        raise ValueError("Gemini API Key is missing. Please provide your Google AI Studio key.")

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("google-genai package is not installed.")

    client = genai.Client(api_key=clean_key)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_bytes)
        tmp_path = tmp_file.name

    uploaded_file = None
    try:
        # Upload directly to Gemini File API (Handles 300+ page Indian reports seamlessly)
        uploaded_file = client.files.upload(file=tmp_path)

        prompt_template = custom_prompt if custom_prompt and custom_prompt.strip() else IDEX_ANALYSIS_PROMPT
        formatted_prompt = prompt_template.format(
            company_name=company_name or "the Company",
            sector=sector or "Diversified"
        )

        response = None
        last_error = None
        for model_name in SUPPORTED_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[uploaded_file, formatted_prompt],
                    config=types.GenerateContentConfig(
                        system_instruction=IDEX_SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        temperature=0.15,
                    )
                )
                if response and response.text:
                    break
            except Exception as me:
                last_error = me
                continue

        if not response or not response.text:
            if last_error:
                raise last_error
            raise RuntimeError("Received empty response from Gemini model.")

        result_text = response.text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        parsed_json = json.loads(result_text.strip())
        return parsed_json

    except json.JSONDecodeError as jde:
        raise ValueError(f"Failed to parse LLM response into JSON: {str(jde)}\nResponse was: {response.text[:500] if response else 'None'}")
    except Exception as e:
        raise RuntimeError(f"Error during Gemini analysis: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if uploaded_file and hasattr(uploaded_file, 'name'):
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass
