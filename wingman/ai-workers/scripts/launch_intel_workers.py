#!/usr/bin/env python3
"""
INTEL-SYSTEM ENHANCEMENT WITH AUTOGEN
- Focus on intelligence system core capabilities
- CodeLlama 13B for complex tasks
- Full RAG/Vector/Memory infrastructure
- Autonomous execution
"""

import os
import sys
import autogen_agentchat as autogen
import chromadb
import redis
from sentence_transformers import SentenceTransformer
import json
from datetime import datetime

# Initialize infrastructure
print("🚀 Initializing INTEL-SYSTEM infrastructure...")

# 1. Redis for memory
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print("✅ Redis connected")
except:
    print("⚠️ Redis not available, continuing without memory")
    r = None

# 2. ChromaDB for vector search
try:
    chroma_client = chromadb.Client()
    collection = chroma_client.create_collection("intel_system_knowledge")
    print("✅ ChromaDB initialized")
except:
    print("⚠️ ChromaDB already exists, using existing")
    chroma_client = chromadb.Client()
    collection = chroma_client.get_collection("intel_system_knowledge")

# 3. Embeddings model
print("Loading embeddings model...")
embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Embeddings model loaded")

# 4. Configure models - 13B for complex, 7B for simple
LOCAL_13B_CONFIG = [{
    "model": "codellama:13b",
    "base_url": "http://localhost:11434/v1",
    "api_key": "not-needed",
    "temperature": 0.1,
}]

LOCAL_7B_CONFIG = [{
    "model": "mistral:7b",
    "base_url": "http://localhost:11434/v1",
    "api_key": "not-needed",
    "temperature": 0.3,
}]

# INTEL-SYSTEM Enhancement Workers
WORKER_SPECS = {
    # Core Intelligence (13B)
    "Intelligence_Architect": {
        "model": LOCAL_13B_CONFIG,
        "task": "Design enhanced intel-system architecture with full RAG, vector search, knowledge graph, and memory systems",
        "priority": 1
    },
    "RAG_Pipeline_Builder": {
        "model": LOCAL_13B_CONFIG,
        "task": "Build complete RAG pipeline for intel-system that ingests all /Volumes/intel-system docs and code",
        "priority": 1
    },
    "Knowledge_Graph_Engineer": {
        "model": LOCAL_13B_CONFIG,
        "task": "Create Neo4j knowledge graph to map all relationships in intel-system data",
        "priority": 1
    },

    # Infrastructure (7B)
    "Vector_Search_Developer": {
        "model": LOCAL_7B_CONFIG,
        "task": "Implement ChromaDB vector search for all intel-system documents and code",
        "priority": 2
    },
    "Memory_System_Builder": {
        "model": LOCAL_7B_CONFIG,
        "task": "Create Redis-based conversation memory and context management",
        "priority": 2
    },
    "API_Gateway_Creator": {
        "model": LOCAL_7B_CONFIG,
        "task": "Build FastAPI gateway for intel-system with all intelligence endpoints",
        "priority": 3
    },
    "Monitor_Dashboard_Dev": {
        "model": LOCAL_7B_CONFIG,
        "task": "Create monitoring dashboard showing intel-system performance and insights",
        "priority": 4
    }
}

class IntelWorker(autogen.AssistantAgent):
    """Worker for intel-system enhancement"""

    def __init__(self, name, spec):
        system_message = f"""
You are {name}, an autonomous intel-system enhancement worker.
Your task: {spec['task']}

CRITICAL RULES:
- Work in /Volumes/intel-system/
- NEVER ask for permission
- CREATE files immediately
- IMPLEMENT complete solutions
- Update PROJECT_STATUS.md with progress
- Use existing infrastructure (engine/, monitoring/, processor/)
- Enhance, don't replace existing systems

Begin implementation NOW.
        """

        super().__init__(
            name=name,
            llm_config={"config_list": spec["model"]},
            max_consecutive_auto_reply=100,
            system_message=system_message
        )
        self.spec = spec
        self.setup_memory()

    def setup_memory(self):
        """Initialize worker memory"""
        self.memory_key = f"intel_worker:{self.name}"
        self.memory = []

        if r:
            stored = r.get(self.memory_key)
            if stored:
                self.memory = json.loads(stored)
                print(f"  Loaded {len(self.memory)} memories for {self.name}")

    def save_progress(self, task_result):
        """Save progress to memory"""
        progress = {
            "timestamp": datetime.now().isoformat(),
            "task": self.spec['task'],
            "result": task_result
        }
        self.memory.append(progress)

        if r:
            r.set(self.memory_key, json.dumps(self.memory))

# Create workers
print("\n🤖 Creating intel-system enhancement workers...")
workers = []

for name, spec in WORKER_SPECS.items():
    worker = IntelWorker(name, spec)
    workers.append(worker)
    model_type = "13B" if spec["model"] == LOCAL_13B_CONFIG else "7B"
    print(f"  ✅ {name} ready (CodeLlama {model_type})")

# Create user proxy
user_proxy = autogen.UserProxyAgent(
    name="Coordinator",
    human_input_mode="NEVER",  # Full autonomy
    max_consecutive_auto_reply=0,
    code_execution_config={"work_dir": "/Volumes/intel-system/"}
)

# Create group chat
print("\n🎼 Creating orchestrator...")
groupchat = autogen.GroupChat(
    agents=workers + [user_proxy],
    messages=[],
    max_round=100,
    speaker_selection_method="auto"
)

manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config={"config_list": LOCAL_7B_CONFIG}
)

print("\n" + "="*60)
print("🚀 INTEL-SYSTEM MASSIVE ENHANCEMENT")
print("="*60)

print(f"""
Configuration:
- Workers: {len(workers)} specialized
- Models: 3×CodeLlama 13B (complex) + 4×Mistral 7B (infrastructure)
- Infrastructure: ChromaDB + Redis + RAG
- Target: Enhance /Volumes/intel-system/
- Mode: FULLY AUTONOMOUS

Current intel-system structure:
- engine/: LLM processing engine
- processor/: Data processing
- monitoring/: System monitoring
- extractor/: Content extraction
- docs/: Documentation
""")

# Launch the enhancement!
print("\n🎭 Starting intel-system enhancement...")

initial_message = """
ALL WORKERS: Begin enhancing intel-system NOW.

Your workspace: /Volumes/intel-system/

Priority tasks:
1. Add vector search to existing engine/
2. Implement RAG pipeline for all docs/
3. Create knowledge graph of system relationships
4. Add memory layer to processor/
5. Build unified API gateway

Rules:
- Enhance existing code, don't replace
- Create new files in appropriate directories
- Update PROJECT_STATUS.md with progress
- Work autonomously, no approvals needed

START IMMEDIATELY.
"""

user_proxy.initiate_chat(
    manager,
    message=initial_message,
    clear_history=False
)

print("\n✅ Intel-system enhancement workers launched!")
print("\n📊 Monitor progress:")
print("  - Check status: cat /Volumes/intel-system/PROJECT_STATUS.md")
print("  - View logs: tail -f /tmp/intel_worker_*.log")
print("  - System health: redis-cli KEYS 'intel_worker:*'")