# Repository Structure Organization

**Date**: 2026-01-15  
**Purpose**: Document the organized structure of the wingman repository

---

## Document Control (Mandatory)

**Rule**: Any doc that is “authoritative / current” must be named `AAA_*` and must contain doc-control metadata (Doc-ID, Version, Status, Last Updated, Scope, Change Log).

See: `docs/00-Strategic/AAA_DOCUMENT_CONTROL_STANDARD.md`

---

## Root Directory (Minimal)

The root directory now contains only essential files:

### Core Documentation
- `README.md` - Main repository README
- `CLAUDE.md` - Core instructions for AI agents
- `QUICK_START.md` - Quick start guide

### Core Python Modules
- Core system modules (api_server.py, telegram_bot.py, etc.)
- These are the main entry points and should remain in root

---

## Organized Directories

### `ai-workers/docs/`
All AI workers documentation organized by category:

```
ai-workers/docs/
├── analysis/          ← Root cause, lessons learned, cost analysis
├── execution/        ← Execution strategies, status reports
├── planning/         ← Checklists, readiness checks
├── fixes/            ← Fix documentation
└── standards/        ← Documentation standards
```

### `docs/deployment/`
Deployment-related documentation:

```
docs/deployment/
├── README.md
├── AAA_DEPLOYMENT_COMPLETE.md
├── AAA_PRD_DEPLOYMENT_PLAN.md
├── AAA_PRD_DEPLOYMENT_TEST_PLAN.md
├── AAA_PRD_DEPLOYMENT_TEST_PLAN_COMPLETE.md
├── AAA_EXECUTION_GATEWAY_DEPLOYMENT.md
├── AAA_VALIDATION_ENHANCEMENT_DEPLOYMENT_PLAN.md
├── AAA_WINGMAN_SSD_DEPLOYMENT_PLAN.md
├── AAA_WINGMAN_SSD_FRESH_DEPLOYMENT.md
└── AAA_WINGMAN_SSD_ACTIVATION_PLAN.md
```

### `scripts/standalone/`
Standalone utility scripts:

```
scripts/standalone/
├── deploy.sh
├── deploy-secure-production.sh
├── backup_wingman_db.sh
├── proper_wingman_deployment.py
└── dev_e2e_phase4.py
```

---

## Benefits

1. **Clear Organization**: Related files grouped together
2. **Minimal Root**: Only essential files in root directory
3. **Easy Navigation**: Clear folder structure with READMEs
4. **Maintainability**: Easy to find and update documentation

---

**Last Updated**: 2026-01-15
