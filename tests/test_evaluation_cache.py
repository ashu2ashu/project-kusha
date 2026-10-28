"""
tests/test_evaluation_cache.py
Unit tests for the local evaluation replay cache.
"""

import unittest
import shutil
import tempfile
from pathlib import Path
from evaluation_cache import (
    sanitize_cache_token,
    make_cache_filename,
    save_cached_evaluation,
    load_cached_evaluation,
    get_cache_stats,
    clear_evaluation_cache,
    get_cache_dir
)

class TestEvaluationCache(unittest.TestCase):
    def setUp(self):
        # Create a sample valid result dictionary
        self.sample_result = {
            "company_name": "Tata Consumer Products Ltd.",
            "ticker": "TATACONSUM",
            "pillars": [
                {"pillar_id": 1, "score": 85, "title": "Governance"},
                {"pillar_id": 2, "score": 80, "title": "Forensics"}
            ],
            "final_score": 82.5,
            "verdict": "High financial integrity franchise"
        }
        self.version = "TEST_v1.0"

    def tearDown(self):
        clear_evaluation_cache()

    def test_sanitize_cache_token(self):
        self.assertEqual(sanitize_cache_token("TATACONSUM.NS"), "TATACONSUM")
        self.assertEqual(sanitize_cache_token("RELIANCE.BO"), "RELIANCE")
        self.assertEqual(sanitize_cache_token("Reliance Industries!"), "RELIANCE_INDUSTRIES_")
        self.assertEqual(sanitize_cache_token(""), "UNKNOWN")

    def test_make_cache_filename(self):
        fname = make_cache_filename("Reliance", "RELIANCE", "gemini-2.5-flash")
        self.assertEqual(fname, "eval_RELIANCE_GEMINI-2_5-FLASH.json")
        self.assertTrue(fname.endswith(".json"))

    def test_save_and_load_cached_evaluation(self):
        saved = save_cached_evaluation(
            company_name="Reliance Industries",
            ticker="RELIANCE",
            model="gemini-2.5-flash",
            result=self.sample_result,
            pipeline_version=self.version
        )
        self.assertTrue(saved, "Failed to save evaluation to cache")

        # Load it back
        loaded = load_cached_evaluation(
            company_name="Reliance Industries",
            ticker="RELIANCE",
            model="gemini-2.5-flash",
            current_pipeline_version=self.version
        )
        self.assertIsNotNone(loaded, "Failed to load cached evaluation")
        res, cached_at = loaded
        self.assertEqual(res["ticker"], "TATACONSUM")
        self.assertEqual(res["final_score"], 82.5)
        self.assertTrue(isinstance(cached_at, str))

    def test_load_cached_evaluation_version_mismatch(self):
        save_cached_evaluation(
            company_name="Infosys",
            ticker="INFY",
            model="gemini-2.5-flash",
            result=self.sample_result,
            pipeline_version="OLD_VERSION"
        )
        # Attempt to load with NEW_VERSION
        loaded = load_cached_evaluation(
            company_name="Infosys",
            ticker="INFY",
            model="gemini-2.5-flash",
            current_pipeline_version="NEW_VERSION"
        )
        self.assertIsNone(loaded, "Cache should not load when pipeline version mismatches")

    def test_get_cache_stats_and_clear(self):
        save_cached_evaluation(
            company_name="TCS",
            ticker="TCS",
            model="gemini-2.5-flash",
            result=self.sample_result,
            pipeline_version=self.version
        )
        stats = get_cache_stats()
        self.assertGreaterEqual(stats["count"], 1)
        self.assertGreater(stats["total_kb"], 0)

        # Clear cache
        deleted = clear_evaluation_cache()
        self.assertGreaterEqual(deleted, 1)
        stats_after = get_cache_stats()
        self.assertEqual(stats_after["count"], 0)
        self.assertEqual(stats_after["total_kb"], 0)

if __name__ == "__main__":
    unittest.main()
