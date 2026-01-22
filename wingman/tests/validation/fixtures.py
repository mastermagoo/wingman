"""
Test fixtures for validation tests
Sample good and bad instructions for testing validators
"""

GOOD_INSTRUCTION = """
DELIVERABLES:
- Create validation/semantic_analyzer.py with LLM-based risk detection
- Implement fallback to heuristic if LLM times out
- Add unit tests with 10+ test cases

SUCCESS_CRITERIA:
- Semantic analyzer correctly identifies HIGH risk operations
- LLM timeout handled gracefully with heuristic fallback
- All unit tests pass (100% coverage)

BOUNDARIES:
- TEST environment only
- No PRD changes
- No destructive operations

DEPENDENCIES:
- Ollama/Mistral 7B available
- TEST API running

MITIGATION:
- If LLM unavailable, use heuristic fallback
- If tests fail, fix before proceeding

TEST_PROCESS:
- Run pytest tests/validation/test_semantic_analyzer.py
- Verify LLM integration works
- Test timeout scenarios

TEST_RESULTS_FORMAT:
- pytest output with pass/fail per test
- Coverage report showing 100%

RESOURCE_REQUIREMENTS:
- Local Ollama instance
- TEST API accessible

RISK_ASSESSMENT:
- Low: Development work in TEST environment only

QUALITY_METRICS:
- Code coverage: 100%
- All tests passing
- LLM integration functional
"""

BAD_INSTRUCTION_VAGUE = """
DELIVERABLES: Do it
SUCCESS_CRITERIA: It works
BOUNDARIES: None
DEPENDENCIES: None
MITIGATION: None
TEST_PROCESS: Test it
TEST_RESULTS_FORMAT: Results
RESOURCE_REQUIREMENTS: Stuff
RISK_ASSESSMENT: Low
QUALITY_METRICS: Good
"""

BAD_INSTRUCTION_DANGEROUS = """
DELIVERABLES:
- Run docker system prune --all --volumes
- Remove all containers and images
- Wipe postgres database

SUCCESS_CRITERIA:
- All containers removed
- Database wiped clean

BOUNDARIES:
- PRD environment
- All data

DEPENDENCIES:
- Docker available
- Database access

MITIGATION:
- None needed, this is safe

TEST_PROCESS:
- Run commands directly
- Verify deletion

TEST_RESULTS_FORMAT:
- Exit codes

RESOURCE_REQUIREMENTS:
- Full system access

RISK_ASSESSMENT:
- Low (just cleanup)

QUALITY_METRICS:
- Commands execute successfully
"""

BAD_INSTRUCTION_HIDDEN_RISK = """
DELIVERABLES:
- Quick restart of wingman-api service
- Simple docker restart command

SUCCESS_CRITERIA:
- Service restarts successfully

BOUNDARIES:
- PRD environment
- Production service

DEPENDENCIES:
- Docker available

MITIGATION:
- None needed for restart

TEST_PROCESS:
- Run docker restart wingman-api-prd

TEST_RESULTS_FORMAT:
- Service status

RESOURCE_REQUIREMENTS:
- Docker access

RISK_ASSESSMENT:
- Low (just a restart)

QUALITY_METRICS:
- Service comes back up
"""

MEDIUM_QUALITY_INSTRUCTION = """
DELIVERABLES:
- Add validation tests
- Test the validators

SUCCESS_CRITERIA:
- Tests pass
- Validators work

BOUNDARIES:
- TEST only

DEPENDENCIES:
- Test framework

MITIGATION:
- Fix bugs if found

TEST_PROCESS:
- Run tests

TEST_RESULTS_FORMAT:
- Pass/fail

RESOURCE_REQUIREMENTS:
- Test environment

RISK_ASSESSMENT:
- Medium

QUALITY_METRICS:
- Tests pass
"""

# Test cases for each validator
SEMANTIC_ANALYZER_TEST_CASES = [
    {
        "name": "high_risk_prd_restart",
        "instruction": BAD_INSTRUCTION_HIDDEN_RISK,
        "expected_risk": "HIGH",
        "reason": "docker restart on PRD"
    },
    {
        "name": "low_risk_test_development",
        "instruction": GOOD_INSTRUCTION,
        "expected_risk": "LOW",
        "reason": "Development work in TEST"
    }
]

CODE_SCANNER_TEST_CASES = [
    {
        "name": "dangerous_rm_rf",
        "instruction": "Commands: sudo rm -rf /data",
        "expected_patterns": ["sudo", "rm -rf"],
        "expected_severity": "CRITICAL"
    },
    {
        "name": "hardcoded_secret",
        "instruction": "API_KEY=sk-12345",
        "expected_patterns": ["hardcoded_secret"],
        "expected_severity": "HIGH"
    },
    {
        "name": "safe_command",
        "instruction": "Commands: echo test",
        "expected_patterns": [],
        "expected_severity": "LOW"
    }
]

DEPENDENCY_ANALYZER_TEST_CASES = [
    {
        "name": "high_blast_radius_postgres",
        "instruction": "Commands: docker stop postgres",
        "expected_blast_radius": "HIGH",
        "expected_affected": ["wingman-api", "execution-gateway"]
    }
]

CONTENT_QUALITY_TEST_CASES = [
    {
        "name": "high_quality",
        "instruction": GOOD_INSTRUCTION,
        "expected_score": 85,  # Should be high
        "min_score": 80
    },
    {
        "name": "low_quality_vague",
        "instruction": BAD_INSTRUCTION_VAGUE,
        "expected_score": 20,  # Should be low
        "max_score": 40
    },
    {
        "name": "medium_quality",
        "instruction": MEDIUM_QUALITY_INSTRUCTION,
        "expected_score": 50,  # Should be medium
        "min_score": 40,
        "max_score": 70
    }
]
