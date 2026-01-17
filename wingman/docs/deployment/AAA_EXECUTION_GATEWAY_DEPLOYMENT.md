# Execution Gateway Deployment Guide

**Last Updated**: 2026-01-17  
**Version**: 1.0  
**Scope**: Wingman deployment documentation (DEV/TEST/PRD)  

**Status**: Core code already exists, needs deployment only

---

## 🎯 PHASE 1: Fix Dockerfile.gateway Ports

**File**: `Dockerfile.gateway`

**Line 30**: Change `EXPOSE 5001` to `EXPOSE 5002`

**Line 34**: Change `localhost:5001` to `localhost:5002`

---

## 🎯 PHASE 2: Update docker-compose.prd.yml

**Action**: Add execution-gateway service
**Location**: `/Volumes/Data/ai_projects/wingman-system/wingman/docker-compose.prd.yml`
**Insert After**: Line 151 (after telegram-bot service, before postgres)

```yaml
  # Execution Gateway - Phase 5: Capability-Based Execution
  execution-gateway:
    build:
      context: .
      dockerfile: Dockerfile.gateway
    container_name: wingman-prd-gateway
    environment:
      - GATEWAY_JWT_SECRET=${GATEWAY_JWT_SECRET:?GATEWAY_JWT_SECRET is required}
      - GATEWAY_PORT=5002
      - AUDIT_STORAGE=postgres
      - ALLOWED_ENVIRONMENTS=prd
      # Database connection for audit logs
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=${DB_NAME:-wingman_prd}
      - POSTGRES_USER=${DB_USER:-wingman_prd}
      - POSTGRES_PASSWORD=${DB_PASSWORD:?DB_PASSWORD is required}
      - DEPLOYMENT_ENV=prd
    ports:
      - "127.0.0.1:5002:5002"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - wingman-network-prd
    volumes:
      - ./logs/prd:/app/logs
      - ./data/prd:/app/data
    restart: unless-stopped
    labels:
      - "com.wingman.compose-file=docker-compose.prd.yml"
      - "com.wingman.environment=production"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5002/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

```

**EXACT LINE NUMBERS**:
- Open `docker-compose.prd.yml`
- Find line 151 (end of `telegram-bot` service)
- Add **blank line** after line 151
- Paste the above YAML starting at line 152
- This pushes `postgres:` service down to approximately line 197

---

## 🎯 PHASE 3: Update .env.prd

**File**: `.env.prd`
**Line**: 43 (after `DEPLOYMENT_ENV=prd`)

```bash
# Generate secret
openssl rand -hex 32

# Add after line 42 in .env.prd:
GATEWAY_JWT_SECRET=<paste-generated-secret>
```

---

## 🎯 PHASE 4: Deploy

```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

# Deploy gateway
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d execution-gateway

# Verify health
curl http://127.0.0.1:5002/health

# Run test suite
./tools/test_execution_gateway.sh
```

---

## 🎯 PHASE 5: Troubleshooting & Validation

### 5.1 Basic Health Checks

**CORRECT SYNTAX** (--env-file must come BEFORE the logs command):
```bash
# Check gateway status
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd ps execution-gateway

# Check health endpoint
curl http://127.0.0.1:5002/health

# Expected: {"status": "healthy", "service": "execution-gateway", "timestamp": "..."}
```

### 5.2 Check Logs

```bash
# View recent logs
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd logs --tail=100 execution-gateway

# Follow logs in real-time
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd logs -f execution-gateway

# Search for errors
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd logs execution-gateway | grep -i error
```

**WRONG** (this will fail with "required variable is missing"):
```bash
# ❌ DON'T DO THIS
docker compose -f docker-compose.prd.yml -p wingman-prd logs execution-gateway .env.prd
```

### 5.3 Verify Docker Socket Access

```bash
# Gateway SHOULD have docker socket
docker inspect wingman-prd-gateway --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}' | grep docker
# Expected: /var/run/docker.sock -> /var/run/docker.sock

# API SHOULD NOT have docker socket
docker inspect wingman-prd-api --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}' | grep docker
# Expected: (empty - no socket mount)
```

