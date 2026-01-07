# Wingman Review Required - GitHub Reconciliation & Clone Plan

**Date:** 2025-11-23 00:16
**Reviewer:** Wingman Overwatch
**Status:** ⏳ PENDING APPROVAL

## Executive Summary

We discovered critical GitHub repository chaos during DR test preparation. This document outlines the reconciliation plan and robust PRD→TEST cloning procedure. **Wingman approval required before execution.**

## Issues Discovered

### 1. **Mem0 Repository Confusion** ❌
- **Problem:** Mem0 files exist in THREE locations:
  1. `/Volumes/Data/ai_projects/mem0-platform` (wrong repo)
  2. `intel-system/deploy/docker/mem0_tailscale/` (not in git, working)
  3. `intel-system/deployment/docker/mem0_tailscale/` (in git, corrupted)

- **Root Cause:** SMB corruption + manual folder rename (deployment→deploy)

- **Correct Source of Truth:** https://github.com/mastermagoo/mem0 (has full working version in root)

### 2. **Intel-System Embedded Mem0** ❌
- **Problem:** Mem0 embedded in intel-system repo, but mem0 has its own repo
- **Impact:** Confusion, duplicate code, unclear deployment

### 3. **deploy/ vs deployment/ Folders** ❌
- **Problem:** Two folders with different names, neither fully correct
- **Impact:** Git tracking chaos, unclear which is authoritative

## Proposed Solutions

### Solution 1: Repository Separation ✅

**Intel-System Repo** (mastermagoo/intel_sys):
- Contains ONLY intel-system microservices
- 3 compose files: infra, services, monitoring
- 33 containers total
- Remove all mem0 references

**Mem0 Repo** (mastermagoo/mem0):
- Contains ONLY mem0 system
- 1 compose file in root: docker-compose.prd.yml
- 5 containers: postgres, neo4j, mem0, grafana, telegram_bot
- Already up-to-date on GitHub ✅

**Benefits:**
- Clean separation of concerns
- Independent versioning
- No more folder confusion
- Easier DR recovery

### Solution 2: Robust Clone Script ✅

**Script:** `/Volumes/Data/ai_projects/intel-system/scripts/clone_prd_to_test.sh`

**Features:**
- ✅ Pre-flight validation (PRD must be running)
- ✅ Automatic TEST compose file generation
- ✅ Port offset strategy (+10000)
- ✅ Data directory creation
- ✅ Network creation
- ✅ Sequential startup (infra→services→monitoring)
- ✅ Post-deployment validation
- ✅ Comprehensive logging
- ✅ Error handling
- ✅ Rollback capability (--force flag)

**Usage:**
```bash
# Standard clone
./scripts/clone_prd_to_test.sh

# Force recreation
./scripts/clone_prd_to_test.sh --force

# Skip validation (for testing)
./scripts/clone_prd_to_test.sh --skip-validation
```

## Execution Plan

### Phase 1: GitHub Reconciliation (15 minutes)

#### Step 1.1: Clone mem0 Repo Locally
```bash
cd /Volumes/Data/ai_projects
git clone https://github.com/mastermagoo/mem0.git mem0-system
```
**Expected:** Repo cloned with docker-compose.prd.yml in root

#### Step 1.2: Verify Mem0 Repo Current
```bash
cd mem0-system
git log -1 --oneline
ls -la docker-compose.prd.yml mem0_gds_patch_v2.py start_mem0_with_patch.sh
```
**Expected:** All files present, last commit recent

#### Step 1.3: Update Mem0 Repo (if needed)
```bash
# Compare running version vs GitHub
diff docker-compose.prd.yml \
     /Volumes/Data/ai_projects/intel-system/deploy/docker/mem0_tailscale/docker-compose.prd.yml

# If differences, update and push
git add docker-compose.prd.yml
git commit -m "update: Latest working PRD configuration"
git push origin main
```

#### Step 1.4: Clean Up intel-system Repo
```bash
cd /Volumes/Data/ai_projects/intel-system

# Remove embedded mem0 folders
rm -rf deploy/docker/mem0_tailscale/
rm -rf deployment/docker/mem0_tailscale/
rm -rf deploy/docker/ deployment/docker/  # if empty
rmdir deploy/ deployment/  # if empty

# Update .gitignore
echo "deploy/" >> .gitignore
echo "deployment/" >> .gitignore

# Commit cleanup
git add -A
git commit -m "refactor: Remove embedded mem0 - now separate repo

- Removed deploy/ and deployment/ folders
- Mem0 now in mastermagoo/mem0 repo
- Intel-system focused on core microservices only

Closes #reconciliation"
```

#### Step 1.5: Push Clean intel-system
```bash
git push origin wingman
```

