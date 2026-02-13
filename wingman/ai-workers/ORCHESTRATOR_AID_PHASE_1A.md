# Orchestrator Aid — Phase 1A (Semantic Analyzer)

**Purpose**: Single "start here" for the **AI orchestrator** to run Phase 1A.  
**Role note**: The chat agent (Cursor AI) **assists the orchestrator only** — it does not design, build, test, or deploy. The orchestrator executes the steps below and **instructs the AI workers**; workers receive their instructions from the orchestrator.

**Complete workflow (orchestrator, worker instructions, full validation)**: See **`ai-workers/COMPLETE_WORKFLOW.md`** for the end-to-end flow: 10-point instruction format, how the orchestrator parses and validates (TEST_PROCESS from repo root), and E2E verification.

---

## Prerequisites (verify before starting)

| Check | Command / Location |
|-------|--------------------|
| TEST Wingman API | `curl -s http://127.0.0.1:8101/health` → healthy |
| Instruction check endpoint | `POST http://127.0.0.1:8101/check` (body: `{"instruction": "<full markdown>"}`) |
| Ollama (host) | `curl -s http://127.0.0.1:11434/api/tags` (or `OLLAMA_HOST`/`OLLAMA_PORT` from containers) |
| Phase 1A worker files | `ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md` … `WORKER_018_Semantic_Tests_Integration.md` |

**Repo root**: `/Volumes/Data/ai_projects/wingman-system/wingman` (or your clone path). All commands below assume this root.

---

## How to start the orchestrator (run the 18 workers)

**Repo root is derived from the script path** — you can run from any directory; the orchestrator and verification script both use the script’s location to find the repo.

1. **Verify path/command chain (required for 100% confidence):** Run the e2e verification once. It writes a minimal `validation/semantic_analyzer.py`, runs WORKER_001’s four test commands from repo root, and exits 0 only if all pass. The script uses the same parsing as the orchestrator for all 18 workers and fails only on path/command errors; any validation failure after this step is attributable to generated code or tests, not path/command mismatches.
   ```bash
   ./ai-workers/.venv/bin/python ai-workers/scripts/verify_phase1a_e2e.py
   ```
   (This overwrites `validation/semantic_analyzer.py` with a minimal version; use `git checkout validation/semantic_analyzer.py` to restore.)

2. **Ensure TEST Wingman API is up** (so `/check` and later approval/deploy work):  
   `curl -s http://127.0.0.1:8101/health`  
   If not healthy, start TEST stack:  
   `docker compose -f docker-compose.yml -p wingman-test --env-file .env.test up -d`

2. **Optional: run Step 1 (instruction quality gate)** — POST each of the 18 worker instructions to `/check` and fix any that score &lt; 80. Use the worker file list and `/check` example below, or a script that reads `orchestrator_input_phase1a.json` and POSTs each file.

4. **Start the orchestrator for the 18 Phase 1A workers** (use the run script so the venv is used automatically):
   ```bash
   ./ai-workers/run_orchestrator.sh --phase 1a
   ```
   Or activate the venv first, then run:
   ```bash
   source ai-workers/.venv/bin/activate
   python ai-workers/scripts/wingman_orchestrator.py --phase 1a
   ```
   **Phase 1A runs sequentially (batch_size=1)** — workers share `semantic_analyzer.py` and `test_semantic_analyzer.py`; parallel execution causes overwrites and validation failures. The orchestrator forces `batch_size=1` for `--phase 1a`. Other phases can use `--batch-size N`.

5. **Monitor progress** (optional): in another terminal, run `./monitor_orchestrator.sh` to watch `validation/semantic_analyzer.py` and `tests/validation/test_semantic_analyzer.py`.

**Required environment (Phase 1A):**
- **OPENAI_API_KEY** — Phase 1A uses OpenAI for all 18 workers. If unset, the orchestrator exits with a clear error before running. The run script `run_orchestrator.sh` auto-sources from repo root in this order: **`.env.ai-workers`**, then **`.env.test`**, then **`.env`** (later files override earlier). For Phase 1A (TEST), **`.env.test`** is the correct file when present (keys there are loaded). No PRD env or files are used or changed by the orchestrator. You can also `export OPENAI_API_KEY=...` before running.
- **requests** — In `ai-workers/requirements.txt`; run `./ai-workers/setup_venv.sh` to ensure the venv has it. Validation uses the venv Python so `requests` is available for WORKER_002.
- **WORKER_002 (Ollama)** — Test 3 expects `docker exec wingman-test-ollama-1 ollama list`. If your stack has no Ollama container (wingman uses shared host Ollama via intel-system), that test will fail. Start an Ollama container named `wingman-test-ollama-1`, or accept WORKER_002 validation failure and continue; workers 003+ do not require Ollama.

