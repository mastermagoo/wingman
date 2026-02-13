#!/usr/bin/env python3
"""
OPTIMAL AUTOGEN CONFIGURATION
- 13B models for quality
- RAG for context
- Vector search for speed
- Memory for continuity
- Hierarchical summarization
- Active learning
"""

import autogen
import chromadb
import redis
from sentence_transformers import SentenceTransformer
from langchain.memory import ConversationSummaryBufferMemory
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
import os
import json
from datetime import datetime

# Initialize infrastructure
print("🚀 Initializing infrastructure...")

# 1. Redis for memory
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
print("✅ Redis connected")

# 2. ChromaDB for vector search
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("wingman_knowledge")
print("✅ ChromaDB initialized")

# 3. Embeddings model
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'mps'}  # Use Apple Silicon GPU
)
print("✅ Embeddings model loaded")

# 4. Configure models
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

# Worker definitions with specializations
WORKER_SPECS = {
    # Core Architecture (13B - needs quality)
    "Chief_Architect": {
        "model": LOCAL_13B_CONFIG,
        "tasks": ["System design", "API architecture", "Database schema"],
        "skills": ["RAG", "Knowledge Graph", "Vector Search"]
    },

    # Browser Extensions (13B - complex)
    "Extension_Expert": {
        "model": LOCAL_13B_CONFIG,
        "tasks": ["Chrome extension", "Safari extension", "Firefox addon"],
        "skills": ["Manifest V3", "WebExtensions API", "Browser APIs"]
    },

    # ML/NLP Engineer (13B - critical)
    "ML_Engineer": {
        "model": LOCAL_13B_CONFIG,
        "tasks": ["NLP pipeline", "Model training", "RAG implementation"],
        "skills": ["Transformers", "Embeddings", "Fine-tuning"]
    },

    # Frontend (7B - simpler)
    "Frontend_Dev": {
        "model": LOCAL_7B_CONFIG,
        "tasks": ["React dashboard", "UI components", "Styling"],
        "skills": ["React", "TypeScript", "Tailwind"]
    },

    # Backend API (7B - straightforward)
    "Backend_Dev": {
        "model": LOCAL_7B_CONFIG,
        "tasks": ["REST endpoints", "WebSocket server", "Database queries"],
        "skills": ["FastAPI", "PostgreSQL", "Redis"]
    },

    # DevOps (7B - automation)
    "DevOps_Engineer": {
        "model": LOCAL_7B_CONFIG,
        "tasks": ["Docker setup", "CI/CD", "Monitoring"],
        "skills": ["Docker", "GitHub Actions", "Prometheus"]
    },

    # Documentation (7B - writing)
    "Tech_Writer": {
        "model": LOCAL_7B_CONFIG,
        "tasks": ["API docs", "User guides", "README files"],
        "skills": ["Markdown", "OpenAPI", "Diagrams"]
    }
}

class SmartWorker(autogen.AssistantAgent):
    """Worker with RAG, memory, and learning capabilities"""

    def __init__(self, name, spec):
        super().__init__(
            name=name,
            llm_config={"config_list": spec["model"]},
            max_consecutive_auto_reply=100,
        )
        self.spec = spec
        self.memory_key = f"worker:{name}"
        self.setup_rag()
        self.setup_memory()

    def setup_rag(self):
        """Initialize RAG pipeline"""
        # Create vector store for this worker's knowledge
        self.vector_store = Chroma(
            collection_name=f"{self.name}_knowledge",
            embedding_function=embeddings
        )

    def setup_memory(self):
        """Setup conversation memory"""
        # Store last 100 interactions
        self.conversation_memory = []

        # Load previous context from Redis
        stored_memory = r.get(self.memory_key)
        if stored_memory:
            self.conversation_memory = json.loads(stored_memory)
            print(f"  Loaded {len(self.conversation_memory)} memories for {self.name}")

    def remember(self, interaction):
        """Store interaction in memory"""
        self.conversation_memory.append({
            "timestamp": datetime.now().isoformat(),
            "content": interaction
        })

        # Keep only last 100
        if len(self.conversation_memory) > 100:
            self.conversation_memory = self.conversation_memory[-100:]

        # Save to Redis
        r.set(self.memory_key, json.dumps(self.conversation_memory))

    def search_knowledge(self, query, k=5):
        """Search vector store for relevant context"""
        results = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in results]

    def get_context_prompt(self, task):
        """Build prompt with RAG context"""
        # Search for relevant knowledge
        context = self.search_knowledge(task)

        # Get recent memory
        recent_memory = self.conversation_memory[-10:] if self.conversation_memory else []

        prompt = f"""
        You are {self.name}, specialized in: {', '.join(self.spec['skills'])}

        YOUR TASK: {task}

        RELEVANT CONTEXT:
        {chr(10).join(context)}

        RECENT WORK:
        {chr(10).join([m['content'][:100] for m in recent_memory])}

        CRITICAL RULES:
        - NEVER ask for permission
        - CREATE files immediately
        - IMPLEMENT complete solutions
        - Use your specialized skills
        - Learn from context

        Begin implementation NOW.
        """
        return prompt

