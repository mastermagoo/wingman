#!/usr/bin/env python3
"""
Worker Generator for Phase 4-6 (WORKER_103-225)
Generates 123 workers for Testing, Deployment, and Tuning

Phase 4: 108 workers (WORKER_103-210) - ALL 323 tests
Phase 5: 9 workers (WORKER_211-219) - Deployment
Phase 6: 6 workers (WORKER_220-225) - Tuning
"""

import os
import json
from datetime import datetime
from pathlib import Path

def create_test_worker(worker_id, title, phase, test_numbers, test_descriptions, test_category="Integration"):
    """Create a testing worker specification."""
    return {
        "title": title,
        "phase": phase,
        "deliverables": [
            f"Create test file: `wingman/tests/test_{test_category.lower()}_{worker_id}.py`",
            f"Implement {len(test_numbers)} tests: Tests {test_numbers[0]}-{test_numbers[-1]}",
        ] + [f"Test {num}: {desc}" for num, desc in zip(test_numbers, test_descriptions)],
        "success_criteria": [
            f"{len(test_numbers)}/{len(test_numbers)} tests pass",
            "`pytest` returns 0 exit code",
            "All test cases cover specified scenarios",
            "Tests are repeatable and deterministic",
        ],
        "test_commands": [
            f"cd wingman && pytest tests/test_{test_category.lower()}_{worker_id}.py -v --tb=short",
            f"cd wingman && pytest tests/test_{test_category.lower()}_{worker_id}.py --cov --cov-report=term-missing",
        ],
        "dependencies": [
            "Phase 1-2 complete (all 4 validators available)",
            "Phase 3 complete (CompositeValidator, API integration)",
            "TEST environment running (docker compose up)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": test_numbers,
    }

# Phase 4: Integration Tests (WORKER_103-109, 7 workers, 38 tests: 124-161)
phase4_integration = {}
for i, (worker_id, spec_data) in enumerate([
    ("103", {
        "title": "Validator_Interaction_Tests",
        "test_nums": list(range(124, 130)),
        "test_descs": [
            "Semantic→Code validator interaction",
            "Code→Dependency validator interaction",
            "All 4 validators work together",
            "Score conflicts between validators",
            "Error propagation across validators",
            "Timeout handling in validator chain",
        ]
    }),
    ("104", {
        "title": "Composite_Validator_Tests",
        "test_nums": list(range(130, 136)),
        "test_descs": [
            "All validators pass scenario",
            "One validator fails scenario",
            "Mixed results scenario",
            "Score weighting calculation",
            "Final recommendation logic",
            "Edge cases in score combination",
        ]
    }),
    ("105", {
        "title": "API_Integration_Tests",
        "test_nums": list(range(136, 142)),
        "test_descs": [
            "POST /approvals/validate endpoint",
            "Validation in request flow",
            "Validation in response",
            "Error handling",
            "Rate limiting",
            "Concurrent requests",
        ]
    }),
    ("106", {
        "title": "Auto_Approve_Logic_Tests",
        "test_nums": list(range(142, 149)),
        "test_descs": [
            "LOW risk + quality 95 → AUTO_APPROVE",
            "MEDIUM risk + quality 95 → MANUAL (no auto)",
            "LOW + quality 85 → MANUAL (no auto)",
            "Quality 100 → AUTO_APPROVE",
            "Edge case: quality 89.9",
            "Edge case: quality 90.0",
            "Edge case: quality 90.1",
        ]
    }),
    ("107", {
        "title": "Auto_Reject_Logic_Tests",
        "test_nums": list(range(149, 155)),
        "test_descs": [
            "Quality 50 → AUTO_REJECT",
            "Quality 59 → AUTO_REJECT",
            "Quality 60 → MANUAL (no reject)",
            "CRITICAL risk → AUTO_REJECT",
            "HIGH risk + quality 80 → MANUAL (no reject)",
            "Edge cases at threshold boundaries",
        ]
    }),
    ("108", {
        "title": "Integration_Edge_Cases",
        "test_nums": list(range(155, 159)),
        "test_descs": [
            "All validators unavailable",
            "Partial validator failure",
            "LLM timeout chain",
            "Database connection loss",
        ]
    }),
    ("109", {
        "title": "Performance_Integration_Tests",
        "test_nums": list(range(159, 162)),
        "test_descs": [
            "End-to-end latency <5s",
            "Concurrent validation (10 requests)",
            "Throughput test (100 requests/min)",
        ]
    }),
]):
    phase4_integration[spec_data["test_nums"][0]] = create_test_worker(
        worker_id,
        spec_data["title"],
        f"4.1 - Integration Tests Part {i+1}",
        spec_data["test_nums"],
        spec_data["test_descs"],
        "integration"
    )

# Phase 4: Edge Case Tests (WORKER_110-131, 22 workers, 44 tests: 162-205)
phase4_edge = {}
edge_case_workers = [
    ("110", list(range(162, 164)), ["Empty/null inputs", "Null instruction field"]),
    ("111", list(range(164, 166)), ["Extremely long input (10K chars)", "Extremely long input (100K chars)"]),
    ("112", list(range(166, 168)), ["Special characters (Unicode)", "Emojis and SQL injection attempts"]),
    ("113", list(range(168, 170)), ["Malformed JSON in instruction", "Invalid JSON structure"]),
    ("114", list(range(170, 172)), ["Boundary value: score 0", "Boundary value: score 100"]),
    ("115", list(range(172, 174)), ["Missing DELIVERABLES section", "Missing SUCCESS_CRITERIA section"]),
    ("116", list(range(174, 176)), ["Incomplete instruction (half-written)", "Truncated instruction"]),
    ("117", list(range(176, 178)), ["Contradictory requirements", "Conflicting constraints"]),
    ("118", list(range(178, 180)), ["Circular dependency A→B→A", "Circular dependency chain"]),
    ("119", list(range(180, 182)), ["Invalid service reference", "Non-existent service dependency"]),
    ("120", list(range(182, 184)), ["Network timeout to LLM", "Network timeout to database"]),
    ("121", list(range(184, 186)), ["LLM service down", "LLM returns invalid response"]),
    ("122", list(range(186, 188)), ["Database connection error", "Database query timeout"]),
    ("123", list(range(188, 190)), ["Memory exhaustion scenario", "OOM during validation"]),
    ("124", list(range(190, 192)), ["Disk full error", "No space left on device"]),
    ("125", list(range(192, 194)), ["Permission denied (file)", "Permission denied (directory)"]),
    ("126", list(range(194, 196)), ["Rate limit exceeded (LLM)", "Rate limit exceeded (API)"]),
    ("127", list(range(196, 198)), ["Concurrent modification conflict", "Race condition in update"]),
    ("128", list(range(198, 200)), ["Race condition in status update", "Race condition in score calculation"]),
    ("129", list(range(200, 202)), ["Deadlock scenario (2 approvals)", "Deadlock scenario (validator lock)"]),
    ("130", list(range(202, 204)), ["Cache inconsistency", "Stale cache data"]),
    ("131", list(range(204, 206)), ["JWT token expiration", "Capability token expiration"]),
]

for worker_id, test_nums, test_descs in edge_case_workers:
    phase4_edge[test_nums[0]] = create_test_worker(
        worker_id,
        f"Edge_Case_Tests_{worker_id}",
        f"4.2 - Edge Case Tests",
        test_nums,
        test_descs,
        "edge_cases"
    )

# Phase 4: Security Tests (WORKER_132-138, 7 workers, 15 tests: 206-220)
phase4_security = {}
security_workers = [
    ("132", list(range(206, 208)), ["Command injection detection", "Shell command injection"]),
    ("133", list(range(208, 210)), ["SQL injection in DELIVERABLES", "SQL injection in task name"]),
    ("134", list(range(210, 212)), ["Path traversal attack", "Directory traversal attempt"]),
    ("135", list(range(212, 214)), ["Secret leakage detection", "API key in instruction"]),
    ("136", list(range(214, 216)), ["Privilege escalation attempt", "Sudo command detection"]),
    ("137", list(range(216, 219)), ["Docker socket access validation", "Container escape attempt", "Host access attempt"]),
    ("138", list(range(219, 221)), ["Sensitive data exposure", "PII in logs"]),
]

for worker_id, test_nums, test_descs in security_workers:
    phase4_security[test_nums[0]] = create_test_worker(
        worker_id,
        f"Security_Tests_{worker_id}",
        f"4.3 - Security Tests",
        test_nums,
        test_descs,
        "security"
    )

# Phase 4: Concurrency Tests (WORKER_139-147, 9 workers, 18 tests: 221-238)
phase4_concurrency = {}
concurrency_workers = [
    ("139", list(range(221, 223)), ["Parallel validator execution", "Validators run concurrently"]),
    ("140", list(range(223, 225)), ["100 concurrent approval requests", "Concurrent requests with same instruction"]),
    ("141", list(range(225, 227)), ["Thread safety in score calculation", "Thread safety in database updates"]),
    ("142", list(range(227, 229)), ["Database connection pooling", "Connection pool exhaustion"]),
    ("143", list(range(229, 231)), ["Lock contention on approval record", "Lock contention on validator state"]),
    ("144", list(range(231, 233)), ["Message queue ordering", "Queue message priority"]),
    ("145", list(range(233, 235)), ["Transaction isolation READ_COMMITTED", "Transaction isolation SERIALIZABLE"]),
    ("146", list(range(235, 237)), ["Cache coherency across instances", "Cache invalidation"]),
    ("147", list(range(237, 239)), ["Resource cleanup after validation", "Connection cleanup after error"]),
]

for worker_id, test_nums, test_descs in concurrency_workers:
    phase4_concurrency[test_nums[0]] = create_test_worker(
        worker_id,
        f"Concurrency_Tests_{worker_id}",
        f"4.4 - Concurrency Tests",
        test_nums,
        test_descs,
        "concurrency"
    )

# Phase 4: Performance Tests (WORKER_148-152, 5 workers, 5 tests: 239-243)
phase4_performance = {}
performance_workers = [
    ("148", [239], ["Response time benchmark (validation <3s)"]),
    ("149", [240], ["Throughput test (50 validations/min)"]),
    ("150", [241], ["Memory usage (validation <100MB)"]),
    ("151", [242], ["CPU usage (validation <30% CPU)"]),
    ("152", [243], ["Database query count (<20 queries per validation)"]),
]

for worker_id, test_nums, test_descs in performance_workers:
    phase4_performance[test_nums[0]] = create_test_worker(
        worker_id,
        f"Performance_Test_{worker_id}",
        f"4.5 - Performance Tests",
        test_nums,
        test_descs,
        "performance"
    )

# Phase 4: LLM Consistency Tests (WORKER_153-157, 5 workers, 5 tests: 244-248)
phase4_llm = {}
llm_workers = [
    ("153", [244], ["Same instruction 10x (variance <10%)"]),
    ("154", [245], ["Prompt robustness (score consistency)"]),
    ("155", [246], ["Model switching (Ollama vs Claude)"]),
    ("156", [247], ["Temperature sensitivity (temp 0.0 vs 0.7)"]),
    ("157", [248], ["JSON format consistency"]),
]

for worker_id, test_nums, test_descs in llm_workers:
    phase4_llm[test_nums[0]] = create_test_worker(
        worker_id,
        f"LLM_Consistency_Test_{worker_id}",
        f"4.6 - LLM Consistency Tests",
        test_nums,
        test_descs,
        "llm_consistency"
    )

# Phase 4: E2E Approval Flow Tests (WORKER_158-162, 5 workers, 5 tests: 249-253)
phase4_e2e = {}
e2e_workers = [
    ("158", [249], ["Full approval flow (submission → validation → approval → execution)"]),
    ("159", [250], ["Auto-approve flow (LOW risk + quality 95)"]),
    ("160", [251], ["Auto-reject flow (quality 50)"]),
    ("161", [252], ["Manual review flow (MEDIUM risk + quality 75)"]),
    ("162", [253], ["Telegram notification delivery"]),
]

for worker_id, test_nums, test_descs in e2e_workers:
    phase4_e2e[test_nums[0]] = create_test_worker(
        worker_id,
        f"E2E_Flow_Test_{worker_id}",
        f"4.7 - E2E Approval Flow Tests",
        test_nums,
        test_descs,
        "e2e"
    )

# Combine all Phase 4 workers
WORKERS_SPEC = {}
for phase_dict in [phase4_integration, phase4_edge, phase4_security, phase4_concurrency, phase4_performance, phase4_llm, phase4_e2e]:
    for test_num, spec in phase_dict.items():
        # Find corresponding worker ID
        worker_id_num = 103 + len(WORKERS_SPEC)
        worker_id = f"{worker_id_num:03d}"
        WORKERS_SPEC[worker_id] = spec

# Phase 4: False Positive/Negative Analysis (WORKER_163-176, 14 workers)
false_positive_workers = [
    ("163", "Create_Validation_Dataset_Good_Instructions", "Create 20 good instruction examples", ["20 high-quality instructions with complete 10-point framework"]),
    ("164", "Create_Validation_Dataset_Bad_Instructions", "Create 20 bad instruction examples", ["20 low-quality instructions with incomplete/vague sections"]),
    ("165", "Create_Validation_Dataset_Edge_Instructions", "Create 20 edge case instructions", ["20 edge case instructions (boundary conditions, unusual scenarios)"]),
    ("166", "Validation_Dataset_Organization", "Organize dataset into test fixtures", ["Store all 60 instructions in fixtures/ directory", "Add metadata (expected scores, risk levels)"]),
    ("167", "Run_Validation_On_Good_Dataset", "Run validation on 20 good instructions", ["Collect validation results for all 20 good instructions"]),
    ("168", "Run_Validation_On_Bad_Dataset", "Run validation on 20 bad instructions", ["Collect validation results for all 20 bad instructions"]),
    ("169", "Run_Validation_On_Edge_Dataset", "Run validation on 20 edge instructions", ["Collect validation results for all 20 edge instructions"]),
    ("170", "Analyze_Validation_Results", "Analyze all validation results", ["Calculate accuracy, precision, recall", "Identify false positives and false negatives"]),
    ("171", "Identify_False_Positive_Patterns", "Analyze false positives", ["Find common patterns in false positives", "Document why good instructions were rejected"]),
    ("172", "Tune_Thresholds_For_False_Positives", "Tune rejection thresholds", ["Adjust auto-reject threshold to reduce false positives", "Test new thresholds on dataset"]),
    ("173", "Enhance_Prompts_For_False_Positives", "Refine LLM prompts", ["Update prompts to reduce false positive rate", "Re-run validation with new prompts"]),
    ("174", "Identify_False_Negative_Patterns", "Analyze false negatives", ["Find common patterns in false negatives", "Document why bad instructions were approved"]),
    ("175", "Enhance_Detection_Patterns", "Add missing detection patterns", ["Add new dangerous patterns to code scanner", "Add new validation checks"]),
    ("176", "Validate_Improvements", "Re-run full dataset validation", ["Verify false positive rate <10%", "Verify false negative rate <5%"]),
]

for worker_id, title, deliverable, success_criteria in false_positive_workers:
    WORKERS_SPEC[worker_id] = {
        "title": title,
        "phase": "4.8 - False Positive/Negative Analysis",
        "deliverables": [
            deliverable,
            "Document findings and changes",
            "Test results file: `ai-workers/results/worker-{}-results.json`".format(worker_id),
        ],
        "success_criteria": success_criteria + [
            "Documentation complete",
            "Changes tested and validated",
        ],
        "test_commands": [
            "cd wingman && pytest tests/test_false_positive_analysis.py -v",
        ],
        "dependencies": [
            "Phase 4.1-4.7 complete (all validation tests pass)",
        ],
        "task_type": "HYBRID",
        "tests_covered": [],
    }

# Phase 4: Regression Testing (WORKER_177-186, 10 workers)
regression_workers = [
    ("177", "Create_Regression_Baseline_Part1", "Capture baseline for instructions 1-10", ["Run validation on 10 instructions", "Store results as baseline"]),
    ("178", "Create_Regression_Baseline_Part2", "Capture baseline for instructions 11-20", ["Run validation on 10 instructions", "Store results as baseline"]),
    ("179", "Create_Regression_Baseline_Part3", "Capture baseline for instructions 21-30", ["Run validation on 10 instructions", "Store results as baseline"]),
    ("180", "Create_Regression_Baseline_Part4", "Capture baseline for instructions 31-40", ["Run validation on 10 instructions", "Store results as baseline"]),
    ("181", "Create_Regression_Baseline_Part5", "Capture baseline for instructions 41-50", ["Run validation on 10 instructions", "Store results as baseline"]),
    ("182", "Run_Regression_Suite_Semantic", "Regression test after semantic validator change", ["Run full baseline suite", "Compare results to baseline", "Report any regressions"]),
    ("183", "Run_Regression_Suite_Code", "Regression test after code scanner change", ["Run full baseline suite", "Compare results to baseline", "Report any regressions"]),
    ("184", "Run_Regression_Suite_Dependency", "Regression test after dependency analyzer change", ["Run full baseline suite", "Compare results to baseline", "Report any regressions"]),
    ("185", "Run_Regression_Suite_Content", "Regression test after content quality validator change", ["Run full baseline suite", "Compare results to baseline", "Report any regressions"]),
    ("186", "Regression_Report_Generation", "Generate regression test report", ["Summary of all regression tests", "Identify any breaking changes", "Recommendations for fixes"]),
]

for worker_id, title, deliverable, success_criteria in regression_workers:
    WORKERS_SPEC[worker_id] = {
        "title": title,
        "phase": "4.9 - Regression Testing",
        "deliverables": [
            deliverable,
            "Store baseline/results in fixtures/regression/",
            "Test results file: `ai-workers/results/worker-{}-results.json`".format(worker_id),
        ],
        "success_criteria": success_criteria + [
            "Baseline captured or regression tests pass",
            "No unexpected regressions detected",
        ],
        "test_commands": [
            "cd wingman && pytest tests/test_regression.py -v",
        ],
        "dependencies": [
            "Phase 4.8 complete (false positive/negative analysis done)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": [],
    }

# Phase 4: Extended Test Coverage (WORKER_187-210, 24 workers, 70 tests: 254-323)
extended_workers = [
    # Semantic analyzer extended tests (9 workers, 27 tests: 254-280)
    ("187", "Semantic_Extended_Tests_Part1", "Tests 254-256", ["Complex nested instructions", "Multi-step dependencies", "Conditional logic"]),
    ("188", "Semantic_Extended_Tests_Part2", "Tests 257-259", ["Ambiguous language", "Technical jargon", "Domain-specific terms"]),
    ("189", "Semantic_Extended_Tests_Part3", "Tests 260-262", ["Risk level edge cases", "Hidden destructive operations", "Benign-looking dangerous commands"]),
    ("190", "Semantic_Extended_Tests_Part4", "Tests 263-265", ["Large instruction (5K+ words)", "Complex multi-service orchestration", "Cross-environment operations"]),
    ("191", "Semantic_Extended_Tests_Part5", "Tests 266-268", ["Non-English text", "Mixed language", "Translation artifacts"]),
    ("192", "Semantic_Extended_Tests_Part6", "Tests 269-271", ["Code blocks in instruction", "Inline scripts", "Configuration snippets"]),
    ("193", "Semantic_Extended_Tests_Part7", "Tests 272-274", ["Time-sensitive operations", "Scheduled tasks", "Cron expressions"]),
    ("194", "Semantic_Extended_Tests_Part8", "Tests 275-277", ["Rollback scenarios", "Failure recovery", "Disaster recovery"]),
    ("195", "Semantic_Extended_Tests_Part9", "Tests 278-280", ["Performance optimization tasks", "Resource tuning", "Scaling operations"]),

    # Code scanner extended tests (7 workers, 20 tests: 281-300)
    ("196", "Code_Scanner_Extended_Tests_Part1", "Tests 281-283", ["Obfuscated commands", "Base64 encoded strings", "Hex encoded data"]),
    ("197", "Code_Scanner_Extended_Tests_Part2", "Tests 284-286", ["Environment variable injection", "Indirect command execution", "Eval/exec patterns"]),
    ("198", "Code_Scanner_Extended_Tests_Part3", "Tests 287-289", ["Docker-in-Docker patterns", "Privileged container operations", "Host network access"]),
    ("199", "Code_Scanner_Extended_Tests_Part4", "Tests 290-292", ["Git history manipulation", "Force push detection", "Branch deletion"]),
    ("200", "Code_Scanner_Extended_Tests_Part5", "Tests 293-295", ["Package manager operations", "Dependency installation", "Unverified sources"]),
    ("201", "Code_Scanner_Extended_Tests_Part6", "Tests 296-298", ["File permission changes", "Ownership changes", "ACL modifications"]),
    ("202", "Code_Scanner_Extended_Tests_Part7", "Tests 299-300", ["Network operations", "Port forwarding"]),

    # Dependency analyzer extended tests (5 workers, 15 tests: 301-315)
    ("203", "Dependency_Extended_Tests_Part1", "Tests 301-303", ["Complex dependency graphs", "Circular dependencies", "Diamond dependencies"]),
    ("204", "Dependency_Extended_Tests_Part2", "Tests 304-306", ["Service mesh dependencies", "Sidecar container dependencies", "Init container dependencies"]),
    ("205", "Dependency_Extended_Tests_Part3", "Tests 307-309", ["External service dependencies", "Third-party API dependencies", "Cloud service dependencies"]),
    ("206", "Dependency_Extended_Tests_Part4", "Tests 310-312", ["Data dependencies", "Database schema dependencies", "Cache dependencies"]),
    ("207", "Dependency_Extended_Tests_Part5", "Tests 313-315", ["Time-based dependencies", "Scheduled job dependencies", "Event-driven dependencies"]),

    # Content quality extended tests (3 workers, 8 tests: 316-323)
    ("208", "Content_Quality_Extended_Tests_Part1", "Tests 316-318", ["Incomplete mitigation plans", "Vague success criteria", "Unclear deliverables"]),
    ("209", "Content_Quality_Extended_Tests_Part2", "Tests 319-321", ["Missing context", "Insufficient detail", "Ambiguous requirements"]),
    ("210", "Content_Quality_Extended_Tests_Part3", "Tests 322-323", ["Inconsistent terminology", "Contradictory statements"]),
]

for worker_id, title, test_range, test_descs in extended_workers:
    test_nums = [int(test_range.split()[1].split("-")[0]) + i for i in range(len(test_descs))]
    WORKERS_SPEC[worker_id] = create_test_worker(
        worker_id,
        title,
        f"4.10 - Extended Test Coverage",
        test_nums,
        test_descs,
        "extended"
    )

# Phase 5: Deployment (WORKER_211-219, 9 workers)
phase5_workers = {
    "211": {
        "title": "Feature_Flag_Setup",
        "phase": "5.1 - Deployment Preparation",
        "deliverables": [
            "Add VALIDATION_ENABLED feature flag to .env.test and .env.prd",
            "Implement feature flag check in api_server.py",
            "Default: VALIDATION_ENABLED=false (disabled until ready)",
            "Add /admin/feature-flags endpoint to toggle flags",
            "Test results file: `ai-workers/results/worker-211-results.json`"
        ],
        "success_criteria": [
            "Feature flag present in environment files",
            "API respects feature flag setting",
            "Can enable/disable validation without code changes",
            "Admin endpoint works (requires auth)",
        ],
        "test_commands": [
            "grep VALIDATION_ENABLED wingman/.env.test",
            "curl http://localhost:8001/admin/feature-flags",
        ],
        "dependencies": [
            "Phase 4 complete (all tests pass)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": [],
    },
    "212": {
        "title": "Deploy_Validators_To_TEST",
        "phase": "5.2 - TEST Deployment",
        "deliverables": [
            "Deploy all 4 validators to TEST environment",
            "Update docker-compose.yml with validator services",
            "Restart TEST stack with new validators",
            "Verify all services healthy",
            "Test results file: `ai-workers/results/worker-212-results.json`"
        ],
        "success_criteria": [
            "All validator services running in TEST",
            "API can reach all validators",
            "Health checks pass for all services",
            "No errors in logs",
        ],
        "test_commands": [
            "docker compose -f wingman/docker-compose.yml -p wingman-test ps",
            "curl http://localhost:8001/health | jq '.validators'",
        ],
        "dependencies": [
            "WORKER_211 complete (feature flag setup)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": [],
    },
    "213": {
        "title": "Smoke_Test_In_TEST",
        "phase": "5.2 - TEST Deployment",
        "deliverables": [
            "Enable VALIDATION_ENABLED=true in TEST",
            "Submit 20 approval requests (mix of good/bad/edge)",
            "Verify validation runs for each request",
            "Check auto-approve and auto-reject work",
            "Test results file: `ai-workers/results/worker-213-results.json`"
        ],
        "success_criteria": [
            "20/20 requests validated successfully",
            "Auto-approve works (at least 1 case)",
            "Auto-reject works (at least 1 case)",
            "Manual review works (at least 5 cases)",
            "No crashes or errors",
        ],
        "test_commands": [
            "# Submit 20 test requests and verify validation",
            "cd wingman && python3 tests/smoke_test_validation.py",
        ],
        "dependencies": [
            "WORKER_212 complete (validators deployed to TEST)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": [],
    },
    "214": {
        "title": "TEST_Deployment_Verification",
        "phase": "5.2 - TEST Deployment",
        "deliverables": [
            "Run full health check suite",
            "Check all logs for errors",
            "Verify database has validation results",
            "Verify Telegram notifications include validation scores",
            "Test results file: `ai-workers/results/worker-214-results.json`"
        ],
        "success_criteria": [
            "All health checks pass",
            "No errors in last 100 log lines",
            "Database has validation_results column populated",
            "Telegram shows validation scores",
        ],
        "test_commands": [
            "curl http://localhost:8001/health",
            "docker compose -f wingman/docker-compose.yml -p wingman-test logs --tail=100 api-server | grep -i error",
            "docker compose -f wingman/docker-compose.yml -p wingman-test exec -T postgres psql -U wingman -d wingman_db -c 'SELECT COUNT(*) FROM approvals WHERE validation_results IS NOT NULL;'",
        ],
        "dependencies": [
            "WORKER_213 complete (smoke test pass)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": [],
    },
    "215": {
        "title": "PRD_Pre_Deployment_Checklist",
        "phase": "5.3 - PRD Deployment",
        "deliverables": [
            "Create database backup (PRD)",
            "Document rollback plan",
            "Verify docker images built and tagged",
            "Create deployment runbook",
            "Test results file: `ai-workers/results/worker-215-results.json`"
        ],
        "success_criteria": [
            "Database backup created and verified",
            "Rollback plan documented (step-by-step)",
            "Docker images available",
            "Runbook complete and reviewed",
        ],
        "test_commands": [
            "ls -lh wingman/backups/wingman_db_*.sql",
            "docker images | grep wingman-api",
        ],
        "dependencies": [
            "WORKER_214 complete (TEST verified)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": [],
    },
    "216": {
        "title": "Deploy_To_PRD_With_Flag_OFF",
        "phase": "5.3 - PRD Deployment",
        "deliverables": [
            "Deploy new code to PRD with VALIDATION_ENABLED=false",
            "Restart PRD stack",
            "Verify all services healthy",
            "Verify existing approvals still work (no regression)",
            "Test results file: `ai-workers/results/worker-216-results.json`"
        ],
        "success_criteria": [
            "PRD deployment successful",
            "All services healthy",
            "Existing approval flow works (validation disabled)",
            "No errors in logs",
        ],
        "test_commands": [
            "docker compose -f wingman/docker-compose.prd.yml -p wingman-prd --env-file wingman/.env.prd ps",
            "curl http://localhost:8002/health",
        ],
        "dependencies": [
            "WORKER_215 complete (pre-deployment checklist)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": [],
    },
    "217": {
        "title": "Gradual_Rollout_10_Percent",
        "phase": "5.3 - PRD Deployment",
        "deliverables": [
            "Enable validation for 10% of requests (sampling)",
            "Monitor for 2 hours",
            "Check error rate, response time, false positive rate",
            "Verify no production issues",
            "Test results file: `ai-workers/results/worker-217-results.json`"
        ],
        "success_criteria": [
            "10% sampling active",
            "Error rate <1%",
            "Response time <5s (p95)",
            "No production incidents",
        ],
        "test_commands": [
            "# Monitor PRD logs and metrics for 2 hours",
            "docker compose -f wingman/docker-compose.prd.yml -p wingman-prd logs --tail=100 api-server",
        ],
        "dependencies": [
            "WORKER_216 complete (PRD deployed with flag OFF)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": [],
    },
    "218": {
        "title": "Gradual_Rollout_50_Percent",
        "phase": "5.3 - PRD Deployment",
        "deliverables": [
            "Enable validation for 50% of requests",
            "Monitor for 4 hours",
            "Check error rate, response time, false positive rate",
            "Review Telegram notifications for quality",
            "Test results file: `ai-workers/results/worker-218-results.json`"
        ],
        "success_criteria": [
            "50% sampling active",
            "Error rate <1%",
            "Response time <5s (p95)",
            "False positive rate <15% (acceptable at this stage)",
            "No production incidents",
        ],
        "test_commands": [
            "# Monitor PRD logs and metrics for 4 hours",
            "docker compose -f wingman/docker-compose.prd.yml -p wingman-prd logs --tail=100 api-server",
        ],
        "dependencies": [
            "WORKER_217 complete (10% rollout successful)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": [],
    },
    "219": {
        "title": "Gradual_Rollout_100_Percent",
        "phase": "5.3 - PRD Deployment",
        "deliverables": [
            "Enable validation for 100% of requests (VALIDATION_ENABLED=true)",
            "Monitor for 24 hours",
            "Final health check and verification",
            "Document deployment completion",
            "Test results file: `ai-workers/results/worker-219-results.json`"
        ],
        "success_criteria": [
            "100% validation active",
            "Error rate <1%",
            "Response time <5s (p95)",
            "No production incidents in 24 hours",
            "Deployment marked complete",
        ],
        "test_commands": [
            "grep VALIDATION_ENABLED=true wingman/.env.prd",
            "curl http://localhost:8002/health | jq '.validators'",
        ],
        "dependencies": [
            "WORKER_218 complete (50% rollout successful)",
        ],
        "task_type": "MECHANICAL",
        "tests_covered": [],
    },
}

WORKERS_SPEC.update(phase5_workers)

# Phase 6: Tuning (WORKER_220-225, 6 workers)
phase6_workers = {
    "220": {
        "title": "Tune_Auto_Reject_Threshold",
        "phase": "6.1 - Threshold Tuning",
        "deliverables": [
            "Test auto-reject thresholds: 50, 55, 60, 65, 70",
            "Analyze false positive rate for each threshold",
            "Select optimal threshold (target: false positive <10%)",
            "Update threshold in code",
            "Test results file: `ai-workers/results/worker-220-results.json`"
        ],
        "success_criteria": [
            "All 5 thresholds tested on validation dataset",
            "False positive rate calculated for each",
            "Optimal threshold selected and documented",
            "Code updated with new threshold",
        ],
        "test_commands": [
            "cd wingman && python3 tests/tune_reject_threshold.py",
        ],
        "dependencies": [
            "Phase 5 complete (deployed to PRD)",
            "Validation dataset available (Phase 4.8)",
        ],
        "task_type": "HYBRID",
        "tests_covered": [],
    },
    "221": {
        "title": "Tune_Auto_Approve_Threshold",
        "phase": "6.1 - Threshold Tuning",
        "deliverables": [
            "Test auto-approve thresholds: 85, 87, 90, 92, 95",
            "Analyze false negative rate for each threshold",
            "Select optimal threshold (target: false negative <5%)",
            "Update threshold in code",
            "Test results file: `ai-workers/results/worker-221-results.json`"
        ],
        "success_criteria": [
            "All 5 thresholds tested on validation dataset",
            "False negative rate calculated for each",
            "Optimal threshold selected and documented",
            "Code updated with new threshold",
        ],
        "test_commands": [
            "cd wingman && python3 tests/tune_approve_threshold.py",
        ],
        "dependencies": [
            "WORKER_220 complete (reject threshold tuned)",
        ],
        "task_type": "HYBRID",
        "tests_covered": [],
    },
    "222": {
        "title": "Tune_Risk_Level_Boundaries",
        "phase": "6.1 - Threshold Tuning",
        "deliverables": [
            "Analyze risk level distribution in production data",
            "Test LOW/MEDIUM/HIGH boundaries",
            "Optimize for accurate risk classification",
            "Update risk level thresholds in semantic analyzer",
            "Test results file: `ai-workers/results/worker-222-results.json`"
        ],
        "success_criteria": [
            "Risk level distribution analyzed (aim for ~40% LOW, ~40% MEDIUM, ~20% HIGH)",
            "Boundaries adjusted to match actual risk patterns",
            "Risk classification accuracy >85%",
            "Code updated with new boundaries",
        ],
        "test_commands": [
            "cd wingman && python3 tests/tune_risk_boundaries.py",
        ],
        "dependencies": [
            "WORKER_221 complete (approve threshold tuned)",
        ],
        "task_type": "HYBRID",
        "tests_covered": [],
    },
    "223": {
        "title": "Refine_Semantic_Analyzer_Prompt",
        "phase": "6.2 - Prompt Tuning",
        "deliverables": [
            "Analyze semantic analyzer false positives from production",
            "Identify prompt improvement opportunities",
            "Test 3-5 prompt variations",
            "Select best prompt based on accuracy",
            "Test results file: `ai-workers/results/worker-223-results.json`"
        ],
        "success_criteria": [
            "At least 3 prompt variations tested",
            "Best prompt improves accuracy by ≥5%",
            "False positive rate reduced",
            "Updated prompt deployed",
        ],
        "test_commands": [
            "cd wingman && python3 tests/tune_semantic_prompt.py",
        ],
        "dependencies": [
            "WORKER_222 complete (risk boundaries tuned)",
            "Production data available (at least 50 approvals)",
        ],
        "task_type": "CREATIVE",
        "tests_covered": [],
    },
    "224": {
        "title": "Refine_Content_Quality_Prompt",
        "phase": "6.2 - Prompt Tuning",
        "deliverables": [
            "Analyze content quality validator inconsistencies",
            "Identify sections with high variance",
            "Test 3-5 prompt variations",
            "Select best prompt based on consistency (variance <10%)",
            "Test results file: `ai-workers/results/worker-224-results.json`"
        ],
        "success_criteria": [
            "At least 3 prompt variations tested",
            "Best prompt reduces variance by ≥20%",
            "Consistency improved (same instruction scored 10x, variance <10%)",
            "Updated prompt deployed",
        ],
        "test_commands": [
            "cd wingman && python3 tests/tune_content_quality_prompt.py",
        ],
        "dependencies": [
            "WORKER_223 complete (semantic prompt tuned)",
        ],
        "task_type": "CREATIVE",
        "tests_covered": [],
    },
    "225": {
        "title": "Final_Tuning_Report",
        "phase": "6.3 - Final Report",
        "deliverables": [
            "Generate comprehensive tuning report",
            "Document all threshold changes",
            "Document all prompt improvements",
            "Measure final metrics: false positive rate, false negative rate, consistency",
            "Create recommendations for ongoing tuning",
            "Test results file: `ai-workers/results/worker-225-results.json`"
        ],
        "success_criteria": [
            "Report includes all tuning activities",
            "Final metrics documented: false positive <10%, false negative <5%, consistency >90%",
            "Recommendations for ongoing monitoring",
            "Report saved to docs/",
        ],
        "test_commands": [
            "cd wingman && python3 tests/generate_tuning_report.py",
            "test -f wingman/docs/VALIDATION_TUNING_REPORT.md",
        ],
        "dependencies": [
            "WORKER_224 complete (content quality prompt tuned)",
        ],
        "task_type": "HYBRID",
        "tests_covered": [],
    },
}

WORKERS_SPEC.update(phase6_workers)

def generate_worker_file(worker_id, spec):
    """Generate a single worker instruction file."""

    # Build test commands section
    test_commands_section = "\n".join(spec['test_commands'])

    # Build test results format
    test_results_format = {
        "worker_id": worker_id,
        "worker_name": spec['title'],
        "status": "pass|fail",
        "deliverables_created": spec['deliverables'][:2],
        "test_results": {
            f"test_{i+1}": "pass|fail" for i in range(min(len(spec['test_commands']), 5))
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
- **Tool:** Python file editing, API testing, pytest
- **Reasoning:** Implementation follows clear specification with defined behavior
- **Local-first:** Yes - file operations, local testing
- **AI Assistance:** Minimal to moderate - template-based implementation

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
{f'- Tests Covered: {", ".join([str(t) for t in spec["tests_covered"]])}' if spec['tests_covered'] else ''}

**Wingman Validation Score:** [To be filled]
**Wingman Status:** PENDING APPROVAL
"""

    return content

def main():
    """Generate all worker files for Phases 4-6."""
    output_dir = Path("/Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/workers")

    workers_generated = []

    for worker_id in sorted(WORKERS_SPEC.keys()):
        spec = WORKERS_SPEC[worker_id]
        filename = f"WORKER_{worker_id}_{spec['title']}.md"
        filepath = output_dir / filename

        content = generate_worker_file(worker_id, spec)

        with open(filepath, 'w') as f:
            f.write(content)

        workers_generated.append(filename)
        print(f"✅ Generated: {filename}")

    print(f"\n✅ Total workers generated: {len(workers_generated)}")
    print(f"✅ Worker range: WORKER_{min(WORKERS_SPEC.keys())}-WORKER_{max(WORKERS_SPEC.keys())}")

    # Print test coverage summary
    total_tests = sum(len(spec['tests_covered']) for spec in WORKERS_SPEC.values() if spec['tests_covered'])
    print(f"✅ Total tests covered: {total_tests}")

    return workers_generated

if __name__ == "__main__":
    main()
