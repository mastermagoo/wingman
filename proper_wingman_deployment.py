#!/usr/bin/env python3
"""
Proper Wingman Deployment - 100% Gatekeeping
Uses actual Wingman verifier to check deliverables and BLOCKS until 100% complete
"""

import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
WINGMAN_DIR = BASE_DIR / "wingman"
OUTPUT_DIR = BASE_DIR / "mega_delegation_output"
WORKERS_DIR = BASE_DIR / "ai-workers" / "workers"

def use_wingman_verifier(claim_text):
    """Use actual Wingman verifier to check claim"""
    simple_verifier = WINGMAN_DIR / "simple_verifier.py"
    
    if not simple_verifier.exists():
        print(f"⚠️  Wingman verifier not found: {simple_verifier}")
        return "UNVERIFIABLE"
    
    try:
        result = subprocess.run(
            ["python3", str(simple_verifier), claim_text],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse verdict from output
        output = result.stdout
        if "VERDICT: TRUE" in output:
            return "TRUE"
        elif "VERDICT: FALSE" in output:
            return "FALSE"
        else:
            return "UNVERIFIABLE"
    except Exception as e:
        print(f"⚠️  Wingman verification error: {e}")
        return "UNVERIFIABLE"

def verify_deliverable_with_wingman(worker_id, deliverable, test_process):
    """Verify deliverable actually exists using enhanced verifier"""
    # Use enhanced verifier that actually checks TEST environment
    enhanced_verifier = BASE_DIR / "enhanced_wingman_verifier.py"
    
    if enhanced_verifier.exists():
        try:
            result = subprocess.run(
                ["python3", str(enhanced_verifier), deliverable, str(worker_id)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse verdict
            output = result.stdout
            if "Verdict: TRUE" in output:
                evidence = output.split("Evidence: ")[1].strip() if "Evidence: " in output else "Verified"
                return "TRUE", evidence
            elif "Verdict: FALSE" in output:
                evidence = output.split("Evidence: ")[1].strip() if "Evidence: " in output else "Not verified"
                return "FALSE", evidence
            else:
                evidence = output.split("Evidence: ")[1].strip() if "Evidence: " in output else "Cannot verify"
                return "UNVERIFIABLE", evidence
        except Exception as e:
            return "UNVERIFIABLE", f"Verification error: {str(e)[:100]}"
    
    # Fallback to simple checks
    deliverable_lower = deliverable.lower()
    
    if "schema" in deliverable_lower and "postgresql" in deliverable_lower:
        # Actually check PostgreSQL
        try:
            result = subprocess.run(
                ["psql", "-h", "localhost", "-p", "6432", "-U", "admin", "-d", "intel_system_test", "-c", "\\dn sap_deutschland"],
                capture_output=True,
                text=True,
                timeout=10,
                env={"PGPASSWORD": "secure_pass_2024"}
            )
            if result.returncode == 0 and "sap_deutschland" in result.stdout:
                return "TRUE", "Schema exists in PostgreSQL TEST"
            else:
                return "FALSE", "Schema NOT found in PostgreSQL TEST"
        except:
            return "UNVERIFIABLE", "Cannot connect to PostgreSQL TEST"
    
    elif deliverable.endswith('.py') or deliverable.endswith('.sql'):
        file_path = OUTPUT_DIR / f"worker_{worker_id:03d}" / deliverable.split('/')[-1].replace('`', '').strip()
        if file_path.exists():
            return "TRUE", f"File exists: {file_path}"
        else:
            return "FALSE", f"File does not exist: {file_path}"
    
    return "UNVERIFIABLE", "Cannot verify this deliverable type"

def deploy_worker_with_wingman_gate(worker_id):
    """Deploy worker and verify with Wingman - BLOCK if not 100%"""
    print(f"\n{'='*70}")
    print(f"WORKER {worker_id}: Deployment with Wingman Gate")
    print(f"{'='*70}")
    
    # Load instruction
    instruction_file = list(WORKERS_DIR.glob(f"WORKER_{worker_id:03d}_*.md"))
    if not instruction_file:
        print(f"❌ Instruction file not found")
        return False
    
    instruction = instruction_file[0].read_text()
    
    # Extract deliverables and test process
    deliverables = []
    test_process = ""
    
    if "## 1. DELIVERABLES" in instruction:
        deliv_section = instruction.split("## 1. DELIVERABLES")[1].split("## 2. SUCCESS_CRITERIA")[0]
        for line in deliv_section.split('\n'):
            if '- [ ]' in line or '- [x]' in line:
                deliverable = line.replace('- [ ]', '').replace('- [x]', '').strip()
                if deliverable:
                    deliverables.append(deliverable)
    
    if "## 6. TEST_PROCESS" in instruction:
        test_section = instruction.split("## 6. TEST_PROCESS")[1].split("## 7. TEST_RESULTS_FORMAT")[0]
        test_process = test_section.strip()
    
    print(f"\n📋 Deliverables to verify: {len(deliverables)}")
    
    # Execute worker (if code exists)
    worker_dir = OUTPUT_DIR / f"worker_{worker_id:03d}"
    if worker_dir.exists():
        main_script = worker_dir / f"worker_{worker_id:03d}.py"
        if not main_script.exists():
            main_script = list(worker_dir.glob("create_*.py"))
            if main_script:
                main_script = main_script[0]
        
        if main_script and main_script.exists():
            print(f"🔄 Executing: {main_script.name}")
            try:
                result = subprocess.run(
                    ["python3", str(main_script)],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=str(worker_dir)
                )
                if result.returncode == 0:
                    print(f"   ✅ Execution completed")
                else:
                    print(f"   ⚠️  Execution had issues")
            except Exception as e:
                print(f"   ⚠️  Execution error: {str(e)[:100]}")
    
    # Verify each deliverable with Wingman
    print(f"\n🔍 Wingman Verification:")
    all_verified = True
    verification_results = []
    
    for deliverable in deliverables:
        verdict, evidence = verify_deliverable_with_wingman(worker_id, deliverable, test_process)
        verification_results.append({
            "deliverable": deliverable,
            "verdict": verdict,
            "evidence": evidence
        })
        
        if verdict == "TRUE":
            print(f"   ✅ {deliverable[:60]}... - VERIFIED")
        elif verdict == "FALSE":
            print(f"   ❌ {deliverable[:60]}... - NOT VERIFIED")
            all_verified = False
        else:
            print(f"   ❓ {deliverable[:60]}... - UNVERIFIABLE")
            # For unverifiable, we need manual check
            all_verified = False
    
    # WINGMAN GATE: Block if not 100% verified
    if not all_verified:
        print(f"\n🚨 WINGMAN GATE: BLOCKED")
        print(f"   Worker {worker_id} NOT 100% verified")
        print(f"   Cannot proceed to next worker")
        print(f"   Fix issues and re-verify")
        return False
    
    print(f"\n✅ WINGMAN GATE: PASSED")
    print(f"   Worker {worker_id} 100% verified")
    print(f"   Proceeding to next worker")
    
    return True

def deploy_phase_with_wingman_gate(phase_name, worker_ids):
    """Deploy phase with Wingman gatekeeping - BLOCKS until 100% complete"""
    print(f"\n{'='*70}")
    print(f"PHASE: {phase_name}")
    print(f"WINGMAN GATEKEEPING: ENABLED")
    print(f"Workers: {worker_ids[0]}-{worker_ids[-1]} ({len(worker_ids)} workers)")
    print(f"{'='*70}")
    
    results = []
    all_verified = True
    
    for worker_id in worker_ids:
        verified = deploy_worker_with_wingman_gate(worker_id)
        results.append({
            "worker_id": worker_id,
            "wingman_verified": verified
        })
        
        if not verified:
            all_verified = False
            print(f"\n🚨 PHASE BLOCKED: Worker {worker_id} not verified")
            print(f"   Fix Worker {worker_id} before proceeding")
            break  # STOP - Wingman gate blocks progression
    
    # WINGMAN PHASE GATE: Block if not 100%
    if not all_verified:
        print(f"\n{'='*70}")
        print(f"🚨 WINGMAN PHASE GATE: BLOCKED")
        print(f"{'='*70}")
        print(f"Phase {phase_name} NOT 100% complete")
        print(f"Cannot proceed to next phase")
        print(f"Fix all workers and re-verify")
        return False
    
    print(f"\n{'='*70}")
    print(f"✅ WINGMAN PHASE GATE: PASSED")
    print(f"{'='*70}")
    print(f"Phase {phase_name} 100% verified")
    print(f"Proceeding to next phase")
    
    return True

def main():
    print("=" * 70)
    print("PROPER WINGMAN DEPLOYMENT - 100% GATEKEEPING")
    print("=" * 70)
    print("Rules:")
    print("1. Verify each deliverable with actual Wingman verifier")
    print("2. Block worker if not 100% verified")
    print("3. Block phase if not 100% complete")
    print("4. Only proceed when Wingman says TRUE")
    print("=" * 70)
    
    # Phase 1 with Wingman gate
    phase1_verified = deploy_phase_with_wingman_gate("Phase 1: SAP Namespace", list(range(1, 21)))
    
    if not phase1_verified:
        print(f"\n🚨 STOPPING: Phase 1 not 100% verified")
        print(f"   Fix issues and re-run")
        sys.exit(1)
    
    # Only proceed if Phase 1 is 100%
    print(f"\n✅ Phase 1 100% verified - Proceeding to Phase 2")
    
    # Phase 2 with Wingman gate
    phase2_verified = deploy_phase_with_wingman_gate("Phase 2: Multi-Tenant", list(range(21, 41)))
    
    if not phase2_verified:
        print(f"\n🚨 STOPPING: Phase 2 not 100% verified")
        sys.exit(1)
    
    print(f"\n✅ All phases 100% verified by Wingman")

if __name__ == "__main__":
    main()

