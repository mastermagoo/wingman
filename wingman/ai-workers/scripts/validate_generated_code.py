#!/usr/bin/env python3
"""
Code Validation Script for Generated Workers
Validates syntax, structure, and dependencies
"""

import os
import sys
import json
import ast
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Script was relocated under tools/orchestration; keep BASE_DIR pointing at repo root.
BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "mega_delegation_output"
RESULTS_FILE = OUTPUT_DIR / "validation_results.json"

class CodeValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.stats = {
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "python_files": 0,
            "sql_files": 0,
            "json_files": 0,
            "dependencies": set(),
            "worker_directories": 0
        }
        
    def validate_python_syntax(self, file_path):
        """Validate Python file syntax"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error: {e.msg} at line {e.lineno}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def validate_json_syntax(self, file_path):
        """Validate JSON file syntax"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True, None
        except json.JSONDecodeError as e:
            return False, f"JSON error: {e.msg} at line {e.lineno}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def extract_imports(self, file_path):
        """Extract Python imports from file"""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except:
            pass
        return imports
    
    def validate_file(self, file_path):
        """Validate a single file"""
        self.stats["total_files"] += 1
        file_path = Path(file_path)
        
        if file_path.suffix == '.py':
            self.stats["python_files"] += 1
            valid, error = self.validate_python_syntax(file_path)
            if valid:
                self.stats["valid_files"] += 1
                # Extract imports
                imports = self.extract_imports(file_path)
                for imp in imports:
                    # Extract base package name
                    base = imp.split('.')[0]
                    if base not in ['os', 'sys', 'json', 'pathlib', 'datetime', 'typing', 'threading', 'subprocess']:
                        self.stats["dependencies"].add(base)
            else:
                self.stats["invalid_files"] += 1
                self.errors.append({
                    "file": str(file_path),
                    "type": "Python Syntax",
                    "error": error
                })
                
        elif file_path.suffix == '.json':
            self.stats["json_files"] += 1
            valid, error = self.validate_json_syntax(file_path)
            if valid:
                self.stats["valid_files"] += 1
            else:
                self.stats["invalid_files"] += 1
                self.errors.append({
                    "file": str(file_path),
                    "type": "JSON Syntax",
                    "error": error
                })
        else:
            # Other files (SQL, MD, etc.) - just count
            self.stats["valid_files"] += 1
    
    def validate_structure(self):
        """Validate directory structure"""
        worker_dirs = list(OUTPUT_DIR.glob("worker_*"))
        self.stats["worker_directories"] = len(worker_dirs)
        
        # Check for expected files in each directory
        for worker_dir in worker_dirs:
            if not worker_dir.is_dir():
                continue
            
            files = list(worker_dir.glob("*"))
            if not files:
                self.warnings.append({
                    "type": "Empty Directory",
                    "directory": str(worker_dir),
                    "message": "Worker directory has no files"
                })
            
            # Check for generated_code.md
            if not (worker_dir / "generated_code.md").exists():
                self.warnings.append({
                    "type": "Missing Documentation",
                    "directory": str(worker_dir),
                    "message": "Missing generated_code.md"
                })
    
    def generate_report(self):
        """Generate validation report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files": self.stats["total_files"],
                "valid_files": self.stats["valid_files"],
                "invalid_files": self.stats["invalid_files"],
                "success_rate": (self.stats["valid_files"] / self.stats["total_files"] * 100) if self.stats["total_files"] > 0 else 0,
                "python_files": self.stats["python_files"],
                "sql_files": self.stats["sql_files"],
                "json_files": self.stats["json_files"],
                "worker_directories": self.stats["worker_directories"],
                "errors_count": len(self.errors),
                "warnings_count": len(self.warnings)
            },
            "dependencies": sorted(list(self.stats["dependencies"])),
            "errors": self.errors[:50],  # Limit to first 50 errors
            "warnings": self.warnings[:50]  # Limit to first 50 warnings
        }
        
        return report

def main():
    print("=" * 70)
    print("CODE VALIDATION - Generated Workers")
    print("=" * 70)
    print()
    
    validator = CodeValidator()
    
    # Validate structure first
    print("📁 Validating directory structure...")
    validator.validate_structure()
    print(f"   Found {validator.stats['worker_directories']} worker directories")
    print()
    
    # Validate all files
    print("🔍 Validating files...")
    file_count = 0
    
    # Get all files in worker directories
    for worker_dir in OUTPUT_DIR.glob("worker_*"):
        if not worker_dir.is_dir():
            continue
        
        for file_path in worker_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.py', '.sql', '.json', '.yaml', '.yml', '.md', '.sh']:
                validator.validate_file(file_path)
                file_count += 1
                if file_count % 50 == 0:
                    print(f"   Validated {file_count} files...", end='\r')
    
    print(f"   Validated {file_count} files")
    print()
    
    # Generate report
    print("📊 Generating report...")
    report = validator.generate_report()
    
    # Save report
    with open(RESULTS_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print()
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Total Files: {report['summary']['total_files']}")
    print(f"Valid Files: {report['summary']['valid_files']}")
    print(f"Invalid Files: {report['summary']['invalid_files']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"Python Files: {report['summary']['python_files']}")
    print(f"Worker Directories: {report['summary']['worker_directories']}")
    print(f"Errors: {report['summary']['errors_count']}")
    print(f"Warnings: {report['summary']['warnings_count']}")
    print()
    
    if report['dependencies']:
        print("📦 Dependencies Found:")
        for dep in report['dependencies'][:20]:
            print(f"   - {dep}")
        if len(report['dependencies']) > 20:
            print(f"   ... and {len(report['dependencies']) - 20} more")
        print()
    
    if report['errors']:
        print("❌ Errors Found:")
        for error in report['errors'][:10]:
            print(f"   {error['file']}: {error['error']}")
        if len(report['errors']) > 10:
            print(f"   ... and {len(report['errors']) - 10} more errors")
        print()
    
    if report['warnings']:
        print("⚠️  Warnings:")
        for warning in report['warnings'][:10]:
            print(f"   {warning['directory']}: {warning['message']}")
        if len(report['warnings']) > 10:
            print(f"   ... and {len(report['warnings']) - 10} more warnings")
        print()
    
    print(f"📄 Full report saved to: {RESULTS_FILE}")
    print()
    
    # Exit code based on errors
    if report['summary']['errors_count'] > 0:
        print("❌ Validation completed with errors")
        sys.exit(1)
    else:
        print("✅ Validation completed successfully")
        sys.exit(0)

if __name__ == "__main__":
    main()


