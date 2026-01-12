# Worker 005: Approval → Gateway Bridge Integration

**Date:** 2026-01-07
**Environment:** TEST
**Phase:** 2 (Integration)
**Task Owner:** Human Operator (Mark)
**AI Assistant:** Claude (Sonnet 4.5) - Draft code only
**Status:** PENDING EXECUTION (Blocked until Phase 1 complete)

---

## 1. DELIVERABLES

- [ ] Modified `wingman/api_server.py` - Add consensus call, token issuance, `/execute` endpoint (AI draft, human reviews)
- [ ] `ai-workers/results/worker-005-results.json` - Execution results (human creates)

---

## 2. SUCCESS_CRITERIA

- [ ] `/approvals/request` triggers consensus verification (Worker 003)
- [ ] `/approvals/<id>/approve` issues JWT capability token
- [ ] New `/execute` endpoint forwards to gateway with token
- [ ] Backward compatible with existing approval API
- [ ] Existing Telegram bot still works
- [ ] Unit tests passing (>90% coverage for new code)
- [ ] Integration tests passing

---

## 3. BOUNDARIES

**CAN:**
- Modify `api_server.py` (add imports, new endpoints, integrate consensus)
- Import Workers 001/003 components (gateway client, consensus verifier)
- Add new `/execute` endpoint
- Modify approval flow to include consensus

**CANNOT:**
- Change approval_store.py schema (preserve existing data)
- Remove existing endpoints (backward compatibility required)
- Modify Telegram bot (it should continue to work)
- Change approval request/response format (breaking change)

**MUST:**
- Preserve all existing API endpoints
- Maintain approval audit trail
- Support clients that don't use /execute (graceful degradation)
- Handle consensus/gateway unavailability gracefully

---

## 4. DEPENDENCIES

**Hard Dependencies:**
- Worker 001 complete (execution_gateway.py)
- Worker 003 complete (consensus_verifier.py)
- Existing `approval_store.py` unchanged
- Existing `api_server.py` running

**Blocking:** Cannot start until Phase 1 workers (001-004) complete

---

## 5. MITIGATION

**If consensus verifier fails:**
- Fall back to existing keyword-based risk assessment
- Log warning
- Approval continues (availability over consensus)

**If gateway unavailable:**
- `/execute` returns 503 Service Unavailable
- Client can retry
- Do not block approval (approval != execution)

**If backward compatibility breaks:**
- Revert changes immediately
- Test with existing Telegram bot flows
- Fix and retest

**Rollback:**
- `git checkout HEAD -- api_server.py` (revert to before Worker 005)
- Restart API service
- No database changes (approval_store unchanged)
- ~2 minutes downtime

**Escalation:**
- If existing clients break: immediate rollback
- If consensus slows approvals >10s: make consensus async

**Risk Level:** HIGH (modifies critical API, backward compatibility required)

---

## 6. TEST_PROCESS

### Manual Testing (Human)
```bash
# After applying AI-drafted changes to api_server.py:

# 1. Restart API service
docker compose -f docker-compose.yml -p wingman-test restart wingman-api

# 2. Test backward compatibility: existing approval flow
curl -X POST http://localhost:5002/approvals/request \
  -H "Content-Type: application/json" \
  -d '{"worker_id": "test", "task_name": "Test", "instruction": "List containers", "deployment_env": "test"}'

# Expected: {"needs_approval": true|false, "status": "PENDING"|"AUTO_APPROVED", ...}
# No errors, same format as before

# 3. Test consensus integration (if approval created)
# Verify logs show consensus was called:
docker compose -f docker-compose.yml -p wingman-test logs wingman-api | grep -i consensus

# Expected: See consensus verifier logs

# 4. Test approval with token issuance
APPROVAL_ID="<from step 2>"
curl -X POST http://localhost:5002/approvals/$APPROVAL_ID/approve \
  -H "X-Wingman-Approval-Decide-Key: <key>" \
  -H "Content-Type: application/json" \
  -d '{"decided_by": "test"}'

# Expected: {"status": "APPROVED", "token": "eyJ..."}  # JWT token returned

# 5. Test new /execute endpoint
TOKEN="<from step 4>"
curl -X POST http://localhost:5002/execute \
  -H "X-Capability-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "docker compose -f docker-compose.yml ps", "approval_id": "'$APPROVAL_ID'"}'

# Expected: {"success": true, "output": "...", "execution_id": "..."}
# (Gateway executed command, returned result)

# 6. Test Telegram bot still works
# Send /pending command via Telegram
# Expected: Bot shows pending approvals (no errors)
```

