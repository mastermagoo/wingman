# Wingman Automation Complete Audit — 2026-02-17

## Executive Summary

**Overall Status: 🟡 OPERATIONAL with Configuration Issues**

- ✅ Core services: HEALTHY (TEST + PRD)
- ✅ Telegram: OPERATIONAL (TEST + PRD)
- ✅ Database backups: RUNNING (daily at 02:30)
- ⚠️ Cron health checks: FAILING (wrong container ports)
- ⚠️ Watcher approval monitoring: FAILING (API connection issues)
- ❌ Prometheus/Grafana: NOT CONFIGURED
- ❌ Scheduled cron jobs: NONE (no automated tasks beyond monitoring)

---

## 1. Container Stack Health

### TEST Environment (localhost:8101)
```
Service              Status      Uptime
wingman-api          healthy     26 hours
telegram-bot         running     29 hours
wingman-watcher      running     3 days
execution-gateway    healthy     3 days
postgres             healthy     3 days
redis                healthy     3 days
```

**Health Endpoint:**
```json
{
  "status": "healthy",
  "database": "memory",
  "phase": "6.1",
  "validators": {
    "input_validation": "available",
    "output_validation": "available"
  }
}
```

### PRD Environment (localhost:5001)
```
Service              Status      Uptime
wingman-prd-api      healthy     26 hours
wingman-prd-telegram running     3 days
wingman-prd-watcher  running     3 days
wingman-prd-gateway  healthy     3 days
wingman-prd-postgres healthy     26 hours
wingman-prd-redis    healthy     3 days
```

**Health Endpoint:**
```json
{
  "status": "healthy",
  "database": "connected",
  "phase": "6.1",
  "validators": {
    "input_validation": "available",
    "output_validation": "available"
  }
}
```

**Database Size (PRD):**
- verification_logs: 72 KB
- output_validations: 48 KB
- Total: Minimal usage (< 1 MB)

---

## 2. Telegram Integration

### Status: ✅ OPERATIONAL

**TEST:**
```bash
✅ Telegram: Connected
API: http://wingman-api:5000
Last connection: 2026-02-16 10:34:40
```

**PRD:**
```bash
✅ Telegram: Connected
API: http://wingman-prd-api:5001
```

### Configuration
- Bot token: ✅ Configured (env_file)
- Chat ID: ✅ Configured (env_file)
- Connectivity: ✅ Verified to api.telegram.org
- Approval notifications: ✅ Enabled

---

## 3. Cron Jobs

### Status: ⚠️ CONFIGURED BUT FAILING

**Wingman-specific cron jobs:**
```bash
# Wingman Health Monitoring (FAILING - wrong ports)
*/5 * * * * check_wingman_health_cron.py --env TEST --container wingman-api --container-port 5000
*/5 * * * * check_wingman_health_cron.py --env PRD --container wingman-prd-api --container-port 8001

# Wingman PRD Database Backup (WORKING)
30 2 * * * backup_wingman_db.sh >> /tmp/wingman_prd_backup.log 2>&1
```

### Issues Identified

#### Issue 1: TEST Health Check
**Problem:** Container name mismatch
- Cron calls: `--container wingman-api`
- Actual container: `wingman-test-wingman-api-1`
- Error: `cannot discover port for wingman-api:5000`

#### Issue 2: PRD Health Check
**Problem:** Wrong container port
- Cron calls: `--container-port 8001`
- Actual API port: `5001` (confirmed in compose + env)
- Error: `cannot discover port for wingman-prd-api:8001`

#### Issue 3: Backup Script
**Status:** ✅ Working
- Last run: 2026-02-17 02:30:01
- Backup location: `/Volumes/Data/backups/wingman/prd/daily/`
- Format: `wingman_data_YYYYMMDD_HHMMSS.tar.gz`
- Recent backups: 4 days (2026-02-14 to 2026-02-17)

---

## 4. Wingman Watcher (Autonomous Monitoring)

### Status: ⚠️ RUNNING BUT DEGRADED

**TEST Watcher:**
```
✅ Redis: Connected (redis:6379)
✅ Postgres: Connected (postgres:5432/wingman)
✅ Audit log monitoring: Active (data/claims_audit.jsonl)
⚠️ Approval monitoring: FAILING (DNS resolution error for wingman-api)
```

**Error Log:**
```
⚠️ Failed to fetch pending approvals: HTTPConnectionPool(host='wingman-api', port=5000):
   Failed to resolve 'wingman-api'
```

**PRD Watcher:**
```
⚠️ Approval monitoring: FAILING (wrong API port)
```

**Error Log:**
```
⚠️ Failed to fetch pending approvals: HTTPConnectionPool(host='wingman-api', port=8001):
   Connection refused
```

### Root Cause
PRD watcher is using hardcoded port 8001 instead of 5001 (likely stale env var or config).

### Watcher State (PRD)
```json
{
  "offset": 1737,
  "recent_alerts": {},
  "notified_approval_ids": []
}
```

---

## 5. Prometheus/Grafana Integration

### Status: ❌ NOT CONFIGURED

**Findings:**
- No Prometheus service in docker-compose files
- No Grafana service in docker-compose files
- No `/metrics` endpoint in API server
- No metrics collection configured

