# Wingman Architecture

> **Version**: 3.0 (Phase 4 Active)  
> **Last Updated**: January 2026  
> **Status**: Production (PRD on Mac Studio)

---

## Executive Summary

Wingman is an **AI Governance System** that verifies AI worker claims and enforces security policies. It answers one critical question: **"Did the AI actually do what it claimed?"**

### Core Value Proposition

| Problem | Wingman Solution |
|---------|------------------|
| AI claims "I created backup.tar" | Wingman verifies the file actually exists |
| AI runs risky operations unsupervised | Wingman blocks until human approves |
| No audit trail of AI actions | Wingman logs every claim to immutable ledger |
| Instructions missing safety metadata | Wingman rejects incomplete instructions |

---

## Current State (January 2026)

### Production Status

```
┌─────────────────────────────────────────────────────────────────┐
│                    WINGMAN SYSTEM STATUS                        │
├─────────────────────────────────────────────────────────────────┤
│  Phase 1: Base Infrastructure      ████████████████████  ✅     │
│  Phase 2: Instruction Gate         ████████████████████  ✅     │
│  Phase 3: Technical Truth          ████████████████████  ✅     │
│  Phase 4: Human Approval (HITL)    ████████████████████  ✅     │
│  Phase 5: Hardening & Multi-tenant ████░░░░░░░░░░░░░░░░  🚧     │
└─────────────────────────────────────────────────────────────────┘
```

### Environment Matrix

| Environment | Host | API Port | Purpose | Status |
|-------------|------|----------|---------|--------|
| **DEV** | MacBook Pro | 8002 | Development | ✅ Phase 3 |
| **TEST** | Mac Studio | 8101 | Validation | ✅ Phase 4 |
| **PRD** | Mac Studio | 5001 | Production | ✅ Phase 4 |

### Active Components (PRD)

| Component | Container | Port | Status |
|-----------|-----------|------|--------|
| Wingman API | `wingman-api-prd` | 5001 (ext) / 8001 (int) | ✅ Healthy |
| PostgreSQL | `wingman-postgres-prd` | 5434 | ✅ Healthy |
| Redis | `wingman-redis-prd` | 6380 | ✅ Healthy |
| Telegram Bot | `wingman-telegram-prd` | N/A | ✅ Running |
| Watcher | `wingman-watcher-prd` | N/A | 🚧 Deploying |

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SERVICES                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Intel System │  │    Mem0      │  │CV Automation │  │  Any AI      │    │
│  │              │  │              │  │              │  │  Worker      │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼─────────────────┼─────────────────┼─────────────────┼────────────┘
          │                 │                 │                 │
          └─────────────────┴────────┬────────┴─────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WINGMAN API LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Flask API Server                             │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────────┐   │   │
