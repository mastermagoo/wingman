# Wingman Approval Workflow with Validation - User Guide

**Status**: CURRENT
**Version**: 1.0
**Last Updated**: 2026-02-14
**Audience**: All Wingman users (developers, operators, admins)

---

## Purpose

This guide explains how Wingman's approval workflow works with the new validation system, what happens when requests are auto-rejected or auto-approved, and how to read validation reports.

---

## Overview: Three Possible Outcomes

When you submit an approval request to Wingman, validation runs automatically (if enabled) and produces one of three outcomes:

1. **AUTO_REJECTED**: Request is rejected without human review (secrets, dangerous patterns, low quality)
2. **AUTO_APPROVED**: Request is approved without human review (safe, low-risk, high quality)
3. **MANUAL_REVIEW**: Request sent to human approver via Telegram (includes validation report)

---

## End-to-End Approval Workflow

### Step 1: Submit Approval Request

**API Endpoint**: `POST /approvals/request`

**Example Request**:
```bash
curl -X POST http://127.0.0.1:5001/approvals/request \
  -H "Content-Type: application/json" \
  -H "X-Wingman-Approval-Request-Key: ${WINGMAN_APPROVAL_REQUEST_KEY}" \
  -d '{
    "worker_id": "deploy-worker-001",
    "task_name": "Check API logs for errors",
    "instruction": "docker logs wingman-prd-api | tail -100",
    "deployment_env": "prd"
  }'
```

### Step 2: Validation Runs Automatically

**What Happens Behind the Scenes**:

1. **Feature Flag Check**: System checks if validation is enabled (`VALIDATION_ENABLED`)
2. **Rollout Check**: If gradual rollout, check if this request is in the percentage (`VALIDATION_ROLLOUT_PERCENT`)
3. **Profile Detection**: CompositeValidator detects if this is "operational" or "deployment" profile
4. **Validator Execution**: Runs appropriate validators based on profile
5. **Scoring**: Calculates weighted overall score
6. **Decision**: Determines AUTO_REJECT, AUTO_APPROVE, or MANUAL_REVIEW

**Typical Processing Time**: <1 second

### Step 3A: AUTO_REJECTED (Immediate Rejection)

**Response**:
```json
{
  "needs_approval": false,
  "status": "AUTO_REJECTED",
  "request": {
    "request_id": "req_abc123",
    "worker_id": "deploy-worker-001",
    "task_name": "Check API logs for errors",
    "status": "AUTO_REJECTED",
    "risk_level": "CRITICAL"
  },
  "validation": {
    "overall_score": 0,
    "recommendation": "REJECT",
    "risk_level": "CRITICAL",
    "reasoning": "Code scanner found secrets or credentials; immediate reject.",
    "validator_scores": {
      "code_scanner": 0,
      "semantic_analyzer": 50,
      "content_quality": 20,
      "dependency_analyzer": 40
    },
    "profile": "deployment",
    "active_validators": ["code_scanner", "content_quality", "dependency_analyzer", "semantic_analyzer"]
  }
}
```

**What This Means**:
- Request is **rejected immediately** without human review
- No approval required (cannot be executed)
- Status saved as `AUTO_REJECTED` in database

**Common Reasons for Auto-Rejection**:
1. **Secrets detected**: Hardcoded passwords, API keys, tokens (CodeScanner score = 0)
2. **Dangerous patterns**: `rm -rf`, `DROP TABLE`, `--force --no-verify` (CodeScanner score < 30)
3. **Very low quality**: Missing critical 10-point sections or vague instructions (ContentQuality score < 30)
4. **Any validator below hard floor**: Any active validator scores below 30

**What to Do**:
1. Review the `reasoning` field to understand why rejected
2. Check `validator_scores` to see which validator failed
3. Fix the issue (remove secrets, add missing sections, clarify instructions)
4. Resubmit the corrected request

### Step 3B: AUTO_APPROVED (Immediate Approval)

**Response**:
```json
{
  "needs_approval": false,
  "status": "AUTO_APPROVED",
  "request": {
    "request_id": "req_xyz789",
    "worker_id": "ops-worker-002",
    "task_name": "Check API logs for errors",
    "status": "AUTO_APPROVED",
    "risk_level": "LOW"
  },
  "validation": {
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
}
```

