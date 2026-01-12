# Worker 006: Docker Privilege Separation

**Date:** 2026-01-07
**Environment:** TEST
**Phase:** 2 (Integration)
**Task Owner:** Human Operator (Mark)
**AI Assistant:** Claude (Sonnet 4.5) - Draft changes only
**Status:** PENDING EXECUTION (Blocked until Phase 1 complete)

---

## 1. DELIVERABLES

- [ ] Modified `wingman/docker-compose.yml` - Add gateway service, remove docker socket from workers (AI draft, human reviews)
- [ ] Modified `wingman/docker-compose.prd.yml` - Add gateway service, remove docker socket from workers (AI draft, human reviews)
- [ ] `ai-workers/results/worker-006-results.json` - Execution results (human creates)

---

## 2. SUCCESS_CRITERIA

- [ ] `execution-gateway` service added to both TEST and PRD compose files
- [ ] Docker socket mounted ONLY on gateway service (read-only where possible)
- [ ] Docker socket removed from: `wingman-api`, `telegram-bot`, `wingman-watcher`
- [ ] Network policies prevent container escape
- [ ] Gateway service has security constraints: `no-new-privileges`, `read_only` rootfs where possible
- [ ] Existing services can still communicate with gateway via internal network
- [ ] Stack restart successful (TEST and PRD)
- [ ] All services healthy after privilege separation

---

## 3. BOUNDARIES

**CAN:**
- Modify `docker-compose.yml` (add gateway service, remove socket mounts)
- Modify `docker-compose.prd.yml` (add gateway service, remove socket mounts)
- Add internal Docker network for gateway communication
- Set security options on gateway container

**CANNOT:**
- Remove docker socket from gateway (it needs it to execute commands)
- Change existing service logic (code changes done in Worker 005)
- Deploy to production (Phase 4 does that)
- Break backward compatibility with existing approval API

**MUST:**
- Mount docker socket as read-only where possible (write needed for exec)
- Use security_opt to drop unnecessary capabilities
- Ensure gateway is isolated on internal network
- Verify no other containers can access docker socket directly
- Test full stack restart after changes

---

## 4. DEPENDENCIES

**Hard Dependencies:**
- Worker 001 complete (execution_gateway.py exists)
- Worker 005 complete (api_server.py integrated with gateway)
- Existing docker-compose.yml and docker-compose.prd.yml

**Blocking:** Cannot start until Phase 1 complete (Workers 001-004) and Worker 005 complete

---

## 5. MITIGATION

**If stack fails to start after changes:**
- Revert to backup compose files
- Restart with previous configuration
- Review logs for mount/permission errors
- Fix and retry

**If gateway cannot access docker socket:**
- Verify socket mount path (`/var/run/docker.sock:/var/run/docker.sock`)
- Check gateway container user has socket group membership
- May need `user: root` or `group_add: [docker]`

**If services cannot reach gateway:**
- Verify all services on same Docker network
- Check gateway port exposed to internal network
- Test network connectivity: `docker compose exec wingman-api curl http://execution-gateway:5001/health`

**If security constraints too restrictive:**
- Gateway may need `CAP_SYS_ADMIN` for docker operations
- Adjust security_opt if gateway fails to execute commands
- Balance security with functionality

**Rollback:**
- `git checkout HEAD -- docker-compose.yml docker-compose.prd.yml`
- `docker compose -f docker-compose.yml -p wingman-test down`
- `docker compose -f docker-compose.yml -p wingman-test up -d`
- ~5 minutes downtime

**Escalation:**
- If gateway cannot execute commands: review docker socket permissions
- If privilege separation breaks existing functionality: immediate rollback

**Risk Level:** HIGH (modifies critical infrastructure, affects all services)

---

## 6. TEST_PROCESS

### Manual Testing (Human)
```bash
# After applying AI-drafted changes to compose files:

# 1. Backup existing compose files
cp docker-compose.yml docker-compose.yml.backup
cp docker-compose.prd.yml docker-compose.prd.yml.backup

# 2. Validate compose files (no secrets printed)
docker compose -f docker-compose.yml -p wingman-test config --quiet
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd config --quiet

# Expected: No errors, validation passes

# 3. Restart TEST stack
docker compose -f docker-compose.yml -p wingman-test down
docker compose -f docker-compose.yml -p wingman-test up -d --build

# 4. Verify all services healthy
docker compose -f docker-compose.yml -p wingman-test ps

# Expected: All services "Up" and healthy

# 5. Verify docker socket ONLY on gateway
docker compose -f docker-compose.yml -p wingman-test exec wingman-api ls -la /var/run/docker.sock
# Expected: "No such file or directory"

docker compose -f docker-compose.yml -p wingman-test exec execution-gateway ls -la /var/run/docker.sock
# Expected: "srw-rw---- ... /var/run/docker.sock"

# 6. Test gateway can execute commands
TOKEN=$(python -c "from capability_token import generate_token; print(generate_token('test-privilege-sep'))")
curl -X POST http://localhost:5001/gateway/execute \
  -H "X-Capability-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "docker compose -f docker-compose.yml -p wingman-test ps", "approval_id": "test-privilege-sep"}'

# Expected: {"success": true, "output": "... container list ..."}

# 7. Test API server cannot access docker directly
docker compose -f docker-compose.yml -p wingman-test exec wingman-api \
  python -c "import subprocess; subprocess.run(['docker', 'ps'], check=True)"

# Expected: FileNotFoundError or "docker: command not found"

# 8. Test Telegram bot still works
# Send /pending command via Telegram
# Expected: Bot responds (no docker socket errors)

# 9. Repeat for PRD stack (if approved)
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd down
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d --build
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd ps
```

