#!/usr/bin/env python3
"""
Simple Wingman Verifier - Bottom Up Build
Just the basics that actually work
"""

import os
import sys
import re
from datetime import datetime

def extract_file_paths(text):
    """Extract potential file paths from text"""
    # Improved patterns based on enhanced verifier
    patterns = [
        r'/[^\s]+',  # Unix paths
        r'\w+\.(txt|json|py|md|log|csv|sql|db|tar|zip|conf|cfg|yaml|yml)',  # More extensions
        r'[A-Za-z]:\\[^\s]+',  # Windows paths
    ]

    paths = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        paths.extend(matches)

    # Clean up paths - remove trailing punctuation
    cleaned_paths = []
    for path in paths:
        # Remove trailing punctuation
        path = path.rstrip('.,;:!?"\'')
        # Only include if it looks like a real path
        if len(path) > 3 and ('/' in path or '\\' in path or '.' in path):
            cleaned_paths.append(path)

    return list(set(cleaned_paths))  # Remove duplicates

def extract_process_names(text):
    """Extract potential process or service names"""
    text_lower = text.lower()

    # Known service names
    known_services = [
        'docker', 'nginx', 'apache', 'mysql', 'postgres', 'postgresql',
        'redis', 'mongodb', 'elasticsearch', 'node', 'python', 'java'
    ]

    processes = []
    for service in known_services:
        if service in text_lower:
            processes.append(service)

    return list(set(processes))

def check_file_exists(filepath):
    """Check if a file actually exists"""
    try:
        return os.path.exists(filepath)
    except:
        return False

def check_process_running(process_name):
    """Check if a process is running (basic check)"""
    try:
        import subprocess
        result = subprocess.run(
            ["pgrep", "-f", process_name],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return None  # Can't check

def verify_claim(claim_text):
    """Main verification function - enhanced but still simple"""
    print(f"\n🔍 Verifying: {claim_text}")
    print("-" * 50)

    # Extract targets from the claim
    file_paths = extract_file_paths(claim_text)
    process_names = extract_process_names(claim_text)

    if not file_paths and not process_names:
        print("❌ No verifiable targets found in claim")
        return "UNVERIFIABLE"

    file_results = []
    process_results = []

    # Check files
    for filepath in file_paths:
        exists = check_file_exists(filepath)
        file_results.append({
            'path': filepath,
            'exists': exists
        })

        if exists:
            print(f"✅ File exists: {filepath}")
        else:
            print(f"❌ File missing: {filepath}")

    # Check processes
    for process in process_names:
        running = check_process_running(process)
        process_results.append({
            'name': process,
            'running': running
        })

        if running is None:
            print(f"❓ Process {process}: Cannot check")
        elif running:
            print(f"✅ Process running: {process}")
        else:
            print(f"❌ Process not running: {process}")
    
    # Determine verdict based on claim type
    claim_lower = claim_text.lower()

    # File operations
    if file_results:
        if "created" in claim_lower or "made" in claim_lower or "generated" in claim_lower or "wrote" in claim_lower:
            # AI claims to have created files
            missing_files = [r for r in file_results if not r['exists']]
            if missing_files:
                print(f"\n🚨 VERDICT: FALSE")
                print(f"   AI claimed to create {len(missing_files)} files that don't exist")
                return "FALSE"
            else:
                print(f"\n✅ VERDICT: TRUE")
                print(f"   All claimed files exist")
                return "TRUE"

        elif "deleted" in claim_lower or "removed" in claim_lower:
            # AI claims to have deleted files
            existing_files = [r for r in file_results if r['exists']]
            if existing_files:
                print(f"\n🚨 VERDICT: FALSE")
                print(f"   AI claimed to delete {len(existing_files)} files that still exist")
                return "FALSE"
            else:
                print(f"\n✅ VERDICT: TRUE")
                print(f"   All claimed files are gone")
                return "TRUE"

    # Process operations
    if process_results:
        if "started" in claim_lower or "launched" in claim_lower or "running" in claim_lower:
            # AI claims to have started processes
            not_running = [r for r in process_results if r['running'] is False]
            if not_running:
                print(f"\n🚨 VERDICT: FALSE")
                print(f"   AI claimed to start {len(not_running)} processes not running")
                return "FALSE"
            else:
                running = [r for r in process_results if r['running'] is True]
                if running:
                    print(f"\n✅ VERDICT: TRUE")
                    print(f"   {len(running)} processes are running")
                    return "TRUE"

        elif "stopped" in claim_lower or "killed" in claim_lower or "terminated" in claim_lower:
            # AI claims to have stopped processes
            running = [r for r in process_results if r['running'] is True]
            if running:
                print(f"\n🚨 VERDICT: FALSE")
                print(f"   AI claimed to stop {len(running)} processes still running")
                return "FALSE"
            else:
                print(f"\n✅ VERDICT: TRUE")
                print(f"   All processes successfully stopped")
                return "TRUE"

    # Default
    print(f"\n❓ VERDICT: UNVERIFIABLE")
    print(f"   Can't determine claim validity")
    return "UNVERIFIABLE"

def main():
    """Main function"""
    print("🚀 Simple Wingman Verifier")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # Command line argument
        claim = " ".join(sys.argv[1:])
        verify_claim(claim)
    else:
        # Interactive mode
        print("Enter AI claims to verify (or 'quit' to exit):")
        while True:
            claim = input("\n> ").strip()
            if claim.lower() in ['quit', 'exit', 'q']:
                break
            if claim:
                verify_claim(claim)
    
    print("\n✅ Verification complete!")

if __name__ == "__main__":
    main()
