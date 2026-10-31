# Phase 8b — Truth repairs found in post-deployment audit

Copy everything between the markers into Antigravity, with the repository open at root.

**Context:** all 8 phases are committed and green (`main` @ `82292bd`, 200 tests `OK`,
monitor run `41227247509` all 5 jobs ✓). This prompt fixes four defects found by auditing the
deployed state. Two are unbacked claims inside the truth-monitoring system itself.

---

===BEGIN PROMPT===

# TASK: Phase 8b — "Truth Repairs" for Project KUSHA

## Context

Phases 1-8 are deployed. An external audit of the deployed repository (not the working tree)
found four defects. Three are lies or stale statements; one is a documented instruction the
repository does not follow. Fix all four. Do not redesign anything.

Measured state at the start of this task:

| Fact | Evidence |
|---|---|
| `main` @ `82292bd`, tree clean | `git status --porcelain` empty |
| 200 tests, `OK` | `python -m unittest discover -s tests` |
| Tests & Code Quality: 5/5 success | `gh run list --limit 5` |
| Data Truth Monitor: 1 run, 5/5 jobs ✓ | `gh run view 41227247509` (workflow_dispatch, run by auditor) |
| Repository visibility | `gh repo view --json visibility` → **PUBLIC** |
| Repository secrets | `gh secret list` → **empty** |
| CI model probe | logged `Gemini model availability probe skipped (no GEMINI_API_KEY set)` |

## Non-negotiable constraints

- **Zero cost.** No new dependencies, no paid service.
- **Do not fabricate a verification.** If you did not call the Gemini API with a key, say so
  in the file. An honest "not verified" beats a false "verified".
- **Do not decide the licence.** Task 3 records an open decision; it does not resolve it.
- **Do not weaken the monitor** to make anything green. WARN is the correct output for an
  unverified claim.
- **Keep the suite green.** 200 tests plus whatever you add.

---

## Task 1 — Remove the false model-verification attestation (highest severity)

`monitoring/model_watchlist.json` currently reads:

```json
{
  "last_verified": "2026-10-31",
  "models": [ ... 6 ids ... ],
  "notes": "Verified against the Gemini API on 2026-10-31. gemini-3.5-flash is deprecated and auto-routed; gemini-3.8-flash experienced temporary 503 high demand."
}
```

That is false. There is no `GEMINI_API_KEY` in repository secrets, and the CI probe explicitly
skipped. Nobody called the API on 2026-10-31 from this repository. The `gemini-3.8-flash`
503 anecdote is likewise unobservable here.

### 1a. Add explicit provenance to the schema

Add two fields to `monitoring/model_watchlist.json`:

```json
{
  "schema": 1,
  "last_verified": "YYYY-MM-DD",
  "verification_method": "api_call" | "docs_review" | "unverified",
  "verified_with_api": false,
  "models": [ ... ],
  "notes": "..."
}
```

Definitions — the agent must pick the one that is **actually true**:

- `api_call` — a real `models.list()` call was made with a working key. `verified_with_api` must
  be `true`. `last_verified` is the date of that call.
- `docs_review` — the list was checked against published Google documentation only. `last_verified`
  is the date of that review, and `notes` must start with `Checked against published Gemini model
  documentation only; not verified against the live API.`
- `unverified` — neither happened. `last_verified` must be `null`.

**If a key is available to you**, run `tools/check_api_key.py` (or a `models.list()` call),
confirm every id in `analyzer.SUPPORTED_MODELS` responds, and use `api_call`. Record which path
you took in the report. If no key is available, use `docs_review` or `unverified` — never
`api_call`.

Remove the 503 sentence unless you observed it yourself in this task.

### 1b. Make the monitor surface the provenance

In `tools/monitor.py`, in the existing model-watchlist block (~line 263-292), after the models
equality check:

- `verification_method == "api_call"` → `OK: Model list verified against the live Gemini API on <date>`
- anything else → `WARN: Model list is NOT verified against the live API (method=<value>); ids may be stale or retired`
- `verified_with_api` disagreeing with `verification_method` → `MISCONFIGURED` (exit 4), because
  the file contradicts itself.

This is a WARN, not a failure. The point is that the run summary always states the truth.

### 1c. Tests (`tests/test_monitoring.py`)

Add:

- `test_12_watchlist_schema_requires_provenance` — missing `verification_method` →
  `MISCONFIGURED`, exit 4.
- `test_13_watchlist_self_contradiction_exits_4` — `verification_method="api_call"` with
  `verified_with_api=false` → exit 4.
- `test_14_non_api_verification_warns_but_exits_0` — `docs_review` → a `WARN` mentioning
  "NOT verified", exit 0.
- `test_15_watchlist_last_verified_not_in_future` — parse `last_verified`; if it is after today
  → fail. This is the check that would have caught the original defect.

## Task 2 — Fix the broken CI badge

`README.md:3`:

```markdown
[![CI](https://github.com/ashu2ashu/project-kusha/actions/workflows/ci.yml/badge.svg)](https://github.com/ashu2ashu/project-kusha/actions/workflows/ci.yml)
```

`.github/workflows/ci.yml` does not exist. The test workflow is `tests.yml` (name
"Tests & Code Quality"), which has 5 successful runs. A badge pointing at a missing workflow
renders "no status" forever — a dead indicator that looks like a working one.

