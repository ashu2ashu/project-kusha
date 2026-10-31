"""
test_financial_invariants_suite.py
Permanent Financial Research Regression Suite for Project KUSHA / StockSage.
Framework: IDEX-7.5SC Hybrid Pro

Verifies invariant physical and arithmetic properties across:
1. Accounting Consistency: Balance-sheet equation, Cash-flow reconciliation, PAT vs CFO divergence, Accruals.
2. Receivables & Working Capital: Debtor days velocity, Channel stuffing detection, Provisioning coverage.
3. Promoter & Governance Integrity: Auditor resignation, Regulatory enforcement, Related-party misuse, Pledge spikes.
4. Scoring Mathematical Invariants: Pillar score limits, Penalty cap (-7.5), Bonus cap (+10%), PIO override enforcement.
5. Synthetic & Historical Edge-Case Fixtures: Conglomerate, NBFC/Banking, Early-stage growth, Cyclical turnaround, Distressed/NPA.
"""

import unittest
import math
import copy
from typing import Dict, Any, List

from data_integrity_agent import DataIntegritySentinel
from forensic_risk_engine import ForensicRiskEngine
from analyzer import validate_and_reconcile_idex_analysis, CANONICAL_PILLARS


class TestAccountingConsistencyInvariants(unittest.TestCase):
    """
    Validates arithmetic and physical accounting invariants:
    - Assets >= Liabilities + Equity (Balance Sheet Identity)
    - Free Cash Flow = CFO - Capex
    - PAT vs CFO cash conversion and negative cash divergence
    - Structural hierarchy: Sales >= PAT under regular operations
    """

    def test_balance_sheet_equation_valid(self):
        """Clean balance sheet where Total Assets covers Net Worth and Liabilities."""
        statements = {
            "bs": {
                "Total Net Worth / Equity": {"values": [1000.0, 1200.0, 1400.0]},
                "Total Liabilities & Assets": {"values": [2500.0, 2800.0, 3200.0]}
            },
            "years": ["FY23", "FY24", "FY25"]
        }
        res = DataIntegritySentinel.audit_and_certify("TESTCO", "Test Co", financial_statements=statements)
        chk = next(c for c in res["checks"] if c["id"] == "CHK_01_BS_EQUATION")
        self.assertEqual(chk["status"], "PASSED")
        self.assertTrue(chk["passed"])

    def test_balance_sheet_equation_anomaly_net_worth_exceeds_assets(self):
        """Violation: Reported Net Worth exceeds Total Assets (impossible accounting identity)."""
        statements = {
            "bs": {
                "Total Net Worth / Equity": {"values": [1000.0, 1200.0, 5000.0]},
                "Total Liabilities & Assets": {"values": [2500.0, 2800.0, 3000.0]}  # 5000 > 3000 * 1.05
            },
            "years": ["FY23", "FY24", "FY25"]
        }
        res = DataIntegritySentinel.audit_and_certify("TESTCO", "Test Co", financial_statements=statements)
        chk = next(c for c in res["checks"] if c["id"] == "CHK_01_BS_EQUATION")
        self.assertEqual(chk["status"], "FAILED")
        self.assertFalse(chk["passed"])
        self.assertIn("Anomalous equation", chk["detail"])

    def test_cash_flow_reconciliation_valid(self):
        """Free Cash Flow reconciles with CFO - Capex within standard tolerance."""
        statements = {
            "cf": {
                "Cash from Operations (CFO)": {"values": [500.0, 600.0, 800.0]},
                "Capital Expenditure (Capex)": {"values": [-200.0, -250.0, -300.0]},
                "Free Cash Flow (FCF)": {"values": [300.0, 350.0, 500.0]}  # 800 - 300 = 500
            },
            "years": ["FY23", "FY24", "FY25"]
        }
        res = DataIntegritySentinel.audit_and_certify("TESTCO", "Test Co", financial_statements=statements)
        chk = next(c for c in res["checks"] if c["id"] == "CHK_02_CF_RECONCILE")
        self.assertEqual(chk["status"], "PASSED")
        self.assertTrue(chk["passed"])

    def test_cash_flow_reconciliation_variance_detected(self):
        """Discrepancy: Reported FCF diverges significantly from CFO - Capex."""
        statements = {
            "cf": {
                "Cash from Operations (CFO)": {"values": [500.0, 600.0, 800.0]},
                "Capital Expenditure (Capex)": {"values": [-200.0, -250.0, -300.0]},
                "Free Cash Flow (FCF)": {"values": [300.0, 350.0, 150.0]}  # Expected 500, reported 150 (diff 350)
            },
            "years": ["FY23", "FY24", "FY25"]
        }
        res = DataIntegritySentinel.audit_and_certify("TESTCO", "Test Co", financial_statements=statements)
        chk = next(c for c in res["checks"] if c["id"] == "CHK_02_CF_RECONCILE")
        self.assertEqual(chk["status"], "FAILED")
        self.assertFalse(chk["passed"])
        self.assertIn("Variance detected", chk["detail"])

    def test_earnings_quality_negative_cfo_with_positive_pat(self):
        """Divergence: High positive Net Profit (PAT) but Operating Cash Flow is negative."""
        statements = {
            "pnl": {
                "Net Profit (PAT)": {"values": [200.0, 300.0, 500.0]}
            },
            "cf": {
                "Cash from Operations (CFO)": {"values": [150.0, 200.0, -120.0]}
            },
            "years": ["FY23", "FY24", "FY25"]
        }
        res = DataIntegritySentinel.audit_and_certify("TESTCO", "Test Co", financial_statements=statements)
        chk = next(c for c in res["checks"] if c["id"] == "CHK_03_ACCRUAL_STRESS")
        self.assertEqual(chk["status"], "FAILED")
        self.assertFalse(chk["passed"])
        self.assertIn("Negative CFO Divergence", chk["detail"])

    def test_pnl_structural_hierarchy_pat_exceeds_revenue(self):
        """Anomaly: Reported Net Profit exceeds Total Revenue."""
        statements = {
            "pnl": {
                "Sales / Total Revenue": {"values": [1000.0, 1200.0, 1500.0]},
                "Net Profit (PAT)": {"values": [100.0, 150.0, 2000.0]}  # 2000 > 1500
            },
            "years": ["FY23", "FY24", "FY25"]
        }
        res = DataIntegritySentinel.audit_and_certify("TESTCO", "Test Co", financial_statements=statements)
        chk = next(c for c in res["checks"] if c["id"] == "CHK_04_PNL_HIERARCHY")
        self.assertEqual(chk["status"], "FAILED")
        self.assertFalse(chk["passed"])
        self.assertIn("Hierarchy anomaly", chk["detail"])


