# Watcher Enhancement Design (Phase 4)

**Date**: 2026-02-14
**Status**: Implementation
**Owner**: Wingman System
**Related**: Phase 4 - Autonomous Monitoring Enhancement

---

## Executive Summary

This document defines the enhancement of the Wingman Watcher service (`wingman_watcher.py`) to add enterprise-grade features:

1. **Deduplication**: Prevent alert spam via Redis-based fingerprinting
2. **Persistence**: Database tracking of all alerts with acknowledgment workflow
3. **Severity Classification**: CRITICAL/HIGH/MEDIUM/LOW based on event type and environment
4. **Automated Quarantine**: Block compromised workers from approval flow (Phase 1 - safe actions only)

**Key Principle**: NO auto-rollback. Quarantine is defensive (block future approvals), not corrective.

---

## 1. Deduplication Strategy

### 1.1 Problem Statement

Current watcher sends Telegram alerts for every FALSE claim event, causing:
- Alert fatigue when same worker triggers multiple violations
- Missed critical alerts buried in noise
- No visibility into suppressed duplicate events

### 1.2 Solution: Redis-based Fingerprinting

**Fingerprint Generation**:
```python
import hashlib
import json

def generate_fingerprint(event_type: str, worker_id: str, timestamp: int, window_sec: int = 3600) -> str:
    """
    Generate fingerprint for deduplication.

    timestamp_window: Round timestamp to window boundaries (e.g., 1-hour windows)
    This ensures events in the same window get the same fingerprint.
    """
    window_bucket = (timestamp // window_sec) * window_sec
    data = {
        "event_type": event_type,
        "worker_id": worker_id,
        "window": window_bucket
    }
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    return fingerprint[:16]  # Use first 16 chars for Redis key
```

**Redis Storage**:
- Key: `watcher:dedup:{fingerprint}`
- Value: JSON object with `{ "count": N, "first_seen": ts, "last_seen": ts, "event_type": ..., "worker_id": ... }`
- TTL: 1 hour (configurable via `WINGMAN_WATCHER_DEDUP_TTL_SEC`, default 3600)

**Deduplication Logic**:
1. Generate fingerprint from event
2. Check Redis: `GET watcher:dedup:{fingerprint}`
3. If exists:
   - Increment counter: `HINCRBY watcher:dedup:{fingerprint} count 1`
   - Update last_seen timestamp
   - Skip Telegram alert (suppressed)
4. If not exists:
   - Create Redis entry with count=1
   - Send Telegram alert (first occurrence)
   - Set TTL

**Hourly Digest**:
- Run every hour (configurable via `WINGMAN_WATCHER_DIGEST_INTERVAL_SEC`, default 3600)
- Scan Redis for all `watcher:dedup:*` keys with count > 1
- Send single digest message to Telegram:
  ```
  📊 Watcher Digest (last hour)

  Suppressed duplicates:
  - CRITICAL: Worker worker_123 (5 occurrences)
  - HIGH: Worker worker_456 (3 occurrences)

  Total alerts suppressed: 8
  ```
- Clear digest counters after sending

### 1.3 Environment Variables

```bash
# Deduplication window (seconds) - default 3600 (1 hour)
WINGMAN_WATCHER_DEDUP_TTL_SEC=3600

# Digest interval (seconds) - default 3600 (1 hour)
WINGMAN_WATCHER_DIGEST_INTERVAL_SEC=3600

# Redis connection
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
```

---

## 2. Persistence Schema

### 2.1 Problem Statement

Current watcher has no database tracking:
- No audit trail of alerts sent
- No acknowledgment workflow
- Cannot query alert history
- No retention policy

### 2.2 Solution: Postgres Table

**Table Schema** (migration `002_add_watcher_alerts.sql`):

```sql
CREATE TABLE IF NOT EXISTS watcher_alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    worker_id TEXT,
    severity TEXT NOT NULL CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    message TEXT,
    fingerprint TEXT,  -- For dedup tracking
    sent_at TIMESTAMP NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMP,
    acknowledged_by TEXT,
    environment TEXT NOT NULL,  -- 'test' or 'prd'
    metadata JSONB  -- Store full event details
);

-- Indexes
CREATE INDEX idx_alerts_severity ON watcher_alerts(severity);
CREATE INDEX idx_alerts_sent_at ON watcher_alerts(sent_at DESC);
CREATE INDEX idx_alerts_worker ON watcher_alerts(worker_id);
CREATE INDEX idx_alerts_acked ON watcher_alerts(acknowledged_at) WHERE acknowledged_at IS NULL;
CREATE INDEX idx_alerts_fingerprint ON watcher_alerts(fingerprint);

-- Retention: auto-delete alerts older than 30 days
-- (To be implemented via cron or scheduled job)
COMMENT ON TABLE watcher_alerts IS 'Audit trail of all watcher alerts sent (30-day retention)';
```

