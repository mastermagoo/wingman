#!/usr/bin/env python3
"""
WORKFORCE V2 - PROPER PROMPT ENGINEERING
Applied learnings from v1 failure analysis
"""

import os
import json
import subprocess
import time
import re
from pathlib import Path
from datetime import datetime
import concurrent.futures

# Configuration
WORK_DIR = Path("/Volumes/intel-system")
OUTPUT_DIR = WORK_DIR / "workforce_v2_output"
OUTPUT_DIR.mkdir(exist_ok=True)

# KEY LEARNING: Use temperature 0.1 for code generation
OLLAMA_CONFIG = {
    "temperature": 0.1,  # Deterministic code generation
    "top_p": 0.95,      # Focused output
    "num_predict": 2000, # Reasonable length
    "stop": ["```", "I hope", "Let me know", "This should"]  # Stop on explanations
}

def call_ollama_v2(prompt, model="mistral:7b", max_retries=2):
    """Improved Ollama call with validation"""

    for attempt in range(max_retries):
        try:
            cmd = [
                "curl", "-s", "--max-time", "180",
                "http://localhost:11434/api/generate",
                "-d", json.dumps({
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": OLLAMA_CONFIG
                })
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                response = json.loads(result.stdout)
                content = response.get("response", "")

                # VALIDATION: Check if it's code or explanation
                if content and not content.strip().startswith(("I", "This", "Here", "The", "Let")):
                    return content
                elif attempt == 0:
                    # Retry with stronger prompt
                    prompt = "OUTPUT ONLY CODE. NO EXPLANATIONS.\n\n" + prompt
                    continue

        except Exception as e:
            print(f"Error: {e}")

    return None

def extract_code_from_response(response):
    """Extract actual code from mixed responses"""
    # Remove explanation lines
    lines = response.split('\n')
    code_lines = []
    in_code = False

    for line in lines:
        # Skip obvious explanation lines
        if line.strip().startswith(("I'll", "I'm", "This", "Here", "The", "Let")):
            continue
        # Start of code block
        if '```' in line:
            in_code = not in_code
            continue
        # Collect code lines
        if in_code or (line.strip() and not line.strip()[0].isupper()):
            code_lines.append(line)

    return '\n'.join(code_lines)

def validate_python_syntax(code):
    """Check if Python code is valid"""
    try:
        compile(code, '<string>', 'exec')
        return True, "Valid"
    except SyntaxError as e:
        return False, str(e)

# FOCUSED COMPONENT DEFINITIONS - One clear task each
COMPONENTS_V2 = {
    "redis_config": {
        "model": "mistral:7b",
        "task": "Redis configuration with persistence",
        "prompt": """OUTPUT ONLY PYTHON CODE. NO EXPLANATIONS.

import redis
import json
import os

class RedisConfig:
    def __init__(self):
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.db = int(os.getenv('REDIS_DB', 0))
        self.password = os.getenv('REDIS_PASSWORD', None)

    def get_client(self):
        # Create Redis client with connection pooling

    def setup_persistence(self):
        # Configure AOF and RDB persistence

    def test_connection(self):
        # Test Redis connection

Complete the class implementation:"""
    },

    "vector_search": {
        "model": "codellama:13b",
        "task": "ChromaDB vector search",
        "prompt": """OUTPUT ONLY PYTHON CODE.

import chromadb
from sentence_transformers import SentenceTransformer

class VectorSearch:
    def __init__(self):
        self.client = chromadb.Client()
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def create_collection(self, name):
        # Create or get collection

    def add_documents(self, docs, ids):
        # Add documents with embeddings

    def search(self, query, k=5):
        # Search similar documents

Complete the implementation:"""
    },

    "api_server": {
        "model": "codellama:13b",
        "task": "Flask REST API",
        "prompt": """OUTPUT ONLY PYTHON CODE.

from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

@app.route('/verify', methods=['POST'])
def verify():
    # Implement verification endpoint
    pass

@app.route('/search', methods=['POST'])
def search():
    # Implement search endpoint
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

Complete all endpoint implementations:"""
    },

    "docker_compose": {
        "model": "mistral:7b",
        "task": "Docker Compose configuration",
        "prompt": """OUTPUT ONLY YAML. NO EXPLANATIONS.

version: '3.8'

services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  api:
    build: .
    ports:
      - "5000:5000"

  # Add neo4j, postgres, and nginx services

Complete the docker-compose.yml:"""
    }
}

def generate_component_v2(name, spec):
    """Generate a single component with proper prompt engineering"""
    print(f"\n🔧 Generating {name}...")

    component_dir = OUTPUT_DIR / name
    component_dir.mkdir(exist_ok=True)

    # Generate code
    response = call_ollama_v2(spec["prompt"], spec["model"])

    if response:
        # Clean the response
        code = extract_code_from_response(response)

        # Validate if Python
        if name != "docker_compose":
            valid, error = validate_python_syntax(code)
            if not valid:
                print(f"   ⚠️ Syntax issue: {error}")
                # Try to fix common issues
                code = fix_common_syntax_issues(code)
                valid, error = validate_python_syntax(code)

        # Save the implementation
        if name == "docker_compose":
            output_file = component_dir / "docker-compose.yml"
        else:
            output_file = component_dir / f"{name}.py"

        with open(output_file, 'w') as f:
            if name != "docker_compose" and not code.startswith("#!"):
                f.write("#!/usr/bin/env python3\n")
                f.write(f"# {name} - Generated with proper prompt engineering\n\n")
            f.write(code)

        os.chmod(output_file, 0o755)
        print(f"   ✅ Saved: {output_file}")

        # Create requirements.txt for Python components
        if name != "docker_compose":
            create_requirements(component_dir, code)

        return True
    else:
        print(f"   ❌ Generation failed")
        return False

def fix_common_syntax_issues(code):
    """Fix common LLM code generation issues"""
    # Remove incomplete function stubs with just 'pass'
    code = re.sub(r'\n\s*pass\s*\n', '\n    return {}\n', code)

    # Add missing colons
    code = re.sub(r'def (\w+)\((.*?)\)\s*\n', r'def \1(\2):\n', code)

    # Fix indentation issues
    lines = code.split('\n')
    fixed_lines = []
    indent_level = 0

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'with ')):
            fixed_lines.append('    ' * indent_level + stripped)
            if stripped.endswith(':'):
                indent_level += 1
        elif stripped.startswith(('return', 'break', 'continue', 'pass')):
            fixed_lines.append('    ' * indent_level + stripped)
            if indent_level > 0:
                indent_level -= 1
        elif stripped:
            fixed_lines.append('    ' * indent_level + stripped)
        else:
            fixed_lines.append('')

    return '\n'.join(fixed_lines)