class TestReceivablesAndWorkingCapitalInvariants(unittest.TestCase):
    """
    Validates working capital stress and channel stuffing radar:
    - Receivables growth outpacing revenue growth (>18% spread)
    - Working capital cash trapping (sub-60% cumulative CFO/PAT)
    - Long-term cash generation resilience
    """

    def test_channel_stuffing_radar_critical(self):
        """Critical alert when trade receivables expand substantially faster than sales."""
        statements = {
            "pnl": {
                "Sales / Total Revenue": {"values": [1000.0, 1050.0]},  # +5% YoY
                "Net Profit (PAT)": {"values": [100.0, 110.0]}
            },
            "bs": {
                "Trade Receivables": {"values": [200.0, 300.0]},  # +50% YoY -> Spread = 45% (>18%)
                "Total Liabilities & Assets": {"values": [1500.0, 1700.0]}
            },
            "cf": {
                "Cash from Operations (CFO)": {"values": [90.0, 95.0]}
            },
            "cagr": {"sales_cagr": 5.0},
            "years": ["FY24", "FY25"]
        }
        res = ForensicRiskEngine.audit_company_forensics("CHANNEL_CO", "Channel Test Ltd", "Manufacturing", financial_statements=statements)
        rec_chk = next(c for c in res["checks"] if c["id"] == "FOR_02_RECEIVABLE_VELOCITY")
        self.assertEqual(rec_chk["status"], "CRITICAL")
        self.assertIn("Channel Stuffing Alert", rec_chk["detail"])
        self.assertIn("Receivables Expansion Outpacing Revenue", res["critical_red_flags"][0])

    def test_working_capital_cash_trapping_low_conversion(self):
        """Severe cash trapping alert when multi-year cumulative CFO is < 60% of PAT."""
        statements = {
            "pnl": {
                "Sales / Total Revenue": {"values": [1000.0, 1200.0, 1400.0]},
                "Net Profit (PAT)": {"values": [200.0, 250.0, 300.0]}  # Cum PAT = 750
            },
            "cf": {
                "Cash from Operations (CFO)": {"values": [100.0, 120.0, 150.0]}  # Cum CFO = 370 -> 49.3% (<60%)
            },
            "years": ["FY23", "FY24", "FY25"]
        }
        res = ForensicRiskEngine.audit_company_forensics("TRAP_CO", "Trapped Cash Ltd", "Services", financial_statements=statements)
        cf_chk = next(c for c in res["checks"] if c["id"] == "FOR_01_CASH_CONVERSION")
        self.assertEqual(cf_chk["status"], "CRITICAL")
        self.assertIn("Weak Cash Conversion", cf_chk["detail"])

    def test_harmonious_collections_and_pristine_conversion(self):
        """Clean collections and pristine cash conversion (CFO >= 80% of PAT)."""
        statements = {
            "pnl": {
                "Sales / Total Revenue": {"values": [1000.0, 1200.0]},  # +20%
                "Net Profit (PAT)": {"values": [150.0, 180.0]}  # Cum PAT = 330
            },
            "bs": {
                "Trade Receivables": {"values": [120.0, 140.0]}  # +16.7%
            },
            "cf": {
                "Cash from Operations (CFO)": {"values": [150.0, 190.0]}  # Cum CFO = 340 -> 103%
            },
            "years": ["FY24", "FY25"]
        }
        res = ForensicRiskEngine.audit_company_forensics("CLEAN_CO", "Pristine Collections Ltd", "Technology", financial_statements=statements)
        rec_chk = next(c for c in res["checks"] if c["id"] == "FOR_02_RECEIVABLE_VELOCITY")
        cf_chk = next(c for c in res["checks"] if c["id"] == "FOR_01_CASH_CONVERSION")
        self.assertEqual(rec_chk["status"], "PASS")
        self.assertEqual(cf_chk["status"], "PASS")


