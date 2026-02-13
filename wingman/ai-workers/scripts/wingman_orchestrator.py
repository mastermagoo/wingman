#!/usr/bin/env python3
"""
WINGMAN AUTONOMOUS WORKFORCE ORCHESTRATOR
Adapted from intel-system for Wingman's 225 workers

Key adaptations:
- Reads .md worker instructions (10-point framework)
- Multi-LLM support: OpenAI (203 workers) + Ollama (22 workers)
- Validates against SUCCESS_CRITERIA from each worker
- Stores retrospectives in mem0 (namespace: wingman)
- Anti-guide detection ("Step 1:", "TODO:", "implement")
- Parallel execution: 50 workers at a time
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional

from openai import OpenAI
import requests


class WorkerStatus(Enum):
    """Worker execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    GUIDE_DETECTED = "guide_detected"
    ROLLED_BACK = "rolled_back"


@dataclass
class WorkerInstruction:
    """Parsed worker instruction from .md file"""
    worker_id: str
    worker_name: str
    file_path: Path
    deliverables: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    boundaries: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    mitigation: Dict[str, str] = field(default_factory=dict)
    test_process: List[str] = field(default_factory=list)
    test_results_format: Dict[str, Any] = field(default_factory=dict)
    task_classification: str = "MECHANICAL"
    retrospective: Dict[str, Any] = field(default_factory=dict)
    performance_requirements: Dict[str, Any] = field(default_factory=dict)
    raw_content: str = ""


@dataclass
class WorkerExecution:
    """Runtime execution state for a worker"""
    instruction: WorkerInstruction
    status: WorkerStatus = WorkerStatus.PENDING
    llm_provider: str = "openai"  # "openai" or "ollama"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    output: str = ""
    errors: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    deliverables_created: List[str] = field(default_factory=list)
    retrospective_stored: bool = False


