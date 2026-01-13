# CLAUDE.md — Core Instructions & Critical Rules (Wingman Repo)
This file is the **single source of truth** for how work is executed in this repository.

## 🚨 CRITICAL — NEVER COMPROMISE THESE RULES 🚨
1. **NEVER push to GitHub** unless the User explicitly says **"push to github"**.
2. **PROTECT MARK'S ROLE**: maintain an interpretation layer — provide **insights**, not internal process exposition.
3. **ABSOLUTE AUTONOMY**: execute immediately, but **never bypass** required human-in-the-loop approval gates.
4. **THREE-LAYER PROTECTION**: physical/filesystem + container/network + application controls; do not weaken security for convenience.
5. **CONDITIONAL AUTONOMY FOR DESTRUCTIVE OPERATIONS**: For any destructive operation (Docker stop/remove/rebuild, file deletion, database changes, production deployments), you MUST request Wingman approval via `POST /approvals/request` and wait for APPROVED status before executing. Do NOT execute destructive operations autonomously, even if the user requests them. The only exception is if the operation is explicitly marked as low-risk and auto-approved by Wingman.
6. **BASICS FIRST**: get the simple version working end-to-end before adding complexity.
13. **WINGMAN APPROVAL REQUIRED FOR ALL DESTRUCTIVE OPERATIONS**: Before executing any destructive operation (including but not limited to: Docker container stop/remove/rebuild, file deletion, database schema changes, production deployments, system configuration changes), you MUST:
   - Submit an approval request to Wingman API (`POST /approvals/request`)
   - Wait for the approval to be APPROVED or AUTO_APPROVED
   - If REJECTED or timeout, abort the operation and report to the user
   - Only execute the operation after receiving explicit approval
   - This applies to ALL systems (Wingman, Intel-system, Mem0, cv-automation, and any future clients)
   - Use `WingmanApprovalClient` library when available, or direct API calls if library is not available

14. **GIT WORKFLOW - ANTI-CONTAMINATION RULES**: This repo contains ONLY wingman/ subdirectory. To prevent cross-project contamination:
   - **ALWAYS work from wingman/ subdirectory** when doing git operations
   - **NEVER run `git add -A` from project root** (/Volumes/Data/ai_projects/wingman-system)
   - **ALWAYS run `git add .` from wingman/ subdirectory** (cd wingman && git add .)
   - **ALWAYS verify `git status` before commit** - if you see files outside wingman/, STOP and ask user
   - **Pre-commit hook will block** non-wingman/ files automatically
   - **Why**: Other projects (intel-system, cv-automation, mem0, migration docs) may exist at root level but must NOT be committed to wingman repo
   - **If uncertain about git state**: Ask user before staging files

15. **MEM0 NAMESPACE REQUIREMENT**: This repo has a dedicated mem0 namespace that MUST ALWAYS be used:
   - **ALWAYS use user_id**: `wingman` for all mem0 operations
   - **TEST environment**: `http://127.0.0.1:18888` (mem0_server_test)
   - **PRD environment**: `http://127.0.0.1:8889` (mem0_server_prd)
   - **Store worker retrospectives**: All AI worker executions must store retrospectives in mem0 (10-point framework point 9)
   - **Store execution strategies**: All execution plans and monitoring data stored in mem0
   - **Never use other namespaces**: intel-system, cv-automation have their own mem0 namespaces - do not cross-contaminate
   - **API endpoint**: `POST http://127.0.0.1:18888/memories` with `user_id: "wingman"`

## ✅ Truth-build standards (how we work)
- **Do what was asked; nothing more, nothing less.**
- **Incremental**: small steps, each independently validated.
- **Honest reporting**: if something cannot be verified from here, say so and request the minimum required input.
- **No secrets in output**: never print tokens/passwords/keys; use quiet/summary modes.

## Limits (be explicit)
- **No GitHub push without the exact phrase**: "push to github".
- **No “I accessed your credentials/emails/calendar” claims**: if external data is needed, the user must provide it.
- **Do not hard-code credentials** anywhere (code/images/compose/scripts/docs).

