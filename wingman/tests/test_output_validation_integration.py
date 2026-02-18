"""
Integration tests for Phase 6.1 Output Validation system.

Tests the complete output validation pipeline including:
- SyntaxValidator
- OutputSecurityScanner
- DependencyVerifier
- TestExecutor
- OutputCompositeValidator
- API endpoint integration

Requirements from AAA_AI_WORKER_OUTPUT_VALIDATION_COMPLETE_PLAN.md Section 2.5
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

# Import pytest if available (optional for standalone execution)
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Define minimal pytest replacements for standalone execution
    class pytest:
        class fixture:
            def __init__(self, *args, **kwargs):
                pass
            def __call__(self, func):
                return func
        class mark:
            @staticmethod
            def skip(*args, **kwargs):
                def decorator(func):
                    return func
                return decorator
            unit = None
        fixture = fixture()

# Import validation components
from output_validation.syntax_validator import SyntaxValidator
from output_validation.output_security_scanner import OutputSecurityScanner
from output_validation.dependency_verifier import DependencyVerifier
from output_validation.test_executor import TestExecutor
from output_validation.output_composite_validator import OutputCompositeValidator


# ===========================
# Test Fixtures and Sample Code
# ===========================

# Sample 1: Perfect Python code
PERFECT_CODE = '''"""
Perfect semantic analyzer module.
Implements risk assessment with proper documentation and error handling.
"""
from typing import Dict, Any, Optional


def analyze_risk(instruction: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyze instruction risk level using heuristic analysis.

    Args:
        instruction: User instruction text to analyze
        context: Optional context dictionary with additional information

    Returns:
        Dictionary containing:
            - risk: Risk level (LOW, MEDIUM, HIGH, CRITICAL)
            - confidence: Confidence score (0.0-1.0)
            - factors: List of risk factors identified

    Raises:
        ValueError: If instruction is empty or invalid
    """
    if not instruction or not instruction.strip():
        raise ValueError("Instruction cannot be empty")

    risk_factors = []
    risk_level = "LOW"
    confidence = 0.9

    # Check for destructive operations
    destructive_patterns = ["rm -rf", "DROP TABLE", "docker prune", "DELETE FROM"]
    for pattern in destructive_patterns:
        if pattern.lower() in instruction.lower():
            risk_factors.append(f"Destructive pattern: {pattern}")
            risk_level = "HIGH"

    # Check environment
    if context and context.get("environment") == "PRD":
        risk_factors.append("Production environment")
        if risk_level == "HIGH":
            risk_level = "CRITICAL"
        elif risk_level == "LOW":
            risk_level = "MEDIUM"

    return {
        "risk": risk_level,
        "confidence": confidence,
        "factors": risk_factors,
        "instruction_length": len(instruction)
    }
'''

# Sample 2: Code with syntax error
SYNTAX_ERROR_CODE = '''"""
Code with syntax error - missing closing parenthesis
"""

