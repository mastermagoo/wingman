# Wingman PRD Execution Gateway Deployment Plan
**Status**: CURRENT
**Last Updated**: 2026-02-14
**Version**: 1.1
**Scope**: Wingman deployment documentation (DEV/TEST/PRD)

**Date:** 2026-01-10
**Status:** Ready for Approval
**Environment:** PRD (Mac Studio)

---

## 🎯 **OBJECTIVE**

Deploy Execution Gateway to PRD environment with full HITL approval gates, matching TEST implementation.

---

## ⚠️ **MANDATORY PREREQUISITE: Docker Wrapper Setup**

**CRITICAL**: Before executing ANY docker commands in this runbook, you MUST have the Docker wrapper active.

### Setup Instructions:

```bash
# 1. Add wrapper to PATH (one-time per shell session)
export PATH="/Volumes/Data/ai_projects/wingman-system/wingman/tools:$PATH"
export DOCKER_BIN="/Users/kermit/.orbstack/bin/docker"

# 2. Verify wrapper is active
which docker
# Expected: /Volumes/Data/ai_projects/wingman-system/wingman/tools/docker

# 3. Test wrapper blocks destructive commands
docker stop test
# Expected: ❌ BLOCKED: Destructive docker command requires Wingman approval
```

### Permanent Setup (Recommended):

Add to `~/.zshrc` or `~/.bashrc`:
```bash
export PATH="/Volumes/Data/ai_projects/wingman-system/wingman/tools:$PATH"
export DOCKER_BIN="/Users/kermit/.orbstack/bin/docker"
```

**Why Required**: The wrapper enforces infrastructure-level protection. All destructive docker commands must go through Wingman approval + Execution Gateway. Without the wrapper, commands bypass this protection.

**See**: [Docker Wrapper Audit Report](../03-operations/DOCKER_WRAPPER_AUDIT.md)

---

## ✅ **PREREQUISITES**

- [x] **Docker wrapper setup complete** (see above - MANDATORY)
- [x] TEST environment validated (Stages A-E complete)
- [x] Execution gateway working in TEST
- [x] Privilege separation verified
- [x] Enforcement tests passing
- [ ] PRD approval for deployment

---

## 📋 **DEPLOYMENT STAGES**

### **Stage 1: Add Gateway Service to docker-compose.prd.yml**

**File:** `wingman/docker-compose.prd.yml`

**Add service:**
```yaml
  execution-gateway:
    build:
      context: .
      dockerfile: Dockerfile.gateway
    env_file:
      - .env.prd
    environment:
      - ALLOWED_ENVIRONMENTS=prd
      - GATEWAY_PORT=5001
      - AUDIT_STORAGE=postgres
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - wingman-network-prd
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5001/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Location:** After `telegram-bot` service, before `postgres`

---

### **Stage 2: Remove Docker Socket from Other Services**

**Verify these services do NOT have docker socket:**
- `wingman-api-prd` - Remove if present
- `wingman-telegram-prd` - Remove if present  
- `wingman-watcher-prd` - Remove if present

**Check current state:**
```bash
docker inspect wingman-api-prd --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} {{end}}' | grep docker.sock
docker inspect wingman-telegram-prd --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} {{end}}' | grep docker.sock
docker inspect wingman-watcher-prd --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} {{end}}' | grep docker.sock
```

**If any have socket, remove from docker-compose.prd.yml:**
```yaml
# REMOVE these lines:
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

---

### **Stage 3: Update Environment Variables**

**File:** `.env.prd`

**Add/verify:**
```bash
# Execution Gateway
ALLOWED_ENVIRONMENTS=prd
GATEWAY_PORT=5001
AUDIT_STORAGE=postgres
GATEWAY_URL=http://execution-gateway:5001
```

---

### **Stage 4: Deploy with Approval Gates**

**Each stage requires Wingman approval:**

1. **Stage A: Stop PRD stack** → Approval required
2. **Stage B: Remove old containers** → Approval required
3. **Stage C: Build and start with gateway** → Approval required
4. **Stage D: Validate deployment** → Approval required

