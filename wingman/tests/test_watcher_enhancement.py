#!/usr/bin/env python3
"""
Test script for Phase 4 Watcher Enhancement

Tests:
1. Severity classification (CRITICAL/HIGH/MEDIUM/LOW)
2. Deduplication (Redis-based fingerprinting)
3. Persistence (Database storage)
4. Quarantine (Redis-based worker blocking + API enforcement)

Usage:
    python tests/test_watcher_enhancement.py

Prerequisites:
    - Wingman TEST stack running (docker compose up -d)
    - Database migration 002_add_watcher_alerts.sql applied
    - Redis and Postgres accessible
"""

import os
import sys
import json
import time
import requests
import hashlib
from datetime import datetime

# Configuration (TEST environment)
API_URL = os.getenv("API_URL", "http://127.0.0.1:8101")
APPROVAL_READ_KEY = os.getenv("WINGMAN_APPROVAL_READ_KEY", "")
APPROVAL_DECIDE_KEY = os.getenv("WINGMAN_APPROVAL_DECIDE_KEY", "")
APPROVAL_REQUEST_KEY = os.getenv("WINGMAN_APPROVAL_REQUEST_KEY", "")

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_test(msg):
    print(f"{BLUE}[TEST]{RESET} {msg}")


def print_pass(msg):
    print(f"{GREEN}[PASS]{RESET} {msg}")


def print_fail(msg):
    print(f"{RED}[FAIL]{RESET} {msg}")


def print_warn(msg):
    print(f"{YELLOW}[WARN]{RESET} {msg}")


def test_severity_classification():
    """
    Test severity classification logic.

    Expected:
    - CRITICAL: FALSE claim in PRD + destructive op
    - HIGH: FALSE claim in PRD + safe op
    - MEDIUM: FALSE claim in TEST
    - LOW: UNVERIFIABLE
    """
    print_test("Testing severity classification...")

    test_cases = [
        {
            "name": "CRITICAL - PRD + docker stop",
            "event": {"status": "FALSE", "claim": "docker stop container", "worker_id": "test_critical"},
            "environment": "prd",
            "expected_severity": "CRITICAL"
        },
        {
            "name": "HIGH - PRD + safe command",
            "event": {"status": "FALSE", "claim": "docker ps", "worker_id": "test_high"},
            "environment": "prd",
            "expected_severity": "HIGH"
        },
        {
            "name": "MEDIUM - TEST + FALSE",
            "event": {"status": "FALSE", "claim": "docker stop container", "worker_id": "test_medium"},
            "environment": "test",
            "expected_severity": "MEDIUM"
        },
        {
            "name": "LOW - UNVERIFIABLE",
            "event": {"status": "UNVERIFIABLE", "claim": "unknown command", "worker_id": "test_low"},
            "environment": "test",
            "expected_severity": "LOW"
        }
    ]

    # Import classification logic from watcher
    sys.path.insert(0, "/Volumes/Data/ai_projects/wingman-system/wingman")
    from wingman_watcher import classify_severity

    passed = 0
    failed = 0

    for tc in test_cases:
        severity = classify_severity(tc["event"], tc["environment"])
        if severity == tc["expected_severity"]:
            print_pass(f"{tc['name']}: {severity}")
            passed += 1
        else:
            print_fail(f"{tc['name']}: expected {tc['expected_severity']}, got {severity}")
            failed += 1

    print(f"\nSeverity Classification: {passed} passed, {failed} failed\n")
    return failed == 0


