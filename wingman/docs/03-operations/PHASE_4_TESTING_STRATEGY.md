# Phase 4 Watcher Enhancement - Testing Strategy

**Date**: 2026-02-14
**Environment**: TEST (validate before PRD deployment)
**Duration**: 24-48 hours monitoring recommended

---

## Overview

This document provides a comprehensive testing strategy to validate Phase 4 Watcher Enhancement features before promoting to PRD.

**Phase 4 Features to Test**:
1. ✅ Deduplication (Redis-based alert suppression)
2. ✅ Persistence (Postgres database tracking)
3. ✅ Severity Classification (CRITICAL/HIGH/MEDIUM/LOW)
4. ✅ Automated Quarantine (block compromised workers)

---

## Test 1: Trigger a Test Alert (Baseline)

### Objective
Verify watcher can detect and alert on FALSE claims.

### Steps

1. **Create a fake audit log entry**:
   ```bash
   # Add a FALSE claim to the audit log
   echo '{"timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "worker_id": "test_worker_001", "task_name": "Test Alert", "claim": "I executed docker stop wingman-test-api", "status": "FALSE", "reason": "Manual test - worker did not execute this command"}' >> data/claims_audit.jsonl
   ```

2. **Check watcher logs**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test logs --tail=20 wingman-watcher
   ```

3. **Expected Output**:
   - `🚨 FALSE CLAIM DETECTED` message
   - Telegram alert sent (check your Telegram)
   - Severity: MEDIUM (TEST environment)

4. **Verify persistence**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T postgres \
     psql -U wingman -d wingman -c "SELECT alert_id, event_type, severity, worker_id, message FROM watcher_alerts ORDER BY sent_at DESC LIMIT 5;"
   ```

   Expected: 1 row with `event_type=FALSE_CLAIM`, `severity=MEDIUM`, `worker_id=test_worker_001`

---

## Test 2: Deduplication (Alert Suppression)

### Objective
Verify that duplicate alerts within the 1-hour window are suppressed.

### Steps

1. **Trigger the SAME alert 5 times**:
   ```bash
   for i in {1..5}; do
     echo '{"timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "worker_id": "test_worker_001", "task_name": "Test Dedup", "claim": "I executed docker stop wingman-test-api", "status": "FALSE", "reason": "Duplicate test"}' >> data/claims_audit.jsonl
     sleep 2
   done
   ```

2. **Check Redis dedup keys**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T redis \
     redis-cli --scan --pattern "watcher:dedup:*"
   ```

   Expected: 1 key (all 5 events have same fingerprint)

3. **Check dedup counter**:
   ```bash
   # Get the fingerprint key from above, then:
   docker compose -f docker-compose.yml -p wingman-test exec -T redis \
     redis-cli HGETALL watcher:dedup:<fingerprint>
   ```

   Expected: `count` field = 5

4. **Verify only 1 Telegram alert**:
   - Check Telegram: should see only 1 alert (first occurrence)
   - Subsequent 4 alerts were suppressed

5. **Wait for hourly digest** (or trigger manually):
   - After 1 hour, watcher sends digest of suppressed alerts
   - Check Telegram for digest message: "📊 Watcher Digest (last hour)"

---

## Test 3: Severity Classification

### Objective
Verify severity is correctly classified based on environment and operation type.

### Steps

1. **MEDIUM severity (TEST + FALSE + destructive)**:
   ```bash
   echo '{"timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "worker_id": "test_medium", "task_name": "Test Medium", "claim": "I executed docker rm -f container", "status": "FALSE", "reason": "Test medium severity"}' >> data/claims_audit.jsonl
   ```

   Expected: Telegram alert with `ℹ️ MEDIUM` severity

2. **LOW severity (UNVERIFIABLE)**:
   ```bash
   echo '{"timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "worker_id": "test_low", "task_name": "Test Low", "claim": "I checked the weather", "status": "UNVERIFIABLE", "reason": "Test low severity"}' >> data/claims_audit.jsonl
   ```

   Expected: Telegram alert with `📝 LOW` severity

3. **Query database by severity**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T postgres \
     psql -U wingman -d wingman -c "SELECT severity, COUNT(*) FROM watcher_alerts GROUP BY severity ORDER BY severity;"
   ```

   Expected: Counts for MEDIUM and LOW

---

## Test 4: Automated Quarantine

### Objective
Verify that workers triggering CRITICAL alerts are automatically quarantined and blocked from approval flow.

**Note**: CRITICAL alerts only occur in PRD. In TEST, we'll manually simulate quarantine.

### Steps

1. **Manually quarantine a worker** (simulate CRITICAL event):
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T redis redis-cli SADD quarantined_workers test_worker_quarantine

   docker compose -f docker-compose.yml -p wingman-test exec -T redis redis-cli HSET quarantine:test_worker_quarantine \
     reason "Manual test - simulating CRITICAL alert" \
     quarantined_at "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
     environment "test"
   ```

2. **Verify quarantine status**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T redis redis-cli SMEMBERS quarantined_workers
   ```

   Expected: `test_worker_quarantine`

