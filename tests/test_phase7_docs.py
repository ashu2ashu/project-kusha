"""
tests/test_phase7_docs.py
Documentation, legal posture, and positioning ratchets for Project KUSHA (Phase 7).
Ensures checkable claims, verified links, historical provenance banners, model sync,
accurate test counts, licence consistency, de-advisory contracts, and privacy completeness.
"""

import ast
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestPhase7DocsRatchets(unittest.TestCase):
    """10 automated ratchets enforcing documentation truthfulness and legal positioning."""

    CURRENT_DOCS = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "docs" / "ARCHITECTURE.md",
        REPO_ROOT / "docs" / "LEGAL_DECISIONS.md",
        REPO_ROOT / "docs" / "PRIVACY.md",
        REPO_ROOT / "docs" / "LIMITATIONS.md",
    ]

    def test_01_banned_claims_in_readme_and_current_docs(self):
        """1. Banned claims: no overclaims or unqualified 'deterministic' in README or current docs."""
        banned_regexes = [
            re.compile(r"trade\s*secret", re.I),
            re.compile(r"institutional[- ]grade", re.I),
            re.compile(r"audit[- ]grade", re.I),
            re.compile(r"100%\s*free", re.I),
            re.compile(r"\bguarantee\b", re.I),
            re.compile(r"compiled\s+under", re.I),
            re.compile(r"ip\s+safeguards", re.I),
            re.compile(r"10[- ]pillar", re.I),
        ]

        for doc_path in self.CURRENT_DOCS:
            self.assertTrue(doc_path.exists(), f"Expected document {doc_path} does not exist")
            text = doc_path.read_text(encoding="utf-8")

            for pat in banned_regexes:
                match = pat.search(text)
                self.assertIsNone(
                    match,
                    f"Banned claim pattern '{pat.pattern}' found in {doc_path.name}: '{match.group(0) if match else ''}'",
                )

            # Check that 'deterministic' is only used when qualified by 'arithmetic' or 'post-model'
            for idx, line in enumerate(text.splitlines(), 1):
                if "deterministic" in line.lower():
                    is_qualified = (
                        "arithmetic" in line.lower()
                        or "post-model" in line.lower()
                        or "the arithmetic after the model returns is deterministic" in line.lower()
                    )
                    self.assertTrue(
                        is_qualified,
                        f"Unqualified 'deterministic' at {doc_path.name}:{idx}: '{line.strip()}'",
                    )

    def test_02_required_links_exist(self):
        """2. Required links: README links PRIVACY, LIMITATIONS, LEGAL_DECISIONS, and all relative links exist."""
        readme_path = REPO_ROOT / "README.md"
        text = readme_path.read_text(encoding="utf-8")

        for req in ["docs/PRIVACY.md", "docs/LIMITATIONS.md", "docs/LEGAL_DECISIONS.md"]:
            self.assertIn(req, text, f"README.md does not link to required document {req}")

        # Verify all relative Markdown links
        link_pat = re.compile(r"\[.*?\]\((docs/[^\)#\s]+)\)")
        for link in link_pat.findall(text):
            target = REPO_ROOT / link
            self.assertTrue(target.exists(), f"Relative link in README points to missing file: {link}")

    def test_03_history_banner(self):
        """3. History banner: every file under docs/history/ except README.md starts with '> **HISTORICAL'."""
        history_dir = REPO_ROOT / "docs" / "history"
        self.assertTrue(history_dir.exists(), "docs/history/ directory does not exist")

        md_files = list(history_dir.glob("*.md"))
        self.assertGreater(len(md_files), 1, "docs/history/ should contain archived markdown reports")

        for md in md_files:
            if md.name == "README.md":
                continue
            lines = md.read_text(encoding="utf-8").splitlines()
            self.assertTrue(len(lines) > 0, f"Historical file {md.name} is empty")
            first_line = lines[0].strip()
            self.assertTrue(
                first_line.startswith("> **HISTORICAL"),
                f"Historical file {md.name} missing mandatory banner: starts with '{first_line[:50]}'",
            )

    def test_04_no_duplicate_markdown(self):
        """4. No duplicate markdown: no two markdown files in the repository have identical content."""
        seen_contents = {}
        duplicates = []

        for p in REPO_ROOT.glob("**/*.md"):
            # Exclude virtual environments or agent skills directories
            if any(part.startswith(".") for part in p.parts):
                continue
            content = p.read_text(encoding="utf-8")
            rel = str(p.relative_to(REPO_ROOT))
            if content in seen_contents:
                duplicates.append((rel, seen_contents[content]))
            else:
                seen_contents[content] = rel

        self.assertEqual(duplicates, [], f"Duplicate markdown files detected: {duplicates}")

    def test_05_model_list_consistency(self):
        """5. Model list consistency: block between <!-- MODELS:START --> and <!-- MODELS:END --> matches SUPPORTED_MODELS."""
        from analyzer import SUPPORTED_MODELS

        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        marker_pat = re.compile(r"<!-- MODELS:START -->(.*?)<!-- MODELS:END -->", re.DOTALL)
        match = marker_pat.search(readme_text)
        self.assertIsNotNone(match, "README.md missing <!-- MODELS:START --> ... <!-- MODELS:END --> block")

        extracted_models = [m.strip() for m in match.group(1).strip().splitlines() if m.strip()]
        self.assertEqual(
            extracted_models,
            SUPPORTED_MODELS,
            f"README models {extracted_models} do not match analyzer.SUPPORTED_MODELS {SUPPORTED_MODELS}",
        )

    def test_06_no_stale_test_counts(self):
        """6. No stale test counts: any '\\b\\d+ (unit )?tests\\b' in docs equals actual def test_ count or is absent."""
        # Count actual test methods in tests/
        actual_test_count = 0
        for test_file in (REPO_ROOT / "tests").glob("*.py"):
            lines = test_file.read_text(encoding="utf-8").splitlines()
            actual_test_count += sum(1 for line in lines if line.strip().startswith("def test_"))

        count_pat = re.compile(r"\b(\d+)\s+(?:unit\s+)?tests\b", re.I)

        for doc_path in self.CURRENT_DOCS:
            text = doc_path.read_text(encoding="utf-8")
            for match in count_pat.finditer(text):
                stated_count = int(match.group(1))
                self.assertEqual(
                    stated_count,
                    actual_test_count,
                    f"Stale test count {stated_count} in {doc_path.name} (actual count is {actual_test_count})",
                )

    def test_07_licence_consistency(self):
        """7. Licence consistency: if LICENSE exists, README matches; if not, README contains 'All rights reserved'."""
        license_path = REPO_ROOT / "LICENSE"
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        if license_path.exists():
            lic_content = license_path.read_text(encoding="utf-8").upper()
            if "MIT" in lic_content:
                self.assertIn("MIT", readme_text)
            elif "APACHE" in lic_content:
                self.assertIn("Apache", readme_text)
        else:
            self.assertIn("All rights reserved", readme_text)
            self.assertNotIn("MIT License", readme_text)
            self.assertNotIn("Apache License", readme_text)

    def test_08_de_advisory_contract(self):
        """8. De-advisory contract: no BUY/SELL/AVOID stances in app/render; verdict_band returns risk_tier."""
        from analyzer import verdict_band

        # 1. verdict_band() returns risk_tier and no position_sizing
        res_high = verdict_band(92.0)
        self.assertIn("risk_tier", res_high)
        self.assertNotIn("position_sizing", res_high)
        self.assertEqual(res_high["risk_tier"], "Constructive")

        res_mid = verdict_band(70.0)
        self.assertIn("risk_tier", res_mid)
        self.assertNotIn("position_sizing", res_mid)
        self.assertEqual(res_mid["risk_tier"], "Monitored")

        res_low = verdict_band(40.0)
        self.assertIn("risk_tier", res_low)
        self.assertNotIn("position_sizing", res_low)
        self.assertEqual(res_low["risk_tier"], "Elevated Caution")

        # 2. No user-facing BUY / SELL / AVOID stances in app.py and kusha_render.py
        stance_pat = re.compile(r"stance\s*=\s*['\"](BUY|SELL|AVOID)['\"]", re.I)
        for py_path in [REPO_ROOT / "app.py", REPO_ROOT / "kusha_render.py"]:
            src = py_path.read_text(encoding="utf-8")
            self.assertIsNone(
                stance_pat.search(src),
                f"Advisory stance assignment found in {py_path.name}",
            )

    def test_09_dcf_absence_in_current_docs(self):
        """9. DCF absence: no current doc describes a computed DCF or WACC."""
        wacc_pat = re.compile(r"\bWACC\b.*?(?:=|:|\d+%)", re.I)

        for doc_path in self.CURRENT_DOCS:
            text = doc_path.read_text(encoding="utf-8")
            self.assertIsNone(
                wacc_pat.search(text),
                f"Computed WACC/DCF found in current doc {doc_path.name}",
            )

    def test_10_privacy_completeness(self):
        """10. Privacy completeness: docs/PRIVACY.md contains Gemini, Google, Yahoo, bseindia.com, .env, .cache/evaluations."""
        privacy_path = REPO_ROOT / "docs" / "PRIVACY.md"
        self.assertTrue(privacy_path.exists(), "docs/PRIVACY.md does not exist")
        text = privacy_path.read_text(encoding="utf-8")

        required_strings = [
            "Gemini",
            "Google",
            "Yahoo",
            "bseindia.com",
            ".env",
            ".cache/evaluations",
        ]
        for req in required_strings:
            self.assertIn(
                req,
                text,
                f"Required privacy disclosure '{req}' missing from docs/PRIVACY.md",
            )

    def test_12_every_readme_badge_resolves(self):
        """12. Every README badge resolves: extract every actions/workflows/<file>/badge.svg from README, assert <file> exists under .github/workflows/."""
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        badge_pat = re.compile(r"actions/workflows/([^/]+)/badge\.svg")
        matches = badge_pat.findall(readme_text)
        self.assertGreater(len(matches), 0, "No GitHub workflow badges found in README.md")

        for workflow_file in matches:
            target_path = REPO_ROOT / ".github" / "workflows" / workflow_file
            self.assertTrue(
                target_path.exists(),
                f"Badge in README references non-existent workflow file: .github/workflows/{workflow_file}",
            )

    def test_13_licence_statement_matches_repo_state(self):
        """13. Licence statement matches repo state: assert README contains 'No licence is granted' and does not contain 'Keep the repository private'."""
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("No licence is granted", readme_text)
        self.assertNotIn("Keep the repository private", readme_text)


if __name__ == "__main__":
    unittest.main()
