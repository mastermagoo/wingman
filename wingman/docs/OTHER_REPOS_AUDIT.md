# Other Repos Approval Bypass Audit
**Created:** 2026-01-10  
**Status:** IN PROGRESS  
**Purpose:** Audit all repositories for approval bypass gaps

---

## 🎯 **AUDIT SCOPE**

**Repositories to Audit:**
1. ✅ Intel-system - **AUDITED** (wired to Wingman)
2. ✅ Mem0 - **AUDITED** (wired to Wingman)
3. ⚠️ cv-automation - **PENDING**
4. ⚠️ Other repos - **PENDING**

---

## 📊 **AUDIT RESULTS**

### **1. Intel-System** ✅

**Status:** ✅ **REMEDIATED**

**Findings:**
- ✅ `tools/dr_with_approval.py` created
- ✅ Uses `WingmanApprovalClient`
- ✅ All destructive operations require approval
- ✅ Stop and rebuild operations protected

**Evidence:**
- File: `/Volumes/Data/ai_projects/intel-system/tools/dr_with_approval.py`
- Integration: Uses `WingmanApprovalClient` library
- Status: All operations require Wingman approval

---

### **2. Mem0** ✅

**Status:** ✅ **REMEDIATED**

**Findings:**
- ✅ `tools/dr_with_approval.py` created
- ✅ Uses `WingmanApprovalClient`
- ✅ All destructive operations require approval

**Evidence:**
- File: `/Volumes/Data/ai_projects/mem0-system/tools/dr_with_approval.py`
- Integration: Uses `WingmanApprovalClient` library
- Status: All operations require Wingman approval

---

### **3. cv-automation** ⚠️

**Status:** ⚠️ **GAPS FOUND - REMEDIATION REQUIRED**

**Findings:**
- ✅ **Docker operations found:** 52 files contain Docker commands
- ✅ **Destructive operations found:** 
  - `scripts/promote_test_to_prod.sh` - Production deployment script
  - `scripts/promote_dev_to_test.sh` - Test deployment script
  - `docker/docker-compose.dev.yml` - Development stack
  - `docker/docker-compose.prod.yml` - Production stack
- ❌ **WingmanApprovalClient:** NOT integrated
- ❌ **DR wrapper script:** NOT created

**Critical Scripts Found:**
1. `scripts/promote_test_to_prod.sh` - Executes production deployments
2. `scripts/promote_dev_to_test.sh` - Executes test deployments
3. Multiple docker-compose files for dev/test/prod environments

**Action Required:**
1. ✅ **AUDITED** - Repository located and scanned
2. ⚠️ **REQUIRED:** Create `tools/dr_with_approval.py` wrapper
3. ⚠️ **REQUIRED:** Integrate WingmanApprovalClient into promotion scripts
4. ⚠️ **REQUIRED:** Update deployment scripts to require approval
5. ⚠️ **REQUIRED:** Update documentation (CLAUDE.md) with approval rules

**Remediation Priority:** HIGH (production deployment scripts found)

---

### **4. automation-stack** ⚠️

**Status:** ⚠️ **PENDING AUDIT** (timeout during scan)

**Findings:**
- ⚠️ **Scan timeout** - Repository too large or complex
- ⚠️ **Docker operations:** Likely present (docker-compose files found)
- ❌ **WingmanApprovalClient:** Not verified (scan timeout)

**Action Required:**
1. Manual audit required (repository too large for automated scan)
2. Check for docker-compose files
3. Check for deployment scripts
4. Integrate WingmanApprovalClient if Docker operations found

---

### **5. Other Repositories** ⚠️

**Status:** ⚠️ **PENDING AUDIT**

**Repositories Found:**
- `prd_clones/` - Status unknown
- `Skool - David - Cursor - Codex/` - Status unknown

**Repositories to Check:**
- [ ] Any other repos in `/Volumes/Data/ai_projects/`
- [ ] Any repos that interact with Docker
- [ ] Any repos that modify system state
- [ ] Any repos with deployment scripts

