# Wingman Operations Guide

**Status**: CURRENT
**Last Updated**: 2026-02-14
**Version**: 1.1
**Scope**: Wingman operations/runbooks (DEV/TEST/PRD)

> **Audience**: System operators, DevOps, and anyone running Wingman day-to-day

---

## Prerequisites: Docker Wrapper Setup (MANDATORY)

**REQUIRED**: All docker/compose commands in this runbook assume the Docker wrapper is in effect.

The Docker wrapper (`tools/docker-wrapper.sh`) blocks destructive Docker commands unless they are executed via the Wingman Execution Gateway with proper approval. This is a **mandatory** infrastructure-level protection.

### One-Time Setup (per shell session):

```bash
# Add wrapper to PATH so 'docker' resolves to wrapper first
export PATH="/Volumes/Data/ai_projects/wingman-system/wingman/tools:$PATH"

# Verify wrapper is active
which docker
# Expected output: /Volumes/Data/ai_projects/wingman-system/wingman/tools/docker

# If real docker not in wrapper's search path, set DOCKER_BIN
export DOCKER_BIN="/Users/kermit/.orbstack/bin/docker"
```

### Permanent Setup (recommended for daily use):

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
# Wingman Docker Wrapper (mandatory for all Wingman operations)
export PATH="/Volumes/Data/ai_projects/wingman-system/wingman/tools:$PATH"
export DOCKER_BIN="/Users/kermit/.orbstack/bin/docker"
```

Then reload your shell:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

### Verify Wrapper is Active:

```bash
# Test 1: Check which docker binary is being used
which docker
# Expected: /Volumes/Data/ai_projects/wingman-system/wingman/tools/docker

# Test 2: Try a safe command (should work)
docker ps

# Test 3: Try a destructive command (should be blocked)
docker stop test-container
# Expected: ❌ BLOCKED: Destructive docker command requires Wingman approval
```

### CRITICAL: Bypass Prevention

**DO NOT** bypass the wrapper using absolute paths:
```bash
# ❌ PROHIBITED - bypasses wrapper
/usr/bin/docker stop container

# ✅ CORRECT - uses wrapper
docker stop container  # (will be blocked and require approval)
```

All destructive Docker operations must:
1. Go through the wrapper (blocked at shell level)
2. Be submitted as approval request to Wingman API
3. Be approved via Telegram
4. Be executed via Execution Gateway with capability token

See: [Docker Wrapper Audit Report](DOCKER_WRAPPER_AUDIT.md) for implementation details.

---

## Wingman 5 (Phase 5) — Deployment Plan

- **Secure deployment plan (Phase 5)**: [PHASE_5_SECURE_DEPLOYMENT.md](../99-archive/paul-wingman/PHASE_5_SECURE_DEPLOYMENT.md)
- **Docker wrapper enforcement audit**: [DOCKER_WRAPPER_AUDIT.md](DOCKER_WRAPPER_AUDIT.md)

---


## Phase R0 (Execution Gateway) — TEST Workflow & Validation

**Goal**: ensure privileged execution (Docker access) is **non-bypassable**: only the Execution Gateway can touch Docker; all other containers cannot.

### What’s enforced (TEST)

- **Only** `execution-gateway` mounts `/var/run/docker.sock`
- Non-gateway containers must have:
  - **no** `/var/run/docker.sock`
  - **no** `DOCKER_HOST` env var
  - **no** access to OrbStack socket paths (e.g. `/Users/kermit/.orbstack/run/docker.sock`)

### How to validate (TEST)

Run these from repo root (`/Volumes/Data/ai_projects/wingman-system`):

```bash
# 1) Bring up TEST
docker compose -f wingman/docker-compose.yml -p wingman-test up -d --build

# 2) Health
curl -sS http://127.0.0.1:8101/health

