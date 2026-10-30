# Phase 5 — Tests & CI

Copy everything between the markers into Antigravity, with the repository open at root.

**Prerequisite:** Task 0 below closes the unfinished parts of Phase 4. Do not skip it —
CI must not go green on top of a known data-integrity bug.

---

===BEGIN PROMPT===

# TASK: Phase 5 — "Tests & CI" remediation of Project KUSHA

## Context

The suite currently reports 124 passing tests. Three things are true at once:

1. **23 tests never run.** `test_terminal_quality.py` sits at the repository root; unittest
   discovery is scoped to `tests/`, so it is never collected. Verify: `grep -c "def test_"`
   returns 23, and `python -m unittest discover -s tests -v` contains zero mentions of it.
2. **Phase 4 is incomplete**, and its most important fix only *looks* finished.
3. **There is no CI**, so none of this is checked on commit.

## Non-negotiable constraints

- **Zero cost.** GitHub Actions free minutes only. No paid CI, no paid coverage SaaS.
- **No new runtime dependencies.** `coverage` may be added as a **dev-only** dependency
  (`requirements-dev.txt`) — it is free and open source. Nothing else.
- **Tests use stdlib `unittest`.** CI must not require pytest.
- **Tests must never hit the network.** `yfinance`, `google.genai` and HTTP calls are
  patched. A test that needs the internet is a broken test.
- **Tests must never write outside a temporary directory.** This includes the ledger, the
  evaluation cache, and any `*.json` fixture.

---

## Task 0 — Gate: finish Phase 4 before touching CI

Phase 4 was partially applied. Complete these five items first; CI work starts only after
they pass.

### 0a. The cache key is hashed but not differentiated — **the critical bug**

`make_cache_key` (evaluation_cache.py:53) accepts `document_hash`, `sector`,
`skip_web_search`, `analysis_mode`. **Every call site omits them**, so they take their
defaults:

```python
document_hash: Optional[str] = "no_document",
sector: Optional[str] = "unknown",
skip_web_search: bool = False,
analysis_mode: Optional[str] = "standard"
```

The SHA-256 is therefore computed over a constant suffix. The key still varies only by
ticker + model + pipeline version. Analysing RELIANCE with a PDF and then without one hits
the **same cache entry**, and the earlier result is replayed for different evidence.

Required:

1. In `app.py`, compute the document hash once per run:
   `document_hash = hashlib.sha256(pdf_bytes).hexdigest() if pdf_bytes else "no_document"`
2. Pass the full argument set at **all three** call sites — the existence probe
   (~2169), the load (~4001), and the save (~4091):
   ```python
   load_cached_evaluation(
       company_name=clean_target_name,
       ticker=clean_target_ticker,
       model=selected_gemini_model,
       current_pipeline_version=ANALYSIS_PIPELINE_VERSION,
       document_hash=document_hash,
       sector=target_sector,
       skip_web_search=skip_web_search,
       analysis_mode=mode_pill,
   )
   ```
   The load, save and probe must receive **identical** values. A mismatch causes a permanent
   cache miss — silent, expensive, and invisible in the UI.
3. Store `result["document_hash"] = document_hash` so the saved payload records what it was
   built from.
4. Delete the now-dead `make_cache_filename` if nothing references it.

**Acceptance:** analysing ACME with a PDF and then without one produces **two** files in
`.cache/evaluations` with different hashes.

### 0b. Cache TTL

`created_at` is stored but never enforced. Add:

- `MAX_CACHE_AGE_HOURS = 24`, env override `KUSHA_CACHE_MAX_AGE_HOURS`.
- On load, older than TTL → return `None`, log at `INFO` with the age.
- Older than 4× TTL → delete the file.
- Malformed or missing `created_at` → treat as stale, never fresh.
- UI shows "Cached 3 hours ago (30 Oct 2026, 14:02 UTC)" derived from the ISO timestamp.

### 0c. `data_quality`

Add `result["data_quality"]` with `live_data_available`, `statements_available`,
`pdf_attached`, `web_search_used`, `degraded_sources` (list of short strings). Populate from
facts already known — do not add new fetches. Render one amber banner above results when
`degraded_sources` is non-empty.

### 0d. Unified retry helper

Extract `_call_with_retry(fn, *, attempts=2, base_delay=1.5, label="gemini")` in
`analyzer.py`: log each retry at `WARNING`, add jitter, re-raise immediately on 429/quota,
preserve the original exception on the final attempt (`raise ... from e`). Use it for both
the research call and the analysis call. Do not change model fallback order.

