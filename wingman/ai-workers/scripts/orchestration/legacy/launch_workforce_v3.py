#!/usr/bin/env python3
"""Compatibility entrypoint.

Canonical implementation now lives at: tools/orchestration/launch_workforce_v3.py
This wrapper preserves existing root-level paths while keeping the codebase organized.
"""

from __future__ import annotations

from pathlib import Path
import runpy
import sys


def main() -> int:
    impl = Path(__file__).resolve().parent / "tools" / "orchestration" / "launch_workforce_v3.py"
    runpy.run_path(str(impl), run_name="__main__")
    return 0


if __name__ == "__main__":
    sys.exit(main())
