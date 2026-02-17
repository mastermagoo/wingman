# Output Validation User Guide

**Created**: 2026-02-16
**Status**: CURRENT
**Scope**: Phase 6.1 Output Validation integration for AI workers

---

## Overview

**Phase 6.1 Output Validation** provides automated quality and security validation for AI-generated code before deployment. This system ensures that code produced by AI workers meets quality standards and doesn't introduce security vulnerabilities.

**Key Features**:

- **5 Validators**: Syntax, Security, Dependency, Test Execution, Composite
- **3 Decision Outcomes**: AUTO_APPROVE, AUTO_REJECT, MANUAL_REVIEW
- **Security Integration**: Automatic worker quarantine on critical security issues
- **Audit Trail**: All validations logged in Postgres database
- **Telegram Notifications**: Real-time alerts for validation outcomes

---

## Quick Start

### 1. Validate Generated Code

After your AI worker generates code files, call the validation endpoint:

```bash
curl -X POST http://127.0.0.1:8101/output_validation/validate \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "intel_worker_001",
    "generated_files": [
      "/path/to/semantic_analyzer.py",
      "/path/to/test_semantic_analyzer.py"
    ],
    "task_name": "Generate Semantic Analyzer"
  }'
```

### 2. Handle Response

The API returns one of three status codes:

- **200 OK + status: "APPROVED"**: Code passed validation - safe to deploy
- **200 OK + status: "PENDING"**: Manual review required - approval request created
- **403 Forbidden + status: "REJECTED"**: Code blocked due to critical issues - do NOT deploy

---

## API Reference

### Endpoint

```
POST /output_validation/validate
```

### Request Body

```json
{
  "worker_id": "string (required)",
  "generated_files": ["array of file paths (required)"],
  "task_name": "string (optional)"
}
```

**Fields**:

- `worker_id`: Unique identifier for your AI worker (e.g., "intel_worker_001")
- `generated_files`: Array of absolute file paths to validate
- `task_name`: Human-readable task description (optional, defaults to "Code Generation")

### Response: AUTO_APPROVE (200 OK)

Code passed all validators and is safe to deploy.

```json
{
  "status": "APPROVED",
  "validation_report": {
    "decision": "APPROVE",
    "overall_score": 95,
    "recommendation": "Code passed all validators. Safe to deploy.",
    "validation_id": 123
  },
  "message": "Code passed validation. Safe to deploy."
}
```

**Action**: Deploy the code immediately.

### Response: AUTO_REJECT (403 Forbidden)

Code has critical issues and is blocked.

```json
{
  "status": "REJECTED",
  "reason": "Syntax errors detected",
  "validation_report": {
    "decision": "REJECT",
    "overall_score": 45,
    "blocking_issues": [
      "Syntax error in semantic_analyzer.py: unexpected EOF while parsing",
      "Missing required import: typing module"
    ],
    "recommendation": "Fix syntax errors and missing imports before deployment",
    "validation_id": 124
  }
}
```

**Action**: Do NOT deploy. Fix the issues listed in `blocking_issues` and resubmit for validation.

### Response: MANUAL_REVIEW (200 OK)

Code requires human review before deployment.

```json
{
  "status": "PENDING",
  "approval_id": "APR_20260216_001",
  "validation_report": {
    "decision": "MANUAL_REVIEW",
    "overall_score": 65,
    "blocking_issues": [],
    "recommendation": "Code quality concerns. Manual review recommended.",
    "validation_id": 125
  },
  "message": "Manual review required. Approval request created."
}
```

**Action**: Wait for Mark to approve via Telegram. Poll the approval status or wait for notification.

### Response: WORKER_QUARANTINED (403 Forbidden)

Worker has been quarantined due to previous violations.

```json
{
  "status": "REJECTED",
  "rejection_reason": "WORKER_QUARANTINED",
  "reason": "Worker quarantined: CRITICAL security issue in generated code",
  "quarantined_at": "2026-02-16T10:30:00",
  "message": "Contact Mark to release this worker via /release_worker command"
}
```

