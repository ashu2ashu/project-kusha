# 🇮🇳 StockSage / Project KUSHA — Equity Research & Forensic Screening Terminal

StockSage is an equity intelligence and forensic screening terminal designed for evaluating Indian NSE/BSE listed companies. It pairs automated data consistency checks and public market data feeds with the 8-Pillar IDEX-7.5SC evaluation framework powered by Google Gemini.

---

## 🏛️ The 8-Pillar IDEX-7.5SC Framework (Core Score: 0–100)

StockSage evaluates companies deterministically across 8 canonical vectors:

1. **Governance & Capital Allocation** — Promoter integrity, capital reinvestment discipline, board independence, dilution control, and M&A track record.
2. **Forensic Accounting & Cash Flow** — Cash flow conversion (CFO vs PAT), accrual quality, working capital sanity, and embedded **Sector-Specific Receivable Health Layer** (DSO, aging >90 days, provision coverage).
3. **Risk, ESG & Fragility** — Balance sheet leverage (Net Debt/EBITDA), debt service coverage, environmental/litigation exposure, and raw material volatility.
4. **Valuation & Sanity Layer** — Relative valuation multiples (P/E, EV/EBITDA, P/B), DCF margin of safety corridors, and operational stress testing.
5. **Moat Durability & Scalability** — Pricing power, distribution reach, network effects, cost advantage, and brand durability.
6. **Simplicity & Repeatability** — Business clarity, revenue predictability, subsidiary hygiene, and low execution complexity.
7. **Innovation & TAM Optionality** — R&D velocity, new market adjacency expansion, and addressable total market optionality.
8. **Insider & Minority Shareholder Risk** — Promoter share pledging (PPRM), insider transactions, and related-party transaction (RPT) transparency.

### Deterministic Application Guardrails
- **Promoter Integrity Override (PIO)**: Hard distress triggers (auditor qualifications/resignations, regulatory enforcement, material RPT misuse, or excessive promoter share pledging) automatically trigger a governance circuit breaker, revoke upside bonuses, enforce `GOV-RED 🔴`, and clamp the overall score into high-risk territory.
- **Controlled Penalty & Bonus Curves**: Risk deductions and trajectory bonuses are mathematically bounded to prevent outsized distortions and eliminate black-box volatility.
- **Trade Secret Protection**: Exact algorithmic weights, penalty multipliers, and non-linear scoring curves are compiled under internal IP safeguards.

---

## 🔍 Data Consistency Engine (Internal Quality Checks)

Before scoring proceeds, the built-in consistency engine evaluates ingested statements against 6 mathematical sanity checks:
1. **Balance Sheet Equation**: Confirms Assets cover Net Worth and Liabilities.
2. **Cash Flow Reconcilement**: Tests CFO - |Capex| against Free Cash Flow.
3. **Accrual Quality**: Compares Operating Cash Flow to Net Profit to flag non-cash earnings.
4. **P&L Structural Hierarchy**: Verifies Revenue covers Operating Profit and Net Profit.
5. **Market Pricing Bounds**: Checks current price within official 52-week channels.
6. **Reporting History Depth**: Confirms multi-year reporting depth.

> [!NOTE]
> **Data Scope Disclosure**: Automated consistency checks evaluate internal arithmetic relationships within ingested third-party data. They do **not** constitute an independent statutory audit, certification of filing authenticity, or guarantee against accounting fraud. Market data is provided via Yahoo Finance (unverified third-party feeds; delayed).

---

## ⚡ Automated Statutory Annual Report Ingestion (BSE India)

StockSage automatically queries public exchange archives to discover and stream official statutory annual report PDFs directly into Google Gemini for analysis:
- **1-Click Regulatory Retrieval**: Selecting any tracked Indian equity displays available official annual reports (2024, 2023, etc.) with verified exchange links.
- **100% Free Public Access**: Zero marker/API costs—streams official statutory filings directly from BSE India regulatory archives (`bseindia.com/xml-data/corpfiling/AttachHis/...`).
- **Native Multimodal Extraction**: Official PDFs are ingested natively by Gemini's multimodal document engine alongside live Google Search grounding.
- **Statutory Provenance Tracking**: Every evaluation retains document metadata and a direct link to the official BSE India regulatory filing.

---

## 🚀 Quickstart & Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.11)
- Google Gemini API key from [Google AI Studio](https://aistudio.google.com)

### 1. Clone & Setup Environment
```bash
git clone https://github.com/ashu2ashu/project-kusha.git
cd project-kusha

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Your API Key
Copy `.env.example` or create a `.env` file in the project root:
```bash
echo 'GEMINI_API_KEY="your_actual_key_here"' > .env
```
*(Alternatively, enter your key securely in the application password field at runtime. Keys are kept in session memory and never persisted to logs or disk.)*

### 3. Verify Key Connectivity
```bash
python3 test_key.py
```

### 4. Launch the Terminal
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Demo Mode
To explore the user interface, interactive charts, and 8-pillar visualizations without an API key:
- Toggle **Demo Mode** in the sidebar.
- Click **Quick Demo** to run a sample evaluation on synthetic demonstration data.
- All demo outputs are visibly marked as `[SYNTHETIC DEMO SAMPLE]` and must not be used as investment research or advice.

---

## 🤖 Supported Gemini Models
StockSage supports Google Gemini models configurable directly from the sidebar:
- `gemini-3.5-flash` (Default — fast, ultra-low latency multimodal reasoning)
- `gemini-3.5-flash-lite` (Lightweight fallback with dedicated free tier quota)
- `gemini-3-flash-preview`
- `gemini-flash-lite-latest`
- `gemini-3.8-flash` (Advanced reasoning, recommended by Google)
- `gemini-flash-latest`

---

## 🔒 Security Best Practices
- **Protections Enabled**: Streamlit CORS and XSRF protections are active by default in `.streamlit/config.toml`.
- **Secret Hygiene**: Do not pass API keys as command-line arguments. Keep secrets in environment variables or Streamlit secrets (`.streamlit/secrets.toml`), which are excluded by `.gitignore`.
- **Untrusted Input Protection**: Uploaded PDFs and financial texts are treated strictly as untrusted external evidence; prompt injection defenses prevent uploaded text from altering evaluation methodology or scoring schema.

---

## ⚖️ Regulatory Notice & Disclaimer
StockSage / Project KUSHA is an automated analytical research and educational technology prototype. It is NOT registered with the Securities and Exchange Board of India (SEBI) as an Investment Adviser (under IA Regulations, 2013) or Research Analyst (under RA Regulations, 2014).

All valuations, scores, ratings, traffic-light badges, and estimates are generated algorithmically for screening purposes and do NOT constitute financial, investment, legal, tax, or accounting advice. Always consult a qualified SEBI-registered financial advisor before making capital allocation decisions.
