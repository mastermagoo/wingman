# Worker 001: Execution Gateway

**Date:** 2026-01-07
**Environment:** TEST
**Phase:** 1 (Core Components)
**Task Owner:** Human Operator (Mark)
**AI Assistant:** Claude (Sonnet 4.5) - Draft code only
**Status:** PENDING EXECUTION

---

## 1. DELIVERABLES

- [ ] `wingman/execution_gateway.py` - Gateway Flask service (draft provided by AI, human reviews/applies)
- [ ] `wingman/capability_token.py` - JWT token management (draft provided by AI, human reviews/applies)
- [ ] `wingman/Dockerfile.gateway` - Container definition (draft provided by AI, human reviews/applies)
- [ ] `ai-workers/results/worker-001-results.json` - Execution results (human creates after completion)

---

## 2. SUCCESS_CRITERIA

- [ ] Gateway accepts `POST /gateway/execute` with valid JWT token
- [ ] Gateway rejects expired tokens (returns 401)
- [ ] Gateway rejects forged tokens (signature validation fails)
- [ ] Gateway rejects replayed tokens (single-use enforcement)
- [ ] Gateway logs all execution attempts to audit trail (PostgreSQL)
- [ ] Unit tests passing (>95% coverage)

---

## 3. BOUNDARIES

**CAN:**
- Create new files: `execution_gateway.py`, `capability_token.py`, `Dockerfile.gateway`
- Add dependencies to requirements (PyJWT, Flask)
- Create unit tests in `tests/test_gateway.py`
- Connect to existing PostgreSQL for audit logging

**CANNOT:**
- Modify existing `api_server.py` (Worker 005 does that)
- Modify docker-compose files (Worker 006 does that)
- Deploy to TEST/PRD (Phase 4 does that)
- Remove docker socket from existing services yet

**MUST:**
- Follow Flask patterns from existing `api_server.py`
- Use PyJWT for token validation
- Log to PostgreSQL using existing connection pattern
- Include comprehensive error handling

---

## 4. DEPENDENCIES

**Hard Dependencies:**
- PostgreSQL running (for audit log storage)
- PyJWT library available
- Flask library available
- Existing `approval_store.py` (for approval_id validation)

**Soft Dependencies:**
- None (independent worker, can run in parallel with 002/003/004)

---

## 5. MITIGATION

**If PostgreSQL unavailable:**
- Gateway can fallback to JSONL file logging (`data/execution_audit.jsonl`)
- Add configuration flag: `AUDIT_STORAGE=postgres|jsonl`
- Graceful degradation, no execution blocking

**If token validation fails:**
- Log failure reason (expired / forged / replay)
- Return clear error message to caller
- Increment security metrics counter

**If command execution fails:**
- Log error to audit trail
- Return failure with stderr output
- Do not retry (idempotency responsibility of caller)

**Rollback:**
- Delete 3 created files
- No database changes (audit log is append-only)
- No stack restart needed (not deployed yet)

**Escalation:**
- If unit tests fail after human review: notify immediately
- If security vulnerabilities found: block execution until resolved

**Risk Level:** MEDIUM (new security-critical component)

---

## 6. TEST_PROCESS

### Manual Testing (Human)
```bash
# After applying AI-drafted code:

# 1. Install dependencies
cd wingman
pip install PyJWT flask

# 2. Run unit tests
pytest tests/test_gateway.py -v

# 3. Start gateway locally (without docker)
python execution_gateway.py

# 4. Test valid token (in another terminal)
TOKEN=$(python -c "from capability_token import generate_token; print(generate_token('test-approval-id'))")
curl -X POST http://localhost:5001/gateway/execute \
  -H "X-Capability-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "echo test", "approval_id": "test-approval-id"}'

# Expected: {"success": true, "output": "test", "execution_id": "..."}

# 5. Test expired token
curl -X POST http://localhost:5001/gateway/execute \
  -H "X-Capability-Token: expired-token-here" \
  -H "Content-Type: application/json" \
  -d '{"command": "echo test", "approval_id": "test"}'

# Expected: {"success": false, "error": "Token expired"}

# 6. Verify audit log
psql -h localhost -p 6432 -U admin -d wingman_test -c "SELECT * FROM execution_audit ORDER BY created_at DESC LIMIT 5;"

# Expected: See logged execution attempts
```

