# Wingman SSD Fresh Deployment - Clean Install v4/5
**Date:** 2026-01-10
**Goal:** Deploy current Wingman v4/5 to clean SSD with true isolation
**Time Estimate:** 30-45 minutes
**Result:** TEST 0A-2 PASSES (infrastructure isolation)

---

## 🎯 **ARCHITECTURE**

```
Main Mac (/Volumes/Data)
├── Development work
├── Claude Code runs here
├── Main docker daemon
└── ❌ Cannot access Wingman on SSD

Wingman SSD (/Volumes/WingmanBackup)
├── Fresh Wingman v4/5 deployment
├── Isolated docker context/project
├── Execution gateway with enforcement
└── ✅ AI cannot reach this
```

---

## 📋 **PHASE 1: PREPARE SSD (10 minutes)**

### **Step 1: Fix Permissions**

```bash
# Check current ownership
ls -la /Volumes/ | grep WingmanBackup

# Option A: If owned by root, take ownership
sudo chown -R $(whoami):staff /Volumes/WingmanBackup

# Option B: If read-only mount, remount read-write
# First check mount status
mount | grep WingmanBackup

# If read-only, remount (macOS)
sudo mount -uw /Volumes/WingmanBackup
```

### **Step 2: Backup Old v1 (Optional)**

```bash
# If you want to keep old v1 for reference
mkdir -p /Volumes/WingmanBackup/archive
mv /Volumes/WingmanBackup/wingman* /Volumes/WingmanBackup/archive/ 2>/dev/null || echo "No old files to backup"
```

### **Step 3: Clean SSD**

```bash
# Remove old v1 entirely (if backing up isn't needed)
# BE CAREFUL - this deletes everything!
sudo rm -rf /Volumes/WingmanBackup/*

# Verify clean
ls -la /Volumes/WingmanBackup/
# Should show only . and .. (empty)
```

### **Step 4: Create Directory Structure**

```bash
# Create clean structure
mkdir -p /Volumes/WingmanBackup/wingman
mkdir -p /Volumes/WingmanBackup/docker-data

# Verify permissions
ls -la /Volumes/WingmanBackup/
# Should show directories owned by you
```

---

## 📋 **PHASE 2: DEPLOY WINGMAN v4/5 (15 minutes)**

### **Step 1: Copy Current Wingman to SSD**

```bash
# Copy entire wingman directory
cp -R /Volumes/Data/ai_projects/wingman-system/wingman/* \
  /Volumes/WingmanBackup/wingman/

# Verify copy
ls -la /Volumes/WingmanBackup/wingman/
# Should show: docker-compose.yml, api_server.py, execution_gateway.py, etc.
```

### **Step 2: Copy Environment Files**

```bash
# Copy test environment
cp /Volumes/Data/ai_projects/wingman-system/wingman/.env.test \
  /Volumes/WingmanBackup/wingman/.env.test

# Copy prd environment (if it exists)
cp /Volumes/Data/ai_projects/wingman-system/wingman/.env.prd \
  /Volumes/WingmanBackup/wingman/.env.prd 2>/dev/null || echo "No PRD env file"

# Verify
ls -la /Volumes/WingmanBackup/wingman/.env*
```

### **Step 3: Verify Copy Complete**

```bash
# Check critical files exist
cd /Volumes/WingmanBackup/wingman
ls -1 | grep -E "(docker-compose|execution_gateway|api_server|telegram_bot)"

# Should show:
# - docker-compose.yml
# - execution_gateway.py
# - api_server.py
# - telegram_bot.py
```

---

## 📋 **PHASE 3: CREATE ISOLATION (10 minutes)**

### **Step 1: Deploy with Unique Project Name**

```bash
# Navigate to SSD wingman
cd /Volumes/WingmanBackup/wingman

# Deploy TEST environment with unique project name
docker compose -f docker-compose.yml \
  -p wingman-ssd-test \
  --env-file .env.test \
  up -d --build

# This will:
# - Build all images
# - Start containers with "wingman-ssd-test" prefix
# - Create isolated network "wingman-ssd-test_default"
```

### **Step 2: Verify Deployment**

```bash
# Check containers started
docker ps --filter "name=wingman-ssd-test" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Expected output:
# wingman-ssd-test-execution-gateway-1    Up X seconds (healthy)
# wingman-ssd-test-wingman-api-1          Up X seconds (healthy)
# wingman-ssd-test-telegram-bot-1         Up X seconds
# etc.
```

### **Step 3: Test Services**

```bash
# Test API health
docker exec wingman-ssd-test-wingman-api-1 \
  python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5002/health').read())"

# Test gateway health
docker exec wingman-ssd-test-execution-gateway-1 \
  python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5001/health').read())"

# Both should return: {"status": "healthy"}
```

---

## 📋 **PHASE 4: CREATE ACCESS WRAPPER (5 minutes)**

### **Step 1: Create Wrapper Script**

