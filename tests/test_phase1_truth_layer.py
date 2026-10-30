"""
tests/test_phase1_truth_layer.py
Regression tests for Phase 1 of docs/PHASED_PLAN.md ("Truth layer").

Each test encodes a specific way the app used to lie:
- missing data produced a PASS / perfect score
- "GOV-CREDIBLE" matched the "RED" guardrail via substring search
- a loss-making company passed the accrual check
- "0.00%" pledge text was read as pledged
- the UI claimed DCF, encryption, determinism and 10 pillars
"""

import pathlib
import unittest

from analyzer import (
    GUARDRAIL_CLEAN,
    GUARDRAIL_RED,
    guardrail_level,
    validate_and_reconcile_idex_analysis,
)
from data_integrity_agent import DataIntegritySentinel
from forensic_risk_engine import ForensicRiskEngine, render_forensic_dossier_html

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _raw_analysis(guardrail_tag):
    return {
        "pillars": [{"id": i, "score": 10.0, "justification": "test"} for i in range(1, 9)],
        "guardrail_tag": guardrail_tag,
        "pio_triggered": False,
        "penalties_breakdown": [],
        "bonuses_breakdown": {},
    }


class TestForensicNoFabricatedPasses(unittest.TestCase):
    def test_empty_input_never_scores_or_reports_pristine(self):
        report = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol="XYZ",
            company_name="No Data Ltd.",
            sector="Unknown",
            financial_statements={},
            live_market_data={},
        )

        self.assertIsNone(report["fqi_score"], "Empty input must not produce a numeric FQI")
        self.assertFalse(report["score_issued"])
        self.assertEqual(report["evaluated_count"], 0)
        self.assertEqual(report["insufficient_count"], 8)
        self.assertIn("INSUFFICIENT DATA", report["verdict"])
        self.assertNotEqual(report["verdict_badge"], "PRISTINE")

        for check in report["checks"]:
            self.assertEqual(
                check["status"],
                "INSUFFICIENT_DATA",
                f"{check['id']} fabricated a result from missing data",
            )

    def test_renderer_uses_na_when_score_is_withheld(self):
        report = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol="XYZ",
            company_name="No Data Ltd.",
            sector="Unknown",
            financial_statements={},
            live_market_data={},
        )
        html = render_forensic_dossier_html(report)
        self.assertIn("N/A / 100", html)
        self.assertNotIn("100.0 / 100", html)
        self.assertNotIn("Clean Audit • 0.0% Pledged", html)

    def test_zero_zero_pledge_is_not_flagged(self):
        report = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol="CLEAN",
            company_name="Clean Ltd.",
            sector="Industrials",
            financial_statements={},
            live_market_data={"screener_metrics": {"promoter_pledging": "0.00%"}},
        )
        pledge = next(c for c in report["checks"] if c["id"] == "FOR_07_PROMOTER_PLEDGE")
        self.assertEqual(pledge["status"], "PASS")

    def test_missing_pledge_is_not_assumed_zero(self):
        report = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol="CLEAN",
            company_name="Clean Ltd.",
            sector="Industrials",
            financial_statements={},
            live_market_data={},
        )
        pledge = next(c for c in report["checks"] if c["id"] == "FOR_07_PROMOTER_PLEDGE")
        self.assertEqual(pledge["status"], "INSUFFICIENT_DATA")

    def test_renderer_escapes_injected_check_text(self):
        report = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol="X", company_name="X", sector="X",
            financial_statements={}, live_market_data={},
        )
        report["checks"][0]["detail"] = "<script>alert(1)</script>"
        html = render_forensic_dossier_html(report)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)


class TestGuardrailEnum(unittest.TestCase):
    def test_credible_is_not_red(self):
        self.assertEqual(guardrail_level("GOV-CREDIBLE 🟢"), GUARDRAIL_CLEAN)
        self.assertEqual(guardrail_level("GOV-RED 🔴"), GUARDRAIL_RED)

    def test_credible_tag_does_not_trigger_override(self):
        result = validate_and_reconcile_idex_analysis(_raw_analysis("GOV-CREDIBLE 🟢"))
        self.assertFalse(result["pio_triggered"])
        self.assertGreaterEqual(result["final_score"], 49.0)
        self.assertEqual(result["guardrail_tag"], "GOV-CREDIBLE 🟢")

    def test_red_tag_still_triggers_override(self):
        result = validate_and_reconcile_idex_analysis(_raw_analysis("GOV-RED 🔴"))
        self.assertTrue(result["pio_triggered"])
        self.assertLessEqual(result["final_score"], 49.0)