---

## 🔧 **DEPLOYMENT COMMANDS**

**Stage A: Stop**
```bash
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd down
```

**Stage B: Remove (if needed)**
```bash
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd down --remove-orphans
```

**Stage C: Build and Start**
```bash
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d --build
```

**Stage D: Validate**
```bash
# Check gateway health
docker exec wingman-prd-execution-gateway python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5001/health').read())"

# Verify privilege separation
docker inspect wingman-prd-execution-gateway --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} {{end}}' | grep docker.sock && echo "✅ Gateway has socket" || echo "❌ Gateway missing socket"

docker inspect wingman-prd-api --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} {{end}}' | grep docker.sock && echo "❌ API has socket (BAD)" || echo "✅ API no socket (GOOD)"
```

---

## ✅ **VALIDATION CHECKLIST**

After deployment, verify:

- [ ] Gateway container running and healthy
- [ ] Gateway health endpoint responds
- [ ] Gateway has docker socket access
- [ ] API does NOT have docker socket
- [ ] Telegram bot does NOT have docker socket
- [ ] Watcher does NOT have docker socket
- [ ] Token minting works (`POST /gateway/token`)
- [ ] Command execution works (`POST /gateway/execute`)
- [ ] Enforcement blocks unauthorized commands
- [ ] Audit logging to Postgres working

---

## 🚨 **ROLLBACK PLAN**

If deployment fails:

1. **Stop new stack:**
   ```bash
   docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd down
   ```

2. **Restore previous docker-compose.prd.yml** (from git)

3. **Restart without gateway:**
   ```bash
   docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d
   ```

4. **Verify services restored**

---

## 📊 **SUCCESS CRITERIA**

**Deployment successful when:**
- ✅ All validation checklist items pass
- ✅ Gateway operational and enforcing
- ✅ No service disruptions
- ✅ Privilege separation maintained
- ✅ Audit trail functional

---

## 🔐 **SECURITY NOTES**

- Gateway is ONLY service with docker socket
- All other services have no privileged access
- All commands require capability tokens
- All executions logged to audit trail
- No bypass paths exist

---

**Status:** Execution Gateway deployed; Validation system ready for Phase 3.6 rollout

---

## 🎯 **PHASE 3.6: VALIDATION GRADUAL ROLLOUT TO PRD**

**Date Added**: 2026-02-14
**Status**: Ready for execution
**Prerequisites**: Validation system deployed to PRD (VALIDATION_ENABLED=0, ready to enable)

### **Overview**

Validation enhancement (Phase 1-2) is deployed to PRD but disabled by default. This section describes the gradual rollout procedure to enable validation for 10% → 50% → 100% of approval requests.

### **Current PRD Validation Status**

**Deployment Status**: ✅ Complete
- All 5 validators deployed (990 LOC)
- CompositeValidator with profile system available
- Integrated into api_server.py approval flow
- Feature flags configured

**Current Configuration**:
```bash
# .env.prd (current)
VALIDATION_ENABLED=0           # Validation disabled
VALIDATION_ROLLOUT_PERCENT=100 # Not used (validation disabled)
```

### **Rollout Schedule**

**Week 1, Day 1-3: Enable for 10%**
- **Goal**: Initial validation exposure, monitor for issues
- **Success Criteria**: <5% false positives, no system instability
- **Monitoring**: Auto-reject rate, auto-approve rate, manual review rate

**Week 1, Day 4-7: Increase to 50%**
- **Goal**: Broader validation coverage, collect more data
- **Success Criteria**: Metrics stable, <5% false positives
- **Monitoring**: Same metrics, watch for patterns

**Week 2, Full Week: Enable for 100%**
- **Goal**: Full validation for all requests
- **Success Criteria**: Metrics acceptable for 7 consecutive days
- **Monitoring**: Continuous monitoring for 7 days before declaring success

### **Rollout Stage 1: Enable for 10% (Week 1, Day 1-3)**

