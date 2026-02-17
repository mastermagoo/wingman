# Wingman Client Integration Guide

**Purpose**: Integrate external systems (like intel-system, cv-automation, mem0) with Wingman approval flow
**Audience**: AI agents (Claude Code) working in client repositories
**Date**: 2026-02-17
**Updated**: Phase 6.1 Output Validation + Phase 6.2 Monitoring

---

## Overview

This guide shows how to integrate your system with Wingman as an **approval authority**. Wingman provides:

1. **Human-in-the-loop approval** for destructive operations
2. **Output validation** for AI-generated code (Phase 6.1)
3. **Claim verification** via semantic analyzer + watcher
4. **Worker quarantine** for compromised agents
5. **Audit trail** of all operations
6. **Real-time monitoring** via Prometheus/Grafana (Phase 6.2)

**Architecture**:
```
┌─────────────────────┐
│  Your System        │
│  (intel-system,     │
│   cv-automation,    │──┐
│   mem0, etc.)       │  │
└─────────────────────┘  │
                         │ HTTP API calls
                         ▼
┌─────────────────────────────────────┐
│  Wingman Approval Service           │
│  http://127.0.0.1:8101              │
│                                     │
│  - Approval flow (TEST: auto)      │
│  - Claim verification              │
│  - Worker quarantine               │
│  - Telegram notifications          │
└─────────────────────────────────────┘
           │
           ▼
    ┌──────────┐
    │ Telegram │
    │  (Mark)  │
    └──────────┘
```

---

## Prerequisites

### 1. Wingman Service Running

Wingman must be running (TEST or PRD stack):

```bash
# Check Wingman is running
curl -s http://127.0.0.1:8101/health | python3 -m json.tool

# Expected response:
{
  "status": "healthy",
  "phase": "6.1",
  "database": "memory",
  "validators": {
    "input_validation": "available",
    "output_validation": "available"
  },
  "verifiers": {
    "simple": "available",
    "enhanced": "unavailable"
  },
  "timestamp": "2026-02-17T..."
}
```

If not running, start Wingman TEST stack:
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman
docker compose -f docker-compose.yml -p wingman-test up -d
```

### 2. API Keys

Get API keys from Wingman `.env.test`:

```bash
# Read keys from Wingman
cat /Volumes/Data/ai_projects/wingman-system/wingman/.env.test | grep WINGMAN_APPROVAL
```

You'll need:
- `WINGMAN_APPROVAL_REQUEST_KEY` - Submit approval requests
- `WINGMAN_APPROVAL_READ_KEY` - Query approval status
- `WINGMAN_APPROVAL_DECIDE_KEY` - Approve/reject (optional - Mark uses this via Telegram)

---

## Environment Configuration (TEST vs PRD)

Wingman runs in two environments with different behavior and API endpoints.

### TEST Environment

**Purpose**: Development and testing
**API URL**: `http://127.0.0.1:8101`
**Behavior**: Most operations auto-approved for faster iteration
**API Keys**: From `/Volumes/Data/ai_projects/wingman-system/wingman/.env.test`

**Start TEST stack**:
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman
docker compose -f docker-compose.yml -p wingman-test up -d
```

**Health check**:
```bash
curl -s http://127.0.0.1:8101/health | python3 -m json.tool
```

**Get API keys**:
```bash
cat /Volumes/Data/ai_projects/wingman-system/wingman/.env.test | grep WINGMAN_APPROVAL_REQUEST_KEY
cat /Volumes/Data/ai_projects/wingman-system/wingman/.env.test | grep WINGMAN_APPROVAL_READ_KEY
```

### PRD Environment

**Purpose**: Production operations with strict approval controls
**API URL**: `http://127.0.0.1:5001`
**Behavior**: ALL destructive operations require Mark's manual approval via Telegram
**API Keys**: From `/Volumes/Data/ai_projects/wingman-system/wingman/.env.prd`

