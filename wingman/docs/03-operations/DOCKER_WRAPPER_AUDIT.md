# Docker Wrapper Enforcement Audit Report

**Status**: ACTIVE
**Created**: 2026-02-14
**Author**: Claude Code (Phase 5 - Docker Wrapper Enforcement)
**Purpose**: Comprehensive audit of all Docker invocation paths to ensure mandatory wrapper usage

---

## Executive Summary

This audit identifies all Docker invocation points in the Wingman codebase and categorizes them by risk level and required action. The Docker wrapper (`tools/docker-wrapper.sh`) exists and blocks destructive commands, but it is currently **optional** and can be bypassed.

**Key Findings**:
- **Total Docker invocations found**: 215+ across scripts, Python, docs, and tests
- **High-risk bypass points**: 4 (scripts that execute destructive Docker commands)
- **Medium-risk**: Documentation with copy-paste commands (needs wrapper setup instructions)
- **Low-risk**: Test files, archived docs, read-only commands

**Recommendation**: Make wrapper mandatory via PATH setup in all execution contexts (shell, scripts, runbooks, CI).

---

## Audit Methodology

### Search Strategy
```bash
# Pattern 1: Docker compose commands
grep -r "docker compose" --include="*.py" --include="*.sh" --include="*.md"

# Pattern 2: Direct docker commands
grep -r "docker (stop|rm|down|kill|restart|build)" --include="*.py" --include="*.sh" --include="*.md"

# Pattern 3: Absolute path bypasses
grep -r "/usr/bin/docker|/usr/local/bin/docker" --include="*.py" --include="*.sh" --include="*.md"

# Pattern 4: Python subprocess docker calls
grep -r "subprocess.*docker|os\.system.*docker" --include="*.py"
```

### Risk Classification
- **SAFE**: Read-only commands (ps, logs, version), already use wrapper, or in test fixtures
- **MEDIUM**: Scripts that could invoke destructive commands but have approval gates
- **HIGH**: Direct destructive invocations without approval gates or wrapper enforcement
- **DOC**: Documentation examples (need wrapper setup instructions added)

---

## Findings by Category

### 1. Shell Scripts (Deployment/Operations)

#### HIGH RISK: Scripts with Direct Destructive Commands

| File | Line | Command | Risk Level | Action Required |
|------|------|---------|------------|-----------------|
| `deploy_test_to_prd.sh` | 259 | `docker compose -f ... ps -q` | SAFE | None (read-only) |
| `deploy_test_to_prd.sh` | 436 | `docker rm -f` | **HIGH** | Refactor to use wrapper |
| `deploy_test_to_prd.sh` | 470 | `docker compose ... up -d --build` | **HIGH** | Refactor to use wrapper |
| `deploy.sh` | 42, 72, 84, 96 | `docker-compose` (legacy) | **MEDIUM** | Refactor to use wrapper + compose v2 |
| `backup_wingman_db.sh` | N/A | No docker commands | SAFE | None |
| `deploy-secure-production.sh` | 304, 305 | `docker-compose` (legacy) | **MEDIUM** | Refactor to use wrapper |

**Analysis**:
- `deploy_test_to_prd.sh`: Critical production deployment script. Lines 436 and 470 execute destructive commands **after HITL approval** but do not use wrapper. Bypass risk: can be circumvented by calling `/usr/bin/docker` directly.
- `deploy.sh`: Legacy script using `docker-compose` (v1 syntax). Should be updated to compose v2 and wrapper.
- `deploy-secure-production.sh`: Phase 5 secure deployment script. Uses legacy compose. Should use wrapper.

**Recommendation**:
- Prepend wrapper to PATH at script start: `export PATH="/Volumes/Data/ai_projects/wingman-system/wingman/tools:$PATH"`
- Or call wrapper explicitly: `/Volumes/Data/ai_projects/wingman-system/wingman/tools/docker-wrapper.sh compose ...`

---

#### SAFE: Scripts Already Using Wrapper or Read-Only

| File | Commands | Status |
|------|----------|--------|
| `tools/verify_test_privilege_removal.sh` | `docker compose ps` (read-only) | SAFE |
| `tools/verify_approval_bypass.sh` | `docker compose ps` (read-only) | SAFE |
| `tools/test_execution_gateway.sh` | `docker compose exec` (safe within containers) | SAFE |
| `ai-workers/run_orchestrator.sh` | No docker commands | SAFE |
| `ai-workers/setup_venv.sh` | No docker commands | SAFE |
| `monitor_orchestrator.sh` | No docker commands | SAFE |

---

### 2. Python Code

#### HIGH RISK: Direct subprocess Docker Calls

