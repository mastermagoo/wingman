# Wingman API Reference

> **Base URLs**:  
> - PRD: `http://127.0.0.1:5001`  
> - TEST: `http://127.0.0.1:8101`  
> - DEV: `http://127.0.0.1:8002`

---

## Overview

| Endpoint | Method | Phase | Purpose |
|----------|--------|-------|---------|
| `/` | GET | - | API documentation |
| `/health` | GET | 1 | Health check |
| `/check` | POST | 2 | Validate instruction |
| `/log_claim` | POST | 3 | Record claim to audit trail |
| `/verify` | POST | 3 | Verify claim against reality |
| `/stats` | GET | 3 | Get verification statistics |
| `/approvals/request` | POST | 4 | Request human approval |
| `/approvals/pending` | GET | 4 | List pending approvals |
| `/approvals/<id>` | GET | 4 | Get approval details |
| `/approvals/<id>/approve` | POST | 4 | Approve request |
| `/approvals/<id>/reject` | POST | 4 | Reject request |

---

## Common Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (missing/invalid fields) |
| 401 | Unauthorized (missing/invalid API key) |
| 404 | Not found |
| 500 | Server error |

---

## Endpoints

### GET /

Returns API documentation and available endpoints.

**Response**:
```json
{
  "name": "Wingman Verification API",
  "version": "3.0.0",
  "phase": "3",
  "endpoints": {
    "POST /check": "Validate instruction (Phase 2)",
    "POST /log_claim": "Record worker claim (Phase 3)",
    "POST /verify": "Verify a claim (Phase 1/3)",
    "POST /approvals/request": "Request human approval (Phase 4)",
    "GET /approvals/pending": "List pending approvals (Phase 4)",
    "GET /approvals/<id>": "Get approval request (Phase 4)",
    "POST /approvals/<id>/approve": "Approve (Phase 4)",
    "POST /approvals/<id>/reject": "Reject (Phase 4)",
    "GET /health": "Check API status",
    "GET /stats": "Get verification statistics"
  },
  "timestamp": "2026-01-06T10:30:00"
}
```

---

### GET /health

Check if API is healthy and which components are available.

**Response**:
```json
{
  "status": "healthy",
  "phase": "3",
  "verifiers": {
    "simple": "available",
    "enhanced": "available"
  },
  "database": "connected",
  "timestamp": "2026-01-06T10:30:00"
}
```

| Field | Values |
|-------|--------|
| `status` | `healthy` or `unhealthy` |
| `database` | `connected` or `memory` (fallback) |
| `verifiers.enhanced` | `available` if Ollama running, else `unavailable` |

---

### POST /check

**Phase 2**: Validate an instruction against the 10-point framework.

**Request**:
```json
{
  "instruction": "DELIVERABLES: ...\nSUCCESS_CRITERIA: ...\n..."
}
```

**Required Sections** (must appear in instruction):
1. `DELIVERABLES`
2. `SUCCESS_CRITERIA`
3. `BOUNDARIES`
4. `DEPENDENCIES`
5. `MITIGATION`
6. `TEST_PROCESS`
7. `TEST_RESULTS_FORMAT`
8. `RESOURCE_REQUIREMENTS`
9. `RISK_ASSESSMENT`
10. `QUALITY_METRICS`

**Response (approved)**:
```json
{
  "approved": true,
  "score": 100,
  "missing_sections": [],
  "policy_checks": {
    "no_force_flags": true,
    "no_hardcoded_secrets": true
  }
}
```

**Response (rejected)**:
```json
{
  "approved": false,
  "score": 60,
  "missing_sections": ["MITIGATION", "RISK_ASSESSMENT", "QUALITY_METRICS", "BOUNDARIES"],
  "policy_checks": {
    "no_force_flags": true,
    "no_hardcoded_secrets": true
  }
}
```

---

### POST /log_claim

**Phase 3**: Record a claim to the audit trail.

