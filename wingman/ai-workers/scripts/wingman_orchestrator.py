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
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional

import openai
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

    def __init__(self, workers_dir: Path, results_dir: Path):
        self.workers_dir = Path(workers_dir)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True, parents=True)

        # API configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.ollama_endpoint = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
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

        # Batch configuration
        self.batch_size = 50
        self.monitoring_interval = 60  # seconds

        print(f"🚀 WINGMAN ORCHESTRATOR INITIALIZED")
        print(f"   Workers dir: {self.workers_dir}")
        print(f"   Results dir: {self.results_dir}")
        print(f"   OpenAI: {'✅' if self.openai_api_key else '❌'}")
        print(f"   Ollama: {self.ollama_endpoint}")
        print(f"   mem0: {self.mem0_api_url} (namespace: {self.mem0_user_id})")

    def load_worker_instructions(self, pattern: str = "WORKER_*.md"):
        """Load all worker instruction files"""
        print(f"\n📋 LOADING WORKER INSTRUCTIONS...")

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

            # Parse code blocks for TEST_PROCESS
            if header == "6. TEST_PROCESS":
                code_blocks = re.findall(r'```(?:bash)?\n(.*?)\n```', section_text, re.DOTALL)
                if code_blocks:
                    # Split commands by lines
                    commands = []
                    for block in code_blocks:
                        commands.extend([cmd.strip() for cmd in block.split('\n') if cmd.strip() and not cmd.strip().startswith('#')])
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

        print(f"\n✅ EXECUTION COMPLETE")
        print(f"   Completed: {len(self.completed_workers)}")
        print(f"   Failed: {len(self.failed_workers)}")

    async def execute_batch(self, worker_ids: List[str]):
        """Execute a batch of workers in parallel"""
        tasks = [self.execute_worker(worker_id) for worker_id in worker_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

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
                execution.errors.append("GUIDE DETECTED: Output contains guide keywords instead of code")
                print(f"   ❌ GUIDE DETECTED")
                self.failed_workers.append(worker_id)
                return

            # Write code to file
            execution.output = code
            await self.write_deliverables(instruction, code)

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
                execution.errors.append(f"Validation failed: {test_results}")
                self.failed_workers.append(worker_id)
                print(f"   ❌ VALIDATION FAILED")

        except Exception as e:
            execution.status = WorkerStatus.FAILED
            execution.errors.append(str(e))
            self.failed_workers.append(worker_id)
            print(f"   ❌ ERROR: {e}")

    async def generate_code_openai(self, instruction: WorkerInstruction) -> str:
        """Generate code using OpenAI API"""
        prompt = f"""You are a code generator for Wingman validation enhancement.

Worker: {instruction.worker_id} - {instruction.worker_name}

DELIVERABLES:
{chr(10).join(instruction.deliverables)}

SUCCESS_CRITERIA:
{chr(10).join(instruction.success_criteria)}

BOUNDARIES:
{instruction.boundaries}

Generate ONLY executable Python code. NO explanations, NO guides, NO comments like "Step 1" or "TODO".
Output must be complete, working code that satisfies ALL success criteria.

CODE:"""

        response = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert Python code generator. Output ONLY code, no explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )

        code = response.choices[0].message.content.strip()

        # Extract code from markdown blocks if present
        if "```python" in code:
            code = re.search(r'```python\n(.*?)\n```', code, re.DOTALL).group(1)

        return code

    async def generate_code_ollama(self, instruction: WorkerInstruction) -> str:
        """Generate code using Ollama"""
        prompt = f"""PYTHON CODE ONLY. NO EXPLANATIONS.

{instruction.worker_name}

Deliverables:
{chr(10).join(instruction.deliverables)}

Code:"""

        payload = {
            "model": "mistral:7b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 4000
            }
        }

        response = await asyncio.to_thread(
            requests.post,
            f"{self.ollama_endpoint}/api/generate",
            json=payload,
            timeout=300
        )

        result = response.json()
        code = result.get("response", "")

        return code

    def detect_guide(self, code: str) -> bool:
        """Detect if output is a guide instead of code"""
        for keyword in self.guide_keywords:
            if keyword.lower() in code.lower()[:500]:  # Check first 500 chars
                return True
        return False

    async def write_deliverables(self, instruction: WorkerInstruction, code: str):
        """Write generated code to deliverable files"""
        # Extract file paths from deliverables
        for deliverable in instruction.deliverables:
            if deliverable.startswith("Create file:") or deliverable.startswith("Implement"):
                # Extract file path
                path_match = re.search(r'`(.*?\.py)`', deliverable)
                if path_match:
                    file_path = Path(path_match.group(1))
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(code)

    async def validate_worker(self, instruction: WorkerInstruction) -> Dict[str, Any]:
        """Validate worker output against SUCCESS_CRITERIA"""
        results = {"all_passed": True, "tests": []}

        for test_cmd in instruction.test_process:
            try:
                result = subprocess.run(
                    test_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                passed = result.returncode == 0
                results["tests"].append({
                    "command": test_cmd,
                    "passed": passed,
                    "output": result.stdout if passed else result.stderr
                })
                if not passed:
                    results["all_passed"] = False
            except Exception as e:
                results["tests"].append({
                    "command": test_cmd,
                    "passed": False,
                    "error": str(e)
                })
                results["all_passed"] = False

        return results

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


async def main():
    """Main entry point"""
    workers_dir = Path("ai-workers/workers")
    results_dir = Path("ai-workers/results")

    orchestrator = WingmanOrchestrator(workers_dir, results_dir)
    orchestrator.load_worker_instructions()

    # Execute all workers
    await orchestrator.execute_workers()


if __name__ == "__main__":
    asyncio.run(main())