### Automated Testing
```bash
pytest tests/test_api_integration.py -v
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "005",
  "task": "Approval → Gateway Bridge Integration",
  "status": "pass|fail",
  "deliverables_created": [
    "wingman/api_server.py (modified)"
  ],
  "test_results": {
    "unit_tests_pass": true,
    "integration_tests_pass": true,
    "backward_compatibility": "pass",
    "consensus_integration": "pass",
    "token_issuance": "pass",
    "execute_endpoint": "pass",
    "telegram_bot_works": "pass"
  },
  "evidence": {
    "pytest_output": "22 passed, 0 failed",
    "backward_compat_test": "existing approval flow works",
    "consensus_called": true,
    "token_format": "valid JWT",
    "gateway_called": true
  },
  "duration_minutes": 45,
  "timestamp": "2026-01-07T...",
  "human_operator": "Mark",
  "ai_assistance": "Claude drafted code changes, human reviewed and applied"
}
```

---

## 8. TASK_CLASSIFICATION

- **Type:** INTEGRATION (modify existing critical API)
- **Complexity:** HIGH (backward compatibility, multiple component integration)
- **Tool:** Python + Flask (modify existing service)
- **Reasoning:** Integrates Phase 1 workers into approval flow
- **Human-Led:** YES - AI drafts changes, human reviews ALL changes before applying
- **AI Role:** Code generation assistant only, no autonomous execution

---

## 9. RETROSPECTIVE

**Time estimate:** 30 minutes (AI draft) + 15 minutes (human review/test) = 45 minutes total

**Actual time:** [To be filled after execution]

**Challenges:** [To be filled after execution]

**Backward compatibility issues:** [To be filled - any existing clients broken?]

**Performance impact:** [To be filled - did consensus slow approvals?]

**Store in mem0:**
- Backward-compatible API integration pattern
- JWT token issuance on approval
- Consensus verification integration

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Current approval flow: <500ms
- No consensus, no token issuance

**Targets:**
- AI code generation: <30 minutes
- Human review/testing: <20 minutes
- Approval with consensus: <5 minutes (async consensus)
- Token issuance: <10ms
- /execute endpoint: <100ms (forward to gateway)

**Quality:**
- 100% backward compatibility (existing flows work)
- Zero breaking changes for existing clients
- Consensus doesn't block approval >10s (async if needed)

**Monitoring:**
- Before: Backup api_server.py, verify TEST stack healthy
- During: Monitor API response times, error rates
- After: Verify all existing clients work, consensus integrates smoothly
- Degradation limit: If approval latency >10s, rollback

---

## EXECUTION INSTRUCTIONS (HUMAN OPERATOR)

### Step 1: Prerequisites Check
Verify Phase 1 complete:
- [ ] Worker 001 complete (gateway exists)
- [ ] Worker 003 complete (consensus exists)
- [ ] All Phase 1 tests passing

### Step 2: Backup
```bash
cp api_server.py api_server.py.backup
```

### Step 3: Request AI Code Draft
Ask AI to generate modifications to `api_server.py`:
1. Import `consensus_verifier` (Worker 003)
2. Import `capability_token` (Worker 001)
3. Modify `/approvals/request` to call consensus
4. Modify `/approvals/<id>/approve` to issue token
5. Add new `/execute` endpoint that forwards to gateway
6. Preserve all existing endpoints unchanged

### Step 4: Human Review
Review AI-generated changes:
- [ ] No breaking changes to existing endpoints
- [ ] Consensus called but doesn't block
- [ ] Token issuance is secure (proper signing)
- [ ] /execute endpoint validates token before forwarding
- [ ] Error handling doesn't leak tokens
- [ ] Backward compatible with existing Telegram bot

### Step 5: Apply Changes (Manual)
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman
nano api_server.py  # Apply reviewed changes
```

### Step 6: Restart API
```bash
docker compose -f docker-compose.yml -p wingman-test restart wingman-api
```

### Step 7: Run Tests
Follow TEST_PROCESS section, verify backward compatibility.

### Step 8: Record Results
Create `ai-workers/results/worker-005-results.json`.

### Step 9: Gate Decision
- **PASS:** Proceed to Worker 006
- **FAIL:** Rollback (`mv api_server.py.backup api_server.py`)

---

**Wingman Validation Score:** N/A
**Human Approval Required:** YES
**Security Review Required:** HIGH (critical API modification)
**Status:** AWAITING HUMAN EXECUTION (BLOCKED: Phase 1 must complete first)
