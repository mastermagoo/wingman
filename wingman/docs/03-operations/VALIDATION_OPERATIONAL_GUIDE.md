# Wingman Validation System - Operational Guide

**Status**: CURRENT
**Version**: 2.0 (Phase 4 Enhanced)
**Last Updated**: 2026-02-14
**Scope**: DEV / TEST / PRD

---

## Purpose

This guide explains how Wingman's validation system works, including the Phase 4 enhanced watcher service with deduplication, persistence, severity classification, and automated quarantine.

---

## Overview

Wingman uses a **profile-based validation system** to automatically assess approval requests and recommend AUTO_REJECT, AUTO_APPROVE, or MANUAL_REVIEW.

### Key Concepts

**Validation Profiles**: Two profiles that adapt validation to request type
- **Operational Profile**: For read-only, low-risk commands (logs, status checks)
- **Deployment Profile**: For write operations, deployments, schema changes

**Validators**: Five specialized validators that assess different aspects
1. **CodeScanner**: Pattern-based detection of secrets and dangerous commands
2. **SemanticAnalyzer**: Intent analysis and risk assessment
3. **DependencyAnalyzer**: Blast radius assessment
4. **ContentQualityValidator**: Quality of 10-point framework sections
5. **CompositeValidator**: Orchestrates profile detection and weighted scoring

**Recommendations**:
- **REJECT**: Auto-reject (secrets, dangerous patterns, score < 30)
- **APPROVE**: Auto-approve (low risk, high quality, score >= 85-90)
- **MANUAL_REVIEW**: Requires human decision

---

## How Validation Works

### Step 1: Profile Detection

CompositeValidator automatically detects which profile to use based on instruction keywords.

**Operational Profile Keywords**:
- `docker logs`, `docker ps`, `docker inspect`
- `curl health`, `curl status`, `curl metrics`
- `cat`, `tail`, `head`, `less`, `grep`
- `ls`, `pwd`, `whoami`, `uptime`
- `status check`, `health check`, `verify`

**Deployment Profile Keywords**:
- `deploy`, `release`, `rollout`, `publish`
- `migrate`, `migration`
- `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE`
- `restart container`, `stop container`, `docker stop`
- `kubectl apply`, `kubectl delete`
- `update config`, `modify env`

**Default**: If uncertain, uses Deployment profile (safer/stricter)

### Step 2: Validator Execution

CompositeValidator runs all validators and selects which ones to use based on profile.

**Operational Profile** (read-only commands):
- **Active Validators**: CodeScanner (60%), SemanticAnalyzer (40%)
- **Skipped**: ContentQualityValidator (10-point framework not needed for ops)
- **Weights**: CodeScanner weighted higher (safety is primary concern)

**Deployment Profile** (high-risk operations):
- **Active Validators**: CodeScanner (30%), ContentQualityValidator (25%), DependencyAnalyzer (20%), SemanticAnalyzer (25%)
- **Balanced weights**: All aspects important for deployments

### Step 3: Scoring and Decision

**Hard Floor Enforcement**: Any active validator scoring below 30 → immediate REJECT

**Secret Detection**: Any secrets found → immediate REJECT (bypasses all other logic)

**Weighted Score Calculation**:
```
overall_score = sum(validator_score * weight for each active validator)
```

**Auto-Reject**: `overall_score < 30` OR secrets found OR any validator < hard floor

**Auto-Approve**:
- Operational: All active validators >= 85 AND risk_level = LOW
- Deployment: All active validators >= 90 AND risk_level = LOW

**Manual Review**: Everything else (60-80% of requests expected)

---

## Interpreting Validation Results

### Example: Operational Command (Auto-Approved)

**Request**: "docker logs wingman-prd-api | tail -100"

**Validation Result**:
```json
{
  "overall_score": 90,
  "recommendation": "APPROVE",
  "profile": "operational",
  "risk_level": "LOW",
  "active_validators": ["code_scanner", "semantic_analyzer"],
  "validator_scores": {
    "code_scanner": 95,
    "semantic_analyzer": 88,
    "content_quality": 0,
    "dependency_analyzer": 50
  },
  "reasoning": "Profile 'operational': All validators passed with score >= 85 and risk LOW."
}
```

**Interpretation**:
- Detected as **operational** profile (read-only command)
- CodeScanner: 95 (no secrets, no dangerous patterns)
- SemanticAnalyzer: 88 (low risk, clear intent)
- ContentQuality/Dependency not used (operational profile skips these)
- Weighted score: 90 (95 * 0.6 + 88 * 0.4 = 92)
- **Result**: AUTO_APPROVED (score >= 85, risk LOW)

