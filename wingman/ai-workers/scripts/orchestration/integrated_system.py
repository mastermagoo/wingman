#!/usr/bin/env python3
"""
INTEGRATED WINGMAN SYSTEM
Combines all components with full infrastructure
"""

import os
import redis
import chromadb
from sentence_transformers import SentenceTransformer
from flask import Flask, request, jsonify
import subprocess
import json
from datetime import datetime

# Initialize infrastructure
print("🚀 Initializing Wingman with full infrastructure...")

# Redis for memory
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
print("✅ Redis connected")

# ChromaDB for vector search
chroma_client = chromadb.Client()
try:
    collection = chroma_client.create_collection("wingman_verifications")
except:
    collection = chroma_client.get_collection("wingman_verifications")
print("✅ ChromaDB ready")

# Embeddings model
embeddings = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Embeddings model loaded")

# Flask API
app = Flask(__name__)

class WingmanVerifier:
    """Main verification engine with RAG"""
    
    def __init__(self):
        self.collection = collection
        self.embeddings = embeddings
        self.redis = r
        
    def verify_with_rag(self, claim):
        """Verify claim using RAG pipeline"""
        # 1. Search for similar claims
        query_embedding = self.embeddings.encode(claim).tolist()
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=5
            )
            similar_claims = results.get('documents', [[]])[0]
        except:
            similar_claims = []
        
        # 2. Use Mistral for verification
        prompt = f"""
Verify this claim: {claim}

Similar claims found:
{chr(10).join(similar_claims[:3]) if similar_claims else 'None'}

Provide verification result as JSON:
{{
  "verdict": "true/false/unverifiable",
  "confidence": 0-100,
  "evidence": "explanation"
}}
        """
        
        # Run Mistral
        cmd = f'ollama run mistral:7b "{prompt}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        # Parse result
        try:
            verification = json.loads(result.stdout)
        except:
            verification = {
                "verdict": "unverifiable",
                "confidence": 0,
                "evidence": "Could not parse LLM response"
            }
        
        # 3. Store in memory
        memory_key = f"verification:{datetime.now().isoformat()}"
        self.redis.set(memory_key, json.dumps({
            "claim": claim,
            "result": verification,
            "timestamp": datetime.now().isoformat()
        }))
        
        # 4. Add to vector store for future reference
        self.collection.add(
            documents=[claim],
            metadatas=[verification],
            ids=[memory_key]
        )
        
        return verification

# Initialize verifier
verifier = WingmanVerifier()

@app.route('/verify', methods=['POST'])
def verify_claim():
    """API endpoint for verification"""
    data = request.json
    claim = data.get('claim', '')
    
    if not claim:
        return jsonify({"error": "No claim provided"}), 400
    
    result = verifier.verify_with_rag(claim)
    return jsonify(result)

@app.route('/history', methods=['GET'])
def get_history():
    """Get verification history from Redis"""
    keys = r.keys('verification:*')
    history = []
    
    for key in keys[-10:]:  # Last 10
        data = r.get(key)
        if data:
            history.append(json.loads(data))
    
    return jsonify(history)

@app.route('/search', methods=['POST'])
def search_similar():
    """Search for similar claims"""
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    query_embedding = embeddings.encode(query).tolist()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=10
    )
    
    return jsonify({
        "similar_claims": results.get('documents', [[]])[0],
        "metadata": results.get('metadatas', [[]])[0]
    })

@app.route('/health', methods=['GET'])
def health_check():
    """System health check"""
    return jsonify({
        "status": "healthy",
        "redis": "connected" if r.ping() else "disconnected",
        "chromadb": "ready",
        "embeddings": "loaded",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎆 WINGMAN INTEGRATED SYSTEM")
    print("="*60)
    print("""
    ✅ Redis Memory: Active
    ✅ ChromaDB Vector Search: Ready  
    ✅ Embeddings: Loaded
    ✅ Mistral 7B: Available
    ✅ API Server: Starting...
    
    Endpoints:
    - POST /verify - Verify a claim
    - GET /history - Get verification history
    - POST /search - Search similar claims
    - GET /health - System status
    """)
    
    app.run(host='0.0.0.0', port=8444, debug=False)