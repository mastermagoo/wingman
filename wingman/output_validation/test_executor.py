"""
Test Executor - Runs tests for generated code.

Executes pytest or unittest for test files and captures results.
"""

import os
import re
import subprocess
from typing import Any, Dict, List


class TestExecutor:
    """Executes tests for generated code."""

    def __init__(self, target_container: str = "wingman-test-wingman-api-1", timeout: int = 60):
        """
        Initialize executor.

        Args:
            target_container: Docker container to run tests in
            timeout: Timeout in seconds for test execution
        """
        self.target_container = target_container
        self.timeout = timeout

    def execute_tests(self, test_file_path: str, working_dir: str = "/app") -> Dict[str, Any]:
        """
        Execute tests for file.

        Args:
            test_file_path: Path to test file (relative to container working dir)
            working_dir: Working directory in container

        Returns:
            {
                "passed": int,
                "failed": int,
                "errors": List[Dict],
                "duration": float,
                "output": str,
                "success": bool
            }
        """
        # Check if file looks like a test file
        if not self._is_test_file(test_file_path):
            return {
                "passed": 0,
                "failed": 0,
                "errors": [],
                "duration": 0.0,
                "output": "",
                "success": True,
                "skipped": True,
                "reason": "Not a test file"
            }

        # Determine test framework (pytest or unittest)
        if self._has_pytest():
            return self._run_pytest(test_file_path, working_dir)
        else:
            return self._run_unittest(test_file_path, working_dir)

    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        filename = os.path.basename(file_path)
        return (
            filename.startswith('test_') or
            filename.endswith('_test.py') or
            'test' in filename.lower()
        )

    def _has_pytest(self) -> bool:
        """Check if pytest is available in target container."""
        try:
            result = subprocess.run(
                ['docker', 'exec', self.target_container, 'which', 'pytest'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _run_pytest(self, test_file_path: str, working_dir: str) -> Dict[str, Any]:
        """Run tests using pytest."""
        try:
            cmd = [
                'docker', 'exec', '-w', working_dir,
                self.target_container,
                'pytest', test_file_path,
                '-v',  # Verbose
                '--tb=short',  # Short traceback
                '--no-header',  # No header
                '-q'  # Quiet (less output)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            output = result.stdout + result.stderr

            # Parse pytest output
            passed, failed = self._parse_pytest_output(output)
            errors = self._extract_pytest_errors(output)
            duration = self._extract_duration(output)

            return {
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "duration": duration,
                "output": output,
                "success": result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            return {
                "passed": 0,
                "failed": 1,
                "errors": [{"error": f"Test execution timed out after {self.timeout}s", "line": 0}],
                "duration": float(self.timeout),
                "output": "",
                "success": False
            }
        except Exception as e:
            return {
                "passed": 0,
                "failed": 1,
                "errors": [{"error": f"Test execution failed: {str(e)}", "line": 0}],
                "duration": 0.0,
                "output": "",
                "success": False
            }

    def _run_unittest(self, test_file_path: str, working_dir: str) -> Dict[str, Any]:
        """Run tests using unittest."""
        try:
            # Convert file path to module name (e.g., tests/test_foo.py -> tests.test_foo)
            module_name = test_file_path.replace('/', '.').replace('.py', '')

            cmd = [
                'docker', 'exec', '-w', working_dir,
                self.target_container,
                'python', '-m', 'unittest', module_name, '-v'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            output = result.stdout + result.stderr

            # Parse unittest output
            passed, failed = self._parse_unittest_output(output)
            errors = self._extract_unittest_errors(output)

            return {
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "duration": 0.0,  # Unittest doesn't provide duration easily
                "output": output,
                "success": result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            return {
                "passed": 0,
                "failed": 1,
                "errors": [{"error": f"Test execution timed out after {self.timeout}s", "line": 0}],
                "duration": float(self.timeout),
                "output": "",
                "success": False
            }
        except Exception as e:
            return {
                "passed": 0,
                "failed": 1,
                "errors": [{"error": f"Test execution failed: {str(e)}", "line": 0}],
                "duration": 0.0,
                "output": "",
                "success": False
            }

    def _parse_pytest_output(self, output: str) -> tuple:
        """Parse pytest output to extract passed/failed counts."""
        # Look for pattern: "X passed, Y failed"
        match = re.search(r'(\d+) passed', output)
        passed = int(match.group(1)) if match else 0

        match = re.search(r'(\d+) failed', output)
        failed = int(match.group(1)) if match else 0

        return passed, failed

    def _parse_unittest_output(self, output: str) -> tuple:
        """Parse unittest output to extract passed/failed counts."""
        # Look for pattern: "Ran X tests"
        match = re.search(r'Ran (\d+) test', output)
        total = int(match.group(1)) if match else 0

        # Check for failures/errors
        match = re.search(r'FAILED \(.*failures=(\d+)', output)
        failed = int(match.group(1)) if match else 0

        match = re.search(r'errors=(\d+)', output)
        errors = int(match.group(1)) if match else 0

        failed += errors
        passed = total - failed

        return passed, failed

    def _extract_pytest_errors(self, output: str) -> List[Dict]:
        """Extract error details from pytest output."""
        errors = []
        # Simple extraction: lines starting with FAILED or ERROR
        for line in output.split('\n'):
            if 'FAILED' in line or 'ERROR' in line:
                errors.append({"error": line.strip(), "line": 0})

        return errors

    def _extract_unittest_errors(self, output: str) -> List[Dict]:
        """Extract error details from unittest output."""
        errors = []
        # Simple extraction: lines starting with FAIL or ERROR
        for line in output.split('\n'):
            if line.startswith('FAIL') or line.startswith('ERROR'):
                errors.append({"error": line.strip(), "line": 0})

        return errors

    def _extract_duration(self, output: str) -> float:
        """Extract test duration from output."""
        # pytest format: "X.XXs"
        match = re.search(r'([\d\.]+)s', output)
        if match:
            return float(match.group(1))
        return 0.0

    def execute_batch(self, test_files: List[str], working_dir: str = "/app") -> Dict[str, Dict[str, Any]]:
        """
        Execute tests for multiple files.

        Args:
            test_files: List of test file paths
            working_dir: Working directory in container

        Returns:
            Dict mapping file paths to test results
        """
        results = {}
        for test_file in test_files:
            results[test_file] = self.execute_tests(test_file, working_dir)
        return results