**Prerequisites**:
- [ ] PRD environment healthy (all containers running)
- [ ] Baseline metrics collected (auto-approve rate without validation)
- [ ] Monitoring dashboard ready
- [ ] Rollback procedure tested in TEST

**Steps**:

1. **Update environment variables**:
   ```bash
   # Edit .env.prd
   VALIDATION_ENABLED=1
   VALIDATION_ROLLOUT_PERCENT=10
   ```

2. **Restart API container**:
   ```bash
   docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d wingman-api
   ```

3. **Verify validation enabled**:
   ```bash
   docker exec wingman-prd-api printenv | grep VALIDATION

   # Should see:
   # VALIDATION_ENABLED=1
   # VALIDATION_ROLLOUT_PERCENT=10
   ```

4. **Monitor for 72 hours**:
   - Auto-reject rate (expect: 5-10% of validated requests)
   - Auto-approve rate (expect: 15-30% of validated requests)
   - Manual review rate (expect: 60-80% of validated requests)
   - False positive reports (target: <5%)
   - API errors or validation failures (target: 0%)

**Success Criteria**:
- ✅ No system instability (API remains healthy)
- ✅ Auto-reject rate 5-10% (not rejecting everything)
- ✅ Auto-approve rate 15-30% (approving safe operations)
- ✅ False positive rate <5% (few incorrect rejections)
- ✅ No validation errors or timeouts

**Go/No-Go Decision** (Day 3):
- **GO**: Proceed to 50% if all success criteria met
- **NO-GO**: Rollback to 0% if false positive rate >10% or system issues

### **Rollout Stage 2: Increase to 50% (Week 1, Day 4-7)**

**Prerequisites**:
- [ ] Stage 1 success criteria met
- [ ] No outstanding validation issues from 10% rollout

**Steps**:

1. **Update rollout percentage**:
   ```bash
   # Edit .env.prd
   VALIDATION_ROLLOUT_PERCENT=50
   ```

2. **Restart API container**:
   ```bash
   docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d wingman-api
   ```

3. **Monitor for 96 hours**:
   - Same metrics as Stage 1
   - Watch for patterns in auto-rejected requests
   - Collect feedback from manual reviews

**Success Criteria**:
- ✅ Same as Stage 1 (false positive rate <5%)
- ✅ Metrics stable compared to 10% rollout
- ✅ No new issues introduced

**Go/No-Go Decision** (Day 7):
- **GO**: Proceed to 100% if all success criteria met
- **NO-GO**: Rollback to 10% or 0% if issues emerge

### **Rollout Stage 3: Enable for 100% (Week 2)**

**Prerequisites**:
- [ ] Stage 2 success criteria met
- [ ] Admin prepared for potential increased manual review volume

**Steps**:

1. **Update to full rollout**:
   ```bash
   # Edit .env.prd
   VALIDATION_ROLLOUT_PERCENT=100
   ```

2. **Restart API container**:
   ```bash
   docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d wingman-api
   ```

3. **Monitor for 7 days**:
   - Same metrics as Stage 1/2
   - Monitor for 7 consecutive days before declaring success

**Success Criteria**:
- ✅ False positive rate <5% for 7 consecutive days
- ✅ Auto-approve rate 15-30% (reducing manual review burden)
- ✅ Auto-reject rate 5-10% (catching dangerous patterns)
- ✅ No system instability or performance degradation
- ✅ Manual review rate 60-80% (expected baseline)

**Final Go/No-Go Decision** (Week 2, Day 7):
- **GO**: Declare Phase 3.6 complete, validation is production-ready
- **NO-GO**: Tune thresholds or rollback to 50%

### **Monitoring Metrics**

**Key Metrics to Track**:

1. **Auto-Reject Rate**:
   ```sql
   SELECT COUNT(*) FILTER (WHERE status = 'AUTO_REJECTED') * 100.0 / COUNT(*)
   FROM approval_requests
   WHERE created_at > NOW() - INTERVAL '24 hours';
   ```
   - **Expected**: 5-10%
   - **Alert if**: >15% (too many rejections) or <2% (missing issues)

