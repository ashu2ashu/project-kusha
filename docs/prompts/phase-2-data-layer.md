# Phase 2 — Data Layer

Copy everything between the markers into Antigravity, with the repository open at root.
Run Phase 1 first — this prompt assumes the Phase 1 truth layer is in place.

---

===BEGIN PROMPT===

# TASK: Phase 2 — "Data Layer" remediation of Project KUSHA

## Context

Phase 1 removed the app's ability to fabricate *scores* from missing data. Phase 2 fixes
the **data underneath the scores**. Right now the app still presents static, stale or
invented market data as if it were current, and it ranks companies against numbers from
different financial periods.

## Non-negotiable constraints

- **Zero cost.** No paid data vendors, no paid APIs, no paid hosting.
- **No new third-party dependencies.** `yfinance`, `pandas`, `numpy`, `streamlit` and the
  stdlib are already installed. Do not add anything else.
- **Tests use stdlib `unittest` only.** `python -m unittest discover -s tests`.
- **Do not refactor architecture.** No module splits, no renames.
- **Do not change the 16-metric peer schema** — `test_terminal_quality.py` asserts
  exactly 50 constituents each carrying all 16 metric keys.
- **Do not delete `NIFTY_50_DATA`.** It stays as a labelled reference dataset.
- **Do not invent a fix for a defect you cannot reproduce.** Several items below are
  marked *VERIFY*. If the code is already correct, report "not present" and move on.
  Do not "improve" working code to look busy.

## Honesty rule for this phase

> If a number came from a static table, the UI must say so and must show its date.
> If two numbers come from different periods, they must never be ranked against
> each other.

---

## Task 0 — Blocking: stop the test suite from writing to the real audit ledger

**Why first:** every `python -m unittest discover -s tests` currently appends findings to
`IMPROVEMENT_LEDGER.md` and `improvement_ledger.json`. The audit trail is being corrupted
by the test suite. Fix this before anything else, otherwise every later test run re-dirties
the repo.

Evidence:

- `self_improvement_engine.py:50-51` — module-level `LEDGER_MD_PATH = "IMPROVEMENT_LEDGER.md"`
  and `LEDGER_JSON_PATH = "improvement_ledger.json"`.
- `tests/test_self_improvement_engine.py:168` and `:188` call `SelfImprovementLoop(dry_run=True).run_cycle()`.
- Even `dry_run=True` writes a `PROPOSED (DRY-RUN)` finding to both files.

Required:

1. Make the ledger paths injectable. Add constructor parameters to `SelfImprovementLoop`:

   ```python
   def __init__(self, dry_run=False, ledger_md_path=None, ledger_json_path=None):
       self.ledger_md_path = ledger_md_path or LEDGER_MD_PATH
       self.ledger_json_path = ledger_json_path or LEDGER_JSON_PATH
   ```

   Replace every bare use of `LEDGER_MD_PATH` / `LEDGER_JSON_PATH` inside the class with
   `self.ledger_md_path` / `self.ledger_json_path`. Keep the module constants as defaults
   so application behaviour is unchanged.

2. Update `tests/test_self_improvement_engine.py` so every `SelfImprovementLoop(...)`
   construction passes paths inside a `tempfile.mkdtemp()` directory, cleaned up in
   `tearDown`.

3. Add a regression test that proves the isolation works: run a dry-run cycle with
   temporary paths, then assert the repository's real ledger files are byte-identical to
   a snapshot taken before the test.

**Acceptance:** run the full suite, then `git status --short` must show no modification to
`IMPROVEMENT_LEDGER.md` or `improvement_ledger.json`.

---

## Task 1 — Index quotes fall back to hardcoded numbers presented as live

**File:** `nifty_universe.py`, function `fetch_live_indices_data` (approx lines 514-600).

