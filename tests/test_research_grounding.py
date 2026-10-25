"""Offline tests for Gemini Google Search grounding and evidence-gap handling."""

import json
import os
import sys
import types as pytypes
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyzer import CANONICAL_PILLARS, analyze_document_with_gemini


def _analysis_json():
    return json.dumps({
        "company_name": "Example Ltd", "sector": "Industrials",
        "pillars": [{"id": p["id"], "name": p["name"], "score": 5, "justification": f"Evidence for pillar {p['id']}"} for p in CANONICAL_PILLARS],
        "final_call": "Neutral pending current filing review.",
        "evidence_gaps": ["Latest shareholding filing date not verified"],
    })


class TestGeminiSearchGrounding(unittest.TestCase):
    def _run_with_mock_client(self, pdf_bytes=None, failure=False, no_sources=False):
        source = pytypes.SimpleNamespace(title="Example Annual Report", uri="https://example.com/report.pdf")
        metadata = pytypes.SimpleNamespace(
            web_search_queries=["Example Ltd annual report 2025", "Example Ltd BSE pledge filing"],
            grounding_chunks=[] if no_sources else [pytypes.SimpleNamespace(web=source)],
            grounding_supports=[] if no_sources else [pytypes.SimpleNamespace(
                segment=pytypes.SimpleNamespace(text="Evidence for pillar 1"),
                grounding_chunk_indices=[0],
            )],
        )
        response = pytypes.SimpleNamespace(
            text=_analysis_json(),
            candidates=[pytypes.SimpleNamespace(grounding_metadata=metadata)],
        )
        uploaded = pytypes.SimpleNamespace(name="files/mock-pdf")
        fake_client = MagicMock()
        fake_client.files.upload.return_value = uploaded
        if failure:
            fake_client.models.generate_content.side_effect = RuntimeError("mock search failure")
        else:
            fake_client.models.generate_content.return_value = response

        class Config:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        type_module = pytypes.ModuleType("google.genai.types")
        type_module.GenerateContentConfig = Config
        type_module.Tool = lambda **kwargs: kwargs
        type_module.GoogleSearch = lambda: "google-search-tool"
        genai_module = pytypes.ModuleType("google.genai")
        genai_module.Client = MagicMock(return_value=fake_client)
        google_module = pytypes.ModuleType("google")
        google_module.genai = genai_module

        modules = {"google": google_module, "google.genai": genai_module, "google.genai.types": type_module}
        with unittest.mock.patch.dict(sys.modules, modules):
            result = analyze_document_with_gemini(
                "Example Ltd", "Industrials", "test-key", pdf_bytes=pdf_bytes
            )
        return result, fake_client, uploaded

    def test_search_tool_is_configured_with_and_without_uploaded_pdf(self):
        for pdf in (None, b"%PDF-mock"):
            with self.subTest(uploaded_pdf=bool(pdf)):
                _, client, uploaded = self._run_with_mock_client(pdf_bytes=pdf)
                config = client.models.generate_content.call_args.kwargs["config"]
                self.assertEqual(config.tools, [{"google_search": "google-search-tool"}])
                contents = client.models.generate_content.call_args.kwargs["contents"]
                if pdf:
                    self.assertIn(uploaded, contents)
                else:
                    self.assertTrue(any(isinstance(item, str) for item in contents))
                    self.assertNotIn(uploaded, contents)

    def test_grounding_queries_sources_and_claim_citations_are_preserved(self):
        result, _, _ = self._run_with_mock_client()
        research = result["web_research"]
        self.assertTrue(research["search_performed"])
        self.assertEqual(research["search_queries"], ["Example Ltd annual report 2025", "Example Ltd BSE pledge filing"])
        self.assertEqual(research["sources"][0]["title"], "Example Annual Report")
        self.assertEqual(research["sources"][0]["url"], "https://example.com/report.pdf")
        self.assertTrue(research["sources"][0]["retrieved_at"])
        self.assertEqual(result["pillars"][0]["citations"][0]["source_id"], "S1")
        self.assertEqual(result["analysis_status"], "insufficient_evidence")

    def test_search_failure_returns_explicit_evidence_gap(self):
        result, client, _ = self._run_with_mock_client(failure=True)
        self.assertEqual(result["analysis_status"], "insufficient_evidence")
        self.assertIn("Google Search grounding failed", result["evidence_gaps"][0])
        self.assertFalse(result["web_research"]["search_performed"])
        self.assertIn("INSUFFICIENT EVIDENCE", result["final_call"])
        self.assertGreater(client.models.generate_content.call_count, 0)

    def test_search_without_useful_source_urls_returns_evidence_gap(self):
        result, _, _ = self._run_with_mock_client(no_sources=True)
        self.assertEqual(result["analysis_status"], "insufficient_evidence")
        self.assertIn("no usable web source URLs", result["evidence_gaps"][-1])
        self.assertEqual(result["web_research"]["sources"], [])
        self.assertEqual(result["pillars"][0]["evidence_status"], "insufficient_evidence")
        self.assertIn("INSUFFICIENT EVIDENCE", result["final_call"])


if __name__ == "__main__":
    unittest.main()
