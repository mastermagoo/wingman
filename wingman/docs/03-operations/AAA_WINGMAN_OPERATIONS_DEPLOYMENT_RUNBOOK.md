# Wingman Operations Guide

**Status**: CURRENT  
**Last Updated**: 2026-01-17  
**Version**: 1.0  
**Scope**: Wingman operations/runbooks (DEV/TEST/PRD)  

> **Audience**: System operators, DevOps, and anyone running Wingman day-to-day

---

## Wingman 5 (Phase 5) — Deployment Plan

- **Secure deployment plan (Phase 5)**: [PHASE_5_SECURE_DEPLOYMENT.md](../99-archive/paul-wingman/PHASE_5_SECURE_DEPLOYMENT.md)

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

## See Also

- [Architecture](../02-architecture/README.md) — System design
- [How to Use](../01-how-to-use/README.md) — Integration guide
- [DEPLOYMENT_PLAN.md](../../DEPLOYMENT_PLAN.md) — Detailed deployment status
- [CLAUDE.md](../../CLAUDE.md) — AI agent instructions
