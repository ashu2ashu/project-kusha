# Phase 1 — Truth Layer

Copy everything between the `===BEGIN PROMPT===` and `===END PROMPT===` markers into
Antigravity as a single message, with the repository open at its root.

---

===BEGIN PROMPT===

# TASK: Phase 1 — "Truth Layer" remediation of Project KUSHA

## Your role

You are fixing a Streamlit + Python financial-analysis app (Project KUSHA / StockSage).
It scores Indian listed companies on 8 pillars, using Google Gemini to extract scores
and deterministic Python to clamp and sum them.

The app currently **fabricates favourable results when data is missing**, and displays
claims that the code does not implement. Your job is Phase 1 only: make it impossible
for the app to invent a clean result, and make every user-facing claim true.

This is a financial tool. A fabricated "PRISTINE" verdict is a real-world harm, not a
cosmetic bug. Treat it that way.

## Non-negotiable constraints

- **Zero cost.** No paid services, APIs, data vendors, or hosting.
- **No new third-party dependencies.** stdlib only: `json`, `re`, `html`, `datetime`,
  `unittest`, `typing`. Do not add pytest, do not add a linter, do not add coverage tools.
- **Tests use stdlib `unittest` only.** Run them with `python -m unittest discover -s tests`.
- **Do not refactor architecture.** Do not split `app.py`, do not rename modules, do not
  reorganise files. Later phases handle that.
- **Do not change scoring weights**, pillar allocations, or the prompt text in
  `prompt_template.py`.
- **Do not delete data sources or network calls.**
- **Do not fix anything not listed here.** If you find another falsehood, list it in your
  final report under "Found but out of scope" and leave it alone.
- **Preserve the existing visual design.** Only text, labels and logic change.

## Critical operational warning — read before running tests

Running the test suite **writes to the real audit ledger**
(`tests/test_self_improvement_engine.py` appends to `IMPROVEMENT_LEDGER.md` and
`improvement_ledger.json`). Before any test run:

```bash
cp improvement_ledger.json /tmp/ledger_backup.json
cp IMPROVEMENT_LEDGER.md /tmp/ledger_backup.md
```

After the run, restore them:

```bash
cp /tmp/ledger_backup.json improvement_ledger.json
cp /tmp/ledger_backup.md IMPROVEMENT_LEDGER.md
```

Never commit ledger changes. They are the audit trail, not test output.

## The invariant you are enforcing

> A check that was not evaluated must never report PASS.
> A score must never be issued from missing data.
> Absence of evidence is not evidence of quality.

---

## Task 1 — No fabricated PASS in the forensic engine

**File:** `forensic_risk_engine.py`
**Function:** `ForensicRiskEngine.audit_company_forensics`

Checks 2 through 8 currently fall through to `status = "PASS"` with invented detail
text when their input series is absent. Two examples of what it emits from nothing:

- "Audited by recognized statutory auditor with an unqualified (clean) opinion.
  Zero mid-term auditor resignations under SEBI LODR Regulation 30 Annexure A."
- `"rating": "CONSERVATIVE POSTURE"` and a default of `"CRISIL AAA / Stable"`.

Required:

1. Every check must return exactly one of: `PASS`, `MONITOR`, `CRITICAL`,
   `INSUFFICIENT_DATA`.
2. When the required input series is missing, empty, or too short to compute the
   metric: return `INSUFFICIENT_DATA`, with a factual detail line naming what was
   unavailable and stating the check was not evaluated.
3. **Auditor check** (`FOR_08_AUDITOR_GOVERNANCE`): evaluate only when
   `live["auditor_opinion"]` is a non-empty string.
   - Contains any of `qualified`, `adverse`, `disclaimer of opinion`, `resign`
     → `CRITICAL`, +18.0 penalty, add a critical red flag.
   - Otherwise → `PASS`.
   - Not supplied → `INSUFFICIENT_DATA`, `metric = "N/A"`.
   - Delete all invented default text.
