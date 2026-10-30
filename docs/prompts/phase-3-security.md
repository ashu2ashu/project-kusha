# Phase 3 — Security & Deployment

Copy everything between the markers into Antigravity, with the repository open at root.

---

===BEGIN PROMPT===

# TASK: Phase 3 — "Security & Deployment" remediation of Project KUSHA

## Context

Phase 1 made the app stop fabricating results. Phase 2 fixed the data underneath them.
Phase 3 makes the app **safe to run**.

Current state: a Streamlit app with **no authentication**, a **network-reachable default
bind**, **no cap on Gemini API spend**, and a large HTML-rendering surface fed partly by
untrusted LLM output (which itself is influenced by user-uploaded PDFs).

## Non-negotiable constraints

- **Zero cost.** No paid auth provider, no paid WAF, no paid secret manager, no paid hosting.
- **No new third-party dependencies.** stdlib only: `hmac`, `secrets`, `html`, `re`, `os`,
  `time`, `functools`, `logging`. `streamlit` is already present.
- **Tests use stdlib `unittest` only.**
- **Do not refactor architecture.** No module splits, no renames, no new frameworks.
- **Do not break the existing UI.** This phase changes plumbing, not layout.
- **Do not add a login database.** There is no user store and there will not be one.

## Threat model — write this down before you start

State it explicitly in your final report, then fix accordingly:

1. **Untrusted input:** the uploaded PDF, and every string the Gemini model returns.
   A malicious PDF can contain prompt-injection text that makes the model emit HTML,
   fake citations, or markdown headings.
2. **Untrusted network:** anyone who can reach port 8501.
3. **Trusted:** the repository code and the operator running it locally.

Everything below follows from those three.

---

## Task 0 — The app is reachable from the network by default

**File:** `.streamlit/config.toml`

Currently:

```toml
[server]
port = 8501
headless = true
```

With `headless = true` and no `server.address`, Streamlit binds to all interfaces
(`0.0.0.0`). On a laptop on a café or office network, anyone can open the app, read
analyses, and spend the operator's Gemini quota.

Required:

1. Add `address = "127.0.0.1"` under `[server]` so the default is local-only.
2. Add a comment explaining how an operator deliberately exposes it:
   `streamlit run app.py --server.address 0.0.0.0` **and only behind a proxy with auth**.
3. Set `enableCORS = false` **only if** you keep the localhost bind; leave it `true`
   otherwise. Document whichever choice you make in the comment. Default recommendation:
   keep `enableCORS = true` and `enableXsrfProtection = true`, bind to localhost.
4. Add a startup guard in `app.py`: if the process detects a non-loopback bind and no
   password is configured (Task 1), show a red banner at the top of the page:
   "This app is network-reachable with no authentication. Anyone on this network can use
   it and consume your API quota." Do not block startup — warn loudly.

**Acceptance:** `streamlit run app.py` on a machine with a LAN IP does not accept
connections from another host.

## Task 1 — No authentication, and no way to add one safely

There is no auth anywhere in `app.py`. For local-only use that is acceptable. For any
exposed deployment it is not. Since we cannot add a user database, implement a single
operator password gate that is **off by default**.

Required:

1. Read an optional password from the environment **or** `st.secrets`:
   - env var `KUSHA_ACCESS_PASSWORD`
   - fallback `st.secrets["KUSHA_ACCESS_PASSWORD"]` (wrap in try/except — secrets.toml may
     not exist)
2. If the value is unset or empty: **no gate**, and (per Task 0) warn only when the bind is
   non-loopback.
3. If it is set: render a password form before any other UI. Compare with
   `hmac.compare_digest` — never `==`. Store the authenticated flag in
   `st.session_state["kusha_authenticated"]`.
4. On failure, show a generic message ("Incorrect password"). Do not reveal length or
   whether the variable is configured.
5. Add a "Lock session" button in the sidebar that clears the flag.
6. Do **not** store the password in the repo, in logs, or in `st.session_state` in plain
   text. Store only the boolean.

**Acceptance:** with `KUSHA_ACCESS_PASSWORD` unset, the app renders exactly as before.
With it set, no analysis UI renders until the correct password is entered, and a wrong
password never grants access.

