"""
diagnose_quota.py
Manual, read-only diagnosis of a Gemini API key when the app reports
"Gemini quota exhausted on every available model".

Why this exists: the app's own message is a summary. It cannot tell you whether you
hit a per-minute throttle, a spent daily bucket, a search-grounding quota, or a
project with zero quota. Google's raw 429 text can. This script prints it.

It makes one tiny generation request per model (max_output_tokens=1), so the cost is
negligible even on a free tier. It never prints the API key.

Usage:
    export GEMINI_API_KEY="..."      # or put it in .env
    python tools/diagnose_quota.py

Exit codes:
    0  at least one model answered
    1  no key provided
    2  every model failed (the raw reasons are printed)
"""

import getpass
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

# Allow `python tools/diagnose_quota.py` from the repo root to import analyzer.py.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

load_dotenv()

MAX_DETAIL_CHARS = 400


def get_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        return key
    if len(sys.argv) > 1:
        print("Refusing to read an API key from argv (shell history / process list leak).")
    try:
        if sys.stdin.isatty():
            return getpass.getpass("Enter your Gemini API key (hidden): ").strip()
    except Exception:
        pass
    return ""


def redact(text: str) -> str:
    text = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED_API_KEY]", str(text))
    text = re.sub(r"key=[0-9A-Za-z_-]{16,}", "key=[REDACTED]", text)
    return " ".join(text.split())[:MAX_DETAIL_CHARS]


def classify(detail: str) -> str:
    """Turn Google's error text into the one conclusion that matters: throttle or spent."""
    lowered = (detail or "").lower()
    if "per day" in lowered or "perday" in lowered or "daily" in lowered:
        return "DAILY LIMIT — this model's bucket is spent until the midnight-Pacific reset."
    if "per minute" in lowered or "perminute" in lowered or "rpm" in lowered:
        return "PER-MINUTE THROTTLE — wait ~60s and the same model will work."
    if "per 1m tokens" in lowered or "tokens per minute" in lowered or "tpm" in lowered:
        return "TOKEN-PER-MINUTE THROTTLE — the prompt is too large for this tier right now."
    if "billing" in lowered or "free tier" in lowered and "not available" in lowered:
        return "PROJECT/Billing — this project may not have free-tier access to this model."
    if "suspended" in lowered or "disabled" in lowered:
        return "PROJECT SUSPENDED or API disabled."
    if "google_search" in lowered or "grounding" in lowered:
        return "SEARCH-GROUNDING QUOTA — generation may be fine; the search tool is limited."
    if "quota" in lowered or "429" in lowered or "resource_exhausted" in lowered:
        return "UNSPECIFIED 429 — no metric named. Treat as rate limit until proven otherwise."
    return "NON-429 ERROR — see the detail above."


def main() -> int:
    key = get_api_key()
    if not key:
        print("No API key. Set GEMINI_API_KEY or add it to .env, then re-run.")
        return 1

    try:
        from analyzer import SUPPORTED_MODELS
        from google import genai
        from google.genai import types
    except ImportError as exc:
        print(f"Missing dependency: {exc}")
        return 1

    client = genai.Client(api_key=key)
    working, failures = [], []

    for model in SUPPORTED_MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents="Reply with the single word: ok",
                config=types.GenerateContentConfig(max_output_tokens=1, temperature=0),
            )
            text = (getattr(response, "text", "") or "").strip()
            print(f"[ OK ] {model:<26} responded ({text!r})")
            working.append(model)
        except Exception as exc:
            detail = redact(str(exc))
            print(f"[FAIL] {model:<26} {detail}")
            print(f"       -> {classify(detail)}")
            failures.append((model, detail))

    print()
    if not working:
        print("Every model failed. The classification lines above say which kind of limit it is.")
        print("If they all read PER-MINUTE THROTTLE, wait one minute and re-run this script.")
        print("If they read DAILY LIMIT, wait for the Pacific reset; nothing else recovers it.")
        return 2

    print(f"{len(working)}/{len(SUPPORTED_MODELS)} models answered: {', '.join(working)}")
    print("The app's fallback will pick one of these on the next run.")

    # Two immediate calls on the same model: a daily bucket survives this, an RPM cap does not.
    print(f"\nRate-limit probe: two back-to-back calls to {working[0]} ...")
    for attempt in (1, 2):
        try:
            client.models.generate_content(
                model=working[0],
                contents="ok",
                config=types.GenerateContentConfig(max_output_tokens=1, temperature=0),
            )
            print(f"  call {attempt}: OK")
        except Exception as exc:
            detail = redact(str(exc))
            print(f"  call {attempt}: {detail}")
            print(f"  -> {classify(detail)}")
            if "per minute" in detail.lower():
                print("  Conclusion: this is a RATE limit, not a spent daily bucket.")
                print("  The app now honours Google's retryDelay for short waits; re-run the app.")
            break

    return 0


if __name__ == "__main__":
    sys.exit(main())