**Action**: Contact Mark to investigate and potentially release the worker.

---

## Decision Logic Explained

### AUTO_APPROVE Criteria

Code is automatically approved if ALL of the following are true:

- Overall validation score >= 70 (out of 100)
- No syntax errors detected
- No CRITICAL security issues
- No missing critical dependencies
- All tests pass (if tests exist)

### AUTO_REJECT Criteria

Code is automatically rejected if ANY of the following are true:

- Overall validation score < 50
- Syntax errors detected
- CRITICAL security issues (hardcoded secrets, dangerous imports)
- Missing critical dependencies that block execution
- Test failures in critical test cases

**Note**: CRITICAL security issues trigger automatic worker quarantine.

### MANUAL_REVIEW Criteria

Code requires manual review if:

- Overall validation score is between 50-69
- Non-critical security issues detected (LOW, MEDIUM severity)
- Missing non-critical dependencies
- Test warnings or non-critical test failures
- Code quality concerns (poor documentation, complex logic)

---

## Validators Explained

### 1. SyntaxValidator

**Purpose**: Validates Python syntax using `ast.parse()`

**Checks**:

- Valid Python syntax
- No missing parentheses, brackets, or quotes
- No indentation errors

**Blocking Issues**:

- Syntax errors (immediate reject)

**Example Issue**:

```
Syntax error in semantic_analyzer.py: unexpected EOF while parsing (line 45)
```

### 2. OutputSecurityScanner

**Purpose**: Detects security vulnerabilities and dangerous patterns

**Checks**:

- Hardcoded secrets (API keys, passwords, tokens)
- Dangerous imports (os, subprocess, eval)
- SQL injection patterns
- Command injection patterns
- File system traversal patterns

**Severity Levels**:

- **CRITICAL**: Hardcoded secrets, command injection (immediate reject + quarantine)
- **HIGH**: Dangerous imports without proper safeguards (reject)
- **MEDIUM**: Suspicious patterns, potential vulnerabilities (manual review)
- **LOW**: Code quality concerns (manual review)

**Example Issue**:

```
CRITICAL: Hardcoded API key detected in semantic_analyzer.py (line 12):
API_KEY = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
```

### 3. DependencyVerifier

**Purpose**: Validates that all imported modules are available

**Checks**:

- All imports can be resolved
- Required dependencies are installed in container
- No circular imports

**Method**: Docker exec into Wingman API container to verify imports

**Blocking Issues**:

- Missing critical dependencies (immediate reject)
- Import errors

**Example Issue**:

```
Missing dependency: nltk (required in semantic_analyzer.py line 5)
```

### 4. TestExecutor

**Purpose**: Runs automated tests for generated code

**Checks**:

- Tests execute without errors
- All test cases pass
- No test timeouts

**Method**: Runs pytest in docker container (if pytest available)

**Blocking Issues**:

- Test failures in critical test cases (manual review or reject)

**Example Issue**:

```
Test failure: test_semantic_analyzer.py::test_risk_analysis FAILED
AssertionError: Expected risk level HIGH, got MEDIUM
```

### 5. OutputCompositeValidator

**Purpose**: Orchestrates all validators and makes final decision

**Scoring**:

- Syntax: 30 points
- Security: 30 points
- Dependencies: 20 points
- Tests: 20 points

**Decision Logic**:

- Score >= 70 + no blocking issues = AUTO_APPROVE
- Score < 50 OR blocking issues = AUTO_REJECT
- Score 50-69 = MANUAL_REVIEW

---

## Integration Guide

### For intel-system AI Workers

After generating code, validate before deployment:

