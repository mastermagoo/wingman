# Docker Wrapper Setup Guide

**Phase 5 Requirement**: MANDATORY for all operators
**Purpose**: Infrastructure-level protection against unauthorized Docker operations
**Date**: 2026-02-14

---

## What is the Docker Wrapper?

The Docker wrapper is a **mandatory shell script** that intercepts all `docker` and `docker compose` commands. It blocks destructive operations (stop, rm, down, build, etc.) and requires Wingman approval before execution.

**Why Required**:
- Layer 2 protection in the three-layer security model
- Prevents accidental/unauthorized container stops, deletions, rebuilds
- Enforces human-in-the-loop approval for destructive operations
- Audit trail of all blocked commands

**What it Blocks**:
- `docker stop`, `docker rm`, `docker kill`, `docker restart`
- `docker compose down`, `docker compose stop`, `docker compose rm`
- `docker build`, `docker compose build`, `docker compose up --build`
- `docker system prune`, `docker volume rm`, `docker network rm`

**What it Allows**:
- `docker ps`, `docker logs`, `docker version`, `docker info`
- `docker compose ps`, `docker compose logs`, `docker compose config`
- Any read-only operation

---

## Setup Instructions

### Option 1: Permanent Setup (Recommended)

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
# Wingman Docker Wrapper (MANDATORY - Phase 5)
export PATH="/Volumes/Data/ai_projects/wingman-system/wingman/tools:$PATH"
export DOCKER_BIN="/Users/kermit/.orbstack/bin/docker"
```

**Apply changes**:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

### Option 2: Per-Session Setup

Run in each terminal session:

```bash
export PATH="/Volumes/Data/ai_projects/wingman-system/wingman/tools:$PATH"
export DOCKER_BIN="/Users/kermit/.orbstack/bin/docker"
```

---

## Verification Steps

### Step 1: Check Wrapper is Active

```bash
which docker
# Expected: /Volumes/Data/ai_projects/wingman-system/wingman/tools/docker
```

If output is `/usr/local/bin/docker` or similar, wrapper is **NOT active** - repeat setup.

### Step 2: Test Safe Command

```bash
docker ps
```

Expected: Command executes normally (shows running containers)

### Step 3: Test Blocked Command

```bash
docker stop test-container
```

**Expected Output**:
```
❌ BLOCKED: Destructive docker command requires Wingman approval

Command blocked: docker stop test-container

To execute this command:
1. Submit approval request to Wingman API: POST /approvals/request
2. Wait for approval via Telegram
3. Execute via Execution Gateway with capability token

See: docs/04-user-guides/APPROVAL_WORKFLOW_WITH_VALIDATION.md
```

Exit code: **1** (blocked)

### Step 4: Run Verification Tests

```bash
/Volumes/Data/ai_projects/wingman-system/wingman/tools/verify_wrapper_enforcement.sh
```

Expected: **12/12 tests passing**

---

## Usage Examples

### Allowed (Read-Only Commands)

```bash
# These work normally
docker ps
docker logs wingman-test-api-1
docker compose -f docker-compose.yml -p wingman-test ps
docker version
docker inspect wingman-test-postgres-1
```

### Blocked (Require Approval)

```bash
# These are BLOCKED and require Wingman approval
docker stop wingman-test-api-1
docker rm -f wingman-test-api-1
docker compose -f docker-compose.yml -p wingman-test down
docker compose -f docker-compose.yml -p wingman-test up -d --build
docker system prune -f
```

---

## How to Execute Blocked Commands

When wrapper blocks a command, you must go through the approval flow:

### Step 1: Submit Approval Request

```bash
curl -X POST http://127.0.0.1:8101/approvals/request \
  -H "Content-Type: application/json" \
  -H "X-Wingman-Approval-Request-Key: $REQUEST_KEY" \
  -d '{
    "worker_id": "operator_manual",
    "task_name": "Stop container for maintenance",
    "instruction": "DELIVERABLES: Stop wingman-test-api container for maintenance. Context: Need to apply config changes.",
    "deployment_env": "test",
    "claim": "I will execute: docker stop wingman-test-api-1"
  }'
```

Response includes `approval_id` and `capability_token` (if auto-approved).

### Step 2: Wait for Approval (if Pending)

- Check Telegram for approval notification
- Mark approves/rejects via Telegram buttons
- If rejected, request is blocked

### Step 3: Execute via Execution Gateway

Use the `capability_token` from approval response:

```bash
curl -X POST http://127.0.0.1:8101/execute \
  -H "Authorization: Bearer $CAPABILITY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "docker stop wingman-test-api-1"}'
```

**See**: [APPROVAL_WORKFLOW_WITH_VALIDATION.md](../04-user-guides/APPROVAL_WORKFLOW_WITH_VALIDATION.md)

---

## Troubleshooting

### Issue: `which docker` shows wrong path

**Symptom**: `which docker` returns `/usr/local/bin/docker` instead of wrapper path

**Fix**:
```bash
# Check PATH
echo $PATH | tr ':' '\n' | grep wingman

# If missing, re-export PATH
export PATH="/Volumes/Data/ai_projects/wingman-system/wingman/tools:$PATH"

