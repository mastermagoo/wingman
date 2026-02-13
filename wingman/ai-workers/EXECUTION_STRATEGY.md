# WINGMAN AI-WORKERS EXECUTION STRATEGY & MONITORING PLAN

**Date**: 2026-01-12
**Status**: AGREED & COMMITTED
**Stored in**: mem0/wingman

---

## DELEGATED AUTHORITY AGREEMENT

### Claude's Responsibilities (Accepted):
1. ✅ ALL 225 worker instructions must be complete to exact detail (file paths, function signatures, test commands)
2. ✅ Workers MUST deliver CODE, not guides - zero tolerance
3. ✅ Immediate mitigation authority for worker failures (no user approval needed)
4. ✅ Real-time monitoring every 60 seconds during execution
5. ✅ Report failures + mitigations to user (informational, non-blocking)

### User Requirements (Confirmed):
1. ✅ Work instructions complete to detail without exception
2. ✅ Constant monitoring during execution - no failed workers delivering guides
3. ✅ Immediate resolution/mitigation by Claude (delegated authority)
4. ✅ Zero tolerance for documentation instead of code

---

## DELIVERY PRINCIPLE (NON-NEGOTIABLE)

We **deliver one functional capability at a time** and take it through a full **build → test → deploy** cycle before starting the next capability.

**Phase 1A starting point**: Semantic Analyzer (WORKER_001–018).

- **Functional phase examples**: Semantic Analyzer only, then Code Scanner only, then Dependency Analyzer only, then Content Quality Validator only.
- **Quality gate**: Each phase must ship to **TEST**, pass its tests, and produce runtime evidence before the next phase begins.
- **No “big bang” execution**: We do not run “all 225 workers” as a single delivery unit unless explicitly instructed after prior phases have proven quality.

---

## 225 WORKERS BREAKDOWN

### META_WORKER_WINGMAN_01: Phase 1 (54 workers × 20 min)
- **Semantic Analyzer**: 18 workers (structure, prompts, 23 tests)
- **Code Scanner**: 18 workers (patterns, secrets, 20 tests)
- **Dependency Analyzer**: 18 workers (topology, blast radius, 20 tests)

### META_WORKER_WINGMAN_02: Phase 2 (33 workers × 20 min)
- **Content Quality Structure**: 8 workers
- **Section Scoring Logic**: 10 workers (1 per 10-point section)
- **Overall Quality Score**: 7 workers
- **Unit Tests**: 8 workers (30 tests)

### META_WORKER_WINGMAN_03: Phases 3-6 (138 workers × 20 min)
- **Phase 3 Integration**: 15 workers
- **Phase 4 Testing**: 108 workers (ALL 203 mandatory tests + 120 extended)
- **Phase 5 Deployment**: 9 workers (TEST + PRD gradual rollout)
- **Phase 6 Tuning**: 6 workers (thresholds + prompts)

**Total**: 225 workers, 3h execution (vs 75h sequential), 96% time reduction

---

## MONITORING STRATEGY

### Phase 1: Pre-Execution Quality Gate (Before ANY Worker Runs)

Gate checks for each of 225 worker instructions:
1. ✅ File exists
2. ✅ All 10 points present (DELIVERABLES through PERFORMANCE_REQUIREMENTS)
3. ✅ Deliverables are specific (exact file paths like `wingman/validation/semantic_analyzer.py`)
4. ✅ Success criteria measurable (X tests pass, coverage ≥Y%)
5. ✅ Test commands executable (pytest/curl/docker exec)

**BLOCKING**: If ANY worker fails → STOP ALL → Fix meta-worker → Regenerate → Re-validate

### Phase 2: Real-Time Execution Monitoring (Every 60 seconds)

Checks during worker execution:
1. ⏱️ Timeout check (>20 min = FAIL)
2. 📁 Deliverables created? (files exist)
3. 💻 Is CODE not guide? (detect "Step 1:", "TODO:", "implement this")
4. ✅ Tests executable? (run pytest, check exit code)
5. 📊 Progress indicator (git diff not empty)

**Detection triggers immediate mitigation (delegated authority)**

### Phase 3: Post-Execution Validation (Within 1 minute of completion)

Validate each worker output:
1. ✅ Expected files exist
2. ✅ Files are CODE (has class/def, no guide language)
3. ✅ Syntax valid (python -m py_compile)
4. ✅ Tests pass (pytest returns 0, X/X passed)
5. ✅ Success criteria met (all measurable criteria verified)

### Phase 4: Batch Progress Dashboard (Every 5 minutes)

Real-time dashboard showing:
- Phase progress (X/Y workers complete)
- In progress workers (name, elapsed time, status)
- Completed workers (count)
- Failed workers (count, mitigation status)
- Success metrics (deliverables created, tests passing, code quality)
- ETA (estimated time remaining)

---

## MITIGATION PROCEDURES (Delegated Authority)

### Mitigation 1: Worker Wrote Guide Instead of Code

**Detection**: Keywords "Step 1:", "TODO:", "implement this"

**Action** (immediate):
1. `git checkout HEAD wingman/` (rollback)
2. Enhance instruction: Add "❌ NO DOCUMENTATION. EXECUTABLE CODE ONLY"
3. Re-execute worker
4. Monitor (1-min intervals)
5. If fails again → escalate to user

### Mitigation 2: Worker Tests Failed

**Detection**: pytest returns non-zero exit code

**Action**:
1. `git checkout HEAD wingman/` (rollback)
2. Analyze test failure (read pytest output)
3. Enhance instruction with specific fix
4. Re-execute worker
5. If fails after 2 attempts → escalate to user

### Mitigation 3: Worker Timeout (>20 min)

**Detection**: Worker running >20 minutes

**Action**:
1. Kill worker process
2. Split worker into 2 smaller workers (10 min each)
3. Execute both sequentially
4. If still timeout → escalate to user

### Mitigation 4: Worker Stalled (No Progress >5 min)

**Detection**: No git diff changes for 5 minutes

**Action**:
1. Kill worker process
2. Check dependencies (LLM offline, database down)
3. Fix dependencies
4. Re-execute worker
5. If still stalled → escalate to user

---

## EXECUTION SEQUENCE

### Step 1: Execute Meta-Workers (2 hours)
- META_WORKER_WINGMAN_01 → generates WORKER_001-054
- META_WORKER_WINGMAN_02 → generates WORKER_055-087
- META_WORKER_WINGMAN_03 → generates WORKER_088-225

**Result**: 225 complete worker instruction files

### Step 2: Phase Instruction Quality Gate (NO human approvals noise)

For the **current phase only** (e.g., Semantic Analyzer), we validate the relevant worker instructions for completeness and measurability **without generating 225 human approvals**.

- Use Wingman **instruction validation** (`POST /check`) as the quality gate for worker instructions.
- Only use Wingman **approvals** (`POST /approvals/request`) when a step is genuinely destructive (deploy/restart/rebuild), per repo safety rules.

**Result**: Phase instructions are quality-gated without spamming approvals.

### Step 3: Execute Phase Workers (Build + Unit Tests)

- Execute only the workers required for the phase deliverable (e.g., Semantic Analyzer = WORKER_001–018).
- Run the phase’s unit tests and capture evidence (pytest output, coverage where applicable).

**Result**: Phase capability built and test-verified in the codebase.

### Step 4: Deploy Phase to TEST (approval-gated destructive ops)

- Deploy the phase to **TEST** behind a feature flag (if applicable).
- Any Docker rebuild/restart/down/up is treated as a destructive operation and must go through Wingman approval gates.
- Run TEST smoke checks and capture evidence.

**Result**: Phase capability deployed and validated in TEST.

### Step 5: Quality Review Gate

Stop and present evidence. Only proceed to the next functional phase after quality is accepted.

---

## TEST COVERAGE (ALL 203 MANDATORY)

- **Tests 1-23**: Semantic analyzer (WORKER_013-018)
- **Tests 24-53**: Content quality (WORKER_080-087)
- **Tests 54-73**: Code scanner (WORKER_034-036)
- **Tests 74-93**: Dependency analyzer (WORKER_051-054)
- **Tests 94-123**: Content quality extended (WORKER_080-087)
- **Tests 124-323**: Integration, edge cases, security, concurrency, performance, E2E (WORKER_103-210)

**Total**: 323 tests (203 mandatory + 120 extended)

---

## 10-POINT FRAMEWORK (NON-NEGOTIABLE)

ALL 225 workers must have:

1. **DELIVERABLES** - Exact files, functions, tests
2. **SUCCESS_CRITERIA** - Measurable (X tests pass, Y works)
3. **BOUNDARIES** - Scope limits
4. **DEPENDENCIES** - Prerequisites
5. **MITIGATION** - Rollback procedures
6. **TEST_PROCESS** - Exact pytest/curl commands
7. **TEST_RESULTS_FORMAT** - JSON structure
8. **TASK_CLASSIFICATION** - MECHANICAL/CREATIVE/HYBRID
9. **RETROSPECTIVE** - Time tracking (store in mem0)
10. **PERFORMANCE_REQUIREMENTS** - 20-minute target

---

## API TIER CAPACITY (COST OPTIMIZED)

- **OpenAI**: 10,000 RPM → Using 203 workers (2.03%)
- **Claude**: 4,000 RPM → Using 0 workers (0%) ← REMOVED due to high cost
- **Ollama**: Unlimited → Using 22 workers (free)

**Total capacity used**: 2.03% (well under limits)
**Cost savings**: ~70% reduction by eliminating Claude API usage

---

## COMMITS

- `1d51804` - Infrastructure migration (21 meta-worker templates)
- `d46ad09` - 3 wingman-specific meta-workers (225 workers, 20-min granularity)

**Location**: `/Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/`
**Status**: READY FOR EXECUTION

---

## MONITORING CODE REFERENCE

```python
class WorkerMonitor:
    """Real-time monitoring for 225 workers during execution"""

    def __init__(self):
        self.workers_in_progress = {}
        self.workers_completed = {}
        self.workers_failed = {}
        self.check_interval = 60  # seconds

    def check_worker_progress(self, worker_id):
        """Check every 60 seconds"""
        # 1. Timeout check (>20 min)
        # 2. Deliverables exist
        # 3. CODE not guide
        # 4. Tests pass
        # 5. Progress (git diff)

    def mitigate_failure(self, worker_id, failure_type):
        """Immediate mitigation with delegated authority"""
        # 1. Rollback (git checkout)
        # 2. Enhance instruction
        # 3. Re-execute worker
        # 4. Monitor re-execution
        # 5. Escalate if still fails
```

---

**AGREEMENT CONFIRMED**: Claude has delegated authority to mitigate worker failures immediately without user approval.