# 3) Privilege boundary proof (must PASS)
./tools/verify_test_privilege_removal.sh
```


### Tests (local)

If you need to run the gateway unit tests locally on macOS:

```bash
cd /Volumes/Data/ai_projects/wingman-system
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r wingman/api_requirements.txt pytest
python3 -m pytest -q wingman/tests/test_gateway.py
```

### If it fails (how to fix)

- **FAIL: `<svc>` has DOCKER_HOST set**
  - Fix: remove `DOCKER_HOST` from that service’s `environment:` in `wingman/docker-compose.yml` and rebuild TEST.
- **FAIL: `<svc>` can see `/Users/kermit/.orbstack/.../docker.sock`**
  - Fix: remove any bind-mount that exposes home directories into that container.
- **FAIL: `<svc>` has `/var/run/docker.sock`**
  - Fix: ensure only `execution-gateway` has the socket mount in `wingman/docker-compose.yml`.

### Extra security measures currently in place

- **Postgres execution audit (append-only)**: gateway writes to `execution_audit` table when `AUDIT_STORAGE=postgres` (TEST).
- **Consensus risk (advisory)**: approvals use multi-source consensus when `WINGMAN_CONSENSUS_ENABLED=1` (TEST default).
- **Allowlist hardening**: gateway blocks shell operators like `&&`, `|`, `;`, redirections, etc. (prevents injection).
- **CI tests + coverage gate**: `.github/workflows/wingman-tests.yml` runs `pytest` + `--cov-fail-under=95`.

- **GitHub Action gate**: `.github/workflows/secret-scan.yml` blocks committing `.env*` and common secret patterns (server-side).
- **Local pre-commit**: `.githooks/pre-commit` runs repo secret scanning before commit (client-side; CI still enforces).
- **Capability tokens**: short-lived JWTs (TEST) minted only for approved requests, then executed via the gateway.

---


## Quick Reference

### Health Checks

```bash
# PRD
curl -s http://127.0.0.1:5001/health | jq

# TEST
curl -s http://127.0.0.1:8101/health | jq
```

### Stack Management

```bash
# View running containers
docker ps --filter "name=wingman"

# PRD stack status
docker compose -f wingman/docker-compose.prd.yml -p wingman-prd ps

# TEST stack status
docker compose -f wingman/docker-compose.yml -p wingman-test ps
```

---

## Environment Details

| Environment | Compose File | Project Name | API Port |
|-------------|--------------|--------------|----------|
| TEST | `docker-compose.yml` | `wingman-test` | 8101 |
| PRD | `docker-compose.prd.yml` | `wingman-prd` | 5001 |

---

## Starting & Stopping

### Start PRD Stack

```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

# Ensure .env.prd exists with secrets
# cp env.prd.example .env.prd && vim .env.prd

docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d
```

### Start TEST Stack

```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

docker compose -f docker-compose.yml -p wingman-test up -d
```

### Stop Stacks

```bash
# Stop PRD (keeps volumes)
docker compose -f docker-compose.prd.yml -p wingman-prd down

# Stop TEST
docker compose -f docker-compose.yml -p wingman-test down

# Stop and remove volumes (DATA LOSS!)
docker compose -f docker-compose.prd.yml -p wingman-prd down -v
```

### Restart Individual Services

```bash
# Restart API only
docker compose -f docker-compose.prd.yml -p wingman-prd restart api

# Restart bot only
docker compose -f docker-compose.prd.yml -p wingman-prd restart telegram-bot
```

---

## Viewing Logs

### API Logs

```bash
# PRD
docker logs wingman-api-prd --tail 100 -f

# TEST
docker logs wingman-api-test --tail 100 -f
```

### Bot Logs

```bash
docker logs wingman-telegram-prd --tail 100 -f
```

### All Logs

```bash
docker compose -f docker-compose.prd.yml -p wingman-prd logs -f
```

### Audit Log

```bash
# View claims audit (Phase 3)
tail -f /Volumes/Data/ai_projects/wingman-system/wingman/data/prd/claims_audit.jsonl
```

---

## Validation Commands

### Validate Compose Config (No Secrets Printed)

```bash
# PRD
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd config --quiet

# TEST
docker compose -f docker-compose.yml -p wingman-test config --quiet
```

### Test API Endpoints

```bash
# Health
curl -s http://127.0.0.1:5001/health | jq

# Root (shows all endpoints)
curl -s http://127.0.0.1:5001/ | jq

