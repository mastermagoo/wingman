# Meta-Worker WINGMAN-03: Generate Phase 3-6 Integration, Testing, Deployment & Tuning Workers

**Date:** 2026-01-12
**Status:** READY FOR EXECUTION
**Focus:** Phases 3-6 - Integration, ALL 203 Tests, Deployment, Tuning
**Target:** Generate 138 worker instructions (20 min each)
**Total Phase Time:** 46 hours → 138 workers × 20 min

---

## YOUR TASK

You are Meta-Worker WINGMAN-03. Your job is to write complete 10-point work instructions for the following workers:

**Assigned Workers:** WORKER_088 through WORKER_225
**Total Workers:** 138
**Focus Area:** Phases 3-6 (20-minute granularity)

**Worker Breakdown:**
- **Phase 3 - Integration** (5h → 15 workers): WORKER_088-102
- **Phase 4 - Testing** (36h → 108 workers): WORKER_103-210 (ALL 203 TESTS)
- **Phase 5 - Deployment** (3h → 9 workers): WORKER_211-219
- **Phase 6 - Tuning** (2h → 6 workers): WORKER_220-225

---

## INSTRUCTION REQUIREMENTS

For EACH of your assigned workers, you MUST create a complete instruction file following the 10-Point Framework:

### Required Sections (ALL 10 POINTS - NON-NEGOTIABLE):

1. **DELIVERABLES** - Specific files, code, tests to create
2. **SUCCESS_CRITERIA** - Measurable criteria
3. **BOUNDARIES** - What can/cannot be modified
4. **DEPENDENCIES** - Prerequisites (Phase 1-2 complete: WORKER_001-087)
5. **MITIGATION** - Rollback, escalation, failure handling
6. **TEST_PROCESS** - Exact pytest/curl commands
7. **TEST_RESULTS_FORMAT** - JSON structure
8. **TASK_CLASSIFICATION** - MECHANICAL/CREATIVE/HYBRID
9. **RETROSPECTIVE** - Time tracking, lessons learned (store in mem0)
10. **PERFORMANCE_REQUIREMENTS** - Baseline, target (20 min), monitoring

---

## SOURCE MATERIALS

1. **Implementation Plan:** `/Volumes/Data/ai_projects/wingman-system/wingman/docs/VALIDATION_ENHANCEMENT_IMPLEMENTATION_PLAN.md`
   - Phase 3: Lines 761-873 (Integration)
   - **Phase 4: Lines 874-3685 (ALL 203 TESTS - CRITICAL SECTION)**
   - Phase 5: Lines 3686-3985 (Deployment)
   - Phase 6: Lines 3986-4147 (Tuning)

2. **Original Deployment Plan:** `/Volumes/Data/ai_projects/wingman-system/wingman/docs/claude-code-5.2/VALIDATION_ENHANCEMENT_DEPLOYMENT_PLAN.md`
   - Complete 203 test specifications

3. **Intel-System Reference:** `/Volumes/Data/ai_projects/intel-system/ai-workers/workers/WORKER_*.md`
   - 20-minute granularity examples

---

## PHASE 3: INTEGRATION (15 Workers × 20 min = 5 hours)

### WORKER_088-093: Composite Validator (6 workers)
- **WORKER_088**: Composite validator class skeleton (20 min)
- **WORKER_089**: Call all 4 validators (semantic, code, dependency, content) (20 min)
- **WORKER_090**: Combine scores into final recommendation (20 min)
- **WORKER_091**: Auto-approve logic (LOW risk + quality ≥ 90) (20 min)
- **WORKER_092**: Auto-reject logic (quality < 60 OR CRITICAL risk) (20 min)
- **WORKER_093**: Composite validator tests (5 tests) (20 min)

### WORKER_094-099: API Server Integration (6 workers)
- **WORKER_094**: Add `/approvals/validate` endpoint (20 min)
- **WORKER_095**: Import all 4 validators into api_server.py (20 min)
- **WORKER_096**: Add validation to approval request flow (20 min)
- **WORKER_097**: Add validation to approval response (20 min)
- **WORKER_098**: Error handling for validation failures (20 min)
- **WORKER_099**: API integration tests (5 tests) (20 min)

### WORKER_100-102: Telegram Notification Enhancement (3 workers)
- **WORKER_100**: Add validation scores to Telegram notification (20 min)
- **WORKER_101**: Add auto-approve/reject indicators (20 min)
- **WORKER_102**: Telegram notification tests (3 tests) (20 min)

---

## PHASE 4: COMPREHENSIVE TESTING (108 Workers × 20 min = 36 hours)

**CRITICAL**: ALL 203 TESTS from implementation plan MUST be covered

### WORKER_103-109: Integration Tests (7 workers - 38 tests)
**Reference: Implementation Plan Lines 2108-2707**

- **WORKER_103**: Tests 124-129 - Validator interaction tests (6 tests) (20 min)
  - Tests: Semantic→Code, Code→Dependency, all 4 together, score conflicts, error propagation, timeout handling

- **WORKER_104**: Tests 130-135 - Composite validator tests (6 tests) (20 min)
  - Tests: All validators pass, one fails, mixed results, score weighting, final recommendation, edge cases

- **WORKER_105**: Tests 136-141 - API integration tests (6 tests) (20 min)
  - Tests: POST /approvals/validate, validation in request flow, validation in response, error handling, rate limiting, concurrent requests

- **WORKER_106**: Tests 142-148 - Auto-approve logic tests (7 tests) (20 min)
  - Tests: LOW risk + quality 95, MEDIUM risk + quality 95 (no auto), LOW + quality 85 (no auto), quality 100 (yes), edge cases (89.9, 90.0, 90.1)

- **WORKER_107**: Tests 149-154 - Auto-reject logic tests (6 tests) (20 min)
  - Tests: Quality 50 (reject), quality 59 (reject), quality 60 (no reject), CRITICAL risk (reject), HIGH risk + quality 80 (no reject), edge cases

- **WORKER_108**: Tests 155-158 - Integration edge cases (4 tests) (20 min)
  - Tests: All validators unavailable, partial validator failure, LLM timeout chain, database connection loss

- **WORKER_109**: Tests 159-161 - Performance integration tests (3 tests) (20 min)
  - Tests: End-to-end latency <5s, concurrent validation (10 requests), throughput test (100 requests/min)

### WORKER_110-131: Edge Case Tests (22 workers - 44 tests)
**Reference: Implementation Plan Lines 2708-3307**

- **WORKER_110**: Tests 162-163 - Empty/null inputs (2 tests) (20 min)
- **WORKER_111**: Tests 164-165 - Extremely long inputs (10K, 100K chars) (2 tests) (20 min)
- **WORKER_112**: Tests 166-167 - Special characters (Unicode, emojis, SQL injection) (2 tests) (20 min)
- **WORKER_113**: Tests 168-169 - Malformed JSON (2 tests) (20 min)
- **WORKER_114**: Tests 170-171 - Boundary values (score 0, 50, 100) (2 tests) (20 min)
- **WORKER_115**: Tests 172-173 - Missing required sections (2 tests) (20 min)
- **WORKER_116**: Tests 174-175 - Incomplete instructions (2 tests) (20 min)
- **WORKER_117**: Tests 176-177 - Contradictory requirements (2 tests) (20 min)
- **WORKER_118**: Tests 178-179 - Circular dependencies (2 tests) (20 min)
- **WORKER_119**: Tests 180-181 - Invalid service references (2 tests) (20 min)
- **WORKER_120**: Tests 182-183 - Network timeouts (2 tests) (20 min)
- **WORKER_121**: Tests 184-185 - LLM failures (2 tests) (20 min)
- **WORKER_122**: Tests 186-187 - Database connection errors (2 tests) (20 min)
- **WORKER_123**: Tests 188-189 - Memory exhaustion (2 tests) (20 min)
- **WORKER_124**: Tests 190-191 - Disk full errors (2 tests) (20 min)
- **WORKER_125**: Tests 192-193 - Permission denied errors (2 tests) (20 min)
- **WORKER_126**: Tests 194-195 - Rate limit exceeded (2 tests) (20 min)
- **WORKER_127**: Tests 196-197 - Concurrent modification (2 tests) (20 min)
- **WORKER_128**: Tests 198-199 - Race conditions (2 tests) (20 min)
- **WORKER_129**: Tests 200-201 - Deadlock scenarios (2 tests) (20 min)
- **WORKER_130**: Tests 202-203 - Cache inconsistency (2 tests) (20 min)
- **WORKER_131**: Tests 204-205 - Token expiration (2 tests) (20 min)

### WORKER_132-138: Security Tests (7 workers - 15 tests)
**Reference: Implementation Plan Lines 2308-2507**

- **WORKER_132**: Tests 206-207 - Command injection detection (2 tests) (20 min)
- **WORKER_133**: Tests 208-209 - SQL injection attempts (2 tests) (20 min)
- **WORKER_134**: Tests 210-211 - Path traversal attacks (2 tests) (20 min)
- **WORKER_135**: Tests 212-213 - Secret leakage detection (2 tests) (20 min)
- **WORKER_136**: Tests 214-215 - Privilege escalation attempts (2 tests) (20 min)
- **WORKER_137**: Tests 216-218 - Docker socket access validation (3 tests) (20 min)
- **WORKER_138**: Tests 219-220 - Sensitive data exposure (2 tests) (20 min)

### WORKER_139-147: Concurrency Tests (9 workers - 18 tests)
**Reference: Implementation Plan Lines 2508-2707**

- **WORKER_139**: Tests 221-222 - Parallel validator execution (2 tests) (20 min)
- **WORKER_140**: Tests 223-224 - Concurrent approval requests (2 tests) (20 min)
- **WORKER_141**: Tests 225-226 - Thread safety (2 tests) (20 min)
- **WORKER_142**: Tests 227-228 - Database connection pooling (2 tests) (20 min)
- **WORKER_143**: Tests 229-230 - Lock contention (2 tests) (20 min)
- **WORKER_144**: Tests 231-232 - Message queue ordering (2 tests) (20 min)
- **WORKER_145**: Tests 233-234 - Transaction isolation (2 tests) (20 min)
- **WORKER_146**: Tests 235-236 - Cache coherency (2 tests) (20 min)
- **WORKER_147**: Tests 237-238 - Resource cleanup (2 tests) (20 min)

### WORKER_148-152: Performance Tests (5 workers - 5 tests)
**Reference: Implementation Plan Lines 2708-2807**

- **WORKER_148**: Test 239 - Response time benchmark (validation <3s) (20 min)
- **WORKER_149**: Test 240 - Throughput test (50 validations/min) (20 min)
- **WORKER_150**: Test 241 - Memory usage (validation <100MB) (20 min)
- **WORKER_151**: Test 242 - CPU usage (validation <30% CPU) (20 min)
- **WORKER_152**: Test 243 - Database query count (<20 queries) (20 min)

### WORKER_153-157: LLM Consistency Tests (5 workers - 5 tests)
**Reference: Implementation Plan Lines 2808-2907**

- **WORKER_153**: Test 244 - Same instruction 10x (variance <10%) (20 min)
- **WORKER_154**: Test 245 - Prompt robustness (score consistency) (20 min)
- **WORKER_155**: Test 246 - Model switching (Ollama vs Claude) (20 min)
- **WORKER_156**: Test 247 - Temperature sensitivity (temp 0.0 vs 0.7) (20 min)
- **WORKER_157**: Test 248 - JSON format consistency (20 min)

### WORKER_158-162: E2E Approval Flow Tests (5 workers - 5 tests)
**Reference: Implementation Plan Lines 2908-3307**

- **WORKER_158**: Test 249 - Full approval flow (submission → validation → approval → execution) (20 min)
- **WORKER_159**: Test 250 - Auto-approve flow (LOW risk + quality 95) (20 min)
- **WORKER_160**: Test 251 - Auto-reject flow (quality 50) (20 min)
- **WORKER_161**: Test 252 - Manual review flow (MEDIUM risk + quality 75) (20 min)
- **WORKER_162**: Test 253 - Telegram notification delivery (20 min)

### WORKER_163-176: False Positive/Negative Analysis (14 workers)
**Reference: Implementation Plan Lines 3308-3507**

- **WORKER_163-166**: Create validation dataset (20 good + 20 bad + 20 edge instructions) (4 workers × 20 min)
- **WORKER_167-170**: Run validation on dataset, collect results (4 workers × 20 min)
- **WORKER_171-173**: Analyze false positives (identify patterns, tune thresholds) (3 workers × 20 min)
- **WORKER_174-176**: Analyze false negatives (identify gaps, enhance patterns) (3 workers × 20 min)

### WORKER_177-186: Regression Testing (10 workers)
**Reference: Implementation Plan Lines 3508-3607**

- **WORKER_177-181**: Create regression baseline (capture current behavior for 50 instructions) (5 workers × 20 min)
- **WORKER_182-185**: Run regression suite after each validator change (4 workers × 20 min)
- **WORKER_186**: Regression report generation (20 min)

### WORKER_187-210: Extended Test Coverage (24 workers - 70 additional tests)
**Covering remaining tests from Phase 4 specification**

- **WORKER_187-195**: Semantic analyzer extended tests (9 workers, Tests 254-280 - 27 tests)
- **WORKER_196-202**: Code scanner extended tests (7 workers, Tests 281-300 - 20 tests)
- **WORKER_203-207**: Dependency analyzer extended tests (5 workers, Tests 301-315 - 15 tests)
- **WORKER_208-210**: Content quality extended tests (3 workers, Tests 316-323 - 8 tests)

**TOTAL PHASE 4 TESTS: 323 tests** (exceeds 203 minimum requirement for comprehensive coverage)

---

## PHASE 5: DEPLOYMENT (9 Workers × 20 min = 3 hours)

### WORKER_211-214: TEST Deployment (4 workers)
- **WORKER_211**: Feature flag setup (enable/disable validation) (20 min)
- **WORKER_212**: Deploy validators to TEST environment (20 min)
- **WORKER_213**: Smoke test in TEST (20 validations) (20 min)
- **WORKER_214**: TEST deployment verification (health checks, logs) (20 min)

### WORKER_215-219: PRD Deployment (5 workers)
- **WORKER_215**: PRD pre-deployment checklist (backups, rollback plan) (20 min)
- **WORKER_216**: Deploy to PRD with feature flag OFF (20 min)
- **WORKER_217**: Gradual rollout (10% → 50% → 100%) (3 workers × 20 min)
  - WORKER_217: Enable for 10% of requests
  - WORKER_218: Monitor + enable for 50%
  - WORKER_219: Monitor + enable for 100%

---

## PHASE 6: TUNING (6 Workers × 20 min = 2 hours)

### WORKER_220-222: Threshold Tuning (3 workers)
- **WORKER_220**: Auto-reject threshold optimization (test 50-70 range) (20 min)
- **WORKER_221**: Auto-approve threshold optimization (test 85-95 range) (20 min)
- **WORKER_222**: Risk level threshold tuning (LOW/MEDIUM/HIGH boundaries) (20 min)

### WORKER_223-225: Prompt Tuning (3 workers)
- **WORKER_223**: Semantic analyzer prompt refinement (reduce false positives) (20 min)
- **WORKER_224**: Content quality prompt refinement (improve consistency) (20 min)
- **WORKER_225**: Final tuning report + recommendations (20 min)

---

## OUTPUT REQUIREMENTS

For each worker, create a file:
- **Location:** `ai-workers/workers/WORKER_[ID]_[TITLE].md`
- **Naming Convention**:
  - `WORKER_088_Composite_Validator_Skeleton.md`
  - `WORKER_103_Integration_Tests_Part1.md`
  - `WORKER_158_E2E_Approval_Flow_Test1.md`
  - `WORKER_211_Feature_Flag_Setup.md`
  - ... (138 total)
- **Format:** Complete 10-point instruction
- **Quality:** 20-minute autonomous execution
- **Validation:** Must score ≥80% with Wingman

---

## EXECUTION INSTRUCTIONS

1. **Read Implementation Plan** (2 hours)
   - Phase 3: Lines 761-873
   - **Phase 4: Lines 874-3685 (ALL 203 TESTS - READ COMPLETELY)**
   - Phase 5: Lines 3686-3985
   - Phase 6: Lines 3986-4147

2. **For Each Worker (088-225):**
   - Extract specific deliverable from implementation plan
   - Map to exact test numbers (e.g., Tests 124-129)
   - Fill in all 10 points (non-negotiable)
   - Specify exact 20-minute scope
   - Include exact pytest/curl commands
   - Reference implementation plan line numbers

3. **Save Files** (1 hour)
   - Save to: `ai-workers/workers/WORKER_[ID]_[TITLE].md`
   - Create summary: `ai-workers/workers/META_WORKER_WINGMAN_03_SUMMARY.md`

4. **Validation Check** (1 hour)
   - Verify all 138 files complete
   - Verify 10-point framework complete for each
   - **CRITICAL: Verify ALL 203 tests covered** (map each test to worker)
   - Check dependencies on Phase 1-2 (WORKER_001-087) clear

---

## QUALITY STANDARDS

Each instruction must:
- ✅ Have ALL 10 POINTS complete (no exceptions)
- ✅ Be scoped for 20-minute execution
- ✅ Include exact file paths, test commands
- ✅ Define clear success criteria (X/X tests pass)
- ✅ Specify dependencies on Phase 1-2 (all validators available)
- ✅ Specify rollback procedures
- ✅ Include 20-minute time estimate
- ✅ Reference implementation plan line numbers
- ✅ Map to specific test numbers from Phase 4
- ✅ Score ≥80% when submitted to Wingman

---

## SUCCESS CRITERIA

**Meta-Worker WINGMAN-03 Complete When:**
- ✅ All 138 worker instruction files created
- ✅ Summary file created with execution plan
- ✅ **ALL 203 TESTS covered across workers** (Test 124-323 mapped)
- ✅ All files pass Wingman validation (≥80% score)
- ✅ Ready for Phase 3-6 worker execution (50 workers in parallel batches)

**Expected Duration:** 4 hours
**Output:** 138 worker instruction files + 1 summary file
**Test Coverage:** 323 tests total (exceeds 203 minimum requirement)
**Dependencies:** Phase 1-2 complete (WORKER_001-087 executed, all 4 validators available)

---

## TEST COVERAGE MAPPING (CRITICAL)

**Phase 4 Testing Breakdown** (All 203 mandatory tests):
- Tests 1-23: Semantic analyzer (covered by WORKER_013-018 in Phase 1) ✅
- Tests 24-53: Content quality (covered by WORKER_080-087 in Phase 2) ✅
- Tests 54-73: Code scanner (covered by WORKER_034-036 in Phase 1) ✅
- Tests 74-93: Dependency analyzer (covered by WORKER_051-054 in Phase 1) ✅
- Tests 94-123: Content quality extended (covered by WORKER_080-087 in Phase 2) ✅
- **Tests 124-323: Integration, edge cases, security, concurrency, performance, E2E (covered by WORKER_103-210 in Phase 4)** ✅

**Total Coverage: 323 tests** (203 mandatory + 120 extended for robustness)

---

**FINAL WORKER COUNT: 225 TOTAL**
- Phase 1: 54 workers (WORKER_001-054)
- Phase 2: 33 workers (WORKER_055-087)
- Phase 3-6: 138 workers (WORKER_088-225)
