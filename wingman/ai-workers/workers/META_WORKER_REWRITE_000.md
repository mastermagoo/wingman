# META_WORKER: Rewrite WORKER_000 Using Proven Intel-System Pattern

**Date:** 2026-02-06
**Environment:** TEST
**Phase:** 0 (Pre-Phase 1A Quality Gate)
**LLM Provider:** OpenAI
**Status:** READY FOR EXECUTION

---

## 1. DELIVERABLES

- [ ] Rewritten file: `ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md`
- [ ] Test results file: `ai-workers/results/meta-worker-rewrite-000-results.json`

**Exact File Path:** (repo root)/ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md

---

## 2. SUCCESS_CRITERIA

- [ ] WORKER_001 follows intel-system pattern EXACTLY
- [ ] NO shortcuts or variations added
- [ ] TEST_PROCESS uses direct commands with proper exit codes (like intel-system)
- [ ] NO echo wrappers in test commands
- [ ] All 10 sections present and complete
- [ ] File passes validation when read back
- [ ] Isolated output directory: `validation_build/WORKER_001/semantic_analyzer.py`
- [ ] NO dependency language ("first worker in sequence")
- [ ] CLAUDE.md Rule #13 (approval gates) compliance
- [ ] CLAUDE.md Rule #15 (mem0 namespace "wingman") compliance

---

## 3. BOUNDARIES

- **CAN modify:** WORKER_001_Semantic_Class_Skeleton.md only
- **CAN read:** /Volumes/Data/ai_projects/intel-system/ai-workers/workers/WORKER_001_PostgreSQL_TEST_Schema_Creation.md (template)
- **CAN read:** ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md (current version)
- **CANNOT modify:** Any other worker instructions
- **CANNOT add:** Custom test patterns, shortcuts, or variations
- **Idempotency:** Safe to re-run (overwrites existing file)

**Scope Limit:** Rewrite WORKER_001 only - use proven intel-system pattern

---

## 4. DEPENDENCIES

- **Template file:** /Volumes/Data/ai_projects/intel-system/ai-workers/workers/WORKER_001_PostgreSQL_TEST_Schema_Creation.md
- **Current file:** ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md
- **Reference files:** CLAUDE.md, PARALLEL_EXECUTION_PLAN.md, EXECUTION_STRATEGY.md
- **Python environment:** Python 3.9+ with standard library

---

## 5. MITIGATION

- **If template missing:** Escalate immediately (cannot proceed without proven pattern)
- **If current WORKER_001 missing:** Escalate (need to understand current purpose)
- **Rollback:** Keep backup of original WORKER_001 before overwrite
- **Escalation:** If uncertain about pattern, escalate (no guessing allowed)
- **Risk Level:** LOW (file rewrite only)

---

## 6. TEST_PROCESS

```bash
# Test 1: File exists
test -f ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md

# Test 2: Has all 10 sections
test $(grep -c "^## [0-9]\+\." ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md) -eq 10

# Test 3: Uses isolated directory
grep -q "validation_build/WORKER_001" ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md

# Test 4: NO dependency language
! grep -q "first worker in sequence" ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md

# Test 5: Uses wingman namespace
grep -q 'Namespace: "wingman"' ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md

# Test 6: NO echo wrappers in test commands
! grep -q '&& echo "PASS"' ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "META_WORKER_REWRITE_000",
  "status": "pass|fail",
  "deliverables_created": [
    "ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md"
  ],
  "test_results": {
    "file_created": "pass|fail",
    "all_10_sections": "pass|fail",
    "isolated_directory": "pass|fail",
    "no_dependency_language": "pass|fail",
    "wingman_namespace": "pass|fail",
    "no_echo_wrappers": "pass|fail"
  },
  "duration_seconds": 0,
  "timestamp": "2026-02-06T00:00:00Z",
  "errors": []
}
```

---

## 8. TASK_CLASSIFICATION

- **Type:** MECHANICAL
- **Tool:** File reading and writing
- **Reasoning:** Pattern copying from proven template
- **Local-first:** No - Use cloud LLM to ensure accuracy

---

## 9. RETROSPECTIVE

- **Time estimate:** 20 minutes
- **Actual time:** [To be filled after execution]
- **Challenges:** [To be filled after execution]
- **Lessons learned:** [To be filled after execution]
- **Store in mem0:**
  - Key: "wingman_meta_worker_rewrite_000"
  - Namespace: "wingman"
  - Content: WORKER_001 rewrite using intel-system pattern, isolated directories, no dependencies

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Manual execution time: 30 minutes (read template, adapt, write)
- Current process: Manual file editing

**Targets:**
- Automated execution: <20 minutes
- Accuracy: 100% (exact pattern match to intel-system)
- Quality: No shortcuts, no variations

**Monitoring:**
- Before: Verify template file exists
- During: Track file read, pattern adaptation, file write
- After: Validate rewritten file structure
- Degradation limit: If execution takes >40 minutes, abort and escalate

---

## EXECUTION INSTRUCTIONS

Follow these steps EXACTLY (like META_WORKER_WINGMAN_01 pattern):

### Step 1: Read Source Materials (5 minutes)

Read these files in order:
1. `/Volumes/Data/ai_projects/intel-system/ai-workers/workers/WORKER_001_PostgreSQL_TEST_Schema_Creation.md` - Intel-system template
2. `ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md` - Current wingman version
3. Extract current purpose: "Create SemanticAnalyzer class skeleton"