```python
import requests

# Generate code files
generated_files = [
    "/path/to/semantic_analyzer.py",
    "/path/to/test_semantic_analyzer.py"
]

# Validate via Wingman
response = requests.post(
    "http://127.0.0.1:8101/output_validation/validate",
    json={
        "worker_id": "intel_worker_001",
        "generated_files": generated_files,
        "task_name": "Generate Semantic Analyzer"
    }
)

result = response.json()

if result["status"] == "APPROVED":
    print("✅ Code approved - deploying...")
    # Deploy code
    deploy_code(generated_files)
elif result["status"] == "REJECTED":
    print(f"❌ Code rejected: {result['reason']}")
    print("Blocking issues:")
    for issue in result["validation_report"]["blocking_issues"]:
        print(f"  - {issue}")
    # Fix issues and retry
elif result["status"] == "PENDING":
    print(f"⏳ Manual review required - approval ID: {result['approval_id']}")
    # Wait for approval
    wait_for_approval(result["approval_id"])
```

### For cv-automation AI Workers

Similar integration pattern:

```python
from wingman_client import WingmanClient

client = WingmanClient(system_name="cv-automation")

# Generate code
generated_files = generate_cv_parser()

# Validate
validation_result = client.validate_output(
    worker_id="cv_worker_001",
    generated_files=generated_files,
    task_name="Generate CV Parser"
)

# Handle decision
if validation_result["decision"] == "APPROVE":
    deploy_code(generated_files)
elif validation_result["decision"] == "REJECT":
    fix_issues(validation_result["blocking_issues"])
else:  # MANUAL_REVIEW
    wait_for_approval(validation_result["approval_id"])
```

### Error Handling

Always handle validation errors gracefully:

```python
try:
    response = requests.post(
        "http://127.0.0.1:8101/output_validation/validate",
        json={"worker_id": "worker_001", "generated_files": files},
        timeout=60
    )
    response.raise_for_status()
    result = response.json()
except requests.exceptions.Timeout:
    print("❌ Validation timeout - treat as MANUAL_REVIEW")
    # Create manual approval request
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 403:
        # Code rejected or worker quarantined
        print(f"❌ Validation failed: {e.response.json()['reason']}")
    else:
        raise
except Exception as e:
    print(f"❌ Validation error: {e}")
    # Fallback to manual review
```

---

## Environment Configuration

### TEST Environment

**URL**: `http://127.0.0.1:8101`

**Configuration**: Output validation enabled by default

```bash
# .env.test
VALIDATION_ENABLED=1
VALIDATION_ROLLOUT_PERCENT=100
```

**Behavior**: All validations run immediately

### PRD Environment

**URL**: `http://127.0.0.1:5001`

**Configuration**: Output validation disabled by default (gradual rollout)

```bash
# .env.prd
VALIDATION_ENABLED=0
VALIDATION_ROLLOUT_PERCENT=0
```

**Behavior**: Returns error until enabled

**To Enable in PRD**:

1. Update `.env.prd`: `VALIDATION_ENABLED=1`
2. Restart Wingman API container:

```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman
docker compose -f docker-compose.prd.yml -p wingman-prd up -d wingman-api
```

3. Verify health: `curl http://127.0.0.1:5001/health`

**Gradual Rollout**:

```bash
# Enable for 25% of requests
VALIDATION_ENABLED=1
VALIDATION_ROLLOUT_PERCENT=25
```

---

## Monitoring and Audit

### View Validation History

All validations are stored in the `output_validations` table:

```sql
-- Recent validations
SELECT
    validation_id,
    worker_id,
    decision,
    overall_score,
    created_at
FROM output_validations
ORDER BY created_at DESC
LIMIT 10;

-- Validation statistics
SELECT
    decision,
    COUNT(*) as count,
    AVG(overall_score) as avg_score
FROM output_validations
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY decision;
```

### Telegram Notifications

Wingman sends Telegram notifications for all validation outcomes:

- **AUTO_APPROVE**: Low priority notification (FYI)
- **AUTO_REJECT**: High priority alert with blocking issues
- **MANUAL_REVIEW**: Approval request with validation report

### Check Validation Status

Query specific validation:

```bash
curl http://127.0.0.1:8101/approvals/pending
```

---

## Troubleshooting

