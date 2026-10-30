# Phase 7 — Docs, Legal & Positioning

Copy everything between the markers into Antigravity, with the repository open at root.

**This phase is blocked by an unfinished Phase 6 and by three owner decisions.** Task 0 handles
both. Do not rewrite the README on top of a red test suite — it would document a state that does
not exist.

---

===BEGIN PROMPT===

# TASK: Phase 7 — "Docs, Legal & Positioning" remediation of Project KUSHA

## Context

Phases 1-6 fixed what the code *does*. Phase 7 fixes what the project *says about itself*.

Right now the documentation describes a product that no longer exists, and the legal posture
contradicts the code:

- The README claims the app scores companies "deterministically". Pillar scores are produced by
  Gemini and are not reproducible across runs or model versions. Only the arithmetic applied
  afterwards is deterministic.
- The README and the app claim "Trade Secret Protection" and "compiled under internal IP
  safeguards". The scoring weights are plain Python in a local repository. Nothing is compiled,
  protected, or secret.
- The README lists `gemini-3.5-flash` as the default. Google's API docs now mark it **deprecated,
  automatically routed to `gemini-3.6-flash`**.
- The README says it is not a SEBI-registered adviser, while the app computes `BUY` / `HOLD` /
  `AVOID` stances and allocation bands ("10–15%"). A disclaimer does not neutralise an advisory
  output.
- `docs/BROWSER_VERIFICATION_REPORT.md` reports "6 / 6 CHECKS PASSED — ALL CLEAR" and a DCF fair
  value. Phase 6 changed exactly that behaviour: the shield now reports `NOT EVALUATED` when the
  engine did not run a check, and the DCF was removed in Phase 1. The report is now false.
- `docs/PRODUCT_DESIGN_AND_IMPLEMENTATION_REPORT.md` says "73 unit tests". There are 169.
- There is no `LICENSE`, no privacy notice, and no limitations page.

## Non-negotiable constraints

- **Zero cost.** No paid legal service, no paid docs hosting.
- **No new dependencies.**
- **Do not invent a licence.** Licence choice is the owner's; see Task 1.
- **Do not claim legal compliance you cannot verify.** "Not registered with SEBI" is a fact.
  "Compliant with SEBI RA Regulations" is a legal conclusion you are not qualified to assert.
- **Documentation must describe the code as it is**, not the roadmap.

---

## Task 0 — Gate: finish Phase 6 and record the decisions

### 0a. Phase 6 is incomplete and the suite is red

Current state, measured:

| Item | Expected after Phase 6 | Actual |
|---|---|---|
| `app.py` length | ≤ 3,400 lines | 3,031 — done |
| `kusha_render.py` | 14 pure functions | exists, shield rows extracted — done |
| `assets/kusha.css` | exists, byte-identical | exists — done |
| `pyproject.toml` | exists | **missing** |
| `docs/ARCHITECTURE.md` | exists | **missing** |
| `tests/test_architecture.py` | 10 ratchets | **missing** |
| root `FORENSIC_FRAMEWORK_ANALYSIS.md` | deleted (duplicate) | **still present** |
| full suite | `OK`, ≥169 | **169 run, 8 failures + 1 error** |

The nine failures are Phase 6 migration fallout, not new bugs:

- `test_phase1_truth_layer.test_pillar_chips_match_canonical_pillars` — reads
  `_PILLAR_STYLE = [` from `app.py`; it moved to `kusha_render.py`.
- `test_phase1_truth_layer.test_app_routes_red_zones_through_guardrail_level` — counts guardrail
  call sites in `app.py`; some moved to `kusha_render.py`. The check must scan both files.
- `test_terminal_quality.TestCSSMotionAndFluidity.*` (3 tests) — assert CSS strings inside
  `app.py`; the CSS moved to `assets/kusha.css`. Point them at the CSS file.