**OpenAI Tier 4:** If your account is **Tier 4**, set **`OPENAI_TIER=4`** in `.env.test` (or export it). For Phase 1A, the orchestrator **always uses batch_size=1** (sequential) because workers share files; Tier 4 settings apply to other phases. For non–Phase 1A runs, Tier 4 uses batch size 5 and 2s stagger; override with `OPENAI_TIER4_BATCH_SIZE` and `OPENAI_TIER4_STAGGER_SECONDS` if needed.

**Optional:** `MEM0_API_URL`, `MEM0_USER_ID` (e.g. in `.env.test` for TEST); `INTEL_LLM_PROCESSOR` only if you use Ollama workers. Step 1 (/check) and Step 3 (approvals) use TEST Wingman API at `http://127.0.0.1:8101`; the orchestrator run itself does not call that API.

**Note:** The orchestrator uses `ai-workers/workers` and `ai-workers/results`. Run from repo root.

**Dependencies (use a venv — macOS/Homebrew Python is externally managed):**
```bash
# One-time: create venv and install orchestrator deps
./ai-workers/setup_venv.sh

# Then activate and run (each time you open a new terminal)
source ai-workers/.venv/bin/activate
python ai-workers/scripts/wingman_orchestrator.py --phase 1a
```

---

## Step 1: Instruction quality gate (WORKER_001–018)

- **Action**: POST each worker instruction (full markdown) to `http://127.0.0.1:8101/check`.
- **Threshold**: Each worker must score **≥ 80**.
- **On failure**: Revise the failing worker instruction file(s), then re-run `/check` until all pass.
- **Output**: Pass/fail list + aggregate summary; optional machine-readable:  
  `{"phase":"1A","environment":"test","workers":[{"id":"WORKER_001","score":92,"approved":true}, ...]}`

**Worker IDs and files** (in order; paths relative to repo root):

| ID | Path |
|----|------|
| WORKER_001 | `ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md` |
| WORKER_002 | `ai-workers/workers/WORKER_002_Semantic_Ollama_Client.md` |
| WORKER_003 | `ai-workers/workers/WORKER_003_Semantic_Analyze_Method_Structure.md` |
| WORKER_004 | `ai-workers/workers/WORKER_004_Semantic_Score_Calculation.md` |
| WORKER_005 | `ai-workers/workers/WORKER_005_Semantic_Reasoning_Dict.md` |
| WORKER_006 | `ai-workers/workers/WORKER_006_Semantic_Error_Handling.md` |
| WORKER_007 | `ai-workers/workers/WORKER_007_Semantic_Clarity_Prompt.md` |
| WORKER_008 | `ai-workers/workers/WORKER_008_Semantic_Completeness_Prompt.md` |
| WORKER_009 | `ai-workers/workers/WORKER_009_Semantic_Coherence_Prompt.md` |
| WORKER_010 | `ai-workers/workers/WORKER_010_Semantic_Prompt_Parser.md` |
| WORKER_011 | `ai-workers/workers/WORKER_011_Semantic_Heuristic_Fallback.md` |
| WORKER_012 | `ai-workers/workers/WORKER_012_Semantic_Prompt_Consistency.md` |
| WORKER_013 | `ai-workers/workers/WORKER_013_Semantic_Tests_Clarity.md` |
| WORKER_014 | `ai-workers/workers/WORKER_014_Semantic_Tests_Completeness.md` |
| WORKER_015 | `ai-workers/workers/WORKER_015_Semantic_Tests_Coherence.md` |
| WORKER_016 | `ai-workers/workers/WORKER_016_Semantic_Tests_Edge_Cases.md` |
| WORKER_017 | `ai-workers/workers/WORKER_017_Semantic_Tests_Error_Handling.md` |
| WORKER_018 | `ai-workers/workers/WORKER_018_Semantic_Tests_Integration.md` |