`indices_def` (lines 516-521) carries hardcoded values — NIFTY 50 `24350.0`, SENSEX
`80150.0`, BANK NIFTY `51800.0`, NIFTY IT `38200.0` — with fixed intraday changes. When
Yahoo Finance is unreachable, lines 588-598 return those values through the same dict shape
as a live quote, with **no** `data_status`, **no** `as_of`, and **no** date. The caller
(`app.py:777`) cannot tell a live tick from a number frozen at authoring time.

Required:

1. Keep the static values, but never let them masquerade as live.
2. Every returned row must carry:
   - `"data_status"`: `"live"` for a Yahoo fetch, `"stale_reference"` for the static table.
   - `"as_of"`: an ISO date string. For live rows use the fetch timestamp. For static rows
     use a module constant `INDICES_REFERENCE_AS_OF = "2024-06-30"` (adjust to the true
     authoring date if you can determine it; if not, state clearly in the code comment that
     the date is the last known verification and is not authoritative).
3. Also fix the live branch: line 544-545 substitutes `cur` for `hi`/`lo` when the high/low
   series is missing (`hi = ... else cur`). That reports a day high equal to the current
   price. Use `None` instead and let the renderer show "N/A".
4. Add a module docstring note that these are **delayed** third-party quotes.

**File:** `app.py` — wherever indices are rendered, show the status. If any row is
`stale_reference`, display a caption: "Index levels unavailable from provider; showing a
static reference set as of <date>. Not current."

**Acceptance:** with the network blocked (monkeypatch `yf.download` and `yf.Ticker` to
raise), `fetch_live_indices_data()` returns four rows where every row has
`data_status == "stale_reference"` and a non-empty `as_of`.

## Task 2 — Marquee stock fallback is labelled but still rendered as current

**File:** `nifty_universe.py`, `fetch_marquee_stocks_data` (approx 603-668).

The fallback table (lines 652-663) hardcodes prices such as TCS `2530.0`, INFY `1153.8`,
RELIANCE `1190.0`. It does set `data_status: "sample_fallback"`, which is good, but the
caller (`app.py:781`) renders `data_status` nowhere, so the user sees stale prices
formatted identically to live ones.

Required:

1. Add `"as_of"` to every fallback row, using a constant
   `MARQUEE_REFERENCE_AS_OF = "2024-06-30"` (adjust/verify as above).
2. In `app.py`, render a visible badge or caption for any row whose `data_status` is not
   `"provider"`: "Sample reference data as of <date> — not live."
3. Do not silently substitute the fallback when the live fetch returns a *partial* list.
   If Yahoo returns 6 of 10 tickers, return those 6 with `data_status: "provider"` and add
   the 4 missing ones with `data_status: "unavailable"` and `cur: None` — do not paste in
   old prices for the missing ones.

## Task 3 — Invented peer metrics for non-Nifty-50 companies

**File:** `nifty_peer_comparison.py`, `get_peers_for_company` (approx 1131-1178).

When the target company is not in `NIFTY_50_DATA`, lines 1155-1175 build a target record
with **fabricated valuations**:

```python
"ind_pe": 25.0, "peg": 1.0, "ev_ebitda": 15.0,
"roic": 15.0, "croic": 12.0, "roce": 18.0,
```

These are presented as that company's industry P/E, PEG, EV/EBITDA, ROIC, CROIC and ROCE.
They are not the company's figures, not an industry average, and not sourced from anything.
Every other field is `0.0`, which will win or lose a "leader" comparison depending on
whether the metric is better high or low.

Required:

1. Replace every fabricated number with `None`, including the `0.0` placeholders.
2. `render_head_to_head_comparison_html` must render `None` as `"N/A"` and must exclude
   that row from any "leader" badge, best/worst highlight, and sort ordering.
3. If the target has *no* usable valuation data, the comparison must state
   "Target valuation data unavailable — comparison shows peers only" instead of drawing a
   matrix with a fabricated column.

**Acceptance:** `get_peers_for_company("ZZZUNKNOWN", "Banks (Commercial & Retail)")` returns
a first row where `ind_pe`, `peg`, `ev_ebitda`, `roic`, `croic`, `roce` are all `None`.

