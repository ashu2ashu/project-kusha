# Phase 4 — Reliability & Caching

Copy everything between the markers into Antigravity, with the repository open at root.

---

===BEGIN PROMPT===

# TASK: Phase 4 — "Reliability & Caching" remediation of Project KUSHA

## Context

Phases 1-3 made results truthful, data honest, and the app safe to run. Phase 4 makes it
**predictable**: no silent failures, no cache that replays the wrong analysis, and no errors
that vanish without a trace.

## Non-negotiable constraints

- **Zero cost.** No paid monitoring, no paid log aggregation, no paid APM.
- **No new third-party dependencies.** stdlib `logging`, `hashlib`, `json`, `os`, `time`,
  `datetime` only.
- **Tests use stdlib `unittest` only.**
- **Do not refactor architecture.** No module splits, no renames.
- **Do not change scoring, pillar weights, or prompt text.**
- **Do not remove deliberate best-effort behaviour.** Some `except` blocks exist so a
  missing optional field does not kill an analysis. Those are legitimate. Your job is to
  make them *visible*, not to make them fatal. See Task 2 for the triage rules.

## The single most important defect in this phase

The cache key is `eval_{TICKER}_{MODEL}.json`. It does not include what the analysis was
actually based on.

`app.py:3874` loads with `(company_name, ticker, model, pipeline_version)`.
`app.py:3961` saves with the same four values.

Consequence: analyse RELIANCE with an uploaded annual-report PDF attached. The result is
cached. Later analyse RELIANCE with no PDF, or with a *different* PDF, or with the
"skip web search" toggle flipped. The app finds the same file, passes `pipeline_version`,
and **replays the earlier analysis as if it were the new one**. Same ticker, different
evidence, wrong answer presented as current.

Everything else in this phase is secondary to fixing that.

---

## Task 1 — Logging infrastructure

**File:** new module `kusha_logging.py` (small, ~40 lines).

Required:

1. `configure_logging()` — idempotent, called once from `app.py` at startup and from
   `cli.py`. Level from `KUSHA_LOG_LEVEL` env var, default `INFO`.
2. Format: `%(asctime)s %(levelname)s %(name)s :: %(message)s`. Write to **stderr only**.
   Do not add a file handler by default; if `KUSHA_LOG_FILE` is set, add one.
3. `get_logger(name)` returns a module-level logger.
4. Hard rule, enforced by a test: **never log** the API key, the password, prompt text, or
   full company financial statements. Log tickers, model names, durations, cache keys,
   exception class names and short messages only.
5. Replace the ad-hoc `safe_print(...)` telemetry in `self_improvement_engine.py` with
   logger calls. Keep the console output behaviour for CLI use by logging at `INFO`.

Note: `cli.py:16` already does `logging.getLogger("streamlit").setLevel(logging.ERROR)`.
Keep that; it suppresses Streamlit's own noise.

## Task 2 — Triage the silent exception handlers

There are 10 `except Exception: pass` blocks and 31 `except Exception` blocks outside
`tests/`. **Do not rewrite them all identically.** Classify each into one of three
categories and act accordingly:

**Category A — must log and continue.** The failure is expected and tolerable, but a human
debugging a bad result needs to see it happened.
Action: `logger.warning("...", exc_info=True)` or `logger.warning("...: %s", e)`, keep the
same control flow.

Known members:
- `nifty_universe.py:257` — primary Yahoo fetch failed, retrying
- `nifty_universe.py:296` — `stock.info` unavailable, fundamentals will be `None`
- `nifty_universe.py:513` — whole quote build failed
- `nifty_universe.py:568`, `:599`, `:689`, `:723` — index/marquee/history fallbacks
- `financial_trends.py:56`, `:65` — date parsing fallbacks
- `nifty_peer_comparison.py:1202`, `:1209` — lazy live-data fetch for a custom ticker
- `analyzer.py:790` — PDF upload to Gemini failed
- `analyzer.py:1009` — remote file cleanup failed (log at `DEBUG`, it is genuinely harmless)
- `evaluation_cache.py` load/save failures

**Category B — must propagate, not swallow.** The failure means the result would be
silently wrong.
- `evaluation_cache.py:load_cached_evaluation` — a corrupt cache file currently returns
  `None` and the app silently does a live run. Log at `WARNING` **and delete the corrupt
  file**, so it cannot fail again on every request. (Phase 3 added provenance checks; this
  completes them.)