**Request**:
```json
{
  "worker_id": "intel-system-extractor",
  "claim": "Created file /data/backup.tar"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `claim` | Yes | What you're claiming to have done |
| `worker_id` | No | Identifier for the worker (default: "unknown") |

**Response**:
```json
{
  "status": "logged",
  "entry": {
    "timestamp": "2026-01-06T10:30:00",
    "worker_id": "intel-system-extractor",
    "claim": "Created file /data/backup.tar",
    "status": "PENDING_VERIFICATION"
  }
}
```

---

### POST /verify

**Phase 3**: Verify a claim against reality.

**Request**:
```json
{
  "claim": "Created file /data/backup.tar",
  "use_enhanced": false
}
```

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `claim` | Yes | - | The claim to verify |
| `use_enhanced` | No | `false` | Use LLM-powered verifier (slower) |
| `source` | No | `"api"` | Source identifier for logging |

**Response**:
```json
{
  "verdict": "TRUE",
  "details": "Simple verification completed with verdict: TRUE",
  "timestamp": "2026-01-06T10:30:00",
  "verifier": "simple",
  "processing_time_ms": 12
}
```

**Verdict Values**:

| Verdict | Meaning |
|---------|---------|
| `TRUE` | Evidence confirms the claim |
| `FALSE` | Evidence contradicts the claim |
| `UNVERIFIABLE` | Cannot determine truth |
| `ERROR` | Verification failed |

**What Can Be Verified**:

| Claim Type | Example | Verifier |
|------------|---------|----------|
| File creation | `Created file /data/x.txt` | simple |
| File deletion | `Deleted file /tmp/old.log` | simple |
| Process running | `Process postgres is running` | simple |
| Complex claims | `Database backup is valid` | enhanced |

---

### GET /stats

Get verification statistics.

**Query Parameters**:
| Param | Default | Options |
|-------|---------|---------|
| `range` | `24h` | `1h`, `24h`, `7d`, `30d` |

**Response**:
```json
{
  "total_verifications": 150,
  "verdicts": {
    "TRUE": 140,
    "FALSE": 5,
    "UNVERIFIABLE": 5
  },
  "avg_processing_time_ms": 15,
  "time_range": "24h",
  "source": "database",
  "timestamp": "2026-01-06T10:30:00"
}
```

---

### POST /approvals/request

**Phase 4**: Request human approval for a high-risk operation.

**Request**:
```json
{
  "worker_id": "intel-system-migrator",
  "task_name": "Database Migration",
  "instruction": "ALTER TABLE users ADD COLUMN verified BOOLEAN",
  "deployment_env": "prd"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `instruction` | Yes | The instruction to approve |
| `worker_id` | No | Worker identifier |
| `task_name` | No | Short task description |
| `deployment_env` | No | Environment (dev/test/prd) |

**Response (auto-approved, low risk)**:
```json
{
  "needs_approval": false,
  "status": "AUTO_APPROVED",
  "request": {
    "request_id": "abc123",
    "worker_id": "intel-system-migrator",
    "task_name": "Database Migration",
    "status": "AUTO_APPROVED",
    "risk_level": "LOW",
    "created_at": "2026-01-06T10:30:00"
  },
  "risk": {
    "risk_level": "LOW",
    "risk_reason": "No high-risk indicators detected"
  }
}
```

**Response (needs approval, high risk)**:
```json
{
  "needs_approval": true,
  "status": "PENDING",
  "request": {
    "request_id": "def456",
    "worker_id": "intel-system-migrator",
    "task_name": "Database Migration",
    "status": "PENDING",
    "risk_level": "HIGH",
    "created_at": "2026-01-06T10:30:00"
  },
  "risk": {
    "risk_level": "HIGH",
    "risk_reason": "Deployment environment is PRD"
  }
}
```

**Risk Assessment Rules**:

| Condition | Risk Level |
|-----------|------------|
| `deployment_env == "prd"` | HIGH |
| Contains: prod, production, delete, drop, truncate, secret, token, password, --force | HIGH |
| Contains: migration, deploy, schema, postgres, redis, sudo | MEDIUM |
| Otherwise | LOW (auto-approved) |

---

### GET /approvals/pending

**Phase 4**: List pending approval requests.

**Query Parameters**:
| Param | Default | Description |
|-------|---------|-------------|
| `limit` | 20 | Max results to return |

**Headers** (if auth enabled):
```
X-Wingman-Approval-Read-Key: your-read-key
```

**Response**:
```json
{
  "pending": [
    {
      "request_id": "def456",
      "worker_id": "intel-system-migrator",
      "task_name": "Database Migration",
      "instruction": "ALTER TABLE...",
      "status": "PENDING",
      "risk_level": "HIGH",
      "risk_reason": "Deployment environment is PRD",
      "created_at": "2026-01-06T10:30:00"
    }
  ],
  "count": 1
}
```

---

### GET /approvals/{request_id}

**Phase 4**: Get details of a specific approval request.

**Headers** (if auth enabled):
```
X-Wingman-Approval-Read-Key: your-read-key
```

**Response**:
```json
{
  "request_id": "def456",
  "worker_id": "intel-system-migrator",
  "task_name": "Database Migration",
  "instruction": "ALTER TABLE users ADD COLUMN verified BOOLEAN",
  "status": "PENDING",
  "risk_level": "HIGH",
  "risk_reason": "Deployment environment is PRD",
  "created_at": "2026-01-06T10:30:00",
  "decided_at": null,
  "decided_by": null,
  "decision_note": null
}
```

**Status Values**:
| Status | Meaning |
|--------|---------|
| `PENDING` | Awaiting human decision |
| `APPROVED` | Human approved |
| `REJECTED` | Human rejected |
| `AUTO_APPROVED` | Low-risk, auto-approved |

---

### POST /approvals/{request_id}/approve

**Phase 4**: Approve a pending request.

**Headers** (if auth enabled):
```
X-Wingman-Approval-Decide-Key: your-decide-key
```

**Request**:
```json
{
  "decided_by": "mark",
  "note": "Reviewed and approved"
}
```

**Response**:
```json
{
  "request_id": "def456",
  "status": "APPROVED",
  "decided_at": "2026-01-06T10:35:00",
  "decided_by": "mark",
  "decision_note": "Reviewed and approved"
}
```

---

### POST /approvals/{request_id}/reject

**Phase 4**: Reject a pending request.

**Headers** (if auth enabled):
```
X-Wingman-Approval-Decide-Key: your-decide-key
```

**Request**:
```json
{
  "decided_by": "mark",
  "note": "Too risky, needs review"
}
```

**Response**:
```json
{
  "request_id": "def456",
  "status": "REJECTED",
  "decided_at": "2026-01-06T10:35:00",
  "decided_by": "mark",
  "decision_note": "Too risky, needs review"
}
```

---

## Authentication

### Approval Endpoints (Phase 4)

If configured, approval endpoints require API keys in headers.

**Environment Variables** (server-side):
```bash
# Role-separated keys (recommended)
WINGMAN_APPROVAL_READ_KEYS=key1,key2    # For GET /approvals/*
WINGMAN_APPROVAL_DECIDE_KEYS=key3,key4  # For POST /approvals/*/approve|reject
WINGMAN_APPROVAL_REQUEST_KEYS=key5      # For POST /approvals/request

# Legacy single key (backwards compatible)
WINGMAN_APPROVAL_API_KEY=legacy-key
```

**Client Headers**:
```bash
# Role-separated
curl -H "X-Wingman-Approval-Read-Key: your-key" http://127.0.0.1:5001/approvals/pending
curl -H "X-Wingman-Approval-Decide-Key: your-key" -X POST http://127.0.0.1:5001/approvals/abc/approve

# Legacy
curl -H "X-Wingman-Approval-Key: legacy-key" http://127.0.0.1:5001/approvals/pending
```

---

## Error Responses

**400 Bad Request**:
```json
{
  "error": "Missing 'claim' field",
  "timestamp": "2026-01-06T10:30:00"
}
```

**401 Unauthorized**:
```json
{
  "error": "Unauthorized"
}
```

**404 Not Found**:
```json
{
  "error": "Not found"
}
```

**500 Server Error**:
```json
{
  "error": "Internal server error message",
  "timestamp": "2026-01-06T10:30:00"
}
```

---

## Examples

### cURL Examples

```bash
# Health check
curl -s http://127.0.0.1:5001/health | jq

# Validate instruction (Phase 2)
curl -s -X POST http://127.0.0.1:5001/check \
  -H "Content-Type: application/json" \
  -d '{
    "instruction": "DELIVERABLES: Export data\nSUCCESS_CRITERIA: File created\nBOUNDARIES: Read only\nDEPENDENCIES: DB connection\nMITIGATION: Retry on failure\nTEST_PROCESS: Check file exists\nTEST_RESULTS_FORMAT: JSON\nRESOURCE_REQUIREMENTS: Low\nRISK_ASSESSMENT: Low\nQUALITY_METRICS: 100% accuracy"
  }' | jq

# Log a claim (Phase 3)
curl -s -X POST http://127.0.0.1:5001/log_claim \
  -H "Content-Type: application/json" \
  -d '{"worker_id": "test", "claim": "Created file /tmp/test.txt"}' | jq

# Verify a claim (Phase 3)
curl -s -X POST http://127.0.0.1:5001/verify \
  -H "Content-Type: application/json" \
  -d '{"claim": "Process postgres is running"}' | jq

# Request approval (Phase 4)
curl -s -X POST http://127.0.0.1:5001/approvals/request \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "test-worker",
    "task_name": "Test Task",
    "instruction": "Do something in production",
    "deployment_env": "prd"
  }' | jq

# List pending approvals (Phase 4)
curl -s http://127.0.0.1:5001/approvals/pending | jq

# Approve (Phase 4)
curl -s -X POST http://127.0.0.1:5001/approvals/REQUEST_ID/approve \
  -H "Content-Type: application/json" \
  -d '{"decided_by": "mark", "note": "ok"}' | jq
```

### Python Examples

See [wingman_client.py](../01-how-to-use/wingman_client.py) for a complete client library.

```python
import requests

WINGMAN_URL = "http://127.0.0.1:5001"

# Verify a claim
response = requests.post(f"{WINGMAN_URL}/verify", json={
    "claim": "Created file /data/output.txt"
})
print(response.json())
# {"verdict": "TRUE", "verifier": "simple", ...}
```

---

## See Also

- [How to Use](../01-how-to-use/README.md) — Integration patterns
- [Architecture](../02-architecture/README.md) — System design
- [Operations](../03-operations/README.md) — Running Wingman
