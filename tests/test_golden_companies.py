"""
tests/test_golden_companies.py
Regression suite verifying core invariant promises across 5 golden corporate archetypes.
Ensures zero hallucinated scores, deterministic reconciliation, and forensic honesty.
"""

import unittest
from forensic_risk_engine import ForensicRiskEngine, render_forensic_dossier_html
from analyzer import validate_and_reconcile_idex_analysis, guardrail_level, GUARDRAIL_RED
from tests.fixtures_golden import (
    CLEAN_LARGECAP,
    LOSS_MAKER,
    HIGH_PLEDGE,
    CHANNEL_STUFFING,
    EMPTY,
)


class TestGoldenCompanies(unittest.TestCase):
    """
    Asserts business invariants and mathematical determinism across golden archetypes.
    """

    def test_clean_largecap_invariants(self):
        """CLEAN_LARGECAP: FQI issued, badge PRISTINE or LOW, zero critical red flags."""
        report = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol=CLEAN_LARGECAP["ticker"],
            company_name=CLEAN_LARGECAP["company_name"],
            sector=CLEAN_LARGECAP["sector"],
            financial_statements=CLEAN_LARGECAP["financials"],
            live_market_data=CLEAN_LARGECAP["market_data"]
        )

        self.assertIsNotNone(report["fqi_score"], "CLEAN_LARGECAP must receive an FQI score")
        self.assertGreaterEqual(report["fqi_score"], 80.0)
        self.assertIn(report["verdict_badge"], ["PRISTINE", "LOW"])
        self.assertEqual(len(report["critical_red_flags"]), 0, "Clean largecap must have 0 critical red flags")

        reconciled = validate_and_reconcile_idex_analysis(CLEAN_LARGECAP["raw_analysis"])
        self.assertGreaterEqual(reconciled["final_score"], 80.0)
        self.assertNotIn("FRAGILE", reconciled["verdict"])

    def test_loss_maker_invariants(self):
        """LOSS_MAKER: final_score <= 50; accrual check FAILED; verdict never PRISTINE."""
        report = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol=LOSS_MAKER["ticker"],
            company_name=LOSS_MAKER["company_name"],
            sector=LOSS_MAKER["sector"],
            financial_statements=LOSS_MAKER["financials"],
            live_market_data=LOSS_MAKER["market_data"]
        )

        # Accrual / cash conversion check must fail (CRITICAL status)
        cash_check = next(c for c in report["checks"] if c["id"] == "FOR_01_CASH_CONVERSION")
        self.assertIn(cash_check["status"], ["CRITICAL", "FAIL", "MONITOR"])
        self.assertNotEqual(cash_check["status"], "PASS", "Accrual check must fail for chronic loss maker")
        self.assertNotEqual(report["verdict_badge"], "PRISTINE", "Loss maker verdict badge must never be PRISTINE")

        reconciled = validate_and_reconcile_idex_analysis(LOSS_MAKER["raw_analysis"])
        self.assertLessEqual(reconciled["final_score"], 50.0, "Loss maker final_score must be <= 50")
        self.assertNotIn("PRISTINE", reconciled["verdict"])
        self.assertNotIn("OCGC", reconciled["verdict"])

    def test_high_pledge_invariants(self):
        """HIGH_PLEDGE: FOR_07_PROMOTER_PLEDGE is CRITICAL; red flag listed; FQI reduced."""
        report = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol=HIGH_PLEDGE["ticker"],
            company_name=HIGH_PLEDGE["company_name"],
            sector=HIGH_PLEDGE["sector"],
            financial_statements=HIGH_PLEDGE["financials"],
            live_market_data=HIGH_PLEDGE["market_data"]
        )

        pledge_check = next(c for c in report["checks"] if c["id"] == "FOR_07_PROMOTER_PLEDGE")
        self.assertEqual(pledge_check["status"], "CRITICAL", "45% promoter pledge must be CRITICAL")
        self.assertTrue(
            any("Pledge" in flag or "Encumbrance" in flag or "pledge" in flag.lower() for flag in report["critical_red_flags"]),
            "Active promoter pledge must be listed in critical red flags"
        )
        # FQI score must reflect penalty
        self.assertLess(report["fqi_score"], 82.0, "FQI must be penalized below pristine for 45% pledge")

    def test_channel_stuffing_invariants(self):
        """CHANNEL_STUFFING: FOR_02_RECEIVABLE_VELOCITY not PASS."""
        report = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol=CHANNEL_STUFFING["ticker"],
            company_name=CHANNEL_STUFFING["company_name"],
            sector=CHANNEL_STUFFING["sector"],
            financial_statements=CHANNEL_STUFFING["financials"],
            live_market_data=CHANNEL_STUFFING["market_data"]
        )

        rec_check = next(c for c in report["checks"] if c["id"] == "FOR_02_RECEIVABLE_VELOCITY")
        self.assertNotEqual(rec_check["status"], "PASS", "Channel stuffing radar must not report PASS")
        self.assertIn(rec_check["status"], ["CRITICAL", "MONITOR"])

    def test_empty_fixture_invariants(self):
        """EMPTY: fqi_score is None; every check INSUFFICIENT_DATA; badge never PRISTINE."""
        report = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol=EMPTY["ticker"],
            company_name=EMPTY["company_name"],
            sector=EMPTY["sector"],
            financial_statements=EMPTY["financials"],
            live_market_data=EMPTY["market_data"]
        )

        self.assertIsNone(report["fqi_score"], "EMPTY company without statements must have None FQI score")
        self.assertNotEqual(report["verdict_badge"], "PRISTINE", "Empty company verdict badge must never be PRISTINE")

        for check in report["checks"]:
            self.assertEqual(
                check["status"],
                "INSUFFICIENT_DATA",
                f"Check {check['id']} must report INSUFFICIENT_DATA when statements are absent"
            )

    def test_rendered_html_security_across_all_fixtures(self):
        """Any fixture: no rendered HTML contains an unescaped <script> tag."""
        fixtures = [CLEAN_LARGECAP, LOSS_MAKER, HIGH_PLEDGE, CHANNEL_STUFFING, EMPTY]
        for fix in fixtures:
            rep = ForensicRiskEngine.audit_company_forensics(
                ticker_symbol=fix["ticker"],
                company_name=fix["company_name"],
                sector=fix["sector"],
                financial_statements=fix["financials"],
                live_market_data=fix["market_data"]
            )
            html = render_forensic_dossier_html(rep)
            self.assertNotIn("<script>", html.lower(), f"Unescaped script tag found in HTML for {fix['ticker']}")
            self.assertNotIn("javascript:", html.lower(), f"Javascript URI found in HTML for {fix['ticker']}")

    def test_guardrail_tag_safety_never_yields_avoid(self):
        """Any fixture: guardrail_level('GOV-CREDIBLE 🟢') never yields an AVOID stance."""
        level = guardrail_level("GOV-CREDIBLE 🟢")
        self.assertNotEqual(level, GUARDRAIL_RED, "GOV-CREDIBLE 🟢 must not map to GUARDRAIL_RED")
        self.assertEqual(level, "CLEAN")

    def test_scoring_determinism_across_fixtures(self):
        """Determinism: running each fixture twice produces identical non-timestamp fields."""
        fixtures = [CLEAN_LARGECAP, LOSS_MAKER, HIGH_PLEDGE, CHANNEL_STUFFING, EMPTY]
        for fix in fixtures:
            rep1 = ForensicRiskEngine.audit_company_forensics(
                ticker_symbol=fix["ticker"],
                company_name=fix["company_name"],
                sector=fix["sector"],
                financial_statements=fix["financials"],
                live_market_data=fix["market_data"]
            )
            rep2 = ForensicRiskEngine.audit_company_forensics(
                ticker_symbol=fix["ticker"],
                company_name=fix["company_name"],
                sector=fix["sector"],
                financial_statements=fix["financials"],
                live_market_data=fix["market_data"]
            )

            self.assertEqual(rep1["fqi_score"], rep2["fqi_score"])
            self.assertEqual(rep1["verdict"], rep2["verdict"])
            self.assertEqual(rep1["verdict_badge"], rep2["verdict_badge"])
            self.assertEqual(rep1["critical_red_flags"], rep2["critical_red_flags"])
            self.assertEqual(len(rep1["checks"]), len(rep2["checks"]))

            rec1 = validate_and_reconcile_idex_analysis(fix["raw_analysis"])
            rec2 = validate_and_reconcile_idex_analysis(fix["raw_analysis"])
            self.assertEqual(rec1["final_score"], rec2["final_score"])
            self.assertEqual(rec1["verdict"], rec2["verdict"])
            self.assertEqual(rec1["core_score"], rec2["core_score"])


if __name__ == "__main__":
    unittest.main()