## Task 2 — No cap on API spend

Every analysis consumes Gemini quota. There is currently no limit on how many times a user
(or a misbehaving client) can trigger one. The free tier will simply start returning 429.

Required:

1. Add a per-session budget in `app.py`:
   - `st.session_state["kusha_runs"]` counter.
   - Constant `MAX_RUNS_PER_SESSION = 25` (make it read an env override
     `KUSHA_MAX_RUNS` if present, defaulting to 25).
   - When the budget is exhausted, disable the run button and show: "Session analysis
     budget reached (N of N). Reload to start a new session." Do not silently reuse cache
     to fake a result.
2. Add a minimum interval between runs: ignore a run request within 10 seconds of the
   previous one, with the message "Please wait — an analysis just completed."
3. Add a concurrency guard so a double-click cannot launch two analyses.
   `st.session_state["kusha_running"] = True` around the call, cleared in `finally`.
4. In `analyzer.py`, handle HTTP 429 explicitly in the existing model retry loop:
   - detect `429`, `resource_exhausted`, `quota` in the error text (partly present at
     lines ~843-844 for the search call — extend it to the analysis call)
   - stop retrying other models immediately on a project-wide quota error, and raise a
     clear `RuntimeError("Gemini quota exhausted. Try again later or reduce usage.")`
   - never fall back to a cached or stale result and present it as fresh.
5. Log each run at `INFO` with the model used and elapsed time. No API key, no prompt
   text, no company financials in the log.

**Acceptance:** a test can set the budget to 1, run once, and the second attempt is
rejected with the budget message.

## Task 3 — Uploaded PDFs are unbounded

**File:** `app.py` (the `st.file_uploader` around line 2152), `analyzer.py`.

Current behaviour: magic-byte check for `%PDF-` (good), temp file cleaned in `finally`
(good), but **no size limit**. Streamlit's default upload cap is 200 MB; the bytes are
written to temp disk and uploaded to Gemini.

Required:

1. Reject uploads over `MAX_PDF_MB = 40` with a clear message before doing any work.
2. Reject a file that is not `%PDF-` **before** it reaches `analyzer.py`, and say so
   plainly ("Not a valid PDF").
3. In `app.py`, always `uploaded_file.getvalue()` once into a local variable; do not call
   `read()` repeatedly.
4. Confirm the temp file is still removed on every path, including exceptions. Add a test
   that monkeypatches `client.files.upload` to raise and asserts no `*.pdf` remains in the
   temp directory afterwards.

## Task 4 — Systematic HTML escaping audit

There are **37** `unsafe_allow_html=True` and **47** `st.html(` call sites in `app.py`.
Some model-derived fields are already escaped (pillar `justification`, citation URLs), but
there has been no systematic pass.

The attack path: a malicious PDF contains injected instructions → the model returns a
string containing `<img src=x onerror=...>` → that string is interpolated into an HTML
f-string → it executes in the operator's browser.

Required:

1. Add one central helper near the top of `app.py`:

   ```python
   def esc(value):
       """Escape any value for safe HTML interpolation. None becomes an empty string."""
       return html.escape(str(value if value is not None else ""), quote=True)
   ```

2. Walk **every** `st.html(...)` and `st.markdown(..., unsafe_allow_html=True)` call site
   in `app.py`. For each interpolated value, decide its provenance:
   - constant / literal → no change
   - numeric formatted with `:.1f` → no change
   - **anything from `res`, `live`, `financial_data`, `forensic_report`, `sentinel_audit`,
     or any model output → wrap in `esc()`**
3. Pay special attention to: `verdict`, `final_call`, `pio_reason`, `guardrail_evidence`
   items, `evidence_gaps`, pillar `justification` and `name`, penalty `reason` and
   `penalty_name`, forensic check `detail`/`metric`/`benchmark`, sentinel `detail`,
   `business_summary`, `about_summary`, source `title`, and any date/period string.
4. Do not escape values that are already escaped — double-escaping will render `&amp;`
   visibly. Grep for existing `html.escape(` and leave those alone.

