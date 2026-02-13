#!/usr/bin/env python3
"""
Proper approval polling - matches Wingman's proper_wingman_deployment.py pattern
Blocks until approved/rejected/timeout, returns True/False
"""
import requests
import time
import os
import sys
import subprocess

def poll_approval(request_id: str, api_url: str = None, timeout_sec: int = 3600) -> bool:
    """
    Poll for approval status until approved/rejected/timeout.
    
    Returns:
        True if approved
        False if rejected or timeout
    """
    if api_url is None:
        api_url = os.getenv("WINGMAN_API_URL", "http://127.0.0.1:8101")
    
    poll_sec = float(os.getenv("WINGMAN_APPROVAL_POLL_SEC", "2.0"))
    deadline = time.time() + timeout_sec
    
    print(f"🔄 Polling for approval {request_id[:8]}...")
    print(f"⏱️  Timeout: {timeout_sec}s ({timeout_sec/60:.1f} minutes)")
    print(f"📱 Approve in Telegram while I wait...")
    print("")
    
    attempt = 0
    
    # Get auth headers from bot container (has keys)
    def check_status():
        """Check approval status using bot container's auth"""
        try:
            result = subprocess.run(
                ['docker', 'exec', 'wingman-test-telegram-bot-1',
                 'python3', '-c', f'''
import requests
import os
import json

api_url = os.getenv("API_URL", "http://wingman-api:5000")
headers = {{}}
if os.getenv("WINGMAN_APPROVAL_READ_KEY"):
    headers["X-Wingman-Approval-Read-Key"] = os.getenv("WINGMAN_APPROVAL_READ_KEY")
elif os.getenv("WINGMAN_APPROVAL_API_KEY"):
    headers["X-Wingman-Approval-Key"] = os.getenv("WINGMAN_APPROVAL_API_KEY")

try:
    resp = requests.get(
        f"{{api_url}}/approvals/{request_id}",
        headers=headers,
        timeout=10
    )
    if resp.status_code == 200:
        data = resp.json()
        print(json.dumps({{"status": data.get("status"), "decided_by": data.get("decided_by")}}))
    else:
        print(json.dumps({{"error": resp.status_code}}))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
'''],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout.strip())
                return data
        except Exception:
            pass
        return None
    
    try:
        while time.time() < deadline:
            attempt += 1
            elapsed = int(time.time() - (deadline - timeout_sec))
            
            data = check_status()
            
            if data:
                status = data.get("status")
                
                if status == "APPROVED":
                    decided_by = data.get("decided_by", "unknown")
                    print(f"✅ APPROVED by {decided_by}!")
                    print(f"   (Detected after {elapsed}s, {attempt} polls)")
                    return True
                    
                elif status == "REJECTED":
                    decided_by = data.get("decided_by", "unknown")
                    print(f"❌ REJECTED by {decided_by}")
                    return False
                    
                elif status == "PENDING":
                    # Still pending - show progress every 30 seconds
                    if attempt % 15 == 0:  # Every 30 seconds (15 * 2s)
                        print(f"  ⏳ Still waiting... ({elapsed}s elapsed, poll #{attempt})")
            
            # Sleep before next poll
            time.sleep(poll_sec)
        
        # Timeout
        print(f"⏱️  TIMEOUT after {timeout_sec}s ({attempt} polls)")
        return False
        
    except KeyboardInterrupt:
        print(f"\n⛔ Interrupted while waiting for approval")
        print(f"Request remains pending: {request_id}")
        return False
    except Exception as e:
        print(f"❌ Polling error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: poll_approval.py <request_id> [api_url] [timeout_sec]")
        sys.exit(1)
    
    request_id = sys.argv[1]
    api_url = sys.argv[2] if len(sys.argv) > 2 else None
    timeout_sec = int(sys.argv[3]) if len(sys.argv) > 3 else 3600
    
    approved = poll_approval(request_id, api_url, timeout_sec)
    sys.exit(0 if approved else 1)
