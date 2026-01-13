#!/usr/bin/env python3
"""
Worker Generator for META_WORKER_WINGMAN_03
Generates workers 088-225 for Phases 3-6 (Integration, Testing, Deployment, Tuning)

Total: 138 workers
- Phase 3: 15 workers (WORKER_088-102)
- Phase 4: 108 workers (WORKER_103-210)
- Phase 5: 9 workers (WORKER_211-219)
- Phase 6: 6 workers (WORKER_220-225)
"""

import os
import json
from datetime import datetime
from pathlib import Path

# Define worker specifications
WORKERS_SPEC = {
    # Phase 3: Integration (15 workers)
    "088": {
        "title": "Composite_Validator_Skeleton",
        "phase": "3.1 - Composite Validator",
        "deliverables": [
            "Create file: `wingman/validation/composite_validator.py`",
            "Implement class `CompositeValidator` with `__init__` method",
            "Add validator references for semantic, code, dependency, content",
            "Add basic imports and module docstring",
            "Test results file: `ai-workers/results/worker-088-results.json`"
        ],
        "success_criteria": [
            "File created at specified path",
            "Class `CompositeValidator` instantiates without error",
            "Constructor accepts 4 validator objects",
            "Module imports successfully",
            "Basic smoke test passes: `validator = CompositeValidator(s, c, d, q); assert validator is not None`"
        ],
        "test_commands": [
            "test -f wingman/validation/composite_validator.py && echo 'PASS: File exists' || echo 'FAIL: File missing'",
            "cd wingman && python3 -c \"from validation.composite_validator import CompositeValidator; print('PASS: Import successful')\" || echo 'FAIL: Import failed'",
            "cd wingman && python3 -c \"from validation.composite_validator import CompositeValidator; from validation.semantic_analyzer import SemanticAnalyzer; from validation.code_scanner import CodeScanner; from validation.dependency_analyzer import DependencyAnalyzer; from validation.content_quality_validator import ContentQualityValidator; s=SemanticAnalyzer(); c=CodeScanner(); d=DependencyAnalyzer(); q=ContentQualityValidator(); v=CompositeValidator(s,c,d,q); assert v is not None; print('PASS: Instantiation successful')\""
        ],
        "dependencies": [
            "Phase 1-2 complete (WORKER_001-087 executed)",
            "All 4 validators available: SemanticAnalyzer, CodeScanner, DependencyAnalyzer, ContentQualityValidator",
            "Python 3.9+ environment"
        ],
        "task_type": "MECHANICAL",
        "tests_covered": []
    },
    "089": {
        "title": "Composite_Validator_Call_All_Validators",
        "phase": "3.1 - Composite Validator",
        "deliverables": [
            "Implement `validate()` method in `CompositeValidator`",
            "Call semantic_analyzer.analyze(instruction, task_name, env)",
            "Call code_scanner.scan(instruction)",
            "Call dependency_analyzer.analyze(instruction, task_name, env)",
            "Call content_quality_validator.assess(instruction)",
            "Collect all 4 validator results",
            "Test results file: `ai-workers/results/worker-089-results.json`"
        ],
        "success_criteria": [
            "`validate()` method exists and callable",
            "Calls all 4 validators in sequence",
            "Returns dict with 4 result sets: semantic, code, dependency, content",
            "Test with sample instruction: all 4 validators executed",
            "Error handling: if one validator fails, others still run"
        ],
        "test_commands": [
            "cd wingman && python3 -c \"from validation.composite_validator import CompositeValidator; v=CompositeValidator(); result=v.validate('DELIVERABLES: Test\\nSUCCESS_CRITERIA: Test\\n...', 'test', 'test'); assert 'semantic' in result; assert 'code' in result; assert 'dependency' in result; assert 'content' in result; print('PASS: All validators called')\"",
        ],
        "dependencies": [
            "WORKER_088 complete (CompositeValidator skeleton)",
            "All 4 validators fully implemented (Phase 1-2)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": []
    },
    "090": {
        "title": "Composite_Validator_Score_Combination",
        "phase": "3.1 - Composite Validator",
        "deliverables": [
            "Implement `_calculate_final_score()` method",
            "Combine semantic (risk level), code (dangerous patterns), dependency (blast radius), content (quality score)",
            "Weight calculation: content quality 40%, semantic risk 30%, dependency 20%, code 10%",
            "Return final score 0-100",
            "Add `recommendation` field: AUTO_APPROVE, AUTO_REJECT, MANUAL_REVIEW",
            "Test results file: `ai-workers/results/worker-090-results.json`"
        ],
        "success_criteria": [
            "`_calculate_final_score()` method exists",
            "Scores combined with correct weights",
            "Final score normalized to 0-100 range",
            "Recommendation based on score and risk level",
            "Test: LOW risk + quality 95 → score ≥90, recommendation=AUTO_APPROVE"
        ],
        "test_commands": [
            "cd wingman && python3 -c \"from validation.composite_validator import CompositeValidator; v=CompositeValidator(); score=v._calculate_final_score({'risk_level': 'LOW'}, {'dangerous_count': 0}, {'blast_radius': 'LOW'}, {'overall_quality': 95}); assert 85 <= score <= 100; print(f'PASS: Score calculation: {score}')\"",
        ],
        "dependencies": [
            "WORKER_089 complete (validate method)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": []
    },
    "091": {
        "title": "Composite_Validator_Auto_Approve_Logic",
        "phase": "3.1 - Composite Validator",
        "deliverables": [
            "Implement auto-approve logic in `_determine_recommendation()`",
            "Condition: risk_level == 'LOW' AND final_score >= 90",
            "Return 'AUTO_APPROVE' when conditions met",
            "Add reasoning field explaining auto-approve decision",
            "Test with 5 scenarios (including edge cases at score=90)",
            "Test results file: `ai-workers/results/worker-091-results.json`"
        ],
        "success_criteria": [
            "LOW risk + score 95 → AUTO_APPROVE",
            "LOW risk + score 90 → AUTO_APPROVE (boundary)",
            "LOW risk + score 89.9 → MANUAL_REVIEW (just below boundary)",
            "MEDIUM risk + score 95 → MANUAL_REVIEW (not auto-approved)",
            "HIGH risk + score 95 → MANUAL_REVIEW (not auto-approved)"
        ],
        "test_commands": [
            "cd wingman && python3 -c \"from validation.composite_validator import CompositeValidator; v=CompositeValidator(); assert v._determine_recommendation('LOW', 95) == 'AUTO_APPROVE'; assert v._determine_recommendation('LOW', 90) == 'AUTO_APPROVE'; assert v._determine_recommendation('LOW', 89.9) == 'MANUAL_REVIEW'; assert v._determine_recommendation('MEDIUM', 95) == 'MANUAL_REVIEW'; print('PASS: Auto-approve logic correct')\"",
        ],
        "dependencies": [
            "WORKER_090 complete (score calculation)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": []
    },
    "092": {
        "title": "Composite_Validator_Auto_Reject_Logic",
        "phase": "3.1 - Composite Validator",
        "deliverables": [
            "Implement auto-reject logic in `_determine_recommendation()`",
            "Condition 1: final_score < 60 → AUTO_REJECT",
            "Condition 2: risk_level == 'CRITICAL' → AUTO_REJECT (regardless of score)",
            "Add reasoning field explaining auto-reject decision",
            "Test with 6 scenarios (including edge cases at score=60)",
            "Test results file: `ai-workers/results/worker-092-results.json`"
        ],
        "success_criteria": [
            "Score 50 → AUTO_REJECT",
            "Score 59 → AUTO_REJECT (just below threshold)",
            "Score 60 → MANUAL_REVIEW (at threshold)",
            "CRITICAL risk + score 100 → AUTO_REJECT (risk override)",
            "HIGH risk + score 50 → AUTO_REJECT (both conditions)",
            "Reasoning field populated for all rejections"
        ],
        "test_commands": [
            "cd wingman && python3 -c \"from validation.composite_validator import CompositeValidator; v=CompositeValidator(); assert v._determine_recommendation('LOW', 50) == 'AUTO_REJECT'; assert v._determine_recommendation('LOW', 59) == 'AUTO_REJECT'; assert v._determine_recommendation('LOW', 60) == 'MANUAL_REVIEW'; assert v._determine_recommendation('CRITICAL', 100) == 'AUTO_REJECT'; print('PASS: Auto-reject logic correct')\"",
        ],
        "dependencies": [
            "WORKER_091 complete (auto-approve logic)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": []
    },
    "093": {
        "title": "Composite_Validator_Tests",
        "phase": "3.1 - Composite Validator",
        "deliverables": [
            "Create file: `wingman/tests/test_composite_validator.py`",
            "Test 1: All validators called successfully",
            "Test 2: Score calculation with mock validator results",
            "Test 3: Auto-approve decision (LOW risk, quality 95)",
            "Test 4: Auto-reject decision (quality 50)",
            "Test 5: Manual review decision (MEDIUM risk, quality 75)",
            "Test results file: `ai-workers/results/worker-093-results.json`"
        ],
        "success_criteria": [
            "5/5 tests pass",
            "`pytest wingman/tests/test_composite_validator.py` returns 0 exit code",
            "All code paths covered (auto-approve, auto-reject, manual)"
        ],
        "test_commands": [
            "cd wingman && pytest tests/test_composite_validator.py -v --tb=short",
            "cd wingman && pytest tests/test_composite_validator.py --cov=validation.composite_validator --cov-report=term-missing"
        ],
        "dependencies": [
            "WORKER_088-092 complete (CompositeValidator fully implemented)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": []
    },
}

# Phase 3 continued: API Server Integration (6 workers: 094-099)
WORKERS_SPEC.update({
    "094": {
        "title": "API_Server_Validate_Endpoint",
        "phase": "3.2 - API Integration",
        "deliverables": [
            "Add `/approvals/validate` POST endpoint to `api_server.py`",
            "Accept JSON: {instruction, task_name, deployment_env}",
            "Call CompositeValidator.validate()",
            "Return validation results as JSON",
            "Test results file: `ai-workers/results/worker-094-results.json`"
        ],
        "success_criteria": [
            "Endpoint responds to POST /approvals/validate",
            "Returns 200 OK with validation results",
            "Returns 400 Bad Request for invalid input",
            "Validation results include: semantic, code, dependency, content, final_score, recommendation"
        ],
        "test_commands": [
            "curl -X POST http://localhost:8001/approvals/validate -H 'Content-Type: application/json' -d '{\"instruction\": \"DELIVERABLES: Test\\nSUCCESS_CRITERIA: Test\\n...\", \"task_name\": \"test\", \"deployment_env\": \"test\"}' | jq '.final_score'",
        ],
        "dependencies": [
            "WORKER_093 complete (CompositeValidator fully tested)",
            "API server running (docker compose up)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": []
    },
    "095": {
        "title": "API_Server_Import_Validators",
        "phase": "3.2 - API Integration",
        "deliverables": [
            "Import all 4 validators into `api_server.py`",
            "Initialize validators at startup (module-level)",
            "Pass validator instances to CompositeValidator",
            "Add health check: verify all validators initialized",
            "Test results file: `ai-workers/results/worker-095-results.json`"
        ],
        "success_criteria": [
            "All 4 validators imported successfully",
            "API server starts without import errors",
            "GET /health includes validator_status: ok",
            "Validators accessible in request handlers"
        ],
        "test_commands": [
            "cd wingman && python3 -c \"import api_server; print('PASS: API imports validators')\"",
            "curl http://localhost:8001/health | jq '.validator_status'"
        ],
        "dependencies": [
            "WORKER_094 complete (validate endpoint)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": []
    },
    "096": {
        "title": "API_Server_Validation_In_Request_Flow",
        "phase": "3.2 - API Integration",
        "deliverables": [
            "Modify POST /approvals/request to call validation",
            "Run validation BEFORE creating approval record",
            "Store validation results in approval record (new field)",
            "If AUTO_REJECT: return 400 with rejection reason",
            "If AUTO_APPROVE: set status=AUTO_APPROVED",
            "Test results file: `ai-workers/results/worker-096-results.json`"
        ],
        "success_criteria": [
            "Validation runs on every approval request",
            "AUTO_REJECT requests return 400 immediately",
            "AUTO_APPROVE requests skip manual review queue",
            "Validation results saved in database",
            "Manual review requests include validation in notification"
        ],
        "test_commands": [
            "curl -X POST http://localhost:8001/approvals/request -H 'Content-Type: application/json' -d '{\"instruction\": \"DELIVERABLES: Do it\\nSUCCESS_CRITERIA: none\\n\", \"task_name\": \"bad\", \"deployment_env\": \"test\"}' -w '%{http_code}' | grep 400",
        ],
        "dependencies": [
            "WORKER_095 complete (validators imported)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": []
    },
    "097": {
        "title": "API_Server_Validation_In_Response",
        "phase": "3.2 - API Integration",
        "deliverables": [
            "Add validation_results field to GET /approvals/{id} response",
            "Include: semantic analysis, code scan, dependency, content quality",
            "Add final_score and recommendation to response",
            "Format validation results for Telegram display",
            "Test results file: `ai-workers/results/worker-097-results.json`"
        ],
        "success_criteria": [
            "GET /approvals/{id} includes validation_results",
            "All 4 validator outputs present in response",
            "final_score and recommendation visible",
            "Formatting appropriate for Telegram markdown"
        ],
        "test_commands": [
            "curl http://localhost:8001/approvals/1 | jq '.validation_results.final_score'",
        ],
        "dependencies": [
            "WORKER_096 complete (validation in request flow)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": []
    },
    "098": {
        "title": "API_Server_Validation_Error_Handling",
        "phase": "3.2 - API Integration",
        "deliverables": [
            "Add try/except around validation calls",
            "If LLM timeout: log error, use heuristic fallback",
            "If validator crash: log error, set score=0, continue",
            "Add /approvals/validate/health endpoint (test all validators)",
            "Test results file: `ai-workers/results/worker-098-results.json`"
        ],
        "success_criteria": [
            "LLM timeout doesn't crash API server",
            "Validator failures logged with details",
            "Heuristic fallback used when LLM fails",
            "Health endpoint reports validator status",
            "API continues functioning even if one validator fails"
        ],
        "test_commands": [
            "curl http://localhost:8001/approvals/validate/health | jq '.validators'",
        ],
        "dependencies": [
            "WORKER_097 complete (validation in response)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": []
    },
    "099": {
        "title": "API_Integration_Tests",
        "phase": "3.2 - API Integration",
        "deliverables": [
            "Create file: `wingman/tests/test_api_validation.py`",
            "Test 1: POST /approvals/validate returns validation results",
            "Test 2: POST /approvals/request with poor quality → 400",
            "Test 3: POST /approvals/request with excellent quality → AUTO_APPROVED",
            "Test 4: GET /approvals/{id} includes validation_results",
            "Test 5: Validation error doesn't crash API",
            "Test results file: `ai-workers/results/worker-099-results.json`"
        ],
        "success_criteria": [
            "5/5 tests pass",
            "`pytest wingman/tests/test_api_validation.py` returns 0 exit code",
        ],
        "test_commands": [
            "cd wingman && pytest tests/test_api_validation.py -v --tb=short",
        ],
        "dependencies": [
            "WORKER_098 complete (error handling)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": []
    },
})

# Phase 3 continued: Telegram Notification Enhancement (3 workers: 100-102)
WORKERS_SPEC.update({
    "100": {
        "title": "Telegram_Notification_Validation_Scores",
        "phase": "3.3 - Telegram Integration",
        "deliverables": [
            "Modify `telegram_bot.py` notification formatting",
            "Add validation scores to approval notification",
            "Display: final_score, risk_level, quality_score",
            "Format: Use emojis for risk level (🟢 LOW, 🟡 MEDIUM, 🔴 HIGH)",
            "Test results file: `ai-workers/results/worker-100-results.json`"
        ],
        "success_criteria": [
            "Telegram notification includes validation scores",
            "Scores formatted clearly (e.g., 'Quality: 85/100')",
            "Risk level shown with emoji",
            "Notification still readable (not cluttered)"
        ],
        "test_commands": [
            "# Submit approval request and verify Telegram message includes scores",
            "curl -X POST http://localhost:8001/approvals/request -H 'Content-Type: application/json' -d @test_instruction.json",
        ],
        "dependencies": [
            "WORKER_099 complete (API integration tested)",
            "Telegram bot running",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": []
    },
    "101": {
        "title": "Telegram_Notification_Auto_Indicators",
        "phase": "3.3 - Telegram Integration",
        "deliverables": [
            "Add AUTO_APPROVE indicator to notification",
            "Add AUTO_REJECT indicator (if visible to user)",
            "Show recommendation: AUTO_APPROVE, AUTO_REJECT, MANUAL_REVIEW",
            "Include reasoning for auto decisions",
            "Test results file: `ai-workers/results/worker-101-results.json`"
        ],
        "success_criteria": [
            "AUTO_APPROVE shown with ✅ emoji",
            "MANUAL_REVIEW shown with ⏸️ emoji",
            "Reasoning visible for auto decisions",
            "User understands why decision was made"
        ],
        "test_commands": [
            "# Test with auto-approve scenario (LOW risk, quality 95)",
            "curl -X POST http://localhost:8001/approvals/request -H 'Content-Type: application/json' -d @test_auto_approve.json",
        ],
        "dependencies": [
            "WORKER_100 complete (validation scores in notification)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": []
    },
    "102": {
        "title": "Telegram_Notification_Tests",
        "phase": "3.3 - Telegram Integration",
        "deliverables": [
            "Create file: `wingman/tests/test_telegram_validation.py`",
            "Test 1: Notification includes validation scores",
            "Test 2: AUTO_APPROVE indicator shown correctly",
            "Test 3: Risk level emoji correct (LOW/MEDIUM/HIGH)",
            "Test results file: `ai-workers/results/worker-102-results.json`"
        ],
        "success_criteria": [
            "3/3 tests pass",
            "`pytest wingman/tests/test_telegram_validation.py` returns 0 exit code",
        ],
        "test_commands": [
            "cd wingman && pytest tests/test_telegram_validation.py -v --tb=short",
        ],
        "dependencies": [
            "WORKER_101 complete (auto indicators)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": []
    },
})

def generate_worker_file(worker_id, spec):
    """Generate a single worker instruction file."""

    # Format worker ID with leading zeros
    worker_num = int(worker_id)

    # Build test commands section
    test_commands_section = "\n".join([f"{cmd}" for cmd in spec['test_commands']])

    # Build test results format
    test_results_format = {
        "worker_id": worker_id,
        "worker_name": spec['title'],
        "status": "pass|fail",
        "deliverables_created": spec['deliverables'][:2],  # First 2 deliverables
        "test_results": {
            f"test_{i+1}": "pass|fail" for i in range(len(spec['test_commands']))
        },
        "duration_seconds": 0,
        "timestamp": "2026-01-13T00:00:00Z",
        "errors": []
    }

    # Generate content
    content = f"""# Worker {worker_id}: {spec['title'].replace('_', ' ')}

**Date:** 2026-01-13
**Environment:** TEST
**Phase:** {spec['phase']}
**Duration:** 20 minutes
**Status:** READY FOR EXECUTION

---

## 1. DELIVERABLES

{chr(10).join(['- [ ] ' + d for d in spec['deliverables']])}

---

## 2. SUCCESS_CRITERIA

{chr(10).join(['- [ ] ' + c for c in spec['success_criteria']])}

---

## 3. BOUNDARIES

- **CAN create:** New files/methods as specified in DELIVERABLES
- **CAN modify:** Existing validation files to add new functionality
- **CANNOT modify:** Core API logic unrelated to validation, database schema (unless explicitly required)
- **CANNOT add:** Features beyond scope of this worker
- **Idempotency:** Check if deliverable exists; if exists, validate and update only if needed

**Scope Limit:** 20-minute execution - focused implementation only

---

## 4. DEPENDENCIES

{chr(10).join(['- ' + d for d in spec['dependencies']])}

---

## 5. MITIGATION

- **If file/method missing:** Create as specified
- **If import fails:** Check Python path, verify dependencies installed
- **If tests fail:** Review error logs, fix implementation, re-run tests
- **Rollback:** Revert changes to modified files using git (if committed)
- **Escalation:** If validators unavailable or LLM service down, escalate to human (critical dependency)
- **Risk Level:** LOW (new feature, no destructive operations)

---

## 6. TEST_PROCESS

```bash
{test_commands_section}
```

---

## 7. TEST_RESULTS_FORMAT

```json
{json.dumps(test_results_format, indent=2)}
```

---

## 8. TASK_CLASSIFICATION

- **Type:** {spec['task_type']}
- **Tool:** Python file editing, API testing
- **Reasoning:** Implementation follows clear specification with defined behavior
- **Local-first:** Yes - file operations, local testing
- **AI Assistance:** Minimal - template-based implementation

---

## 9. RETROSPECTIVE

- **Time estimate:** 20 minutes
- **Actual time:** [To be filled after execution]
- **Challenges:** [To be filled after execution]
- **Lessons learned:** [To be filled after execution]
- **Store in mem0:**
  - Key: "wingman_worker_{worker_id}_retrospective"
  - Namespace: "wingman"
  - Content: Execution time, any issues encountered, test results

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Manual execution time: 30-45 minutes
- Current process: Manual coding + testing

**Targets:**
- Automated execution: <20 minutes (includes testing)
- Accuracy: >95% (clear specification)
- Quality: All tests pass, code follows existing patterns

**Monitoring:**
- Before: Verify dependencies available
- During: Track implementation progress, test execution
- After: Run all test commands, verify all pass
- Degradation limit: If execution takes >40 minutes (2x estimate), abort and escalate

---

**Reference:**
- Implementation Plan: `/Volumes/Data/ai_projects/wingman-system/wingman/docs/VALIDATION_ENHANCEMENT_IMPLEMENTATION_PLAN.md`
- Meta-Worker: `META_WORKER_WINGMAN_03_INSTRUCTION.md`
{f'- Tests Covered: {", ".join(spec["tests_covered"])}' if spec['tests_covered'] else ''}

**Wingman Validation Score:** [To be filled]
**Wingman Status:** PENDING APPROVAL
"""

    return content

def main():
    """Generate all worker files for Phase 3."""
    output_dir = Path("/Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/workers")

    workers_generated = []

    for worker_id, spec in WORKERS_SPEC.items():
        filename = f"WORKER_{worker_id}_{spec['title']}.md"
        filepath = output_dir / filename

        content = generate_worker_file(worker_id, spec)

        with open(filepath, 'w') as f:
            f.write(content)

        workers_generated.append(filename)
        print(f"✅ Generated: {filename}")

    print(f"\n✅ Total workers generated: {len(workers_generated)}")
    print(f"✅ Worker range: WORKER_088-WORKER_{max(WORKERS_SPEC.keys())}")

    return workers_generated

if __name__ == "__main__":
    main()