### 2.3 API Endpoints

**New endpoints in `api_server.py`**:

#### 2.3.1 Acknowledge Alert
```
POST /watcher/acknowledge/{alert_id}

Body:
{
  "acknowledged_by": "mark@example.com"  # optional
}

Response:
{
  "success": true,
  "alert_id": "uuid",
  "acknowledged_at": "2026-02-14T10:30:00"
}
```

#### 2.3.2 Alert History
```
GET /watcher/alerts?severity=CRITICAL&since=2026-02-01&limit=50&worker_id=worker_123

Response:
{
  "alerts": [
    {
      "alert_id": "uuid",
      "event_type": "FALSE_CLAIM",
      "worker_id": "worker_123",
      "severity": "CRITICAL",
      "message": "...",
      "sent_at": "2026-02-14T10:00:00",
      "acknowledged_at": null,
      "environment": "prd"
    }
  ],
  "count": 15,
  "page": 1
}
```

#### 2.3.3 Release Worker (Quarantine Management)
```
POST /watcher/release/{worker_id}

Body:
{
  "released_by": "mark@example.com",  # optional
  "reason": "False positive investigation complete"  # optional
}

Response:
{
  "success": true,
  "worker_id": "worker_123",
  "quarantine_status": "RELEASED",
  "released_at": "2026-02-14T10:30:00"
}
```

### 2.4 Retention Policy

**Implementation**: Cron job or scheduled task (future enhancement)

```sql
-- Run daily at 00:00
DELETE FROM watcher_alerts
WHERE sent_at < NOW() - INTERVAL '30 days';
```

Alternatively, implement in `wingman_watcher.py` as a daily cleanup task.

---

## 3. Severity Classification

### 3.1 Problem Statement

Current watcher treats all FALSE claims as equal severity:
- Cannot prioritize critical PRD violations vs. TEST warnings
- No distinction between destructive vs. non-destructive operations
- Alert fatigue from low-priority events

### 3.2 Solution: Risk-based Severity Scoring

**Severity Levels**:
- **CRITICAL**: FALSE claim in PRD + destructive operation
- **HIGH**: FALSE claim in PRD + non-destructive operation
- **MEDIUM**: FALSE claim in TEST environment
- **LOW**: Informational events (UNVERIFIABLE, metrics)

**Classification Algorithm**:

```python
def classify_severity(event: dict, environment: str) -> str:
    """
    Classify event severity based on environment and operation type.

    Args:
        event: Audit log entry with status, claim, worker_id
        environment: "test" or "prd"

    Returns:
        "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    """
    status = event.get("status", "")
    claim = (event.get("claim") or "").lower()

    # UNVERIFIABLE is always LOW (noisy, not actionable)
    if status == "UNVERIFIABLE":
        return "LOW"

    # FALSE claims in PRD
    if status == "FALSE" and environment == "prd":
        # Check for destructive operations
        destructive_keywords = [
            "docker stop", "docker rm", "docker kill", "docker down",
            "drop table", "truncate", "delete from",
            "alter table", "drop database",
            "rm -rf", "rm -f",
            "--force-delete", "--delete",
            "sudo shutdown", "sudo reboot"
        ]
        if any(kw in claim for kw in destructive_keywords):
            return "CRITICAL"
        else:
            return "HIGH"

    # FALSE claims in TEST
    if status == "FALSE" and environment == "test":
        return "MEDIUM"

    # Default
    return "LOW"
```

**Telegram Alert Formatting**:

```python
SEVERITY_EMOJI = {
    "CRITICAL": "🚨",
    "HIGH": "⚠️",
    "MEDIUM": "ℹ️",
    "LOW": "📝"
}

def format_alert(severity: str, event: dict) -> str:
    emoji = SEVERITY_EMOJI.get(severity, "❓")
    return f"{emoji} *{severity}*\n\n" + _render_message(event)
```

### 3.3 Environment Variables

```bash
# Deployment environment (used for severity classification)
DEPLOYMENT_ENV=test  # or "prd"
```

---

## 4. Automated Quarantine (Phase 1 - Safe Actions Only)

### 4.1 Problem Statement

