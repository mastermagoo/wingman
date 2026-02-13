# Wingman Validation Depth Analysis
**Date:** 2026-01-11
**Status:** 🚨 CRITICAL GAP IDENTIFIED
**Concern:** Current approval workflow lacks substance - validates PRESENCE, not QUALITY

---

## 🎯 **THE QUESTION**

> "What about the 10 point validation plan, etc. i do not want to end up having what we have today, an approval work flow that human finally approves, without any substance verfifying i.e. request approved by human but theres no due-dilegence tests, validation, checks by LLM to confirm code meets all agreed stasndards, prior to seeking final human approval?"

**User's Fear:** Approval theater - humans approving without Wingman doing real validation first.

**This Analysis:** What validation ACTUALLY happens vs what's NEEDED for real due-diligence.

---

## 📊 **CURRENT VALIDATION (What Actually Happens)**

### **When Approval Request Submitted:**

```
AI Agent → POST /approvals/request → Wingman validates → Creates PENDING request → Human approves/rejects
                                          ↓
                                    What happens here?
```

### **Validation Flow (consensus_verifier.py)**

#### **1. Heuristic Vote** ⚠️ KEYWORD MATCHING ONLY

**Code:** `consensus_verifier.py:49-83`

```python
def _heuristic_vote(instruction: str, task_name: str, deployment_env: str) -> Vote:
    txt = f"{task_name}\n{instruction}\n{deployment_env}".lower()

    # HIGH risk keywords
    high_terms = ["prod", "production", "drop ", "truncate ", "delete ", "rm -",
                  "wipe", "format ", "secret", "token", "password", "docker",
                  "compose", "kubectl", "deploy", "migration"]
    if any(t in txt for t in high_terms):
        return Vote("heuristic", "HIGH", "keyword match")

    # MEDIUM risk keywords
    med_terms = ["restart", "update", "install", "config", "env", "schema", "database"]
    if any(t in txt for t in med_terms):
        return Vote("heuristic", "MEDIUM", "keyword match")

    return Vote("heuristic", "LOW", "no risky keywords")
```

**What This Does:**
- ✅ Detects HIGH-risk keywords (docker, delete, production, etc.)
- ✅ Detects MEDIUM-risk keywords (restart, install, config, etc.)
- ✅ Returns LOW if no keywords match

**What This DOESN'T Do:**
- ❌ No semantic understanding of what instruction actually DOES
- ❌ No analysis of blast radius or side effects
- ❌ No dependency analysis
- ❌ No rollback capability check
- ❌ Can be bypassed with synonyms ("remove" vs "delete", "prod" vs "production environment")

**Example Bypass:**
```
Instruction: "Modify container lifecycle for production environment"
Result: ✅ LOW risk (no exact keyword "docker" or "prod")
Reality: 🚨 HIGH risk (stopping prod containers)
```

---

#### **2. Structural Vote** ⚠️ PRESENCE CHECK ONLY

**Code:** `consensus_verifier.py:86-95`

```python
def _strict_structural_vote(instruction: str, task_name: str, deployment_env: str) -> Vote:
    txt = instruction or ""
    missing = []
    for field in ["DELIVERABLES", "SUCCESS_CRITERIA", "BOUNDARIES", "TEST_PROCESS"]:
        if re.search(rf"(?im)^\s*{re.escape(field)}\s*:\s*", txt) is None:
            missing.append(field)
    if missing:
        return Vote("structure", "MEDIUM", f"missing required fields: {', '.join(missing)}")
    return Vote("structure", "LOW", "required instruction fields present")
```

**What This Does:**
- ✅ Checks if 4 required fields are PRESENT (DELIVERABLES, SUCCESS_CRITERIA, BOUNDARIES, TEST_PROCESS)
- ✅ Returns MEDIUM if fields missing, LOW if present

**What This DOESN'T Do:**
- ❌ No validation of CONTENT quality
- ❌ No check if DELIVERABLES are specific/measurable
- ❌ No check if SUCCESS_CRITERIA are verifiable
- ❌ No check if BOUNDARIES are clearly defined
- ❌ No check if TEST_PROCESS is comprehensive
- ❌ Missing 6 other 10-point plan fields (DEPENDENCIES, MITIGATION, TEST_RESULTS_FORMAT, RESOURCE_REQUIREMENTS, RISK_ASSESSMENT, QUALITY_METRICS)

