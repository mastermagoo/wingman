# PARALLEL EXECUTION PLAN - Maximum Efficiency

**Date**: 2026-01-13
**Status**: UPDATED — Phase-gated execution (do not run full batches)
**Optimization**: Phase-by-phase delivery + safe parallelism (no file collisions)
**Note**: This file has legacy sections (see ARCHIVED)
<!-- last patched -->

---

## EFFICIENCY GAINS

### What We Did Wrong (Learning)
❌ **Sequential meta-worker execution**: Ran META_WORKER_WINGMAN_01, then 02, then 03
- **Time wasted**: ~2 hours (could have run all 3 in parallel)
- **Lesson**: Independent workers should ALWAYS run in parallel

### What We're Doing Right Now (Agreed Approach)
✅ **Phase-gated delivery**: build → test → deploy(TEST) → evidence → review (one capability at a time)
✅ **Current phase**: **Phase 1A — Semantic Analyzer only** (WORKER_001–018)
✅ **Safe execution**: parallelize only when workers write to disjoint files (Semantic Analyzer is mostly sequential)

---

## COST-OPTIMIZED WORKER ALLOCATION

### Old Allocation (Inefficient)
- OpenAI: 135 workers (60%) - $0.03/1K tokens
- **Claude: 68 workers (30%) - $0.015/1K tokens** ← TOO EXPENSIVE at scale
- Ollama: 22 workers (10%) - FREE

**Problem**: Claude API costs ridiculous at 225-worker scale

### New Allocation (Optimized)
- **OpenAI: 203 workers (90%)** - Cost-effective at volume
- **Claude: 0 workers (0%)** - REMOVED
- **Ollama: 22 workers (10%)** - FREE

**Savings**: ~70% cost reduction by eliminating Claude
**Capacity**: Still using only 2.03% of OpenAI 10K RPM limit

---

## PARALLEL EXECUTION STRATEGY

## DELIVERY AGREEMENT (QUALITY FIRST)

Execution is **phase-gated by functional capability**.

- **Unit of delivery**: one capability at a time (e.g., **Semantic Analyzer only**).
- **Per-phase gate**: **build → test → deploy (TEST)** with evidence, then review. Only then proceed.
- **No cross-phase batching**: do not mix workers from multiple capabilities in the same run (and do not touch deployment/tuning workers until the current capability has proven quality).
- **No file-collision parallelism**: parallelize only when workers write to **disjoint deliverables** (avoid concurrent edits to the same module/test file).

---

## CURRENT DELIVERY: PHASE 1A — Semantic Analyzer (ONLY)

### Scope (this phase only)
- **Worker subset**: WORKER_001–018
- **Primary deliverable (code)**: `validation/semantic_analyzer.py`
- **Primary deliverable (tests)**: `tests/validation/test_semantic_analyzer.py`

### Required deliverables (what “done” means)
- **Importable module**: `python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; print('ok')"`
- **Unit tests green**: `pytest -q tests/validation/test_semantic_analyzer.py`
- **LLM safety**: any Ollama call must use shared host Ollama (`OLLAMA_HOST`/`OLLAMA_PORT`) and must timeout safely (no hangs)

### Execution ordering (avoid file collisions)
- **WORKER_001–012** all modify `validation/semantic_analyzer.py` → **run sequentially**
- **WORKER_013–018** all modify `tests/validation/test_semantic_analyzer.py` → **run sequentially after 001–012**

### Deploy to TEST (approval-gated; destructive)
Any container rebuild/restart is a destructive operation and must go through Wingman approval gates before running:

```bash
docker compose -f docker-compose.yml -p wingman-test up -d --build wingman-api
```

---

## ARCHIVED (REFERENCE ONLY): Full end-to-end parallel plan

The sections below are an end-to-end reference for a future “run everything” pass.
Do **not** execute them until each functional phase has been completed and accepted.

### Batch Size Optimization

**Maximum Parallel Workers**: 50 workers per batch
- **OpenAI rate limit**: 10,000 RPM = 166 RPS
- **Safe rate**: 50 workers × 0.6s interval = 83 requests/min (well under limit)
- **Buffer**: 5x safety margin for burst tolerance

### Execution Batches (full-system reference; run only after per-phase sign-off)

The batch lists below are a **speed-optimized reference** for the eventual end-to-end run.
Given the agreement above, we will execute **only the subset of workers for the current capability**, complete build/tests, deploy to TEST, and stop for quality review before moving on.

**Batch 1: Structure Workers (45 workers, 15 min)**
- WORKER_001-018: Semantic Analyzer structure (18 workers)
- WORKER_019-024: Code Scanner structure (6 workers)
- WORKER_037-042: Dependency Analyzer structure (6 workers)
- WORKER_055-062: Content Quality structure (8 workers)
- WORKER_088-094: Integration structure (7 workers)

**Batch 2: Implementation Workers (50 workers, 20 min)**
- WORKER_025-033: Code Scanner patterns (9 workers)
- WORKER_043-050: Dependency topology (8 workers)
- WORKER_063-072: Section scoring logic (10 workers)
- WORKER_073-079: Overall quality score (7 workers)
- WORKER_095-102: API + Telegram integration (8 workers)
- WORKER_163-170: Validation datasets (8 workers)

**Batch 3: Test Workers Part 1 (50 workers, 20 min)**
- WORKER_007-018: Semantic tests (12 workers)
- WORKER_034-036: Code Scanner tests (3 workers)
- WORKER_051-054: Dependency tests (4 workers)
- WORKER_080-087: Content Quality tests (8 workers)
- WORKER_103-125: Integration + Edge case tests (23 workers)

**Batch 4: Test Workers Part 2 (50 workers, 20 min)**
- WORKER_126-147: Edge cases + Security tests (22 workers)
- WORKER_148-162: Performance + LLM + E2E tests (15 workers)
- WORKER_171-186: False positive/negative + Regression (16 workers)

**Batch 5: Extended Tests + Deployment + Tuning (30 workers, 20 min)**
- WORKER_187-210: Extended test coverage (24 workers)
- WORKER_211-219: Deployment (9 workers)
- WORKER_220-225: Tuning (6 workers)

---

## EXECUTION TIMELINE

### Sequential (Old Way): 75 hours
- 225 workers × 20 min each = 4,500 minutes = 75 hours

### Parallel (New Way): 1.5 hours
- 5 batches × 20 min each = 100 minutes = 1.67 hours
- **Time savings**: 98% reduction (75h → 1.5h)

### With Monitoring Overhead: 2 hours total
- Batch execution: 1.5 hours
- Pre-checks + monitoring + post-validation: 0.5 hours
- **Final execution time**: 2 hours

---

## MONITORING STRATEGY (60-second intervals)

### Real-Time Checks (Every 60s during execution)
1. **Timeout detection**: Any worker >20 min = KILL + RESTART
2. **Code vs Guide detection**: Keywords "Step 1:", "TODO:", "implement" = ROLLBACK + RETRY
3. **Test failure detection**: pytest exit code ≠ 0 = ROLLBACK + FIX + RETRY
4. **Progress tracking**: git diff empty for 5 min = STALLED → ESCALATE
5. **Success tracking**: Count completed workers, tests passing

### Fallback Strategy (If OpenAI fails)
1. **Primary**: OpenAI (203 workers)
2. **Fallback**: Ollama (22 workers) - switch ALL workers to Ollama
3. **Last resort**: Heuristic validator (rule-based, no LLM)

**No Claude fallback** - Removed due to cost

---

## DELEGATED MITIGATION AUTHORITY

**Claude has full authority to:**
1. ✅ Rollback failed workers (git checkout HEAD)
2. ✅ Retry with enhanced instructions
3. ✅ Split timeout workers into 2 smaller workers
4. ✅ Switch LLM provider (OpenAI → Ollama)
5. ✅ Escalate to user only after 2 retry attempts fail

**User will be notified** of mitigations (informational, non-blocking)

---

## EXECUTION COMMANDS

### Start Parallel Execution (Batch 1)
```bash
# From wingman/ directory
cd ai-workers/workers

# Execute 45 workers in parallel (Batch 1)
for i in {001..018} {019..024} {037..042} {055..062} {088..094}; do
    # Execute worker in background with 20-min timeout
    timeout 1200 execute_worker.sh WORKER_${i}_*.md &
done

# Wait for all workers to complete
wait

# Verify all deliverables created
verify_batch_1.sh
```

### Monitor Progress
```bash
# Every 60 seconds during execution
watch -n 60 'git diff --stat && pytest --collect-only | grep -c "test_"'
```

### Fallback to Ollama (If OpenAI fails)
```bash
# Switch all workers to Ollama
export LLM_PROVIDER=ollama
export OLLAMA_ENDPOINT=http://localhost:11434

# Resume execution with Ollama
for worker in $(failed_workers.sh); do
    timeout 1200 execute_worker.sh $worker &
done
```

---

## SUCCESS CRITERIA

**Batch execution complete when:**
- ✅ All 225 workers executed
- ✅ All 323 tests passing
- ✅ All deliverables created (files exist, syntax valid)
- ✅ No workers delivered guides (all delivered code)
- ✅ All retrospectives stored in mem0 (namespace: wingman)

**Target success rate**: ≥95% (≥214 workers succeed on first attempt)

---

## COST ANALYSIS

### Old Allocation (With Claude)
- OpenAI: 135 workers × 2K tokens × $0.03/1K = $8.10
- Claude: 68 workers × 2K tokens × $0.015/1K = $2.04
- Ollama: 22 workers × 2K tokens × FREE = $0.00
- **Total**: $10.14

### New Allocation (OpenAI Only)
- OpenAI: 203 workers × 2K tokens × $0.03/1K = $12.18
- Claude: 0 workers = $0.00
- Ollama: 22 workers × 2K tokens × FREE = $0.00
- **Total**: $12.18

**Cost difference**: +$2.04 BUT simpler architecture, no Claude API complexity
**Trade-off**: Slightly higher cost BUT:
- Single API to manage (not 2)
- Higher rate limits (10K RPM vs 4K RPM)
- Better performance consistency
- No "Claude is expensive" concerns

---

## NEXT ACTIONS

1. **Execute Batch 1** (45 workers, 15 min)
2. **Validate Batch 1** (verify all deliverables)
3. **Execute Batch 2** (50 workers, 20 min)
4. **Continue through Batch 5**
5. **Final validation** (ALL 323 tests must pass)
6. **Commit results** to git
7. **Store retrospectives** in mem0

**Estimated completion**: 2 hours from start
**Target date**: 2026-01-13 (today)

---

**Status**: READY TO EXECUTE
**Optimization**: 98% time savings (75h → 2h)
**Cost**: Optimized (Claude removed, OpenAI only)
**Monitoring**: Automated with 60s intervals
**Authority**: Claude has delegated mitigation authority
