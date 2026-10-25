"""
annual_report_fetcher.py
Automated statutory annual report discovery and ingestion engine.
Locates and streams official BSE/NSE annual report PDFs directly from exchange archives,
enabling 1-click automated multimodal analysis in Google Gemini without manual downloads.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import urljoin, urlparse
import streamlit as st

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
MAX_REDIRECTS = 3


def _is_bse_pdf_url(value: str) -> bool:
    """Accept only HTTPS PDF URLs hosted by BSE or one of its subdomains."""
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower().rstrip(".")
        return (
            parsed.scheme == "https"
            and (host == "bseindia.com" or host.endswith(".bseindia.com"))
            and parsed.username is None
            and parsed.password is None
            and parsed.port in (None, 443)
            and parsed.path.lower().endswith(".pdf")
        )
    except ValueError:
        return False


@st.cache_data(ttl=43200, show_spinner=False)
def get_available_annual_reports(symbol: str) -> List[Dict[str, str]]:
    """
    Discovers available statutory annual report PDFs for an Indian equity symbol.
    Uses Screener.in as a discovery index and returns only HTTPS PDF links hosted
    on BSE domains. The linked document is still a candidate until downloaded.
    """
    if not symbol or symbol == "CUSTOM":
        return []

    clean_sym = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    if not re.fullmatch(r"[A-Z0-9&._-]{1,30}", clean_sym):
        return []
    url = f"https://www.screener.in/company/{clean_sym}/"

    resp = None
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=False)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        reports: List[Dict[str, str]] = []
        seen_urls = set()

        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"].strip())
            text = a.text.strip()
            clean_url = href.split("#")[0]

            if clean_url in seen_urls:
                continue

            # The discovery page is third-party. Never trust link text alone:
            # require a PDF path on an HTTPS BSE host before offering it.
            if not _is_bse_pdf_url(clean_url):
                continue

            is_ar = False
            title = text
            year = ""

            if "annual report" in text.lower():
                is_ar = True
                m = re.search(r"(20\d\d)", text)
                if m:
                    year = m.group(1)
            else:
                parent_text = a.find_parent().text if a.find_parent() else ""
                if "annual" in parent_text.lower() or "report" in parent_text.lower():
                    is_ar = True
                    m = re.search(r"(20\d\d)", parent_text)
                    if m:
                        year = m.group(1)
                        title = f"Annual Report {year}"

            if is_ar:
                seen_urls.add(clean_url)
                reports.append({
                    "title": title if title else f"Annual Report {year}".strip(),
                    "url": clean_url,
                    "year": year or "Latest",
                    "source": "BSE-hosted PDF (discovered via Screener.in)"
                })

        return reports

    except Exception:
        return []
    finally:
        if resp is not None:
            resp.close()


@st.cache_data(ttl=86400, show_spinner=False)
def download_annual_report_bytes(pdf_url: str, max_size_mb: int = 60) -> bytes:
    """
    Streams and downloads the official statutory PDF bytes from the exchange archive.
    Enforces a maximum file size safety limit.
    """
    if not _is_bse_pdf_url(pdf_url):
        raise ValueError("Invalid filing URL. Only HTTPS PDF links hosted by BSE are accepted.")

    max_bytes = max_size_mb * 1024 * 1024
    current_url = pdf_url
    for redirect_count in range(MAX_REDIRECTS + 1):
        if not _is_bse_pdf_url(current_url):
            raise ValueError("Filing redirect left the approved BSE HTTPS PDF hosts.")

        resp = None
        try:
            resp = requests.get(
                current_url,
                headers=HEADERS,
                stream=True,
                timeout=30,
                allow_redirects=False,
            )
            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get("Location")
                if not location:
                    raise RuntimeError("BSE filing redirect did not include a destination.")
                if redirect_count >= MAX_REDIRECTS:
                    raise RuntimeError("BSE filing exceeded the redirect limit.")
                current_url = urljoin(current_url, location)
                continue

            if resp.status_code != 200:
                raise RuntimeError(f"Failed to download statutory filing (HTTP {resp.status_code}).")
            if not _is_bse_pdf_url(getattr(resp, "url", current_url)):
                raise ValueError("Downloaded filing resolved to a non-BSE URL.")

            # Verify content-length if available. Invalid values are a clear
            # source error rather than an uncaught int conversion traceback.
            content_length = resp.headers.get("Content-Length")
            if content_length:
                try:
                    declared_size = int(content_length)
                except (TypeError, ValueError) as exc:
                    raise ValueError("Filing response included an invalid Content-Length.") from exc
                if declared_size > max_bytes:
                    raise ValueError(
                        f"Filing size ({declared_size / (1024 * 1024):.1f} MB) exceeds maximum allowed limit of {max_size_mb} MB."
                    )

            content = bytearray()
            for chunk in resp.iter_content(chunk_size=128 * 1024):
                if chunk:
                    content.extend(chunk)
                    if len(content) > max_bytes:
                        raise ValueError(f"Filing size exceeds maximum allowed limit of {max_size_mb} MB.")

            if not bytes(content).lstrip().startswith(b"%PDF-"):
                raise ValueError("The BSE-hosted response was not a valid PDF document.")
            return bytes(content)
        except requests.RequestException as exc:
            raise RuntimeError(f"Network error while downloading statutory filing: {str(exc)}") from exc
        finally:
            if resp is not None:
                resp.close()

    raise RuntimeError("BSE filing redirect limit was reached.")
