# Wingman Architecture — Current Build Design (DEV/TEST/PRD)
**Version**: 2.0

**Status**: CURRENT (authoritative for "what is implemented now")
**Last Updated**: 2026-02-16
**Scope**: DEV / TEST / PRD  

---

## What this document is (and is not)

- **This is**: the design/implementation shape of the *current Wingman build* (what exists in code + compose stacks today).
- **This is not**: the long-term product vision. For that, see `../00-Strategic/AAA_WINGMAN_STRATEGY_ROADMAP.md`.

---

## Current build: key security property

**Non-bypassable privileged execution** is enforced by the **Execution Gateway** (Phase R0):

- Only `execution-gateway` gets Docker socket access in TEST (`wingman/docker-compose.yml`).
- Privileged actions must flow through:
  - `POST /gateway/token` (token minted only after APPROVED/AUTO_APPROVED)
  - `POST /gateway/execute` (execution constrained to token scope)
- Dangerous shell operators are blocked even if present (`&&`, `|`, `;`, redirections, etc.).

**AI-generated code validation** is enforced by **Output Validation** (Phase 6.1):

- All AI worker generated code must pass validation before deployment.
- 5 validators analyze code: Syntax, Security, Dependency, Test Execution, Composite.
- Decision logic: AUTO_APPROVE (score >= 70), AUTO_REJECT (blocking issues), MANUAL_REVIEW (human approval required).
- Integration via `POST /output_validation/validate` endpoint.

Operational validation steps (TEST) are captured in:
- `../03-operations/AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md`

---

## Current build: environments (what matters)

**Base URLs (documented):**
- **PRD**: `http://127.0.0.1:5001`
- **TEST**: `http://127.0.0.1:8101`

**Compose stacks (source of truth):**
- **TEST**: `wingman/docker-compose.yml` (project: `wingman-test`)
- **PRD**: `wingman/docker-compose.prd.yml` (project: `wingman-prd`)

---

## Current build: core components

### API (Flask)

Core endpoints:
- `GET /health`
- `POST /check` (10-point framework presence check + policy checks)
- `POST /log_claim` (claims ledger)
- `POST /verify` (verification)
- `POST /approvals/request` + approval lifecycle endpoints

### Approvals (HITL)

Risk-based flow with validation enhancement:
- **AUTO_REJECTED**: Secrets found, dangerous patterns, or validation score < 30
- **AUTO_APPROVED**: LOW risk + validation score >= 90 (operational profile: >=85)
- **MANUAL_REVIEW**: Medium/high risk or validation inconclusive

### Validation Layer (Phase 1-2, Complete 2026-02-14)

**Status**: Deployed to TEST and PRD (PRD: disabled by default, ready for gradual rollout)

**Architecture**: Profile-based validation with 5 validators
- **CompositeValidator**: Orchestrates validation based on detected profile
  - **Operational Profile**: Read-only/low-risk commands (docker logs, status checks)
    - Validators: CodeScanner (60%), SemanticAnalyzer (40%)
    - Auto-approve threshold: 85, Auto-reject threshold: 30
    - Skips ContentQualityValidator (no 10-point framework needed)
  - **Deployment Profile**: Deployments, schema changes, high-risk operations
    - Validators: CodeScanner (30%), ContentQualityValidator (25%), DependencyAnalyzer (20%), SemanticAnalyzer (25%)
    - Auto-approve threshold: 90, Auto-reject threshold: 30
    - Requires full 10-point framework validation

**Validators** (990 LOC total):
1. **CodeScanner** (207 LOC): Pattern-based detection of secrets, dangerous commands, destructive operations
2. **SemanticAnalyzer** (129 LOC): Intent analysis and risk assessment (heuristic-based, no LLM dependency)
3. **DependencyAnalyzer** (138 LOC): Blast radius assessment for cascading failures
4. **ContentQualityValidator** (283 LOC): Evaluates quality of 10-point framework sections
5. **CompositeValidator** (214 LOC): Profile detection and weighted scoring

**Decision Logic**:
- **Auto-Reject Triggers**:
  - Secrets or credentials detected (immediate reject)
  - Any active validator scores below hard floor (30)
  - Overall weighted score below auto-reject threshold (30)
- **Auto-Approve Criteria**:
  - Profile-appropriate validators all score above auto-approve threshold (85-90)
  - Risk level is LOW
  - No secrets or dangerous patterns detected
- **Manual Review**: Everything else (includes full validation report)

