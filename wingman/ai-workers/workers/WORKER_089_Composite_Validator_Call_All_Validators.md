# Worker 089: Composite Validator Call All Validators

**Date:** 2026-01-13
**Environment:** TEST
**Phase:** 3.1 - Composite Validator
**Duration:** 20 minutes
**Status:** READY FOR EXECUTION

---

## 1. DELIVERABLES

- [ ] Implement `validate()` method in `CompositeValidator`
- [ ] Call semantic_analyzer.analyze(instruction, task_name, env)
- [ ] Call code_scanner.scan(instruction)
- [ ] Call dependency_analyzer.analyze(instruction, task_name, env)
- [ ] Call content_quality_validator.assess(instruction)
- [ ] Collect all 4 validator results
- [ ] Test results file: `ai-workers/results/worker-089-results.json`

---

## 2. SUCCESS_CRITERIA

- [ ] `validate()` method exists and callable
- [ ] Calls all 4 validators in sequence
- [ ] Returns dict with 4 result sets: semantic, code, dependency, content
- [ ] Test with sample instruction: all 4 validators executed
- [ ] Error handling: if one validator fails, others still run

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

- WORKER_088 complete (CompositeValidator skeleton)
- All 4 validators fully implemented (Phase 1-2)

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
cd wingman && python3 -c "from validation.composite_validator import CompositeValidator; v=CompositeValidator(); result=v.validate('DELIVERABLES: Test\nSUCCESS_CRITERIA: Test\n...', 'test', 'test'); assert 'semantic' in result; assert 'code' in result; assert 'dependency' in result; assert 'content' in result; print('PASS: All validators called')"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "089",
  "worker_name": "Composite_Validator_Call_All_Validators",
  "status": "pass|fail",
  "deliverables_created": [
    "Implement `validate()` method in `CompositeValidator`",
    "Call semantic_analyzer.analyze(instruction, task_name, env)"
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
  - Key: "wingman_worker_089_retrospective"
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
