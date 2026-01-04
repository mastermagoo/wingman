#!/usr/bin/env python3
"""
Proper Wingman Deployment - PHASE 3 INTEGRATED (Mac Studio PRD)
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

# Configuration for Mac Studio PRD Environment
BASE_DIR = Path(__file__).parent
API_URL = "http://localhost:5001"  # PRD Port (Moved from 5000 due to AirTunes conflict)
# PRD Data path on Mac Studio
PRD_DATA_DIR = "/Volumes/Data/ai_projects/intel-system/wingman/data/prd"

def wingman_contract_gate(label: str = "PRD") -> bool:
    """
    Unavoidable gate for any "complete" claim in PRD:
    - API health must be healthy
    - Core API contracts must respond with expected JSON shape
    """
    print(f"\n🔒 WINGMAN CONTRACT GATE ({label}): validating system health + API contracts...")
    try:
        r = requests.get(f"{API_URL}/health", timeout=10)
        if r.status_code != 200:
            print(f"   ❌ /health HTTP {r.status_code}")
            return False
        j = r.json()
        if j.get("status") != "healthy":
            print(f"   ❌ /health status not healthy: {j.get('status')}")
            return False

        good_instruction = (
            "DELIVERABLES: x\nSUCCESS_CRITERIA: x\nBOUNDARIES: x\nDEPENDENCIES: x\nMITIGATION: x\n"
            "TEST_PROCESS: x\nTEST_RESULTS_FORMAT: x\nRESOURCE_REQUIREMENTS: x\nRISK_ASSESSMENT: x\nQUALITY_METRICS: x\n"
        )
        r = requests.post(f"{API_URL}/check", json={"instruction": good_instruction}, timeout=10)
        if r.status_code != 200:
            print(f"   ❌ /check HTTP {r.status_code}")
            return False
        j = r.json()
        for k in ("approved", "score", "missing_sections", "policy_checks"):
            if k not in j:
                print(f"   ❌ /check missing key: {k}")
                return False

        r = requests.post(f"{API_URL}/verify", json={"claim": "contract probe"}, timeout=10)
        if r.status_code != 200:
            print(f"   ❌ /verify HTTP {r.status_code}")
            return False
        j = r.json()
        for k in ("verdict", "verifier", "processing_time_ms", "timestamp"):
            if k not in j:
                print(f"   ❌ /verify missing key: {k}")
                return False
        if j.get("verdict") not in ("TRUE", "FALSE", "UNVERIFIABLE", "ERROR"):
            print(f"   ❌ /verify unexpected verdict: {j.get('verdict')}")
            return False

        print("   ✅ Contract gate passed")
        return True
    except Exception as e:
        print(f"   ❌ Contract gate failed: {e}")
        return False

def wingman_check(instruction_text):
    """PHASE 2: Instruction Gate"""
    print(f"\n🛡️  WINGMAN GATE (PRD): Validating instruction...")
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

def wingman_request_approval(worker_id, task_name, instruction, deployment_env="prd"):
    """PHASE 4 (Original): Human Approval Layer (always required in PRD by default)."""
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

        poll_sec = float(os.getenv("WINGMAN_APPROVAL_POLL_SEC", "2.0"))
        timeout_sec = float(os.getenv("WINGMAN_APPROVAL_TIMEOUT_SEC", "86400"))
        deadline = time.time() + timeout_sec

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

        print("   ⏳ Approval timed out")
        wingman_log(worker_id, f"Approval timed out: {request_id}")
        return False

    except Exception as e:
        print(f"   ❌ Approval flow failed: {e}")
        return False

def simulate_worker(worker_id, task_name, instruction):
    print(f"\n{'='*70}\nWORKER {worker_id} (PRD): {task_name}\n{'='*70}")
    
    # 0. CONTRACT GATE (system health + API contracts)
    if not wingman_contract_gate(label="PRE"):
        print(f"\n🛑 WORKER {worker_id} BLOCKED (contract gate)")
        return False

    # 1. PHASE 2 GATE
    if not wingman_check(instruction):
        print(f"\n🛑 WORKER {worker_id} BLOCKED BY WINGMAN")
        return False

    # 2. PHASE 4 (Original) APPROVAL (before any execution)
    if not wingman_request_approval(worker_id, task_name, instruction, deployment_env="prd"):
        print(f"\n🛑 WORKER {worker_id} BLOCKED (Phase 4 approval)")
        return False

    # 3. PHASE 3 LOGGING (Start)
    wingman_log(worker_id, f"Started execution of {task_name}")

    # 3. Simulate Logic with Verifiable Claims
    print(f"\n⚙️  Executing PRD worker logic...")
    
    # Create a real file in the PRD volume to verify
    test_file = Path(PRD_DATA_DIR) / "prd_worker_proof.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(f"Worker {worker_id} PRD proof of work at {datetime.now()}")
    
    # Log verifiable claims
    wingman_log(worker_id, "Process postgres is running")
    # Path inside container for verification
    wingman_log(worker_id, f"Created file data/prd_worker_proof.txt")
    
    # 4. PHASE 3 LOGGING (Complete)
    wingman_log(worker_id, f"Successfully completed Worker {worker_id} (PRD)")
    
    # Final contract gate before any "complete" claim
    if not wingman_contract_gate(label="POST"):
        print(f"\n🛑 WORKER {worker_id} NOT MARKED COMPLETE (contract gate failed)")
        wingman_log(worker_id, f"Completion blocked: contract gate failed for Worker {worker_id}")
        return False

    print(f"\n✅ Worker {worker_id} complete and verified in PRD (gates passed).")
    return True

def main():
    print("=" * 70)
    print("WINGMAN SECURE PIPELINE: MAC STUDIO PRD VERIFICATION")
    print("=" * 70)
    
    valid_instruction = """
    DELIVERABLES: PostgreSQL PRD Schema, prd_worker_proof.txt
    SUCCESS_CRITERIA: File exists, Postgres running
    BOUNDARIES: production environment
    DEPENDENCIES: postgres-prd service
    MITIGATION: manual intervention
    TEST_PROCESS: run ls and pgrep
    TEST_RESULTS_FORMAT: text
    RESOURCE_REQUIREMENTS: medium
    RISK_ASSESSMENT: High (PROD)
    QUALITY_METRICS: 100% verification
    """
    
    simulate_worker(2001, "PRD Security Task", valid_instruction)

if __name__ == "__main__":
    main()


