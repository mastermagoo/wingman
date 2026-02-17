# Intel-System + Wingman Integration - Quick Start

**Purpose**: Get Claude working in intel-system to use Wingman as approval authority
**Time**: 15 minutes
**Date**: 2026-02-17
**Updated**: Phase 6.1 Output Validation + Phase 6.2 Monitoring

---

## 1. Copy Client Library to Intel-System

```bash
# Copy Wingman client to intel-system
cp /Volumes/Data/ai_projects/wingman-system/wingman/docs/04-user-guides/WINGMAN_CLIENT_INTEGRATION.md \
   /Volumes/Data/ai_projects/intel-system/docs/

# Extract Python client library
cd /Volumes/Data/ai_projects/intel-system
# Create wingman_client.py from the integration guide
```

Or manually create `/Volumes/Data/ai_projects/intel-system/wingman_client.py` with the WingmanClient class from the integration guide.

---

## 2. Configure Intel-System Environment

Choose TEST or PRD configuration based on your needs:

### TEST Environment Configuration

Add to `/Volumes/Data/ai_projects/intel-system/.env` or `.env.test`:

```bash
# Wingman Integration (Approval Authority) - TEST
WINGMAN_API_URL=http://127.0.0.1:8101
WINGMAN_APPROVAL_REQUEST_KEY=XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY
WINGMAN_APPROVAL_READ_KEY=XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY

# System identifier
SYSTEM_NAME=intel-system
DEPLOYMENT_ENV=test
```

### PRD Environment Configuration

Add to `/Volumes/Data/ai_projects/intel-system/.env.prd`:

```bash
# Wingman Integration (Approval Authority) - PRD
WINGMAN_API_URL=http://127.0.0.1:5001
WINGMAN_APPROVAL_REQUEST_KEY=outgunning-web-serin-profounder-swans-globule
WINGMAN_APPROVAL_READ_KEY=outgunning-web-serin-profounder-swans-globule

# System identifier
SYSTEM_NAME=intel-system
DEPLOYMENT_ENV=prd
```

**CRITICAL**: Get actual PRD keys from Wingman `.env.prd`. NEVER commit `.env.prd` to git.

---

## 3. Update Intel-System CLAUDE.md

Add this section to `/Volumes/Data/ai_projects/intel-system/CLAUDE.md`:

```markdown
## 🚨 CRITICAL: Wingman Approval Integration

**This system uses Wingman as the approval authority for ALL destructive operations.**

### When to Request Approval

**ALWAYS request Wingman approval before**:
- Docker operations: `stop`, `rm`, `down`, `build`, `restart`, `up -d --build`
- Database changes: `DROP`, `TRUNCATE`, `ALTER`, `DELETE`
- File deletions: `rm -rf`, `rm -f`
- Production deployments
- System configuration changes

### How to Request Approval

Use the WingmanClient library:

```python
from wingman_client import WingmanClient

client = WingmanClient(system_name="intel-system")

# Request approval
result = client.request_approval(
    worker_id="your_unique_id",  # e.g., "intel_deployer_001"
    task_name="Brief description of task",
    instruction="DELIVERABLES: What you will do. VALIDATION: How to verify.",
    claim="I will execute: <exact command>"
)

# Check result
if result["status"] == "APPROVED":
    # Execute via gateway with capability token
    exec_result = client.execute_command(
        "<exact command>",
        result["capability_token"]
    )
    print(exec_result)
elif result["status"] == "QUARANTINED":
    print(f"⚠️ Worker quarantined: {result['reason']}")
    # DO NOT execute - contact Mark
elif result["status"] == "REJECTED":
    print(f"❌ Request rejected: {result['reason']}")
    # DO NOT execute
elif result["status"] == "PENDING":
    # Wait for Mark to approve via Telegram
    print("⏳ Waiting for approval...")
```

### Claim Verification - BE TRUTHFUL

**Wingman watches and verifies your claims.**

✅ **Good**:
- "I will execute: docker stop intel-api"
- "I executed: docker stop intel-api" (and you actually did)

❌ **FALSE CLAIM** (will trigger quarantine):
- "I executed: docker stop intel-api" (but you didn't)
- "I successfully deployed to PRD" (but deployment failed)

**If you make FALSE claims**:
1. Watcher detects discrepancy
2. Telegram alert sent to Mark
3. Severity: MEDIUM (TEST) or CRITICAL (PRD)
4. Repeated violations → automatic quarantine
5. Quarantined workers CANNOT request approvals

### Deployment Environment

- `test` - Most operations auto-approved (for development)
- `prd` - ALL destructive operations require Mark's approval via Telegram

**Current**: Set via `DEPLOYMENT_ENV` in `.env`
```