### 5.4 Common Issues & Solutions

#### Issue 1: Gateway Won't Start
```bash
# Check if port 5002 is already in use
lsof -i :5002

# Check environment variables
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd config | grep -A 10 execution-gateway

# Rebuild and restart
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d --build --force-recreate execution-gateway
```

#### Issue 2: Health Check Failing
```bash
# Check if service is listening
docker exec wingman-prd-gateway netstat -tlnp 2>/dev/null || docker exec wingman-prd-gateway ss -tlnp

# Test health endpoint from inside container
docker exec wingman-prd-gateway python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5002/health').read())"

# Check for Python errors in logs
docker logs wingman-prd-gateway 2>&1 | grep -i "traceback\|error"
```

#### Issue 3: Database Connection Failed
```bash
# Check if postgres is healthy
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd ps postgres

# Test connection from gateway
docker exec wingman-prd-gateway python -c "import psycopg2; conn=psycopg2.connect('host=postgres port=5432 dbname=wingman_prd user=wingman_prd password=SECRET'); print('Connected')"

# Check if audit table exists
docker exec wingman-prd-postgres psql -U wingman_prd -d wingman_prd -c '\dt execution_audit'
```

#### Issue 4: Token Validation Failing
```bash
# Check if GATEWAY_JWT_SECRET is set
docker exec wingman-prd-gateway env | grep GATEWAY_JWT_SECRET
# Should show: GATEWAY_JWT_SECRET=<value>

# Verify secret matches between Wingman API and Gateway
docker exec wingman-prd-api env | grep GATEWAY_JWT_SECRET
docker exec wingman-prd-gateway env | grep GATEWAY_JWT_SECRET
# Values MUST match
```

### 5.5 Restart/Rebuild Commands

```bash
# Restart gateway (preserves container)
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd restart execution-gateway

# Rebuild and restart (fresh build)
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d --build execution-gateway

# Force recreate (new container)
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d --force-recreate execution-gateway

# Full rebuild + recreate
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d --build --force-recreate execution-gateway
```

---

## 🎯 PHASE 6: Post-Deployment Validation

### 6.1 Run Automated Test Suite

```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

# Set environment for PRD
export WINGMAN_API=http://127.0.0.1:5002
export GATEWAY_API=http://127.0.0.1:5002
export WINGMAN_APPROVAL_DECIDE_KEY="<your-decide-key>"

# Run test suite
./tools/test_execution_gateway.sh
```

**Expected Output:**
```
🧪 Execution Gateway Test Suite
================================

Test 1: Gateway health check... ✓ PASS
Test 2: Wingman API health check... ✓ PASS
Test 3: Request low-risk approval... ✓ PASS (Auto-approved)
Test 4: Generate capability token... ✓ PASS
Test 5: Execute command via gateway... ✓ PASS
Test 6: Token replay protection... ✓ PASS (Replay blocked)
Test 7: Invalid token rejection... ✓ PASS (Invalid token rejected)
Test 8: Audit log verification... ✓ PASS (Execution logged to database)

================================
✅ ALL TESTS PASSED
================================
```

### 6.2 Manual Validation Tests

#### Test A: Gateway Health
```bash
curl -s http://127.0.0.1:5002/health | jq
# Expected: {"status": "healthy", ...}
```

#### Test B: Privilege Separation
```bash
# Gateway SHOULD have docker socket
docker exec wingman-prd-gateway ls -la /var/run/docker.sock
# Expected: srw-rw---- (socket exists)

# API SHOULD NOT have docker socket
docker exec wingman-prd-api ls -la /var/run/docker.sock 2>&1
# Expected: No such file or directory
```