### Issue: "Output validation not available"

**Cause**: Output validation module not loaded in API container

**Solution**:

```bash
# Rebuild and restart API container
cd /Volumes/Data/ai_projects/wingman-system/wingman
docker compose -f docker-compose.yml -p wingman-test build wingman-api
docker compose -f docker-compose.yml -p wingman-test up -d wingman-api

# Verify health
curl http://127.0.0.1:8101/health | jq '.output_validation'
```

### Issue: "Missing 'generated_files' field"

**Cause**: Request body doesn't include required `generated_files` array

**Solution**: Ensure request includes `generated_files` field:

```json
{
  "worker_id": "worker_001",
  "generated_files": ["file1.py", "file2.py"]  // <-- Required
}
```

### Issue: Worker quarantined

**Cause**: Worker generated code with CRITICAL security issues

**Solution**:

1. Check quarantine reason:

```bash
curl http://127.0.0.1:8101/workers/intel_worker_001/status
```

2. Fix security issues in code generation logic
3. Contact Mark to release worker via Telegram: `/release_worker intel_worker_001`

### Issue: Dependency verification fails

**Cause**: Docker container not available or missing dependencies

**Solution**:

```bash
# Verify container is running
docker ps | grep wingman-api

# Install missing dependencies in container
docker exec wingman-test-wingman-api-1 pip install <missing-package>

# Or rebuild image with dependencies in requirements.txt
```

### Issue: Tests not running

**Cause**: pytest not installed in container

**Solution**:

```bash
# Install pytest in container
docker exec wingman-test-wingman-api-1 pip install pytest

# Or add to requirements.txt and rebuild
```

---

## Best Practices

### 1. Always Validate Before Deployment

Never deploy AI-generated code without validation:

```python
# ❌ BAD: Deploy without validation
generated_files = generate_code()
deploy_code(generated_files)

# ✅ GOOD: Validate first
generated_files = generate_code()
validation_result = validate_code(generated_files)
if validation_result["decision"] == "APPROVE":
    deploy_code(generated_files)
```

### 2. Handle All Three Decision Outcomes

Don't assume code will always be approved:

```python
# ✅ GOOD: Handle all cases
if decision == "APPROVE":
    deploy_code()
elif decision == "REJECT":
    fix_issues_and_retry()
elif decision == "MANUAL_REVIEW":
    wait_for_approval()
```

### 3. Log Validation Results

Store validation IDs for audit trail:

```python
validation_id = result["validation_report"]["validation_id"]
logger.info(f"Code validated: validation_id={validation_id}, decision={decision}")
```

### 4. Use Unique Worker IDs

Use consistent, descriptive worker IDs:

```python
# ✅ GOOD: Descriptive worker ID
worker_id = "intel_semantic_analyzer_worker_001"

# ❌ BAD: Generic worker ID
worker_id = "worker1"
```

### 5. Include Task Names

Help human reviewers understand context:

```python
# ✅ GOOD: Descriptive task name
task_name = "Generate Semantic Analyzer with Risk Assessment"

# ❌ BAD: Generic task name
task_name = "Code Generation"
```

---

## Related Documentation

- **Architecture**: `../02-architecture/AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md`
- **Test Documentation**: `../../tests/OUTPUT_VALIDATION_TESTS_README.md`
- **Test Summary**: `../../tests/OUTPUT_VALIDATION_TEST_SUMMARY.md`
- **Complete Plan**: `../00-Strategic/AAA_AI_WORKER_OUTPUT_VALIDATION_COMPLETE_PLAN.md`
- **Deployment**: `../deployment/AAA_DEPLOYMENT_COMPLETE.md`

---

## Support

For issues or questions:

1. Check Telegram notifications for validation reports
2. Query validation history in Postgres database
3. Review API logs: `docker logs wingman-test-wingman-api-1`
4. Contact Mark via Telegram

---

**Document Status**: COMPLETE
**Last Updated**: 2026-02-16
**Maintainer**: Wingman Development Team
