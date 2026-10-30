# Phase 8 — Permanent Data-Truth Monitoring

Copy everything between the markers into Antigravity, with the repository open at root.

**Prerequisite:** Phase 7 committed, suite green, `docs/PRIVACY.md` / `docs/LIMITATIONS.md` /
`docs/LEGAL_DECISIONS.md` present. Run Phase 8 after Phase 7, not before — the monitor's doc
checks reference those files.

---

===BEGIN PROMPT===

# TASK: Phase 8 — "Permanent Data-Truth Monitoring" for Project KUSHA

## Context

Phases 1-7 make the app honest *at the moment you run it*. Nothing keeps it honest next month.

The failure mode this phase exists to catch is not a crash. It is silent drift:

- Yahoo changes a field name → `fetch_live_market_data` falls back to `sample_fallback`, the UI
  labels it, and nobody notices for months.
- A code change makes `FOR_07` return `PASS` where it used to return `INSUFFICIENT_DATA` → the app
  starts certifying companies it never evaluated.
- The peer dataset (`FY24`) quietly becomes three years old.
- `gemini-3.5-flash` is already deprecated and auto-routed; the next model retirement will happen
  without a commit.
- A new `pandas`/`yfinance` release inside the allowed range breaks the suite, and you find out
  when you next open the app.

A monitor that only runs when you remember to run it is not monitoring. This phase runs on a
schedule, for free, and files an issue when truth drifts.

## Non-negotiable constraints

- **Zero cost.** GitHub Actions free minutes, GitHub Issues as the alert channel. No PagerDuty, no
  Slack app, no hosted cron, no paid APM.
- **No new dependencies.** Alerting uses stdlib `urllib.request` + `json`. The probes reuse
  `yfinance` / `requests` already in `requirements.txt`.
- **The monitor must not write to the repository.** No auto-commits, no baseline updates from CI.
  A committed baseline that CI can rewrite is a baseline that hides drift.
- **Monitoring must not fabricate.** If a source is unavailable, the report says "unavailable",
  never "OK".
- **Never leak secrets or financial statements** into an issue body. Tickers, check ids, statuses,
  counts, and exception classes only.

## The design rule that makes this work

A status change is only meaningful relative to *what produced it*. So the baseline stores a
fingerprint of the inputs:

```
fingerprint = sha256(
    ANALYSIS_PIPELINE_VERSION
  | ForensicRiskEngine.VERSION
  | NIFTY_50_DATASET_DATE
  | sha256(tests/fixtures_golden.py)
  | comma-joined canonical pillar ids
)
```

- Fingerprint **matches** + status changed → real drift or nondeterminism. **FAIL.**
- Fingerprint **changed** → the baseline is stale. The monitor refuses to compare and exits with
  "update the baseline with a reason". **STALE BASELINE.** This forces every intentional change to
  be a reviewed commit, not a silent acceptance.
- Fingerprint matches + statuses identical → **OK.**

That single rule is the difference between a monitor and a green light that means nothing.

---

## Task 0 — Gate and baseline hygiene

1. Confirm Phase 7 is committed and the suite is green:
   ```bash
   git status --short          # should be clean or only this phase's new files
   python -m unittest discover -s tests 2>&1 | tail -3
   ```
   If the suite is not `OK`, stop. Do not build monitoring on a red tree — the baseline would
   capture broken behaviour as the truth.
2. Record the current ledger hashes:
   ```bash
   shasum improvement_ledger.json IMPROVEMENT_LEDGER.md > /tmp/ledger_before.sha
   ```

## Task 1 — Make the dataset date machine-readable

`nifty_peer_comparison.py:37` has:

```python
NIFTY_50_DATASET_AS_OF = "FY24 financial basis; updated Q2 FY25"
```

That is a human sentence, not a date. A monitor cannot compute age from it.

Required:

1. Add an ISO date constant next to it:
   ```python
   # Date of the underlying financial statements, not the date the file was edited.
   NIFTY_50_DATASET_DATE = "YYYY-MM-DD"
   ```
   Pick the date that matches what the display string claims. If the statements are FY24
   (year ended March 2024) but the dataset was updated in Q2 FY25, the honest date is
   `2024-03-31` — label it as the *statement date*. Do not use the edit date. State your choice
   and reasoning in the report.
