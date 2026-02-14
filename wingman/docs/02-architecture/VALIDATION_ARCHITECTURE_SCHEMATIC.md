# Wingman Validation System - Architecture Schematic

**Status**: CURRENT
**Version**: 1.0
**Last Updated**: 2026-02-14
**Scope**: Validation system architecture and data flow

---

## Purpose

This document provides visual and textual representations of Wingman's validation system architecture, including profile detection, validator execution, scoring logic, and decision tree.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Approval Request                               │
│                    (worker_id, task_name, instruction)                  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Feature Flag Check                              │
│                                                                         │
│  ┌─────────────────────┐      ┌──────────────────────┐                │
│  │ VALIDATION_ENABLED  │──Yes─▶│ Rollout Hash Check  │                │
│  │    (1 or 0)         │      │  (0-100 vs percent)  │                │
│  └─────────────────────┘      └──────────────────────┘                │
│            │ No                           │ In rollout                 │
│            │                              │                            │
└────────────┼──────────────────────────────┼────────────────────────────┘
             │                              │
             ▼                              ▼
    ┌────────────────┐          ┌─────────────────────────────────────┐
    │ Skip Validation│          │    CompositeValidator.validate()    │
    │ (use heuristic)│          │                                     │
    └────────────────┘          └──────────────┬──────────────────────┘
                                               │
                                               ▼
                                 ┌─────────────────────────────┐
                                 │   Profile Detection         │
                                 │                             │
                                 │  Operational vs Deployment  │
                                 │  (keyword-based)            │
                                 └──────────┬──────────────────┘
                                            │
                   ┌────────────────────────┴───────────────────────┐
                   │                                                │
                   ▼                                                ▼
        ┌──────────────────────┐                       ┌──────────────────────┐
        │  Operational Profile │                       │  Deployment Profile  │
        │                      │                       │                      │
        │  • CodeScanner (60%) │                       │  • CodeScanner (30%) │
        │  • Semantic (40%)    │                       │  • Content (25%)     │
        │  • Auto-approve: 85  │                       │  • Dependency (20%)  │
        │  • Auto-reject: 30   │                       │  • Semantic (25%)    │
        │                      │                       │  • Auto-approve: 90  │
        └──────────┬───────────┘                       │  • Auto-reject: 30   │
                   │                                   └──────────┬───────────┘
                   │                                              │
                   └────────────────────┬─────────────────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │   Execute All Validators     │
                         │                              │
                         │  1. CodeScanner.scan()       │
                         │  2. SemanticAnalyzer.analyze()│
                         │  3. DependencyAnalyzer.analyze()│
                         │  4. ContentQualityValidator.validate()│
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │  Validator Results           │
                         │                              │
                         │  {                           │
                         │    code_scanner: 95,         │
                         │    semantic_analyzer: 88,    │
                         │    dependency_analyzer: 60,  │
                         │    content_quality: 75       │
                         │  }                           │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │  Decision Logic              │
                         │  (see Decision Tree below)   │
                         └──────────────┬───────────────┘
                                        │
                   ┌────────────────────┼────────────────────┐
                   │                    │                    │
                   ▼                    ▼                    ▼
        ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
        │   AUTO_REJECTED  │ │  AUTO_APPROVED   │ │  MANUAL_REVIEW   │
        │                  │ │                  │ │                  │
        │  Status: 403     │ │  Status: 200     │ │  Status: 200     │
        │  No approval     │ │  Immediate OK    │ │  Send to Telegram│
        └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Profile Detection Logic

