#!/usr/bin/env python3
"""
FIX FAILED COMPONENTS
Re-run Neo4j_Graph and Auth_System with longer timeout
"""

import os
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

FAILED_TASKS = [
    ("Neo4j_Graph", "Deploy Neo4j container, create knowledge graph schema with nodes for entities, relationships, and properties. Include Cypher queries for CRUD operations", "codellama:13b"),
    ("Auth_System", "Implement complete JWT authentication system with access and refresh tokens, API key management, role-based access control, and secure password hashing", "codellama:13b")
]

OUTPUT_DIR = Path("/Volumes/intel-system/max_workforce_output")

def call_ollama_extended(prompt, model="codellama:13b", timeout=300):
    """Call Ollama with extended timeout for complex tasks"""
    print(f"   🧠 Generating with {model} (timeout: {timeout}s)...")

    try:
        cmd = [
            "curl", "-s", "--max-time", str(timeout),
            "http://localhost:11434/api/generate",
            "-d", json.dumps({
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,  # Lower temperature for more focused output
                    "num_predict": 3000,  # Allow longer responses
                    "top_p": 0.9
                }
            })
        ]

        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time

        if result.returncode == 0:
            response = json.loads(result.stdout)
            content = response.get("response", "")
            if content:
                print(f"   ✅ Generated in {duration:.2f}s")
                return content
        else:
            print(f"   ❌ Failed after {duration:.2f}s")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    return None

def fix_component(name, task, model):
    """Fix a single failed component"""
    print(f"\n🔧 FIXING: {name}")
    print(f"   📋 Task: {task[:80]}...")

    component_dir = OUTPUT_DIR / name
    component_dir.mkdir(exist_ok=True)

    # Create comprehensive prompt
    prompt = f"""You are an expert infrastructure engineer.

COMPONENT: {name}
CRITICAL TASK: {task}

Generate a COMPLETE, PRODUCTION-READY implementation including:

1. Main Python implementation file with all functionality
2. Configuration files (YAML/JSON) with all settings
3. Docker setup if needed
4. Installation/setup scripts
5. Test files to verify functionality
6. Clear documentation

This is a critical component. Be thorough and complete.
Start with the main implementation:

#!/usr/bin/env python3
# {name} - Complete Implementation
# Generated: {datetime.now()}

import os
import json
"""

    # Try with extended timeout
    response = call_ollama_extended(prompt, model, timeout=300)

    if response:
        # Save implementation
        impl_file = component_dir / f"{name.lower()}_implementation.py"
        with open(impl_file, "w") as f:
            if not response.startswith("#!"):
                f.write("#!/usr/bin/env python3\n")
            f.write(f"# {name} - Fixed Implementation\n")
            f.write(f"# Generated: {datetime.now()}\n")
            f.write(f"# Model: {model}\n\n")
            f.write(response)

        os.chmod(impl_file, 0o755)
        print(f"   ✅ Saved: {impl_file}")

        # Extract config files
        extract_configs(response, component_dir)

        # Create setup script
        setup_script = component_dir / "setup.sh"
        with open(setup_script, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f"# Setup script for {name}\n\n")

            if name == "Neo4j_Graph":
                f.write("# Deploy Neo4j container\n")
                f.write("docker run -d \\\n")
                f.write("  --name neo4j \\\n")
                f.write("  -p 7474:7474 -p 7687:7687 \\\n")
                f.write("  -e NEO4J_AUTH=neo4j/password \\\n")
                f.write("  neo4j:latest\n\n")
                f.write("echo 'Neo4j deployed at http://localhost:7474'\n")
            elif name == "Auth_System":
                f.write("# Install dependencies\n")
                f.write("pip install pyjwt bcrypt flask-cors\n\n")
                f.write("# Generate secret key\n")
                f.write("python -c \"import secrets; print('JWT_SECRET=' + secrets.token_hex(32))\" > .env\n")
                f.write("echo 'Auth system configured'\n")

        os.chmod(setup_script, 0o755)
        print(f"   ✅ Created setup script: {setup_script}")

        return True
    else:
        # If still failing, create minimal working version
        print("   ⚠️ Generation failed, creating minimal version...")
        create_minimal_version(name, component_dir)
        return False