**Example Bypass:**
```
DELIVERABLES: TBD
SUCCESS_CRITERIA: Fix the thing
BOUNDARIES: None
TEST_PROCESS: Will test later

Result: ✅ LOW risk (all fields present)
Reality: 🚨 Meaningless content, no real plan
```

---

#### **3. Ollama Vote** ⚠️ OPTIONAL + BASIC PROMPT

**Code:** `consensus_verifier.py:98-145`

```python
def _ollama_vote(instruction: str, task_name: str, deployment_env: str) -> Vote:
    if (os.getenv("WINGMAN_CONSENSUS_OLLAMA_ENABLED") or "").strip() != "1":
        return Vote("ollama", "LOW", "disabled", available=False)

    prompt = (
        "You are a security risk classifier for infrastructure operations.\n"
        "Return ONLY valid JSON with keys risk_level (LOW|MEDIUM|HIGH) and reason.\n\n"
        f"deployment_env: {deployment_env}\n"
        f"task_name: {task_name}\n"
        f"instruction:\n{instruction}\n"
    )

    # Call local Ollama with prompt
    # Returns risk_level + reason
```

**What This Does:**
- ✅ Sends instruction to local LLM for analysis
- ✅ Gets risk classification (LOW/MEDIUM/HIGH) + reason
- ✅ No external network dependency

**What This DOESN'T Do:**
- ❌ Disabled by default (requires WINGMAN_CONSENSUS_OLLAMA_ENABLED=1)
- ❌ Basic prompt (no detailed validation criteria)
- ❌ No code quality checks
- ❌ No security vulnerability scanning
- ❌ No compliance validation
- ❌ No best practices verification
- ❌ LLM may hallucinate or miss subtle issues

**Current State:**
- Likely DISABLED in most deployments
- Even when enabled, prompt doesn't request deep analysis

---

#### **4. Consensus Rule** ✅ CONSERVATIVE

**Code:** `consensus_verifier.py:148-194`

```python
def assess_risk_consensus(instruction: str, task_name: str = "", deployment_env: str = "") -> Dict[str, Any]:
    votes: List[Vote] = [
        _heuristic_vote(instruction, task_name, deployment_env),
        _strict_structural_vote(instruction, task_name, deployment_env),
        _ollama_vote(instruction, task_name, deployment_env),
    ]

    available_votes = [v for v in votes if v.available]
    levels = [v.risk_level for v in available_votes]

    # Consensus rule: take MAX risk among available sources
    consensus_level = _max_risk(levels)
```

**What This Does:**
- ✅ Collects all votes (heuristic, structure, ollama)
- ✅ Takes MAXIMUM risk level (conservative)
- ✅ Records dissent
- ✅ Structured consensus blob

**Result:**
- If ANY vote says HIGH → Overall HIGH
- If ANY vote says MEDIUM (and no HIGH) → Overall MEDIUM
- Only LOW if ALL votes say LOW

**The Problem:**
Even with conservative consensus, if all underlying validators are WEAK (keyword matching + presence checks), the final result is still WEAK.

---

## 🚨 **THE GAP: What's Missing for "Substance"**

### **Current Reality:**

```
AI Agent submits instruction
    ↓
Heuristic: Check keywords ✅
    ↓
Structure: Check headers exist ✅
    ↓
Ollama: (disabled) ❌
    ↓
Consensus: LOW risk ✅
    ↓
Human: "Looks fine, approve" ✅
    ↓
Execute: (Oops, disaster)
```

### **What User Wants:**

```
AI Agent submits instruction
    ↓
Semantic Analysis: What does this ACTUALLY do? ✅
    ↓
Code Quality: Syntax, linting, best practices ✅
    ↓
Security Scan: Vulnerabilities, secrets, dangerous patterns ✅
    ↓
Compliance Check: Meets agreed standards? ✅
    ↓
10-Point Content Validation: Are DELIVERABLES measurable? Are BOUNDARIES clear? ✅
    ↓
Dependency Analysis: What does this depend on? What depends on this? ✅
    ↓
Blast Radius: What's the impact if this fails? ✅
    ↓
Rollback Plan: How do we undo this? ✅
    ↓
Test Coverage: Are tests comprehensive? ✅
    ↓
Generate Validation Report: Show human the ANALYSIS ✅
    ↓
Human: Reviews SUBSTANCE, makes informed decision ✅
    ↓
Execute: (Confident it's safe)
```

