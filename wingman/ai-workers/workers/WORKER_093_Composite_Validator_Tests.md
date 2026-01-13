# Worker 093: Composite Validator Tests

**Date:** 2026-01-13
**Environment:** TEST
**Phase:** 3.1 - Composite Validator
**Duration:** 20 minutes
**Status:** READY FOR EXECUTION

---

## 1. DELIVERABLES

- [ ] Create file: `wingman/tests/test_composite_validator.py`
- [ ] Test 1: All validators called successfully
- [ ] Test 2: Score calculation with mock validator results
- [ ] Test 3: Auto-approve decision (LOW risk, quality 95)
- [ ] Test 4: Auto-reject decision (quality 50)
- [ ] Test 5: Manual review decision (MEDIUM risk, quality 75)
- [ ] Test results file: `ai-workers/results/worker-093-results.json`

---

## 2. SUCCESS_CRITERIA

- [ ] 5/5 tests pass
- [ ] `pytest wingman/tests/test_composite_validator.py` returns 0 exit code
- [ ] All code paths covered (auto-approve, auto-reject, manual)

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

- WORKER_088-092 complete (CompositeValidator fully implemented)

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
cd wingman && pytest tests/test_composite_validator.py -v --tb=short
cd wingman && pytest tests/test_composite_validator.py --cov=validation.composite_validator --cov-report=term-missing
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "093",
  "worker_name": "Composite_Validator_Tests",
  "status": "pass|fail",
  "deliverables_created": [
    "Create file: `wingman/tests/test_composite_validator.py`",
    "Test 1: All validators called successfully"
  ],
  "test_results": {
    "test_1": "pass|fail",
    "test_2": "pass|fail"
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
  - Key: "wingman_worker_093_retrospective"
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
