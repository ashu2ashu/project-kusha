# Phase 6 — Architecture & Packaging

Copy everything between the markers into Antigravity, with the repository open at root.

**Read Task 0 first.** This is the only phase that moves working code. The tree currently has
~1,840 uncommitted insertions and no rollback point. Commit before touching anything.

---

===BEGIN PROMPT===

# TASK: Phase 6 — "Architecture & Packaging" remediation of Project KUSHA

## Context

Phases 1-5 made the product truthful, its data labelled, its runtime safe, its cache correct,
and its tests real: 169 tests pass, `AppTest` renders with 0 exceptions, CI exists.

Structurally, nothing changed. `app.py` is 5,437 lines, and it is not one program — it is two:

- **~2,476 lines of function definitions**, of which **14 functions (~1,780 lines) have exactly
  zero Streamlit calls**. They build HTML strings and Plotly figures. They are pure.
- **~2,900 lines of top-level script** that executes on import: a 606-line inline CSS
  `st.markdown`, a 413-line input block, and the results renderer split across a 217-line and a
  **1,236-line top-level `if` block**.

That second half is why 169 tests can pass while the main analysis flow has **zero** test
coverage. Importing `app` runs the UI; nothing in the suite drives it end to end.

## What this phase does and does not do

**Does:**

1. Move the pure render code and the stylesheet out of `app.py`, with re-exports so every
   existing test import keeps working.
2. Delete the second, contradictory implementation of the forensic checks inside the UI.
3. Establish single sources of truth for pillars and score bands.
4. Make packaging honest: dependencies declared, bounded, and complete.
5. Install ratchets so `app.py` cannot silently regrow.

**Does not:** split the 1,236-line main flow into modules.

That is deliberate. A blind split of untested top-level script produces an app that is broken at
runtime and green in CI, because no test executes that code. A full MVC split is a separate
phase that must first add `AppTest`-driven coverage of the main flow. Say so in the report
instead of pretending this phase finished the job.

## Non-negotiable constraints

- **Zero cost.** No paid tooling, no paid coverage, no paid packaging service.
- **No new runtime dependencies.** `numpy` is already imported by `financial_trends.py` and
  `nifty_peer_comparison.py` and is currently undeclared — declaring it is a fix, not an
  addition. Nothing else new.
- **No behaviour change except where explicitly required by Task 3** (fraud-shield statuses).
- **Do not change scoring formulas, pillar weights, prompt wording, or cache semantics.**
- **`app.py` must keep exporting every name the tests import.**
  Currently: `MAX_PDF_MB`, `build_filing_ingestion_notice_html`, `esc`, `get_kusha_access_password`,
  `nav_alias_map`, `render_forensic_fraud_shield_html`,
  `render_research_provenance_and_evidence_card`, `render_traffic_light_and_eli15_html`,
  `render_valuation_compass_html`, `safe_url`, `sanitize_memo_field`, `workspace_options`.
- **No module outside `tests/` may import `app`.** `app.py` executes the UI on import; importing
  it from a library module creates a cycle and makes unit tests launch Streamlit.
- **Tests: stdlib `unittest` only.**

---

## Task 0 — Baseline, branch, and rollback point

The working tree has 18 modified files and multiple untracked files, none committed since
`e75a403`. You are about to move ~2,400 lines. Without a baseline you cannot tell a refactor
mistake from a pre-existing bug.

Required:

```bash
git switch -c phase-6-architecture
git add -A
git commit -m "wip: phases 1-5 remediation (pre-architecture baseline)"
git rev-parse HEAD            # record this
```

Then record the baseline, verbatim, in your report:

```bash
wc -l app.py
python -m unittest discover -s tests 2>&1 | tail -3
python - <<'PY'
from streamlit.testing.v1 import AppTest
at = AppTest.from_file("app.py", default_timeout=120).run()
print("EXCEPTIONS:", len(at.exception))
PY
```

**Gate:** tests `OK`, `EXCEPTIONS: 0`. If either fails, stop and report — do not refactor on a
red baseline. Rollback at any point is `git reset --hard <recorded hash>`.

## Task 1 — Extract the stylesheet (606 lines, `app.py:212-817`)

The block is `st.markdown("""<style> … </style>""", unsafe_allow_html=True)`. It is a plain
string: no f-string, no interpolation.

Required:

