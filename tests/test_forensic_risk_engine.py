"""
tests/test_forensic_risk_engine.py
Unit tests for Institutional Forensic Due Diligence & Concealed Risk Audit Engine.
"""

import unittest
from forensic_risk_engine import ForensicRiskEngine, render_forensic_dossier_html


class TestForensicRiskEngine(unittest.TestCase):

    def setUp(self):
        self.healthy_fin = {
            "years": ["Mar 2022", "Mar 2023", "Mar 2024", "Mar 2025"],
            "pnl": {
                "Sales / Total Revenue": {"values": [8000.0, 9500.0, 11000.0, 12500.0]},
                "Profit Before Tax (PBT)": {"values": [1200.0, 1500.0, 1800.0, 2100.0]},
                "Tax Provision": {"values": [300.0, 375.0, 450.0, 525.0]},
                "Net Profit (PAT)": {"values": [900.0, 1125.0, 1350.0, 1575.0]},
                "Other Income": {"values": [60.0, 75.0, 90.0, 110.0]}
            },
            "bs": {
                "Fixed Assets (Net PPE)": {"values": [2500.0, 2800.0, 3100.0, 3400.0]},
                "Capital WIP": {"values": [100.0, 120.0, 150.0, 180.0]},
                "Current & Other Assets": {"values": [3000.0, 3400.0, 3800.0, 4200.0]}
            },
            "cf": {
                "Cash from Operations (CFO)": {"values": [850.0, 1100.0, 1300.0, 1550.0]},
                "Free Cash Flow (FCF)": {"values": [600.0, 800.0, 950.0, 1150.0]}
            },
            "cagr": {
                "sales_cagr": 16.0,
                "pat_cagr": 20.0,
                "latest_roe": 22.0
            }
        }
        self.healthy_live = {
            "current_price": 4500.0,
            "market_cap_cr": 85000.0,
            "pe_ratio": 42.0,
            "high_52w": 4800.0,
            "debt_to_equity": 0.05,
            "screener_metrics": {"promoter_pledging": "0.0%"}
        }

    def test_pristine_company_audit(self):
        """Verify that a pristine company receives high FQI and PRISTINE verdict with 0 red flags."""
        rep = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol="ABB",
            company_name="ABB India Ltd.",
            sector="Capital Goods",
            financial_statements=self.healthy_fin,
            live_market_data=self.healthy_live
        )
        self.assertGreaterEqual(rep["fqi_score"], 85.0)
        self.assertEqual(rep["verdict_badge"], "PRISTINE")
        self.assertEqual(len(rep["critical_red_flags"]), 0)
        self.assertEqual(rep["total_checks"], 8)
        self.assertEqual(rep["passed_count"], 8)

    def test_detects_negative_cash_conversion_divergence(self):
        """Verify that negative cumulative CFO triggers a CRITICAL red flag."""
        divergent_fin = dict(self.healthy_fin)
        divergent_fin["cf"] = {
            "Cash from Operations (CFO)": {"values": [-200.0, -150.0, -300.0, -400.0]}
        }
        rep = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol="RISKY",
            company_name="Risky Paper Profits Ltd.",
            sector="Industrials",
            financial_statements=divergent_fin,
            live_market_data=self.healthy_live
        )
        self.assertLess(rep["fqi_score"], 80.0)
        self.assertTrue(any("Negative Cumulative Cash Flow Divergence" in f for f in rep["critical_red_flags"]))
        cfo_check = next(c for c in rep["checks"] if c["id"] == "FOR_01_CASH_CONVERSION")
        self.assertEqual(cfo_check["status"], "CRITICAL")

    def test_detects_channel_stuffing_velocity(self):
        """Verify that receivables growth outpacing sales growth triggers CRITICAL alert."""
        stuffing_fin = dict(self.healthy_fin)
        # Sales grows 2%, but receivables grow 45%
        stuffing_fin["pnl"] = dict(self.healthy_fin["pnl"])
        stuffing_fin["pnl"]["Sales / Total Revenue"] = {"values": [10000.0, 10200.0]}
        stuffing_fin["bs"] = dict(self.healthy_fin["bs"])
        stuffing_fin["bs"]["Current & Other Assets"] = {"values": [2000.0, 2900.0]}

        rep = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol="STUFFCO",
            company_name="Channel Stuffer Ltd.",
            sector="Consumer",
            financial_statements=stuffing_fin,
            live_market_data=self.healthy_live
        )
        self.assertTrue(any("Receivables Expansion Outpacing Revenue" in f for f in rep["critical_red_flags"]))
        rec_check = next(c for c in rep["checks"] if c["id"] == "FOR_02_RECEIVABLE_VELOCITY")
        self.assertEqual(rec_check["status"], "CRITICAL")

    def test_detects_abnormally_low_tax_rate(self):
        """Verify effective tax rate < 12% triggers tax divergence flag."""
        tax_fin = dict(self.healthy_fin)
        tax_fin["pnl"] = dict(self.healthy_fin["pnl"])
        tax_fin["pnl"]["Profit Before Tax (PBT)"] = {"values": [1000.0, 2000.0]}
        tax_fin["pnl"]["Tax Provision"] = {"values": [50.0, 100.0]}  # 5% tax rate

        rep = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol="TAXLEAK",
            company_name="Tax Leakage Corp",
            sector="Technology",
            financial_statements=tax_fin,
            live_market_data=self.healthy_live
        )
        self.assertTrue(any("Abnormally Low Effective Tax Rate" in f for f in rep["critical_red_flags"]))
        tax_check = next(c for c in rep["checks"] if c["id"] == "FOR_04_TAX_DIVERGENCE")
        self.assertEqual(tax_check["status"], "CRITICAL")

    def test_render_forensic_dossier_html(self):
        """Verify HTML rendering contains all institutional badges and checks."""
        rep = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol="ABB",
            company_name="ABB India Ltd.",
            sector="Capital Goods",
            financial_statements=self.healthy_fin,
            live_market_data=self.healthy_live
        )
        html = render_forensic_dossier_html(rep)
        self.assertIn("Institutional Forensic Due Diligence & Concealed Risk Audit", html)
        self.assertIn("Forensic Quality Index", html)
        self.assertIn("Credit Rating Agency Surveillance", html)
        self.assertIn("Cash Conversion Quality", html)
        self.assertIn("Channel Stuffing Radar", html)
        self.assertIn("Capital WIP Aging", html)
        self.assertIn("Cash Tax Alignment", html)


if __name__ == "__main__":
    unittest.main()
