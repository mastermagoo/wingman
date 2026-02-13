# Meta-Worker WINGMAN-02: Generate Phase 2 Content Quality Validator Workers

**Date:** 2026-01-12
**Status:** READY FOR EXECUTION
**Focus:** Phase 2 - Content Quality Validator (Per-Section Scoring)
**Target:** Generate 33 worker instructions (20 min each)
**Total Phase Time:** 11 hours → 33 workers × 20 min

---

## YOUR TASK

You are Meta-Worker WINGMAN-02. Your job is to write complete 10-point work instructions for the following workers:

**Assigned Workers:** WORKER_055 through WORKER_087
**Total Workers:** 33
**Focus Area:** Phase 2 - Content Quality Validator (20-minute granularity)

**Worker Breakdown:**
- **WORKER_055-062**: Content Quality Validator Structure (2.7h → 8 workers)
- **WORKER_063-072**: Section Scoring Logic (3.3h → 10 workers)
- **WORKER_073-079**: Overall Quality Score (2.3h → 7 workers)
- **WORKER_080-087**: Unit Tests (2.7h → 8 workers, 30 tests total)

---

## INSTRUCTION REQUIREMENTS

For EACH of your assigned workers, you MUST create a complete instruction file following the 10-Point Framework:

### Required Sections (ALL 10 POINTS - NON-NEGOTIABLE):

1. **DELIVERABLES** - Specific files, code, functions to create
2. **SUCCESS_CRITERIA** - Measurable criteria (tests pass, functions work)
3. **BOUNDARIES** - What can/cannot be modified
4. **DEPENDENCIES** - Prerequisites (Phase 1 complete: WORKER_001-054)
5. **MITIGATION** - Rollback, escalation, failure handling
6. **TEST_PROCESS** - Exact pytest commands
7. **TEST_RESULTS_FORMAT** - JSON structure for results
8. **TASK_CLASSIFICATION** - MECHANICAL/CREATIVE/HYBRID
9. **RETROSPECTIVE** - Time tracking, lessons learned (store in mem0)
10. **PERFORMANCE_REQUIREMENTS** - Baseline (manual), target (20 min), monitoring

---

## SOURCE MATERIALS

1. **Implementation Plan:** `/Volumes/Data/ai_projects/wingman-system/wingman/docs/VALIDATION_ENHANCEMENT_IMPLEMENTATION_PLAN.md`
   - Phase 2 detailed breakdown (Tasks 2.1-2.4)
   - Reference sections: Lines 491-759 (Phase 2)
   - **ALL 203 TESTS** specified in Phase 4 must be covered

2. **Original Deployment Plan:** `/Volumes/Data/ai_projects/wingman-system/wingman/docs/claude-code-5.2/VALIDATION_ENHANCEMENT_DEPLOYMENT_PLAN.md`
   - Content quality specifications (per-section scoring 0-10)

3. **Intel-System Reference:** `/Volumes/Data/ai_projects/intel-system/ai-workers/workers/WORKER_*.md`
   - Examples of 20-minute granularity

---

## DETAILED WORKER BREAKDOWN (33 Workers × 20 min)

### CONTENT QUALITY VALIDATOR STRUCTURE (8 workers)

- **WORKER_055**: Class skeleton + __init__ method (20 min)
  - File: `wingman/validation/content_quality_validator.py`
  - Success: Class instantiates, accepts semantic_analyzer ref

- **WORKER_056**: analyze_section() method structure (20 min)
  - Add: Main method for per-section scoring
  - Success: Method signature correct, accepts section name + text

- **WORKER_057**: Section extractor (parse 10-point instruction) (20 min)
  - Add: Extract sections from instruction text
  - Success: Returns dict {DELIVERABLES: str, SUCCESS_CRITERIA: str, ...}

- **WORKER_058**: Section validation (check if section present) (20 min)
  - Add: Validate section not empty, not placeholder
  - Success: Returns bool for each section

- **WORKER_059**: Score aggregator (combine 10 section scores) (20 min)
  - Add: Calculate weighted average of section scores
  - Success: Returns single score 0-100

- **WORKER_060**: LLM prompt orchestrator (call semantic_analyzer) (20 min)
  - Add: Use semantic_analyzer for LLM scoring
  - Success: Can call semantic_analyzer, get scores