1. Create `assets/kusha.css` containing exactly the CSS between `<style>` and `</style>`.
2. In `app.py`, replace the literal with:
   ```python
   from pathlib import Path
   _CSS_PATH = Path(__file__).parent / "assets" / "kusha.css"
   st.markdown(f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
   ```
   Use `f"<style>{css}</style>"` or concatenation — the CSS contains `{` braces, so do **not**
   format the CSS string itself.
3. **Byte-identical requirement:** extract the old CSS from git (`git show HEAD:app.py`), strip
   the wrapper, and `diff` it against `assets/kusha.css`. The diff must be empty. A single lost
   selector changes the UI silently and no test will catch it.

**Acceptance:** empty diff; `AppTest` still `EXCEPTIONS: 0`; `wc -l app.py` dropped by ~605.

## Task 2 — Extract the pure render functions (14 functions, ~1,780 lines)

Create `kusha_render.py` and move these functions **verbatim**, with no logic edits:

Line ranges below are from the **baseline commit (before Task 1)**. After the CSS extraction
they shift by ~605 lines — locate functions by name, not by line number.

| Line range (baseline) | Function | Streamlit calls | Session state |
|---|---|---|---|
| 99-101 | `esc` | 0 | no |
| 104-107 | `safe_url` | 0 | no |
| 110-123 | `sanitize_memo_field` | 0 | no |
| 142-194 | `build_filing_ingestion_notice_html` | 0 | no |
| 1203-1296 | `render_dalal_street_metric_cards_html` | 0 | no |
| 1299-1395 | `build_ticker_chart` | 0 | no |
| 2444-2488 | `build_radar_chart` | 0 | no |
| 2491-2522 | `parse_dcf_estimate` | 0 | no |
| 2524-2968 | `render_live_analysis_timer_html` | 0 | no |
| 2970-3112 | `render_research_provenance_and_evidence_card` | 0 | no |
| 3114-3336 | `render_traffic_light_and_eli15_html` | 0 | no |
| 3338-3666 | `render_forensic_fraud_shield_html` | 0 | no |
| 3668-3820 | `render_valuation_compass_html` | 0 | no |
| 3822-3962 | `render_graphical_forensic_architecture_html` | 0 | no |

Rules:

1. **`kusha_render.py` must not import `streamlit`.** It imports stdlib (`html`, `re`, `json`,
   `math`, `datetime` as needed) plus `plotly.graph_objects`. Add a test that enforces this
   (Task 8).
2. `parse_dcf_estimate` is called by `render_traffic_light_and_eli15_html` and
   `render_valuation_compass_html`. Both move together, so no cross-module cycle — but keep
   `parse_dcf_estimate` defined before its consumers for readability.
3. In `app.py`, import them back explicitly:
   ```python
   from kusha_render import (
       esc, safe_url, sanitize_memo_field, build_filing_ingestion_notice_html,
       render_dalal_street_metric_cards_html, build_ticker_chart, build_radar_chart,
       parse_dcf_estimate, render_live_analysis_timer_html,
       render_research_provenance_and_evidence_card, render_traffic_light_and_eli15_html,
       render_forensic_fraud_shield_html, render_valuation_compass_html,
       render_graphical_forensic_architecture_html, PILLAR_METADATA,
   )
   ```
   This re-export is mandatory: `from app import esc` must keep working for existing tests.
   `PILLAR_METADATA` is consumed in the results block (`app.py:4897` in the baseline), so it
   must be imported back too — missing it is a `NameError` at render time, not at import.
4. Delete the original definitions from `app.py`. Do not leave duplicates — a duplicate that
   shadows the import is the classic failure mode here.
5. `PILLAR_METADATA` and `_PILLAR_STYLE` (currently `app.py:2419-2441`) also move to
   `kusha_render.py` (see Task 6 for the required keying change).

### Proof that nothing changed — golden master

Before moving anything, capture the rendered output of the moved functions on the five golden
fixtures, and compare after. HTML strings are deterministic, so this catches every accidental
edit that tests do not cover.

