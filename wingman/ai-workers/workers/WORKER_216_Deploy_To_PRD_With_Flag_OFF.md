# Worker 216: Deploy To PRD With Flag OFF

**Date:** 2026-01-13
**Environment:** TEST
**Phase:** 5.3 - PRD Deployment
**Duration:** 20 minutes
**Status:** READY FOR EXECUTION

---

## 1. DELIVERABLES

- [ ] Deploy new code to PRD with VALIDATION_ENABLED=false
- [ ] Restart PRD stack
- [ ] Verify all services healthy
- [ ] Verify existing approvals still work (no regression)
- [ ] Test results file: `ai-workers/results/worker-216-results.json`

---

## 2. SUCCESS_CRITERIA

- [ ] PRD deployment successful
- [ ] All services healthy
- [ ] Existing approval flow works (validation disabled)
- [ ] No errors in logs

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

- WORKER_215 complete (pre-deployment checklist)

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
docker compose -f wingman/docker-compose.prd.yml -p wingman-prd --env-file wingman/.env.prd ps
curl http://localhost:8002/health
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "216",
  "worker_name": "Deploy_To_PRD_With_Flag_OFF",
  "status": "pass|fail",
  "deliverables_created": [
    "Deploy new code to PRD with VALIDATION_ENABLED=false",
    "Restart PRD stack"
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
- **Tool:** Python file editing, API testing, pytest
- **Reasoning:** Implementation follows clear specification with defined behavior
- **Local-first:** Yes - file operations, local testing
- **AI Assistance:** Minimal to moderate - template-based implementation

---

## 9. RETROSPECTIVE

- **Time estimate:** 20 minutes
- **Actual time:** [To be filled after execution]
- **Challenges:** [To be filled after execution]
- **Lessons learned:** [To be filled after execution]
- **Store in mem0:**
  - Key: "wingman_worker_216_retrospective"
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
