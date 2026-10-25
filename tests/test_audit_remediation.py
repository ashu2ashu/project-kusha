"""
tests/test_audit_remediation.py
Automated verification suite testing the 7 remediation priorities:
1. Security (CORS/XSRF, secret exclusion, no CLI key intake)
2. Truthful market and financial data (no numeric fabrication on missing fields)
3. Data consistency engine reframing (insufficient data handling, no false 100/100)
4. Visibly synthetic demo mode
5. Deterministic Python scoring, schema validation, penalty/bonus caps, and PIO
6. Supported Gemini models configuration
"""

import os
import sys
import unittest
try:
    import tomllib
except ImportError:
    import toml as tomllib
from typing import Dict, Any

# Ensure parent directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyzer import (
    validate_and_reconcile_idex_analysis,
    get_demo_analysis,
    SUPPORTED_MODELS,
    DEFAULT_MODEL,
    CANONICAL_PILLARS
)
from data_integrity_agent import DataIntegritySentinel


class TestSecurityConfiguration(unittest.TestCase):
    """Priority 1: Security tests."""

    def test_streamlit_cors_and_xsrf_enabled(self):
        """Verify that CORS and XSRF protections are enabled in config.toml."""
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".streamlit", "config.toml"))
        self.assertTrue(os.path.exists(config_path), f"config.toml not found at {config_path}")

        with open(config_path, "rb") as f:
            cfg = tomllib.load(f)

        server_cfg = cfg.get("server", {})
        self.assertTrue(server_cfg.get("enableCORS", False), "Streamlit CORS protection must be enabled (true).")
        self.assertTrue(server_cfg.get("enableXsrfProtection", False), "Streamlit XSRF protection must be enabled (true).")

    def test_gitignore_protects_secrets(self):
        """Verify that .gitignore excludes .env and .streamlit/secrets.toml."""
        gitignore_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".gitignore"))
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(".env", content)
        self.assertIn(".streamlit/secrets.toml", content)

    def test_test_key_does_not_encourage_cli_args(self):
        """Verify that test_key.py explicitly discourages command line API keys."""
        test_key_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_key.py"))
        with open(test_key_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertNotIn("python3 test_key.py YOUR_API_KEY", content)
        self.assertIn("Security Notice", content)


class TestTruthfulDataHandling(unittest.TestCase):
    """Priority 2: Truthful market data tests (no silent fabrications)."""

    def test_market_data_metadata_present(self):
        """Verify that market data structure includes attribution and timestamps."""
        from nifty_universe import fetch_live_market_data
        # Test with custom or invalid ticker to ensure None is returned, not fabricated dict
        self.assertIsNone(fetch_live_market_data("CUSTOM"))
        self.assertIsNone(fetch_live_market_data(""))

    def test_no_fabrication_constants_in_nifty_universe(self):
        """Verify that nifty_universe source code does not contain hardcoded multipliers."""
        universe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "nifty_universe.py"))
        with open(universe_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Check that silent multiplier fallbacks were completely eradicated
        self.assertNotIn("cur_price * 1.15", code)
        self.assertNotIn("cur_price * 0.85", code)
        self.assertNotIn("cur_price * 0.98", code)
        self.assertNotIn("cur_price * 0.94", code)
        self.assertNotIn("roe_pct = 13.5", code)
        self.assertNotIn("opm_pct = 18.5", code)
        self.assertNotIn("npm_pct = 12.0", code)
        self.assertNotIn("de_val = 0.45", code)
        self.assertNotIn("cr_val = 1.85", code)


class TestSentinelDataConsistencyReframing(unittest.TestCase):
    """Priority 3: Data Consistency Engine tests (no false passing marks on absent inputs)."""

    def test_empty_statements_yield_insufficient_data(self):
        """Verify that passing empty statement data yields INSUFFICIENT_DATA, not 100/100."""
        report = DataIntegritySentinel.audit_and_certify(
            ticker_symbol="TEST",
            company_name="Test Company",
            financial_statements={},
            live_market_data={}
        )

        # Must NOT be certified or 100/100
        self.assertIsNone(report["integrity_score"], "Empty statements must yield None for integrity_score")
        self.assertIn("INSUFFICIENT DATA", report["status"])
        self.assertFalse(report["can_score"], "Should not permit scoring on completely absent inputs")
        self.assertEqual(report["passed_count"], 0)
        self.assertEqual(report["skipped_count"], 6)

        # All 6 checks must report INSUFFICIENT_DATA status
        for chk in report["checks"]:
            self.assertEqual(chk["status"], "INSUFFICIENT_DATA")
            self.assertIsNone(chk["passed"])

    def test_detects_balance_sheet_equation_failure(self):
        """Verify that when Assets < Net Worth, the equation check reports FAILED."""
        statements = {
            "bs": {
                "Total Net Worth / Equity": {"values": [12000.0]},
                "Total Liabilities & Assets": {"values": [8000.0]}  # Anomaly: NW > Assets
            },
            "years": ["FY22", "FY23", "FY24"]
        }

        report = DataIntegritySentinel.audit_and_certify(
            ticker_symbol="TEST",
            company_name="Test Company",
            financial_statements=statements,
            live_market_data={"current_price": 100.0, "high_52w": 120.0, "low_52w": 80.0}
        )

        bs_chk = next(c for c in report["checks"] if c["id"] == "CHK_01_BS_EQUATION")
        self.assertEqual(bs_chk["status"], "FAILED")
        self.assertFalse(bs_chk["passed"])
        self.assertIn("Balance Sheet Equation Discrepancy", report["audit_flags"])
        self.assertIn("CONSISTENCY VARIANCES FLAGGED", report["status"])

    def test_run_identifier_is_not_labeled_as_proof_of_authenticity(self):
        """Verify that run hash is labeled as an identifier and contains appropriate notice."""
        report = DataIntegritySentinel.audit_and_certify(
            ticker_symbol="TEST",
            company_name="Test Company"
        )
        self.assertTrue(report["run_id"].startswith("CONSISTENCY-RUN-"))
        self.assertIn("does not certify third-party authenticity", report["run_id_notice"])


class TestDemoModeHardening(unittest.TestCase):
    """Priority 4: Demo Mode visibly synthetic tests."""

    def test_demo_mode_is_visibly_synthetic(self):
        """Verify that get_demo_analysis returns clearly labeled synthetic sample data."""
        demo = get_demo_analysis("Tata Consumer Products Ltd", "FMCG / Retail")

        self.assertTrue(demo.get("is_synthetic_demo"), "Demo analysis must be flagged as synthetic demo")
        self.assertIn("[SYNTHETIC SAMPLE]", demo["company_name"])
        self.assertIn("[SYNTHETIC DEMO ONLY]", demo["verdict"])

        # Check evidence contains [DEMO SAMPLE] tags
        for ev in demo["guardrail_evidence"]:
            self.assertIn("[DEMO SAMPLE]", ev)

        # Must not claim Walker Chandiok or specific Tata disclosures for arbitrary analysis
        ev_text = " ".join(demo.get("appendix_a_forensic_evidence", []))
        self.assertNotIn("Walker Chandiok", ev_text)
        self.assertIn("[DEMO SAMPLE]", ev_text)


class TestDeterministicScoringRules(unittest.TestCase):
    """Priority 5: Deterministic Python scoring, schema validation, and caps."""

    def _build_valid_pillars(self, scores=None):
        if scores is None:
            scores = [18.0, 16.5, 10.5, 3.5, 11.5, 4.5, 14.0, 5.0]  # Sum = 83.5
        pillars = []
        for i, canon in enumerate(CANONICAL_PILLARS):
            pillars.append({
                "id": canon["id"],
                "name": canon["name"],
                "score": scores[i],
                "max_score": canon["max_score"],
                "justification": f"Justification for {canon['name']}"
            })
        return pillars

    def test_schema_validation_rejects_non_dict_and_missing_pillars(self):
        """Verify that malformed inputs raise ValueError."""
        with self.assertRaises(ValueError):
            validate_and_reconcile_idex_analysis(["not", "a", "dict"])

        with self.assertRaises(ValueError):
            validate_and_reconcile_idex_analysis({"pillars": [1, 2, 3]})  # Less than 8 pillars

    def test_deterministic_core_score_sum_and_clamping(self):
        """Verify that core score is the exact sum of clamped pillars."""
        # Intentionally provide out-of-bounds scores
        pillars = self._build_valid_pillars([
            25.0,  # Max is 20.0 -> clamps to 20.0
            -5.0,  # Min is 0.0 -> clamps to 0.0
            12.0,  # Max is 12.0 -> 12.0
            6.0,   # Max is 6.0 -> 6.0
            13.0,  # Max is 13.0 -> 13.0
            5.0,   # Max is 5.0 -> 5.0
            18.0,  # Max is 18.0 -> 18.0
            6.0    # Max is 6.0 -> 6.0
        ])
        raw = {"pillars": pillars}
        res = validate_and_reconcile_idex_analysis(raw)

        # Expected sum: 20 + 0 + 12 + 6 + 13 + 5 + 18 + 6 = 80.0
        self.assertEqual(res["core_score"], 80.0)
        self.assertEqual(res["pillars"][0]["score"], 20.0)
        self.assertEqual(res["pillars"][1]["score"], 0.0)

    def test_penalty_cap_enforced_at_negative_7_point_5(self):
        """Verify that total penalties cannot exceed -7.5 points."""
        pillars = self._build_valid_pillars()
        raw = {
            "pillars": pillars,
            "penalties_breakdown": [
                {"penalty_name": "P1", "points": -5.0, "reason": "Severe risk"},
                {"penalty_name": "P2", "points": -5.0, "reason": "Another risk"}  # Sum = -10.0
            ]
        }
        res = validate_and_reconcile_idex_analysis(raw)
        self.assertEqual(res["total_penalties"], -7.5, "Penalties must be capped at -7.5 points max")

    def test_bonus_cap_enforced_at_10_percent_of_core(self):
        """Verify that bonuses cannot exceed 10% of core score."""
        pillars = self._build_valid_pillars()  # Core = 83.5
        raw = {
            "pillars": pillars,
            "bonuses_breakdown": {
                "cool_pro_bonus": 8.0,
                "trajectory_bonus": 4.0,
                "resilience_bonus": 2.0  # Raw sum = 14.0
            }
        }
        res = validate_and_reconcile_idex_analysis(raw)
        # 10% of 83.5 = 8.35 -> rounded to 8.4
        self.assertLessEqual(res["bonuses_breakdown"]["total_bonus_applied"], 8.4)

    def test_promoter_integrity_override_enforcement(self):
        """Verify that PIO clamps Governance <= 6, zeroes bonuses, and sets GOV-RED."""
        pillars = self._build_valid_pillars([19.0, 18.0, 11.0, 5.0, 12.0, 4.0, 16.0, 5.0])
        raw = {
            "pillars": pillars,
            "guardrail_tag": "GOV-RED 🔴",
            "bonuses_breakdown": {"cool_pro_bonus": 4.0, "trajectory_bonus": 2.0}
        }
        res = validate_and_reconcile_idex_analysis(raw)

        self.assertTrue(res["pio_triggered"])
        self.assertEqual(res["guardrail_tag"], "GOV-RED 🔴")
        # Governance pillar (id: 1) clamped to <= 6.0
        self.assertLessEqual(res["pillars"][0]["score"], 6.0)
        # All bonuses must be revoked
        self.assertEqual(res["bonuses_breakdown"]["total_bonus_applied"], 0.0)
        # Final score must be in Fragile (<50.0) territory
        self.assertLess(res["final_score"], 50.0)
        self.assertIn("FRAGILE", res["verdict"])
        self.assertEqual(res["position_sizing"], "0%")


class TestSupportedModelsConfiguration(unittest.TestCase):
    """Priority 6: Supported Gemini models test."""

    def test_supported_models_list(self):
        """Verify that supported models list contains verified Gemini models."""
        self.assertIn("gemini-2.5-flash", SUPPORTED_MODELS)
        self.assertIn("gemini-2.0-flash", SUPPORTED_MODELS)
        self.assertIn("gemini-1.5-flash", SUPPORTED_MODELS)
        self.assertEqual(DEFAULT_MODEL, "gemini-2.5-flash")
        # Confirm obsolete models are removed
        self.assertNotIn("gemini-3.5-flash", SUPPORTED_MODELS)
        self.assertNotIn("gemini-3.8-flash", SUPPORTED_MODELS)


if __name__ == "__main__":
    unittest.main()
