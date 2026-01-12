# Meta-Worker WINGMAN-01: Generate Phase 1 Core Validator Workers

**Date:** 2026-01-12
**Status:** READY FOR EXECUTION
**Focus:** Phase 1 - Core Validators (Semantic Analyzer, Code Scanner, Dependency Analyzer)
**Target:** Generate 54 worker instructions (20 min each)
**Total Phase Time:** 18 hours → 54 workers × 20 min

---

## YOUR TASK

You are Meta-Worker WINGMAN-01. Your job is to write complete 10-point work instructions for the following workers:

**Assigned Workers:** WORKER_001 through WORKER_054
**Total Workers:** 54
**Focus Area:** Phase 1 - Core Validators Implementation (20-minute granularity)

**Worker Breakdown:**
- **WORKER_001-018**: Semantic Analyzer (6h → 18 workers)
- **WORKER_019-036**: Code Scanner (6h → 18 workers)
- **WORKER_037-054**: Dependency Analyzer (6h → 18 workers)

---

## INSTRUCTION REQUIREMENTS

For EACH of your assigned workers, you MUST create a complete instruction file following the 10-Point Framework:

### Required Sections (ALL 10 POINTS - NON-NEGOTIABLE):

1. **DELIVERABLES** - Specific files, code, functions to create (exact file paths)
2. **SUCCESS_CRITERIA** - Measurable criteria (tests pass, functions work)
3. **BOUNDARIES** - What can/cannot be modified (scope limits)
4. **DEPENDENCIES** - Prerequisites (services, files, previous workers)
5. **MITIGATION** - Rollback, escalation, failure handling
6. **TEST_PROCESS** - Exact commands to validate (pytest, curl commands)
7. **TEST_RESULTS_FORMAT** - JSON structure for execution results
8. **TASK_CLASSIFICATION** - MECHANICAL/CREATIVE/HYBRID with tool selection
9. **RETROSPECTIVE** - Time tracking, lessons learned (store in mem0)
10. **PERFORMANCE_REQUIREMENTS** - Baseline (manual time), target (20 min), monitoring

---

## SOURCE MATERIALS

1. **Implementation Plan:** `/Volumes/Data/ai_projects/wingman-system/wingman/docs/VALIDATION_ENHANCEMENT_IMPLEMENTATION_PLAN.md`
   - Contains Phase 1 detailed breakdown (Tasks 1.1-1.9)
   - Reference sections: Lines 127-489 (Phase 1: Core Validators)
   - **ALL 203 TESTS** specified in Phase 4 (Lines 874-3685) must be covered

2. **Original Deployment Plan:** `/Volumes/Data/ai_projects/wingman-system/wingman/docs/claude-code-5.2/VALIDATION_ENHANCEMENT_DEPLOYMENT_PLAN.md`
   - Architecture details, validator specifications

3. **Intel-System Reference:** `/Volumes/Data/ai_projects/intel-system/ai-workers/workers/WORKER_*.md`
   - Examples of 20-minute granularity workers
   - Proven 10-point framework implementation

---

## DETAILED WORKER BREAKDOWN (54 Workers × 20 min)

### SEMANTIC ANALYZER (18 workers)

#### Structure & Core Logic (6 workers)
- **WORKER_001**: Class skeleton + __init__ method (20 min)
  - File: `wingman/validation/semantic_analyzer.py` (class definition only)
  - Success: Class instantiates with ollama endpoint parameter

- **WORKER_002**: Ollama client integration + connection test (20 min)
  - Add: Ollama client setup, test connection method
  - Success: Can connect to Ollama, send test prompt

- **WORKER_003**: analyze() method structure + input validation (20 min)
  - Add: Main analyze(instruction: str) method, input validation
  - Success: Method accepts string, validates length/format

- **WORKER_004**: Score calculation logic + normalization (20 min)
  - Add: Calculate final score from LLM responses, normalize 0-100
  - Success: Score calculation returns int 0-100

- **WORKER_005**: Reasoning dict structure + JSON schema (20 min)
  - Add: Reasoning dict builder, JSON schema validation
  - Success: Returns {clarity: str, completeness: str, coherence: str}

- **WORKER_006**: Error handling (timeout, invalid JSON, connection) (20 min)
  - Add: Try/except blocks, timeout handling, fallback logic
  - Success: Handles LLM timeout, invalid JSON, connection errors gracefully

