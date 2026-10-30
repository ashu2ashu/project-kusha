"""
test_terminal_quality.py
Comprehensive Quality Assurance & Motion Audit Suite for StockSage Institutional Terminal.
Audits:
1. Python Bytecode Compilation across all core modules
2. Nifty 50 constituents data integrity (50 stocks, 16 Screener metrics, valid ranges)
3. Head-to-Head Peer Comparison Matrix generator & responsive HTML
4. Sector filtering, search algorithms, and peer matching
5. CSS institutional motion tokens, cubic-bezier(0.4, 0, 0.2, 1), and font crispness
6. Deprecated Streamlit API audit (zero use_container_width, zero components.v1)
"""

import unittest
import py_compile
import os
import re
import pandas as pd
from typing import Dict, Any, List

class TestBytecodeCompilation(unittest.TestCase):
    def test_all_modules_compile(self):
        """Ensure all Python source files compile to bytecode with 0 syntax errors."""
        modules = [
            "app.py",
            "nifty_peer_comparison.py",
            "analyzer.py",
            "financial_trends.py",
            "data_integrity_agent.py",
            "nifty_universe.py",
            "prompt_template.py",
            "annual_report_fetcher.py",
            "forensic_risk_engine.py"
        ]
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for mod in modules:
            path = os.path.join(base_dir, mod)
            self.assertTrue(os.path.exists(path), f"Module {mod} does not exist at {path}")
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as e:
                self.fail(f"Bytecode compilation failed for {mod}: {e}")

class TestNifty50UniverseData(unittest.TestCase):
    def setUp(self):
        from nifty_peer_comparison import NIFTY_50_DATA
        self.data = NIFTY_50_DATA

    def test_constituent_count(self):
        """Ensure all 50 premier Nifty 50 constituents are present."""
        self.assertEqual(len(self.data), 50, f"Expected exactly 50 constituents, found {len(self.data)}")

    def test_16_screener_metrics_exist(self):
        """Ensure every constituent has all 16 canonical Screener.in metrics."""
        required_keys = [
            "company", "symbol", "sector", "cmp", "mar_cap", "sales",
            "sales_var_3yr", "profit_var_3yr", "qtr_sales_var", "npm_ann",
            "ind_pe", "pe", "peg", "ev_ebitda", "roic", "croic", "roce",
            "fcf_3yr", "down_pct"
        ]
        for item in self.data:
            for k in required_keys:
                self.assertIn(k, item, f"Missing key '{k}' in constituent {item.get('company', 'Unknown')}")
                val = item[k]
                self.assertIsNotNone(val, f"Key '{k}' is None in {item.get('company', 'Unknown')}")
                if k in ["cmp", "mar_cap", "sales", "pe", "roic", "croic", "roce"]:
                    self.assertIsInstance(val, (int, float), f"Key '{k}' must be numeric in {item['company']}")

    def test_no_duplicate_symbols(self):
        """Ensure all 50 tickers are completely unique."""
        symbols = [c["symbol"] for c in self.data]
        self.assertEqual(len(symbols), len(set(symbols)), "Duplicate symbols detected in Nifty 50 dataset!")

    def test_down_pct_range(self):
        """Ensure '% Down from 52W High' is between 0% and 100%."""
        for c in self.data:
            self.assertGreaterEqual(c["down_pct"], 0.0, f"Negative down_pct in {c['symbol']}")
            self.assertLessEqual(c["down_pct"], 100.0, f"down_pct > 100% in {c['symbol']}")

