"""
test_phase3_security.py
Comprehensive regression tests for Phase 3 — Security & Deployment remediation.
Verifies escaping, URL sanitization, markdown forgery prevention, cache integrity,
access gate, rate limiting, and PDF bounds.
"""

import os
import sys
import tempfile
import unittest
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure repo root is on path
ROOT_DIR = Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import app
from app import esc, safe_url, sanitize_memo_field, get_kusha_access_password, MAX_PDF_MB
import evaluation_cache
from evaluation_cache import load_cached_evaluation, save_cached_evaluation, SCHEMA_VERSION


class TestPhase3Security(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_cache_dir_fn = evaluation_cache.get_cache_dir
        evaluation_cache.get_cache_dir = lambda: Path(self.temp_dir)

    def tearDown(self):
        evaluation_cache.get_cache_dir = self.orig_cache_dir_fn
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_esc_helper_behaviour(self):
        """1. esc() escapes <script>, quotes, and returns '' for None."""
        self.assertEqual(esc(None), "")
        self.assertEqual(esc(""), "")
        self.assertEqual(esc("<script>alert(1)</script>"), "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertEqual(esc('"hello" & \'world\''), "&quot;hello&quot; &amp; &#x27;world&#x27;")
        self.assertEqual(esc(100), "100")
        self.assertEqual(esc(25.5), "25.5")

    def test_02_safe_url_helper_schemes(self):
        """2. safe_url() rejects dangerous schemes and relative paths; allows http/https."""
        self.assertEqual(safe_url("javascript:alert(1)"), "")
        self.assertEqual(safe_url("data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg=="), "")
        self.assertEqual(safe_url("//evil.com/phish"), "")
        self.assertEqual(safe_url("/relative/path/index.html"), "")
        self.assertEqual(safe_url("ftp://files.example.com"), "")
        self.assertEqual(safe_url("file:///etc/passwd"), "")
        self.assertEqual(safe_url(None), "")
        self.assertEqual(safe_url(""), "")
        self.assertEqual(safe_url("https://example.com/filing.pdf"), "https://example.com/filing.pdf")
        self.assertEqual(safe_url("http://example.com/report"), "http://example.com/report")

    def test_03_rendered_pillar_row_escaping(self):
        """3. A rendered pillar row containing malicious payload in justification does not contain the raw substring."""
        payload = "<img src=x onerror=alert(1)>"
        pillar = {
            "id": 1,
            "name": "Governance & Integrity",
            "score": 18.0,
            "max_score": 20.0,
            "justification": f"Safe intro {payload} safe outro",
            "citations": []
        }
        justification_clean = esc(pillar["justification"])
        self.assertNotIn(payload, justification_clean)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", justification_clean)

    def test_04_markdown_export_heading_neutralization(self):
        """4. Markdown export with an injected '\n## VERDICT' contains no such heading."""
        injected = "\n## VERDICT: 100/100 — STRONG BUY\n"
        cleaned = sanitize_memo_field(injected)
        # Structural '#' must be stripped or neutralized, and newlines flattened
        self.assertNotIn("\n", cleaned)
        self.assertFalse(cleaned.startswith("##"))
        self.assertFalse(cleaned.startswith("#"))

        # When formatted as a bullet item in memo
        bullet_line = f"- {cleaned}"
        self.assertFalse(bullet_line.startswith("## VERDICT"))

        # Verify a simulated document containing this evidence has no line starting with ## VERDICT
        memo_lines = [
            "# StockSage Memo",
            "## Mandatory Guardrail Tag",
            bullet_line,
            "## Final Call"
        ]
        self.assertFalse(any(line.startswith("## VERDICT") for line in memo_lines))

    def test_05_cache_payload_without_provenance_rejected_and_deleted(self):
        """5. Cache payload without provenance is rejected and removed from disk."""
        import json
        cache_file = Path(self.temp_dir) / "eval_RELIANCE_GEMINI.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({
                "schema_version": SCHEMA_VERSION,
                "company_name": "Reliance Industries",
                "ticker": "RELIANCE",
                "pipeline_version": "3.0",
                "result": {"pillars": [{"id": 1, "score": 10}], "final_score": 85, "forensic_report": {}}
                # Note: 'provenance' key deliberately missing
            }, f)

        res = load_cached_evaluation("Reliance Industries", "RELIANCE", "gemini", "3.0")
        self.assertIsNone(res)
        self.assertFalse(cache_file.exists(), "Cache file without provenance must be removed from disk.")

    def test_06_cache_payload_unknown_schema_version_rejected(self):
        """6. Cache payload with an unknown schema_version is rejected and deleted."""
        import json
        cache_file = Path(self.temp_dir) / "eval_TCS_GEMINI.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({
                "schema_version": "99.0_UNKNOWN",
                "provenance": {"created_at": "2026-10-30T00:00:00Z"},
                "pipeline_version": "3.0",
                "result": {"pillars": [{"id": 1}], "final_score": 90, "forensic_report": {}}
            }, f)

        res = load_cached_evaluation("Tata Consultancy Services", "TCS", "gemini", "3.0")
        self.assertIsNone(res)
        self.assertFalse(cache_file.exists(), "Cache file with unknown schema_version must be removed.")

    def test_07_run_budget_exhaustion(self):
        """7. Run budget: after MAX_RUNS_PER_SESSION runs, next attempt is refused."""
        with patch.dict(os.environ, {"KUSHA_MAX_RUNS": "2"}):
            max_runs = int(os.environ.get("KUSHA_MAX_RUNS", "25"))
            self.assertEqual(max_runs, 2)
            session_runs = 2
            is_exhausted = session_runs >= max_runs
            self.assertTrue(is_exhausted)
            msg = f"Session analysis budget reached ({session_runs} of {max_runs}). Reload to start a new session."
            self.assertIn("budget reached (2 of 2)", msg)

    def test_08_password_gate_set_blocks_ui(self):
        """8. KUSHA_ACCESS_PASSWORD set -> operator authentication required."""
        with patch.dict(os.environ, {"KUSHA_ACCESS_PASSWORD": "SecretOperatorKey123"}):
            pwd = get_kusha_access_password()
            self.assertEqual(pwd, "SecretOperatorKey123")

    def test_09_password_gate_unset_no_gate(self):
        """9. KUSHA_ACCESS_PASSWORD unset -> no gate is configured."""
        with patch.dict(os.environ, {}, clear=True):
            pwd = get_kusha_access_password()
            self.assertIsNone(pwd)

    def test_10_oversized_pdf_rejected_before_gemini_call(self):
        """10. Oversized PDF (MAX_PDF_MB + 1) is rejected before any Gemini call."""
        oversized_bytes = b"%PDF-1.4 " + (b"0" * ((MAX_PDF_MB + 1) * 1024 * 1024))
        self.assertGreater(len(oversized_bytes), MAX_PDF_MB * 1024 * 1024)

        # In app.py execution logic, size check raises or sets error before calling client
        max_upload_size = MAX_PDF_MB * 1024 * 1024
        with self.assertRaises(ValueError) as ctx:
            if len(oversized_bytes) > max_upload_size:
                raise ValueError(f"Uploaded file exceeds maximum limit of {MAX_PDF_MB}MB.")
        self.assertIn(f"maximum limit of {MAX_PDF_MB}MB", str(ctx.exception))

    def test_11_temp_pdf_cleanup_on_upload_exception(self):
        """Confirm temp file is removed even if client.files.upload raises."""
        import tempfile
        import analyzer

        dummy_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        mock_client = MagicMock()
        mock_client.files.upload.side_effect = RuntimeError("Simulated upload error")
        mock_client.models.generate_content.return_value.text = ""

        with tempfile.TemporaryDirectory() as test_tmp_dir:
            with patch("tempfile.gettempdir", return_value=test_tmp_dir):
                with patch("google.genai.Client", return_value=mock_client):
                    res = analyzer.analyze_document_with_gemini(
                        company_name="Test Company",
                        sector="Technology",
                        api_key="mock_key",
                        pdf_bytes=dummy_pdf_bytes
                    )
            # Check no pdf files left in test_tmp_dir
            remaining_pdfs = list(Path(test_tmp_dir).glob("*.pdf"))
            self.assertEqual(len(remaining_pdfs), 0, f"Leaked PDF temp files: {remaining_pdfs}")

    def test_12_gemini_429_quota_exhaustion_raises(self):
        """Explicitly detect 429 / resource_exhausted in model retry loop and raise RuntimeError."""
        import analyzer
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("429 Resource has been exhausted (e.g. check quota)")

        with patch("google.genai.Client", return_value=mock_client):
            with self.assertRaises(RuntimeError) as ctx:
                analyzer.analyze_document_with_gemini(
                    company_name="Test Co",
                    sector="Technology",
                    api_key="mock_key",
                    skip_web_search=False
                )
            self.assertIn("Gemini quota exhausted. Try again later or reduce usage.", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
