"""
tests/test_monitoring.py
Unit tests for Project KUSHA Data-Truth Monitor (Phase 8).
Guarantees drift detection, fingerprint staleness handling, CI baseline freeze,
alert secret redaction, and workflow structure invariants without network calls.
"""

import json
import os
import re
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent

from tools.alert_issue import build_issue_body, redact_secrets_and_content
from tools.monitor import (
    audit_golden_fixtures,
    compute_fingerprint,
    run_offline_checks,
    update_baseline,
)


class TestMonitoringSuite(unittest.TestCase):
    """Hermetic unit tests for data-truth monitoring and alert infrastructure."""

    def test_01_fingerprint_match_no_change_exits_0(self):
        """1. Fingerprint match, no change -> exit 0."""
        exit_code, status, findings, details = run_offline_checks(REPO_ROOT)
        self.assertEqual(exit_code, 0, f"Expected exit 0 but got {exit_code}: {findings}")
        self.assertEqual(status, "OK")
        self.assertGreaterEqual(details.get("fixtures_count", 0), 5)

    def test_02_fingerprint_mismatch_exits_2_names_changed_input(self):
        """2. Fingerprint mismatch -> exit 2, and the message names which input changed."""
        with patch("analyzer.ANALYSIS_PIPELINE_VERSION", "modified-pipeline-v999"):
            exit_code, status, findings, details = run_offline_checks(REPO_ROOT)
            self.assertEqual(exit_code, 2, f"Expected exit 2 for stale baseline, got {exit_code}")
            self.assertEqual(status, "STALE_BASELINE")
            finding_text = " ".join(findings)
            self.assertIn("Fingerprint mismatch", finding_text)
            self.assertIn("pipeline_version", finding_text)

    def test_03_simulated_drift_exits_1_shows_statuses(self):
        """3. Simulated drift -> patch engine to return INSUFFICIENT_DATA for a check that baseline records as PASS -> exit 1."""
        from forensic_risk_engine import ForensicRiskEngine

        orig_audit = ForensicRiskEngine.audit_company_forensics

        def mock_audit(*args, **kwargs):
            rep = orig_audit(*args, **kwargs)
            if kwargs.get("ticker_symbol") == "CLEANLARGECAP":
                # Degrade FOR_02_RECEIVABLE_VELOCITY from PASS to INSUFFICIENT_DATA
                for c in rep.get("checks", []):
                    if c["id"] == "FOR_02_RECEIVABLE_VELOCITY":
                        c["status"] = "INSUFFICIENT_DATA"
            return rep

        with patch.object(ForensicRiskEngine, "audit_company_forensics", side_effect=mock_audit):
            exit_code, status, findings, details = run_offline_checks(REPO_ROOT)
            self.assertEqual(exit_code, 1, f"Expected exit 1 on drift, got {exit_code}")
            self.assertEqual(status, "DRIFT")
            finding_text = " ".join(findings)
            self.assertIn("FOR_02_RECEIVABLE_VELOCITY", finding_text)
            self.assertIn("INSUFFICIENT_DATA", finding_text)
            self.assertIn("DEGRADED", finding_text)

    def test_04_simulated_fabrication_recovery_exits_1(self):
        """4. Simulated fabrication -> patch INSUFFICIENT_DATA -> PASS -> exit 1 with RECOVERED classification."""
        from forensic_risk_engine import ForensicRiskEngine

        orig_audit = ForensicRiskEngine.audit_company_forensics

        def mock_audit(*args, **kwargs):
            rep = orig_audit(*args, **kwargs)
            if kwargs.get("ticker_symbol") == "LOSSMAKER":  # LOSS_MAKER
                # Falsely recover FOR_01_CASH_CONVERSION from CRITICAL to PASS
                for c in rep.get("checks", []):
                    if c["id"] == "FOR_01_CASH_CONVERSION":
                        c["status"] = "PASS"
            return rep

        with patch.object(ForensicRiskEngine, "audit_company_forensics", side_effect=mock_audit):
            exit_code, status, findings, details = run_offline_checks(REPO_ROOT)
            self.assertEqual(exit_code, 1, f"Expected exit 1 on unbacked recovery, got {exit_code}")
            self.assertEqual(status, "DRIFT")
            finding_text = " ".join(findings)
            self.assertIn("FOR_01_CASH_CONVERSION", finding_text)
            self.assertIn("RECOVERED", finding_text)

    def test_05_baseline_update_refused_in_ci(self):
        """5. Baseline update refused in CI -> GITHUB_ACTIONS=true -> exit 4, file unchanged."""
        baseline_file = REPO_ROOT / "monitoring" / "baseline.json"
        orig_bytes = baseline_file.read_bytes()

        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "ALLOW_BASELINE_UPDATE": "0"}):
            code = update_baseline(REPO_ROOT, reason="Valid detailed reason for update")
            self.assertEqual(code, 4, f"Expected update_baseline to exit 4 in CI, got {code}")
            self.assertEqual(baseline_file.read_bytes(), orig_bytes, "Baseline file must remain byte-identical")

    def test_06_baseline_update_requires_meaningful_reason(self):
        """6. Baseline update requires a reason -> empty or generic -> exit 4."""
        for bad_reason in ["", "   ", "update", "fix", "test", "baseline", "refresh"]:
            code = update_baseline(REPO_ROOT, reason=bad_reason)
            self.assertEqual(code, 4, f"Expected exit 4 for bad reason '{bad_reason}', got {code}")

    def test_07_dataset_age_warns_exits_0(self):
        """7. Dataset age -> a date older than threshold -> WARN, exit 0."""
        # 1000 days ago
        old_date_str = (date.today() - timedelta(days=1000)).isoformat()
        with patch("nifty_peer_comparison.NIFTY_50_DATASET_DATE", old_date_str):
            # Patch fingerprint input so we don't trigger fingerprint mismatch
            orig_compute = compute_fingerprint
            def mock_compute(root):
                fp, inp = orig_compute(root)
                base_data = json.loads((REPO_ROOT / "monitoring" / "baseline.json").read_text(encoding="utf-8"))
                return base_data["fingerprint"], base_data["inputs"]

            with patch("tools.monitor.compute_fingerprint", side_effect=mock_compute):
                exit_code, status, findings, _ = run_offline_checks(REPO_ROOT)
                self.assertEqual(exit_code, 0, f"Expected exit 0 with age warning, got {exit_code}")
                finding_text = " ".join(findings)
                self.assertIn("WARN: Peer dataset is", finding_text)

    def test_08_model_watchlist_mismatch_exits_1(self):
        """8. Model watchlist mismatch -> a model not in SUPPORTED_MODELS -> exit 1."""
        with patch("analyzer.SUPPORTED_MODELS", ["gemini-2.5-flash", "gemini-unrecognized-model-v9"]):
            exit_code, status, findings, _ = run_offline_checks(REPO_ROOT)
            self.assertEqual(exit_code, 1, f"Expected exit 1 on watchlist mismatch, got {exit_code}")
            self.assertEqual(status, "DRIFT")
            self.assertIn("Model watchlist does not match analyzer.SUPPORTED_MODELS", " ".join(findings))

    def test_09_alert_redaction_strips_keys_and_statements(self):
        """9. Alert redaction -> a findings payload containing AIzaSy... and financial statements must be redacted."""
        raw_finding = "Error calling model with key AIzaSyB1234567890abcdefghijklmnopqrstuvwxyz and data"
        payload = {
            "status": "DRIFT",
            "fingerprint": "8bdd11b12f74bfde3eec20d72982334950f576d7a7f40970c363f3557a0207ef",
            "findings": [raw_finding],
            "details": {"offline": {"financial_statements": {"revenue": 50000}}},
        }
        summary, body = build_issue_body("fixture-drift", payload, "https://github.com/runs/123")
        self.assertNotIn("AIzaSyB1234567890abcdefghijklmnopqrstuvwxyz", body)
        self.assertIn("[REDACTED_API_KEY]", body)
        self.assertNotIn("50000", body)

    def test_10_no_network_in_offline_suite(self):
        """10. No network in tests -> patch fetch_live_market_data and get_available_annual_reports; assert not called."""
        with patch("nifty_universe.fetch_live_market_data") as mock_market, \
             patch("annual_report_fetcher.get_available_annual_reports") as mock_reports:
            exit_code, status, findings, _ = run_offline_checks(REPO_ROOT)
            self.assertEqual(exit_code, 0)
            mock_market.assert_not_called()
            mock_reports.assert_not_called()

    def test_11_workflow_shape_invariants(self):
        """11. Workflow shape -> parse monitor.yml as text and assert permissions, timeout, schedule, no token echo."""
        workflow_path = REPO_ROOT / ".github" / "workflows" / "monitor.yml"
        self.assertTrue(workflow_path.exists(), "monitor.yml missing")
        content = workflow_path.read_text(encoding="utf-8")

        self.assertIn("issues: write", content, "Workflow must declare 'issues: write'")
        self.assertIn("contents: read", content, "Workflow must declare 'contents: read'")
        self.assertIn("timeout-minutes: 15", content, "Workflow must declare 'timeout-minutes: 15'")
        self.assertIn("cron:", content, "Workflow must declare a cron schedule")
        self.assertIsNone(
            re.search(r"echo\s+.*GITHUB_TOKEN", content),
            "Workflow must never echo GITHUB_TOKEN",
        )
        self.assertNotIn("pull_request:", content, "Workflow must not trigger on pull_request")

    def test_12_watchlist_schema_requires_provenance(self):
        """12. Watchlist schema requires provenance -> missing verification_method -> MISCONFIGURED, exit 4."""
        orig_loads = json.loads

        def mock_loads(s, *args, **kwargs):
            val = orig_loads(s, *args, **kwargs)
            if isinstance(val, dict) and "models" in val and "verification_method" in val:
                val = dict(val)
                del val["verification_method"]
            return val

        with patch("json.loads", side_effect=mock_loads):
            exit_code, status, findings, _ = run_offline_checks(REPO_ROOT)
            self.assertEqual(exit_code, 4, f"Expected exit 4 for missing verification_method, got {exit_code}")
            self.assertEqual(status, "MISCONFIGURED")
            self.assertIn("verification_method", " ".join(findings))

    def test_13_watchlist_self_contradiction_exits_4(self):
        """13. Watchlist self contradiction exits 4 -> verification_method='api_call' with verified_with_api=false -> exit 4."""
        orig_loads = json.loads

        def mock_loads(s, *args, **kwargs):
            val = orig_loads(s, *args, **kwargs)
            if isinstance(val, dict) and "verification_method" in val:
                val = dict(val)
                val["verification_method"] = "api_call"
                val["verified_with_api"] = False
            return val

        with patch("json.loads", side_effect=mock_loads):
            exit_code, status, findings, _ = run_offline_checks(REPO_ROOT)
            self.assertEqual(exit_code, 4, f"Expected exit 4 for self-contradiction, got {exit_code}")
            self.assertEqual(status, "MISCONFIGURED")
            self.assertIn("contradicts itself", " ".join(findings))

    def test_14_non_api_verification_warns_but_exits_0(self):
        """14. Non-API verification warns but exits 0 -> docs_review -> WARN mentioning 'NOT verified', exit 0."""
        exit_code, status, findings, _ = run_offline_checks(REPO_ROOT)
        self.assertEqual(exit_code, 0, f"Expected exit 0 for docs_review, got {exit_code}")
        findings_text = " ".join(findings)
        self.assertIn("NOT verified", findings_text)
        self.assertIn("docs_review", findings_text)

    def test_15_watchlist_last_verified_not_in_future(self):
        """15. Watchlist last verified not in future -> parse last_verified; if it is after today -> fail."""
        # 1. Assert committed watchlist is not in the future
        watchlist = json.loads((REPO_ROOT / "monitoring" / "model_watchlist.json").read_text(encoding="utf-8"))
        if watchlist.get("last_verified"):
            wl_date = date.fromisoformat(watchlist["last_verified"])
            self.assertLessEqual(wl_date, date.today(), f"Committed last_verified {wl_date} is in the future")

        # 2. Assert monitor catches a simulated future date and fails with exit 1 (DRIFT)
        future_date = (date.today() + timedelta(days=1)).isoformat()
        orig_loads = json.loads

        def mock_loads(s, *args, **kwargs):
            val = orig_loads(s, *args, **kwargs)
            if isinstance(val, dict) and "last_verified" in val and "models" in val:
                val = dict(val)
                val["last_verified"] = future_date
            return val

        with patch("json.loads", side_effect=mock_loads):
            exit_code, status, findings, _ = run_offline_checks(REPO_ROOT)
            self.assertEqual(exit_code, 1, f"Expected exit 1 for future last_verified, got {exit_code}")
            self.assertEqual(status, "DRIFT")
            self.assertIn("future", " ".join(findings).lower())


if __name__ == "__main__":
    unittest.main()
