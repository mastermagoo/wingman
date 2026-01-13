# Wingman SSD Activation Plan - Use Existing Hardened Build
**Date:** 2026-01-10
**Status:** Existing hardened Wingman on SSD - Ready to activate
**Goal:** Access hardened Wingman for TEST 0A-2 verification

---

## 🎯 **CURRENT STATE**

```
/Volumes/WingmanBackup/
└── [Contains original hardened Wingman build]
    ├── Execution gateway (deployed)
    ├── Enforcement layers (implemented)
    ├── HITL approval gates (configured)
    └── Full security stack (hardened)
```

**Key Advantage:** Don't need to build - just activate and test ✅

---

## 📋 **DISCOVERY PHASE** (REQUIRED FIRST)

**Before we can use it, we need to know:**

### **1. What's the directory structure?**
```bash
# List SSD contents
ls -la /Volumes/WingmanBackup/

# Find Wingman directory
find /Volumes/WingmanBackup -name "docker-compose.yml" -type f 2>/dev/null

# Find Wingman main directory
ls -la /Volumes/WingmanBackup/ | grep -i wingman
```

### **2. Is it running?**
```bash
# Check for running containers
docker ps | grep wingman

# Check all containers (including stopped)
docker ps -a | grep wingman

# Check by filtering for SSD path
docker ps -a --format "{{.Names}}\t{{.Mounts}}" | grep WingmanBackup
```

### **3. What version/configuration?**
```bash
# Check docker compose files
ls -la /Volumes/WingmanBackup/*/docker-compose*.yml

# Check if execution gateway exists
find /Volumes/WingmanBackup -name "execution_gateway.py" -type f

# Check for environment files
find /Volumes/WingmanBackup -name ".env*" -type f 2>/dev/null | grep -v example
```

### **4. What's the project name?**
```bash
# If containers exist, find project name
docker ps -a --format "{{.Names}}" | grep wingman | head -1 | cut -d- -f1-2
# Example output: "wingman-prd" or "wingman-test"

# Check compose file for project name
grep -r "name:" /Volumes/WingmanBackup/*/docker-compose*.yml 2>/dev/null
```

---

## 🚀 **ACTIVATION SCENARIOS**

### **Scenario A: Containers Already Running**

**If `docker ps | grep wingman` shows containers:**

```bash
# They're using the SAME docker daemon (not isolated)
# Need to create isolation

# Option A1: Stop existing, redeploy with isolation
docker compose -f <path-to-compose> -p <project-name> down
cd /Volumes/WingmanBackup/<wingman-dir>
docker compose -f docker-compose.yml -p wingman-ssd up -d

# Option A2: Create wrapper to existing containers
cat > ~/bin/wingman-exec.sh << 'EOF'
#!/bin/bash
cd /Volumes/WingmanBackup/<wingman-dir>
exec docker compose -f docker-compose.yml -p <existing-project-name> "$@"
EOF
chmod +x ~/bin/wingman-exec.sh
```

---

### **Scenario B: Containers Stopped (Most Likely)**

**If `docker ps -a | grep wingman` shows stopped containers:**

```bash
# Start existing containers
cd /Volumes/WingmanBackup/<wingman-dir>
docker compose -f docker-compose.yml -p <project-name> up -d

# Create wrapper
cat > ~/bin/wingman-exec.sh << 'EOF'
#!/bin/bash
cd /Volumes/WingmanBackup/<wingman-dir>
exec docker compose -f docker-compose.yml -p <project-name> "$@"
EOF
chmod +x ~/bin/wingman-exec.sh

# Test
~/bin/wingman-exec.sh ps
```

---

### **Scenario C: Clean State (Nothing Running)**

**If no Wingman containers exist:**

```bash
# Deploy from SSD
cd /Volumes/WingmanBackup/<wingman-dir>

# Determine which environment
# TEST:
docker compose -f docker-compose.yml -p wingman-ssd-test --env-file .env.test up -d

# OR PRD:
docker compose -f docker-compose.prd.yml -p wingman-ssd-prd --env-file .env.prd up -d

# Create wrapper
cat > ~/bin/wingman-exec.sh << 'EOF'
#!/bin/bash
cd /Volumes/WingmanBackup/<wingman-dir>
exec docker compose -f docker-compose.yml -p wingman-ssd-test "$@"
EOF
chmod +x ~/bin/wingman-exec.sh
```

---

## 🔍 **ISOLATION VERIFICATION**

**After activation, verify isolation:**

```bash
# Test 1: Default docker should NOT see SSD Wingman
docker ps --format "{{.Names}}\t{{.Mounts}}" | grep WingmanBackup
# Expected: Empty (if properly isolated)
# OR: Shows containers (if not isolated - need fix)

# Test 2: Wrapper should show Wingman
~/bin/wingman-exec.sh ps
# Expected: Shows Wingman containers

# Test 3: AI context test
docker ps | grep wingman
# Expected: Empty if isolated
# Expected: Shows containers if NOT isolated (same daemon)
```