2. Keep `NIFTY_50_DATASET_AS_OF` for display, but make the two consistent: if they disagree, the
   display string wins and the ISO date is wrong — fix the date.
3. No UI change.

## Task 2 — `monitoring/baseline.json`

Generate it, do not hand-write it. Format:

```json
{
  "schema": 1,
  "generated_at": "2026-10-30T00:00:00+00:00",
  "reason": "initial baseline after phase 7",
  "fingerprint": "<sha256>",
  "inputs": {
    "pipeline_version": "evidence-gate-2026-10-25-v1",
    "engine_version": "2026.1",
    "dataset_date": "2024-03-31",
    "fixtures_sha256": "<sha256 of tests/fixtures_golden.py>",
    "pillars": ["1", "2", "..."]
  },
  "thresholds": {
    "peer_dataset_max_age_days": 900,
    "model_watchlist_max_age_days": 90,
    "market_data_max_age_hours": 48
  },
  "fixtures": {
    "CLEAN_LARGECAP": {
      "fqi_score": 92.0,
      "verdict_badge": "PRISTINE",
      "score_issued": true,
      "checks": {
        "FOR_01_CASH_CONVERSION": "PASS",
        "FOR_02_RECEIVABLE_VELOCITY": "PASS"
      }
    }
  }
}
```

Rules:

- Every fixture in `tests/fixtures_golden.py` appears, with every check id the engine emits.
- Store `fqi_score` rounded to 1 decimal and `verdict_badge`; do not store free-text `detail`
  (it changes for cosmetic reasons and would create false drift).
- `thresholds.peer_dataset_max_age_days` defaults to **900**. FY24 data is already old; the point
  is to stop it becoming silently older. If 900 days is wrong for this dataset, pick a number and
  defend it in the report — do not set 30 to make the check pass.

## Task 3 — `tools/monitor.py` (stdlib only)

CLI:

```bash
python tools/monitor.py --check --offline
python tools/monitor.py --check --online
python tools/monitor.py --update-baseline --reason "refresh after engine change"
python tools/monitor.py --check --offline --json
```

Exit codes — these are the contract:

| Code | Meaning |
|---|---|
| 0 | OK (warnings may still be printed) |
| 1 | DRIFT — status, score, or badge changed with an unchanged fingerprint |
| 2 | STALE BASELINE — fingerprint changed; human must update with a reason |
| 3 | SOURCE UNAVAILABLE — online probe failed after retries (structural, not OK) |
| 4 | MISCONFIGURED — missing baseline, unreadable fixture, bad threshold |

Required behaviour:

### Offline checks (deterministic, no network)

1. **Fingerprint.** Recompute per the design rule. Compare with `baseline["fingerprint"]`.
   Mismatch → exit 2, and print exactly which input changed (pipeline version, engine version,
   dataset date, fixtures hash, pillar ids).
2. **Fixture drift.** Run `ForensicRiskEngine.audit_company_forensics(...)` on each fixture with
   `ticker_symbol`, `company_name`, `sector`, `financial_statements`, `live_market_data` (the same
   call the golden tests use). Compare `fqi_score`, `verdict_badge`, `score_issued`, and every
   check status. Output a table:
   ```
   CLEAN_LARGECAP  FOR_02_RECEIVABLE_VELOCITY  PASS -> INSUFFICIENT_DATA   DEGRADED
   CLEAN_LARGECAP  FOR_01_CASH_CONVERSION      PASS -> PASS                same
   ```
   Any difference → exit 1, listing only the changed rows.
3. **Dataset age.** `(today - NIFTY_50_DATASET_DATE).days` against the threshold. Over threshold →
   **WARN** (does not change the exit code), with the actual age in days.
4. **Model watchlist age.** `monitoring/model_watchlist.json` contains
   `{"last_verified": "YYYY-MM-DD", "models": [...]}`. Older than the threshold → WARN.
   Also assert its `models` list equals `analyzer.SUPPORTED_MODELS`; a mismatch means someone
   changed the model list without re-verifying it → exit 1.

### Online checks (`--online` only)

Each probe: 3 attempts, exponential backoff (2s, 4s), 20s timeout. All probes are read-only and
rate-limited (one request per source per run).

