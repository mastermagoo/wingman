# Wingman Design vs. As-Is Gap Analysis
**Created:** 2026-01-10  
**Status:** CRITICAL - Design-Implementation Gaps Identified  
**Purpose:** Identify discrepancies between designed requirements and actual implementation

---

## 🎯 **EXECUTIVE SUMMARY**

**CRITICAL FINDING:** Wingman's actual implementation has significant gaps compared to the designed architecture, particularly:
1. **DR Stages:** Designed for 4-6 separate stages, implemented as 2 combined stages
2. **Multi-Tenant/Tiered Landscape:** Designed but NOT implemented
3. **PRD Deployment:** Execution Gateway designed for PRD, only deployed in TEST
4. **Client-Ready:** Hardening not yet suitable for multi-client deployment

---

## 📊 **DESIGNED vs. AS-IS COMPARISON**

### **1. DR HITL Stages**

#### **DESIGNED (CLAUDE.md):**
```
Stage A: Stop stacks → Separate approval gate
Stage B: Remove stacks → Separate approval gate
Stage C: Cold start TEST → Separate approval gate
Stage D: Validate TEST → Separate approval gate
Stage E: Cold start PRD → Separate approval gate
Stage F: Validate PRD → Separate approval gate
```

#### **AS-IS (dr_drill.py):**
```python
# TEST only:
Stage "A-stop": down --remove-orphans (STOP + REMOVE combined)
  → Has approval gate ✅
  
Stage "C-cold-start": up -d --build (REBUILD + VALIDATE combined)
  → Has approval gate ✅
  → Validation inline (do_validate=True), NOT separate gate ❌

# PRD: Same pattern
```

**GAP:**
- ❌ Stage B (Remove) missing as separate gate
- ❌ Stage D (Validate) missing as separate gate
- ❌ Stages E & F (PRD) missing entirely
- ⚠️ Only 2 stages instead of 4-6 designed stages

**Impact:**
- Less granular control
- Cannot abort between stop and remove
- Cannot validate separately before proceeding
- PRD stages not implemented

---

### **2. Execution Gateway Deployment**

#### **DESIGNED:**
- TEST: Deploy and validate ✅
- PRD: Deploy after TEST validation ✅
- Both environments with same enforcement

#### **AS-IS:**
- TEST: ✅ Deployed and tested
- PRD: ❌ NOT deployed (only planned)

**GAP:**
- ❌ PRD still vulnerable (no enforcement layer)
- ❌ PRD operations can bypass approval

**Impact:**
- Production operations not enforced
- PRD can execute destructive ops without gateway

---

### **3. Multi-Tenant / Tiered Landscape Support**

#### **DESIGNED (Phase 5):**
```
Planned Features:
- Tenant isolation (per-org policies, audit trails)
- Rate limiting per tenant
- Dashboard UI
- Multi-organization support
```

#### **AS-IS:**
- ❌ No tenant isolation
- ❌ No per-org policies
- ❌ No rate limiting per tenant
- ❌ No dashboard UI
- ❌ Single operator only

**GAP:**
- ❌ Cannot support multiple clients
- ❌ Cannot support tiered landscape
- ❌ All operations share same approval store
- ❌ No client/tenant separation

**Impact:**
- **NOT ready for multi-client deployment**
- **NOT ready for tiered landscape**
- Cannot isolate client operations
- Cannot enforce per-client policies

---

### **4. DR Script Architecture**

#### **DESIGNED (from saved chat):**
```
4 separate approval requests queued:
- Stage A: Stop → 9a90dbee...
- Stage B: Remove → 0ec22466...
- Stage C: Rebuild → 47c6e9bf...
- Stage D: Validate → eca929c6...
```

#### **AS-IS:**
```python
# Only 2 stages, not 4:
run_stage("A-stop", ...)      # Combines A+B
run_stage("C-cold-start", ...) # Combines C+D
```

**GAP:**
- ❌ Stages B and D not separate
- ❌ Cannot approve/reject remove independently
- ❌ Cannot validate independently

---

### **5. Client Integration Architecture**

#### **DESIGNED:**
- Reusable WingmanApprovalClient library ✅
- All systems submit TO Wingman ✅
- Single source of truth ✅

#### **AS-IS:**
- ✅ Library created
- ✅ Intel-system wired
- ✅ Mem0 wired
- ⚠️ But: No tenant isolation means all clients share same approval queue

**GAP:**
- ❌ No client/tenant ID in approval requests
- ❌ No per-client approval filtering
- ❌ All clients see all approvals (security issue)

**Impact:**
- Cannot deploy for multiple clients safely
- Client A could see Client B's approvals
- No client-specific policies

---

### **6. Verification Script**

#### **DESIGNED:**
- `tools/verify_test_privilege_removal.sh` - Verify privilege separation

#### **AS-IS:**
- ❌ Script NOT found in codebase
- ⚠️ Manual verification done, but no automated script

**GAP:**
- ❌ No automated verification
- ❌ No continuous monitoring for bypass attempts

---

## 🚨 **CRITICAL GAPS FOR TIERED LANDSCAPE**

### **Gap 1: No Tenant/Client Isolation**

