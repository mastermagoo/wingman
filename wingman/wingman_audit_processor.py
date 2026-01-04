#!/usr/bin/env python3
"""
Wingman Audit Processor - Phase 3 "Technical Truth"
Processes the audit log and runs actual verifications.
"""

import json
import requests
import os
from datetime import datetime

# In Docker environments, we connect via the service name or localhost mapping
API_URL = os.getenv("WINGMAN_API_URL", "http://localhost:8101")

def process_audit_log(log_path="data/claims_audit.jsonl"):
    if not os.path.exists(log_path):
        print(f"❌ Error: {log_path} not found")
        return

    print(f"🔍 WINGMAN AUDITOR: Starting verification loop...")
    processed_entries = []
    
    try:
        with open(log_path, "r") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if entry.get("status") == "PENDING_VERIFICATION":
                    print(f"\n🧐 Checking claim: '{entry['claim'][:50]}...'")
                    
                    # Call Phase 1 /verify endpoint
                    try:
                        r = requests.post(f"{API_URL}/verify", json={"claim": entry['claim']}, timeout=10)
                        
                        if r.status_code == 200:
                            verdict = r.json().get("verdict", "UNVERIFIABLE")
                            entry["status"] = verdict
                            entry["verified_at"] = datetime.now().isoformat()
                            print(f"   ⚖️  VERDICT: {verdict}")
                        else:
                            print(f"   ⚠️  Verification failed (API error {r.status_code})")
                    except Exception as e:
                        print(f"   ⚠️  Connection error: {e}")
                
                processed_entries.append(entry)
        
        # Save updated log
        with open(log_path, "w") as f:
            for entry in processed_entries:
                f.write(json.dumps(entry) + "\n")
        
        print(f"\n✅ Audit complete. Log updated.")
        
    except Exception as e:
        print(f"❌ Error processing audit log: {e}")

if __name__ == "__main__":
    process_audit_log()

