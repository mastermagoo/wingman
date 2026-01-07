# Wingman Operations Guide

> **Audience**: System operators, DevOps, and anyone running Wingman day-to-day

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