**Required for Multi-Client:**
```python
# Approval request should include:
{
    "tenant_id": "client-abc",
    "tier": "enterprise|standard|basic",
    "worker_id": "...",
    "task_name": "...",
    "instruction": "..."
}
```

**Current:**
```python
# No tenant_id field
{
    "worker_id": "...",
    "task_name": "...",
    "instruction": "..."
}
```

**Impact:** Cannot support multiple clients safely

---

### **Gap 2: No Per-Tenant Policies**

**Required:**
- Different approval requirements per tier
- Different risk thresholds per client
- Client-specific approval workflows

**Current:**
- Single global policy
- Same risk assessment for all

**Impact:** Cannot enforce tiered service levels

---

### **Gap 3: No Tenant-Scoped Audit Trails**

**Required:**
- Per-tenant execution logs
- Per-tenant approval history
- Client-specific audit reports

**Current:**
- Single global audit trail
- All clients mixed together

**Impact:** Cannot provide client-specific audit reports

---

### **Gap 4: No Rate Limiting Per Tenant**

**Required:**
- Per-client rate limits
- Tier-based limits (enterprise = higher)
- Abuse prevention

**Current:**
- No rate limiting
- Or global rate limiting only

**Impact:** Cannot prevent abuse or enforce tier limits

---

## 📋 **REQUIRED FIXES FOR TIERED LANDSCAPE**

### **Priority 1: Fix DR Stages (Immediate)**

**Action:** Update `dr_drill.py` to implement 4 separate stages:
1. Stage A: Stop only
2. Stage B: Remove only
3. Stage C: Rebuild + start
4. Stage D: Validate only

**Files to Update:**
- `wingman/wingman/dr_drill.py` - Add stages B and D

---

### **Priority 2: Add Tenant/Client Support (Critical for Multi-Client)**

**Actions:**
1. Add `tenant_id` field to approval requests
2. Add `tier` field (enterprise/standard/basic)
3. Filter approvals by tenant in API
4. Isolate audit trails by tenant
5. Add per-tenant policies

**Files to Update:**
- `wingman/api_server.py` - Add tenant filtering
- `wingman/approval_store.py` - Add tenant_id column
- `wingman/execution_gateway.py` - Add tenant to audit logs
- `wingman/wingman_approval_client.py` - Add tenant_id parameter

---

### **Priority 3: Deploy Gateway to PRD**

**Action:** Follow PRD_DEPLOYMENT_PLAN.md

**Status:** Ready to deploy, needs approval

---

### **Priority 4: Create Verification Script**

**Action:** Create `tools/verify_test_privilege_removal.sh`

**Requirements:**
- Check all containers for docker socket
- Verify only gateway has socket
- Report violations
- Exit code 0 if pass, 1 if fail

---

## 🎯 **SUCCESS CRITERIA FOR TIERED LANDSCAPE**

**Wingman is ready for multi-client deployment when:**

1. ✅ **Tenant Isolation:**
   - Approval requests include tenant_id
   - Approvals filtered by tenant
   - Audit trails scoped to tenant

2. ✅ **Per-Tier Policies:**
   - Different approval requirements per tier
   - Tier-based rate limits
   - Client-specific workflows

3. ✅ **4-Stage DR:**
   - Separate approval gates for A, B, C, D
   - Can abort at any stage
   - Independent validation

4. ✅ **PRD Enforcement:**
   - Gateway deployed in PRD
   - All operations enforced
   - No bypass paths

5. ✅ **Verification:**
   - Automated privilege check script
   - Continuous monitoring
   - Bypass detection

---

## 📊 **GAP SUMMARY TABLE**

| Component | Designed | As-Is | Gap | Impact |
|-----------|----------|-------|-----|--------|
| **DR Stages** | 4-6 separate | 2 combined | ❌ Missing B, D | High - Less control |
| **PRD Gateway** | Deployed | TEST only | ❌ Not in PRD | Critical - PRD vulnerable |
| **Tenant Isolation** | Required | None | ❌ No support | Critical - Not multi-client ready |
| **Per-Tier Policies** | Required | None | ❌ No support | Critical - Not tiered ready |
| **Verification Script** | Required | Missing | ❌ Not created | Medium - Manual only |
| **Client Integration** | Library | ✅ Done | ✅ Complete | Low - Works but needs tenant support |

---

## 🔧 **IMMEDIATE ACTION PLAN**

### **Phase 1: Fix DR Stages (1 hour)**
- [ ] Update `dr_drill.py` to implement 4 separate stages
- [ ] Test 4-stage approval flow
- [ ] Verify each stage requires separate approval

### **Phase 2: Add Tenant Support (4-6 hours)**
- [ ] Add tenant_id to approval schema
- [ ] Add tenant filtering to API
- [ ] Update client library to include tenant_id
- [ ] Test multi-tenant isolation

### **Phase 3: Deploy PRD Gateway (1 hour)**
- [ ] Follow PRD_DEPLOYMENT_PLAN.md
- [ ] Deploy with approval gates
- [ ] Verify enforcement

### **Phase 4: Create Verification (30 min)**
- [ ] Create `verify_test_privilege_removal.sh`
- [ ] Test on TEST environment
- [ ] Document usage

---

**Status:** GAPS IDENTIFIED - Ready for remediation
