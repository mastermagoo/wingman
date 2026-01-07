# How to Use Wingman

> **Audience**: Developers integrating external services (intel-system, mem0, cv-automation, or any AI worker)

This guide shows you how to integrate your service with Wingman's verification and governance system.

---

## Quick Reference

| Environment | API URL | Purpose |
|-------------|---------|---------|
| **DEV** (MBP) | `http://127.0.0.1:8002` | Development & prototyping |
| **TEST** (Mac Studio) | `http://127.0.0.1:8101` | High-fidelity validation |
| **PRD** (Mac Studio) | `http://127.0.0.1:5001` | Live secure operations |

---

## What Wingman Does

Wingman is a **governance layer** for AI workers. It provides:

1. **Instruction Validation** (Phase 2) — Blocks work that doesn't meet the 10-point framework
2. **Claims Logging** (Phase 3) — Records every "I did X" claim for audit
3. **Truth Verification** (Phase 3) — Checks if claims match reality
4. **Human Approval** (Phase 4) — Requires human sign-off for high-risk operations

---

## Integration Patterns

### Pattern 1: Simple Verification (Any Service)

Your service makes a claim → Wingman verifies it's true.

```python
import requests

WINGMAN_URL = "http://127.0.0.1:5001"  # PRD

# After your service does something, verify the claim
response = requests.post(f"{WINGMAN_URL}/verify", json={
    "claim": "Created backup file at /data/backup.tar",
    "use_enhanced": False  # Use simple verifier (faster)
})

result = response.json()
# {
#   "verdict": "TRUE",  # or "FALSE" or "UNVERIFIABLE"
#   "verifier": "simple",
#   "processing_time_ms": 12,
#   "timestamp": "2026-01-06T10:30:00"
# }

if result["verdict"] == "FALSE":
    # The claim was a lie - handle accordingly
    raise Exception("Verification failed!")
```

### Pattern 2: Instruction Gate (Before Execution)

Before running risky operations, validate the instruction meets security standards.

```python
import requests

WINGMAN_URL = "http://127.0.0.1:5001"

# Your instruction MUST include all 10 required sections
instruction = """
DELIVERABLES: Export user data to CSV
SUCCESS_CRITERIA: CSV file contains all active users
BOUNDARIES: Read-only database access, no PII in logs
DEPENDENCIES: Database connection, disk space
MITIGATION: Rollback on failure, notify admin
TEST_PROCESS: Verify row count matches source
TEST_RESULTS_FORMAT: JSON summary
RESOURCE_REQUIREMENTS: 2GB RAM, 500MB disk
RISK_ASSESSMENT: Medium - involves user data
QUALITY_METRICS: 100% row accuracy
"""

response = requests.post(f"{WINGMAN_URL}/check", json={
    "instruction": instruction
})

result = response.json()
# {
#   "approved": true,
#   "score": 100,
#   "missing_sections": [],
#   "policy_checks": {"no_force_flags": true, "no_hardcoded_secrets": true}
# }

if not result["approved"]:
    print(f"BLOCKED: Missing {result['missing_sections']}")
    exit(1)

# Proceed with execution...
```

### Pattern 3: Claims Audit Trail (During Execution)

Log every significant action for audit purposes.

```python
import requests

WINGMAN_URL = "http://127.0.0.1:5001"
WORKER_ID = "intel-system-extractor-01"

def log_claim(claim: str):
    """Log a claim to Wingman's audit trail"""
    requests.post(f"{WINGMAN_URL}/log_claim", json={
        "worker_id": WORKER_ID,
        "claim": claim
    })

# During your execution, log what you're doing
log_claim("Started email extraction batch job")
log_claim("Processed 150 emails from inbox")
log_claim("Created summary file at /data/summaries/2026-01-06.json")
log_claim("Completed email extraction batch job")
```

### Pattern 4: Human Approval Gate (High-Risk Operations)

For dangerous operations, require human approval before proceeding.