```python
# run BEFORE the move, from repo root; writes /tmp/render_before.json
import hashlib, json
import tests.fixtures_golden as g
from app import (esc, safe_url, sanitize_memo_field,
                 render_dalal_street_metric_cards_html,
                 render_forensic_fraud_shield_html,
                 render_valuation_compass_html,
                 render_traffic_light_and_eli15_html,
                 render_research_provenance_and_evidence_card,
                 render_graphical_forensic_architecture_html,
                 parse_dcf_estimate)

def h(x):
    return hashlib.sha256(str(x).encode()).hexdigest()[:16]

out = {}
for name in ["CLEAN_LARGECAP", "LOSS_MAKER", "HIGH_PLEDGE", "CHANNEL_STUFFING", "EMPTY"]:
    fx = getattr(g, name)
    res = fx.get("result", {})
    live = fx.get("live", {})
    out[f"{name}:shield"] = h(render_forensic_fraud_shield_html(res, live))
    out[f"{name}:compass"] = h(render_valuation_compass_html(res, live))
    out[f"{name}:traffic"] = h(render_traffic_light_and_eli15_html(res, live, "T", "S"))
    out[f"{name}:provenance"] = h(render_research_provenance_and_evidence_card(res, live, "T", "T", "S"))
    out[f"{name}:dalal"] = h(render_dalal_street_metric_cards_html(live))
out["arch"] = h(render_graphical_forensic_architecture_html())
out["esc"] = h(esc('<script>alert(1)</script>'))
out["safe_url"] = h(safe_url("javascript:alert(1)"))
out["memo"] = h(sanitize_memo_field("x" * 900))
out["dcf"] = h(parse_dcf_estimate("INR 1,200 - 1,450"))
json.dump(out, open("/tmp/render_before.json", "w"), indent=2, sort_keys=True)
print("captured", len(out))
```

After the move, run the same script with `import app` replaced by `import kusha_render` and diff
`/tmp/render_before.json` against `/tmp/render_after.json`. **Every hash must match.** If a
fixture lacks `result`/`live` keys, adapt the adapter — do not delete the comparison.

## Task 3 — Kill the second implementation of the forensic checks

`render_forensic_fraud_shield_html` is 329 lines with **42 status assignments**, and it
re-derives verdicts that `forensic_risk_engine` already computed. Worse, it uses different
rules under the same check names:

| Check | Engine rule | Shield rule |
|---|---|---|
| `FOR_01` cash conversion | cumulative CFO/PAT, benchmark **≥ 80%**, status from a 3-way band | PASS at **≥ 90%**, independent band |
| `FOR_02` receivable velocity | receivables growth **vs revenue growth** (spread ≤ +8%) | **DSO ≤ 90 days** (or ≤110 with low overdue) — a different metric entirely |
| `FOR_06` solvency | D/E ≤ 0.3 PASS via rating/lvg logic | local `de_pass`, own cut-offs |
| `FOR_08` auditor | explicit opinion string, else `INSUFFICIENT_DATA` | keyword-scans `appendix_a_forensic_evidence` for "clean"/"adverse" and labels PASS/ALERT |

So a company can display "DSO PASS" under a card titled "Revenue vs Receivables Velocity" while
the engine's actual check is `CRITICAL` — or the UI claims a clean audit for a company the
engine never evaluated.

Required:

1. Split the function into:
   - `shield_rows(res, live_data, financial_data=None, forensic_report=None) -> list[dict]` —
     pure, returns `{"title", "status", "badge", "evidence", "check_id"}` rows.
   - `render_forensic_fraud_shield_html(...)` — thin HTML wrapper around `shield_rows`.
   Put both in `kusha_render.py`.
2. **Status mapping must be a single function:**
   ```python
   def _display_status(engine_status: str) -> str:
       return {
           "PASS": "PASS",
           "MONITOR": "MONITOR",
           "CRITICAL": "ALERT",
           "INSUFFICIENT_DATA": "NOT EVALUATED",
       }.get(engine_status, "NOT EVALUATED")
   ```
   Each row's status comes from `forensic_report["checks"]` by `check_id`. **No local PASS.**
   Numeric display values (DSO, conversion %, D/E, pledge %) may still be computed for the
   label text, but they must never decide the status.
3. If the engine did not emit a check at all, the row is `NOT EVALUATED` with
   evidence "This check was not performed on the available data." Do not substitute MONITOR —
   MONITOR asserts "we looked and found a concern".
4. Remove the auditor keyword-matching branch. `FOR_08` is the only source of truth. When it is
   `INSUFFICIENT_DATA`, the row says so.
5. `FOR_02`'s badge becomes the engine's `metric` (spread), not DSO. If you want DSO visible,
   add it as secondary evidence text clearly labelled "DSO (not the engine metric)" — or omit
   it. Do not present it as the check.