```
┌─────────────────────────────────────────────────────────────────┐
│                   Instruction + Task Name                       │
│                     (combined text)                             │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
                   ┌─────────────────────────────┐
                   │  Check Deployment Keywords  │
                   │                             │
                   │  • deploy, release, rollout │
                   │  • migrate, migration       │
                   │  • CREATE/ALTER/DROP TABLE  │
                   │  • restart/stop container   │
                   │  • kubectl apply/delete     │
                   │  • update config/env        │
                   └──────────────┬──────────────┘
                                  │
                        Match?    │   No match
                   ┌──────────────┼──────────────┐
                   │ Yes          │              │
                   ▼              │              ▼
        ┌──────────────────┐     │   ┌──────────────────────┐
        │ Deployment       │     │   │ Check Operational    │
        │ Profile          │     │   │ Keywords             │
        │                  │     │   │                      │
        │ (stricter)       │     │   │ • docker logs/ps     │
        └──────────────────┘     │   │ • curl health/status │
                                 │   │ • cat/tail/head/less │
                                 │   │ • ls/pwd/whoami      │
                                 │   │ • status/health check│
                                 │   └──────────┬───────────┘
                                 │              │
                                 │    Match?    │   No match
                                 │   ┌──────────┼──────────┐
                                 │   │ Yes      │          │
                                 │   ▼          │          ▼
                                 │ ┌────────────────┐  ┌─────────────┐
                                 │ │ Operational    │  │ Deployment  │
                                 │ │ Profile        │  │ Profile     │
                                 │ │                │  │ (default)   │
                                 │ │ (lenient)      │  └─────────────┘
                                 │ └────────────────┘
                                 │
                                 └──────────────────────────────────┐
                                                                    │
                                                                    ▼
                                                    ┌───────────────────────┐
                                                    │ Default: Deployment   │
                                                    │ (safer when uncertain)│
                                                    └───────────────────────┘

Profile Selection Rules:
1. Deployment keywords take precedence (stricter profile is safer)
2. If no deployment keywords, check operational keywords
3. If no matches, default to deployment (safer)
4. Same instruction always gets same profile (deterministic)
```

---

## Validator Execution and Scoring

### Validator Details

```
┌───────────────────────────────────────────────────────────────────────┐
│                          CodeScanner                                  │
│                                                                       │
│  Input: instruction text                                             │
│  Logic: Pattern matching against known dangerous patterns            │
│                                                                       │
│  Checks:                                                              │
│  • Hardcoded secrets (API keys, passwords, tokens)                   │
│  • Dangerous commands (rm -rf, DROP TABLE, docker system prune)      │
│  • Force flags (--force, --no-verify, -rf)                           │
│  • Privilege escalation (sudo, chmod 777)                            │
│  • Destructive operations (delete, destroy, drop)                    │
│                                                                       │
│  Output: {                                                            │
│    score: 0-100 (0=critical, 100=safe),                              │
│    secrets_found: boolean,                                            │
│    dangerous_patterns: [list],                                        │
│    risk_level: "LOW|MEDIUM|HIGH|CRITICAL"                            │
│  }                                                                    │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│                      SemanticAnalyzer                                 │
│                                                                       │
│  Input: instruction text                                             │
│  Logic: Heuristic-based intent and risk assessment                   │
│                                                                       │
│  Checks:                                                              │
│  • Operation type (read, write, deploy, delete)                      │
│  • Clarity of intent (vague vs specific)                             │
│  • Risk indicators (production, database, critical services)         │
│  • Scope (single service vs multi-service)                           │
│                                                                       │
│  Output: {                                                            │
│    score: 0-100 (0=high risk/unclear, 100=low risk/clear),           │
│    risk_level: "LOW|MEDIUM|HIGH|CRITICAL",                           │
│    reasoning: "explanation of risk assessment"                       │
│  }                                                                    │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│                     DependencyAnalyzer                                │
│                                                                       │
│  Input: instruction text                                             │
│  Logic: Identify affected services and blast radius                  │
│                                                                       │
│  Checks:                                                              │
│  • Affected services (postgres, redis, api, telegram, gateway)       │
│  • Cascading failure potential (db down -> api down -> all fail)     │
│  • Single point of failure operations                                │
│                                                                       │
│  Output: {                                                            │
│    risk_level: "LOW|MEDIUM|HIGH|CRITICAL",                           │
│    blast_radius: "description",                                      │
│    affected_services: [list],                                        │
│    reasoning: "explanation of dependencies"                          │
│  }                                                                    │
│                                                                       │
│  Risk Level Mapping: LOW=90, MEDIUM=60, HIGH=30, CRITICAL=10         │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│                   ContentQualityValidator                             │
│                                                                       │
│  Input: instruction text (10-point framework)                        │
│  Logic: Evaluate quality of each required section                    │
│                                                                       │
│  Checks:                                                              │
│  • DELIVERABLES: specific vs vague                                   │
│  • SUCCESS_CRITERIA: measurable vs generic                           │
│  • MITIGATION: detailed plan vs "none"                               │
│  • RISK_ASSESSMENT: thorough analysis vs one word                    │
│  • ... (all 10 sections)                                             │
│                                                                       │
│  Output: {                                                            │
│    score: 0-100 (average of section scores),                         │
│    section_scores: {DELIVERABLES: 80, SUCCESS_CRITERIA: 70, ...},   │
│    issues: [list of detected quality issues]                         │
│  }                                                                    │
└───────────────────────────────────────────────────────────────────────┘
```