- `test_terminal_quality.test_fraud_shield_clean_statutory_filings_pass_all_six_checks` and
  `..._handles_string_and_na_dso` — assert the **old, fabricated** shield output
  (`CLEAN AUDIT`, `DSO: N/A`). Phase 6 deliberately replaced those with engine statuses and
  `NOT EVALUATED`. These two tests encode the old falsehood; rewrite them to assert the new
  contract, and say so in the report. Do not revert the shield to satisfy them.
- `test_evaluation_cache.test_save_and_load_cached_evaluation` and
  `test_get_cache_stats_and_clear` — inspect why they fail before changing anything; likely the
  cache payload/signature changed. If the test is right, fix the code.

Finish Phase 6 first:

1. Create `pyproject.toml` with dependencies single-sourced from `requirements.txt`, add `numpy`,
   bound every dependency, and raise the `streamlit` floor to a version you verified by installing
   it and running the AppTest smoke check.
2. Create `docs/ARCHITECTURE.md` and `tests/test_architecture.py` (the 10 ratchets from the Phase 6
   prompt).
3. Delete the duplicate root `FORENSIC_FRAMEWORK_ANALYSIS.md`.
4. Fix the nine failures. For the two shield tests, rewrite the assertions — they were asserting
   fabricated behaviour.
5. Commit before starting Phase 7 docs:
   ```bash
   git add -A
   git commit -m "phase 6: extract render module, unify shield and score bands, packaging"
   git rev-parse HEAD
   ```

**Gate:** `python -m unittest discover -s tests` prints `OK` with ≥169 tests, `AppTest` prints
`EXCEPTIONS: 0`. Do not proceed otherwise.

### 0b. Owner decisions — the honest options

Record these in `docs/LEGAL_DECISIONS.md` (created in Task 2). If the owner has not answered before
you start, apply the **conservative default** marked below and record it as *provisional*. Do not
silently pick the permissive option.

**Decision 1 — SEBI posture.** The app currently produces directional stances and allocation
bands. That is what the regulations care about, not the disclaimer.

| Option | What it means | Consequence |
|---|---|---|
| **A. De-advisory reframing (default, provisional)** | Remove `BUY`/`HOLD`/`AVOID` stances and numeric allocation bands from every output. Keep the quality score, verdict band, red flags, and a qualitative risk tier ("Constructive / Monitored / Elevated Caution"). | No registration needed for the *output type*. Reversible. Loses the "actionable" feel. |
| B. Keep as-is with disclaimers | Current state. | A disclaimer does not cure advisory output. If the app is distributed publicly, this is the weakest position. |
| C. Register as RA/IA | Real compliance. | Not free, not this project. Out of scope. |

If the app is **personal and never distributed**, Option B is defensible; if it is published,
Option A is the honest default. Default when unanswered: **A**, labelled provisional.

**Decision 2 — Distribution.** Personal/local only, or published? This is the fact that decides
Decision 1. Default when unanswered: **personal/local**, and the README must say so explicitly.

**Decision 3 — Licence.** There is no `LICENSE` file, while the README advertises "Trade Secret
Protection" — the two claims are incompatible whichever way you go.

| Option | Action |
|---|---|
| Proprietary / all rights reserved (default when unanswered) | Do **not** add a permissive licence. Add one line to README: "All rights reserved. No licence granted." Keep the repository private. |
| MIT / Apache-2.0 | Add the full standard text as `LICENSE`, remove every trade-secret claim, and note the licence in README. |

**Decision 4 — Data redistribution.** Yahoo Finance data and BSE filing PDFs are third-party.
Confirm the tool does not redistribute raw data or repackage it as a dataset; it fetches on demand
for local analysis. State this in the privacy/data notice.

---

## Task 1 — Rewrite the README so every claim is checkable

**File:** `README.md` (currently 137 lines, ~20 claims, several false).

Required structure, in this order:

1. **What this is** — three lines, no adjectives: "A local Streamlit app that sends Indian listed
   company financials and optional annual-report PDFs to Google Gemini, and renders an AI-generated
   8-pillar quality score, forensic checks, and evidence gaps. It is a screening aid, not an
   audit, valuation, or advice."