| File | Line | Command | Risk Level | Action Required |
|------|------|---------|------------|-----------------|
| `ai-workers/scripts/AUTONOMOUS_DEPLOY_FIX.py` | 195, 197 | `subprocess.run(["docker", "stop/rm", ...])` | **HIGH** | Refactor to call wrapper script |
| `ai-workers/scripts/orchestration/AUTONOMOUS_DEPLOY_FIX.py` | 195, 197 | `subprocess.run(["docker", "stop/rm", ...])` | **HIGH** | Refactor to call wrapper script |

**Analysis**:
- Two Python scripts (`AUTONOMOUS_DEPLOY_FIX.py`) directly invoke `docker stop` and `docker rm` via subprocess.
- These bypass the wrapper entirely by calling `docker` (which resolves to first `docker` in PATH).
- If wrapper is not in PATH, these will call real docker binary directly.

**Recommendation**:
```python
# BEFORE (bypasses wrapper):
subprocess.run(["docker", "stop", "redis", "postgres", "neo4j"])

# AFTER (uses wrapper):
wrapper_path = "/Volumes/Data/ai_projects/wingman-system/wingman/tools/docker-wrapper.sh"
subprocess.run([wrapper_path, "stop", "redis", "postgres", "neo4j"])

# OR: Ensure PATH includes wrapper directory before subprocess call:
import os
os.environ["PATH"] = "/Volumes/Data/ai_projects/wingman-system/wingman/tools:" + os.environ["PATH"]
subprocess.run(["docker", "stop", "redis", "postgres", "neo4j"])
```

---

#### SAFE: Python Files with Safe Docker References

| File | Context | Status |
|------|---------|--------|
| `api_server.py` | Example command string (not executed) | SAFE |
| `wingman/dr_drill.py` | Comments/strings about docker compose | SAFE |
| `wingman_watcher.py` | Example comment (not executed) | SAFE |
| `validation/semantic_analyzer.py` | Risk detection patterns (static analysis) | SAFE |
| `validation/code_scanner.py` | Dangerous command patterns (static analysis) | SAFE |
| `execution_gateway.py` | Allowlist example (not executed) | SAFE |
| `tests/test_gateway.py` | Test fixtures | SAFE |
| `tests/validation/*.py` | Test fixtures | SAFE |

---

### 3. Documentation Files

#### DOC: Runbooks and Deployment Guides (Need Wrapper Prerequisites)

| File | Type | Action Required |
|------|------|-----------------|
| `CLAUDE.md` | Core instructions | **UPDATE**: Strengthen wrapper enforcement section |
| `docs/03-operations/AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md` | Operations runbook | **ADD**: Wrapper prerequisite section |
| `docs/deployment/AAA_PRD_DEPLOYMENT_PLAN.md` | PRD deployment | **ADD**: Wrapper setup to checklist |
| `docs/deployment/AAA_PRD_DEPLOYMENT_TEST_PLAN_COMPLETE.md` | PRD test plan | **ADD**: Wrapper prerequisite |
| `docs/deployment/AAA_DELTA_REPORT_VALIDATION_DEPLOYMENT.md` | Validation deployment | **ADD**: Wrapper prerequisite |
| `QUICK_START.md` | Quick start guide | **ADD**: Wrapper setup step |

**Analysis**:
- These docs contain copy-paste Docker commands for operators.
- If operators run these without wrapper in PATH, destructive commands bypass protection.
- Need to add mandatory wrapper setup as **prerequisite** section.

**Recommendation**:
Add to each runbook before any Docker command examples:

```markdown
## Prerequisites: Docker Wrapper Setup (MANDATORY)

**REQUIRED**: All docker/compose commands assume the docker wrapper is in effect.

### One-Time Setup (per shell session):
\`\`\`bash
export PATH="/Volumes/Data/ai_projects/wingman-system/wingman/tools:$PATH"

# Verify wrapper is active
which docker
# Expected: /Volumes/Data/ai_projects/wingman-system/wingman/tools/docker

# If real docker not in wrapper's search path, set DOCKER_BIN
export DOCKER_BIN="/Users/kermit/.orbstack/bin/docker"
\`\`\`

### Permanent Setup (add to ~/.zshrc or ~/.bashrc):
\`\`\`bash
export PATH="/Volumes/Data/ai_projects/wingman-system/wingman/tools:$PATH"
\`\`\`
```

---

#### SAFE: Documentation with Docker References (No Action Needed)