class TestPromoterAndGovernanceIntegrityInvariants(unittest.TestCase):
    """
    Validates Promoter Integrity Override (PIO) and governance invariants:
    - Mandatory PIO triggering on GOV-RED 🔴 or severe governance breach
    - Pillar 1 (Corporate Governance) clamping strictly <= 6.0 / 20.0
    - Complete zeroing of all bonus categories under PIO
    - Strict score ceiling (< 50.0, maximum 49.0)
    - Position sizing locked to 0%
    - Model outputs cannot bypass PIO or unclamp Pillar 1
    """

    def setUp(self):
        self.valid_raw_pillars = [
            {"id": p["id"], "name": p["name"], "score": p["max_score"] * 0.9, "justification": "Robust"}
            for p in CANONICAL_PILLARS
        ]

    def test_pio_trigger_enforces_pillar1_clamp(self):
        """When PIO is triggered, Pillar 1 (Corporate Governance) is clamped to <= 6.0."""
        raw = {
            "pillars": copy.deepcopy(self.valid_raw_pillars),
            "pio_triggered": True,
            "pio_reason": "Auditor resignation following adverse CARO qualifications.",
            "guardrail_tag": "GOV-RED 🔴",
            "penalties_breakdown": [],
            "bonuses_breakdown": {"cool_pro_bonus": 5.0, "trajectory_bonus": 3.0}
        }
        # Pillar 1 was initially 18.0 (90% of 20)
        reconciled = validate_and_reconcile_idex_analysis(raw)
        p1 = next(p for p in reconciled["pillars"] if p["id"] == 1)
        self.assertLessEqual(p1["score"], 6.0)
        self.assertEqual(reconciled["guardrail_tag"], "GOV-RED 🔴")
        self.assertTrue(reconciled["pio_triggered"])

    def test_pio_trigger_zeroes_all_bonuses(self):
        """Under PIO, cool_pro, trajectory, resilience, and total bonus must all be exactly 0.0."""
        raw = {
            "pillars": copy.deepcopy(self.valid_raw_pillars),
            "pio_triggered": True,
            "pio_reason": "SEBI investigation into related party diversion.",
            "guardrail_tag": "GOV-RED 🔴",
            "penalties_breakdown": [],
            "bonuses_breakdown": {
                "cool_pro_bonus": 8.0,
                "trajectory_bonus": 4.0,
                "resilience_bonus": 2.0
            }
        }
        reconciled = validate_and_reconcile_idex_analysis(raw)
        bonuses = reconciled["bonuses_breakdown"]
        self.assertEqual(bonuses["cool_pro_bonus"], 0.0)
        self.assertEqual(bonuses["trajectory_bonus"], 0.0)
        self.assertEqual(bonuses["resilience_bonus"], 0.0)
        self.assertEqual(bonuses["total_bonus_applied"], 0.0)

    def test_pio_trigger_caps_final_score_below_50(self):
        """Under PIO, final score cannot exceed 49.0 regardless of other pillars."""
        raw = {
            "pillars": copy.deepcopy(self.valid_raw_pillars),
            "pio_triggered": True,
            "pio_reason": "Severe promoter pledge spike and debt default.",
            "guardrail_tag": "GOV-RED 🔴",
            "penalties_breakdown": [],
            "bonuses_breakdown": {}
        }
        reconciled = validate_and_reconcile_idex_analysis(raw)
        self.assertLessEqual(reconciled["final_score"], 49.0)
        self.assertIn("FRAGILE", reconciled["verdict"])
        self.assertEqual(reconciled["risk_tier"], "Elevated Caution")

    def test_gov_red_tag_automatically_activates_pio(self):
        """Even if pio_triggered is falsely set to False by model, GOV-RED tag deterministically forces PIO."""
        raw = {
            "pillars": copy.deepcopy(self.valid_raw_pillars),
            "pio_triggered": False,  # Hallucinated or injected False
            "guardrail_tag": "GOV-RED 🔴",
            "penalties_breakdown": [],
            "bonuses_breakdown": {"cool_pro_bonus": 4.0}
        }
        reconciled = validate_and_reconcile_idex_analysis(raw)
        self.assertTrue(reconciled["pio_triggered"])
        self.assertLessEqual(reconciled["final_score"], 49.0)
        self.assertEqual(reconciled["bonuses_breakdown"]["total_bonus_applied"], 0.0)