Current watcher only sends alerts:
- Compromised workers can continue requesting approvals
- Manual intervention required to block malicious workers
- No automatic defensive measures

### 4.2 Solution: Redis Quarantine Set

**Key Principle**: Quarantine is **defensive, not corrective**:
- ✅ Block future approval requests from quarantined workers
- ❌ NO auto-rollback (too risky without approval)
- ❌ NO automatic container stop/removal
- ❌ NO automatic database changes

**Quarantine Trigger**:
- When: Severity = CRITICAL event detected
- Action: Add worker_id to Redis set `quarantined_workers`

**Redis Storage**:
- Key: `quarantined_workers` (Redis SET)
- Members: worker_id strings
- Additional key per worker: `quarantine:{worker_id}` (HASH) with metadata
  - `reason`: "FALSE claim detected: {claim}"
  - `quarantined_at`: ISO timestamp
  - `event_id`: Reference to audit log event
  - `environment`: "test" or "prd"

**Enforcement in `/approvals/request` Endpoint**:

```python
# In api_server.py, approvals_request() function
# Add quarantine check BEFORE risk assessment

def is_quarantined(worker_id: str) -> dict:
    """
    Check if worker is quarantined.

    Returns:
        {"quarantined": False} if not quarantined
        {"quarantined": True, "reason": "...", "quarantined_at": "..."} if quarantined
    """
    try:
        import redis
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=0,
            decode_responses=True
        )

        if r.sismember("quarantined_workers", worker_id):
            metadata = r.hgetall(f"quarantine:{worker_id}")
            return {
                "quarantined": True,
                "reason": metadata.get("reason", "Unknown"),
                "quarantined_at": metadata.get("quarantined_at", "Unknown")
            }
        return {"quarantined": False}
    except Exception as e:
        print(f"⚠️ Quarantine check failed: {e}")
        # Fail open (allow request) to avoid breaking service
        return {"quarantined": False}

# In approvals_request():
worker_id = str(data.get("worker_id", "unknown"))

# Check quarantine FIRST
quarantine_status = is_quarantined(worker_id)
if quarantine_status["quarantined"]:
    return jsonify({
        "needs_approval": False,
        "status": "AUTO_REJECTED",
        "reason": f"Worker quarantined: {quarantine_status['reason']}",
        "quarantined_at": quarantine_status["quarantined_at"],
        "message": "Contact Mark to release this worker via /release_worker command"
    }), 403
```

### 4.3 Release Mechanism

**Manual Release Only** (via Telegram or API):

```python
def release_worker(worker_id: str, released_by: str = None, reason: str = None) -> dict:
    """
    Release a quarantined worker.

    Args:
        worker_id: Worker to release
        released_by: Who released (for audit trail)
        reason: Why released (for audit trail)

    Returns:
        {"success": True/False, "message": "..."}
    """
    try:
        import redis
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=0,
            decode_responses=True
        )

        # Check if worker is quarantined
        if not r.sismember("quarantined_workers", worker_id):
            return {"success": False, "message": "Worker not quarantined"}

        # Remove from quarantine set
        r.srem("quarantined_workers", worker_id)

        # Delete quarantine metadata
        r.delete(f"quarantine:{worker_id}")

        # Log release event to audit trail
        from datetime import datetime
        release_event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "WORKER_RELEASED",
            "worker_id": worker_id,
            "released_by": released_by or "unknown",
            "reason": reason or "Manual release",
            "status": "RELEASED"
        }

        # TODO: Log to database (watcher_events table)

        return {
            "success": True,
            "message": f"Worker {worker_id} released from quarantine",
            "released_at": release_event["timestamp"]
        }
    except Exception as e:
        return {"success": False, "message": f"Release failed: {str(e)}"}
```

**Telegram Command** (add to telegram_bot.py):
```
/release_worker <worker_id>
```

Only Mark (authenticated) can release workers.

### 4.4 Audit Trail

All quarantine actions are logged to:
1. **Redis**: Metadata stored in `quarantine:{worker_id}` hash
2. **Postgres**: `watcher_alerts` table (with event_type = "WORKER_QUARANTINED")
3. **Audit log**: `data/claims_audit.jsonl` (existing file)

### 4.5 Environment Variables

```bash
# Enable/disable quarantine feature (default: enabled)
WINGMAN_QUARANTINE_ENABLED=1

# Redis connection
REDIS_HOST=redis
REDIS_PORT=6379
```

---

## 5. Implementation Plan

