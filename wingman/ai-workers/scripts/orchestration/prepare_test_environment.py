#!/usr/bin/env python3
"""
TEST Environment Preparation Script
Verifies TEST environment and prepares for deployment
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

# Script was relocated under tools/orchestration; keep BASE_DIR pointing at repo root.
BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "mega_delegation_output"
TEST_STATUS_FILE = OUTPUT_DIR / "test_environment_status.json"

def check_docker_containers():
    """Check TEST containers"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=-test", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        containers = [c for c in result.stdout.strip().split('\n') if c]
        return len(containers), containers
    except Exception as e:
        return 0, []

def test_postgresql(port=6432):
    """Test PostgreSQL TEST connection"""
    try:
        result = subprocess.run(
            ["psql", "-h", "localhost", "-p", str(port), "-U", "admin", "-d", "intel_system_test", "-c", "SELECT 1"],
            capture_output=True,
            text=True,
            timeout=5,
            env={"PGPASSWORD": "secure_pass_2024"}
        )
        return result.returncode == 0
    except:
        return False

def test_redis(port=7379):
    """Test Redis TEST connection"""
    try:
        result = subprocess.run(
            ["redis-cli", "-p", str(port), "PING"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return "PONG" in result.stdout
    except:
        return False

def test_neo4j(port=7475):
    """Test Neo4j TEST connection"""
    try:
        import requests
        response = requests.get(f"http://localhost:{port}", timeout=5)
        return response.status_code in [200, 401]  # 401 is OK (auth required)
    except:
        return False

def test_chromadb(port=8002):
    """Test ChromaDB TEST connection"""
    try:
        import requests
        response = requests.get(f"http://localhost:{port}/api/v1/heartbeat", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("=" * 70)
    print("TEST ENVIRONMENT PREPARATION")
    print("=" * 70)
    print()
    
    status = {
        "timestamp": datetime.now().isoformat(),
        "docker_containers": {},
        "databases": {},
        "services": {},
        "ready": False
    }
    
    # Check Docker containers
    print("🐳 Checking Docker containers...")
    container_count, containers = check_docker_containers()
    status["docker_containers"] = {
        "count": container_count,
        "containers": containers,
        "expected": 33,
        "status": "✅" if container_count >= 30 else "⚠️"
    }
    print(f"   Found {container_count} TEST containers (expected: 33)")
    print()
    
    # Test PostgreSQL
    print("🐘 Testing PostgreSQL TEST (port 6432)...")
    pg_status = test_postgresql(6432)
    status["databases"]["postgresql"] = {
        "port": 6432,
        "status": "✅" if pg_status else "❌",
        "accessible": pg_status
    }
    print(f"   PostgreSQL TEST: {'✅ Accessible' if pg_status else '❌ Not accessible'}")
    print()
    
    # Test Redis
    print("📦 Testing Redis TEST (port 7379)...")
    redis_status = test_redis(7379)
    status["databases"]["redis"] = {
        "port": 7379,
        "status": "✅" if redis_status else "❌",
        "accessible": redis_status
    }
    print(f"   Redis TEST: {'✅ Accessible' if redis_status else '❌ Not accessible'}")
    print()
    
    # Test Neo4j
    print("🕸️  Testing Neo4j TEST (port 7475)...")
    neo4j_status = test_neo4j(7475)
    status["databases"]["neo4j"] = {
        "port": 7475,
        "status": "✅" if neo4j_status else "❌",
        "accessible": neo4j_status
    }
    print(f"   Neo4j TEST: {'✅ Accessible' if neo4j_status else '❌ Not accessible'}")
    print()
    
    # Test ChromaDB
    print("🔍 Testing ChromaDB TEST (port 8002)...")
    chroma_status = test_chromadb(8002)
    status["services"]["chromadb"] = {
        "port": 8002,
        "status": "✅" if chroma_status else "⚠️",
        "accessible": chroma_status
    }
    print(f"   ChromaDB TEST: {'✅ Accessible' if chroma_status else '⚠️ Not accessible (optional)'}")
    print()
    
    # Overall status
    critical_services = [pg_status, redis_status, neo4j_status]
    status["ready"] = all(critical_services) and container_count >= 30
    
    # Save status
    with open(TEST_STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)
    
    # Print summary
    print("=" * 70)
    print("TEST ENVIRONMENT STATUS")
    print("=" * 70)
    print(f"Docker Containers: {status['docker_containers']['status']} {container_count}/33")
    print(f"PostgreSQL TEST: {status['databases']['postgresql']['status']}")
    print(f"Redis TEST: {status['databases']['redis']['status']}")
    print(f"Neo4j TEST: {status['databases']['neo4j']['status']}")
    print(f"ChromaDB TEST: {status['services']['chromadb']['status']}")
    print()
    
    if status["ready"]:
        print("✅ TEST environment is READY for deployment")
        sys.exit(0)
    else:
        print("⚠️  TEST environment has issues - review status above")
        sys.exit(1)

if __name__ == "__main__":
    main()


