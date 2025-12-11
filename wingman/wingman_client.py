#!/usr/bin/env python3
"""
Wingman Client - Simple CLI wrapper for the Wingman API

Usage:
    python wingman_client.py "I created /tmp/test.txt"
    python wingman_client.py --enhanced "I started Docker"

The client talks to the Wingman service running at:
    WINGMAN_API_URL (env) or http://127.0.0.1:8001 by default.
"""

import json
import os
import sys
import urllib.request
import urllib.error


DEFAULT_API_URL = "http://127.0.0.1:8001"


def verify_claim(claim: str, use_enhanced: bool = False) -> dict:
    """Call Wingman /verify and return parsed JSON response."""
    api_base = os.getenv("WINGMAN_API_URL", DEFAULT_API_URL).rstrip("/")
    url = f"{api_base}/verify"

    payload = {
        "claim": claim,
        "use_enhanced": use_enhanced,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        return {
            "error": f"HTTP {e.code}: {e.reason}",
            "body": e.read().decode("utf-8", errors="ignore"),
        }
    except urllib.error.URLError as e:
        return {
            "error": f"Failed to reach Wingman API at {url}: {e.reason}",
        }
    except Exception as e:
        return {
            "error": f"Unexpected error calling Wingman API: {e}",
        }


def main(argv: list[str]) -> int:
    if not argv:
        print("Usage: python wingman_client.py [--enhanced] \"claim text\"")
        return 1

    use_enhanced = False
    args = []
    for arg in argv:
        if arg in ("--enhanced", "-e"):
            use_enhanced = True
        else:
            args.append(arg)

    if not args:
        print("Error: missing claim text.")
        print("Usage: python wingman_client.py [--enhanced] \"claim text\"")
        return 1

    claim = " ".join(args)

    print(f"🔍 Sending claim to Wingman: {claim}")
    if use_enhanced:
        print("   Mode: enhanced (if available)")

    result = verify_claim(claim, use_enhanced=use_enhanced)

    if "error" in result:
        print(f"\n🚨 Error: {result['error']}")
        body = result.get("body")
        if body:
            print(f"\nResponse body:\n{body}")
        return 1

    verdict = result.get("verdict", "UNVERIFIABLE")
    details = result.get("details", "")

    print("\n📊 Wingman Verdict")
    print("------------------")
    print(f"Verdict: {verdict}")
    if details:
        print(f"Details: {details}")

    ts = result.get("timestamp")
    if ts:
        print(f"Time:    {ts}")

    verifier = result.get("verifier")
    if verifier:
        print(f"Verifier: {verifier}")

    return 0 if verdict == "TRUE" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


