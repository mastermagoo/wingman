## Updating existing guide instead of creating new version
# Wingman Deployment Record (Execution Log)

**Status**: CURRENT  
**Last Updated**: 2026-01-17  
**Version**: 1.0  
**Scope**: Wingman deployment documentation (DEV/TEST/PRD)  

**Purpose:** factual record of what was deployed, when, and why (PRD + TEST).  
**Scope:** infrastructure + endpoints + configuration deltas.  
**Note:** `../00-Strategic/AAA_WINGMAN_STRATEGY_ROADMAP.md` is the master strategy/roadmap; this file is the run log.

---

## ✅ Current Reality Snapshot (as deployed)

### **PRD (Mac Studio)**
- **API external port**: **5001** (moved off 5000 due to macOS service conflict on this host)
- **API internal port**: 8001 (container)
- **Health**: `GET /health` on `http://127.0.0.1:5001/health`
- **Core endpoints**:
  - `POST /check` (Phase 2)
  - `POST /log_claim` (Phase 3)
  - `POST /verify` (Phase 3)
- **Data**:
  - App data mounted to `./data/prd` (host)
  - Audit log stored under PRD data volume (`claims_audit.jsonl`)

### **TEST (Mac Studio)**
- **API external port**: 8101
- **Core endpoints**: same as PRD
- **Audit log path**: stored under TEST `data/` volume

---

## 🔧 Key Fixes Applied (Why they were required)

### **1) PRD port change (5000 → 5001)**
- **Why**: port 5000 on this host responds as `AirTunes/...` (macOS). That prevents Wingman from being reachable.
- **Consequence**: all PRD clients must call Wingman on **5001** (API base URL).

### **2) PRD config hardening (no hardcoding in PRD compose)**
- **Why**: the repo’s security gates reject hardcoded infra values in PRD compose.
- **Change**: `docker-compose.prd.yml` now uses `${VAR}` substitution (with safe defaults) for hosts/ports.
- **Consequence**: PRD deployments are environment-driven; future changes occur via `.env.prd` rather than editing compose.

### **3) Technical Truth verifier bug fix**
- **Why**: the simple verifier incorrectly treated the slash inside `data/...` as an absolute path and produced false `FALSE` verdicts.
- **Change**: file path extraction now distinguishes absolute paths (only at start/after whitespace) vs relative paths.
- **Consequence**: PRD “created file data/…” claims can now correctly verify to `TRUE` when evidence exists.

### **4) Watcher credential handling**
- **Why**: hardcoded tokens are not acceptable in a resellable product.
- **Change**: watcher now reads notification creds from environment variables only.
- **Consequence**: secrets live in `.env` / secret manager, not in git.

---

## 📌 Operational Commands (Reference)

### PRD health
- `curl -s http://127.0.0.1:5001/health`

### TEST health
- `curl -s http://127.0.0.1:8101/health`

---

## 🧾 Notes / Follow-ups
- Phase 4 “Watcher” is implemented in code and wired into PRD compose; production-grade features (dedupe, persistence, severity, actions) are tracked in the roadmap (see `DEPLOYMENT_PLAN.md`).




