# Wingman Documentation

> **Wingman**: AI Governance System — Verify AI claims, enforce policies, require human approval.

---

## Authoritative docs (AAA_*)

**These are the definitive, current docs**. `README.md` files are only indexes/navigation.

### Strategy + business (DEV/TEST/PRD)

- **Business strategy / roadmap (master)**: [AAA_WINGMAN_STRATEGY_ROADMAP.md](./00-Strategic/AAA_WINGMAN_STRATEGY_ROADMAP.md)
- **Business case (enforcement layer)**: [AAA_WINGMAN_ENFORCEMENT_BUSINESS_CASE.md](./00-Strategic/AAA_WINGMAN_ENFORCEMENT_BUSINESS_CASE.md)
- **Non-orchestrator build (doc plan)**: [AAA_NON_ORCHESTRATOR_BUILD_DOCUMENTATION_PLAN.md](./00-Strategic/AAA_NON_ORCHESTRATOR_BUILD_DOCUMENTATION_PLAN.md)

### Architecture (3 docs: current state, current build, gap/next)

- **Current state (overall)**: [AAA_WINGMAN_ARCHITECTURE_CURRENT_STATE.md](./02-architecture/AAA_WINGMAN_ARCHITECTURE_CURRENT_STATE.md)
- **Current build design (what is implemented now)**: [AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md](./02-architecture/AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md)
- **Gap + what comes next (after current deployment)**: [AAA_WINGMAN_ARCHITECTURE_GAP_NEXT.md](./02-architecture/AAA_WINGMAN_ARCHITECTURE_GAP_NEXT.md)

### Deployments & plans

- **Deployment index (previous/current/future)**: [deployment/README.md](./deployment/README.md)
- **Deployment record (what was deployed)**: [AAA_DEPLOYMENT_COMPLETE.md](./deployment/AAA_DEPLOYMENT_COMPLETE.md)
- **PRD plan (Execution Gateway)**: [AAA_PRD_DEPLOYMENT_PLAN.md](./deployment/AAA_PRD_DEPLOYMENT_PLAN.md)

### Document control standard

- **Doc control rules (mandatory for new/edited docs)**: [AAA_DOCUMENT_CONTROL_STANDARD.md](./00-Strategic/AAA_DOCUMENT_CONTROL_STANDARD.md)

---

## Quick Links

| I want to... | Go to... |
|--------------|----------|
| Integrate my service with Wingman | [How to Use](./01-how-to-use/README.md) |
| Understand how Wingman works | [Architecture (Current State)](./02-architecture/AAA_WINGMAN_ARCHITECTURE_CURRENT_STATE.md) |
| Run/troubleshoot Wingman | [Operations Runbook](./03-operations/AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md) |
| Look up an API endpoint | [API Reference](./05-api-reference/README.md) |

---

## Wingman 5 (Phase 5) — Key Docs

These exist today, but were previously buried under the archive folder:

- **System architecture**: [WINGMAN_ARCHITECTURE.md](./99-archive/paul-wingman/WINGMAN_ARCHITECTURE.md)
- **Deployment plan (Phase 5)**: [PHASE_5_SECURE_DEPLOYMENT.md](./99-archive/paul-wingman/PHASE_5_SECURE_DEPLOYMENT.md)

---


## Documentation Structure

```
docs/
├── README.md                    ← You are here
│
├── 00-Strategic/                ← Strategy, roadmap, business case (AAA_*)
│
├── 01-how-to-use/               ← Integration guides
│   ├── README.md                   Main guide + patterns
│   ├── intel-system.md             Intel System integration
│   ├── mem0.md                     Mem0 integration
│   ├── cv-automation.md            CV Automation integration
│   └── wingman_client.py           Reusable Python client
│
├── 02-architecture/             ← System design
│   └── AAA_*.md                    Authoritative architecture docs
│
├── 03-operations/               ← Running Wingman
│   └── AAA_*.md                    Operator runbooks
│
├── 05-api-reference/            ← API documentation
│   └── README.md                   All endpoints, request/response
│
├── deployment/                  ← Deployment plans + deployment records (AAA_*)
│
└── 99-archive/                  ← Legacy documentation
    └── paul-wingman/               Original docs (pre-migration)
```

---

## Getting Started

### For Developers (Integrating with Wingman)

1. Read [How to Use](./01-how-to-use/README.md) for integration patterns
2. Copy [wingman_client.py](./01-how-to-use/wingman_client.py) into your service
3. Configure `WINGMAN_URL` environment variable

### For Operators (Running Wingman)

1. Read [Operations Runbook](./03-operations/AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md) for day-to-day commands
2. Check [Architecture (Current State)](./02-architecture/AAA_WINGMAN_ARCHITECTURE_CURRENT_STATE.md) for system overview
3. See [API Reference](./05-api-reference/README.md) for testing endpoints

---

## API Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check API status |
| `/check` | POST | Validate instruction (10-point framework) |
| `/log_claim` | POST | Record claim to audit trail |
| `/verify` | POST | Verify claim (TRUE/FALSE/UNVERIFIABLE) |
| `/approvals/request` | POST | Request human approval |
| `/approvals/pending` | GET | List pending approvals |
| `/approvals/<id>/approve` | POST | Approve request |
| `/approvals/<id>/reject` | POST | Reject request |

**Base URLs**:
- PRD: `http://127.0.0.1:5001`
- TEST: `http://127.0.0.1:8101`

---

## Key Concepts

### The 5 Phases

| Phase | Name | Status | Purpose |
|-------|------|--------|---------|
| 1 | Base Infrastructure | ✅ Done | Docker, PostgreSQL, Redis |
| 2 | Instruction Gate | ✅ Done | 10-point validation |
| 3 | Technical Truth | ✅ Done | Claims logging + verification |
| 4 | Human Approval | ✅ Done | HITL for high-risk ops |
| 5 | Hardening | 🚧 WIP | Security hardening, multi-tenant |

### Verdicts

| Verdict | Meaning |
|---------|---------|
| `TRUE` | Claim verified against reality |
| `FALSE` | Claim contradicted by evidence |
| `UNVERIFIABLE` | Cannot determine |

### Risk Levels

| Level | Action | Example Triggers |
|-------|--------|------------------|
| LOW | Auto-approved | No risky keywords |
| MEDIUM | Requires approval | migration, deploy, schema |
| HIGH | Requires approval | production, delete, --force, PRD env |

---

## Related Files (Outside docs/)

| File | Purpose |
|------|---------|
| `CLAUDE.md` | AI agent instructions |
| `docs/00-Strategic/AAA_WINGMAN_STRATEGY_ROADMAP.md` | Master strategy/roadmap (DEV/TEST/PRD) |
| `docs/deployment/AAA_DEPLOYMENT_COMPLETE.md` | Deployment record (what was deployed) |
| `QUICK_START.md` | Quick deployment reference |
| `README.md` (root) | Project overview |

---

## Legacy Documentation

Original documentation from the intel-system migration is archived in [99-archive/paul-wingman/](./99-archive/paul-wingman/). This includes:

- Original product vision documents
- Build logs and phase plans
- Assessment and gap analysis documents

These are kept for historical reference but may contain outdated paths and configurations.
