"""
evaluation_cache.py
Local Response Replay Cache for Project KUSHA / StockSage.

Caches structured Gemini analysis results locally to preserve API quota
and provide instantaneous (<0.05s) replays during iterative development.
Enforces multi-factor input cache keys (preventing document cross-replay),
24-hour TTL expiration, schema 3.0 provenance, and malformed payload purging.
"""

import os
import json
import re
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

CACHE_SUBDIR = ".cache/evaluations"
SCHEMA_VERSION = "3.0"
MAX_CACHE_AGE_HOURS = 24


def get_max_cache_age_hours() -> int:
    """Returns the maximum cache TTL in hours (default: 24, env override: KUSHA_CACHE_MAX_AGE_HOURS)."""
    try:
        return int(os.getenv("KUSHA_CACHE_MAX_AGE_HOURS", str(MAX_CACHE_AGE_HOURS)))
    except ValueError:
        return MAX_CACHE_AGE_HOURS


def get_cache_dir() -> Path:
    """Returns the Path to the evaluations cache directory, creating it if needed."""
    base = Path(__file__).parent.resolve()
    cache_path = base / CACHE_SUBDIR
    cache_path.mkdir(parents=True, exist_ok=True)
    return cache_path


def sanitize_cache_token(val: str) -> str:
    """Sanitizes ticker or token strings for safe filenames."""
    raw = str(val or "").strip()
    if raw.upper().endswith(".NS"):
        raw = raw[:-3]
    elif raw.upper().endswith(".BO"):
        raw = raw[:-3]
    cleaned = re.sub(r'[^A-Za-z0-9_-]', '_', raw).upper()
    return cleaned[:30] if cleaned else "UNKNOWN"


