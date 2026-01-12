# AI Workers Results (Wingman-Specific)

**Purpose**: Store execution results from wingman ai-workers (gitignored, local-only)

---

## Structure

- `meta-workers/` - Results from meta-workers that generate worker instructions
- `workers/` - Results from individual worker executions

---

## Result Format

All results are stored in JSON format following this schema:

```json
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
  "evidence": "Validation output or screenshot path",
  "duration_seconds": 3600,
  "timestamp": "2026-01-12T23:00:00Z",
  "approval_id": "abc-123",
  "approval_score": 92,
  "retrospective": {
    "lessons_learned": ["Key insight 1", "Key insight 2"],
    "stored_in_mem0": true
  }
}
```

---

## Rules

- **Do NOT commit results to git** (automatically gitignored)
- **Results are local-only artifacts** for debugging and retrospectives
- **Keep results for analysis** but they don't need to be shared in repo
- **Store lessons learned in mem0** for continuous improvement

---

## File Naming Convention

- Meta-workers: `meta-workers/META_WORKER_WINGMAN_01.json`
- Workers: `workers/WORKER_001.json`

---

## Usage

```bash
# View a worker's result
cat results/workers/WORKER_001.json | python3 -m json.tool

# Check all completed workers
ls -la results/workers/*.json

# Aggregate results (once orchestration scripts added)
python scripts/aggregate_results.py --output validation_enhancement_report.md
```

---

**Note**: This directory structure mirrors intel-system but contains ONLY wingman execution data. No cross-contamination.
