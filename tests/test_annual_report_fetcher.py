"""
tests/test_annual_report_fetcher.py
Unit tests for automated statutory annual report discovery and ingestion.
"""

import unittest
from unittest.mock import patch, MagicMock
from annual_report_fetcher import get_available_annual_reports, download_annual_report_bytes
from analyzer import analyze_document_with_gemini
from app import build_filing_ingestion_notice_html


class TestAnnualReportFetcher(unittest.TestCase):

    def test_empty_or_custom_symbol_returns_empty_list(self):
        self.assertEqual(get_available_annual_reports(""), [])
        self.assertEqual(get_available_annual_reports(None), [])
        self.assertEqual(get_available_annual_reports("CUSTOM"), [])

    @patch("annual_report_fetcher.requests.get")
    def test_parses_statutory_bse_filing_links(self, mock_get):
        sample_html = """
        <html>
            <body>
                <div>
                    <h3>Annual Reports</h3>
                    <a href="https://www.bseindia.com/xml-data/corpfiling/AttachHis/abc-123.pdf">Annual Report 2024</a>
                    <a href="https://www.bseindia.com/xml-data/corpfiling/AttachHis/def-456.pdf">Annual Report 2023</a>
                    <a href="https://www.bseindia.com/xml-data/corpfiling/AttachHis/abc-123.pdf#page=1">Annual Report 2024 duplicate</a>
                    <a href="https://example.com/Annual-Report-2025.pdf">Annual Report 2025</a>
                    <a href="https://example.com/unrelated.pdf">Investor Presentation</a>
                    <a href="https://bseindia.com.example.com/Annual-Report-2022.pdf">Annual Report 2022</a>
                </div>
            </body>
        </html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = sample_html
        mock_get.return_value = mock_resp

        reports = get_available_annual_reports("TESTSTOCK")
        self.assertGreaterEqual(len(reports), 2)
        urls = [r["url"] for r in reports]
        self.assertIn("https://www.bseindia.com/xml-data/corpfiling/AttachHis/abc-123.pdf", urls)
        self.assertIn("https://www.bseindia.com/xml-data/corpfiling/AttachHis/def-456.pdf", urls)
        self.assertEqual(reports[0]["source"], "BSE-hosted PDF (discovered via Screener.in)")
        self.assertEqual(len(reports), 2)

    def test_rejects_malformed_symbol_before_request(self):
        with patch("annual_report_fetcher.requests.get") as mock_get:
            self.assertEqual(get_available_annual_reports("../../etc/passwd"), [])
            mock_get.assert_not_called()

    @patch("annual_report_fetcher.requests.get")
    def test_network_failure_returns_empty_list(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        reports = get_available_annual_reports("FAILSTOCK")
        self.assertEqual(reports, [])

    def test_download_annual_report_invalid_url(self):
        with self.assertRaises(ValueError):
            download_annual_report_bytes("")
        with self.assertRaises(ValueError):
            download_annual_report_bytes("ftp://invalid-url.pdf")
        with self.assertRaises(ValueError):
            download_annual_report_bytes("http://www.bseindia.com/report.pdf")
        with self.assertRaises(ValueError):
            download_annual_report_bytes("https://example.com/report.pdf")
        with self.assertRaises(ValueError):
            download_annual_report_bytes("https://bseindia.com.example.com/report.pdf")

    @patch("annual_report_fetcher.requests.get")
    def test_rejects_redirect_to_untrusted_host(self, mock_get):
        response = MagicMock()
        response.status_code = 302
        response.headers = {"Location": "http://127.0.0.1/private.pdf"}
        mock_get.return_value = response

        with self.assertRaisesRegex(ValueError, "redirect left the approved"):
            download_annual_report_bytes("https://www.bseindia.com/report.pdf")

        mock_get.assert_called_once()
        response.close.assert_called_once()

    @patch("annual_report_fetcher.requests.get")
    def test_accepts_redirect_within_bse_host_family(self, mock_get):
        redirect = MagicMock()
        redirect.status_code = 302
        redirect.headers = {"Location": "https://archives.bseindia.com/reports/report.pdf"}
        response = MagicMock()
        response.status_code = 200
        response.url = "https://archives.bseindia.com/reports/report.pdf"
        response.headers = {"Content-Length": "9"}
        response.iter_content.return_value = [b"%PDF-1.4"]
        mock_get.side_effect = [redirect, response]

        data = download_annual_report_bytes("https://www.bseindia.com/reports/report.pdf")

        self.assertTrue(data.startswith(b"%PDF-"))
        self.assertEqual(mock_get.call_count, 2)
        redirect.close.assert_called_once()
        response.close.assert_called_once()

    @patch("annual_report_fetcher.requests.get")
    def test_download_annual_report_size_limit_exceeded(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Length": str(100 * 1024 * 1024)}  # 100 MB
        mock_resp.url = "https://bseindia.com/test.pdf"
        mock_get.return_value = mock_resp

        with self.assertRaises(ValueError) as ctx:
            download_annual_report_bytes("https://bseindia.com/test.pdf", max_size_mb=50)
        self.assertIn("exceeds maximum allowed limit", str(ctx.exception))
        mock_resp.close.assert_called_once()

    @patch("annual_report_fetcher.requests.get")
    def test_download_annual_report_streaming_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Length": "1024"}
        mock_resp.url = "https://bseindia.com/test.pdf"
        mock_resp.iter_content = MagicMock(return_value=[b"%PDF-1.4 sample content", b" additional chunk"])
        mock_get.return_value = mock_resp

        data = download_annual_report_bytes("https://bseindia.com/test.pdf", max_size_mb=10)
        self.assertTrue(data.startswith(b"%PDF-1.4"))
        self.assertEqual(data, b"%PDF-1.4 sample content additional chunk")
        mock_resp.close.assert_called_once()

    @patch("annual_report_fetcher.requests.get")
    def test_rejects_non_pdf_response(self, mock_get):
        response = MagicMock()
        response.status_code = 200
        response.headers = {"Content-Length": "18"}
        response.url = "https://bseindia.com/test.pdf"
        response.iter_content.return_value = [b"<html>not a PDF</html>"]
        mock_get.return_value = response

        with self.assertRaisesRegex(ValueError, "not a valid PDF"):
            download_annual_report_bytes("https://bseindia.com/test.pdf")
        response.close.assert_called_once()

    @patch("google.genai.Client")
    def test_analyze_document_preserves_filing_metadata(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.return_value = None  # Triggers gap_result

        filing_meta = {
            "title": "Annual Report 2024",
            "year": "2024",
            "url": "https://www.bseindia.com/xml-data/corpfiling/AttachHis/sample.pdf",
            "source": "BSE-hosted PDF (discovered via Screener.in)"
        }
        res = analyze_document_with_gemini(
            company_name="Tata Consumer Products",
            sector="FMCG",
            api_key="mock_key",
            pdf_bytes=b"%PDF-test",
            filing_metadata=filing_meta
        )
        self.assertEqual(res.get("filing_metadata", {}).get("ingestion_status"), "not_analyzed")
        self.assertEqual(res.get("filing_metadata", {}).get("source"), filing_meta["source"])

    def test_filing_notice_never_claims_success_for_unanalyzed_document(self):
        rendered = build_filing_ingestion_notice_html({
            "title": "Annual Report",
            "source": "BSE-hosted PDF (discovered via Screener.in)",
            "url": "https://www.bseindia.com/report.pdf",
            "ingestion_status": "not_analyzed",
        })
        self.assertIn("Filing listed · PDF not analyzed", rendered)
        self.assertNotIn("Verified Statutory Document Ingestion", rendered)

    def test_filing_notice_escapes_untrusted_metadata_and_labels_upload(self):
        rendered = build_filing_ingestion_notice_html({
            "title": '<img src=x onerror="alert(1)">',
            "source": "Manual PDF Upload",
            "ingestion_status": "analyzed",
        })
        self.assertIn("&lt;img", rendered)
        self.assertNotIn("<img", rendered)
        self.assertIn("Uploaded PDF analyzed", rendered)
        self.assertIn("source not independently verified", rendered)


if __name__ == "__main__":
    unittest.main()