def make_cache_key(
    ticker: Optional[str],
    model: Optional[str],
    pipeline_version: Optional[str],
    document_hash: Optional[str] = "no_document",
    sector: Optional[str] = "unknown",
    skip_web_search: bool = False,
    analysis_mode: Optional[str] = "standard"
) -> str:
    """
    Generates a deterministic 32-character SHA-256 hash incorporating all
    inputs that affect the analysis output.
    """
    raw = "|".join([
        str(ticker or "").upper().strip(),
        str(model or ""),
        str(pipeline_version or ""),
        str(document_hash or "no_document"),
        str(sector or "unknown").upper().strip(),
        "noweb" if skip_web_search else "web",
        str(analysis_mode or "standard"),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def make_cache_filename(ticker_or_company: str, key_or_ticker: str, *args) -> str:
    """
    Generates a cache filename.
    New standard: eval_<sanitized_ticker>_<32char_key>.json
    Legacy compatibility: eval_<sanitized_ticker>_<model>.json when 3 args provided.
    """
    if args:
        # Legacy call: make_cache_filename(company_name, ticker, model)
        company_name = ticker_or_company
        ticker = key_or_ticker
        model = args[0]
        t_clean = sanitize_cache_token(ticker or company_name)
        m_clean = sanitize_cache_token(model or "gemini")
        return f"eval_{t_clean}_{m_clean}.json"

    t_clean = sanitize_cache_token(ticker_or_company)[:12]
    return f"eval_{t_clean}_{key_or_ticker}.json"


def format_relative_cache_time(dt: datetime) -> str:
    """
    Formats a UTC datetime into a human-readable relative string:
    e.g. 'Cached 3 hours ago (30 Oct 2026, 14:02 UTC)'
    """
    now = datetime.now(timezone.utc)
    delta_sec = max(0, int((now - dt).total_seconds()))
    human_stamp = dt.strftime("%d %b %Y, %H:%M UTC")

    if delta_sec < 60:
        return f"Cached just now ({human_stamp})"
    mins = delta_sec // 60
    if mins < 60:
        return f"Cached {mins} min{'s' if mins != 1 else ''} ago ({human_stamp})"
    hours = mins // 60
    if hours < 24:
        return f"Cached {hours} hour{'s' if hours != 1 else ''} ago ({human_stamp})"
    days = hours // 24
    return f"Cached {days} day{'s' if days != 1 else ''} ago ({human_stamp})"


def load_cached_evaluation(
    ticker: Optional[str] = None,
    model: Optional[str] = None,
    current_pipeline_version: Optional[str] = None,
    document_hash: Optional[str] = "no_document",
    sector: Optional[str] = "unknown",
    skip_web_search: bool = False,
    analysis_mode: Optional[str] = "standard",
    company_name: Optional[str] = None,
    *args,
    **kwargs
) -> Optional[Tuple[Dict[str, Any], str]]:
    """
    Attempts to load a previously cached evaluation matching all input factors.
    Enforces schema_version 3.0, provenance block, payload shape integrity,
    and 24-hour TTL expiration.
    Returns (result_dict, relative_cached_time_str) or None.
    """
    # Detect legacy positional call: (company_name, ticker, model, pipeline_version)
    if current_pipeline_version and any(m in str(current_pipeline_version).lower() for m in ["gemini", "flash", "gpt", "model"]):
        company_name = ticker
        ticker = model
        model = current_pipeline_version
        current_pipeline_version = document_hash
        document_hash = "no_document"

    if not ticker and company_name:
        ticker = company_name

    key = make_cache_key(
        ticker=ticker,
        model=model,
        pipeline_version=current_pipeline_version,
        document_hash=document_hash,
        sector=sector,
        skip_web_search=skip_web_search,
        analysis_mode=analysis_mode,
    )

    cache_dir = get_cache_dir()
    fname = make_cache_filename(str(ticker), key)
    fpath = cache_dir / fname

    # Fallback probe for legacy filename format during version migration
    if not fpath.exists():
        legacy_fname = f"eval_{sanitize_cache_token(str(ticker))}_{sanitize_cache_token(str(model))}.json"
        legacy_fpath = cache_dir / legacy_fname
        if legacy_fpath.exists():
            fpath = legacy_fpath
            fname = legacy_fname
        else:
            return None

    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.warning("Corrupt cache file %s: failed to parse JSON: %s. Purging.", fname, e)
        try:
            fpath.unlink(missing_ok=True)
        except OSError:
            # Best effort cleanup of corrupt cache file; pass
            pass
        return None

    # 1. Schema version validation
    schema_ver = data.get("schema_version")
    if schema_ver != SCHEMA_VERSION:
        logger.warning("Rejected cache payload %s: invalid or missing schema_version (%s)", fname, schema_ver)
        try:
            fpath.unlink(missing_ok=True)
        except OSError:
            # Best effort cleanup of invalid cache file; pass
            pass
        return None

    # 2. Provenance block validation
    provenance = data.get("provenance")
    if not isinstance(provenance, dict) or not provenance.get("created_at"):
        logger.warning("Rejected cache payload %s: missing or invalid provenance block", fname)
        try:
            fpath.unlink(missing_ok=True)
        except OSError:
            # Best effort cleanup of unprovenanced cache file; pass
            pass
        return None

    # 3. Pipeline version check
    if data.get("pipeline_version") != current_pipeline_version:
        return None

    # 4. Shape validation (must contain pillars, final_score, and forensic_report)
    res = data.get("result")
    if not isinstance(res, dict):
        logger.warning("Rejected cache payload %s: result is not a dictionary", fname)
        try:
            fpath.unlink(missing_ok=True)
        except OSError:
            # Best effort cleanup of malformed cache file; pass
            pass
        return None

    if not isinstance(res.get("pillars"), list) or not isinstance(res.get("final_score"), (int, float)) or not isinstance(res.get("forensic_report"), (dict, str)):
        logger.warning("Rejected cache payload %s: missing required shape (pillars, final_score, forensic_report)", fname)
        try:
            fpath.unlink(missing_ok=True)
        except OSError:
            # Best effort cleanup of malformed cache file; pass
            pass
        return None

    # 5. Freshness / TTL validation (Task 4)
    created_at_raw = provenance.get("created_at") or data.get("created_at")
    if not created_at_raw:
        logger.info("Cache entry %s rejected: missing created_at timestamp", fname)
        return None

    try:
        created_dt = datetime.fromisoformat(created_at_raw)
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)
    except Exception as e:
        logger.info("Cache entry %s rejected: malformed created_at timestamp (%s)", fname, e)
        return None

    max_age_h = get_max_cache_age_hours()
    age_seconds = (datetime.now(timezone.utc) - created_dt).total_seconds()
    age_hours = age_seconds / 3600.0

    if age_hours > (4 * max_age_h):
        logger.info("Cache entry %s is older than 4x TTL (%.1fh > %dh); deleting file", fname, age_hours, 4 * max_age_h)
        try:
            fpath.unlink(missing_ok=True)
        except OSError:
            # Best effort cleanup of expired cache file; pass
            pass
        return None

    if age_hours > max_age_h:
        logger.info("Cache entry %s expired (age: %.1fh > %dh)", fname, age_hours, max_age_h)
        return None

    relative_label = format_relative_cache_time(created_dt)
    return res, relative_label


def save_cached_evaluation(
    ticker: Optional[str] = None,
    model: Optional[str] = None,
    pipeline_version: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
    document_hash: Optional[str] = "no_document",
    sector: Optional[str] = "unknown",
    skip_web_search: bool = False,
    analysis_mode: Optional[str] = "standard",
    company_name: Optional[str] = None,
    *args,
    **kwargs
) -> bool:
    """
    Saves an analysis result dictionary into the local evaluation cache with
    schema_version 3.0, ISO timestamp, and multi-factor input cache key.
    """
    # Detect legacy positional call: (company_name, ticker, model, result, pipeline_version)
    if pipeline_version and any(m in str(pipeline_version).lower() for m in ["gemini", "flash", "gpt", "model"]):
        company_name = ticker
        ticker = model
        model = pipeline_version
        pipeline_version = document_hash
        document_hash = "no_document"

    if not ticker and company_name:
        ticker = company_name

    if not isinstance(result, dict) or not result.get("pillars"):
        return False

    key = make_cache_key(
        ticker=ticker,
        model=model,
        pipeline_version=pipeline_version,
        document_hash=document_hash,
        sector=sector,
        skip_web_search=skip_web_search,
        analysis_mode=analysis_mode,
    )

    cache_dir = get_cache_dir()
    fname = make_cache_filename(str(ticker), key)
    fpath = cache_dir / fname

    # Create a safe serializable copy of the result
    serializable_result = dict(result)

    now_dt = datetime.now(timezone.utc)
    now_iso = now_dt.isoformat()
    now_formatted = format_relative_cache_time(now_dt)

    provenance_block = {
        "created_at": now_iso,
        "pipeline_version": pipeline_version,
        "model_requested": model,
        "model_used": result.get("model_used") or model,
        "model_fallback_used": result.get("model_fallback_used", False),
        "data_source_note": result.get("data_source_note") or "Third-party market & filing data; Gemini grounded search",
        "cache_key": key,
        "document_hash": document_hash,
    }

    payload = {
        "schema_version": SCHEMA_VERSION,
        "company_name": company_name or ticker,
        "ticker": ticker,
        "model": model,
        "pipeline_version": pipeline_version,
        "document_hash": document_hash,
        "created_at": now_iso,
        "provenance": provenance_block,
        "cached_at": now_formatted,
        "result": serializable_result
    }

    try:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.warning("Failed to save cache file %s: %s", fname, e)
        return False


def get_cache_stats() -> Dict[str, Any]:
    """
    Returns total count of cached evaluations and disk space in KB and MB.
    """
    cache_dir = get_cache_dir()
    files = list(cache_dir.glob("eval_*.json"))
    total_bytes = sum(f.stat().st_size for f in files if f.is_file())
    return {
        "count": len(files),
        "total_kb": round(total_bytes / 1024, 1),
        "total_mb": round(total_bytes / (1024 * 1024), 2)
    }


def clear_evaluation_cache() -> int:
    """
    Deletes all cached evaluation files. Returns count of files deleted.
    """
    cache_dir = get_cache_dir()
    files = list(cache_dir.glob("eval_*.json"))
    count = 0
    for f in files:
        try:
            f.unlink()
            count += 1
        except Exception:
            # Best effort cleanup of cache directory; pass
            pass
    return count