**Start PRD stack**:
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d
```

**Health check**:
```bash
curl -s http://127.0.0.1:5001/health | python3 -m json.tool
```

**Get API keys**:

```bash
# CRITICAL: Never commit .env.prd - it contains production secrets
cat /Volumes/Data/ai_projects/wingman-system/wingman/.env.prd | grep WINGMAN_APPROVAL_READ_KEY
```

### Which Environment to Use?

| Scenario                              | Environment | Auto-Approve                          |
| ------------------------------------- | ----------- | ------------------------------------- |
| Development, testing, experimentation | TEST        | ✅ Yes (most operations)              |
| Production deployments                | PRD         | ❌ No - requires Telegram approval    |
| FALSE claim testing                   | TEST        | ✅ Yes (but still triggers alerts)    |
| Real infrastructure changes           | PRD         | ❌ No - human approval required       |

**CRITICAL**: Both environments enforce claim verification via watcher. FALSE claims will trigger alerts and eventual quarantine in either environment.

---

## Integration Steps

### Step 1: Configure Your System

Add to your `.env` file (choose TEST or PRD configuration):

**For TEST environment** (`.env.test` or `.env`):

```bash
# Wingman Integration - TEST
WINGMAN_API_URL=http://127.0.0.1:8101
WINGMAN_APPROVAL_REQUEST_KEY=XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY
WINGMAN_APPROVAL_READ_KEY=XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY

# Your system identifier (for audit trail)
SYSTEM_NAME=intel-system  # or cv-automation, mem0, etc.
DEPLOYMENT_ENV=test
```

**For PRD environment** (`.env.prd`):

```bash
# Wingman Integration - PRD
WINGMAN_API_URL=http://127.0.0.1:5001
WINGMAN_APPROVAL_REQUEST_KEY=outgunning-web-serin-profounder-swans-globule
WINGMAN_APPROVAL_READ_KEY=outgunning-web-serin-profounder-swans-globule

# Your system identifier (for audit trail)
SYSTEM_NAME=intel-system  # or cv-automation, mem0, etc.
DEPLOYMENT_ENV=prd
```

**CRITICAL**: Get actual PRD keys from `/Volumes/Data/ai_projects/wingman-system/wingman/.env.prd`. NEVER commit `.env.prd` to git.

### Step 2: Create Wingman Client Library (Optional)

For cleaner integration, create a client library in your repo:

**File**: `wingman_client.py`

```python
#!/usr/bin/env python3
"""
Wingman Approval Client

Usage:
    from wingman_client import WingmanClient

    client = WingmanClient(
        api_url="http://127.0.0.1:8101",
        request_key="...",
        read_key="..."
    )

    # Submit approval request
    result = client.request_approval(
        worker_id="intel_deployer_001",
        task_name="Deploy intel-system to TEST",
        instruction="DELIVERABLES: Rebuild intel-api container...",
        claim="I will execute: docker compose up -d --build intel-api"
    )

    if result["auto_approved"]:
        # Execute with capability token
        client.execute_command("docker compose up -d --build intel-api", result["capability_token"])
    else:
        print("Waiting for approval...")
"""

import os
import requests
import time
from typing import Dict, Optional


