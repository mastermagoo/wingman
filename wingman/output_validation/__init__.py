"""
Output validation package for AI worker generated code.

Validates generated code before deployment:
- Syntax validation (Python, YAML, JSON, JavaScript)
- Security scanning (secrets, dangerous patterns)
- Dependency verification (imports available)
- Test execution (pytest/unittest)
- Quality scoring (complexity, documentation)

Usage:
    from output_validation import OutputCompositeValidator

    validator = OutputCompositeValidator()
    result = validator.validate_output(worker_id="WORKER_001",
                                       generated_files=["semantic_analyzer.py"])
"""

from output_validation.syntax_validator import SyntaxValidator
from output_validation.output_security_scanner import OutputSecurityScanner
from output_validation.dependency_verifier import DependencyVerifier
from output_validation.test_executor import TestExecutor
from output_validation.output_composite_validator import OutputCompositeValidator

__all__ = [
    "SyntaxValidator",
    "OutputSecurityScanner",
    "DependencyVerifier",
    "TestExecutor",
    "OutputCompositeValidator",
]