## Task 4 — Cross-sector peers are substituted silently

**File:** `nifty_peer_comparison.py`, `get_peers_for_company` lines 1143-1146.

If there are not enough same-sector peers in `NIFTY_50_DATA`, the code appends unrelated
companies from other sectors:

```python
other_peers = [c for c in NIFTY_50_DATA if c["symbol"] != sym and c not in sector_peers]
sector_peers.extend(other_peers[:limit - 1 - len(sector_peers)])
```

A cement company gets compared against an IT services company with no indication.

Required — choose the honest option:

1. Prefer: keep the peer set within the sector and return fewer peers (2 instead of 4)
   when there genuinely are not enough. Fewer rows is correct; unrelated rows are not.
2. If you keep cross-sector rows for UX reasons, each such row must carry
   `"peer_scope": "cross_sector"` and the matrix must label it "Different sector — not a
   direct comparable", and it must be excluded from any ranking.

Do not leave a silent substitution.

## Task 5 — Live target data ranked against FY24 peer data

**File:** `nifty_peer_comparison.py`, `render_head_to_head_comparison_html`
(approx 1181-1300) plus `NIFTY_50_DATASET_AS_OF` (line 33).

This is the most damaging defect in the phase.

The function fetches **live** data for the target company and overwrites its row:
`target_p["cmp"]`, `["pe"]`, `["ev_ebitda"]`, `["peg"]`, `["npm_ann"]`, `["mar_cap"]`,
`["down_pct"]` (lines ~1209-1260). The three peer rows remain the static
`NIFTY_50_DATA` values, which the module itself dates `"FY24 financial basis; updated
Q2 FY25"`.

The renderer then draws "leader badges" across this mixed matrix. A current P/E is being
ranked against FY24 P/Es and declared cheapest or most expensive.

Required:

1. Every row gets an explicit `period` label: `"live"` for freshly fetched values, or the
   dataset's `NIFTY_50_DATASET_AS_OF` string for static values.
2. Compute `mixed_periods = len(set(period_labels)) > 1`.
3. When `mixed_periods` is True:
   - render a prominent warning above the matrix: "Periods differ — this table mixes live
     market data with <dataset date> reference data. Values are not directly comparable
     and no ranking is shown."
   - suppress every leader badge, best/worst colouring, and any "cheapest / highest /
     best in class" text derived from cross-row comparison.
   - show the period label in each cell header or as a per-row column.
4. When all rows share a period, ranking may be shown.
5. Do the same for the Nifty-50 screener view (`render_nifty50_screener_view`,
   `get_nifty50_dataframe`): the whole table is a single dated dataset. It must display
   `NIFTY_50_DATASET_AS_OF` and `NIFTY_50_DATASET_DISCLAIMER` above the table, always —
   not only on hover or in an expander.
6. Keep `test_terminal_quality.py` passing: 50 constituents, 16 metrics each.

**Acceptance:** rendering the head-to-head for a Nifty-50 target with live data supplied
produces HTML containing the mixed-period warning and containing no leader badge.

## Task 6 — VERIFY, do not assume: `financial_trends.py`

Prior review claimed `financial_trends.py` coerces missing values to `0.0`. On inspection
this appears **not** to be true: `get_val` returns `None` (line 63-70) and the ratio series
are computed with explicit `None` guards.

Your job:

1. Verify by reading `fetch_financial_statements` end to end.
2. If any field is silently coerced to `0.0`, or any missing year is filled, fix it to
   `None`.
3. If the file is already correct, report "not present" and change nothing.

The same instruction applies to the claim that `nifty_universe.fetch_live_market_data`
contains synthetic multipliers. On inspection it returns `None` for missing fields and
carries `provider`, `is_delayed`, `retrieved_at` and `source_disclaimer`. Verify and
report; do not edit working code.

## Task 7 — Period alignment in statement series

**File:** `financial_trends.py`, `fetch_financial_statements`.