class TestLossMakingCompany(unittest.TestCase):
    def test_negative_pat_and_negative_cfo_fails_accrual_check(self):
        report = DataIntegritySentinel.audit_and_certify(
            ticker_symbol="LOSS",
            company_name="Loss Maker Ltd.",
            financial_statements={
                "years": ["FY23", "FY24"],
                "pnl": {"Net Profit (PAT)": {"values": [-100.0, -200.0]}},
                "cf": {"Cash from Operations (CFO)": {"values": [-50.0, -120.0]}},
            },
            live_market_data={},
        )
        accrual = next(c for c in report["checks"] if c["id"] == "CHK_03_ACCRUAL_STRESS")
        self.assertEqual(accrual["status"], "FAILED")
        self.assertIsNotNone(report["integrity_score"])
        self.assertLess(report["integrity_score"], 100.0)


class TestNoFalseClaimsInSource(unittest.TestCase):
    FORBIDDEN = [
        "3-Stage DCF",
        "ENCRYPTION &amp; TAMPER GUARD",
        "MATHEMATICAL DETERMINISM VERIFIED",
        "10 governance and financial pillars",
        "compiled on the backend under institutional IP protection",
        # Fraud-shield fallback labels that used to appear without any evidence:
        "CLEAN RECORD",
        "HEALTHY DSO",
        '"SOLVENT"',
        "100% unencumbered",
    ]

    def test_app_source_contains_no_forbidden_claims(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        for claim in self.FORBIDDEN:
            self.assertNotIn(claim, source, f"False claim still present: {claim}")

    def test_pillar_chips_match_canonical_pillars(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        start = source.index("_PILLAR_STYLE = [")
        block = source[start:source.index("]", start)]
        for stale in ("Working Cap", "Capital Allocation"):
            self.assertNotIn(stale, block)

    def test_no_substring_matching_on_guardrail_tags(self):
        """`"RED" in tag` matched "GOV-CREDIBLE". Routing must go through the enum.

        Comments and docstrings are stripped with `tokenize` first, so prose that
        quotes the old bug does not trip the check.
        """
        import io
        import tokenize

        offending = []
        for name in ("app.py", "analyzer.py", "forensic_risk_engine.py", "data_integrity_agent.py"):
            path = ROOT / name
            raw = path.read_text(encoding="utf-8")
            code_tokens = []
            for tok in tokenize.generate_tokens(io.StringIO(raw).readline):
                if tok.type in (tokenize.COMMENT, tokenize.STRING):
                    continue
                code_tokens.append(tok)
            code = tokenize.untokenize(code_tokens)
            for lineno, line in enumerate(code.splitlines(), start=1):
                for pattern in ('"RED" in', '"ALERT" in', '"GOV-RED" in', '"PROM-ALERT" in'):
                    if pattern in line:
                        offending.append(f"{name}: {line.strip()[:90]}")
        self.assertEqual(offending, [], "substring guardrail matching reintroduced:\n" + "\n".join(offending))

    def test_app_routes_red_zones_through_guardrail_level(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertGreaterEqual(
            source.count("analyzer.guardrail_level("), 5,
            "every red/alert decision must use the explicit enum",
        )

    def test_valuation_compass_does_not_invent_a_fair_value(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertNotIn("dcf_mid = round(cmp * 1.06, 0)", source)


class TestForensicCoverageMetadata(unittest.TestCase):
    def test_report_exposes_coverage_and_score_flag(self):
        report = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol="X", company_name="X", sector="X",
            financial_statements={}, live_market_data={},
        )
        for key in ("evaluated_count", "insufficient_count", "coverage", "score_issued"):
            self.assertIn(key, report)
        self.assertEqual(report["coverage"], 0.0)
        self.assertFalse(report["score_issued"])


if __name__ == "__main__":
    unittest.main()