**Expected and acceptable behaviour change:** some companies will lose a displayed `PASS` or
`MONITOR` and show `NOT EVALUATED`, because the engine never evaluated that check. That is the
fix. Produce a table in the report listing, per golden fixture and per check, the old displayed
status and the new one.

**Acceptance test:** for every golden fixture and every row with a `check_id`, the displayed
status equals `_display_status(engine_check_status)`. No row may be `PASS` unless the engine
check is `PASS`.

## Task 4 — Single source of truth for score bands

`analyzer.py:247-270` defines the real bands (90 / 85 / 75 / 60 / 50) and the verdict strings.
`app.py` re-implements cut-offs twice: ELI15 at `>= 75` / `>= 60` (`app.py:3263`) and gauge
colours at `>= 80` / `>= 60` (`app.py:4341`). Those numbers disagree with the analyzer and with
each other: a 78 scores "HIGH FINANCIAL INTEGRITY" in one card and blue (not green) in the other.

Required:

1. Add to `analyzer.py` (or a new `kusha_scoring.py` if you prefer — one module, not both):
   ```python
   SCORE_BANDS = [
       (90.0, "OCGC", "≥90", "10–15%", "#059669"),
       (85.0, "PCGC", "85–89", "5–10%", "#059669"),
       (75.0, "QTC",  "75–84", "0–5%",   "#2563EB"),
       (60.0, "VTC",  "60–74", "0–3%",   "#2563EB"),
       (50.0, "STC",  "50–59", "0%",     "#D97706"),
       (0.0,  "FRAGILE", "<50", "0%",    "#DC2626"),
   ]

   def verdict_band(score) -> dict:
       """Returns {code, label, color, position_sizing} for a 0-100 score."""
   ```
   Keep the existing verdict strings byte-identical — `tests/test_financial_invariants_suite.py`
   asserts `"OCGC (≥90)"`, `"PCGC (85–89)"` and `"FRAGILE"`.
2. `analyzer.py` builds its `verdict` from `verdict_band()`.
3. `app.py`'s ELI15 badge and gauge colour take `color` from the same function. Delete the
   independent 75/60 and 80/60 cut-offs.
4. PIO override stays where it is: `final_score` is already clamped to 49 when PIO triggers, so
   it lands in FRAGILE. Do not duplicate that rule in the UI.
5. Golden fixtures must be unaffected in score; only colours/badges may shift for scores in
   the 75-80 and 60-75 windows. Report any such shift explicitly.

## Task 5 — Single source of truth for pillars

`app.py:2419-2441` pairs pillar styles with `analyzer.CANONICAL_PILLARS` **by list index**. Add a
pillar to `CANONICAL_PILLARS` and either the styles misalign silently (reorder) or the dict
comprehension raises `IndexError` (append). Separately, `prompt_template.py` hardcodes all eight
pillar names, so the prompt and the scoring schema can drift without anything failing.

Required:

1. In `kusha_render.py`, key `PILLAR_STYLE` by **pillar id**, not index:
   ```python
   PILLAR_STYLE = {
       "1": {...}, "2": {...}, ...   # one entry per canonical id
   }
   ```
   Build `PILLAR_METADATA` from `analyzer.CANONICAL_PILLARS` and **raise at import** if any
   canonical id has no style or a style has no canonical pillar:
   ```python
   missing = [p["id"] for p in analyzer.CANONICAL_PILLARS if str(p["id"]) not in PILLAR_STYLE]
   if missing:
       raise RuntimeError(f"PILLAR_STYLE missing ids: {missing}")
   ```
2. In `prompt_template.py`, generate the pillar list from `CANONICAL_PILLARS` instead of
   restating it, or — if the prompt text is too entangled to template safely — add an import-time
   assertion that every canonical name appears exactly once and that no other `"N. <name>"`
   pillar line exists. State which approach you took and why.
3. Test (Task 8): `set(PILLAR_METADATA) == {str(p["id"]) for p in CANONICAL_PILLARS}`, and the
   prompt contains every canonical pillar name.

## Task 6 — Packaging: `pyproject.toml`, bounds, and the missing `numpy`

Current state:

- No `pyproject.toml`.
- `requirements.txt` uses bare lower bounds: `streamlit>=1.35.0`, `google-genai>=1.0.0`,
  `yfinance>=0.2.40`, `pandas>=2.0.0`, `plotly>=5.22.0`, etc. `google-genai` and `yfinance` both
  ship breaking changes across minors; an unpinned install is a future outage.
- **`numpy` is imported directly** by `financial_trends.py:9` and `nifty_peer_comparison.py:10`
  but is not declared. It works only because `pandas` happens to pull it in.
- `streamlit>=1.35.0` is false advertising: the app uses `st.iframe` (4 sites) and
  `width="stretch"` (19 sites). The locally verified version is **1.66.1**; 1.35 does not have
  these APIs, so a user who installs the declared floor gets a broken app.

Required:

1. Create `pyproject.toml`:
   ```toml
   [project]
   name = "project-kusha"
   version = "0.1.0"
   requires-python = ">=3.11"
   dynamic = ["dependencies"]

   [tool.setuptools]
   py-modules = ["analyzer", "app", "cli", "data_integrity_agent", "evaluation_cache",
                 "financial_trends", "forensic_risk_engine", "kusha_logging", "kusha_render",
                 "nifty_peer_comparison", "nifty_universe", "prompt_template",
                 "self_improvement_engine", "annual_report_fetcher"]

   [tool.setuptools.dynamic]
   dependencies = {file = ["requirements.txt"]}
   ```
   Single-sourcing dependencies from `requirements.txt` avoids the classic two-files-drift bug.
   Do not duplicate the dependency list.
2. Update `requirements.txt`:
   - Add `numpy>=1.26,<3.0`.
   - Raise the Streamlit floor to a version you **verified**, not guessed. Create a scratch venv,
     `pip install streamlit==<candidate>`, and run the AppTest smoke check. Start from
     `1.66.1` (known good); if you want a lower floor, prove it with that check. Record the
     command and result in your report.
   - Add upper bounds at the next major for every dependency (`<2.0` for streamlit/google-genai,
     `<1.0` for yfinance where the project pins a 0.x line, `<3.0` for pandas/numpy, etc.).
     Do not invent versions — use the installed, tested versions as the lower bound.
3. Delete the duplicate root `FORENSIC_FRAMEWORK_ANALYSIS.md`. It is byte-identical to
   `docs/FORENSIC_FRAMEWORK_ANALYSIS.md` (208 lines each, verified). Keep the `docs/` copy.
4. `app.py:23` calls `load_dotenv(override=True)`. That makes a checked-in `.env` beat real
   deployment environment variables. Change to `override=False` and note it.
5. `app.py:25-40` calls `importlib.reload(...)` on eight modules at import time. Under
   Streamlit this re-executes on **every rerun**, defeats module caching, and makes imports
   non-deterministic. Gate it:
   ```python
   if os.getenv("KUSHA_DEV_RELOAD") == "1":
       for _m in (...): importlib.reload(_m)
   ```
   Default off. Report the startup-time difference if you measure it.
6. Keep CI installing `requirements.txt -r requirements-dev.txt`. If you switch CI to
   `pip install -e .`, prove it works in the same job; otherwise leave CI alone.

## Task 7 — Document the architecture decision

Add `docs/ARCHITECTURE.md` (max 60 lines):

- The module map after this phase, one line per module.
- Which modules are pure (no Streamlit) and therefore unit-testable without a runtime.
- The explicit statement that the main analysis flow is **still** top-level script in `app.py`,
  and why it was not split in this phase.
- The follow-up precondition for splitting it: `AppTest`-driven coverage of the input → analyze
  → render path, happy path plus one failure path, before any code moves.

Do not describe an architecture the code does not have.

## Task 8 — Ratchets in `tests/test_architecture.py`

These fail CI if the monolith regrows or the duplication returns. All stdlib `unittest`.

1. **Size ratchet:** `app.py` ≤ **3,400 lines**. (Baseline 5,437 minus ~2,400 moved.) Pick the
   exact number after the move, rounded up — but state the final count and do not set the
   threshold above it.
2. **Purity:** `kusha_render.py` source contains no `import streamlit` and no AST call whose
   value is the name `st`.
3. **No duplicate definitions:** none of the 14 moved function names is defined in `app.py`.
4. **No library imports `app`:** scan every top-level `*.py` except `app.py`; assert no
   `import app` / `from app import`.