3. **Attempt approval request from quarantined worker**:
   ```bash
   curl -X POST http://127.0.0.1:8101/approvals/request \
     -H "Content-Type: application/json" \
     -H "X-Wingman-Approval-Request-Key: XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY" \
     -d '{
       "worker_id": "test_worker_quarantine",
       "task_name": "Test Quarantine Block",
       "instruction": "DELIVERABLES: Test if quarantine blocks approval",
       "deployment_env": "test"
     }' | python3 -m json.tool
   ```

4. **Expected Response**:
   ```json
   {
     "needs_approval": false,
     "status": "AUTO_REJECTED",
     "reason": "Worker quarantined: Manual test - simulating CRITICAL alert",
     "message": "Contact Mark to release this worker via /release_worker command"
   }
   ```

   HTTP Status: **403 Forbidden**

5. **Release worker from quarantine**:
   ```bash
   curl -X POST http://127.0.0.1:8101/watcher/release/test_worker_quarantine \
     -H "Content-Type: application/json" \
     -H "X-Wingman-Approval-Read-Key: XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY" \
     -d '{
       "released_by": "mark@example.com",
       "reason": "Test complete - false alarm"
     }' | python3 -m json.tool
   ```

6. **Verify worker is released**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T redis redis-cli SMEMBERS quarantined_workers
   ```

   Expected: Empty (worker removed)

7. **Retry approval request** (should succeed now):
   ```bash
   curl -X POST http://127.0.0.1:8101/approvals/request \
     -H "Content-Type: application/json" \
     -H "X-Wingman-Approval-Request-Key: XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY" \
     -d '{
       "worker_id": "test_worker_quarantine",
       "task_name": "Test Post-Release",
       "instruction": "DELIVERABLES: Test if worker can request approval after release",
       "deployment_env": "test"
     }' | python3 -m json.tool
   ```

   Expected: Normal approval flow (not auto-rejected)

---

## Test 5: Alert Acknowledgment

### Objective
Verify operators can acknowledge alerts and query alert history.

### Steps

1. **Query recent unacknowledged alerts**:
   ```bash
   curl -s "http://127.0.0.1:8101/watcher/alerts?unacknowledged=true&limit=10" \
     -H "X-Wingman-Approval-Read-Key: XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY" | python3 -m json.tool
   ```

2. **Get alert_id from response**, then acknowledge:
   ```bash
   curl -X POST http://127.0.0.1:8101/watcher/acknowledge/<alert_id> \
     -H "Content-Type: application/json" \
     -H "X-Wingman-Approval-Read-Key: XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY" \
     -d '{"acknowledged_by": "mark@example.com"}' | python3 -m json.tool
   ```

3. **Verify acknowledgment in database**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T postgres \
     psql -U wingman -d wingman -c "SELECT alert_id, acknowledged_at, acknowledged_by FROM watcher_alerts WHERE alert_id = '<alert_id>';"
   ```

   Expected: `acknowledged_at` and `acknowledged_by` populated

4. **Query acknowledgment rate** (metric):
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T postgres \
     psql -U wingman -d wingman -c "SELECT COUNT(*) FILTER (WHERE acknowledged_at IS NOT NULL) * 100.0 / COUNT(*) as ack_rate_pct FROM watcher_alerts WHERE sent_at > NOW() - INTERVAL '7 days';"
   ```

---

## Test 6: Alert History Queries

### Objective
Verify API endpoints for querying alert history.

### Steps

1. **Query by severity**:
   ```bash
   curl -s "http://127.0.0.1:8101/watcher/alerts?severity=MEDIUM&limit=10" \
     -H "X-Wingman-Approval-Read-Key: XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY" | python3 -m json.tool
   ```

2. **Query by worker_id**:
   ```bash
   curl -s "http://127.0.0.1:8101/watcher/alerts?worker_id=test_worker_001&limit=10" \
     -H "X-Wingman-Approval-Read-Key: XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY" | python3 -m json.tool
   ```

3. **Query by date range**:
   ```bash
   curl -s "http://127.0.0.1:8101/watcher/alerts?since=2026-02-14T00:00:00&limit=50" \
     -H "X-Wingman-Approval-Read-Key: XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY" | python3 -m json.tool
   ```

4. **Query unacknowledged alerts**:
   ```bash
   curl -s "http://127.0.0.1:8101/watcher/alerts?unacknowledged=true" \
     -H "X-Wingman-Approval-Read-Key: XuDeKtTJ6bldz_7igJRTfm-nGyc2BWj5d5xyRCKptlY" | python3 -m json.tool
   ```

---

## Test 7: Database Performance

### Objective
Verify database can handle alert volume and queries remain fast.

### Steps

1. **Generate 100 test alerts**:
   ```bash
   for i in {1..100}; do
     worker_id="load_test_worker_$(( RANDOM % 20 ))"
     severity=$(( RANDOM % 4 ))
     status="FALSE"

     echo '{"timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "worker_id": "'$worker_id'", "task_name": "Load Test '$i'", "claim": "load test claim '$i'", "status": "'$status'", "reason": "Performance test"}' >> data/claims_audit.jsonl

     sleep 0.1
   done
   ```

2. **Check database size**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T postgres \
     psql -U wingman -d wingman -c "SELECT COUNT(*), pg_size_pretty(pg_total_relation_size('watcher_alerts')) as table_size FROM watcher_alerts;"
   ```