class WingmanClient:
    """Client for Wingman approval service"""

    def __init__(
        self,
        api_url: str = None,
        request_key: str = None,
        read_key: str = None,
        system_name: str = None,
        deployment_env: str = "test"
    ):
        self.api_url = api_url or os.getenv("WINGMAN_API_URL", "http://127.0.0.1:8101")
        self.request_key = request_key or os.getenv("WINGMAN_APPROVAL_REQUEST_KEY")
        self.read_key = read_key or os.getenv("WINGMAN_APPROVAL_READ_KEY")
        self.system_name = system_name or os.getenv("SYSTEM_NAME", "unknown")
        self.deployment_env = deployment_env or os.getenv("DEPLOYMENT_ENV", "test")

        if not self.request_key or not self.read_key:
            raise ValueError("WINGMAN_APPROVAL_REQUEST_KEY and WINGMAN_APPROVAL_READ_KEY required")

    def request_approval(
        self,
        worker_id: str,
        task_name: str,
        instruction: str,
        claim: str = None,
        timeout_sec: int = 300
    ) -> Dict:
        """
        Submit approval request to Wingman.

        Returns:
            {
                "approval_id": "uuid",
                "needs_approval": true/false,
                "auto_approved": true/false,
                "status": "APPROVED" | "PENDING" | "REJECTED",
                "capability_token": "jwt_token" (if auto-approved),
                "reason": "..." (if rejected)
            }
        """
        url = f"{self.api_url}/approvals/request"

        payload = {
            "worker_id": f"{self.system_name}_{worker_id}",
            "task_name": task_name,
            "instruction": instruction,
            "deployment_env": self.deployment_env,
            "system": self.system_name
        }

        if claim:
            payload["claim"] = claim

        headers = {
            "Content-Type": "application/json",
            "X-Wingman-Approval-Request-Key": self.request_key
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # If needs approval, poll until approved/rejected or timeout
            if data.get("needs_approval") and data.get("status") == "PENDING":
                approval_id = data.get("approval_id")
                print(f"⏳ Approval request {approval_id} pending (check Telegram)")

                return self._wait_for_approval(approval_id, timeout_sec)

            return {
                "approval_id": data.get("approval_id"),
                "needs_approval": data.get("needs_approval", False),
                "auto_approved": data.get("status") == "APPROVED",
                "status": data.get("status"),
                "capability_token": data.get("capability_token"),
                "reason": data.get("reason")
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                # Worker is quarantined
                error_data = e.response.json()
                return {
                    "approval_id": None,
                    "needs_approval": False,
                    "auto_approved": False,
                    "status": "QUARANTINED",
                    "rejection_reason": error_data.get("rejection_reason", "WORKER_QUARANTINED"),
                    "capability_token": None,
                    "reason": error_data.get("reason", "Worker quarantined")
                }
            elif e.response.status_code == 422:
                # Validation failed
                error_data = e.response.json()
                return {
                    "approval_id": error_data.get("request", {}).get("request_id"),
                    "needs_approval": False,
                    "auto_approved": False,
                    "status": "VALIDATION_FAILED",
                    "rejection_reason": error_data.get("rejection_reason", "VALIDATION_FAILED"),
                    "capability_token": None,
                    "reason": error_data.get("validation", {}).get("reasoning", "Validation failed"),
                    "validation": error_data.get("validation")
                }
            raise

    def _wait_for_approval(self, approval_id: str, timeout_sec: int) -> Dict:
        """Poll approval status until approved/rejected or timeout"""
        url = f"{self.api_url}/approvals/{approval_id}"
        headers = {"X-Wingman-Approval-Read-Key": self.read_key}

        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            try:
                response = requests.get(url, headers=headers, timeout=5)
                response.raise_for_status()
                data = response.json()

                status = data.get("status")
                if status == "APPROVED":
                    print(f"✅ Approval {approval_id} APPROVED")
                    return {
                        "approval_id": approval_id,
                        "needs_approval": True,
                        "auto_approved": False,
                        "status": "APPROVED",
                        "capability_token": data.get("capability_token"),
                        "reason": None
                    }
                elif status == "REJECTED":
                    print(f"❌ Approval {approval_id} REJECTED")
                    return {
                        "approval_id": approval_id,
                        "needs_approval": True,
                        "auto_approved": False,
                        "status": "REJECTED",
                        "capability_token": None,
                        "reason": data.get("reason", "Rejected by operator")
                    }

                # Still pending, wait and retry
                time.sleep(5)

            except Exception as e:
                print(f"⚠️ Error polling approval status: {e}")
                time.sleep(5)

        # Timeout
        print(f"⏱️ Approval {approval_id} timed out after {timeout_sec}s")
        return {
            "approval_id": approval_id,
            "needs_approval": True,
            "auto_approved": False,
            "status": "TIMEOUT",
            "capability_token": None,
            "reason": f"Approval request timed out after {timeout_sec}s"
        }

    def execute_command(self, command: str, capability_token: str) -> Dict:
        """
        Execute command via Wingman Execution Gateway.

        Args:
            command: Shell command to execute
            capability_token: JWT token from approval response

        Returns:
            {
                "success": true/false,
                "output": "...",
                "exit_code": 0
            }
        """
        url = f"{self.api_url}/execute"
        headers = {
            "Authorization": f"Bearer {capability_token}",
            "Content-Type": "application/json"
        }
        payload = {"command": command}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "output": str(e),
                "exit_code": 1
            }

    def get_pending_approvals(self) -> list:
        """Get all pending approval requests"""
        url = f"{self.api_url}/approvals/pending"
        headers = {"X-Wingman-Approval-Read-Key": self.read_key}

        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    client = WingmanClient(
        system_name="intel-system",
        deployment_env="test"
    )

    # Request approval for docker rebuild
    result = client.request_approval(
        worker_id="deployer_001",
        task_name="Rebuild intel-api container",
        instruction="DELIVERABLES: Rebuild intel-api container with latest changes. VALIDATION: Container running and healthy.",
        claim="I will execute: docker compose -f docker-compose.yml up -d --build intel-api"
    )

    print(f"Status: {result['status']}")
    print(f"Auto-approved: {result['auto_approved']}")

    if result["status"] == "APPROVED":
        # Execute command
        exec_result = client.execute_command(
            "docker compose -f docker-compose.yml up -d --build intel-api",
            result["capability_token"]
        )
        print(f"Execution result: {exec_result}")
    elif result["status"] == "QUARANTINED":
        print(f"⚠️ Worker is quarantined: {result['reason']}")
    elif result["status"] == "REJECTED":
        print(f"❌ Request rejected: {result['reason']}")
```

### Step 3: Update Your CLAUDE.md (Client System)

Add Wingman integration rules to your system's CLAUDE.md:

```markdown
## Wingman Integration (Approval Authority)

**CRITICAL**: This system uses Wingman as the approval authority for destructive operations.

### When to Request Approval

**ALWAYS request Wingman approval before**:
- Docker operations: stop, rm, down, build, restart
- Database changes: DROP, TRUNCATE, ALTER, DELETE
- File deletions: rm -rf, rm -f
- Production deployments
- System configuration changes

**DO NOT execute destructive operations without approval**

### How to Request Approval

1. Use `WingmanClient` library:
   ```python
   from wingman_client import WingmanClient

   client = WingmanClient(system_name="intel-system")
   result = client.request_approval(
       worker_id="your_worker_id",
       task_name="What you're doing",
       instruction="DELIVERABLES: ...",
       claim="I will execute: <command>"
   )

   if result["status"] == "APPROVED":
       # Execute via gateway
       client.execute_command("<command>", result["capability_token"])
   ```

2. Or use curl:
   ```bash
   curl -X POST http://127.0.0.1:8101/approvals/request \
     -H "Content-Type: application/json" \
     -H "X-Wingman-Approval-Request-Key: $WINGMAN_APPROVAL_REQUEST_KEY" \
     -d '{"worker_id": "intel_deployer", "task_name": "...", ...}'
   ```

### Claim Verification

**IMPORTANT**: Wingman will verify your claims against actual system state.

**Always be truthful**:
- ✅ Claim: "I will execute: docker stop container"
- ❌ FALSE claim: "I executed: docker stop container" (when you didn't)

**If you make a FALSE claim**:
- Wingman watcher detects it
- You receive a MEDIUM severity alert (TEST) or CRITICAL (PRD)
- Repeated FALSE claims → automatic quarantine
- Quarantined workers cannot request approvals

### Deployment Environment

Set `DEPLOYMENT_ENV` in your `.env`:
- `test` - auto-approves most operations (for development)
- `prd` - requires human approval for all destructive operations
```

---

## Testing the Integration

### Test 1: Simple Approval Request

```bash
# From your system (e.g., intel-system)
curl -X POST http://127.0.0.1:8101/approvals/request \
  -H "Content-Type: application/json" \
  -H "X-Wingman-Approval-Request-Key: XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY" \
  -d '{
    "worker_id": "intel_test_001",
    "task_name": "Test Wingman Integration",
    "instruction": "DELIVERABLES: Test approval flow. VALIDATION: Request succeeds.",
    "deployment_env": "test",
    "claim": "I will test the approval system"
  }' | python3 -m json.tool
```

**Expected (TEST environment)**:
```json
{
  "approval_id": "uuid",
  "needs_approval": false,
  "auto_approved": true,
  "status": "APPROVED",
  "capability_token": "jwt_token",
  "expires_at": "..."
}
```

### Test 2: Execute Command via Gateway

```bash
# Use capability_token from above
curl -X POST http://127.0.0.1:8101/execute \
  -H "Authorization: Bearer $CAPABILITY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "echo Hello from intel-system"}' | python3 -m json.tool
```

**Expected**:
```json
{
  "success": true,
  "output": "Hello from intel-system\n",
  "exit_code": 0
}
```

### Test 3: Trigger FALSE Claim Detection

```bash
# Make a FALSE claim (claim you did something but don't actually do it)
curl -X POST http://127.0.0.1:8101/approvals/request \
  -H "Content-Type: application/json" \
  -H "X-Wingman-Approval-Request-Key: XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY" \
  -d '{
    "worker_id": "intel_test_false_claim",
    "task_name": "Test FALSE Claim Detection",
    "instruction": "DELIVERABLES: Stop intel-api container",
    "deployment_env": "test",
    "claim": "I executed: docker stop intel-api (but I did not actually execute this)"
  }' | python3 -m json.tool