---

## 📋 **MISSING VALIDATION LAYERS**

### **1. Semantic Understanding** 🚨 CRITICAL GAP

**Current:** Keyword matching (can be bypassed)
**Needed:** Deep understanding of what instruction DOES

**Examples:**
```
Instruction: "Optimize container resource allocation for primary services"
Keywords: None
Heuristic: ✅ LOW
Reality: 🚨 May stop/restart production containers

Instruction: "Archive obsolete deployment artifacts"
Keywords: None
Heuristic: ✅ LOW
Reality: 🚨 May delete production data
```

**Solution:** LLM-based semantic analysis with detailed prompt:
- What operations does this instruction perform?
- What systems/services are affected?
- What's the blast radius?
- What are the dependencies?
- What's the rollback plan?

---

### **2. Code Quality Validation** 🚨 CRITICAL GAP

**Current:** No code validation
**Needed:** Automated code quality checks

**What's Missing:**
- Syntax validation (linting)
- Security vulnerability scanning (bandit, semgrep, etc.)
- Best practices verification (PEP8, type hints, etc.)
- Code complexity analysis (cyclomatic complexity)
- Testing coverage requirements

**Example:**
```python
# Code submitted for approval
def deploy():
    os.system("rm -rf /")  # 🚨 DISASTER

Current validation: ✅ PASSES (just checks headers exist)
Needed validation: ❌ FAILS (security scan detects dangerous command)
```

---

### **3. 10-Point Plan CONTENT Validation** 🚨 CRITICAL GAP

**Current:** Checks if headers exist (4 of 10 fields)
**Needed:** Validate QUALITY of each section

**10-Point Plan Fields:**

| Field | Current Check | Needed Check |
|-------|--------------|--------------|
| DELIVERABLES | ❌ Not checked | ✅ Are they specific, measurable, achievable? |
| SUCCESS_CRITERIA | ✅ Exists | ✅ Are they verifiable, objective, testable? |
| BOUNDARIES | ✅ Exists | ✅ Are they clearly defined, enforceable? |
| DEPENDENCIES | ❌ Not checked | ✅ Are all dependencies identified and validated? |
| MITIGATION | ❌ Not checked | ✅ Is there a rollback plan? Are risks mitigated? |
| TEST_PROCESS | ✅ Exists | ✅ Is testing comprehensive, automated, documented? |
| TEST_RESULTS_FORMAT | ❌ Not checked | ✅ Is output format structured, verifiable? |
| RESOURCE_REQUIREMENTS | ❌ Not checked | ✅ Are resources realistic, available, budgeted? |
| RISK_ASSESSMENT | ❌ Not checked | ✅ Are risks identified, quantified, prioritized? |
| QUALITY_METRICS | ❌ Not checked | ✅ Are metrics defined, measurable, meaningful? |

**Example Content Validation:**

```
# Current (PASSES)
DELIVERABLES: TBD
SUCCESS_CRITERIA: Make it work
BOUNDARIES: None
TEST_PROCESS: Will test

# Enhanced Validation (FAILS)
DELIVERABLES: ❌ Not specific or measurable
SUCCESS_CRITERIA: ❌ Not verifiable or objective
BOUNDARIES: ❌ Not clearly defined
TEST_PROCESS: ❌ Not comprehensive or automated
MISSING FIELDS: ❌ 6 required fields not present
```

---

### **4. Compliance Validation** 🚨 CRITICAL GAP

**Current:** No compliance checks
**Needed:** Automated compliance verification

**What's Missing:**
- Alignment with agreed standards (CLAUDE.md rules)
- Documentation completeness
- Change management process adherence
- Security policy compliance
- Audit trail requirements

