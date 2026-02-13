#!/usr/bin/env python3
"""
Phase 1A E2E verification: 100% confidence that path/command/parsing work.
Uses the EXACT same parsing logic as wingman_orchestrator.py so there are
no assumptions — any failure is attributable to generated code/tests, not
path or command mismatches.

Run from anywhere; repo root is derived from this script's path.
Exits 0 only if:
  1. All 18 Phase 1A workers parse correctly (same logic as orchestrator).
  2. No path/command anti-patterns (no wingman/ prefix, no "cd wingman").
  3. WORKER_001 test commands pass with minimal semantic_analyzer.py.
  4. WORKER_002–018 commands execute without path/command errors (failure
     may be code/test content; we only fail on path/command-specific errors).
"""
import re
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def extract_section(content: str, header: str):
    """Exact copy of WingmanOrchestrator.extract_section for TEST_PROCESS and DELIVERABLES."""
    pattern = rf"##\s*{re.escape(header)}(.*?)(?=##\s*\d+\.|---|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return None
    section_text = match.group(1).strip()

    if header == "1. DELIVERABLES":
        lines = [
            line.strip().lstrip("-•[]✓✗").strip()
            for line in section_text.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]
        return [line for line in lines if line]

    if header == "6. TEST_PROCESS":
        code_blocks = re.findall(r"```(?:bash)?\n(.*?)\n```", section_text, re.DOTALL)
        if code_blocks:
            commands = []
            for block in code_blocks:
                lines = [
                    ln.strip()
                    for ln in block.split("\n")
                    if ln.strip() and not ln.strip().startswith("#")
                ]
                i = 0
                while i < len(lines):
                    line = lines[i]
                    if re.match(r'python3\s+-c\s+["\']', line):
                        q = '"' if line.split("-c", 1)[1].strip()[0] == '"' else "'"
                        if line.count(q) < 2 or not re.search(rf"\{q}\s*(#.*)?$", line.rstrip()):
                            buf = [line]
                            i += 1
                            while i < len(lines) and not re.search(
                                rf"\{q}\s*(#.*)?$", lines[i].rstrip()
                            ):
                                buf.append(lines[i])
                                i += 1
                            if i < len(lines):
                                buf.append(lines[i])
                                i += 1
                            commands.append("\n".join(buf))
                            continue
                    commands.append(line)
                    i += 1
        return commands
    return None


def parse_worker(worker_file: Path):
    """Parse DELIVERABLES and TEST_PROCESS the same way the orchestrator does."""
    content = worker_file.read_text()
    deliverables = extract_section(content, "1. DELIVERABLES")
    test_process = extract_section(content, "6. TEST_PROCESS")
    return deliverables or [], test_process or []


def extract_deliverable_py_path(deliverables: list) -> str | None:
    """Same regex as orchestrator: first backticked .py path in any deliverable line."""
    for line in deliverables:
        m = re.search(r"`(.*?\.py)`", line)
        if m:
            return m.group(1).strip()
    return None


