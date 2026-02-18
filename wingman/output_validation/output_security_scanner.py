"""
Output Security Scanner - Scans generated code for security issues.

Reuses CodeScanner patterns from validation/code_scanner.py.
Scans for:
- Hardcoded secrets (API keys, passwords, tokens)
- Dangerous commands (rm -rf, DROP TABLE, eval, exec)
- Vulnerability patterns (SQL injection, XSS)
"""

import os
import re
from typing import Any, Dict, List

# Import existing CodeScanner for pattern reuse
try:
    from validation.code_scanner import CodeScanner
    CODE_SCANNER_AVAILABLE = True
except ImportError:
    CODE_SCANNER_AVAILABLE = False


class OutputSecurityScanner:
    """Scans generated code for security issues."""

    def __init__(self):
        """Initialize scanner with patterns."""
        if CODE_SCANNER_AVAILABLE:
            self.code_scanner = CodeScanner()
        else:
            self.code_scanner = None

        # Additional patterns specific to generated code
        self.code_specific_patterns = {
            # Hardcoded secrets (CRITICAL) - case insensitive
            "api_key_pattern": r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]",
            "secret_key_pattern": r"(?i)(secret[_-]?key|secretkey)\s*[=:]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]",
            "password_pattern": r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
            "token_pattern": r"(?i)(token|auth[_-]?token)\s*[=:]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]",
            "aws_key": r"(?i)(AKIA[0-9A-Z]{16}|aws[_-]?access[_-]?key)",

            # Python dangerous functions (CRITICAL)
            "eval_usage": r"\beval\s*\(",
            "exec_usage": r"\bexec\s*\(",
            "compile_usage": r"\bcompile\s*\(",
            "__import__": r"\b__import__\s*\(",

            # Pickle vulnerabilities (CRITICAL)
            "pickle_load": r"\bpickle\.loads?\s*\(",

            # SQL without parameterization (HIGH)
            "sql_concat": r"(execute|cursor\.execute)\s*\([^)]*\+[^)]*\)",
            "sql_format": r"(execute|cursor\.execute)\s*\([^)]*\.format\s*\(",
            "sql_f_string": r"(execute|cursor\.execute)\s*\(f['\"]",

            # OS command injection (CRITICAL)
            "os_system": r"\bos\.system\s*\(",
            "subprocess_shell": r"subprocess\.(run|call|Popen)\s*\([^)]*shell\s*=\s*True",

            # Path traversal (MEDIUM)
            "path_traversal": r"\.\./|\.\.\\\\",
        }

    def scan(self, file_path: str, content: str = None) -> Dict[str, Any]:
        """
        Scan file for security issues.

        Args:
            file_path: Path to file
            content: File content (optional, will read from file_path if not provided)

        Returns:
            {
                "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
                "findings": List[Dict],
                "safe": bool,
                "total_findings": int
            }
        """
        if content is None:
            if not os.path.exists(file_path):
                return {
                    "severity": "LOW",
                    "findings": [],
                    "safe": True,
                    "total_findings": 0,
                    "error": f"File not found: {file_path}"
                }
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

        findings = []

        # Use existing CodeScanner if available (for secret detection)
        if self.code_scanner:
            code_scanner_result = self.code_scanner.scan(content)
            if code_scanner_result.get("findings"):
                for finding in code_scanner_result["findings"]:
                    findings.append({
                        "pattern": finding.get("type", "unknown"),
                        "severity": finding.get("severity", "MEDIUM"),
                        "line": finding.get("line", 0),
                        "context": finding.get("context", ""),
                        "recommendation": finding.get("recommendation", "Review this pattern"),
                        "source": "CodeScanner"
                    })

        # Scan for code-specific patterns
        lines = content.split('\n')
        for line_num, line in enumerate(lines, start=1):
            # Skip comments (Python style)
            if line.strip().startswith('#'):
                continue

            for pattern_name, pattern in self.code_specific_patterns.items():
                if re.search(pattern, line):
                    severity = self._get_pattern_severity(pattern_name)
                    findings.append({
                        "pattern": pattern_name,
                        "severity": severity,
                        "line": line_num,
                        "context": line.strip()[:100],  # Truncate long lines
                        "recommendation": self._get_recommendation(pattern_name),
                        "source": "OutputSecurityScanner"
                    })

        # Determine overall severity (highest severity found)
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        overall_severity = "LOW"
        for finding in findings:
            f_severity = finding.get("severity", "LOW")
            if severity_order.index(f_severity) < severity_order.index(overall_severity):
                overall_severity = f_severity

        # Safe if no CRITICAL or HIGH findings
        safe = overall_severity not in ["CRITICAL", "HIGH"]

        return {
            "severity": overall_severity,
            "findings": findings,
            "safe": safe,
            "total_findings": len(findings)
        }

    def _get_pattern_severity(self, pattern_name: str) -> str:
        """Map pattern to severity level."""
        critical_patterns = [
            "api_key_pattern", "secret_key_pattern", "password_pattern", "token_pattern", "aws_key",
            "eval_usage", "exec_usage", "pickle_load",
            "os_system", "subprocess_shell"
        ]
        high_patterns = [
            "sql_concat", "sql_format", "sql_f_string",
            "__import__", "compile_usage"
        ]
        medium_patterns = [
            "path_traversal"
        ]

        if pattern_name in critical_patterns:
            return "CRITICAL"
        elif pattern_name in high_patterns:
            return "HIGH"
        elif pattern_name in medium_patterns:
            return "MEDIUM"
        else:
            return "LOW"

    def _get_recommendation(self, pattern_name: str) -> str:
        """Get recommendation for pattern."""
        recommendations = {
            "eval_usage": "Avoid eval(). Use ast.literal_eval() or JSON parsing instead",
            "exec_usage": "Avoid exec(). Refactor to use explicit function calls",
            "pickle_load": "Pickle is unsafe. Use JSON or other serialization formats",
            "sql_concat": "Use parameterized queries to prevent SQL injection",
            "sql_format": "Use parameterized queries, not string formatting",
            "sql_f_string": "Use parameterized queries, not f-strings",
            "os_system": "Use subprocess with shell=False and explicit arguments",
            "subprocess_shell": "Set shell=False and pass arguments as list",
            "path_traversal": "Validate and sanitize file paths to prevent traversal",
            "__import__": "Use explicit imports instead of dynamic __import__",
            "compile_usage": "Avoid compile() for untrusted code",
        }
        return recommendations.get(pattern_name, "Review this pattern for security")

    def scan_batch(self, files: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Scan multiple files.

        Args:
            files: List of file paths

        Returns:
            Dict mapping file paths to scan results
        """
        results = {}
        for file_path in files:
            results[file_path] = self.scan(file_path)
        return results