### 0e. Remaining silent handlers

Eight `except Exception: pass` remain:

```
analyzer.py:1020
nifty_universe.py:165, 297, 569, 600, 690
nifty_peer_comparison.py:1204, 1212
app.py:136
```

Each needs a `logger.warning(...)`/`logger.debug(...)` with context, or a one-line comment
explaining why silence is correct. No bare `pass` with no explanation.

### Gate

Do not proceed to Task 1 until this passes:

```bash
rm -rf .cache/evaluations
python -m unittest discover -s tests      # must be OK
# then manually: analyse the same ticker with and without a PDF
ls -1 .cache/evaluations                   # must show 2 files, different hashes
```

---

## Task 1 — Rescue the 23 dead tests

**File:** `test_terminal_quality.py` (root, 383 lines, 23 test methods).

It validates the 50 Nifty constituents and their 16 metrics — the exact schema Phase 2
depended on — and it has never executed in CI or locally.

Required:

1. Move it to `tests/test_terminal_quality.py`.
2. Fix any import paths (`from nifty_peer_comparison import ...` still works because tests
   run from the repo root).
3. Run it. **Some of these 23 will fail** — they were written against the pre-Phase-2
   behaviour. For each failure, decide: is the test asserting a falsehood (delete/rewrite
   it), or has the code regressed (fix the code)? State which, per test, in your report.
4. Do not delete a failing test just to get green. If it encoded a fabricated expectation,
   say so explicitly.

**Other stray files:**

- `test_key.py` (root) is a manual connectivity script, not a test. Move to `tools/check_api_key.py`
  and add a module docstring saying it is manual and makes a live API call.
- `scratch/` contains `test_browser_feedback_hud.py`, `test_browser_interaction.py`,
  `test_financial_trends.py`, `verify_calculations.py` and three `capture_*.py` scripts.
  These are not unit tests and would fail discovery. Move to `tools/scratch/` (keep them,
  they are useful) **and** ensure they are never collected: no `test_*.py` naming in a
  discovered path, or add a `tools/` exclusion.
- Confirm `python -m unittest discover -s tests` still collects only real tests, and count
  them: it must now be **147 or more** (124 + 23), minus any you legitimately removed.

## Task 2 — Golden-company regression suite

**File:** `tests/test_golden_companies.py`.

The current suite tests units. Nothing asserts end-to-end behaviour on a *known* company
profile. Build five fixtures as plain dicts in `tests/fixtures_golden.py`, no network:

1. **`CLEAN_LARGECAP`** — 4 years of growth, positive CFO > PAT, low debt, 0% pledge,
   unqualified auditor opinion supplied.
2. **`LOSS_MAKER`** — negative PAT in the latest two years, negative CFO, shrinking revenue.
3. **`HIGH_PLEDGE`** — 45% promoter pledge, otherwise healthy.
4. **`CHANNEL_STUFFING`** — revenue flat, receivables growing 40% YoY, CFO diverging.
5. **`EMPTY`** — no statements, no live data.

