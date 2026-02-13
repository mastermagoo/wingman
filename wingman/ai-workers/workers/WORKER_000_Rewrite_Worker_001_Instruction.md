# Worker 000: Rewrite WORKER_001 Instruction

**Date:** 2026-02-05
**Environment:** TEST
**Phase:** 0 (Pre-Phase 1A Quality Gate)
**LLM Provider:** OpenAI
**Status:** PENDING VALIDATION

---

## 1. DELIVERABLES

- [ ] Rewritten file: `ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md`
- [ ] Test results file: `ai-workers/results/worker-000-results.json`

**Exact File Path:** (repo root)/ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md

---

## 2. SUCCESS_CRITERIA

- [ ] WORKER_001.md rewritten with NO dependencies on other workers
- [ ] Isolated output directory specified: `validation_build/WORKER_001/semantic_analyzer.py`
- [ ] Test commands use proper exit codes (no echo wrappers)
- [ ] CLAUDE.md Rule #13 mentioned in MITIGATION
- [ ] CLAUDE.md Rule #15 mem0 namespace "wingman" in RETROSPECTIVE
- [ ] All 10 sections present and complete
- [ ] Based on intel-system WORKER_001 pattern (creates deliverables)

---

## 3. BOUNDARIES

- **CAN modify:** WORKER_001_Semantic_Class_Skeleton.md file only
- **CANNOT modify:** Any other worker instruction files
- **CAN create:** New version of WORKER_001 instruction
- **CANNOT restart:** No services affected
- **Idempotency:** Backup original before overwriting (safe to re-run)

---

## 4. DEPENDENCIES

- **Template file:** /Volumes/Data/ai_projects/intel-system/ai-workers/workers/WORKER_001_PostgreSQL_TEST_Schema_Creation.md
- **Original file:** ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md
- **Reference files:** CLAUDE.md, PRODUCTION_ORCHESTRATION_ARCHITECTURE.md
- **No external services:** File operations only

---

## 5. MITIGATION

- **If template missing:** Escalate immediately (cannot proceed)
- **If original missing:** Create new from scratch
- **If rewrite fails:** Restore from backup
- **Rollback:** Keep backup at WORKER_001_Semantic_Class_Skeleton.md.backup
- **Escalation:** If uncertain about pattern, escalate
- **Risk Level:** Low (file rewrite only)

---

## 6. TEST_PROCESS

```bash
# Test 1: Rewritten file exists
test -f ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md

# Test 2: Has all 10 sections
test $(grep -c "^## [0-9]\\+\\." ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md) -eq 10

# Test 3: Uses isolated directory
grep -q "validation_build/WORKER_001" ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md

# Test 4: No dependency on other workers
grep -q "No prior workers" ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md

# Test 5: mem0 namespace is "wingman"
grep -q 'Namespace: "wingman"' ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": 0,
  "status": "pass/fail",
  "deliverables_created": [
    "ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md"
  ],
  "test_results": {
    "file_exists": "pass/fail",
    "all_10_sections": "pass/fail",
    "isolated_directory": "pass/fail",
    "no_dependencies": "pass/fail",
    "correct_mem0_namespace": "pass/fail"
  },
  "evidence": "Rewritten WORKER_001 instruction",
  "duration": "time in seconds",
  "timestamp": "2026-02-05T17:00:00"
}
```

---

## 8. TASK_CLASSIFICATION

- **Type:** MECHANICAL
- **Tool:** File reading and writing
- **Reasoning:** Pattern-based rewrite following proven template
- **Local-first:** No - Use cloud LLM for accuracy

---

## 9. RETROSPECTIVE

- **Time estimate:** 5-10 minutes
- **Actual time:** [To be filled after execution]
- **Challenges:** [To be filled after execution]
- **Lessons learned:** [To be filled after execution]
- **Store in mem0:**
  - Key: "wingman_worker_000_retrospective"
  - Namespace: "wingman"
  - Content: WORKER_001 rewrite completed, dependency removed, isolated directory added

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Manual execution time: 15 minutes (read template, adapt, write)
- Current process: Manual file editing

**Targets:**
- Automated execution: <10 minutes
- Accuracy: 100% (follow intel-system pattern exactly)
- Quality: All requirements met, no shortcuts

**Monitoring:**
- Before: Verify template exists, backup original
- During: Track file read, adaptation, write
- After: Run all 5 test commands, verify 5/5 pass
- Degradation limit: If execution takes >20 minutes, abort and escalate

---

## REWRITE REQUIREMENTS

### Key Changes from Current WORKER_001

**REMOVE:**
1. Dependency on validation/ directory existing → create validation_build/WORKER_001/ instead
2. "This is WORKER_001 - first worker in sequence" → make truly independent
3. File path `validation/semantic_analyzer.py` → use `validation_build/WORKER_001/semantic_analyzer.py`

**ADD:**
1. Isolated output directory: `validation_build/WORKER_001/`
2. No dependencies statement: "This worker is independent - no prior workers required"
3. Proper test commands (no echo wrappers)
4. CLAUDE.md Rule #13 in MITIGATION
5. mem0 namespace "wingman" in RETROSPECTIVE

**KEEP:**
1. Same goal: Create SemanticAnalyzer class skeleton
2. Same structure: All 10 sections
3. Same deliverable type: Python file with class

### Test Commands Format (Intel-System Style)

```bash
# WRONG (current):
test -f validation/semantic_analyzer.py && echo "PASS" || echo "FAIL"

# RIGHT (intel-system):
test -f validation_build/WORKER_001/semantic_analyzer.py
```

**No echo wrappers. Direct commands only.**

---

**Reference Files:**
- Template: /Volumes/Data/ai_projects/intel-system/ai-workers/workers/WORKER_001_PostgreSQL_TEST_Schema_Creation.md
- Original: ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md
- Architecture: PRODUCTION_ORCHESTRATION_ARCHITECTURE.md (lines 401-402: isolated directories)
- CLAUDE.md (Rule #13, Rule #15)

**Wingman Validation Score:** [To be filled]
**Wingman Status:** PENDING