---

## 4. Verify Wingman is Running

### TEST Environment

```bash
# Check Wingman TEST health
curl -s http://127.0.0.1:8101/health | python3 -m json.tool

# Should return:
# {
#   "status": "healthy",
#   "phase": "6.1",
#   "database": "memory",
#   "validators": {
#     "input_validation": "available",
#     "output_validation": "available"
#   },
#   "verifiers": {
#     "simple": "available",
#     "enhanced": "unavailable"
#   }
# }
```

If not running:

```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman
docker compose -f docker-compose.yml -p wingman-test up -d
```

### PRD Environment

```bash
# Check Wingman PRD health
curl -s http://127.0.0.1:5001/health | python3 -m json.tool

# Should return:
# {
#   "status": "healthy",
#   "phase": "6.1",
#   "database": "connected",
#   "validators": {
#     "input_validation": "available",
#     "output_validation": "available"
#   },
#   "verifiers": {
#     "simple": "available",
#     "enhanced": "unavailable"
#   }
# }
```

If not running:

```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d
```

---

## 5. Test the Integration

### Test 1: Simple Approval Request

```bash
cd /Volumes/Data/ai_projects/intel-system

curl -X POST http://127.0.0.1:8101/approvals/request \
  -H "Content-Type: application/json" \
  -H "X-Wingman-Approval-Request-Key: XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY" \
  -d '{
    "worker_id": "intel_test_001",
    "task_name": "Test Wingman Integration",
    "instruction": "DELIVERABLES: Test approval flow from intel-system. VALIDATION: Request succeeds and returns approval_id.",
    "deployment_env": "test",
    "claim": "I am testing the Wingman approval integration",
    "system": "intel-system"
  }' | python3 -m json.tool
```

**Expected** (TEST auto-approves):
```json
{
  "approval_id": "uuid",
  "needs_approval": false,
  "status": "APPROVED",
  "capability_token": "jwt...",
  "auto_approved": true
}
```

### Test 2: Execute Command via Gateway

```bash
# Use capability_token from above
curl -X POST http://127.0.0.1:8101/execute \
  -H "Authorization: Bearer <capability_token>" \
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

### Test 3: Use Python Client

Create `test_wingman.py`:

```python
#!/usr/bin/env python3
from wingman_client import WingmanClient

client = WingmanClient(
    api_url="http://127.0.0.1:8101",
    request_key="XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY",
    read_key="XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY",
    system_name="intel-system",
    deployment_env="test"
)

# Test approval request
result = client.request_approval(
    worker_id="intel_python_test",
    task_name="Test Python Client",
    instruction="DELIVERABLES: Test Wingman client library. VALIDATION: Success response.",
    claim="Testing WingmanClient from intel-system"
)

print(f"Status: {result['status']}")
print(f"Approved: {result.get('auto_approved', False)}")

if result['status'] == 'APPROVED':
    # Execute test command
    exec_result = client.execute_command(
        "echo 'Python client test successful'",
        result['capability_token']
    )
    print(f"Output: {exec_result['output']}")
```

Run it:
```bash
python3 test_wingman.py
```

---

## 6. Real-World Test: Deploy Intel-System Container

### Scenario: Rebuild intel-api with Wingman approval

```python
#!/usr/bin/env python3
"""Deploy intel-system with Wingman approval"""
from wingman_client import WingmanClient

client = WingmanClient(system_name="intel-system")

# Request approval
result = client.request_approval(
    worker_id="intel_deployer_real_test",
    task_name="Rebuild intel-api container (TEST)",
    instruction="""
    DELIVERABLES:
    1. Stop current intel-api container
    2. Rebuild with latest code
    3. Start new container
    4. Verify health endpoint responds

    VALIDATION:
    - Container running: docker ps | grep intel-api
    - Health check: curl http://localhost:8080/health
    """,
    claim="I will execute: docker compose -f docker-compose.yml -p intel-test up -d --build intel-api"
)

if result['status'] == 'APPROVED':
    print("✅ Approval granted - executing deployment")

    # Execute via Wingman gateway
    exec_result = client.execute_command(
        "cd /Volumes/Data/ai_projects/intel-system && docker compose -f docker-compose.yml -p intel-test up -d --build intel-api",
        result['capability_token']
    )

    if exec_result['success']:
        print("✅ Deployment successful")
        print(exec_result['output'])
    else:
        print("❌ Deployment failed")
        print(exec_result['output'])

