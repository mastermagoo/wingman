"""
Syntax Validator - Validates code parses correctly.

Supports:
- Python: ast.parse()
- YAML: yaml.safe_load()
- JSON: json.loads()
- JavaScript: node --check (if available)
"""

import ast
import json
import os
import subprocess
from typing import Any, Dict, List

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class SyntaxValidator:
    """Validates syntax of generated code files."""

    def validate(self, file_path: str, content: str = None) -> Dict[str, Any]:
        """
        Validate syntax of file.

        Args:
            file_path: Path to file (used for extension detection)
            content: File content (optional, will read from file_path if not provided)

        Returns:
            {
                "valid": bool,
                "errors": List[str],
                "line_numbers": List[int],
                "error_details": List[Dict]
            }
        """
        if content is None:
            if not os.path.exists(file_path):
                return {
                    "valid": False,
                    "errors": [f"File not found: {file_path}"],
                    "line_numbers": [],
                    "error_details": [{"error": "File not found", "line": 0}]
                }
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        # Detect file type from extension
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.py':
            return self._validate_python(content, file_path)
        elif ext in ['.yaml', '.yml']:
            return self._validate_yaml(content, file_path)
        elif ext == '.json':
            return self._validate_json(content, file_path)
        elif ext == '.js':
            return self._validate_javascript(content, file_path)
        else:
            # Unknown file type, skip validation
            return {
                "valid": True,
                "errors": [],
                "line_numbers": [],
                "error_details": [],
                "warning": f"Unknown file type: {ext}, skipping syntax validation"
            }

    def _validate_python(self, content: str, file_path: str) -> Dict[str, Any]:
        """Validate Python syntax using ast.parse()."""
        try:
            ast.parse(content, filename=file_path)
            return {
                "valid": True,
                "errors": [],
                "line_numbers": [],
                "error_details": []
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "errors": [f"SyntaxError: {e.msg} at line {e.lineno}"],
                "line_numbers": [e.lineno] if e.lineno else [],
                "error_details": [{
                    "error": e.msg,
                    "line": e.lineno,
                    "offset": e.offset,
                    "text": e.text
                }]
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Parsing error: {str(e)}"],
                "line_numbers": [],
                "error_details": [{"error": str(e), "line": 0}]
            }

    def _validate_yaml(self, content: str, file_path: str) -> Dict[str, Any]:
        """Validate YAML syntax."""
        if not YAML_AVAILABLE:
            return {
                "valid": True,
                "errors": [],
                "line_numbers": [],
                "error_details": [],
                "warning": "PyYAML not installed, skipping YAML validation"
            }

        try:
            yaml.safe_load(content)
            return {
                "valid": True,
                "errors": [],
                "line_numbers": [],
                "error_details": []
            }
        except yaml.YAMLError as e:
            line = getattr(e, 'problem_mark', None)
            line_num = line.line + 1 if line else 0
            return {
                "valid": False,
                "errors": [f"YAML error: {str(e)}"],
                "line_numbers": [line_num] if line_num else [],
                "error_details": [{
                    "error": str(e),
                    "line": line_num
                }]
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"YAML parsing error: {str(e)}"],
                "line_numbers": [],
                "error_details": [{"error": str(e), "line": 0}]
            }

    def _validate_json(self, content: str, file_path: str) -> Dict[str, Any]:
        """Validate JSON syntax."""
        try:
            json.loads(content)
            return {
                "valid": True,
                "errors": [],
                "line_numbers": [],
                "error_details": []
            }
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "errors": [f"JSON error: {e.msg} at line {e.lineno}"],
                "line_numbers": [e.lineno],
                "error_details": [{
                    "error": e.msg,
                    "line": e.lineno,
                    "column": e.colno
                }]
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"JSON parsing error: {str(e)}"],
                "line_numbers": [],
                "error_details": [{"error": str(e), "line": 0}]
            }

    def _validate_javascript(self, content: str, file_path: str) -> Dict[str, Any]:
        """Validate JavaScript syntax using node --check."""
        try:
            # Check if node is available
            result = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                return {
                    "valid": True,
                    "errors": [],
                    "line_numbers": [],
                    "error_details": [],
                    "warning": "Node.js not available, skipping JS validation"
                }

            # Write content to temp file and validate
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(content)
                temp_path = f.name

            try:
                result = subprocess.run(
                    ['node', '--check', temp_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    return {
                        "valid": True,
                        "errors": [],
                        "line_numbers": [],
                        "error_details": []
                    }
                else:
                    # Parse error from stderr
                    error_msg = result.stderr.strip()
                    return {
                        "valid": False,
                        "errors": [f"JavaScript syntax error: {error_msg}"],
                        "line_numbers": [],
                        "error_details": [{"error": error_msg, "line": 0}]
                    }
            finally:
                os.unlink(temp_path)

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {
                "valid": True,
                "errors": [],
                "line_numbers": [],
                "error_details": [],
                "warning": "Node.js validation unavailable"
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"JavaScript validation error: {str(e)}"],
                "line_numbers": [],
                "error_details": [{"error": str(e), "line": 0}]
            }

    def validate_batch(self, files: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Validate multiple files.

        Args:
            files: List of file paths

        Returns:
            Dict mapping file paths to validation results
        """
        results = {}
        for file_path in files:
            results[file_path] = self.validate(file_path)
        return results
