# Worker 094: API Server Validate Endpoint

**Date:** 2026-01-13
**Environment:** TEST
**Phase:** 3.2 - API Integration
**Duration:** 20 minutes
**Status:** READY FOR EXECUTION

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/composite_validator.py`
- [ ] Add `/approvals/validate` POST endpoint to `api_server.py`
- [ ] Accept JSON: {instruction, task_name, deployment_env}
- [ ] Call CompositeValidator.validate()
- [ ] Return validation results as JSON
- [ ] Test results file: `ai-workers/results/worker-094-results.json`

---

## 2. SUCCESS_CRITERIA

- [ ] Endpoint responds to POST /approvals/validate
- [ ] Returns 200 OK with validation results
- [ ] Returns 400 Bad Request for invalid input
- [ ] Validation results include: semantic, code, dependency, content, final_score, recommendation

---

## 3. BOUNDARIES

- **CAN create:** New files/methods as specified in DELIVERABLES
- **CAN modify:** Existing validation files to add new functionality
- **CANNOT modify:** Core API logic unrelated to validation, database schema (unless explicitly required)
- **CANNOT add:** Features beyond scope of this worker
- **Idempotency:** Check if deliverable exists; if exists, validate and update only if needed

**Scope Limit:** 20-minute execution - focused implementation only

---

## 4. DEPENDENCIES

- WORKER_093 complete (CompositeValidator fully tested)
- API server running (docker compose up)

---

## 5. MITIGATION

- **If file/method missing:** Create as specified
- **If import fails:** Check Python path, verify dependencies installed
- **If tests fail:** Review error logs, fix implementation, re-run tests
- **Rollback:** Revert changes to modified files using git (if committed)
- **Escalation:** If validators unavailable or LLM service down, escalate to human (critical dependency)
- **Risk Level:** LOW (new feature, no destructive operations)

---

## 6. TEST_PROCESS

```bash
curl -X POST http://localhost:8001/approvals/validate -H 'Content-Type: application/json' -d '{"instruction": "DELIVERABLES: Test\nSUCCESS_CRITERIA: Test\n...", "task_name": "test", "deployment_env": "test"}' | jq '.final_score'
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "094",
  "worker_name": "API_Server_Validate_Endpoint",
  "status": "pass|fail",
  "deliverables_created": [
    "Add `/approvals/validate` POST endpoint to `api_server.py`",
    "Accept JSON: {instruction, task_name, deployment_env}"
  ],
  "test_results": {
    "test_1": "pass|fail"
  },
  "duration_seconds": 0,
  "timestamp": "2026-01-13T00:00:00Z",
  "errors": []
}
```

---

## 8. TASK_CLASSIFICATION

- **Type:** MECHANICAL
- **Tool:** Python file editing, API testing
- **Reasoning:** Implementation follows clear specification with defined behavior
- **Local-first:** Yes - file operations, local testing
- **AI Assistance:** Minimal - template-based implementation

---

## 9. RETROSPECTIVE

- **Time estimate:** 20 minutes
- **Actual time:** [To be filled after execution]
- **Challenges:** [To be filled after execution]
- **Lessons learned:** [To be filled after execution]
- **Store in mem0:**
  - Key: "wingman_worker_094_retrospective"
  - Namespace: "wingman"
  - Content: Execution time, any issues encountered, test results

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Manual execution time: 30-45 minutes
- Current process: Manual coding + testing

**Targets:**
- Automated execution: <20 minutes (includes testing)
- Accuracy: >95% (clear specification)
- Quality: All tests pass, code follows existing patterns

**Monitoring:**
- Before: Verify dependencies available
- During: Track implementation progress, test execution
- After: Run all test commands, verify all pass
- Degradation limit: If execution takes >40 minutes (2x estimate), abort and escalate

---

**Reference:**
- Implementation Plan: `/Volumes/Data/ai_projects/wingman-system/wingman/docs/VALIDATION_ENHANCEMENT_IMPLEMENTATION_PLAN.md`
- Meta-Worker: `META_WORKER_WINGMAN_03_INSTRUCTION.md`


**Wingman Validation Score:** [To be filled]
**Wingman Status:** PENDING APPROVAL