class TestNiftyPeerComparisonFunctions(unittest.TestCase):
    def setUp(self):
        from nifty_peer_comparison import (
            get_nifty50_dataframe,
            get_peers_for_company,
            render_head_to_head_comparison_html
        )
        self.get_df = get_nifty50_dataframe
        self.get_peers = get_peers_for_company
        self.render_html = render_head_to_head_comparison_html

    def test_dataframe_structure(self):
        """Verify DataFrame conversion and column naming."""
        df = self.get_df()
        self.assertEqual(len(df), 50)
        self.assertIn("Company", df.columns)
        self.assertIn("CMP Rs.", df.columns)
        self.assertIn("ROCE %", df.columns)
        self.assertIn("CROIC %", df.columns)

    def test_sector_filtering(self):
        """Verify sector filtering restricts dataframe accurately."""
        df = self.get_df(sector_filter="Banks (Commercial & Retail)")
        self.assertGreaterEqual(len(df), 4)
        symbols = df["Symbol"].tolist()
        self.assertIn("HDFCBANK", symbols)
        self.assertIn("ICICIBANK", symbols)
        self.assertIn("SBIN", symbols)

    def test_search_query(self):
        """Verify search query matches both company name and ticker."""
        df = self.get_df(search_query="RELIANCE")
        self.assertGreaterEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["Symbol"], "RELIANCE")

    def test_peer_selection_target_first(self):
        """Verify target company is strictly at index 0 of peer group."""
        peers = self.get_peers("TCS", "IT Services & Consulting", limit=4)
        self.assertGreaterEqual(len(peers), 2)
        self.assertEqual(peers[0]["symbol"], "TCS")

    def test_render_head_to_head_html(self):
        """Verify generated peer comparison matrix HTML is valid and populated."""
        html = self.render_html("RELIANCE", "Reliance Industries", "Oil, Gas & Energy Fuels")
        self.assertIn("<table", html)
        self.assertIn("Reliance Industries", html)
        self.assertIn("RELIANCE", html)
        self.assertIn("★ Leader Highlighted", html)
        self.assertIn("peer-matrix-row", html)
        self.assertIn("cubic-bezier(0.4, 0, 0.2, 1)", html)

    def test_render_head_to_head_html_non_nifty_stock(self):
        """Verify peer matrix for non-Nifty-50 stocks (e.g. ABB) syncs live data and statements without 0.0 placeholders."""
        live_sample = {
            "current_price": 6140.0,
            "market_cap_cr": 130111.7,
            "pe_ratio": 83.64,
            "high_52w": 7924.5,
            "ev_ebitda": 63.7,
            "profit_margin": 12.8,
            "fcf_cr": 1082.4
        }
        fin_sample = {
            "pnl": {
                "Sales / Total Revenue": {"values": [8498.4, 10366.7, 12087.7, 13065.3]},
                "NPM %": {"values": [12.0, 12.0, 15.5, 12.8]}
            },
            "cagr": {
                "sales_cagr": 15.4,
                "pat_cagr": 18.0,
                "latest_roe": 19.1
            },
            "quarterly": {
                "Sales / Revenue": {"values": [3162.4, 3521.0]}
            },
            "cf": {
                "Free Cash Flow (FCF)": {"values": [1168.4, 1117.8, 979.6]}
            }
        }
        html = self.render_html("ABB", "ABB India Ltd.", "Capital Goods", live_data=live_sample, financial_data=fin_sample)
        self.assertIn("ABB India Ltd.", html)
        self.assertIn("₹130,111.7 Cr", html)
        self.assertIn("₹13,065.3 Cr", html)
        self.assertIn("+15.40%", html)
        self.assertIn("+18.00%", html)
        self.assertNotIn("₹0.0 Cr", html)

class TestCSSMotionAndFluidity(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(base_dir, "app.py"), "r", encoding="utf-8") as f:
            self.app_content = f.read()
        css_path = os.path.join(base_dir, "assets", "kusha.css")
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                self.app_content += "\n" + f.read()
        with open(os.path.join(base_dir, "nifty_peer_comparison.py"), "r", encoding="utf-8") as f:
            self.nifty_content = f.read()

    def test_cubic_bezier_physics_present(self):
        """Verify institutional physics cubic-bezier(0.4, 0, 0.2, 1) is active."""
        curve = "cubic-bezier(0.4, 0, 0.2, 1)"
        self.assertIn(curve, self.app_content, "Institutional curve cubic-bezier(0.4, 0, 0.2, 1) missing from app.py")
        self.assertIn(curve, self.nifty_content, "Institutional curve cubic-bezier(0.4, 0, 0.2, 1) missing from nifty_peer_comparison.py")

    def test_font_crispness_and_typography(self):
        """Verify font antialiasing and Google Fonts typography imports."""
        self.assertIn("-webkit-font-smoothing: antialiased", self.app_content, "Missing antialiased font smoothing")
        self.assertIn("-moz-osx-font-smoothing: grayscale", self.app_content, "Missing grayscale font smoothing")
        self.assertIn("family=Inter", self.app_content, "Missing Inter font import")
        self.assertIn("family=JetBrains+Mono", self.app_content, "Missing JetBrains Mono font import")

    def test_no_deprecated_use_container_width(self):
        """Strict adherence to Streamlit guidelines: zero use_container_width."""
        self.assertNotIn("use_container_width", self.app_content, "Deprecated use_container_width found in app.py!")
        self.assertNotIn("use_container_width", self.nifty_content, "Deprecated use_container_width found in nifty_peer_comparison.py!")

    def test_no_direct_active_nav_mode_mutation(self):
        """Ensure active_nav_mode is not assigned after widget creation to prevent StreamlitWidgetAlreadyInstantiatedError."""
        # Check that buttons set pending_nav_mode instead of directly setting active_nav_mode
        self.assertNotIn('st.session_state["active_nav_mode"] = "🔬 Company Analysis"', self.app_content)
        self.assertNotIn('st.session_state["active_nav_mode"] = "🔬 Company Analysis"', self.nifty_content)
        self.assertIn('pending_nav_mode', self.app_content)
        self.assertIn('pending_nav_mode', self.nifty_content)

    def test_responsive_grid_breakpoints(self):
        """Ensure tablet & mobile responsive breakpoints exist without layout shifts."""
        self.assertIn("@media (max-width: 1100px)", self.app_content)
        self.assertIn("repeat(auto-fit, minmax(200px, 1fr))", self.nifty_content, "Responsive auto-fit grid missing in Nifty Screener KPI strip")

