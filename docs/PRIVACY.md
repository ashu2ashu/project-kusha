# Privacy & Data Handling Notice

Project KUSHA is a local research screening application. This document details all network transmissions, local artifacts, credentials, and data lifecycles.

## 1. What Leaves Your Machine
- **Uploaded Filing PDFs:** Sent directly to Google servers via the Gemini Files API for multimodal token ingestion.
- **Analysis Prompts:** Financial summary extracts, company ticker, and sector names are sent to Google via Gemini API generateContent endpoints.
- **Web-Search Grounding Queries:** Contextual company verification queries are dispatched to Google Search via Gemini grounding.
- **Market & Financial Data:** Stock ticker queries and financial statement requests are sent over HTTPS to Yahoo Finance endpoints.
- **Statutory Filing Archives:** Corporate filing lookup queries and PDF download requests are sent to BSE public archives (`bseindia.com`).

No data is transmitted to any other party or telemetry collector.

## 2. What Stays Local
All persistent artifacts remain strictly on your local disk:
- `.cache/evaluations/*.json`: Ephemeral full analysis payloads stored in unencrypted plaintext JSON.
- `.cache/feedback/*.json`: Free-text user feedback, ratings, and analyst correction notes.
- `improvement_ledger.json`: Autonomous self-improvement and audit ledger history.
- `kusha.log` (optional): Diagnostic logs written only if `KUSHA_LOG_FILE` environment variable is explicitly set.

## 3. Retention & Data Lifecycles
- **Local Cache:** Evaluation cache entries expire after 24 hours (TTL). Expired entries older than 4× TTL are automatically deleted from `.cache/evaluations/` during routine maintenance.
- **Feedback & Ledger:** Persisted indefinitely until manually deleted.
- **Google Data Retention:** Subject to Google Gemini API terms of service. Google's free-tier API terms permit model training on submitted data, which differs from paid tier agreements. Do not submit confidential or non-public filings without reviewing current Google API terms.

## 4. API Key Handling
- In the Streamlit UI, the `GEMINI_API_KEY` is held transiently in session memory and cleared upon session close.
- When configured via `.env`, the key is stored in plaintext on disk under file permissions of your user account.
- Diagnostic logs strictly redact API keys, passwords, and sensitive financial inputs.
- The key is transmitted exclusively in authorization headers to Google Gemini endpoints.

## 5. No Telemetry or Usage Tracking
Streamlit usage statistics are permanently disabled via `.streamlit/config.toml` (`gatherUsageStats = false`). Project KUSHA includes zero analytics SDKs, third-party trackers, or crash reporting aggregators.

## 6. Single-User Workstation Assumption
Project KUSHA lacks multi-tenant access control, encrypted session boundaries, and user isolation. Anyone with access to the host machine or local port can inspect cached evaluations and session data. Do not host this app as a shared or public service. The source is public but the tool is not hosted; no user data is published.

## 7. How to Delete Your Data
To purge all cached evaluations, feedback, and logs, execute from the repository root:
```bash
rm -rf .cache/evaluations/* .cache/feedback/*
rm -f kusha.log
```
