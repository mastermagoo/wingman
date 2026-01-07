# CLAUDE.md — Core Instructions & Critical Rules (Wingman Repo)
This file is the **single source of truth** for how work is executed in this repository.

## 🚨 CRITICAL — NEVER COMPROMISE THESE RULES 🚨
1. **NEVER push to GitHub** unless the User explicitly says **"push to github"**.
2. **PROTECT MARK'S ROLE**: maintain an interpretation layer — provide **insights**, not internal process exposition.
3. **ABSOLUTE AUTONOMY**: execute immediately, but **never bypass** required human-in-the-loop approval gates.
4. **THREE-LAYER PROTECTION**: physical/filesystem + container/network + application controls; do not weaken security for convenience.
5. **FACTUAL REAL SOLUTIONS ONLY**: do not claim checks were performed without evidence; prefer real validation commands and outputs.
6. **BASICS FIRST**: get the simple version working end-to-end before adding complexity.

## ✅ Truth-build standards (how we work)
- **Do what was asked; nothing more, nothing less.**
- **Incremental**: small steps, each independently validated.
- **Honest reporting**: if something cannot be verified from here, say so and request the minimum required input.
- **No secrets in output**: never print tokens/passwords/keys; use quiet/summary modes.

## Limits (be explicit)
- **No GitHub push without the exact phrase**: "push to github".
- **No “I accessed your credentials/emails/calendar” claims**: if external data is needed, the user must provide it.
- **Do not hard-code credentials** anywhere (code/images/compose/scripts/docs).

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

