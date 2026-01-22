#!/usr/bin/env python3
"""
Wingman Approval Client Library
Reusable client for submitting approval requests to Wingman authority.

All systems (intel-system, mem0, etc.) must use this to request approval
for destructive operations. NO independent approval systems allowed.
"""
import requests
import time
import os
from typing import Dict, Optional, Any


class WingmanApprovalClient:
    """
    Client for submitting approval requests to Wingman.
    
    Usage:
        client = WingmanApprovalClient(api_url="http://127.0.0.1:5001")
        approved = client.request_approval(
            worker_id="intel-dr-script",
            task_name="Stop Intel-System PRD",
            instruction="...",
            deployment_env="prd"
        )
        if approved:
            # Execute operation
    """
    
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize client.
        
        Args:
            api_url: Wingman API URL (explicit override; if None, will be resolved from env vars based on deployment_env)
            api_key: Approval request key (defaults to WINGMAN_APPROVAL_REQUEST_KEY env var)
        """
        # Store explicit override (highest priority) or None for dynamic resolution
        self._api_url_override = api_url.rstrip("/") if api_url else None
        self.api_key = api_key or os.getenv("WINGMAN_APPROVAL_REQUEST_KEY", "")
        
        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["X-Wingman-Approval-Request-Key"] = self.api_key
        
        # Polling configuration
        self.poll_interval = float(os.getenv("WINGMAN_APPROVAL_POLL_SEC", "2.0"))
        self.timeout_sec = float(os.getenv("WINGMAN_APPROVAL_TIMEOUT_SEC", "3600"))
    
    def _resolve_api_url(self, deployment_env: str = "test") -> str:
        """
        Resolve the correct API URL based on deployment environment.
        
        Priority (highest to lowest):
        1. Explicit api_url override (passed to __init__)
        2. WINGMAN_API_URL_TEST (if deployment_env="test")
        3. WINGMAN_API_URL_PRD (if deployment_env="prd")
        4. WINGMAN_API_URL (fallback)
        5. Default PRD URL (http://127.0.0.1:5001)
        
        This ensures cold restart capability: env vars persist in .env files.
        
        Args:
            deployment_env: Environment name (test/prd)
            
        Returns:
            Resolved API URL string
        """
        # Priority 1: Explicit override
        if self._api_url_override:
            return self._api_url_override
        
        env_lower = (deployment_env or "").strip().lower()
        
        # Priority 2-3: Environment-specific URLs
        if env_lower == "test":
            test_url = os.getenv("WINGMAN_API_URL_TEST", "").strip()
            if test_url:
                return test_url.rstrip("/")
        elif env_lower in ("prd", "prod", "production"):
            prd_url = os.getenv("WINGMAN_API_URL_PRD", "").strip()
            if prd_url:
                return prd_url.rstrip("/")
        
        # Priority 4: Generic fallback
        generic_url = os.getenv("WINGMAN_API_URL", "").strip()
        if generic_url:
            return generic_url.rstrip("/")
        
        # Priority 5: Default (PRD)
        return "http://127.0.0.1:5001"
    
    def request_approval(
        self,
        worker_id: str,
        task_name: str,
        instruction: str,
        deployment_env: str = "test",
        timeout_sec: Optional[float] = None
    ) -> bool:
        """
        Submit approval request to Wingman and wait for decision.
        
        Args:
            worker_id: Identifier for the worker/script requesting approval
            task_name: Human-readable task name
            instruction: Full instruction text (must include 10-point framework)
            deployment_env: Environment (test/prd)
            timeout_sec: Override default timeout
            
        Returns:
            True if approved, False if rejected or timeout
        """
        timeout = timeout_sec or self.timeout_sec
        
        # Resolve API URL based on deployment environment (cold restart capable)
        api_url = self._resolve_api_url(deployment_env)
        
        print(f"\n🧑‍⚖️  WINGMAN APPROVAL: Requesting decision...")
        print(f"   Task: {task_name}")
        print(f"   Environment: {deployment_env}")
        print(f"   API: {api_url}")
        
        try:
            # Submit request
            response = requests.post(
                f"{api_url}/approvals/request",
                headers=self.headers,
                json={
                    "worker_id": worker_id,
                    "task_name": task_name,
                    "instruction": instruction,
                    "deployment_env": deployment_env,
                },
                timeout=10,
            )
            
            if response.status_code != 200:
                print(f"   ❌ Approval request failed (Status: {response.status_code})")
                return False
            
            data = response.json()
            
            # Check if auto-approved (low risk)
            if not data.get("needs_approval", False):
                risk_level = data.get("risk", {}).get("risk_level", "UNKNOWN")
                print(f"   ✅ AUTO-APPROVED (risk={risk_level})")
                return True
            
            # Get request ID for polling
            request = data.get("request", {}) or {}
            request_id = request.get("request_id", "")
            risk = data.get("risk", {}) or {}
            risk_level = risk.get("risk_level", "UNKNOWN")
            
            print(f"   🟡 PENDING (risk={risk_level}) request_id={request_id}")
            print(f"   📱 Approve in Telegram: /approve {request_id}")
            print(f"   ⏱️  Waiting for decision (timeout: {timeout}s)...")
            
            # Poll for decision
            deadline = time.time() + timeout
            attempt = 0
            
            while time.time() < deadline:
                attempt += 1
                time.sleep(self.poll_interval)
                
                # Check status (use same API URL as request)
                status_resp = requests.get(
                    f"{api_url}/approvals/{request_id}",
                    headers=self.headers,
                    timeout=10,
                )
                
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    request_status = status_data.get("status", "")
                    
                    if request_status == "APPROVED":
                        decided_by = status_data.get("decided_by", "unknown")
                        print(f"   ✅ APPROVED by {decided_by}")
                        return True
                    elif request_status == "REJECTED":
                        decided_by = status_data.get("decided_by", "unknown")
                        note = status_data.get("decision_note", "")
                        print(f"   ❌ REJECTED by {decided_by}")
                        if note:
                            print(f"   Note: {note}")
                        return False
                
                # Show progress every 30 seconds
                elapsed = int(time.time() - (deadline - timeout))
                if attempt % 15 == 0:  # Every 30 seconds
                    print(f"   ⏳ Still waiting... ({elapsed}s elapsed)")
            
            # Timeout
            print(f"   ⏱️  TIMEOUT after {timeout}s")
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Approval flow failed: {e}")
            return False
    
    def get_approval_status(self, request_id: str, deployment_env: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get status of an approval request.
        
        Args:
            request_id: Approval request ID
            deployment_env: Environment (test/prd) - required if not using explicit api_url override
            
        Returns:
            Dict with status info, or None if error
        """
        # Resolve API URL (use provided env or fallback to test)
        api_url = self._resolve_api_url(deployment_env or "test")
        
        try:
            response = requests.get(
                f"{api_url}/approvals/{request_id}",
                headers=self.headers,
                timeout=10,
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None


# Convenience function for quick usage
def request_approval(
    worker_id: str,
    task_name: str,
    instruction: str,
    deployment_env: str = "test",
    api_url: Optional[str] = None
) -> bool:
    """
    Convenience function to request approval.
    
    Automatically selects API URL based on deployment_env:
    - test -> WINGMAN_API_URL_TEST (default: http://127.0.0.1:8101)
    - prd -> WINGMAN_API_URL_PRD (default: http://127.0.0.1:5001)
    
    Usage:
        if request_approval("my-script", "Stop containers", "...", "prd"):
            # Execute operation
    """
    client = WingmanApprovalClient(api_url=api_url)
    return client.request_approval(worker_id, task_name, instruction, deployment_env)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: wingman_approval_client.py <worker_id> <task_name> <instruction> [env]")
        sys.exit(1)
    
    worker_id = sys.argv[1]
    task_name = sys.argv[2]
    instruction = sys.argv[3]
    env = sys.argv[4] if len(sys.argv) > 4 else "test"
    
    client = WingmanApprovalClient()
    approved = client.request_approval(worker_id, task_name, instruction, env)
    
    sys.exit(0 if approved else 1)