**Audit Script:**
```bash
#!/bin/bash
# audit_all_repos.sh

REPO_DIR="/Volumes/Data/ai_projects"

for repo in "$REPO_DIR"/*; do
    if [ -d "$repo" ]; then
        echo "Auditing: $(basename "$repo")"
        
        # Check for Docker operations
        if grep -rq "docker compose\|docker stop\|docker rm" "$repo" 2>/dev/null; then
            echo "  ⚠️  Found Docker operations"
        fi
        
        # Check for destructive operations
        if grep -rq "rm -rf\|unlink\|delete" "$repo" 2>/dev/null; then
            echo "  ⚠️  Found destructive operations"
        fi
        
        # Check for WingmanApprovalClient
        if grep -rq "WingmanApprovalClient" "$repo" 2>/dev/null; then
            echo "  ✅ Uses WingmanApprovalClient"
        else
            echo "  ❌ Does NOT use WingmanApprovalClient"
        fi
    fi
done
```

---

## 🔧 **REMEDIATION TEMPLATE**

For any repository found with bypass gaps:

### **Step 1: Create DR Wrapper Script**

**File:** `tools/dr_with_approval.py`

```python
#!/usr/bin/env python3
"""
<REPO-NAME> DR Operations (HITL-Protected)
All destructive operations require Wingman approval
"""
from wingman_approval_client import WingmanApprovalClient
import subprocess
import sys

def stop_containers(env="test"):
    """Stop containers (requires approval)"""
    client = WingmanApprovalClient()
    
    instruction = f"""
    OPERATION: Stop all <REPO-NAME> {env.upper()} containers
    SCOPE: <describe scope>
    RISK: <describe risk>
    ROLLBACK: <describe rollback>
    """
    
    approved = client.request_approval(
        worker_id="<repo>-dr-script",
        task_name=f"Stop <REPO-NAME> {env.upper()}",
        instruction=instruction,
        deployment_env=env,
    )
    
    if not approved:
        print("❌ Operation cancelled - approval denied/timeout")
        return False
    
    # Execute ONLY if approved
    subprocess.run([
        "docker", "compose",
        "-f", f"docker-compose.{env}.yml",
        "-p", f"<repo>-{env}",
        "stop"
    ])
    
    return True

# Similar functions for remove, rebuild, etc.
```

### **Step 2: Update Documentation**

Add to repo's README or CLAUDE.md:
```
## Destructive Operations

All destructive operations (stop, remove, rebuild) MUST use:
- `tools/dr_with_approval.py` - Wrapper script with Wingman approval
- DO NOT execute docker compose commands directly
- DO NOT bypass approval gates
```

### **Step 3: Update AI Agent Rules**

If repo has CLAUDE.md, add:
```
RULE: DESTRUCTIVE OPERATIONS REQUIRE WINGMAN APPROVAL
- Use tools/dr_with_approval.py for all Docker operations
- Never execute docker compose stop/rm/down without approval
```

---

## 📋 **AUDIT CHECKLIST**

For each repository:

- [ ] **Repository identified**
- [ ] **Docker operations found?** (Yes/No)
- [ ] **Destructive operations found?** (Yes/No)
- [ ] **WingmanApprovalClient integrated?** (Yes/No)
- [ ] **DR wrapper script created?** (Yes/No)
- [ ] **Documentation updated?** (Yes/No)
- [ ] **AI agent rules updated?** (Yes/No)
- [ ] **Status:** (REMEDIATED/PENDING/NO_ACTION_NEEDED)

---

## 🎯 **SUCCESS CRITERIA**

**All repositories are compliant when:**
1. ✅ All destructive operations use WingmanApprovalClient
2. ✅ No direct Docker operations bypass approval
3. ✅ All repos have `dr_with_approval.py` if they have DR operations
4. ✅ Documentation updated to reflect approval requirements
5. ✅ AI agent rules enforce approval gates

---

**Next Action:** Run audit script to identify all repositories requiring remediation.