2. **What this is not** — not SEBI-registered, not an audit, not a DCF, not real-time, not
   reproducible across model versions.
3. **Data sources and freshness** — Yahoo Finance (~4 years, unaudited, delayed); BSE India
   public filing archive; Gemini web grounding. Each with a link and a one-line limitation.
4. **Quickstart** — Python **3.11+** (not 3.10; CI is 3.11/3.12), venv, install, key, run.
5. **Models** — generated from `analyzer.SUPPORTED_MODELS`, inside markers, plus one sentence:
   "Model availability and free-tier quotas change; verify in AI Studio." Mark
   `gemini-3.5-flash` as deprecated/auto-routed **if it is still in the list**, and remove any
   unverified adjectives ("ultra-low latency", "recommended by Google").
6. **Demo mode** — synthetic, labelled, not research.
7. **Security & privacy** — 6 lines max, linking `docs/PRIVACY.md`. Must state: PDFs leave the
   machine and go to Google; local cache is plaintext JSON; the free tier's data-use terms differ
   from paid — do not upload confidential filings.
8. **Limitations** — link `docs/LIMITATIONS.md`, plus the three that matter most inline (AI scores
   are not reproducible; peer data is an FY24 reference set; auditor/governance checks are usually
   not evaluated).
9. **Testing** — keep the existing section, correct the count.
10. **Licence** — per Decision 3.

Delete outright, from README and from any doc:

- "evaluates companies deterministically" → "the arithmetic after the model returns is
  deterministic; the scores are not".
- "Trade Secret Protection", "compiled under internal IP safeguards", "proprietary scoring
  thresholds".
- "100% Free Public Access: Zero marker/API costs" → "no paid data vendor; Gemini free-tier quota
  applies" (and fix the "marker" typo).
- "institutional-grade", "Institutional Research Memo", "Institutional Report",
  "Institutional Equity Research Brief" — replace with "research memo/brief". The product is a
  local screening tool; "institutional-grade" is a quality claim with nothing behind it.
- "The Gemini API key ... never persisted to logs or disk" — qualify: it is held in session memory
  when entered in the UI; if you use `.env`, it is stored in plaintext on disk. Logs redact it.

**Model list accuracy:** the one task here that needs a live key. For each entry in
`SUPPORTED_MODELS`, make a minimal call and confirm it responds. Remove or mark deprecated any that
does not. If no key is available, do **not** guess: leave the code alone and label the README list
"unverified — run `tools/check_api_key.py`". Record which path you took.

## Task 2 — `docs/LEGAL_DECISIONS.md` (the decision record)

Max 60 lines. A table, one row per decision:

| Decision | Options considered | Chosen | Date | Owner | Consequence |
|---|---|---|---|---|---|

Then four short sections with the reasoning from Task 0b, and this sentence verbatim:

> This document records product decisions, not legal advice. If the tool is distributed publicly,
> obtain a qualified opinion on SEBI (Research Analysts) Regulations, 2014 and SEBI (Investment
> Advisers) Regulations, 2013.

Mark any defaulted decision **PROVISIONAL** in bold.

## Task 3 — `docs/PRIVACY.md`

Max 70 lines. Answer these questions plainly; do not use "we respect your privacy" filler.

1. **What leaves your machine** — uploaded PDF bytes (Gemini Files API), prompts containing company
   name/sector/financial extracts, web-search queries (Gemini grounding), ticker lookups (Yahoo
   Finance), archive requests (bseindia.com). Name the recipient for each.
2. **What stays local** — `.cache/evaluations/*.json` (full analysis, plaintext), `.cache/feedback/*.json`
   (free-text analyst comments), `improvement_ledger.json`, optional log file. Give the paths.
3. **Retention** — cache entries expire after 24h and entries older than 4× TTL are deleted;
   feedback and ledger files are kept until you delete them. State that Google's retention is
   governed by its API terms and that the free tier's data-use terms differ from paid — verify the
   current terms before uploading anything confidential.