### Example: Deployment Request (Manual Review)

**Request**: "Deploy new feature to PRD" (with full 10-point framework)

**Validation Result**:
```json
{
  "overall_score": 78,
  "recommendation": "MANUAL_REVIEW",
  "profile": "deployment",
  "risk_level": "MEDIUM",
  "active_validators": ["code_scanner", "content_quality", "dependency_analyzer", "semantic_analyzer"],
  "validator_scores": {
    "code_scanner": 85,
    "content_quality": 75,
    "dependency_analyzer": 70,
    "semantic_analyzer": 75
  },
  "reasoning": "Profile 'deployment': Overall score 78; risk MEDIUM. Manual review required."
}
```

**Interpretation**:
- Detected as **deployment** profile (deploy keyword)
- All validators ran (deployment profile uses all 4)
- Weighted score: 78 (below auto-approve threshold of 90)
- Risk level: MEDIUM (not LOW, so no auto-approve)
- **Result**: MANUAL_REVIEW (includes full validation report for human decision)

### Example: Dangerous Request (Auto-Rejected)

**Request**: "docker exec api-server bash -c 'export API_KEY=sk-12345 && restart'"

**Validation Result**:
```json
{
  "overall_score": 15,
  "recommendation": "REJECT",
  "profile": "deployment",
  "risk_level": "CRITICAL",
  "active_validators": ["code_scanner", "content_quality", "dependency_analyzer", "semantic_analyzer"],
  "validator_scores": {
    "code_scanner": 0,
    "content_quality": 20,
    "dependency_analyzer": 40,
    "semantic_analyzer": 25
  },
  "reasoning": "Code scanner found secrets or credentials; immediate reject."
}
```

**Interpretation**:
- CodeScanner: 0 (hardcoded API key detected: `API_KEY=sk-12345`)
- Secrets found: TRUE
- **Result**: AUTO_REJECTED (secrets bypass all other logic)

---

## Tuning Validation Thresholds

### When to Tune

**Tune if**:
- False positive rate > 5% (valid requests incorrectly rejected)
- False negative rate > 2% (dangerous requests incorrectly approved)
- Auto-approve rate too low (<10%) or too high (>40%)

**Don't tune if**:
- System working as expected (manual review 60-80% is normal)
- Edge cases (rare scenarios should be manual review)

### How to Tune

#### 1. Adjust Auto-Approve Thresholds

**Location**: `validation/composite_validator.py`, `VALIDATION_PROFILES`

**Operational Profile**:
```python
"auto_approve_threshold": 85,  # Lower = more auto-approvals
```

**Deployment Profile**:
```python
"auto_approve_threshold": 90,  # Higher = stricter auto-approval
```

**Recommendation**: Start conservative (90), reduce gradually (85, 80) if too strict

#### 2. Adjust Hard Floor

**Location**: `validation/composite_validator.py`, `VALIDATION_PROFILES`

```python
"hard_floor": 30,  # Minimum score for any validator
```

**Effect**: Any validator below this → immediate REJECT

**Recommendation**: Keep at 30 unless seeing too many false positives

#### 3. Adjust Validator Weights

**Location**: `validation/composite_validator.py`, `VALIDATION_PROFILES`

**Operational Profile**:
```python
"weights": {
    "code_scanner": 0.6,      # Safety is primary
    "semantic_analyzer": 0.4  # Intent is secondary
}
```

**Deployment Profile**:
```python
"weights": {
    "code_scanner": 0.3,
    "content_quality": 0.25,
    "dependency_analyzer": 0.2,
    "semantic_analyzer": 0.25
}
```

**Recommendation**: Adjust based on which validator is causing most false positives/negatives

#### 4. Add Profile Detection Keywords

**Location**: `validation/composite_validator.py`, `OPERATIONAL_KEYWORDS` / `DEPLOYMENT_KEYWORDS`

**Add Operational Keyword**:
```python
OPERATIONAL_KEYWORDS = [
    # ... existing patterns ...
    r"\byour_new_pattern\b",  # Add new pattern here
]
```

**Example**: If "show metrics" should be operational but gets deployment profile:
```python
r"\bshow\s+(metrics|stats|graphs)\b",
```

#### 5. Adjust Feature Flags

**Location**: Environment variables (`.env.test`, `.env.prd`)

**Enable/Disable Validation**:
```bash
VALIDATION_ENABLED=1  # 1=enabled, 0=disabled
```

