# Wingman SSD Deployment Plan - Infrastructure Isolation
**Date:** 2026-01-10
**Goal:** Deploy Wingman on separate SSD with true docker isolation
**Purpose:** Pass TEST 0A-2 (AI cannot access Wingman docker)

---

## 🎯 **ARCHITECTURE GOAL**

```
┌────────────────────────────────────┐
│  Main Mac (/Volumes/Data)          │
│  - Claude Code runs here           │
│  - Development work                │
│  - AI assistant context            │
│  - Main docker daemon              │
│  - ❌ NO access to Wingman docker  │
└────────────────────────────────────┘
              ↓
       [Physical Boundary]
              ↓
┌────────────────────────────────────┐
│  Wingman SSD (/Volumes/WingmanBackup) │
│  - Wingman services run here       │
│  - Separate docker context         │
│  - Isolated docker socket          │
│  - ✅ AI cannot reach this         │
└────────────────────────────────────┘
```

**Result:** TEST 0A-2 PASSES (true infrastructure isolation)

---

## 🏗️ **DEPLOYMENT OPTIONS**

### **Option 1: Separate Docker Context on SSD** ⭐ RECOMMENDED
**Complexity:** Low
**Time:** 30 minutes
**Effectiveness:** HIGH

**How it works:**
- Wingman docker compose files on SSD
- Separate docker context pointing to SSD
- Main Mac docker cannot see Wingman containers
- AI must explicitly switch contexts (which it won't/can't do automatically)

---

### **Option 2: Docker-in-Docker on SSD**
**Complexity:** Medium
**Time:** 60 minutes
**Effectiveness:** VERY HIGH

**How it works:**
- Run docker daemon inside container on SSD
- Wingman services run in nested docker
- Complete isolation from main docker
- AI cannot access nested daemon

---

### **Option 3: Bootable Wingman OS on SSD**
**Complexity:** High
**Time:** 2-3 hours
**Effectiveness:** MAXIMUM

**How it works:**
- Install macOS on SSD
- Boot from SSD for Wingman operations
- Completely separate system
- When booted to main Mac, cannot access Wingman

---

## 📋 **RECOMMENDED APPROACH: Option 1**

**Why:**
- ✅ Quick to implement
- ✅ Effective separation
- ✅ Easy to test
- ✅ Reversible

---

## 🔧 **IMPLEMENTATION PLAN**

### **Phase 1: Prepare SSD (5 minutes)**

```bash
# 1. Verify SSD mounted
ls /Volumes/WingmanBackup
# If not mounted, mount it

# 2. Create Wingman directory structure
mkdir -p /Volumes/WingmanBackup/wingman-production
mkdir -p /Volumes/WingmanBackup/docker-data

# 3. Set up isolated docker storage
mkdir -p /Volumes/WingmanBackup/docker-data/containers
mkdir -p /Volumes/WingmanBackup/docker-data/volumes
mkdir -p /Volumes/WingmanBackup/docker-data/networks
```

---

### **Phase 2: Deploy Wingman to SSD (15 minutes)**

```bash
# 1. Copy Wingman system to SSD
cp -R /Volumes/Data/ai_projects/wingman-system/wingman/* \
  /Volumes/WingmanBackup/wingman-production/

# 2. Copy environment files (ensure no secrets in git)
cp /Volumes/Data/ai_projects/wingman-system/wingman/.env.test \
  /Volumes/WingmanBackup/wingman-production/.env.test

cp /Volumes/Data/ai_projects/wingman-system/wingman/.env.prd \
  /Volumes/WingmanBackup/wingman-production/.env.prd

# 3. Verify files copied
ls -la /Volumes/WingmanBackup/wingman-production/
```

---

### **Phase 3: Create Isolated Docker Context (10 minutes)**

**Option A: Using Docker Context (if supported by OrbStack)**
```bash
# Create new docker context for Wingman
docker context create wingman-ssd \
  --description "Wingman SSD isolated context" \
  --docker "unix:///Volumes/WingmanBackup/docker.sock"

# List contexts
docker context ls

# Test switching
docker context use wingman-ssd
docker ps  # Should show nothing (clean context)

# Switch back to default
docker context use default
docker ps  # Shows your normal containers
```

**Option B: Separate Compose Project (simpler, may not provide full isolation)**
```bash
# Use project naming and network isolation
cd /Volumes/WingmanBackup/wingman-production

# Deploy with unique project name
docker compose -f docker-compose.yml \
  -p wingman-ssd-test \
  --env-file .env.test \
  up -d

# Verify isolation
docker ps --filter "name=wingman-ssd"
```