**References to metrics:**
- Found 9 Python files with "metrics" mentions (mostly in AI worker scripts)
- No production metrics infrastructure

---

## 6. Automated Tasks/Orchestration

### Status: ⚠️ MONITORING ONLY (No active automation)

**What Exists:**
1. **Health monitoring** (every 5 min) - BROKEN
2. **Database backups** (daily 02:30) - WORKING
3. **Watcher monitoring** (continuous) - DEGRADED

**What Does NOT Exist:**
- No scheduled AI worker execution
- No automated deployments
- No scheduled maintenance tasks
- No automated testing
- No scheduled reports/metrics collection

**AI Worker Scripts Available (Not Scheduled):**
- `/ai-workers/scripts/AUTONOMOUS_DEPLOY_FIX.py`
- `/ai-workers/scripts/AUTONOMOUS_BUILD.py`
- `/ai-workers/scripts/ORCHESTRATED_VALIDATION.py`
- Various workforce launch scripts (not automated)

---

## 7. Execution Gateway

### Status: ✅ HEALTHY

**PRD Gateway:**
```json
{
  "service": "execution-gateway",
  "status": "healthy",
  "timestamp": "2026-02-17T15:58:18.933581+00:00"
}
```

**Configuration:**
- Port: localhost:5002
- Docker socket access: ✅ Mounted
- Audit storage: Postgres
- JWT secret: ✅ Configured
- Environment: prd

---

## Critical Issues Summary

### 🔴 High Priority

1. **PRD Watcher API Connection Failure**
   - Watcher cannot monitor approval queue
   - Using wrong port (8001 vs 5001)
   - Impact: No proactive approval notifications

2. **Cron Health Checks Completely Failing**
   - TEST: Wrong container name
   - PRD: Wrong container port
   - Impact: No automated health alerting

### 🟡 Medium Priority

3. **No Prometheus/Grafana Monitoring**
   - No metrics collection
   - No dashboards
   - Impact: Limited observability

4. **TEST Watcher DNS Issues**
   - Cannot resolve `wingman-api` hostname
   - May be network configuration issue

---

## Recommendations

### Immediate Actions (Before Next Deployment)

1. **Fix PRD watcher API connection**
   ```bash
   # Verify correct API port in watcher environment
   docker compose -f docker-compose.prd.yml -p wingman-prd \
     --env-file .env.prd exec wingman-watcher env | grep WINGMAN_API_URL

   # Should be: http://wingman-prd-api:5001 (not 8001)
   ```

2. **Fix cron health checks**
   ```bash
   # Update crontab with correct container names and ports:
   # TEST: --container wingman-test-wingman-api-1 --container-port 5000
   # PRD:  --container wingman-prd-api --container-port 5001
   ```

3. **Verify TEST watcher network connectivity**
   ```bash
   # Test DNS resolution inside watcher container
   docker compose -f docker-compose.yml -p wingman-test exec wingman-watcher \
     ping -c 1 wingman-api || nslookup wingman-api
   ```

### Future Enhancements

4. **Add Prometheus/Grafana stack**
   - Add `/metrics` endpoint to API server
   - Deploy Prometheus + Grafana services
   - Configure dashboards for key metrics

5. **Schedule AI worker automation** (if desired)
   - Add cron jobs for periodic AI worker execution
   - Configure automated testing cycles
   - Add scheduled deployment checks

6. **Enhance backup strategy**
   - Add weekly/monthly backup rotation
   - Configure off-site backup sync
   - Add restore testing automation

---

## Verification Commands

```bash
# 1. Verify all containers healthy
docker compose -f docker-compose.yml -p wingman-test ps
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd ps

# 2. Test API health
curl -s http://localhost:8101/health | jq .
curl -s http://localhost:5001/health | jq .

# 3. Test Telegram connectivity
docker compose -f docker-compose.yml -p wingman-test exec telegram-bot \
  python -c "import os,requests; t=os.environ.get('BOT_TOKEN'); r=requests.get(f'https://api.telegram.org/bot{t}/getMe',timeout=10); print('OK' if r.ok else 'FAIL')"

# 4. Check watcher logs
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd logs wingman-watcher --tail 50

# 5. Verify backups
ls -lh /Volumes/Data/backups/wingman/prd/daily/

# 6. Check cron logs
tail -30 /tmp/wingman_test_health.log
tail -30 /tmp/wingman_prd_health.log
tail -30 /tmp/wingman_prd_backup.log
```

---

## Conclusion

**Wingman automation is OPERATIONAL but requires configuration fixes:**

✅ **Working:**
- Core services (TEST + PRD)
- Telegram integration
- Database backups
- Execution gateway

⚠️ **Needs Attention:**
- Watcher approval monitoring (API connection)
- Cron health checks (wrong ports/containers)

❌ **Not Implemented:**
- Prometheus/Grafana metrics
- Scheduled automation/orchestration

**Next Steps:**
1. Fix watcher API connection issues (HIGH)
2. Fix cron health check configuration (HIGH)
3. Consider Prometheus/Grafana for observability (MEDIUM)
4. Evaluate need for scheduled AI worker automation (LOW)

---

**Audit Performed:** 2026-02-17 15:13-16:00 UTC
**Environment:** macOS Darwin 25.1.0
**Docker:** OrbStack
**Wingman Version:** Phase 6.1