**Gradual Rollout**:
```bash
VALIDATION_ROLLOUT_PERCENT=10  # 0-100, percentage of requests to validate
```

---

## Troubleshooting Common Issues

### Issue: Valid Request Auto-Rejected

**Symptoms**: Request is safe but validation recommends REJECT

**Diagnosis**:
1. Check `validator_scores` in validation result
2. Identify which validator scored below hard floor (30)
3. Check `reasoning` field for explanation

**Solutions**:
- **CodeScanner false positive**: Add pattern to whitelist in `code_scanner.py`
- **ContentQuality false positive**: Request may be missing required 10-point sections
- **Hard floor too strict**: Consider lowering from 30 to 25 (requires code change)

**Example Fix** (CodeScanner whitelist):
```python
# validation/code_scanner.py
# Add to SAFE_PATTERNS or adjust detection logic
if "safe_known_pattern" in instruction:
    return score + 20  # Boost score for known safe pattern
```

### Issue: Dangerous Request Auto-Approved

**Symptoms**: Risky operation gets AUTO_APPROVED when it should require manual review

**Diagnosis**:
1. Check which profile was detected
2. Check if all validators scored high (>= 85-90)
3. Check if risk_level was incorrectly assessed as LOW

**Solutions**:
- **Wrong profile**: Add deployment keyword to `DEPLOYMENT_KEYWORDS`
- **SemanticAnalyzer too lenient**: Adjust risk assessment heuristics
- **Auto-approve threshold too low**: Increase from 85 to 90

**Example Fix** (Add deployment keyword):
```python
# validation/composite_validator.py
DEPLOYMENT_KEYWORDS = [
    # ... existing patterns ...
    r"\byour_risky_operation\b",  # Add keyword that should trigger deployment profile
]
```

### Issue: Too Many Manual Reviews

**Symptoms**: 90%+ of requests go to manual review (expected: 60-80%)

**Diagnosis**:
1. Check auto-approve threshold (may be too strict)
2. Check if most requests score between 75-85 (just below threshold)

**Solutions**:
- **Operational profile**: Lower auto-approve from 85 to 80
- **Deployment profile**: Accept that deployments should be manual (90 threshold is appropriate)
- **Review request quality**: Many manual reviews may indicate requests need better documentation

### Issue: Validation Disabled but Still Seeing Validation Results

**Symptoms**: `VALIDATION_ENABLED=0` but validation still runs

**Diagnosis**:
1. Check environment variable is set correctly in container
2. Verify container was restarted after env change
3. Check for rollout percentage logic

**Solutions**:
```bash
# Verify env var in container
docker exec wingman-prd-api printenv | grep VALIDATION

# Should see:
VALIDATION_ENABLED=0

# If not, check .env.prd and restart:
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d wingman-api
```

---

## Monitoring and Metrics

### Key Metrics to Track

**Auto-Reject Rate**: % of requests auto-rejected
- **Expected**: 5-10%
- **Alert if**: >15% (too many false positives) or <2% (missing dangerous patterns)

**Auto-Approve Rate**: % of requests auto-approved
- **Expected**: 15-30%
- **Alert if**: >40% (too lenient) or <10% (too strict)

**Manual Review Rate**: % requiring human decision
- **Expected**: 60-80%
- **Alert if**: >85% (thresholds too strict) or <50% (thresholds too lenient)

**False Positive Rate**: Valid requests incorrectly rejected
- **Target**: <5%
- **Critical**: >10%

**False Negative Rate**: Dangerous requests incorrectly approved
- **Target**: <2%
- **Critical**: >5%

### How to Collect Metrics

**Query approval_requests table**:
```sql
-- Auto-reject rate (last 7 days)
SELECT
  COUNT(*) FILTER (WHERE status = 'AUTO_REJECTED') * 100.0 / COUNT(*) as auto_reject_pct,
  COUNT(*) FILTER (WHERE status = 'AUTO_APPROVED') * 100.0 / COUNT(*) as auto_approve_pct,
  COUNT(*) FILTER (WHERE status = 'PENDING') * 100.0 / COUNT(*) as manual_review_pct
FROM approval_requests
WHERE created_at > NOW() - INTERVAL '7 days';

-- False positives (manual override of auto-reject)
SELECT COUNT(*)
FROM approval_requests
WHERE status = 'AUTO_REJECTED'
  AND reviewed_at IS NOT NULL
  AND approved = true;
```

---

## Advanced Topics

### Custom Validation Rules