**What This Means**:
- Request is **approved immediately** without human review
- Worker can proceed with execution
- Status saved as `AUTO_APPROVED` in database

**Criteria for Auto-Approval**:
1. **Profile-appropriate score**: All active validators >= threshold (85 for operational, 90 for deployment)
2. **Low risk**: SemanticAnalyzer and DependencyAnalyzer both assess risk as LOW
3. **No secrets**: CodeScanner found no hardcoded credentials
4. **No dangerous patterns**: CodeScanner found no destructive commands

**Common Auto-Approved Requests**:
- Read-only commands: `docker logs`, `docker ps`, `docker inspect`
- Status checks: `curl health`, `GET /metrics`
- File reading: `cat`, `tail`, `head`, `less`
- Info commands: `ls`, `pwd`, `whoami`, `uptime`

**What to Do**:
- Proceed with execution (request is approved)
- Check `validation` section if you want to understand why it was auto-approved

### Step 3C: MANUAL_REVIEW (Sent to Telegram)

**Response**:
```json
{
  "needs_approval": true,
  "status": "PENDING",
  "request": {
    "request_id": "req_def456",
    "worker_id": "deploy-worker-003",
    "task_name": "Deploy new feature to PRD",
    "status": "PENDING",
    "risk_level": "MEDIUM"
  },
  "validation": {
    "overall_score": 78,
    "recommendation": "MANUAL_REVIEW",
    "risk_level": "MEDIUM",
    "reasoning": "Profile 'deployment': Overall score 78; risk MEDIUM. Manual review required.",
    "validator_scores": {
      "code_scanner": 85,
      "content_quality": 75,
      "dependency_analyzer": 70,
      "semantic_analyzer": 75
    },
    "profile": "deployment",
    "active_validators": ["code_scanner", "content_quality", "dependency_analyzer", "semantic_analyzer"]
  }
}
```

**What This Means**:
- Request sent to human approver via Telegram
- Worker must wait for approval before execution
- Validation report included in Telegram notification

**Telegram Notification Includes**:
- Task name and worker ID
- Risk level and risk reason
- **Validation report**:
  - Overall validation score
  - Profile used (operational vs deployment)
  - Individual validator scores
  - Reasoning for manual review

**Reasons for Manual Review**:
1. **Medium/High risk**: Not low enough for auto-approve
2. **Score below auto-approve threshold**: Good but not excellent (75-85 range)
3. **Mixed validator results**: Some validators high, some low
4. **Validation disabled or unavailable**: Falls back to heuristic risk assessment

**What to Do**:
1. **Worker/Bot**: Wait for approval notification (poll `GET /approvals/pending` or webhook)
2. **Approver**: Review Telegram notification and validation report
3. **Approver**: Approve via Telegram buttons or API (`POST /approvals/{id}/approve`)
4. **Worker/Bot**: Proceed with execution after approval

---

## Reading Validation Reports

### Validation Report Structure

```json
{
  "overall_score": 78,           // Weighted average (0-100)
  "recommendation": "MANUAL_REVIEW",  // REJECT, APPROVE, or MANUAL_REVIEW
  "risk_level": "MEDIUM",        // LOW, MEDIUM, HIGH, CRITICAL
  "reasoning": "Profile 'deployment': Overall score 78; risk MEDIUM. Manual review required.",
  "validator_scores": {
    "code_scanner": 85,          // Pattern-based safety check (0-100)
    "semantic_analyzer": 75,     // Intent and risk assessment (0-100)
    "dependency_analyzer": 70,   // Blast radius (converted from risk_level)
    "content_quality": 75        // 10-point framework quality (0-100)
  },
  "profile": "deployment",       // "operational" or "deployment"
  "active_validators": [         // Which validators were used in scoring
    "code_scanner",
    "content_quality",
    "dependency_analyzer",
    "semantic_analyzer"
  ]
}
```

### Understanding Validator Scores

**CodeScanner (0-100)**:
- **90-100**: No issues (no secrets, no dangerous patterns)
- **60-89**: Minor concerns (borderline patterns, needs review)
- **30-59**: Moderate concerns (some risky patterns detected)
- **0-29**: Critical issues (secrets, very dangerous commands)