4. **Credit rating**: when no curated rating exists, do not produce `PASS`.
   Use `INSUFFICIENT_DATA`, `rating = "NOT EVALUATED"`. When a rating does exist,
   include its disclosure date from the record (`rationale_date`). Never invent
   `CRISIL AAA`.
5. **Promoter pledge** (`FOR_07_PROMOTER_PLEDGE`): parse the numeric percentage with a
   regex. `"0.00%"` and `"0%"` are zero → `PASS`. Any value > 0 → `CRITICAL`,
   +20.0 penalty, red flag. Missing disclosure → `INSUFFICIENT_DATA`.
   The current code uses `"%" in value`, which (a) flags a genuine `"0.00%"` as
   pledged and (b) treats a missing disclosure as clean. Both are wrong.
6. Any `metric` string that formats a float must be guarded:
   `f"{x:.1f}% of PPE" if x is not None else "N/A"`. The missing-data branch now
   yields `None`, and `f"{None:.1f}"` raises `TypeError`.

## Task 2 — Withhold the FQI when evidence coverage is low

**Same function.** Replace:

```python
fqi_score = max(round(100.0 - forensic_penalties, 1), 10.0)
```

Required:

- `evaluated` = checks whose status is `PASS`, `MONITOR` or `CRITICAL`.
- `insufficient` = checks whose status is `INSUFFICIENT_DATA`.
- `coverage = round(len(evaluated) / len(checks), 2)`.
- `score_issued = len(evaluated) > 0 and coverage >= 0.75`.
- If `not score_issued`: `fqi_score = None`, badge `"INSUFFICIENT DATA"`,
  a neutral grey colour scheme, and verdict text containing the sentence
  "Absence of evidence is not evidence of cleanliness."
- If `critical_red_flags` exist, keep the `HIGH RISK` badge, but still withhold the
  numeric score when `score_issued` is False.
- Append a coverage note to every verdict description, e.g.
  `"Evidence coverage 6/8 checks evaluated; 2 not evaluated due to missing data."`
- Add these keys to the returned report dict: `evaluated_count`, `insufficient_count`,
  `coverage`, `score_issued`.

## Task 3 — The renderer must not default to 100

**File:** `forensic_risk_engine.py`
**Function:** `render_forensic_dossier_html`

1. `fqi = report.get("fqi_score", 100.0)` → `report.get("fqi_score")`.
   Display `"N/A"` when it is not a number. Never render `100.0` as a default.
2. Delete the hardcoded governance tile reading `Clean Audit • 0.0% Pledged` with
   subtitle "Zero auditor resignations, zero NCLT actions, unencumbered promoter
   shares." Derive the tile from the actual `FOR_07` / `FOR_08` check status and
   metric. If either is not `PASS`, the tile must say so and must not use green.
3. Rename the heading "Credit Rating Agency Surveillance" to
   "External Credit Rating Disclosure".
4. Escape every interpolated value with `html.escape` (import `html as _html`, add a
   small `_esc()` helper). Fields to escape: `title`, `category`, `detail`, `metric`,
   `benchmark`, `rating`, `agency`, `outlook`, `headroom`, `verdict_badge`,
   `verdict_desc`, governance headline and sub-line.

## Task 4 — Integrity score must scale with evaluated checks

**File:** `data_integrity_agent.py`
**Function:** `DataIntegritySentinel.audit_and_certify`

CHK_03 (accrual) currently has a branch that marks a loss-making company as `PASSED`
with the text "Base period PAT is negative or zero; cash conversion ratio not
stressed." A loss-maker must never earn a passing mark here.

Required:

- `PAT < 0` and `CFO < 0` → `FAILED`, +2.5 penalty, flag `"Loss-Making Period (PAT < 0)"`.
- `PAT < 0` and `CFO >= 0` → `PASSED`, +1.0 penalty, same flag, and a detail line
  explaining that CFO/PAT is not a meaningful ratio in a loss period.
- `PAT == 0` → `INSUFFICIENT_DATA`.

Score:

```python
pass_ratio = passed_count / evaluated_count if evaluated_count else 0.0
integrity_score = round(max(0.0, min(100.0, 100.0 * pass_ratio - penalties)), 1)
```

