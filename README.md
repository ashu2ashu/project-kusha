# StockSage / Project KUSHA — Equity Research & Forensic Screening Aid

[![Tests & Code Quality](https://github.com/ashu2ashu/project-kusha/actions/workflows/tests.yml/badge.svg)](https://github.com/ashu2ashu/project-kusha/actions/workflows/tests.yml)
[![Data Truth Monitor](https://github.com/ashu2ashu/project-kusha/actions/workflows/monitor.yml/badge.svg)](https://github.com/ashu2ashu/project-kusha/actions/workflows/monitor.yml)

## 1. What this is

A local Streamlit app that sends Indian listed company financials and optional annual-report PDFs to Google Gemini, and renders an AI-generated 8-pillar quality score, forensic checks, and evidence gaps. It is a screening aid, not an audit, valuation, or advice.

## 2. What this is not

- **Not SEBI-registered:** StockSage is an educational and analytical research prototype; it is not registered with SEBI under Research Analysts Regulations (2014) or Investment Advisers Regulations (2013).
- **Not an audit:** Automated forensic consistency checks evaluate reported mathematical relationships; they do not audit books or verify statutory authenticity.
- **Not a DCF:** Price anchors in the Valuation Compass are qualitative model heuristics; no discounted cash flow, WACC, or terminal value is computed.
- **Not real-time:** Market feeds and quote data are delayed and subject to provider revision.
- **Not reproducible across model versions:** The arithmetic after the model returns is deterministic; the scores are not. Identical prompts evaluated across runs or model updates may vary.

## 3. Data sources and freshness

- [Yahoo Finance](https://finance.yahoo.com): Provides ~4 years of unaudited historical statements and delayed price telemetry, subject to provider restatements.
- [BSE India Public Filing Archive](https://www.bseindia.com): Exchange archive queried on-demand to fetch official annual report PDFs; retrieval depends on public availability.
- [Google Gemini Search Grounding](https://ai.google.dev): Web retrieval for recent developments; coverage is bounded by Google Search indexing.

## 4. Quickstart

### Prerequisites
- Python 3.11+ (tested on Python 3.11 and 3.12; Python 3.10 is unsupported)
- Google Gemini API key from [Google AI Studio](https://aistudio.google.com)

### Installation
```bash
# Clone the repository
git clone https://github.com/ashu2ashu/project-kusha.git
cd project-kusha

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Credentials
Enter your key in session memory in the UI at runtime, or store it in `.env`. Note: if you use `.env`, the key is stored in plaintext on disk. Logs redact it.
```bash
echo 'GEMINI_API_KEY="your_api_key_here"' > .env
```

Verify connectivity before launching:
```bash
python tools/check_api_key.py
```

### Launch the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

## 5. Models

<!-- MODELS:START -->
gemini-3.5-flash
gemini-3.5-flash-lite
gemini-3-flash-preview
gemini-flash-lite-latest
gemini-3.8-flash
gemini-flash-latest
<!-- MODELS:END -->

Model availability and free-tier quotas change; verify in AI Studio. Note that `gemini-3.5-flash` is marked deprecated in Google documentation and auto-routed to `gemini-3.6-flash`.

## 6. Demo mode

Toggle **Demo Mode** in the sidebar to review the user interface and report layouts using synthetic sample data (Tata Consumer Products). Demo evaluations use synthetic fixtures, are marked `[SYNTHETIC SAMPLE]`, and do not represent actual fundamental research.

## 7. Security & privacy

PDFs leave your machine and are sent to Google Gemini for token processing; local caches (`.cache/evaluations/`) store analyses in plaintext JSON; Google's free-tier data terms permit training on submitted inputs, which differs from paid tier terms — do not upload confidential filings. Review [docs/PRIVACY.md](docs/PRIVACY.md) for data flows, retention lifecycles, and deletion procedures.

## 8. Limitations

Detailed operational constraints are documented in [docs/LIMITATIONS.md](docs/LIMITATIONS.md). Key boundaries include:
1. AI scores are not reproducible across runs; only the post-model arithmetic is deterministic.
2. Peer comparisons use an FY24 reference dataset rather than live streaming market feeds.
3. Auditor and governance checks (e.g. FOR_08) lack automated public feeds and are normally reported as not evaluated.

Refer to [docs/LEGAL_DECISIONS.md](docs/LEGAL_DECISIONS.md) for regulatory framing and product policy decisions.

## 9. Testing

The suite uses Python's standard library `unittest` framework with hermetic test execution (network access disabled, filesystem isolated to temporary directories):

```bash
# Run the full test suite
python -m unittest discover -s tests

# Run scoring invariant tests
python -m unittest tests.test_golden_companies -v

# Check coverage
coverage run -m unittest discover -s tests && coverage report
```

## 10. Licence

All rights reserved. No licence is granted; no permission to use, copy, modify, or
redistribute is given. The source is currently published at
https://github.com/ashu2ashu/project-kusha. Publication is not a licence grant.

The distribution decision (public repository vs private workspace) is recorded as **OPEN** in
[docs/LEGAL_DECISIONS.md](docs/LEGAL_DECISIONS.md); it has not been confirmed by the owner.

## 11. Monitoring

StockSage runs a scheduled GitHub Actions data-truth monitor to detect silent schema drift, upstream source breakages, and model deprecations. Alerts are filed as GitHub Issues without storing API keys or financial statements. Baseline updates cannot be applied by CI and require an explicit human commit with a documented reason; see [docs/MONITORING.md](docs/MONITORING.md).