class WingmanOrchestrator:
    """
    WINGMAN AUTONOMOUS WORKFORCE ORCHESTRATOR
    - 225 workers (203 OpenAI + 22 Ollama)
    - Parallel execution (50 workers at a time)
    - Real-time monitoring (60-second intervals)
    - Anti-guide detection
    - mem0 retrospective storage
    """

    def __init__(self, workers_dir: Path, results_dir: Path, repo_root: Optional[Path] = None):
        self.workers_dir = Path(workers_dir)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True, parents=True)
        self.repo_root = Path(repo_root or Path.cwd())
        if not self.workers_dir.is_absolute():
            self.workers_dir = self.repo_root / self.workers_dir
        if not self.results_dir.is_absolute():
            self.results_dir = self.repo_root / self.results_dir

        # API configuration - using intel-system's LLM infrastructure
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        # Intel-system LLM endpoints (intelligent routing + fallback)
        self.intel_llm_processor = os.getenv("INTEL_LLM_PROCESSOR", "http://localhost:18027")
        self.ollama_endpoint = self.intel_llm_processor  # Use intel-system's LLM processor
        self.mem0_api_url = os.getenv("MEM0_API_URL", "http://127.0.0.1:18888")
        self.mem0_user_id = os.getenv("MEM0_USER_ID", "wingman")

        # Execution state
        self.worker_instructions: Dict[str, WorkerInstruction] = {}
        self.worker_executions: Dict[str, WorkerExecution] = {}
        self.execution_queue = asyncio.Queue()
        self.completed_workers: List[str] = []
        self.failed_workers: List[str] = []

        # Anti-guide detection patterns
        self.guide_keywords = ["Step 1:", "TODO:", "implement", "I'll", "I'm", "Let me", "Here's how"]

        # Batch configuration; Tier 4 = lower RPM, use conservative batch to avoid 429
        self.openai_tier = int(os.getenv("OPENAI_TIER", "0"))
        self.batch_size = 50
        if self.openai_tier == 4:
            self.batch_size = int(os.getenv("OPENAI_TIER4_BATCH_SIZE", "5"))
        self.monitoring_interval = 60  # seconds
        self.tier4_stagger_seconds = float(os.getenv("OPENAI_TIER4_STAGGER_SECONDS", "2.0"))

        print(f"🚀 WINGMAN ORCHESTRATOR INITIALIZED")
        print(f"   Workers dir: {self.workers_dir}")
        print(f"   Results dir: {self.results_dir}")
        print(f"   OpenAI: {'✅' if self.openai_api_key else '❌'}")
        if self.openai_tier == 4:
            print(f"   OpenAI Tier 4: batch_size={self.batch_size}, stagger={self.tier4_stagger_seconds}s (set OPENAI_TIER4_BATCH_SIZE / OPENAI_TIER4_STAGGER_SECONDS to override)")
        print(f"   Intel-system LLM Processor: {self.intel_llm_processor}")
        print(f"   mem0: {self.mem0_api_url} (namespace: {self.mem0_user_id})")
        print(f"   Using shared host Ollama via intel-system (10 models)")

    def load_worker_instructions(self, pattern: str = "WORKER_*.md", worker_ids: Optional[List[str]] = None):
        """Load worker instruction files. If worker_ids is set, only load those (e.g. WORKER_001..WORKER_018)."""
        print(f"\n📋 LOADING WORKER INSTRUCTIONS...")

        if worker_ids is not None:
            worker_files = []
            for wid in worker_ids:
                # Find file matching WORKER_NNN_*.md
                matches = list(self.workers_dir.glob(f"{wid}_*.md"))
                if matches:
                    worker_files.append(matches[0])
                else:
                    print(f"   ⚠️ No file for {wid}")
            worker_files = sorted(worker_files, key=lambda p: p.name)
        else:
            worker_files = sorted(self.workers_dir.glob(pattern))
        print(f"   Found {len(worker_files)} worker files")

        for file_path in worker_files:
            try:
                instruction = self.parse_worker_instruction(file_path)
                self.worker_instructions[instruction.worker_id] = instruction
                print(f"   ✅ {instruction.worker_id}: {instruction.worker_name}")
            except Exception as e:
                print(f"   ❌ {file_path.name}: {e}")

        print(f"\n✅ Loaded {len(self.worker_instructions)} worker instructions")
        return len(self.worker_instructions)

    def parse_worker_instruction(self, file_path: Path) -> WorkerInstruction:
        """Parse worker instruction .md file (10-point framework)"""
        content = file_path.read_text()

        # Extract worker ID and name from filename
        # Format: WORKER_001_Semantic_Class_Skeleton.md
        match = re.match(r'WORKER_(\d+)_(.+)\.md', file_path.name)
        if not match:
            raise ValueError(f"Invalid worker filename format: {file_path.name}")

        worker_id = f"WORKER_{match.group(1)}"
        worker_name = match.group(2).replace('_', ' ')

        instruction = WorkerInstruction(
            worker_id=worker_id,
            worker_name=worker_name,
            file_path=file_path,
            raw_content=content
        )

        # Parse 10-point framework sections
        sections = {
            "1. DELIVERABLES": "deliverables",
            "2. SUCCESS_CRITERIA": "success_criteria",
            "3. BOUNDARIES": "boundaries",
            "4. DEPENDENCIES": "dependencies",
            "5. MITIGATION": "mitigation",
            "6. TEST_PROCESS": "test_process",
            "7. TEST_RESULTS_FORMAT": "test_results_format",
            "8. TASK_CLASSIFICATION": "task_classification",
            "9. RETROSPECTIVE": "retrospective",
            "10. PERFORMANCE_REQUIREMENTS": "performance_requirements"
        }

        for section_header, attr_name in sections.items():
            section_content = self.extract_section(content, section_header)
            if section_content:
                setattr(instruction, attr_name, section_content)

        return instruction

    def extract_section(self, content: str, header: str) -> Any:
        """Extract content between section headers"""
        pattern = rf"##\s*{re.escape(header)}(.*?)(?=##\s*\d+\.|---|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            section_text = match.group(1).strip()

            # Parse lists (lines starting with -, [ ], or bullet points)
            if header in ["1. DELIVERABLES", "2. SUCCESS_CRITERIA", "4. DEPENDENCIES"]:
                lines = [line.strip().lstrip('-•[]✓✗').strip()
                         for line in section_text.split('\n')
                         if line.strip() and not line.strip().startswith('#')]
                return [line for line in lines if line]

            # Parse code blocks for TEST_PROCESS (coalesce multi-line python -c "..." / '...')
            if header == "6. TEST_PROCESS":
                code_blocks = re.findall(r'```(?:bash)?\n(.*?)\n```', section_text, re.DOTALL)
                if code_blocks:
                    commands = []
                    for block in code_blocks:
                        lines = [ln.strip() for ln in block.split('\n') if ln.strip() and not ln.strip().startswith('#')]
                        i = 0
                        while i < len(lines):
                            line = lines[i]
                            # Multi-line: python3 -c " or python3 -c ' when closing quote not on same line (or only one quote = opening)
                            if re.match(r'python3\s+-c\s+["\']', line):
                                q = '"' if line.split('-c', 1)[1].strip()[0] == '"' else "'"
                                if line.count(q) < 2 or not re.search(rf'\{q}\s*(#.*)?$', line.rstrip()):
                                    buf = [line]
                                    i += 1
                                    while i < len(lines) and not re.search(rf'\{q}\s*(#.*)?$', lines[i].rstrip()):
                                        buf.append(lines[i])
                                        i += 1
                                    if i < len(lines):
                                        buf.append(lines[i])
                                        i += 1
                                    commands.append('\n'.join(buf))
                                    continue
                            commands.append(line)
                            i += 1
                    return commands

            # Parse JSON for TEST_RESULTS_FORMAT
            if header == "7. TEST_RESULTS_FORMAT":
                json_match = re.search(r'```json\n(.*?)\n```', section_text, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        pass

            # Default: return raw text
            return section_text

        return None

    async def execute_workers(self, worker_ids: List[str] = None, batch_size: int = None):
        """Execute workers in parallel batches"""
        if worker_ids is None:
            worker_ids = list(self.worker_instructions.keys())

        if batch_size is None:
            batch_size = self.batch_size

        print(f"\n🚀 EXECUTING {len(worker_ids)} WORKERS IN BATCHES OF {batch_size}")

        # Assign LLM providers (203 OpenAI, 22 Ollama)
        for i, worker_id in enumerate(worker_ids):
            instruction = self.worker_instructions[worker_id]
            # Last 22 workers use Ollama, rest use OpenAI
            llm_provider = "ollama" if i >= 203 else "openai"

            execution = WorkerExecution(
                instruction=instruction,
                llm_provider=llm_provider
            )
            self.worker_executions[worker_id] = execution

        # Execute in batches
        batches = [worker_ids[i:i + batch_size] for i in range(0, len(worker_ids), batch_size)]

        for batch_num, batch_ids in enumerate(batches, 1):
            print(f"\n📦 BATCH {batch_num}/{len(batches)}: {len(batch_ids)} workers")
            await self.execute_batch(batch_ids)

        self._print_sorted_summary()

    async def execute_batch(self, worker_ids: List[str]):
        """Execute a batch of workers in parallel. Tier 4: stagger starts to avoid RPM burst."""
        if self.openai_tier == 4 and self.tier4_stagger_seconds > 0:
            tasks = []
            for i, worker_id in enumerate(worker_ids):
                tasks.append(asyncio.create_task(self._execute_worker_after_delay(worker_id, i * self.tier4_stagger_seconds)))
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            tasks = [self.execute_worker(worker_id) for worker_id in worker_ids]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_worker_after_delay(self, worker_id: str, delay: float):
        """Run execute_worker after delay (for Tier 4 staggering)."""
        if delay > 0:
            await asyncio.sleep(delay)
        await self.execute_worker(worker_id)

    def _print_sorted_summary(self):
        """Print sorted summary: Completed (X), then Failed (Y) grouped by GUIDE DETECTED / VALIDATION FAILED / ERROR."""
        completed = sorted(self.completed_workers)
        failed = sorted(self.failed_workers)
        guide_detected = []
        validation_failed = []
        error_other = []
        for wid in failed:
            ex = self.worker_executions.get(wid)
            if not ex:
                error_other.append(wid)
                continue
            if ex.status == WorkerStatus.GUIDE_DETECTED:
                guide_detected.append(wid)
            elif ex.status == WorkerStatus.FAILED:
                err_str = " ".join(ex.errors) if ex.errors else ""
                if "Validation failed" in err_str:
                    validation_failed.append(wid)
                else:
                    error_other.append(wid)
            else:
                error_other.append(wid)
        print(f"\n✅ EXECUTION COMPLETE")
        print(f"   Completed: {len(completed)}")
        if completed:
            print(f"      {', '.join(completed)}")
        print(f"   Failed: {len(failed)}")
        if failed:
            if guide_detected:
                print(f"      GUIDE DETECTED: {', '.join(guide_detected)}")
            if validation_failed:
                print(f"      VALIDATION FAILED: {', '.join(validation_failed)}")
            if error_other:
                print(f"      ERROR: {', '.join(error_other)}")

    async def execute_worker(self, worker_id: str):
        """Execute a single worker"""
        execution = self.worker_executions[worker_id]
        instruction = execution.instruction

        print(f"\n🔧 {worker_id}: {instruction.worker_name}")
        print(f"   LLM: {execution.llm_provider}")

        execution.status = WorkerStatus.IN_PROGRESS
        execution.start_time = datetime.now()

        try:
            # Generate code using LLM
            if execution.llm_provider == "openai":
                code = await self.generate_code_openai(instruction)
            else:
                code = await self.generate_code_ollama(instruction)

            # Anti-guide detection
            if self.detect_guide(code):
                execution.status = WorkerStatus.GUIDE_DETECTED
                execution.end_time = datetime.now()
                execution.duration_seconds = (execution.end_time - execution.start_time).total_seconds()
                execution.errors.append("GUIDE DETECTED: Output contains guide keywords instead of code")
                print(f"   ❌ GUIDE DETECTED")
                self.failed_workers.append(worker_id)
                await self.write_worker_result(execution)
                return

            # Write code to file
            execution.output = code
            execution.deliverables_created = await self.write_deliverables(instruction, code)

            # Validate against SUCCESS_CRITERIA
            execution.status = WorkerStatus.VALIDATING
            test_results = await self.validate_worker(instruction)
            execution.test_results = test_results

            if test_results.get("all_passed", False):
                execution.status = WorkerStatus.COMPLETED
                execution.end_time = datetime.now()
                execution.duration_seconds = (execution.end_time - execution.start_time).total_seconds()
                self.completed_workers.append(worker_id)

                # Store retrospective in mem0
                await self.store_retrospective(execution)

                print(f"   ✅ COMPLETED ({execution.duration_seconds:.1f}s)")
            else:
                execution.status = WorkerStatus.FAILED
                execution.end_time = datetime.now()
                execution.duration_seconds = (execution.end_time - execution.start_time).total_seconds()
                execution.errors.append(f"Validation failed: {test_results}")
                self.failed_workers.append(worker_id)
                print(f"   ❌ VALIDATION FAILED")

        except Exception as e:
            execution.status = WorkerStatus.FAILED
            execution.end_time = datetime.now()
            execution.duration_seconds = (execution.end_time - execution.start_time).total_seconds() if execution.start_time else 0.0
            execution.errors.append(str(e))
            self.failed_workers.append(worker_id)
            print(f"   ❌ ERROR: {e}")

        # Always write per-worker result to results/workers/WORKER_NNN.json (README / full workflow)
        await self.write_worker_result(execution)

    def _read_current_deliverable(self, raw_path: str) -> str:
        """Read current content of deliverable file if it exists. Returns empty string if not found."""
        p = self._deliverable_path(raw_path.strip())
        if p.exists() and p.is_file():
            return p.read_text()
        return ""

    async def generate_code_openai(self, instruction: WorkerInstruction) -> str:
        """Generate code using OpenAI API"""
        # Extract file path from deliverables to determine correct import structure
        file_path = None
        for deliverable in instruction.deliverables:
            path_match = re.search(r'`(.*?\.py)`', deliverable)
            if path_match:
                file_path = path_match.group(1)
                break

        import_hint = ""
        if file_path:
            if "test_" in file_path:
                # Test file - specify correct import paths
                import_hint = f"""
IMPORTANT - Import Structure:
- File location: {file_path}
- For imports from validation/, use: from validation.module_name import ClassName
- For imports from wingman/, use: from wingman.module_name import ClassName
- Example: from validation.semantic_analyzer import SemanticAnalyzer
"""
            else:
                # Implementation file
                import_hint = f"""
IMPORTANT - Module Structure:
- File location: {file_path}
- This module will be imported by tests
- Use standard library imports and local relative imports only
"""

        # Inject current file content for incremental workers so LLM preserves and extends
        current_content = self._read_current_deliverable(file_path) if file_path else ""
        if current_content.strip():
            current_block = f"""
CURRENT FILE CONTENT (you MUST preserve this and add your changes; do NOT remove existing code):
```python
{current_content}
```
Output the COMPLETE updated file with your additions. Preserve all existing imports, classes, and methods.
"""
        else:
            current_block = "\n(File does not exist yet — create it from scratch.)\n"

        prompt = f"""You are a code generator for Wingman validation enhancement.

Worker: {instruction.worker_id} - {instruction.worker_name}

DELIVERABLES:
{chr(10).join(instruction.deliverables)}

SUCCESS_CRITERIA:
{chr(10).join(instruction.success_criteria)}

BOUNDARIES:
{instruction.boundaries}
{import_hint}
{current_block}
Generate ONLY executable Python code for the single deliverable file. NO explanations, NO guides, NO comments like "Step 1" or "TODO".
Do NOT output multiple files, JSON, or test results — only the Python code for the deliverable.
Output must be complete, working code that satisfies ALL success criteria.

CODE:"""

        max_attempts = 3
        backoff_seconds = [2, 4, 8]
        last_error = None
        for attempt in range(max_attempts):
            try:
                response = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert Python code generator. Output ONLY code, no explanations."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_completion_tokens=4000,
                )
                break
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                retryable = "rate" in err_str or "429" in err_str or "500" in err_str or "502" in err_str or "503" in err_str or "timeout" in err_str or "connection" in err_str
                if retryable and attempt < max_attempts - 1:
                    wait = backoff_seconds[attempt]
                    print(f"   ⚠️ OpenAI transient error, retry in {wait}s ({attempt + 1}/{max_attempts}): {e}")
                    await asyncio.sleep(wait)
                else:
                    raise
        else:
            if last_error is not None:
                raise last_error

        code = response.choices[0].message.content.strip()

        # Extract code from markdown blocks if present
        if "```python" in code:
            code = re.search(r'```python\n(.*?)\n```', code, re.DOTALL).group(1)

        return code

    def _extract_deliverable_content(self, full_output: str, target_path: str) -> str:
        """Extract content for target_path from LLM output that may contain multiple '# File: path' sections.
        LLMs sometimes output multiple files concatenated; we write only the block for our deliverable."""
        target = target_path.strip()
        target_basename = target.split('/')[-1]
        # Split by "# File: path" markers (with optional leading newline)
        parts = re.split(r'\n#\s*File:\s*', full_output, flags=re.IGNORECASE)
        for part in parts:
            if not part.strip():
                continue
            first_line, _, rest = part.partition('\n')
            path_in_block = first_line.strip().lstrip('#').strip()
            if path_in_block == target or path_in_block.endswith(target_basename):
                content = rest.strip() if rest else ""
                # Truncate at next # File: if present
                if "\n# File:" in content.lower():
                    content = content.split("\n# File:")[0].strip()
                return content or full_output
        return full_output

    async def generate_code_ollama(self, instruction: WorkerInstruction) -> str:
        """Generate code using intel-system's LLM Processor"""
        # Extract file path for import hints
        file_path = None
        for deliverable in instruction.deliverables:
            path_match = re.search(r'`(.*?\.py)`', deliverable)
            if path_match:
                file_path = path_match.group(1)
                break

        import_hint = ""
        if file_path and "test_" in file_path:
            import_hint = "\nImports: Use 'from validation.module_name import ClassName' for validation modules."

        prompt = f"""PYTHON CODE ONLY. NO EXPLANATIONS.

{instruction.worker_name}

Deliverables:
{chr(10).join(instruction.deliverables)}
{import_hint}

Code:"""

        # Use intel-system LLM Processor endpoint (provides intelligent routing)
        payload = {
            "prompt": prompt,
            "model": "codellama:13b",  # Use proven codellama for code generation
            "max_tokens": 4000
        }

        response = await asyncio.to_thread(
            requests.post,
            f"{self.intel_llm_processor}/generate",
            json=payload,
            timeout=300
        )

        result = response.json()
        code = result.get("text", result.get("response", ""))  # Support multiple response formats

        return code

    def detect_guide(self, code: str) -> bool:
        """Detect if output is a guide instead of code"""
        for keyword in self.guide_keywords:
            if keyword.lower() in code.lower()[:500]:  # Check first 500 chars
                return True
        return False

    def _deliverable_path(self, raw_path: str) -> Path:
        """Resolve deliverable path relative to repo root (instructions use repo-root-relative paths)."""
        return self.repo_root / raw_path.strip()

    async def write_deliverables(self, instruction: WorkerInstruction, code: str) -> List[str]:
        """Write generated code to deliverable files (paths from instructions, resolved from repo root). Returns repo-relative path(s) written."""
        written = []
        for deliverable in instruction.deliverables:
            path_match = re.search(r'`(.*?\.py)`', deliverable)
            if path_match:
                raw = path_match.group(1).strip()
                content = self._extract_deliverable_content(code, raw)
                file_path = self._deliverable_path(raw)
                print(f"   📝 Writing to: {file_path}")
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
                written.append(raw)
                break  # Only write once per worker
        return written

    async def validate_worker(self, instruction: WorkerInstruction) -> Dict[str, Any]:
        """Validate worker output against SUCCESS_CRITERIA (runs from repo root; commands from instructions as-is)."""
        results = {"all_passed": True, "tests": []}
        test_commands = instruction.test_process if isinstance(instruction.test_process, list) else []
        # Use venv Python for validation (so requests etc. are available)
        env = os.environ.copy()
        venv_bin = Path(sys.executable).resolve().parent
        env["PATH"] = str(venv_bin) + os.pathsep + env.get("PATH", "")

        for test_cmd in test_commands:
            cmd = test_cmd.strip()
            if not cmd:
                continue
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.repo_root,
                    env=env
                )
                passed = result.returncode == 0
                results["tests"].append({
                    "command": cmd,
                    "passed": passed,
                    "output": result.stdout if passed else result.stderr
                })
                if not passed:
                    results["all_passed"] = False
            except Exception as e:
                results["tests"].append({
                    "command": cmd,
                    "passed": False,
                    "error": str(e)
                })
                results["all_passed"] = False

        return results

    async def write_worker_result(self, execution: WorkerExecution):
        """Write per-worker result to results/workers/WORKER_NNN.json (full workflow; README)."""
        instruction = execution.instruction
        workers_dir = self.results_dir / "workers"
        workers_dir.mkdir(parents=True, exist_ok=True)
        out_path = workers_dir / f"{instruction.worker_id}.json"
        payload = {
            "worker_id": instruction.worker_id,
            "worker_name": instruction.worker_name,
            "status": execution.status.value,
            "deliverables_created": getattr(execution, "deliverables_created", []) or [],
            "test_results": execution.test_results,
            "duration_seconds": execution.duration_seconds,
            "timestamp": execution.end_time.isoformat() if execution.end_time else None,
            "llm_provider": execution.llm_provider,
            "errors": execution.errors,
        }
        try:
            out_path.write_text(json.dumps(payload, indent=2))
        except Exception as e:
            print(f"   ⚠️ Result write failed: {e}")

    async def store_retrospective(self, execution: WorkerExecution):
        """Store worker retrospective in mem0"""
        instruction = execution.instruction
        retrospective_data = {
            "worker_id": instruction.worker_id,
            "worker_name": instruction.worker_name,
            "duration_seconds": execution.duration_seconds,
            "llm_provider": execution.llm_provider,
            "timestamp": datetime.now().isoformat(),
            "deliverables_created": execution.deliverables_created,
            "test_results": execution.test_results
        }

        payload = {
            "messages": [{"role": "user", "content": json.dumps(retrospective_data)}],
            "user_id": self.mem0_user_id
        }

        try:
            response = await asyncio.to_thread(
                requests.post,
                f"{self.mem0_api_url}/memories",
                json=payload,
                timeout=10
            )
            execution.retrospective_stored = response.status_code == 200
        except Exception as e:
            print(f"   ⚠️ mem0 storage failed: {e}")


