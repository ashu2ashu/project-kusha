#!/usr/bin/env python3
"""
tools/alert_issue.py
GitHub Issues alert channel for Project KUSHA Data-Truth Monitor (Phase 8).
Uses stdlib urllib.request only. Strictly redacts API keys and sensitive financial texts.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

APIZA_REGEX = re.compile(r"AIza[0-9A-Za-z_-]{20,}")

SIGNATURE_SEVERITY_MAP = {
    "fixture-drift": "drift",
    "dependency-drift": "drift",
    "yahoo-unavailable": "source",
    "bse-no-filings": "source",
    "model-unavailable": "source",
    "source-unavailable": "source",
    "stale-dataset": "warning",
    "stale-baseline": "warning",
}


def redact_secrets_and_content(text: str) -> str:
    """Redact API keys, passwords, and sensitive inputs."""
    cleaned = APIZA_REGEX.sub("[REDACTED_API_KEY]", text)
    # Strip any accidental financial statements dump
    for forbidden in ["financial_statements", "balance_sheet", "cash_flow"]:
        if f'"{forbidden}"' in cleaned:
            cleaned = re.sub(rf'"{forbidden}":\s*\{{.*?\}}', f'"{forbidden}": "[REDACTED]"', cleaned)
    return cleaned


def build_issue_body(
    signature: str,
    monitor_data: Dict[str, Any],
    run_url: str,
) -> Tuple[str, str]:
    """Build one-line summary and formatted markdown body."""
    status = monitor_data.get("status", "DRIFT")
    fingerprint = str(monitor_data.get("fingerprint", ""))[:12]
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    findings = monitor_data.get("findings", [])
    offline_dtls = monitor_data.get("details", {}).get("offline", {})
    drift_items = offline_dtls.get("drift_items", [])

    if signature == "fixture-drift" and drift_items:
        summary = f"Fixture status drift detected across {len(drift_items)} check(s)."
        findings_md_lines = [
            "| Fixture | Check ID | Baseline Status | Current Status | Impact |",
            "|---|---|---|---|---|",
        ]
        for item in drift_items:
            findings_md_lines.append(
                f"| `{item.get('fixture')}` | `{item.get('check_id')}` | `{item.get('old')}` | `{item.get('new')}` | **{item.get('classification')}** |"
            )
        findings_md = "\n".join(findings_md_lines)
    elif findings:
        summary = f"Data truth finding: {findings[0]}"
        findings_md = "\n".join(f"- {f}" for f in findings)
    else:
        summary = f"Automated truth monitor status: {status}"
        findings_md = f"Status: `{status}`"

    body = (
        f"**What changed:** {summary}\n"
        f"**Detected:** {now_utc}\n"
        f"**Workflow run:** {run_url}\n"
        f"**Fingerprint:** `{fingerprint}`\n\n"
        f"**Findings:**\n"
        f"{findings_md}\n\n"
        f"**What to do:** see docs/MONITORING.md#{signature}\n"
    )
    return summary, redact_secrets_and_content(body)


def make_github_request(
    url: str,
    token: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Any]:
    """Execute authenticated GitHub REST API request using stdlib."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Project-KUSHA-Data-Truth-Monitor",
    }
    body_bytes = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body_bytes = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp_body = resp.read().decode("utf-8")
            parsed = json.loads(resp_body) if resp_body else {}
            return resp.status, parsed
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        return e.code, err_body
    except Exception as e:
        return 500, str(e)


def ensure_labels_exist(repo: str, token: str, labels: List[str]) -> None:
    """Idempotently ensure required labels exist."""
    base_url = f"https://api.github.com/repos/{repo}/labels"
    label_colors = {
        "data-truth": "0E8A16",
        "severity:drift": "B60205",
        "severity:source": "D93F0B",
        "severity:warning": "FBCA04",
    }
    for lbl in labels:
        status, _ = make_github_request(f"{base_url}/{lbl}", token, method="GET")
        if status == 404:
            color = label_colors.get(lbl, "64748B")
            make_github_request(
                base_url,
                token,
                method="POST",
                data={"name": lbl, "color": color, "description": "Automated data-truth monitor label"},
            )