2. **Auto-Approve Rate**:
   ```sql
   SELECT COUNT(*) FILTER (WHERE status = 'AUTO_APPROVED') * 100.0 / COUNT(*)
   FROM approval_requests
   WHERE created_at > NOW() - INTERVAL '24 hours';
   ```
   - **Expected**: 15-30%
   - **Alert if**: >40% (too lenient) or <10% (too strict)

3. **Manual Review Rate**:
   ```sql
   SELECT COUNT(*) FILTER (WHERE status = 'PENDING') * 100.0 / COUNT(*)
   FROM approval_requests
   WHERE created_at > NOW() - INTERVAL '24 hours';
   ```
   - **Expected**: 60-80%
   - **Alert if**: >85% (thresholds too strict)

4. **False Positive Rate**:
   - Track: Auto-rejected requests that were later manually approved
   - **Target**: <5%
   - **Critical**: >10%

5. **Validation Errors**:
   ```bash
   docker logs wingman-prd-api | grep -i "validation failed" | wc -l
   ```
   - **Expected**: 0 errors
   - **Alert if**: Any errors (indicates validator bugs)

### **Rollback Procedure**

**Trigger Rollback If**:
- False positive rate >10%
- Validation errors/timeouts
- System instability
- Admin decision

**Rollback Steps**:

1. **Disable validation immediately**:
   ```bash
   # Edit .env.prd
   VALIDATION_ENABLED=0
   ```

2. **Restart API container**:
   ```bash
   docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d wingman-api
   ```

3. **Verify rollback**:
   ```bash
   docker exec wingman-prd-api printenv | grep VALIDATION_ENABLED
   # Should see: VALIDATION_ENABLED=0
   ```

4. **Investigate in TEST**:
   - Reproduce issue in TEST environment
   - Fix validators or tune thresholds
   - Re-test in TEST
   - Re-attempt PRD rollout when ready

**Partial Rollback** (reduce percentage instead of disabling):
```bash
# Reduce to lower percentage
VALIDATION_ROLLOUT_PERCENT=10  # or 0 to effectively disable
```

### **Tuning During Rollout**

**If False Positive Rate is High (>5%)**:

1. **Identify which validator is causing false positives**:
   ```sql
   SELECT validator_scores
   FROM approval_requests
   WHERE status = 'AUTO_REJECTED'
     AND created_at > NOW() - INTERVAL '24 hours';
   ```

2. **Common fixes**:
   - **CodeScanner**: Add patterns to whitelist (e.g., safe environment variables)
   - **ContentQuality**: Lower hard floor from 30 to 25 (requires code change)
   - **Profile detection**: Add keywords to operational profile (reduce deployment profile usage)

3. **Apply fix in TEST first**, then deploy to PRD

**If Auto-Approve Rate is Too Low (<10%)**:

1. **Lower auto-approve thresholds**:
   - Operational: 85 → 80 (requires code change)
   - Deployment: 90 → 85 (requires code change)

2. **Test in TEST environment first**

### **Success Declaration**

**Phase 3.6 is complete when**:
- ✅ VALIDATION_ROLLOUT_PERCENT=100 for 7 consecutive days
- ✅ False positive rate <5%
- ✅ Auto-approve rate 15-30%
- ✅ No validation errors or system instability
- ✅ Metrics documented and baseline established

**Post-Rollout**:
- Continue monitoring metrics weekly
- Tune thresholds based on real-world data
- Update profile detection keywords as needed
- Document lessons learned

### **Related Documentation**

- **Validation Report**: `AAA_DELTA_REPORT_VALIDATION_DEPLOYMENT.md`
- **Operational Guide**: `../03-operations/VALIDATION_OPERATIONAL_GUIDE.md`
- **User Guide**: `../04-user-guides/APPROVAL_WORKFLOW_WITH_VALIDATION.md`
- **Architecture**: `../02-architecture/AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md`

---

**Status (Updated 2026-02-14):** Execution Gateway deployed and operational; Validation system deployed and ready for Phase 3.6 gradual rollout