- **WORKER_061**: Heuristic fallback (when LLM fails) (20 min)
  - Add: Rule-based per-section scoring
  - Success: Returns scores without LLM

- **WORKER_062**: Error handling (missing sections, LLM errors) (20 min)
  - Add: Try/except, handle missing sections gracefully
  - Success: No crashes on malformed input

---

### SECTION SCORING LOGIC (10 workers - 1 per section)

- **WORKER_063**: Section 1 - DELIVERABLES scoring (0-10) (20 min)
  - Add: LLM prompt for DELIVERABLES quality
  - Success: Prompt returns score 0-10 + reasoning

- **WORKER_064**: Section 2 - SUCCESS_CRITERIA scoring (0-10) (20 min)
  - Add: LLM prompt for SUCCESS_CRITERIA quality
  - Success: Prompt returns score 0-10 + reasoning

- **WORKER_065**: Section 3 - BOUNDARIES scoring (0-10) (20 min)
  - Add: LLM prompt for BOUNDARIES clarity
  - Success: Prompt returns score 0-10 + reasoning

- **WORKER_066**: Section 4 - DEPENDENCIES scoring (0-10) (20 min)
  - Add: LLM prompt for DEPENDENCIES completeness
  - Success: Prompt returns score 0-10 + reasoning

- **WORKER_067**: Section 5 - MITIGATION scoring (0-10) (20 min)
  - Add: LLM prompt for MITIGATION adequacy
  - Success: Prompt returns score 0-10 + reasoning

- **WORKER_068**: Section 6 - TEST_PROCESS scoring (0-10) (20 min)
  - Add: LLM prompt for TEST_PROCESS specificity
  - Success: Prompt returns score 0-10 + reasoning

- **WORKER_069**: Section 7 - TEST_RESULTS_FORMAT scoring (0-10) (20 min)
  - Add: LLM prompt for TEST_RESULTS_FORMAT clarity
  - Success: Prompt returns score 0-10 + reasoning

- **WORKER_070**: Section 8 - RESOURCE_REQUIREMENTS scoring (0-10) (20 min)
  - Add: LLM prompt for RESOURCE_REQUIREMENTS realism
  - Success: Prompt returns score 0-10 + reasoning

- **WORKER_071**: Section 9 - RISK_ASSESSMENT scoring (0-10) (20 min)
  - Add: LLM prompt for RISK_ASSESSMENT accuracy
  - Success: Prompt returns score 0-10 + reasoning

- **WORKER_072**: Section 10 - QUALITY_METRICS scoring (0-10) (20 min)
  - Add: LLM prompt for QUALITY_METRICS measurability
  - Success: Prompt returns score 0-10 + reasoning

---

### OVERALL QUALITY SCORE (7 workers)

- **WORKER_073**: Overall score formula (weighted average) (20 min)
  - Add: Calculate overall score = avg(10 sections) × 10
  - Success: Returns score 0-100

- **WORKER_074**: Quality category assignment (EXCELLENT/GOOD/FAIR/POOR) (20 min)
  - Add: Assign category based on score ranges
  - Success: 90-100=EXCELLENT, 70-89=GOOD, 60-69=FAIR, <60=POOR

- **WORKER_075**: Auto-reject logic (quality < 60) (20 min)
  - Add: Flag instructions for auto-reject
  - Success: Returns auto_reject boolean

- **WORKER_076**: Section score weighting (adjust weights per section) (20 min)
  - Add: Configurable weights for critical sections
  - Success: Can adjust weights, recalculate overall score

- **WORKER_077**: Threshold tuner (adjust auto-reject threshold) (20 min)
  - Add: Configuration for threshold adjustment
  - Success: Can set threshold 50-70 range

- **WORKER_078**: Result formatter (JSON output structure) (20 min)
  - Add: Format analysis result as JSON
  - Success: Returns structured dict with all scores

- **WORKER_079**: Integration with api_server (endpoint preparation) (20 min)
  - Add: Prepare content_quality_validator for API integration
  - Success: Can be imported, called from api_server.py

---

### UNIT TESTS (8 workers - 30 tests total from Phase 4)

- **WORKER_080**: Tests 94-97 - Section extraction tests (4 tests) (20 min)
  - File: `wingman/tests/test_content_quality.py`
  - Tests: Valid 10-point, missing sections, empty sections, malformed
  - Success: 4/4 tests pass