### Weighted Scoring

**Operational Profile** (read-only, low-risk):
```
overall_score = (code_scanner * 0.6) + (semantic_analyzer * 0.4)

Example:
  code_scanner: 95
  semantic_analyzer: 88
  overall_score = (95 * 0.6) + (88 * 0.4) = 57 + 35.2 = 92.2 ≈ 92

Note: content_quality and dependency_analyzer run but are not used in scoring
```

**Deployment Profile** (write operations, high-risk):
```
overall_score = (code_scanner * 0.3) +
                (content_quality * 0.25) +
                (dependency_analyzer * 0.2) +
                (semantic_analyzer * 0.25)

Example:
  code_scanner: 85
  content_quality: 75
  dependency_analyzer: 60 (MEDIUM risk)
  semantic_analyzer: 75
  overall_score = (85*0.3) + (75*0.25) + (60*0.2) + (75*0.25)
                = 25.5 + 18.75 + 12 + 18.75 = 75

Note: All 4 validators used in scoring
```

---

## Decision Tree

```
                              ┌───────────────────┐
                              │ Validation Result │
                              │ (score, profile)  │
                              └────────┬──────────┘
                                       │
                                       ▼
                          ┌────────────────────────┐
                          │ Secrets Found?         │
                          │ (code_scanner)         │
                          └────┬──────────────┬────┘
                               │ Yes          │ No
                               ▼              │
                    ┌──────────────────┐     │
                    │  AUTO_REJECTED   │     │
                    │                  │     │
                    │  Reason: Secrets │     │
                    │  Score: 0        │     │
                    │  Risk: CRITICAL  │     │
                    └──────────────────┘     │
                                             │
                                             ▼
                          ┌────────────────────────────────┐
                          │ Any Active Validator < 30?     │
                          │ (hard floor check)             │
                          └────┬──────────────────────┬────┘
                               │ Yes                  │ No
                               ▼                      │
                    ┌──────────────────┐             │
                    │  AUTO_REJECTED   │             │
                    │                  │             │
                    │  Reason: Validator│            │
                    │  below hard floor│             │
                    │  Score: <30      │             │
                    └──────────────────┘             │
                                                     │
                                                     ▼
                          ┌────────────────────────────────────┐
                          │ All Active Validators >= Threshold?│
                          │ (85 for operational, 90 for deploy)│
                          └────┬────────────────────────┬──────┘
                               │ No                     │ Yes
                               │                        │
                               │                        ▼
                               │              ┌─────────────────┐
                               │              │ Risk Level = LOW?│
                               │              └────┬───────┬────┘
                               │                   │ No    │ Yes
                               │                   │       │
                               │                   │       ▼
                               │                   │  ┌──────────────┐
                               │                   │  │ AUTO_APPROVED│
                               │                   │  │              │
                               │                   │  │ Score: >=85  │
                               │                   │  │ Risk: LOW    │
                               │                   │  └──────────────┘
                               │                   │
                               ▼                   ▼
                    ┌────────────────────────────────────┐
                    │        MANUAL_REVIEW               │
                    │                                    │
                    │  Reason: Medium/high risk OR       │
                    │  Score below auto-approve threshold│
                    │                                    │
                    │  Includes full validation report   │
                    │  Sent to Telegram for human review │
                    └────────────────────────────────────┘

Decision Rules Summary:
1. Secrets found → immediate AUTO_REJECTED (bypass all other checks)
2. Any active validator < 30 → AUTO_REJECTED (hard floor)
3. All active validators >= threshold AND risk = LOW → AUTO_APPROVED
4. Everything else → MANUAL_REVIEW (with validation report)
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Client/Worker                             │
│                                                                     │
│  POST /approvals/request                                            │
│  {                                                                  │
│    "worker_id": "deploy-001",                                       │
│    "task_name": "Restart API",                                      │
│    "instruction": "docker restart wingman-prd-api"                  │
│  }                                                                  │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         api_server.py                               │
│                    /approvals/request handler                       │
│                                                                     │
│  1. Extract instruction, task_name, worker_id                       │
│  2. Check feature flags (VALIDATION_ENABLED, ROLLOUT_PERCENT)       │
│  3. If validation enabled and in rollout:                           │
│     ├─ Call CompositeValidator.validate(instruction, task_name)     │
│     └─ Store validation result                                      │
│  4. Process recommendation:                                         │
│     ├─ REJECT → create AUTO_REJECTED request, return 403           │
│     ├─ APPROVE + LOW risk → create AUTO_APPROVED request, return 200│
│     └─ MANUAL_REVIEW → create PENDING request, send to Telegram    │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   validation/composite_validator.py                 │
│                                                                     │
│  CompositeValidator.validate(instruction, task_name):               │
│                                                                     │
│  1. detect_profile(instruction, task_name)                          │
│     └─ Returns: "operational" or "deployment"                       │
│                                                                     │
│  2. Run all 4 validators:                                           │
│     ├─ CodeScanner.scan(instruction)                                │
│     ├─ SemanticAnalyzer.analyze(instruction)                        │
│     ├─ DependencyAnalyzer.analyze(instruction)                      │
│     └─ ContentQualityValidator.validate(instruction)                │
│                                                                     │
│  3. Filter to active validators (based on profile)                  │
│                                                                     │
│  4. Check hard floor: if any active validator < 30 → REJECT         │
│                                                                     │
│  5. Check secrets: if code_scanner.secrets_found → REJECT           │
│                                                                     │
│  6. Calculate weighted score (based on profile weights)             │
│                                                                     │
│  7. Determine recommendation:                                       │
│     ├─ All active >= threshold AND risk=LOW → APPROVE              │
│     └─ Otherwise → MANUAL_REVIEW                                    │
│                                                                     │
│  8. Return: {                                                       │
│       overall_score, recommendation, validator_scores,              │
│       profile, active_validators, risk_level, reasoning             │
│     }                                                               │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Database Storage                            │
│                     (approval_requests table)                       │
│                                                                     │
│  Store approval request with:                                       │
│  • request_id, worker_id, task_name, instruction                    │
│  • status (AUTO_REJECTED, AUTO_APPROVED, PENDING)                   │
│  • risk_level, risk_reason                                          │
│  • validation_result (JSON with scores, profile, reasoning)         │
│  • created_at, updated_at                                           │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
         ┌──────────────┐ ┌────────────┐ ┌─────────────────┐
         │AUTO_REJECTED │ │AUTO_APPROVED│ │ MANUAL_REVIEW   │
         │              │ │             │ │ (Telegram)      │
         │ Return 403   │ │ Return 200  │ │                 │
         │ with report  │ │ with report │ │ Send notification│
         └──────────────┘ └─────────────┘ │ with report     │
                                          │                 │
                                          │ Wait for human  │
                                          │ decision        │
                                          └─────────────────┘
```