class TestScoringMathematicalInvariants(unittest.TestCase):
    """
    Validates strict mathematical boundaries of IDEX-7.5SC framework:
    - 8 canonical pillars exactly
    - Each pillar clamped strictly to [0.0, max_score]
    - Core score is strictly the sum of the 8 clamped pillars
    - Penalties capped strictly at -7.5 points maximum
    - Bonuses capped strictly at +10% of core score maximum
    - Final score bounded in [0.0, 100.0]
    - Position sizing and verdict bands align with score ranges
    """

    def setUp(self):
        self.perfect_pillars = [
            {"id": p["id"], "name": p["name"], "score": p["max_score"], "justification": "Perfect"}
            for p in CANONICAL_PILLARS
        ]

    def test_schema_requires_exactly_8_pillars(self):
        """Fails fast with ValueError if fewer than 8 pillars are supplied."""
        raw = {"pillars": [{"id": 1, "name": "Gov", "score": 10.0}]}
        with self.assertRaises(ValueError):
            validate_and_reconcile_idex_analysis(raw)

    def test_pillar_score_cannot_exceed_canonical_maximum(self):
        """If model hallucinates a score higher than pillar max, it is clamped to max."""
        inflated_pillars = copy.deepcopy(self.perfect_pillars)
        inflated_pillars[0]["score"] = 999.0  # Pillar 1 max is 20.0
        inflated_pillars[1]["score"] = 50.0   # Pillar 2 max is 20.0

        raw = {
            "pillars": inflated_pillars,
            "guardrail_tag": "GOV-CLEAN 🟢",
            "penalties_breakdown": [],
            "bonuses_breakdown": {}
        }
        reconciled = validate_and_reconcile_idex_analysis(raw)
        p1 = next(p for p in reconciled["pillars"] if p["id"] == 1)
        p2 = next(p for p in reconciled["pillars"] if p["id"] == 2)
        self.assertEqual(p1["score"], 20.0)
        self.assertEqual(p2["score"], 20.0)

    def test_pillar_score_cannot_be_negative_or_nan(self):
        """Pillar score cannot be negative, NaN, or infinite."""
        corrupt_pillars = copy.deepcopy(self.perfect_pillars)
        corrupt_pillars[0]["score"] = -15.0
        corrupt_pillars[1]["score"] = float("nan")

        raw = {
            "pillars": corrupt_pillars,
            "guardrail_tag": "GOV-CLEAN 🟢",
            "penalties_breakdown": [],
            "bonuses_breakdown": {}
        }
        reconciled = validate_and_reconcile_idex_analysis(raw)
        p1 = next(p for p in reconciled["pillars"] if p["id"] == 1)
        p2 = next(p for p in reconciled["pillars"] if p["id"] == 2)
        self.assertEqual(p1["score"], 0.0)
        self.assertEqual(p2["score"], 0.0)

    def test_penalty_hard_cap_minus_7_5(self):
        """Total penalties can NEVER exceed -7.5 points, even with massive individual deductions."""
        raw = {
            "pillars": copy.deepcopy(self.perfect_pillars),
            "guardrail_tag": "GOV-CLEAN 🟢",
            "penalties_breakdown": [
                {"penalty_name": "Risk 1", "points": -5.0},
                {"penalty_name": "Risk 2", "points": -5.0},
                {"penalty_name": "Risk 3", "points": -10.0}
            ],
            "bonuses_breakdown": {}
        }
        reconciled = validate_and_reconcile_idex_analysis(raw)
        self.assertEqual(reconciled["total_penalties"], -7.5)
        # 100 core - 7.5 = 92.5
        self.assertEqual(reconciled["final_score"], 92.5)

    def test_bonus_hard_cap_10_percent_of_core(self):
        """Total bonus can NEVER exceed 10% of core score."""
        mid_pillars = [
            {"id": p["id"], "name": p["name"], "score": p["max_score"] * 0.5, "justification": "Mid"}
            for p in CANONICAL_PILLARS
        ]
        # Core score = 50.0. Max allowed bonus is 10% of 50.0 = 5.0.
        raw = {
            "pillars": mid_pillars,
            "guardrail_tag": "GOV-CLEAN 🟢",
            "penalties_breakdown": [],
            "bonuses_breakdown": {
                "cool_pro_bonus": 8.0,
                "trajectory_bonus": 4.0,
                "resilience_bonus": 2.0
            }
        }
        reconciled = validate_and_reconcile_idex_analysis(raw)
        self.assertEqual(reconciled["core_score"], 50.0)
        self.assertEqual(reconciled["bonuses_breakdown"]["total_bonus_applied"], 5.0)
        self.assertEqual(reconciled["final_score"], 55.0)

    def test_verdict_band_consistency(self):
        """Verifies deterministic mapping of final score to official IDEX verdict bands."""
        bands = [
            (95.0, "OCGC (≥90)", "Constructive"),
            (88.0, "PCGC (85–89)", "Constructive"),
            (80.0, "QTC (75–84)", "Monitored"),
            (68.0, "VTC (60–74)", "Monitored"),
            (55.0, "STC (50–59)", "Elevated Caution"),
            (42.0, "FRAGILE (<50)", "Elevated Caution")
        ]
        for target_score, expected_verdict_prefix, expected_tier in bands:
            scale = target_score / 100.0
            pillars = [
                {"id": p["id"], "name": p["name"], "score": p["max_score"] * scale, "justification": "Scale"}
                for p in CANONICAL_PILLARS
            ]
            raw = {
                "pillars": pillars,
                "guardrail_tag": "GOV-CLEAN 🟢",
                "penalties_breakdown": [],
                "bonuses_breakdown": {}
            }
            res = validate_and_reconcile_idex_analysis(raw)
            self.assertIn(expected_verdict_prefix, res["verdict"])
            self.assertEqual(res["risk_tier"], expected_tier)