**Acceptance:** a test constructs an analysis dict whose every string field contains
`<script>alert(1)</script>` and `<img src=x onerror=alert(1)>`, renders the full app via
`AppTest`, and asserts neither string appears unescaped in any rendered element.

## Task 5 — Links need scheme validation, not just escaping

`html.escape("javascript:alert(1)")` still yields a working `javascript:` URL inside an
`href`. Escaping does not neutralise a scheme.

Some call sites already filter with `str(u).startswith(("https://", "http://"))` (good).
Make that universal.

Required:

1. Add one helper:

   ```python
   def safe_url(url):
       """Return the URL only if it is an absolute http(s) URL, else ''."""
       u = str(url or "").strip()
       return u if u.lower().startswith(("https://", "http://")) else ""
   ```

2. Use it at **every** place a model-supplied URL becomes an `href`. If `safe_url` returns
   empty, render the source name as plain text with no anchor.
3. Add `rel="noopener noreferrer"` to every `target="_blank"` anchor (most already have it
   — verify all).

## Task 6 — The exported markdown memo can be forged by the model

**File:** `app.py`, the markdown export builder around lines 5039-5100.

Model output is interpolated directly into a downloadable markdown document:

```python
md_text = f"""# StockSage | Institutional Research Memo: {res.get('company_name')}
...
## Mandatory Guardrail Tag
**{res.get('guardrail_tag')}**
{chr(10).join(['- ' + ev for ev in res.get('guardrail_evidence', [])])}
```

A model response containing `\n## VERDICT: 100/100 — STRONG BUY\n` becomes a real section
of the exported memo. This is not XSS, it is **document forgery**: the exported file looks
like the app produced that section.

Required:

1. Neutralise structural markdown in every model-supplied string before interpolation:
   strip or escape leading `#`, `>`, `-`, `*`, `|`, backticks, and any `\n`.
2. Collapse to a single line and cap length (e.g. 600 chars) with an ellipsis.
3. Prefix the exported document with a generated-provenance block:
   company, ticker, model requested, model used, whether a fallback occurred, retrieval
   timestamp, pipeline version, and a line stating the document is model-generated and
   not audited.
4. Escape table-breaking characters in any value placed inside a markdown table.

**Acceptance:** feed a `guardrail_evidence` entry containing
`"\n## VERDICT: 100/100 — STRONG BUY\n"` and assert the exported text contains no line
beginning with `## VERDICT`.

## Task 7 — Cached analyses have no integrity check

**File:** `evaluation_cache.py`.

`load_cached_evaluation` reads a JSON file from the cache directory and replays it as a
genuine prior analysis. Anything that can write to that directory — another process, a
sync client, a malicious archive — can plant a "PRISTINE / 100" result that the app then
presents as its own output.

Required:

1. Add a `schema_version` and a `provenance` block to every cached payload:
   `created_at`, `pipeline_version`, `model_requested`, `model_used`,
   `model_fallback_used`, `data_source_note`.
2. On load, reject (and delete) a payload that is missing `schema_version`, has an
   unknown version, or is missing `provenance`. Log the rejection at `WARNING`.
3. On load, validate the payload shape before returning it: it must contain `pillars`,
   `final_score`, and `forensic_report`. Reject anything else rather than passing it to the
   renderer.
4. When a cached result is displayed, label it as cached with its `created_at` date.
   Never present a cache hit as a fresh analysis.
5. Do not change the cache key or TTL scheme — that is Phase 4.

**Acceptance:** writing a cache file without `provenance` causes it to be ignored and
deleted, and the app does a live run instead.

## Task 8 — Secrets: what to do and what NOT to do

Verified current state — do not redo this work:

- `.env` **is** gitignored (`.gitignore` lines 1-14 cover `.env`, `*.env`,
  `.streamlit/secrets.toml`, `*.key`, `client_secrets*.json`).
- Only `.env.example` is tracked, and it contains the placeholder
  `your_gemini_api_key_here`.
- A git history scan found **no** committed Google API key.
- `tests/test_self_improvement_engine.py:60` contains the string
  `AIzaSyD983274982374982374923847923847`. This is a **deliberate dummy** used to test
  redaction, and line 71 asserts it gets replaced with `[REDACTED_KEY]`. **Do not remove
  it, do not "rotate" it, do not treat it as a leak.**