---

## ⚠️ **ISOLATION PROBLEM DETECTED?**

**If `docker ps | grep wingman` shows containers from SSD:**

**Problem:** Same docker daemon, no isolation (yet)

**Solution Options:**

### **Option 1: Project Name Isolation (Quick)**
```bash
# Redeploy with unique project name
cd /Volumes/WingmanBackup/<wingman-dir>
docker compose -p wingman-ssd-isolated up -d

# Update wrapper
cat > ~/bin/wingman-exec.sh << 'EOF'
#!/bin/bash
cd /Volumes/WingmanBackup/<wingman-dir>
exec docker compose -p wingman-ssd-isolated "$@"
EOF

# Test: AI should not know the project name
docker ps --filter "name=wingman-ssd-isolated"  # AI wouldn't know this name
```

### **Option 2: Network Isolation**
```bash
# Use custom network that AI doesn't know about
docker network create wingman-ssd-network

# Update compose to use this network
# Deploy with network isolation
```

### **Option 3: Accept Same Daemon + Document**
```bash
# Document that isolation is via:
# - AI doesn't know project name
# - AI doesn't know SSD path
# - CLAUDE.md rules prevent guessing
# - Wrapper provides controlled access
```

---

## 📊 **EXPECTED DISCOVERY RESULTS**

**Please run these commands and share output:**

```bash
# 1. What's on the SSD?
echo "=== SSD CONTENTS ==="
ls -la /Volumes/WingmanBackup/

# 2. Find Wingman
echo "=== WINGMAN LOCATION ==="
find /Volumes/WingmanBackup -maxdepth 2 -type d -name "*wingman*" 2>/dev/null

# 3. Current container state
echo "=== CONTAINER STATE ==="
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(NAMES|wingman)"

# 4. Docker compose files
echo "=== COMPOSE FILES ==="
find /Volumes/WingmanBackup -name "docker-compose*.yml" -type f 2>/dev/null | head -5

# 5. Execution gateway
echo "=== EXECUTION GATEWAY ==="
find /Volumes/WingmanBackup -name "execution_gateway.py" -type f 2>/dev/null

# 6. Environment files
echo "=== ENV FILES ==="
find /Volumes/WingmanBackup -name ".env*" -not -name "*.example" -type f 2>/dev/null

# 7. Check if using SSD mounts
echo "=== CONTAINER MOUNTS ==="
docker ps -a --format "{{.Names}}" | xargs -I {} docker inspect {} --format '{}: {{range .Mounts}}{{.Source}}{{end}}' 2>/dev/null | grep WingmanBackup
```

---

## 🎯 **ACTIVATION CHECKLIST**

Based on discovery results, complete these steps:

- [ ] **1. Find Wingman directory on SSD**
  - Path: _______________

- [ ] **2. Determine current state**
  - [ ] Running
  - [ ] Stopped
  - [ ] Clean (no containers)

- [ ] **3. Identify configuration**
  - [ ] Has execution gateway
  - [ ] Has docker-compose.yml
  - [ ] Has .env files
  - [ ] Environment: TEST / PRD / Both

- [ ] **4. Start/Activate Wingman**
  - Command used: _______________

- [ ] **5. Create wrapper script**
  - Path: ~/bin/wingman-exec.sh
  - Tested: [ ]

- [ ] **6. Verify isolation**
  - `docker ps | grep wingman`: Shows / Doesn't show
  - `~/bin/wingman-exec.sh ps`: Works / Fails

- [ ] **7. Document isolation level**
  - [ ] Full (AI cannot see at all)
  - [ ] Partial (Same daemon, obscure name)
  - [ ] Logical (CLAUDE.md rules)

---

## ✅ **TEST 0A-2 READINESS**

**After activation, TEST 0A-2 verification:**

```bash
# As AI (default docker)
docker ps | grep wingman
# Expected: Empty (or shows non-SSD containers only)

# As human (via wrapper)
~/bin/wingman-exec.sh ps | grep wingman
# Expected: Shows SSD Wingman containers

# Result:
# - If AI cannot see: TEST 0A-2 PASSES ✅
# - If AI can see: Need additional isolation
```

---

## 🚀 **IMMEDIATE NEXT STEPS**

**Right now, please run:**

```bash
# Discovery commands (copy/paste all at once)
echo "=== SSD CONTENTS ===" && ls -la /Volumes/WingmanBackup/ && \
echo -e "\n=== WINGMAN DIRS ===" && find /Volumes/WingmanBackup -maxdepth 2 -type d -name "*wingman*" 2>/dev/null && \
echo -e "\n=== COMPOSE FILES ===" && find /Volumes/WingmanBackup -name "docker-compose*.yml" -type f 2>/dev/null && \
echo -e "\n=== RUNNING CONTAINERS ===" && docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(NAMES|wingman)"
```

**Then share the output and I'll provide exact activation commands for your specific setup.**

---

**Status:** WAITING FOR DISCOVERY RESULTS
**Next:** Activate hardened Wingman based on current state