3. **Test query performance** (should be <50ms):
   ```bash
   time docker compose -f docker-compose.yml -p wingman-test exec -T postgres \
     psql -U wingman -d wingman -c "SELECT * FROM watcher_alerts WHERE severity = 'MEDIUM' ORDER BY sent_at DESC LIMIT 10;"
   ```

4. **Check index usage**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T postgres \
     psql -U wingman -d wingman -c "SELECT indexrelname, idx_scan FROM pg_stat_user_indexes WHERE schemaname = 'public' AND relname = 'watcher_alerts';"
   ```

---

## Test 8: Monitoring (24-Hour Soak Test)

### Objective
Let watcher run for 24 hours to identify any issues.

### Monitoring Checklist

**Every 4 hours, check**:

1. **Watcher service health**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test ps wingman-watcher
   docker compose -f docker-compose.yml -p wingman-test logs --tail=50 wingman-watcher | grep -E "⚠️|🚨|ERROR"
   ```

2. **Redis memory usage**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T redis redis-cli INFO memory | grep used_memory_human
   ```

3. **Postgres disk usage**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T postgres \
     psql -U wingman -d wingman -c "SELECT pg_size_pretty(pg_database_size('wingman'));"
   ```

4. **Alert volume**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T postgres \
     psql -U wingman -d wingman -c "SELECT COUNT(*) FROM watcher_alerts WHERE sent_at > NOW() - INTERVAL '4 hours';"
   ```

5. **Deduplication effectiveness**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T redis \
     redis-cli --scan --pattern "watcher:dedup:*" | wc -l
   ```

6. **Check for quarantine events**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T redis redis-cli SMEMBERS quarantined_workers
   ```

---

## Test 9: Failure Recovery

### Objective
Verify watcher can recover from Redis/Postgres outages.

### Steps

1. **Stop Redis temporarily**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test stop redis
   ```

2. **Check watcher logs** (should fail gracefully):
   ```bash
   docker compose -f docker-compose.yml -p wingman-test logs --tail=20 wingman-watcher
   ```

   Expected: `⚠️ Redis connection failed` warnings, but watcher keeps running

3. **Restart Redis**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test start redis
   ```

4. **Verify reconnection**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test logs --tail=20 wingman-watcher
   ```

   Expected: `✅ Redis connected`

5. **Repeat for Postgres**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test stop postgres
   # Wait 30 seconds
   docker compose -f docker-compose.yml -p wingman-test start postgres
   ```

---

## Test 10: Cleanup & Retention

### Objective
Verify old alerts can be safely cleaned up.

### Steps

1. **Check oldest alerts**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T postgres \
     psql -U wingman -d wingman -c "SELECT MIN(sent_at), MAX(sent_at), COUNT(*) FROM watcher_alerts;"
   ```

2. **Test retention cleanup** (dry run - alerts older than 30 days):
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T postgres \
     psql -U wingman -d wingman -c "SELECT COUNT(*) FROM watcher_alerts WHERE sent_at < NOW() - INTERVAL '30 days';"
   ```

3. **If needed, manually clean up test alerts**:
   ```bash
   docker compose -f docker-compose.yml -p wingman-test exec -T postgres \
     psql -U wingman -d wingman -c "DELETE FROM watcher_alerts WHERE worker_id LIKE 'test_%' OR worker_id LIKE 'load_test_%';"
   ```

---

## Success Criteria

After completing all tests, verify:

- ✅ **Deduplication**: Duplicate alerts suppressed, digest sent hourly
- ✅ **Persistence**: All alerts stored in database, queryable via API
- ✅ **Severity**: MEDIUM/LOW correctly classified (CRITICAL/HIGH in PRD)
- ✅ **Quarantine**: Quarantined workers auto-rejected, can be released
- ✅ **Acknowledgment**: Alerts can be acknowledged, history queryable
- ✅ **Performance**: Queries <50ms, no memory leaks
- ✅ **Resilience**: Recovers from Redis/Postgres outages
- ✅ **Monitoring**: 24-hour soak test shows no errors

---

## Known Issues / Limitations

1. **CRITICAL severity only in PRD**: TEST environment cannot generate CRITICAL alerts (by design)
2. **Hourly digest timing**: First digest may take up to 1 hour to appear
3. **Manual retention cleanup**: No automated 30-day cleanup (requires cron job)

---

## Next Steps After Testing

Once all tests pass and 24-hour monitoring shows stability:

1. Review [AAA_PRD_DEPLOYMENT_PLAN.md](../deployment/AAA_PRD_DEPLOYMENT_PLAN.md)
2. Schedule PRD deployment window
3. Apply migration to PRD
4. Update .env.prd with Phase 4 config
5. Rebuild PRD services (requires Wingman approval)
6. Monitor PRD for 24 hours

---

**End of Testing Strategy**
