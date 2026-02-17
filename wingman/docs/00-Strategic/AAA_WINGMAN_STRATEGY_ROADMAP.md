# Wingman Strategic Deployment Plan: Secure Worker Pipeline

**Status**: CURRENT
**Last Updated**: 2026-02-17
**Version**: 1.2
**Scope**: Wingman strategy/business documentation (DEV/TEST/PRD)  

> **MASTER STRATEGY DOCUMENT**  
> *This document supercedes all previous Wingman 2 phased plans and deployment summaries.*

**Date:** 2026-02-17
**Status:** ✅ PHASE 5 COMPLETE | 🚀 PHASE 6.1 DEPLOYED | ✅ PHASE 6.2 OPERATIONAL
**Purpose:** Implementation and enforcement of the Secure AI Worker Pipeline with Output Validation and Observability across DEV, TEST, and PRD.

---

## 🎯 OBJECTIVE

Transform Wingman from a simple API into a **Hardened Security Layer** that governs all AI worker activity. This plan enforces:
1.  **Gatekeeping**: No instruction is executed without a 10-point metadata check.
2.  **Technical Truth**: Every worker action is logged and physically audited.
3.  **Autonomous Response**: The system automatically flags and reacts to security violations.

---

## 🏗️ INFRASTRUCTURE & ENVIRONMENT

### **Environment Architecture**

| Environment | Host | Purpose | Port | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DEV** | MBP | Development & Prototyping | 8002 | ✅ Phase 3 Complete |
| **TEST** | Mac Studio | High-Fidelity Validation | 8101 | ✅ Phase 3 Complete |
| **PRD** | Mac Studio | Live Secure Operations | **5001** | 🚀 Phase 4 Active |

*Note: PRD Port moved from 5000 to 5001 to resolve macOS AirPlay Receiver conflict.*

---

## 📊 THE 5-PHASE SECURE PIPELINE

### **Phase 1: Base Integration** ✅
*   **Infrastructure**: Dockerized Postgres, Redis, and Flask API.
*   **Integrity**: Established separate networks (`wingman-network-prd`) and isolated volumes (`postgres_data_prd`).

### **Phase 2: The Gatekeeper (Instruction Validation)** ✅
*   **10-Point Framework**: Strictly enforces the presence of metadata (Deliverables, Mitigation, Risk, etc.).
*   **Policy Enforcement**: Rejects instructions containing forbidden actions (e.g., `--force`) or hardcoded secrets.
*   **Status**: Active on all environments (`/check` endpoint).

### **Phase 3: Technical Truth (Logger & Auditor)** ✅
*   **Logger**: Every worker claim is recorded in `claims_audit.jsonl` via the `/log_claim` endpoint.
*   **Auditor**: A background processor (`wingman_audit_processor.py`) that verifies claims against reality (filesystem checks, process checks).
*   **Status**: Active on all environments (`/verify` endpoint).

### **Phase 4: The Watcher (Autonomous Monitoring)** ✅ *(COMPLETE)*

*   **Monitoring**: Real-time tailing of audit logs.
*   **Detection**: Immediate identification of `FALSE` verdicts (claims caught as lies).
*   **Response**: Automatic Telegram alerts to Mark and autonomous worker lockdown.
*   **Status**: Deployed to TEST and PRD.

### **Phase 5: Docker Wrapper Enforcement** ✅ *(COMPLETE)*

*   **Infrastructure Protection**: Shell-level wrapper blocks destructive docker commands.
*   **Approval Integration**: All destructive operations require Wingman approval.
*   **Audit Trail**: All docker operations logged in execution audit table.
*   **Status**: Deployed to TEST and PRD (2026-01-17).

### **Phase 6.1: Output Validation** ✅ *(DEPLOYED 2026-02-16)*

*   **Code Quality**: 5 validators (Syntax, Security, Dependency, Test, Composite) analyze AI-generated code before deployment.
*   **Decision Logic**: AUTO_APPROVE (score >= 70), AUTO_REJECT (blocking issues), MANUAL_REVIEW (needs human approval).
*   **Integration**: POST `/output_validation/validate` endpoint deployed to TEST and PRD.
*   **Code Size**: 2000+ LOC with 92% test coverage (13/15 passing tests).
*   **Database**: Migration 006 adds `output_validations` table.
*   **Status**: Deployed to TEST (enabled), PRD (disabled by default, ready for rollout).