# Phase 2: Check instruction
curl -s -X POST http://127.0.0.1:5001/check \
  -H "Content-Type: application/json" \
  -d '{"instruction": "DELIVERABLES: x\nSUCCESS_CRITERIA: x\nBOUNDARIES: x\nDEPENDENCIES: x\nMITIGATION: x\nTEST_PROCESS: x\nTEST_RESULTS_FORMAT: x\nRESOURCE_REQUIREMENTS: x\nRISK_ASSESSMENT: x\nQUALITY_METRICS: x"}' | jq

# Phase 3: Verify claim
curl -s -X POST http://127.0.0.1:5001/verify \
  -H "Content-Type: application/json" \
  -d '{"claim": "Process postgres is running"}' | jq

# Phase 4: List pending approvals
curl -s http://127.0.0.1:5001/approvals/pending | jq
```

### Test Telegram Bot

```bash
# Inside bot container
docker compose -f docker-compose.prd.yml -p wingman-prd exec -T telegram-bot \
  python -c "import os,requests; t=os.environ.get('BOT_TOKEN'); assert t; r=requests.get(f'https://api.telegram.org/bot{t}/getMe',timeout=10); print('ok' if r.ok else r.status_code)"
```

---

## Database Operations

### Check Database Health

```bash
docker exec wingman-postgres-prd pg_isready -U wingman_prd
```

### Connect to Database

```bash
docker exec -it wingman-postgres-prd psql -U wingman_prd -d wingman_prd
```

### Backup Database

```bash
docker exec wingman-postgres-prd pg_dump -U wingman_prd wingman_prd > backup_$(date +%Y%m%d).sql
```

### View Verification Stats (SQL)

```sql
-- In psql
SELECT verdict, COUNT(*) as count 
FROM verification_logs 
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY verdict;
```

---

## Approval Management

### Via API

```bash
# List pending
curl -s http://127.0.0.1:5001/approvals/pending | jq

# Get specific approval
curl -s http://127.0.0.1:5001/approvals/<request_id> | jq

# Approve
curl -s -X POST http://127.0.0.1:5001/approvals/<request_id>/approve \
  -H "Content-Type: application/json" \
  -d '{"decided_by": "mark", "note": "approved via API"}' | jq

# Reject
curl -s -X POST http://127.0.0.1:5001/approvals/<request_id>/reject \
  -H "Content-Type: application/json" \
  -d '{"decided_by": "mark", "note": "rejected - too risky"}' | jq
```

### Via Telegram

Send to the Wingman bot:
- `/pending` — List pending approvals
- `/approve <id>` — Approve request
- `/reject <id>` — Reject request
- `/status` — System status

---

## Troubleshooting

### API Not Responding

```bash
# 1. Check if container is running
docker ps --filter "name=wingman-api-prd"

# 2. Check container logs
docker logs wingman-api-prd --tail 50

# 3. Check if port is bound correctly
lsof -i :5001

# 4. Restart API
docker compose -f docker-compose.prd.yml -p wingman-prd restart api
```

### Port 5000 Conflict (macOS)

macOS uses port 5000 for AirPlay Receiver. PRD uses 5001 instead.

```bash
# Verify what's on 5000
lsof -i :5000
# Shows: ControlCe (AirPlay)

# Use 5001 for Wingman PRD
curl http://127.0.0.1:5001/health
```

### Database Connection Failed

```bash
# Check PostgreSQL container
docker logs wingman-postgres-prd --tail 20

# Check if ready
docker exec wingman-postgres-prd pg_isready -U wingman_prd

# Restart database
docker compose -f docker-compose.prd.yml -p wingman-prd restart postgres

# Wait for it, then restart API
sleep 10
docker compose -f docker-compose.prd.yml -p wingman-prd restart api
```

### Telegram Bot Not Responding

```bash
# Check bot logs
docker logs wingman-telegram-prd --tail 50

# Verify token works
docker exec wingman-telegram-prd python -c "
import os, requests
token = os.environ.get('BOT_TOKEN')
r = requests.get(f'https://api.telegram.org/bot{token}/getMe')
print(r.json())
"

# Restart bot
docker compose -f docker-compose.prd.yml -p wingman-prd restart telegram-bot
```

### Claims Not Being Verified

```bash
# Check audit log exists
ls -la data/prd/claims_audit.jsonl

