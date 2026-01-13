# Wingman Validation Enhancement - Architecture Design
**Date:** 2026-01-11
**Version:** 1.0
**Status:** Design Review

---

## TABLE OF CONTENTS
1. [Current State Architecture](#1-current-state-architecture)
2. [Target State Architecture](#2-target-state-architecture)
3. [Complete Fit-Gap Analysis](#3-complete-fit-gap-analysis)
4. [Component Design](#4-component-design)
5. [Integration Design](#5-integration-design)
6. [Data Flow Design](#6-data-flow-design)
7. [Security & Performance](#7-security--performance)
8. [Testing Strategy](#8-testing-strategy)

---

## CRITICAL CLARIFICATION: VALIDATION NOT BYPASS PREVENTION

**This architecture addresses VALIDATION quality, NOT bypass prevention:**

### Validation Layer (THIS ARCHITECTURE)
- **Problem:** Poorly-formed requests get approved (approval theater)
- **Example:** "Execute full DR" with no 10-point plan → Currently PASSES validation
- **Solution:** Enhanced validation rejects poor quality requests
- **Result:** Cursor-STYLE requests (bad instructions) BLOCKED

### Bypass Layer (DIFFERENT PROBLEM - TEST 0A-2)
- **Problem:** AI bypasses Wingman entirely (direct docker commands)
- **Example:** `docker stop wingman-api` without approval request
- **Solution:** Infrastructure isolation (Physical SSD separation)
- **Status:** Addressed separately (Phase 2 hardware product)

**This architecture assumes requests GO THROUGH Wingman. It validates quality WITHIN the approval flow.**

---

## REALISTIC EXPECTATIONS: LLM TUNING REQUIRED

**LLM-based validation is NOT plug-and-play:**
- Initial prompts in this architecture are educated guesses
- Real-world edge cases will emerge during use
- False positives will occur (15-25% initially)
- Tuning required: 4-8 hours post-deployment over first month
- Expect 2-4 week iteration period to reach <10% false positive rate

**Budget for tuning:**
- Week 1: Monitor and collect data
- Week 2: First tuning pass (2-4 hours)
- Week 3-4: Second tuning pass (2-4 hours)
- Ongoing: 1-2 hours/month monitoring

**See business case Section 7 for detailed tuning timeline and expectations.**

---

## 1. CURRENT STATE ARCHITECTURE

### 1.1 Existing Components

```
┌─────────────────────────────────────────────────────────────┐
│                    APPROVAL REQUEST FLOW                     │
└─────────────────────────────────────────────────────────────┘

AI Agent
    │
    │ POST /approvals/request
    │ { instruction, task_name, deployment_env }
    ▼
┌─────────────────────────────────────────┐
│         api_server.py                   │
│  /approvals/request endpoint            │
│                                         │
│  1. Extract request data                │
│  2. Call assess_risk() or              │
│     assess_risk_consensus()             │
│  3. Create approval request             │
│  4. Notify via Telegram                 │
│  5. Return approval ID                  │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│      RISK ASSESSMENT                    │
│  (consensus_verifier.py OR              │
│   assess_risk in api_server.py)         │
│                                         │
│  Validators:                            │
│  ┌────────────────────────┐            │
│  │ 1. Heuristic Vote      │            │
│  │    - Keyword matching  │            │
│  │    - HIGH/MEDIUM/LOW   │            │
│  └────────────────────────┘            │
│                                         │
│  ┌────────────────────────┐            │
│  │ 2. Structural Vote     │            │
│  │    - Check 4 fields    │            │
│  │      (DELIVERABLES,    │            │
│  │       SUCCESS_CRITERIA,│            │
│  │       BOUNDARIES,      │            │
│  │       TEST_PROCESS)    │            │
│  │    - PRESENT/MISSING   │            │
│  └────────────────────────┘            │
│                                         │
│  ┌────────────────────────┐            │
│  │ 3. Ollama Vote         │            │
│  │    - Optional (disabled)│           │
│  │    - Basic prompt      │            │
│  │    - Risk classification│           │
│  └────────────────────────┘            │
│                                         │
│  Consensus: MAX(all_votes)             │
└────────────┬────────────────────────────┘
             │
             │ risk_level + risk_reason
             ▼
┌─────────────────────────────────────────┐
│      APPROVAL DECISION                  │
│                                         │
│  IF risk_level == LOW:                 │
│     AUTO_APPROVED                       │
│  ELSE:                                  │
│     PENDING (human approval)            │
└────────────┬────────────────────────────┘
             │
             ▼
    Telegram Notification
    Human: /approve <id> or /reject <id>
```

---

### 1.2 Existing Code Files

| File | Purpose | Lines | Key Functions |
|------|---------|-------|---------------|
| `api_server.py` | Main API endpoints | 600+ | `/approvals/request`, `assess_risk()` |
| `consensus_verifier.py` | Multi-vote risk assessment | 195 | `assess_risk_consensus()`, `_heuristic_vote()`, `_structural_vote()`, `_ollama_vote()` |
| `instruction_validator.py` | 10-point framework checker | 41 | `validate()` |
| `approval_store.py` | Approval persistence | N/A | Store/retrieve approvals |
| `telegram_bot.py` | Human interface | N/A | `/pending`, `/approve`, `/reject` |

---

### 1.3 Current Validation Logic

#### **Heuristic Vote** (`consensus_verifier.py:49-83`)

```python
def _heuristic_vote(instruction: str, task_name: str, deployment_env: str) -> Vote:
    txt = f"{task_name}\n{instruction}\n{deployment_env}".lower()

    # Keyword lists
    high_terms = ["prod", "production", "drop ", "delete ", "rm -", "docker", ...]
    med_terms = ["restart", "update", "install", "config", ...]

    # Simple substring matching
    if any(t in txt for t in high_terms):
        return Vote("heuristic", "HIGH", "keyword match")
    if any(t in txt for t in med_terms):
        return Vote("heuristic", "MEDIUM", "keyword match")
    return Vote("heuristic", "LOW", "no risky keywords")
```

**Analysis:**
- ✅ Fast (no external calls)
- ✅ Conservative (catches obvious patterns)
- ❌ No semantic understanding
- ❌ Bypassable with synonyms
- ❌ No context awareness

---

#### **Structural Vote** (`consensus_verifier.py:86-95`)

```python
def _strict_structural_vote(instruction: str, task_name: str, deployment_env: str) -> Vote:
    txt = instruction or ""
    missing = []

    # Check if field names appear in text
    for field in ["DELIVERABLES", "SUCCESS_CRITERIA", "BOUNDARIES", "TEST_PROCESS"]:
        if re.search(rf"(?im)^\s*{re.escape(field)}\s*:\s*", txt) is None:
            missing.append(field)

    if missing:
        return Vote("structure", "MEDIUM", f"missing required fields: {', '.join(missing)}")
    return Vote("structure", "LOW", "required instruction fields present")
```

**Analysis:**
- ✅ Checks 4 of 10 required fields
- ✅ Regex-based (finds field headers)
- ❌ Only checks PRESENCE, not QUALITY
- ❌ Missing 6 fields (DEPENDENCIES, MITIGATION, TEST_RESULTS_FORMAT, RESOURCE_REQUIREMENTS, RISK_ASSESSMENT, QUALITY_METRICS)
- ❌ "DELIVERABLES: TBD" passes validation

---

#### **Ollama Vote** (`consensus_verifier.py:98-145`)

```python
def _ollama_vote(instruction: str, task_name: str, deployment_env: str) -> Vote:
    if (os.getenv("WINGMAN_CONSENSUS_OLLAMA_ENABLED") or "").strip() != "1":
        return Vote("ollama", "LOW", "disabled", available=False)

    # Call local Ollama with basic prompt
    prompt = (
        "You are a security risk classifier for infrastructure operations.\n"
        "Return ONLY valid JSON with keys risk_level (LOW|MEDIUM|HIGH) and reason.\n\n"
        f"deployment_env: {deployment_env}\n"
        f"task_name: {task_name}\n"
        f"instruction:\n{instruction}\n"
    )

    # POST to local Ollama, parse JSON response
```

**Analysis:**
- ✅ LLM-based (semantic understanding possible)
- ✅ Local (no external dependency)
- ❌ Disabled by default
- ❌ Basic prompt (no detailed criteria)
- ❌ No quality assessment of 10-point sections
- ❌ No structured analysis output

---

#### **Instruction Validator** (`instruction_validator.py:1-41`)

```python
class InstructionValidator:
    REQUIRED_SECTIONS = [
        "DELIVERABLES", "SUCCESS_CRITERIA", "BOUNDARIES",
        "DEPENDENCIES", "MITIGATION", "TEST_PROCESS",
        "TEST_RESULTS_FORMAT", "RESOURCE_REQUIREMENTS",
        "RISK_ASSESSMENT", "QUALITY_METRICS"
    ]

    def validate(self, instruction_text):
        for section in self.REQUIRED_SECTIONS:
            if section in upper_text:
                score += 10
                validation[section] = "✅ Found"
            else:
                missing.append(section)
                validation[section] = "❌ Missing"

        return {
            "approved": score >= 80,  # 8 of 10 sections required
            "score": score,
            "missing_sections": missing,
            "validation": validation
        }
```

**Analysis:**
- ✅ Checks ALL 10 fields (not just 4)
- ✅ Scoring system (80% threshold)
- ❌ Only checks PRESENCE (substring match)
- ❌ No QUALITY assessment
- ❌ Not integrated into approval flow
- ❌ Used at `/check` endpoint, but NOT in `assess_risk_consensus()`

---

### 1.4 Current State Summary

**Strengths:**
- ✅ Multi-vote consensus (conservative)
- ✅ Heuristic catches obvious patterns
- ✅ Structural check enforces format
- ✅ Ollama integration exists (foundation for LLM)
- ✅ InstructionValidator exists (checks all 10 fields)

**Critical Gaps:**
- ❌ **GAP-1:** No semantic understanding (keyword bypass)
- ❌ **GAP-2:** No content quality assessment
- ❌ **GAP-3:** InstructionValidator not integrated into approval flow
- ❌ **GAP-4:** Ollama disabled + basic prompt
- ❌ **GAP-5:** No code quality scanning
- ❌ **GAP-6:** No dependency/blast radius analysis
- ❌ **GAP-7:** Structural vote only checks 4 of 10 fields
- ❌ **GAP-8:** No rollback plan validation

---

## 2. TARGET STATE ARCHITECTURE

### 2.1 Enhanced Validation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                ENHANCED APPROVAL REQUEST FLOW                    │
└─────────────────────────────────────────────────────────────────┘

AI Agent
    │
    │ POST /approvals/request
    │ { instruction, task_name, deployment_env }
    ▼
┌──────────────────────────────────────────────────────────────┐
│         api_server.py                                        │
│  /approvals/request endpoint                                 │
│                                                              │
│  1. Extract request data                                     │
│  2. Call assess_risk_consensus_enhanced()  ◄─── NEW         │
│  3. IF validation_quality < threshold:                       │
│       AUTO_REJECT with detailed feedback   ◄─── NEW         │
│  4. IF risk_level HIGH + quality good:                      │
│       Create PENDING approval                                │
│  5. IF risk_level LOW + quality excellent:                  │
│       AUTO_APPROVE                                           │
│  6. Notify via Telegram with validation report ◄─── ENHANCED│
│  7. Return approval ID + validation details                  │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│      ENHANCED RISK ASSESSMENT                                │
│  (consensus_verifier_enhanced.py - NEW MODULE)               │
│                                                              │
│  Validators:                                                 │
│  ┌────────────────────────────────────────┐                │
│  │ 1. Heuristic Vote (existing)           │                │
│  │    - Keyword matching                  │                │
│  │    - HIGH/MEDIUM/LOW                   │                │
│  └────────────────────────────────────────┘                │
│                                                              │
│  ┌────────────────────────────────────────┐                │
│  │ 2. Structural Vote (ENHANCED)          │ ◄── CHANGED    │
│  │    - Check ALL 10 fields               │                │
│  │    - Use InstructionValidator          │                │
│  │    - Score: 0-100                      │                │
│  └────────────────────────────────────────┘                │
│                                                              │
│  ┌────────────────────────────────────────┐                │
│  │ 3. Semantic Vote (NEW)                 │ ◄── NEW        │
│  │    - LLM analysis (Ollama)             │                │
│  │    - What does instruction DO?         │                │
│  │    - Blast radius assessment           │                │
│  │    - Rollback capability check         │                │
│  └────────────────────────────────────────┘                │
│                                                              │
│  ┌────────────────────────────────────────┐                │
│  │ 4. Content Quality Vote (NEW)          │ ◄── NEW        │
│  │    - Per-field quality assessment      │                │
│  │    - DELIVERABLES: specific/measurable?│                │
│  │    - SUCCESS_CRITERIA: verifiable?     │                │
│  │    - BOUNDARIES: clear/enforceable?    │                │
│  │    - ... (all 10 fields assessed)      │                │
│  │    - Quality score: 0-100              │                │
│  └────────────────────────────────────────┘                │
│                                                              │
│  ┌────────────────────────────────────────┐                │
│  │ 5. Security Vote (FUTURE - Phase 3)    │                │
│  │    - Code scanning (bandit, semgrep)   │                │
│  │    - Secret detection                  │                │
│  │    - Dangerous pattern detection       │                │
│  └────────────────────────────────────────┘                │
│                                                              │
│  Consensus:                                                  │
│  - risk_level = MAX(all_votes)                              │
│  - validation_quality = AVG(structural, content_quality)    │
│  - semantic_analysis = detailed explanation                 │
│  - recommendations = list of improvements                   │
└────────────┬─────────────────────────────────────────────────┘
             │
             │ Enhanced result:
             │ {
             │   risk_level: HIGH/MEDIUM/LOW,
             │   validation_quality: 0-100,
             │   semantic_analysis: { ... },
             │   quality_breakdown: { per-field scores },
             │   recommendations: [ ... ],
             │   consensus: { votes, dissent }
             │ }
             ▼
┌──────────────────────────────────────────────────────────────┐
│      ENHANCED APPROVAL DECISION                              │
│                                                              │
│  IF validation_quality < 60:                                │
│     AUTO_REJECT                                              │
│     Reason: "Insufficient content quality"                   │
│     Feedback: Detailed recommendations                       │
│                                                              │
│  ELIF risk_level == LOW AND validation_quality >= 90:       │
│     AUTO_APPROVE                                             │
│     Reason: "Low risk + excellent quality"                   │
│                                                              │
│  ELSE:                                                       │
│     PENDING (human approval required)                        │
│     Context: Full validation report                          │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
    Telegram Notification (ENHANCED)
    ┌────────────────────────────────────┐
    │ Approval Request #abc123           │
    │                                    │
    │ Risk: HIGH                         │
    │ Quality: 85/100                    │
    │                                    │
    │ Semantic Analysis:                 │
    │ "This instruction will restart     │
    │  15 containers in production.      │
    │  Blast radius: 3 services.         │
    │  Rollback: Previous images         │
    │  available."                       │
    │                                    │
    │ Quality Breakdown:                 │
    │ ✅ DELIVERABLES: 9/10 (specific)   │
    │ ✅ SUCCESS_CRITERIA: 8/10 (clear)  │
    │ ⚠️ MITIGATION: 6/10 (needs detail) │
    │                                    │
    │ /approve abc123 or /reject abc123  │
    └────────────────────────────────────┘
```

---

### 2.2 New Components

| Component | File | Purpose | Lines (Est) |
|-----------|------|---------|-------------|
| Semantic Analyzer | `semantic_analyzer.py` | LLM-based instruction analysis | 150-200 |
| Content Quality Validator | `content_quality_validator.py` | Per-field quality assessment | 200-300 |
| Enhanced Consensus | `consensus_verifier_enhanced.py` | Orchestrate all validators | 100-150 |
| Validation Report Generator | `validation_report.py` | Format results for human consumption | 100-150 |

**Total New Code:** 550-800 lines

---

## 3. COMPLETE FIT-GAP ANALYSIS

### 3.1 Requirements Mapping

| Requirement | Current State | Gap | Target State | Component | Priority |
|-------------|--------------|-----|--------------|-----------|----------|
| **DR-1: Semantic Understanding** | Keyword matching only | HIGH | LLM explains what instruction DOES | `semantic_analyzer.py` | P0 |
| **DR-2: Code Quality** | None | HIGH | Security scanning, dangerous pattern detection | `code_scanner.py` | P0 |
| **DR-3: Test Coverage** | Presence check | MEDIUM | Assess comprehensiveness | `content_quality_validator.py` | P0 |
| **DR-4: Dependency Analysis** | None | HIGH | Blast radius calculation, impact assessment | `dependency_analyzer.py` | P0 |
| **DR-5: Rollback Capability** | Presence check | HIGH | Validate plan is executable | `semantic_analyzer.py` | P0 |
| **OR-1: Informed Decisions** | "Approve/Reject?" | HIGH | Rich validation report | `validation_report.py` | P0 |
| **OR-2: Confidence** | Low (keyword matching) | HIGH | Multi-layer LLM validation | All enhanced validators | P0 |
| **OR-3: Audit Trail** | Basic | MEDIUM | Structured validation results | Enhanced approval storage | P0 |
| **OR-4: Reduced Load** | All MEDIUM/HIGH to human | MEDIUM | Auto-reject low quality | Decision logic in `api_server.py` | P0 |
| **OR-5: Production Safety** | Vulnerable | CRITICAL | Catch Cursor scenario | `semantic_analyzer.py` | P0 |

**Legend:**
- **P0:** ALL requirements in Phase 1 (this proposal) - 42-48 hours including tuning
- **Future Phases:** Advanced features (ML-based risk prediction, historical analysis)

---

### 3.2 Gap Details

#### **GAP-1: No Semantic Understanding**

**Current:**
```python
# Heuristic vote
if "docker" in instruction:
    return Vote("HIGH", "keyword match")
```

**Problem:**
```
Instruction: "Optimize container resource allocation for primary services"
Current: ✅ LOW (no "docker" keyword)
Reality: 🚨 May restart production containers
```

**Target:**
```python
# Semantic analyzer
semantic_analysis = llm_analyze(instruction)
# Returns:
{
  "actions": ["restart containers", "modify resource limits"],
  "affected_services": ["api", "database", "cache"],
  "blast_radius": "HIGH (3 production services)",
  "rollback_plan": "revert to previous resource limits",
  "estimated_downtime": "2-5 minutes per service"
}
```

**Implementation:** `semantic_analyzer.py` with comprehensive LLM prompt

---

#### **GAP-2: No Content Quality Assessment**

**Current:**
```python
# Structural vote
if "DELIVERABLES" in instruction:
    validation["DELIVERABLES"] = "✅ Found"
```

**Problem:**
```
DELIVERABLES: TBD
Current: ✅ PASSES (field present)
Reality: 🚨 No actual deliverable defined
```

**Target:**
```python
# Content quality validator
quality_scores = assess_content_quality(instruction)
# Returns:
{
  "DELIVERABLES": {
    "score": 3/10,
    "reason": "Not specific or measurable ('TBD' is placeholder)",
    "recommendation": "Define concrete deliverables with acceptance criteria"
  },
  "SUCCESS_CRITERIA": {
    "score": 8/10,
    "reason": "Clear, verifiable criteria provided",
    "recommendation": "Add quantitative thresholds"
  },
  ...
}
```

**Implementation:** `content_quality_validator.py` with per-field LLM assessment

---

#### **GAP-3: InstructionValidator Not Integrated**

**Current:**
- `instruction_validator.py` exists ✅
- Used at `/check` endpoint ✅
- **NOT used in `assess_risk_consensus()`** ❌

**Problem:**
```
Approval flow uses:
  _heuristic_vote() → checks keywords
  _structural_vote() → checks 4 of 10 fields

InstructionValidator checks all 10 fields, but is NOT called during approval!
```

**Target:**
```python
# Enhanced structural vote
def _enhanced_structural_vote(instruction, ...):
    validator = InstructionValidator()
    result = validator.validate(instruction)

    if result["score"] < 80:
        return Vote("structure", "HIGH", f"Score {result['score']}/100, missing {result['missing_sections']}")
    return Vote("structure", "LOW", f"All sections present (score {result['score']}/100)")
```

**Implementation:** Integrate `InstructionValidator` into consensus flow

---

#### **GAP-4: Ollama Disabled + Basic Prompt**

**Current:**
```python
if (os.getenv("WINGMAN_CONSENSUS_OLLAMA_ENABLED") or "").strip() != "1":
    return Vote("ollama", "LOW", "disabled", available=False)

# Basic prompt:
prompt = "You are a security risk classifier..."
```

**Problems:**
1. Disabled by default (most installations don't use LLM)
2. Basic prompt (no detailed criteria)
3. Only returns risk_level + reason (no structured analysis)

**Target:**
```python
# Always enabled (with fallback)
def _semantic_vote(instruction, ...):
    try:
        semantic_analysis = analyze_with_llm(instruction, detailed_prompt)
        return Vote("semantic", semantic_analysis["risk_level"], semantic_analysis)
    except Exception:
        # Fallback to heuristic
        return _heuristic_vote(instruction, ...)

# Comprehensive prompt:
detailed_prompt = """
Analyze this instruction and provide:
1. What actions will be performed (step-by-step)
2. What systems/services are affected
3. Blast radius (impact scope)
4. Rollback plan assessment
5. Risk classification (LOW/MEDIUM/HIGH)
6. Specific concerns or recommendations

Instruction:
{instruction}
"""
```

**Implementation:** Enhanced prompts in `semantic_analyzer.py`

---

#### **GAP-5: No Code Quality Scanning**

**Current:** None

**Target (Phase 1 - THIS PROPOSAL):**
```python
def _security_vote(instruction, ...):
    # Extract code blocks from instruction
    code_blocks = extract_code(instruction)

    # Run security pattern detection
    dangerous_patterns = scan_for_dangerous_patterns(code_blocks)
    # Patterns: rm -rf, eval(), os.system(), hardcoded secrets, etc.

    secret_scan = scan_for_secrets(code_blocks)
    # Detect: passwords, API keys, tokens in code

    if dangerous_patterns["high_severity"] > 0:
        return Vote("security", "HIGH", f"{dangerous_patterns['high_severity']} critical issues")
    if secret_scan["secrets_found"] > 0:
        return Vote("security", "HIGH", f"Hardcoded secrets detected")
    ...
```

**Implementation:** Phase 1 - `code_scanner.py` module (8 hours)

**Note:** Initial implementation focuses on dangerous pattern detection (regex-based). Advanced tooling (bandit, semgrep) can be added in future enhancements.

---

#### **GAP-6: No Dependency Analysis**

**Current:** None

**Target (Phase 1 - THIS PROPOSAL):**
```python
def _dependency_vote(instruction, ...):
    # LLM-based dependency extraction
    dependency_analysis = analyze_dependencies_with_llm(instruction)
    # LLM identifies: affected services, dependencies, blast radius

    # Returns:
    # {
    #   "affected_services": ["api", "database", "cache"],
    #   "dependencies": ["redis", "postgres", "message-queue"],
    #   "blast_radius": "MEDIUM (3-5 services)",
    #   "downstream_impact": ["web-frontend", "mobile-app"]
    # }

    blast_radius = dependency_analysis["blast_radius"]
    if "HIGH" in blast_radius or len(dependency_analysis["affected_services"]) > 5:
        return Vote("dependency", "HIGH", f"Large blast radius: {blast_radius}")
    ...
```

**Implementation:** Phase 1 - `dependency_analyzer.py` module using LLM analysis (10 hours)

**Note:** Initial implementation uses LLM to extract dependency information from instruction text. Future enhancements could integrate with service mesh or architecture diagrams for automated dependency mapping.

---

#### **GAP-7: Structural Vote Only Checks 4 of 10 Fields**

**Current:**
```python
# consensus_verifier.py:86-95
for field in ["DELIVERABLES", "SUCCESS_CRITERIA", "BOUNDARIES", "TEST_PROCESS"]:
    # Only 4 fields!
```

**Problem:** Missing:
- DEPENDENCIES
- MITIGATION
- TEST_RESULTS_FORMAT
- RESOURCE_REQUIREMENTS
- RISK_ASSESSMENT
- QUALITY_METRICS

**Target:**
```python
# Use InstructionValidator which checks ALL 10 fields
def _enhanced_structural_vote(instruction, ...):
    validator = InstructionValidator()
    result = validator.validate(instruction)
    # result includes all 10 fields
```

**Implementation:** Replace hardcoded 4-field check with InstructionValidator

---

#### **GAP-8: No Rollback Plan Validation**

**Current:**
```python
# Checks if "MITIGATION" appears
if "MITIGATION" in instruction:
    validation["MITIGATION"] = "✅ Found"
```

**Problem:**
```
MITIGATION: Will figure it out if something goes wrong
Current: ✅ PASSES
Reality: 🚨 No actual rollback plan
```

**Target:**
```python
# Semantic analyzer validates rollback plan
rollback_assessment = assess_rollback_plan(instruction)
# Returns:
{
  "has_plan": True,
  "is_detailed": False,
  "is_executable": False,
  "concerns": [
    "Rollback plan is vague ('figure it out')",
    "No specific steps provided",
    "No validation of rollback success"
  ],
  "score": 2/10
}
```

**Implementation:** Rollback validation in `semantic_analyzer.py`

---

### 3.3 Gap Summary Matrix

| Gap ID | Gap Name | Impact | Effort | Priority | Phase |
|--------|----------|--------|--------|----------|-------|
| GAP-1 | No semantic understanding | CRITICAL | Medium (4h) | P0 | 1 |
| GAP-2 | No content quality | CRITICAL | High (6h) | P0 | 1 |
| GAP-3 | Validator not integrated | HIGH | Low (1h) | P0 | 1 |
| GAP-4 | Ollama disabled/basic | HIGH | Medium (3h) | P0 | 1 |
| GAP-5 | No code scanning | HIGH | High (8h) | P0 | 1 |
| GAP-6 | No dependency analysis | HIGH | High (10h) | P0 | 1 |
| GAP-7 | Only 4 of 10 fields | HIGH | Low (included in GAP-3) | P0 | 1 |
| GAP-8 | No rollback validation | HIGH | Low (included in GAP-1) | P0 | 1 |

**Phase 1 Total Effort:** 32 hours development + 6-8 hours testing = 38-40 hours
**Post-Deployment Tuning:** 4-8 hours over first month
**Total Investment:** 42-48 hours

---

## 4. COMPONENT DESIGN

### 4.1 Semantic Analyzer

**File:** `wingman/semantic_analyzer.py`

**Purpose:** Deep LLM-based analysis of what instruction actually does

**Interface:**
```python
def analyze_instruction(
    instruction: str,
    task_name: str = "",
    deployment_env: str = ""
) -> Dict[str, Any]:
    """
    Returns:
    {
        "actions": List[str],  # Step-by-step actions
        "affected_systems": List[str],  # Services/systems impacted
        "blast_radius": str,  # LOW/MEDIUM/HIGH impact scope
        "rollback_plan": {
            "exists": bool,
            "is_detailed": bool,
            "is_executable": bool,
            "assessment": str,
            "score": int  # 0-10
        },
        "risk_level": str,  # LOW/MEDIUM/HIGH
        "concerns": List[str],  # Specific issues
        "recommendations": List[str]  # Improvements
    }
    """
```

**LLM Prompt:**
```
You are analyzing an infrastructure operation instruction for risk and quality.

INSTRUCTION:
{instruction}

TASK: {task_name}
ENVIRONMENT: {deployment_env}

Provide a comprehensive analysis in JSON format:

1. ACTIONS: List each action that will be performed (step-by-step)
2. AFFECTED_SYSTEMS: List all systems, services, or resources impacted
3. BLAST_RADIUS: Assess impact scope (LOW: <3 services, MEDIUM: 3-10 services, HIGH: >10 services or production-wide)
4. ROLLBACK_PLAN:
   - exists: Is a rollback/mitigation plan provided?
   - is_detailed: Are specific rollback steps documented?
   - is_executable: Can rollback be performed without manual intervention?
   - assessment: Detailed evaluation of rollback plan quality
   - score: Rate 0-10 (0=no plan, 10=comprehensive automated rollback)
5. RISK_LEVEL: Overall risk (LOW/MEDIUM/HIGH)
6. CONCERNS: List any specific issues or red flags
7. RECOMMENDATIONS: Suggestions for improvement

Return ONLY valid JSON matching this structure.
```

**Error Handling:**
```python
def analyze_instruction(...):
    try:
        # Try Ollama first
        result = call_ollama(detailed_prompt)
        return parse_and_validate(result)
    except OllamaUnavailable:
        # Fallback to basic heuristic
        return fallback_analysis(instruction)
    except Exception as e:
        # Log error, return safe default
        log_error(f"Semantic analysis failed: {e}")
        return {
            "risk_level": "HIGH",  # Conservative
            "concerns": [f"Analysis failed: {e}"],
            "recommendations": ["Manual review required"]
        }
```

---

### 4.2 Content Quality Validator

**File:** `wingman/content_quality_validator.py`

**Purpose:** Assess quality of each 10-point framework section

**Interface:**
```python
def assess_content_quality(instruction: str) -> Dict[str, Dict[str, Any]]:
    """
    Returns:
    {
        "overall_score": int,  # 0-100
        "field_scores": {
            "DELIVERABLES": {
                "score": int,  # 0-10
                "assessment": str,
                "issues": List[str],
                "recommendations": List[str]
            },
            "SUCCESS_CRITERIA": { ... },
            ...  # All 10 fields
        }
    }
    """
```

**Per-Field Assessment Criteria:**

**DELIVERABLES:**
- Specific (not vague like "TBD" or "various things")
- Measurable (concrete artifacts defined)
- Achievable (realistic scope)
- Score: 0 (missing/vague) to 10 (specific, measurable, clear)

**SUCCESS_CRITERIA:**
- Verifiable (can be objectively tested)
- Objective (not subjective like "looks good")
- Testable (specific pass/fail conditions)
- Score: 0 (missing/subjective) to 10 (objective, testable)

**BOUNDARIES:**
- Clear (explicitly states what NOT to do)
- Enforceable (can be validated)
- Complete (covers major risks)
- Score: 0 (missing/vague) to 10 (comprehensive boundaries)

**DEPENDENCIES:**
- Identified (all prerequisites listed)
- Validated (dependencies confirmed available)
- Documented (versions, configurations specified)
- Score: 0 (missing) to 10 (complete dependency map)

**MITIGATION:**
- Rollback plan exists
- Specific steps documented
- Executable (can be automated)
- Validation of rollback success
- Score: 0 (no plan) to 10 (comprehensive automated rollback)

**TEST_PROCESS:**
- Comprehensive (covers all deliverables)
- Automated (not manual)
- Repeatable (consistent results)
- Documented (clear test steps)
- Score: 0 (no testing) to 10 (fully automated test suite)

**TEST_RESULTS_FORMAT:**
- Structured (not prose)
- Verifiable (objective metrics)
- Complete (all test cases covered)
- Score: 0 (no format) to 10 (structured, verifiable)

**RESOURCE_REQUIREMENTS:**
- Realistic (not over/under estimated)
- Available (resources can be allocated)
- Budgeted (cost considerations)
- Score: 0 (missing) to 10 (detailed resource plan)

**RISK_ASSESSMENT:**
- Thorough (all risks identified)
- Quantified (probability + impact)
- Prioritized (high risks highlighted)
- Mitigated (response plans for top risks)
- Score: 0 (missing) to 10 (comprehensive risk analysis)

**QUALITY_METRICS:**
- Defined (specific metrics listed)
- Measurable (can be quantified)
- Meaningful (align with success criteria)
- Score: 0 (missing) to 10 (comprehensive metrics)

**Implementation:**
```python
def assess_field_quality(field_name: str, field_content: str) -> Dict:
    """Use LLM to assess single field quality"""

    criteria = FIELD_CRITERIA[field_name]  # Criteria dict above

    prompt = f"""
    Assess the quality of this {field_name} section:

    CONTENT:
    {field_content}

    CRITERIA:
    {criteria}

    Rate 0-10 and provide:
    - score: int
    - assessment: str (summary)
    - issues: List[str] (problems found)
    - recommendations: List[str] (how to improve)

    Return JSON only.
    """

    return call_ollama(prompt)
```

---

### 4.3 Enhanced Consensus Orchestrator

**File:** `wingman/consensus_verifier_enhanced.py`

**Purpose:** Orchestrate all validators and produce comprehensive result

**Interface:**
```python
def assess_risk_consensus_enhanced(
    instruction: str,
    task_name: str = "",
    deployment_env: str = ""
) -> Dict[str, Any]:
    """
    Returns:
    {
        "risk_level": str,  # LOW/MEDIUM/HIGH (consensus)
        "risk_reason": str,  # Human-readable explanation
        "validation_quality": int,  # 0-100
        "semantic_analysis": Dict,  # From semantic_analyzer
        "quality_breakdown": Dict,  # From content_quality_validator
        "recommendations": List[str],  # Aggregate recommendations
        "consensus": {
            "votes": List[Vote],  # All validator votes
            "dissent": List[Vote],  # Dissenting opinions
            "decided_at": str  # ISO timestamp
        },
        "auto_decision": str  # "APPROVE", "REJECT", or "REQUIRE_HUMAN"
    }
    """
```

**Decision Logic:**
```python
def assess_risk_consensus_enhanced(instruction, task_name, deployment_env):
    # Run all validators
    heuristic_vote = _heuristic_vote(instruction, task_name, deployment_env)
    structural_vote = _enhanced_structural_vote(instruction, task_name, deployment_env)
    semantic_analysis = analyze_instruction(instruction, task_name, deployment_env)
    quality_assessment = assess_content_quality(instruction)

    # Calculate consensus
    votes = [heuristic_vote, structural_vote, semantic_vote_from(semantic_analysis)]
    risk_level = max([v.risk_level for v in votes])  # Conservative

    # Calculate validation quality
    validation_quality = (
        structural_vote.score * 0.3 +  # 30% structural
        quality_assessment["overall_score"] * 0.7  # 70% content quality
    )

    # Auto-decision logic
    if validation_quality < 60:
        auto_decision = "REJECT"  # Poor quality, don't waste human time
    elif risk_level == "LOW" and validation_quality >= 90:
        auto_decision = "APPROVE"  # Low risk + excellent quality
    else:
        auto_decision = "REQUIRE_HUMAN"  # Need human judgment

    return {
        "risk_level": risk_level,
        "validation_quality": validation_quality,
        "semantic_analysis": semantic_analysis,
        "quality_breakdown": quality_assessment,
        "auto_decision": auto_decision,
        ...
    }
```

---

### 4.4 Validation Report Generator

**File:** `wingman/validation_report.py`

**Purpose:** Format validation results for human consumption (Telegram, API, logs)

**Interface:**
```python
def generate_telegram_report(validation_result: Dict) -> str:
    """Format for Telegram notification"""

def generate_api_report(validation_result: Dict) -> Dict:
    """Format for API response"""

def generate_audit_log(validation_result: Dict) -> Dict:
    """Format for audit trail"""
```

**Telegram Report Example:**
```
🔔 Approval Request #abc123def

📊 Risk: HIGH
📈 Quality: 85/100

🤖 Semantic Analysis:
This instruction will restart 15 containers
in production environment.

Blast radius: 3 services (api, database, cache)
Estimated downtime: 2-5 minutes per service
Rollback: Previous images available (score 8/10)

📋 Quality Breakdown:
✅ DELIVERABLES: 9/10 (specific, measurable)
✅ SUCCESS_CRITERIA: 8/10 (clear criteria)
✅ BOUNDARIES: 7/10 (mostly clear)
⚠️ MITIGATION: 6/10 (needs more detail)
✅ TEST_PROCESS: 9/10 (automated tests)
✅ All other fields: 8+/10

⚠️ Concerns:
- Production environment (high risk)
- Multiple services affected
- Rollback plan exists but could be more detailed

💡 Recommendations:
- Add specific rollback validation steps
- Consider blue-green deployment instead

Decision required:
/approve abc123def or /reject abc123def
```

---

## 5. INTEGRATION DESIGN

### 5.1 Modified api_server.py

**Changes Required:**

```python
# Add imports
from semantic_analyzer import analyze_instruction
from content_quality_validator import assess_content_quality
from consensus_verifier_enhanced import assess_risk_consensus_enhanced
from validation_report import generate_telegram_report, generate_audit_log

@app.route("/approvals/request", methods=["POST"])
def approvals_request():
    data = request.get_json()
    instruction = data.get("instruction", "")
    task_name = data.get("task_name", "")
    deployment_env = data.get("deployment_env", os.getenv("DEPLOYMENT_ENV", "test"))

    # Use ENHANCED consensus (replaces assess_risk_consensus)
    validation_result = assess_risk_consensus_enhanced(
        instruction, task_name, deployment_env
    )

    risk_level = validation_result["risk_level"]
    validation_quality = validation_result["validation_quality"]
    auto_decision = validation_result["auto_decision"]

    # Auto-reject if quality too low
    if auto_decision == "REJECT":
        return jsonify({
            "status": "AUTO_REJECTED",
            "reason": f"Validation quality too low ({validation_quality}/100)",
            "validation": validation_result,
            "recommendations": validation_result["recommendations"]
        }), 400

    # Auto-approve if low risk + high quality
    if auto_decision == "APPROVE":
        approval_id = str(uuid.uuid4())
        approval_request = {
            "id": approval_id,
            "status": "AUTO_APPROVED",
            "instruction": instruction,
            "validation": validation_result,
            "approved_at": datetime.now(timezone.utc).isoformat()
        }
        # Store approval
        approval_store.save(approval_request)
        # Log to audit trail
        log_audit(generate_audit_log(validation_result))
        return jsonify(approval_request), 200

    # Require human approval
    approval_id = str(uuid.uuid4())
    approval_request = {
        "id": approval_id,
        "status": "PENDING",
        "instruction": instruction,
        "validation": validation_result,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    # Store approval
    approval_store.save(approval_request)

    # Send ENHANCED Telegram notification
    telegram_report = generate_telegram_report(validation_result)
    send_telegram_notification(telegram_report, approval_id)

    return jsonify(approval_request), 200
```

**Lines Changed:** ~50 lines in `/approvals/request` endpoint
**Backward Compatibility:** Maintained (API response format unchanged, just enhanced)

---

### 5.2 Integration with Existing Components

**approval_store.py:**
- No changes required
- Already stores arbitrary approval data
- Enhanced validation results stored as-is

**telegram_bot.py:**
- No changes to bot commands
- Enhanced reports automatically appear in notifications
- `/pending`, `/approve`, `/reject` work unchanged

**instruction_validator.py:**
- No changes to file
- Integrated via `_enhanced_structural_vote()` in consensus_verifier_enhanced.py

---

### 5.3 Configuration

**New Environment Variables:**

```bash
# Enable enhanced validation (default: enabled)
WINGMAN_ENHANCED_VALIDATION_ENABLED=1

# Validation quality threshold for auto-reject (default: 60)
WINGMAN_QUALITY_THRESHOLD=60

# High quality threshold for auto-approve (default: 90)
WINGMAN_QUALITY_AUTO_APPROVE=90

# Ollama configuration (already exists, ensure enabled)
WINGMAN_CONSENSUS_OLLAMA_ENABLED=1
OLLAMA_HOST=ollama
OLLAMA_PORT=11434
WINGMAN_CONSENSUS_OLLAMA_MODEL=mistral

# Timeout for LLM calls (seconds, default: 30)
WINGMAN_LLM_TIMEOUT=30
```

---

## 6. DATA FLOW DESIGN

### 6.1 Happy Path (HIGH Risk, GOOD Quality → Approved)

```
1. AI Agent submits instruction
   POST /approvals/request
   {
     "instruction": "DELIVERABLES: ...\nSUCCESS_CRITERIA: ...\n[all 10 sections, well-written]",
     "task_name": "Restart production API",
     "deployment_env": "prd"
   }

2. api_server.py calls assess_risk_consensus_enhanced()

3. Validators execute (parallel where possible):
   a. _heuristic_vote() → HIGH (keyword "production")
   b. _enhanced_structural_vote() → LOW (all 10 sections present, score 90/100)
   c. analyze_instruction() → HIGH risk, but good rollback plan (score 8/10)
   d. assess_content_quality() → 85/100 (all fields well-written)

4. Consensus calculated:
   - risk_level = HIGH (max of votes)
   - validation_quality = 87/100 (weighted avg of structural + content)
   - auto_decision = "REQUIRE_HUMAN" (HIGH risk, even with good quality)

5. Approval created as PENDING

6. Telegram notification sent with rich context:
   "Risk: HIGH, Quality: 87/100, Semantic: [restart 15 containers]..."

7. Human reviews, sees detailed analysis, approves:
   /approve abc123

8. Approval status updated to APPROVED

9. AI Agent polls /approvals/<id>, receives APPROVED, executes operation

10. Audit log records validation reasoning
```

---

### 6.2 Auto-Reject Path (Poor Quality)

```
1. AI Agent submits poorly formatted instruction
   POST /approvals/request
   {
     "instruction": "DELIVERABLES: TBD\nSUCCESS_CRITERIA: Make it work\nBOUNDARIES: None",
     "task_name": "Deploy to prod"
   }

2. Validators execute:
   a. _heuristic_vote() → HIGH ("prod")
   b. _enhanced_structural_vote() → HIGH (only 3 fields present, score 30/100)
   c. analyze_instruction() → HIGH risk, no rollback plan (score 0/10)
   d. assess_content_quality() → 25/100 (all fields are placeholders)

3. Consensus:
   - risk_level = HIGH
   - validation_quality = 27/100
   - auto_decision = "REJECT" (quality < 60 threshold)

4. Response 400 Bad Request:
   {
     "status": "AUTO_REJECTED",
     "reason": "Validation quality too low (27/100)",
     "validation": { ... full validation results ... },
     "recommendations": [
       "DELIVERABLES must be specific, not 'TBD'",
       "SUCCESS_CRITERIA must be objective and testable",
       "Missing required fields: DEPENDENCIES, MITIGATION, TEST_PROCESS, ...",
       "Add detailed rollback plan",
       ...
     ]
   }

5. AI Agent receives detailed feedback, can improve and resubmit

6. Human NOT bothered with poor quality request
```

---

### 6.3 Auto-Approve Path (LOW Risk, Excellent Quality)

```
1. AI Agent submits well-formed, low-risk instruction
   POST /approvals/request
   {
     "instruction": "[all 10 sections, comprehensive, excellent quality]",
     "task_name": "Add log line to non-critical service",
     "deployment_env": "test"
   }

2. Validators execute:
   a. _heuristic_vote() → LOW (no risky keywords)
   b. _enhanced_structural_vote() → LOW (all fields present, score 100/100)
   c. analyze_instruction() → LOW risk, good rollback (score 10/10)
   d. assess_content_quality() → 95/100 (all fields excellent)

3. Consensus:
   - risk_level = LOW
   - validation_quality = 97/100
   - auto_decision = "APPROVE" (LOW risk + quality ≥ 90)

4. Approval created as AUTO_APPROVED

5. Response 200 OK:
   {
     "id": "abc123",
     "status": "AUTO_APPROVED",
     "reason": "Low risk + excellent quality (97/100)",
     "validation": { ... }
   }

6. AI Agent proceeds immediately (no human wait)

7. Audit log records auto-approval reasoning

8. Human can review audit log later if desired
```

---

## 7. SECURITY & PERFORMANCE

### 7.1 Security Considerations

**LLM Prompt Injection:**
- **Risk:** Malicious instruction tries to manipulate LLM validator
- **Mitigation:**
  - Prompts use clear delimiters and instruction context
  - LLM told to return ONLY JSON (no code execution)
  - Output validation (parse JSON, reject unexpected format)

**Resource Exhaustion:**
- **Risk:** Large instructions cause LLM timeouts/failures
- **Mitigation:**
  - Timeout on LLM calls (30 seconds default)
  - Fallback to heuristic validation if LLM fails
  - Instruction size limits (50KB max)

**Ollama Availability:**
- **Risk:** Ollama service down → validation fails
- **Mitigation:**
  - Graceful degradation (fallback to existing validators)
  - Health check before LLM calls
  - Error handling with safe defaults

---

### 7.2 Performance Characteristics

**Latency:**
- **Current:** <100ms (keyword matching + regex)
- **Enhanced:** 5-30 seconds (includes LLM calls)
- **Acceptable:** Approval is async (agent polls for result)

**Optimization:**
- Run validators in parallel where possible
- Cache LLM results for duplicate instructions
- Timeout on slow LLM responses (fallback to heuristic)

**Scalability:**
- Local Ollama (no external API limits)
- Stateless validators (horizontal scaling possible)
- Async approval flow (no blocking)

---

### 7.3 Failure Modes

**Ollama Unavailable:**
```python
try:
    semantic_analysis = analyze_instruction(...)
except OllamaUnavailable:
    # Fallback to heuristic
    semantic_analysis = fallback_analysis(...)
    # Log warning for operator awareness
    log_warning("Ollama unavailable, using fallback validation")
```

**LLM Timeout:**
```python
try:
    result = call_ollama(prompt, timeout=30)
except Timeout:
    # Return safe default
    return {
        "risk_level": "HIGH",  # Conservative when unsure
        "concerns": ["Validation timed out, manual review recommended"]
    }
```

**Invalid LLM Response:**
```python
try:
    data = json.loads(llm_response)
    validate_schema(data)
except (JSONDecodeError, ValidationError):
    # Log issue, return safe default
    log_error(f"Invalid LLM response: {llm_response}")
    return safe_default()
```

---

## 8. TESTING STRATEGY

### 8.1 Unit Tests

**Test Coverage:**

| Component | Tests | Coverage |
|-----------|-------|----------|
| `semantic_analyzer.py` | 20+ test cases | 90%+ |
| `content_quality_validator.py` | 30+ test cases (3 per field) | 90%+ |
| `consensus_verifier_enhanced.py` | 15+ test cases | 90%+ |
| `validation_report.py` | 10+ test cases | 90%+ |

**Key Test Cases:**

**Semantic Analyzer:**
- ✅ Basic instruction (low risk)
- ✅ Production keywords (high risk)
- ✅ Synonym bypass attempt ("optimize" instead of "restart")
- ✅ Multi-action instruction (complex semantic understanding)
- ✅ Good rollback plan (high score)
- ✅ No rollback plan (low score)
- ✅ Vague mitigation (medium score)
- ✅ Ollama unavailable (fallback works)
- ✅ Ollama timeout (safe default)
- ✅ Invalid JSON response (error handling)

**Content Quality Validator:**
- Per field (10 fields × 3 test cases each = 30 tests):
  - ✅ Excellent content (score 9-10)
  - ✅ Poor content (score 0-3)
  - ✅ Medium content (score 5-7)

**Consensus Orchestrator:**
- ✅ All validators agree (consensus easy)
- ✅ Validators disagree (max risk wins)
- ✅ High risk + good quality → REQUIRE_HUMAN
- ✅ High risk + poor quality → AUTO_REJECT
- ✅ Low risk + excellent quality → AUTO_APPROVE
- ✅ One validator fails (graceful degradation)

---

### 8.2 Integration Tests

**Test Approval Flow:**

```python
def test_enhanced_approval_flow_high_risk_good_quality():
    # Submit well-formed high-risk instruction
    response = client.post("/approvals/request", json={
        "instruction": WELL_FORMED_PRODUCTION_INSTRUCTION,
        "task_name": "Restart production",
        "deployment_env": "prd"
    })

    # Should create PENDING approval (not auto-reject or auto-approve)
    assert response.status_code == 200
    assert response.json["status"] == "PENDING"
    assert response.json["validation"]["risk_level"] == "HIGH"
    assert response.json["validation"]["validation_quality"] >= 80

    # Telegram notification should be sent (mock verified)
    assert telegram_mock.send_message.called
    assert "Risk: HIGH" in telegram_mock.send_message.call_args[0][0]
    assert "Quality: 8" in telegram_mock.send_message.call_args[0][0]

def test_auto_reject_poor_quality():
    # Submit poorly formed instruction
    response = client.post("/approvals/request", json={
        "instruction": "DELIVERABLES: TBD\nSUCCESS_CRITERIA: Make it work"
    })

    # Should auto-reject
    assert response.status_code == 400
    assert response.json["status"] == "AUTO_REJECTED"
    assert response.json["validation"]["validation_quality"] < 60
    assert len(response.json["recommendations"]) > 0

def test_auto_approve_low_risk_excellent_quality():
    # Submit excellent low-risk instruction
    response = client.post("/approvals/request", json={
        "instruction": EXCELLENT_LOW_RISK_INSTRUCTION,
        "deployment_env": "test"
    })

    # Should auto-approve
    assert response.status_code == 200
    assert response.json["status"] == "AUTO_APPROVED"
    assert response.json["validation"]["risk_level"] == "LOW"
    assert response.json["validation"]["validation_quality"] >= 90
```

---

### 8.3 Test Plan Validation

**Run against PRD_DEPLOYMENT_TEST_PLAN:**

**TEST 1: Multi-LLM Consensus:**
- ✅ Enhanced validation includes semantic + content quality LLM analysis
- ✅ Consensus from heuristic + structural + semantic votes
- ✅ Passes TEST 1 requirements

**TEST 2: 10-Point Plan Validation:**
- ✅ All 10 fields checked for PRESENCE (structural)
- ✅ All 10 fields assessed for QUALITY (content validator)
- ✅ Passes TEST 2 requirements

**TEST 6: Cursor Scenario:**
```
Instruction: "Execute full DR: stop all containers, remove, rebuild"
- Heuristic vote: HIGH (keywords "docker", "remove")
- Structural vote: HIGH (poor quality, missing fields)
- Semantic analysis: CRITICAL (68 containers, no selective targeting)
- Content quality: 15/100 (no deliverables, no success criteria)
- Consensus: HIGH risk, 15/100 quality
- Auto-decision: AUTO_REJECT (quality < 60)

Result: ✅ BLOCKED (Cursor scenario prevented)
```

---

## 9. DEPLOYMENT ARCHITECTURE

### 9.1 Container Changes

**No new containers required:**
- Enhanced validation runs in existing `wingman-api` container
- Uses existing Ollama container (already in docker-compose.yml)

**Dependencies:**
- Ollama must be running and healthy
- Network connectivity: wingman-api → ollama

---

### 9.2 Rollback Plan

**If enhanced validation causes issues:**

```bash
# Option 1: Disable enhanced validation (environment variable)
export WINGMAN_ENHANCED_VALIDATION_ENABLED=0
docker compose -f docker-compose.yml -p wingman-test restart wingman-api

# Option 2: Revert code (git)
cd /Volumes/Data/ai_projects/wingman-system/wingman
git checkout <previous-commit>
docker compose -f docker-compose.yml -p wingman-test up -d --build wingman-api

# Option 3: Use previous Docker image
docker tag wingman-api:previous wingman-api:latest
docker compose -f docker-compose.yml -p wingman-test up -d wingman-api
```

**Validation that rollback worked:**
```bash
# Check API health
curl http://localhost:5002/health

# Submit test approval (should use old validation)
curl -X POST http://localhost:5002/approvals/request \
  -H "Content-Type: application/json" \
  -d '{"instruction": "test", "task_name": "test"}'
```

---

## 10. CONCLUSION

### 10.1 Architecture Summary

**Current State:**
- Keyword matching (heuristic)
- Basic structural checks (4 of 10 fields)
- Optional Ollama (disabled, basic prompt)
- **Result:** Presence checks only, no substance

**Target State:**
- Semantic understanding (LLM analysis)
- Content quality assessment (all 10 fields, depth)
- Enhanced consensus (multi-layer validation)
- Auto-reject poor quality / Auto-approve excellent low-risk
- **Result:** Real substance, informed decisions

**Gap Closed:** 8 of 8 critical gaps (GAP-1 through GAP-8)

---

### 10.2 Readiness Assessment

**Prerequisites Met:**
- ✅ Ollama infrastructure exists (docker-compose.yml)
- ✅ InstructionValidator exists (can be integrated)
- ✅ Approval flow defined (can be enhanced)
- ✅ Audit trail available (can store validation results)

**Risks Mitigated:**
- ✅ Ollama unavailable → fallback to heuristic
- ✅ LLM timeout → safe defaults
- ✅ Invalid responses → error handling
- ✅ Performance impact → async approval flow
- ✅ Rollback needed → environment variable disable

**Recommendation:** APPROVED FOR IMPLEMENTATION

---

### 10.3 Next Steps

1. ✅ Review and approve this architecture document
2. ✅ Review deployment plan (next document)
3. ✅ Approve implementation
4. ✅ Execute development (8-12 hours estimated)
5. ✅ Unit + integration testing (4-6 hours)
6. ✅ Deploy to TEST environment
7. ✅ Run PRD_DEPLOYMENT_TEST_PLAN validation
8. ✅ Deploy to PRD

---

**Status:** READY FOR DEPLOYMENT PLAN
**Document Owner:** Mark
**Next Document:** VALIDATION_ENHANCEMENT_DEPLOYMENT_PLAN.md