# Check Wingman watcher logs for alert
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test logs --tail=20 wingman-watcher
```

**Expected**:
- Telegram alert sent to Mark
- Alert persisted in database
- If repeated → worker quarantined

### Test 4: Quarantine Enforcement

```bash
# Manually quarantine a test worker
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec -T redis redis-cli SADD quarantined_workers intel_test_quarantined

# Try to request approval
curl -X POST http://127.0.0.1:8101/approvals/request \
  -H "Content-Type: application/json" \
  -H "X-Wingman-Approval-Request-Key: XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY" \
  -d '{
    "worker_id": "intel_test_quarantined",
    "task_name": "Test Quarantine Block",
    "instruction": "DELIVERABLES: Test if quarantine blocks approval",
    "deployment_env": "test"
  }'
```

**Expected**:
```json
{
  "needs_approval": false,
  "status": "AUTO_REJECTED",
  "reason": "Worker quarantined: ...",
  "message": "Contact Mark to release this worker"
}
```

HTTP Status: **403 Forbidden**

---

## HTTP Status Codes and Rejection Reasons

Wingman uses different HTTP status codes to distinguish between rejection types:

### 403 Forbidden - Worker Quarantined

**When**: Worker has been quarantined by Watcher due to suspicious behavior

**Response**:
```json
{
  "needs_approval": false,
  "status": "AUTO_REJECTED",
  "rejection_reason": "WORKER_QUARANTINED",
  "reason": "Worker quarantined: Repeated validation failures",
  "quarantined_at": "2026-02-16T10:30:00Z",
  "environment": "test",
  "message": "Contact Mark to release this worker via /release_worker command or POST /watcher/release/{worker_id}"
}
```

**Client Handling**:
- Worker is actively blocked and cannot make further requests
- Contact system administrator (Mark) to investigate and release
- Do NOT retry - quarantine must be manually lifted

### 422 Unprocessable Entity - Validation Failed

**When**: Instruction content failed validation (secrets found, low quality, dangerous patterns)

**Response**:
```json
{
  "needs_approval": false,
  "status": "AUTO_REJECTED",
  "rejection_reason": "VALIDATION_FAILED",
  "request": { /* approval request details */ },
  "validation": {
    "overall_score": 45,
    "recommendation": "REJECT",
    "risk_level": "CRITICAL",
    "reasoning": "Code scanner found secrets; immediate reject.",
    "validator_scores": {
      "code_scanner": 10,
      "content_quality": 55,
      "dependency_analyzer": 60,
      "semantic_analyzer": 75
    },
    "profile": "deployment",
    "active_validators": ["code_scanner", "content_quality", "dependency_analyzer", "semantic_analyzer"]
  }
}
```

**Client Handling**:
- Instruction content needs improvement (see validation details)
- Review `validation.reasoning` for specific issues
- Check `validation.validator_scores` to identify weak areas
- Fix the instruction and retry
- Common issues:
  - Secrets/credentials in instruction text (code_scanner)
  - Missing or vague 10-point framework sections (content_quality)
  - High-risk dependencies without mitigation (dependency_analyzer)
  - Ambiguous or dangerous intent (semantic_analyzer)

### 200 OK - Auto-Approved or Pending

**Auto-Approved (TEST environment)**:
```json
{
  "needs_approval": false,
  "status": "AUTO_APPROVED",
  "approval_id": "uuid",
  "auto_approved": true,
  "capability_token": "jwt_token_here"
}
```

**Pending Manual Review (PRD environment)**:
```json
{
  "needs_approval": true,
  "status": "PENDING",
  "approval_id": "uuid",
  "message": "Approval request sent to Mark via Telegram"
}
```

### Client Code Pattern

```python
response = requests.post(
    f"{WINGMAN_API_URL}/approvals/request",
    headers={"X-Wingman-Approval-Request-Key": REQUEST_KEY},
    json=approval_request
)