# Check recent claims
tail -5 data/prd/claims_audit.jsonl | jq

# Test verification manually
curl -s -X POST http://127.0.0.1:5001/verify \
  -H "Content-Type: application/json" \
  -d '{"claim": "Created file /tmp/test.txt"}' | jq
```

---

## Disaster Recovery

### Full Cold Start (TEST)

```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

# Stop and remove
docker compose -f docker-compose.yml -p wingman-test down --remove-orphans

# Cold start
docker compose -f docker-compose.yml -p wingman-test up -d --build

# Validate
curl -s http://127.0.0.1:8101/health
```

### Full Cold Start (PRD)

```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

# Stop and remove
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd down --remove-orphans

# Cold start
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d --build

# Validate
curl -s http://127.0.0.1:5001/health
```

### Data Recovery

```bash
# Restore database from backup
docker exec -i wingman-postgres-prd psql -U wingman_prd wingman_prd < backup_20260106.sql

# Restart API to reconnect
docker compose -f docker-compose.prd.yml -p wingman-prd restart api
```

---

## Monitoring

### What to Monitor

| Metric | Check | Alert If |
|--------|-------|----------|
| API Health | `GET /health` | status != "healthy" |
| Response Time | `GET /health` timing | > 1 second |
| Pending Approvals | `GET /approvals/pending` | count > 10 |
| FALSE Verdicts | Check audit log | Any FALSE in PRD |
| Container Status | `docker ps` | Any container down |
| Disk Space | `df -h` | < 10% free |

### Simple Monitoring Script

```bash
#!/bin/bash
# save as: wingman_check.sh

API_URL="http://127.0.0.1:5001"

# Check health
health=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
if [ "$health" != "200" ]; then
    echo "ALERT: Wingman API unhealthy (HTTP $health)"
    exit 1
fi

# Check for pending approvals
pending=$(curl -s "$API_URL/approvals/pending" | jq '.count')
if [ "$pending" -gt 5 ]; then
    echo "WARNING: $pending pending approvals"
fi

echo "OK: Wingman healthy, $pending pending approvals"
```

---

## Security Operations

### Rotate Bot Token

1. Create new bot token via BotFather
2. Update `.env.prd` with new `BOT_TOKEN`
3. Restart bot: `docker compose ... restart telegram-bot`

### Rotate Database Password

1. Update PostgreSQL user password
2. Update `.env.prd` with new `DB_PASSWORD`
3. Restart all services: `docker compose ... down && docker compose ... up -d`

### Audit Log Rotation

```bash
# Archive old audit log
mv data/prd/claims_audit.jsonl data/prd/claims_audit_$(date +%Y%m%d).jsonl

# New log will be created automatically on next claim
```

---

## Useful Aliases

Add to your `~/.zshrc`:

```bash
# Wingman shortcuts
alias wm-prd='docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.prd.yml -p wingman-prd --env-file /Volumes/Data/ai_projects/wingman-system/wingman/.env.prd'
alias wm-test='docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml -p wingman-test'

# Usage:
# wm-prd ps
# wm-prd logs -f api
# wm-prd restart api
# wm-test up -d
```

---

## Phase 4 Enhanced: Watcher Service Operations

**Version**: 2.0
**Features**: Deduplication, Persistence, Severity Classification, Automated Quarantine

### Watcher Service Overview

The Wingman Watcher service (`wingman_watcher.py`) provides autonomous security monitoring with:

- **Real-time monitoring**: Watches `data/claims_audit.jsonl` for FALSE claims
- **Deduplication**: Redis-based fingerprinting prevents alert spam
- **Persistence**: All alerts stored in Postgres with 30-day retention
- **Severity classification**: CRITICAL/HIGH/MEDIUM/LOW based on environment and operation
- **Automated quarantine**: Blocks compromised workers from approval flow
- **Telegram alerts**: Real-time notifications with severity indicators

### Daily Operations

#### 1. Check Watcher Status

```bash
# TEST environment
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test ps wingman-watcher

# PRD environment
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.prd.yml \
  -p wingman-prd --env-file /Volumes/Data/ai_projects/wingman-system/wingman/.env.prd \
  ps wingman-watcher