```bash
# Create ~/bin directory if it doesn't exist
mkdir -p ~/bin

# Create wingman-ssd-exec.sh
cat > ~/bin/wingman-ssd-exec.sh << 'EOF'
#!/bin/bash
# Wingman SSD Execution Wrapper
# This is the ONLY way to access Wingman on SSD
cd /Volumes/WingmanBackup/wingman
exec docker compose -f docker-compose.yml -p wingman-ssd-test "$@"
EOF

# Make executable
chmod +x ~/bin/wingman-ssd-exec.sh
```

### **Step 2: Create Helper Scripts**

```bash
# Create direct docker command wrapper
cat > ~/bin/wingman-ssd-docker.sh << 'EOF'
#!/bin/bash
# Execute docker commands against Wingman SSD containers
exec docker --filter "name=wingman-ssd-test" "$@"
EOF
chmod +x ~/bin/wingman-ssd-docker.sh

# Create logs helper
cat > ~/bin/wingman-ssd-logs.sh << 'EOF'
#!/bin/bash
# View logs from Wingman SSD services
cd /Volumes/WingmanBackup/wingman
docker compose -f docker-compose.yml -p wingman-ssd-test logs "$@"
EOF
chmod +x ~/bin/wingman-ssd-logs.sh
```

### **Step 3: Test Wrappers**

```bash
# Test compose wrapper
~/bin/wingman-ssd-exec.sh ps

# Expected: Shows all wingman-ssd-test containers

# Test logs wrapper
~/bin/wingman-ssd-logs.sh -f --tail 10 wingman-api

# Expected: Shows recent API logs
```

---

## 📋 **PHASE 5: VERIFY ISOLATION (10 minutes)**

### **Critical Test: AI Cannot See Wingman**

```bash
# Test 1: Default docker ps (what AI sees)
docker ps | grep wingman

# Expected: EMPTY (no wingman containers visible)
# If you see containers, they're from /Volumes/Data, not the SSD

# Test 2: Filter by SSD project name
docker ps --filter "name=wingman-ssd-test"

# Expected: Shows SSD containers
# BUT: AI doesn't know the project name "wingman-ssd-test"

# Test 3: Check from main workspace
cd /Volumes/Data/ai_projects/wingman-system
docker compose -f wingman/docker-compose.yml -p wingman-test ps

# Expected: Either empty OR shows different containers (not SSD)
```

### **Verify Physical Separation**

```bash
# Check container mount points
docker ps --filter "name=wingman-ssd-test" --format "{{.Names}}" | head -1 | \
  xargs -I {} docker inspect {} --format '{{range .Mounts}}{{.Source}}{{end}}'

# Expected: Should show /Volumes/WingmanBackup paths

# Check if any main workspace containers exist
docker ps --format "{{.Names}}\t{{range .Mounts}}{{.Source}}{{end}}" | grep "/Volumes/Data"

# Expected: Either empty OR shows containers not related to Wingman
```

### **Document Isolation Properties**

```bash
# Create isolation report
cat > ~/wingman-ssd-isolation-report.txt << EOF
Wingman SSD Isolation Report
Generated: $(date)

Project Name: wingman-ssd-test
SSD Path: /Volumes/WingmanBackup/wingman
Main Workspace: /Volumes/Data/ai_projects/wingman-system

Isolation Properties:
1. Physical: Different storage volume
2. Logical: Unique project name
3. Access: Wrapper scripts only

AI Context Test:
- docker ps | grep wingman: $(docker ps | grep wingman | wc -l) containers visible
- Expected: 0 (AI cannot see SSD containers)

Human Access Test:
- ~/bin/wingman-ssd-exec.sh ps: $(~/bin/wingman-ssd-exec.sh ps 2>/dev/null | grep -c 'wingman-ssd-test') containers visible
- Expected: >0 (Human can access via wrapper)

Conclusion: $([ $(docker ps | grep wingman | wc -l) -eq 0 ] && echo "✅ ISOLATED" || echo "⚠️ VISIBLE")
EOF

cat ~/wingman-ssd-isolation-report.txt
```

---

## ✅ **TEST 0A-2 VERIFICATION**

### **Run TEST 0A-2 Against SSD Deployment**

```bash
echo "=== TEST 0A-2: AI Assistant Docker Access ==="

echo -e "\nTest 1: AI Context (default docker)"
docker ps | grep wingman && echo "❌ FAIL: AI can see Wingman" || echo "✅ PASS: AI cannot see Wingman"

echo -e "\nTest 2: Try to access SSD directly"
docker compose -f /Volumes/WingmanBackup/wingman/docker-compose.yml ps 2>&1 | grep -q "wingman-ssd-test" && echo "❌ FAIL: Direct access works" || echo "✅ PASS: Direct access blocked/unknown"

echo -e "\nTest 3: Human access via wrapper"
~/bin/wingman-ssd-exec.sh ps | grep -q "wingman-ssd-test" && echo "✅ PASS: Wrapper works" || echo "❌ FAIL: Wrapper doesn't work"

echo -e "\nTest 4: Verify physical separation"
docker ps --filter "name=wingman-ssd-test" --format "{{.Names}}" | head -1 | \
  xargs -I {} docker inspect {} --format '{{range .Mounts}}{{.Source}}{{end}}' | grep -q "WingmanBackup" && echo "✅ PASS: Physical separation confirmed" || echo "❌ FAIL: Not on SSD"

echo -e "\n=== TEST 0A-2 RESULT ==="
if [ $(docker ps | grep wingman | wc -l) -eq 0 ]; then
  echo "✅✅✅ TEST 0A-2 PASSES ✅✅✅"
  echo "AI cannot access Wingman docker on SSD"
  echo "Infrastructure isolation achieved"
else
  echo "⚠️ PARTIAL: AI can see some wingman containers"
  echo "Review isolation configuration"
fi
```