│  │  │  /check   │ │/log_claim │ │  /verify  │ │    /approvals/*   │   │   │
│  │  │ Phase 2   │ │  Phase 3  │ │  Phase 3  │ │      Phase 4      │   │   │
│  │  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────────┬─────────┘   │   │
│  └────────┼─────────────┼─────────────┼─────────────────┼─────────────┘   │
└───────────┼─────────────┼─────────────┼─────────────────┼─────────────────┘
            │             │             │                 │
            ▼             ▼             ▼                 ▼
┌───────────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────────┐
│   Instruction     │ │   Claims   │ │ Verifiers  │ │    Approval Store      │
│   Validator       │ │   Ledger   │ │            │ │                        │
│ (10-point check)  │ │  (JSONL)   │ │ ┌────────┐ │ │  ┌─────────────────┐  │
│                   │ │            │ │ │ Simple │ │ │  │   SQLite DB     │  │
│ ┌───────────────┐ │ │            │ │ └────────┘ │ │  │ (approvals.db)  │  │
│ │ Policy Engine │ │ │            │ │ ┌────────┐ │ │  └─────────────────┘  │
│ └───────────────┘ │ │            │ │ │Enhanced│ │ │                        │
└───────────────────┘ └────────────┘ │ │(Ollama)│ │ └───────────┬────────────┘
                                     │ └────────┘ │             │
                                     └────────────┘             ▼
                                                    ┌────────────────────────┐
                                                    │    Telegram Bot        │
                                                    │  (Human Interface)     │
                                                    │                        │
                                                    │  /pending /approve     │
                                                    │  /reject  /status      │
                                                    └────────────────────────┘
```

### Data Flow

```
1. INSTRUCTION VALIDATION (Phase 2)
   ┌──────────┐     ┌─────────┐     ┌───────────────┐     ┌──────────┐
   │ AI Worker├────►│ /check  ├────►│ 10-Point      ├────►│ APPROVED │
   │          │     │         │     │ Validator     │     │   or     │
   │          │     │         │     │ + Policy      │     │ REJECTED │
   └──────────┘     └─────────┘     └───────────────┘     └──────────┘

2. CLAIMS LOGGING (Phase 3)
   ┌──────────┐     ┌───────────┐     ┌──────────────────────────────┐
   │ AI Worker├────►│/log_claim ├────►│ claims_audit.jsonl (append)  │
   │ "I did X"│     │           │     └──────────────────────────────┘
   └──────────┘     └───────────┘

3. VERIFICATION (Phase 3)
   ┌──────────┐     ┌─────────┐     ┌───────────┐     ┌───────────────┐
   │ Claim    ├────►│ /verify ├────►│ Verifier  ├────►│ TRUE/FALSE/   │
   │ "File X" │     │         │     │ (fs/proc) │     │ UNVERIFIABLE  │
   └──────────┘     └─────────┘     └───────────┘     └───────────────┘

4. APPROVAL FLOW (Phase 4)
   ┌──────────┐     ┌───────────────┐     ┌───────────┐     ┌──────────┐
   │ AI Worker├────►│/approvals/    ├────►│ Risk      ├──┬─►│AUTO-     │
   │          │     │request        │     │ Assessor  │  │  │APPROVED  │
   └──────────┘     └───────────────┘     └───────────┘  │  └──────────┘
                                                         │
                                          (HIGH RISK)    │
                                                         ▼
   ┌──────────┐     ┌───────────────┐     ┌───────────┐
   │  Human   │◄────│ Telegram Bot  │◄────│ PENDING   │
   │  (Mark)  │     │               │     │           │
   └────┬─────┘     └───────────────┘     └───────────┘
        │
        │ /approve or /reject
        ▼
   ┌──────────┐
   │ APPROVED │
   │    or    │
   │ REJECTED │
   └──────────┘
```

---

## Phase Architecture Detail

### Phase 1: Base Infrastructure ✅

**Purpose**: Dockerized, isolated, production-ready infrastructure

**Components**:
- Flask API server (`api_server.py`)
- PostgreSQL database (verification logs, analytics)
- Redis (caching, rate limiting)
- Docker Compose orchestration

**Key Files**:
- `docker-compose.yml` (TEST)
- `docker-compose.prd.yml` (PRD)
- `Dockerfile.api`

### Phase 2: Instruction Gate (Gatekeeper) ✅

**Purpose**: Block work that doesn't meet security standards

**Endpoint**: `POST /check`

**10-Point Framework**:
Every instruction must include:

| # | Section | Purpose |
|---|---------|---------|
| 1 | DELIVERABLES | What will be produced |
| 2 | SUCCESS_CRITERIA | How to know it worked |
| 3 | BOUNDARIES | What NOT to do |
| 4 | DEPENDENCIES | What's needed first |
| 5 | MITIGATION | What if it fails |
| 6 | TEST_PROCESS | How to verify |
| 7 | TEST_RESULTS_FORMAT | Expected output format |
| 8 | RESOURCE_REQUIREMENTS | Compute/storage needs |
| 9 | RISK_ASSESSMENT | Risk level and type |
| 10 | QUALITY_METRICS | Success measurement |

**Policy Checks**:
- No `--force` flags
- No hardcoded secrets/tokens
- No dangerous commands (`rm -rf /`, etc.)

**Key Files**:
- `instruction_validator.py`

### Phase 3: Technical Truth (Logger & Auditor) ✅

**Purpose**: Record and verify all AI claims

**Endpoints**:
- `POST /log_claim` — Record a claim
- `POST /verify` — Verify a claim

**Claims Ledger**:
- Append-only JSONL file (`claims_audit.jsonl`)
- Each entry: `{timestamp, worker_id, claim, status}`

**Verifiers**:

| Verifier | Speed | Capability |
|----------|-------|------------|
| Simple (`simple_verifier.py`) | Fast | File existence, process status |
| Enhanced (`enhanced_verifier.py`) | Slower | LLM-powered analysis (Ollama/Mistral) |

**Verdicts**:
- `TRUE` — Evidence confirms claim
- `FALSE` — Evidence contradicts claim
- `UNVERIFIABLE` — Cannot determine

**Key Files**:
- `simple_verifier.py`
- `enhanced_verifier.py`
- `wingman_audit_processor.py`

### Phase 4: Human Approval (HITL) ✅

**Purpose**: Require human sign-off for high-risk operations

**Endpoints**:
- `POST /approvals/request` — Request approval
- `GET /approvals/pending` — List pending
- `GET /approvals/<id>` — Get status
- `POST /approvals/<id>/approve` — Approve
- `POST /approvals/<id>/reject` — Reject

**Risk Assessment**:

| Risk Level | Trigger | Action |
|------------|---------|--------|
| LOW | No risky keywords | Auto-approve |
| MEDIUM | Deploy, migration, schema | Require approval |
| HIGH | Production, delete, secrets, --force | Require approval |
| HIGH | `DEPLOYMENT_ENV=prd` | Always require approval |

**Human Interface**:
- Telegram Bot with `/pending`, `/approve`, `/reject` commands
- API can also be used directly

**Key Files**:
- `approval_store.py`
- `telegram_bot.py`
- `bot_api_client.py`

### Phase 5: Hardening & Multi-tenant 🚧

**Purpose**: Production hardening and multi-organization support

**Planned Features**:
- Remove dev tools from containers (curl, pip)
- Non-root container users
- Tenant isolation (per-org policies, audit trails)
- Rate limiting per tenant
- Dashboard UI

**Status**: Design phase

---

## Security Architecture

### Three-Layer Protection

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Physical/Filesystem                                   │
│  • Secrets in .env files (never committed)                      │
│  • Volumes isolated per environment                             │
│  • localhost-bound ports (127.0.0.1)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: Container/Network                                     │
│  • Isolated Docker networks per stack                           │
│  • No direct database exposure                                  │
│  • Inter-container communication only                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: Application                                           │
│  • 10-point instruction validation                              │
│  • Policy enforcement (no --force, no secrets)                  │
│  • Human approval for PRD operations                            │
│  • Immutable audit log                                          │
└─────────────────────────────────────────────────────────────────┘
```

### Secrets Management

| Secret Type | Storage | Access |
|-------------|---------|--------|
| Database credentials | `.env.prd` | Container env vars |
| Telegram bot token | `.env.prd` | Container env vars |
| Approval API keys | `.env.prd` | HTTP headers |

**Rules**:
- Never commit `.env*` files
- Never hardcode secrets in code
- Never print secrets in logs

---

## Deployment Architecture

### Docker Compose Stack (PRD)

```yaml
# Simplified view of docker-compose.prd.yml
services:
  api:
    build: Dockerfile.api
    ports: ["5001:8001"]
    depends_on: [postgres, redis]
    
  postgres:
    image: postgres:15
    volumes: [postgres_data_prd:/var/lib/postgresql/data]
    
  redis:
    image: redis:7-alpine
    
  telegram-bot:
    build: Dockerfile.bot
    depends_on: [api]

networks:
  wingman-network-prd:
    driver: bridge
```

### Port Allocation

| Environment | API | PostgreSQL | Redis |
|-------------|-----|------------|-------|
| DEV | 8002 | 5432 | 6379 |
| TEST | 8101 | 5433 | 6379 |
| PRD | 5001 | 5434 | 6380 |

---

## Roadmap

### Near-Term (Q1 2026)

| Priority | Item | Status |
|----------|------|--------|
| P1 | Phase 4 Watcher service (auto-alert on FALSE) | 🚧 In Progress |
| P1 | Deduplication for approval requests | ✅ Done |
| P2 | Persistent cursor for audit log tailing | 📋 Planned |
| P2 | Severity classification for alerts | 📋 Planned |

### Mid-Term (Q2 2026)

| Priority | Item | Status |
|----------|------|--------|
| P1 | Phase 5: Container hardening | 📋 Planned |
| P1 | Web dashboard for approvals | 📋 Planned |
| P2 | Multi-tenant support | 📋 Planned |
| P2 | Webhook integrations (Slack, etc.) | 📋 Planned |

### Long-Term (H2 2026)

| Priority | Item | Status |
|----------|------|--------|
| P2 | Vendor-agnostic Agent SDK | 📋 Planned |
| P2 | Kubernetes deployment option | 📋 Planned |
| P3 | SaaS offering | 📋 Concept |

---

## Product Vision

### Wingman 1 vs Wingman 2

| Aspect | Wingman 1 | Wingman 2 |
|--------|-----------|-----------|
| Focus | Verification API | Governance Layer |
| Core | `/verify` endpoint | Policy + Approvals + Audit |
| Verdict | TRUE/FALSE/UNVERIFIABLE | + Actions (alert, block, rollback) |
| User | Developers | Organizations |
| Deployment | Single service | Multi-tenant SaaS |

### Target Properties (Wingman 2)

- **LLM vendor-agnostic**: Works with any AI model
- **Tool/vendor-agnostic**: Integrates with any orchestrator
- **Multi-tenant**: Per-org isolation and policies
- **Autonomous by default**: Continuous monitoring + remediation

---

## File Reference

### Core Application

| File | Purpose |
|------|---------|
| `api_server.py` | Flask API server (all endpoints) |
| `simple_verifier.py` | Fast filesystem/process verification |
| `enhanced_verifier.py` | LLM-powered verification (Ollama) |
| `instruction_validator.py` | 10-point framework checker |
| `approval_store.py` | Approval request persistence |
| `telegram_bot.py` | Human interface bot |
| `bot_api_client.py` | API client for bot |
| `intel_integration.py` | Database integration layer |

### Infrastructure

| File | Purpose |
|------|---------|
| `docker-compose.yml` | TEST stack |
| `docker-compose.prd.yml` | PRD stack |
| `Dockerfile.api` | API container |
| `Dockerfile.bot` | Bot container |
| `env.prd.example` | PRD configuration template |

### Documentation

| File | Purpose |
|------|---------|
| `docs/01-how-to-use/` | Integration guides |
| `docs/02-architecture/` | This document |
| `docs/03-operations/` | Operational runbooks |
| `DEPLOYMENT_PLAN.md` | Master deployment roadmap |
| `CLAUDE.md` | AI agent instructions |

---

## See Also

- [How to Use Wingman](../01-how-to-use/README.md) — Integration guide
- [Operations Guide](../03-operations/README.md) — Day-to-day operations
- [API Reference](../05-api-reference/README.md) — Endpoint documentation
- [DEPLOYMENT_PLAN.md](../../DEPLOYMENT_PLAN.md) — Detailed phase status
