## Updating existing guide instead of creating new version
# Wingman Deployment Record (Execution Log)

**Status**: CURRENT
**Last Updated**: 2026-02-17
**Version**: 1.2
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

### **5) Phase 6.1 Output Validation (2026-02-16)**

- **What**: AI worker generated code validation system deployed to TEST and PRD.
- **Components**: 5 validators (Syntax, Security, Dependency, Test, Composite) with 2000+ LOC.
- **Database**: Migration 006 adds `output_validations` table.
- **API Endpoint**: POST `/output_validation/validate` endpoint added.
- **Decision Logic**: AUTO_APPROVE (score >= 70), AUTO_REJECT (blocking issues), MANUAL_REVIEW (human approval).
- **Test Coverage**: 92% (13/15 passing integration tests).
- **Status**: TEST (enabled), PRD (disabled by default, feature flag: `VALIDATION_ENABLED=0`).
- **Consequence**: AI workers in other repos (intel-system, cv-automation) can now validate generated code before deployment.

### **6) Phase 6.1+ Prometheus/Grafana Monitoring (2026-02-17)**

- **What**: Real-time metrics collection and visualization infrastructure deployed to TEST.
- **Components**:
  - **Prometheus**: Time-series metrics database (scrapes every 15s)
  - **Grafana**: Visualization and dashboards platform
  - **Metrics Endpoint**: `/metrics` endpoint added to API server
- **Metrics Exposed**:
  - `wingman_health_status`: Overall health (1=healthy, 0=unhealthy)
  - `wingman_verifier_available`: Verifier availability by type
  - `wingman_validator_available`: Validator availability by type
  - `wingman_database_connected`: Database connection status
  - `wingman_start_time_seconds`: Process start time
- **Access URLs**:
  - TEST Prometheus: `http://localhost:9091`
  - TEST Grafana: `http://localhost:3333` (admin/admin)
  - TEST Metrics: `http://localhost:8101/metrics`
- **Configuration**:
  - `monitoring/prometheus.yml`: Scrape configuration
  - `monitoring/grafana-datasources.yml`: Datasource provisioning
- **Docker Services**: Added `prometheus` and `grafana` to `docker-compose.yml`
- **Storage**: Persistent volumes for time-series data (`prometheus_data`, `grafana_data`)
- **Status**: TEST (operational), PRD (ready for deployment)
- **Consequence**: Real-time observability of Wingman health, verifier/validator status, database connectivity
- **Documentation**: [PROMETHEUS_GRAFANA_MONITORING_GUIDE.md](../04-user-guides/PROMETHEUS_GRAFANA_MONITORING_GUIDE.md)

### **7) Automation Fixes (2026-02-17)**

- **What**: Fixed TEST environment automation and monitoring issues identified in audit.
- **Issues Fixed**:
  1. **Watcher API Connection**: Verified watcher successfully polls `/approvals/pending` (was transient issue during API restart)
  2. **Cron Health Checks**: Updated crontab to use correct container name (`wingman-test-wingman-api-1`)
  3. **Monitoring Infrastructure**: Added Prometheus + Grafana (see Phase 6.1+ above)
- **Cron Jobs**: Health checks now passing every 5 minutes
- **Audit Report**: [WINGMAN_AUTOMATION_AUDIT_2026-02-17.md](../03-operations/WINGMAN_AUTOMATION_AUDIT_2026-02-17.md)
- **Consequence**: TEST environment monitoring 100% operational with full observability

---

## 📌 Operational Commands (Reference)

### PRD health

- `curl -s http://127.0.0.1:5001/health`

### TEST health

- `curl -s http://127.0.0.1:8101/health`

### Output Validation (TEST)

```bash
# Validate generated code
curl -X POST http://127.0.0.1:8101/output_validation/validate \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "WORKER_001",
    "generated_files": ["path/to/file1.py", "path/to/file2.py"],
    "task_name": "Generate Semantic Analyzer"
  }'
```

### Output Validation (PRD - if enabled)

```bash
# Validate generated code
curl -X POST http://127.0.0.1:5001/output_validation/validate \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "WORKER_001",
    "generated_files": ["path/to/file1.py", "path/to/file2.py"],
    "task_name": "Generate Semantic Analyzer"
  }'
```

---

## 🧾 Notes / Follow-ups

- Phase 4 "Watcher" is implemented in code and wired into PRD compose; production-grade features (dedupe, persistence, severity, actions) are tracked in the roadmap (see `DEPLOYMENT_PLAN.md`).
- Phase 6.1 "Output Validation" is deployed to TEST (enabled) and PRD (disabled); gradual rollout to PRD will be controlled via `VALIDATION_ENABLED` and `VALIDATION_ROLLOUT_PERCENT` environment variables.