```

#### 2. Monitor Watcher Logs

```bash
# TEST
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test logs -f wingman-watcher

# Look for healthy startup messages:
# ✅ Redis connected: redis:6379
# ✅ Postgres connected: postgres:5432/wingman
# 👀 WINGMAN WATCHER: Monitoring data/claims_audit.jsonl
# 🔧 Environment: TEST
# 🔧 Deduplication: Enabled (TTL: 3600s)
# 🔧 Persistence: Enabled
# 🔧 Quarantine: Enabled
```

#### 3. View Recent Alerts

```bash
# Via API (requires READ key from .env.test)
curl "http://127.0.0.1:8101/watcher/alerts?limit=20" \
  -H "X-Wingman-Approval-Read-Key: YOUR_READ_KEY"

# Filter by severity
curl "http://127.0.0.1:8101/watcher/alerts?severity=CRITICAL&limit=50" \
  -H "X-Wingman-Approval-Read-Key: YOUR_READ_KEY"

# Filter by worker
curl "http://127.0.0.1:8101/watcher/alerts?worker_id=worker_123" \
  -H "X-Wingman-Approval-Read-Key: YOUR_READ_KEY"
```

#### 4. Check Quarantined Workers

```bash
# Via Redis CLI
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec redis redis-cli SMEMBERS quarantined_workers

# Get quarantine details for a specific worker
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec redis redis-cli HGETALL quarantine:worker_123
```

### Incident Response

#### Scenario 1: Worker Incorrectly Quarantined

**Symptoms**:
- Worker approval requests auto-rejected with "Worker quarantined" message
- Telegram alert shows FALSE claim that was actually safe

**Resolution**:
```bash
# 1. Investigate the event that triggered quarantine
curl "http://127.0.0.1:8101/watcher/alerts?worker_id=worker_123&severity=CRITICAL" \
  -H "X-Wingman-Approval-Read-Key: YOUR_READ_KEY"

# 2. Verify it's a false positive (check claim details)
# 3. Release worker via API
curl -X POST "http://127.0.0.1:8101/watcher/release/worker_123" \
  -H "X-Wingman-Approval-Decide-Key: YOUR_DECIDE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "released_by": "mark@example.com",
    "reason": "False positive - claim was safe"
  }'

# 4. Verify worker can now request approvals
# Worker's next approval request should succeed (not auto-rejected)
```

#### Scenario 2: Alert Storm (Too Many Duplicate Alerts)

**Symptoms**:
- Multiple identical Telegram alerts in short time
- Deduplication not working

**Resolution**:
```bash
# 1. Check Redis connectivity
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec wingman-watcher \
  python -c "import redis; r=redis.Redis(host='redis', port=6379); print(r.ping())"

# 2. Check dedup TTL setting
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec wingman-watcher env | grep DEDUP_TTL

# 3. Increase TTL if needed (edit .env.test)
# WINGMAN_WATCHER_DEDUP_TTL_SEC=7200  # 2 hours instead of 1

# 4. Restart watcher
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test restart wingman-watcher
```

#### Scenario 3: No Alerts Received

**Symptoms**:
- Watcher running but no Telegram alerts
- Events appearing in `data/claims_audit.jsonl`

**Resolution**:
```bash
# 1. Check Telegram configuration
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec wingman-watcher env | grep TELEGRAM

# 2. Test Telegram connectivity
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec wingman-watcher \
  python -c "import os,requests; t=os.environ.get('TELEGRAM_BOT_TOKEN'); r=requests.get(f'https://api.telegram.org/bot{t}/getMe'); print(r.json())"

# 3. Check watcher logs for errors
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test logs wingman-watcher | grep -i "failed\|error"

# 4. Check database persistence (alerts should be in DB even if Telegram fails)
curl "http://127.0.0.1:8101/watcher/alerts?limit=10" \
  -H "X-Wingman-Approval-Read-Key: YOUR_READ_KEY"
```

#### Scenario 4: Database Full (>30 Days of Alerts)

**Symptoms**:
- Database growing too large
- Alert queries slow

**Resolution**:
```bash
# 1. Check alert volume
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec postgres psql -U wingman -d wingman \
  -c "SELECT COUNT(*), MIN(sent_at), MAX(sent_at) FROM watcher_alerts;"

