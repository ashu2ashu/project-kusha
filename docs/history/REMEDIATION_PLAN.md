> **HISTORICAL — superseded.** This plan references early remediation roadmaps and deprecated model versions (gemini-2.5-flash, gemini-1.5-flash) which have been completed and superseded in Phases 1 through 6.

# StockSage / Project KUSHA — Audit & Remediation Plan

## Summary of Planned Changes by File

### 1. `.streamlit/config.toml` (Priority 1: Security)
- Set `enableCORS = true` (re-enabling Streamlit CORS protection).
- Set `enableXsrfProtection = true` (re-enabling Cross-Site Request Forgery protection).

### 2. `test_key.py` (Priority 1: Security)
- Remove `sys.argv[1]` command-line key intake to prevent secrets leaking into shell history and process table (`ps`).
- Read `GEMINI_API_KEY` from environment variables, or prompt securely using `getpass.getpass()`.
- Ensure error messages never echo or log secret strings.

### 3. `nifty_universe.py` (Priority 2: Truthful Market Data)
- In `fetch_live_market_data()`:
  - Eliminate all magic number synthetic multipliers and silent fallbacks (`* 1.15`, `* 0.85`, `* 0.98`, `13.5`, `18.5`, `12.0`, `14.2`, `0.45`, `1.85`, `0.75`, `8.50`, etc.).
  - Return `None` for any unavailable metric and let UI display `"N/A"`.
  - Add explicit provider attribution: `"data_provider": "Yahoo Finance (Delayed third-party data; unaudited)"`.
  - Attach retrieval timestamp: `"fetched_at": iso_timestamp`.
  - Add retry handling with exponential backoff for network transient errors without inventing substitute data on failure.

### 4. `financial_trends.py` (Priority 2: Truthful Financial Statements)
- In `get_val()`, preserve missing fields as `None` rather than coercing to `0.0`.
- Do not fabricate FCF if raw statements lack necessary data.
- Attach metadata indicating Yahoo Finance third-party aggregation and retrieval date/time.

### 5. `data_integrity_agent.py` (Priority 3: Sentinel Consistency Reframing)
- Rename and reframe from "Autonomous Data Integrity & Forensic Verification Sentinel" to "Data Consistency & Reconciliation Engine".
- Replace inflated certification terms ("Audit Seal", "Authenticity Index", "Certified & Reconciled", "Statutory continuity verified") with honest descriptions ("Arithmetic Consistency Check", "Consistency Index", "Checks Evaluated").
- Treat missing inputs as `"INSUFFICIENT_DATA"` or `"NOT_CHECKED"`, never as passing or 100/100 score.
- Reframe SHA-256 hash as a `"Consistency Run Identifier"`, clarifying it is a local run ID and does not prove source document authenticity.

### 6. `analyzer.py` (Priorities 4 & 5: Supported Models, Deterministic Scoring, Demo Mode)
- **Supported Models**: Update `SUPPORTED_MODELS` to valid, active Gemini models: `["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]` and allow passing a configurable `model_name`.
- **Deterministic Scoring Engine (`validate_and_reconcile_idex_analysis`)**:
  - Implement strict schema validation verifying all 8 pillars are present with their canonical max points.
  - Enforce bounds on each pillar score (`0.0 <= score <= max_score`).
  - Calculate `core_score` deterministically by summing the 8 pillars.
  - Enforce Promoter Integrity Override (PIO) in Python code: clamp Pillar 1 (Governance) to $\le 6.0/20$, revoke all bonuses (bonus = 0.0), set guardrail tag to `"GOV-RED 🔴"`, and cap final score.
  - Deterministically calculate penalties with a hard cap of `-7.5` points.
  - Deterministically calculate bonuses with a hard cap of `+10%` of core score.
  - Compute `final_score = min(100.0, max(0.0, core_score + total_penalties + total_bonuses))`.
  - Deterministically assign official verdict band.
- **Untrusted Document Handling**: Add security directives treating uploaded files purely as untrusted evidence that cannot alter system rules or prompt constraints.
- **Demo Mode (`get_demo_analysis`)**:
  - Clearly label all sample data as synthetic (`[DEMO / SYNTHETIC DATA]`).
  - Remove company-specific claims about statutory auditors (e.g. Walker Chandiok), 0% pledging, or Tata Group RPTs when analyzing arbitrary stocks.
  - Add explicit disclaimers that demo mode is synthetic and not investment advice or verified research.

### 7. `nifty_peer_comparison.py` (Priority 6: Peer Comparison Dating)
- Add explicit dataset metadata labeling it as "Historical Benchmark Sample (March 2024 / FY24 Audited Statements, updated Oct 2024)".
- Display clear notices in the UI that the peer index is a historical reference benchmark, not live tick data.

### 8. `app.py` (Priorities 2, 3, 4, 6: UI Accuracy & Demo Watermarking)
- Replace misleading labels ("Official Exchange Feeds", "Audited Grounding", "100% Verified") with truthful descriptions ("Delayed Yahoo Finance Market Feeds", "Data Consistency Checks").
- Render `"N/A"` clearly for unavailable metrics.
- Display a prominent, persistent synthetic demo banner across demo mode screens and exports.
- Integrate the configurable Gemini model selector.
- Keep user-entered API keys safely in session state / memory without persisting to disk.

### 9. `README.md` (Priority 6: Documentation)
- Update product title to "StockSage / Project KUSHA".
- Accurately describe the 8-Pillar IDEX-7.5SC framework (fixing the outdated 5-pillar description).
- Document currently supported Gemini models (`gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash`).
- Clarify data providers (Yahoo Finance delayed feeds, user-supplied filings) and Sentinel's true role (automated arithmetic consistency checks).
- Clean up any machine-specific paths and provide accurate setup instructions.

### 10. `tests/test_audit_remediation.py` (Priority 7: Verification)
- Add comprehensive unit tests covering:
  - CORS and XSRF enabled in `.streamlit/config.toml`.
  - Absence of CLI argument leakage in `test_key.py`.
  - Truthful market data: no synthetic fallbacks when fields are missing (returns `None` / `"N/A"`).
  - Schema validation and handling of malformed LLM JSON.
  - Deterministic score reconciliation (core sum, penalty cap `-7.5`, bonus cap `+10%`, verdict band mapping).
  - Promoter Integrity Override enforcement in Python code.
  - Sentinel consistency checks properly returning `"INSUFFICIENT_DATA"` on empty inputs (no false 100/100).
  - Demo mode synthetic labeling and absence of unverified real-company claims.