```python
import requests
import time
import os

WINGMAN_URL = "http://127.0.0.1:5001"

def request_approval(worker_id: str, task_name: str, instruction: str) -> bool:
    """Request human approval and wait for decision"""
    
    response = requests.post(f"{WINGMAN_URL}/approvals/request", json={
        "worker_id": worker_id,
        "task_name": task_name,
        "instruction": instruction,
        "deployment_env": os.getenv("DEPLOYMENT_ENV", "dev")
    })
    
    result = response.json()
    
    # Low-risk operations are auto-approved
    if not result.get("needs_approval"):
        print(f"Auto-approved (risk: {result['risk']['risk_level']})")
        return True
    
    # High-risk needs human decision
    request_id = result["request"]["request_id"]
    print(f"Waiting for approval: {request_id}")
    print(f"Risk: {result['risk']['risk_level']} - {result['risk']['risk_reason']}")
    
    # Poll for decision (human approves via Telegram or API)
    timeout = 3600  # 1 hour
    start = time.time()
    
    while time.time() - start < timeout:
        status_response = requests.get(f"{WINGMAN_URL}/approvals/{request_id}")
        status = status_response.json().get("status")
        
        if status == "APPROVED":
            print("✅ Approved by human")
            return True
        elif status == "REJECTED":
            print("❌ Rejected by human")
            return False
        
        time.sleep(2)  # Poll every 2 seconds
    
    print("⏳ Approval timed out")
    return False

# Example: Database migration requires approval
if request_approval(
    worker_id="intel-system-migrator",
    task_name="Database schema migration",
    instruction="ALTER TABLE users ADD COLUMN verified BOOLEAN DEFAULT FALSE"
):
    # Proceed with migration
    run_migration()
else:
    print("Migration blocked - approval denied or timed out")
```

---

## Complete Integration Example

Here's a full example showing all patterns together:

```python
#!/usr/bin/env python3
"""
Example: Intel System Email Processor with Wingman Integration
"""

import requests
import os
from datetime import datetime

class WingmanClient:
    """Reusable Wingman API client"""
    
    def __init__(self, api_url: str = None):
        self.api_url = api_url or os.getenv("WINGMAN_URL", "http://127.0.0.1:5001")
        self.worker_id = os.getenv("WORKER_ID", "unknown-worker")
    
    def health_check(self) -> bool:
        """Check if Wingman is available"""
        try:
            r = requests.get(f"{self.api_url}/health", timeout=5)
            return r.status_code == 200 and r.json().get("status") == "healthy"
        except:
            return False
    
    def check_instruction(self, instruction: str) -> dict:
        """Validate instruction against 10-point framework"""
        r = requests.post(f"{self.api_url}/check", json={"instruction": instruction}, timeout=10)
        return r.json()
    
    def log_claim(self, claim: str):
        """Log a claim to audit trail"""
        requests.post(f"{self.api_url}/log_claim", json={
            "worker_id": self.worker_id,
            "claim": claim
        }, timeout=10)
    
    def verify_claim(self, claim: str) -> str:
        """Verify a claim and return verdict"""
        r = requests.post(f"{self.api_url}/verify", json={"claim": claim}, timeout=10)
        return r.json().get("verdict", "ERROR")
    
    def request_approval(self, task_name: str, instruction: str) -> bool:
        """Request approval for high-risk operation"""
        r = requests.post(f"{self.api_url}/approvals/request", json={
            "worker_id": self.worker_id,
            "task_name": task_name,
            "instruction": instruction,
            "deployment_env": os.getenv("DEPLOYMENT_ENV", "dev")
        }, timeout=10)
        
        result = r.json()
        if not result.get("needs_approval"):
            return True
        
        # Poll for approval
        request_id = result["request"]["request_id"]
        import time
        for _ in range(1800):  # 1 hour max
            time.sleep(2)
            status_r = requests.get(f"{self.api_url}/approvals/{request_id}", timeout=10)
            status = status_r.json().get("status")
            if status == "APPROVED":
                return True
            if status == "REJECTED":
                return False
        return False


def main():
    # Initialize Wingman client
    wingman = WingmanClient()
    wingman.worker_id = "intel-system-email-processor"
    
    # 1. Check Wingman is available
    if not wingman.health_check():
        print("❌ Wingman unavailable - cannot proceed")
        return
    
    # 2. Validate instruction before starting
    instruction = """
    DELIVERABLES: Process inbox emails, generate daily summary
    SUCCESS_CRITERIA: All unread emails processed, summary file created
    BOUNDARIES: Read-only email access, no sending
    DEPENDENCIES: IMAP connection, disk space
    MITIGATION: Skip failed emails, continue processing
    TEST_PROCESS: Verify email count matches IMAP
    TEST_RESULTS_FORMAT: JSON summary
    RESOURCE_REQUIREMENTS: 1GB RAM
    RISK_ASSESSMENT: Low - read-only operation
    QUALITY_METRICS: 95% email processing success rate
    """
    
    check_result = wingman.check_instruction(instruction)
    if not check_result.get("approved"):
        print(f"❌ Instruction rejected: {check_result.get('missing_sections')}")
        return
    
    print("✅ Instruction approved")
    
    # 3. Request approval (will auto-approve for low-risk)
    if not wingman.request_approval("Email Processing", instruction):
        print("❌ Approval denied")
        return
    
    # 4. Execute with logging
    wingman.log_claim("Started email processing job")
    
    # ... your actual email processing logic here ...
    emails_processed = 150
    summary_path = f"/data/summaries/{datetime.now().strftime('%Y-%m-%d')}.json"
    
    wingman.log_claim(f"Processed {emails_processed} emails")
    wingman.log_claim(f"Created summary file at {summary_path}")
    
    # 5. Verify our claims
    verdict = wingman.verify_claim(f"Created file {summary_path}")
    if verdict == "FALSE":
        print("⚠️ Verification failed - summary file not found!")
    
    wingman.log_claim("Completed email processing job")
    print("✅ Job complete")


if __name__ == "__main__":
    main()
```