Invariants to assert (these are the product's actual promises):

| Fixture | Invariant |
|---|---|
| `CLEAN_LARGECAP` | FQI issued, badge `PRISTINE` or `LOW`, zero critical red flags |
| `LOSS_MAKER` | `final_score <= 50`; accrual check `FAILED`; verdict never `PRISTINE` |
| `HIGH_PLEDGE` | `FOR_07_PROMOTER_PLEDGE` is `CRITICAL`; red flag listed; FQI reduced |
| `CHANNEL_STUFFING` | `FOR_02_RECEIVABLE_VELOCITY` not `PASS` |
| `EMPTY` | `fqi_score is None`; every check `INSUFFICIENT_DATA`; badge never `PRISTINE` |
| any fixture | no rendered HTML contains an unescaped `<script>` |
| any fixture | `guardrail_level("GOV-CREDIBLE 🟢")` never yields an AVOID stance |

Also assert **determinism**: run each fixture twice and compare the non-timestamp fields for
equality. A scoring change that flips a verdict must break this suite.

**Acceptance:** `LOSS_MAKER` scoring above 50 is a hard CI failure.

## Task 3 — GitHub Actions CI

**File:** `.github/workflows/tests.yml` (does not exist yet).

Required:

1. Trigger on `push` to any branch and on `pull_request`.
2. Matrix: Python `3.11` and `3.12` on `ubuntu-latest`.
3. Steps:
   - checkout
   - `actions/setup-python` with pip cache
   - `pip install -r requirements.txt -r requirements-dev.txt`
   - `python -m py_compile` on every top-level module
   - `python -m unittest discover -s tests -v`
   - coverage report (Task 4)
4. **No secrets required.** Tests must pass with zero environment variables and no network.
   If a test needs `GEMINI_API_KEY`, that test is wrong — patch it.
5. Add a guard step that fails if the test run modified tracked files:
   ```bash
   git diff --exit-code -- improvement_ledger.json IMPROVEMENT_LEDGER.md
   ```
6. Timeout `timeout-minutes: 10` so a hung network call fails fast instead of burning minutes.

`requirements-dev.txt` (new):

```
coverage>=7.0
```

## Task 4 — Coverage floor

Zero-cost approach: `coverage` (free, open source) as a dev-only dependency.

Required:

1. Run `coverage run -m unittest discover -s tests` then `coverage report`.
2. Enforce a floor **only on the scoring modules**, not the whole repo (UI code would drag
   the number down and encourage fake tests):

   ```
   coverage report --fail-under=70 \
       --include="analyzer.py,forensic_risk_engine.py,data_integrity_agent.py,evaluation_cache.py"
   ```
3. Add `.coveragerc` excluding `tests/`, `tools/`, `scratch/` and `__pycache__`.
4. Do not game the number with assertion-free tests. If coverage is below 70 on those four
   modules, report the actual figure and the specific uncovered branches rather than
   lowering the threshold without saying so.

## Task 5 — Test hygiene rules, enforced

Add to `tests/test_hygiene.py`:

1. **No network in tests:** source scan asserting no `requests.`, `urllib.request`,
   `yf.download`, `yf.Ticker`, or `genai.Client` is constructed without a patched mock in
   any file under `tests/`. Allow an explicit `# noqa: network` marker if genuinely needed.
2. **No writes outside temp:** source scan for `open(` with a literal path in `tests/`.
   Every `open` must use a `tempfile`-derived path.
3. **No sleeps longer than 0.05s** in tests: `time.sleep(` scan.
4. **No test without an assertion:** AST-scan each `def test_*` body for at least one
   `assert*` call or `self.assertRaises`. Report any that have none.
5. **Discovery completeness:** assert that `tests/test_terminal_quality.py` is collected, and
   that no `test_*.py` exists outside `tests/`.

## Task 6 — Document the test workflow

Add a `## Testing` section to `README.md` (10 lines max):

```bash
python -m unittest discover -s tests          # full suite
python -m unittest tests.test_golden_companies -v   # scoring invariants only
coverage run -m unittest discover -s tests && coverage report
```

State that tests need no API key and make no network calls.

## Verification — all of this must succeed

```bash
shasum improvement_ledger.json IMPROVEMENT_LEDGER.md > /tmp/ledger_before.sha

python -m py_compile *.py

python -m unittest discover -s tests

python -m unittest discover -s tests -v 2>&1 | grep -c "test_terminal_quality"

coverage run -m unittest discover -s tests
coverage report --fail-under=70 \
    --include="analyzer.py,forensic_risk_engine.py,data_integrity_agent.py,evaluation_cache.py"

shasum -c /tmp/ledger_before.sha

ls .github/workflows/tests.yml
```

Acceptance criteria:

- Test count is **147+** (124 + the 23 rescued), `unittest` prints `OK`.
- `grep -c "test_terminal_quality"` on the verbose run is **> 0**.
- Coverage on the four scoring modules is **≥ 70%**, or the actual number is reported with
  the reason.
- Both ledger files are byte-identical after the run.
- `.github/workflows/tests.yml` exists and contains `timeout-minutes`.
- `git status` shows no `test_*.py` outside `tests/` and `tools/`.

## Final report — required format

1. **Phase 4 gate result** — the two cache files from `ls -1 .cache/evaluations`, proving the
   document hash now differentiates entries.
2. **Rescued tests table** — the 23 from `test_terminal_quality.py`: pass / failed-and-why /
   deleted-and-why, one line each. Deleting a test requires a stated reason that it asserted
   something false.
3. **Golden suite** — table of the five fixtures and the invariants asserted.
4. **Coverage** — per-module percentages, not a single total.
5. **Files moved** — old path → new path, with a reason.
6. **Verification output pasted verbatim** — `Ran N tests` / `OK`, the coverage report, the
   `shasum -c` lines, and the `grep -c test_terminal_quality` count.
7. **Found but out of scope.**

Do not lower the coverage floor silently. Do not delete a test to reach green without saying
exactly which test and why its assertion was wrong.

===END PROMPT===
