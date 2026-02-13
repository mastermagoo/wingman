# Worker 092: Composite Validator Auto Reject Logic

**Date:** 2026-01-13
**Environment:** TEST
**Phase:** 3.1 - Composite Validator
**Duration:** 20 minutes
**Status:** READY FOR EXECUTION

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/composite_validator.py`
- [ ] Implement auto-reject logic in `_determine_recommendation()`
- [ ] Condition 1: final_score < 60 → AUTO_REJECT
- [ ] Condition 2: risk_level == 'CRITICAL' → AUTO_REJECT (regardless of score)
- [ ] Add reasoning field explaining auto-reject decision
- [ ] Test with 6 scenarios (including edge cases at score=60)
- [ ] Test results file: `ai-workers/results/worker-092-results.json`

---

## 2. SUCCESS_CRITERIA

- [ ] Score 50 → AUTO_REJECT
- [ ] Score 59 → AUTO_REJECT (just below threshold)
- [ ] Score 60 → MANUAL_REVIEW (at threshold)
- [ ] CRITICAL risk + score 100 → AUTO_REJECT (risk override)
- [ ] HIGH risk + score 50 → AUTO_REJECT (both conditions)
- [ ] Reasoning field populated for all rejections

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

- WORKER_091 complete (auto-approve logic)

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
cd wingman && python3 -c "from validation.composite_validator import CompositeValidator; v=CompositeValidator(); assert v._determine_recommendation('LOW', 50) == 'AUTO_REJECT'; assert v._determine_recommendation('LOW', 59) == 'AUTO_REJECT'; assert v._determine_recommendation('LOW', 60) == 'MANUAL_REVIEW'; assert v._determine_recommendation('CRITICAL', 100) == 'AUTO_REJECT'; print('PASS: Auto-reject logic correct')"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "092",
  "worker_name": "Composite_Validator_Auto_Reject_Logic",
  "status": "pass|fail",
  "deliverables_created": [
    "Implement auto-reject logic in `_determine_recommendation()`",
    "Condition 1: final_score < 60 \u2192 AUTO_REJECT"
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
  - Key: "wingman_worker_092_retrospective"
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
