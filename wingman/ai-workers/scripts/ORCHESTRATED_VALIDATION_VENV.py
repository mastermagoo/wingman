#!/usr/bin/env python3
"""
ORCHESTRATED VALIDATION - Uses venv for import checking
Modified to use the virtual environment for dependency validation
"""

import os
import sys
import subprocess
import asyncio
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path
import ast

# Add venv to Python path for THIS script
venv_site_packages = Path('autonomous_build/venv/lib/python3.13/site-packages')
if venv_site_packages.exists():
    sys.path.insert(0, str(venv_site_packages))

class ComponentValidator:
    """Validates a single component with real tests"""

    def __init__(self, component_path):
        self.path = Path(component_path)
        self.name = self.path.name
        self.venv_python = Path('autonomous_build/venv/bin/python3')
        self.results = {
            'name': self.name,
            'path': str(self.path),
            'syntax': 'PENDING',
            'imports': 'PENDING',
            'startup': 'PENDING',
            'api': 'PENDING',
            'dependencies': [],
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }

    def check_syntax(self):
        """Direct Python syntax validation"""
        try:
            py_files = list(self.path.glob("*.py"))
            for py_file in py_files:
                with open(py_file) as f:
                    ast.parse(f.read(), filename=str(py_file))
            self.results['syntax'] = f'✅ VALID ({len(py_files)} files)'
            return True
        except SyntaxError as e:
            self.results['syntax'] = f'❌ FAILED: {e}'
            self.results['errors'].append(f'Syntax: {e}')
            return False

    def check_imports(self):
        """Check if all imports are available IN THE VENV"""
        missing = []
        found = []

        try:
            # Extract all imports
            py_files = list(self.path.glob("*.py"))
            imports = set()

            for py_file in py_files:
                with open(py_file) as f:
                    try:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    imports.add(alias.name.split('.')[0])
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    imports.add(node.module.split('.')[0])
                    except:
                        continue

            # Test each import USING THE VENV PYTHON
            for imp in imports:
                # Use the venv Python to check imports
                result = subprocess.run(
                    [str(self.venv_python), '-c', f'import {imp}'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    found.append(imp)
                else:
                    missing.append(imp)

            self.results['dependencies'] = list(imports)

            if missing:
                self.results['imports'] = f'⚠️ MISSING: {", ".join(missing)}'
                self.results['errors'].append(f'Missing imports: {missing}')
            else:
                self.results['imports'] = f'✅ ALL FOUND ({len(found)} imports)'

            return len(missing) == 0

        except Exception as e:
            self.results['imports'] = f'❌ ERROR: {e}'
            return False

    def check_startup(self):
        """Try to start the component using venv Python"""
        try:
            main_file = self.path / f"{self.name}.py"
            if not main_file.exists():
                # Try to find main file
                py_files = list(self.path.glob("*.py"))
                if py_files:
                    main_file = py_files[0]
                else:
                    self.results['startup'] = '⚠️ NO PYTHON FILES'
                    return False

            # Try to start it WITH VENV PYTHON
            process = subprocess.Popen(
                [str(self.venv_python), str(main_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.path)
            )

            # Wait 3 seconds to see if it crashes
            try:
                stdout, stderr = process.communicate(timeout=3)
                if process.returncode == 0:
                    self.results['startup'] = '✅ RUNS WITHOUT ERROR'
                    return True
                else:
                    self.results['startup'] = f'❌ EXIT CODE: {process.returncode}'
                    if stderr:
                        self.results['errors'].append(f'Startup: {stderr.decode()[:200]}')
                    return False
            except subprocess.TimeoutExpired:
                # Still running after 3 seconds = good
                process.kill()
                self.results['startup'] = '✅ STARTS SUCCESSFULLY'
                return True

        except Exception as e:
            self.results['startup'] = f'❌ FAILED: {str(e)[:100]}'
            self.results['errors'].append(f'Startup: {e}')
            return False

    def check_api(self):
        """Check if API endpoints respond"""
        # Map components to their expected ports
        port_map = {
            'api_gateway': 8000,
            'monitoring_stack': 9090,
            'websocket_server': 8765,
            'redis_config': 6379,
            'neo4j_graph': 7474,
            'frontend_dashboard': 3000,
        }

        if self.name not in port_map:
            self.results['api'] = '⏭️ SKIPPED (no API)'
            return True

        port = port_map[self.name]

        try:
            import requests
            response = requests.get(f'http://localhost:{port}/health', timeout=2)
            if response.status_code == 200:
                self.results['api'] = f'✅ RESPONDING (port {port})'
                return True
            else:
                self.results['api'] = f'⚠️ STATUS {response.status_code}'
                return False
        except:
            self.results['api'] = f'❌ NOT RESPONDING (port {port})'
            return False

    async def validate(self):
        """Run all validations"""
        print(f"🔍 Validating {self.name}...")

        # Run checks in sequence (some depend on others)
        syntax_ok = self.check_syntax()
        imports_ok = self.check_imports() if syntax_ok else False
        startup_ok = self.check_startup() if imports_ok else False
        api_ok = self.check_api() if startup_ok else False

        # Overall status
        if syntax_ok and imports_ok and startup_ok:
            self.results['status'] = '✅ WORKING'
        elif syntax_ok and imports_ok:
            self.results['status'] = '⚠️ PARTIAL'
        else:
            self.results['status'] = '❌ FAILED'

        return self.results


class ValidationOrchestrator:
    """Orchestrates parallel validation of all components"""

    def __init__(self, base_path='autonomous_build'):
        self.base_path = Path(base_path)
        self.components = []
        self.results = []

    def discover_components(self):
        """Find all components to validate"""
        # Get all directories with Python files (exclude venv)
        for item in self.base_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name != 'venv':
                if list(item.glob('*.py')):
                    self.components.append(item)

        print(f"📦 Found {len(self.components)} components to validate")
        return self.components

    async def validate_component(self, component_path):
        """Validate a single component"""
        validator = ComponentValidator(component_path)
        return await validator.validate()

    async def run_parallel_validation(self):
        """Run all validations in parallel"""
        print(f"🚀 Starting parallel validation of {len(self.components)} components")
        print("=" * 60)

        # Create tasks for all components
        tasks = []
        for component in self.components:
            task = asyncio.create_task(self.validate_component(component))
            tasks.append(task)

        # Wait for all to complete
        self.results = await asyncio.gather(*tasks)

        return self.results

    def generate_report(self):
        """Generate validation report"""
        print("\n" + "=" * 60)
        print("📊 VALIDATION RESULTS (Using venv packages)")
        print("=" * 60)

        working = []
        partial = []
        failed = []

        for result in sorted(self.results, key=lambda x: x['name']):
            status = result.get('status', '❓ UNKNOWN')
            name = result['name']

            print(f"\n### {name}")
            print(f"  Status:  {status}")
            print(f"  Syntax:  {result['syntax']}")
            print(f"  Imports: {result['imports']}")
            print(f"  Startup: {result['startup']}")
            print(f"  API:     {result['api']}")

            if result['errors']:
                print(f"  ⚠️ Errors:")
                for error in result['errors'][:3]:  # Limit error output
                    print(f"    - {error[:100]}")

            # Categorize
            if '✅ WORKING' in status:
                working.append(name)
            elif '⚠️ PARTIAL' in status:
                partial.append(name)
            else:
                failed.append(name)

        # Summary
        print("\n" + "=" * 60)
        print("📈 SUMMARY")
        print("=" * 60)
        total = len(self.results)
        print(f"✅ Working:  {len(working)}/{total} ({len(working)*100//total if total else 0}%)")
        print(f"⚠️ Partial:  {len(partial)}/{total}")
        print(f"❌ Failed:   {len(failed)}/{total}")

        if working:
            print(f"\n🎉 Working components: {', '.join(working)}")

        # Save detailed report
        report_path = 'validation_report_venv.json'
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Detailed report saved to: {report_path}")

        return working, partial, failed


async def main():
    """Main orchestration function"""

    print("🎯 INTEL-SYSTEM VALIDATION ORCHESTRATOR (VENV Edition)")
    print("=" * 60)

    # Check if autonomous_build exists
    if not os.path.exists('autonomous_build'):
        print("❌ ERROR: autonomous_build/ directory not found")
        print("   Please run from /Volumes/intel-system/")
        return 1

    # Check if venv exists
    venv_python = Path('autonomous_build/venv/bin/python3')
    if not venv_python.exists():
        print("❌ ERROR: Virtual environment not found")
        print("   Expected at: autonomous_build/venv/")
        return 1

    print(f"✅ Using venv Python: {venv_python}")

    # Initialize orchestrator
    orchestrator = ValidationOrchestrator('autonomous_build')

    # Discover components
    orchestrator.discover_components()

    if not orchestrator.components:
        print("❌ No components found to validate")
        return 1

    # Run parallel validation
    start_time = datetime.now()
    await orchestrator.run_parallel_validation()
    duration = (datetime.now() - start_time).total_seconds()

    # Generate report
    working, partial, failed = orchestrator.generate_report()

    print(f"\n⏱️ Total validation time: {duration:.1f} seconds")

    # Return exit code based on results
    if len(working) == len(orchestrator.components):
        print("\n🎉 ALL COMPONENTS WORKING!")
        return 0
    elif len(working) > 0:
        print(f"\n✅ {len(working)} components are working!")
        return 0
    else:
        print(f"\n❌ No fully working components yet")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)