- **WORKER_081**: Tests 98-102 - Per-section scoring tests (5 tests) (20 min)
  - Tests: High-quality section (9-10), low-quality (0-3), 5 different sections
  - Success: 5/5 tests pass

- **WORKER_082**: Tests 103-107 - Overall score calculation tests (5 tests) (20 min)
  - Tests: All sections 10 → 100, mixed scores, edge cases
  - Success: 5/5 tests pass

- **WORKER_083**: Tests 108-111 - Quality category tests (4 tests) (20 min)
  - Tests: EXCELLENT (95), GOOD (80), FAIR (65), POOR (40)
  - Success: 4/4 tests pass

- **WORKER_084**: Tests 112-115 - Auto-reject threshold tests (4 tests) (20 min)
  - Tests: Below threshold (50), at threshold (60), above (70), edge (59.9)
  - Success: 4/4 tests pass

- **WORKER_085**: Tests 116-119 - Weighting tests (4 tests) (20 min)
  - Tests: Equal weights, DELIVERABLES 2x weight, custom weights, validation
  - Success: 4/4 tests pass

- **WORKER_086**: Tests 120-122 - Error handling tests (3 tests) (20 min)
  - Tests: Missing section, LLM timeout, invalid input
  - Success: 3/3 tests pass

- **WORKER_087**: Tests 123 - Integration test (1 test) (20 min)
  - Tests: Full end-to-end content quality analysis
  - Success: 1/1 test pass (total: 30/30 content quality tests)

---

## OUTPUT REQUIREMENTS

For each worker, create a file:
- **Location:** `ai-workers/workers/WORKER_[ID]_[TITLE].md`
- **Naming Convention**:
  - `WORKER_055_Content_Quality_Class_Skeleton.md`
  - `WORKER_063_Section_DELIVERABLES_Scoring.md`
  - `WORKER_073_Overall_Score_Formula.md`
  - `WORKER_080_Content_Quality_Tests_Part1.md`
  - ... (33 total)
- **Format:** Complete 10-point instruction
- **Quality:** 20-minute autonomous execution
- **Validation:** Must score ≥80% with Wingman

---

## EXECUTION INSTRUCTIONS

1. **Read Implementation Plan** (20 min)
   - Focus on Phase 2: Lines 491-759
   - Extract task details for all 33 workers
   - Note dependencies on Phase 1 (WORKER_001-054 complete)

2. **For Each Worker (055-087):**
   - Extract specific deliverable (1 function, 1 section prompt, 4 tests, etc.)
   - Fill in all 10 points (non-negotiable)
   - Specify exact 20-minute scope
   - Include exact pytest command if applicable
   - Reference specific tests from Phase 4 (Lines 1208-1807 for content quality tests)

3. **Save Files** (20 min)
   - Save to: `ai-workers/workers/WORKER_[ID]_[TITLE].md`
   - Create summary: `ai-workers/workers/META_WORKER_WINGMAN_02_SUMMARY.md`

4. **Validation Check** (20 min)
   - Verify all 33 files complete
   - Verify 10-point framework complete for each
   - Verify all 30 Phase 2 tests covered
   - Check dependencies on Phase 1 clear

---

## QUALITY STANDARDS

Each instruction must:
- ✅ Have ALL 10 POINTS complete (no exceptions)
- ✅ Be scoped for 20-minute execution
- ✅ Include exact file paths, function names, test commands
- ✅ Define clear success criteria
- ✅ Specify dependencies on Phase 1 (semantic_analyzer available)
- ✅ Specify rollback procedures
- ✅ Include 20-minute time estimate
- ✅ Reference implementation plan line numbers
- ✅ Score ≥80% when submitted to Wingman

---

## SUCCESS CRITERIA

**Meta-Worker WINGMAN-02 Complete When:**
- ✅ All 33 worker instruction files created
- ✅ Summary file created with execution plan
- ✅ All 30 Phase 2 tests covered across workers
- ✅ All files pass Wingman validation (≥80% score)
- ✅ Ready for Phase 2 worker execution (sequential after Phase 1)

**Expected Duration:** 1.5 hours
**Output:** 33 worker instruction files + 1 summary file
**Test Coverage:** 30 tests (content quality unit tests)
**Dependencies:** Phase 1 complete (WORKER_001-054 executed, semantic_analyzer available)
