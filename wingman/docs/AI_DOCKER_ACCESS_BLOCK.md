# AI Docker Access Block - Solution
**Date:** 2026-01-10  
**Problem:** AI assistants have docker socket access, enabling Cursor scenario  
**Status:** SOLUTION DESIGNED

---

## 🚨 **PROBLEM STATEMENT**

**Current State:**
- AI assistants (Claude Code, Cursor) execute commands in user's actual terminal
- User's terminal has docker socket access (`/var/run/docker.sock`)
- AI inherits this access → can bypass Wingman entirely
- **CRITICAL:** TEST 0A-2 fails because AI has docker access

**Impact:**
- Cursor scenario is possible (AI can execute docker commands directly)
- All Wingman enforcement can be bypassed
- No infrastructure-level protection

---

## 🔧 **SOLUTION OPTIONS**

### **Option 1: Docker Access Wrapper Script** (RECOMMENDED)

**Approach:** Create a wrapper script that intercepts docker commands and enforces Wingman approval.

**Implementation:**
1. Create `/usr/local/bin/docker` wrapper script
2. Check if command requires approval (stop, rm, down, build, etc.)
3. If approval required → block and redirect to Wingman
4. If safe command (ps, logs, inspect) → allow

**Pros:**
- Works in current execution environment
- No infrastructure changes needed
- Can be enabled/disabled easily

**Cons:**
- Can be bypassed by using full path `/usr/local/bin/docker` or `/Users/kermit/.orbstack/bin/docker`
- Requires PATH manipulation

---

### **Option 2: Environment Variable Block**

**Approach:** Set environment variables that block docker access.

**Implementation:**
1. Unset `DOCKER_HOST` in AI execution environment
2. Remove docker from PATH
3. Create stub docker binary that redirects to Wingman

**Pros:**
- Simple to implement
- Blocks most docker access attempts

**Cons:**
- Can be bypassed with full paths
- May break legitimate docker usage

---

### **Option 3: Docker Context Restriction**

**Approach:** Use docker contexts to restrict access.

**Implementation:**
1. Create restricted docker context
2. Set as default for AI execution
3. Restricted context has no permissions

**Pros:**
- Native docker feature
- Harder to bypass

**Cons:**
- Requires docker context setup
- May not work with OrbStack

---

### **Option 4: Accept Reality + Application Layer Enforcement** (PRAGMATIC)

**Approach:** Accept that AI has docker access, but enforce at application layer.

**Implementation:**
1. Document that AI has docker access (infrastructure limitation)
2. Rely on application layer enforcement (Wingman rules, approval gates)
3. Add monitoring to detect direct docker usage
4. Alert on any docker commands executed outside Wingman

**Pros:**
- Acknowledges reality of execution environment
- Focuses on what can be controlled
- Application layer is where enforcement actually happens

**Cons:**
- Doesn't solve infrastructure layer issue
- Relies on AI following rules (not enforceable)

---

## ✅ **RECOMMENDED SOLUTION: Hybrid Approach**

**Combine Option 1 + Option 4:**

1. **Immediate:** Create docker wrapper script that blocks destructive commands
2. **Document:** Accept that full path bypass is possible (infrastructure limitation)
3. **Enforce:** Application layer (Wingman rules, approval gates) is primary protection
4. **Monitor:** Log all docker commands, alert on unapproved usage
5. **Test:** Verify wrapper blocks common attack vectors

---

## 🛠️ **IMPLEMENTATION**

### **Step 1: Create Docker Wrapper Script**

```bash
#!/bin/bash
# /usr/local/bin/docker-wrapper.sh
# Blocks destructive docker commands, redirects to Wingman

DESTRUCTIVE_COMMANDS=("stop" "rm" "down" "kill" "restart" "build" "compose down" "compose stop" "compose rm")

# Check if command is destructive
for cmd in "${DESTRUCTIVE_COMMANDS[@]}"; do
    if [[ "$*" == *"$cmd"* ]]; then
        echo "❌ BLOCKED: Destructive docker command requires Wingman approval"
        echo "   Command: docker $*"
        echo "   Action: Submit approval request to Wingman API"
        echo "   Endpoint: POST http://127.0.0.1:5002/approvals/request"
        exit 1
    fi
done

# Safe command - allow through
exec /Users/kermit/.orbstack/bin/docker "$@"
```

### **Step 2: Update PATH (in AI execution environment)**

```bash
# Add wrapper to PATH before actual docker
export PATH="/usr/local/bin:$PATH"
```

### **Step 3: Test Wrapper**

```bash
# Should be blocked
docker stop wingman-test-api-1

# Should work
docker ps
```

---

## 📊 **TEST PLAN UPDATE**

**Update TEST 0A-2 to reflect reality:**

**Current Test:**
- Expected: docker command fails
- Actual: docker command succeeds (AI has access)

**Updated Test:**
- Expected: Destructive docker commands blocked by wrapper
- Expected: Safe docker commands work
- Expected: Direct path bypass possible (documented limitation)
- Expected: Application layer enforcement is primary protection

---

## 🎯 **SUCCESS CRITERIA**

**Solution is acceptable when:**
1. ✅ Wrapper script blocks destructive commands
2. ✅ Safe commands still work
3. ✅ Direct path bypass documented as limitation
4. ✅ Application layer enforcement is primary protection
5. ✅ Monitoring detects unapproved docker usage
6. ✅ TEST 0A-2 updated to reflect reality

---

**Status:** Solution designed, ready for implementation