---

## Feature Flag Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Environment Variables                            │
│                                                                     │
│  VALIDATION_ENABLED=1           (1=enabled, 0=disabled)             │
│  VALIDATION_ROLLOUT_PERCENT=50  (0-100, percentage to validate)     │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ VALIDATION_ENABLED == "1"?   │
                    └────┬──────────────────┬──────┘
                         │ No               │ Yes
                         ▼                  │
              ┌──────────────────┐         │
              │ Skip Validation  │         │
              │ (heuristic only) │         │
              └──────────────────┘         │
                                           ▼
                         ┌─────────────────────────────────┐
                         │ Calculate Rollout Hash          │
                         │                                 │
                         │ hash = SHA256(worker_id +       │
                         │              instruction) % 100 │
                         └────────────┬────────────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────────────┐
                         │ hash < ROLLOUT_PERCENT?         │
                         └────┬──────────────────────┬─────┘
                              │ No                   │ Yes
                              ▼                      │
                   ┌──────────────────┐             │
                   │ Skip Validation  │             │
                   │ (not in rollout) │             │
                   └──────────────────┘             │
                                                    ▼
                                      ┌──────────────────────┐
                                      │ Run Validation       │
                                      │ (CompositeValidator) │
                                      └──────────────────────┘

Example Rollout Scenarios:

1. Fully Disabled (VALIDATION_ENABLED=0):
   All requests skip validation → heuristic risk only

2. 10% Rollout (VALIDATION_ENABLED=1, ROLLOUT_PERCENT=10):
   - Request A: hash=5 → 5 < 10 → validate
   - Request B: hash=42 → 42 >= 10 → skip
   - Request C: hash=8 → 8 < 10 → validate
   Result: ~10% validated (deterministic per request)

