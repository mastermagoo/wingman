"""
Output Composite Validator - Orchestrates all validators.

Combines results from:
- SyntaxValidator
- OutputSecurityScanner
- DependencyVerifier
- TestExecutor

Makes final decision: APPROVE, REJECT, or MANUAL_REVIEW
"""

import os
from typing import Any, Dict, List

from output_validation.syntax_validator import SyntaxValidator
from output_validation.output_security_scanner import OutputSecurityScanner
from output_validation.dependency_verifier import DependencyVerifier
from output_validation.test_executor import TestExecutor


class OutputCompositeValidator:
    """Orchestrates all output validators."""

    def __init__(self, target_container: str = "wingman-test-wingman-api-1"):
        """
        Initialize composite validator.

        Args:
            target_container: Docker container for dependency/test checking
        """
        self.syntax_validator = SyntaxValidator()
        self.security_scanner = OutputSecurityScanner()
        self.dependency_verifier = DependencyVerifier(target_container)
        self.test_executor = TestExecutor(target_container)

        # Thresholds (configurable)
        self.auto_approve_threshold = 70  # Score >= 70 → auto-approve
        self.auto_reject_threshold = 30   # Score < 30 → auto-reject

    def validate_output(
        self,
        worker_id: str,
        generated_files: List[str],
        task_name: str = None
    ) -> Dict[str, Any]:
        """
        Validate generated code from AI worker.

        Args:
            worker_id: Worker that generated code
            generated_files: List of file paths (relative or absolute)
            task_name: Optional task name

        Returns:
            {
                "decision": "APPROVE" | "REJECT" | "MANUAL_REVIEW",
                "overall_score": int (0-100),
                "validation_results": {
                    "syntax": {...},
                    "security": {...},
                    "dependencies": {...},
                    "tests": {...}
                },
                "recommendation": str,
                "blocking_issues": List[str],
                "worker_id": str,
                "task_name": str,
                "files_validated": List[str]
            }
        """
        validation_results = {
            "syntax": {},
            "security": {},
            "dependencies": {},
            "tests": {}
        }
        blocking_issues = []

        # Separate code files and test files
        code_files = [f for f in generated_files if not self._is_test_file(f)]
        test_files = [f for f in generated_files if self._is_test_file(f)]

        # 1. Syntax Validation (all files)
        syntax_results = {}
        for file_path in generated_files:
            result = self.syntax_validator.validate(file_path)
            syntax_results[file_path] = result
            if not result["valid"]:
                blocking_issues.append(f"Syntax error in {os.path.basename(file_path)}")

        validation_results["syntax"] = syntax_results

        # 2. Security Scanning (code files only)
        security_results = {}
        for file_path in code_files:
            result = self.security_scanner.scan(file_path)
            security_results[file_path] = result
            if result["severity"] in ["CRITICAL", "HIGH"]:
                blocking_issues.append(f"Security issue ({result['severity']}) in {os.path.basename(file_path)}")

        validation_results["security"] = security_results

        # 3. Dependency Verification (code files only)
        dependency_results = {}
        for file_path in code_files:
            result = self.dependency_verifier.verify(file_path)
            dependency_results[file_path] = result
            if not result["all_available"] and result["missing"]:
                # Missing dependencies are warning, not blocking (can be installed)
                pass

        validation_results["dependencies"] = dependency_results

        # 4. Test Execution (test files only)
        test_results = {}
        for test_file in test_files:
            result = self.test_executor.execute_tests(test_file)
            test_results[test_file] = result
            if not result["success"] and result["failed"] > 0:
                # Failed tests are warning, not blocking (can be fixed)
                pass

        validation_results["tests"] = test_results

        # Calculate overall score
        overall_score = self._calculate_score(validation_results)

        # Make decision
        decision = self._make_decision(overall_score, blocking_issues, validation_results)

        # Generate recommendation
        recommendation = self._generate_recommendation(decision, blocking_issues, validation_results)

        return {
            "decision": decision,
            "overall_score": overall_score,
            "validation_results": validation_results,
            "recommendation": recommendation,
            "blocking_issues": blocking_issues,
            "worker_id": worker_id,
            "task_name": task_name or "Unknown",
            "files_validated": generated_files
        }

    def _calculate_score(self, validation_results: Dict) -> int:
        """
        Calculate overall validation score (0-100).

        Scoring:
        - Syntax: 40% (pass/fail)
        - Security: 30% (severity-based)
        - Dependencies: 20% (availability)
        - Tests: 10% (pass rate)
        """
        score = 0

        # Syntax (40 points)
        syntax_results = validation_results.get("syntax", {})
        if syntax_results:
            valid_count = sum(1 for r in syntax_results.values() if r.get("valid", False))
            total_count = len(syntax_results)
            syntax_score = (valid_count / total_count * 40) if total_count > 0 else 0
            score += syntax_score

        # Security (30 points)
        security_results = validation_results.get("security", {})
        if security_results:
            security_score = 30  # Start with perfect score
            for result in security_results.values():
                severity = result.get("severity", "LOW")
                if severity == "CRITICAL":
                    security_score = 0  # Critical = fail
                    break
                elif severity == "HIGH":
                    security_score = min(security_score, 15)  # High = 50% penalty
                elif severity == "MEDIUM":
                    security_score = min(security_score, 22)  # Medium = 25% penalty
            score += security_score

        # Dependencies (20 points)
        dependency_results = validation_results.get("dependencies", {})
        if dependency_results:
            available_count = sum(1 for r in dependency_results.values() if r.get("all_available", False))
            total_count = len(dependency_results)
            dep_score = (available_count / total_count * 20) if total_count > 0 else 20  # Default 20 if no deps
            score += dep_score
        else:
            score += 20  # No dependencies = full points

        # Tests (10 points)
        test_results = validation_results.get("tests", {})
        if test_results:
            passed_total = sum(r.get("passed", 0) for r in test_results.values())
            failed_total = sum(r.get("failed", 0) for r in test_results.values())
            total_tests = passed_total + failed_total
            test_score = (passed_total / total_tests * 10) if total_tests > 0 else 0
            score += test_score
        else:
            score += 5  # No tests = half points

        return int(score)

    def _make_decision(self, score: int, blocking_issues: List[str], validation_results: Dict) -> str:
        """
        Make validation decision based on score and issues.

        Decision logic:
        - REJECT: blocking issues OR score < 30
        - APPROVE: score >= 70 AND no blocking issues
        - MANUAL_REVIEW: everything else
        """
        if blocking_issues:
            return "REJECT"

        if score < self.auto_reject_threshold:
            return "REJECT"

        if score >= self.auto_approve_threshold:
            # Additional check: no critical security issues
            security_results = validation_results.get("security", {})
            for result in security_results.values():
                if result.get("severity") == "CRITICAL":
                    return "REJECT"
            return "APPROVE"

        return "MANUAL_REVIEW"

    def _generate_recommendation(
        self,
        decision: str,
        blocking_issues: List[str],
        validation_results: Dict
    ) -> str:
        """Generate human-readable recommendation."""
        if decision == "APPROVE":
            return "Code passed all validation checks. Safe to deploy."

        if decision == "REJECT":
            reasons = []
            if blocking_issues:
                reasons.append(f"Blocking issues: {', '.join(blocking_issues)}")

            # Add specific guidance
            syntax_results = validation_results.get("syntax", {})
            for file_path, result in syntax_results.items():
                if not result.get("valid"):
                    reasons.append(f"Fix syntax errors in {os.path.basename(file_path)}")

            security_results = validation_results.get("security", {})
            for file_path, result in security_results.items():
                if result.get("severity") in ["CRITICAL", "HIGH"]:
                    findings_count = result.get("total_findings", 0)
                    reasons.append(f"Fix {findings_count} security issues in {os.path.basename(file_path)}")

            return "REJECTED: " + "; ".join(reasons) if reasons else "REJECTED: Quality below threshold"

        if decision == "MANUAL_REVIEW":
            notes = []

            # Check for missing dependencies
            dependency_results = validation_results.get("dependencies", {})
            all_missing = []
            for result in dependency_results.values():
                all_missing.extend(result.get("missing", []))
            if all_missing:
                notes.append(f"Missing dependencies: {', '.join(set(all_missing))}")

            # Check for test failures
            test_results = validation_results.get("tests", {})
            failed_count = sum(r.get("failed", 0) for r in test_results.values())
            if failed_count > 0:
                notes.append(f"{failed_count} tests failed")

            # Check for medium security issues
            security_results = validation_results.get("security", {})
            for result in security_results.values():
                if result.get("severity") == "MEDIUM":
                    notes.append(f"{result.get('total_findings', 0)} medium security issues")

            return "MANUAL_REVIEW: " + "; ".join(notes) if notes else "MANUAL_REVIEW: Moderate quality, review recommended"

        return "Unknown decision"

    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        filename = os.path.basename(file_path)
        return (
            filename.startswith('test_') or
            filename.endswith('_test.py') or
            '/tests/' in file_path or
            '/test/' in file_path
        )
