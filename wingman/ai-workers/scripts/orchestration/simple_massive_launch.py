#!/usr/bin/env python3
"""
SIMPLIFIED MASSIVE WORKFORCE LAUNCHER
Uses direct Ollama API calls instead of AutoGen
"""

import os
import json
import time
import subprocess
import concurrent.futures
from pathlib import Path
from datetime import datetime

# Configuration
WORK_DIR = Path("/Volumes/intel-system")
OUTPUT_DIR = WORK_DIR / "workforce_output"
LOG_DIR = WORK_DIR / "workforce_logs"

# Create directories
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# WBS Tasks from the document
WBS_TASKS = {
    "foundation": [
        "Install and configure ChromaDB for vector search",
        "Setup Redis with persistence for memory system",
        "Deploy Neo4j container for knowledge graph",
        "Configure document processing pipeline with OCR"
    ],
    "ai_ml": [
        "Install sentence-transformers and download models",
        "Configure LLM serving with Ollama",
        "Setup RAG pipeline with vector search integration",
        "Create embedding service"
    ],
    "api": [
        "Create REST API with Flask/FastAPI",
        "Setup API gateway with rate limiting",
        "Implement WebSocket support",
        "Add authentication middleware"
    ],
    "clients": [
        "Fix Telegram bot configuration",
        "Create web dashboard frontend",
        "Enhance CLI tools",
        "Build monitoring interfaces"
    ],
    "security": [
        "Implement JWT authentication",
        "Configure encryption for data",
        "Setup audit logging",
        "Create backup strategies"
    ]
}

def call_ollama(prompt, model="mistral:7b"):
    """Call Ollama API directly"""
    cmd = [
        "curl", "-s", "http://localhost:11434/api/generate",
        "-d", json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False
        })
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        response = json.loads(result.stdout)
        return response.get("response", "")
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return None

def create_worker_prompt(task, category, output_dir):
    """Create autonomous worker prompt"""
    return f"""You are an expert infrastructure engineer working on Intel-System.

TASK: {task}
CATEGORY: {category}
OUTPUT_DIR: {output_dir}

Create production-ready implementation for this task.
Include:
1. Complete Python/bash scripts
2. Configuration files (YAML/JSON)
3. Documentation in markdown
4. Test scripts

Provide complete, working code. Be specific and detailed.
Format your response as executable code blocks.

BEGIN IMPLEMENTATION:
"""

def execute_task(task_info):
    """Execute a single task"""
    category, task, index = task_info
    worker_name = f"{category}_worker_{index}"
    output_dir = OUTPUT_DIR / category
    output_dir.mkdir(exist_ok=True)

    print(f"🚀 {worker_name}: Starting - {task}")

    # Determine model based on complexity
    model = "codellama:13b" if "configure" in task.lower() or "implement" in task.lower() else "mistral:7b"

    # Generate implementation
    prompt = create_worker_prompt(task, category, output_dir)
    response = call_ollama(prompt, model)

    if response:
        # Save response
        output_file = output_dir / f"{worker_name}_output.md"
        with open(output_file, "w") as f:
            f.write(f"# {task}\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(response)

        print(f"✅ {worker_name}: Completed - Output saved to {output_file}")

        # Log completion
        with open(LOG_DIR / "completions.log", "a") as f:
            f.write(f"{datetime.now().isoformat()},{worker_name},{task},completed\n")
    else:
        print(f"❌ {worker_name}: Failed")

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║     SIMPLIFIED MASSIVE WORKFORCE DEPLOYMENT             ║
╠══════════════════════════════════════════════════════════╣
║  Deploying parallel workers for infrastructure build    ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Check Ollama
    print("🔍 Checking Ollama...")
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Ollama not running. Please start Ollama first.")
        return

    print("✅ Ollama ready")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print(f"📊 Log directory: {LOG_DIR}")
    print()

    # Prepare all tasks
    all_tasks = []
    for category, tasks in WBS_TASKS.items():
        for i, task in enumerate(tasks):
            all_tasks.append((category, task, i))

    print(f"📋 Total tasks: {len(all_tasks)}")
    print("🚀 Starting parallel execution...")
    print()

    # Execute tasks in parallel with thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for task_info in all_tasks:
            future = executor.submit(execute_task, task_info)
            futures.append(future)
            time.sleep(2)  # Stagger starts

        # Wait for completion
        concurrent.futures.wait(futures)

    print()
    print("="*60)
    print("✅ ALL TASKS COMPLETED")
    print("="*60)
    print(f"📁 Outputs saved to: {OUTPUT_DIR}")
    print(f"📊 Logs saved to: {LOG_DIR}")

    # Summary
    total_files = sum(1 for _ in OUTPUT_DIR.rglob("*.md"))
    print(f"📝 Total files generated: {total_files}")

if __name__ == "__main__":
    main()