### **Phase 6.2: Monitoring & Observability** ✅ *(OPERATIONAL 2026-02-17)*

*   **Prometheus Integration**: Time-series metrics collection and storage (scrapes API every 15s).
*   **Grafana Dashboards**: Real-time visualization of Wingman health, verifier/validator status, database connectivity.
*   **Metrics Endpoint**: `/metrics` endpoint added to API server (Prometheus-compatible format).
*   **Metrics Exposed**:
    *   `wingman_health_status`: Overall API health (1=healthy, 0=unhealthy)
    *   `wingman_verifier_available`: Verifier availability by type (simple, enhanced)
    *   `wingman_validator_available`: Validator availability by type (input, output)
    *   `wingman_database_connected`: Database connection status (1=connected, 0=disconnected)
    *   `wingman_start_time_seconds`: Process start timestamp for uptime calculation
*   **Access URLs**:
    *   TEST Prometheus: `http://localhost:9091`
    *   TEST Grafana: `http://localhost:3333` (admin/admin)
    *   PRD Prometheus: `http://localhost:9092` (when deployed)
    *   PRD Grafana: `http://localhost:3334` (when deployed)
*   **Configuration**:
    *   `monitoring/prometheus.yml`: Scrape targets and intervals
    *   `monitoring/grafana-datasources.yml`: Auto-provisioned Prometheus datasource
*   **Automation Fixes**: Resolved TEST watcher API connection issues, fixed cron health check configuration.
*   **Documentation**: [PROMETHEUS_GRAFANA_MONITORING_GUIDE.md](../04-user-guides/PROMETHEUS_GRAFANA_MONITORING_GUIDE.md)
*   **Status**: Operational in TEST, Ready for PRD deployment.

### **Phase 7: Final Lockdown & Certification** 📋 *(FUTURE)*

*   **Hardening**: Removing development tools from containers (curl, pip).
*   **Permissions**: Switching to non-root users everywhere.
*   **Certification**: Final Security Integrity Report and 100% compliance sign-off.

---

## 🔒 SECURITY ENFORCEMENT RULES

### **1. The No-Bypass Policy**
*   Workers MUST use the `proper_wingman_deployment.py` orchestrator.
*   The orchestrator will **BLOCK** execution if Phase 2 fails.
*   The orchestrator will **LOG** all claims to the Phase 3 logger.

### **2. Configuration Integrity**
*   **Zero Hardcoding**: All hostnames and ports in `docker-compose.prd.yml` use `${VAR}` abstraction.
*   **Secrets Isolation**: Credentials reside ONLY in `.env.prd` (excluded from git).
*   **Pre-commit Validation**: Any attempt to commit hardcoded secrets to PRD is blocked by the repository hooks.

---

## 📋 CURRENT DEPLOYMENT STATUS (MAC STUDIO)

| Component | Status | Port (External) |
| :--- | :--- | :--- |
| **wingman-prd-api** | ✅ Healthy (Phase 3) | 5001 |
| **wingman-prd-watcher**| 🚀 Deploying (Phase 4)| N/A |
| **wingman-prd-postgres**| ✅ Healthy | 5434 |
| **wingman-prd-redis** | ✅ Healthy | 6380 |
| **wingman-prd-telegram**| ✅ Running | N/A |

---

## 📋 SUCCESS CRITERIA

1.  ✅ **Phase 2 Gate**: Blocks 100% of instructions missing mandatory metadata.
2.  ✅ **Phase 3 Audit**: Correctly identifies `FALSE` claims when physical evidence is missing.
3.  ✅ **Phase 4 Alerting**: Mark receives Telegram alert within 10 seconds of a security violation.
4.  ✅ **Phase 5 Hardening**: Containers pass a vulnerability scan with zero criticals.

---

**Last Updated:** 2026-02-16
**Revision:** 2.1 (Phase 6.1 Output Validation Deployment)
**Lead AI Worker:** Claude Sonnet 4.5
