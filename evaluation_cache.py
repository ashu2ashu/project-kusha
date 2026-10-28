"""
evaluation_cache.py
Local Response Replay Cache for Project KUSHA / StockSage.

Caches structured Gemini analysis results locally to preserve API quota
and provide instantaneous (<0.05s) replays during iterative development.
"""

import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

CACHE_SUBDIR = ".cache/evaluations"

def get_cache_dir() -> Path:
    """Returns the Path to the evaluations cache directory, creating it if needed."""
    base = Path(__file__).parent.resolve()
    cache_path = base / CACHE_SUBDIR
    cache_path.mkdir(parents=True, exist_ok=True)
    return cache_path

def sanitize_cache_token(val: str) -> str:
    """Sanitizes ticker or model strings for safe filenames."""
    raw = str(val or "").strip()
    if raw.upper().endswith(".NS"):
        raw = raw[:-3]
    elif raw.upper().endswith(".BO"):
        raw = raw[:-3]
    cleaned = re.sub(r'[^A-Za-z0-9_-]', '_', raw).upper()
    return cleaned[:30] if cleaned else "UNKNOWN"

def make_cache_filename(company_name: str, ticker: str, model: str) -> str:
    """Generates a deterministic filename for a given company, ticker, and model."""
    t_clean = sanitize_cache_token(ticker or company_name)
    m_clean = sanitize_cache_token(model or "gemini")
    return f"eval_{t_clean}_{m_clean}.json"

def load_cached_evaluation(
    company_name: str,
    ticker: str,
    model: str,
    current_pipeline_version: str
) -> Optional[Tuple[Dict[str, Any], str]]:
    """
    Attempts to load a previously cached evaluation.
    Returns (result_dict, cached_timestamp_str) if found and pipeline version matches,
    otherwise None.
    """
    cache_dir = get_cache_dir()
    fname = make_cache_filename(company_name, ticker, model)
    fpath = cache_dir / fname
    if not fpath.exists():
        return None

    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("pipeline_version") != current_pipeline_version:
            return None

        res = data.get("result")
        if not isinstance(res, dict) or not res.get("pillars"):
            return None

        cached_at = data.get("cached_at", "Cached")
        return res, cached_at
    except Exception:
        return None

def save_cached_evaluation(
    company_name: str,
    ticker: str,
    model: str,
    result: Dict[str, Any],
    pipeline_version: str
) -> bool:
    """
    Saves an analysis result dictionary into the local evaluation cache.
    """
    if not isinstance(result, dict) or not result.get("pillars"):
        return False

    cache_dir = get_cache_dir()
    fname = make_cache_filename(company_name, ticker, model)
    fpath = cache_dir / fname

    # Create a safe serializable copy of the result
    serializable_result = dict(result)

    payload = {
        "company_name": company_name,
        "ticker": ticker,
        "model": model,
        "pipeline_version": pipeline_version,
        "cached_at": datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC"),
        "result": serializable_result
    }

    try:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
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
            pass
    return count