if response.status_code == 403:
    data = response.json()
    if data.get("rejection_reason") == "WORKER_QUARANTINED":
        print(f"❌ Worker quarantined: {data.get('reason')}")
        print(f"⚠️ Contact administrator to investigate and release worker")
        sys.exit(1)

elif response.status_code == 422:
    data = response.json()
    if data.get("rejection_reason") == "VALIDATION_FAILED":
        validation = data.get("validation", {})
        print(f"❌ Validation failed: {validation.get('reasoning')}")
        print(f"📊 Overall score: {validation.get('overall_score')}/100")
        print(f"🔍 Validator scores:")
        for validator, score in validation.get("validator_scores", {}).items():
            print(f"  - {validator}: {score}")
        print(f"💡 Fix the instruction content and retry")
        sys.exit(1)

elif response.status_code == 200:
    data = response.json()
    if data.get("status") == "AUTO_APPROVED":
        print(f"✅ Auto-approved: {data.get('approval_id')}")
        # Use capability_token for execution
    elif data.get("status") == "PENDING":
        print(f"⏳ Pending approval: {data.get('approval_id')}")
        # Poll for approval
```

---

## Real-World Usage Example (Intel-System)

### Scenario: Deploy Intel-System to TEST

**File**: `intel-system/deploy.sh`

```bash
#!/bin/bash
set -euo pipefail