**Example:**
```
Instruction: "Deploy to production"
CLAUDE.md Rule 5: "Destructive operations require Wingman approval"
Current: ✅ PASSES (got approval)
Reality: ❌ FAILS (no 10-point plan submitted)
```

---

### **5. Dependency & Impact Analysis** 🚨 CRITICAL GAP

**Current:** No dependency analysis
**Needed:** Automated impact assessment

**What's Missing:**
- What services depend on this?
- What does this depend on?
- What's the blast radius if this fails?
- What other systems are affected?
- What's the rollback procedure?

**Example:**
```
Instruction: "Restart API server"
Dependencies: Database, Redis, Message Queue
Dependents: Web frontend, Mobile app, Telegram bot
Blast radius: All user-facing services
Rollback: Previous container image
Current validation: ✅ PASSES (no "docker" keyword)
Needed validation: 🚨 HIGH risk (affects all services)
```

---

## 💡 **RECOMMENDATIONS: Adding Substance**

### **Phase 1: Enhanced LLM Analysis** (Quick Win)

**Goal:** Enable and enhance Ollama vote with comprehensive prompt

**Implementation:**
1. Enable Ollama: `WINGMAN_CONSENSUS_OLLAMA_ENABLED=1`
2. Enhance prompt to request:
   - Semantic understanding (what does this DO?)
   - Security risks (vulnerable patterns?)
   - Compliance (meets standards?)
   - Dependencies (what's affected?)
   - Rollback plan (how to undo?)
   - Test coverage (adequate testing?)

**Estimated Time:** 2-4 hours
**Impact:** HIGH (adds real LLM analysis)

---

### **Phase 2: 10-Point Content Validator** (High Impact)

**Goal:** Validate QUALITY of 10-point plan content, not just presence

**Implementation:**
1. Create new validator: `_content_quality_vote()`
2. For each field, use LLM to assess:
   - **DELIVERABLES**: Specific? Measurable? Achievable?
   - **SUCCESS_CRITERIA**: Verifiable? Objective? Testable?
   - **BOUNDARIES**: Clear? Enforceable? Complete?
   - **DEPENDENCIES**: Identified? Validated? Documented?
   - **MITIGATION**: Adequate? Tested? Documented?
   - **TEST_PROCESS**: Comprehensive? Automated? Repeatable?
   - **TEST_RESULTS_FORMAT**: Structured? Verifiable? Complete?
   - **RESOURCE_REQUIREMENTS**: Realistic? Available? Budgeted?
   - **RISK_ASSESSMENT**: Thorough? Quantified? Prioritized?
   - **QUALITY_METRICS**: Defined? Measurable? Meaningful?

3. Return MEDIUM/HIGH if content quality insufficient

**Estimated Time:** 4-6 hours
**Impact:** VERY HIGH (addresses core concern)

---

### **Phase 3: Code Quality Scanner** (Security)

**Goal:** Automated code quality and security scanning

**Implementation:**
1. Integrate linting tools (pylint, flake8, mypy)
2. Security scanners (bandit, semgrep)
3. Best practices checks
4. Return HIGH risk if security issues found

**Estimated Time:** 6-8 hours
**Impact:** HIGH (prevents security disasters)

---

### **Phase 4: Compliance Validator** (Policy Enforcement)

**Goal:** Ensure instructions comply with CLAUDE.md and agreed standards

**Implementation:**
1. Parse CLAUDE.md rules
2. Validate instruction against rules
3. Check documentation completeness
4. Verify change management process
5. Return HIGH risk if non-compliant

**Estimated Time:** 4-6 hours
**Impact:** MEDIUM (enforces policy)

---

### **Phase 5: Dependency Analyzer** (Impact Assessment)

**Goal:** Understand blast radius and dependencies

**Implementation:**
1. Parse instruction for affected services
2. Query system architecture for dependencies
3. Calculate blast radius
4. Assess rollback capability
5. Return HIGH if blast radius large and no rollback

**Estimated Time:** 8-10 hours
**Impact:** HIGH (prevents cascading failures)

---

## 📊 **IMPLEMENTATION PRIORITY**

### **Immediate (This Week):**
1. **Phase 1: Enhanced LLM Analysis** (2-4 hours)
   - Enable Ollama
   - Enhance prompt with comprehensive criteria
   - **Result:** Real LLM analysis instead of keyword matching

2. **Phase 2: 10-Point Content Validator** (4-6 hours)
   - Validate QUALITY of content, not just presence
   - **Result:** Addresses user's core concern about substance

**Total Time:** 6-10 hours
**Impact:** Transforms approval from theater to substance

---

### **Near-Term (This Month):**
3. **Phase 3: Code Quality Scanner** (6-8 hours)
   - Automated security scanning
   - **Result:** Prevents Cursor-style disasters

4. **Phase 4: Compliance Validator** (4-6 hours)
   - Enforces CLAUDE.md rules
   - **Result:** Ensures policy adherence

**Total Time:** 10-14 hours additional
**Impact:** Comprehensive validation stack

---

### **Long-Term (Next Quarter):**
5. **Phase 5: Dependency Analyzer** (8-10 hours)
   - Blast radius calculation
   - **Result:** Full impact assessment

---

## ✅ **SUCCESS CRITERIA**

**You'll know validation has "substance" when:**

1. ✅ **Semantic Understanding:** LLM explains what instruction DOES, not just keyword match
2. ✅ **Quality Validation:** Content is assessed for completeness, not just presence
3. ✅ **Security Scanning:** Code is scanned for vulnerabilities before approval
4. ✅ **Compliance Checks:** Instructions are validated against CLAUDE.md rules
5. ✅ **Impact Assessment:** Blast radius and dependencies are identified
6. ✅ **Validation Report:** Human sees ANALYSIS, not just "PENDING - approve/reject?"

**Human approval workflow becomes:**
```
Request submitted
    ↓
Wingman generates comprehensive validation report:
  - Semantic analysis: "This instruction will restart 15 containers"
  - Code quality: "Security scan PASSED, no vulnerabilities"
  - Content validation: "All 10 fields present and high-quality"
  - Compliance: "Aligns with CLAUDE.md Rule 5"
  - Impact: "Affects 3 services, rollback available"
  - Risk: HIGH (production environment)
    ↓
Human reviews SUBSTANCE:
  "OK, I see exactly what this does, impacts, and risks. Approved."
    ↓
Execute with confidence
```

---

## 🎯 **IMMEDIATE ACTION PLAN**

### **To Address User's Concern RIGHT NOW:**

**Step 1: Enable Enhanced Ollama Analysis** (2 hours)
- Set `WINGMAN_CONSENSUS_OLLAMA_ENABLED=1`
- Enhance prompt in `_ollama_vote()` to request:
  - Semantic analysis
  - Security assessment
  - Compliance check
  - Impact evaluation

**Step 2: Add Content Quality Validator** (4 hours)
- Create `_content_quality_vote()` function
- Use LLM to assess QUALITY of each 10-point field
- Return MEDIUM/HIGH if content insufficient

**Step 3: Test Enhanced Validation** (1 hour)
- Submit test instruction with weak content
- Verify enhanced validation catches it
- Confirm human sees detailed analysis

**Step 4: Update Test Plan** (1 hour)
- Document new validation layers in PRD_DEPLOYMENT_TEST_PLAN.md
- Add validation substance tests

**Total Time:** 8 hours
**Result:** Approval workflow has REAL SUBSTANCE

---

## 📝 **CONCLUSION**

**User's concern is 100% VALID:**

Current validation is:
- ❌ Keyword matching (can be bypassed)
- ❌ Presence checks (not quality assessment)
- ❌ Optional LLM with basic prompt (often disabled)

**This IS "approval theater":**
- Humans approve without seeing REAL analysis
- No substance, just "does it have the right headers?"
- Cursor incident WOULD STILL HAPPEN with current validation

**Solution:**
- ✅ Phase 1+2 (6-10 hours) transforms approval to have substance
- ✅ Phases 3-5 (18-24 hours) build comprehensive validation stack
- ✅ Result: Humans make INFORMED decisions based on REAL ANALYSIS

---

**Status:** 🚨 CRITICAL GAP IDENTIFIED - Immediate action required
**Next Step:** Implement Phase 1+2 (Enhanced LLM + Content Quality)
**Timeline:** 6-10 hours to add real substance to approval workflow