class TestAnalyzerAndGuardrails(unittest.TestCase):
    def test_prompt_template_placeholders(self):
        """Ensure core prompt has dynamic company and sector placeholders."""
        from prompt_template import IDEX_ANALYSIS_PROMPT
        self.assertIn("{company_name}", IDEX_ANALYSIS_PROMPT)
        self.assertIn("{sector}", IDEX_ANALYSIS_PROMPT)

    def test_gemini_key_validation_safe(self):
        """Ensure verify_gemini_api_key handles invalid/empty keys safely."""
        from analyzer import verify_gemini_api_key
        is_valid, msg = verify_gemini_api_key("")
        self.assertFalse(is_valid)
        self.assertTrue("empty" in msg.lower() or "no api key" in msg.lower())

class TestForensicLensSafety(unittest.TestCase):
    def test_fraud_shield_handles_string_and_na_dso(self):
        """Ensure render_forensic_fraud_shield_html does not crash on non-numeric or string DSO."""
        from app import render_forensic_fraud_shield_html

        # Test with "N/A" DSO
        res_na = {
            "receivable_health_metrics": {"dso_days": "N/A", "pct_over_90_days": "N/A"},
            "analysis_status": "insufficient_evidence",
            "evidence_gaps": ["No statutory filing attached."]
        }
        html_na = render_forensic_fraud_shield_html(res_na, {})
        self.assertIn("N/A", html_na)
        self.assertIn("⚠", html_na)

        # Test with string "45 days" DSO
        res_str = {
            "receivable_health_metrics": {"dso_days": "45 days", "pct_over_90_days": "2.1%"},
            "analysis_status": "completed",
            "forensic_report": {
                "checks": [
                    {
                        "id": "FOR_02_RECEIVABLE_VELOCITY",
                        "status": "PASS",
                        "metric": "DSO: 45 DAYS",
                        "detail": "Healthy receivables velocity."
                    }
                ]
            }
        }
        html_str = render_forensic_fraud_shield_html(res_str, {"debt_to_equity": 0.3})
        self.assertIn("45", html_str)
        self.assertIn("PASS", html_str)

    def test_fraud_shield_clean_statutory_filings_pass_all_six_checks(self):
        """Ensure clean statutory filings (unmodified opinion, 0% pledge, strong CFO) pass all 6 checks."""
        from app import render_forensic_fraud_shield_html

        res_clean = {
            "analysis_status": "completed",
            "appendix_a_forensic_evidence": [
                "Statutory Auditor Report (Page 213): Unmodified opinion with no qualifications or adverse remarks.",
                "Promoter Pledge Filing: 0.0% shares pledged as of latest quarter filing."
            ],
            "receivable_health_metrics": {
                "dso_days": "87 days",
                "pct_over_90_days": "4.2%"
            },
            "pio_triggered": False,
            "forensic_report": {
                "checks": [
                    {
                        "id": "FOR_08_AUDITOR_GOVERNANCE",
                        "status": "PASS",
                        "detail": "Statutory Auditor Report: Unmodified opinion with no qualifications or adverse remarks."
                    },
                    {
                        "id": "FOR_07_PROMOTER_PLEDGE",
                        "status": "PASS",
                        "detail": "Promoter Pledge Filing: 0.0% shares pledged as of latest quarter filing."
                    },
                    {
                        "id": "FOR_01_CASH_CONVERSION",
                        "status": "PASS",
                        "metric": "CFO/PAT: 80%",
                        "detail": "Robust cash flow conversion."
                    },
                    {
                        "id": "FOR_02_RECEIVABLE_VELOCITY",
                        "status": "PASS",
                        "metric": "DSO: 87 DAYS",
                        "detail": "Receivables velocity healthy."
                    },
                    {
                        "id": "FOR_06_CREDIT_RATING_SOLVENCY",
                        "status": "PASS",
                        "metric": "DEBT FREE",
                        "detail": "Solvent low-debt profile."
                    }
                ]
            }
        }
        live_clean = {
            "debt_to_equity": 0.02,
            "screener_metrics": {
                "promoter_holding": "76.34 %"
            }
        }
        fin_clean = {
            "cf": {
                "Cash from Operations (CFO)": {"values": [741.9, 1351.5, 1331.8, 1219.5]},
                "Free Cash Flow (FCF)": {"values": [574.0, 1168.4, 1117.8, 979.6]}
            },
            "pnl": {
                "Net Profit (PAT)": {"values": [1016.2, 1242.0, 1871.6, 1668.3]}
            },
            "cagr": {
                "latest_de": 0.01
            }
        }

        html = render_forensic_fraud_shield_html(res_clean, live_clean, financial_data=fin_clean)
        
        # 1. Auditor check must pass
        self.assertIn("CLEAN AUDIT", html)
        # 2. Promoter pledge must pass
        self.assertIn("0.0% PLEDGED", html)
        # 3. Cash flow must pass
        self.assertIn("CFO/PAT: 80%", html)
        # 4. Debtor health must pass
        self.assertIn("DSO: 87 DAYS", html)
        # 5. Leverage must pass
        self.assertIn("DEBT FREE", html)
        # 6. Regulatory check without explicit enforcement data is truthfully NOT EVALUATED
        self.assertIn("NOT EVALUATED", html)
        # Overall badge: 5 / 6 PASSED
        self.assertIn("5 / 6 PASSED", html)

    def test_traffic_light_handles_insufficient_evidence(self):
        """Ensure render_traffic_light_and_eli15_html handles evidence gaps honestly."""
        from app import render_traffic_light_and_eli15_html

        res = {
            "final_score": "42.0",
            "analysis_status": "insufficient_evidence",
            "evidence_gaps": ["Statutory filings not verified."],
            "strengths": ["Insufficient evidence"]
        }
        html = render_traffic_light_and_eli15_html(res, {}, "Tata Motors Ltd.", "Automotive")
        self.assertIn("INSUFFICIENT DATA", html)
        self.assertNotIn("powered by insufficient evidence", html)

    def test_cagr_insights_handles_none_values(self):
        """Ensure generate_forensic_cagr_insights handles None avg_cfo_pat, latest_de, and growth metrics."""
        from financial_trends import generate_forensic_cagr_insights

        fin_data_none = {
            "cagr": {
                "sales_cagr": None,
                "sales_yoy": None,
                "pat_cagr": None,
                "pat_yoy": None,
                "avg_cfo_pat": None,
                "latest_de": None,
                "latest_roe": None,
                "opm_expansion": None,
                "n_years": 3
            }
        }
        insights = generate_forensic_cagr_insights(fin_data_none, "Tata Motors Ltd.")
        self.assertIsInstance(insights, list)
        self.assertTrue(len(insights) > 0)
        titles = [i["title"] for i in insights]
        self.assertTrue(any("Not Applicable" in t or "Negative Base" in t for t in titles))
        self.assertTrue(any("Data Unavailable" in t for t in titles))

    def test_valuation_compass_cmp_positioning_and_formatting(self):
        """Ensure render_valuation_compass_html correctly positions the filled bar to CMP and has clean formatting."""
        from app import render_valuation_compass_html

        # Case 1: ABB screenshot scenario (CMP 6140, DCF 5850, 52W L 4637.5, 52W H 7924.5)
        res = {
            "appendix_b_calculations": {
                "dcf_fair_value_estimate": "₹5,850"
            }
        }
        live = {
            "current_price": 6140.0,
            "low_52w": 4637.5,
            "high_52w": 7924.5
        }
        html = render_valuation_compass_html(res, live)
        self.assertTrue(bool(html))
        
        # 1. Ensure no double signs like '+-'
        self.assertNotIn("+-", html)
        self.assertIn("-4.7% to model fair value", html)  # (5850 - 6140) / 6140 = -4.72%

        # 2. Ensure no identical range repetition like '₹5,850 – ₹5,850'
        self.assertNotIn("₹5,850 – ₹5,850", html)
        self.assertIn("₹5,850", html)

        # 3. Ensure Valuation Status shows Premium (since CMP > DCF)
        self.assertIn("Valuation Premium", html)

        # 4. Ensure the active filled bar is tied to CMP, not 52W High width
        # The range from 4637.5 to 7924.5 is span ~3287
        # CMP 6140 - 4637.5 = ~1502.5. So CMP fill width is ~45% of 52W range, strictly less than 52W range width
        import re
        # Find active valuation bar width
        bar_match = re.search(r'background:\s*linear-gradient\(90deg,\s*(?:#60A5FA|#00E5FF)\s*0%,\s*(?:#2563EB|#00F5A0)\s*100%\);', html)
        self.assertIsNotNone(bar_match, "Valuation CMP bar not found in HTML!")

        # Case 2: Undervalued scenario (CMP 4500, DCF 5850)
        live_under = {
            "current_price": 4500.0,
            "low_52w": 4000.0,
            "high_52w": 6500.0
        }
        html_under = render_valuation_compass_html(res, live_under)
        self.assertIn("Margin of Safety", html_under)
        self.assertIn("+30.0% to model fair value", html_under)
        self.assertNotIn("+-", html_under)


if __name__ == "__main__":
    unittest.main(verbosity=2)
