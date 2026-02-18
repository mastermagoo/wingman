#!/usr/bin/env python3
"""
Standalone test runner for output validation integration tests.
Can run without pytest for quick validation.

Usage:
    python run_output_validation_tests.py
    python run_output_validation_tests.py --verbose
    python run_output_validation_tests.py --test <test_name>
"""

import sys
import os
import tempfile
import shutil
import traceback
from typing import Callable, List, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test module
try:
    from test_output_validation_integration import (
        TestPerfectCodeAutoApprove,
        TestSyntaxErrorsAutoReject,
        TestSecurityIssuesAutoReject,
        TestMissingDependenciesManualReview,
        TestBatchValidation,
        TestEdgeCases,
        TestIndividualValidators,
        TestPerformance,
        OutputCompositeValidator,
        SyntaxValidator,
        OutputSecurityScanner,
    )
except ImportError as e:
    print(f"❌ Failed to import test modules: {e}")
    sys.exit(1)


class SimpleTestRunner:
    """Simple test runner without pytest."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.temp_workspace = None

    def setup_workspace(self):
        """Create temporary workspace."""
        self.temp_workspace = tempfile.mkdtemp(prefix="wingman_test_")
        return self.temp_workspace

    def teardown_workspace(self):
        """Clean up temporary workspace."""
        if self.temp_workspace and os.path.exists(self.temp_workspace):
            shutil.rmtree(self.temp_workspace)
            self.temp_workspace = None

    def run_test(self, test_name: str, test_func: Callable, setup_func: Callable = None) -> bool:
        """
        Run a single test.

        Args:
            test_name: Name of the test
            test_func: Test function to run
            setup_func: Optional setup function

        Returns:
            True if test passed, False otherwise
        """
        try:
            print(f"\n{'='*60}")
            print(f"Running: {test_name}")
            print('='*60)

            # Setup
            if setup_func:
                fixtures = setup_func()
            else:
                fixtures = {}

            # Run test
            test_func(**fixtures)

            # Success
            print(f"✅ PASSED: {test_name}")
            self.passed += 1
            return True

        except AssertionError as e:
            print(f"❌ FAILED: {test_name}")
            print(f"   Assertion Error: {str(e)}")
            if self.verbose:
                traceback.print_exc()
            self.failed += 1
            return False

        except Exception as e:
            print(f"❌ ERROR: {test_name}")
            print(f"   {type(e).__name__}: {str(e)}")
            if self.verbose:
                traceback.print_exc()
            self.failed += 1
            return False

        finally:
            # Cleanup
            self.teardown_workspace()

    def run_all_tests(self, test_filter: str = None):
        """Run all tests."""
        print("=" * 60)
        print("WINGMAN OUTPUT VALIDATION INTEGRATION TESTS")
        print("=" * 60)

        tests_to_run = []

        # Test 1: Perfect Code Auto-Approve
        if not test_filter or "perfect" in test_filter.lower():
            tests_to_run.append((
                "test_perfect_code_auto_approve",
                lambda temp_workspace, validator: TestPerfectCodeAutoApprove().test_perfect_code_auto_approve(
                    temp_workspace, validator
                ),
                lambda: {
                    "temp_workspace": self.setup_workspace(),
                    "validator": OutputCompositeValidator(target_container="wingman-test-wingman-api-1")
                }
            ))

        # Test 2: Syntax Errors Auto-Reject
        if not test_filter or "syntax" in test_filter.lower():
            tests_to_run.append((
                "test_syntax_errors_auto_reject",
                lambda temp_workspace, validator: TestSyntaxErrorsAutoReject().test_syntax_errors_auto_reject(
                    temp_workspace, validator
                ),
                lambda: {
                    "temp_workspace": self.setup_workspace(),
                    "validator": OutputCompositeValidator(target_container="wingman-test-wingman-api-1")
                }
            ))

        # Test 3: Security Issues Auto-Reject
        if not test_filter or "security" in test_filter.lower():
            tests_to_run.append((
                "test_security_issues_auto_reject",
                lambda temp_workspace, validator: TestSecurityIssuesAutoReject().test_security_issues_auto_reject(
                    temp_workspace, validator
                ),
                lambda: {
                    "temp_workspace": self.setup_workspace(),
                    "validator": OutputCompositeValidator(target_container="wingman-test-wingman-api-1")
                }
            ))

        # Test 4: Missing Dependencies Manual Review
        if not test_filter or "dependency" in test_filter.lower() or "missing" in test_filter.lower():
            tests_to_run.append((
                "test_missing_dependencies_manual_review",
                lambda temp_workspace, validator: TestMissingDependenciesManualReview().test_missing_dependencies_manual_review(
                    temp_workspace, validator
                ),
                lambda: {
                    "temp_workspace": self.setup_workspace(),
                    "validator": OutputCompositeValidator(target_container="wingman-test-wingman-api-1")
                }
            ))

        # Test 5: Batch Validation
        if not test_filter or "batch" in test_filter.lower():
            tests_to_run.append((
                "test_batch_validation",
                lambda temp_workspace, validator: TestBatchValidation().test_batch_validation(
                    temp_workspace, validator
                ),
                lambda: {
                    "temp_workspace": self.setup_workspace(),
                    "validator": OutputCompositeValidator(target_container="wingman-test-wingman-api-1")
                }
            ))

        # Test 6: Edge Cases - Empty File List
        if not test_filter or "edge" in test_filter.lower() or "empty" in test_filter.lower():
            tests_to_run.append((
                "test_empty_file_list",
                lambda validator: TestEdgeCases().test_empty_file_list(validator),
                lambda: {
                    "validator": OutputCompositeValidator(target_container="wingman-test-wingman-api-1")
                }
            ))

        # Test 7: Edge Cases - Nonexistent File
        if not test_filter or "edge" in test_filter.lower() or "nonexistent" in test_filter.lower():
            tests_to_run.append((
                "test_nonexistent_file",
                lambda validator: TestEdgeCases().test_nonexistent_file(validator),
                lambda: {
                    "validator": OutputCompositeValidator(target_container="wingman-test-wingman-api-1")
                }
            ))

        # Test 8: Edge Cases - Mixed Quality
        if not test_filter or "edge" in test_filter.lower() or "mixed" in test_filter.lower():
            tests_to_run.append((
                "test_mixed_quality_files",
                lambda temp_workspace, validator: TestEdgeCases().test_mixed_quality_files(
                    temp_workspace, validator
                ),
                lambda: {
                    "temp_workspace": self.setup_workspace(),
                    "validator": OutputCompositeValidator(target_container="wingman-test-wingman-api-1")
                }
            ))

        # Test 9: Individual Validators - Syntax Valid
        if not test_filter or "individual" in test_filter.lower() or "validator" in test_filter.lower():
            tests_to_run.append((
                "test_syntax_validator_valid_code",
                lambda temp_workspace, validator: TestIndividualValidators().test_syntax_validator_valid_code(
                    temp_workspace, validator
                ),
                lambda: {
                    "temp_workspace": self.setup_workspace(),
                    "validator": SyntaxValidator()
                }
            ))

        # Test 10: Individual Validators - Syntax Invalid
        if not test_filter or "individual" in test_filter.lower() or "validator" in test_filter.lower():
            tests_to_run.append((
                "test_syntax_validator_invalid_code",
                lambda temp_workspace, validator: TestIndividualValidators().test_syntax_validator_invalid_code(
                    temp_workspace, validator
                ),
                lambda: {
                    "temp_workspace": self.setup_workspace(),
                    "validator": SyntaxValidator()
                }
            ))

        # Test 11: Individual Validators - Security Clean
        if not test_filter or "individual" in test_filter.lower() or "validator" in test_filter.lower():
            tests_to_run.append((
                "test_security_scanner_clean_code",
                lambda temp_workspace, scanner: TestIndividualValidators().test_security_scanner_clean_code(
                    temp_workspace, scanner
                ),
                lambda: {
                    "temp_workspace": self.setup_workspace(),
                    "scanner": OutputSecurityScanner()
                }
            ))

        # Test 12: Individual Validators - Security Secret
        if not test_filter or "individual" in test_filter.lower() or "validator" in test_filter.lower():
            tests_to_run.append((
                "test_security_scanner_secret_code",
                lambda temp_workspace, scanner: TestIndividualValidators().test_security_scanner_secret_code(
                    temp_workspace, scanner
                ),
                lambda: {
                    "temp_workspace": self.setup_workspace(),
                    "scanner": OutputSecurityScanner()
                }
            ))

        # Test 13: Performance Test
        if not test_filter or "performance" in test_filter.lower() or "perf" in test_filter.lower():
            tests_to_run.append((
                "test_validation_performance",
                lambda temp_workspace, validator: TestPerformance().test_validation_performance(
                    temp_workspace, validator
                ),
                lambda: {
                    "temp_workspace": self.setup_workspace(),
                    "validator": OutputCompositeValidator(target_container="wingman-test-wingman-api-1")
                }
            ))

        # Run all tests
        for test_name, test_func, setup_func in tests_to_run:
            self.run_test(test_name, test_func, setup_func)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed + self.skipped
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests:   {total}")
        print(f"✅ Passed:     {self.passed}")
        print(f"❌ Failed:     {self.failed}")
        print(f"⏭️  Skipped:    {self.skipped}")
        print("=" * 60)

        if self.failed == 0:
            print("✅ ALL TESTS PASSED!")
        else:
            print(f"❌ {self.failed} TEST(S) FAILED")

        # Exit code
        sys.exit(0 if self.failed == 0 else 1)


def main():
    """Main entry point."""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    test_filter = None

    # Check for --test argument
    if "--test" in sys.argv:
        idx = sys.argv.index("--test")
        if idx + 1 < len(sys.argv):
            test_filter = sys.argv[idx + 1]

    runner = SimpleTestRunner(verbose=verbose)
    runner.run_all_tests(test_filter=test_filter)


if __name__ == "__main__":
    main()
