# Project KUSHA — Master Remediation Plan

> **Constraint: zero cost.** Free Gemini tier only, stdlib `unittest` (no paid tools),
> free GitHub Actions minutes, no paid data vendors, no paid hosting.
> If a fix needs money, it is deferred or replaced with an honest "unavailable".

**Definition of done (global):** every statement shown to a user is true, and every
number is traceable to a timestamped source. "Zero bugs" is not the goal and is not
claimable.

---

## Status legend

- `[ ]` not started
- `[~]` in progress
- `[x]` done
- `[!]` blocked on a decision (not code)

---

## Phase 1 — Truth layer `[x]`

Goal: the app can no longer invent a clean result, and no longer claims things
the code does not do.

**Done:**

- [x] Four-state checks: `PASS` / `MONITOR` / `CRITICAL` / `INSUFFICIENT_DATA`.
      No default `PASS`. Empty input returns `fqi_score=None`.
- [x] FQI withheld unless ≥ 75% of checks were evaluated (`coverage`,
      `score_issued`, `insufficient_count` added to the report).
- [x] Auditor check no longer fabricates "CLEAN / UNQUALIFIED" — it is
      `INSUFFICIENT_DATA` unless an opinion is explicitly supplied.
- [x] Pledge check parses the numeric value; missing pledge is not treated as 0%.
      Fixed the `"0.00%"` false-positive.
- [x] Credit, CWIP, tax, other-income, receivable checks no longer default to PASS.
- [x] Fraud shield (`render_forensic_fraud_shield_html`) no longer fabricates
      `CLEAN AUDIT`, `0.0% PLEDGED`, `HEALTHY DSO`, `SOLVENT`, `CLEAN RECORD`.
- [x] Valuation compass no longer invents a fair value as `CMP × 1.06`.
- [x] Enum guardrail: `guardrail_level()` replaces `"RED" in tag` at **all five**
      call sites in `app.py` (provenance HUD, management-integrity card, stance
      decision, guardrail banner, alert banner). The first pass fixed only two;
      the rest were caught by the new source-scan test and fixed.
- [x] Negative-PAT accrual logic fixed (loss + cash burn = FAILED).
- [x] Integrity index scales with evaluated checks, not `100 - penalties`.
- [x] False claims removed: DCF, encryption/tamper guard, IP protection,
      "mathematical determinism verified", "10 pillars".
- [x] `PILLAR_METADATA` derived from `analyzer.CANONICAL_PILLARS`.
- [x] Correct attribution: Yahoo Finance (~4 years, unaudited) + real retrieval time.
- [x] Actual model recorded after fallback (`model_used`, `model_requested`,
      `model_fallback_used`, `research_model_used`, `pipeline_version`).
- [x] Escaped model output: `pio_reason`, `receivable_subscore`, guardrail tag,
      evidence list, forensic check text, Appendix B values.
- [x] Regression suite: `tests/test_phase1_truth_layer.py` (15 tests), including a
      `tokenize`-based scan that fails if any `"RED" in <tag>`-style substring
      comparison is reintroduced into `app.py`, `analyzer.py`,
      `forensic_risk_engine.py` or `data_integrity_agent.py`.

**Verified:** 101 tests pass; `AppTest.from_file("app.py")` renders with 0 exceptions.

**Known leftovers for later phases (intentionally not done here):**

- `parse_dcf_estimate` can misread a bare 4-digit year as a fair value → Phase 2.
- Shield is still a second, duplicated implementation of the forensic checks, with
  its own thresholds (e.g. cash conversion PASS at ≥90% while
  `FOR_01` benchmarks ≥80%) → Phase 6.
- Score-band cut-offs are duplicated between `analyzer.py` (90/85/75/60/50) and
  `app.py` (75/60, gauge at 80/60) → Phase 6.
- Corrected: `financial_trends.py` does **not** coerce missing fields to `0.0`, and
  `nifty_universe.fetch_live_market_data` has no synthetic multipliers. An earlier
  draft of this plan claimed both; that was wrong.

## Phase 2 — Data layer `[x]`

- [x] **First:** isolate test storage. Ledger paths injectable; test runs no longer
      mutate `IMPROVEMENT_LEDGER.md` / `improvement_ledger.json`
      (verified: both files unchanged after `unittest discover`).
- [x] Invented peer defaults removed from `nifty_peer_comparison.py`.
- [x] `NIFTY_50_DATA` is explicitly dated and disclaimed
      (`NIFTY_50_DATASET_AS_OF = "FY24 financial basis; updated Q2 FY25"`), and every
      peer row carries a `period_label`. Cross-period comparison is refused rather
      than silently ranked.