### Automated Testing
```bash
pytest tests/test_privilege_separation.py -v
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "006",
  "task": "Docker Privilege Separation",
  "status": "pass|fail",
  "deliverables_created": [
    "wingman/docker-compose.yml (modified)",
    "wingman/docker-compose.prd.yml (modified)"
  ],
  "test_results": {
    "compose_validation": "pass",
    "test_stack_restart": "pass",
    "prd_stack_restart": "pass",
    "gateway_has_socket": "pass",
    "api_no_socket": "pass",
    "bot_no_socket": "pass",
    "watcher_no_socket": "pass",
    "gateway_can_execute": "pass",
    "api_cannot_execute_docker": "pass",
    "network_isolation": "pass",
    "security_constraints_applied": "pass"
  },
  "evidence": {
    "socket_mount_count": 1,
    "gateway_security_opts": ["no-new-privileges:true"],
    "test_stack_healthy": true,
    "prd_stack_healthy": true,
    "gateway_response_time_ms": 120
  },
  "duration_minutes": 30,
  "timestamp": "2026-01-07T...",
  "human_operator": "Mark",
  "ai_assistance": "Claude drafted compose changes, human reviewed and applied"
}
```

---

## 8. TASK_CLASSIFICATION

- **Type:** INFRASTRUCTURE (container orchestration changes)
- **Complexity:** HIGH (privilege separation, security constraints)
- **Tool:** Docker Compose + YAML
- **Reasoning:** Modifies critical deployment configuration, affects all services
- **Human-Led:** YES - AI drafts compose changes, human reviews ALL changes before applying
- **AI Role:** Configuration generation assistant only, no autonomous execution

---

## 9. RETROSPECTIVE

**Time estimate:** 20 minutes (AI draft) + 10 minutes (human review/test) = 30 minutes total

**Actual time:** [To be filled after execution]

**Challenges:** [To be filled after execution]

**Docker socket permission issues:** [To be filled - any group membership or user changes needed?]

**Service restart issues:** [To be filled - any services fail to start?]

**Store in mem0:**
- Docker privilege separation pattern
- Gateway-only docker socket mount
- Security constraints for privileged containers

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Current state: All services have docker socket access
- Security posture: Any compromised service can control host

**Targets:**
- AI compose generation: <20 minutes
- Human review/testing: <15 minutes
- Stack restart time: <60 seconds
- Gateway overhead: <50ms per command

**Quality:**
- Zero services with docker socket except gateway
- Gateway has minimal required privileges only
- Network isolation verified
- Full stack functionality preserved

**Monitoring:**
- Before: Backup compose files, verify TEST stack healthy
- During: Monitor service startup, check logs for permission errors
- After: Verify all services healthy, test end-to-end approval → execution flow
- Degradation limit: If any service cannot start, rollback immediately

---

## EXECUTION INSTRUCTIONS (HUMAN OPERATOR)

### Step 1: Prerequisites Check
Verify Phase 1 and Worker 005 complete:
- [ ] Worker 001 complete (gateway exists)
- [ ] Worker 005 complete (api_server.py integrated)
- [ ] All Phase 1 tests passing

### Step 2: Backup
```bash
cp docker-compose.yml docker-compose.yml.backup
cp docker-compose.prd.yml docker-compose.prd.yml.backup
```

### Step 3: Request AI Compose Changes
Ask AI to generate modifications to both compose files:
1. Add `execution-gateway` service:
   - Image: built from `Dockerfile.gateway`
   - Volumes: `/var/run/docker.sock:/var/run/docker.sock` (read-only if possible)
   - Security: `no-new-privileges`, drop unnecessary capabilities
   - Network: internal network only
   - Port: 5001 (internal only, not exposed to host)
2. Remove docker socket from:
   - `wingman-api` service
   - `telegram-bot` service
   - `wingman-watcher` service
3. Ensure all services on same internal network
4. Add health check to gateway service

### Step 4: Human Security Review
Review AI-generated compose changes:
- [ ] Docker socket ONLY on gateway service
- [ ] Gateway has security constraints applied
- [ ] No other services have socket mount
- [ ] Gateway port not exposed to host (internal only)
- [ ] Network configuration allows service-to-gateway communication
- [ ] Health checks defined

### Step 5: Apply Changes (Manual)
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman
nano docker-compose.yml  # Apply reviewed changes
nano docker-compose.prd.yml  # Apply reviewed changes
```

### Step 6: Validate Compose Files
```bash
docker compose -f docker-compose.yml -p wingman-test config --quiet
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd config --quiet
```

### Step 7: Test Stack Restart
```bash
docker compose -f docker-compose.yml -p wingman-test down
docker compose -f docker-compose.yml -p wingman-test up -d --build
docker compose -f docker-compose.yml -p wingman-test ps
```

### Step 8: Run Tests
Follow TEST_PROCESS section, verify privilege separation works.

### Step 9: Record Results
Create `ai-workers/results/worker-006-results.json`.

### Step 10: Gate Decision
- **PASS:** Proceed to Worker 007
- **FAIL:** Rollback (`mv docker-compose.yml.backup docker-compose.yml`)

---

**Wingman Validation Score:** N/A
**Human Approval Required:** YES
**Security Review Required:** HIGH (privilege separation is critical security boundary)
**Status:** AWAITING HUMAN EXECUTION (BLOCKED: Phase 1 and Worker 005 must complete first)
