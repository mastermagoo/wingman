# Wingman Architecture — Current Build Design (DEV/TEST/PRD)
**Version**: 2.0

**Status**: CURRENT (authoritative for "what is implemented now")
**Last Updated**: 2026-02-14
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

Risk-based flow with validation enhancement:
- **AUTO_REJECTED**: Secrets found, dangerous patterns, or validation score < 30
- **AUTO_APPROVED**: LOW risk + validation score >= 90 (operational profile: >=85)
- **MANUAL_REVIEW**: Medium/high risk or validation inconclusive

### Validation Layer (Phase 1-2, Complete 2026-02-14)

**Status**: Deployed to TEST and PRD (PRD: disabled by default, ready for gradual rollout)

**Architecture**: Profile-based validation with 5 validators
- **CompositeValidator**: Orchestrates validation based on detected profile
  - **Operational Profile**: Read-only/low-risk commands (docker logs, status checks)
    - Validators: CodeScanner (60%), SemanticAnalyzer (40%)
    - Auto-approve threshold: 85, Auto-reject threshold: 30
    - Skips ContentQualityValidator (no 10-point framework needed)
  - **Deployment Profile**: Deployments, schema changes, high-risk operations
    - Validators: CodeScanner (30%), ContentQualityValidator (25%), DependencyAnalyzer (20%), SemanticAnalyzer (25%)
    - Auto-approve threshold: 90, Auto-reject threshold: 30
    - Requires full 10-point framework validation

**Validators** (990 LOC total):
1. **CodeScanner** (207 LOC): Pattern-based detection of secrets, dangerous commands, destructive operations
2. **SemanticAnalyzer** (129 LOC): Intent analysis and risk assessment (heuristic-based, no LLM dependency)
3. **DependencyAnalyzer** (138 LOC): Blast radius assessment for cascading failures
4. **ContentQualityValidator** (283 LOC): Evaluates quality of 10-point framework sections
5. **CompositeValidator** (214 LOC): Profile detection and weighted scoring

**Decision Logic**:
- **Auto-Reject Triggers**:
  - Secrets or credentials detected (immediate reject)
  - Any active validator scores below hard floor (30)
  - Overall weighted score below auto-reject threshold (30)
- **Auto-Approve Criteria**:
  - Profile-appropriate validators all score above auto-approve threshold (85-90)
  - Risk level is LOW
  - No secrets or dangerous patterns detected
- **Manual Review**: Everything else (includes full validation report)

**Feature Flags** (environment variables):
- `VALIDATION_ENABLED`: 1=enabled, 0=disabled (default: 1 for TEST, 0 for PRD)
- `VALIDATION_ROLLOUT_PERCENT`: 0-100 (default: 100, allows gradual rollout)

**Profile Detection**: Automatic based on instruction keywords
- Operational: `docker logs`, `docker ps`, `curl health`, `cat`, `tail`, `status check`
- Deployment: `deploy`, `migrate`, `CREATE TABLE`, `restart container`, `docker stop`

**Test Coverage**: 843 LOC comprehensive tests across all validators

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

