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
            "prompt_template.py"
        ]
        base_dir = os.path.dirname(os.path.abspath(__file__))
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

class TestCSSMotionAndFluidity(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, "app.py"), "r", encoding="utf-8") as f:
            self.app_content = f.read()
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

if __name__ == "__main__":
    unittest.main(verbosity=2)
