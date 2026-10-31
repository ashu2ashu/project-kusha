#!/usr/bin/env python3
"""
tools/monitor.py
Permanent data-truth monitor for Project KUSHA (Phase 8).
Detects silent drift, unannounced schema shifts, stale reference datasets,
and third-party provider unavailability without writing to the repo in CI.

Exit codes:
  0: OK (warnings may be printed)
  1: DRIFT — status, score, or badge changed with unchanged fingerprint, or model watchlist mismatch
  2: STALE BASELINE — input fingerprint changed; human must update baseline with reason
  3: SOURCE UNAVAILABLE — online probe failed after retries
  4: MISCONFIGURED — missing baseline, unreadable fixture, invalid threshold, update refused
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import analyzer
from forensic_risk_engine import ForensicRiskEngine
import nifty_peer_comparison


def compute_fingerprint(repo_root: Path) -> Tuple[str, Dict[str, Any]]:
    """Compute sha256 fingerprint of the inputs that define forensic truth."""
    fixtures_path = repo_root / "tests" / "fixtures_golden.py"
    if not fixtures_path.exists():
        raise FileNotFoundError(f"Missing fixtures file: {fixtures_path}")
    fixtures_sha256 = hashlib.sha256(fixtures_path.read_bytes()).hexdigest()

    pipeline_version = str(getattr(analyzer, "ANALYSIS_PIPELINE_VERSION", ""))
    engine_version = str(getattr(ForensicRiskEngine, "VERSION", ""))
    dataset_date = str(getattr(nifty_peer_comparison, "NIFTY_50_DATASET_DATE", ""))
    pillars = [str(p["id"]) for p in getattr(analyzer, "CANONICAL_PILLARS", [])]
    pillar_ids_str = ",".join(pillars)

    raw_str = f"{pipeline_version}|{engine_version}|{dataset_date}|{fixtures_sha256}|{pillar_ids_str}"
    fingerprint = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    inputs = {
        "pipeline_version": pipeline_version,
        "engine_version": engine_version,
        "dataset_date": dataset_date,
        "fixtures_sha256": fixtures_sha256,
        "pillars": pillars,
    }
    return fingerprint, inputs


def audit_golden_fixtures() -> Dict[str, Any]:
    """Run ForensicRiskEngine on each golden fixture and record outputs."""
    import tests.fixtures_golden as g

    fixture_names = ["CLEAN_LARGECAP", "LOSS_MAKER", "HIGH_PLEDGE", "CHANNEL_STUFFING", "EMPTY"]
    out = {}
    for name in fixture_names:
        if not hasattr(g, name):
            raise AttributeError(f"Fixture {name} not found in tests/fixtures_golden.py")
        fx = getattr(g, name)
        rep = ForensicRiskEngine.audit_company_forensics(
            ticker_symbol=fx["ticker"],
            company_name=fx["company_name"],
            sector=fx["sector"],
            financial_statements=fx["financials"],
            live_market_data=fx["market_data"],
        )
        fqi = rep.get("fqi_score")
        if fqi is not None:
            fqi = round(float(fqi), 1)

        checks = {}
        for c in rep.get("checks", []):
            checks[c["id"]] = c["status"]

        out[name] = {
            "fqi_score": fqi,
            "verdict_badge": str(rep.get("verdict_badge", "INSUFFICIENT DATA")),
            "score_issued": bool(rep.get("score_issued", False)),
            "checks": checks,
        }
    return out


def generate_baseline_dict(repo_root: Path, reason: str) -> Dict[str, Any]:
    """Generate the baseline dictionary structure."""
    fp, inputs = compute_fingerprint(repo_root)
    fixtures_data = audit_golden_fixtures()
    return {
        "schema": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason.strip(),
        "fingerprint": fp,
        "inputs": inputs,
        "thresholds": {
            "peer_dataset_max_age_days": 900,
            "model_watchlist_max_age_days": 90,
            "market_data_max_age_hours": 48,
        },
        "fixtures": fixtures_data,
    }


def update_baseline(repo_root: Path, reason: Optional[str]) -> int:
    """Update monitoring/baseline.json with validation rules."""
    # Rule 1: Refuse in CI unless explicitly allowed
    if os.environ.get("GITHUB_ACTIONS") == "true" and os.environ.get("ALLOW_BASELINE_UPDATE") != "1":
        print("MISCONFIGURED: Baseline update refused inside GitHub Actions CI.", file=sys.stderr)
        return 4

    # Rule 2: Require a meaningful reason
    cleaned_reason = (reason or "").strip()
    if not cleaned_reason or cleaned_reason.lower() in {"update", "fix", "test", "baseline", "refresh"}:
        print("MISCONFIGURED: A specific --reason is required to update baseline (generic reasons rejected).", file=sys.stderr)
        return 4

    baseline_path = repo_root / "monitoring" / "baseline.json"
    baseline_path.parent.mkdir(parents=True, exist_ok=True)

    old_fp = None
    if baseline_path.exists():
        try:
            old_data = json.loads(baseline_path.read_text(encoding="utf-8"))
            old_fp = old_data.get("fingerprint")
        except Exception:
            pass

    new_data = generate_baseline_dict(repo_root, cleaned_reason)
    baseline_path.write_text(json.dumps(new_data, indent=2) + "\n", encoding="utf-8")

    print(f"OK: Baseline updated successfully in {baseline_path.relative_to(repo_root)}")
    print(f"  Reason: {cleaned_reason}")
    print(f"  Fingerprint: {new_data['fingerprint'][:16]}... (was {str(old_fp)[:16]}...)")
    print(f"  Fixtures recorded: {len(new_data['fixtures'])}")
    return 0


def run_offline_checks(repo_root: Path) -> Tuple[int, str, List[str], Dict[str, Any]]:
    """
    Run offline deterministic checks.
    Returns: (exit_code, status, findings, details)
    """
    baseline_path = repo_root / "monitoring" / "baseline.json"
    if not baseline_path.exists():
        return 4, "MISCONFIGURED", [f"Missing baseline file at {baseline_path}"], {}

    try:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    except Exception as e:
        return 4, "MISCONFIGURED", [f"Unreadable baseline file: {e}"], {}

    # 1. Fingerprint check
    curr_fp, curr_inputs = compute_fingerprint(repo_root)
    base_fp = baseline.get("fingerprint")
    base_inputs = baseline.get("inputs", {})

    if curr_fp != base_fp:
        mismatched_inputs = []
        for k in ["pipeline_version", "engine_version", "dataset_date", "fixtures_sha256", "pillars"]:
            if base_inputs.get(k) != curr_inputs.get(k):
                mismatched_inputs.append(f"{k} (baseline={base_inputs.get(k)!r}, current={curr_inputs.get(k)!r})")

        finding_msg = f"Fingerprint mismatch (base={str(base_fp)[:12]}, curr={curr_fp[:12]}). Changed inputs: {', '.join(mismatched_inputs)}"
        return 2, "STALE_BASELINE", [finding_msg], {"changed_inputs": mismatched_inputs}

    # 2. Fixture drift check
    curr_fixtures = audit_golden_fixtures()
    base_fixtures = baseline.get("fixtures", {})
    drift_items = []

    for fx_name, b_fx in base_fixtures.items():
        c_fx = curr_fixtures.get(fx_name)
        if not c_fx:
            drift_items.append({
                "fixture": fx_name,
                "check_id": "ENTIRE_FIXTURE",
                "old": "PRESENT",
                "new": "MISSING",
                "classification": "DEGRADED",
            })
            continue

        if b_fx.get("score_issued") != c_fx.get("score_issued"):
            drift_items.append({
                "fixture": fx_name,
                "check_id": "SCORE_ISSUED",
                "old": str(b_fx.get("score_issued")),
                "new": str(c_fx.get("score_issued")),
                "classification": "CHANGED",
            })

        if b_fx.get("fqi_score") != c_fx.get("fqi_score"):
            drift_items.append({
                "fixture": fx_name,
                "check_id": "FQI_SCORE",
                "old": str(b_fx.get("fqi_score")),
                "new": str(c_fx.get("fqi_score")),
                "classification": "CHANGED",
            })

        if b_fx.get("verdict_badge") != c_fx.get("verdict_badge"):
            drift_items.append({
                "fixture": fx_name,
                "check_id": "VERDICT_BADGE",
                "old": str(b_fx.get("verdict_badge")),
                "new": str(c_fx.get("verdict_badge")),
                "classification": "CHANGED",
            })

        b_checks = b_fx.get("checks", {})
        c_checks = c_fx.get("checks", {})
        all_checks = sorted(set(b_checks.keys()) | set(c_checks.keys()))
        for cid in all_checks:
            old_st = b_checks.get(cid, "MISSING")
            new_st = c_checks.get(cid, "MISSING")
            if old_st != new_st:
                if old_st == "PASS" and new_st in {"INSUFFICIENT_DATA", "CRITICAL", "MONITOR"}:
                    cls_tag = "DEGRADED"
                elif old_st in {"INSUFFICIENT_DATA", "CRITICAL", "MONITOR"} and new_st == "PASS":
                    cls_tag = "RECOVERED"
                else:
                    cls_tag = "CHANGED"
                drift_items.append({
                    "fixture": fx_name,
                    "check_id": cid,
                    "old": old_st,
                    "new": new_st,
                    "classification": cls_tag,
                })

    findings = []
    exit_code = 0
    status = "OK"

    if drift_items:
        exit_code = 1
        status = "DRIFT"
        for d in drift_items:
            findings.append(f"DRIFT: {d['fixture']} {d['check_id']}: {d['old']} -> {d['new']} [{d['classification']}]")

    # 3. Dataset age check
    dataset_date_str = nifty_peer_comparison.NIFTY_50_DATASET_DATE
    try:
        ds_date = date.fromisoformat(dataset_date_str)
        ds_age_days = (date.today() - ds_date).days
        max_ds_days = baseline.get("thresholds", {}).get("peer_dataset_max_age_days", 900)
        if ds_age_days > max_ds_days:
            findings.append(f"WARN: Peer dataset is {ds_age_days} days old (statement date: {dataset_date_str}, threshold: {max_ds_days} days)")
        else:
            findings.append(f"OK: Peer dataset age {ds_age_days} days is within threshold ({max_ds_days} days)")
    except Exception as e:
        findings.append(f"WARN: Could not parse dataset date {dataset_date_str!r}: {e}")

    # 4. Model watchlist age, models list equality, and provenance
    watchlist_path = repo_root / "monitoring" / "model_watchlist.json"
    if not watchlist_path.exists():
        findings.append(f"MISCONFIGURED: Missing model watchlist at {watchlist_path}")
        return 4, "MISCONFIGURED", findings, {}

    try:
        watchlist = json.loads(watchlist_path.read_text(encoding="utf-8"))
    except Exception as e:
        return 4, "MISCONFIGURED", [f"Unreadable model watchlist: {e}"], {}

    # Check schema provenance fields
    if "verification_method" not in watchlist or watchlist.get("verification_method") is None:
        return 4, "MISCONFIGURED", ["MISCONFIGURED: Missing required 'verification_method' in model_watchlist.json"], {}

    v_method = watchlist.get("verification_method")
    v_with_api = watchlist.get("verified_with_api")

    # Contradiction check
    if v_method == "api_call" and not v_with_api:
        return 4, "MISCONFIGURED", ["MISCONFIGURED: model_watchlist.json contradicts itself: verification_method='api_call' but verified_with_api is false"], {}
    if v_method != "api_call" and v_with_api:
        return 4, "MISCONFIGURED", [f"MISCONFIGURED: model_watchlist.json contradicts itself: verification_method='{v_method}' but verified_with_api is true"], {}

    # Date parsing and future date check
    last_verified_str = watchlist.get("last_verified")
    if last_verified_str:
        try:
            wl_date = date.fromisoformat(last_verified_str)
            if wl_date > date.today():
                exit_code = 1
                status = "DRIFT"
                findings.append(f"DRIFT: Model watchlist last_verified date {last_verified_str} is in the future")
            else:
                wl_age_days = (date.today() - wl_date).days
                max_wl_days = baseline.get("thresholds", {}).get("model_watchlist_max_age_days", 90)
                if wl_age_days > max_wl_days:
                    findings.append(f"WARN: Model watchlist is {wl_age_days} days old (last verified: {last_verified_str}, threshold: {max_wl_days} days)")
                else:
                    findings.append(f"OK: Model watchlist age {wl_age_days} days is within threshold ({max_wl_days} days)")
        except Exception as e:
            findings.append(f"WARN: Could not parse model watchlist date {last_verified_str!r}: {e}")
    else:
        if v_method != "unverified":
            findings.append(f"WARN: Model watchlist last_verified is null for method '{v_method}'")

    wl_models = watchlist.get("models", [])
    supp_models = analyzer.SUPPORTED_MODELS
    if wl_models != supp_models:
        exit_code = 1
        status = "DRIFT"
        findings.append(f"DRIFT: Model watchlist does not match analyzer.SUPPORTED_MODELS (watchlist={wl_models}, supported={supp_models})")
    else:
        findings.append(f"OK: Model watchlist matches analyzer.SUPPORTED_MODELS ({len(supp_models)} models)")

    # Provenance reporting
    if v_method == "api_call":
        findings.append(f"OK: Model list verified against the live Gemini API on {last_verified_str}")
    else:
        findings.append(f"WARN: Model list is NOT verified against the live API (method={v_method}); ids may be stale or retired")

    details = {
        "fingerprint": curr_fp,
        "drift_items": drift_items,
        "fixtures_count": len(curr_fixtures),
    }
    return exit_code, status, findings, details


def run_online_probes(repo_root: Path) -> Tuple[int, str, List[str], Dict[str, Any]]:
    """
    Run online network probes with 3 attempts and exponential backoff.
    Returns: (exit_code, status, findings, probe_details)
    """
    findings = []
    probes = {}
    exit_code = 0
    status = "OK"

    # Probe 1: Yahoo Finance live quote check
    from nifty_universe import fetch_live_market_data

    yahoo_tickers = ["RELIANCE", "TCS", "HDFCBANK"]
    yahoo_success_count = 0
    yahoo_results = {}

    for attempt in range(3):
        yahoo_success_count = 0
        yahoo_results.clear()
        for tkr in yahoo_tickers:
            try:
                res = fetch_live_market_data(tkr)
                if res and res.get("data_status") in {"live", "provider"} and res.get("current_price"):
                    yahoo_success_count += 1
                    yahoo_results[tkr] = f"OK ({res.get('data_status')}, price={res.get('current_price')})"
                else:
                    st_val = res.get("data_status") if res else "None"
                    yahoo_results[tkr] = f"FALLBACK/NONE ({st_val})"
            except Exception as e:
                yahoo_results[tkr] = f"ERROR ({type(e).__name__})"

        if yahoo_success_count >= 2:
            break
        if attempt < 2:
            time.sleep(2.0 * (attempt + 1))

    probes["yahoo"] = {
        "success_count": yahoo_success_count,
        "tickers": yahoo_results,
    }
    if yahoo_success_count >= 2:
        findings.append(f"OK: Yahoo Finance live market data verified ({yahoo_success_count}/3 tickers live)")
    else:
        exit_code = 3
        status = "SOURCE_UNAVAILABLE"
        findings.append(f"UNAVAILABLE: Yahoo source unavailable or fallback-only ({yahoo_success_count}/3 tickers live; details: {yahoo_results})")

    # Probe 2: BSE / Exchange Annual Report Discovery Check
    from annual_report_fetcher import get_available_annual_reports

    filing_success = False
    filing_count = 0
    for attempt in range(3):
        try:
            reports = get_available_annual_reports("RELIANCE")
            if reports and len(reports) > 0 and any(r.get("url") for r in reports):
                filing_success = True
                filing_count = len(reports)
                break
        except Exception as e:
            pass
        if attempt < 2:
            time.sleep(2.0 * (attempt + 1))

    probes["filing_discovery"] = {
        "success": filing_success,
        "reports_found": filing_count,
    }
    if filing_success:
        findings.append(f"OK: Annual report discovery operational ({filing_count} filings discovered for RELIANCE)")
    else:
        if exit_code < 3:
            exit_code = 3
            status = "SOURCE_UNAVAILABLE"
        findings.append("UNAVAILABLE: Annual report discovery source unavailable (0 filings discovered for RELIANCE)")

    # Probe 3: Gemini Model Availability Check
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        env_file = repo_root / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    gemini_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    if not gemini_key:
        probes["gemini"] = {"status": "SKIPPED", "reason": "no_key"}
        findings.append("OK: Gemini model availability probe skipped (no GEMINI_API_KEY set)")
    else:
        gemini_success = False
        missing_models = []
        for attempt in range(3):
            try:
                from google import genai
                client = genai.Client(api_key=gemini_key)
                listed = [m.name.replace("models/", "") for m in client.models.list()]
                missing = [m for m in analyzer.SUPPORTED_MODELS if m not in listed]
                missing_models = missing
                if not missing:
                    gemini_success = True
                    break
            except Exception as e:
                missing_models = [f"API_ERROR_{type(e).__name__}"]
            if attempt < 2:
                time.sleep(2.0 * (attempt + 1))

        probes["gemini"] = {
            "success": gemini_success,
            "missing_models": missing_models,
        }
        if gemini_success:
            findings.append(f"OK: All {len(analyzer.SUPPORTED_MODELS)} supported Gemini models verified in API Studio")
        else:
            if exit_code < 3:
                exit_code = 3
                status = "SOURCE_UNAVAILABLE"
            findings.append(f"UNAVAILABLE: Gemini models unavailable or missing: {missing_models}")

    # Probe 4: Local Cache Purge Sanity Check
    cache_dir = repo_root / ".cache" / "evaluations"
    stale_cache_count = 0
    now_ts = time.time()
    max_cache_age_sec = 4 * 24 * 3600  # 4x TTL (96 hours)
    if cache_dir.exists():
        for cfile in cache_dir.glob("*.json"):
            try:
                if now_ts - cfile.stat().st_mtime > max_cache_age_sec:
                    stale_cache_count += 1
            except Exception:
                pass

    probes["cache_sanity"] = {
        "stale_cache_count": stale_cache_count,
    }
    if stale_cache_count > 0:
        findings.append(f"WARN: {stale_cache_count} evaluation cache files are older than 4x TTL (96h) and not being purged")
    else:
        findings.append("OK: Evaluation cache TTL hygiene verified")

    return exit_code, status, findings, probes


def main() -> None:
    parser = argparse.ArgumentParser(description="Project KUSHA Data-Truth Monitor")
    parser.add_argument("--check", action="store_true", help="Run monitoring checks")
    parser.add_argument("--offline", action="store_true", help="Run deterministic offline checks")
    parser.add_argument("--online", action="store_true", help="Run live online probes")
    parser.add_argument("--update-baseline", action="store_true", help="Update monitoring/baseline.json")
    parser.add_argument("--reason", type=str, default="", help="Reason for baseline update")
    parser.add_argument("--json", action="store_true", help="Output JSON result on stdout")

    args = parser.parse_args()

    if args.update_baseline:
        code = update_baseline(REPO_ROOT, args.reason)
        sys.exit(code)

    if not args.check and not args.offline and not args.online:
        # Default behavior is --check --offline
        args.check = True
        args.offline = True

    all_findings = []
    overall_exit_code = 0
    overall_status = "OK"
    details_payload: Dict[str, Any] = {}

    fp, _ = compute_fingerprint(REPO_ROOT)

    # 1. Run offline checks if requested or default
    if args.offline or not args.online:
        code, st, findings, dtls = run_offline_checks(REPO_ROOT)
        all_findings.extend(findings)
        details_payload["offline"] = dtls
        if code > overall_exit_code:
            overall_exit_code = code
            overall_status = st

    # 2. Run online probes if requested (only if offline checks did not fail with STALE/MISCONFIGURED)
    if args.online and overall_exit_code in {0, 1}:
        code, st, findings, probes = run_online_probes(REPO_ROOT)
        all_findings.extend(findings)
        details_payload["probes"] = probes
        if code > overall_exit_code:
            overall_exit_code = code
            overall_status = st

    if args.json:
        output_data = {
            "status": overall_status,
            "exit_code": overall_exit_code,
            "fingerprint": fp,
            "findings": all_findings,
            "details": details_payload,
        }
        print(json.dumps(output_data, indent=2))
    else:
        for f in all_findings:
            print(f)
        print(f"\nMonitor finished with status={overall_status} (exit_code={overall_exit_code})")

    sys.exit(overall_exit_code)


if __name__ == "__main__":
    main()
