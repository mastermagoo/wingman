#!/usr/bin/env python3
"""
LAUNCH 20 AGENTS WITH AUTOGEN
Maximum parallel development
"""

import pyautogen
from pyautogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import os

print("🚀 LAUNCHING 20 AGENTS FOR INTEL-SYSTEM")
print("=" * 60)

# Configure models
LOCAL_13B = [{
    "model": "codellama:13b",
    "base_url": "http://localhost:11434/v1",
    "api_key": "not-needed",
}]

LOCAL_7B = [{
    "model": "mistral:7b",
    "base_url": "http://localhost:11434/v1",
    "api_key": "not-needed",
}]

# Define 20 agents with DETAILED instructions
AGENT_SPECS = {
    # Core Architecture (13B - Complex)
    "Chief_Architect": (LOCAL_13B, """
    Create /Volumes/intel-system/architecture/system_design.py with:
    - Complete class hierarchy for intel-system
    - Integration points for ChromaDB, Redis, TimescaleDB
    - API gateway design pattern
    - Message queue architecture
    """),

    "RAG_Engineer": (LOCAL_13B, """
    Create /Volumes/intel-system/engine/rag_pipeline.py with:
    - RAGPipeline class using ChromaDB
    - Methods: add_document(), search(), get_context()
    - Integration with existing engine/ code
    - Ingest all files from docs/ folder
    """),

    "Knowledge_Graph": (LOCAL_13B, """
    Create /Volumes/intel-system/engine/knowledge_graph.py with:
    - Neo4j integration for relationship mapping
    - Entity extraction from documents
    - Relationship inference algorithms
    - Query interface for graph traversal
    """),

    # Infrastructure (13B)
    "Vector_Search": (LOCAL_13B, """
    Create /Volumes/intel-system/engine/vector_search.py with:
    - ChromaDB collection management
    - Embedding generation with sentence-transformers
    - Similarity search functions
    - Batch indexing for all existing docs
    """),

    "Memory_System": (LOCAL_13B, """
    Create /Volumes/intel-system/processor/memory.py with:
    - Redis connection manager
    - Conversation history storage
    - Context window management
    - Session persistence
    """),

    # API Development (7B)
    "API_Gateway": (LOCAL_7B, """
    Create /Volumes/intel-system/api/gateway.py with:
    - FastAPI main application
    - Route aggregation from all services
    - Authentication middleware
    - Rate limiting
    """),

    "REST_Builder": (LOCAL_7B, """
    Create /Volumes/intel-system/api/rest_endpoints.py with:
    - /search endpoint for vector search
    - /index endpoint for document ingestion
    - /query endpoint for knowledge graph
    - /status endpoint for health checks
    """),

    "WebSocket_Dev": (LOCAL_7B, """
    Create /Volumes/intel-system/api/websocket_server.py with:
    - Real-time streaming responses
    - Bi-directional communication
    - Connection pooling
    - Event broadcasting
    """),

    "GraphQL_API": (LOCAL_7B, """
    Create /Volumes/intel-system/api/graphql_schema.py with:
    - GraphQL schema for intel-system
    - Query resolvers for all data types
    - Mutation handlers
    - Subscription support
    """),

    # Data Processing (7B)
    "ETL_Pipeline": (LOCAL_7B, """
    Create /Volumes/intel-system/processor/etl.py with:
    - Document extraction from multiple formats
    - Data transformation pipeline
    - Loading into vector store
    - Error handling and retry logic
    """),

    "Stream_Processor": (LOCAL_7B, """
    Create /Volumes/intel-system/processor/stream.py with:
    - Real-time data ingestion
    - Stream processing with queues
    - Event-driven architecture
    - Backpressure handling
    """),

    "Batch_Worker": (LOCAL_7B, """
    Create /Volumes/intel-system/processor/batch.py with:
    - Batch processing scheduler
    - Parallel job execution
    - Progress tracking
    - Result aggregation
    """),

    # Frontend (7B)
    "Dashboard_UI": (LOCAL_7B, """
    Create /Volumes/intel-system/frontend/dashboard.html with:
    - React dashboard component
    - Real-time metrics display
    - WebSocket integration
    - Chart visualizations
    """),

    "Admin_Panel": (LOCAL_7B, """
    Create /Volumes/intel-system/frontend/admin.html with:
    - System configuration interface
    - User management
    - Log viewer
    - Performance metrics
    """),

    "Analytics_View": (LOCAL_7B, """
    Create /Volumes/intel-system/frontend/analytics.html with:
    - Data visualization dashboards
    - Query builder interface
    - Export functionality
    - Report generation
    """),

    # Testing & Quality (7B)
    "Test_Engineer": (LOCAL_7B, """
    Create /Volumes/intel-system/tests/test_suite.py with:
    - Unit tests for all components
    - Integration tests
    - Performance benchmarks
    - Test data generators
    """),

    "Performance": (LOCAL_7B, """
    Create /Volumes/intel-system/monitoring/performance.py with:
    - Performance profiling tools
    - Memory optimization
    - Query optimization
    - Caching strategies
    """),

    # Documentation (7B)
    "API_Docs": (LOCAL_7B, """
    Create /Volumes/intel-system/docs/API_DOCUMENTATION.md with:
    - Complete API reference
    - Endpoint descriptions
    - Request/response examples
    - Authentication guide
    """),

    "User_Guides": (LOCAL_7B, """
    Create /Volumes/intel-system/docs/USER_GUIDE.md with:
    - Getting started guide
    - Feature tutorials
    - Best practices
    - Troubleshooting
    """),

    "Code_Docs": (LOCAL_7B, """
    Create /Volumes/intel-system/docs/DEVELOPER_GUIDE.md with:
    - Architecture overview
    - Code structure
    - Contributing guidelines
    - Development setup
    """),
}