### Automated Testing
```bash
pytest tests/test_gateway.py -v --cov=execution_gateway --cov-report=term
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "001",
  "task": "Execution Gateway",
  "status": "pass|fail",
  "deliverables_created": [
    "wingman/execution_gateway.py",
    "wingman/capability_token.py",
    "wingman/Dockerfile.gateway",
    "wingman/tests/test_gateway.py"
  ],
  "test_results": {
    "unit_tests_pass": true,
    "coverage_percent": 96,
    "manual_valid_token_test": "pass",
    "manual_expired_token_test": "pass",
    "manual_forged_token_test": "pass",
    "manual_replay_token_test": "pass",
    "audit_log_write": "pass"
  },
  "evidence": {
    "pytest_output": "12 passed, 0 failed",
    "audit_log_sample": "execution_id=abc, approval_id=test, command=echo test",
    "gateway_response_time_ms": 45
  },
  "duration_minutes": 45,
  "timestamp": "2026-01-07T...",
  "human_operator": "Mark",
  "ai_assistance": "Claude drafted code, human reviewed and applied"
}
```

---

## 8. TASK_CLASSIFICATION

- **Type:** IMPLEMENTATION (security-critical component)
- **Complexity:** HIGH (token validation, security boundaries)
- **Tool:** Python + Flask + PyJWT
- **Reasoning:** Requires careful security design, token cryptography
- **Human-Led:** YES - AI drafts code, human reviews ALL code before applying
- **AI Role:** Code generation assistant only, no autonomous execution

---

## 9. RETROSPECTIVE

**Time estimate:** 45 minutes (AI draft) + 30 minutes (human review/test) = 75 minutes total

**Actual time:** [To be filled after execution]

**Challenges:** [To be filled after execution]

**Lessons learned:** [To be filled after execution]

**Security review notes:** [To be filled after human security review]

**Store in mem0:**
- Execution gateway pattern for privileged operation control
- JWT token validation best practices
- Flask security patterns for capability-based systems

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Manual gateway build: 2-3 hours (from scratch)
- Current process: No gateway exists, workers have direct docker access

**Targets:**
- AI code generation: <30 minutes
- Human review/testing: <45 minutes
- Gateway response time: <100ms (P95)
- Token validation: <10ms

**Quality:**
- Zero security vulnerabilities (human-verified)
- 100% of bypass attempts blocked in testing
- >95% test coverage
- Code reviewed and approved by human before deployment

**Monitoring:**
- Before: Verify PostgreSQL accessible, Flask installed
- During: Track AI code generation quality, human review time
- After: Run full test suite, verify all success criteria met
- Degradation limit: If tests fail or security concerns found, do not proceed to Phase 2

---

## EXECUTION INSTRUCTIONS (HUMAN OPERATOR)

### Step 1: Request AI Code Draft
Ask AI to generate complete code for:
1. `execution_gateway.py` (Flask service with /gateway/execute endpoint)
2. `capability_token.py` (JWT generation and validation)
3. `Dockerfile.gateway` (minimal Python container)
4. `tests/test_gateway.py` (comprehensive unit tests)

### Step 2: Human Security Review
Review AI-generated code for:
- [ ] JWT signature validation is correct
- [ ] Token expiry is enforced
- [ ] Single-use tokens (no replay)
- [ ] Command injection prevention
- [ ] Audit logging is comprehensive
- [ ] Error handling doesn't leak sensitive info
- [ ] No hardcoded secrets

### Step 3: Apply Code (Manual)
```bash
# Human manually creates files:
cd /Volumes/Data/ai_projects/wingman-system/wingman
nano execution_gateway.py  # paste reviewed code
nano capability_token.py    # paste reviewed code
nano Dockerfile.gateway     # paste reviewed code
mkdir -p tests
nano tests/test_gateway.py  # paste reviewed code
```

### Step 4: Run Tests (Manual)
```bash
pytest tests/test_gateway.py -v
# If tests fail: review, fix, re-test
# If tests pass: proceed to manual testing
```

### Step 5: Manual Validation (Human)
Follow TEST_PROCESS section above, verify all scenarios work.

### Step 6: Record Results (Human)
Create `ai-workers/results/worker-001-results.json` with test results.

### Step 7: Gate Decision (Human)
- **PASS:** Proceed to next worker
- **FAIL:** Fix issues, re-test, or rollback

---

**Wingman Validation Score:** N/A (Wingman validation currently broken)
**Human Approval Required:** YES
**Security Review Required:** YES (critical security component)
**Status:** AWAITING HUMAN EXECUTION
