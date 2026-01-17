# Wingman Architecture — Current Build Design (DEV/TEST/PRD)
**Version**: 1.0  

**Status**: CURRENT (authoritative for “what is implemented now”)  
**Last Updated**: 2026-01-17  
**Scope**: DEV / TEST / PRD  

---

## What this document is (and is not)

- **This is**: the design/implementation shape of the *current Wingman build* (what exists in code + compose stacks today).
- **This is not**: the long-term product vision. For that, see `../00-Strategic/AAA_WINGMAN_STRATEGY_ROADMAP.md`.

---

## Current build: key security property

**Non-bypassable privileged execution** is enforced by the **Execution Gateway** (Phase R0):

- Only `execution-gateway` gets Docker socket access in TEST (`wingman/docker-compose.yml`).
- Privileged actions must flow through:
  - `POST /gateway/token` (token minted only after APPROVED/AUTO_APPROVED)
  - `POST /gateway/execute` (execution constrained to token scope)
- Dangerous shell operators are blocked even if present (`&&`, `|`, `;`, redirections, etc.).

Operational validation steps (TEST) are captured in:
- `../03-operations/AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md`

---

## Current build: environments (what matters)

**Base URLs (documented):**
- **PRD**: `http://127.0.0.1:5001`
- **TEST**: `http://127.0.0.1:8101`

**Compose stacks (source of truth):**
- **TEST**: `wingman/docker-compose.yml` (project: `wingman-test`)
- **PRD**: `wingman/docker-compose.prd.yml` (project: `wingman-prd`)

---

## Current build: core components

### API (Flask)

Core endpoints:
- `GET /health`
- `POST /check` (10-point framework presence check + policy checks)
- `POST /log_claim` (claims ledger)
- `POST /verify` (verification)
- `POST /approvals/request` + approval lifecycle endpoints

### Approvals (HITL)

Risk-based flow:
- LOW: auto-approve
- MEDIUM/HIGH: human approval (Telegram + API)

### Verifiers

- **Simple verifier**: filesystem/process checks
- **Enhanced verifier**: optional LLM-backed analysis (implementation-specific)

### Watcher

Watcher exists and is part of the system plan; operational status is tracked in:
- `../00-Strategic/AAA_WINGMAN_STRATEGY_ROADMAP.md`
- `../deployment/AAA_DEPLOYMENT_COMPLETE.md` (what is actually deployed)

---

## Current build: what is deployed where (facts live elsewhere)

This doc deliberately does **not** re-assert “what is currently running” as truth because that changes. The factual record is kept in:

- `../deployment/AAA_DEPLOYMENT_COMPLETE.md` — deployed reality snapshot + deltas
- `../deployment/AAA_PRD_DEPLOYMENT_PLAN.md` — PRD gateway rollout plan (when executed)

---

## Related

- `AAA_WINGMAN_ARCHITECTURE_CURRENT_STATE.md` — overall architecture
- `AAA_WINGMAN_ARCHITECTURE_GAP_NEXT.md` — what comes next / remaining gaps

