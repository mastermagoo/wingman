# AI Workers Infrastructure (Wingman)

**Purpose**: Parallel execution framework for validation enhancement implementation

**Copied from**: intel-system ai-workers (proven at 200 workers)
**Adapted for**: Wingman validation enhancement (35 workers planned)
**Date**: 2026-01-12

---

## Overview

This directory contains the infrastructure for executing AI workers in parallel batches. Workers are AI agents that perform specific, well-defined tasks following a standardized 10-point instruction framework.

### Key Concepts

- **Workers**: AI agents that execute specific tasks (e.g., implement semantic analyzer, write tests)
- **Meta-Workers**: AI workers that generate worker instructions from source plans
- **10-Point Framework**: Standardized instruction format ensuring clarity and consistency
- **Parallel Execution**: Workers run in batches (5-10 concurrent) for 76% time reduction
- **Self-Validation**: All worker instructions submitted to Wingman for approval (≥80% score)

---

## Directory Structure

```
ai-workers/
├── README.md                    ← This file
├── meta-workers/                ← Meta-worker instruction templates (20 files)
│   ├── META_WORKER_01_INSTRUCTION.md
│   ├── META_WORKER_02_INSTRUCTION.md
│   └── ... (20 total - generic templates)
├── workers/                     ← Wingman-specific worker instructions
│   ├── WORKER_001_Execution_Gateway.md  (existing)
│   ├── WORKER_002_Command_Allowlist.md  (existing)
│   └── ... (will add 35 more for validation enhancement)
├── results/                     ← Execution results (gitignored)
│   ├── README.md
│   ├── meta-workers/            ← Meta-worker execution results
│   └── workers/                 ← Worker execution results
├── scripts/                     ← Orchestration scripts (empty for now)
└── templates/                   ← Reusable templates (if needed)
```

---

## How It Works

### Phase 1: Meta-Worker Execution (Generate Instructions)

1. **Create Wingman-Specific Meta-Workers** (3 meta-workers)
   - META_WORKER_WINGMAN_01: Generate Phase 1 validators workers (10 workers)
   - META_WORKER_WINGMAN_02: Generate Phase 2 quality validator workers (5 workers)
   - META_WORKER_WINGMAN_03: Generate Phase 4 testing workers (20 workers)

2. **Execute Meta-Workers** (sequential)
   - Input: `VALIDATION_ENHANCEMENT_IMPLEMENTATION_PLAN.md`
   - Output: 35 worker instruction files (WORKER_001-035.md)
   - Each meta-worker reads the plan and generates 10-point instructions

3. **Submit to Wingman for Approval**
   - All 35 worker instructions validated by Wingman API
   - Threshold: ≥80% quality score required
   - Rejected workers revised and resubmitted

### Phase 2: Worker Execution (Implement Tasks)

4. **Execute Approved Workers** (parallel batches)
   - Batch 1: WORKER_001-005 (5 parallel) - Semantic analyzer
   - Batch 2: WORKER_006-010 (5 parallel) - Code scanner + dependency
   - Batch 3: WORKER_011-015 (5 parallel) - Content quality validator
   - Batch 4: WORKER_016-035 (20 parallel) - Testing (203 tests)

5. **Store Results & Retrospectives**
   - Each worker writes execution results to `results/workers/WORKER_[ID].json`
   - Lessons learned stored in mem0 for continuous improvement
   - Results are gitignored (local-only artifacts)

---

## 10-Point Instruction Framework

All worker instructions follow this structure:

1. **DELIVERABLES** - What must be created (files, code, tests, docs)
2. **SUCCESS_CRITERIA** - How to verify completion (tests pass, endpoints work)
3. **BOUNDARIES** - What NOT to change (scope limits, no refactoring)
4. **DEPENDENCIES** - Prerequisites (services, files, APIs)
5. **MITIGATION** - Rollback procedures if task fails
6. **TEST_PROCESS** - Step-by-step validation instructions
7. **TEST_RESULTS_FORMAT** - How to present evidence (command output, screenshots)
8. **RESOURCE_REQUIREMENTS** - Time estimate, environment needs
9. **RISK_ASSESSMENT** - Impact level (LOW/MEDIUM/HIGH) + justification
10. **QUALITY_METRICS** - Success indicators (test coverage, performance)

**Enhanced Framework** (intel-system addition):
- **TASK_CLASSIFICATION** - Type (MECHANICAL/CREATIVE), tool selection
- **RETROSPECTIVE** - Lessons learned, store in mem0
- **PERFORMANCE_REQUIREMENTS** - Baseline vs target metrics

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
   - Wingman: WORKER_001-035 (validation enhancement tasks)
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
claude --file ai-workers/workers/WORKER_001_Semantic_Analyzer.md

# Submit to Wingman for approval
curl -X POST http://localhost:5001/approvals/request \
  -H "Content-Type: application/json" \
  -d @worker_approval_request.json

# Store results
echo '{"worker_id": "001", "status": "pass", "duration": 3600}' > results/workers/WORKER_001.json
```

### Executing Workers (Orchestrated - Future)

Once orchestration scripts are added:

```bash
# Execute all workers in parallel batches
python scripts/orchestrate.py --batch-size 5 --workers 001-035

# Validate all results
python scripts/validate.py --workers 001-035

# Aggregate results and generate report
python scripts/aggregate_results.py --output validation_enhancement_report.md
```

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
    "wingman/validation/semantic_analyzer.py",
    "wingman/tests/test_semantic_analyzer.py"
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
2. **Execute meta-workers** to generate 35 worker instructions
3. **Submit all workers to Wingman** for approval (≥80% threshold)
4. **Execute approved workers** in parallel batches
5. **Store retrospectives in mem0** for continuous learning

---

## References

- Original Plan: `wingman/docs/VALIDATION_ENHANCEMENT_IMPLEMENTATION_PLAN.md`
- Migration Plan: `wingman/docs/AI_WORKERS_MIGRATION_PLAN.md`
- Intel-System Source: `/Volumes/Data/ai_projects/intel-system/ai-workers/` (200 workers)

**Migration Status**: COMPLETE (2026-01-12)
**Next Action**: Create META_WORKER_WINGMAN_01-03