**Expected:** Clean push, no mem0 files in intel-system repo

### Phase 2: TEST Environment Clone (10 minutes)

#### Step 2.1: Stop Existing TEST (if any)
```bash
./scripts/clone_prd_to_test.sh --force
```
**Expected:** All TEST containers stopped and removed

#### Step 2.2: Validate Script Output
Check log file for:
- ✅ All PRD containers detected
- ✅ All compose files found
- ✅ TEST files created
- ✅ Networks created
- ✅ Containers started
- ✅ Health checks passing

#### Step 2.3: Verify TEST Deployment
```bash
# Count containers
docker ps --filter "name=.*-test" --format "{{.Names}}" | wc -l
# Expected: ~36-38 containers

# Check health
docker ps --filter "name=.*-test" --filter "health=healthy" --format "{{.Names}}" | wc -l
# Expected: 30+ healthy

# Test endpoints
curl -f http://localhost:18000/health  # Intel gateway
curl -f http://localhost:18888/docs    # Mem0 API
```

### Phase 3: Documentation & Automation (5 minutes)

#### Step 3.1: Add to Cron (Optional)
```bash
# Weekly TEST refresh every Sunday at 2 AM
0 2 * * 0 /Volumes/Data/ai_projects/intel-system/scripts/clone_prd_to_test.sh --force >> /tmp/clone_cron.log 2>&1
```

#### Step 3.2: Update Deployment Docs
```bash
# Create DEPLOYMENT.md in both repos
cd /Volumes/Data/ai_projects/intel-system
# (already documented in GITHUB_RECONCILIATION_PLAN.md)

cd /Volumes/Data/ai_projects/mem0-system
# Create README with deployment instructions
```

## Wingman Review Checklist

### Safety Checks
- [ ] **Backup Status:** All PRD containers running and healthy
- [ ] **Git Status:** All important files committed to git
- [ ] **Data Persistence:** All volume mounts verified
- [ ] **Rollback Plan:** Can restore from GitHub if issues

### Validation Checks
- [ ] **Clone Script:** Reviewed and approved
- [ ] **Reconciliation Plan:** Logical and safe
- [ ] **Execution Steps:** Clear and specific
- [ ] **Error Handling:** Adequate safeguards

### Compliance Checks
- [ ] **CLAUDE.md:** No hardcoding violations
- [ ] **GitHub:** Proper repo separation
- [ ] **Documentation:** Complete and accurate
- [ ] **Automation Ready:** Script suitable for cron

## Risks & Mitigations

### Risk 1: Mem0 Repo Not Current
- **Likelihood:** Medium
- **Impact:** High (clone would fail)
- **Mitigation:** Verify and update in Step 1.2-1.3

### Risk 2: Port Conflicts
- **Likelihood:** Low
- **Impact:** Medium (TEST won't start)
- **Mitigation:** Script uses +10000 offset, validates before start

### Risk 3: Data Loss During Cleanup
- **Likelihood:** Very Low
- **Impact:** High
- **Mitigation:** Only removing tracked files, PRD data untouched

### Risk 4: Script Fails Mid-Execution
- **Likelihood:** Low
- **Impact:** Medium (partial TEST environment)
- **Mitigation:** Script uses `set -euo pipefail`, stops on error

## Success Criteria

### GitHub Reconciliation
- [ ] Mem0 repo cloned locally at `/Volumes/Data/ai_projects/mem0-system`
- [ ] Mem0 GitHub repo up-to-date
- [ ] Intel-system repo clean (no mem0 files)
- [ ] Both repos pushed to GitHub

### TEST Environment
- [ ] 33+ intel-system TEST containers running
- [ ] 5 mem0 TEST containers running
- [ ] 30+ containers healthy
- [ ] All TEST endpoints responding
- [ ] No port conflicts with PRD

### Documentation
- [ ] GITHUB_RECONCILIATION_PLAN.md complete
- [ ] clone_prd_to_test.sh documented and executable
- [ ] Deployment instructions clear
- [ ] Cron automation ready (optional)

## Wingman Decision

**⏳ PENDING APPROVAL**

Options:
1. ✅ **APPROVE** - Execute plan as written
2. ⚠️ **APPROVE WITH MODIFICATIONS** - Specify changes
3. ❌ **REJECT** - Explain concerns

**Wingman Signature:** _______________________
**Date:** _______________________
**Comments:**

---

## Execution Log

**Start Time:** _______________________
**End Time:** _______________________
**Status:** _______________________
**Issues:** _______________________

**Final Container Counts:**
- Intel-system PRD: _____ / 33
- Mem0 PRD: _____ / 5
- Intel-system TEST: _____ / 33
- Mem0 TEST: _____ / 5
- **Total:** _____ containers

**Wingman Verification:** _______________________