4. **API key handling** — session memory when entered in the UI; plaintext in `.env` if used; redacted
   from logs; sent only to Google.
5. **No telemetry** — `gatherUsageStats = false`; no analytics, no crash reporting.
6. **Single-user assumption** — the app has no multi-user isolation; anyone with access to the
   process can read the cache and session state. Do not host it for multiple users.
7. **How to delete your data** — the exact paths and commands.

## Task 4 — `docs/LIMITATIONS.md` (the page that makes the product honest)

Max 80 lines. This is the most valuable document in the phase. Cover, one short paragraph each:

- **Scores are AI-generated and not reproducible.** Same company, same model, different run → may
  differ. The arithmetic (banding, penalties, PIO clamp) is deterministic; the inputs are not.
- **FQI is withheld below 75% check coverage.** The auditor check (`FOR_08`) has no data source and
  is normally `INSUFFICIENT_DATA`; 7/8 is the realistic maximum.
- **Forensic checks are heuristics, not fraud detection.** Each check is a ratio rule with a
  threshold; passing them proves nothing.
- **Peer data is a dated reference set** (`FY24`), not live; cross-period comparisons are refused or
  warned about, not silently ranked.
- **Market data is Yahoo Finance**, delayed and unaudited, ~4 years of statements, subject to
  restatement.
- **No auditor, CARO, RPT, insider-trading or litigation database** is consulted.
- **BSE retrieval depends on a public archive** and can fail or return an older filing.
- **Cache replay** may show an analysis up to 24h old; the UI shows its age.
- **Demo mode is synthetic.**
- **"Fair value" is a model opinion**, not a DCF; no WACC, no terminal value.
- **Currency/units**: ₹ crore unless stated; ratios depend on the provider's field mapping.
- **Not an audit, not advice, not a valuation.**

Every line must be true of the current code. If you cannot verify a limitation, cut it.

## Task 5 — Retire the false and stale documents

Current `docs/` contents and their status:

| File | Problem | Action |
|---|---|---|
| `docs/BROWSER_VERIFICATION_REPORT.md` | Claims "6 / 6 PASSED — ALL CLEAR", `CLEAN AUDIT`, and a DCF fair value. Phase 6 made those impossible; Phase 1 removed the DCF. | Move to `docs/history/`, prepend a `> **HISTORICAL — superseded.**` banner explaining what is no longer true. |
| `docs/EXTENSIVE_BROWSER_WALKTHROUGH_REPORT.md` | Same, plus "10-pillar scorecards" (there are 8). | Same. |
| `docs/FORENSIC_FRAMEWORK_ANALYSIS.md` | Describes a DCF with WACC 11.2% / g 5.0% and claims "every analytical layer operates deterministically". The DCF does not exist. | Move to `docs/history/` with a banner, or rewrite to match the 8 real checks. Say which you did and why. |
| `docs/PRODUCT_DESIGN_AND_IMPLEMENTATION_REPORT.md` | "73 unit tests" (actual: 169), 10 pillars, pre-remediation claims. | Move to `docs/history/` with a banner. |
| `docs/REMEDIATION_PLAN.md` | References dead models (`gemini-2.5-flash`, `1.5-flash`) and describes work already done. | Move to `docs/history/` with a banner. |
| root `FORENSIC_FRAMEWORK_ANALYSIS.md` | Byte-identical duplicate. | Delete (Phase 6 task). |
| `docs/PHASED_PLAN.md` | Current plan. | Keep; tick Phase 6/7 at the end. |
| `docs/ARCHITECTURE.md` | Current. | Keep. |

Rules:

1. `docs/history/README.md` — 5 lines explaining that these are preserved for provenance, not
   current documentation, and are not evidence of current behaviour.
2. Every moved file gets the banner as its **first** line. A historical file without a banner is a
   false claim.
