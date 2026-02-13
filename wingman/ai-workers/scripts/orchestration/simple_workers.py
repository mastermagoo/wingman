#!/usr/bin/env python3
"""
SIMPLE WORKER SYSTEM - No AutoGen Required
Just Python + Ollama for parallel tasks
"""

import subprocess
import threading
import time
import os
from datetime import datetime
import json

class SimpleWorker:
    """Worker that uses Ollama directly"""

    def __init__(self, name, model="mistral:7b"):
        self.name = name
        self.model = model
        self.results = []

    def run_task(self, task):
        """Execute a task using Ollama"""
        print(f"\n🤖 {self.name} starting: {task[:50]}...")

        prompt = f"""You are {self.name}, an AI worker.
Task: {task}

Rules:
- Create complete, working code
- No explanations, just code
- Include all imports
- Make it production-ready

Output:"""

        cmd = f'ollama run {self.model} "{prompt}"'

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )

            output = result.stdout

            # Save to file
            output_file = f"/Volumes/intel-system/outputs/{self.name}_{datetime.now().strftime('%H%M%S')}.py"
            os.makedirs("/Volumes/intel-system/outputs", exist_ok=True)

            with open(output_file, "w") as f:
                f.write(output)

            self.results.append({
                "task": task,
                "output_file": output_file,
                "timestamp": datetime.now().isoformat()
            })

            print(f"✅ {self.name} completed task! Output: {output_file}")

            # Update status
            self.update_status(task, "completed")

            return output

        except Exception as e:
            print(f"❌ {self.name} failed: {e}")
            self.update_status(task, "failed")
            return None

    def update_status(self, task, status):
        """Update PROJECT_STATUS.md"""
        try:
            with open("/Volumes/intel-system/PROJECT_STATUS.md", "a") as f:
                f.write(f"\n- {datetime.now().strftime('%H:%M')} {self.name}: {status} - {task[:50]}")
        except:
            pass

def launch_workers():
    """Launch multiple workers in parallel"""

    print("🚀 LAUNCHING SIMPLE WORKERS")
    print("=" * 50)

    # Define tasks
    tasks = [
        {
            "worker": "RAG_Builder",
            "model": "codellama:13b",
            "task": "Create a RAG pipeline class with ChromaDB integration and search methods"
        },
        {
            "worker": "API_Creator",
            "model": "mistral:7b",
            "task": "Create a FastAPI server with /search and /index endpoints"
        },
        {
            "worker": "Vector_Expert",
            "model": "mistral:7b",
            "task": "Write functions to generate embeddings and store them in ChromaDB"
        },
        {
            "worker": "Memory_Builder",
            "model": "mistral:7b",
            "task": "Create a Redis memory manager class for conversation history"
        }
    ]

    # Create workers
    workers = []
    threads = []

    for task_info in tasks:
        worker = SimpleWorker(task_info["worker"], task_info["model"])
        workers.append(worker)

        # Launch in thread
        thread = threading.Thread(
            target=worker.run_task,
            args=(task_info["task"],)
        )
        thread.start()
        threads.append(thread)

        time.sleep(2)  # Stagger launches

    print(f"\n✅ Launched {len(workers)} workers!")
    print("\nWorkers running in parallel...")
    print("Check /Volumes/intel-system/outputs/ for results")

    # Wait for all to complete
    for thread in threads:
        thread.join()

    print("\n🎉 ALL WORKERS COMPLETED!")

    # Summary
    print("\n📊 SUMMARY:")
    for worker in workers:
        print(f"  {worker.name}: {len(worker.results)} tasks completed")
        for result in worker.results:
            print(f"    - {result['output_file']}")

if __name__ == "__main__":
    # Check models are available
    print("🔍 Checking models...")

    models_check = subprocess.run("ollama list", shell=True, capture_output=True, text=True)
    print(models_check.stdout)

    if "mistral" in models_check.stdout and "codellama:13b" in models_check.stdout:
        print("✅ All models ready!")
        launch_workers()
    else:
        print("❌ Missing models. Please run:")
        print("  ollama pull mistral:7b")
        print("  ollama pull codellama:13b")