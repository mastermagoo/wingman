# Complete Workflow — Orchestrator, Worker Instructions, Full Validation

**Purpose**: Single reference for the **entire** workflow: orchestrator-level steps, worker instructions (10-point format), per-worker validation, results storage, and how everything ties together. No shortcuts: changes here must stay consistent with the orchestrator script, README, ORCHESTRATOR_AID, and `orchestrator_input_phase1a.json`.

---

## 1. Two different “TEST_PROCESS” meanings (avoid breakage)

| Scope | Where it lives | Meaning |
|-------|----------------|---------|
| **Per-worker TEST_PROCESS** | Each worker file: `## 6. TEST_PROCESS` in `ai-workers/workers/WORKER_NNN_*.md` | Bash commands run **from repo root** to validate **that worker’s** deliverable. The orchestrator parses these from ```bash code block(s), coalesces multi-line `python3 -c "..."`, and runs each command; all must exit 0 for that worker to pass. |
| **Orchestrator-level Phase 1A process** | README “Orchestrator Phase 1A Instructions” and ORCHESTRATOR_AID: subsection “6. TEST_PROCESS” | The **overall** Phase 1A steps: Step 1 = POST each worker to `/check`, Step 2 = run orchestrator (build + per-worker validation), Step 3 = deploy (approval-gated). |

Do not confuse them: per-worker TEST_PROCESS = commands inside each worker .md; orchestrator-level = the three-step Phase 1A process.

---

## 2. Orchestrator-level workflow (full job)

The **full job** for Phase 1A is three steps. The orchestrator script implements **Step 2** only. Steps 1 and 3 are documented in ORCHESTRATOR_AID and README.

| Step | What | Where |
|------|------|--------|
| **Step 1: Instruction quality gate** | POST each of the 18 worker instructions (full markdown) to `http://127.0.0.1:8101/check`. Threshold ≥ 80. Fix failing instructions and re-check. | ORCHESTRATOR_AID_PHASE_1A.md; machine-readable input: `orchestrator_input_phase1a.json` (`check`, `worker_files`). |
| **Step 2: Build and validate** | Run the orchestrator: load workers → for each worker generate code (LLM) → write deliverable → run **per-worker TEST_PROCESS** from repo root → write result to `results/workers/WORKER_NNN.json`. | Script: `ai-workers/scripts/wingman_orchestrator.py`; entry: `./ai-workers/run_orchestrator.sh --phase 1a`. |
| **Step 3: Deploy (approval-gated)** | Request approval, then run deploy command; smoke test in container. | ORCHESTRATOR_AID_PHASE_1A.md Step 3; `orchestrator_input_phase1a.json` (`approvals_request`, `deploy`, `smoke_test`). |

Success criteria for Phase 1A (README, ORCHESTRATOR_AID): all workers score ≥ 80 on `/check`; per-worker validation passes for each; `pytest -q tests/validation/test_semantic_analyzer.py` exits 0; after deploy, smoke test returns dict with expected keys.

---

## 3. Worker instructions (what the orchestrator reads)

### Location and naming

- **Path**: `ai-workers/workers/WORKER_NNN_*.md` (e.g. `WORKER_001_Semantic_Class_Skeleton.md`).
- **Naming**: `WORKER_<3-digit-id>_<Name>.md`. The orchestrator loads by ID (e.g. `--phase 1a` → WORKER_001–WORKER_018).
- **Canonical list for Phase 1A**: `orchestrator_input_phase1a.json` → `worker_files`.

### 10-point framework (exact section names the orchestrator parses)

The **orchestrator** parses these section headers (see `wingman_orchestrator.py`). Worker .md files must use these exact titles for sections 1–10:

| # | Section header (exact) | Orchestrator use |
|---|------------------------|------------------|
| 1. DELIVERABLES | List of items; first backticked `*.py` path = deliverable file (repo-root-relative). |
| 2. SUCCESS_CRITERIA | Passed to LLM. |
| 3. BOUNDARIES | Passed to LLM. |
| 4. DEPENDENCIES | Passed to LLM. |
| 5. MITIGATION | Passed to LLM. |
| **6. TEST_PROCESS** | **Per-worker validation**: Commands from ```bash code block(s). Multi-line `python3 -c "..."` / `'...'` coalesced into one command. Each command run from **repo root**; all must exit 0 for that worker to pass. |
| 7. TEST_RESULTS_FORMAT | Optional; JSON block parsed. |
| 8. TASK_CLASSIFICATION | Passed to LLM / metadata. |
| 9. RETROSPECTIVE | Passed to LLM / metadata. |
| 10. PERFORMANCE_REQUIREMENTS | Passed to LLM / metadata. |

README also documents a **generic** 10-point template (8–10 as RESOURCE_REQUIREMENTS, RISK_ASSESSMENT, QUALITY_METRICS). **Wingman worker files** use the **orchestrator’s** set above (8. TASK_CLASSIFICATION, 9. RETROSPECTIVE, 10. PERFORMANCE_REQUIREMENTS). The implementation plan and other docs may use the generic names; the script only parses the exact headers above.

### Deliverable path rules (must match repo layout)

- Paths in instructions must be **repo-root-relative** (e.g. `validation/semantic_analyzer.py`, `tests/validation/test_semantic_analyzer.py`).
- No `wingman/` prefix; no `cd wingman` in per-worker TEST_PROCESS commands.
- Pytest in TEST_PROCESS: use `tests/validation/test_semantic_analyzer.py` (not `tests/test_semantic_analyzer.py`).

---

## 4. Orchestrator per-worker flow (Step 2 in detail)

### Repo root

- Derived from script path: `Path(__file__).resolve().parent.parent.parent` (i.e. `ai-workers/scripts/wingman_orchestrator.py` → repo root). **Not** `cwd`.

### For each worker

1. **Load instruction** — Read `ai-workers/workers/WORKER_NNN_*.md`, parse 10-point sections (DELIVERABLES, TEST_PROCESS, etc.).
2. **Generate code** — LLM (OpenAI or Ollama) with DELIVERABLES, SUCCESS_CRITERIA, BOUNDARIES, etc.
3. **Anti-guide check** — If output looks like a guide → GUIDE_DETECTED; fail worker, write result JSON, no deliverable write.
4. **Write deliverables** — First backticked `*.py` in DELIVERABLES → resolve path from repo root, write generated code; set `execution.deliverables_created` to that path.
5. **Validate (per-worker)** — Run each parsed **per-worker TEST_PROCESS** command from repo root (`subprocess.run(..., cwd=repo_root)`). All must exit 0 → worker COMPLETED; else VALIDATION FAILED.
6. **Write result** — **Always** write `ai-workers/results/workers/WORKER_NNN.json` (pass or fail). Format: `worker_id`, `worker_name`, `status`, `deliverables_created`, `test_results`, `duration_seconds`, `timestamp`, `llm_provider`, `errors`. See README “Results Storage” for the intended shape.
7. **Retrospective** — If COMPLETED, optionally store retrospective in mem0.

Batch execution: workers run in batches (`--batch-size`); each worker still gets the full flow above. Results dir: `ai-workers/results`; worker results under `ai-workers/results/workers/`.

---

## 5. Results storage (no shortcut)

- **Directory**: `ai-workers/results/` (created by orchestrator); per-worker files: `ai-workers/results/workers/WORKER_NNN.json`.
- **When**: After **every** worker run (COMPLETED, VALIDATION FAILED, GUIDE_DETECTED, or ERROR).
- **Content**: `worker_id`, `worker_name`, `status`, `deliverables_created`, `test_results`, `duration_seconds`, `timestamp`, `llm_provider`, `errors`. README “Results Storage” describes the intended format; the orchestrator writes this so downstream steps (evidence, reports) can rely on it.

---

## 6. E2E verification (path/command sanity)

**Script**: `ai-workers/scripts/verify_phase1a_e2e.py`

- Uses the **same** parsing as the orchestrator (DELIVERABLES, per-worker TEST_PROCESS, multi-line coalescing).
- Checks all 18 Phase 1A workers for path/command anti-patterns; runs WORKER_001 tests with minimal `validation/semantic_analyzer.py`; runs WORKER_002–018 commands and fails only on path/command errors.
- Run from repo root: `./ai-workers/.venv/bin/python ai-workers/scripts/verify_phase1a_e2e.py`. Exit 0 → path/command/parsing correct for Phase 1A.

---

## 7. Machine-readable and other references

| Item | Purpose |
|------|--------|
| `ai-workers/orchestrator_input_phase1a.json` | Phase 1A API endpoints, worker list, deliverables, test commands, deploy, smoke test, success criteria. Use for /check, scripts, or tooling. |
| `ai-workers/ORCHESTRATOR_AID_PHASE_1A.md` | Prerequisites, Step 1–3, worker file list, deploy body, success criteria. |
| `ai-workers/README.md` | Overview, directory structure, **orchestrator-level** Phase 1A steps (including “6. TEST_PROCESS” = three-step process), 10-point framework (generic + enhanced), results storage, anti-contamination, usage. |
| `docs/VALIDATION_ENHANCEMENT_IMPLEMENTATION_PLAN.md` | Source of tasks and phases; worker instructions are derived from it. |
| `ai-workers/scripts/wingman_orchestrator.py` | Implementation: section parsing, deliverable write, per-worker TEST_PROCESS execution, result JSON write. |

---

## 8. Consistency rules (avoid breaking the job elsewhere)

1. **Per-worker TEST_PROCESS** = section 6 in each worker .md; **orchestrator-level process** = Step 1 /check, Step 2 orchestrator run, Step 3 deploy. Keep the two clearly separated in any doc or script.
2. **Section names 1–10** in worker files must match what the orchestrator parses (see table in §3). Do not change parsing in the script without updating this doc and any generator/template.
3. **Paths** in worker instructions and in `orchestrator_input_phase1a.json` must be repo-root-relative and match the actual repo layout (no `wingman/` prefix; tests under `tests/validation/`).
4. **Results**: Orchestrator writes `results/workers/WORKER_NNN.json` for every worker. README and any reporting/evidence step should assume these files exist after a run.
5. **Entry points**: Orchestrated execution uses `wingman_orchestrator.py` and `./ai-workers/run_orchestrator.sh`. Do not reference non-existent scripts (e.g. `orchestrate.py`, `validate.py`, `aggregate_results.py`) as the main entry.

This is the **complete workflow** with **full validation** (per-worker TEST_PROCESS run by the orchestrator, results written for every worker), aligned with the orchestrator, README, ORCHESTRATOR_AID, and `orchestrator_input_phase1a.json`.
