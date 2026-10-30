"""
test_phase2_data_layer.py
Unit tests for Phase 2: Data Layer remediation of Project KUSHA / StockSage.

Covers:
1. fetch_live_indices_data() with provider blocked -> stale_reference with valid as_of date.
2. fetch_live_indices_data() with successful download -> live status with ISO as_of date.
3. fetch_marquee_stocks_data() fallback -> sample_fallback with non-empty as_of.
4. get_peers_for_company() with unknown ticker -> all valuation metrics are None.
5. Peer selection strictly same-sector -> no silent cross-sector peer substitution.
6. Mixed-period head-to-head comparison -> warning banner present and leader badges suppressed.
7. Single-period head-to-head comparison -> renders normally with leader badges.
8. Audit ledger isolation -> dry-run loop leaves repository ledger files byte-identical.
9. NIFTY_50_DATA schema integrity -> exactly 50 constituents each with all canonical keys.
10. Fiscal period statement alignment -> CFO/PAT pairing matches exact overlapping years only.
"""

import unittest
import os
import hashlib
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import pandas as pd

from nifty_universe import (
    fetch_live_indices_data,
    fetch_marquee_stocks_data,
    INDICES_REFERENCE_AS_OF,
    MARQUEE_REFERENCE_AS_OF
)
from nifty_peer_comparison import (
    get_peers_for_company,
    render_head_to_head_comparison_html,
    NIFTY_50_DATA,
    NIFTY_50_DATASET_AS_OF
)
from self_improvement_engine import (
    SelfImprovementLoop,
    LEDGER_MD_PATH,
    LEDGER_JSON_PATH
)
from financial_trends import fetch_financial_statements