Not `100 - penalties`. Two passing checks out of six must not read as 100/100.

## Task 5 — Guardrail must be an enum, not a substring match

The tag `"GOV-CREDIBLE 🟢"` contains the substring `"RED"`. Every `"RED" in tag`
check therefore forces a clean company into a critical / AVOID state.

In `analyzer.py`, add:

```python
GUARDRAIL_CLEAN = "CLEAN"
GUARDRAIL_ALERT = "ALERT"
GUARDRAIL_RED = "RED"


def guardrail_level(tag):
    """Map a display guardrail tag to a strict level enum.

    Must be used instead of `"RED" in tag`, which falsely matched
    "GOV-CREDIBLE 🟢".
    """
    normalized = str(tag or "").strip().upper()
    if normalized.startswith("GOV-RED"):
        return GUARDRAIL_RED
    if normalized.startswith("PROM-ALERT"):
        return GUARDRAIL_ALERT
    return GUARDRAIL_CLEAN
```

Then **find every substring test in the repository**. Do not assume you know them all:

```bash
grep -rn '"RED" in\|"ALERT" in\|"GOV-RED" in\|"PROM-ALERT" in' --include='*.py' .
```

Known call sites in `app.py` (line numbers approximate — re-locate them):
provenance HUD (~2856), management-integrity card (~2964 and ~2971), stance decision
(~4256), guardrail banner (~4377), promoter-alert banner (~4388).

Also `forensic_risk_engine.py` has `elif v_badge in ("MONITOR",) or "ALERT" in v_badge
or "WATCH" in v_badge` applied to an internal enum. Replace with an explicit equality
or membership test.

Replace every one with `analyzer.guardrail_level(x) == analyzer.GUARDRAIL_RED` (or
`_ALERT`). Leave zero substring comparisons behind.

Acceptance: a company tagged `GOV-CREDIBLE 🟢` with `final_score >= 55` must not be
given `pio_triggered = True`, must not be capped at 49.0, and must not receive
`stance = "AVOID"`.

## Task 6 — Remove false claims from the UI

**File:** `app.py`. Replace the text; keep the surrounding layout.

| False text | Replace with |
|---|---|
| "10 governance and financial pillars" | "8 governance and financial pillars" |
| "3-Stage DCF Intrinsic Value" / "DCF Safety Corridors" | "Relative Valuation" / "P/E · EV/EBITDA · P/B multiples" |
| "ENCRYPTION &amp; TAMPER GUARD ENFORCED" | "DETERMINISTIC POST-PROCESSING ONLY" |
| "MATHEMATICAL DETERMINISM VERIFIED ✔" | "DETERMINISTIC POST-PROCESSING APPLIED ✔" |
| "compiled on the backend under institutional IP protection" | Describe what the code does: Gemini extracts pillar scores; Python clamps, caps and sums them; the model output itself is not reproducible; no encryption or tamper-proofing is applied. |
| "Screener.in 10-Yr Audited Statements" | "delayed Yahoo Finance statements (~4 years, unaudited)" |
| "10-Yr Audited Financials" | "~4-Yr Third-Party Financials" |
| "Canonical 10-year audited P&L, Balance Sheet, and Cash Flow datasets" | "Third-party, unaudited P&L, Balance Sheet and Cash Flow data (~4 years)." |
| Credit-rating data-source card claiming "Official credit rating disclosures" for all companies | Note that it is a manually curated set for a small number of large caps only, shown with its disclosure date. |

## Task 7 — `PILLAR_METADATA` must not drift from the canonical pillars

**File:** `app.py`. `PILLAR_METADATA` hardcodes labels that contradict
`analyzer.CANONICAL_PILLARS`:

- Pillar 3 is labelled "Solvency"; canonical name is "Risk, ESG & Fragility".
- Pillar 8 is labelled "Capital Allocation"; canonical name is "Insider & Minority
  Shareholder Risk".

Rebuild the mapping from `analyzer.CANONICAL_PILLARS`, keeping only the visual styling
(icon, chip label, colours) in a local list. Store the canonical `name` in each entry so
a chip can never mislabel a score.

