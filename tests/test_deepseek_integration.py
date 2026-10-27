"""
tests/test_deepseek_integration.py
Tests for DeepSeek API integration in StockSage / Project KUSHA.
"""

import json
import unittest
from unittest.mock import patch, MagicMock

from analyzer import (
    SUPPORTED_DEEPSEEK_MODELS,
    DEFAULT_DEEPSEEK_MODEL,
    verify_deepseek_api_key,
    analyze_document_with_deepseek,
    _safe_deepseek_error
)


class TestDeepSeekIntegration(unittest.TestCase):
    """Verifies DeepSeek API key verification and analysis engine execution."""

    def test_supported_deepseek_models(self):
        """Ensure canonical DeepSeek models are supported."""
        self.assertIn("deepseek-chat", SUPPORTED_DEEPSEEK_MODELS)
        self.assertIn("deepseek-reasoner", SUPPORTED_DEEPSEEK_MODELS)
        self.assertEqual(DEFAULT_DEEPSEEK_MODEL, "deepseek-chat")

    def test_verify_empty_api_key(self):
        """Empty DeepSeek key should fail immediately without making network calls."""
        valid, msg = verify_deepseek_api_key("")
        self.assertFalse(valid)
        self.assertIn("empty", msg.lower())

    @patch("requests.post")
    def test_verify_valid_api_key(self, mock_post):
        """HTTP 200 from DeepSeek verifies key successfully."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        valid, msg = verify_deepseek_api_key("sk-test-secret-key-12345", model_name="deepseek-chat")
        self.assertTrue(valid)
        self.assertIn("valid", msg.lower())
        self.assertNotIn("sk-test-secret-key-12345", msg)

    @patch("requests.post")
    def test_verify_invalid_api_key(self, mock_post):
        """HTTP 401 returns clear invalid key message."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_post.return_value = mock_resp

        valid, msg = verify_deepseek_api_key("sk-invalid-key")
        self.assertFalse(valid)
        self.assertIn("invalid", msg.lower())

    @patch("requests.post")
    def test_verify_insufficient_balance(self, mock_post):
        """HTTP 402 returns clear balance message."""
        mock_resp = MagicMock()
        mock_resp.status_code = 402
        mock_post.return_value = mock_resp

        valid, msg = verify_deepseek_api_key("sk-no-balance")
        self.assertFalse(valid)
        self.assertIn("balance", msg.lower())

    def test_safe_error_masking(self):
        """Verify API keys and bearer tokens are strictly redacted from errors."""
        raw_key = "sk-0123456789abcdef0123456789abcdef"
        raw_err = f"Failed to authorize with Bearer {raw_key} due to timeout"
        masked = _safe_deepseek_error(raw_err, raw_key)
        self.assertNotIn(raw_key, masked)
        self.assertIn("REDACTED", masked)

    @patch("requests.post")
    def test_analyze_document_with_deepseek_success(self, mock_post):
        """Test full execution of DeepSeek analysis with deterministic Python scoring reconciliation."""
        sample_json_response = {
            "cover_line": "Evaluate Tata Consumer in FMCG using Project KUSHA Model",
            "company_name": "Tata Consumer Products Ltd.",
            "sector": "FMCG / Packaged Goods",
            "ticker": "TATACONSUM.NS",
            "financial_year": "FY24-25",
            "final_call": "QUALITY COMPOUNDER — High capital discipline and clean accounting trail.",
            "pillars": [
                {"id": 1, "name": "Governance & Capital Allocation", "score": 18.0, "max_score": 20.0, "justification": "Clean board."},
                {"id": 2, "name": "Forensic Accounting & Cash Flow", "score": 17.5, "max_score": 20.0, "justification": "Strong CFO conversion.", "receivable_subscore": "4.0/4.0"},
                {"id": 3, "name": "Risk, ESG & Fragility", "score": 10.0, "max_score": 12.0, "justification": "Low leverage."},
                {"id": 4, "name": "Valuation & Sanity Layer", "score": 4.5, "max_score": 6.0, "justification": "Trades near median."},
                {"id": 5, "name": "Moat Durability & Scalability", "score": 11.0, "max_score": 13.0, "justification": "Brand dominance."},
                {"id": 6, "name": "Simplicity & Repeatability", "score": 4.5, "max_score": 5.0, "justification": "Predictable FMCG model."},
                {"id": 7, "name": "Innovation & TAM Optionality", "score": 14.0, "max_score": 18.0, "justification": "Portfolio expansion."},
                {"id": 8, "name": "Insider & Minority Shareholder Risk", "score": 5.5, "max_score": 6.0, "justification": "Zero promoter pledge."}
            ],
            "guardrail_tag": "GOV-CLEAN 🟢",
            "pio_triggered": False,
            "penalties_breakdown": [],
            "bonuses_breakdown": {
                "cool_pro_bonus": 2.0,
                "trajectory_bonus": 1.0,
                "resilience_bonus": 1.0,
                "reason": "Consistent 3Y CAGR outperformance."
            },
            "position_sizing": "5-10% Allocation Tier",
            "receivable_health_metrics": {
                "dso_current": 38.0,
                "receivables_pct_sales": 8.5
            }
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(sample_json_response)
                    }
                }
            ]
        }
        mock_post.return_value = mock_resp

        # Case 1: Evaluation with valid statutory PDF filing attached
        import io
        import pypdf
        writer = pypdf.PdfWriter()
        writer.add_blank_page(width=100, height=100)
        pdf_buf = io.BytesIO()
        writer.write(pdf_buf)
        dummy_pdf = pdf_buf.getvalue()

        result = analyze_document_with_deepseek(
            company_name="Tata Consumer Products Ltd.",
            sector="FMCG / Packaged Goods",
            api_key="sk-valid-deepseek-key",
            pdf_bytes=dummy_pdf,
            selected_model="deepseek-chat"
        )

        self.assertEqual(result["llm_provider"], "deepseek")
        self.assertEqual(result["model_used"], "deepseek-chat")
        self.assertEqual(result["analysis_status"], "completed")
        self.assertEqual(len(result["pillars"]), 8)
        self.assertGreater(result["final_score"], 80.0)
        self.assertEqual(result["guardrail_tag"], "GOV-CLEAN 🟢")

        # Case 2: Evaluation without PDF filing document attached (reports evidence gap)
        result_no_pdf = analyze_document_with_deepseek(
            company_name="Tata Consumer Products Ltd.",
            sector="FMCG / Packaged Goods",
            api_key="sk-valid-deepseek-key",
            pdf_bytes=None,
            selected_model="deepseek-chat"
        )
        self.assertEqual(result_no_pdf["analysis_status"], "insufficient_evidence")
        self.assertTrue(len(result_no_pdf["evidence_gaps"]) > 0)


if __name__ == "__main__":
    unittest.main()
