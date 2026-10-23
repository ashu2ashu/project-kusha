"""
test_key.py
Quick utility to test if your Gemini API key works.
Usage:
    python3 test_key.py
    or
    python3 test_key.py YOUR_API_KEY
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

key = sys.argv[1] if len(sys.argv) > 1 else os.getenv("GEMINI_API_KEY", "")

if not key:
    print("\n❌ No API key provided!")
    print("How to use:")
    print("   python3 test_key.py YOUR_API_KEY")
    print("Or add GEMINI_API_KEY to your .env file.\n")
    sys.exit(1)

from analyzer import verify_gemini_api_key

print("\n🔍 Checking your Gemini API key...")
is_valid, msg = verify_gemini_api_key(key)
print(f"\n{msg}\n")