def find_open_issue_by_title(repo: str, token: str, title: str) -> Optional[Dict[str, Any]]:
    """Search open issues with label data-truth for an exact title match."""
    url = f"https://api.github.com/repos/{repo}/issues?labels=data-truth&state=open&per_page=50"
    status, data = make_github_request(url, token, method="GET")
    if status == 200 and isinstance(data, list):
        for item in data:
            if item.get("title") == title:
                return item
    return None


def alert_or_comment(
    repo: str,
    token: str,
    signature: str,
    monitor_data: Dict[str, Any],
    run_url: str,
) -> int:
    """Create a new issue or comment on an existing open issue."""
    title = f"[data-truth] {signature}"
    summary, body = build_issue_body(signature, monitor_data, run_url)
    sev = SIGNATURE_SEVERITY_MAP.get(signature, "warning")
    labels = ["data-truth", f"severity:{sev}"]

    # 1. Search for existing open issue with exact title
    open_issue = find_open_issue_by_title(repo, token, title)
    if open_issue:
        issue_number = open_issue["number"]
        comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
        comment_body = (
            f"### Additional Occurrence Detected\n\n"
            f"**Detected:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"**Workflow run:** {run_url}\n\n"
            f"**Findings:**\n"
            f"{summary}\n"
        )
        status, resp = make_github_request(comment_url, token, method="POST", data={"body": comment_body})
        if status in {200, 201}:
            print(f"OK: Commented on existing open issue #{issue_number}: {title}")
            return 0
        else:
            print(f"WARN: Failed to post comment on #{issue_number}: HTTP {status} {resp}", file=sys.stderr)
            return 1

    # 2. Create new issue if none exists
    ensure_labels_exist(repo, token, labels)
    create_url = f"https://api.github.com/repos/{repo}/issues"
    status, resp = make_github_request(
        create_url,
        token,
        method="POST",
        data={"title": title, "body": body, "labels": labels},
    )
    if status in {200, 201}:
        issue_num = resp.get("number")
        print(f"OK: Created new GitHub issue #{issue_num}: {title}")
        return 0
    else:
        print(f"WARN: Failed to create issue {title}: HTTP {status} {resp}", file=sys.stderr)
        return 1


def handle_recovery(repo: str, token: str, signature: str, run_url: str) -> None:
    """Post recovery note on open source-unavailable issues."""
    sev = SIGNATURE_SEVERITY_MAP.get(signature, "")
    if sev != "source":
        # Never auto-close drift
        return
    title = f"[data-truth] {signature}"
    open_issue = find_open_issue_by_title(repo, token, title)
    if open_issue:
        issue_number = open_issue["number"]
        comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
        make_github_request(
            comment_url,
            token,
            method="POST",
            data={"body": f"### Source Recovery Observed\n\nRecovered at {run_url}."},
        )
        print(f"OK: Posted recovery comment on issue #{issue_number}")


def main() -> None:
    parser = argparse.ArgumentParser(description="GitHub Issue Alert Channel for Project KUSHA")
    parser.add_argument("--body-file", type=str, required=True, help="Path to JSON file output from monitor.py")
    parser.add_argument("--signature", type=str, required=True, help="Stable signature slug for alert deduplication")
    parser.add_argument("--recovery", action="store_true", help="Signal recovery if monitor output was OK")

    args = parser.parse_args()

    body_file = Path(args.body_file)
    if not body_file.exists():
        print(f"Error: body-file not found at {body_file}", file=sys.stderr)
        sys.exit(1)

    try:
        monitor_data = json.loads(body_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error reading JSON from {body_file}: {e}", file=sys.stderr)
        sys.exit(1)

    repo = os.environ.get("GITHUB_REPOSITORY", "ashu2ashu/project-kusha").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
    run_url = f"{server_url}/{repo}/actions/runs/{run_id}" if run_id != "local" else "local workstation"

    summary, body = build_issue_body(args.signature, monitor_data, run_url)

    if not token:
        # Local run fallback: print issue payload and exit 0
        print("INFO: GITHUB_TOKEN not set; local dry-run mode.")
        print(f"Issue Title: [data-truth] {args.signature}")
        print("Issue Body:")
        print("---")
        print(body)
        print("---")
        sys.exit(0)

    if args.recovery or monitor_data.get("status") == "OK":
        handle_recovery(repo, token, args.signature, run_url)
        sys.exit(0)

    code = alert_or_comment(repo, token, args.signature, monitor_data, run_url)
    sys.exit(code)


if __name__ == "__main__":
    main()