class TestPhase2DataLayer(unittest.TestCase):

    def test_01_indices_data_stale_fallback_when_provider_fails(self):
        """When yfinance fails, benchmark indices must return stale_reference with explicit as_of."""
        with patch("yfinance.download", side_effect=RuntimeError("Network offline")), \
             patch("yfinance.Ticker", side_effect=RuntimeError("Network offline")):
            indices = fetch_live_indices_data()
            self.assertEqual(len(indices), 4)
            for idx in indices:
                self.assertEqual(idx["data_status"], "stale_reference")
                self.assertEqual(idx["as_of"], INDICES_REFERENCE_AS_OF)
                self.assertIsNotNone(idx["cur"])

    def test_02_indices_data_live_when_download_succeeds(self):
        """When provider succeeds, benchmark indices must carry data_status == 'live' and ISO as_of."""
        dates = pd.date_range("2026-10-25", periods=5)
        symbols = ["^NSEI", "^BSESN", "^NSEBANK", "^CNXIT"]
        mock_close = pd.DataFrame(
            {s: [24000.0, 24100.0, 24200.0, 24300.0, 24350.0] for s in symbols},
            index=dates
        )
        mock_high = pd.DataFrame(
            {s: [24050.0, 24150.0, 24250.0, 24350.0, 24450.0] for s in symbols},
            index=dates
        )
        mock_low = pd.DataFrame(
            {s: [23950.0, 24050.0, 24150.0, 24250.0, 24300.0] for s in symbols},
            index=dates
        )
        mock_df = MagicMock()
        mock_df.get.side_effect = lambda k: {
            "Close": mock_close,
            "High": mock_high,
            "Low": mock_low
        }.get(k)

        with patch("yfinance.download", return_value=mock_df):
            indices = fetch_live_indices_data()
            self.assertEqual(len(indices), 4)
            for idx in indices:
                self.assertEqual(idx["data_status"], "live")
                self.assertTrue(len(idx["as_of"]) > 10)
                # Verify ISO timestamp
                datetime.fromisoformat(idx["as_of"])

    def test_03_marquee_stocks_fallback_labelled(self):
        """When marquee equities fetch fails, every row has non-empty as_of and data_status != 'provider'."""
        with patch("yfinance.download", side_effect=RuntimeError("Offline")):
            stocks = fetch_marquee_stocks_data()
            self.assertTrue(len(stocks) >= 10)
            for stk in stocks:
                self.assertNotEqual(stk.get("data_status"), "provider")
                self.assertEqual(stk.get("data_status"), "sample_fallback")
                self.assertEqual(stk.get("as_of"), MARQUEE_REFERENCE_AS_OF)

    def test_04_unknown_target_company_valuation_none(self):
        """Unknown company peer record must not fabricate valuation metrics with placeholder numbers."""
        peers = get_peers_for_company("ZZZUNKNOWN", "Banks (Commercial & Retail)")
        self.assertTrue(len(peers) >= 1)
        target = peers[0]
        self.assertEqual(target["symbol"], "ZZZUNKNOWN")
        # Assert none of the valuation / efficiency fields are fabricated
        self.assertIsNone(target["ind_pe"])
        self.assertIsNone(target["peg"])
        self.assertIsNone(target["ev_ebitda"])
        self.assertIsNone(target["roic"])
        self.assertIsNone(target["croic"])
        self.assertIsNone(target["roce"])
        self.assertIsNone(target["cmp"])
        self.assertIsNone(target["mar_cap"])

    def test_05_no_silent_cross_sector_peers(self):
        """Peer rows must strictly match the target sector; never append unrelated sectors."""
        # Find sectors with small counts in NIFTY_50_DATA
        for sector in ["Telecommunications", "Metals & Mining", "Power & Utilities"]:
            peers = get_peers_for_company("UNKNOWN_TICKER", sector, limit=4)
            for p in peers[1:]:
                self.assertEqual(
                    p["sector"],
                    sector,
                    f"Peer {p['symbol']} sector '{p['sector']}' does not match target sector '{sector}'"
                )

    def test_06_mixed_period_head_to_head_warning_and_no_leader(self):
        """Head-to-head table mixing live target data with static peer data must warn and suppress leaders."""
        live_data = {
            "current_price": 1285.0,
            "cmp": 1285.0,
            "pe_ratio": 21.4,
            "high_52w": 1600.0,
            "market_cap_cr": 1600000.0,
            "ev_ebitda": 12.0,
            "peg": 1.5,
            "profit_margin": 8.5
        }
        html = render_head_to_head_comparison_html(
            "RELIANCE",
            "Reliance Industries",
            "Oil, Gas & Energy Fuels",
            live_data=live_data
        )
        self.assertIn("Periods differ — this table mixes live market data with", html)
        self.assertIn("Ranking Withheld (Mixed Periods)", html)
        self.assertIn("Ranking suppressed: mixed periods", html)
        # Verify no leader star badge exists in any td cell
        self.assertNotIn("★</span>", html)
        self.assertNotIn("★ Leader Highlighted", html)

    def test_07_single_period_head_to_head_renders_normally(self):
        """Single-period static head-to-head must show leader highlights without mixed-period warning."""
        html = render_head_to_head_comparison_html(
            "RELIANCE",
            "Reliance Industries",
            "Oil, Gas & Energy Fuels",
            live_data=None,
            financial_data=None
        )
        self.assertNotIn("Periods differ — this table mixes live market data with", html)
        self.assertIn("★ Leader Highlighted", html)
        self.assertIn("★ Indicates sector category leader", html)
        self.assertIn("★</span>", html)

    def test_08_ledger_isolation_leaves_real_ledgers_byte_identical(self):
        """Dry-run self-improvement cycle with temporary paths must not touch repository ledgers."""
        def file_hash(path):
            if not os.path.exists(path):
                return None
            with open(path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()

        before_md = file_hash(LEDGER_MD_PATH)
        before_json = file_hash(LEDGER_JSON_PATH)

        tmp_dir = tempfile.mkdtemp()
        tmp_md = os.path.join(tmp_dir, "temp_ledger.md")
        tmp_json = os.path.join(tmp_dir, "temp_ledger.json")

        try:
            with patch("self_improvement_engine.VerificationRunner.verify_all", return_value=(True, "OK")), \
                 patch("self_improvement_engine.SignalCollector.collect_test_signals", return_value={
                     "signal_type": "TEST_SUITE", "passed": True, "total_ran": 50, "duration_seconds": 0.2, "failures": []
                 }):
                loop = SelfImprovementLoop(dry_run=True, ledger_md_path=tmp_md, ledger_json_path=tmp_json)
                loop.run_cycle()

            after_md = file_hash(LEDGER_MD_PATH)
            after_json = file_hash(LEDGER_JSON_PATH)

            self.assertEqual(before_md, after_md, "IMPROVEMENT_LEDGER.md was modified during test run!")
            self.assertEqual(before_json, after_json, "improvement_ledger.json was modified during test run!")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_09_nifty_50_data_schema_and_constituents(self):
        """NIFTY_50_DATA must retain exactly 50 constituents, each with all 16 canonical metrics."""
        self.assertEqual(len(NIFTY_50_DATA), 50)
        required_keys = [
            "company", "symbol", "sector", "cmp", "mar_cap", "sales",
            "sales_var_3yr", "profit_var_3yr", "qtr_sales_var", "npm_ann",
            "ind_pe", "pe", "peg", "ev_ebitda", "roic", "croic", "roce",
            "fcf_3yr", "down_pct"
        ]
        for item in NIFTY_50_DATA:
            for k in required_keys:
                self.assertIn(k, item, f"Missing key '{k}' in {item.get('symbol')}")

    def test_10_statement_fiscal_period_alignment(self):
        """P&L (4 yrs) and CF (2 yrs) must align on unified axis with None for missing years, pairing overlapping only."""
        pnl_dates = [
            pd.Timestamp("2021-03-31"),
            pd.Timestamp("2022-03-31"),
            pd.Timestamp("2023-03-31"),
            pd.Timestamp("2024-03-31")
        ]
        cf_dates = [
            pd.Timestamp("2023-03-31"),
            pd.Timestamp("2024-03-31")
        ]

        mock_fin = pd.DataFrame(
            {
                pnl_dates[0]: [10000.0 * 1e7, 1000.0 * 1e7],
                pnl_dates[1]: [12000.0 * 1e7, 1200.0 * 1e7],
                pnl_dates[2]: [15000.0 * 1e7, 1500.0 * 1e7],
                pnl_dates[3]: [18000.0 * 1e7, 1800.0 * 1e7]
            },
            index=["Total Revenue", "Net Income"]
        )
        mock_cf = pd.DataFrame(
            {
                cf_dates[0]: [1350.0 * 1e7],
                cf_dates[1]: [1620.0 * 1e7]
            },
            index=["Operating Cash Flow"]
        )

        mock_ticker = MagicMock()
        mock_ticker.financials = mock_fin
        mock_ticker.balance_sheet = pd.DataFrame()
        mock_ticker.cashflow = mock_cf
        mock_ticker.quarterly_financials = pd.DataFrame()

        with patch("yfinance.Ticker", return_value=mock_ticker):
            res = fetch_financial_statements("TESTCO")
            self.assertNotIn("error", res)
            
            # Unified year axis
            self.assertEqual(res["years"], ["Mar 2021", "Mar 2022", "Mar 2023", "Mar 2024"])
            self.assertEqual(res["cf_years"], res["years"])

            # CF values must have None for 2021 and 2022
            cfo_values = res["cf"]["Cash from Operations (CFO)"]["values"]
            self.assertEqual(len(cfo_values), 4)
            self.assertIsNone(cfo_values[0])
            self.assertIsNone(cfo_values[1])
            self.assertEqual(cfo_values[2], 1350.0)
            self.assertEqual(cfo_values[3], 1620.0)

            # CFO / PAT Conversion % must be None for 2021 and 2022, and computed for 2023 and 2024
            conversion_values = res["cf"]["CFO / PAT Conversion %"]["values"]
            self.assertEqual(len(conversion_values), 4)
            self.assertIsNone(conversion_values[0])
            self.assertIsNone(conversion_values[1])
            self.assertEqual(conversion_values[2], 90.0)   # 1350 / 1500 * 100
            self.assertEqual(conversion_values[3], 90.0)   # 1620 / 1800 * 100

            # cfo_pat_pairing must contain exactly 2 elements for 2023 and 2024
            self.assertEqual(len(res["cfo_pat_pairing"]), 2)
            self.assertEqual(res["cfo_pat_pairing"][0]["year"], "Mar 2023")
            self.assertEqual(res["cfo_pat_pairing"][1]["year"], "Mar 2024")


if __name__ == "__main__":
    unittest.main()
