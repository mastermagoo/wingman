# Worker 007: End-to-End Enforcement Testing

**Date:** 2026-01-07
**Environment:** TEST
**Phase:** 3 (Validation)
**Task Owner:** Human Operator (Mark)
**AI Assistant:** Claude (Sonnet 4.5) - Draft test suite only
**Status:** PENDING EXECUTION (Blocked until Phase 2 complete)

---

## 1. DELIVERABLES

- [ ] `wingman/tests/test_e2e_enforcement.py` - Comprehensive E2E test suite (AI draft, human reviews)
- [ ] `wingman/tests/test_penetration.py` - Bypass attempt tests (AI draft, human reviews)
- [ ] `wingman/tests/test_performance.py` - Performance benchmarks (AI draft, human reviews)
- [ ] `wingman/tests/test_false_positives.py` - False positive analysis (AI draft, human reviews)
- [ ] `ai-workers/results/worker-007-results.json` - Execution results (human creates)

---

## 2. SUCCESS_CRITERIA

- [ ] E2E tests pass: approval request → consensus → approval → token → execution → audit
- [ ] Penetration tests pass: all bypass attempts blocked (no token, expired, forged, replay, out-of-scope)
- [ ] False positive rate <5% (legitimate work not blocked)
- [ ] False negative rate 0% (all attacks blocked)
- [ ] Performance tests pass: approval flow <5s, execution <100ms, consensus <30s
- [ ] Multi-environment tests pass (TEST and PRD stacks)
- [ ] Rollback tests pass (can revert to pre-enforcement state)
- [ ] All tests automated (can run in CI/CD)

---

## 3. BOUNDARIES

**CAN:**
- Create comprehensive test suites in `tests/` directory
- Test all enforcement components (consensus, gateway, allowlist, audit)
- Attempt penetration/bypass tests (in TEST environment only)
- Measure performance metrics
- Validate audit logs

**CANNOT:**
- Modify implementation code (Workers 001-006 did that)
- Run penetration tests in PRD (TEST only)
- Disable enforcement to pass tests (tests must validate real enforcement)
- Skip any security test scenarios

**MUST:**
- Test all documented bypass scenarios
- Verify audit trail for every test
- Measure and report performance
- Test backward compatibility (existing approval flows work)
- Test failure modes (consensus timeout, gateway down, etc.)
- Provide clear pass/fail evidence for each test

---

## 4. DEPENDENCIES

**Hard Dependencies:**
- Phase 1 complete (Workers 001-004)
- Phase 2 complete (Workers 005-006)
- TEST stack running with enforcement layer deployed
- All enforcement components healthy

**Blocking:** Cannot start until Phase 2 complete (Workers 005 and 006 done)

---

## 5. MITIGATION

**If E2E tests fail:**
- Review logs to identify which layer failed (consensus/gateway/audit)
- Trace through approval flow step-by-step
- Verify configuration (tokens, network, database)
- Fix root cause in relevant worker component

**If penetration tests fail (bypass succeeds):**
- **CRITICAL SECURITY ISSUE** - halt deployment immediately
- Identify which attack vector succeeded
- Fix vulnerability in relevant component
- Re-run ALL tests after fix
- Do not proceed to Phase 4 until all pen tests pass

**If false positive rate >5%:**
- Review allowlist rules (Worker 002)
- Review consensus prompts (Worker 003)
- Tune thresholds and patterns
- Re-test with adjusted configuration

