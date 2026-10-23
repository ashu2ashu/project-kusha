"""
analyzer.py
Handles PDF parsing and LLM communication with Google Gemini Flash.
Includes fallback demo mode for testing without an API key.
"""

import json
import os
import tempfile
from typing import Dict, Any, Optional
from prompt_template import SYSTEM_INSTRUCTION, DEFAULT_ANALYSIS_PROMPT

def get_demo_analysis(company_name: str, sector: str) -> Dict[str, Any]:
    """Returns a realistic sample analysis for demonstration and preview."""
    return {
        "company_name": company_name or "Tata Consumer Products Ltd",
        "sector": sector or "FMCG / Food & Beverages",
        "financial_year": "FY24",
        "total_score": 79,
        "verdict_grade": "A - Strong Performer",
        "executive_summary": (
            f"{company_name or 'Tata Consumer Products Ltd'} demonstrates resilient operational growth in {sector or 'FMCG'}, "
            "backed by high brand equity, expansion into premium categories, and consistent cash generation. "
            "Operating margins have shown steady expansion despite input cost volatility. Working capital management remains prudent, "
            "and leverage ratios are well within safe thresholds for an Indian consumer goods company."
        ),
        "pillars": [
            {
                "name": "Profitability & Growth",
                "score": 16,
                "max_score": 20,
                "assessment": "Revenue grew at 10.5% YoY with EBITDA margins steady at ~14.8%. Strong domestic volume growth.",
                "key_positives": ["Double-digit revenue growth in core categories", "EBITDA margin expansion of 70 bps"],
                "key_negatives": ["Raw material inflation in tea/coffee segments putting short-term pressure"]
            },
            {
                "name": "Capital Allocation & Return",
                "score": 15,
                "max_score": 20,
                "assessment": "ROCE stands at 14.5% and ROE at 11.2%. Strategic acquisitions being integrated smoothly.",
                "key_positives": ["Disciplined capex with focus on supply chain digitization", "Healthy asset turnover ratio"],
                "key_negatives": ["Goodwill amortization from past M&A slightly dilutes reported ROCE"]
            },
            {
                "name": "Solvency & Balance Sheet",
                "score": 18,
                "max_score": 20,
                "assessment": "Virtually zero net debt with an Interest Coverage Ratio exceeding 12x. Rock-solid balance sheet.",
                "key_positives": ["Net Debt to EBITDA is below 0.2x", "Strong credit rating (CRISIL AAA)"],
                "key_negatives": ["Slight increase in short-term trade payables"]
            },
            {
                "name": "Cash Flow Quality",
                "score": 14,
                "max_score": 20,
                "assessment": "Operating cash flow conversion (CFO / PAT) reached 88%. Positive Free Cash Flow (FCF) throughout the year.",
                "key_positives": ["Strong cash conversion cycle of 38 days", "Predictable operating cash flow"],
                "key_negatives": ["Seasonal inventory build-up temporarily tied up cash in Q3"]
            },
            {
                "name": "Governance & Forensic Audit",
                "score": 16,
                "max_score": 20,
                "assessment": "Unmodified/clean statutory auditor opinion. Zero promoter pledging and high board independence.",
                "key_positives": ["Big 4 statutory auditor with clean report", "Zero promoter share pledging"],
                "key_negatives": ["Minor routine related-party transactions with group entities (within arm's length)"]
            }
        ],
        "indian_red_flags": [
            {
                "flag": "Auditor Opinion",
                "status": "Clean",
                "detail": "Statutory auditors issued an unmodified report with no adverse qualifications or disclaimers."
            },
            {
                "flag": "Related Party Transactions",
                "status": "Low Risk",
                "detail": "Transactions are ordinary-course operational services with Tata Group affiliates, fully disclosed under Ind AS 24."
            },
            {
                "flag": "Contingent Liabilities",
                "status": "Low Risk",
                "detail": "Contingent tax claims represent less than 3.5% of total Net Worth, well within safe parameters."
            },
            {
                "flag": "Promoter Pledging / Dilution",
                "status": "None",
                "detail": "0.0% of promoter shares are pledged. Promoter holding remains stable."
            }
        ],
        "top_strengths": [
            "Strong brand portfolio and distribution network across urban and rural India",
            "Near debt-free balance sheet offering high resilience during economic downturns",
            "High corporate governance standard backed by a reputable promoter group"
        ],
        "top_risks": [
            "Commodity price volatility (tea, coffee, and packaging costs)",
            "Intense competition from regional players and D2C brands in packaged food"
        ],
        "final_recommendation": (
            "Suitable for conservative, long-term wealth compounding. High financial quality with minimal governance risk."
        )
    }

def analyze_document_with_gemini(
    pdf_bytes: bytes,
    company_name: str,
    sector: str,
    api_key: str,
    custom_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Uploads the PDF to Google Gemini Flash and runs structured forensic financial analysis.
    """
    if not api_key or api_key.strip() == "":
        raise ValueError("Gemini API Key is missing. Please provide your free Google AI Studio key.")

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("google-genai package is not installed.")

    client = genai.Client(api_key=api_key)

    # Save PDF bytes to a temporary file for upload to Gemini
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_bytes)
        tmp_path = tmp_file.name

    uploaded_file = None
    try:
        # Upload file directly to Gemini File API (Handles large 300+ page Indian reports seamlessly)
        uploaded_file = client.files.upload(file=tmp_path)

        # Prepare prompt
        prompt_template = custom_prompt if custom_prompt and custom_prompt.strip() else DEFAULT_ANALYSIS_PROMPT
        formatted_prompt = prompt_template.format(
            company_name=company_name or "the Company",
            sector=sector or "Diversified / General"
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[uploaded_file, formatted_prompt],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                temperature=0.2,  # Low temperature for accurate, grounded analysis
            )
        )

        # Parse JSON
        result_text = response.text.strip()
        # Clean potential markdown wrapping if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        parsed_json = json.loads(result_text.strip())
        return parsed_json

    except json.JSONDecodeError as jde:
        raise ValueError(f"Failed to parse LLM response into JSON: {str(jde)}\nResponse was: {response.text[:500]}")
    except Exception as e:
        raise RuntimeError(f"Error during Gemini analysis: {str(e)}")
    finally:
        # Cleanup temporary local file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        # Attempt to clean up remote file from Gemini
        if uploaded_file and hasattr(uploaded_file, 'name'):
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass
