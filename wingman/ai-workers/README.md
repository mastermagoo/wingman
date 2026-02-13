# AI Workers Infrastructure (Wingman)

**Purpose**: Parallel execution framework for validation enhancement implementation

**Copied from**: intel-system ai-workers (proven at 200 workers)
**Adapted for**: Wingman validation enhancement (225 workers generated)
**Date**: 2026-01-12

---

## Overview

This directory contains the infrastructure for executing AI workers in parallel batches. Workers are AI agents that perform specific, well-defined tasks following a standardized 10-point instruction framework.

### Key Concepts

- **Workers**: AI agents that execute specific tasks (e.g., implement semantic analyzer, write tests)
- **Meta-Workers**: AI workers that generate worker instructions from source plans
- **10-Point Framework**: Standardized instruction format ensuring clarity and consistency
- **Parallel Execution**: Workers can run in batches where outputs don’t collide (phase-gated by capability)
- **Self-Validation**: Worker instructions are quality-gated via Wingman `POST /check` (≥80% score)

---

## Directory Structure

```
ai-workers/
├── README.md                    ← This file
├── meta-workers/                ← Meta-worker instruction templates (20 files)
│   ├── META_WORKER_01_INSTRUCTION.md
│   ├── META_WORKER_02_INSTRUCTION.md
│   └── ... (20 total - generic templates)
├── workers/                     ← Wingman-specific worker instructions (225 total)
│   ├── WORKER_001_*.md
│   ├── WORKER_002_*.md
│   └── ... (WORKER_001–WORKER_225)
├── results/                     ← Execution results (gitignored)
│   ├── README.md
│   ├── meta-workers/            ← Meta-worker execution results
│   └── workers/                 ← Worker execution results
├── scripts/                     ← Orchestration scripts (wingman_orchestrator.py, verify_phase1a_e2e.py, etc.)
└── templates/                   ← Reusable templates (if needed)
```

---

## How It Works

## Orchestrator Phase 1A Instructions

**Role boundary**: The chat agent (Cursor AI) does **not** perform design, build, test, or deployment. The chat agent **assists the AI orchestrator only**. The steps below are executed by the **orchestrator**, which instructs the AI workers. Workers receive their instructions from the orchestrator.

**Orchestrator quick start**: See **`ai-workers/ORCHESTRATOR_AID_PHASE_1A.md`** for a single "start here" with prerequisites, Step 1–3, and references.  
**Complete workflow (orchestrator, worker instructions, full validation)**: See **`ai-workers/COMPLETE_WORKFLOW.md`** for the end-to-end flow and how validation is performed from each worker’s TEST_PROCESS.

The following defines what the **orchestrator** delivers for Phase 1A (Semantic Analyzer).

### 1. DELIVERABLES
- **Phase 1A Step 1 report**: A pass/fail list for `WORKER_001–018` from **TEST** `POST http://127.0.0.1:8101/check` (evidence: JSON responses, aggregated summary).
- **Phase 1A code deliverable**: `validation/semantic_analyzer.py` implementing `SemanticAnalyzer.analyze(...)` with safe Ollama calls + retry + heuristic fallback.
- **Phase 1A test deliverable**: `tests/validation/test_semantic_analyzer.py` converted from skipped stubs into real tests (no skips), with mocks for non-LLM tests.
- **Phase 1A deploy evidence (TEST only)**: Approval request ID for the TEST deploy step + smoke-test output from inside `wingman-api` container (no secrets printed).

### 2. SUCCESS_CRITERIA (SMART)
- **Specific**: Only Semantic Analyzer (no Code Scanner/Dependency/Content Quality in this phase).
- **Measurable**:
  - All `WORKER_001–018` score **≥80** on TEST `/check`
  - `pytest -q tests/validation/test_semantic_analyzer.py` exits **0** (no skips)
  - Runtime smoke test returns a dict with keys: `risk_level`, `operation_types`, `blast_radius`, `reasoning`, `confidence`
- **Achievable**: Non-LLM tests use mocks; LLM-marked tests can be gated behind availability of host Ollama.
- **Relevant**: Semantic Analyzer must detect **hidden risk** (e.g., “restart on PRD” → HIGH) using fixtures in `tests/validation/fixtures.py`.
- **Time-bound**: Complete Phase 1A end-to-end (build → test → deploy(TEST) → evidence) before starting the next validator phase.

### 3. BOUNDARIES (NON-NEGOTIABLE)
- **Environment**: Step 1 runs against **TEST** only (`http://127.0.0.1:8101`). No PRD changes for Phase 1A.
- **No destructive ops without approval**: any `docker compose up/down/rebuild/restart` requires a Wingman approval (`POST /approvals/request`) and APPROVED status first.
- **No GitHub push** unless you explicitly say **"push to github"**.
- **No secrets in output**: never print tokens/keys/passwords; use env vars.

### 4. DEPENDENCIES
- TEST Wingman API healthy at `http://127.0.0.1:8101/health`
- Host Ollama reachable at `http://127.0.0.1:11434/api/tags` (or via `OLLAMA_HOST`/`OLLAMA_PORT` from containers)
- Worker instruction files exist: `ai-workers/workers/WORKER_001_*.md` … `WORKER_018_*.md`

### 5. MITIGATION
- If any worker instruction scores <80: patch the worker instruction file(s), then re-run `/check` until passing.
- If tests fail: fix code/tests; if still failing, rollback affected files and isolate the failing case.
- If Ollama is unavailable: ensure fallback path returns a valid result dict and continue with non-LLM tests.

### 6. TEST_PROCESS (orchestrator-level Phase 1A steps — not the per-worker section)
This is the **three-step Phase 1A process**. Do not confuse with **per-worker TEST_PROCESS** (section 6 inside each worker .md file = bash commands to validate that worker’s deliverable). See `COMPLETE_WORKFLOW.md` for both meanings.
- Step 1: POST each `WORKER_001–018` instruction to `http://127.0.0.1:8101/check`, record scores + missing sections.
- Step 2: Run the orchestrator (load workers, generate, write, **run each worker’s TEST_PROCESS** from repo root, write `results/workers/WORKER_NNN.json`); then run `pytest -q tests/validation/test_semantic_analyzer.py`.
- Step 3 (approval-gated): deploy to TEST and run an in-container smoke check (do not print secrets).

### 7. TEST_RESULTS_FORMAT
- Output a summary table + machine-readable JSON:
  - `{ "phase": "1A", "environment": "test", "workers": [{"id":"WORKER_001","score":92,"approved":true}, ...] }`

### 8. TASK_CLASSIFICATION
- **HYBRID**: procedural execution + judgment calls on instruction quality.

### 9. RETROSPECTIVE
- Record what failed, why, and what was changed; store retrospective in mem0 under `user_id: "wingman"` (when running full executions).

### 10. PERFORMANCE_REQUIREMENTS
- Step 1 quality gate: complete within **15 minutes** for WORKER_001–018 (including fixes/rechecks).
- Step 2 unit tests: complete within **5 minutes** locally.

### Phase 1: Meta-Worker Execution (Generate Instructions)

1. **Wingman-Specific Meta-Workers** (3 meta-workers)
   - META_WORKER_WINGMAN_01: Phase 1 core validators (WORKER_001–054)
   - META_WORKER_WINGMAN_02: Phase 2 content quality + scoring (WORKER_055–087)
   - META_WORKER_WINGMAN_03: Phases 3–6 integration/testing/deploy/tuning (WORKER_088–225)

2. **Execute Meta-Workers**
   - Input: `VALIDATION_ENHANCEMENT_IMPLEMENTATION_PLAN.md`
   - Output: 225 worker instruction files (WORKER_001–225)
   - Each meta-worker reads the plan and generates 10-point instructions

3. **Quality-gate worker instructions (NO approval spam)**
   - Use Wingman instruction validation (`POST /check`) on the **current phase** worker set (e.g., Semantic Analyzer only)
   - Threshold: ≥80% quality score required
   - Rejected workers revised and re-checked

### Phase 2: Worker Execution (Implement Tasks)

4. **Execute Phase Workers** (phase-gated)
   - Execute only the workers required for the current capability, then run tests and capture evidence
   - Deploy to TEST only when the phase is complete (approval-gated destructive ops)

5. **Store Results & Retrospectives**
   - Each worker writes execution results to `results/workers/WORKER_[ID].json`
   - Lessons learned stored in mem0 for continuous improvement
   - Results are gitignored (local-only artifacts)

---

## 10-Point Instruction Framework

All worker instructions follow this structure. **Wingman worker .md files** use the **exact section headers the orchestrator parses** (1–7 and 8–10 below). The generic template uses RESOURCE_REQUIREMENTS / RISK_ASSESSMENT / QUALITY_METRICS for 8–10; the **orchestrator** expects **TASK_CLASSIFICATION**, **RETROSPECTIVE**, **PERFORMANCE_REQUIREMENTS** for sections 8–10. See `COMPLETE_WORKFLOW.md` and `wingman_orchestrator.py` for the parsed set.

1. **DELIVERABLES** - What must be created (files, code, tests, docs)
2. **SUCCESS_CRITERIA** - How to verify completion (tests pass, endpoints work)
3. **BOUNDARIES** - What NOT to change (scope limits, no refactoring)
4. **DEPENDENCIES** - Prerequisites (services, files, APIs)
5. **MITIGATION** - Rollback procedures if task fails
6. **TEST_PROCESS** - **Per-worker**: bash commands in a code block, run from repo root to validate this worker’s deliverable. (Orchestrator-level “6. TEST_PROCESS” = the three-step Phase 1A process; see above.)
7. **TEST_RESULTS_FORMAT** - How to present evidence (command output, screenshots)
8. **TASK_CLASSIFICATION** - Type (MECHANICAL/CREATIVE), tool selection (orchestrator-parsed)
9. **RETROSPECTIVE** - Lessons learned, store in mem0 (orchestrator-parsed)
10. **PERFORMANCE_REQUIREMENTS** - Baseline vs target metrics (orchestrator-parsed)

---

## Anti-Contamination Rules

**CRITICAL**: Wingman ai-workers are completely separate from intel-system ai-workers

### Imperial Separation Principles

1. **One-Way Copy Only**
   - ✅ Copied infrastructure (meta-workers, templates) FROM intel-system TO wingman
   - ❌ Never sync changes back and forth
   - After initial copy, the two repos diverge completely

2. **No Intel-System References**
   - ❌ No mentions of "intel-system", "SAP", "Neo4j", "ChromaDB" in wingman workers
   - ✅ All worker content must be wingman-specific

3. **No Shared Workers**
   - Intel-system: WORKER_001-200 (PostgreSQL, SAP, Neo4j tasks)
   - Wingman: WORKER_001-225 (validation enhancement; Phase 1A = WORKER_001–018)
   - Even if numbers overlap, content is completely different

4. **Separate Results**
   - intel-system/ai-workers/results/ → intel-system execution data
   - wingman/ai-workers/results/ → wingman execution data
   - Never mix or cross-reference

5. **Git Boundaries**
   - Pre-commit hook prevents staging files outside wingman/
   - Always work from wingman/ subdirectory for git operations
   - See CLAUDE.md Rule 14 for git workflow

---

## Usage Instructions

### Creating a New Meta-Worker

```markdown
# META_WORKER_WINGMAN_01_INSTRUCTION.md

## YOUR TASK
Generate complete 10-point work instructions for Workers 1-10 (Phase 1 validators).

## SOURCE MATERIALS
1. Original Plan: `/Volumes/Data/ai_projects/wingman-system/wingman/docs/VALIDATION_ENHANCEMENT_IMPLEMENTATION_PLAN.md`
2. Template: Meta-worker templates in `ai-workers/meta-workers/META_WORKER_01_INSTRUCTION.md`

## OUTPUT REQUIREMENTS
For each worker (1-10), create:
- File: `ai-workers/workers/WORKER_[ID]_[TITLE].md`
- Format: 10-point framework (DELIVERABLES through QUALITY_METRICS)
- Content: Extract from implementation plan Phase 1 tasks
```

### Executing Workers (Manual)

```bash
# Execute a single worker
claude --file ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md

# Quality-gate the worker instruction (NO approval spam)
# Use Wingman instruction validation endpoint:
python3 - <<'PY' | curl -s -X POST http://127.0.0.1:8101/check -H "Content-Type: application/json" -d @-
import json
from pathlib import Path
print(json.dumps({"instruction": Path("ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md").read_text()}))
PY

# Store results
echo '{"worker_id": "001", "status": "pass", "duration": 3600}' > results/workers/WORKER_001.json
```

### Executing Workers (Orchestrated)

Use the wingman orchestrator and run script (see `ORCHESTRATOR_AID_PHASE_1A.md` and `COMPLETE_WORKFLOW.md`):

```bash
# From repo root: Phase 1A (WORKER_001–018)
./ai-workers/run_orchestrator.sh --phase 1a

# Or with venv active:
python ai-workers/scripts/wingman_orchestrator.py --phase 1a --batch-size 5

# Worker range (e.g. 001-018)
python ai-workers/scripts/wingman_orchestrator.py --workers 001-018
```

The orchestrator loads worker instructions, generates code (LLM), writes deliverables, runs each worker’s **per-worker TEST_PROCESS** from repo root, and writes `ai-workers/results/workers/WORKER_NNN.json` for every worker.

---

## Results Storage

All results are stored locally and gitignored:

```json
// results/workers/WORKER_001.json
{
  "worker_id": "001",
  "worker_name": "Semantic Analyzer Implementation",
  "status": "pass",
  "deliverables_created": [
    "validation/semantic_analyzer.py",
    "tests/validation/test_semantic_analyzer.py"
  ],
  "test_results": {
    "unit_tests": "23/23 passed",
    "integration_tests": "5/5 passed"
  },
  "evidence": "pytest output showing 100% pass rate",
  "duration_seconds": 3600,
  "timestamp": "2026-01-12T23:00:00Z",
  "approval_id": "abc-123",
  "approval_score": 92
}
```

---

## Next Steps

1. **Create 3 wingman-specific meta-workers** (META_WORKER_WINGMAN_01-03)
2. **Execute meta-workers** to generate 225 worker instructions
3. **Execute phase-by-phase** (one capability at a time): build → test → deploy (TEST) → review evidence
4. **Use Wingman approvals only for destructive steps** (deploy/restart/rebuild), not for every worker instruction
5. **Store retrospectives in mem0** for continuous learning

---

## References

- Original Plan: `wingman/docs/VALIDATION_ENHANCEMENT_IMPLEMENTATION_PLAN.md`
- Migration Plan: `wingman/docs/AI_WORKERS_MIGRATION_PLAN.md`
- Intel-System Source: `/Volumes/Data/ai_projects/intel-system/ai-workers/` (200 workers)

**Migration Status**: COMPLETE (2026-01-12)
**Next Action**: Create META_WORKER_WINGMAN_01-03
