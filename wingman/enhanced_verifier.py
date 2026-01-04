#!/usr/bin/env python3
"""
Enhanced Wingman Verifier - Step B
Combines Mistral 7B analysis with simple verification
"""

import os
import sys
import re
import json
import subprocess
from datetime import datetime

class EnhancedVerifier:
    def __init__(self):
        self.mistral_available = self.check_ollama()

    def check_ollama(self):
        """Check if Ollama and Mistral are available"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "mistral" in result.stdout.lower():
                print("✅ Mistral 7B available via Ollama")
                return True
            else:
                print("⚠️  Mistral not found. Install with: ollama pull mistral")
                return False
        except:
            print("⚠️  Ollama not available. Falling back to simple verification")
            return False

    def analyze_with_mistral(self, claim_text):
        """Use Mistral to analyze the claim"""
        if not self.mistral_available:
            return None

        prompt = f"""Analyze this AI claim and respond with ONLY a JSON object.
Claim: "{claim_text}"

Return ONLY this JSON structure (no other text):
{{
  "action": "CREATE or DELETE or START or STOP or MODIFY or UNKNOWN",
  "targets": ["list", "of", "file", "paths", "or", "process", "names"],
  "verification": "How to verify this claim",
  "confidence": "HIGH or MEDIUM or LOW",
  "explanation": "Brief explanation of the claim"
}}"""

        try:
            result = subprocess.run(
                ["ollama", "run", "mistral", prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            response = result.stdout.strip()

            # Try to parse as JSON
            try:
                # Find JSON in response (Mistral might add text around it)
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    return json.loads(json_str)
                else:
                    # Return raw text if no JSON found
                    return {"raw_response": response}
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured dict from text
                return {"raw_response": response}

        except Exception as e:
            print(f"❌ Mistral analysis failed: {e}")
            return None

    def extract_file_paths(self, text):
        """Extract potential file paths from text"""
        patterns = [
            r'/[^\s]+',  # Unix paths
            r'\w+\.(txt|json|py|md|log|csv|sql|db|tar|zip)',  # Files with extensions
            r'[A-Za-z]:\\[^\s]+',  # Windows paths
        ]

        paths = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            paths.extend(matches)

        # Clean up paths
        cleaned_paths = []
        for path in paths:
            # Remove trailing punctuation
            path = path.rstrip('.,;:!?"\'')
            if len(path) > 3 and '/' in path or '\\' in path or '.' in path:
                cleaned_paths.append(path)

        return list(set(cleaned_paths))

    def extract_process_names(self, text):
        """Extract potential process or service names"""
        text_lower = text.lower()

        # Known service names to look for
        known_services = [
            'docker', 'nginx', 'apache', 'mysql', 'postgres', 'postgresql',
            'redis', 'mongodb', 'elasticsearch', 'kibana', 'grafana',
            'prometheus', 'node', 'python', 'java', 'tomcat', 'jenkins'
        ]

        processes = []

        # Check for known services
        for service in known_services:
            if service in text_lower:
                processes.append(service)

        # Look for "X service" or "service X" patterns
        service_patterns = [
            r'(\w+)\s+service',
            r'service\s+(\w+)',
        ]

        for pattern in service_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                # Filter out common words that aren't services
                if match not in ['the', 'a', 'an', 'and', 'or', 'is', 'was', 'been']:
                    processes.append(match)

        return list(set(processes))

    def check_file_exists(self, filepath):
        """Check if a file actually exists"""
        try:
            return os.path.exists(filepath)
        except:
            return False

    def check_process_running(self, process_name):
        """Check if a process is running"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", process_name],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return None  # Can't check

    def determine_action(self, text):
        """Determine what action the AI claimed"""
        text_lower = text.lower()

        if any(word in text_lower for word in ["created", "made", "generated", "wrote"]):
            return "CREATE"
        elif any(word in text_lower for word in ["deleted", "removed", "erased"]):
            return "DELETE"
        elif any(word in text_lower for word in ["started", "launched", "running"]):
            return "START"
        elif any(word in text_lower for word in ["stopped", "killed", "terminated"]):
            return "STOP"
        elif any(word in text_lower for word in ["modified", "edited", "updated", "changed"]):
            return "MODIFY"
        else:
            return "UNKNOWN"

    def verify_claim(self, claim_text):
        """Enhanced verification with Mistral analysis"""
        print(f"\n🔍 Enhanced Verification: {claim_text}")
        print("=" * 60)

        # Step 1: Analyze with Mistral
        print("\n📊 Mistral Analysis:")
        print("-" * 40)
        mistral_analysis = self.analyze_with_mistral(claim_text)
        if mistral_analysis:
            if isinstance(mistral_analysis, dict):
                if "raw_response" in mistral_analysis:
                    print(f"Raw: {mistral_analysis['raw_response'][:300]}...")
                else:
                    print(f"Action: {mistral_analysis.get('action', 'N/A')}")
                    print(f"Targets: {mistral_analysis.get('targets', [])}")
                    print(f"Confidence: {mistral_analysis.get('confidence', 'N/A')}")
                    print(f"Explanation: {mistral_analysis.get('explanation', 'N/A')}")
        else:
            print("⚠️  Mistral analysis not available")

        # Step 2: Extract targets
        print("\n🎯 Extracted Targets:")
        print("-" * 40)

        file_paths = self.extract_file_paths(claim_text)
        process_names = self.extract_process_names(claim_text)
        action = self.determine_action(claim_text)

        print(f"Action: {action}")
        print(f"Files: {file_paths if file_paths else 'None'}")
        print(f"Processes: {process_names if process_names else 'None'}")

        # Step 3: Verify targets
        print("\n✅ Verification Results:")
        print("-" * 40)

        file_results = []
        process_results = []

        # Check files
        for filepath in file_paths:
            exists = self.check_file_exists(filepath)
            file_results.append({
                'path': filepath,
                'exists': exists,
                'action': action
            })

            status = "✅ EXISTS" if exists else "❌ MISSING"
            print(f"File: {filepath} - {status}")

        # Check processes
        for process in process_names:
            running = self.check_process_running(process)
            process_results.append({
                'name': process,
                'running': running,
                'action': action
            })

            if running is None:
                status = "❓ UNKNOWN"
            elif running:
                status = "✅ RUNNING"
            else:
                status = "❌ NOT RUNNING"
            print(f"Process: {process} - {status}")

        # Step 4: Determine verdict
        print("\n🏁 VERDICT:")
        print("-" * 40)

        verdict = self.calculate_verdict(action, file_results, process_results)

        # Add Mistral context if available
        if mistral_analysis and isinstance(mistral_analysis, dict):
            print(f"\n💭 Mistral Context:")
            if "confidence" in mistral_analysis:
                conf = mistral_analysis["confidence"]
                if conf == "HIGH":
                    print("  Confidence: HIGH - Claim appears plausible")
                elif conf == "LOW":
                    print("  Confidence: LOW - Claim seems suspicious")
                else:
                    print("  Confidence: MEDIUM - Claim needs verification")
            if "explanation" in mistral_analysis:
                print(f"  Analysis: {mistral_analysis['explanation']}")

        return verdict

    def calculate_verdict(self, action, file_results, process_results):
        """Calculate final verdict based on action and results"""

        # File-based verdicts
        if file_results:
            if action == "CREATE":
                missing = [f for f in file_results if not f['exists']]
                if missing:
                    print(f"🚨 FALSE - AI claimed to create {len(missing)} files that don't exist")
                    for f in missing:
                        print(f"   Missing: {f['path']}")
                    return "FALSE"
                else:
                    print(f"✅ TRUE - All {len(file_results)} claimed files exist")
                    return "TRUE"

            elif action == "DELETE":
                existing = [f for f in file_results if f['exists']]
                if existing:
                    print(f"🚨 FALSE - AI claimed to delete {len(existing)} files that still exist")
                    for f in existing:
                        print(f"   Still exists: {f['path']}")
                    return "FALSE"
                else:
                    print(f"✅ TRUE - All {len(file_results)} files successfully deleted")
                    return "TRUE"

        # Process-based verdicts
        if process_results:
            if action == "START":
                not_running = [p for p in process_results if p['running'] is False]
                if not_running:
                    print(f"🚨 FALSE - AI claimed to start {len(not_running)} processes not running")
                    for p in not_running:
                        print(f"   Not running: {p['name']}")
                    return "FALSE"
                else:
                    running = [p for p in process_results if p['running'] is True]
                    if running:
                        print(f"✅ TRUE - {len(running)} processes are running")
                        return "TRUE"
                    else:
                        print(f"❓ UNVERIFIABLE - Cannot check process status")
                        return "UNVERIFIABLE"

            elif action == "STOP":
                running = [p for p in process_results if p['running'] is True]
                if running:
                    print(f"🚨 FALSE - AI claimed to stop {len(running)} processes still running")
                    for p in running:
                        print(f"   Still running: {p['name']}")
                    return "FALSE"
                else:
                    print(f"✅ TRUE - All processes successfully stopped")
                    return "TRUE"

        # No verifiable targets
        if not file_results and not process_results:
            print(f"❓ UNVERIFIABLE - No targets found to verify")
            return "UNVERIFIABLE"

        # Default
        print(f"❓ UNVERIFIABLE - Cannot determine claim validity")
        return "UNVERIFIABLE"

def main():
    """
    DEV-only helper.

    Note: In normal operation, Wingman should route claims to this
    verifier via the API layer, not by executing this module directly.
    """
    print("🚀 Enhanced Wingman Verifier (DEV helper, with Mistral 7B)")
    print("=" * 60)

    verifier = EnhancedVerifier()

    if len(sys.argv) > 1:
        claim = " ".join(sys.argv[1:])
        verifier.verify_claim(claim)
    else:
        print("\nEnter AI claims to verify (or 'quit' to exit):")
        print("Examples:")
        print("  - I created /tmp/backup.tar")
        print("  - I started the Docker service")
        print("  - I deleted all log files")

        while True:
            claim = input("\n> ").strip()
            if claim.lower() in ['quit', 'exit', 'q']:
                break
            if claim:
                verifier.verify_claim(claim)

    print("\n✅ Enhanced verification complete!")

# Intentionally no __main__ block – engine is used via Wingman API only.