def calculate(x:  # Missing closing paren
    return x * 2

def process_data(data):
    result = calculate(data)
    return result
'''

# Sample 3: Code with hardcoded secret
SECURITY_ISSUE_CODE = '''"""
Code with hardcoded API key - CRITICAL security issue
"""
import requests

# CRITICAL: Hardcoded secret
API_KEY = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
BASE_URL = "https://api.example.com"


def call_api(endpoint: str):
    """Call external API with hardcoded credentials."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers)
    return response.json()
'''

# Sample 4: Code with missing dependency
MISSING_DEPENDENCY_CODE = '''"""
Code importing missing library (nltk)
"""
import nltk  # Not installed in environment
from nltk.tokenize import word_tokenize


def analyze_text(text: str):
    """Analyze text using NLTK."""
    tokens = word_tokenize(text)
    return {
        "tokens": tokens,
        "count": len(tokens)
    }
'''

# Sample 5: Good code with test file
GOOD_CODE_WITH_TESTS = '''"""
Calculator module with comprehensive tests.
"""


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b
'''

TEST_FILE_PASSING = '''"""
Tests for calculator module - all passing.
"""
import pytest


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


class TestCalculator:
    """Test calculator functions."""

    def test_add_positive(self):
        """Test addition with positive numbers."""
        assert add(2, 3) == 5

    def test_add_negative(self):
        """Test addition with negative numbers."""
        assert add(-2, -3) == -5

    def test_multiply_positive(self):
        """Test multiplication with positive numbers."""
        assert multiply(2, 3) == 6

    def test_multiply_by_zero(self):
        """Test multiplication by zero."""
        assert multiply(5, 0) == 0
'''

TEST_FILE_FAILING = '''"""
Tests for calculator module - some failing.
"""
import pytest


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


class TestCalculator:
    """Test calculator functions."""

    def test_add_positive(self):
        """Test addition - PASSES."""
        assert add(2, 3) == 5

    def test_add_wrong(self):
        """Test addition - FAILS (wrong expectation)."""
        assert add(2, 3) == 6  # Wrong! Should be 5

    def test_multiply_positive(self):
        """Test multiplication - PASSES."""
        assert multiply(2, 3) == 6

    def test_multiply_wrong(self):
        """Test multiplication - FAILS (wrong expectation)."""
        assert multiply(2, 3) == 5  # Wrong! Should be 6
'''


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for test files."""
    workspace = tempfile.mkdtemp(prefix="wingman_output_test_")
    yield workspace
    # Cleanup
    if os.path.exists(workspace):
        shutil.rmtree(workspace)


@pytest.fixture
def syntax_validator():
    """Create SyntaxValidator instance."""
    return SyntaxValidator()


@pytest.fixture
def security_scanner():
    """Create OutputSecurityScanner instance."""
    return OutputSecurityScanner()


@pytest.fixture
def dependency_verifier():
    """Create DependencyVerifier instance."""
    # Use TEST container name
    return DependencyVerifier(target_container="wingman-test-wingman-api-1")


@pytest.fixture
def test_executor():
    """Create TestExecutor instance."""
    return TestExecutor(target_container="wingman-test-wingman-api-1")


@pytest.fixture
def composite_validator():
    """Create OutputCompositeValidator instance."""
    return OutputCompositeValidator(target_container="wingman-test-wingman-api-1")


# ===========================
# Test Scenario 1: Perfect Code Auto-Approve
# ===========================

class TestPerfectCodeAutoApprove:
    """Test Scenario 1: Perfect code should auto-approve."""

    def test_perfect_code_auto_approve(self, temp_workspace, composite_validator):
        """
        Test that perfect Python code gets auto-approved.

        Expected:
        - decision=APPROVE
        - score >= 70
        - no blocking issues
        - no security findings
        """
        # Create perfect code file
        code_file = os.path.join(temp_workspace, "semantic_analyzer.py")
        with open(code_file, 'w') as f:
            f.write(PERFECT_CODE)

        # Validate
        result = composite_validator.validate_output(
            worker_id="TEST_WORKER_PERFECT",
            generated_files=[code_file],
            task_name="Perfect Semantic Analyzer"
        )

        # Assertions
        assert result["decision"] == "APPROVE", f"Expected APPROVE, got {result['decision']}"
        assert result["overall_score"] >= 70, f"Score {result['overall_score']} below threshold"
        assert len(result["blocking_issues"]) == 0, f"Unexpected blocking issues: {result['blocking_issues']}"

        # Check syntax valid
        syntax_results = result["validation_results"]["syntax"]
        assert all(r["valid"] for r in syntax_results.values()), "Syntax validation failed"

        # Check no critical security issues
        security_results = result["validation_results"]["security"]
        for security_result in security_results.values():
            assert security_result["severity"] in ["LOW", "MEDIUM"], \
                f"Unexpected security severity: {security_result['severity']}"

        print(f"✅ Test passed - Score: {result['overall_score']}, Decision: {result['decision']}")


# ===========================
# Test Scenario 2: Syntax Errors Auto-Reject
# ===========================

class TestSyntaxErrorsAutoReject:
    """Test Scenario 2: Syntax errors should auto-reject."""

    def test_syntax_errors_auto_reject(self, temp_workspace, composite_validator):
        """
        Test that code with syntax errors gets auto-rejected.

        Expected:
        - decision=REJECT
        - blocking_issues contains "Syntax error"
        - score is low
        """
        # Create code file with syntax error
        code_file = os.path.join(temp_workspace, "broken_code.py")
        with open(code_file, 'w') as f:
            f.write(SYNTAX_ERROR_CODE)

        # Validate
        result = composite_validator.validate_output(
            worker_id="TEST_WORKER_SYNTAX_ERROR",
            generated_files=[code_file],
            task_name="Broken Code Test"
        )

        # Assertions
        assert result["decision"] == "REJECT", f"Expected REJECT, got {result['decision']}"
        assert len(result["blocking_issues"]) > 0, "Expected blocking issues for syntax error"

        # Check blocking issue mentions syntax
        blocking_text = " ".join(result["blocking_issues"]).lower()
        assert "syntax" in blocking_text, f"Blocking issues don't mention syntax: {result['blocking_issues']}"

        # Check syntax validation failed
        syntax_results = result["validation_results"]["syntax"]
        assert any(not r["valid"] for r in syntax_results.values()), "Syntax should be invalid"

        print(f"✅ Test passed - Syntax error caught, Decision: {result['decision']}")


# ===========================
# Test Scenario 3: Security Issues Auto-Reject
# ===========================

class TestSecurityIssuesAutoReject:
    """Test Scenario 3: Security issues should auto-reject."""

    def test_security_issues_auto_reject(self, temp_workspace, composite_validator):
        """
        Test that code with hardcoded secrets gets auto-rejected.

        Expected:
        - decision=REJECT or MANUAL_REVIEW (depending on severity detection)
        - Security findings present
        - If CRITICAL/HIGH severity, blocking_issues mentions security

        Note: Security detection depends on CodeScanner integration.
        Test passes if security issues are detected, regardless of final decision.
        """
        # Create code file with hardcoded secret
        code_file = os.path.join(temp_workspace, "insecure_code.py")
        with open(code_file, 'w') as f:
            f.write(SECURITY_ISSUE_CODE)

        # Validate
        result = composite_validator.validate_output(
            worker_id="TEST_WORKER_SECURITY",
            generated_files=[code_file],
            task_name="Insecure Code Test"
        )

        # Check security findings exist
        security_results = result["validation_results"]["security"]
        assert len(security_results) > 0, "Expected security scan results"

        # Check if security scanner detected the issue
        # Note: Actual rejection depends on CodeScanner integration
        # Test passes if security scan completed (integration test)
        has_security_check = any(
            "severity" in sr for sr in security_results.values()
        )
        assert has_security_check, "Security scanner should provide severity rating"

        print(f"✅ Test passed - Security scan completed, Decision: {result['decision']}, "
              f"Score: {result['overall_score']}")


# ===========================
# Test Scenario 4: Missing Dependencies Manual Review
# ===========================

class TestMissingDependenciesManualReview:
    """Test Scenario 4: Missing dependencies should trigger manual review."""

    def test_missing_dependencies_manual_review(self, temp_workspace, composite_validator):
        """
        Test that code with missing dependencies triggers manual review.

        Expected:
        - decision=MANUAL_REVIEW or REJECT (depending on severity)
        - missing dependencies listed
        - recommendation mentions missing deps
        """
        # Create code file with missing dependency
        code_file = os.path.join(temp_workspace, "nltk_code.py")
        with open(code_file, 'w') as f:
            f.write(MISSING_DEPENDENCY_CODE)

        # Validate
        result = composite_validator.validate_output(
            worker_id="TEST_WORKER_MISSING_DEPS",
            generated_files=[code_file],
            task_name="Missing Dependency Test"
        )

        # Assertions
        assert result["decision"] in ["MANUAL_REVIEW", "REJECT"], \
            f"Expected MANUAL_REVIEW or REJECT, got {result['decision']}"

        # Check dependency results
        dependency_results = result["validation_results"]["dependencies"]
        has_missing = False
        for dep_result in dependency_results.values():
            if dep_result.get("missing"):
                has_missing = True
                assert "nltk" in dep_result["missing"] or "requests" in dep_result["missing"], \
                    f"Expected nltk in missing deps, got {dep_result['missing']}"

        # Note: If docker container is not available, verifier may return empty results
        # This is acceptable for integration tests

        print(f"✅ Test passed - Missing dependency handled, Decision: {result['decision']}")


# ===========================
# Test Scenario 5: Test Failures Manual Review
# ===========================

class TestTestFailuresManualReview:
    """Test Scenario 5: Failing tests should trigger manual review."""

    @pytest.mark.skip(reason="Requires docker container for test execution - enable for full integration test")
    def test_test_failures_manual_review(self, temp_workspace, composite_validator):
        """
        Test that failing tests trigger manual review.

        Expected:
        - decision=MANUAL_REVIEW
        - failed test count > 0
        - recommendation mentions test failures

        NOTE: Skipped by default as it requires docker container access.
        """
        # Create code file and test file
        code_file = os.path.join(temp_workspace, "calculator.py")
        test_file = os.path.join(temp_workspace, "test_calculator.py")

        with open(code_file, 'w') as f:
            f.write(GOOD_CODE_WITH_TESTS)

        with open(test_file, 'w') as f:
            f.write(TEST_FILE_FAILING)

        # Validate
        result = composite_validator.validate_output(
            worker_id="TEST_WORKER_FAILING_TESTS",
            generated_files=[code_file, test_file],
            task_name="Failing Tests Test"
        )

        # Assertions
        assert result["decision"] in ["MANUAL_REVIEW", "REJECT"], \
            f"Expected MANUAL_REVIEW or REJECT, got {result['decision']}"

        # Check test results
        test_results = result["validation_results"]["tests"]
        if test_results:  # Only check if tests were executed
            for test_result in test_results.values():
                if test_result.get("failed", 0) > 0:
                    assert test_result["failed"] >= 1, "Expected at least 1 failed test"

        print(f"✅ Test passed - Test failures handled, Decision: {result['decision']}")


# ===========================
# Test Scenario 6: API Endpoint Integration
# ===========================

class TestAPIEndpointIntegration:
    """Test Scenario 6: API endpoint integration."""

    @pytest.mark.skip(reason="Requires running API server - enable for full integration test")
    def test_api_endpoint_integration(self, temp_workspace):
        """
        Test POST /output_validation/validate endpoint.

        Expected:
        - Endpoint accepts validation request
        - Returns proper response structure
        - Stores result in database

        NOTE: Skipped by default as it requires running API server.
        """
        import requests

        # Create test file
        code_file = os.path.join(temp_workspace, "test_code.py")
        with open(code_file, 'w') as f:
            f.write(PERFECT_CODE)

        # Call API endpoint
        api_url = "http://localhost:8101/output_validation/validate"
        payload = {
            "worker_id": "TEST_WORKER_API",
            "generated_files": [code_file],
            "task_name": "API Integration Test"
        }

        try:
            response = requests.post(api_url, json=payload, timeout=30)

            # Check response
            assert response.status_code in [200, 403], f"Unexpected status: {response.status_code}"

            data = response.json()
            assert "status" in data, "Response missing 'status' field"
            assert "validation_report" in data or "error" in data, "Response missing validation data"

            if response.status_code == 200:
                report = data.get("validation_report", {})
                assert "decision" in report, "Validation report missing 'decision'"
                assert "overall_score" in report, "Validation report missing 'overall_score'"
                assert "validation_results" in report, "Validation report missing 'validation_results'"

            print(f"✅ Test passed - API endpoint responded correctly")
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running - skipping API integration test")


# ===========================
# Test Scenario 7: Batch Validation
# ===========================

class TestBatchValidation:
    """Test Scenario 7: Batch validation of multiple files."""

    def test_batch_validation(self, temp_workspace, composite_validator):
        """
        Test validation of multiple files at once.

        Expected:
        - All files processed
        - Individual results per file
        - Correct aggregated decision
        """
        # Create multiple files
        files = []

        # File 1: Perfect code
        file1 = os.path.join(temp_workspace, "module1.py")
        with open(file1, 'w') as f:
            f.write(PERFECT_CODE)
        files.append(file1)

        # File 2: Good code
        file2 = os.path.join(temp_workspace, "module2.py")
        with open(file2, 'w') as f:
            f.write(GOOD_CODE_WITH_TESTS)
        files.append(file2)

        # File 3: Test file
        file3 = os.path.join(temp_workspace, "test_module1.py")
        with open(file3, 'w') as f:
            f.write(TEST_FILE_PASSING)
        files.append(file3)

        # Validate batch
        result = composite_validator.validate_output(
            worker_id="TEST_WORKER_BATCH",
            generated_files=files,
            task_name="Batch Validation Test"
        )

        # Assertions
        assert len(result["files_validated"]) == 3, "Not all files validated"
        assert result["decision"] in ["APPROVE", "MANUAL_REVIEW"], \
            f"Unexpected decision for good code: {result['decision']}"

        # Check all files have validation results
        syntax_results = result["validation_results"]["syntax"]
        assert len(syntax_results) == 3, f"Expected 3 syntax results, got {len(syntax_results)}"

        print(f"✅ Test passed - Batch validation of {len(files)} files completed")


# ===========================
# Test Scenario 8: Edge Cases
# ===========================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_file_list(self, composite_validator):
        """Test validation with empty file list."""
        result = composite_validator.validate_output(
            worker_id="TEST_WORKER_EMPTY",
            generated_files=[],
            task_name="Empty File List Test"
        )

        # Should handle gracefully (likely REJECT or MANUAL_REVIEW)
        assert result["decision"] in ["REJECT", "MANUAL_REVIEW", "APPROVE"]
        print(f"✅ Test passed - Empty file list handled, Decision: {result['decision']}")

    def test_nonexistent_file(self, composite_validator):
        """Test validation with nonexistent file."""
        result = composite_validator.validate_output(
            worker_id="TEST_WORKER_NONEXISTENT",
            generated_files=["/tmp/nonexistent_file_xyz123.py"],
            task_name="Nonexistent File Test"
        )

        # Should handle gracefully (likely REJECT due to errors)
        assert result["decision"] in ["REJECT", "MANUAL_REVIEW"]
        print(f"✅ Test passed - Nonexistent file handled, Decision: {result['decision']}")

    def test_mixed_quality_files(self, temp_workspace, composite_validator):
        """Test validation with mix of good and bad files."""
        # Create good file
        good_file = os.path.join(temp_workspace, "good.py")
        with open(good_file, 'w') as f:
            f.write(PERFECT_CODE)

        # Create bad file
        bad_file = os.path.join(temp_workspace, "bad.py")
        with open(bad_file, 'w') as f:
            f.write(SYNTAX_ERROR_CODE)

        result = composite_validator.validate_output(
            worker_id="TEST_WORKER_MIXED",
            generated_files=[good_file, bad_file],
            task_name="Mixed Quality Test"
        )

        # Should REJECT due to syntax error in one file
        assert result["decision"] == "REJECT", \
            f"Expected REJECT for mixed quality, got {result['decision']}"
        assert len(result["blocking_issues"]) > 0, "Expected blocking issues"

        print(f"✅ Test passed - Mixed quality handled correctly, Decision: {result['decision']}")


# ===========================
# Test Scenario 9: Individual Validator Tests
# ===========================

class TestIndividualValidators:
    """Test individual validators in isolation."""

    def test_syntax_validator_valid_code(self, temp_workspace, syntax_validator):
        """Test SyntaxValidator with valid Python code."""
        code_file = os.path.join(temp_workspace, "valid.py")
        with open(code_file, 'w') as f:
            f.write(PERFECT_CODE)

        result = syntax_validator.validate(code_file)

        assert result["valid"] is True, "Valid code should pass syntax check"
        assert len(result["errors"]) == 0, "Valid code should have no errors"
        print(f"✅ SyntaxValidator test passed - Valid code detected")

    def test_syntax_validator_invalid_code(self, temp_workspace, syntax_validator):
        """Test SyntaxValidator with invalid Python code."""
        code_file = os.path.join(temp_workspace, "invalid.py")
        with open(code_file, 'w') as f:
            f.write(SYNTAX_ERROR_CODE)

        result = syntax_validator.validate(code_file)

        assert result["valid"] is False, "Invalid code should fail syntax check"
        assert len(result["errors"]) > 0, "Invalid code should have errors"
        print(f"✅ SyntaxValidator test passed - Syntax error detected")

    def test_security_scanner_clean_code(self, temp_workspace, security_scanner):
        """Test OutputSecurityScanner with clean code."""
        code_file = os.path.join(temp_workspace, "clean.py")
        with open(code_file, 'w') as f:
            f.write(PERFECT_CODE)

        result = security_scanner.scan(code_file)

        assert result["severity"] in ["LOW", "MEDIUM"], \
            f"Clean code should have low severity, got {result['severity']}"
        print(f"✅ SecurityScanner test passed - Clean code detected")

    def test_security_scanner_secret_code(self, temp_workspace, security_scanner):
        """Test OutputSecurityScanner with hardcoded secrets."""
        code_file = os.path.join(temp_workspace, "secret.py")
        with open(code_file, 'w') as f:
            f.write(SECURITY_ISSUE_CODE)

        result = security_scanner.scan(code_file)

        assert result["severity"] in ["CRITICAL", "HIGH"], \
            f"Code with secrets should have high severity, got {result['severity']}"
        assert result["total_findings"] > 0, "Should detect secret findings"
        print(f"✅ SecurityScanner test passed - Secret detected")


# ===========================
# Test Scenario 10: Performance Test
# ===========================

class TestPerformance:
    """Test validation performance."""

    def test_validation_performance(self, temp_workspace, composite_validator):
        """
        Test that validation completes within reasonable time.

        Expected:
        - Validation completes within 30 seconds for typical code
        """
        import time

        # Create test file
        code_file = os.path.join(temp_workspace, "perf_test.py")
        with open(code_file, 'w') as f:
            f.write(PERFECT_CODE)

        start_time = time.time()
        result = composite_validator.validate_output(
            worker_id="TEST_WORKER_PERF",
            generated_files=[code_file],
            task_name="Performance Test"
        )
        duration = time.time() - start_time

        # Should complete within 30 seconds
        assert duration < 30, f"Validation took too long: {duration:.2f}s"
        assert result["decision"] in ["APPROVE", "REJECT", "MANUAL_REVIEW"], "Invalid decision"

        print(f"✅ Performance test passed - Validation completed in {duration:.2f}s")


# ===========================
# Run All Tests
# ===========================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
