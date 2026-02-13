# Worker 096: API Server Validation In Request Flow

**Date:** 2026-01-13
**Environment:** TEST
**Phase:** 3.2 - API Integration
**Duration:** 20 minutes
**Status:** READY FOR EXECUTION

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/composite_validator.py`
- [ ] Modify POST /approvals/request to call validation
- [ ] Run validation BEFORE creating approval record
- [ ] Store validation results in approval record (new field)
- [ ] If AUTO_REJECT: return 400 with rejection reason
- [ ] If AUTO_APPROVE: set status=AUTO_APPROVED
- [ ] Test results file: `ai-workers/results/worker-096-results.json`

---

## 2. SUCCESS_CRITERIA

- [ ] Validation runs on every approval request
- [ ] AUTO_REJECT requests return 400 immediately
- [ ] AUTO_APPROVE requests skip manual review queue
- [ ] Validation results saved in database
- [ ] Manual review requests include validation in notification

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

- WORKER_095 complete (validators imported)

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
curl -X POST http://localhost:8001/approvals/request -H 'Content-Type: application/json' -d '{"instruction": "DELIVERABLES: Do it\nSUCCESS_CRITERIA: none\n", "task_name": "bad", "deployment_env": "test"}' -w '%{http_code}' | grep 400
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "096",
  "worker_name": "API_Server_Validation_In_Request_Flow",
  "status": "pass|fail",
  "deliverables_created": [
    "Modify POST /approvals/request to call validation",
    "Run validation BEFORE creating approval record"
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
  - Key: "wingman_worker_096_retrospective"
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
