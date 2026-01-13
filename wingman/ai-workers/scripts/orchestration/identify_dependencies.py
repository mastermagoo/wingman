#!/usr/bin/env python3
"""
Dependency Identification Script
Extracts all Python dependencies from generated code
"""

import ast
import json
from pathlib import Path
from collections import defaultdict

# Script was relocated under tools/orchestration; keep BASE_DIR pointing at repo root.
BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "mega_delegation_output"
DEPS_FILE = OUTPUT_DIR / "dependencies_list.json"

def extract_imports(file_path):
    """Extract all imports from a Python file"""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split('.')[0])
    except:
        pass
    return imports

def main():
    print("🔍 Identifying dependencies...")
    
    dependencies = defaultdict(int)
    stdlib_modules = {
        'os', 'sys', 'json', 'pathlib', 'datetime', 'typing', 'threading',
        'subprocess', 'time', 'argparse', 'collections', 'functools',
        'itertools', 're', 'hashlib', 'base64', 'urllib', 'http', 'socket',
        'sqlite3', 'csv', 'io', 'logging', 'unittest', 'tempfile', 'shutil'
    }
    
    file_count = 0
    for worker_dir in OUTPUT_DIR.glob("worker_*"):
        if not worker_dir.is_dir():
            continue
        
        for file_path in worker_dir.rglob("*.py"):
            file_count += 1
            imports = extract_imports(file_path)
            for imp in imports:
                if imp not in stdlib_modules:
                    dependencies[imp] += 1
    
    print(f"   Scanned {file_count} Python files")
    print(f"   Found {len(dependencies)} unique dependencies")
    print()
    
    # Sort by frequency
    sorted_deps = sorted(dependencies.items(), key=lambda x: x[1], reverse=True)
    
    # Save to file
    deps_data = {
        "total_files_scanned": file_count,
        "unique_dependencies": len(dependencies),
        "dependencies": {dep: count for dep, count in sorted_deps}
    }
    
    with open(DEPS_FILE, 'w') as f:
        json.dump(deps_data, f, indent=2)
    
    print("📦 Top Dependencies:")
    for dep, count in sorted_deps[:20]:
        print(f"   {dep}: {count} files")
    
    if len(sorted_deps) > 20:
        print(f"   ... and {len(sorted_deps) - 20} more")
    
    print()
    print(f"📄 Dependencies list saved to: {DEPS_FILE}")
    
    # Generate requirements.txt
    requirements_file = OUTPUT_DIR / "requirements.txt"
    with open(requirements_file, 'w') as f:
        f.write("# Generated dependencies from worker code\n")
        f.write("# Review and adjust versions as needed\n\n")
        for dep, count in sorted_deps:
            f.write(f"{dep}  # Used in {count} files\n")
    
    print(f"📄 requirements.txt saved to: {requirements_file}")

if __name__ == "__main__":
    main()