1. Point it at `tests.yml` in both the image URL and the link.
2. Verify `monitor.yml` badge (line 4) is correct — it is, leave it.
3. Add `test_12_every_readme_badge_resolves` to `tests/test_phase7_docs.py`: extract every
   `actions/workflows/<file>/badge.svg` from README, assert `<file>` exists under
   `.github/workflows/`. This is the check that would have caught the original defect.

## Task 3 — Reconcile the licence statement with observed reality (DO NOT DECIDE)

Two contradictory statements coexist:

- `docs/LEGAL_DECISIONS.md` Decision 3: *"Proprietary / all rights reserved (PROVISIONAL)"*, with
  the consequence *"no license granted to public"*.
- `README.md:108`: *"All rights reserved. No licence granted. Keep the repository private."*
- Observed: `gh repo view --json visibility` → **PUBLIC**, `origin/main` pushed, three phase
  branches on the remote.

The README is instructing the owner to do something the repository does not do. Do not pick
private or public — you are not the owner.

Required:

1. **README §Licence** — replace the instruction with a fact plus an open decision:

   ```markdown
   ## 10. Licence

   All rights reserved. No licence is granted; no permission to use, copy, modify, or
   redistribute is given. The source is currently published at
   <repository URL from `git remote -v`>. Publication is not a licence grant.

   The distribution decision (public repository vs private workspace) is recorded as **OPEN** in
   [docs/LEGAL_DECISIONS.md](docs/LEGAL_DECISIONS.md); it has not been confirmed by the owner.
   ```

2. **`docs/LEGAL_DECISIONS.md`** — keep Decision 3 as PROVISIONAL, and add a row:

   | 5. Repository Visibility | Public repository / Private repository | **OPEN — not decided** | — | Product Owner | Source is currently PUBLIC with no licence granted. One of: make private, keep public under all-rights-reserved, or adopt an OSS licence. |

   Add no reasoning you cannot support. Do not claim the owner chose anything.

3. `docs/PRIVACY.md` — one line: the source is public but the tool is not hosted; no user data is
   published.

4. **`test_13_licence_statement_matches_repo_state`** in `tests/test_phase7_docs.py`: assert README
   contains "No licence is granted" and does **not** contain "Keep the repository private" (the
   removed instruction). Do not assert the remote's visibility — tests must not require network.

## Task 4 — Correct the stale plan caveat

`docs/PHASED_PLAN.md`, Phase 8 section, currently ends with:

> The workflow has not run in cloud CI until the repo is pushed with Actions enabled.

That is now stale and understates the work. Replace with the measured fact:

> The monitor has run in cloud CI: run `41227247509` (workflow_dispatch, 2026-10-31) — 5/5 jobs
> green; offline truth exit 0 with a WARN that the peer dataset is 944 days old; Yahoo 3/3 live;
> 14 BSE filings discovered for RELIANCE; Gemini probe skipped (no `GEMINI_API_KEY` secret
> configured). Scheduled runs begin at 21:30 UTC daily.

Also add to Phase 8 the open item: "Model list provenance is `docs_review`, not `api_call` —
add the `GEMINI_API_KEY` secret to enable a real probe."

## Task 5 — Verification

Run all of this and paste the output:

```bash
git status --porcelain                 # expect empty before you start

python -m py_compile tools/monitor.py
python -m unittest discover -s tests
python -m unittest tests.test_monitoring tests.test_phase7_docs -v 2>&1 | tail -5

python tools/monitor.py --check --offline
echo "exit=$?"

python - <<'PY'
import json
w = json.load(open("monitoring/model_watchlist.json"))
print("method:", w["verification_method"], "| api:", w["verified_with_api"], "| date:", w["last_verified"])
PY

grep -n "badge.svg" README.md
grep -rn "Keep the repository private" README.md docs/ || echo "stale instruction removed"
grep -c "def test_" tests/*.py | awk -F: '{s+=$2} END {print "test defs:", s}'

shasum improvement_ledger.json IMPROVEMENT_LEDGER.md > /tmp/ledger.sha
# ... run the suite ...
shasum -c /tmp/ledger.sha
```

Then commit and push, and confirm the badge renders:

```bash
git add -A
git commit -m "fix(truth): honest model verification provenance, working CI badge, licence reconciliation"
git push origin main
gh run list --limit 3
```

Acceptance criteria:

- `monitoring/model_watchlist.json` contains `verification_method` and `verified_with_api`, and
  the values are true statements about what actually happened in this task.
- The monitor prints a `WARN` (not `OK`) for the model list when the method is not `api_call`.
- README badges all resolve to existing workflow files.
- README contains no instruction the repository does not follow; the visibility decision is
  recorded as OPEN, not silently resolved.
- Suite `OK`, ≥ 200 + 5 new tests.
- Ledger files byte-identical.
- Pushed to `origin/main`; the new `tests.yml` run is green.
- Ledger and `.cache/` untouched.

## Final report — required format

1. **Model provenance:** which method you used and why; the exact evidence (API call output, doc
   URL, or "no key, therefore docs_review"). If you used `api_call`, paste the probe output.
2. **Badge:** before/after lines, and the new test that prevents recurrence.
3. **Licence:** the exact README diff and the new OPEN row. State plainly that you did not decide it.
4. **Plan caveat:** the old sentence and the replacement.
5. **Verification output pasted verbatim** — suite count, monitor exit code and lines, watchlist
   provenance print, badge grep, ledger `shasum -c`.
6. **Found but out of scope.**
7. **Confirmation** that the work is pushed and which `tests.yml` run is green.

Do not describe the model list as "verified" unless you called the API. Do not close the
visibility decision. Do not add a `LICENSE` file.

===END PROMPT===