**If performance tests fail:**
- Identify bottleneck (consensus is likely slowest)
- Consider async consensus (don't block approval)
- Optimize database queries (audit logging)
- May need infrastructure scaling

**Rollback:**
- Tests are non-destructive (no rollback needed)
- If enforcement layer must be removed: revert Workers 005 and 006 changes

**Escalation:**
- If any penetration test succeeds: immediate security review, no deployment
- If performance degradation >10s per approval: tune or make consensus async

**Risk Level:** CRITICAL (validates entire security posture, gates production deployment)

---

## 6. TEST_PROCESS

### E2E Test Suite
```bash
# After all Phase 1 and 2 workers complete:

# 1. Verify TEST stack healthy
docker compose -f docker-compose.yml -p wingman-test ps

# Expected: All services "Up" including execution-gateway

# 2. Run E2E test suite
pytest tests/test_e2e_enforcement.py -v --tb=short

# Expected tests:
# - test_full_approval_flow_low_risk (auto-approve → execute)
# - test_full_approval_flow_high_risk (consensus → pending → human approve → execute)
# - test_approval_rejection_flow (human rejects → no token → execution blocked)
# - test_consensus_integration (3 LLMs queried, 2/3 threshold)
# - test_token_issuance_on_approval (JWT token returned)
# - test_gateway_execution_with_token (command executed via gateway)
# - test_audit_trail_complete (all steps logged)
# - test_backward_compatibility (existing approval API still works)

# 3. Run penetration test suite
pytest tests/test_penetration.py -v --tb=short

# Expected tests:
# - test_no_token_blocked (POST /gateway/execute without token → 401)
# - test_expired_token_blocked (expired JWT → 401)
# - test_forged_token_blocked (invalid signature → 401)
# - test_replay_token_blocked (same token twice → 403)
# - test_out_of_scope_file_blocked (test token, prd file → 403)
# - test_dangerous_flag_blocked (--force flag → 403)
# - test_environment_mismatch_blocked (test token, prd command → 403)
# - test_command_injection_blocked (malicious command → 403)
# - test_docker_socket_not_accessible (api server cannot access socket → pass)
# - test_gateway_isolation (cannot bypass gateway → pass)

# 4. Run performance test suite
pytest tests/test_performance.py -v --tb=short

# Expected tests:
# - test_approval_latency (baseline <500ms, with consensus <5s)
# - test_token_validation_latency (<10ms)
# - test_gateway_execution_latency (<100ms)
# - test_audit_log_write_latency (<50ms)
# - test_consensus_latency (<30s for 3 LLMs in parallel)
# - test_allowlist_validation_latency (<20ms)

# 5. Run false positive analysis
pytest tests/test_false_positives.py -v --tb=short

# Expected tests:
# - test_valid_docker_compose_commands (20 legitimate commands → all pass)
# - test_valid_test_environment_work (test scope operations → all pass)
# - test_valid_prd_environment_work (prd scope operations with prd token → all pass)
# - test_false_positive_rate (<5%)
```

### Manual Penetration Testing
```bash
# After automated tests pass, manual penetration attempts:

# 1. Attempt to execute without approval
curl -X POST http://localhost:5001/gateway/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "docker compose ps", "approval_id": "none"}'

# Expected: 401 Unauthorized (no token)

# 2. Attempt to forge token
curl -X POST http://localhost:5001/gateway/execute \
  -H "X-Capability-Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.forged.token" \
  -H "Content-Type: application/json" \
  -d '{"command": "docker compose ps", "approval_id": "fake"}'

# Expected: 401 Unauthorized (invalid signature)

# 3. Attempt to access docker socket from API
docker compose -f docker-compose.yml -p wingman-test exec wingman-api \
  python -c "import docker; docker.from_env().containers.list()"

# Expected: Error (no docker socket access)

# 4. Attempt to use test token for prd file
# (Get valid test token, try to execute prd command)
# Expected: 403 Forbidden (out of scope)

# 5. Attempt command injection
TOKEN=$(python -c "from capability_token import generate_token; print(generate_token('test'))")
curl -X POST http://localhost:5001/gateway/execute \
  -H "X-Capability-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "echo test && rm -rf /", "approval_id": "test"}'

# Expected: 403 Forbidden (command injection blocked by allowlist)
```

### Audit Trail Validation
```bash
# After running tests, verify audit trail:

psql -h localhost -p 6432 -U admin -d wingman_test -c "
  SELECT
    execution_id,
    approval_id,
    command,
    exit_code,
    created_at
  FROM execution_audit
  ORDER BY created_at DESC
  LIMIT 20;
"

# Expected: All E2E test executions logged
# Expected: All penetration test attempts logged (including blocked ones)
# Expected: No UPDATE or DELETE operations on audit table (append-only)
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "007",
  "task": "End-to-End Enforcement Testing",
  "status": "pass|fail",
  "deliverables_created": [
    "wingman/tests/test_e2e_enforcement.py",
    "wingman/tests/test_penetration.py",
    "wingman/tests/test_performance.py",
    "wingman/tests/test_false_positives.py"
  ],
  "test_results": {
    "e2e_tests_pass": true,
    "e2e_test_count": 8,
    "penetration_tests_pass": true,
    "penetration_test_count": 10,
    "performance_tests_pass": true,
    "performance_test_count": 6,
    "false_positive_tests_pass": true,
    "false_positive_rate": "2.5%",
    "false_negative_rate": "0%",
    "all_bypass_attempts_blocked": true,
    "audit_trail_complete": true,
    "backward_compatibility": "pass"
  },
  "evidence": {
    "pytest_output": "24 passed, 0 failed",
    "penetration_summary": "10/10 attacks blocked",
    "performance_summary": {
      "approval_latency_ms": 3200,
      "token_validation_ms": 8,
      "gateway_execution_ms": 85,
      "audit_log_write_ms": 42,
      "consensus_latency_ms": 2800
    },
    "false_positive_rate": 0.025,
    "false_negative_rate": 0.0,
    "audit_record_count": 34,
    "security_posture": "STRONG"
  },
  "duration_minutes": 90,
  "timestamp": "2026-01-07T...",
  "human_operator": "Mark",
  "ai_assistance": "Claude drafted test suites, human reviewed and executed"
}
```

---

## 8. TASK_CLASSIFICATION

- **Type:** VALIDATION (comprehensive security testing)
- **Complexity:** HIGH (E2E flows, penetration testing, performance analysis)
- **Tool:** Pytest + curl + psql + performance profiling
- **Reasoning:** Validates entire enforcement layer, gates production deployment
- **Human-Led:** YES - AI drafts test code, human reviews ALL tests before running
- **AI Role:** Test generation assistant only, no autonomous execution

---

## 9. RETROSPECTIVE

**Time estimate:** 60 minutes (AI draft) + 30 minutes (human review/execution) = 90 minutes total

**Actual time:** [To be filled after execution]

**Challenges:** [To be filled after execution]

**Penetration test findings:** [To be filled - any successful bypasses?]

**Performance bottlenecks:** [To be filled - what's the slowest component?]

**False positive analysis:** [To be filled - legitimate work blocked?]

**Store in mem0:**
- E2E test patterns for capability-based systems
- Penetration testing checklist for token-based enforcement
- Performance benchmarking for multi-layer security

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Manual testing: 2-3 hours (human tests each scenario)
- Current process: Ad-hoc testing, no penetration tests

**Targets:**
- AI test generation: <60 minutes
- Human review/execution: <30 minutes
- Automated test suite runtime: <5 minutes (all tests)
- Penetration test coverage: 100% of documented attack vectors

**Quality:**
- 100% of bypass attempts blocked (zero false negatives)
- <5% false positive rate (legitimate work not blocked)
- All tests automated (repeatable in CI/CD)
- Complete audit trail for all test executions

**Monitoring:**
- Before: Verify TEST stack healthy, all enforcement components deployed
- During: Track test failures, identify root causes
- After: Review comprehensive test report, verify all success criteria met
- Degradation limit: If ANY penetration test succeeds, HALT deployment

---

## EXECUTION INSTRUCTIONS (HUMAN OPERATOR)

### Step 1: Prerequisites Check
Verify Phase 1 and Phase 2 complete:
- [ ] Workers 001-004 complete (Phase 1)
- [ ] Workers 005-006 complete (Phase 2)
- [ ] TEST stack running with enforcement layer
- [ ] All services healthy

### Step 2: Request AI Test Suite
Ask AI to generate comprehensive test files:
1. `test_e2e_enforcement.py` - Full approval → execution flows
2. `test_penetration.py` - All documented bypass attempts
3. `test_performance.py` - Latency benchmarks for each component
4. `test_false_positives.py` - Legitimate work validation

### Step 3: Human Security Review
Review AI-generated tests for:
- [ ] All attack vectors from threat model covered
- [ ] Tests actually validate enforcement (not just mocked)
- [ ] Penetration tests run in TEST only
- [ ] Performance thresholds realistic
- [ ] False positive test cases representative

### Step 4: Apply Tests (Manual)
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman
nano tests/test_e2e_enforcement.py
nano tests/test_penetration.py
nano tests/test_performance.py
nano tests/test_false_positives.py
```

### Step 5: Run Automated Tests
```bash
pytest tests/test_e2e_enforcement.py -v
pytest tests/test_penetration.py -v
pytest tests/test_performance.py -v
pytest tests/test_false_positives.py -v
```

### Step 6: Manual Penetration Testing
Follow manual penetration testing section, verify all attacks blocked.

### Step 7: Validate Audit Trail
Query PostgreSQL, verify all test executions logged.

### Step 8: Performance Analysis
Review performance test results, identify any bottlenecks.

### Step 9: Record Results
Create `ai-workers/results/worker-007-results.json` with comprehensive evidence.

### Step 10: Gate Decision (CRITICAL)
- **PASS:** All tests passing, all attacks blocked → Proceed to Phase 4 (deployment)
- **FAIL:** ANY penetration test succeeds → HALT, fix vulnerability, re-run ALL tests
- **PERFORMANCE DEGRADATION:** If approval flow >10s → tune or make consensus async

---

## CRITICAL DEPLOYMENT GATE

**Before proceeding to Phase 4 (deployment):**
- [ ] ALL E2E tests passing (8/8)
- [ ] ALL penetration tests passing (10/10 attacks blocked)
- [ ] False negative rate: 0%
- [ ] False positive rate: <5%
- [ ] Performance acceptable (<5s approval, <100ms execution)
- [ ] Audit trail complete and immutable
- [ ] Backward compatibility verified
- [ ] Human operator reviews and approves test results

**If ANY criterion fails: DO NOT DEPLOY TO PRODUCTION**

---

**Wingman Validation Score:** N/A
**Human Approval Required:** YES (CRITICAL - gates production deployment)
**Security Review Required:** CRITICAL (final security validation before deployment)
**Status:** AWAITING HUMAN EXECUTION (BLOCKED: Phase 2 must complete first)