### Step 2: Understand Key Differences (5 minutes)

**Intel-System Pattern (CORRECT):**
- Deliverable: Concrete item (schema, file, function)
- Dependencies: "PostgreSQL TEST running" (service dependency)
- Test commands: `psql -h localhost -p 6432 -U admin ...` (direct command, proper exit code)
- Sections: Exactly 10, clean format

**Current Wingman WORKER_001 (INCORRECT):**
- Deliverable: `validation/semantic_analyzer.py` (WRONG - should be `validation_build/WORKER_001/semantic_analyzer.py`)
- Dependencies: "This is WORKER_001 - first worker in sequence" (position language, WRONG)
- Test commands: `test -f file && echo "PASS" || echo "FAIL"` (echo wrapper, WRONG - always exits 0)
- Sections: 13 sections (WRONG - should be 10)

### Step 3: Rewrite WORKER_001 Following Intel-System Pattern (7 minutes)

For EACH of the 10 sections, apply these transformations:

**1. DELIVERABLES:**
- OLD: `Create file: validation/semantic_analyzer.py`
- NEW: `Create file: validation_build/WORKER_001/semantic_analyzer.py`
- Add: `Create directory: validation_build/WORKER_001/`

**2. SUCCESS_CRITERIA:**
- Keep: Class instantiation checks
- Change: File path to `validation_build/WORKER_001/semantic_analyzer.py`

**3. BOUNDARIES:**
- OLD: `CAN create: New file semantic_analyzer.py in validation/ directory`
- NEW: `CAN create: New file semantic_analyzer.py in validation_build/WORKER_001/ directory`
- Add: `CANNOT modify: validation/ directory (shared space)`

**4. DEPENDENCIES:**
- OLD: `No prior workers: This is WORKER_001 - first worker in sequence`
- NEW: `Python 3.9+ with standard library (no service dependencies)`
- Remove: ALL position/sequence language

**5. MITIGATION:**
- Update: References to file paths use `validation_build/WORKER_001/`
- Update: Rollback uses `rm -rf validation_build/WORKER_001/`

**6. TEST_PROCESS:**
- OLD: `test -f validation/semantic_analyzer.py && echo "PASS: File exists" || echo "FAIL: File missing"`
- NEW: `test -f validation_build/WORKER_001/semantic_analyzer.py`
- OLD: `python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; print('PASS: Import successful')" || echo "FAIL: Import failed"`
- NEW: `python3 -c "import sys; sys.path.insert(0, 'validation_build/WORKER_001'); from semantic_analyzer import SemanticAnalyzer; assert SemanticAnalyzer"`

**Remove ALL echo statements. Commands must return proper exit codes (0=pass, non-zero=fail).**

**7. TEST_RESULTS_FORMAT:**
- Keep: JSON structure
- Update: All file paths to `validation_build/WORKER_001/`

**8. TASK_CLASSIFICATION:**
- Keep: MECHANICAL, Python file writing

**9. RETROSPECTIVE:**
- Add: `Namespace: "wingman"` (CLAUDE.md Rule #15)
- Add: Store execution time, path configuration issues

**10. PERFORMANCE_REQUIREMENTS:**
- Keep: Baseline/targets/monitoring structure

**Remove sections 8-10 from current file (RESOURCE_REQUIREMENTS, RISK_ASSESSMENT, QUALITY_METRICS).**

### Step 4: Save Rewritten File (1 minute)

Save to: `ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md`

### Step 5: Validation Check (2 minutes)

Run all 6 test commands from TEST_PROCESS section:
1. File exists
2. Has all 10 sections (not 13)
3. Uses isolated directory `validation_build/WORKER_001`
4. NO dependency language ("first worker in sequence")
5. Uses wingman namespace
6. NO echo wrappers

All 6 tests must PASS.

---

## QUALITY STANDARDS

The rewritten instruction must:
- ✅ Have EXACTLY 10 POINTS (not 13)
- ✅ Use isolated directory: `validation_build/WORKER_001/semantic_analyzer.py`
- ✅ Have NO dependency language (no "first worker", no "prior workers")
- ✅ Use direct test commands with proper exit codes (NO echo wrappers)
- ✅ Reference CLAUDE.md Rule #13 (approval gates for destructive ops)
- ✅ Reference CLAUDE.md Rule #15 (mem0 namespace "wingman")
- ✅ Match intel-system structure EXACTLY

---

## SUCCESS CRITERIA

**Meta-Worker REWRITE_000 Complete When:**
- ✅ WORKER_001.md file rewritten
- ✅ All 6 validation tests pass
- ✅ File follows intel-system pattern EXACTLY
- ✅ No shortcuts taken
- ✅ Ready for WORKER_001 execution

**Expected Duration:** 20 minutes
**Output:** 1 rewritten worker instruction file + test results JSON

---

**Reference:**
- Intel-System Template: /Volumes/Data/ai_projects/intel-system/ai-workers/workers/WORKER_001_PostgreSQL_TEST_Schema_Creation.md
- Proven META_WORKER Pattern: ai-workers/workers/META_WORKER_WINGMAN_01_INSTRUCTION.md
- CLAUDE.md Rules #13, #15

**Wingman Validation Score:** [To be filled]
**Wingman Status:** READY FOR EXECUTION