Two structural risks, independent of the coercion question:

1. `bs_cols` / `cf_cols` are derived from each statement's own columns
   (lines ~94-97, ~144), so a balance sheet with a different year set than the P&L can
   silently misalign values against `years`.
2. Line ~436: `pat = pnl.get("Net Profit (PAT)", {}).get("values", [])[-len(cf_years):]`
   assumes the cash-flow year set is a suffix of the P&L year set. If it is not, the wrong
   PAT values are paired with CFO values, and the cash-conversion ratio is wrong.

Required:

1. Align every statement to a single ordered year axis. Any year present in one statement
   but not another must produce `None` for that statement's values — never a shifted value.
2. If the year sets cannot be aligned, set the derived ratio (CAGR, cash conversion) to
   `None` and add a `"alignment_warning"` key describing the mismatch.
3. Add a test with a P&L covering Mar 2021-2024 and a cash-flow statement covering only
   Mar 2023-2024, asserting the resulting CFO/PAT pairing uses Mar 2023 and Mar 2024 only.

## Task 8 — Regression tests

Create `tests/test_phase2_data_layer.py` (stdlib `unittest`). Minimum:

1. `fetch_live_indices_data()` with `yf.download` and `yf.Ticker` monkeypatched to raise →
   four rows, every `data_status == "stale_reference"`, every `as_of` non-empty.
2. Same function with a successful download → every `data_status == "live"`.
3. `fetch_marquee_stocks_data()` with the provider failing → every row has `as_of` and
   `data_status != "provider"`.
4. `get_peers_for_company("ZZZUNKNOWN", <sector>)` → first row's `ind_pe`, `peg`,
   `ev_ebitda`, `roic`, `croic`, `roce` are all `None`.
5. No peer row is silently cross-sector: either `peer_scope` is set to `"cross_sector"`,
   or every peer's sector equals the target sector.
6. Mixed-period head-to-head HTML contains the warning string and no leader badge.
7. Single-period head-to-head still renders normally.
8. Ledger isolation: a full dry-run cycle with temp paths leaves the real ledger files
   byte-identical (hash comparison).
9. `NIFTY_50_DATA` still has exactly 50 entries, each with all 16 keys — guard that
   `test_terminal_quality.py` keeps passing.

## Verification — all of this must succeed

```bash
# 1. Snapshot the ledgers
shasum improvement_ledger.json IMPROVEMENT_LEDGER.md > /tmp/ledger_before.sha

# 2. Compile
python -m py_compile nifty_universe.py nifty_peer_comparison.py financial_trends.py \
    self_improvement_engine.py app.py

# 3. Full suite
python -m unittest discover -s tests

# 4. Streamlit smoke test
python - <<'PY'
from streamlit.testing.v1 import AppTest
at = AppTest.from_file("app.py", default_timeout=120).run()
print("EXCEPTIONS:", len(at.exception))
for e in at.exception[:5]:
    print(e.value)
PY

# 5. Prove the ledger was untouched
shasum -c /tmp/ledger_before.sha
```

Acceptance criteria:

- `unittest` prints `OK`.
- `AppTest` prints `EXCEPTIONS: 0`.
- `shasum -c` prints `improvement_ledger.json: OK` and `IMPROVEMENT_LEDGER.md: OK`.
- `git status --short` shows no ledger files modified.

## Final report — required format

1. **Files changed**, one line each explaining why.
2. **Defects confirmed** — for each task above, the exact line you found and the before/after.
3. **Defects NOT present** — the VERIFY items that were already correct. This section is
   expected to contain at least one entry; a report with none is suspicious.
4. **Verification output pasted verbatim** — `Ran N tests` / `OK`, `EXCEPTIONS: N`, and the
   two `shasum -c` OK lines.
5. **Found but out of scope** — other issues you noticed and deliberately left.
6. **Could not do** — anything blocked, and why.

Do not say "done" unless every acceptance criterion passed.

===END PROMPT===