| File | Context | Status |
|------|---------|--------|
| `docs/Intelligence/*.md` | Historical/archived | SAFE (archived) |
| `docs/99-archive/**/*.md` | Archived docs | SAFE (archived) |
| `cursor_deployment_plans_and_next_steps.md` | Planning doc | SAFE (planning) |
| `docs/AI_DOCKER_ACCESS_BLOCK.md` | Design doc about wrapper | SAFE (design) |
| `docs/04-user-guides/APPROVAL_WORKFLOW_WITH_VALIDATION.md` | User guide examples | DOC (add wrapper note) |
| `ai-workers/*.md` | AI worker docs | DOC (add wrapper note) |
| `ai-workers/workers/*.md` | Generated worker specs | SAFE (generated) |

---

### 4. Test Files

#### SAFE: All Test Files

| File | Context | Status |
|------|---------|--------|
| `tests/test_gateway.py` | Test fixtures for gateway | SAFE (tests) |
| `tests/validation/*.py` | Validation test fixtures | SAFE (tests) |
| `test_approval_request.json` | Test data | SAFE (test data) |

**Analysis**: Test files use docker commands in strings/fixtures for validation. No actual execution. Safe.

---

### 5. Configuration Files

#### SAFE: No Direct Docker Invocations

| File | Context | Status |
|------|---------|--------|
| `docker-compose.yml` | Compose file (not executable) | SAFE |
| `docker-compose.prd.yml` | Compose file (not executable) | SAFE |
| `ai-workers/orchestrator_input_phase1a.json` | JSON config (contains docker string) | SAFE |

---

## Summary by Risk Level

### HIGH RISK (Requires Immediate Refactoring)

1. **`deploy_test_to_prd.sh`** (lines 436, 470)
   - Direct `docker rm -f` and `docker compose up` calls
   - **Action**: Prepend wrapper to PATH at script start

2. **`ai-workers/scripts/AUTONOMOUS_DEPLOY_FIX.py`** (lines 195, 197)
   - Direct `subprocess.run(["docker", "stop/rm", ...])` calls
   - **Action**: Call wrapper script or set PATH before subprocess

3. **`ai-workers/scripts/orchestration/AUTONOMOUS_DEPLOY_FIX.py`** (duplicate, lines 195, 197)
   - Same as above
   - **Action**: Same as above

### MEDIUM RISK (Should Refactor)

4. **`deploy.sh`**
   - Uses legacy `docker-compose` (v1)
   - **Action**: Update to compose v2 + wrapper PATH

5. **`deploy-secure-production.sh`**
   - Uses legacy `docker-compose` (v1)
   - **Action**: Update to compose v2 + wrapper PATH

### DOCUMENTATION (Add Wrapper Prerequisites)

6. **`CLAUDE.md`**
   - Core instructions file
   - **Action**: Strengthen wrapper enforcement section (make it more prominent)

7. **`docs/03-operations/AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md`**
   - Operations runbook
   - **Action**: Add wrapper prerequisite section at top

8. **`docs/deployment/AAA_PRD_DEPLOYMENT_PLAN.md`**
   - PRD deployment guide
   - **Action**: Add wrapper setup to deployment checklist

9. **`docs/deployment/AAA_PRD_DEPLOYMENT_TEST_PLAN_COMPLETE.md`**
   - PRD test plan
   - **Action**: Add wrapper prerequisite

10. **`QUICK_START.md`**
    - Quick start guide
    - **Action**: Add wrapper setup as step 0

---

## Recommended Actions (Priority Order)

### Phase 1: Critical Scripts (Immediate)

1. **Refactor `deploy_test_to_prd.sh`**
   - Add at top of script (after shebang and set -euo pipefail):
     ```bash
     # MANDATORY: Use docker wrapper for all docker commands
     export PATH="/Volumes/Data/ai_projects/wingman-system/wingman/tools:$PATH"
     export DOCKER_BIN="${DOCKER_BIN:-/Users/kermit/.orbstack/bin/docker}"

     # Verify wrapper is active
     if ! command -v docker >/dev/null 2>&1; then
         echo "❌ Docker wrapper not found in PATH. Check tools/docker-wrapper.sh" >&2
         exit 1
     fi
     if [[ "$(which docker)" != */wingman/tools/docker* ]]; then
         echo "⚠️  Warning: docker command not using wrapper. Expected wrapper in tools/" >&2
         echo "   Current: $(which docker)" >&2
         echo "   Setting PATH to prioritize wrapper..." >&2
         export PATH="/Volumes/Data/ai_projects/wingman-system/wingman/tools:$PATH"
     fi
     ```

2. **Refactor Python scripts with direct docker calls**
   - `ai-workers/scripts/AUTONOMOUS_DEPLOY_FIX.py`
   - `ai-workers/scripts/orchestration/AUTONOMOUS_DEPLOY_FIX.py`
   - Add wrapper invocation or PATH setup before subprocess calls