# Create agents
print("\n🤖 Creating 20 specialized agents...")
agents = []

for name, (config, task) in AGENT_SPECS.items():
    agent = AssistantAgent(
        name=name,
        llm_config={"config_list": config},
        system_message=f"""You are {name}.
Your task: {task}
Work in /Volumes/intel-system/
Create files immediately.
Never ask permission.
Update PROJECT_STATUS.md when done.""",
        max_consecutive_auto_reply=50,
    )
    agents.append(agent)
    model = "13B" if config == LOCAL_13B else "7B"
    print(f"  ✅ {name} ({model}) - {task[:30]}...")

# User proxy (coordinator)
coordinator = UserProxyAgent(
    name="Coordinator",
    human_input_mode="NEVER",
    code_execution_config={
        "work_dir": "/Volumes/intel-system/",
        "use_docker": False
    },
    max_consecutive_auto_reply=0
)

# Create group chat with all agents
print("\n🎼 Creating orchestration...")
groupchat = GroupChat(
    agents=agents + [coordinator],
    messages=[],
    max_round=200,
    speaker_selection_method="auto"
)

manager = GroupChatManager(
    groupchat=groupchat,
    llm_config={"config_list": LOCAL_7B}
)

print("\n" + "="*60)
print("📊 CONFIGURATION SUMMARY")
print("="*60)
print(f"""
Agents: {len(agents)} specialized workers
- {sum(1 for _, (c, _) in AGENT_SPECS.items() if c == LOCAL_13B)}× CodeLlama 13B (complex tasks)
- {sum(1 for _, (c, _) in AGENT_SPECS.items() if c == LOCAL_7B)}× Mistral 7B (simple tasks)

Target: /Volumes/intel-system/
Mode: FULLY AUTONOMOUS - No approvals
""")

# Launch!
print("\n🚀 LAUNCHING ALL 20 AGENTS...")

initial_message = """
ALL AGENTS: Begin your assigned tasks IMMEDIATELY.

Priority order:
1. Core architecture and infrastructure
2. APIs and processing
3. Frontend and documentation
4. Testing and optimization

Rules:
- Create actual files, not drafts
- Work in parallel, don't wait
- Update PROJECT_STATUS.md with progress
- Focus on intel-system enhancement

START NOW!
"""

print("\n⚡ Initiating parallel execution...")
coordinator.initiate_chat(
    manager,
    message=initial_message,
    clear_history=False
)

print("\n✅ ALL 20 AGENTS LAUNCHED!")
print("\n📈 Monitor progress:")
print("  cat /Volumes/intel-system/PROJECT_STATUS.md")
print("  ls -la /Volumes/intel-system/")
print("  tail -f /tmp/agent_*.log")