def main() -> int:
    root = repo_root()
    workers_dir = root / "ai-workers" / "workers"
    if not workers_dir.is_dir():
        print("ERROR: ai-workers/workers not found:", workers_dir)
        return 1

    phase1a_ids = [f"WORKER_{i:03d}" for i in range(1, 19)]
    errors = []

    # --- 1. Parse all 18 workers (same logic as orchestrator) ---
    parsed = {}
    for wid in phase1a_ids:
        matches = list(workers_dir.glob(f"{wid}_*.md"))
        if not matches:
            errors.append(f"{wid}: no instruction file found")
            continue
        path = matches[0]
        deliverables, test_process = parse_worker(path)
        if not deliverables:
            errors.append(f"{wid}: no DELIVERABLES parsed")
        if not test_process:
            errors.append(f"{wid}: no TEST_PROCESS parsed (missing or empty code block)")
        parsed[wid] = {"path": path, "deliverables": deliverables, "test_process": test_process}

    # --- 2. Path/command anti-patterns (no assumptions) ---
    for wid, data in parsed.items():
        py_path = extract_deliverable_py_path(data["deliverables"])
        if py_path:
            if "wingman/" in py_path or py_path.startswith("wingman"):
                errors.append(f"{wid}: deliverable path must be repo-root-relative (got {py_path!r})")
            resolved = root / py_path
            if not resolved.parent.exists() and wid == "WORKER_001":
                errors.append(f"{wid}: deliverable parent dir does not exist: {resolved.parent}")
        for cmd in data["test_process"]:
            if "cd wingman" in cmd or "cd wingman;" in cmd or "cd wingman " in cmd:
                errors.append(f"{wid}: test command must not use 'cd wingman': {cmd!r}")
            if "wingman/" in cmd or "wingman\\" in cmd:
                errors.append(f"{wid}: test command must not reference wingman/ path: {cmd!r}")
            if "pytest " in cmd and "tests/validation/" not in cmd and "test_semantic_analyzer" in cmd:
                errors.append(f"{wid}: pytest should target tests/validation/test_semantic_analyzer.py: {cmd!r}")

    if errors:
        for e in errors:
            print("FAIL:", e)
        return 1

    # --- 3. WORKER_001: minimal file + run all test commands, assert pass ---
    minimal_py = '''"""Semantic analyzer - minimal implementation for WORKER_001."""
class SemanticAnalyzer:
    def __init__(self, ollama_endpoint="http://ollama:11434"):
        self.ollama_endpoint = ollama_endpoint
'''
    semantic_file = root / "validation" / "semantic_analyzer.py"
    semantic_file.parent.mkdir(parents=True, exist_ok=True)
    semantic_file.write_text(minimal_py)

    for cmd in parsed["WORKER_001"]["test_process"]:
        r = subprocess.run(
            cmd, shell=True, cwd=root, capture_output=True, text=True, timeout=15
        )
        if r.returncode != 0:
            errors.append(
                f"WORKER_001 command failed (path/command must be correct): {cmd!r}\n"
                f"stderr: {r.stderr or r.stdout or '(none)'}"
            )
    if errors:
        for e in errors:
            print("FAIL:", e)
        return 1

    # --- 4. WORKER_002–018: run commands; fail only on path/command errors ---
    path_error_indicators = (
        "no such file or directory",
        "cannot find",
        "filenotfounderror",
        "cd: wingman:",
        "modulenotfounderror: no module named 'wingman",
        "error: file or directory not found",
        "path not found",
    )

    for wid in phase1a_ids:
        if wid == "WORKER_001":
            continue
        for cmd in parsed[wid]["test_process"]:
            r = subprocess.run(
                cmd, shell=True, cwd=root, capture_output=True, text=True, timeout=60
            )
            if r.returncode == 0:
                continue
            stderr_lower = (r.stderr or "").lower()
            stdout_lower = (r.stdout or "").lower()
            combined = stderr_lower + "\n" + stdout_lower
            if any(ind in combined for ind in path_error_indicators):
                errors.append(
                    f"{wid}: path/command error (not code): {cmd!r}\n"
                    f"stderr: {(r.stderr or '')[:500]}\nstdout: {(r.stdout or '')[:500]}"
                )
            # If pytest ran but tests failed, ensure it found the file (no "not found" for test file)
            if "pytest" in cmd and "test_semantic_analyzer" in cmd:
                if "tests/validation/test_semantic_analyzer.py" not in combined and "not found" in combined:
                    errors.append(
                        f"{wid}: pytest may have wrong path: {cmd!r}\nstderr: {(r.stderr or '')[:500]}"
                    )

    if errors:
        for e in errors:
            print("FAIL:", e)
        return 1

    print("OK: Phase 1A e2e verification passed (parsing, paths, commands, WORKER_001 green).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