### Phase 1: Database Schema (30 min)
- Create migration `002_add_watcher_alerts.sql`
- Run migration in TEST environment
- Verify table creation

### Phase 2: Deduplication (2-3 hours)
- Add Redis client to `wingman_watcher.py`
- Implement fingerprint generation
- Add dedup check before sending Telegram alerts
- Implement hourly digest
- Test with duplicate events

### Phase 3: Persistence (2-3 hours)
- Modify `wingman_watcher.py` to insert alerts to Postgres
- Add API endpoints to `api_server.py`:
  - `POST /watcher/acknowledge/{alert_id}`
  - `GET /watcher/alerts`
  - `POST /watcher/release/{worker_id}`
- Test acknowledgment workflow
- Test alert history queries

### Phase 4: Severity Classification (2-3 hours)
- Implement `classify_severity()` function
- Update alert formatting with severity emojis
- Store severity in database
- Test all 4 severity levels

### Phase 5: Quarantine (2-3 hours)
- Implement `quarantine_worker()` in `wingman_watcher.py`
- Add quarantine check to `api_server.py` `/approvals/request`
- Implement `release_worker()` function
- Add API endpoint `POST /watcher/release/{worker_id}`
- Test quarantine → auto-reject → release flow

### Phase 6: Testing (2 hours)
- Trigger FALSE claim event → verify CRITICAL severity, alert sent, quarantine triggered
- Attempt approval from quarantined worker → verify auto-reject
- Release worker → verify approval allowed again
- Trigger same event 5 times → verify dedup (only 1 alert + digest)
- Check database → verify alert persistence and history query
- Verify severity classification for all 4 levels

### Phase 7: Documentation (1 hour)
- Update `VALIDATION_OPERATIONAL_GUIDE.md` with watcher section
- Update `AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md` with watcher procedures

---

## 6. Security Considerations

### 6.1 Fail-Safe Defaults

- **Quarantine check failure**: Fail open (allow request) to avoid breaking service
- **Redis unavailable**: Deduplication disabled, all alerts sent (prefer noise over missing critical alerts)
- **Postgres unavailable**: Alerts sent via Telegram, persistence skipped

### 6.2 Authentication

- **Watcher API endpoints**: Protected by same approval keys as other endpoints
- **Telegram commands**: Only Mark (authenticated via ALLOWED_USERS) can release workers

### 6.3 Rate Limiting

- **Digest messages**: Max 1 per hour (prevents spam)
- **Quarantine actions**: Logged to audit trail (prevents abuse)

---

## 7. Monitoring & Observability

### 7.1 Metrics (Future Enhancement)

- Alert volume by severity
- Deduplication ratio (suppressed / total)
- Quarantine events per day
- Acknowledgment rate

### 7.2 Alerting

- Critical alerts trigger Telegram push notifications (disable_notification=False)
- Digest messages use quiet notifications

---

## 8. Rollback Plan

If any feature causes issues:

1. **Disable feature via env var**:
   - Deduplication: Set `WINGMAN_WATCHER_DEDUP_TTL_SEC=0`
   - Quarantine: Set `WINGMAN_QUARANTINE_ENABLED=0`
   - Persistence: Set `WINGMAN_WATCHER_PERSISTENCE_ENABLED=0`

2. **Rollback migration** (if needed):
   ```sql
   DROP TABLE IF EXISTS watcher_alerts;
   ```

3. **Clear Redis quarantine** (emergency):
   ```bash
   redis-cli DEL quarantined_workers
   redis-cli KEYS "quarantine:*" | xargs redis-cli DEL
   ```

---

## 9. Future Enhancements (Out of Scope)

- Auto-rollback (requires approval workflow integration)
- Machine learning-based severity classification
- Integration with external incident management (PagerDuty, Opsgenie)
- Multi-channel notifications (Slack, email, SMS)
- Worker reputation scoring
- Anomaly detection (sudden spike in FALSE claims)

---

## Appendix A: Database Schema Reference

See migration file: `migrations/002_add_watcher_alerts.sql`

## Appendix B: API Endpoint Reference

See section 2.3 and 4.3 for detailed endpoint specifications.

## Appendix C: Redis Key Reference

| Key | Type | Purpose | TTL |
|-----|------|---------|-----|
| `watcher:dedup:{fingerprint}` | HASH | Deduplication tracking | 1 hour |
| `quarantined_workers` | SET | Active quarantines | None |
| `quarantine:{worker_id}` | HASH | Quarantine metadata | None |

---

**End of Design Document**
