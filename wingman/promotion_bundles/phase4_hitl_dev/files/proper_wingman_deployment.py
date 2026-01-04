#!/usr/bin/env python3
"""
Proper Wingman Deployment - PHASE 3 INTEGRATED (Mac Studio TEST)
1. Blocks work if instructions are invalid (Phase 2 Gate)
2. Logs all work progress/claims to Technical Truth Logger (Phase 3)
"""

import sys
import subprocess
import json
import requests
import os
from pathlib import Path
from datetime import datetime
import time

BASE_DIR = Path(__file__).parent

# API URL is environment-configurable so the same script can run in DEV/TEST/PRD safely.
# Examples:
#   DEV:  API_URL=http://localhost:8002 python3 proper_wingman_deployment.py
#   TEST: API_URL=http://localhost:8101 python3 proper_wingman_deployment.py
API_URL = os.getenv("API_URL", "").strip() or os.getenv("WINGMAN_API_URL", "").strip() or "http://localhost:8101"

def wingman_check(instruction_text):
    """PHASE 2: Instruction Gate"""
    print(f"\n🛡️  WINGMAN GATE: Validating instruction...")
    try:
        r = requests.post(f"{API_URL}/check", json={"instruction": instruction_text}, timeout=10)
        if r.status_code == 200:
            res = r.json()
            if res.get('approved'):
                print(f"   ✅ APPROVED (Score: {res['score']}%)")
                return True
            print(f"   ❌ REJECTED (Score: {res['score']}%) - Missing: {', '.join(res.get('missing_sections', []))}")
        else:
            print(f"   ❌ Gate rejected request (Status: {r.status_code})")
        return False
    except Exception as e:
        print(f"   ❌ Gate Connection Failed: {e}")
        return False

def wingman_log(worker_id, claim):
    """PHASE 3: Technical Truth Logger"""
    try:
        r = requests.post(f"{API_URL}/log_claim", json={"worker_id": worker_id, "claim": claim}, timeout=10)
        if r.status_code == 200:
            print(f"   📝 Logged: {claim[:60]}...")
        else:
            print(f"   ⚠️  Logging failed (Status: {r.status_code})")
    except Exception as e:
        print(f"   ⚠️  Logging failed: {e}")

def wingman_request_approval(worker_id, task_name, instruction, deployment_env="test"):
    """PHASE 4 (Original): Human Approval Layer"""
    print("\n🧑‍⚖️  WINGMAN APPROVAL (Phase 4): Requesting decision...")
    try:
        r = requests.post(
            f"{API_URL}/approvals/request",
            json={
                "worker_id": worker_id,
                "task_name": task_name,
                "instruction": instruction,
                "deployment_env": deployment_env,
            },
            timeout=10,
        )
        if r.status_code != 200:
            print(f"   ❌ Approval request failed (Status: {r.status_code})")
            return False
        res = r.json()
        if not res.get("needs_approval", False):
            print(f"   ✅ AUTO-APPROVED (risk={res.get('risk', {}).get('risk_level')})")
            return True

        req = res.get("request", {}) or {}
        request_id = req.get("request_id", "")
        risk = res.get("risk", {}) or {}
        print(f"   🟡 PENDING (risk={risk.get('risk_level')}) request_id={request_id}")
        wingman_log(worker_id, f"Approval requested: {request_id} (risk={risk.get('risk_level')})")
        print("")
        print("   To decide (in another terminal):")
        print(f"     curl -s -X POST {API_URL}/approvals/{request_id}/approve -H 'Content-Type: application/json' -d '{{\"decided_by\":\"mark\",\"note\":\"ok\"}}'")
        print(f"     curl -s -X POST {API_URL}/approvals/{request_id}/reject  -H 'Content-Type: application/json' -d '{{\"decided_by\":\"mark\",\"note\":\"no\"}}'")

        poll_sec = float(os.getenv("WINGMAN_APPROVAL_POLL_SEC", "2.0"))
        timeout_sec = float(os.getenv("WINGMAN_APPROVAL_TIMEOUT_SEC", "3600"))
        deadline = time.time() + timeout_sec

        try:
            while time.time() < deadline:
                time.sleep(poll_sec)
                g = requests.get(f"{API_URL}/approvals/{request_id}", timeout=10)
                if g.status_code != 200:
                    continue
                cur = g.json() or {}
                status = cur.get("status", "")
                if status == "APPROVED":
                    print("   ✅ APPROVED BY HUMAN")
                    wingman_log(worker_id, f"Approval granted: {request_id}")
                    return True
                if status == "REJECTED":
                    print("   🛑 REJECTED BY HUMAN")
                    wingman_log(worker_id, f"Approval rejected: {request_id}")
                    return False
        except KeyboardInterrupt:
            print("\n   ⛔ Interrupted while waiting for approval.")
            print(f"   Request remains pending: {request_id}")
            return False

        print("   ⏳ Approval timed out")
        wingman_log(worker_id, f"Approval timed out: {request_id}")
        return False

    except Exception as e:
        print(f"   ❌ Approval flow failed: {e}")
        return False

def simulate_worker(worker_id, task_name, instruction):
    print(f"\n{'='*70}\nWORKER {worker_id}: {task_name}\n{'='*70}")
    
    # 1. PHASE 2 GATE
    if not wingman_check(instruction):
        print(f"\n🛑 WORKER {worker_id} BLOCKED BY WINGMAN")
        return False

    # 2. PHASE 4 (Original) APPROVAL (before any execution)
    deployment_env = os.getenv("DEPLOYMENT_ENV", "dev")
    if not wingman_request_approval(worker_id, task_name, instruction, deployment_env=deployment_env):
        print(f"\n🛑 WORKER {worker_id} BLOCKED (Phase 4 approval)")
        return False

    # 3. PHASE 3 LOGGING (Start)
    wingman_log(worker_id, f"Started execution of {task_name}")

    # 4. Simulate Logic with Verifiable Claims
    print(f"\n⚙️  Executing worker logic...")
    
    # Create a real file to verify
    test_file = Path(BASE_DIR) / "data" / "worker_proof.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(f"Worker {worker_id} proof of work at {datetime.now()}")
    
    # Log claims that the simple_verifier can check
    wingman_log(worker_id, "Process postgres is running")
    wingman_log(worker_id, f"Created file {test_file}")
    
    # 5. PHASE 3 LOGGING (Complete)
    wingman_log(worker_id, f"Successfully completed Worker {worker_id}")
    
    print(f"\n✅ Worker {worker_id} complete.")
    return True

def main():
    print("=" * 70)
    print("WINGMAN SECURE PIPELINE: ORCHESTRATOR (Phase 2/3/4)")
    print(f"API_URL={API_URL}")
    print("=" * 70)
    
    # Instruction with all required sections
    valid_instruction = """
    DELIVERABLES: PostgreSQL Schema, worker_proof.txt
    SUCCESS_CRITERIA: File exists, Postgres running
    BOUNDARIES: environment appropriate
    DEPENDENCIES: postgres service
    MITIGATION: cleanup on failure
    TEST_PROCESS: run ls and pgrep
    TEST_RESULTS_FORMAT: text
    RESOURCE_REQUIREMENTS: low
    RISK_ASSESSMENT: Low
    QUALITY_METRICS: 100% verification
    """
    
    # Execute worker
    simulate_worker(1001, "Secure Data Task", valid_instruction)

if __name__ == "__main__":
    main()