3. **Update `deploy.sh` and `deploy-secure-production.sh`**
   - Same PATH setup as deploy_test_to_prd.sh
   - Update `docker-compose` to `docker compose` (v2)

### Phase 2: Documentation Updates (High Priority)

4. **Update `CLAUDE.md`**
   - Move Docker Wrapper section higher (before Docker Compose conventions)
   - Make enforcement language stronger ("MUST" not "should")
   - Add verification steps

5. **Update `docs/03-operations/AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md`**
   - Add "Prerequisites: Docker Wrapper Setup (MANDATORY)" section at top
   - Include one-time and permanent setup instructions
   - Add verification command

6. **Update `docs/deployment/AAA_PRD_DEPLOYMENT_PLAN.md`**
   - Add wrapper setup to pre-deployment checklist
   - Add verification step before any docker commands

7. **Update `QUICK_START.md`**
   - Add wrapper setup as "Step 0: Setup Docker Wrapper"

### Phase 3: Verification (Final)

8. **Test wrapper enforcement**
   - Run docker command without wrapper in PATH → should fail or warn
   - Run docker command with wrapper in PATH → should work (for safe commands)
   - Try destructive command with wrapper → should block
   - Verify all refactored scripts work correctly

9. **Create verification checklist**
   - Document test scenarios
   - Confirm all high-risk scripts refactored
   - Confirm all critical docs updated

---

## Bypass Scenarios (Known Risks)

Even after wrapper is in PATH, these bypass scenarios exist:

### 1. Absolute Path Bypass
```bash
# Wrapper in PATH, but absolute path bypasses it:
/usr/bin/docker stop container  # BYPASSES WRAPPER
```

**Mitigation**:
- Document this as prohibited in CLAUDE.md
- Code review should flag absolute paths to docker binary
- Consider filesystem permissions (make /usr/bin/docker non-executable for AI user) - **NOT RECOMMENDED** (breaks system)

### 2. DOCKER_HOST Environment Variable
```bash
# Setting DOCKER_HOST bypasses wrapper:
DOCKER_HOST=unix:///var/run/docker.sock docker stop container  # BYPASSES WRAPPER
```

