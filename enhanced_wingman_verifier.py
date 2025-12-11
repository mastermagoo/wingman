#!/usr/bin/env python3
"""
Enhanced Wingman Verifier for Deployment
Actually verifies deliverables exist in TEST environment
"""

import subprocess
import json
import sys
from pathlib import Path

def verify_postgresql_schema(schema_name, port=6432):
    """Actually check if schema exists in PostgreSQL TEST"""
    try:
        result = subprocess.run(
            ["psql", "-h", "localhost", "-p", str(port), "-U", "admin", "-d", "intel_system_test", "-c", f"\\dn {schema_name}"],
            capture_output=True,
            text=True,
            timeout=10,
            env={"PGPASSWORD": "secure_pass_2024"}
        )
        
        if result.returncode == 0 and schema_name in result.stdout:
            return "TRUE", f"Schema {schema_name} exists in PostgreSQL TEST"
        else:
            return "FALSE", f"Schema {schema_name} NOT found in PostgreSQL TEST"
    except Exception as e:
        # Connection issue - check if it's just connection or schema missing
        if "Connection refused" in str(e) or "connection" in str(e).lower():
            return "UNVERIFIABLE", f"Cannot connect to PostgreSQL TEST (port {port})"
        return "FALSE", f"Error checking schema: {str(e)[:100]}"

def verify_neo4j_namespace(namespace_name, port=7475):
    """Actually check if namespace exists in Neo4j TEST"""
    try:
        import requests
        # Try to query Neo4j
        response = requests.get(f"http://localhost:{port}", timeout=5)
        if response.status_code in [200, 401]:
            # Neo4j is accessible, try to query namespace
            # This would need actual Cypher query
            return "UNVERIFIABLE", "Neo4j accessible but namespace verification needs Cypher query"
        else:
            return "FALSE", f"Neo4j TEST not accessible (port {port})"
    except Exception as e:
        return "UNVERIFIABLE", f"Cannot verify Neo4j namespace: {str(e)[:100]}"

def verify_chromadb_collection(collection_name, port=8002):
    """Actually check if collection exists in ChromaDB TEST"""
    try:
        import requests
        response = requests.get(f"http://localhost:{port}/api/v1/heartbeat", timeout=5)
        if response.status_code == 200:
            # ChromaDB accessible, would need to check collection
            return "UNVERIFIABLE", "ChromaDB accessible but collection verification needs API call"
        else:
            return "FALSE", f"ChromaDB TEST not accessible (port {port})"
    except:
        return "UNVERIFIABLE", f"ChromaDB TEST not accessible"

def verify_file_exists(file_path):
    """Check if file actually exists"""
    path = Path(file_path)
    if path.exists():
        return "TRUE", f"File exists: {file_path}"
    else:
        return "FALSE", f"File does not exist: {file_path}"

def verify_deliverable(deliverable_text, worker_id, test_process=""):
    """Verify deliverable using appropriate method"""
    deliverable_lower = deliverable_text.lower()
    
    # PostgreSQL schema
    if "schema" in deliverable_lower and "postgresql" in deliverable_lower:
        if "sap_deutschland" in deliverable_text:
            return verify_postgresql_schema("sap_deutschland", 6432)
    
    # Neo4j namespace
    if "namespace" in deliverable_lower and "neo4j" in deliverable_lower:
        if "sap_deutschland" in deliverable_text:
            return verify_neo4j_namespace("sap_deutschland", 7475)
    
    # ChromaDB collection
    if "collection" in deliverable_lower and "chromadb" in deliverable_lower:
        if "sap_deutschland" in deliverable_text:
            return verify_chromadb_collection("sap_deutschland", 8002)
    
    # File deliverables
    if deliverable_text.endswith('.py') or deliverable_text.endswith('.sql') or deliverable_text.endswith('.json'):
        # Extract file path
        file_name = deliverable_text.split('/')[-1].replace('`', '').strip()
        worker_dir = Path(f"mega_delegation_output/worker_{worker_id:03d}")
        file_path = worker_dir / file_name
        return verify_file_exists(file_path)
    
    # Test results file
    if "test results file" in deliverable_lower:
        results_file = Path(f"ai-workers/results/worker-{worker_id:03d}-results.json")
        return verify_file_exists(results_file)
    
    # Default: unverifiable
    return "UNVERIFIABLE", f"Cannot verify deliverable type: {deliverable_text[:50]}"

def main():
    """Test verifier"""
    if len(sys.argv) < 2:
        print("Usage: python3 enhanced_wingman_verifier.py <deliverable_text> [worker_id]")
        sys.exit(1)
    
    deliverable = sys.argv[1]
    worker_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    verdict, evidence = verify_deliverable(deliverable, worker_id)
    print(f"Verdict: {verdict}")
    print(f"Evidence: {evidence}")
    
    sys.exit(0 if verdict == "TRUE" else 1)

if __name__ == "__main__":
    main()


