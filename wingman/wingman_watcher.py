#!/usr/bin/env python3
"""
Wingman Watcher - Phase 4: Autonomous Monitoring (Enhanced)

Features:
- Vendor-agnostic notifications (Telegram via env-config, or webhook later)
- Persistent cursor (resume after restart)
- Redis-based deduplication with hourly digest
- Database persistence (Postgres) with acknowledgment workflow
- Severity classification (CRITICAL/HIGH/MEDIUM/LOW)
- Automated quarantine for compromised workers (Phase 1 - safe defensive actions only)
- Proactive approval queue monitoring (notify when new approvals arrive)
"""

import json
import time
import os
import requests
import shlex
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
LOG_PATH = os.getenv("WINGMAN_AUDIT_LOG", "data/claims_audit.jsonl")
STATE_PATH = os.getenv("WINGMAN_WATCHER_STATE", "data/watcher_state.json")
INCIDENTS_PATH = os.getenv("WINGMAN_WATCHER_INCIDENTS", "data/incidents.jsonl")
CHECK_INTERVAL = float(os.getenv("WINGMAN_WATCHER_INTERVAL_SEC", "2.0"))

# Environment
DEPLOYMENT_ENV = os.getenv("DEPLOYMENT_ENV", "test").lower()

# Database configuration (Postgres)
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "wingman")
DB_USER = os.getenv("DB_USER", "wingman")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Deduplication settings
DEDUP_TTL_SEC = int(os.getenv("WINGMAN_WATCHER_DEDUP_TTL_SEC", "3600"))  # 1 hour
DIGEST_INTERVAL_SEC = int(os.getenv("WINGMAN_WATCHER_DIGEST_INTERVAL_SEC", "3600"))  # 1 hour

# Quarantine settings
QUARANTINE_ENABLED = os.getenv("WINGMAN_QUARANTINE_ENABLED", "1").strip() == "1"

# Persistence settings
PERSISTENCE_ENABLED = os.getenv("WINGMAN_WATCHER_PERSISTENCE_ENABLED", "1").strip() == "1"

# Approval queue monitoring
APPROVAL_API_URL = os.getenv("WINGMAN_API_URL", "http://wingman-api:5000")
APPROVAL_READ_KEY = os.getenv("WINGMAN_APPROVAL_READ_KEY", "")
APPROVAL_CHECK_INTERVAL = int(os.getenv("WINGMAN_APPROVAL_CHECK_INTERVAL_SEC", "30"))
APPROVAL_NOTIFY_ENABLED = os.getenv("WINGMAN_APPROVAL_NOTIFY_ENABLED", "true").lower() in ("true", "1", "yes")

# Notifications (env only; no secrets in code)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
WEBHOOK_URL = os.getenv("WINGMAN_WEBHOOK_URL", "")
NOTIFY_BACKENDS = [s.strip().lower() for s in os.getenv("WINGMAN_NOTIFY_BACKENDS", "stdout,telegram").split(",") if s.strip()]

# Alert hygiene (legacy - now using DEDUP_TTL_SEC)
DEDUP_WINDOW_SEC = int(os.getenv("WINGMAN_WATCHER_DEDUP_SEC", "600"))

# Initialize connections
_redis_client = None
_db_conn = None