**SemanticAnalyzer (0-100)**:
- **80-100**: Clear intent, low risk
- **60-79**: Moderate clarity, medium risk
- **40-59**: Unclear intent, higher risk
- **0-39**: Very unclear or high risk

**DependencyAnalyzer (0-100)**:
- **90-100**: Low blast radius (LOW risk)
- **60**: Medium blast radius (MEDIUM risk)
- **30**: High blast radius (HIGH risk)
- **10**: Critical blast radius (CRITICAL risk)

**ContentQualityValidator (0-100)**:
- **90-100**: Excellent 10-point framework (all sections clear and detailed)
- **70-89**: Good quality (minor issues, some vague sections)
- **50-69**: Moderate quality (several vague or missing sections)
- **0-49**: Poor quality (many sections missing or vague)

### Understanding Profiles

**Operational Profile** (read-only, low-risk):
- **Active Validators**: CodeScanner (60%), SemanticAnalyzer (40%)
- **Skipped**: ContentQualityValidator (10-point framework not required)
- **Auto-Approve Threshold**: 85
- **Focus**: Safety (no secrets, no dangerous commands)

**Deployment Profile** (write operations, high-risk):
- **Active Validators**: All 4 validators with balanced weights
- **Auto-Approve Threshold**: 90 (stricter)
- **Focus**: Comprehensive assessment (safety, quality, dependencies, intent)

---

## Example Scenarios

### Scenario 1: Operational Command (Auto-Approved)

**Request**:
```json
{
  "task_name": "Check API health",
  "instruction": "docker exec wingman-prd-api curl -s http://localhost:5000/health"
}
```

**Validation Result**:
- **Profile**: operational (curl health keyword detected)
- **CodeScanner**: 95 (safe command, no secrets)
- **SemanticAnalyzer**: 90 (clear intent, low risk)
- **Overall Score**: 93 (95 * 0.6 + 90 * 0.4)
- **Outcome**: AUTO_APPROVED (score >= 85, risk LOW)

**Why Auto-Approved**:
- Read-only operation (curl GET)
- No dangerous patterns
- Clear operational intent
- Low blast radius

**What Happens Next**:
- Worker receives immediate approval
- Executes curl command
- Returns health check result

### Scenario 2: Deployment with Good Framework (Manual Review)

**Request**:
```json
{
  "task_name": "Deploy feature X to PRD",
  "instruction": "... full 10-point framework with clear DELIVERABLES, SUCCESS_CRITERIA, etc. ..."
}
```

**Validation Result**:
- **Profile**: deployment (deploy keyword detected)
- **CodeScanner**: 90 (safe commands, no secrets)
- **ContentQuality**: 85 (good 10-point framework, minor vague sections)
- **DependencyAnalyzer**: 60 (MEDIUM blast radius, affects API)
- **SemanticAnalyzer**: 75 (clear intent, moderate risk)
- **Overall Score**: 77 (weighted average)
- **Outcome**: MANUAL_REVIEW (score < 90, risk MEDIUM)

**Why Manual Review**:
- Deployment operation (requires careful review)
- Good quality but not excellent (score 77 < threshold 90)
- Medium risk (not LOW, so no auto-approve)

**What Happens Next**:
- Request sent to Telegram with full validation report
- Approver reviews quality scores and risk assessment
- Approver can make informed decision based on validation insights
- If approved, worker proceeds with deployment

### Scenario 3: Dangerous Request (Auto-Rejected)

**Request**:
```json
{
  "task_name": "Emergency database fix",
  "instruction": "docker exec postgres psql -c 'DROP TABLE users; CREATE TABLE users ...' -e PASSWORD=admin123"
}
```

**Validation Result**:
- **Profile**: deployment (DROP TABLE keyword detected)
- **CodeScanner**: 0 (hardcoded password detected: PASSWORD=admin123)
- **Outcome**: AUTO_REJECTED (secrets found, immediate reject)

**Why Auto-Rejected**:
- **Critical Issue**: Hardcoded credential (`PASSWORD=admin123`)
- Security policy: Never allow secrets in instructions
- Even if other validators scored high, secrets trigger immediate reject

**What Happens Next**:
- Request immediately rejected
- Response explains secrets were found
- Worker must revise request:
  - Remove hardcoded password
  - Use environment variable or secure credential store
  - Resubmit corrected request