def extract_configs(content, output_dir):
    """Extract configuration files from response"""
    lines = content.split("\n")
    current_file = None
    file_content = []

    for line in lines:
        if "```yaml" in line or "```json" in line or "cat >" in line:
            if current_file and file_content:
                save_config(current_file, file_content, output_dir)

            if "```yaml" in line:
                current_file = "config.yaml"
            elif "```json" in line:
                current_file = "config.json"
            elif "cat >" in line:
                parts = line.split(">")
                if len(parts) > 1:
                    current_file = parts[1].strip().strip("'\"").split("<<")[0].strip()
            file_content = []

        elif ("```" in line or "EOF" in line) and current_file:
            if file_content:
                save_config(current_file, file_content, output_dir)
            current_file = None
            file_content = []

        elif current_file:
            file_content.append(line)

def save_config(filename, content, output_dir):
    """Save extracted config file"""
    file_path = output_dir / filename
    with open(file_path, "w") as f:
        f.write("\n".join(content))
    print(f"      📁 Extracted: {file_path}")

def create_minimal_version(name, output_dir):
    """Create minimal working version as fallback"""
    impl_file = output_dir / f"{name.lower()}_minimal.py"

    if name == "Neo4j_Graph":
        content = '''#!/usr/bin/env python3
"""Neo4j Graph Database Interface - Minimal Version"""

from neo4j import GraphDatabase
import os

class Neo4jConnection:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", pwd="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, pwd))

    def close(self):
        self.driver.close()

    def create_node(self, label, properties):
        with self.driver.session() as session:
            query = f"CREATE (n:{label} $props) RETURN id(n)"
            result = session.run(query, props=properties)
            return result.single()[0]

    def create_relationship(self, node1_id, rel_type, node2_id):
        with self.driver.session() as session:
            query = """
            MATCH (a), (b)
            WHERE id(a) = $id1 AND id(b) = $id2
            CREATE (a)-[r:""" + rel_type + """]->(b)
            RETURN id(r)
            """
            result = session.run(query, id1=node1_id, id2=node2_id)
            return result.single()[0]

if __name__ == "__main__":
    print("Neo4j Graph Interface - Minimal Version")
    print("Run setup.sh to deploy Neo4j container")
'''
    else:  # Auth_System
        content = '''#!/usr/bin/env python3
"""JWT Authentication System - Minimal Version"""

import jwt
import bcrypt
import datetime
import os
from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET_KEY = os.environ.get("JWT_SECRET", "change-this-secret-key")

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    # Verify credentials (simplified)
    token = generate_token(data.get('user_id', 1))
    return jsonify({'token': token})

@app.route('/auth/verify', methods=['POST'])
def verify():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = verify_token(token)
    if user_id:
        return jsonify({'valid': True, 'user_id': user_id})
    return jsonify({'valid': False}), 401

if __name__ == "__main__":
    print("JWT Auth System - Minimal Version")
    app.run(port=5001)
'''

    with open(impl_file, "w") as f:
        f.write(content)
    os.chmod(impl_file, 0o755)
    print(f"   ✅ Created minimal version: {impl_file}")

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║          FIXING FAILED COMPONENTS                       ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Check Ollama
    print("🔍 Checking Ollama service...")
    try:
        subprocess.run(["curl", "-s", "http://localhost:11434"],
                      capture_output=True, timeout=2)
        print("✅ Ollama ready\n")
    except:
        print("❌ Ollama not running! Starting...")
        subprocess.Popen(["ollama", "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        time.sleep(3)

    success_count = 0
    for name, task, model in FAILED_TASKS:
        if fix_component(name, task, model):
            success_count += 1

    print("\n" + "="*60)
    print("✅ FIX COMPLETE")
    print("="*60)
    print(f"Fixed: {success_count}/{len(FAILED_TASKS)} components")

    if success_count == len(FAILED_TASKS):
        print("\n🎉 All failed components now have implementations!")
    else:
        print("\n⚠️ Some components have minimal versions - review and enhance")

    print(f"\nNext steps:")
    print("1. Test the fixed components:")
    print("   python test_and_commit_workforce.py")
    print("2. Review implementations in:")
    print(f"   {OUTPUT_DIR}/Neo4j_Graph/")
    print(f"   {OUTPUT_DIR}/Auth_System/")

if __name__ == "__main__":
    main()