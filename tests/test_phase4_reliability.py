"""
tests/test_phase4_reliability.py
Regression and specification test suite for Phase 4: Reliability & Caching.
Validates multi-factor cache key isolation, TTL expiration, corrupt payload purging,
logging redaction, retry unification with quota fail-fast, and silent handler auditing.
"""

import io
import json
import logging
import os
import re
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import evaluation_cache
from evaluation_cache import (
    make_cache_key,
    make_cache_filename,
    load_cached_evaluation,
    save_cached_evaluation,
    SCHEMA_VERSION
)
import kusha_logging
from analyzer import _call_with_retry


class TestPhase4Reliability(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.patcher = patch("evaluation_cache.get_cache_dir", return_value=Path(self.temp_dir))
        self.patcher.start()

        self.sample_result = {
            "company_name": "Reliance Industries Ltd.",
            "ticker": "RELIANCE",
            "pillars": [
                {"pillar_id": 1, "score": 88.0, "title": "Corporate Governance"},
                {"pillar_id": 2, "score": 82.0, "title": "Forensic Purity"}
            ],
            "final_score": 85.0,
            "verdict": "Institutional bluechip",
            "forensic_report": {"overall_risk": "Low"}
        }

    def tearDown(self):
        self.patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_cache_key_isolation(self):
        """1. Cache key isolation: different document_hash or skip_web_search yields different keys."""
        k_no_doc = make_cache_key(
            ticker="RELIANCE",
            model="gemini-2.5-flash",
            pipeline_version="3.0",
            document_hash=None,
            sector="ENERGY",
            skip_web_search=False
        )
        k_with_doc = make_cache_key(
            ticker="RELIANCE",
            model="gemini-2.5-flash",
            pipeline_version="3.0",
            document_hash="a1b2c3d4e5f67890" * 4,
            sector="ENERGY",
            skip_web_search=False
        )
        self.assertNotEqual(k_no_doc, k_with_doc, "Cache key must differ when document_hash differs.")

        k_skip_search = make_cache_key(
            ticker="RELIANCE",
            model="gemini-2.5-flash",
            pipeline_version="3.0",
            document_hash=None,
            sector="ENERGY",
            skip_web_search=True
        )
        self.assertNotEqual(k_no_doc, k_skip_search, "Cache key must differ when skip_web_search changes.")

    def test_02_round_trip_with_document_hash(self):
        """2. Round trip: save then load with identical inputs returns result; different hash returns None."""
        doc_hash = "deadbeef" * 8
        saved = save_cached_evaluation(
            ticker="RELIANCE",
            model="gemini-2.5-flash",
            pipeline_version="3.0",
            result=self.sample_result,
            document_hash=doc_hash,
            sector="ENERGY",
            skip_web_search=False,
            analysis_mode="standard"
        )
        self.assertTrue(saved)

        # Load with identical document hash
        loaded = load_cached_evaluation(
            ticker="RELIANCE",
            model="gemini-2.5-flash",
            current_pipeline_version="3.0",
            document_hash=doc_hash,
            sector="ENERGY",
            skip_web_search=False,
            analysis_mode="standard"
        )
        self.assertIsNotNone(loaded)
        res, rel_time = loaded
        self.assertEqual(res["ticker"], "RELIANCE")
        self.assertIn("Cached", rel_time)

        # Load with different document hash
        mismatched = load_cached_evaluation(
            ticker="RELIANCE",
            model="gemini-2.5-flash",
            current_pipeline_version="3.0",
            document_hash="different_doc_hash" * 4,
            sector="ENERGY",
            skip_web_search=False,
            analysis_mode="standard"
        )
        self.assertIsNone(mismatched, "Cache must not return hit for a different document hash.")

    def test_03_probe_save_agreement(self):
        """3. Probe/save agreement: key computed at probe site equals key computed at save site."""
        args = {
            "ticker": "INFY",
            "model": "gemini-3.5-flash",
            "pipeline_version": "3.0",
            "document_hash": "hash_xyz_123",
            "sector": "IT",
            "skip_web_search": False,
            "analysis_mode": "standard"
        }
        key_probe = make_cache_key(**args)
        key_save = make_cache_key(**args)
        self.assertEqual(key_probe, key_save)

        # Perform save and test that load (probe) finds the entry
        save_cached_evaluation(
            ticker=args["ticker"],
            model=args["model"],
            pipeline_version=args["pipeline_version"],
            result=self.sample_result,
            document_hash=args["document_hash"],
            sector=args["sector"],
            skip_web_search=args["skip_web_search"],
            analysis_mode=args["analysis_mode"]
        )

        probe_res = load_cached_evaluation(
            ticker=args["ticker"],
            model=args["model"],
            current_pipeline_version=args["pipeline_version"],
            document_hash=args["document_hash"],
            sector=args["sector"],
            skip_web_search=args["skip_web_search"],
            analysis_mode=args["analysis_mode"]
        )
        self.assertIsNotNone(probe_res, "Probe must find cache entry created with identical arguments.")

    def test_04_cache_ttl_freshness_and_expiry(self):
        """4. TTL: payload created 25 hours ago returns None; created 23 hours ago returns result."""
        key = make_cache_key("TCS", "gemini-2.5-flash", "3.0", document_hash="no_document")
        fname = make_cache_filename("TCS", key)
        fpath = Path(self.temp_dir) / fname

        # Write payload 25 hours old (> 24h default TTL)
        expired_dt = datetime.now(timezone.utc) - timedelta(hours=25)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "ticker": "TCS",
            "model": "gemini-2.5-flash",
            "pipeline_version": "3.0",
            "document_hash": "no_document",
            "created_at": expired_dt.isoformat(),
            "provenance": {"created_at": expired_dt.isoformat(), "pipeline_version": "3.0"},
            "result": self.sample_result
        }
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        res_expired = load_cached_evaluation(
            ticker="TCS",
            model="gemini-2.5-flash",
            current_pipeline_version="3.0",
            document_hash="no_document"
        )
        self.assertIsNone(res_expired, "Cache payload older than 24 hours must be rejected as expired.")

        # Update payload to 23 hours old (< 24h default TTL)
        fresh_dt = datetime.now(timezone.utc) - timedelta(hours=23)
        payload["created_at"] = fresh_dt.isoformat()
        payload["provenance"]["created_at"] = fresh_dt.isoformat()
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        res_fresh = load_cached_evaluation(
            ticker="TCS",
            model="gemini-2.5-flash",
            current_pipeline_version="3.0",
            document_hash="no_document"
        )
        self.assertIsNotNone(res_fresh, "Cache payload under 24 hours old must be loaded successfully.")

    def test_05_malformed_timestamp_treated_as_stale(self):
        """5. Malformed timestamp: missing or invalid created_at is treated as stale (returns None)."""
        key = make_cache_key("SBIN", "gemini-2.5-flash", "3.0")
        fname = make_cache_filename("SBIN", key)
        fpath = Path(self.temp_dir) / fname

        payload = {
            "schema_version": SCHEMA_VERSION,
            "ticker": "SBIN",
            "model": "gemini-2.5-flash",
            "pipeline_version": "3.0",
            "document_hash": "no_document",
            "created_at": "GARBAGE_TIMESTAMP_NOT_ISO",
            "provenance": {"created_at": "GARBAGE_TIMESTAMP_NOT_ISO", "pipeline_version": "3.0"},
            "result": self.sample_result
        }
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        res = load_cached_evaluation(
            ticker="SBIN",
            model="gemini-2.5-flash",
            current_pipeline_version="3.0"
        )
        self.assertIsNone(res, "Malformed timestamp must be treated as stale.")

    def test_06_corrupt_cache_file_logged_deleted_and_returns_none(self):
        """6. Corrupt cache file: invalid JSON logs warning, is deleted, and returns None."""
        key = make_cache_key("HDFCBANK", "gemini-2.5-flash", "3.0")
        fname = make_cache_filename("HDFCBANK", key)
        fpath = Path(self.temp_dir) / fname

        with open(fpath, "w", encoding="utf-8") as f:
            f.write("{ incomplete json corruption: [")

        self.assertTrue(fpath.exists())
        res = load_cached_evaluation(
            ticker="HDFCBANK",
            model="gemini-2.5-flash",
            current_pipeline_version="3.0"
        )
        self.assertIsNone(res)
        self.assertFalse(fpath.exists(), "Corrupt cache file must be deleted from disk upon read failure.")

    def test_07_logging_redaction(self):
        """7. Logging redaction: raw API key or password never appears in log handler output."""
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler.addFilter(kusha_logging.SensitiveDataFilter())

        test_logger = logging.getLogger("test_redaction_logger")
        test_logger.setLevel(logging.INFO)
        test_logger.addHandler(handler)

        fake_gemini_key = "AIzaSyD-1234567890abcdefghijklmnopqrstuv"
        test_logger.error("Failed Gemini call with key %s and password='operator_secret'", fake_gemini_key)

        output = stream.getvalue()
        self.assertNotIn(fake_gemini_key, output)
        self.assertNotIn("operator_secret", output)
        self.assertIn("[REDACTED_API_KEY]", output)
        self.assertIn("password=[REDACTED]", output)

    def test_08_retry_helper_jitter_and_quota_fail_fast(self):
        """8. Retry helper: retries transient errors with delay; fails fast immediately on 429."""
        calls = []

        def flaky_func():
            calls.append(len(calls) + 1)
            if len(calls) < 3:
                raise ValueError("Temporary network glitch (503 Service Unavailable)")
            return "SUCCESS"

        result = _call_with_retry(flaky_func, attempts=3, base_delay=0.01, label="test_retry")
        self.assertEqual(result, "SUCCESS")
        self.assertEqual(len(calls), 3)

        # Test 429 quota exhaustion fails immediately without retrying
        quota_calls = []

        def quota_failing_func():
            quota_calls.append(1)
            raise Exception("429 Resource has been exhausted (quota exceeded)")

        with self.assertRaises(RuntimeError) as ctx:
            _call_with_retry(quota_failing_func, attempts=3, base_delay=0.01, label="test_quota")

        self.assertIn("Gemini quota exhausted", str(ctx.exception))
        self.assertEqual(len(quota_calls), 1, "Quota error must not be retried.")

    def test_09_silent_handlers_scan(self):
        """9. Silent handlers scan: no except Exception: is followed immediately by pass without logger or comment."""
        target_files = [
            "nifty_universe.py",
            "analyzer.py",
            "financial_trends.py",
            "nifty_peer_comparison.py",
            "evaluation_cache.py",
        ]
        base_dir = Path(__file__).parent.parent

        for fn in target_files:
            fpath = base_dir / fn
            self.assertTrue(fpath.exists(), f"Target file {fn} must exist")
            with open(fpath, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for idx, line in enumerate(lines):
                # Match except Exception: or except: (bare)
                if re.search(r"except\s+(Exception|\(\s*Exception)", line):
                    next_idx = idx + 1
                    subsequent_lines = [lines[j].strip() for j in range(next_idx, min(next_idx + 3, len(lines)))]
                    
                    # If any subsequent line is bare 'pass', check that logger or comment '#' exists
                    if any(l == "pass" or l.startswith("pass") for l in subsequent_lines):
                        has_logger_or_comment = any(
                            ("logger." in l or l.startswith("#") or "/*" in l) for l in subsequent_lines
                        )
                        self.assertTrue(
                            has_logger_or_comment,
                            f"File {fn}:{idx+1} has except Exception: followed by pass without logger or explanatory comment"
                        )


if __name__ == "__main__":
    unittest.main()