3. Do not delete history to make the tree look clean. The reports are evidence of what was
   previously claimed; that is useful.

## Task 6 — De-advisory reframing (only if Decision 1 = A, the default)

If the owner selected B (keep), skip to Task 7 and state in the report that advisory output
remains, with the distribution assumption recorded in `LEGAL_DECISIONS.md`.

If A:

1. **Stance:** replace the `BUY` / `HOLD` / `AVOID` computation in `app.py` (`stance = ...`,
   ~line 2063) with a qualitative risk tier: `Constructive` / `Monitored` / `Elevated Caution`.
   Do not derive it from keyword matching on model text — derive it from the score band and the
   guardrail enum that already exist.
2. **Allocation bands:** `analyzer.SCORE_BANDS` currently carries `position_sizing` strings
   ("10–15%", "0–5%", …). Replace with `risk_tier` labels. Remove every "Illustrative Exposure:
   2–5% Cap", "0.0% Allocation", "Risk Allocation Sizing" string from the UI, exports, and memo.
3. **Wording:** "Analyst Recommendation" → "Research Observations"; "Final Call" → "Summary
   Assessment"; "Investment Memo" → "Research Memo". These are the exact strings that make the
   output read as advice.
4. **Tests:** `tests/test_financial_invariants_suite.py` asserts the old sizing strings
   (`10–15%`, `5–10%`). Update those assertions to the new tier labels — and state in the report
   that the assertion changed because the product contract changed, not to get green.
5. **Exports:** JSON, markdown memo, HTML report and the plain-text brief all change together. A
   stale `position_sizing` field left in one export is worse than keeping it everywhere.

Acceptance: `grep -nE "\b(BUY|SELL|AVOID)\b" app.py kusha_render.py` returns no user-facing
stance; `grep -n "position_sizing" app.py kusha_render.py analyzer.py` returns nothing (or only a
migration comment); exports contain no `%` allocation band.

## Task 7 — Remove in-app overclaims

Exact strings currently rendered to users:

| Location (approximate) | Claim | Action |
|---|---|---|
| `app.py:839` | "Proprietary Quantitative Engine … compiled trade secrets protected under quantitative IP safeguards." | Delete or replace with "Scoring rules are open Python in this repository; the thresholds are listed in the Methodology tab." |
| `app.py:2738` | "Exact mathematical weights … protected under trade secret guidelines to prevent reverse engineering." | Same. |
| `app.py:2745` | "Download institutional-grade research outputs" | "Download research outputs". |
| `app.py:3-4` | "Fundamental & Forensic Institutional Terminal / Institutional AI Financial Intelligence Terminal" | Keep the brand if the owner wants it, but never combine it with "grade". |
| `app.py:1815` | "Institutional Equity Research Brief" | "Equity Research Brief". |
| memo/HTML export | "StockSage Institutional Report" | "StockSage Research Report". |

Also check the Methodology tab for any "compiled", "proprietary", "trade secret", or
"deterministic pipeline" wording and remove it, except where "deterministic" accurately describes
the post-model arithmetic and says so.

## Task 8 — `tests/test_phase7_docs.py` (stdlib `unittest`)

Docs rot silently. These checks make rot fail CI.

1. **Banned claims in README and current docs:** `deterministic` (unless immediately qualified by
   "arithmetic"), `trade secret`, `institutional-grade`, `institutional grade`, `audit-grade`,
   `100% free`, `guarantee`, `compiled under`, `IP safeguards`, `10-pillar`, `10 pillar`.
2. **Required links exist:** README links `docs/PRIVACY.md`, `docs/LIMITATIONS.md`,
   `docs/LEGAL_DECISIONS.md`, and every relative link in README points to a real file.
3. **History banner:** every file under `docs/history/` except `README.md` starts with
   `> **HISTORICAL`.