- `analyzer.py` — a `JSONDecodeError` on the model response must not produce a partial
  result. Confirm it already routes to the evidence-gap path, and log the parse failure
  with the model name and response length (never the response body).

**Category C — genuinely fine, add a comment.** If a handler is correct as-is, add a
one-line comment saying why. Do not add noise.

**Deliverable:** a table in your report listing every handler you touched, its category, and
the one-line reason.

## Task 3 — Cache key must include every input that changes the output

**File:** `evaluation_cache.py`.

Required:

1. Replace the two-argument filename with a key built from **all** result-affecting inputs:

   ```python
   def make_cache_key(ticker, model, pipeline_version, document_hash,
                      sector, skip_web_search, analysis_mode) -> str:
       raw = "|".join([
           str(ticker or "").upper().strip(),
           str(model or ""),
           str(pipeline_version or ""),
           str(document_hash or "no_document"),
           str(sector or "unknown").upper().strip(),
           "noweb" if skip_web_search else "web",
           str(analysis_mode or "standard"),
       ])
       return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]
   ```

2. Filename becomes `eval_<sanitized_ticker>_<key>.json`. Keep the ticker prefix so the
   cache directory stays human-browsable.
3. `document_hash` is `sha256(pdf_bytes).hexdigest()` when a PDF is attached, else
   `"no_document"`. Compute it **once** in `app.py` and store it on the result dict as
   `result["document_hash"]` so save and load agree.
4. Update all three call sites: `app.py:2071` (existence probe), `:3874` (load),
   `:3961` (save). They must pass identical arguments — a mismatch means a permanent cache
   miss. Add a test that asserts the probe and the save produce the same key for the same
   inputs.
5. `sanitize_cache_token` truncates to 30 chars and uppercases. Two long company names can
   collide. Use the hash for the key and keep only a short sanitized prefix for readability.
6. Do not use `company_name` as a key component — it is free text and changes with user
   input.

**Acceptance:** analysing the same ticker with and without a PDF produces two distinct cache
files, and neither replays the other's result.

## Task 4 — Cache freshness

**File:** `evaluation_cache.py`, `app.py`.

There is currently **no TTL**. A cached analysis replays forever as long as
`pipeline_version` matches. `cached_at` is a display string
(`"%d %b %Y, %H:%M UTC"`), so its age cannot be computed.

Required:

1. Store `created_at` as a real UTC ISO timestamp (`datetime.now(timezone.utc).isoformat()`)
   in the payload. Keep a human string only for display, derived from the ISO value.
2. Add `MAX_CACHE_AGE_HOURS = 24` (env override `KUSHA_CACHE_MAX_AGE_HOURS`).
3. On load, if the payload is older than the TTL, return `None` and log at `INFO` with the
   age. Delete the file if it is older than 4x the TTL.
4. `cached_at` displayed in the UI must become "Cached 3 hours ago (30 Oct 2026, 14:02 UTC)"
   — computed from the ISO timestamp, not trusted as a string.
5. If the timestamp is malformed or missing, treat the entry as stale. Never assume fresh.

## Task 5 — Surface degradation instead of hiding it

**File:** `analyzer.py`, `app.py`.

Right now failures are absorbed into `evidence_gaps` as free text. Some are results of
optional-data failures that should be visible as structured state.

Required:

1. Add `result["data_quality"]` — a dict with:
   - `"live_data_available": bool`
   - `"statements_available": bool`
   - `"pdf_attached": bool`
   - `"web_search_used": bool`
   - `"degraded_sources": [list of short strings]`
2. Populate it wherever those facts are already known. Do not invent new fetches.
3. In `app.py`, if `degraded_sources` is non-empty, show one compact amber banner listing
   them above the results — not scattered through the report.
4. Do not double-report: if a degradation is already in `evidence_gaps`, it may appear in
   both, but the banner text must be the short form, not the full paragraph.

## Task 6 — Unify the retry policy

**File:** `analyzer.py`.

Retry logic exists twice (lines ~819 and ~898), both `range(2)` with `time.sleep(1.5)` on
503. The 429/quota handling was extended in Phase 3. There is still no jitter and no
logging of retries.