## Command formatting (copy-paste friendly)
- **Always format commands for direct copy-paste**: commands must work when pasted directly into terminal.
- **Single-line commands preferred**: keep commands on one line when possible (even if long).
- **If line continuation needed**: use proper backslash (`\`) continuation with indentation:
  ```bash
  docker compose -f docker-compose.prd.yml -p wingman-prd \
    --env-file .env.prd rm -f telegram-bot
  ```
- **Never break commands mid-argument**: `--env-file` and its value must stay together.
- **Always use code blocks**: wrap all commands in ` ```bash ` blocks for proper formatting.
- **Test copy-paste**: ensure commands can be copied and pasted without syntax errors.

---

## Repo operating rules (Agent + Human)
This repository contains the Wingman system and its Docker deployment stacks.

## Security: non-negotiables
- **Never commit secrets**: no passwords, tokens, API keys, client secrets, certs, or secret-bearing `.env` files.
- **Environment files are local-only**:
  - Use `.env.test`, `.env.prd` locally.
  - Keep examples in `wingman/env.*.example` only.
- **No hard-coded credentials** in code, images, compose files, or scripts.
- **Prefer localhost-bound ports** (`127.0.0.1:...`) for host publishing.
- **Do not print secrets** in logs/CI output. When validating, use “quiet” modes.

## Repo layout (high level)
- `wingman/`: application code + primary compose stacks
  - `wingman/docker-compose.yml` (TEST stack)
  - `wingman/docker-compose.prd.yml` (PRD stack)
- `docker-compose-wingman.yml`: legacy/alternate compose (do not assume it is active unless explicitly used)
- `docs/`: design and operational references (do not copy sensitive content into runtime configs)

## Docker Compose conventions
- Always use Compose v2:

```bash
docker compose version
```

- Prefer explicit compose file + project name, so stacks don’t collide:

```bash
# TEST
docker compose -f wingman/docker-compose.yml -p wingman-test ps

# PRD
docker compose -f wingman/docker-compose.prd.yml -p wingman-prd --env-file wingman/.env.prd ps
```

### Healthchecks must not depend on missing tools
- Example: the upstream `ollama/ollama` image does **not** ship with `curl`, so use `ollama list` (or another built-in command) for health probes.

## DR flow (cold start / stop / remove)
The DR test must be executed with **human-in-the-loop approval gates** (see next section).

### Stop + remove (containers + networks; keep volumes unless explicitly wiping)

```bash
# TEST
docker compose -f wingman/docker-compose.yml -p wingman-test down --remove-orphans

# PRD
docker compose -f wingman/docker-compose.prd.yml -p wingman-prd --env-file wingman/.env.prd down --remove-orphans
```

### Cold start

```bash
# TEST
docker compose -f wingman/docker-compose.yml -p wingman-test up -d --build

# PRD
docker compose -f wingman/docker-compose.prd.yml -p wingman-prd --env-file wingman/.env.prd up -d --build
```

### Validation (no secrets printed)

```bash
# Render/validate compose without dumping values:
docker compose -f wingman/docker-compose.yml -p wingman-test config --quiet
docker compose -f wingman/docker-compose.prd.yml -p wingman-prd --env-file wingman/.env.prd config --quiet
```

## Mandatory HITL approvals for DR
The DR test must be staged and **blocked until Wingman approves** each stage:
- Stage A: Stop stacks
- Stage B: Remove stacks
- Stage C: Cold start TEST
- Stage D: Validate TEST (API health + Telegram bot)
- Stage E: Cold start PRD
- Stage F: Validate PRD (API health + Telegram bot)

Implementation note: use the Wingman API approval endpoints:
- `POST /approvals/request`
- `GET /approvals/pending`
- `POST /approvals/<id>/approve`
- `POST /approvals/<id>/reject`

## Telegram validation (TEST + PRD)
Telegram must be validated at runtime from inside the bot container (no secrets printed):

```bash
# TEST: check bot can reach Telegram
docker compose -f wingman/docker-compose.yml -p wingman-test exec -T telegram-bot \
  python -c "import os,requests; t=os.environ.get('BOT_TOKEN'); assert t; r=requests.get(f'https://api.telegram.org/bot{t}/getMe',timeout=10); print('ok' if r.ok else r.status_code)"

# PRD: check bot can reach Telegram
docker compose -f wingman/docker-compose.prd.yml -p wingman-prd --env-file wingman/.env.prd exec -T telegram-bot \
  python -c "import os,requests; t=os.environ.get('BOT_TOKEN'); assert t; r=requests.get(f'https://api.telegram.org/bot{t}/getMe',timeout=10); print('ok' if r.ok else r.status_code)"
```

If `getMe` is OK, confirm send/receive by sending a test message to the configured chat (do not print the token).

## Migration notes (from intel-system `CLAUDE.md`)
- **Policy text can be merged**, but **never include secrets** (tokens/passwords/keys) or claims about accessing external credential stores.
- External file paths referenced in intel-system docs are **not copied automatically** into this repo; only copy in **sanitized**, repo-relevant content.

