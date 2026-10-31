# Permanent Data-Truth Monitoring

Project KUSHA implements an automated monitoring system to catch silent drift, schema changes, and provider degradation before they pollute financial research.

## 1. What is Monitored
- **Offline Truth (Deterministic):** SHA-256 input fingerprint match, golden fixture output stability across 5 corporate archetypes and all 8 forensic checks, reference dataset staleness, and Gemini model watchlist synchronization.
- **Online Sources (Probes):** Yahoo Finance live quote telemetry (RELIANCE, TCS, HDFCBANK), BSE public exchange annual report discovery endpoints, Google Gemini model availability in API Studio, and evaluation cache purge hygiene.
- **Dependency Invariants:** Weekly scheduled matrix test execution under Python 3.11 and 3.12 to detect upstream package regressions.

## 2. What is Not Monitored
- **Content Accuracy:** Unaudited or restated vendor financials that remain numerically valid.
- **Field Mappings:** Upstream structural reclassifications that continue to return numbers.
- **LLM Output Quality:** Subjective prompt synthesis or qualitative memo writing drift.
- **Regulatory Standing:** Changes in SEBI statutory advisories or external legal compliance.
- **Untested UI Regressions:** Visual presentation changes outside automated unit tests.

## 3. Severity & Incident Response Matrix

| Signature | Severity | Meaning | What to Check First | Remediation |
|---|---|---|---|---|
| `fixture-drift` | `severity:drift` | Golden fixture output changed with unchanged fingerprint | Diff between baseline output and engine checks | Fix engine bug or update baseline if intentional |
| `stale-baseline` | `severity:warning` | Input constants or fixtures changed | Changed inputs printed in monitor log | Run `--update-baseline` with documented reason |
| `source-unavailable` | `severity:source` | Yahoo or BSE endpoints failed after 3 retries | Yahoo Finance symbol changes or BSE archive downtime | Verify network endpoints or update fetcher URL regex |
| `model-unavailable` | `severity:source` | A supported Gemini model was retired by Google | Gemini API release notes & Google AI Studio | Update `SUPPORTED_MODELS` and model watchlist |
| `dependency-drift` | `severity:drift` | Upstream package release broke unit tests | Failing assertion in weekly matrix test log | Pin dependency in `requirements.txt` |
| `stale-dataset` | `severity:warning` | Nifty reference dataset exceeds 900-day threshold | Statement period vs current calendar date | Ingest updated FY financial statements |

## 4. Baseline Update Procedure
When forensic rules or fixtures intentionally change:
1. Make code or fixture modifications in your local workspace.
2. Confirm the complete test suite passes: `python -m unittest discover -s tests`.
3. Update baseline with a specific reason:
   ```bash
   python tools/monitor.py --update-baseline --reason "Add explicit DSO provision check"
   ```
4. Review the generated diff in `monitoring/baseline.json`.
5. Commit the updated baseline alongside code changes. CI will strictly refuse auto-updating baselines.

## 5. Free-Tier Execution & GitHub Actions Caveat
- **Resource Budget:** 4 jobs/day running ~2 minutes each, plus weekly 2-minute matrix runs, totaling ~260 minutes/month. Well within GitHub's 2,000 free monthly minutes for private repositories (unlimited for public repositories).
- **The 60-Day Inactivity Rule:** GitHub automatically suspends scheduled workflows after 60 days of repository inactivity. If the schedule stops triggering, re-enable it manually from the GitHub Actions tab.

## 6. How to Run Locally

```bash
# Deterministic offline validation (no network required):
python tools/monitor.py --check --offline

# Full online source connectivity verification (requires network):
python tools/monitor.py --check --online

# Update baseline after reviewed code changes:
python tools/monitor.py --update-baseline --reason "<detailed explanation>"

# Emit structured JSON payload:
python tools/monitor.py --check --offline --json
```
