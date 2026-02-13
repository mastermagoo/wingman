# Non-Orchestrator Build — Documentation Plan
**Status**: CURRENT  
**Last Updated**: 2026-02-13  
**Version**: 1.0  
**Scope**: DEV / TEST / PRD  

---

## Purpose

This document defines the **non-orchestrator build** (agent and scripts do not run destructive docker; only the Execution Gateway does) and lists the **documentation changes** required so all authoritative docs reflect and support this build. No bypass: one path for privileged execution (approval → gateway with capability token), with the docker wrapper enforcing that path everywhere else.

---

## Non-Orchestrator Build (definition)

**Target state:**

- **Agents (e.g. Cursor)** do not orchestrate destructive docker/compose. They request approval, then execution is performed via the Execution Gateway with a capability token.
- **Scripts, cron, Makefiles, docs** do not invoke the real docker binary for destructive operations. All docker/compose invocations go through a path that uses `tools/docker-wrapper.sh` (or equivalent logic): either PATH has `wingman/tools` first so `docker` resolves to the wrapper, or scripts explicitly call the wrapper.
- **Execution Gateway** is the only component that runs destructive docker (gateway has real docker in its environment; tokens are minted only after APPROVED/AUTO_APPROVED).

**Three layers (unchanged):**

1. **Infrastructure (wrapper everywhere):** Wrapper blocks destructive commands unless run via gateway with token. No “optional” wrapper: every invocation path (shell, script, cron, doc copy-paste) uses the wrapper.
2. **Application (CLAUDE.md):** Approval required for destructive ops; agents must follow rules.
3. **Execution (gateway):** Only gateway has docker socket; commands require capability tokens.

---

## Sources / References

- `wingman/CLAUDE.md` — Use the docker wrapper everywhere (mandatory)
- `wingman/docs/00-Strategic/AAA_WINGMAN_STRATEGY_ROADMAP.md` — Master strategy
- `wingman/docs/02-architecture/AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md` — Current build design
- `wingman/docs/02-architecture/AAA_WINGMAN_ARCHITECTURE_GAP_NEXT.md` — Gap and next steps
- `wingman/docs/TEST_0A2_MITIGATION_COMPLETE.md` — Wrapper as Layer 1
- `wingman/docs/00-Strategic/AAA_DOCUMENT_CONTROL_STANDARD.md` — Doc control rules

---

## Documentation Plan (file-by-file)

### 1. `docs/02-architecture/AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md`

**Updates:**

- Add a subsection under “Current build: key security property” describing **wrapper-everywhere** and **non-orchestrator**:
  - All docker/compose use (scripts, cron, agent shells) must go through `tools/docker-wrapper.sh` (e.g. PATH with `wingman/tools` first; shim `tools/docker`).
  - Optional: `DOCKER_BIN` for real docker when wrapper’s fallback search is insufficient.
  - Only the Execution Gateway runs destructive docker; agents and scripts do not (non-orchestrator build).
- Add a one-line reference to this plan: `../00-Strategic/AAA_NON_ORCHESTRATOR_BUILD_DOCUMENTATION_PLAN.md`.

### 2. `docs/02-architecture/AAA_WINGMAN_ARCHITECTURE_GAP_NEXT.md`

**Updates:**

- Under “Close remaining enforcement gaps”, add an explicit bullet:
  - **Wrapper everywhere**: Ensure every docker/compose invocation path (scripts, cron, runbooks, IDE/copy-paste) uses the wrapper; refactor or remove scripts that call the real docker binary for destructive ops. See `../00-Strategic/AAA_NON_ORCHESTRATOR_BUILD_DOCUMENTATION_PLAN.md`.
- No other structural change required.

### 3. `docs/TEST_0A2_MITIGATION_COMPLETE.md`

**Updates:**

- In “Known limitations”, update the “Wrapper not auto-enabled” / “Direct path bypass” text to state that the **target** is wrapper everywhere (PATH in all environments, scripts refactored), so “optional” is no longer the stance; document any remaining limitation (e.g. legacy cron not yet migrated) as a known gap, not as acceptable.
- In “Next steps”, replace “OPTIONAL: Auto-enable wrapper” with: “Ensure wrapper everywhere per AAA_NON_ORCHESTRATOR_BUILD_DOCUMENTATION_PLAN.md (PATH, script refactors, runbook).”
- Add **Sources / References**: link to `AAA_NON_ORCHESTRATOR_BUILD_DOCUMENTATION_PLAN.md` and `CLAUDE.md` (wrapper section).

### 4. `docs/03-operations/AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md`

**Updates:**

- Add a **Prerequisites / Environment** (or equivalent) section that states: For any step that runs `docker` or `docker compose`, the wrapper must be in effect. Prepend `wingman/tools` to PATH (e.g. `export PATH="/path/to/wingman/tools:$PATH"`). Optionally set `DOCKER_BIN` if the real docker is not in the wrapper’s fallback search paths.
- Ensure every runbook command that runs docker/compose is either (a) under that PATH assumption and documented, or (b) explicitly invokes the wrapper. No direct use of the real docker binary for destructive operations in copy-paste blocks.

### 5. `docs/README.md`

**Updates:**

- Under “Strategy + business” (or a new “Plans” line), add:
  - **Non-orchestrator build (doc plan)**: [AAA_NON_ORCHESTRATOR_BUILD_DOCUMENTATION_PLAN.md](./00-Strategic/AAA_NON_ORCHESTRATOR_BUILD_DOCUMENTATION_PLAN.md)

### 6. Deployment docs (as needed)

- **`docs/deployment/README.md`** (or deployment index): If it lists “how to run docker/compose”, add a note that the non-orchestrator build and wrapper-everywhere policy apply; link to this plan and to CLAUDE.md.
- **`docs/deployment/AAA_PRD_DEPLOYMENT_PLAN.md`** (and similar): When they prescribe docker/compose commands, state that operators must use an environment where the wrapper is in PATH (or call the wrapper); no change to approval flow, which remains mandatory.

---

## Completion checklist

- [ ] AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md updated (wrapper-everywhere + non-orchestrator + link to this plan)
- [ ] AAA_WINGMAN_ARCHITECTURE_GAP_NEXT.md updated (wrapper-everywhere under enforcement gaps)
- [ ] TEST_0A2_MITIGATION_COMPLETE.md updated (target = wrapper everywhere; next steps; references)
- [ ] AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md updated (PATH/prereq; no destructive docker without wrapper)
- [ ] docs/README.md updated (link to this plan)
- [ ] Deployment index/PRD plan updated if they contain docker/compose run instructions

---

**Last Updated:** 2026-02-13  
**Revision:** 1.0