#### Test C: Token Flow (End-to-End)
```bash
# 1. Submit approval request
REQUEST_ID=$(curl -s -X POST http://127.0.0.1:5002/approvals/request \
  -H "Content-Type: application/json" \
  -H "X-Wingman-Approval-Request-Key: <your-key>" \
  -d '{
    "worker_id": "manual-test",
    "task_name": "Manual Validation Test",
    "instruction": "DELIVERABLES: Test command\nSUCCESS_CRITERIA: Exit 0\nBOUNDARIES: Read-only\nDEPENDENCIES: None\nMITIGATION: None\nTEST_PROCESS: Run echo\nTEST_RESULTS_FORMAT: stdout\nRESOURCE_REQUIREMENTS: None\nRISK_ASSESSMENT: Low\nQUALITY_METRICS: Success\n\nCommand: echo test",
    "deployment_env": "prd"
  }' | jq -r '.request.request_id')

echo "Request ID: $REQUEST_ID"

# 2. Approve via Telegram: /approve $REQUEST_ID

# 3. Mint capability token
TOKEN=$(curl -s -X POST http://127.0.0.1:5002/gateway/token \
  -H "Content-Type: application/json" \
  -H "X-Wingman-Approval-Decide-Key: <your-decide-key>" \
  -d "{\"approval_id\": \"$REQUEST_ID\", \"command\": \"echo test\", \"environment\": \"prd\"}" \
  | jq -r '.token')

echo "Token: $TOKEN"

# 4. Execute via gateway
curl -s -X POST http://127.0.0.1:5002/gateway/execute \
  -H "Content-Type: application/json" \
  -H "X-Capability-Token: $TOKEN" \
  -d "{\"command\": \"echo test\", \"approval_id\": \"$REQUEST_ID\", \"environment\": \"prd\"}" \
  | jq

# Expected: {"success": true, "output": "test\n", "exit_code": 0, "execution_id": "...", ...}
```

#### Test D: Replay Protection
```bash
# Try to reuse same token (should fail)
curl -s -X POST http://127.0.0.1:5002/gateway/execute \
  -H "Content-Type: application/json" \
  -H "X-Capability-Token: $TOKEN" \
  -d "{\"command\": \"echo test\", \"approval_id\": \"$REQUEST_ID\", \"environment\": \"prd\"}" \
  | jq

# Expected: {"success": false, "error": "Token has already been used"}
```

#### Test E: Audit Log Verification
```bash
# Check execution was logged
docker exec wingman-prd-postgres psql -U wingman_prd -d wingman_prd -c \
  "SELECT execution_id, approval_id, command, exit_code, created_at FROM execution_audit ORDER BY created_at DESC LIMIT 5;"

# Expected: Recent execution logged with correct approval_id
```

### 6.3 Verification Checklist

**Infrastructure:**
- [ ] Gateway container running and healthy
- [ ] Gateway has docker socket mounted
- [ ] API/bot/watcher do NOT have docker socket
- [ ] Health endpoints responding (API: 5002, Gateway: 5002)

**Functionality:**
- [ ] Can submit approval requests
- [ ] Can mint capability tokens (with DECIDE key)
- [ ] Can execute commands via gateway (with valid token)
- [ ] Token replay protection works
- [ ] Invalid tokens rejected
- [ ] Audit logs written to database

**Security:**
- [ ] Unauthorized execution blocked (no token = no execution)
- [ ] Command scope enforced (can't execute unapproved commands)
- [ ] Environment boundaries enforced (TEST token can't execute PRD ops)
- [ ] Audit logs immutable (append-only table with triggers)

---

## Summary

**3 files to edit**:
1. `Dockerfile.gateway` - Fix ports (lines 30, 34)
2. `docker-compose.prd.yml` - Add gateway service (after line 151)
3. `.env.prd` - Add GATEWAY_JWT_SECRET

**Deploy**: `docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d execution-gateway`

**Test**: `./tools/test_execution_gateway.sh`

**Validate**: Complete Phase 6 validation checklist above

**Check Logs**: `docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd logs execution-gateway`

---

## 🚨 Critical Notes

1. **Port Configuration**: Ensure Dockerfile.gateway EXPOSE and healthcheck use port 5002 (not 5001)
2. **Environment Variables**: GATEWAY_JWT_SECRET must match between Wingman API and Gateway
3. **Database**: Gateway requires database connection for audit logging (POSTGRES_* env vars)
4. **Privilege Separation**: ONLY gateway should have docker socket - verify with `docker inspect`
5. **Testing**: Run full test suite after deployment to verify all functionality
