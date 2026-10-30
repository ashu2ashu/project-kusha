"""
tests/test_architecture.py
Architecture and packaging ratchets for Project KUSHA (Phase 6).
Guarantees monolith bounds, render purity, re-export fidelity, dependency completeness,
score band single-source-of-truth, and forensic truthfulness.
"""

import ast
import os
import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestArchitectureRatchets(unittest.TestCase):
    """Automated ratchets enforcing architectural boundaries and packaging invariants."""

    def test_01_app_size_ratchet(self):
        """1. Size ratchet: app.py must not exceed 3,400 lines."""
        app_path = REPO_ROOT / "app.py"
        line_count = len(app_path.read_text(encoding="utf-8").splitlines())
        self.assertLessEqual(
            line_count,
            3400,
            f"app.py has grown to {line_count} lines, exceeding the 3,400 line ceiling.",
        )

    def test_02_kusha_render_purity(self):
        """2. Purity: kusha_render.py must not import streamlit and have no AST calls to 'st'."""
        render_path = REPO_ROOT / "kusha_render.py"
        src = render_path.read_text(encoding="utf-8")
        self.assertNotIn("import streamlit", src, "kusha_render.py must not import streamlit")

        tree = ast.parse(src, filename="kusha_render.py")
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotEqual(alias.name, "streamlit", "Import of streamlit detected in kusha_render")
                elif isinstance(node, ast.ImportFrom):
                    self.assertNotEqual(node.module, "streamlit", "from streamlit import detected in kusha_render")
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    self.assertNotEqual(
                        node.func.value.id,
                        "st",
                        f"Streamlit call st.{node.func.attr} detected at line {node.lineno} in kusha_render.py",
                    )

    def test_03_no_duplicate_definitions_in_app(self):
        """3. No duplicate definitions: none of the 14 moved functions is defined in app.py."""
        moved_functions = {
            "esc",
            "safe_url",
            "sanitize_memo_field",
            "build_filing_ingestion_notice_html",
            "render_dalal_street_metric_cards_html",
            "build_ticker_chart",
            "build_radar_chart",
            "parse_dcf_estimate",
            "render_live_analysis_timer_html",
            "render_research_provenance_and_evidence_card",
            "render_traffic_light_and_eli15_html",
            "render_forensic_fraud_shield_html",
            "render_valuation_compass_html",
            "render_graphical_forensic_architecture_html",
        }
        app_path = REPO_ROOT / "app.py"
        tree = ast.parse(app_path.read_text(encoding="utf-8"), filename="app.py")
        defined_in_app = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        duplicates = moved_functions.intersection(defined_in_app)
        self.assertEqual(
            duplicates,
            set(),
            f"Functions duplicated in app.py instead of pure import: {duplicates}",
        )

    def test_04_no_library_module_imports_app(self):
        """4. No library imports app: no top-level *.py except app.py imports app."""
        for py_file in REPO_ROOT.glob("*.py"):
            if py_file.name == "app.py":
                continue
            src = py_file.read_text(encoding="utf-8")
            tree = ast.parse(src, filename=py_file.name)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotEqual(
                            alias.name,
                            "app",
                            f"Module {py_file.name} imports app.py at line {node.lineno}",
                        )
                elif isinstance(node, ast.ImportFrom):
                    self.assertNotEqual(
                        node.module,
                        "app",
                        f"Module {py_file.name} imports from app at line {node.lineno}",
                    )

    def test_05_reexport_compatibility(self):
        """5. Re-export compatibility: all 12 specified names succeed from app and match origins."""
        import app
        import kusha_render

        expected_symbols = [
            "MAX_PDF_MB",
            "build_filing_ingestion_notice_html",
            "esc",
            "get_kusha_access_password",
            "nav_alias_map",
            "render_forensic_fraud_shield_html",
            "render_research_provenance_and_evidence_card",
            "render_traffic_light_and_eli15_html",
            "render_valuation_compass_html",
            "safe_url",
            "sanitize_memo_field",
            "workspace_options",
        ]
        for name in expected_symbols:
            self.assertTrue(hasattr(app, name), f"app is missing re-export of {name}")

        moved_names = [
            "esc",
            "safe_url",
            "sanitize_memo_field",
            "build_filing_ingestion_notice_html",
            "render_forensic_fraud_shield_html",
            "render_valuation_compass_html",
            "render_traffic_light_and_eli15_html",
            "render_research_provenance_and_evidence_card",
        ]
        for name in moved_names:
            app_obj = getattr(app, name)
            render_obj = getattr(kusha_render, name)
            self.assertIs(
                app_obj,
                render_obj,
                f"app.{name} is not the exact object from kusha_render.{name}",
            )

    def test_06_dependencies_declared_and_bounded(self):
        """6. Dependencies declared: all third-party imports appear with bounds in requirements.txt."""
        req_path = REPO_ROOT / "requirements.txt"
        req_text = req_path.read_text(encoding="utf-8")
        requirements = [
            line.strip().split(";")[0]
            for line in req_text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

        expected_dists = {
            "streamlit",
            "plotly",
            "google-genai",
            "pypdf",
            "python-dotenv",
            "yfinance",
            "beautifulsoup4",
            "requests",
            "pandas",
            "numpy",
        }

        declared_dists = set()
        for req in requirements:
            m = re.match(r"^([A-Za-z0-9_\-]+)", req)
            if m:
                dist = m.group(1).lower()
                declared_dists.add(dist)
                # Ensure each dependency has both lower and upper bounds
                self.assertIn(">=", req, f"Requirement {req} lacks a lower bound (>=)")
                self.assertIn("<", req, f"Requirement {req} lacks an upper bound (<)")

        missing = expected_dists - declared_dists
        self.assertEqual(missing, set(), f"Missing required dependencies in requirements.txt: {missing}")

    def test_07_no_duplicate_docs(self):
        """7. No duplicate docs: no two tracked *.md files have identical content."""
        git_cmd = subprocess.run(
            ["git", "ls-files", "*.md"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        md_files = [f.strip() for f in git_cmd.stdout.splitlines() if f.strip()]
        seen_contents = {}
        duplicates = []
        for md in md_files:
            md_path = REPO_ROOT / md
            if not md_path.exists():
                continue
            content = md_path.read_text(encoding="utf-8")
            if content in seen_contents:
                duplicates.append((md, seen_contents[content]))
            else:
                seen_contents[content] = md
        self.assertEqual(duplicates, [], f"Duplicate documentation detected: {duplicates}")

    def test_08_pillar_integrity(self):
        """8. Pillar integrity: PILLAR_METADATA keys match CANONICAL_PILLARS and prompt template."""
        from analyzer import CANONICAL_PILLARS
        from kusha_render import PILLAR_METADATA
        from prompt_template import IDEX_ANALYSIS_PROMPT

        expected_ids = {str(p["id"]) for p in CANONICAL_PILLARS}
        self.assertEqual(
            set(PILLAR_METADATA.keys()),
            expected_ids,
            "PILLAR_METADATA keys do not match canonical pillar IDs",
        )

        for pillar in CANONICAL_PILLARS:
            self.assertIn(
                pillar["name"],
                IDEX_ANALYSIS_PROMPT,
                f"Canonical pillar '{pillar['name']}' not found in IDEX_ANALYSIS_PROMPT",
            )

    def test_09_score_bands_consistency(self):
        """9. Score bands: verdict_band maps correctly and colors align with institutional palette."""
        from analyzer import verdict_band

        ocgc = verdict_band(95.0)
        self.assertEqual(ocgc["code"], "OCGC")
        self.assertEqual(ocgc["color"], "#059669")

        pcgc = verdict_band(88.0)
        self.assertEqual(pcgc["code"], "PCGC")
        self.assertEqual(pcgc["color"], "#059669")

        qtc = verdict_band(76.0)
        self.assertEqual(qtc["code"], "QTC")
        self.assertEqual(qtc["color"], "#2563EB")

        fragile = verdict_band(45.0)
        self.assertEqual(fragile["code"], "FRAGILE")
        self.assertEqual(fragile["color"], "#DC2626")

    def test_10_shield_truthfulness_against_engine(self):
        """10. Shield truth: rows are only PASS when engine is PASS; missing engine checks are NOT EVALUATED."""
        import tests.fixtures_golden as g
        from kusha_render import shield_rows

        fixtures = ["CLEAN_LARGECAP", "LOSS_MAKER", "HIGH_PLEDGE", "CHANNEL_STUFFING", "EMPTY"]
        for fix_name in fixtures:
            fx = getattr(g, fix_name)
            res = fx.get("result") or fx.get("raw_analysis") or {}
            live = fx.get("live") or fx.get("market_data") or {}
            forensic_rep = res.get("forensic_report") or {}
            engine_checks = {c.get("id"): c.get("status") for c in forensic_rep.get("checks", [])}

            rows = shield_rows(res, live)
            for row in rows:
                check_id = row.get("check_id")
                status = row["status"]

                if check_id is None:
                    self.assertEqual(
                        status,
                        "NOT EVALUATED",
                        f"Unbacked check '{row['title']}' in {fix_name} must be NOT EVALUATED",
                    )
                elif check_id not in engine_checks:
                    self.assertEqual(
                        status,
                        "NOT EVALUATED",
                        f"Check '{check_id}' absent from engine report in {fix_name} must be NOT EVALUATED",
                    )
                else:
                    engine_st = engine_checks[check_id]
                    if status == "PASS":
                        self.assertEqual(
                            engine_st,
                            "PASS",
                            f"Shield row '{check_id}' in {fix_name} is PASS but engine status is {engine_st}",
                        )


if __name__ == "__main__":
    unittest.main()