def get_redis():
    """Get Redis client (lazy initialization)."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            # Test connection
            _redis_client.ping()
            print(f"✅ Redis connected: {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
            _redis_client = None
    return _redis_client

def get_db():
    """Get Postgres connection (lazy initialization)."""
    global _db_conn
    if _db_conn is None or _db_conn.closed:
        try:
            import psycopg2
            _db_conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            print(f"✅ Postgres connected: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        except Exception as e:
            print(f"⚠️ Postgres connection failed: {e}")
            _db_conn = None
    return _db_conn

# Optional remediation hook (disabled by default)
# Example: WINGMAN_REMEDIATE_CMD="docker stop worker-{worker_id}"
REMEDIATE_MODE = os.getenv("WINGMAN_REMEDIATE_MODE", "disabled").lower()  # disabled|command
REMEDIATE_CMD = os.getenv("WINGMAN_REMEDIATE_CMD", "")

# ---------------------------------------------------------------------------
# Severity Classification
# ---------------------------------------------------------------------------

SEVERITY_EMOJI = {
    "CRITICAL": "🚨",
    "HIGH": "⚠️",
    "MEDIUM": "ℹ️",
    "LOW": "📝"
}

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


# ---------------------------------------------------------------------------
# Fingerprinting for Deduplication
# ---------------------------------------------------------------------------

def generate_fingerprint(event_type: str, worker_id: str, timestamp: int, window_sec: int = 3600) -> str:
    """
    Generate fingerprint for deduplication.

    Args:
        event_type: Type of event (FALSE_CLAIM, WORKER_QUARANTINED, etc.)
        worker_id: Worker identifier
        timestamp: Event timestamp (epoch seconds)
        window_sec: Window size for bucketing (default 3600 = 1 hour)

    Returns:
        16-character hex fingerprint
    """
    window_bucket = (timestamp // window_sec) * window_sec
    data = {
        "event_type": event_type,
        "worker_id": worker_id,
        "window": window_bucket
    }
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    return fingerprint[:16]


# ---------------------------------------------------------------------------
# Quarantine Management
# ---------------------------------------------------------------------------

def quarantine_worker(worker_id: str, reason: str, event: dict) -> bool:
    """
    Add worker to quarantine (Redis set).

    Args:
        worker_id: Worker to quarantine
        reason: Why quarantined
        event: Event that triggered quarantine

    Returns:
        True if quarantined successfully, False otherwise
    """
    if not QUARANTINE_ENABLED:
        return False

    redis_client = get_redis()
    if not redis_client:
        print(f"⚠️ Cannot quarantine {worker_id}: Redis unavailable")
        return False

    try:
        # Add to quarantine set
        redis_client.sadd("quarantined_workers", worker_id)

        # Store metadata
        redis_client.hset(f"quarantine:{worker_id}", mapping={
            "reason": reason,
            "quarantined_at": datetime.now().isoformat(),
            "event_id": event.get("timestamp", ""),
            "environment": DEPLOYMENT_ENV
        })

        print(f"🔒 Worker {worker_id} quarantined: {reason}")

        # Log quarantine event to database
        if PERSISTENCE_ENABLED:
            db = get_db()
            if db:
                try:
                    cursor = db.cursor()
                    cursor.execute("""
                        INSERT INTO watcher_alerts
                        (event_type, worker_id, severity, message, environment, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        "WORKER_QUARANTINED",
                        worker_id,
                        "CRITICAL",
                        reason,
                        DEPLOYMENT_ENV,
                        json.dumps(event)
                    ))
                    db.commit()
                    cursor.close()
                except Exception as e:
                    print(f"⚠️ Failed to log quarantine to database: {e}")
                    if db:
                        db.rollback()

        return True
    except Exception as e:
        print(f"⚠️ Failed to quarantine {worker_id}: {e}")
        return False


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
    redis_client = get_redis()
    if not redis_client:
        return {"success": False, "message": "Redis unavailable"}

    try:
        # Check if worker is quarantined
        if not redis_client.sismember("quarantined_workers", worker_id):
            return {"success": False, "message": "Worker not quarantined"}

        # Remove from quarantine set
        redis_client.srem("quarantined_workers", worker_id)

        # Delete quarantine metadata
        redis_client.delete(f"quarantine:{worker_id}")

        # Log release event
        release_timestamp = datetime.now().isoformat()
        print(f"🔓 Worker {worker_id} released from quarantine by {released_by or 'unknown'}")

        # Log to database
        if PERSISTENCE_ENABLED:
            db = get_db()
            if db:
                try:
                    cursor = db.cursor()
                    cursor.execute("""
                        INSERT INTO watcher_alerts
                        (event_type, worker_id, severity, message, environment, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        "WORKER_RELEASED",
                        worker_id,
                        "LOW",
                        f"Released by {released_by or 'unknown'}: {reason or 'No reason provided'}",
                        DEPLOYMENT_ENV,
                        json.dumps({"released_by": released_by, "reason": reason})
                    ))
                    db.commit()
                    cursor.close()
                except Exception as e:
                    print(f"⚠️ Failed to log release to database: {e}")
                    if db:
                        db.rollback()

        return {
            "success": True,
            "message": f"Worker {worker_id} released from quarantine",
            "released_at": release_timestamp
        }
    except Exception as e:
        return {"success": False, "message": f"Release failed: {str(e)}"}


# ---------------------------------------------------------------------------
# Legacy Incident Tracking (Kept for Backward Compatibility)
# ---------------------------------------------------------------------------

def _emit_incident(entry, verdict, severity):
    incident = {
        "ts": int(time.time()),
        "severity": severity,
        "verdict": verdict,
        "worker_id": entry.get("worker_id"),
        "claim": entry.get("claim"),
        "raw": entry,
    }
    try:
        os.makedirs(os.path.dirname(INCIDENTS_PATH), exist_ok=True)
        with open(INCIDENTS_PATH, "a") as f:
            f.write(json.dumps(incident) + "\n")
    except Exception as e:
        print(f"⚠️ Failed to write incident ledger: {e}")
    return incident


# ---------------------------------------------------------------------------
# Approval Queue Monitoring
# ---------------------------------------------------------------------------

def _fetch_pending_approvals():
    """Fetch pending approvals from the API."""
    try:
        headers = {}
        if APPROVAL_READ_KEY:
            headers["X-Wingman-Approval-Read-Key"] = APPROVAL_READ_KEY
        resp = requests.get(
            f"{APPROVAL_API_URL}/approvals/pending",
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("pending", [])
        else:
            print(f"⚠️ Approval API returned {resp.status_code}")
            return []
    except Exception as e:
        print(f"⚠️ Failed to fetch pending approvals: {e}")
        return []


def _format_approval_alert(approval):
    """Format a pending approval for Telegram notification."""
    req_id = approval.get("request_id", "unknown")[:8]
    risk = approval.get("risk_level", "UNKNOWN")
    worker = approval.get("worker_id", "unknown")
    task = approval.get("task_name", "No task name")
    created = approval.get("created_at", "")[:19] if approval.get("created_at") else ""
    
    emoji = "🔴" if risk == "HIGH" else "🟡" if risk == "MEDIUM" else "🟢"
    
    return (
        f"{emoji} *NEW APPROVAL REQUEST*\n\n"
        f"ID: `{req_id}`\n"
        f"Risk: `{risk}`\n"
        f"Worker: `{worker}`\n"
        f"Task: {task}\n"
        f"Created: {created}\n\n"
        f"Reply with /pending to see all, or /approve {req_id} to approve."
    )


def _send_approval_notification(approval):
    """Send Telegram notification for a new pending approval."""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Approval notification skipped (missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID).")
        return
    
    message = _format_approval_alert(approval)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_notification": False,  # Force push notifications
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('ok'):
                msg_id = result.get('result', {}).get('message_id', 'unknown')
                print(f"📨 Sent approval notification for {approval.get('request_id', 'unknown')[:8]} (msg_id: {msg_id})")
            else:
                print(f"⚠️ Telegram API error: {result.get('description', 'unknown')}")
        else:
            print(f"⚠️ Failed to send approval notification: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"⚠️ Failed to send approval notification: {e}")


def check_pending_approvals(state):
    """
    Check for new pending approvals and notify.
    Returns updated state.
    """
    if not APPROVAL_NOTIFY_ENABLED:
        return state
    
    notified_ids = set(state.get("notified_approval_ids", []))
    pending = _fetch_pending_approvals()
    
    new_approvals = []
    for approval in pending:
        req_id = approval.get("request_id")
        if req_id and req_id not in notified_ids:
            new_approvals.append(approval)
            notified_ids.add(req_id)
    
    # Notify for each new approval
    for approval in new_approvals:
        if "stdout" in NOTIFY_BACKENDS:
            print(f"🔔 New pending approval: {approval.get('request_id', 'unknown')[:8]} ({approval.get('risk_level', 'UNKNOWN')})")
        if "telegram" in NOTIFY_BACKENDS:
            _send_approval_notification(approval)
    
    # Prune notified_ids to only keep IDs still in pending (avoid unbounded growth)
    current_ids = {a.get("request_id") for a in pending if a.get("request_id")}
    notified_ids = notified_ids & current_ids  # Keep only IDs still pending
    
    state["notified_approval_ids"] = list(notified_ids)
    return state

def send_telegram_alert(message, severity="CRITICAL"):
    """Send immediate security alert to Mark"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Telegram alert skipped (missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID).")
        return

    emoji = SEVERITY_EMOJI.get(severity, "❓")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": f"{emoji} *WINGMAN {severity} ALERT*\n\n{message}",
        "parse_mode": "Markdown",
        "disable_notification": False  # Force push notifications
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"📨 Sent {severity} alert to Telegram")
        else:
            print(f"⚠️ Failed to send Telegram alert: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"⚠️ Failed to send Telegram alert: {e}")

def send_webhook_alert(payload):
    """Send a vendor-agnostic webhook (Slack/Teams/custom gateway can sit behind this)."""
    if not WEBHOOK_URL:
        print("⚠️ Webhook alert skipped (missing WINGMAN_WEBHOOK_URL).")
        return
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Failed to send webhook alert: {e}")

def _render_message(incident):
    wid = incident.get("worker_id")
    sev = incident.get("severity")
    verdict = incident.get("verdict")
    claim = incident.get("claim", "")
    env = DEPLOYMENT_ENV.upper()
    return f"Severity: `{sev}`\nEnvironment: `{env}`\nVerdict: `{verdict}`\nWorker: `{wid}`\nClaim: \"{claim}\""


# ---------------------------------------------------------------------------
# Deduplication Logic
# ---------------------------------------------------------------------------

def should_send_alert(event: dict, severity: str) -> dict:
    """
    Check if alert should be sent (deduplication via Redis).

    Args:
        event: Event dict with worker_id, claim, status, timestamp
        severity: Severity level (CRITICAL/HIGH/MEDIUM/LOW)

    Returns:
        {
            "should_send": True/False,
            "fingerprint": "...",
            "count": N  # Number of occurrences in current window
        }
    """
    redis_client = get_redis()
    if not redis_client or DEDUP_TTL_SEC == 0:
        # Deduplication disabled or Redis unavailable
        return {"should_send": True, "fingerprint": None, "count": 1}

    try:
        event_type = f"{event.get('status', 'UNKNOWN')}_CLAIM"
        worker_id = event.get("worker_id", "unknown")
        timestamp = int(time.time())

        # Generate fingerprint
        fingerprint = generate_fingerprint(event_type, worker_id, timestamp, window_sec=DEDUP_TTL_SEC)

        # Check if already seen
        redis_key = f"watcher:dedup:{fingerprint}"
        existing = redis_client.get(redis_key)

        if existing:
            # Already seen - increment count and skip alert
            data = json.loads(existing)
            data["count"] += 1
            data["last_seen"] = timestamp
            redis_client.set(redis_key, json.dumps(data), ex=DEDUP_TTL_SEC)

            print(f"🔕 Alert suppressed (dedup): {event_type} for {worker_id} (count: {data['count']})")
            return {"should_send": False, "fingerprint": fingerprint, "count": data["count"]}
        else:
            # First occurrence - send alert
            data = {
                "count": 1,
                "first_seen": timestamp,
                "last_seen": timestamp,
                "event_type": event_type,
                "worker_id": worker_id,
                "severity": severity
            }
            redis_client.set(redis_key, json.dumps(data), ex=DEDUP_TTL_SEC)

            return {"should_send": True, "fingerprint": fingerprint, "count": 1}
    except Exception as e:
        print(f"⚠️ Deduplication check failed: {e}")
        # Fail open - send alert
        return {"should_send": True, "fingerprint": None, "count": 1}


# ---------------------------------------------------------------------------
# Database Persistence
# ---------------------------------------------------------------------------

def persist_alert(event: dict, severity: str, fingerprint: str = None) -> Optional[str]:
    """
    Persist alert to Postgres database.

    Args:
        event: Event dict
        severity: Severity level
        fingerprint: Dedup fingerprint (optional)

    Returns:
        alert_id (UUID) if successful, None otherwise
    """
    if not PERSISTENCE_ENABLED:
        return None

    db = get_db()
    if not db:
        print("⚠️ Cannot persist alert: Database unavailable")
        return None

    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO watcher_alerts
            (event_type, worker_id, severity, message, fingerprint, environment, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING alert_id
        """, (
            f"{event.get('status', 'UNKNOWN')}_CLAIM",
            event.get("worker_id"),
            severity,
            event.get("claim", "")[:500],  # Truncate long claims
            fingerprint,
            DEPLOYMENT_ENV,
            json.dumps(event)
        ))
        alert_id = cursor.fetchone()[0]
        db.commit()
        cursor.close()

        print(f"💾 Alert persisted to database: {alert_id}")
        return str(alert_id)
    except Exception as e:
        print(f"⚠️ Failed to persist alert to database: {e}")
        if db:
            db.rollback()
        return None

def _maybe_remediate(incident):
    if REMEDIATE_MODE != "command":
        return
    if not REMEDIATE_CMD:
        print("⚠️ Remediation mode enabled but WINGMAN_REMEDIATE_CMD is empty.")
        return
    # Substitute placeholders safely; no shell execution.
    cmd = REMEDIATE_CMD.format(
        worker_id=str(incident.get("worker_id", "")),
        verdict=str(incident.get("verdict", "")),
        severity=str(incident.get("severity", "")),
    )
    args = shlex.split(cmd)
    try:
        subprocess.run(args, timeout=30, check=False)
    except Exception as e:
        print(f"⚠️ Remediation command failed: {e}")

def trigger_incident_response(incident, event: dict):
    """
    Autonomous response to a FALSE claim.

    Enhanced with:
    - Severity classification
    - Deduplication
    - Database persistence
    - Automated quarantine

    Args:
        incident: Legacy incident dict (for backward compatibility)
        event: Full event dict from audit log
    """
    # Classify severity
    severity = classify_severity(event, DEPLOYMENT_ENV)
    incident["severity"] = severity  # Update incident dict

    # Check deduplication
    dedup_result = should_send_alert(event, severity)
    fingerprint = dedup_result.get("fingerprint")

    # Always persist to database (even if deduplicated)
    alert_id = persist_alert(event, severity, fingerprint)

    # Send alert only if not deduplicated
    if dedup_result["should_send"]:
        msg = _render_message(incident)

        if "stdout" in NOTIFY_BACKENDS:
            print(f"🚨 WINGMAN INCIDENT\n{msg}")

        if "telegram" in NOTIFY_BACKENDS:
            send_telegram_alert(msg, severity=severity)

        if "webhook" in NOTIFY_BACKENDS:
            send_webhook_alert({"type": "wingman_incident", "incident": incident})

    # Quarantine worker if CRITICAL
    if severity == "CRITICAL" and QUARANTINE_ENABLED:
        worker_id = event.get("worker_id")
        claim = event.get("claim", "")[:100]  # Truncate for Redis
        reason = f"FALSE claim detected: {claim}"
        quarantine_worker(worker_id, reason, event)

    # Legacy remediation (usually disabled)
    _maybe_remediate(incident)

def _load_state():
    try:
        if not os.path.exists(STATE_PATH):
            return {"offset": 0, "recent_alerts": {}}
        with open(STATE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"offset": 0, "recent_alerts": {}}

def _save_state(state):
    try:
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        with open(STATE_PATH, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"⚠️ Failed to persist watcher state: {e}")

def _should_alert(state, entry):
    """
    De-dupe alerts by (worker_id, claim, status) for a cooldown window.
    """
    wid = str(entry.get("worker_id", "unknown"))
    claim = str(entry.get("claim", ""))
    status = str(entry.get("status", ""))
    key = f"{wid}|{status}|{claim}"
    now = int(time.time())

    recent = state.get("recent_alerts", {})
    last = int(recent.get(key, 0)) if isinstance(recent.get(key, 0), (int, float, str)) else 0
    try:
        last = int(last)
    except Exception:
        last = 0

    if now - last < DEDUP_WINDOW_SEC:
        return False

    # update last-seen
    recent[key] = now
    # prune old keys
    cutoff = now - DEDUP_WINDOW_SEC
    state["recent_alerts"] = {k: v for k, v in recent.items() if int(v) >= cutoff}
    return True

def send_hourly_digest():
    """
    Send hourly digest of suppressed alerts.
    """
    redis_client = get_redis()
    if not redis_client:
        return

    try:
        # Scan for all dedup keys
        digest_items = []
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match="watcher:dedup:*", count=100)
            for key in keys:
                data_str = redis_client.get(key)
                if data_str:
                    data = json.loads(data_str)
                    if data.get("count", 0) > 1:  # Only include suppressed alerts
                        digest_items.append(data)
            if cursor == 0:
                break

        if not digest_items:
            return  # No suppressed alerts

        # Build digest message
        digest_msg = "📊 *Watcher Digest (last hour)*\n\n*Suppressed duplicates:*\n"
        total_suppressed = 0

        # Group by severity
        by_severity = {}
        for item in digest_items:
            severity = item.get("severity", "UNKNOWN")
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(item)

        # Format by severity (CRITICAL first)
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if severity in by_severity:
                digest_msg += f"\n*{severity}:*\n"
                for item in by_severity[severity]:
                    worker_id = item.get("worker_id", "unknown")
                    count = item.get("count", 0)
                    event_type = item.get("event_type", "UNKNOWN")
                    digest_msg += f"  • {event_type} - Worker `{worker_id}` ({count - 1} suppressed)\n"
                    total_suppressed += (count - 1)

        digest_msg += f"\n*Total alerts suppressed:* {total_suppressed}"

        # Send to Telegram
        if "telegram" in NOTIFY_BACKENDS and TELEGRAM_TOKEN and CHAT_ID:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {
                "chat_id": CHAT_ID,
                "text": digest_msg,
                "parse_mode": "Markdown",
                "disable_notification": True  # Quiet notification for digest
            }
            try:
                requests.post(url, json=payload, timeout=10)
                print(f"📨 Sent hourly digest ({total_suppressed} suppressed alerts)")
            except Exception as e:
                print(f"⚠️ Failed to send digest: {e}")

    except Exception as e:
        print(f"⚠️ Failed to generate digest: {e}")


def watch_logs():
    print(f"👀 WINGMAN WATCHER: Monitoring {LOG_PATH} (state: {STATE_PATH})...")
    print(f"🔧 Environment: {DEPLOYMENT_ENV.upper()}")
    print(f"🔧 Deduplication: {'Enabled' if DEDUP_TTL_SEC > 0 else 'Disabled'} (TTL: {DEDUP_TTL_SEC}s)")
    print(f"🔧 Persistence: {'Enabled' if PERSISTENCE_ENABLED else 'Disabled'}")
    print(f"🔧 Quarantine: {'Enabled' if QUARANTINE_ENABLED else 'Disabled'}")

    if APPROVAL_NOTIFY_ENABLED:
        print(f"📋 Approval notifications enabled (checking every {APPROVAL_CHECK_INTERVAL}s)")

    # Initialize connections
    get_redis()
    get_db()

    state = _load_state()
    last_pos = int(state.get("offset", 0) or 0)
    last_approval_check = 0
    last_digest = 0

    while True:
        now = time.time()

        # Send hourly digest
        if DEDUP_TTL_SEC > 0 and (now - last_digest) >= DIGEST_INTERVAL_SEC:
            send_hourly_digest()
            last_digest = now

        # Check pending approvals periodically
        if APPROVAL_NOTIFY_ENABLED and (now - last_approval_check) >= APPROVAL_CHECK_INTERVAL:
            state = check_pending_approvals(state)
            last_approval_check = now
            _save_state(state)

        # Check claims audit log
        if not os.path.exists(LOG_PATH):
            time.sleep(CHECK_INTERVAL)
            continue

        with open(LOG_PATH, 'r') as f:
            f.seek(last_pos)
            lines = f.readlines()
            last_pos = f.tell()
            state["offset"] = last_pos

            for line in lines:
                if not line.strip(): continue
                try:
                    entry = json.loads(line)
                    status = entry.get("status")

                    if status == "FALSE":
                        # Legacy dedup check (now superseded by Redis dedup in trigger_incident_response)
                        # Keep for backward compatibility with old state format
                        if _should_alert(state, entry):
                            print(f"🚨 ALERT: False claim detected for Worker {entry.get('worker_id')}")
                            # Use actual severity classification instead of hardcoded
                            severity = classify_severity(entry, DEPLOYMENT_ENV)
                            incident = _emit_incident(entry, verdict="FALSE", severity=severity)
                            trigger_incident_response(incident, entry)
                    elif status == "UNVERIFIABLE":
                        # Optional: UNVERIFIABLE can be noisy; still log, but don't alert by default
                        print(f"⚠️ WARNING: Unverifiable claim for Worker {entry.get('worker_id')}")
                        # Still write to incident ledger for later reporting
                        incident = _emit_incident(entry, verdict="UNVERIFIABLE", severity="LOW")
                        # Persist but don't send alert
                        persist_alert(entry, "LOW", None)

                except json.JSONDecodeError:
                    continue

            _save_state(state)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    watch_logs()