**Scenario**: You want to auto-reject all requests containing "production database drop"

**Solution**: Add pattern to CodeScanner dangerous patterns
```python
# validation/code_scanner.py
DANGEROUS_PATTERNS = {
    # ... existing patterns ...
    "production_db_drop": r"\bproduction\s+database\s+drop\b",
}
```

### Environment-Specific Thresholds

**Scenario**: PRD should have stricter validation than TEST

**Solution**: Use environment variable-based configuration
```python
# validation/composite_validator.py
import os

deployment_env = os.getenv("DEPLOYMENT_ENV", "test")
auto_approve_threshold = 90 if deployment_env == "prd" else 85
```

### Integration with External Systems

**Scenario**: Send validation results to monitoring system

**Solution**: Add webhook or logging in `api_server.py`
```python
# api_server.py (after validation)
if validation_result:
    send_to_monitoring_system({
        "request_id": req.request_id,
        "validation_score": validation_result["overall_score"],
        "recommendation": validation_result["recommendation"],
        "profile": validation_result["profile"]
    })
```

---

## Phase 4 Enhanced: Watcher Service

**Version**: 2.0
**Status**: Deployed to PRD
**Features**: Deduplication, Persistence, Severity Classification, Automated Quarantine

### Overview

The Wingman Watcher service monitors the claims audit log and provides autonomous security monitoring with:

1. **Redis-based deduplication** - Prevents alert spam from duplicate events
2. **Postgres persistence** - Full audit trail with acknowledgment workflow
3. **Severity classification** - CRITICAL/HIGH/MEDIUM/LOW based on environment and operation type
4. **Automated quarantine** - Blocks compromised workers from approval flow (defensive only)

### Architecture

```
┌─────────────────┐
│ Claims Audit    │
│ Log (JSONL)     │
└────────┬────────┘
         │
         v
┌─────────────────────────────────────────────┐
│ Wingman Watcher (wingman_watcher.py)       │
│                                             │
│ 1. Read new events                          │
│ 2. Classify severity (env + operation)     │
│ 3. Check deduplication (Redis)              │
│ 4. Persist to database (Postgres)           │
│ 5. Send alert (Telegram if not deduped)    │
│ 6. Quarantine worker (if CRITICAL)          │
│ 7. Hourly digest (suppressed alerts)        │
└──┬──────────────┬──────────────┬────────────┘
   │              │              │
   v              v              v
┌─────────┐  ┌──────────┐  ┌─────────────┐
│ Redis   │  │ Postgres │  │ Telegram    │
│ Dedup + │  │ Alerts   │  │ Alerts      │
│ Quarant.│  │ Table    │  │             │
└─────────┘  └──────────┘  └─────────────┘
```

### Severity Classification

| Severity | Condition | Example | Action |
|----------|-----------|---------|--------|
| **CRITICAL** | FALSE claim in PRD + destructive op | `docker stop`, `DROP TABLE`, `rm -rf` | Alert + Quarantine |
| **HIGH** | FALSE claim in PRD + safe op | Read-only command in PRD | Alert only |
| **MEDIUM** | FALSE claim in TEST | Any FALSE claim in TEST env | Alert only |
| **LOW** | Informational | UNVERIFIABLE claims | Persist only (no alert) |

**Telegram Formatting**:
- 🚨 CRITICAL (push notification enabled)
- ⚠️ HIGH (push notification enabled)
- ℹ️ MEDIUM (push notification enabled)
- 📝 LOW (silent notification)

### Deduplication

**How it works**:
1. Generate fingerprint: `SHA256(event_type + worker_id + timestamp_window)`
2. Check Redis: `GET watcher:dedup:{fingerprint}`
3. If exists → increment counter, skip alert
4. If not exists → send alert, store in Redis with 1-hour TTL

**Hourly Digest**:
- Runs every hour (configurable via `WINGMAN_WATCHER_DIGEST_INTERVAL_SEC`)
- Sends single message summarizing suppressed alerts
- Example:
  ```
  📊 Watcher Digest (last hour)

  Suppressed duplicates:
  - CRITICAL: Worker worker_123 (5 occurrences)
  - HIGH: Worker worker_456 (3 occurrences)

  Total alerts suppressed: 8
  ```

**Configuration**:
```bash
# .env.test / .env.prd
WINGMAN_WATCHER_DEDUP_TTL_SEC=3600  # 1 hour
WINGMAN_WATCHER_DIGEST_INTERVAL_SEC=3600  # 1 hour
```

### Persistence