**Feature Flags** (environment variables):
- `VALIDATION_ENABLED`: 1=enabled, 0=disabled (default: 1 for TEST, 0 for PRD)
- `VALIDATION_ROLLOUT_PERCENT`: 0-100 (default: 100, allows gradual rollout)

**Profile Detection**: Automatic based on instruction keywords
- Operational: `docker logs`, `docker ps`, `curl health`, `cat`, `tail`, `status check`
- Deployment: `deploy`, `migrate`, `CREATE TABLE`, `restart container`, `docker stop`

**Test Coverage**: 843 LOC comprehensive tests across all validators

### Output Validation (Phase 6.1, Deployed 2026-02-16)

**Status**: Deployed to TEST (enabled) and PRD (disabled by default, ready for gradual rollout)

**Purpose**: Validate AI-generated code before deployment to prevent security issues, syntax errors, and missing dependencies.

**Architecture**: 5-validator pipeline with composite decision-making

**Validators** (2000+ LOC total):

1. **SyntaxValidator** (~200 LOC): Python syntax validation using `ast.parse()`
   - Detects: Syntax errors, malformed code
   - Blocking: Yes (syntax errors trigger AUTO_REJECT)

2. **OutputSecurityScanner** (~300 LOC): Security pattern detection
   - Detects: Hardcoded secrets, dangerous imports, SQL injection patterns
   - Severity levels: LOW, MEDIUM, HIGH, CRITICAL
   - Blocking: Yes (CRITICAL issues trigger AUTO_REJECT + worker quarantine)

3. **DependencyVerifier** (~250 LOC): Import validation and dependency checking
   - Detects: Missing dependencies, import errors
   - Method: Docker exec into container to verify imports
   - Blocking: Yes (missing critical dependencies trigger AUTO_REJECT)

4. **TestExecutor** (~200 LOC): Automated test execution for generated code
   - Method: Runs pytest in docker container
   - Detects: Test failures, test errors
   - Blocking: Yes (test failures trigger MANUAL_REVIEW)

5. **OutputCompositeValidator** (~1050 LOC): Orchestrates validation and makes decisions
   - Aggregates results from all validators
   - Calculates weighted score (0-100)
   - Decision logic:
     - **AUTO_REJECT**: score < 50 OR blocking issues detected
     - **AUTO_APPROVE**: score >= 70 AND no blocking issues
     - **MANUAL_REVIEW**: score 50-69 OR non-blocking issues

**API Endpoint**: `POST /output_validation/validate`

Request format:
```json
{
  "worker_id": "WORKER_001",
  "generated_files": ["path/to/file1.py", "path/to/file2.py"],
  "task_name": "Generate Semantic Analyzer"
}
```

Response format (AUTO_APPROVE):
```json
{
  "status": "APPROVED",
  "validation_report": {
    "decision": "APPROVE",
    "overall_score": 95,
    "recommendation": "Code passed all validators. Safe to deploy.",
    "validation_id": 123
  },
  "message": "Code passed validation. Safe to deploy."
}
```

Response format (AUTO_REJECT):
```json
{
  "status": "REJECTED",
  "reason": "Syntax errors detected",
  "validation_report": {
    "decision": "REJECT",
    "overall_score": 45,
    "blocking_issues": ["Syntax error in file1.py: unexpected EOF"],
    "recommendation": "Fix syntax errors before deployment",
    "validation_id": 124
  }
}
```

Response format (MANUAL_REVIEW):
```json
{
  "status": "PENDING",
  "approval_id": "APR_20260216_001",
  "validation_report": {
    "decision": "MANUAL_REVIEW",
    "overall_score": 65,
    "blocking_issues": [],
    "recommendation": "Code quality concerns. Manual review recommended.",
    "validation_id": 125
  },
  "message": "Manual review required. Approval request created."
}
```

**Database**: Migration 006 adds `output_validations` table
- Fields: validation_id, worker_id, generated_files, decision, overall_score, validation_results, created_at, approval_id
- Linked to approvals table for MANUAL_REVIEW cases

**Test Coverage**: 92% (13/15 passing tests)
- Integration tests: `tests/test_output_validation_integration.py` (755 LOC)
- Test runner: `tests/run_output_validation_tests.py` (495 LOC)
- Documentation: `tests/OUTPUT_VALIDATION_TESTS_README.md`

