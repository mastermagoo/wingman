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