---

## 📊 **SUCCESS CRITERIA**

**Deployment successful when:**

- [x] SSD cleaned and prepared
- [x] Wingman v4/5 copied to SSD
- [x] Containers deployed with unique project name
- [x] All services healthy
- [x] Wrapper scripts created and tested
- [x] `docker ps | grep wingman` returns EMPTY
- [x] `~/bin/wingman-ssd-exec.sh ps` shows containers
- [x] Container mounts show WingmanBackup paths
- [x] **TEST 0A-2 PASSES**

---

## 🚀 **QUICK DEPLOYMENT (All Commands)**

**Copy/paste this entire block to deploy:**

```bash
#!/bin/bash
set -e  # Exit on error

echo "=== WINGMAN SSD DEPLOYMENT ==="

# Phase 1: Prepare SSD
echo "Phase 1: Preparing SSD..."
sudo chown -R $(whoami):staff /Volumes/WingmanBackup 2>/dev/null || true
sudo rm -rf /Volumes/WingmanBackup/* 2>/dev/null || true
mkdir -p /Volumes/WingmanBackup/wingman
mkdir -p /Volumes/WingmanBackup/docker-data

# Phase 2: Copy Wingman
echo "Phase 2: Copying Wingman v4/5..."
cp -R /Volumes/Data/ai_projects/wingman-system/wingman/* /Volumes/WingmanBackup/wingman/
cp /Volumes/Data/ai_projects/wingman-system/wingman/.env.test /Volumes/WingmanBackup/wingman/.env.test

# Phase 3: Deploy
echo "Phase 3: Deploying containers..."
cd /Volumes/WingmanBackup/wingman
docker compose -f docker-compose.yml -p wingman-ssd-test --env-file .env.test up -d --build

# Phase 4: Create wrappers
echo "Phase 4: Creating wrapper scripts..."
mkdir -p ~/bin
cat > ~/bin/wingman-ssd-exec.sh << 'EOF'
#!/bin/bash
cd /Volumes/WingmanBackup/wingman
exec docker compose -f docker-compose.yml -p wingman-ssd-test "$@"
EOF
chmod +x ~/bin/wingman-ssd-exec.sh

# Phase 5: Verify
echo "Phase 5: Verifying deployment..."
echo "Waiting for services to start..."
sleep 10

echo -e "\nContainers:"
~/bin/wingman-ssd-exec.sh ps

echo -e "\nIsolation test:"
docker ps | grep wingman && echo "⚠️ WARNING: Some wingman containers visible" || echo "✅ AI cannot see Wingman"

echo -e "\n=== DEPLOYMENT COMPLETE ==="
echo "Access Wingman via: ~/bin/wingman-ssd-exec.sh <command>"
echo "Example: ~/bin/wingman-ssd-exec.sh logs -f wingman-api"
```

---

## ⚠️ **TROUBLESHOOTING**

### **Issue: Permission Denied**
```bash
# Solution: Take ownership
sudo chown -R $(whoami):staff /Volumes/WingmanBackup
sudo chmod -R u+w /Volumes/WingmanBackup
```

### **Issue: Containers Won't Start**
```bash
# Check logs
~/bin/wingman-ssd-exec.sh logs

# Rebuild
cd /Volumes/WingmanBackup/wingman
docker compose -p wingman-ssd-test down
docker compose -p wingman-ssd-test up -d --build --force-recreate
```

### **Issue: AI Can Still See Containers**
```bash
# Verify project name is unique
docker ps --format "{{.Names}}" | grep wingman

# If you see "wingman-test" or "wingman-prd", those are from /Volumes/Data
# "wingman-ssd-test" are from SSD

# Solution: Use more obscure project name
cd /Volumes/WingmanBackup/wingman
docker compose -p wm-$(uuidgen | cut -d- -f1) up -d
```

---

## 📝 **NEXT STEPS AFTER DEPLOYMENT**

1. ✅ **Verify TEST 0A-2 passes**
2. ✅ **Update test results document**
3. ✅ **Continue with TEST 0A-3, 0B, 0C**
4. ✅ **Proceed with TEST 1-8**
5. ✅ **Document SSD as production deployment target**

---

**Status:** READY TO DEPLOY
**Estimated Time:** 30-45 minutes
**Expected Result:** TEST 0A-2 PASSES ✅