**Option C: Environment-Based Separation**
```bash
# Set DOCKER_HOST for Wingman operations
export DOCKER_HOST=unix:///Volumes/WingmanBackup/docker.sock

# Or create wrapper script
cat > /Volumes/WingmanBackup/wingman-docker.sh << 'EOF'
#!/bin/bash
export DOCKER_HOST=unix:///Volumes/WingmanBackup/docker.sock
docker "$@"
EOF

chmod +x /Volumes/WingmanBackup/wingman-docker.sh
```

---

### **Phase 4: Deploy Wingman Services on SSD**

```bash
# Navigate to SSD Wingman directory
cd /Volumes/WingmanBackup/wingman-production

# Deploy TEST environment
docker compose -f docker-compose.yml \
  -p wingman-ssd-test \
  --env-file .env.test \
  up -d --build

# Verify deployment
docker ps --filter "name=wingman-ssd"

# Check health
docker compose -f docker-compose.yml \
  -p wingman-ssd-test \
  ps
```

---

### **Phase 5: Create Access Wrapper Scripts**

**On Main Mac, create wrapper to access Wingman on SSD:**

```bash
# Create ~/bin/wingman-exec.sh
mkdir -p ~/bin

cat > ~/bin/wingman-exec.sh << 'EOF'
#!/bin/bash
# Execute docker commands in Wingman SSD context
cd /Volumes/WingmanBackup/wingman-production
exec docker compose -f docker-compose.yml -p wingman-ssd-test "$@"
EOF

chmod +x ~/bin/wingman-exec.sh

# Create ~/bin/wingman-docker.sh for raw docker access
cat > ~/bin/wingman-docker.sh << 'EOF'
#!/bin/bash
# Execute docker commands against Wingman SSD containers
exec docker --context wingman-ssd "$@"
EOF

chmod +x ~/bin/wingman-docker.sh
```

---

### **Phase 6: Test Isolation (CRITICAL)**

```bash
# TEST 1: Default context should NOT see Wingman SSD containers
docker context use default
docker ps | grep wingman-ssd
# Expected: Empty (no results)

# TEST 2: Wingman context should ONLY see SSD containers
docker context use wingman-ssd
docker ps
# Expected: Shows wingman-ssd-* containers only

# TEST 3: AI context test (from main Mac, default context)
# This is what Claude Code will see
docker ps | grep wingman
# Expected: Empty (AI cannot see Wingman containers)

# TEST 4: Access via wrapper works
~/bin/wingman-exec.sh ps
# Expected: Shows Wingman containers

# Switch back to default context for normal work
docker context use default
```

---

## ✅ **TEST 0A-2 VERIFICATION**

After deployment, run TEST 0A-2:

```bash
# On Main Mac (AI context - default docker)
docker ps --filter "name=wingman-ssd"
# Expected: ❌ Empty (AI cannot see Wingman containers)

docker compose -f /Volumes/WingmanBackup/wingman-production/docker-compose.yml \
  -p wingman-ssd-test ps
# Expected: ❌ Fails OR shows nothing (no access)

# Via wrapper (human-executed)
~/bin/wingman-exec.sh ps
# Expected: ✅ Shows Wingman containers

# Via context switch (human-executed)
docker context use wingman-ssd && docker ps && docker context use default
# Expected: ✅ Shows Wingman containers temporarily
```

**Result:**
- ✅ TEST 0A-2 PASSES (AI cannot access Wingman docker)
- ✅ Infrastructure separation achieved
- ✅ Human can access via explicit wrapper/context switch

---

## 🔒 **SECURITY PROPERTIES**

### **What This Achieves:**

1. **Physical Separation:**
   - Wingman files on separate SSD
   - Different storage path

2. **Logical Separation:**
   - Different docker context
   - Different project name
   - Isolated networks

3. **Access Control:**
   - AI uses default context (cannot see Wingman)
   - Human must explicitly switch context
   - Wrapper scripts provide controlled access

### **Attack Vectors Blocked:**