def parse_worker_range(s: str) -> List[str]:
    """Parse '001-018' or '1-18' into list of worker IDs WORKER_001..WORKER_018."""
    s = s.strip()
    if "-" in s:
        a, b = s.split("-", 1)
        start = int(a.strip())
        end = int(b.strip())
        return [f"WORKER_{i:03d}" for i in range(start, end + 1)]
    return [f"WORKER_{int(s):03d}"]


async def main():
    """Main entry point. Run from repo root."""
    import argparse
    parser = argparse.ArgumentParser(description="Wingman orchestrator: run AI workers from ai-workers/workers")
    parser.add_argument("--workers", type=str, default=None,
                        help="Worker range, e.g. 001-018 (Phase 1A) or 001-035. Default: all loaded.")
    parser.add_argument("--phase", type=str, default=None,
                        help="Phase shortcut: 1a = 001-018 (Semantic Analyzer).")
    parser.add_argument("--batch-size", type=int, default=50, help="Parallel batch size (default 50)")
    args = parser.parse_args()

    # Repo root is derived from this script's path (ai-workers/scripts/wingman_orchestrator.py), not cwd.
    _script_dir = Path(__file__).resolve().parent
    repo_root = _script_dir.parent.parent
    workers_dir = repo_root / "ai-workers" / "workers"
    results_dir = repo_root / "ai-workers" / "results"
    if not workers_dir.is_dir():
        print("ERROR: ai-workers/workers not found. Repo root:", repo_root)
        return
    orchestrator = WingmanOrchestrator(workers_dir, results_dir, repo_root=repo_root)

    worker_ids = None
    if args.phase and args.phase.lower() == "1a":
        worker_ids = [f"WORKER_{i:03d}" for i in range(1, 19)]
        print(f"Phase 1A: loading and running {len(worker_ids)} workers (WORKER_001–WORKER_018)")
    elif args.workers:
        worker_ids = parse_worker_range(args.workers)
        print(f"Worker range {args.workers}: loading and running {len(worker_ids)} workers")

    # Phase 1A uses OpenAI for all 18 workers; fail fast if key missing
    if worker_ids and orchestrator.openai_client is None:
        print("ERROR: OPENAI_API_KEY is not set. Phase 1A requires OpenAI for all workers.")
        print("   Export it before running: export OPENAI_API_KEY=sk-...")
        print("   Or copy env.ai-workers.example to .env.ai-workers, set OPENAI_API_KEY, and run: source .env.ai-workers && ./ai-workers/run_orchestrator.sh --phase 1a")
        return

    orchestrator.load_worker_instructions(worker_ids=worker_ids)

    if worker_ids and len(orchestrator.worker_instructions) == 0:
        print("ERROR: No matching workers found.")
        return

    # Phase 1A: strict dependency chain — workers share semantic_analyzer.py and test_semantic_analyzer.py.
    # Parallel execution causes overwrites and validation failures. Force sequential.
    batch_size = args.batch_size
    if args.phase and args.phase.lower() == "1a":
        batch_size = 1
        print("   Phase 1A: running sequentially (batch_size=1) — workers share files")
    elif orchestrator.openai_tier == 4 and args.batch_size == 50:
        batch_size = orchestrator.batch_size
    await orchestrator.execute_workers(worker_ids=worker_ids, batch_size=batch_size)


if __name__ == "__main__":
    asyncio.run(main())