def create_requirements(component_dir, code):
    """Extract and create requirements.txt"""
    imports = re.findall(r'^import (\w+)', code, re.MULTILINE)
    imports += re.findall(r'^from (\w+)', code, re.MULTILINE)

    # Map common imports to pip packages
    package_map = {
        'flask': 'flask==2.3.3',
        'redis': 'redis==5.0.0',
        'chromadb': 'chromadb==0.4.0',
        'sentence_transformers': 'sentence-transformers==2.2.2',
        'jwt': 'pyjwt==2.8.0',
        'bcrypt': 'bcrypt==4.0.1',
        'neo4j': 'neo4j==5.0.0',
        'fastapi': 'fastapi==0.100.0',
        'numpy': 'numpy==1.24.0',
        'pandas': 'pandas==2.0.0'
    }

    requirements = []
    for imp in set(imports):
        if imp in package_map:
            requirements.append(package_map[imp])

    if requirements:
        req_file = component_dir / "requirements.txt"
        with open(req_file, 'w') as f:
            f.write('\n'.join(requirements))
        print(f"      📦 Created requirements.txt")

def create_test_script(component_dir, component_name):
    """Create a simple test script"""
    test_script = f"""#!/usr/bin/env python3
'''Test script for {component_name}'''

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

try:
    import {component_name}
    print(f"✅ {component_name} module loaded successfully")

    # Basic syntax test
    if hasattr({component_name}, '__file__'):
        print(f"✅ Module file: {{{component_name}.__file__}}")

    # List available classes/functions
    items = [item for item in dir({component_name}) if not item.startswith('_')]
    print(f"✅ Available items: {{items}}")

except ImportError as e:
    print(f"❌ Import failed: {{e}}")
except SyntaxError as e:
    print(f"❌ Syntax error: {{e}}")
"""

    test_file = component_dir / f"test_{component_name}.py"
    with open(test_file, 'w') as f:
        f.write(test_script)
    os.chmod(test_file, 0o755)

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║        WORKFORCE V2 - PROPER PROMPT ENGINEERING         ║
╠══════════════════════════════════════════════════════════╣
║  Applying lessons learned from V1:                      ║
║  • Single-purpose prompts                               ║
║  • Code-only output                                     ║
║  • Temperature 0.1                                      ║
║  • Syntax validation                                    ║
║  • Automatic fixes                                      ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Check Ollama
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    if "mistral" not in result.stdout:
        print("⚠️ Loading models...")
        subprocess.run(["ollama", "pull", "mistral:7b"])
        subprocess.run(["ollama", "pull", "codellama:13b"])

    print(f"\n📁 Output directory: {OUTPUT_DIR}\n")

    # Generate components with proper prompts
    success = 0
    failed = 0

    for name, spec in COMPONENTS_V2.items():
        if generate_component_v2(name, spec):
            success += 1
            # Create test script
            if name != "docker_compose":
                create_test_script(OUTPUT_DIR / name, name)
        else:
            failed += 1

    # Summary
    print("\n" + "="*60)
    print("📊 GENERATION COMPLETE")
    print("="*60)
    print(f"✅ Successful: {success}/{len(COMPONENTS_V2)}")
    print(f"❌ Failed: {failed}/{len(COMPONENTS_V2)}")

    # Run syntax validation
    print("\n🧪 Running validation...")
    for name in COMPONENTS_V2:
        if name == "docker_compose":
            continue

        component_dir = OUTPUT_DIR / name
        test_script = component_dir / f"test_{name}.py"
        if test_script.exists():
            result = subprocess.run(
                ["/usr/bin/python3", str(test_script)],
                capture_output=True, text=True
            )
            print(f"{name}: {result.stdout.strip()}")

    print(f"\n✅ Components ready in: {OUTPUT_DIR}")
    print("\nKey improvements from V1:")
    print("• Focused single-task prompts")
    print("• Explicit code-only instructions")
    print("• Lower temperature (0.1)")
    print("• Syntax validation")
    print("• Auto-fixing common issues")

if __name__ == "__main__":
    main()