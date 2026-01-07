# Wingman Documentation

> **Wingman**: AI Governance System — Verify AI claims, enforce policies, require human approval.

---

## Quick Links

| I want to... | Go to... |
|--------------|----------|
| Integrate my service with Wingman | [How to Use](./01-how-to-use/README.md) |
| Understand how Wingman works | [Architecture](./02-architecture/README.md) |
| Run/troubleshoot Wingman | [Operations](./03-operations/README.md) |
| Look up an API endpoint | [API Reference](./05-api-reference/README.md) |

---

## Documentation Structure

```
docs/
├── README.md                    ← You are here
│
├── 01-how-to-use/               ← Integration guides
│   ├── README.md                   Main guide + patterns
│   ├── intel-system.md             Intel System integration
│   ├── mem0.md                     Mem0 integration
│   ├── cv-automation.md            CV Automation integration
│   └── wingman_client.py           Reusable Python client
│
├── 02-architecture/             ← System design
│   └── README.md                   Current state, components, roadmap
│
├── 03-operations/               ← Running Wingman
│   └── README.md                   Start/stop, logs, troubleshooting
│
├── 05-api-reference/            ← API documentation
│   └── README.md                   All endpoints, request/response
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

1. Read [Operations](./03-operations/README.md) for day-to-day commands
2. Check [Architecture](./02-architecture/README.md) for system overview
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
| `DEPLOYMENT_PLAN.md` | Master deployment roadmap |
| `DEPLOYMENT_COMPLETE.md` | Execution log |
| `QUICK_START.md` | Quick deployment reference |
| `README.md` (root) | Project overview |

---

## Legacy Documentation

Original documentation from the intel-system migration is archived in [99-archive/paul-wingman/](./99-archive/paul-wingman/). This includes:

- Original product vision documents
- Build logs and phase plans
- Assessment and gap analysis documents

These are kept for historical reference but may contain outdated paths and configurations.