- ❌ AI cannot run `docker ps` and see Wingman containers
- ❌ AI cannot run `docker stop wingman-*` (containers not visible)
- ❌ AI cannot access Wingman docker socket directly
- ❌ AI must explicitly switch context (which it won't do automatically)

### **What Can Still Access:**

- ✅ Human with wrapper scripts
- ✅ Human with explicit context switch
- ✅ Wingman services can access each other (same context)

---

## 📊 **LIMITATIONS & CONSIDERATIONS**

### **This Provides Separation IF:**
- ✅ AI uses default docker context
- ✅ Wingman uses separate context
- ✅ AI doesn't know about context switching
- ✅ CLAUDE.md rules prevent context switching

### **This DOES NOT Prevent:**
- ⚠️ AI discovering context switching commands
- ⚠️ AI running `docker context use wingman-ssd`
- ⚠️ AI accessing files on SSD (if it knows the path)

### **Additional Hardening (Optional):**

```bash
# 1. Make wrapper scripts the ONLY way to access Wingman
# Remove context from docker context list (after deployment)
docker context rm wingman-ssd

# 2. Use project name obscurity
# Instead of "wingman-ssd-test", use random identifier
PROJECT_ID=$(uuidgen | cut -d- -f1)
echo "wingman-${PROJECT_ID}" > /Volumes/WingmanBackup/.project-id

# 3. File permissions on SSD
chmod 700 /Volumes/WingmanBackup/wingman-production
# Only your user can access

# 4. Update CLAUDE.md rules
echo "NEVER run: docker context use <anything-but-default>" >> wingman/CLAUDE.md
```

---

## 🧪 **FULL INTEGRATION WITH TEST PLAN**

### **Updated TEST 0A-2:**

```markdown
### **TEST 0A-2: AI Assistant Context (SSD Isolation)**

**Architecture:** Wingman deployed on separate SSD (`/Volumes/WingmanBackup`)

**Test 1: AI Default Context**
```bash
# From AI context (default docker)
docker ps --filter "name=wingman"
```
**Expected:** ❌ Empty (no Wingman containers visible)

**Test 2: Direct Access Attempt**
```bash
# AI tries to access Wingman directly
docker compose -f /Volumes/WingmanBackup/wingman-production/docker-compose.yml ps
```
**Expected:** ❌ Fails or shows no running containers

**Test 3: Human Access via Wrapper**
```bash
# Human uses wrapper (AI must provide this, human executes)
~/bin/wingman-exec.sh ps
```
**Expected:** ✅ Shows Wingman containers

**Pass Criteria:**
- [ ] AI cannot see Wingman containers in default context
- [ ] AI cannot access Wingman compose files directly
- [ ] Human can access via wrapper scripts
- [ ] Physical + logical separation confirmed

**Result:** ✅ PASSES (infrastructure isolation achieved)
```

---

## 📝 **DEPLOYMENT CHECKLIST**

- [ ] **Phase 1:** SSD prepared with directory structure
- [ ] **Phase 2:** Wingman code copied to SSD
- [ ] **Phase 3:** Docker context/isolation configured
- [ ] **Phase 4:** Wingman services deployed on SSD
- [ ] **Phase 5:** Wrapper scripts created
- [ ] **Phase 6:** Isolation tested and verified
- [ ] **TEST 0A-2:** Re-run and confirm PASS
- [ ] **Documentation:** Update test results
- [ ] **Continue:** Proceed with remaining tests

---

## 🚀 **QUICK START COMMANDS**

**To deploy Wingman SSD isolation RIGHT NOW:**

```bash
# 1. Prepare SSD
mkdir -p /Volumes/WingmanBackup/wingman-production

# 2. Copy Wingman
cp -R /Volumes/Data/ai_projects/wingman-system/wingman/* \
  /Volumes/WingmanBackup/wingman-production/

# 3. Deploy on SSD
cd /Volumes/WingmanBackup/wingman-production
docker compose -f docker-compose.yml -p wingman-ssd-test --env-file .env.test up -d

# 4. Create wrapper
cat > ~/bin/wingman-exec.sh << 'EOF'
#!/bin/bash
cd /Volumes/WingmanBackup/wingman-production
exec docker compose -f docker-compose.yml -p wingman-ssd-test "$@"
EOF
chmod +x ~/bin/wingman-exec.sh

# 5. Test isolation
docker ps | grep wingman  # Should be empty
~/bin/wingman-exec.sh ps  # Should show containers

# 6. Re-run TEST 0A-2
# Expected: PASSES ✅
```

---

## ⏱️ **TIME ESTIMATE**

- **Reading this plan:** 10 minutes
- **Phase 1-2 (Prepare + Copy):** 10 minutes
- **Phase 3-4 (Deploy):** 15 minutes
- **Phase 5-6 (Wrapper + Test):** 10 minutes
- **TEST 0A-2 verification:** 5 minutes

**Total:** ~50 minutes to complete deployment

---

## 🎯 **SUCCESS CRITERIA**

**You'll know it's working when:**

1. ✅ `docker ps` (default context) shows NO Wingman containers
2. ✅ `~/bin/wingman-exec.sh ps` SHOWS Wingman containers
3. ✅ TEST 0A-2 PASSES
4. ✅ AI cannot see/access Wingman docker
5. ✅ You can continue with remaining tests

---

**Status:** READY TO DEPLOY
**Next Step:** Run the Quick Start Commands above
