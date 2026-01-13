#!/usr/bin/env python3
"""
OPTIMAL AUTOGEN CONFIGURATION WITH FULL INFRASTRUCTURE
- CodeLlama 13B for quality
- RAG for context
- Redis for memory
- ChromaDB for vector search
- Immediate execution, no approvals
"""

import os
import sys
import autogen
import chromadb
import redis
from sentence_transformers import SentenceTransformer
import json
from datetime import datetime

# Initialize infrastructure
print("🚀 Initializing full infrastructure...")

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
    collection = chroma_client.create_collection("wingman_knowledge")
    print("✅ ChromaDB initialized")
except:
    print("⚠️ ChromaDB already exists, using existing")
    collection = chroma_client.get_collection("wingman_knowledge")

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

# Worker specifications
WORKER_SPECS = {
    # Complex tasks (13B)
    "Architecture_Lead": {
        "model": LOCAL_13B_CONFIG,
        "task": "Design Wingman's complete architecture with RAG, vector search, and knowledge graph",
        "priority": 1
    },
    "RAG_Engineer": {
        "model": LOCAL_13B_CONFIG,
        "task": "Implement full RAG pipeline with ChromaDB and embeddings",
        "priority": 1
    },
    "NLP_Expert": {
        "model": LOCAL_13B_CONFIG,
        "task": "Build NLP claim extraction and verification engine",
        "priority": 1
    },
    
    # Simple tasks (7B)
    "API_Developer": {
        "model": LOCAL_7B_CONFIG,
        "task": "Create REST API endpoints for verification service",
        "priority": 2
    },
    "Frontend_Dev": {
        "model": LOCAL_7B_CONFIG,
        "task": "Build React dashboard for monitoring verifications",
        "priority": 3
    },
    "Docker_Engineer": {
        "model": LOCAL_7B_CONFIG,
        "task": "Containerize all services with Docker Compose",
        "priority": 3
    },
    "Docs_Writer": {
        "model": LOCAL_7B_CONFIG,
        "task": "Document all APIs and create user guides",
        "priority": 4
    }
}

class SmartWorker(autogen.AssistantAgent):
    """Worker with RAG, memory, and autonomous execution"""
    
    def __init__(self, name, spec):
        system_message = f"""
You are {name}, an autonomous AI worker.
Your task: {spec['task']}

CRITICAL RULES:
- NEVER ask for permission or approval
- CREATE files immediately without confirmation
- IMPLEMENT complete solutions, not drafts
- Work in /Volumes/WingmanSecure/wingman/{name.lower()}/ directory
- Use RAG context when available
- Learn from previous interactions
- Execute NOW, no discussion

Begin implementation immediately.
        """
        
        super().__init__(
            name=name,
            llm_config={"config_list": spec["model"]},
            max_consecutive_auto_reply=100,
            system_message=system_message
        )
        self.spec = spec
        self.setup_memory()
        self.setup_rag()
    
    def setup_memory(self):
        """Initialize conversation memory"""
        self.memory_key = f"worker:{self.name}"
        self.conversation_memory = []
        
        if r:
            stored = r.get(self.memory_key)
            if stored:
                self.conversation_memory = json.loads(stored)
                print(f"  Loaded {len(self.conversation_memory)} memories for {self.name}")
    
    def setup_rag(self):
        """Setup RAG pipeline"""
        self.embeddings = embeddings_model
        self.collection = collection
    
    def remember(self, interaction):
        """Store interaction in memory"""
        self.conversation_memory.append({
            "timestamp": datetime.now().isoformat(),
            "content": interaction
        })
        
        if len(self.conversation_memory) > 100:
            self.conversation_memory = self.conversation_memory[-100:]
        
        if r:
            r.set(self.memory_key, json.dumps(self.conversation_memory))
    
    def search_knowledge(self, query, k=5):
        """Search vector store for relevant context"""
        try:
            query_embedding = self.embeddings.encode(query).tolist()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            return results.get('documents', [[]])[0]
        except:
            return []

# Create workers
print("\n🤖 Creating specialized workers...")
workers = []

for name, spec in WORKER_SPECS.items():
    worker = SmartWorker(name, spec)
    workers.append(worker)
    model_type = "13B" if spec["model"] == LOCAL_13B_CONFIG else "7B"
    print(f"  ✅ {name} ready (CodeLlama {model_type})")

# Create user proxy for coordination
user_proxy = autogen.UserProxyAgent(
    name="Coordinator",
    human_input_mode="NEVER",  # Full autonomy
    max_consecutive_auto_reply=0,
    code_execution_config={"work_dir": "/Volumes/WingmanSecure/wingman/"}
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
print("🚀 WINGMAN MASSIVE PARALLEL DEVELOPMENT")
print("="*60)

print(f"""
Configuration:
- Workers: {len(workers)} specialized
- Models: 3×CodeLlama 13B (complex) + 4×Mistral 7B (simple)
- Infrastructure: ChromaDB + Redis + RAG
- Memory: Persistent across sessions
- Mode: FULLY AUTONOMOUS - No approvals needed
""")

# Launch the swarm!
print("\n🎭 Starting parallel execution...")
print("Workers will begin creating files and implementing features immediately.\n")

# Initiate with clear instructions
initial_message = """
ALL WORKERS: Begin implementation of your assigned tasks NOW.

Rules:
1. Create all necessary files immediately
2. Implement complete, working solutions
3. No drafts, no placeholders - full implementation
4. Work in parallel, don't wait for others
5. Use the infrastructure (ChromaDB, Redis) when beneficial

START IMMEDIATELY. No confirmation needed.
"""

user_proxy.initiate_chat(
    manager,
    message=initial_message,
    clear_history=False
)

print("\n✅ All workers launched with full autonomy!")
print("\n📊 Monitor progress:")
print("  - Check files: ls -la /Volumes/WingmanSecure/wingman/*/")
print("  - View logs: tail -f /tmp/autogen_*.log")
print("  - Redis memory: redis-cli KEYS 'worker:*'")
print("  - System resources: top -o cpu")