1. **Yahoo.** Call `nifty_universe.fetch_live_market_data` for `RELIANCE`, `TCS`, `HDFCBANK`.
   Success requires a non-`None` result with `data_status` in `{"live", "provider"}` for at least
   2 of 3. If all three return `sample_fallback` or `None` → exit 3 with "Yahoo source unavailable
   or fallback-only". Do not treat one failure as structural.
2. **Filing discovery.** `annual_report_fetcher.get_available_annual_reports("RELIANCE")` must
   return at least one URL. Note in the report that discovery goes through **screener.in** and the
   PDFs are on BSE — the probe covers both hops. Zero results after retries → exit 3.
3. **Gemini model availability.** Only if `GEMINI_API_KEY` is set:
   `genai.Client(api_key=...).models.list()` and assert every id in `SUPPORTED_MODELS` is present.
   Missing id → exit 3 with `model id unavailable: <id>`. No key → print "skipped (no key)" and
   do not fail. Never print the key. This is a free metadata call; it does not consume generation
   quota.
4. **Cache age sanity.** Read `.cache/evaluations/*.json`; if any has `created_at` older than
   4× `MAX_CACHE_AGE_HOURS`, WARN "cache files are not being purged". This catches a broken TTL.

### Baseline update

`--update-baseline` must:

1. Refuse to run when `GITHUB_ACTIONS=true` unless `ALLOW_BASELINE_UPDATE=1` — CI never rewrites
   the truth. Exit 4 with a clear message.
2. Require `--reason` and refuse an empty or generic reason ("update", "fix", "test").
3. Rewrite only `monitoring/baseline.json`, preserve `schema`, set `generated_at` and the new
   fingerprint, and print a diff summary of what changed.
4. Never write outside `monitoring/`.

### Output

- Default: human-readable lines, one per finding, prefixed `OK`, `WARN`, `DRIFT`, `STALE`,
  `UNAVAILABLE`.
- `--json`: one JSON object on stdout with `status`, `exit_code`, `fingerprint`, `findings[]`,
  `probes{}`. This is what the workflow consumes.

## Task 4 — `tools/alert_issue.py` (stdlib only)

The alert channel is a GitHub issue. No webhook, no paid service.

Inputs: `GITHUB_TOKEN`, `GITHUB_REPOSITORY` (`owner/repo`), `GITHUB_RUN_ID`, optional
`GITHUB_SERVER_URL`.

Behaviour:

1. Read the monitor's JSON output from a file path passed via `--body-file`.
2. Title: `[data-truth] <signature>`, where signature is a stable slug such as
   `fixture-drift`, `yahoo-unavailable`, `bse-no-filings`, `model-unavailable`, `stale-dataset`.
3. Search open issues with label `data-truth`; if one exists with the exact title, **comment**
   with a new occurrence (timestamp, run URL, findings). Otherwise **create** it.
4. Labels: `data-truth` plus a severity label (`severity:drift`, `severity:source`,
   `severity:warning`). Create labels if missing (REST API, idempotent).
5. Body format:
   ```markdown
   **What changed:** <one line>
   **Detected:** <UTC timestamp>
   **Workflow run:** <run URL>
   **Fingerprint:** <sha256 prefix>
   **Findings:**
   <table of check ids and status transitions>
   **What to do:** see docs/MONITORING.md#<signature>
   ```
6. **Redaction:** apply the same rules as the logger — strip anything matching
   `AIza[0-9A-Za-z_-]{20,}`, never include `financial_statements`, `detail` text, prompts, or
   uploaded document content. Add a test.
7. No token set (local run) → print the body to stdout, exit 0, create nothing.
8. Do not auto-close issues. A human closes after triage.
9. On recovery, the workflow may comment "Recovered at <run URL>" on the matching open issue, but
   only for `severity:source` — never auto-close drift.

## Task 5 — `.github/workflows/monitor.yml`

Required:

1. Triggers:
   ```yaml
   on:
     schedule:
       - cron: "30 21 * * *"   # 03:00 IST daily
       - cron: "30 21 * * 1"   # same time, Mondays: dependency job
     workflow_dispatch:
     release:
       types: [published]
   ```
2. `permissions: contents: read` and `issues: write`. Nothing else.
3. `concurrency: {group: data-truth-monitor, cancel-in-progress: false}` — overlapping runs must
   not race on issue comments.