---

## API Reference (Quick)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check Wingman status |
| `/check` | POST | Validate instruction (Phase 2) |
| `/log_claim` | POST | Record claim to audit trail (Phase 3) |
| `/verify` | POST | Verify claim against reality (Phase 3) |
| `/approvals/request` | POST | Request human approval (Phase 4) |
| `/approvals/pending` | GET | List pending approvals |
| `/approvals/<id>` | GET | Get approval status |
| `/approvals/<id>/approve` | POST | Approve request |
| `/approvals/<id>/reject` | POST | Reject request |
| `/stats` | GET | Get verification statistics |

See [API Reference](../05-api-reference/README.md) for full documentation.

---

## Environment Configuration

Set these environment variables in your service:

```bash
# Required
WINGMAN_URL=http://127.0.0.1:5001  # Or 8101 for TEST, 8002 for DEV
WORKER_ID=your-service-name

# Optional (for approval endpoints with auth enabled)
WINGMAN_APPROVAL_READ_KEY=your-read-key
WINGMAN_APPROVAL_DECIDE_KEY=your-decide-key
WINGMAN_APPROVAL_REQUEST_KEY=your-request-key

# Deployment context
DEPLOYMENT_ENV=dev|test|prd
```

---

## Service-Specific Guides

- [Intel System Integration](./intel-system.md)
- [Mem0 Integration](./mem0.md)
- [CV Automation Integration](./cv-automation.md)

---

## Troubleshooting

### "Connection refused" to Wingman

```bash
# Check Wingman is running
curl http://127.0.0.1:5001/health

# If not, start it:
cd /Volumes/Data/ai_projects/wingman-system/wingman
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d
```

### Instruction rejected (score < 100%)

Your instruction is missing required sections. Check `missing_sections` in the response:

```python
result = wingman.check_instruction(instruction)
print(result["missing_sections"])  # e.g., ["MITIGATION", "RISK_ASSESSMENT"]
```

### Approval stuck on PENDING

Human needs to approve via Telegram bot or API:
```bash
# Via API
curl -X POST http://127.0.0.1:5001/approvals/<request_id>/approve \
  -H "Content-Type: application/json" \
  -d '{"decided_by": "mark", "note": "approved"}'
```

---

## Next Steps

- Read the [Architecture Guide](../02-architecture/README.md) to understand how Wingman works internally
- Check the [Operations Guide](../03-operations/README.md) for day-to-day running
- See the [API Reference](../05-api-reference/README.md) for complete endpoint documentation
