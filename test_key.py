"""
test_key.py
Security-hardened utility to verify Google Gemini API connectivity.
Reads API key securely from environment variable GEMINI_API_KEY or prompts
interactively via masked input (getpass) to prevent exposure in shell history
and process listings.
"""

import os
import sys
import getpass
from dotenv import load_dotenv

load_dotenv()

def get_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        return key
    
    # Do not allow keys as command-line arguments (avoids shell history and `ps` leakage)
    if len(sys.argv) > 1:
        print("\n⚠️ Security Notice: Passing API keys as command-line arguments is disabled")
        print("to prevent secrets from being recorded in shell history or process listings.")
        print("Please set the GEMINI_API_KEY environment variable or enter it securely below.\n")
    
    try:
        if sys.stdin.isatty():
            return getpass.getpass("Enter your Gemini API key (hidden): ").strip()
    except Exception:
        pass
    
    return ""

def main():
    key = get_api_key()
    if not key:
        print("\n❌ No API key provided.")
        print("Set GEMINI_API_KEY in your environment or .env file, e.g.:")
        print("   export GEMINI_API_KEY=\"your_key_here\"")
        print("   python3 test_key.py\n")
        sys.exit(1)

    from analyzer import verify_gemini_api_key

    print("\n🔍 Checking your Gemini API key connectivity...")
    # Safe verification: verify_gemini_api_key never logs or prints the raw key
    is_valid, msg = verify_gemini_api_key(key)
    print(f"\n{msg}\n")

if __name__ == "__main__":
    main()
