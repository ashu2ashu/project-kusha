"""
test_self_improvement_engine.py
Unit tests for the Controlled Autonomous Self-Improvement System.
Framework: IDEX-7.5SC Hybrid Pro

Verifies:
1. Signal collection (test output, analyst feedback, static code audit).
2. Diagnostic categorization and P0–P3 severity assignment.
3. Priority matrix ordering (P0 > P1 > P2 > P3).
4. Proposal generation with 10-point plan structure.
5. Human escalation trigger detection.
6. Bounded operational cycle limits (max 5 cycles).
7. Dry-run mode invariants.
"""

import unittest
import os
import json
import shutil
import tempfile
from unittest.mock import patch
from typing import Dict, Any

from self_improvement_engine import (
    SignalCollector,
    DiagnosticEngine,
    PriorityMatrix,
    ImprovementPlanner,
    ImprovementLedgerManager,
    SelfImprovementLoop,
    SEVERITY_P0,
    SEVERITY_P1,
    SEVERITY_P2,
    SEVERITY_P3,
    MAX_CYCLES_PER_RUN,
    FEEDBACK_DIR
)


class TestSignalCollector(unittest.TestCase):
    """Verifies privacy-preserving signal collection."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orig_feedback_dir = FEEDBACK_DIR

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_collect_feedback_signals_and_redact_secrets(self):
        """Ensures feedback is collected and sensitive API key patterns are masked."""
        os.makedirs(FEEDBACK_DIR, exist_ok=True)
        sample_feedback_path = os.path.join(FEEDBACK_DIR, "mock_test_feedback.json")
        sample_payload = {
            "timestamp": "2026-10-28 14:00:00",
            "category": "Incorrect Financial Figure",
            "ticker": "RELIANCE",
            "claim_or_figure": "Reported debt is ₹3,00,000 Cr",
            "expected_or_correct": "Actual standalone debt is ₹1,16,000 Cr",
            "user_comment": "Testing key redaction: AIzaSyD983274982374982374923847923847"
        }
        with open(sample_feedback_path, "w", encoding="utf-8") as f:
            json.dump(sample_payload, f)

        try:
            signals = SignalCollector.collect_feedback_signals()
            mock_sig = next((s for s in signals if s.get("source_file") == "mock_test_feedback.json"), None)
            self.assertIsNotNone(mock_sig, "Mock feedback signal was not collected")
            self.assertEqual(mock_sig.get("ticker"), "RELIANCE")
            # Verify sensitive key pattern is redacted
            self.assertNotIn("AIzaSyD983274982374982374923847923847", mock_sig.get("user_comment", ""))
            self.assertIn("[REDACTED_KEY]", mock_sig.get("user_comment", ""))
        finally:
            if os.path.exists(sample_feedback_path):
                os.remove(sample_feedback_path)


class TestDiagnosticEngineAndPrioritization(unittest.TestCase):
    """Verifies severity assignment and strict P0 > P1 > P2 > P3 priority sorting."""

    def test_severity_ordering(self):
        """Ensures P0 (Security/Integrity) ranks above P1, P2, and P3."""
        mock_findings = [
            {"id": "F3", "title": "Typo in label", "severity": SEVERITY_P3},
            {"id": "F0", "title": "Exposed credentials", "severity": SEVERITY_P0},
            {"id": "F2", "title": "Slow statement query", "severity": SEVERITY_P2},
            {"id": "F1", "title": "Balance sheet equation mismatch", "severity": SEVERITY_P1},
        ]
        sorted_findings = PriorityMatrix.prioritize(mock_findings)
        self.assertEqual(sorted_findings[0]["id"], "F0")  # P0 first
        self.assertEqual(sorted_findings[1]["id"], "F1")  # P1 second
        self.assertEqual(sorted_findings[2]["id"], "F2")  # P2 third
        self.assertEqual(sorted_findings[3]["id"], "F3")  # P3 fourth

    def test_feedback_diagnosis_critical_vs_warning(self):
        """Analyst feedback for financial figures maps to P1; suggestions map to P2."""
        signals = {
            "test_signals": {"passed": True},
            "code_signals": [],
            "feedback_signals": [
                {
                    "category": "Incorrect Financial Figure",
                    "ticker": "INFY",
                    "claim_or_figure": "Operating cash flow ₹15,000 Cr",
                    "expected_or_correct": "Annual report states ₹22,000 Cr"
                },
                {
                    "category": "UI Defect",
                    "ticker": "TCS",
                    "claim_or_figure": "Table header wrap issue",
                    "expected_or_correct": "Single line layout"
                }
            ]
        }
        findings = DiagnosticEngine.diagnose(signals)
        self.assertEqual(len(findings), 2)
        infy_finding = next(f for f in findings if "INFY" in f["title"])
        tcs_finding = next(f for f in findings if "TCS" in f["title"])
        self.assertEqual(infy_finding["severity"], SEVERITY_P1)
        self.assertEqual(tcs_finding["severity"], SEVERITY_P2)


class TestImprovementPlanner(unittest.TestCase):
    """Verifies 10-point plan structure and human escalation flags."""

    def test_10_point_plan_fields(self):
        """Proposal must include all 10 required operational plan dimensions."""
        finding = {
            "id": "FINDING-999",
            "component": "analyzer.py",
            "severity": SEVERITY_P1,
            "title": "Cash conversion calculation edge-case",
            "root_cause": "Division by zero on zero PAT",
            "recommended_action": "Add guard for zero PAT denominator",
            "requires_human_approval": False
        }
        plan = ImprovementPlanner.create_plan(finding)
        required_fields = [
            "proposal_id", "finding_id", "severity", "problem_statement",
            "evidence", "proposed_solution", "files_expected_to_change",
            "expected_benefits", "regression_risks", "tests_to_run",
            "acceptance_criteria", "rollback_plan", "requires_human_approval"
        ]
        for f in required_fields:
            self.assertIn(f, plan)
            self.assertIsNotNone(plan[f])

    def test_human_escalation_for_security_exposure(self):
        """Security exposure findings must have requires_human_approval = True."""
        finding = {
            "id": "FINDING-SEC-1",
            "component": "analyzer.py",
            "severity": SEVERITY_P0,
            "title": "Exposed credential in module",
            "root_cause": "Hardcoded secret",
            "recommended_action": "Revoke and move to environment variable",
            "requires_human_approval": True
        }
        plan = ImprovementPlanner.create_plan(finding)
        self.assertTrue(plan["requires_human_approval"])


class TestSelfImprovementLoop(unittest.TestCase):
    """Verifies loop execution, dry-run safety, and bounded cycle limits."""

    def test_bounded_cycle_limits(self):
        """Loop must safely halt when max cycles are reached."""
        loop = SelfImprovementLoop(dry_run=True)
        loop.cycle_count = MAX_CYCLES_PER_RUN
        result = loop.run_cycle()
        self.assertEqual(result["status"], "HALTED")
        self.assertIn("Maximum cycles per run", result["reason"])

    @patch("self_improvement_engine.VerificationRunner.verify_all")
    @patch("self_improvement_engine.SignalCollector.collect_test_signals")
    def test_dry_run_executes_safely(self, mock_collect, mock_verify):
        """Dry-run completes with status COMPLETED and does not mutate source code."""
        mock_collect.return_value = {
            "signal_type": "TEST_SUITE",
            "passed": True,
            "total_ran": 102,
            "duration_seconds": 0.45,
            "failures": [],
            "raw_summary": "OK"
        }
        mock_verify.return_value = (True, "Passed: True | Duration: 0.45s | Status: OK")

        loop = SelfImprovementLoop(dry_run=True)
        res = loop.run_cycle()
        self.assertEqual(res["status"], "COMPLETED")
        self.assertTrue(res["dry_run"])
        self.assertTrue(res["tests_passed"])


if __name__ == "__main__":
    unittest.main()