# Load Wingman client
source .env

echo "🚀 Deploying intel-system to TEST..."

# Request approval from Wingman
APPROVAL_RESPONSE=$(curl -s -X POST http://127.0.0.1:8101/approvals/request \
  -H "Content-Type: application/json" \
  -H "X-Wingman-Approval-Request-Key: $WINGMAN_APPROVAL_REQUEST_KEY" \
  -d '{
    "worker_id": "intel_deployer_manual",
    "task_name": "Deploy intel-system to TEST",
    "instruction": "DELIVERABLES: Rebuild intel-api and intel-worker containers with latest code. VALIDATION: Containers running and healthy, API responding.",
    "deployment_env": "test",
    "claim": "I will execute: docker compose -f docker-compose.yml -p intel-test up -d --build intel-api intel-worker"
  }')

STATUS=$(echo $APPROVAL_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'UNKNOWN'))")

if [[ "$STATUS" == "APPROVED" ]]; then
  echo "✅ Approval granted"

  # Extract capability token
  TOKEN=$(echo $APPROVAL_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('capability_token', ''))")

  # Execute via Wingman gateway
  curl -X POST http://127.0.0.1:8101/execute \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"command": "cd /Volumes/Data/ai_projects/intel-system && docker compose -f docker-compose.yml -p intel-test up -d --build intel-api intel-worker"}'

  echo "✅ Deployment complete"
