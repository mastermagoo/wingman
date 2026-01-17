# Wingman Documentation Control Standard (AAA_*)
**Status**: CURRENT (mandatory)  
**Last Updated**: 2026-01-17  
**Version**: 1.0  
**Scope**: Wingman documentation in this repo (`wingman/docs/`)  

---

## Rule: “Authoritative = AAA_*”

If a document is meant to represent the **current, authoritative** position for Wingman, it must:

- Be named `AAA_*.md`
- Live in the correct `wingman/docs/*` folder (strategy, architecture, deployment, etc.)
- Contain **at least**:
  - **Status** (CURRENT / DRAFT / ARCHIVE / SUPERSEDED)
  - **Last Updated** (YYYY-MM-DD) *(or `Date` if that’s all we have; prefer `Last Updated`)*
  - **Scope** (DEV/TEST/PRD as applicable)
  - **Version** (1.0, 1.1, 2.0…)
  - A short **Purpose** paragraph
  - A **“Sources / References”** section pointing to the files it depends on

---

## README.md files are not authoritative

`README.md` files exist only as **indexes/navigation** and must link to the authoritative `AAA_*` docs.

---

## Rule: No timestamps = not authoritative

If a doc has no timestamp or status, it must be treated as:

- **ARCHIVE** (historical) or **DRAFT** (incomplete)

and must be moved/labelled accordingly.

---

## Rule: “Facts vs Targets”

Docs must clearly label:

- **Facts**: “as deployed” / “as implemented” (with source: deployment record, code path, test result)
- **Targets**: business/strategy goals (with success criteria)

---

## Git is the “version control”

Internal `Version`/`Last Updated` makes documents readable. **Git history is the actual version control**.

If an `AAA_*` file shows as untracked (`??`) in `git status`, it is **not yet under version control** until it is added + committed.

---

## Agent Brief: “What’s what” (share this with other agents)

### Canonical location + branch

- **Canonical docs location**: `wingman/docs/`
- **Canonical branch for docs**: `main`
  - Note: the legacy root folder `/Volumes/Data/ai_projects/wingman-system/docs` has been **moved into** `wingman/docs/99-archive/` and the root folder no longer exists in this workspace.

### Where to start (the authoritative map)

#### Strategy / roadmap (DEV/TEST/PRD)

- `wingman/docs/00-Strategic/AAA_WINGMAN_STRATEGY_ROADMAP.md`

#### Business cases

- `wingman/docs/00-Strategic/AAA_WINGMAN_ENFORCEMENT_BUSINESS_CASE.md`
- `wingman/docs/00-Strategic/AAA_VALIDATION_ENHANCEMENT_BUSINESS_CASE.md` *(validation enhancement track)*

#### Architecture (3 docs: current state, current build, gap/next)

- `wingman/docs/02-architecture/AAA_WINGMAN_ARCHITECTURE_CURRENT_STATE.md`
- `wingman/docs/02-architecture/AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md`
- `wingman/docs/02-architecture/AAA_WINGMAN_ARCHITECTURE_GAP_NEXT.md`

#### Operations (runbooks)

- `wingman/docs/03-operations/AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md`

#### Deployments (plans + records)

- Index: `wingman/docs/deployment/README.md`
- Deployment record: `wingman/docs/deployment/AAA_DEPLOYMENT_COMPLETE.md`
- PRD gateway plan: `wingman/docs/deployment/AAA_PRD_DEPLOYMENT_PLAN.md`

#### Legacy / archive (read-only unless explicitly resurrecting)

- `wingman/docs/99-archive/`

### Rules of engagement (so agents don’t create doc chaos)

- **Do not create “new versions” of docs by copying files** (no `*_v2.md`, no `NEW_*.md` duplicates).
- **Update the existing authoritative `AAA_*` doc in-place** and bump:
  - `**Last Updated**`
  - `**Version**`
  - add a short change note (if appropriate)
- **If a doc is concept/legacy**: set `**Status**: ARCHIVE` and keep it under `99-archive/`.

