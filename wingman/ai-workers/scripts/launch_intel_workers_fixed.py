#!/usr/bin/env python3
"""
FIXED INTEL WORKERS - Direct Ollama Implementation
Works without complex AutoGen dependencies
"""

import os
import json
import subprocess
import time
import threading
from pathlib import Path
from datetime import datetime
import chromadb
import redis
from sentence_transformers import SentenceTransformer

# Initialize infrastructure
print("🚀 Initializing Intel-System Workers...")

# Redis for memory
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print("✅ Redis connected")
except:
    print("⚠️ Redis not running - starting it...")
    subprocess.run(["redis-server", "--daemonize", "yes"])
    time.sleep(2)
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# ChromaDB for vector search
try:
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection("intel_system")
    print("✅ ChromaDB initialized")
except Exception as e:
    print(f"⚠️ ChromaDB: {e}")
    collection = None

# Embeddings model
print("📦 Loading embeddings model...")
embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Embeddings model loaded")

# Worker tasks
WORKER_TASKS = [
    ("VectorDB_Setup", "Create ChromaDB collections and indexes", "codellama:13b"),
    ("Redis_Config", "Setup Redis persistence and memory schemas", "mistral:7b"),
    ("API_Server", "Create Flask API with /verify, /search, /chat endpoints", "codellama:13b"),
    ("RAG_Pipeline", "Build RAG pipeline with vector search", "codellama:13b"),
    ("Docker_Config", "Create docker-compose.yml for all services", "mistral:7b"),
    ("Telegram_Bot", "Setup Telegram bot with command handlers", "mistral:7b"),
    ("Monitoring", "Configure Prometheus and Grafana", "mistral:7b"),
    ("Security", "Implement JWT authentication", "codellama:13b")
]

def call_ollama(prompt, model="mistral:7b"):
    """Direct Ollama API call"""
    cmd = [
        "curl", "-s", "http://localhost:11434/api/generate",
        "-d", json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 1500}
        })
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        response = json.loads(result.stdout)
        return response.get("response", "")
    except Exception as e:
        return f"Error: {e}"

class IntelWorker(threading.Thread):
    """Autonomous worker thread"""

    def __init__(self, name, task, model):
        super().__init__(daemon=True)
        self.name = name
        self.task = task
        self.model = model
        self.output_dir = Path(f"/Volumes/intel-system/workforce_output/{name}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self):
        """Execute worker task"""
        print(f"\n🤖 {self.name} starting...")

        # Generate implementation
        prompt = f"""You are {self.name}, an expert DevOps engineer.

TASK: {self.task}

Generate a complete, production-ready implementation including:
1. All necessary code
2. Configuration files
3. Docker setup if relevant
4. Testing scripts

Output executable code only. Be specific and complete.

IMPLEMENTATION:
"""

        print(f"🧠 {self.name}: Generating with {self.model}...")
        response = call_ollama(prompt, self.model)

        if response and response != "Error":
            # Save implementation
            impl_file = self.output_dir / "implementation.py"
            with open(impl_file, "w") as f:
                f.write(f"# {self.task}\n")
                f.write(f"# Generated: {datetime.now()}\n\n")
                f.write(response)

            print(f"✅ {self.name}: Saved to {impl_file}")

            # Store in Redis
            if r:
                r.hset(f"worker:{self.name}", "status", "completed")
                r.hset(f"worker:{self.name}", "output", str(impl_file))

            # Add to vector DB
            if collection and embeddings_model:
                embedding = embeddings_model.encode(response).tolist()
                collection.add(
                    documents=[response],
                    embeddings=[embedding],
                    ids=[self.name]
                )
        else:
            print(f"❌ {self.name}: Failed to generate")

def main():
    print("\n" + "="*60)
    print("🎯 INTEL-SYSTEM AUTONOMOUS WORKERS")
    print("="*60)

    # Check Ollama
    print("\n🔍 Checking Ollama models...")
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    if "mistral" not in result.stdout or "codellama" not in result.stdout:
        print("⚠️ Loading required models...")
        subprocess.run(["ollama", "pull", "mistral:7b"])
        subprocess.run(["ollama", "pull", "codellama:13b"])
    else:
        print("✅ Models ready")

    # Launch workers
    print(f"\n🚀 Launching {len(WORKER_TASKS)} workers...")
    workers = []

    for name, task, model in WORKER_TASKS:
        worker = IntelWorker(name, task, model)
        worker.start()
        workers.append(worker)
        time.sleep(2)  # Stagger starts

    print("\n⏳ Workers running... Press Ctrl+C to stop")

    # Monitor progress
    try:
        while True:
            active = sum(1 for w in workers if w.is_alive())
            print(f"\r🔄 Active workers: {active}/{len(workers)}", end="")

            if active == 0:
                break
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n⛔ Stopping workers...")

    print("\n\n✅ EXECUTION COMPLETE")
    print(f"📁 Outputs in: /Volumes/intel-system/workforce_output/")

    # Summary
    if r:
        completed = 0
        for name, _, _ in WORKER_TASKS:
            status = r.hget(f"worker:{name}", "status")
            if status == "completed":
                completed += 1
        print(f"📊 Completed: {completed}/{len(WORKER_TASKS)} tasks")

if __name__ == "__main__":
    main()