elif [[ "$STATUS" == "PENDING" ]]; then
  echo "⏳ Waiting for approval (check Telegram)..."
  APPROVAL_ID=$(echo $APPROVAL_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('approval_id', ''))")
  echo "   Approval ID: $APPROVAL_ID"
  echo "   Poll status: curl http://127.0.0.1:8101/approvals/$APPROVAL_ID"
elif [[ "$STATUS" == "REJECTED" ]]; then
  echo "❌ Deployment rejected"
  exit 1
elif [[ "$STATUS" == "QUARANTINED" ]]; then
  echo "⚠️ Worker is quarantined - cannot deploy"
  exit 1
else
  echo "❌ Unknown approval status: $STATUS"
  exit 1
fi
```

---

## API Reference

### POST /approvals/request

Submit approval request.

**Headers**:
- `X-Wingman-Approval-Request-Key`: API key

**Body**:
```json
{
  "worker_id": "string (required)",
  "task_name": "string (required)",
  "instruction": "string (required - DELIVERABLES format)",
  "deployment_env": "test | prd (required)",
  "claim": "string (optional - what you claim to have done/will do)",
  "system": "string (optional - your system name)"
}
```

**Response (200 OK - Auto-approved)**:
```json
{
  "approval_id": "uuid",
  "needs_approval": false,
  "status": "APPROVED",
  "capability_token": "jwt_token",
  "expires_at": "iso_timestamp"
}
```

**Response (202 Accepted - Pending)**:
```json
{
  "approval_id": "uuid",
  "needs_approval": true,
  "status": "PENDING",
  "message": "Approval request sent to Mark via Telegram"
}
```

**Response (403 Forbidden - Quarantined)**:
```json
{
  "needs_approval": false,
  "status": "AUTO_REJECTED",
  "reason": "Worker quarantined: ...",
  "message": "Contact Mark to release this worker"
}
```

### GET /approvals/{approval_id}

Get approval status.

**Headers**:
- `X-Wingman-Approval-Read-Key`: API key

**Response**:
```json
{
  "approval_id": "uuid",
  "status": "PENDING | APPROVED | REJECTED",
  "capability_token": "jwt_token (if approved)",
  "reason": "string (if rejected)"
}
```

### POST /execute

Execute command (requires capability token).

**Headers**:
- `Authorization: Bearer {capability_token}`

**Body**:
```json
{
  "command": "string (shell command to execute)"
}
```

**Response**:
```json
{
  "success": true,
  "output": "command output",
  "exit_code": 0
}
```

---

## Phase 6.1: Output Validation

**Added**: 2026-02-16

If your AI workers generate code, use output validation BEFORE deployment to ensure code quality and security.

### Endpoint: `POST /output_validation/validate`

```python
import requests

response = requests.post(
    "http://127.0.0.1:8101/output_validation/validate",
    json={
        "worker_id": "YOUR_WORKER_ID",
        "generated_files": [
            "/path/to/generated_file1.py",
            "/path/to/generated_file2.py"
        ],
        "task_name": "Generate backup script"
    }
)

result = response.json()

if result['status'] == 'APPROVED':
    # Code passed all validators - safe to deploy
    print("✅ Code validation passed")
    print(f"Score: {result['validation_report']['overall_score']}")