3. Full Rollout (VALIDATION_ENABLED=1, ROLLOUT_PERCENT=100):
   All requests validated (all hashes < 100)

Note: Same worker_id + instruction always gets same hash → consistent behavior
```

---

## Integration Points

### API Server Integration

**File**: `api_server.py`

**Integration Point**: `/approvals/request` endpoint

**Code Flow**:
```python
def request_approval(data):
    # 1. Feature flag check
    validation_enabled = os.getenv("VALIDATION_ENABLED", "1") == "1"
    validation_rollout_pct = int(os.getenv("VALIDATION_ROLLOUT_PERCENT", "100"))

    # 2. Rollout decision
    rollout_hash = hash(worker_id + instruction) % 100
    use_validation = validation_enabled and (rollout_hash < validation_rollout_pct)

    # 3. Run validation if enabled
    validation_result = None
    if use_validation and composite_validator:
        validation_result = composite_validator.validate(instruction, task_name)

    # 4. Process recommendation
    if validation_result and validation_result["recommendation"] == "REJECT":
        # Create AUTO_REJECTED request
        return {"status": "AUTO_REJECTED", "validation": {...}}, 403

    # 5. Check for auto-approve
    if validation_result and validation_result["recommendation"] == "APPROVE":
        if heuristic_risk["risk_level"] == "LOW":
            # Create AUTO_APPROVED request
            return {"status": "AUTO_APPROVED", "validation": {...}}, 200

    # 6. Manual review (default)
    # Create PENDING request, send to Telegram
    return {"status": "PENDING", "validation": {...}}, 200
```

### Database Schema

**Table**: `approval_requests`

**New Columns** (added for validation):
```sql
-- Validation result stored as JSONB
validation_result JSONB

-- Example stored data:
{
  "overall_score": 92,
  "recommendation": "APPROVE",
  "risk_level": "LOW",
  "reasoning": "Profile 'operational': All validators passed with score >= 85 and risk LOW.",
  "validator_scores": {
    "code_scanner": 95,
    "semantic_analyzer": 88,
    "content_quality": 0,
    "dependency_analyzer": 50
  },
  "profile": "operational",
  "active_validators": ["code_scanner", "semantic_analyzer"]
}
```

### Telegram Notification

**Enhanced Notification Format**:
```
🔔 Approval Request #req_abc123

Task: Restart API
Worker: deploy-worker-001
Risk: MEDIUM

📊 Validation Report:
  Profile: deployment
  Overall Score: 78/100
  Recommendation: MANUAL_REVIEW

  Validator Scores:
  • CodeScanner: 85/100 (safe commands)
  • SemanticAnalyzer: 75/100 (moderate risk)
  • DependencyAnalyzer: 60/100 (MEDIUM blast radius)
  • ContentQuality: 75/100 (good framework)

  Reasoning: Overall score 78; risk MEDIUM. Manual review required.

[Approve] [Reject]
```

---

## Performance Characteristics

### Execution Time

**Typical Validation Time**: <1 second

**Breakdown**:
- Profile detection: <10ms (regex matching)
- CodeScanner: 50-100ms (pattern matching)
- SemanticAnalyzer: 50-100ms (heuristic analysis)
- DependencyAnalyzer: 50-100ms (service identification)
- ContentQualityValidator: 100-200ms (section parsing)
- Weighted scoring: <10ms
- **Total**: ~300-500ms typical, <1s worst case

### Scalability

**Validators are stateless**: No shared state, safe for concurrent requests

**Caching**: Not implemented (each request is unique)

**Bottlenecks**: None identified (all pattern-based, no external API calls)

### Error Handling

**Validator Failure**: If any validator throws exception:
1. Log error
2. Set validation_result = None
3. Fall back to heuristic risk assessment
4. Continue with approval flow (safe fallback)

**Feature Flag Failure**: If env vars invalid:
1. Default to VALIDATION_ENABLED=1 (safer)
2. Default to VALIDATION_ROLLOUT_PERCENT=100
3. Log warning

---

## Related Documentation

- **Deployment Report**: `../deployment/AAA_DELTA_REPORT_VALIDATION_DEPLOYMENT.md`
- **Operational Guide**: `../03-operations/VALIDATION_OPERATIONAL_GUIDE.md`
- **User Guide**: `../04-user-guides/APPROVAL_WORKFLOW_WITH_VALIDATION.md`
- **Architecture Overview**: `AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md`

---

**Document End**
