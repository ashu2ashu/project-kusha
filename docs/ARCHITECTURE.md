# Project KUSHA — Architecture & Module Map

## Post-Phase 6 Module Map

- `analyzer.py`: Canonical pillars, score bands, deterministic arithmetic reconciliation, and verdict classification (pure).
- `annual_report_fetcher.py`: Statutory annual report retrieval and ingestion helpers (pure).
- `app.py`: Streamlit entrypoint, session state orchestration, user inputs, and top-level analysis execution flow.
- `cli.py`: Headless command-line execution runner for automated audits (pure).
- `data_integrity_agent.py`: Pre-flight sanity checks, schema validation, and outlier detection (pure).
- `evaluation_cache.py`: Content-hashed disk evaluation cache with 24h TTL policy (pure).
- `financial_trends.py`: Balance sheet metrics, DuPont breakdown, CAGR, and financial ratio math (pure).
- `forensic_risk_engine.py`: Multi-check forensic accounting engine and fraud risk heuristics (pure).
- `kusha_logging.py`: Standardized stderr logging with security redaction filters (pure).
- `kusha_render.py`: Pure visualization engine building HTML components, cards, and Plotly figures (pure).
- `nifty_peer_comparison.py`: Peer group analysis, relative valuation, and sector ranking (pure).
- `nifty_universe.py`: Nifty index constituents, company metadata, and quote retrieval (pure).
- `prompt_template.py`: IDEX-7.5SC system prompt template, schema, and pillar synchronization assertion (pure).
- `self_improvement_engine.py`: Improvement ledger maintenance and drift correction telemetry (pure).

## Runtime Purity & Testability

13 of the 14 modules are pure Python: they contain zero Streamlit imports and execute without a
Streamlit runtime context (`ScriptRunContext`). They are directly unit-testable via standard `unittest`.
Only `app.py` interacts with Streamlit UI state and widgets.

## Monolith Flow Scope Decision

The main analysis flow (~1,236 lines inside `app.py`) remains top-level procedural script.
It was deliberately **not** split into modules in Phase 6. A blind refactor of top-level procedural
script without end-to-end integration test coverage risks silent runtime breakage while unit tests
remain green.

### Preconditions for MVC Split

Before `app.py`'s top-level execution script can be decomposed into an MVC controller:
1. End-to-end `AppTest`-driven test suite covering user input -> execution pipeline -> render stage.
2. Verified automated test for the happy path (successful audit with cache save).
3. Verified automated test for at least one failure path (e.g. rate limit / network error fallback).
Once this harness is green, the execution flow can safely be extracted into structured controller classes.
