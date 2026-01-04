#!/usr/bin/env python3
"""
DEV E2E smoke test for Phase 4 (Original): Human Approval Layer (HITL).

This script does NOT deploy anything. It just calls the API endpoints:
  - POST /approvals/request
  - GET  /approvals/pending
  - POST /approvals/<id>/approve
  - POST /approvals/<id>/reject

Usage:
  API_URL=http://localhost:8002 python3 dev_e2e_phase4.py
"""

import os
import time
import requests


API_URL = os.getenv("API_URL", "http://localhost:5000").rstrip("/")


def jprint(obj):
    import json

    print(json.dumps(obj, indent=2, sort_keys=True))


def main():
    print(f"🔧 API_URL={API_URL}")

    # Force a MEDIUM risk by including postgres keyword
    instruction = "\n".join(
        [
            "DELIVERABLES: x",
            "SUCCESS_CRITERIA: x",
            "BOUNDARIES: dev",
            "DEPENDENCIES: postgres",
            "MITIGATION: rollback",
            "TEST_PROCESS: x",
            "TEST_RESULTS_FORMAT: x",
            "RESOURCE_REQUIREMENTS: x",
            "RISK_ASSESSMENT: low",
            "QUALITY_METRICS: x",
        ]
    )

    r = requests.post(
        f"{API_URL}/approvals/request",
        json={"worker_id": "dev-1", "task_name": "DB change", "instruction": instruction, "deployment_env": "dev"},
        timeout=10,
    )
    r.raise_for_status()
    res = r.json()
    print("\n--- request")
    jprint(res)

    req = (res.get("request") or {})
    request_id = req.get("request_id")
    if not request_id:
        raise SystemExit("No request_id returned")

    r = requests.get(f"{API_URL}/approvals/pending", timeout=10)
    r.raise_for_status()
    pending = r.json()
    print("\n--- pending")
    jprint(pending)

    # Approve it
    r = requests.post(
        f"{API_URL}/approvals/{request_id}/approve",
        json={"decided_by": "dev_e2e", "note": "smoke test"},
        timeout=10,
    )
    r.raise_for_status()
    approved = r.json()
    print("\n--- approve")
    jprint(approved)

    # Confirm it left pending
    time.sleep(0.2)
    r = requests.get(f"{API_URL}/approvals/pending", timeout=10)
    r.raise_for_status()
    pending2 = r.json()
    print("\n--- pending after")
    jprint(pending2)

    print("\n✅ Phase 4 HITL E2E smoke test passed.")


if __name__ == "__main__":
    main()