- [x] Hardcoded index/marquee quotes are labelled `data_status: "sample_fallback"`
      and surfaced as such, not presented as live.
- [x] Period labels on every peer row; mixed live/FY24 tables warn before ranking.
      The reference dataset is retained by choice (free, no data licence), not because
      it is live.
- Verified: `tests/test_phase2_data_layer.py`.

## Phase 3 — Security & deployment `[x]`

- [x] `html.escape` on LLM-sourced strings across the render paths.
- [x] Binds `127.0.0.1` by default (`.streamlit/config.toml`).
- [x] Optional password gate (`KUSHA_ACCESS_PASSWORD`) and per-session run budget
      (`MAX_RUNS_PER_SESSION`).
- [x] Trust boundary documented.
- Corrected: there is no committed Google API key. `.env` is gitignored, only
  `.env.example` is tracked, and `AIzaSyD9…` in `tests/test_self_improvement_engine.py`
  is a deliberate redaction-test dummy. Rotation is not required.
- Verified: `tests/test_phase3_security.py`.

## Phase 4 — Reliability & caching `[x]`

- [x] Silent handlers triaged: logged or commented; no bare `except …: pass`
      remains in library code.
- [x] Cache key = ticker + model + pipeline + document hash + sector + web-search
      flag + analysis mode, wired identically at probe, load and save.
- [x] Cache TTL (`MAX_CACHE_AGE_HOURS = 24`, env-overridable); stale entries are
      discarded and very old ones deleted. UI shows relative age.
- [x] Structured stdlib logging (`kusha_logging.py`), no `st.write` telemetry.
- [x] `data_quality` dict and degradation banner; shared `_call_with_retry`.
- Verified: `tests/test_phase4_reliability.py`; full suite 169 tests.

## Phase 5 — Tests & CI `[x]`

- [x] `test_terminal_quality.py` moved into `tests/`; `test_key.py` moved to
      `tools/check_api_key.py` (manual script, not collected).
- [x] Storage isolated: tmpdir for cache + ledger; tests do not write repo files.
- [x] `.github/workflows/tests.yml` running stdlib `unittest` on Python 3.11/3.12.
- [x] Coverage floor (70%) on the four scoring modules.
- [x] Golden-company regression suite (`tests/test_golden_companies.py`), with
      `LOSS_MAKER` capped at 50.
- Verified: 169 tests, `unittest discover` prints `OK`; `test_hygiene.py` enforces
  the no-network / no-outside-write rules.

## Phase 6 — Architecture & packaging `[ ]`

- [ ] Extract the 606-line inline CSS block and the 13 streamlit-free render
      functions out of `app.py`. **Do not** attempt to split the 1,236-line main
      flow in this phase — no test executes it, so a bad split would still go green.
- [ ] Single source of truth for pillars (analyzer, app, prompt template).
- [ ] Single source of truth for score bands (analyzer verdicts vs app ELI15/gauge).
- [ ] Merge the duplicated fraud-shield logic into `forensic_risk_engine` output.
- [ ] Move magic constants (score bands, thresholds, retry defaults) into config.
- [ ] Add `pyproject.toml`, bound dependencies, add missing `numpy`, raise the
      `streamlit` floor to a version that actually has `st.iframe` / `width="stretch"`.
- [ ] Delete duplicate `FORENSIC_FRAMEWORK_ANALYSIS.md`.

## Phase 7 — Docs, legal & positioning `[ ]`

- [ ] Rewrite README to match code exactly (remove DCF / IP / injection claims).
- [ ] Add `LICENSE`.
- [ ] Accurate privacy notice (PDFs are sent to Google).
- [ ] `[!]` Decide SEBI posture: strip buy/sell + sizing, or register.
- [ ] Update or delete stale `docs/REMEDIATION_PLAN.md` (references dead models).

## Phase 8 — Permanent data-truth monitoring `[ ]`

- [ ] Scheduled staleness checks for index/peer data.
- [ ] Alert on PASS → INSUFFICIENT_DATA without a source change.
- [ ] Re-run golden company suite on every release.

---

## Decisions needed from the owner (not code)

1. **SEBI posture** — keep scores + position sizing (registration risk) or strip them.
2. **LLM-only scoring** — position as "AI-assisted, non-reproducible", or build a
   real per-pillar formula.
3. **Data licensing** — Yahoo is delayed/unverified; confirm terms of use.

## Zero-cost tool choices

| Need | Free option |
|---|---|
| Model | Gemini free tier (existing key) |
| Tests | `python -m unittest` (already used, no install) |
| CI | GitHub Actions free minutes |
| Lint | `ruff` (free, open source) |
| Data | Yahoo Finance via `yfinance` (delayed, attributed) |
| Hosting | Local only until auth exists |
