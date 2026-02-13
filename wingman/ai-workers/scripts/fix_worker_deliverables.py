#!/usr/bin/env python3
"""
Fix all 225 worker instructions to include file paths in DELIVERABLES
Ensures orchestrator can properly write generated code to files
"""

import re
from pathlib import Path
from typing import Dict, List

# Mapping of worker types to their output file paths
WORKER_FILE_PATHS: Dict[str, str] = {
    # Phase 1: Semantic Analyzer (WORKER_001-018)
    "WORKER_001": "wingman/validation/semantic_analyzer.py",
    "WORKER_002": "wingman/validation/semantic_analyzer.py",
    "WORKER_003": "wingman/validation/semantic_analyzer.py",
    "WORKER_004": "wingman/validation/semantic_analyzer.py",
    "WORKER_005": "wingman/validation/semantic_analyzer.py",
    "WORKER_006": "wingman/validation/semantic_analyzer.py",
    "WORKER_007": "wingman/validation/semantic_analyzer.py",
    "WORKER_008": "wingman/validation/semantic_analyzer.py",
    "WORKER_009": "wingman/validation/semantic_analyzer.py",
    "WORKER_010": "wingman/validation/semantic_analyzer.py",
    "WORKER_011": "wingman/validation/semantic_analyzer.py",
    "WORKER_012": "wingman/validation/semantic_analyzer.py",
    "WORKER_013": "wingman/tests/test_semantic_analyzer.py",
    "WORKER_014": "wingman/tests/test_semantic_analyzer.py",
    "WORKER_015": "wingman/tests/test_semantic_analyzer.py",
    "WORKER_016": "wingman/tests/test_semantic_analyzer.py",
    "WORKER_017": "wingman/tests/test_semantic_analyzer.py",
    "WORKER_018": "wingman/tests/test_semantic_analyzer.py",

    # Phase 1: Code Scanner (WORKER_019-036)
    "WORKER_019": "wingman/validation/code_scanner.py",
    "WORKER_020": "wingman/validation/code_scanner.py",
    "WORKER_021": "wingman/validation/code_scanner.py",
    "WORKER_022": "wingman/validation/code_scanner.py",
    "WORKER_023": "wingman/validation/code_scanner.py",
    "WORKER_024": "wingman/validation/code_scanner.py",
    "WORKER_025": "wingman/validation/code_scanner.py",
    "WORKER_026": "wingman/validation/code_scanner.py",
    "WORKER_027": "wingman/validation/code_scanner.py",
    "WORKER_028": "wingman/validation/code_scanner.py",
    "WORKER_029": "wingman/validation/code_scanner.py",
    "WORKER_030": "wingman/validation/code_scanner.py",
    "WORKER_031": "wingman/validation/code_scanner.py",
    "WORKER_032": "wingman/validation/code_scanner.py",
    "WORKER_033": "wingman/validation/code_scanner.py",
    "WORKER_034": "wingman/tests/test_code_scanner.py",
    "WORKER_035": "wingman/tests/test_code_scanner.py",
    "WORKER_036": "wingman/tests/test_code_scanner.py",

    # Phase 1: Dependency Analyzer (WORKER_037-054)
    "WORKER_037": "wingman/validation/dependency_analyzer.py",
    "WORKER_038": "wingman/validation/dependency_analyzer.py",
    "WORKER_039": "wingman/validation/dependency_analyzer.py",
    "WORKER_040": "wingman/validation/dependency_analyzer.py",
    "WORKER_041": "wingman/validation/dependency_analyzer.py",
    "WORKER_042": "wingman/validation/dependency_analyzer.py",
    "WORKER_043": "wingman/validation/dependency_analyzer.py",
    "WORKER_044": "wingman/validation/dependency_analyzer.py",
    "WORKER_045": "wingman/validation/dependency_analyzer.py",
    "WORKER_046": "wingman/validation/dependency_analyzer.py",
    "WORKER_047": "wingman/validation/dependency_analyzer.py",
    "WORKER_048": "wingman/validation/dependency_analyzer.py",
    "WORKER_049": "wingman/validation/dependency_analyzer.py",
    "WORKER_050": "wingman/validation/dependency_analyzer.py",
    "WORKER_051": "wingman/tests/test_dependency_analyzer.py",
    "WORKER_052": "wingman/tests/test_dependency_analyzer.py",
    "WORKER_053": "wingman/tests/test_dependency_analyzer.py",
    "WORKER_054": "wingman/tests/test_dependency_analyzer.py",

    # Phase 2: Content Quality (WORKER_055-087)
    "WORKER_055": "wingman/validation/content_quality_validator.py",
    "WORKER_056": "wingman/validation/content_quality_validator.py",
    "WORKER_057": "wingman/validation/content_quality_validator.py",
    "WORKER_058": "wingman/validation/content_quality_validator.py",
    "WORKER_059": "wingman/validation/content_quality_validator.py",
    "WORKER_060": "wingman/validation/content_quality_validator.py",
    "WORKER_061": "wingman/validation/content_quality_validator.py",
    "WORKER_062": "wingman/validation/content_quality_validator.py",
    "WORKER_063": "wingman/validation/content_quality_validator.py",
    "WORKER_064": "wingman/validation/content_quality_validator.py",
    "WORKER_065": "wingman/validation/content_quality_validator.py",
    "WORKER_066": "wingman/validation/content_quality_validator.py",
    "WORKER_067": "wingman/validation/content_quality_validator.py",
    "WORKER_068": "wingman/validation/content_quality_validator.py",
    "WORKER_069": "wingman/validation/content_quality_validator.py",
    "WORKER_070": "wingman/validation/content_quality_validator.py",
    "WORKER_071": "wingman/validation/content_quality_validator.py",
    "WORKER_072": "wingman/validation/content_quality_validator.py",
    "WORKER_073": "wingman/validation/content_quality_validator.py",
    "WORKER_074": "wingman/validation/content_quality_validator.py",
    "WORKER_075": "wingman/validation/content_quality_validator.py",
    "WORKER_076": "wingman/validation/content_quality_validator.py",
    "WORKER_077": "wingman/validation/content_quality_validator.py",
    "WORKER_078": "wingman/validation/content_quality_validator.py",
    "WORKER_079": "wingman/validation/content_quality_validator.py",
    "WORKER_080": "wingman/tests/test_content_quality_validator.py",
    "WORKER_081": "wingman/tests/test_content_quality_validator.py",
    "WORKER_082": "wingman/tests/test_content_quality_validator.py",
    "WORKER_083": "wingman/tests/test_content_quality_validator.py",
    "WORKER_084": "wingman/tests/test_content_quality_validator.py",
    "WORKER_085": "wingman/tests/test_content_quality_validator.py",
    "WORKER_086": "wingman/tests/test_content_quality_validator.py",
    "WORKER_087": "wingman/tests/test_content_quality_validator.py",

    # Phase 3-6: Integration, Testing, Deployment, Tuning (WORKER_088-225)
    # These workers output to various files - will be filled dynamically
}