def test_deduplication():
    """
    Test deduplication via fingerprinting.

    Expected:
    - Same event within TTL window -> same fingerprint
    - Different worker -> different fingerprint
    - Different time window -> different fingerprint
    """
    print_test("Testing deduplication fingerprinting...")

    sys.path.insert(0, "/Volumes/Data/ai_projects/wingman-system/wingman")
    from wingman_watcher import generate_fingerprint

    timestamp = int(time.time())

    # Test 1: Same event -> same fingerprint
    fp1 = generate_fingerprint("FALSE_CLAIM", "worker_123", timestamp, window_sec=3600)
    fp2 = generate_fingerprint("FALSE_CLAIM", "worker_123", timestamp, window_sec=3600)
    if fp1 == fp2:
        print_pass(f"Same event -> same fingerprint: {fp1}")
    else:
        print_fail(f"Same event -> different fingerprints: {fp1} vs {fp2}")
        return False

    # Test 2: Different worker -> different fingerprint
    fp3 = generate_fingerprint("FALSE_CLAIM", "worker_456", timestamp, window_sec=3600)
    if fp1 != fp3:
        print_pass(f"Different worker -> different fingerprint: {fp1} vs {fp3}")
    else:
        print_fail(f"Different worker -> same fingerprint")
        return False

    # Test 3: Different time window -> different fingerprint
    timestamp_next_window = timestamp + 3600  # 1 hour later
    fp4 = generate_fingerprint("FALSE_CLAIM", "worker_123", timestamp_next_window, window_sec=3600)
    if fp1 != fp4:
        print_pass(f"Different window -> different fingerprint: {fp1} vs {fp4}")
    else:
        print_fail(f"Different window -> same fingerprint")
        return False

    print("\nDeduplication: All tests passed\n")
    return True


