## Updating existing guide instead of creating new version
## Wingman 1 vs Wingman 2 — Product Architecture (Vendor-Agnostic)

This document captures the **intended resellable architecture**. It is written as a product spec + technical design, not as a deployment checklist.

---

## 1) Wingman 1 (Verifier Service) — “Truth as a Service”

### **Goal**
Provide a deterministic verification API that answers: **is a claim true, false, or unverifiable** based on evidence.

### **Core Interfaces**
- **HTTP API**
  - `POST /verify` → `{ verdict: TRUE|FALSE|UNVERIFIABLE, evidence, verifier_id, timestamp }`
  - `GET /health`
- **Verifier Plugins (extensible)**
  - `filesystem`: file exists / checksum / size / permissions
  - `process`: process running
  - `http`: endpoint reachable + expected payload
  - `db`: schema/table existence + row counts
  - `docker`: container status / image digest

### **Evidence Model**
Every verification result should carry **evidence**:
- **what** was checked (target)
- **how** it was checked (probe type + command / query)
- **when** (timestamp)
- **where** (environment)
- **outcome** (verdict + confidence)

### **Storage**
- JSONL for dev/simplicity
- DB-backed ledger for productization (append-only, indexed)

---

## 2) Wingman 2 (Governance Layer) — “Secure Autonomy”

Wingman 2 wraps Wingman 1 with gates, policy, audit, approvals, and autonomous response.

### **Target Product Properties**
- **LLM vendor-agnostic**: works with OpenAI, Anthropic, local models, etc.
- **Tool/vendor-agnostic**: can emit actions to different orchestrators (docker, k8s, SSH, CI jobs)
- **Multi-tenant**: tenant isolation, per-tenant policy, per-tenant audit trails
- **Autonomous by default** (with safety): continuous monitoring + remediation

---

## 3) Architecture (Logical Components)

### **A) Policy Engine (Gate 1)**
Validates instruction packets and forbids unsafe work.
- Input: `InstructionPacket` (structured JSON + raw text)
- Output: `approved: bool`, `violations: [...]`, `score`, `required_human_approval: bool`
- Policy-as-code (YAML/JSON rules), versioned and signed

### **B) Claims Ledger (Gate 2)**
All “I did X” claims are written to a ledger.
- Append-only
- Each claim references: `worker_id`, `run_id`, `tenant_id`, `artifact_refs`, `timestamps`

### **C) Verification Orchestrator**
Batch-verifies claims against Wingman 1 and records verdicts.
- `TRUE`: allow
- `UNVERIFIABLE`: quarantine / request human confirmation depending on risk
- `FALSE`: trigger incident response

### **D) Human Approval Layer**
For high-risk actions:
- review queue (Telegram / web UI)
- approve/reject with audit trail

### **E) Watcher / Incident Response (Phase 4+)**
Monitors ledger and triggers actions:
- alerting (Telegram/webhook)
- auto-quarantine: stop worker, revoke tokens, disable routes
- rollback: revert changes or restore from snapshot

---

## 4) Phases (Implementation Roadmap)

### **Phase 1 — Wingman 1 baseline**
- `/verify` + evidence model + minimal plugins

### **Phase 2 — Gatekeeper (10-point instruction + policy)**
- structured instruction packets
- policy-as-code rules

### **Phase 3 — Technical Truth**
- claims ledger + audit processor
- hard gates: block on FALSE, quarantine on UNVERIFIABLE (configurable)

### **Phase 4 — Autonomous Watcher**
Product-grade version (not a demo):
- de-dupe + rate limiting
- persistent cursor offsets
- severity classification
- action plugins (notify / stop / rollback / quarantine)

### **Phase 5 — UI + Multi-tenant**
- tenant partitioning
- dashboards / KPIs / drift monitoring

### **Phase 6 — Vendor-agnostic Agent SDK**
- SDK wrappers for “any” LLM runner
- unified tool execution interface + tracing