# Auto-populate remaining workers (088-225) with sensible defaults
for i in range(88, 226):
    worker_id = f"WORKER_{i:03d}"
    if i <= 102:  # Integration
        WORKER_FILE_PATHS[worker_id] = "wingman/validation/composite_validator.py"
    elif i <= 210:  # Tests
        WORKER_FILE_PATHS[worker_id] = f"wingman/tests/test_integration_{i:03d}.py"
    elif i <= 219:  # Deployment
        WORKER_FILE_PATHS[worker_id] = f"wingman/deployment/deploy_{i:03d}.sh"
    else:  # Tuning
        WORKER_FILE_PATHS[worker_id] = "wingman/validation/tuning_config.py"


def fix_worker_deliverables(worker_file: Path) -> bool:
    """Fix DELIVERABLES section to include file path in backticks"""
    content = worker_file.read_text()

    # Extract worker ID from filename
    match = re.match(r'WORKER_(\d+)_', worker_file.name)
    if not match:
        print(f"❌ {worker_file.name}: Invalid filename format")
        return False

    worker_id = f"WORKER_{match.group(1)}"

    # Get the file path for this worker
    file_path = WORKER_FILE_PATHS.get(worker_id)
    if not file_path:
        print(f"⚠️  {worker_id}: No file path mapping found")
        return False

    # Check if DELIVERABLES section already has file path in backticks
    if f"`{file_path}`" in content:
        print(f"✓ {worker_id}: Already has file path")
        return True

    # Find and update DELIVERABLES section
    deliverables_pattern = r'(## 1\. DELIVERABLES\s*\n\s*\n)(.*?)(\n\s*\n##|---)'

    def add_file_path(match):
        header = match.group(1)
        deliverables = match.group(2)
        footer = match.group(3)

        # Add file path as first deliverable if not present
        new_deliverables = f"- [ ] Create/update file: `{file_path}`\n{deliverables}"
        return header + new_deliverables + footer

    new_content, count = re.subn(deliverables_pattern, add_file_path, content, flags=re.DOTALL)

    if count > 0:
        worker_file.write_text(new_content)
        print(f"✅ {worker_id}: Added file path `{file_path}`")
        return True
    else:
        print(f"❌ {worker_id}: Could not find DELIVERABLES section")
        return False


def main():
    """Fix all worker instructions"""
    workers_dir = Path("ai-workers/workers")

    if not workers_dir.exists():
        print(f"❌ Workers directory not found: {workers_dir}")
        return

    worker_files = sorted(workers_dir.glob("WORKER_*.md"))
    print(f"📋 Found {len(worker_files)} worker files\n")

    fixed = 0
    skipped = 0
    failed = 0

    for worker_file in worker_files:
        result = fix_worker_deliverables(worker_file)
        if result:
            fixed += 1
        else:
            if "`" in worker_file.read_text():
                skipped += 1
            else:
                failed += 1

    print(f"\n📊 SUMMARY:")
    print(f"   ✅ Fixed: {fixed}")
    print(f"   ✓ Skipped (already fixed): {skipped}")
    print(f"   ❌ Failed: {failed}")
    print(f"   Total: {len(worker_files)}")


if __name__ == "__main__":
    main()