**Database Table**: `watcher_alerts`
```sql
CREATE TABLE watcher_alerts (
    alert_id UUID PRIMARY KEY,
    event_type TEXT NOT NULL,
    worker_id TEXT,
    severity TEXT CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    message TEXT,
    fingerprint TEXT,
    sent_at TIMESTAMP DEFAULT NOW(),
    acknowledged_at TIMESTAMP,
    acknowledged_by TEXT,
    environment TEXT NOT NULL,
    metadata JSONB
);
```

**API Endpoints**:

#### Get Alert History
```bash
# Get all CRITICAL alerts in PRD
curl "http://127.0.0.1:8101/watcher/alerts?severity=CRITICAL&environment=prd&limit=50" \
  -H "X-Wingman-Approval-Read-Key: YOUR_READ_KEY"

# Get unacknowledged alerts
curl "http://127.0.0.1:8101/watcher/alerts?unacknowledged=true" \
  -H "X-Wingman-Approval-Read-Key: YOUR_READ_KEY"
```

#### Acknowledge Alert
```bash
curl -X POST "http://127.0.0.1:8101/watcher/acknowledge/{alert_id}" \
  -H "X-Wingman-Approval-Decide-Key: YOUR_DECIDE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"acknowledged_by": "mark@example.com"}'
```

**Retention**: 30 days (to be implemented via cron job)
```sql
-- Run daily
DELETE FROM watcher_alerts WHERE sent_at < NOW() - INTERVAL '30 days';
```

### Automated Quarantine

**Principle**: Defensive only - block future approvals, NO auto-rollback.

**Trigger**: CRITICAL severity event (FALSE claim in PRD + destructive operation)

**Action**:
1. Add worker_id to Redis set: `quarantined_workers`
2. Store metadata in Redis hash: `quarantine:{worker_id}`
3. Log quarantine event to database
4. Send Telegram alert: "🔒 Worker {worker_id} quarantined"

**Enforcement**: In `api_server.py` `/approvals/request` endpoint:
```python
# Check quarantine FIRST (before risk assessment)
if is_quarantined(worker_id):
    return 403 AUTO_REJECTED with message:
    "Worker quarantined: {reason}. Contact Mark to release."
```

**Release Mechanism** (manual only):

Via API:
```bash
curl -X POST "http://127.0.0.1:8101/watcher/release/worker_123" \
  -H "X-Wingman-Approval-Decide-Key: YOUR_DECIDE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "released_by": "mark@example.com",
    "reason": "False positive investigation complete"
  }'
```

Via Telegram (to be implemented):
```
/release_worker worker_123
```

**Audit Trail**: All quarantine/release events logged to:
- Redis (metadata)
- Postgres (`watcher_alerts` table)
- Claims audit log (`data/claims_audit.jsonl`)

### Configuration Reference

```bash
# Environment
DEPLOYMENT_ENV=test  # or "prd"

# Database (Postgres)
DB_HOST=postgres
DB_PORT=5432
DB_NAME=wingman
DB_USER=wingman
DB_PASSWORD=<from_secrets>

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Deduplication
WINGMAN_WATCHER_DEDUP_TTL_SEC=3600  # 1 hour
WINGMAN_WATCHER_DIGEST_INTERVAL_SEC=3600  # 1 hour

# Quarantine
WINGMAN_QUARANTINE_ENABLED=1  # 1=enabled, 0=disabled

# Persistence
WINGMAN_WATCHER_PERSISTENCE_ENABLED=1  # 1=enabled, 0=disabled

# Notifications
TELEGRAM_BOT_TOKEN=<from_secrets>
TELEGRAM_CHAT_ID=<from_secrets>
WINGMAN_NOTIFY_BACKENDS=stdout,telegram  # comma-separated
```

### Operational Procedures

#### 1. Check Quarantined Workers
```bash
# Via Redis CLI
docker compose -f docker-compose.yml -p wingman-test exec redis redis-cli
> SMEMBERS quarantined_workers
> HGETALL quarantine:worker_123
```

#### 2. Review Alert History
```bash
# Get all CRITICAL alerts in last 24 hours
curl "http://127.0.0.1:8101/watcher/alerts?severity=CRITICAL&since=$(date -u -v-24H +%Y-%m-%dT%H:%M:%S)&limit=100" \
  -H "X-Wingman-Approval-Read-Key: YOUR_KEY"
```

