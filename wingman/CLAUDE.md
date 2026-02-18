# CLAUDE.md — Wingman Core Rules

This file is the **single source of truth** for how work is executed in this repository.

## 🚨 HARD RULES (non-negotiable)

1. **NEVER push to GitHub** unless Mark explicitly says **"push to github"**
2. **PROTECT MARK'S ROLE** — maintain an interpretation layer; provide insights, not internal process exposition
3. **ABSOLUTE AUTONOMY** — execute immediately, but never bypass required human-in-the-loop approval gates
4. **THREE-LAYER PROTECTION** — physical/filesystem + container/network + application controls; do not weaken security
5. **CONDITIONAL AUTONOMY FOR DESTRUCTIVE OPERATIONS** — request Wingman approval via `POST /approvals/request`; wait for APPROVED status before executing (see [.claude/rules/approvals.md](.claude/rules/approvals.md))
6. **BASICS FIRST** — get the simple version working end-to-end before adding complexity

## Project

- **Repository:** Wingman system and Docker deployment stacks
- **Root:** `/Volumes/Data/ai_projects/wingman-system/wingman`
- **Remote:** `https://github.com/mastermagoo/wingman-system.git`
- **Branch:** `main` (commits), `dev` (PRs)

## Repo Layout

- `wingman/` — application code + primary compose stacks
  - `docker-compose.yml` (TEST stack)
  - `docker-compose.prd.yml` (PRD stack)
- `docs/` — design and operational references
- `tools/` — docker wrapper and utilities
- `migrations/` — database migrations
- `ai-workers/` — AI worker scripts

## Commit Conventions

Use conventional commits:
- `feat(wingman):` / `fix(wingman):` / `chore(wingman):` / `docs(wingman):` / `refactor(wingman):`

## Truth-Build Standards

- Do what was asked; nothing more, nothing less
- Incremental: small steps, each independently validated
- Honest reporting: if something cannot be verified from here, say so
- No secrets in output: never print tokens/passwords/keys; use quiet/summary modes

## Key Rules (see `.claude/rules/` for details)

- **Security**: [.claude/rules/security.md](.claude/rules/security.md) — never commit secrets, localhost-bound ports, no hard-coded credentials
- **Git Workflow**: [.claude/rules/git-workflow.md](.claude/rules/git-workflow.md) — anti-contamination rules; always work from `wingman/` subdirectory
- **Mem0 Namespace**: [.claude/rules/mem0-namespace.md](.claude/rules/mem0-namespace.md) — ALWAYS use `user_id: "wingman"` for all mem0 operations
- **Docker Wrapper**: [.claude/rules/docker-wrapper.md](.claude/rules/docker-wrapper.md) — MANDATORY wrapper for all docker/compose commands
- **Approvals**: [.claude/rules/approvals.md](.claude/rules/approvals.md) — approval flow + bootstrap exception for Wingman self-updates
- **Deployment**: [.claude/rules/deployment.md](.claude/rules/deployment.md) — compose conventions, DR flow, Telegram validation
- **Command Formatting**: [.claude/rules/command-formatting.md](.claude/rules/command-formatting.md) — copy-paste friendly commands

## Environments

**TEST**: `http://localhost:8101` (API), `http://localhost:18888` (mem0)
**PRD**: `http://localhost:5001` (API), `http://localhost:8889` (mem0)

## Quick Verification

```bash
# Verify docker wrapper is active
which docker
# Expected: /Volumes/Data/ai_projects/wingman-system/wingman/tools/docker

# Check git status (no files outside wingman/)
cd /Volumes/Data/ai_projects/wingman-system/wingman && git status

# Verify no secrets in compose files
grep -r "password\|secret\|token" docker-compose*.yml | grep -v "\${" | grep -v "REPLACE_ME"

# Validate compose configs (no secrets printed)
docker compose -f docker-compose.yml -p wingman-test config --quiet
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd config --quiet

# Check TEST stack health
curl -s http://localhost:8101/health

# Check PRD stack health
curl -s http://localhost:5001/health
```

## What I Can Do

Execute Python/bash scripts, manage Docker (via wrapper), commit to git, document deployments, run tests, validate configs, request approvals, validate AI worker output.

## What I Cannot Do

Push to GitHub without explicit "push to github" command, bypass approval gates, commit secrets, access external credentials directly, execute destructive operations without approval.

## Philosophy

This system is:
- **Approval Authority** — all systems request approval for destructive operations
- **Output Validator** — all AI-generated code validated before deployment
- **Self-Healing** — monitors and recovers with human oversight
- **Bootstrap Exception** — can self-update with user approval (can't approve itself)
- **Three-Layer Security** — physical/filesystem + container/network + application controls
- **Truth-Build** — do what was asked, nothing more, nothing less

**Wingman watches, validates, and protects — but never operates alone.**
