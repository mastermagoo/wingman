# Worker 091: Composite Validator Auto Approve Logic

**Date:** 2026-01-13
**Environment:** TEST
**Phase:** 3.1 - Composite Validator
**Duration:** 20 minutes
**Status:** READY FOR EXECUTION

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/composite_validator.py`
- [ ] Implement auto-approve logic in `_determine_recommendation()`
- [ ] Condition: risk_level == 'LOW' AND final_score >= 90
- [ ] Return 'AUTO_APPROVE' when conditions met
- [ ] Add reasoning field explaining auto-approve decision
- [ ] Test with 5 scenarios (including edge cases at score=90)
- [ ] Test results file: `ai-workers/results/worker-091-results.json`

---

## 2. SUCCESS_CRITERIA

- [ ] LOW risk + score 95 → AUTO_APPROVE
- [ ] LOW risk + score 90 → AUTO_APPROVE (boundary)
- [ ] LOW risk + score 89.9 → MANUAL_REVIEW (just below boundary)
- [ ] MEDIUM risk + score 95 → MANUAL_REVIEW (not auto-approved)
- [ ] HIGH risk + score 95 → MANUAL_REVIEW (not auto-approved)

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

- WORKER_090 complete (score calculation)

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
cd wingman && python3 -c "from validation.composite_validator import CompositeValidator; v=CompositeValidator(); assert v._determine_recommendation('LOW', 95) == 'AUTO_APPROVE'; assert v._determine_recommendation('LOW', 90) == 'AUTO_APPROVE'; assert v._determine_recommendation('LOW', 89.9) == 'MANUAL_REVIEW'; assert v._determine_recommendation('MEDIUM', 95) == 'MANUAL_REVIEW'; print('PASS: Auto-approve logic correct')"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "091",
  "worker_name": "Composite_Validator_Auto_Approve_Logic",
  "status": "pass|fail",
  "deliverables_created": [
    "Implement auto-approve logic in `_determine_recommendation()`",
    "Condition: risk_level == 'LOW' AND final_score >= 90"
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
  - Key: "wingman_worker_091_retrospective"
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