elif result['status'] == 'PENDING':
    print("⏳ Waiting for Mark's approval via Telegram")
    print(f"Approval ID: {result['approval_id']}")

elif result['status'] == 'QUARANTINED':
    print(f"⚠️ Worker quarantined: {result['reason']}")
    print("Contact Mark to release worker")

else:
    print(f"❌ Request rejected: {result.get('reason', 'Unknown')}")
```

---

## 7. Monitor Wingman Watcher

After running operations, check if Wingman detected any issues:

```bash
# Check watcher logs
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test logs --tail=50 wingman-watcher

# Check for alerts in database
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec -T postgres \
  psql -U wingman -d wingman -c "SELECT alert_id, event_type, severity, worker_id, message FROM watcher_alerts WHERE worker_id LIKE 'intel%' ORDER BY sent_at DESC LIMIT 10;"
```

---

## 8. Test FALSE Claim Detection (Optional)

**WARNING**: This will trigger a watcher alert!

```python
from wingman_client import WingmanClient

client = WingmanClient(system_name="intel-system")

# Make a FALSE claim (claim you did something but don't do it)
result = client.request_approval(
    worker_id="intel_false_claim_test",
    task_name="Test FALSE Claim Detection",
    instruction="DELIVERABLES: Test watcher detection",
    claim="I executed: docker stop intel-api-1 (THIS IS A LIE - testing detection)"
)

# Check Wingman watcher logs - should see alert
```

Expected:
- Telegram alert to Mark
- Alert in database with `severity=MEDIUM` (TEST environment)
- Worker ID logged for potential quarantine

---

## Success Criteria

✅ All tests pass:
1. Health check returns `{"status": "healthy", "phase": "6.1"}`
2. Approval request returns `status=APPROVED`
3. Command execution via gateway succeeds
4. Python client works
5. Real deployment test succeeds
6. Watcher logs show monitoring is active

---

## Phase 6.1/6.2 Features

### Output Validation (Phase 6.1)

If your AI workers generate code, use output validation BEFORE deployment:

```python
# Validate AI-generated code
validation_result = client.validate_output(
    worker_id="intel_code_generator",
    generated_files=["/path/to/generated_script.py"],
    task_name="Generate backup script"
)

if validation_result['status'] == 'APPROVED':
    print("✅ Code passed validation - safe to deploy")
elif validation_result['status'] == 'REJECTED':
    print(f"❌ Code rejected: {validation_result['reason']}")
else:  # PENDING
    print("⏳ Code requires manual review")
```

**Documentation**: [OUTPUT_VALIDATION_USER_GUIDE.md](OUTPUT_VALIDATION_USER_GUIDE.md)

### Monitoring & Observability (Phase 6.2)

Real-time metrics and dashboards available:

- **Prometheus**: http://localhost:9091 (metrics database)
- **Grafana**: http://localhost:3333 (dashboards, login: admin/admin)
- **Metrics Endpoint**: http://localhost:8101/metrics

Monitor Wingman health, approval queue depth, validation success rates, and more.

**Documentation**: [PROMETHEUS_GRAFANA_MONITORING_GUIDE.md](PROMETHEUS_GRAFANA_MONITORING_GUIDE.md)

---

## Next Steps

1. **Update Claude Context**: Tell Claude in intel-system about Wingman integration
2. **Test Real Operations**: Try actual intel-system deployments through Wingman
3. **Use Output Validation**: Validate any AI-generated code before deployment
4. **Monitor Metrics**: Check Grafana dashboards for system health
5. **Expand to Other Systems**: cv-automation, mem0, etc.

---

## Troubleshooting

**Issue**: Connection refused
- **Fix**: Start Wingman: `cd /Volumes/Data/ai_projects/wingman-system/wingman && docker compose -f docker-compose.yml -p wingman-test up -d`

**Issue**: 401 Unauthorized
- **Fix**: Check API key in `.env` matches Wingman `.env.test`

**Issue**: Worker quarantined
- **Check**: `docker compose -f .../wingman/docker-compose.yml -p wingman-test exec -T redis redis-cli SMEMBERS quarantined_workers`
- **Release**: See integration guide section "Troubleshooting"

---

**Ready to test?** Start with Test 1 and work through the tests in order.

**Full documentation**: [WINGMAN_CLIENT_INTEGRATION.md](WINGMAN_CLIENT_INTEGRATION.md)

---

**End of Quick Start**