4. **No duplicate markdown:** no two tracked `*.md` files have identical content.
5. **Model list consistency:** the block between `<!-- MODELS:START -->` and `<!-- MODELS:END -->`
   in README lists exactly `analyzer.SUPPORTED_MODELS`, one per line. (Generate the block with a
   small script, then assert equality.)
6. **No stale test counts:** any `\b\d+ (unit )?tests\b` in docs equals the actual number of
   `def test_` functions, or the phrase is absent. This is the check that catches "73 tests".
7. **Licence consistency:** if `LICENSE` exists, README mentions the same licence name; if it does
   not, README contains "All rights reserved" and no permissive-licence claim.
8. **De-advisory contract (only if Decision 1 = A):** no `BUY`/`SELL`/`AVOID` stance strings in
   `app.py` / `kusha_render.py` user-facing literals; `verdict_band()` returns `risk_tier` and no
   `position_sizing`.
9. **DCF:** no current doc describes a computed DCF or WACC; historical files may, but must carry
   the banner.
10. **Privacy completeness:** `docs/PRIVACY.md` contains "Gemini", "Google", "Yahoo",
    "bseindia.com", `.env`, and `.cache/evaluations`.

## Verification — all of this must succeed

```bash
shasum improvement_ledger.json IMPROVEMENT_LEDGER.md > /tmp/ledger_before.sha

python -m py_compile *.py

python -m unittest discover -s tests
python -m unittest discover -s tests -v 2>&1 | tail -3

python - <<'PY'
from streamlit.testing.v1 import AppTest
at = AppTest.from_file("app.py", default_timeout=120).run()
print("EXCEPTIONS:", len(at.exception))
PY

shasum -c /tmp/ledger_before.sha

ls docs/PRIVACY.md docs/LIMITATIONS.md docs/LEGAL_DECISIONS.md docs/history/
grep -n "MODELS:START" README.md
grep -c "def test_" tests/*.py | awk -F: '{s+=$2} END {print "test defs:", s}'
```

Additional manual checks:

- Open the app and confirm the Methodology tab no longer claims trade secrets, and the export tab
  no longer says "institutional-grade".
- Every command in the README Quickstart runs as written (Python 3.11+, install, key, launch).
- If Decision 1 = A: export a memo and confirm no `%` allocation band and no BUY/SELL/AVOID.

Acceptance criteria:

- Suite prints `OK`, count ≥ 169 plus the new Phase 7 tests.
- `AppTest` prints `EXCEPTIONS: 0`.
- `README.md` contains no banned claim from Task 8.1.
- `docs/PRIVACY.md`, `docs/LIMITATIONS.md`, `docs/LEGAL_DECISIONS.md` and
  `docs/history/README.md` exist.
- Every file in `docs/history/` except its README starts with the banner.
- Every remaining `*.md` pair is content-distinct.
- README's Python floor matches `pyproject.toml` (`>=3.11`).
- The model block matches `analyzer.SUPPORTED_MODELS` exactly.
- Ledger files byte-identical.

## Final report — required format

1. **Phase 6 gate:** the nine failures, what each one was, and how each was resolved. For the two
   shield tests, quote the old assertion and explain why it encoded a falsehood.
2. **Decisions table:** decision, chosen option, provisional or confirmed, and who decided.
3. **README claim diff:** each removed claim, quoted, with the replacement — a table, not a
   summary.
4. **Docs triage:** file, action (kept / moved to history / rewritten / deleted), and the reason.
5. **De-advisory changes:** every string and field removed, and the test assertions that changed.
6. **Verification output pasted verbatim:** `Ran N tests` / `OK`, `EXCEPTIONS: N`, `shasum -c`,
   the test-def count, and the model-block grep.
7. **Behaviour changes users will notice** — e.g. no allocation band, no BUY/AVOID stance, honest
   "not evaluated" wording.
8. **Found but out of scope** — including anything in the docs you could not verify.

Do not claim the README is "accurate" without listing the specific claims you removed. Do not
describe the tool as compliant with any regulation. State what it is, what it is not, and who
decided.

===END PROMPT===
