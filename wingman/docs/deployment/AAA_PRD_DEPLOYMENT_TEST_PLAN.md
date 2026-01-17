# PRD Deployment Test Plan - Prove All Concerns Addressed
**Status**: CURRENT  
**Last Updated**: 2026-01-17  
**Version**: 1.0  
**Scope**: Wingman deployment documentation (DEV/TEST/PRD)  

**Date:** 2026-01-10  
**Purpose:** Real test aligned to actual work (DR operations) that proves all Wingman concerns are history  
**Status:** TEST PLAN - Ready for Execution

---

## 🎯 **TEST OBJECTIVE**

**Prove 100% that all concerns raised are honestly and truthfully history:**

1. ✅ Multi-LLM consensus is working (not just string matching)
2. ✅ 10-point plan is actually enforced (not just checking if words exist)
3. ✅ Post-approval verification works (can't execute unapproved commands)
4. ✅ Execution is logged and auditable
5. ✅ No shortcuts or bypasses are possible

---

## 📋 **TEST SCENARIO: The Actual Work**

**What you were doing when this started:**
- Telegram token rotation
- DR operation on intel-system (stop/remove/rebuild 68 containers)
- **Problem:** Executed WITHOUT approval gates

**Test simulates:**
- Request DR operation on TEST environment (stop/remove/rebuild containers)
- Prove all enforcement layers work
- Prove bypass attempts are blocked

---

## 🔬 **TEST 1: Multi-LLM Consensus Verification**

### **Test Setup:**
**Current State:** Consensus verifier exists (`consensus_verifier.py`) with 3 evaluators:
- Heuristic (keyword-based)
- Structural (10-point plan validation)
- Ollama (local LLM, optional)

**Enable consensus:** Set `WINGMAN_CONSENSUS_ENABLED=1` in environment

1. Submit approval request with instruction that should trigger multi-LLM consensus
2. Verify multiple evaluators are consulted (not just keyword matching)
3. Verify consensus result is stored with approval request

### **Test Steps:**
```bash
# 1. Enable consensus mode
export WINGMAN_CONSENSUS_ENABLED=1

# 2. Submit approval request for DR operation
RESPONSE=$(curl -X POST http://127.0.0.1:5002/approvals/request \
  -H "Content-Type: application/json" \
  -H "X-Wingman-Approval-Request-Key: ${WINGMAN_APPROVAL_REQUEST_KEY}" \
  -d '{
    "worker_id": "test-dr-agent",
    "task_name": "TEST DR Operation - Stop/Remove/Rebuild",
    "instruction": "OPERATION: Full DR on TEST environment\nDELIVERABLES: Stop all containers, remove, rebuild\nSUCCESS_CRITERIA: All containers restarted\nBOUNDARIES: TEST only\nDEPENDENCIES: None\nMITIGATION: Rollback available\nTEST_PROCESS: Health checks\nTEST_RESULTS_FORMAT: JSON\nRESOURCE_REQUIREMENTS: Docker\nRISK_ASSESSMENT: Medium\nQUALITY_METRICS: 100% uptime",
    "deployment_env": "test"
  }')

# 3. Extract and verify consensus data
echo "$RESPONSE" | jq '.risk.consensus'
```

### **Expected Results:**
- ✅ Approval request created with `request_id`
- ✅ Response includes `risk.consensus` field with:
  - `votes`: Array of votes from all evaluators (heuristic, structure, ollama)
  - `dissent`: Array of votes that disagree with consensus
  - `decided_at`: Timestamp of consensus decision
  - `rule`: "max_risk_of_available_sources"
- ✅ At least 2 evaluators consulted (heuristic + structure minimum)
- ✅ If Ollama enabled, 3 evaluators consulted
- ✅ Database stores full consensus audit trail

### **Pass Criteria:**
- [ ] Multiple evaluators consulted (minimum 2: heuristic + structure)
- [ ] Consensus result stored with approval (`risk.consensus` present)
- [ ] Dissent logged if evaluators disagree (`dissent` array populated)
- [ ] NOT just keyword matching (structural validator checks content)
- [ ] Consensus uses max risk (conservative approach)

---

## 🔬 **TEST 2: 10-Point Plan Real Validation**

### **Test Setup:**
1. Submit approval request with INCOMPLETE 10-point plan
2. Verify validation REJECTS incomplete plans
3. Submit with COMPLETE 10-point plan
4. Verify validation ACCEPTS complete plans

### **Test Steps:**

**Step 2A: Incomplete Plan (Should Fail)**
```bash
curl -X POST http://127.0.0.1:5002/approvals/request \
  -H "Content-Type: application/json" \
  -H "X-Wingman-Approval-Request-Key: ${WINGMAN_APPROVAL_REQUEST_KEY}" \
  -d '{
    "worker_id": "test-dr-agent",
    "task_name": "TEST DR - Incomplete Plan",
    "instruction": "OPERATION: DR test\nDELIVERABLES: Stop containers",
    "deployment_env": "test"
  }'
```

**Expected:** Validation score < 80, request rejected or flagged

**Step 2B: Complete Plan (Should Pass)**
```bash
curl -X POST http://127.0.0.1:5002/approvals/request \
  -H "Content-Type: application/json" \
  -H "X-Wingman-Approval-Request-Key: ${WINGMAN_APPROVAL_REQUEST_KEY}" \
  -d '{
    "worker_id": "test-dr-agent",
    "task_name": "TEST DR - Complete Plan",
    "instruction": "OPERATION: Full DR on TEST\nDELIVERABLES: Stop all containers, remove, rebuild\nSUCCESS_CRITERIA: All containers restarted, health checks pass\nBOUNDARIES: TEST environment only, no PRD impact\nDEPENDENCIES: Docker, network access\nMITIGATION: Rollback script ready, backups available\nTEST_PROCESS: Health checks after each stage\nTEST_RESULTS_FORMAT: JSON with timestamps\nRESOURCE_REQUIREMENTS: Docker socket, network\nRISK_ASSESSMENT: Medium - TEST environment, rollback available\nQUALITY_METRICS: 100% container restart success",
    "deployment_env": "test"
  }'
```

**Expected:** Validation score >= 80, request accepted

### **Pass Criteria:**
- [ ] Incomplete plan rejected (score < 80)
- [ ] Complete plan accepted (score >= 80)
- [ ] Validation checks CONTENT, not just keywords
- [ ] Each section validated for completeness
- [ ] NOT just string matching (actual content analysis)

**NOTE:** Current validator uses string matching. Test should verify:
- [ ] Validator checks for section headers (DELIVERABLES:, SUCCESS_CRITERIA:, etc.)
- [ ] Validator requires minimum 8/10 sections (score >= 80)
- [ ] Validator checks policy violations (hardcoded secrets, --force flags)
- [ ] **FUTURE:** Validator should check section CONTENT quality, not just presence

---

## 🔬 **TEST 3: Post-Approval Execution Verification**

### **Test Setup:**
1. Submit approval request for DR operation
2. Approve via Telegram
3. Verify execution is logged
4. Verify execution matches approved plan
5. Attempt to execute unapproved command (should fail)

### **Test Steps:**

**Step 3A: Submit and Approve**
```bash
# Submit request (get request_id)
REQUEST_ID=$(curl -X POST http://127.0.0.1:5002/approvals/request ... | jq -r '.request.request_id')

# Approve via Telegram (manual)
# /approve ${REQUEST_ID}
```

**Step 3B: Execute via Gateway (Should Succeed)**
```bash
# Get capability token
TOKEN=$(curl -X POST http://127.0.0.1:5002/gateway/token \
  -H "X-Wingman-Approval-Decide-Key: ${WINGMAN_APPROVAL_DECIDE_KEY}" \
  -d "{\"approval_id\": \"${REQUEST_ID}\", \"command\": \"docker compose -f docker-compose.yml -p wingman-test stop\"}" \
  | jq -r '.token')

# Execute command
curl -X POST http://127.0.0.1:5001/gateway/execute \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"command": "docker compose -f docker-compose.yml -p wingman-test stop"}'
```

**Step 3C: Verify Execution Logged**
```bash
# Check execution audit log
curl http://127.0.0.1:5002/audit/executions?approval_id=${REQUEST_ID}
```

**Step 3D: Attempt Unapproved Command (Should Fail)**
```bash
# Try to execute command NOT in approved plan
curl -X POST http://127.0.0.1:5001/gateway/execute \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"command": "docker compose -f docker-compose.yml -p wingman-test down -v"}'
```

**Expected:** Gateway rejects (command not in approved scope)

### **Pass Criteria:**
- [ ] Execution logged with approval_id
- [ ] Execution matches approved plan
- [ ] Unapproved commands blocked
- [ ] Audit trail complete (who, what, when, why)

---

## 🔬 **TEST 4: Bypass Attempt Detection**

### **Test Setup:**
1. Attempt to execute command WITHOUT approval
2. Attempt to execute command WITHOUT token
3. Attempt to execute command with invalid token
4. Verify all attempts are blocked and logged

### **Test Steps:**

**Step 4A: Direct Docker Access (Should Fail)**
```bash
# Try to execute directly (bypassing gateway)
docker compose -f wingman/docker-compose.yml -p wingman-test stop
```

**Expected:** If privilege separation is correct, this should fail (no docker socket access)

**Step 4B: Gateway Without Token (Should Fail)**
```bash
curl -X POST http://127.0.0.1:5001/gateway/execute \
  -d '{"command": "docker compose -f docker-compose.yml -p wingman-test stop"}'
```

**Expected:** 401 Unauthorized

**Step 4C: Gateway With Invalid Token (Should Fail)**
```bash
curl -X POST http://127.0.0.1:5001/gateway/execute \
  -H "Authorization: Bearer invalid-token-12345" \
  -d '{"command": "docker compose -f docker-compose.yml -p wingman-test stop"}'
```

**Expected:** 401 Unauthorized

**Step 4D: Gateway With Expired Token (Should Fail)**
```bash
# Use token that's expired (TTL passed)
curl -X POST http://127.0.0.1:5001/gateway/execute \
  -H "Authorization: Bearer ${EXPIRED_TOKEN}" \
  -d '{"command": "docker compose -f docker-compose.yml -p wingman-test stop"}'
```

**Expected:** 401 Unauthorized

### **Pass Criteria:**
- [ ] Direct docker access blocked (no socket)
- [ ] Gateway rejects requests without token
- [ ] Gateway rejects invalid tokens
- [ ] Gateway rejects expired tokens
- [ ] All attempts logged for audit

---

## 🔬 **TEST 5: Full DR Operation End-to-End**

### **Test Setup:**
Simulate the EXACT scenario that triggered this:
- DR operation on TEST environment
- All 4 stages (Stop, Remove, Rebuild, Validate)
- Prove each stage requires separate approval
- Prove execution is logged and verified

### **Test Steps:**

**Step 5A: Stage A - Stop (Requires Approval)**
```bash
# Submit approval request
REQUEST_A=$(curl -X POST http://127.0.0.1:5002/approvals/request ... | jq -r '.request.request_id')

# Approve via Telegram
# /approve ${REQUEST_A}

# Execute via gateway
TOKEN_A=$(curl -X POST http://127.0.0.1:5002/gateway/token ... | jq -r '.token')
curl -X POST http://127.0.0.1:5001/gateway/execute \
  -H "Authorization: Bearer ${TOKEN_A}" \
  -d '{"command": "docker compose -f docker-compose.yml -p wingman-test stop"}'
```

**Step 5B: Stage B - Remove (Requires Separate Approval)**
```bash
# Submit NEW approval request (cannot reuse Stage A approval)
REQUEST_B=$(curl -X POST http://127.0.0.1:5002/approvals/request ... | jq -r '.request.request_id')

# Approve via Telegram
# /approve ${REQUEST_B}

# Execute via gateway
TOKEN_B=$(curl -X POST http://127.0.0.1:5002/gateway/token ... | jq -r '.token')
curl -X POST http://127.0.0.1:5001/gateway/execute \
  -H "Authorization: Bearer ${TOKEN_B}" \
  -d '{"command": "docker compose -f docker-compose.yml -p wingman-test rm -f"}'
```

**Step 5C: Stage C - Rebuild (Requires Separate Approval)**
```bash
# Submit NEW approval request
REQUEST_C=$(curl -X POST http://127.0.0.1:5002/approvals/request ... | jq -r '.request.request_id')

# Approve via Telegram
# /approve ${REQUEST_C}

# Execute via gateway
TOKEN_C=$(curl -X POST http://127.0.0.1:5002/gateway/token ... | jq -r '.token')
curl -X POST http://127.0.0.1:5001/gateway/execute \
  -H "Authorization: Bearer ${TOKEN_C}" \
  -d '{"command": "docker compose -f docker-compose.yml -p wingman-test up -d --build"}'
```

**Step 5D: Stage D - Validate (Requires Separate Approval)**
```bash
# Submit NEW approval request
REQUEST_D=$(curl -X POST http://127.0.0.1:5002/approvals/request ... | jq -r '.request.request_id')

# Approve via Telegram
# /approve ${REQUEST_D}

# Execute validation
TOKEN_D=$(curl -X POST http://127.0.0.1:5002/gateway/token ... | jq -r '.token')
curl -X POST http://127.0.0.1:5001/gateway/execute \
  -H "Authorization: Bearer ${TOKEN_D}" \
  -d '{"command": "docker compose -f docker-compose.yml -p wingman-test ps"}'
```

### **Pass Criteria:**
- [ ] Each stage requires separate approval
- [ ] Cannot skip stages (must approve A before B)
- [ ] Cannot reuse approvals (each stage needs new approval)
- [ ] All executions logged with approval_id
- [ ] Execution matches approved plan
- [ ] Full audit trail available

---

## 📊 **TEST RESULTS SUMMARY**

### **Test Execution Checklist:**

- [ ] **TEST 1:** Multi-LLM consensus working
  - [ ] Multiple LLMs consulted
  - [ ] Consensus stored with approval
  - [ ] NOT just keyword matching

- [ ] **TEST 2:** 10-point plan real validation
  - [ ] Incomplete plan rejected
  - [ ] Complete plan accepted
  - [ ] Content validated, not just keywords

- [ ] **TEST 3:** Post-approval verification
  - [ ] Execution logged
  - [ ] Execution matches plan
  - [ ] Unapproved commands blocked

- [ ] **TEST 4:** Bypass attempt detection
  - [ ] Direct access blocked
  - [ ] Invalid tokens rejected
  - [ ] All attempts logged

- [ ] **TEST 5:** Full DR operation end-to-end
  - [ ] All 4 stages require separate approval
  - [ ] Cannot skip stages
  - [ ] Full audit trail

---

## ✅ **PASS CRITERIA FOR PRD DEPLOYMENT**

**Wingman is ready for PRD when ALL tests pass:**

1. ✅ Multi-LLM consensus is working (not just string matching)
2. ✅ 10-point plan is actually enforced (not just checking if words exist)
3. ✅ Post-approval verification works (can't execute unapproved commands)
4. ✅ Execution is logged and auditable
5. ✅ No shortcuts or bypasses are possible

**If ANY test fails, PRD deployment is BLOCKED until fixed.**

---

## 🚨 **FAILURE SCENARIOS**

**If Test 1 fails (Multi-LLM):**
- Block PRD deployment
- Fix consensus system
- Re-test

**If Test 2 fails (10-Point Plan):**
- Block PRD deployment
- Fix validation logic
- Re-test

**If Test 3 fails (Post-Approval):**
- Block PRD deployment
- Fix execution logging
- Re-test

**If Test 4 fails (Bypass Detection):**
- Block PRD deployment
- Fix privilege separation
- Re-test

**If Test 5 fails (End-to-End):**
- Block PRD deployment
- Fix stage gates
- Re-test

---

**Status:** Test plan ready. Execute tests before PRD deployment approval.