**Corrected Request**:
```json
{
  "task_name": "Emergency database fix",
  "instruction": "docker exec postgres psql -c 'DROP TABLE users; CREATE TABLE users ...' (uses container env var for password)"
}
```

### Scenario 4: Vague Request (Auto-Rejected)

**Request**:
```json
{
  "task_name": "Fix the thing",
  "instruction": "DELIVERABLES: Do it\nSUCCESS_CRITERIA: It works\nMITIGATION: None\n..."
}
```

**Validation Result**:
- **Profile**: deployment (default when uncertain)
- **CodeScanner**: 85 (no dangerous patterns)
- **ContentQuality**: 15 (all sections vague/missing details)
- **Overall Score**: 28 (below hard floor of 30)
- **Outcome**: AUTO_REJECTED (quality too low)

**Why Auto-Rejected**:
- **Critical Issue**: ContentQuality score (15) below hard floor (30)
- Vague deliverables, non-measurable criteria, no mitigation plan
- Cannot assess safety without clear instructions

**What Happens Next**:
- Request immediately rejected
- Response explains quality is too low
- Worker must revise with proper 10-point framework:
  - Clear, specific deliverables
  - Measurable success criteria
  - Detailed mitigation plan
  - Proper risk assessment

---

## How to Improve Validation Scores

### Improving CodeScanner Score

**Common Issues**:
- Hardcoded secrets (API keys, passwords, tokens)
- Dangerous commands (`rm -rf`, `DROP TABLE`, `--force`)
- Privilege escalation (`sudo`, `chmod 777`)

**How to Fix**:
1. **Remove hardcoded secrets**: Use environment variables or secret management
   ```bash
   # BAD
   export API_KEY=sk-12345

   # GOOD
   export API_KEY=${SECURE_API_KEY}  # from environment
   ```

2. **Avoid force flags**: Let system use safe defaults
   ```bash
   # BAD
   git push --force --no-verify

   # GOOD
   git push  # let pre-push hooks run
   ```

3. **Use safer alternatives**:
   ```bash
   # BAD
   rm -rf /data/*

   # GOOD
   # List files first, confirm, then delete specific files
   ls /data && rm /data/specific-file.txt
   ```

### Improving ContentQuality Score

**Common Issues**:
- Vague deliverables ("do the thing", "fix it")
- Non-measurable success criteria ("it works", "looks good")
- Missing or minimal mitigation plans ("none", "N/A")

**How to Fix**:
1. **Write specific deliverables**:
   ```
   # BAD
   DELIVERABLES: Fix the API

   # GOOD
   DELIVERABLES:
   - Restart wingman-prd-api container using docker compose
   - Verify /health endpoint returns 200 OK
   - Confirm Telegram bot reconnects within 60 seconds
   ```

2. **Write measurable success criteria**:
   ```
   # BAD
   SUCCESS_CRITERIA: It works

   # GOOD
   SUCCESS_CRITERIA:
   - API /health returns HTTP 200 within 5 seconds of restart
   - Telegram bot sends "reconnected" message within 60 seconds
   - No error logs in docker logs for 5 minutes post-restart
   ```

3. **Write detailed mitigation plans**:
   ```
   # BAD
   MITIGATION: None

   # GOOD
   MITIGATION:
   - If restart fails: check docker logs for error messages
   - If health check fails: rollback to previous container image
   - If Telegram bot doesn't reconnect: manually restart telegram-bot container
   - Rollback command: docker compose -f docker-compose.prd.yml up -d --no-deps wingman-api
   ```

### Improving DependencyAnalyzer Score (Reducing Blast Radius)

**Common Issues**:
- Operations affect multiple critical services (postgres, redis)
- No clear impact assessment

**How to Fix**:
1. **Identify affected services explicitly**:
   ```
   DEPENDENCIES:
   - postgres (wingman-prd-postgres): required for approval storage
   - redis (wingman-prd-redis): required for session caching
   - wingman-api: depends on both postgres and redis
   - telegram-bot: depends on wingman-api

   BLAST RADIUS: HIGH
   - If postgres fails: all approvals fail, system becomes read-only
   - If redis fails: sessions lost, but system remains functional
   ```

