"""
Wingman Validation package.

Important: this package must remain import-safe even when validator modules are not yet present.

Status (repo reality on `test` as of 2026-01-19):
- Validator modules under `wingman/validation/` are missing (semantic/code/dependency/content/composite).
- This `__init__.py` therefore MUST NOT import those modules at import-time.
"""

__all__ = []
