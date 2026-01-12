#!/usr/bin/env python3
"""
Wingman Watcher - Phase 4: Autonomous Monitoring (Product-grade v1)

Design goals:
- Vendor-agnostic notifications (Telegram via env-config, or webhook later)
- Persistent cursor (resume after restart)
- De-dupe / cooldown to prevent alert storms
- Action hooks (notify-only by default; pluggable remediation later)
- Proactive approval queue monitoring (notify when new approvals arrive)
"""

import json
import time
import os
import requests
import shlex
import subprocess
from pathlib import Path

# Configuration
LOG_PATH = os.getenv("WINGMAN_AUDIT_LOG", "data/claims_audit.jsonl")
STATE_PATH = os.getenv("WINGMAN_WATCHER_STATE", "data/watcher_state.json")
INCIDENTS_PATH = os.getenv("WINGMAN_WATCHER_INCIDENTS", "data/incidents.jsonl")
CHECK_INTERVAL = float(os.getenv("WINGMAN_WATCHER_INTERVAL_SEC", "2.0"))

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

# Alert hygiene
DEDUP_WINDOW_SEC = int(os.getenv("WINGMAN_WATCHER_DEDUP_SEC", "600"))

# Optional remediation hook (disabled by default)
# Example: WINGMAN_REMEDIATE_CMD="docker stop worker-{worker_id}"
REMEDIATE_MODE = os.getenv("WINGMAN_REMEDIATE_MODE", "disabled").lower()  # disabled|command
REMEDIATE_CMD = os.getenv("WINGMAN_REMEDIATE_CMD", "")

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

def send_telegram_alert(message):
    """Send immediate security alert to Mark"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Telegram alert skipped (missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID).")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": f"🚨 *WINGMAN SECURITY ALERT*\n\n{message}",
        "parse_mode": "Markdown",
        "disable_notification": False  # Force push notifications
    }
    try:
        requests.post(url, json=payload, timeout=10)
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
    return f"Severity: `{sev}`\nVerdict: `{verdict}`\nWorker: `{wid}`\nClaim: \"{claim}\""

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

def trigger_incident_response(incident):
    """Autonomous response to a FALSE claim"""
    msg = _render_message(incident)
    if "stdout" in NOTIFY_BACKENDS:
        print(f"🚨 WINGMAN INCIDENT\n{msg}")
    if "telegram" in NOTIFY_BACKENDS:
        send_telegram_alert(msg)
    if "webhook" in NOTIFY_BACKENDS:
        send_webhook_alert({"type": "wingman_incident", "incident": incident})

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

def watch_logs():
    print(f"👀 WINGMAN WATCHER: Monitoring {LOG_PATH} (state: {STATE_PATH})...")
    if APPROVAL_NOTIFY_ENABLED:
        print(f"📋 Approval notifications enabled (checking every {APPROVAL_CHECK_INTERVAL}s)")
    state = _load_state()
    last_pos = int(state.get("offset", 0) or 0)
    last_approval_check = 0

    while True:
        now = time.time()
        
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
                        if _should_alert(state, entry):
                            print(f"🚨 ALERT: False claim detected for Worker {entry.get('worker_id')}")
                            incident = _emit_incident(entry, verdict="FALSE", severity="CRITICAL")
                            trigger_incident_response(incident)
                    elif status == "UNVERIFIABLE":
                        # Optional: UNVERIFIABLE can be noisy; still log, but don't alert by default
                        print(f"⚠️ WARNING: Unverifiable claim for Worker {entry.get('worker_id')}")
                        # Still write to incident ledger for later reporting
                        _emit_incident(entry, verdict="UNVERIFIABLE", severity="WARN")
                    
                except json.JSONDecodeError:
                    continue

            _save_state(state)
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    watch_logs()

