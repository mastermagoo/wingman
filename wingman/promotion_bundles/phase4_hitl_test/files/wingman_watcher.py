#!/usr/bin/env python3
"""
Wingman Watcher - Phase 4: Autonomous Monitoring (Product-grade v1)

Design goals:
- Vendor-agnostic notifications (Telegram via env-config, or webhook later)
- Persistent cursor (resume after restart)
- De-dupe / cooldown to prevent alert storms
- Action hooks (notify-only by default; pluggable remediation later)
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

def send_telegram_alert(message):
    """Send immediate security alert to Mark"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Telegram alert skipped (missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID).")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": f"🚨 *WINGMAN SECURITY ALERT*\n\n{message}",
        "parse_mode": "Markdown"
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
    state = _load_state()
    last_pos = int(state.get("offset", 0) or 0)

    while True:
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

