# 🇮🇳 StockSage / Project KUSHA — Institutional Equity Research & Forensic Intelligence Terminal

StockSage is an institutional-grade equity intelligence terminal designed for evaluating Indian NSE/BSE listed companies. It pairs automated data consistency checks and third-party market data feeds with the 8-Pillar IDEX-7.5SC evaluation framework powered by Google Gemini.

---

## 🏛️ The 8-Pillar IDEX-7.5SC Framework (Core Score: 100 Max)

StockSage scores companies deterministically across 8 canonical pillars:

1. **Governance & Capital Allocation (Max: 20.0 pts)** — Promoter integrity, capital reinvestment discipline, board independence, dilution control, and M&A track record.
2. **Forensic Accounting & Cash Flow (Max: 20.0 pts)** — Cash flow conversion (CFO vs PAT), accrual quality, working capital sanity, and embedded **Sector-Specific Receivable Health Layer** (DSO, aging >90 days, provision coverage).
3. **Risk, ESG & Fragility (Max: 12.0 pts)** — Balance sheet leverage (Net Debt/EBITDA), debt service coverage, environmental/litigation exposure, and raw material volatility.
4. **Valuation & Sanity Layer (Max: 6.0 pts)** — Relative valuation multiples (P/E, EV/EBITDA, P/B), DCF margin of safety, and operational stress testing.
5. **Moat Durability & Scalability (Max: 13.0 pts)** — Pricing power, distribution reach, network effects, cost advantage, and brand durability.
6. **Simplicity & Repeatability (Max: 5.0 pts)** — Business clarity, revenue predictability, subsidiary hygiene, and low execution complexity.
7. **Innovation & TAM Optionality (Max: 18.0 pts)** — R&D velocity, new market adjacency expansion, and addressable total market optionality.
8. **Insider & Minority Shareholder Risk (Max: 6.0 pts)** — Promoter share pledging (PPRM), insider transactions, and related-party transaction (RPT) transparency.

### Deterministic Application Guardrails
- **Promoter Integrity Override (PIO)**: Hard triggers (auditor resignations, SEBI/regulatory enforcement, material RPT misuse, or promoter pledging >50%) automatically clamp Governance to $\le 6.0/20$, revoke all bonuses, enforce `GOV-RED 🔴`, and cap the score in fragile territory (<50.0).
- **Penalty Cap**: Risk deductions are deterministically capped at `-7.5` points maximum.
- **Bonus Cap**: Trajectory and resilience bonuses are deterministically capped at `+10%` of core score (+10.0 points maximum).

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
- `gemini-2.5-flash` (Default — fast, authoritative reasoning)
- `gemini-2.0-flash`
- `gemini-1.5-flash`

---

## 🔒 Security Best Practices
- **Protections Enabled**: Streamlit CORS and XSRF protections are active by default in `.streamlit/config.toml`.
- **Secret Hygiene**: Do not pass API keys as command-line arguments. Keep secrets in environment variables or Streamlit secrets (`.streamlit/secrets.toml`), which are excluded by `.gitignore`.
- **Untrusted Input Protection**: Uploaded PDFs and financial texts are treated strictly as untrusted external evidence; prompt injection defenses prevent uploaded text from altering evaluation methodology or scoring schema.

---

## ⚖️ Disclaimer
StockSage is an educational and analytical research software tool. All valuations, scores, ratings, and estimates are generated algorithmically and do not constitute financial, investment, legal, tax, or accounting advice. Always consult a qualified SEBI-registered financial advisor before making investment decisions.
