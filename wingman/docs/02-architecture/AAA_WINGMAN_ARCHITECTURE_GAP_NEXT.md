# Wingman Architecture — Gap Analysis & What Comes Next
**Version**: 1.0  

**Status**: CURRENT (authoritative for “strategy vs build” and next steps)  
**Last Updated**: 2026-01-17  
**Scope**: DEV / TEST / PRD  

---

## Purpose

This document answers:

- **Where the strategy says we’re going**
- **Where the current build actually is**
- **What is still missing / what comes next** (by environment)

Strategy reference (source):
- `../00-Strategic/AAA_WINGMAN_STRATEGY_ROADMAP.md`

Current build reference (source):
- `AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md`

Deployed reality reference (source):
- `../deployment/AAA_DEPLOYMENT_COMPLETE.md`

---

## Gap framing (no assumptions)

This file does **not** assume runtime state. It uses:

- **Strategy doc claims** (planned/target state)
- **Repo code/compose shape** (what is implementable)
- **Deployment record** (what was deployed at the time it was written)

If you want this doc to assert “what is running now”, we must regenerate that from live checks (outside the scope of static docs).

---

## What comes next (high level)

### Cross-environment priorities (DEV/TEST/PRD)

- **Close remaining enforcement gaps**: ensure no privileged operations are possible outside the gateway path.
- **Operationalize watcher**: dedupe, persistence, severity, and actions (notify/quarantine/rollback) aligned to roadmap.
- **Hardening**: non-root containers, minimal toolchains, strict secret handling.

### PRD-specific next steps

- **Execution Gateway rollout to PRD**:
  - Plan: `../deployment/AAA_PRD_DEPLOYMENT_PLAN.md`
  - Testing: `../deployment/AAA_PRD_DEPLOYMENT_TEST_PLAN.md` + `../deployment/AAA_PRD_DEPLOYMENT_TEST_PLAN_COMPLETE.md`

### TEST-specific next steps

- Continue to treat TEST as the enforcement proving ground:
  - Runbook: `../03-operations/AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md`
  - Test evidence: `../TEST_EXECUTION_RESULTS.md` and `../TEST_0A2_MITIGATION_COMPLETE.md`

### DEV-specific next steps

- Keep DEV focused on fast iteration while keeping the enforcement constraints compatible with TEST/PRD.

---

## Related legacy / archive context (intel-system origin)

Wingman originated under an intel-system repo lineage. In this workspace, legacy materials exist under:

- `/Volumes/Data/ai_projects/wingman-system/migration_from_intel-system/` (repo snapshot content)
- `../99-archive/` (curated archive inside wingman docs)

Curated concept doc (creation date unknown):
- `../99-archive/concepts/AAA_CONCEPT_PAUL_WINGMAN_COMPLETE_DESIGN_SPEC.md`