5. **Re-export compatibility:** `from app import` succeeds for all 12 names listed in the
   constraints, and each is the same object as in its home module (e.g.
   `app.esc is kusha_render.esc`).
6. **Dependencies declared:** parse the top-level imports of every module, map the third-party
   ones to distributions (`streamlit, plotly, google.genai→google-genai, pypdf, dotenv→python-dotenv,
   yfinance, bs4→beautifulsoup4, requests, pandas, numpy`), and assert each appears in
   `requirements.txt`. This is the check that would have caught the missing `numpy`.
7. **No duplicate docs:** no two tracked `*.md` files have identical content.
8. **Pillar integrity:** `PILLAR_METADATA` keys equal canonical ids; every canonical pillar name
   appears in `prompt_template.py`.
9. **Score bands:** `verdict_band(95)["code"] == "OCGC"`, `verdict_band(88)["code"] == "PCGC"`,
   `verdict_band(76)["code"] == "QTC"`, `verdict_band(45)["code"] == "FRAGILE"`, and the app's
   ELI15/gauge colour for a score equals `verdict_band(score)["color"]`.
10. **Shield truth:** for each golden fixture, no shield row is `PASS` unless the corresponding
    engine check is `PASS`; rows with no engine check are `NOT EVALUATED`.

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
for e in at.exception[:5]:
    print(e.value)
PY

shasum -c /tmp/ledger_before.sha

python -c "from app import esc, safe_url, sanitize_memo_field, MAX_PDF_MB, nav_alias_map, workspace_options, build_filing_ingestion_notice_html, render_forensic_fraud_shield_html, render_valuation_compass_html, render_traffic_light_and_eli15_html, render_research_provenance_and_evidence_card; print('re-exports OK')"

python -c "import kusha_render, ast; src=open('kusha_render.py').read(); assert 'streamlit' not in src, 'streamlit leaked'; print('pure module OK')"

wc -l app.py kusha_render.py

diff <(git show HEAD:app.py | sed -n '/^<style>$/,/^<\/style>$/p' | sed '1d;$d') assets/kusha.css && echo "CSS identical"
```

Additional checks:

- `/tmp/render_before.json` vs `/tmp/render_after.json` — all hashes equal for Tasks 1-2.
- `.cache/evaluations` unchanged in behaviour: cache still hits on repeat analysis with the same
  inputs (Phase 4 gate).
- `git diff --stat` shows moved code, not rewritten code: deletions in `app.py` ≈ insertions in
  `kusha_render.py`.

Acceptance criteria:

- `unittest` prints `OK`, count is **≥ 169** (additions expected from Task 8, no deletions).
- `AppTest` prints `EXCEPTIONS: 0`.
- `app.py` ≤ 3,400 lines; `kusha_render.py` exists and contains the 14 functions.
- Every re-export prints OK.
- CSS `diff` is empty.
- Render golden-master hashes identical for Tasks 1-2.
- Ledger files byte-identical (`shasum -c` OK).
- `FORENSIC_FRAMEWORK_ANALYSIS.md` no longer exists at repo root.
- `numpy` present in `requirements.txt`; every dependency has an upper bound.
- `tests/test_architecture.py` exists and its 10 checks pass.

## Final report — required format

1. **Baseline vs final table:** `app.py` lines, `kusha_render.py` lines, test count, AppTest
   exceptions, before and after.
2. **Moved functions table:** function, old line range, new module, lands in import list (yes/no).
3. **Golden-master proof:** the `diff` result for the 19 render hashes (or `all equal`).
4. **Shield status delta table:** per fixture, per check, old displayed status → new displayed
   status, and why. This is the only intentional behaviour change; do not bury it.
5. **Packaging:** final `requirements.txt` with bounds, the verified Streamlit floor and the
   command used to verify it, and the `pyproject.toml` dependency-sourcing approach.
6. **Verification output pasted verbatim:** `Ran N tests` / `OK`, `EXCEPTIONS: N`,
   `shasum -c`, `wc -l`, the re-export line, the CSS diff, and the `diff --stat` summary.
7. **Behaviour changes users will notice** — shield statuses, any colour shift from Task 4,
   `.env` precedence change, dev reload now opt-in.
8. **Found but out of scope** — in particular: the main flow is still untested script, with the
   concrete precondition for fixing it.

Do not claim the app was "modularised". Two modules were extracted; the main flow was not
touched. Say exactly what moved and what did not.

===END PROMPT===