#### 3. Investigate False Positives
```bash
# Check worker history
curl "http://127.0.0.1:8101/watcher/alerts?worker_id=worker_123&limit=50" \
  -H "X-Wingman-Approval-Read-Key: YOUR_KEY"

# If false positive: release worker
curl -X POST "http://127.0.0.1:8101/watcher/release/worker_123" \
  -H "X-Wingman-Approval-Decide-Key: YOUR_KEY" \
  -d '{"released_by": "mark", "reason": "False positive - safe claim"}'
```

#### 4. Emergency: Clear All Quarantines
```bash
# WARNING: Only use in emergency (e.g., watcher bug causing mass quarantine)
docker compose -f docker-compose.yml -p wingman-test exec redis redis-cli DEL quarantined_workers
docker compose -f docker-compose.yml -p wingman-test exec redis redis-cli KEYS "quarantine:*" | xargs docker compose -f docker-compose.yml -p wingman-test exec redis redis-cli DEL
```

#### 5. Disable Quarantine (Emergency)
```bash
# Edit .env.test or .env.prd
WINGMAN_QUARANTINE_ENABLED=0

# Restart watcher
docker compose -f docker-compose.yml -p wingman-test restart wingman-watcher
```

### Monitoring

**Health Checks**:
```bash
# Check watcher is running
docker compose -f docker-compose.yml -p wingman-test ps wingman-watcher

# Check logs
docker compose -f docker-compose.yml -p wingman-test logs -f wingman-watcher

# Look for:
# ✅ Redis connected: redis:6379
# ✅ Postgres connected: postgres:5432/wingman
# 👀 WINGMAN WATCHER: Monitoring data/claims_audit.jsonl
# 🔧 Environment: TEST
# 🔧 Deduplication: Enabled (TTL: 3600s)
# 🔧 Persistence: Enabled
# 🔧 Quarantine: Enabled
```

**Metrics** (via database):
```sql
-- Alert volume by severity (last 7 days)
SELECT severity, COUNT(*), environment
FROM watcher_alerts
WHERE sent_at > NOW() - INTERVAL '7 days'
GROUP BY severity, environment
ORDER BY severity;

-- Quarantine events
SELECT COUNT(*), environment
FROM watcher_alerts
WHERE event_type = 'WORKER_QUARANTINED'
  AND sent_at > NOW() - INTERVAL '30 days'
GROUP BY environment;

-- Acknowledgment rate
SELECT
  COUNT(*) FILTER (WHERE acknowledged_at IS NOT NULL) * 100.0 / COUNT(*) as ack_rate
FROM watcher_alerts
WHERE sent_at > NOW() - INTERVAL '7 days';
```

### Troubleshooting

**Problem**: Watcher not sending alerts

**Solution**:
1. Check Telegram credentials:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec wingman-watcher env | grep TELEGRAM
   ```
2. Test Telegram connectivity:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec wingman-watcher \
     python -c "import os,requests; t=os.environ.get('TELEGRAM_BOT_TOKEN'); r=requests.get(f'https://api.telegram.org/bot{t}/getMe'); print(r.json())"
   ```
3. Check Redis connectivity:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec wingman-watcher \
     python -c "import redis; r=redis.Redis(host='redis', port=6379); print(r.ping())"
   ```

**Problem**: Too many duplicate alerts

**Solution**:
1. Increase dedup TTL:
   ```bash
   # .env.test
   WINGMAN_WATCHER_DEDUP_TTL_SEC=7200  # 2 hours instead of 1
   ```
2. Restart watcher:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test restart wingman-watcher
   ```

**Problem**: Worker incorrectly quarantined

**Solution**:
1. Release worker via API (see procedure #3 above)
2. Investigate root cause:
   - Check event that triggered quarantine in `watcher_alerts` table
   - Review severity classification logic in `wingman_watcher.py`
   - If pattern is common false positive, adjust severity classification

**Problem**: Database table full (>30 days of alerts)

**Solution**:
1. Manual cleanup:
   ```sql
   DELETE FROM watcher_alerts WHERE sent_at < NOW() - INTERVAL '30 days';
   ```
2. Set up daily cron job (future enhancement)

---

## Related Documentation

- **Architecture**: `../02-architecture/AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md`
- **Deployment Plan**: `../deployment/AAA_DELTA_REPORT_VALIDATION_DEPLOYMENT.md`
- **Watcher Design**: `WATCHER_ENHANCEMENT_DESIGN.md`
- **Operations Runbook**: `AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md`
- **User Guide**: `../04-user-guides/APPROVAL_WORKFLOW_WITH_VALIDATION.md` (to be created)

---

**Document End**
