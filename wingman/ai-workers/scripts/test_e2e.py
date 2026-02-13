#!/usr/bin/env python3
"""
E2E Test: WORKER_001 + WORKER_013
Tests full pipeline: Code generation → Test generation → Validation
"""

import asyncio
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from wingman_orchestrator import WingmanOrchestrator


async def main():
    """Run E2E test with 2 workers"""
    print("=" * 80)
    print("E2E TEST: WORKER_001 (Code) + WORKER_013 (Tests)")
    print("=" * 80)

    # Setup
    workers_dir = Path("ai-workers/workers")
    results_dir = Path("ai-workers/results/e2e_test")

    orchestrator = WingmanOrchestrator(workers_dir, results_dir)

    # Load all workers
    orchestrator.load_worker_instructions()

    # Execute only WORKER_001 and WORKER_013
    test_workers = ["WORKER_001", "WORKER_013"]

    print(f"\n🧪 TESTING {len(test_workers)} WORKERS:")
    for worker_id in test_workers:
        if worker_id in orchestrator.worker_instructions:
            instruction = orchestrator.worker_instructions[worker_id]
            print(f"   ✅ {worker_id}: {instruction.worker_name}")
        else:
            print(f"   ❌ {worker_id}: NOT FOUND")
            return 1

    # Execute workers
    print("\n" + "=" * 80)
    print("STARTING EXECUTION")
    print("=" * 80)

    await orchestrator.execute_workers(
        worker_ids=test_workers,
        batch_size=2  # Both in parallel
    )

    # Results summary
    print("\n" + "=" * 80)
    print("E2E TEST RESULTS")
    print("=" * 80)

    success = True
    for worker_id in test_workers:
        execution = orchestrator.worker_executions[worker_id]
        status = execution.status.value

        if status == "completed":
            print(f"✅ {worker_id}: {status} ({execution.duration_seconds:.1f}s)")
        else:
            print(f"❌ {worker_id}: {status}")
            if execution.errors:
                for error in execution.errors:
                    print(f"   ERROR: {error}")
            success = False

    if success:
        print("\n✅ E2E TEST PASSED - Ready for full execution (225 workers)")
        return 0
    else:
        print("\n❌ E2E TEST FAILED - Fix issues before proceeding")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