2. **Scope operations to minimize impact**:
   ```bash
   # BAD (affects all services)
   docker compose -f docker-compose.prd.yml down && up -d

   # GOOD (affects only API)
   docker compose -f docker-compose.prd.yml up -d --no-deps wingman-api
   ```

### Improving SemanticAnalyzer Score

**Common Issues**:
- Unclear intent (why is this operation needed?)
- Risky operations without justification

**How to Fix**:
1. **State intent clearly**:
   ```
   TASK: Emergency API restart due to memory leak

   WHY: API container memory usage at 95%, causing slow response times
   EXPECTED OUTCOME: Memory usage drops to <50%, response times improve
   ```

2. **Justify risky operations**:
   ```
   TASK: Restart postgres container

   JUSTIFICATION: Postgres has been running for 45 days, routine maintenance restart
   TIMING: Low-traffic period (2 AM UTC), <30 second downtime expected
   NOTIFICATION: Mark notified via Slack, standing by for rollback if needed
   ```

---

## Feature Flags and Gradual Rollout

### Checking if Validation is Enabled

**Environment Variables**:
- `VALIDATION_ENABLED`: 1=enabled, 0=disabled
- `VALIDATION_ROLLOUT_PERCENT`: 0-100 (percentage of requests to validate)

**How to Check**:
```bash
# Check if validation is enabled in container
docker exec wingman-prd-api printenv | grep VALIDATION

# Should see:
VALIDATION_ENABLED=1
VALIDATION_ROLLOUT_PERCENT=100
```

### Gradual Rollout Example

**Week 1**: Enable for 10% of requests
```bash
# .env.prd
VALIDATION_ENABLED=1
VALIDATION_ROLLOUT_PERCENT=10

# Restart API
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d wingman-api
```

**Week 2**: Increase to 50%
```bash
# .env.prd
VALIDATION_ROLLOUT_PERCENT=50
```

**Week 3**: Enable for all requests
```bash
# .env.prd
VALIDATION_ROLLOUT_PERCENT=100
```

**How Rollout Works**:
- System hashes `worker_id + instruction` to get a consistent value (0-99)
- If hash < `VALIDATION_ROLLOUT_PERCENT`, validation runs
- Same request always gets same decision (consistent behavior)

---

## Frequently Asked Questions

### Q: Can I bypass validation for urgent requests?

**A**: No, validation cannot be bypassed on a per-request basis. However:
- If request is auto-rejected, fix the issue and resubmit
- If validation is too strict, contact admin to disable (`VALIDATION_ENABLED=0`)
- Emergency: Admin can disable validation globally for all requests

### Q: Why was my safe request auto-rejected?

**A**: Check the validation report's `reasoning` and `validator_scores`:
- **CodeScanner = 0**: Likely detected a secret or credential (even if unintentional)
- **ContentQuality < 30**: 10-point framework sections are too vague
- **Any validator < 30**: Hit the hard floor, need to improve that specific validator

### Q: Why was my risky request auto-approved?

**A**: This may indicate validation is too lenient. Check:
- **Profile**: Was it detected as "operational" when it should be "deployment"?
- **Thresholds**: Are auto-approve thresholds too low?
- **Report to admin**: Share the request and validation report for tuning

### Q: How long does validation take?

**A**: Typically <1 second. Validation runs synchronously during approval request processing.

### Q: What happens if validation fails (error/timeout)?

**A**: System falls back to heuristic risk assessment (pre-validation behavior):
- No auto-reject (safe fallback)
- Risk assessment based on keywords only
- Request still sent to manual review if risk >= MEDIUM

### Q: Can I see validation results for past requests?

**A**: Yes, validation results are stored in the database with each approval request:
```bash
# Query validation results
curl http://127.0.0.1:5001/approvals/{request_id}

# Response includes validation section
```

---

## Related Documentation

- **Operational Guide**: `../03-operations/VALIDATION_OPERATIONAL_GUIDE.md` (for admins/operators)
- **Architecture**: `../02-architecture/AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md`
- **Deployment Plan**: `../deployment/AAA_DELTA_REPORT_VALIDATION_DEPLOYMENT.md`
- **Schematic**: `../02-architecture/VALIDATION_ARCHITECTURE_SCHEMATIC.md` (to be created)

---

**Document End**