# Verify
which docker
```

### Issue: Wrapper not blocking destructive commands

**Symptom**: `docker stop` executes without blocking

**Possible Causes**:
1. Using absolute path (bypasses wrapper): `/usr/bin/docker stop`
2. Using `sudo docker` (bypasses wrapper)
3. `DOCKER_BIN` not set correctly

**Fix**:
- Never use absolute paths to docker binaries
- Don't use `sudo docker` (use wrapper instead)
- Set `DOCKER_BIN` correctly:
  ```bash
  export DOCKER_BIN="/Users/kermit/.orbstack/bin/docker"
  ```

### Issue: Verification tests failing

**Symptom**: `verify_wrapper_enforcement.sh` shows failures

**Debug**:
```bash
# Check wrapper script exists
ls -la /Volumes/Data/ai_projects/wingman-system/wingman/tools/docker*

# Check permissions
chmod +x /Volumes/Data/ai_projects/wingman-system/wingman/tools/docker*

# Test wrapper directly
/Volumes/Data/ai_projects/wingman-system/wingman/tools/docker-wrapper.sh stop test
# Expected: BLOCKED message
```

---

## Known Limitations

### 1. Absolute Path Bypass

Wrapper can be bypassed with absolute paths:
```bash
/usr/bin/docker stop container  # ❌ BYPASSES WRAPPER
```

**Mitigation**:
- **PROHIBITED** in CLAUDE.md - code reviews must flag this
- Layer 1 (container isolation) still protects containers
- Layer 3 (approval flow) still applies if executed via API

**Risk**: LOW (requires intentional bypass + code review miss)

### 2. DOCKER_HOST Environment Variable

Setting `DOCKER_HOST` bypasses wrapper:
```bash
DOCKER_HOST=unix:///var/run/docker.sock docker stop container
```

**Mitigation**:
- Layer 1 (container isolation) prevents socket access in non-gateway containers
- Socket not accessible in most contexts

**Risk**: VERY LOW (socket not accessible)

### 3. Direct Socket Access

Direct socket access via curl/socat bypasses wrapper:
```bash
curl --unix-socket /var/run/docker.sock -X POST http://localhost/containers/xyz/stop
```

**Mitigation**:
- Layer 1 (container isolation) prevents socket access
- Socket not mounted in non-gateway containers

**Risk**: VERY LOW (socket not accessible)

---

## For AI Agents (Claude Code, Cursor, etc.)

**CRITICAL**: AI agents MUST use the wrapper for all docker operations.

**Rules**:
1. ✅ Always use `docker` command (assumes wrapper in PATH)
2. ❌ NEVER use absolute paths: `/usr/bin/docker`, `/usr/local/bin/docker`, etc.
3. ❌ NEVER bypass wrapper with `sudo docker` or `DOCKER_HOST=...`
4. ✅ For blocked commands, submit approval request via Wingman API
5. ✅ Include wrapper setup in all deployment scripts:
   ```bash
   export PATH="${SCRIPT_DIR}/tools:${PATH}"
   export DOCKER_BIN="${DOCKER_BIN:-/Users/kermit/.orbstack/bin/docker}"
   ```

**See**: [CLAUDE.md](../../CLAUDE.md) - Section "Docker Wrapper (MANDATORY - Phase 5 Enforcement)"

---

## For Deployment Scripts

All deployment scripts MUST include wrapper setup at the top:

```bash
#!/bin/bash
set -euo pipefail

################################################################################
# MANDATORY: Docker Wrapper Enforcement (Phase 5)
################################################################################
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER_DIR="${SCRIPT_DIR}/tools"
export PATH="${WRAPPER_DIR}:${PATH}"

# Set DOCKER_BIN for wrapper fallback
if [[ -z "${DOCKER_BIN:-}" ]]; then
    for candidate in /usr/local/bin/docker /opt/homebrew/bin/docker "${HOME}/.orbstack/bin/docker" /usr/bin/docker; do
        if [[ -x "$candidate" ]]; then
            export DOCKER_BIN="$candidate"
            break
        fi
    done
fi

# Verify wrapper is active (optional but recommended)
DOCKER_CMD="$(command -v docker 2>/dev/null || echo '')"
if [[ "$DOCKER_CMD" != *"/tools/docker"* ]]; then
    echo "⚠️  WARNING: docker may not be using wrapper" >&2
fi
################################################################################

# ... rest of script
```

**Files already refactored**:
- ✅ `deploy_test_to_prd.sh`
- ✅ `deploy.sh`
- ✅ `ai-workers/scripts/AUTONOMOUS_DEPLOY_FIX.py`
- ✅ `ai-workers/scripts/orchestration/AUTONOMOUS_DEPLOY_FIX.py`

---

## Wrapper Files Reference

| File | Purpose | Location |
|------|---------|----------|
| `docker-wrapper.sh` | Main wrapper script | `tools/docker-wrapper.sh` |
| `docker` | Shim (symlink/wrapper invoked when in PATH) | `tools/docker` |
| `verify_wrapper_enforcement.sh` | Verification test suite | `tools/verify_wrapper_enforcement.sh` |

---

## Related Documentation

- [Docker Wrapper Audit](DOCKER_WRAPPER_AUDIT.md) - Comprehensive audit of all docker invocation paths
- [Phase 5 Complete](../deployment/PHASE_5_DOCKER_WRAPPER_ENFORCEMENT_COMPLETE.md) - Implementation report
- [Operations Runbook](AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md) - Includes wrapper prerequisites
- [PRD Deployment Plan](../deployment/AAA_PRD_DEPLOYMENT_PLAN.md) - Includes wrapper setup

---

**Setup Complete?** Run verification:
```bash
/Volumes/Data/ai_projects/wingman-system/wingman/tools/verify_wrapper_enforcement.sh
```

Expected: **12/12 tests passing** ✅

---

**End of Setup Guide**