#### Prompt Engineering (6 workers)
- **WORKER_007**: Clarity scoring prompt template (20 min)
  - Add: LLM prompt for clarity evaluation (0-100)
  - Success: Prompt returns JSON {score: int, reasoning: str}

- **WORKER_008**: Completeness scoring prompt template (20 min)
  - Add: LLM prompt for completeness evaluation (10-point check)
  - Success: Prompt returns JSON {score: int, reasoning: str}

- **WORKER_009**: Coherence scoring prompt template (20 min)
  - Add: LLM prompt for coherence evaluation (flow, logic)
  - Success: Prompt returns JSON {score: int, reasoning: str}

- **WORKER_010**: Prompt result parser + JSON extraction (20 min)
  - Add: Parse LLM JSON responses, extract scores
  - Success: Handles both ```json and plain JSON responses

- **WORKER_011**: Heuristic fallback scoring (when LLM fails) (20 min)
  - Add: Rule-based scoring (word count, section presence, etc.)
  - Success: Returns score 0-100 without LLM

- **WORKER_012**: Prompt consistency validator (run same prompt 3x) (20 min)
  - Add: Run prompt multiple times, check variance
  - Success: Variance <10% across 3 runs

#### Unit Tests (6 workers - covering 23 tests from Phase 4)
- **WORKER_013**: Tests 1-4 - Clarity scoring tests (20 min)
  - File: `wingman/tests/test_semantic_analyzer.py`
  - Tests: High clarity, moderate, low, vague instructions
  - Success: 4/4 tests pass

- **WORKER_014**: Tests 5-8 - Completeness scoring tests (20 min)
  - Tests: Complete 10-point, missing DELIVERABLES, missing SUCCESS_CRITERIA, partial
  - Success: 4/4 tests pass

- **WORKER_015**: Tests 9-12 - Coherence scoring tests (20 min)
  - Tests: Coherent, incoherent, mixed, technical jargon
  - Success: 4/4 tests pass

- **WORKER_016**: Tests 13-17 - Edge case tests (20 min)
  - Tests: Empty, single word, 10K chars, special characters, multi-language
  - Success: 5/5 tests pass

- **WORKER_017**: Tests 18-21 - Error handling tests (20 min)
  - Tests: LLM timeout, invalid JSON, retry logic, fallback
  - Success: 4/4 tests pass

- **WORKER_018**: Tests 22-23 - Integration tests (20 min)
  - Tests: Score range validation, performance benchmark
  - Success: 2/2 tests pass (total: 23/23 semantic tests)

---

### CODE SCANNER (18 workers)

#### Structure & Core Logic (6 workers)
- **WORKER_019**: Class skeleton + __init__ (20 min)
- **WORKER_020**: scan() method structure + input validation (20 min)
- **WORKER_021**: Pattern matching engine (regex compilation) (20 min)
- **WORKER_022**: Risk level assignment logic (LOW/MEDIUM/HIGH/CRITICAL) (20 min)
- **WORKER_023**: Detection result formatting + JSON structure (20 min)
- **WORKER_024**: Error handling + malformed input handling (20 min)

#### Dangerous Pattern Detection (6 workers - 30 patterns total)
- **WORKER_025**: Patterns 1-5 - File system ops (rm -rf, dd, mkfs, etc.) (20 min)
- **WORKER_026**: Patterns 6-10 - Docker socket, privileged mode (20 min)
- **WORKER_027**: Patterns 11-15 - Network commands (iptables, nc, curl to external) (20 min)
- **WORKER_028**: Patterns 16-20 - System commands (reboot, shutdown, kill -9) (20 min)
- **WORKER_029**: Patterns 21-25 - Database drops, truncates (20 min)
- **WORKER_030**: Patterns 26-30 - Code execution (eval, exec, os.system) (20 min)

#### Secret Detection + Tests (6 workers)
- **WORKER_031**: Secret patterns 1-5 - API keys, tokens (20 min)
- **WORKER_032**: Secret patterns 6-10 - Passwords, credentials (20 min)
- **WORKER_033**: Secret patterns 11-15 - Private keys, certificates (20 min)
- **WORKER_034**: Tests 54-58 - Dangerous pattern tests (5 tests) (20 min)
- **WORKER_035**: Tests 59-63 - Secret detection tests (5 tests) (20 min)
- **WORKER_036**: Tests 64-73 - Integration tests (10 tests, total: 20/20 code scanner tests) (20 min)

---

### DEPENDENCY ANALYZER (18 workers)

#### Structure & Core Logic (6 workers)
- **WORKER_037**: Class skeleton + __init__ (20 min)
- **WORKER_038**: analyze() method structure + input parsing (20 min)
- **WORKER_039**: Service dependency graph builder (20 min)
- **WORKER_040**: Blast radius calculation logic (0-100 scale) (20 min)
- **WORKER_041**: Dependency tree formatting + JSON output (20 min)
- **WORKER_042**: Error handling + unknown service handling (20 min)

#### Service Topology Mapping (6 workers - 7 services)
- **WORKER_043**: Map service 1 - wingman-api dependencies (postgres, redis) (20 min)
- **WORKER_044**: Map service 2 - execution-gateway dependencies (docker socket) (20 min)
- **WORKER_045**: Map service 3 - postgres dependencies (none, root service) (20 min)
- **WORKER_046**: Map service 4 - redis dependencies (none, root service) (20 min)
- **WORKER_047**: Map service 5 - telegram-bot dependencies (wingman-api) (20 min)
- **WORKER_048**: Map services 6-7 - watcher, ollama dependencies (20 min)

#### Cascade Impact + Tests (6 workers)
- **WORKER_049**: Cascade impact calculator (if postgres down, what breaks?) (20 min)
- **WORKER_050**: Critical path identifier (which services are single points of failure?) (20 min)
- **WORKER_051**: Tests 74-78 - Service detection tests (5 tests) (20 min)
- **WORKER_052**: Tests 79-83 - Blast radius tests (5 tests) (20 min)
- **WORKER_053**: Tests 84-88 - Cascade impact tests (5 tests) (20 min)
- **WORKER_054**: Tests 89-93 - Integration tests (5 tests, total: 20/20 dependency tests) (20 min)

---

## OUTPUT REQUIREMENTS

For each worker, create a file:
- **Location:** `ai-workers/workers/WORKER_[ID]_[TITLE].md`
- **Naming Convention**:
  - `WORKER_001_Semantic_Class_Skeleton.md`
  - `WORKER_002_Semantic_Ollama_Client.md`
  - `WORKER_025_Code_Scanner_File_System_Patterns.md`
  - `WORKER_043_Dependency_API_Service_Mapping.md`
  - ... (54 total)
- **Format:** Complete 10-point instruction following framework
- **Quality:** Detailed enough for 20-minute autonomous execution
- **Validation:** Must score ≥80% when submitted to Wingman

---

## EXECUTION INSTRUCTIONS

1. **Read Implementation Plan** (30 min)
   - Focus on Phase 1: Lines 127-489
   - Extract task details for all 54 workers
   - Note 20-minute execution constraint

2. **For Each Worker (001-054):**
   - Extract specific deliverable (1 file, 1 function, 5 patterns, etc.)
   - Fill in all 10 points (non-negotiable)
   - Specify exact 20-minute scope
   - Include exact pytest command if applicable
   - Reference specific tests from Phase 4 (Lines 874-3685)

3. **Save Files** (30 min)
   - Save to: `ai-workers/workers/WORKER_[ID]_[TITLE].md`
   - Create summary: `ai-workers/workers/META_WORKER_WINGMAN_01_SUMMARY.md`

4. **Validation Check** (20 min)
   - Verify all 54 files complete
   - Verify 10-point framework complete for each
   - Verify all 63 Phase 1 tests covered (23 semantic + 20 code + 20 dependency)
   - Check 20-minute scope realistic

---

## QUALITY STANDARDS

Each instruction must:
- ✅ Have ALL 10 POINTS complete (no exceptions)
- ✅ Be scoped for 20-minute execution (not 2 hours!)
- ✅ Include exact file paths, function names, test commands
- ✅ Define clear success criteria (function works, X tests pass)
- ✅ Specify rollback procedures (git revert specific file)
- ✅ Include 20-minute time estimate in PERFORMANCE_REQUIREMENTS
- ✅ Reference implementation plan line numbers
- ✅ Score ≥80% when submitted to Wingman for approval

---

## SUCCESS CRITERIA

**Meta-Worker WINGMAN-01 Complete When:**
- ✅ All 54 worker instruction files created
- ✅ Summary file created with execution plan
- ✅ All 63 Phase 1 tests covered across workers
- ✅ All files pass Wingman validation (≥80% score)
- ✅ Ready for Phase 1 worker execution (50 workers in parallel batches)

**Expected Duration:** 2 hours
**Output:** 54 worker instruction files + 1 summary file
**Test Coverage:** 63 tests (23 semantic + 20 code scanner + 20 dependency)