# Create workers
print("\n🤖 Creating specialized workers...")
workers = []

for name, spec in WORKER_SPECS.items():
    worker = SmartWorker(name, spec)
    workers.append(worker)
    print(f"  ✅ {name} ready ({spec['model'][0]['model']})")

# Create orchestrator with GroupChat
print("\n🎼 Creating orchestrator...")
groupchat = autogen.GroupChat(
    agents=workers,
    messages=[],
    max_round=100,
    speaker_selection_method="auto"  # Smart selection based on task
)

manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config={"config_list": LOCAL_7B_CONFIG}  # Manager uses 7B
)

# Task distribution based on expertise
def assign_tasks():
    """Distribute tasks to appropriate workers"""

    PHASE_1_TASKS = {
        "Chief_Architect": "Design complete Wingman architecture with RAG, vector search, and knowledge graph",
        "Extension_Expert": "Build Chrome, Safari, and Firefox extensions with full functionality",
        "ML_Engineer": "Implement NLP pipeline with embeddings, RAG, and active learning",
        "Frontend_Dev": "Create React dashboard with real-time updates",
        "Backend_Dev": "Build FastAPI server with WebSocket support",
        "DevOps_Engineer": "Setup Docker containers and CI/CD pipeline",
        "Tech_Writer": "Document all APIs and create user guides"
    }

    print("\n📋 Assigning tasks to workers...")
    for worker_name, task in PHASE_1_TASKS.items():
        worker = next(w for w in workers if w.name == worker_name)
        prompt = worker.get_context_prompt(task)

        print(f"\n  {worker_name}: {task[:50]}...")

        # Worker starts immediately
        manager.initiate_chat(
            worker,
            message=prompt,
            clear_history=False  # Keep memory
        )

# Monitoring function
def monitor_progress():
    """Real-time progress monitoring"""
    print("\n📊 Progress Monitor:")
    for worker in workers:
        memory_size = len(worker.conversation_memory)
        print(f"  {worker.name}: {memory_size} tasks completed")

# Active learning
def learn_from_feedback(worker_name, feedback):
    """System learns from corrections"""
    worker = next(w for w in workers if w.name == worker_name)

    # Store feedback in vector store
    worker.vector_store.add_texts(
        texts=[feedback],
        metadatas=[{"type": "feedback", "timestamp": datetime.now().isoformat()}]
    )

    # Remember for future
    worker.remember(f"LEARNING: {feedback}")

    print(f"✅ {worker_name} learned: {feedback[:50]}...")

# Hierarchical summarization
def generate_summary(level="daily"):
    """Create summaries at different levels"""
    summaries = {}

    for worker in workers:
        if level == "daily":
            recent = worker.conversation_memory[-20:]
        elif level == "weekly":
            recent = worker.conversation_memory[-100:]
        else:  # monthly
            recent = worker.conversation_memory

        if recent:
            summary = f"{worker.name}: Completed {len(recent)} tasks"
            summaries[worker.name] = summary

    return summaries

# Main execution
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 WINGMAN MASSIVE PARALLEL DEVELOPMENT")
    print("="*60)

    print(f"""
    Configuration:
    - Workers: {len(workers)} specialized
    - Models: 3×13B (complex) + 4×7B (simple)
    - Infrastructure: ChromaDB + Redis + RAG
    - Memory: Persistent across sessions
    - Learning: Active feedback loop
    """)

    # Start the orchestra!
    print("\n🎭 Starting parallel execution...")
    assign_tasks()

    # Monitor
    monitor_progress()

    # Generate summary
    summary = generate_summary("daily")
    print(f"\n📊 Daily Summary: {json.dumps(summary, indent=2)}")

    print("\n✅ All workers launched with full infrastructure!")
    print("   Monitor logs: tail -f worker_*.log")
    print("   Check progress: python optimal_autogen_workers.py --status")