Required:

1. Extract one helper:

   ```python
   def _call_with_retry(fn, *, attempts=2, base_delay=1.5, label="gemini"):
   ```

   It must:
   - log each retry at `WARNING` with `label`, attempt number and exception class
   - add jitter (`base_delay * (1 + random.random() * 0.3)`)
   - re-raise immediately on quota/429 errors without further retries
   - re-raise on the final attempt with the original exception preserved (`raise ... from e`)

2. Use it for both the research call and the analysis call. Do not change the model
   fallback order or the number of attempts.

## Task 7 — Tests

Create `tests/test_phase4_reliability.py` (stdlib `unittest`). Minimum:

1. **Cache key isolation:** same ticker, one call with `document_hash=None` and one with a
   real hash → different keys. Same ticker, `skip_web_search` True vs False → different keys.
2. **Round trip:** save then load with identical inputs → returns the result. Load with a
   different `document_hash` → returns `None`.
3. **Probe/save agreement:** the key used by the existence probe equals the key used by
   save, for the same inputs.
4. **TTL:** write a payload with `created_at` 25 hours ago → load returns `None`. At 23 hours
   → returns the result.
5. **Malformed timestamp:** missing or garbage `created_at` → treated as stale.
6. **Corrupt cache file:** invalid JSON is logged at WARNING, deleted, and returns `None`.
7. **Logging redaction:** configure a logger to a `StringIO` handler, run a code path that
   logs an error, and assert the API key string never appears in the output.
8. **Retry helper:** a function that raises twice then succeeds is called 3 times with
   `attempts=3`; a quota error is not retried.
9. **Silent handlers:** a source scan asserting no `except Exception:` is followed
   immediately by `pass` in `nifty_universe.py`, `analyzer.py`, `financial_trends.py`,
   `nifty_peer_comparison.py`, `evaluation_cache.py`. (Some are legitimate — if you keep
   one, it must have a `logger` call or an explanatory comment within the next two lines,
   and the test must encode that rule.)

## Verification — all of this must succeed

```bash
shasum improvement_ledger.json IMPROVEMENT_LEDGER.md > /tmp/ledger_before.sha

python -m py_compile app.py analyzer.py evaluation_cache.py kusha_logging.py \
    nifty_universe.py nifty_peer_comparison.py financial_trends.py

python -m unittest discover -s tests

python - <<'PY'
from streamlit.testing.v1 import AppTest
at = AppTest.from_file("app.py", default_timeout=120).run()
print("EXCEPTIONS:", len(at.exception))
for e in at.exception[:5]:
    print(e.value)
PY

shasum -c /tmp/ledger_before.sha
```

Additional manual checks:

```bash
# 1. A cache hit must not be reachable from a different input
rm -rf .cache/evaluations
# analyse ACME with a PDF, then analyse ACME without one
# -> two files in .cache/evaluations, different hashes in the names
ls -1 .cache/evaluations

# 2. Logs must be informative and clean
KUSHA_LOG_LEVEL=DEBUG streamlit run app.py 2>&1 | head -40
# -> no API key, no prompt text, no stack trace spam for expected failures
```

Acceptance criteria:

- `unittest` prints `OK`.
- `AppTest` prints `EXCEPTIONS: 0`.
- `shasum -c` prints OK for both ledger files.
- Two files in `.cache/evaluations` after analysing the same ticker with and without a PDF.
- `grep -c "except Exception:$" ... ` followed by `pass` is zero, or every remaining one has
  a log call or comment on the next line.

## Final report — required format

1. **Handler triage table** — every `except Exception` touched, its category (A/B/C), and a
   one-line reason. This is the core deliverable; do not summarise it as "fixed several".
2. **Cache key before/after** — the exact string used before and the exact string used after.
3. **Files changed**, one line each explaining why.
4. **Verification output pasted verbatim** — `Ran N tests` / `OK`, `EXCEPTIONS: N`, the
   `shasum -c` lines, and the `ls -1 .cache/evaluations` showing two distinct files.
5. **Behaviour changes users will notice** — e.g. "cache now expires after 24h, so a repeat
   analysis may hit the API where it previously replayed instantly."
6. **Found but out of scope.**

Do not claim reliability improvements you did not test.

===END PROMPT===
