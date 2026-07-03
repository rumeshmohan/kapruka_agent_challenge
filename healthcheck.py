#!/usr/bin/env python3
"""
Simple health check script for Railway deployment monitoring.
Usage: python healthcheck.py
"""
import sys
import os
from pathlib import Path

def check_health() -> bool:
    """
    Verify essential components are available.
    Returns True if healthy, False otherwise.
    """
    checks_passed = []
    checks_failed = []

    # Check 1: Python environment
    try:
        assert sys.version_info >= (3, 10)
        checks_passed.append("✓ Python version >= 3.10")
    except AssertionError:
        checks_failed.append("✗ Python version too old")

    # Check 2: Required directories exist
    required_dirs = ["agents", "ui", "config", "utils", "memory"]
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            checks_passed.append(f"✓ Directory '{dir_name}' exists")
        else:
            checks_failed.append(f"✗ Directory '{dir_name}' missing")

    # Check 3: Required files exist
    required_files = ["app.py", "main.py", "requirements.txt"]
    for file_name in required_files:
        if Path(file_name).exists():
            checks_passed.append(f"✓ File '{file_name}' exists")
        else:
            checks_failed.append(f"✗ File '{file_name}' missing")

    # Check 4: At least one API key is set
    api_keys = ["OPENAI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY", "COHERE_API_KEY"]
    has_api_key = any(os.getenv(key) for key in api_keys)
    if has_api_key:
        checks_passed.append("✓ At least one API key configured")
    else:
        checks_failed.append("✗ No API keys configured")

    # Check 5: Can import main modules
    try:
        import streamlit
        checks_passed.append("✓ Streamlit installed")
    except ImportError:
        checks_failed.append("✗ Streamlit not installed")

    try:
        import openai
        checks_passed.append("✓ OpenAI SDK installed")
    except ImportError:
        checks_failed.append("✗ OpenAI SDK not installed")

    # Print results
    print("=" * 60)
    print("HEALTH CHECK RESULTS")
    print("=" * 60)

    if checks_passed:
        print("\nPassed Checks:")
        for check in checks_passed:
            print(f"  {check}")

    if checks_failed:
        print("\nFailed Checks:")
        for check in checks_failed:
            print(f"  {check}")

    print("\n" + "=" * 60)

    is_healthy = len(checks_failed) == 0
    if is_healthy:
        print("STATUS: HEALTHY ✓")
    else:
        print("STATUS: UNHEALTHY ✗")
    print("=" * 60)

    return is_healthy

if __name__ == "__main__":
    is_healthy = check_health()
    sys.exit(0 if is_healthy else 1)
