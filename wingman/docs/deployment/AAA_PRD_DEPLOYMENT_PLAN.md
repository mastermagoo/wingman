# Wingman PRD Execution Gateway Deployment Plan
**Status**: CURRENT  
**Last Updated**: 2026-01-17  
**Version**: 1.0  
**Scope**: Wingman deployment documentation (DEV/TEST/PRD)  

**Date:** 2026-01-10  
**Status:** Ready for Approval  
**Environment:** PRD (Mac Studio)

---

## 🎯 **OBJECTIVE**

Deploy Execution Gateway to PRD environment with full HITL approval gates, matching TEST implementation.

---

## ✅ **PREREQUISITES**

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

**Status:** Ready for PRD deployment approval