4. `timeout-minutes: 15` per job.
5. Jobs:
   - **`truth`** — checkout, Python 3.11, `pip install -r requirements.txt`,
     `python tools/monitor.py --check --offline --json > /tmp/monitor.json`.
     On failure: `python tools/alert_issue.py --body-file /tmp/monitor.json --signature ...`.
   - **`sources`** — same, with `--online`. Network flake is expected; the script retries 3 times
     before declaring `UNAVAILABLE`. Do **not** wrap it in `continue-on-error`; a structural source
     failure should be a red run and an issue.
   - **`models`** — same; skips internally when `GEMINI_API_KEY` is absent. Pass the secret via
     `env: GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}`. Do not echo it.
   - **`deps`** — only on the Monday schedule or `workflow_dispatch`: fresh
     `pip install -r requirements.txt` + full `unittest` suite on Python 3.11 and 3.12, to catch
     upstream releases inside the allowed ranges. On failure, alert with signature
     `dependency-drift`.
6. Every job writes a `$GITHUB_STEP_SUMMARY` section: status, fingerprint prefix, findings count,
   and the probe results. The summary is the free dashboard.
7. Do not add `pull_request` — this workflow is for scheduled truth, not PR gating (Phase 5's
   `tests.yml` already gates PRs).

Note in `docs/MONITORING.md`: GitHub **disables scheduled workflows after 60 days of repository
inactivity**. Re-enable from the Actions tab when that happens. This is a real limitation of a free
monitor; state it rather than implying it runs forever.

## Task 6 — `monitoring/model_watchlist.json`

```json
{
  "last_verified": "YYYY-MM-DD",
  "models": ["gemini-3.5-flash", "..."],
  "notes": "Verified against the Gemini API on <date>. gemini-3.5-flash is deprecated and auto-routed."
}
```

`models` must equal `analyzer.SUPPORTED_MODELS` exactly. `last_verified` is the date of a real
verification, not today's date by default — if you did not call the API, put the date of the last
verification you can attest to, and say so in the report.

## Task 7 — `docs/MONITORING.md`

Max 90 lines:

1. **What is monitored** — the four offline checks, the four online probes, dependency drift.
2. **What is not monitored** — wrong prices, wrong field mappings that still return numbers,
   LLM output quality, legal/compliance status, UI regressions without a unit test. Say it plainly.
3. **Severity and response** — one row per signature: what it means, what to check first, who
   fixes it.
4. **Baseline update procedure** — edit code → suite green → `--update-baseline --reason "..."` →
   review the diff → commit. CI refuses to do this.
5. **Free-tier math** — 4 jobs/day, ~2 min each, plus a weekly dependency job → well under the
   free minutes for a private repo; public repos are unlimited. No paid service.
6. **The 60-day disable caveat.**
7. **How to run locally** — the four commands, and which ones need a key/network.

## Task 8 — Tests: `tests/test_monitoring.py` (stdlib, no network)

1. **Fingerprint match, no change** → exit 0.
2. **Fingerprint mismatch** → exit 2, and the message names which input changed.
3. **Simulated drift** — patch the engine to return `INSUFFICIENT_DATA` for a check that the
   baseline records as `PASS` → exit 1, output contains the check id and both statuses.
4. **Simulated fabrication** — patch `INSUFFICIENT_DATA` → `PASS` → exit 1 with `DEGRADED/RECOVERED`
   classification. A recovery without new data is as suspicious as a degradation.
5. **Baseline update refused in CI** — `GITHUB_ACTIONS=true` → exit 4, file unchanged.
6. **Baseline update requires a reason** — empty or `"update"` → exit 4.
7. **Dataset age** — a baseline date 1,000 days old with threshold 900 → WARN, exit 0.
8. **Model watchlist mismatch** — a model not in `SUPPORTED_MODELS` → exit 1.
9. **Alert redaction** — a findings payload containing `AIzaSy...` and a fake financial statement
   must not appear in the generated issue body.
10. **No network in tests** — patch `fetch_live_market_data` and `get_available_annual_reports`;
    assert they were not called by the offline suite. The existing `test_hygiene.py` rules still
    apply.
