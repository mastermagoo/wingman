"""
Dependency Verifier - Verifies imported dependencies are available.

Extracts imports from generated code and checks if they're available
in the target environment (docker container).
"""

import ast
import os
import re
import subprocess
from typing import Any, Dict, List, Set


class DependencyVerifier:
    """Verifies dependencies for generated code."""

    def __init__(self, target_container: str = "wingman-test-wingman-api-1"):
        """
        Initialize verifier.

        Args:
            target_container: Docker container name to check dependencies against
        """
        self.target_container = target_container
        self.import_cache = {}  # Cache results to avoid repeated checks

    def verify(self, file_path: str, content: str = None) -> Dict[str, Any]:
        """
        Verify dependencies for file.

        Args:
            file_path: Path to file
            content: File content (optional)

        Returns:
            {
                "all_available": bool,
                "missing": List[str],
                "available": List[str],
                "unknown": List[str],
                "imports": List[str]
            }
        """
        if content is None:
            if not os.path.exists(file_path):
                return {
                    "all_available": False,
                    "missing": [],
                    "available": [],
                    "unknown": [],
                    "imports": [],
                    "error": f"File not found: {file_path}"
                }
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        # Extract imports based on file type
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.py':
            imports = self._extract_python_imports(content)
        else:
            # Unsupported file type
            return {
                "all_available": True,
                "missing": [],
                "available": [],
                "unknown": [],
                "imports": [],
                "warning": f"Unsupported file type for dependency verification: {ext}"
            }

        # Check each import
        missing = []
        available = []
        unknown = []

        for imp in imports:
            # Check cache first
            if imp in self.import_cache:
                if self.import_cache[imp]:
                    available.append(imp)
                else:
                    missing.append(imp)
                continue

            # Check availability in target container
            is_available = self._check_import_available(imp)
            self.import_cache[imp] = is_available

            if is_available is None:
                unknown.append(imp)
            elif is_available:
                available.append(imp)
            else:
                missing.append(imp)

        all_available = len(missing) == 0

        return {
            "all_available": all_available,
            "missing": sorted(missing),
            "available": sorted(available),
            "unknown": sorted(unknown),
            "imports": sorted(imports)
        }

    def _extract_python_imports(self, content: str) -> Set[str]:
        """Extract import statements from Python code."""
        imports = set()

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Get top-level package (e.g., "requests" from "requests.auth")
                        package = alias.name.split('.')[0]
                        imports.add(package)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Get top-level package
                        package = node.module.split('.')[0]
                        imports.add(package)
        except SyntaxError:
            # If syntax error, try regex fallback
            import_patterns = [
                r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import',
            ]
            for line in content.split('\n'):
                for pattern in import_patterns:
                    match = re.match(pattern, line)
                    if match:
                        imports.add(match.group(1))

        # Filter out standard library modules (common ones)
        stdlib_modules = {
            'os', 'sys', 're', 'json', 'time', 'datetime', 'collections',
            'itertools', 'functools', 'typing', 'pathlib', 'subprocess',
            'tempfile', 'shutil', 'copy', 'math', 'random', 'string',
            'logging', 'argparse', 'configparser', 'io', 'ast', 'inspect'
        }

        # Return both stdlib and non-stdlib (we'll check all)
        return imports

    def _check_import_available(self, package: str) -> bool:
        """
        Check if package is available in target container.

        Args:
            package: Package name (e.g., "requests", "flask")

        Returns:
            True if available, False if missing, None if can't determine
        """
        try:
            # Try importing in target container
            cmd = [
                'docker', 'exec', self.target_container,
                'python', '-c', f'import {package}'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=5
            )

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            return None  # Can't determine
        except FileNotFoundError:
            # Docker not available (testing locally?)
            return None
        except Exception:
            return None

    def verify_batch(self, files: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Verify dependencies for multiple files.

        Args:
            files: List of file paths

        Returns:
            Dict mapping file paths to verification results
        """
        results = {}
        for file_path in files:
            results[file_path] = self.verify(file_path)
        return results

    def get_install_commands(self, missing_packages: List[str]) -> List[str]:
        """
        Generate pip install commands for missing packages.

        Args:
            missing_packages: List of missing package names

        Returns:
            List of install commands
        """
        if not missing_packages:
            return []

        return [f"pip install {' '.join(missing_packages)}"]