## Task 8 — Delete the invented fair value

**File:** `app.py` **Function:** `render_valuation_compass_html`

Delete this block entirely:

```python
if not dcf_mid and cmp:
    dcf_mid = round(cmp * 1.06, 0)
    dcf_low = round(dcf_mid * 0.95, 0)
    dcf_high = round(dcf_mid * 1.05, 0)
```

It manufactures a "target price" by adding 6% to the current price, then reports
"Trading at discount to DCF Intrinsic Value" against a number derived from the same
price. If there is no estimate, return `""` and render no compass.

Relabel nearby strings: "DCF Intrinsic Value" → "model fair-value estimate",
"▲ DCF Fair" → "▲ Est. Fair", "FAIR VALUE (DCF)" → "FAIR VALUE (MODEL ESTIMATE)",
"DCF Fair Value Zone" → "Model Fair Value Zone". Add a caption under the heading
stating the band is a Gemini-generated estimate, not a computed DCF, and should be
treated as an opinion.

## Task 9 — The fraud shield must not fabricate either

**File:** `app.py` **Function:** `render_forensic_fraud_shield_html`

This is a second, independent reimplementation of the forensic checks, with its own
fabricated fallbacks that emit: `CLEAN AUDIT`, `0.0% PLEDGED`, `HEALTHY DSO`,
`SOLVENT`, `CLEAN RECORD`, plus the sentence "Promoter shareholding is 100%
unencumbered. Official filings confirm zero promoter shares are pledged as loan
collateral." — all with no supporting data.

Required:

1. Each of the six items reads its result from `forensic_rep["checks"]` by check id
   (`FOR_01_CASH_CONVERSION`, `FOR_02_RECEIVABLE_VELOCITY`, `FOR_07_PROMOTER_PLEDGE`,
   `FOR_08_AUDITOR_GOVERNANCE`, plus the debt/equity and regulatory items).
2. When a check is absent or `INSUFFICIENT_DATA`: `status = "MONITOR"`,
   `badge = "NOT VERIFIED"`, and evidence text stating it was not verified — and that
   absence of a disclosure is not evidence of cleanliness.
3. `"ALL CLEAR"` appears only when all six items genuinely `PASS`.
4. The summary badge must distinguish the three states:
   `"{passed}/{total} PASSED · {n} NOT VERIFIED"` when anything is unverified.
5. Escape `title`, `badge` and `evidence` with `html.escape`.

## Task 10 — Honest provenance

**File:** `analyzer.py` **Function:** `analyze_document_with_gemini`

1. The model loop iterates `models_sequence` and silently falls back. Track the model
   that actually answered: record the winning `m_name` for the research call and for
   the analysis call.
2. Add these keys to the returned dict:
   - `model_requested` — the model the user selected
   - `model_used` — the model that actually answered (may be a fallback)
   - `model_fallback_used` — bool
   - `research_model_used`
   - `retrieved_at` — a real UTC ISO timestamp
   - `pipeline_version` — `ANALYSIS_PIPELINE_VERSION`
   - `data_source_note` — one honest sentence naming Yahoo Finance as delayed,
     unaudited third-party aggregation and Gemini grounding as the web evidence source
3. Add the same provenance keys to the `_research_gap_result` path.

**File:** `app.py` — `retrieval_time = res.get("retrieved_at") or
datetime.now().strftime("%d %b %Y")` must become `or "Not recorded"`.
Never default to today's date.

## Task 11 — Escape model output

**File:** `app.py`. These values originate from the LLM and are interpolated into HTML:

- `pio_reason`
- `receivable_subscore`
- the guardrail tag (in all three banner branches)
- each item of `guardrail_evidence`
- Appendix B calculation keys and values

Wrap each in `html.escape(str(value))`.

## Task 12 — Regression tests

Create `tests/test_phase1_truth_layer.py` using stdlib `unittest`. Minimum coverage:

1. Empty `financial_statements` + empty `live_market_data` → `fqi_score is None`,
   `score_issued is False`, all 8 checks `INSUFFICIENT_DATA`, badge != `"PRISTINE"`.
2. Renderer output contains `"N/A / 100"` and does not contain
   `"Clean Audit • 0.0% Pledged"`.
3. `"0.00%"` pledge → `PASS`. Missing pledge → `INSUFFICIENT_DATA`.
4. Injected `<script>alert(1)</script>` in a check `detail` is escaped in the HTML.
5. `guardrail_level("GOV-CREDIBLE 🟢") == GUARDRAIL_CLEAN`; reconciling a credible tag
   does not set `pio_triggered` and leaves `final_score >= 49.0`.
6. `"GOV-RED 🔴"` still triggers the override and caps the score at `<= 49.0`.
7. Negative PAT + negative CFO → CHK_03 `FAILED`, integrity score `< 100.0`.
8. `app.py` contains none of the forbidden claim strings from Task 6.
9. **No substring guardrail test survives** in `app.py`, `analyzer.py`,
   `forensic_risk_engine.py`, `data_integrity_agent.py`. Implement with `tokenize` so
   docstrings and comments are stripped first — otherwise the explanatory docstring in
   `guardrail_level` trips the check itself.
10. `dcf_mid = round(cmp * 1.06, 0)` is absent from `app.py`.

**Update existing tests that assert the old fabricated behaviour.** At minimum:

- `tests/test_forensic_risk_engine.py` expects 8/8 passing checks including a
  fabricated auditor PASS. It must now expect 7 passed + 1 `INSUFFICIENT_DATA`.
- `tests/test_audit_remediation.py` asserts the old provenance string
  `"BSE India Statutory Annual Report"`.

List every test you changed and why the old assertion was wrong. Do not silently
weaken a test to make it pass.

## Verification — all of this must succeed

```bash
cp improvement_ledger.json /tmp/lb.json
cp IMPROVEMENT_LEDGER.md /tmp/lb.md

python -m py_compile app.py analyzer.py forensic_risk_engine.py data_integrity_agent.py

python -m unittest discover -s tests

python - <<'PY'
from streamlit.testing.v1 import AppTest
at = AppTest.from_file("app.py", default_timeout=120).run()
print("EXCEPTIONS:", len(at.exception))
for e in at.exception[:5]:
    print(e.value)
PY

cp /tmp/lb.json improvement_ledger.json
cp /tmp/lb.md IMPROVEMENT_LEDGER.md
```

Acceptance criteria:

- `unittest` prints `OK`.
- `AppTest` prints `EXCEPTIONS: 0`.
- The ledger files are byte-identical to before the run (`git status` shows no change).
- `python -m py_compile` succeeds for all four modules.

## Final report — required format

1. **Files changed**, one line each explaining why.
2. **Tests changed**, and the reason the old assertion was wrong.
3. **Verification output pasted verbatim** — the `Ran N tests` / `OK` line and the
   `EXCEPTIONS:` line. Do not claim success without pasting it.
4. **Found but out of scope** — other falsehoods or bugs you noticed and deliberately
   did not touch.
5. **Could not do** — anything blocked, and why.

Do not say "done" unless every acceptance criterion above passed.

===END PROMPT===

## Notes for the human running this

- **Before you start:** the working tree already contains a Phase 1 implementation.
  If you want Antigravity to build it fresh, revert first:

  ```bash
  git checkout -- app.py analyzer.py forensic_risk_engine.py data_integrity_agent.py \
      tests/test_audit_remediation.py tests/test_forensic_risk_engine.py
  rm -f tests/test_phase1_truth_layer.py
  ```

  If you want to keep it, `git diff` first, then let Antigravity review and finish it.

- **After it runs:** `git diff --stat` should show roughly 420–450 changed lines across
  `app.py`, `analyzer.py`, `forensic_risk_engine.py` and `data_integrity_agent.py`.

- **Red flag:** if the agent reports fewer than ~100 tests, it did not add the
  regression suite. If it reports `EXCEPTIONS` above 0, it broke the Streamlit render.