# 2. Manual cleanup (delete alerts older than 30 days)
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec postgres psql -U wingman -d wingman \
  -c "DELETE FROM watcher_alerts WHERE sent_at < NOW() - INTERVAL '30 days';"

# 3. Set up daily cleanup cron (future enhancement)
# Add to crontab: 0 2 * * * docker compose ... exec postgres psql -U wingman -d wingman -c "DELETE FROM watcher_alerts WHERE sent_at < NOW() - INTERVAL '30 days';"
```

### Emergency Procedures

#### Emergency: Disable Quarantine

**When**: Watcher bug causing mass quarantine of legitimate workers

```bash
# 1. Disable quarantine feature
# Edit .env.test or .env.prd:
# WINGMAN_QUARANTINE_ENABLED=0

# 2. Restart watcher
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test restart wingman-watcher

# 3. Clear all quarantines
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec redis redis-cli DEL quarantined_workers

docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec redis redis-cli --scan --pattern "quarantine:*" | \
  xargs docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec redis redis-cli DEL

# 4. Re-enable after fix deployed
# WINGMAN_QUARANTINE_ENABLED=1
# Restart watcher
```

#### Emergency: Disable Watcher Completely

**When**: Watcher causing service disruption

```bash
# Stop watcher (preserves state)
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test stop wingman-watcher

# Verify other services still running
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test ps

# Re-enable after fix
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test start wingman-watcher
```

### Database Queries

#### Alert Volume by Severity (Last 7 Days)
```bash
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec postgres psql -U wingman -d wingman -c "
SELECT severity, COUNT(*), environment
FROM watcher_alerts
WHERE sent_at > NOW() - INTERVAL '7 days'
GROUP BY severity, environment
ORDER BY CASE severity
  WHEN 'CRITICAL' THEN 1
  WHEN 'HIGH' THEN 2
  WHEN 'MEDIUM' THEN 3
  WHEN 'LOW' THEN 4
END;
"
```

#### Quarantine Events
```bash
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec postgres psql -U wingman -d wingman -c "
SELECT worker_id, message, sent_at, environment
FROM watcher_alerts
WHERE event_type = 'WORKER_QUARANTINED'
  AND sent_at > NOW() - INTERVAL '30 days'
ORDER BY sent_at DESC;
"
```

#### Acknowledgment Rate
```bash
docker compose -f /Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.yml \
  -p wingman-test exec postgres psql -U wingman -d wingman -c "
SELECT
  COUNT(*) FILTER (WHERE acknowledged_at IS NOT NULL) * 100.0 / COUNT(*) as ack_rate_pct,
  COUNT(*) FILTER (WHERE acknowledged_at IS NOT NULL) as acknowledged,
  COUNT(*) FILTER (WHERE acknowledged_at IS NULL) as unacknowledged,
  COUNT(*) as total
FROM watcher_alerts
WHERE sent_at > NOW() - INTERVAL '7 days';
"
```

### Configuration Reference

**Environment Variables** (`.env.test` / `.env.prd`):

```bash
# Environment
DEPLOYMENT_ENV=test  # or "prd"

# Database (Postgres)
DB_HOST=postgres
DB_PORT=5432
DB_NAME=wingman
DB_USER=wingman
DB_PASSWORD=<secret>

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
TELEGRAM_BOT_TOKEN=<secret>
TELEGRAM_CHAT_ID=<secret>
WINGMAN_NOTIFY_BACKENDS=stdout,telegram
```

---

## See Also

- [Architecture](../02-architecture/README.md) — System design
- [How to Use](../01-how-to-use/README.md) — Integration guide
- [Watcher Design](WATCHER_ENHANCEMENT_DESIGN.md) — Phase 4 design document
- [Validation Guide](VALIDATION_OPERATIONAL_GUIDE.md) — Validation system operations
- [DEPLOYMENT_PLAN.md](../../DEPLOYMENT_PLAN.md) — Detailed deployment status
- [CLAUDE.md](../../CLAUDE.md) — AI agent instructions