- The API key is entered through a `type="password"` widget (app.py ~855) and held in
  session state. That is acceptable.

Required, small:

1. Confirm `st.session_state` never renders the key anywhere — grep for any `st.write`,
   `st.markdown`, `st.code`, `st.text` or `st.caption` that receives the key variable.
2. Ensure no exception handler stringifies the client object or the key into a message or
   a log line. Check `except` blocks in `analyzer.py`.
3. Add one line to README: the key is used for the operator's own quota and is never
   persisted; on a shared machine, use a dedicated key.
4. Tell the user, in your report, to rotate the key **if** it was ever pasted into a chat,
   a screenshot, or a public repo. That is an operator action, not a code change.

## Task 9 — Document the trust boundary

**File:** `README.md` — add a short `## Security & Trust Boundary` section (8-12 lines
maximum, factual, no marketing):

- The app runs locally and is not multi-user.
- Uploaded PDFs and all model output are treated as untrusted.
- PDFs are uploaded to Google's Gemini API — they leave the machine.
- Analyses are cached in plain JSON on local disk.
- Data comes from Yahoo Finance (delayed, unaudited) and Gemini web grounding.
- The app is not a registered investment adviser and outputs are not advice.

Do not write longer than that. Do not make security claims the code does not implement —
that exact failure was the subject of Phase 1.

## Task 10 — Regression tests

Create `tests/test_phase3_security.py` (stdlib `unittest`). Minimum:

1. `esc()` escapes `<script>`, quotes, and returns `""` for `None`.
2. `safe_url()` returns `""` for `javascript:alert(1)`, `data:text/html,...`, `//evil.com`,
   and relative paths; returns the URL for `https://example.com`.
3. A rendered pillar row containing `<img src=x onerror=alert(1)>` in `justification`
   does not contain the raw substring.
4. Markdown export with an injected `\n## VERDICT` contains no such heading.
5. Cache payload without `provenance` is rejected and removed from disk.
6. Cache payload with an unknown `schema_version` is rejected.
7. Run budget: after `MAX_RUNS_PER_SESSION` runs, the next attempt is refused.
8. `KUSHA_ACCESS_PASSWORD` set → no analysis UI before authentication (assert on
   `st.session_state`, not on visual layout).
9. `KUSHA_ACCESS_PASSWORD` unset → no gate is rendered.
10. Oversized PDF (`MAX_PDF_MB + 1`) is rejected before any Gemini call — assert the client
    was never constructed.

## Verification — all of this must succeed

```bash
shasum improvement_ledger.json IMPROVEMENT_LEDGER.md > /tmp/ledger_before.sha

python -m py_compile app.py analyzer.py evaluation_cache.py

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

Additional manual check:

```bash
# Terminal 1
streamlit run app.py
# Terminal 2 — from another machine on the LAN
# curl to <your-lan-ip>:8501 must FAIL (connection refused / timeout)
```

Acceptance criteria:

- `unittest` prints `OK`.
- `AppTest` prints `EXCEPTIONS: 0`.
- `shasum -c` prints OK for both ledger files.
- The LAN curl fails.
- With neither `KUSHA_ACCESS_PASSWORD` nor `KUSHA_MAX_RUNS` set, the app behaves exactly as
  before this phase.

## Final report — required format

1. **Threat model** as you actually applied it.
2. **Files changed**, one line each explaining why.
3. **Escaping audit table** — how many `st.html` / `unsafe_allow_html` call sites you
   reviewed, how many had unescaped model-derived values, and the count you fixed. This
   number must be concrete, not "several".
4. **Verification output pasted verbatim** — `Ran N tests` / `OK`, `EXCEPTIONS: N`, the
   `shasum -c` lines, and the result of the LAN connectivity check.
5. **Known remaining risks** — what is still unsafe and why (e.g. "no CSRF on the password
   form beyond Streamlit's XSRF token", "cache directory permissions are inherited from
   umask").
6. **Found but out of scope** — other issues deliberately left for later phases.

Do not claim the app is "secure". Claim exactly what you fixed and what remains.

===END PROMPT===