class TestSyntheticAndEdgeCaseFixtures(unittest.TestCase):
    """
    Validates behavioral correctness against real-world complex corporate profiles:
    - Fixture 1: Conglomerate with high subsidiary debt & multi-tier entities
    - Fixture 2: NBFC / Banking entity with provisioning stress
    - Fixture 3: Early-stage high-growth firm with negative CFO but legitimate Capex
    - Fixture 4: Cyclical turnaround company recovering from base-year losses
    - Fixture 5: Distressed firm with adverse auditor remarks & promoter pledge spike
    """

    def test_fixture_1_conglomerate_high_debt(self):
        """Conglomerate with elevated debt-to-equity and steady cash flow."""
        statements = {
            "pnl": {
                "Sales / Total Revenue": {"values": [50000.0, 58000.0, 65000.0]},
                "Net Profit (PAT)": {"values": [4000.0, 4800.0, 5500.0]}
            },
            "bs": {
                "Total Net Worth / Equity": {"values": [30000.0, 35000.0, 40000.0]},
                "Total Liabilities & Assets": {"values": [90000.0, 105000.0, 120000.0]},
                "Trade Receivables": {"values": [4000.0, 4600.0, 5100.0]}
            },
            "cf": {
                "Cash from Operations (CFO)": {"values": [4200.0, 5000.0, 5800.0]},
                "Capital Expenditure (Capex)": {"values": [-3000.0, -3500.0, -3800.0]},
                "Free Cash Flow (FCF)": {"values": [1200.0, 1500.0, 2000.0]}
            },
            "cagr": {"sales_cagr": 14.0},
            "years": ["FY23", "FY24", "FY25"]
        }
        market = {"current_price": 2500.0, "high_52w": 2800.0, "low_52w": 2200.0}
        res_sentinel = DataIntegritySentinel.audit_and_certify("CONGLOMERATE", "Conglomerate Ltd", statements, live_market_data=market)
        res_forensics = ForensicRiskEngine.audit_company_forensics("CONGLOMERATE", "Conglomerate Ltd", "Conglomerate", statements)

        # Sentinel: All 6 equations reconcile cleanly when market data provided
        self.assertEqual(res_sentinel["status"], "CONSISTENCY CHECKS PASSED 🟢")
        self.assertTrue(res_sentinel["can_score"])
        self.assertTrue(res_sentinel["all_passed"])

        # Also verify Sentinel handling when market data is absent
        res_partial = DataIntegritySentinel.audit_and_certify("CONGLOMERATE", "Conglomerate Ltd", statements)
        self.assertEqual(res_partial["status"], "PARTIALLY EVALUATED 🟡")
        self.assertTrue(res_partial["can_score"])

        # Forensics: Cash conversion is healthy
        cf_chk = next(c for c in res_forensics["checks"] if c["id"] == "FOR_01_CASH_CONVERSION")
        self.assertEqual(cf_chk["status"], "PASS")

    def test_fixture_2_nbfc_banking_profile(self):
        """NBFC/Banking entity with zero inventory and receivables as loan assets."""
        statements = {
            "pnl": {
                "Sales / Total Revenue": {"values": [12000.0, 14500.0, 17000.0]},
                "Net Profit (PAT)": {"values": [2200.0, 2800.0, 3400.0]}
            },
            "bs": {
                "Total Net Worth / Equity": {"values": [15000.0, 18000.0, 21500.0]},
                "Total Liabilities & Assets": {"values": [80000.0, 95000.0, 110000.0]}
            },
            "cf": {
                "Cash from Operations (CFO)": {"values": [2000.0, 2600.0, 3200.0]},
                "Capital Expenditure (Capex)": {"values": [-100.0, -120.0, -150.0]},
                "Free Cash Flow (FCF)": {"values": [1900.0, 2480.0, 3050.0]}
            },
            "years": ["FY23", "FY24", "FY25"]
        }
        market = {"current_price": 450.0, "high_52w": 520.0, "low_52w": 380.0}
        res = DataIntegritySentinel.audit_and_certify("NBFC_TEST", "NBFC Finance Ltd", statements, live_market_data=market)
        self.assertEqual(res["status"], "CONSISTENCY CHECKS PASSED 🟢")
        self.assertTrue(res["can_score"])

    def test_fixture_3_early_stage_high_growth(self):
        """Early stage high-growth: Rapid revenue growth, heavy Capex, negative FCF."""
        statements = {
            "pnl": {
                "Sales / Total Revenue": {"values": [100.0, 250.0, 600.0]},  # >100% CAGR
                "Net Profit (PAT)": {"values": [10.0, 25.0, 60.0]}
            },
            "bs": {
                "Total Net Worth / Equity": {"values": [200.0, 400.0, 800.0]},
                "Total Liabilities & Assets": {"values": [250.0, 500.0, 1000.0]},
                "Trade Receivables": {"values": [15.0, 35.0, 80.0]}
            },
            "cf": {
                "Cash from Operations (CFO)": {"values": [8.0, 20.0, 50.0]},
                "Capital Expenditure (Capex)": {"values": [-50.0, -120.0, -200.0]},
                "Free Cash Flow (FCF)": {"values": [-42.0, -100.0, -150.0]}  # Legitimate negative FCF due to Capex
            },
            "cagr": {"sales_cagr": 145.0},
            "years": ["FY23", "FY24", "FY25"]
        }
        market = {"current_price": 120.0, "high_52w": 150.0, "low_52w": 90.0}
        res = DataIntegritySentinel.audit_and_certify("GROWTH_CO", "Tech Hypergrowth Ltd", statements, live_market_data=market)
        self.assertEqual(res["status"], "CONSISTENCY CHECKS PASSED 🟢")
        chk = next(c for c in res["checks"] if c["id"] == "CHK_02_CF_RECONCILE")
        self.assertTrue(chk["passed"])

    def test_fixture_4_cyclical_turnaround(self):
        """Cyclical turnaround: Negative base year PAT, recovering sharply in current fiscal."""
        statements = {
            "pnl": {
                "Sales / Total Revenue": {"values": [5000.0, 4800.0, 6200.0]},
                "Net Profit (PAT)": {"values": [-300.0, -50.0, 400.0]}  # Rebound
            },
            "bs": {
                "Total Net Worth / Equity": {"values": [2000.0, 1950.0, 2350.0]},
                "Total Liabilities & Assets": {"values": [6000.0, 5800.0, 6500.0]}
            },
            "cf": {
                "Cash from Operations (CFO)": {"values": [50.0, 100.0, 420.0]},
                "Capital Expenditure (Capex)": {"values": [-100.0, -80.0, -120.0]},
                "Free Cash Flow (FCF)": {"values": [-50.0, 20.0, 300.0]}
            },
            "years": ["FY23", "FY24", "FY25"]
        }
        market = {"current_price": 180.0, "high_52w": 210.0, "low_52w": 140.0}
        res = DataIntegritySentinel.audit_and_certify("TURNAROUND_CO", "Cyclical Steel Ltd", statements, live_market_data=market)
        self.assertEqual(res["status"], "CONSISTENCY CHECKS PASSED 🟢")
        accrual_chk = next(c for c in res["checks"] if c["id"] == "CHK_03_ACCRUAL_STRESS")
        self.assertTrue(accrual_chk["passed"])

    def test_fixture_5_distressed_npa_auditor_resignation(self):
        """Distressed firm: Severe PIO triggered, auditor resignation, negative cash, capped <50."""
        raw = {
            "pillars": [
                {"id": 1, "name": "Corporate Governance & Promoter Integrity", "score": 18.0, "justification": "Pre-adjustment"},
                {"id": 2, "name": "Business Model, Moat & Market Dominance", "score": 12.0, "justification": "Eroding"},
                {"id": 3, "name": "Capital Allocation & Historical ROIC", "score": 10.0, "justification": "Sub-par"},
                {"id": 4, "name": "Forensic Accounting & Cash Flow Reality", "score": 8.0, "justification": "Negative cash"},
                {"id": 5, "name": "Balance Sheet Conservatism & Debt Profile", "score": 4.0, "justification": "High leverage"},
                {"id": 6, "name": "Growth Runway & Reinvestment Optionality", "score": 5.0, "justification": "Stagnant"},
                {"id": 7, "name": "Sector Tailwinds & Fragility", "score": 5.0, "justification": "Regulatory headwind"},
                {"id": 8, "name": "Management Guidance & Truthfulness Track Record", "score": 2.0, "justification": "Missed targets"}
            ],
            "pio_triggered": True,
            "pio_reason": "Statutory auditor resignation mid-year citing lack of disclosures on related-party loans.",
            "guardrail_tag": "GOV-RED 🔴",
            "penalties_breakdown": [
                {"penalty_name": "Auditor Resignation", "points": -5.0},
                {"penalty_name": "Promoter Pledge Spike", "points": -2.5}
            ],
            "bonuses_breakdown": {"cool_pro_bonus": 5.0}
        }
        reconciled = validate_and_reconcile_idex_analysis(raw)
        self.assertTrue(reconciled["pio_triggered"])
        self.assertLessEqual(reconciled["pillars"][0]["score"], 6.0)
        self.assertEqual(reconciled["bonuses_breakdown"]["total_bonus_applied"], 0.0)
        self.assertEqual(reconciled["total_penalties"], -7.5)
        self.assertLessEqual(reconciled["final_score"], 49.0)
        self.assertIn("FRAGILE", reconciled["verdict"])
        self.assertEqual(reconciled["risk_tier"], "Elevated Caution")


if __name__ == "__main__":
    unittest.main()