11. **Workflow shape** — parse `monitor.yml` as text (no PyYAML dependency) and assert:
    `issues: write`, `timeout-minutes`, a `schedule` block, and that `GITHUB_TOKEN` is not echoed
    (`grep -c "echo .*GITHUB_TOKEN" == 0`).

## Task 9 — README + plan

1. Add a badge under the title, using the real remote from `git remote -v`:
   ```markdown
   ![Data Truth Monitor](https://github.com/<owner>/<repo>/actions/workflows/monitor.yml/badge.svg)
   ```
   A red badge is the point — do not omit it because it might be red.
2. Add a **Monitoring** section: 3 lines, link `docs/MONITORING.md`, state that alerts are GitHub
   issues and that the baseline is human-updated.
3. Tick Phase 8 in `docs/PHASED_PLAN.md`, including the 60-day caveat and the fact that the peer
   dataset is already older than its threshold (if it is).

## Verification — all of this must succeed

```bash
shasum improvement_ledger.json IMPROVEMENT_LEDGER.md > /tmp/ledger_before.sha

python -m py_compile tools/monitor.py tools/alert_issue.py

python tools/monitor.py --check --offline
echo "exit=$?"

python tools/monitor.py --check --offline --json | head -40

python -m unittest discover -s tests
python -m unittest tests.test_monitoring -v

shasum -c /tmp/ledger_before.sha

ls monitoring/baseline.json monitoring/model_watchlist.json \
   .github/workflows/monitor.yml docs/MONITORING.md

grep -n "issues: write" .github/workflows/monitor.yml
grep -n "timeout-minutes" .github/workflows/monitor.yml
grep -c "echo .*GITHUB_TOKEN" .github/workflows/monitor.yml
```

Drift simulation — required proof, run it and paste it:

```bash
cp monitoring/baseline.json /tmp/baseline.bak
python - <<'PY'
import json
p = "monitoring/baseline.json"
b = json.load(open(p))
b["fixtures"]["CLEAN_LARGECAP"]["checks"]["FOR_02_RECEIVABLE_VELOCITY"] = "INSUFFICIENT_DATA"
json.dump(b, open(p, "w"), indent=2)
PY
python tools/monitor.py --check --offline; echo "exit=$?"   # must be 1, naming FOR_02
cp /tmp/baseline.bak monitoring/baseline.json
```

Online probe (only if a key is available; otherwise record "not run — no key"):

```bash
python tools/monitor.py --check --online; echo "exit=$?"
```

Acceptance criteria:

- Offline monitor exits **0** on the current tree, and prints the dataset age as a WARN if it
  exceeds the threshold (it is allowed to be old; it is not allowed to be hidden).
- Drift simulation exits **1** and names the changed check.
- Fingerprint mismatch exits **2**.
- `--update-baseline` in `GITHUB_ACTIONS=true` exits **4** and leaves the file byte-identical.
- Suite `OK`; test count ≥ previous + the new monitoring tests.
- `monitor.yml` contains `issues: write`, `timeout-minutes`, a schedule, and does not echo the
  token.
- Ledger files byte-identical.
- Nothing under `.cache/` or `monitoring/` was modified by the test run (except temp copies).

## Final report — required format

1. **Baseline summary** — fingerprint inputs, per-fixture FQI/badge at baseline, dataset date and
   computed age, and the thresholds chosen with a one-line justification each.
2. **Checks implemented** — table: check, offline/online, exit code on failure, what it catches.
3. **Drift simulation output** — pasted verbatim, including `exit=1`.
4. **Stale-baseline proof** — how you triggered exit 2 (e.g. temporarily bump `ENGINE.VERSION`) and
   the output. Restore afterwards.
5. **Workflow** — the cron schedule, jobs, permissions, and the free-minute estimate. If the repo
   has not been pushed, say the workflow has **not run** — do not imply it is verified in Actions.
6. **What is not monitored** — the honest list from `docs/MONITORING.md`.
7. **Verification output pasted verbatim** — monitor exit code, `Ran N tests` / `OK`, `shasum -c`,
   the `grep` results.
8. **Found but out of scope.**

Do not claim the monitor is "permanent" if the repository is not on GitHub with Actions enabled.
State the 60-day disable rule and the fact that a scheduled workflow is only as permanent as the
repository's activity.

===END PROMPT===