**POST /check** — request body: `{"instruction": "<full markdown of worker file>"}`. Response: `approved` (bool), `score` (0–100), `missing_sections` (list), `validation`, `policy_checks`. Pass = `score >= 80`.

**Example (one worker)** — from repo root, sending WORKER_001:

```bash
curl -s -X POST http://127.0.0.1:8101/check -H "Content-Type: application/json" -d "{\"instruction\": \"$(cat ai-workers/workers/WORKER_001_Semantic_Class_Skeleton.md | sed 's/"/\\"/g' | tr '\n' ' ')\"}"
```

(Or read file in your script and POST `{"instruction": "<content>"}`.)

---

## Baseline facts (orchestrator context)

| Item | Status |
|------|--------|
| `validation/semantic_analyzer.py` | Does not exist yet; workers create it |
| `tests/validation/test_semantic_analyzer.py` | Exists; tests skipped until module exists |
| `tests/validation/fixtures.py` | Exists; has `SEMANTIC_ANALYZER_TEST_CASES` |
| Ollama | Shared host; containers use `OLLAMA_HOST`/`OLLAMA_PORT`; host: `http://127.0.0.1:11434/api/tags` |

---

## Step 2: Build and test (orchestrator instructs workers, then runs tests)

- **Action**: Orchestrator **instructs** AI workers (using WORKER_001–018) to produce:
  - `validation/semantic_analyzer.py` (SemanticAnalyzer, `analyze(...)`, Ollama path with timeouts/retry/fallback).
  - `tests/validation/test_semantic_analyzer.py` (no skips; mocks for non-LLM tests).
- **Validation**: From repo root:
  - `pytest -q tests/validation/test_semantic_analyzer.py` → exit **0** (no skips).
- **Mitigation**: If tests fail, fix code/tests (orchestrator/workers); rollback only affected files if needed.

---

## Step 3: Deploy to TEST (approval-gated)

- **Rule**: Any `docker compose up/down/rebuild/restart` is destructive → requires Wingman approval first.
- **Action**:
  1. **Request approval** — `POST http://127.0.0.1:8101/approvals/request`  
     Headers: `Content-Type: application/json` (and `X-Wingman-Approval-Request-Key: <key>` if API requires).  
     Body (instruction must contain the exact deploy command for later token mint):

     ```json
     {
       "worker_id": "phase1a_semantic",
       "task_name": "Deploy Semantic Analyzer to TEST",
       "instruction": "docker compose -f docker-compose.yml -p wingman-test --env-file .env.test up -d --build wingman-api",
       "deployment_env": "test"
     }
     ```

     Response: `needs_approval` (true/false), `status` (PENDING or AUTO_APPROVED), `request` (includes `id` for polling).
  2. **Wait for APPROVED** (e.g. poll `GET /approvals/<id>` or Telegram).
  3. **Deploy** (from repo root):  
     `docker compose -f docker-compose.yml -p wingman-test --env-file .env.test up -d --build wingman-api`
  4. **Smoke test** (no secrets in output):  
     `docker compose -f docker-compose.yml -p wingman-test exec -T wingman-api python -c "from validation.semantic_analyzer import SemanticAnalyzer; s=SemanticAnalyzer(); r=s.analyze('DELIVERABLES: Read logs\n...','smoke','test'); assert isinstance(r,dict); print('ok')"`

---

## Success criteria (Phase 1A)

- All WORKER_001–018 score ≥ 80 on TEST `/check`.
- `pytest -q tests/validation/test_semantic_analyzer.py` exits 0 (no skips).
- After deploy: smoke test returns a dict with expected shape (e.g. `risk_level`, `operation_types`, `blast_radius`, `reasoning`, `confidence`).

---

## References

- **Full Phase 1A deliverables and SMART criteria**: `docs/deployment/AAA_DELTA_REPORT_VALIDATION_DEPLOYMENT.md` (Semantic Analyzer section + measurable checklist).
- **Execution strategy and phase-gating**: `ai-workers/EXECUTION_STRATEGY.md`.
- **Worker framework and 10-point format**: `ai-workers/README.md`.