**Mitigation**:
- Already mitigated by Execution Gateway architecture (containers don't have docker socket)
- Wrapper cannot prevent this (environment vars set before wrapper runs)

### 3. Direct Socket Access
```bash
# Direct socket access via curl/socat bypasses wrapper:
curl --unix-socket /var/run/docker.sock -X POST http://localhost/containers/xyz/stop  # BYPASSES WRAPPER
```

**Mitigation**:
- Already mitigated by Execution Gateway architecture (only gateway container has socket)
- Filesystem layer protection (socket not mounted in non-gateway containers)

---

## Enforcement Strategy

### Three-Layer Protection Model

The wrapper is **Layer 2** of a three-layer security model:

#### Layer 1: Filesystem/Container Isolation (STRONGEST)
- Only `execution-gateway` container has `/var/run/docker.sock`
- All other containers: no socket, no DOCKER_HOST
- **Status**: ✅ Implemented and verified (see `tools/verify_test_privilege_removal.sh`)

#### Layer 2: Docker Wrapper (INFRASTRUCTURE BLOCK)
- Blocks destructive commands at shell/script level
- Requires Wingman approval for destructive ops
- **Status**: ⚠️ Implemented but optional (this audit addresses making it mandatory)

#### Layer 3: Application Logic (APPROVAL FLOW)
- Wingman API approval gates
- Execution Gateway capability tokens
- Audit trail in Postgres
- **Status**: ✅ Implemented (Phase 4 HITL)

**Defense in Depth**: All three layers must be active. Wrapper adds infrastructure-level protection for human operators and scripts running outside containers.

---

## Files Requiring Updates

### Scripts to Refactor (4 files)
1. `/Volumes/Data/ai_projects/wingman-system/wingman/deploy_test_to_prd.sh`
2. `/Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/scripts/AUTONOMOUS_DEPLOY_FIX.py`
3. `/Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/scripts/orchestration/AUTONOMOUS_DEPLOY_FIX.py`
4. `/Volumes/Data/ai_projects/wingman-system/wingman/deploy.sh`
5. `/Volumes/Data/ai_projects/wingman-system/wingman/deploy-secure-production.sh`

### Documentation to Update (5 files)
1. `/Volumes/Data/ai_projects/wingman-system/wingman/CLAUDE.md`
2. `/Volumes/Data/ai_projects/wingman-system/wingman/docs/03-operations/AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md`
3. `/Volumes/Data/ai_projects/wingman-system/wingman/docs/deployment/AAA_PRD_DEPLOYMENT_PLAN.md`
4. `/Volumes/Data/ai_projects/wingman-system/wingman/docs/deployment/AAA_PRD_DEPLOYMENT_TEST_PLAN_COMPLETE.md`
5. `/Volumes/Data/ai_projects/wingman-system/wingman/QUICK_START.md`

**Total Files**: 10

---

## Verification Test Plan

After refactoring, run these tests:

### Test 1: Wrapper Blocks Destructive Command
```bash
# Setup: Ensure wrapper in PATH
export PATH="/Volumes/Data/ai_projects/wingman-system/wingman/tools:$PATH"

# Test: Try destructive command
docker stop wingman-test-api

# Expected: ❌ BLOCKED: Destructive docker command requires Wingman approval
```

### Test 2: Wrapper Allows Safe Command
```bash
# Setup: Wrapper in PATH
export PATH="/Volumes/Data/ai_projects/wingman-system/wingman/tools:$PATH"

# Test: Try safe command
docker ps

# Expected: Lists containers (passes through to real docker)
```

### Test 3: Refactored Scripts Use Wrapper
```bash
# Test: Run deploy_test_to_prd.sh
cd /Volumes/Data/ai_projects/wingman-system/wingman
./deploy_test_to_prd.sh --help

# Expected: Script should verify wrapper is in PATH at startup
# Should see verification message like: "✅ Docker wrapper active"
```

### Test 4: Bypass Attempt Fails
```bash
# Test: Try absolute path bypass
/usr/bin/docker stop wingman-test-api

# Expected: Bypasses wrapper (KNOWN LIMITATION)
# Mitigation: CLAUDE.md prohibits this pattern
```

---

## Conclusions

### Current State
- Docker wrapper exists and works correctly
- Wrapper is **optional** (can be bypassed by not setting PATH)
- 4 high-risk scripts call docker directly without wrapper
- Documentation lacks wrapper setup instructions

### After Phase 5 Implementation
- All deployment scripts will use wrapper (PATH setup at script start)
- All runbooks will document wrapper as mandatory prerequisite
- CLAUDE.md will enforce wrapper usage
- Verification tests will confirm enforcement

### Limitations
- Absolute path bypass (`/usr/bin/docker`) still possible (document as prohibited)
- Environment var bypass (DOCKER_HOST) still possible (mitigated by container isolation)
- Wrapper only protects host-level operations (containers already isolated via Layer 1)

### Success Criteria
- ✅ All high-risk scripts refactored to use wrapper
- ✅ All critical documentation updated with wrapper prerequisites
- ✅ CLAUDE.md enforces wrapper usage
- ✅ Verification tests pass
- ✅ No regression in existing functionality

---

## Appendix: Wrapper Implementation Review

### Current Wrapper Design

**File**: `/Volumes/Data/ai_projects/wingman-system/wingman/tools/docker-wrapper.sh`

**Destructive Commands Blocked**:
- `stop`, `rm`, `down`, `kill`, `restart`, `build`
- `compose down`, `compose stop`, `compose rm`, `compose kill`
- `system prune`, `volume rm`, `network rm`, `image rm`
- `container rm`, `container stop`, `container kill`

**Safe Commands Allowed**:
- `ps`, `logs`, `version`, `info`, `inspect`
- `compose ps`, `compose logs`, `compose config`
- Any command not in destructive list

**Fallback Logic**:
1. Check `DOCKER_BIN` env var
2. Search standard locations: `/usr/local/bin/docker`, `/opt/homebrew/bin/docker`, `~/.orbstack/bin/docker`, `/usr/bin/docker`
3. Exec to real docker binary for safe commands
4. Block and exit 1 for destructive commands

### Wrapper Strengths
- ✅ Clear block message with remediation steps
- ✅ Comprehensive destructive command list
- ✅ DOCKER_BIN override for flexible deployment
- ✅ No hardcoded paths (searches multiple locations)

### Wrapper Limitations
- ⚠️ Optional (requires PATH setup by caller)
- ⚠️ Can be bypassed with absolute paths
- ⚠️ Cannot prevent DOCKER_HOST environment variable bypass
- ⚠️ No logging/telemetry (could add blocked command log for audit)

### Future Enhancements (Optional)
1. **Telemetry**: Log blocked commands to file or Wingman API
2. **Stricter mode**: Require approval even for safe commands in PRD
3. **Integration**: Auto-submit approval request when blocked (instead of manual)
4. **Allowlist mode**: Only allow specific commands (default deny)

---

**End of Audit Report**