**Feature Flags**:
- `VALIDATION_ENABLED`: 1=enabled, 0=disabled (default: 1 for TEST, 0 for PRD)
- `VALIDATION_ROLLOUT_PERCENT`: 0-100 (default: 100, allows gradual rollout)

**Integration Points**:
- Calls approval system for MANUAL_REVIEW decisions
- Quarantines workers on CRITICAL security issues
- Sends Telegram notifications for all validation outcomes
- Stores results in Postgres for audit trail

### Verifiers

- **Simple verifier**: filesystem/process checks
- **Enhanced verifier**: optional LLM-backed analysis (implementation-specific)

### Watcher

Watcher exists and is part of the system plan; operational status is tracked in:
- `../00-Strategic/AAA_WINGMAN_STRATEGY_ROADMAP.md`
- `../deployment/AAA_DEPLOYMENT_COMPLETE.md` (what is actually deployed)

### Monitoring & Observability (Phase 6.1+, Deployed 2026-02-17)

**Status**: Operational in TEST, Ready for PRD

**Purpose**: Real-time metrics collection, visualization, and alerting for Wingman system health and performance.

**Architecture**: Prometheus + Grafana stack

**Components**:

1. **Metrics Endpoint** (`/metrics`) — Prometheus-format metrics exposed by Wingman API
   - `wingman_health_status` (gauge): Overall health (1=healthy, 0=unhealthy)
   - `wingman_verifier_available` (gauge): Verifier availability by type (simple, enhanced)
   - `wingman_validator_available` (gauge): Validator availability by type (input, output)
   - `wingman_database_connected` (gauge): Database connection status (1=connected, 0=disconnected)
   - `wingman_start_time_seconds` (gauge): Process start time (Unix timestamp)

2. **Prometheus** — Time-series metrics database and scraper
   - Scrapes Wingman API `/metrics` endpoint every 15s
   - Stores historical metrics data
   - Supports PromQL queries and alerting rules
   - TEST: `http://localhost:9091` (port 9090 internal)
   - PRD: `http://localhost:9092` (when deployed)

3. **Grafana** — Metrics visualization and dashboards
   - Pre-configured Prometheus datasource
   - Custom dashboards for Wingman health monitoring
   - Alert notification channels (Telegram, email, Slack)
   - TEST: `http://localhost:3333` (login: admin/admin)
   - PRD: `http://localhost:3334` (when deployed)

**Deployment**:
- TEST: Operational since 2026-02-17
- PRD: Ready for deployment (compose config prepared)

**Docker Services**:
```yaml
# docker-compose.yml (TEST)
prometheus:
  image: prom/prometheus:latest
  ports: ["127.0.0.1:9091:9090"]
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - prometheus_data:/prometheus

grafana:
  image: grafana/grafana:latest
  ports: ["127.0.0.1:3333:3000"]
  volumes:
    - grafana_data:/var/lib/grafana
    - ./monitoring/grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml:ro
```

**Configuration Files**:
- `monitoring/prometheus.yml` — Prometheus scrape configuration
- `monitoring/grafana-datasources.yml` — Grafana datasource provisioning
- Future: `monitoring/prometheus-alerts.yml` — Alert rules (planned)

**Use Cases**:
- Real-time health monitoring (API uptime, database connectivity)
- Verifier/validator availability tracking
- Performance metrics (request latency, throughput — planned)
- Custom alerting (API down, database disconnected, etc.)
- Historical trend analysis and capacity planning

**Documentation**: [PROMETHEUS_GRAFANA_MONITORING_GUIDE.md](../04-user-guides/PROMETHEUS_GRAFANA_MONITORING_GUIDE.md)

**Future Enhancements**:
- Postgres Exporter (database metrics)
- Redis Exporter (cache metrics)
- Custom application metrics (approval queue depth, validation scores)
- Alertmanager integration (alert routing and silencing)
- Telegram alert integration with Wingman bot

---

## Current build: what is deployed where (facts live elsewhere)

This doc deliberately does **not** re-assert “what is currently running” as truth because that changes. The factual record is kept in:

- `../deployment/AAA_DEPLOYMENT_COMPLETE.md` — deployed reality snapshot + deltas
- `../deployment/AAA_PRD_DEPLOYMENT_PLAN.md` — PRD gateway rollout plan (when executed)

---

## Related

- `AAA_WINGMAN_ARCHITECTURE_CURRENT_STATE.md` — overall architecture
- `AAA_WINGMAN_ARCHITECTURE_GAP_NEXT.md` — what comes next / remaining gaps