elif result['status'] == 'REJECTED':
    # Code has blocking issues - DO NOT deploy
    print("❌ Code validation failed")
    print(f"Issues: {result['validation_report']['blocking_issues']}")

else:  # PENDING
    # Code needs manual review
    print("⏳ Code requires manual review")
    print(f"Approval ID: {result['approval_id']}")
```

### Validation Pipeline

Code goes through 5 validators:

1. **SyntaxValidator**: Python syntax checking
2. **OutputSecurityScanner**: Security pattern detection (secrets, SQL injection, etc.)
3. **DependencyVerifier**: Import validation and dependency checking
4. **TestExecutor**: Automated test execution (if tests exist)
5. **OutputCompositeValidator**: Aggregates results and makes decision

### Decision Logic

- **AUTO_APPROVE**: Score >= 70, no blocking issues
- **AUTO_REJECT**: Score < 50 OR blocking issues (syntax errors, secrets, critical security issues)
- **MANUAL_REVIEW**: Score 50-69 OR non-blocking concerns

**Full Documentation**: [OUTPUT_VALIDATION_USER_GUIDE.md](OUTPUT_VALIDATION_USER_GUIDE.md)

---

## Phase 6.2: Monitoring & Observability

**Added**: 2026-02-17

Real-time metrics and dashboards for Wingman system health and performance.

### Prometheus Metrics

Access metrics at: `http://localhost:8101/metrics`

Available metrics:
- `wingman_health_status` - Overall health (1=healthy, 0=unhealthy)
- `wingman_verifier_available` - Verifier availability by type
- `wingman_validator_available` - Validator availability by type
- `wingman_database_connected` - Database connection status
- `wingman_start_time_seconds` - Process start time

### Grafana Dashboards

Access dashboards at: `http://localhost:3333` (login: admin/admin)

Pre-configured datasource connects to Prometheus automatically.

### Monitoring Your Integrations

Track your system's interaction with Wingman:

```promql
# Query approval request rate for your system
rate(wingman_approval_requests_total{system="intel-system"}[5m])

# Check approval success rate
wingman_approvals_approved_total / wingman_approval_requests_total

# Monitor validation scores
histogram_quantile(0.95, wingman_validation_score_bucket)
```

**Full Documentation**: [PROMETHEUS_GRAFANA_MONITORING_GUIDE.md](PROMETHEUS_GRAFANA_MONITORING_GUIDE.md)

---

## Troubleshooting

### Issue: Connection refused

**Symptom**: `Connection refused` when calling Wingman API

**Fix**:
```bash
# Check Wingman is running
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test ps

# If not running, start it
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test up -d
```

### Issue: 401 Unauthorized

**Symptom**: `401 Unauthorized` response

**Fix**: Check API key is correct
```bash
# Get correct key from Wingman
cat /Volumes/Data/ai_projects/wingman-system/wingman/.env.test | grep WINGMAN_APPROVAL_REQUEST_KEY
```

### Issue: Worker quarantined unexpectedly

**Symptom**: All requests return 403 Forbidden

**Check quarantine status**:
```bash
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec -T redis redis-cli SMEMBERS quarantined_workers
```

**Release worker**:
```bash
curl -X POST http://127.0.0.1:8101/watcher/release/your_worker_id \
  -H "X-Wingman-Approval-Read-Key: $WINGMAN_APPROVAL_READ_KEY" \
  -H "Content-Type: application/json" \
  -d '{"released_by": "operator", "reason": "False alarm"}'
```

---

## Next Steps

1. ✅ Copy `wingman_client.py` to your system
2. ✅ Add Wingman config to your `.env`
3. ✅ Update your CLAUDE.md with integration rules
4. ✅ Test approval flow (see Testing section)
5. ✅ Update deployment scripts to use Wingman

**Ready to integrate?** Start with Test 1 above to verify connectivity.

---

**End of Integration Guide**