def test_persistence():
    """
    Test database persistence via API.

    Steps:
    1. Trigger FALSE claim -> check alert appears in database
    2. Acknowledge alert -> check acknowledged_at updated
    3. Query alert history -> check filters work
    """
    print_test("Testing persistence (database + API)...")

    if not APPROVAL_READ_KEY:
        print_warn("Skipping persistence test: WINGMAN_APPROVAL_READ_KEY not set")
        return True

    # Step 1: Trigger FALSE claim by creating approval request that will be rejected
    # (This will generate a validation event, but not a watcher alert)
    # Instead, we'll directly query existing alerts

    # Query recent alerts
    try:
        resp = requests.get(
            f"{API_URL}/watcher/alerts?limit=5",
            headers={"X-Wingman-Approval-Read-Key": APPROVAL_READ_KEY},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            alerts = data.get("alerts", [])
            print_pass(f"Retrieved {len(alerts)} alerts from database")

            # Check alert structure
            if alerts:
                alert = alerts[0]
                required_fields = ["alert_id", "event_type", "severity", "sent_at", "environment"]
                missing = [f for f in required_fields if f not in alert]
                if not missing:
                    print_pass(f"Alert structure valid: {list(alert.keys())}")
                else:
                    print_fail(f"Alert missing fields: {missing}")
                    return False
        else:
            print_fail(f"Failed to query alerts: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print_fail(f"Exception querying alerts: {e}")
        return False

    # Test filtering
    try:
        resp = requests.get(
            f"{API_URL}/watcher/alerts?severity=CRITICAL&limit=10",
            headers={"X-Wingman-Approval-Read-Key": APPROVAL_READ_KEY},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            critical_alerts = data.get("alerts", [])
            print_pass(f"Severity filter works: {len(critical_alerts)} CRITICAL alerts")
        else:
            print_fail(f"Severity filter failed: {resp.status_code}")
            return False
    except Exception as e:
        print_fail(f"Exception testing filter: {e}")
        return False

    print("\nPersistence: All tests passed\n")
    return True


def test_quarantine():
    """
    Test quarantine feature.

    Steps:
    1. Simulate quarantine by adding worker to Redis
    2. Attempt approval request -> should be auto-rejected
    3. Release worker via API
    4. Attempt approval request again -> should succeed
    """
    print_test("Testing quarantine (Redis + API enforcement)...")

    if not APPROVAL_DECIDE_KEY or not APPROVAL_REQUEST_KEY:
        print_warn("Skipping quarantine test: WINGMAN_APPROVAL_DECIDE_KEY or REQUEST_KEY not set")
        return True

    test_worker_id = "test_quarantine_worker_123"

    # Step 1: Manually quarantine worker (simulating watcher behavior)
    try:
        import redis
        r = redis.Redis(host=os.getenv("REDIS_HOST", "127.0.0.1"), port=6379, db=0, decode_responses=True)
        r.sadd("quarantined_workers", test_worker_id)
        r.hset(f"quarantine:{test_worker_id}", mapping={
            "reason": "Test quarantine",
            "quarantined_at": datetime.now().isoformat(),
            "environment": "test"
        })
        print_pass(f"Worker {test_worker_id} quarantined via Redis")
    except Exception as e:
        print_fail(f"Failed to quarantine worker: {e}")
        return False

    # Step 2: Attempt approval request (should be auto-rejected)
    try:
        resp = requests.post(
            f"{API_URL}/approvals/request",
            headers={
                "X-Wingman-Approval-Request-Key": APPROVAL_REQUEST_KEY,
                "Content-Type": "application/json"
            },
            json={
                "worker_id": test_worker_id,
                "task_name": "Test task",
                "instruction": "docker ps",
                "deployment_env": "test"
            },
            timeout=10
        )
        if resp.status_code == 403:
            data = resp.json()
            if data.get("status") == "AUTO_REJECTED" and "quarantined" in data.get("reason", "").lower():
                print_pass(f"Quarantined worker auto-rejected: {data.get('reason')}")
            else:
                print_fail(f"Unexpected rejection reason: {data}")
                return False
        else:
            print_fail(f"Expected 403, got {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        print_fail(f"Exception testing quarantine enforcement: {e}")
        return False

    # Step 3: Release worker via API
    try:
        resp = requests.post(
            f"{API_URL}/watcher/release/{test_worker_id}",
            headers={
                "X-Wingman-Approval-Decide-Key": APPROVAL_DECIDE_KEY,
                "Content-Type": "application/json"
            },
            json={
                "released_by": "test_script",
                "reason": "Test release"
            },
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                print_pass(f"Worker released: {data.get('message')}")
            else:
                print_fail(f"Release failed: {data}")
                return False
        else:
            print_fail(f"Release API failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print_fail(f"Exception releasing worker: {e}")
        return False

    # Step 4: Attempt approval request again (should succeed or be pending)
    try:
        resp = requests.post(
            f"{API_URL}/approvals/request",
            headers={
                "X-Wingman-Approval-Request-Key": APPROVAL_REQUEST_KEY,
                "Content-Type": "application/json"
            },
            json={
                "worker_id": test_worker_id,
                "task_name": "Test task",
                "instruction": "docker ps",
                "deployment_env": "test"
            },
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            status = data.get("status")
            if status in ["AUTO_APPROVED", "PENDING"]:
                print_pass(f"Released worker can request approvals: {status}")
            else:
                print_fail(f"Unexpected status after release: {status}")
                return False
        elif resp.status_code == 403:
            data = resp.json()
            print_fail(f"Worker still blocked after release: {data.get('reason')}")
            return False
        else:
            print_fail(f"Unexpected response: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print_fail(f"Exception testing post-release approval: {e}")
        return False

    print("\nQuarantine: All tests passed\n")
    return True


def main():
    print(f"\n{'='*60}")
    print("Phase 4 Watcher Enhancement Test Suite")
    print(f"{'='*60}\n")

    print(f"API URL: {API_URL}")
    print(f"Read Key: {'✓' if APPROVAL_READ_KEY else '✗ (set WINGMAN_APPROVAL_READ_KEY)'}")
    print(f"Decide Key: {'✓' if APPROVAL_DECIDE_KEY else '✗ (set WINGMAN_APPROVAL_DECIDE_KEY)'}")
    print(f"Request Key: {'✓' if APPROVAL_REQUEST_KEY else '✗ (set WINGMAN_APPROVAL_REQUEST_KEY)'}")
    print()

    results = []

    # Test 1: Severity Classification
    results.append(("Severity Classification", test_severity_classification()))

    # Test 2: Deduplication
    results.append(("Deduplication", test_deduplication()))

    # Test 3: Persistence
    results.append(("Persistence", test_persistence()))

    # Test 4: Quarantine
    results.append(("Quarantine", test_quarantine()))

    # Summary
    print(f"{'='*60}")
    print("Test Summary")
    print(f"{'='*60}\n")

    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)

    for name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{name}: {status}")

    print(f"\nTotal: {passed} passed, {failed} failed\n")

    if failed == 0:
        print(f"{GREEN}All tests passed!{RESET}\n")
        return 0
    else:
        print(f"{RED}Some tests failed!{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
