#!/usr/bin/env python3
"""
Wingman Client Library
Copy this file into your service to integrate with Wingman.

Usage:
    from wingman_client import WingmanClient
    
    wingman = WingmanClient()
    wingman.worker_id = "my-service"
    
    wingman.log_claim("Started processing")
    verdict = wingman.verify_claim("Created file /data/output.txt")
"""

import os
import time
import requests
from typing import Dict, Optional
from urllib.parse import urlparse, urlunparse


class WingmanClient:
    """
    Reusable API client for Wingman verification and governance.
    
    Environment Variables:
        WINGMAN_URL: API base URL (default: http://127.0.0.1:5001)
        WORKER_ID: Identifier for this service (default: unknown-worker)
        DEPLOYMENT_ENV: Environment name (dev/test/prd)
        WINGMAN_APPROVAL_READ_KEY: Key for reading approvals
        WINGMAN_APPROVAL_DECIDE_KEY: Key for approving/rejecting
        WINGMAN_APPROVAL_REQUEST_KEY: Key for requesting approvals
    """
    
    def __init__(self, api_url: str = None, worker_id: str = None):
        # Get API URL, normalizing localhost to 127.0.0.1
        raw_url = api_url or os.getenv("WINGMAN_URL", "http://127.0.0.1:5001")
        parsed = urlparse(raw_url.rstrip('/'))
        if parsed.hostname == "localhost":
            parsed = parsed._replace(netloc=parsed.netloc.replace("localhost", "127.0.0.1"))
        self.api_url = urlunparse(parsed).rstrip('/')
        
        self.worker_id = worker_id or os.getenv("WORKER_ID", "unknown-worker")
        self.deployment_env = os.getenv("DEPLOYMENT_ENV", "dev")
        self.timeout = 10
        
        # Set up session with auth headers
        self.session = requests.Session()
        self._setup_auth_headers()
    
    def _setup_auth_headers(self):
        """Configure authentication headers from environment"""
        headers = {}
        
        # Role-separated keys (preferred)
        if os.getenv("WINGMAN_APPROVAL_READ_KEY"):
            headers["X-Wingman-Approval-Read-Key"] = os.getenv("WINGMAN_APPROVAL_READ_KEY")
        if os.getenv("WINGMAN_APPROVAL_DECIDE_KEY"):
            headers["X-Wingman-Approval-Decide-Key"] = os.getenv("WINGMAN_APPROVAL_DECIDE_KEY")
        if os.getenv("WINGMAN_APPROVAL_REQUEST_KEY"):
            headers["X-Wingman-Approval-Request-Key"] = os.getenv("WINGMAN_APPROVAL_REQUEST_KEY")
        
        # Legacy single key (fallback)
        if os.getenv("WINGMAN_APPROVAL_API_KEY"):
            headers["X-Wingman-Approval-Key"] = os.getenv("WINGMAN_APPROVAL_API_KEY")
        
        self.session.headers.update(headers)
    
    # =========================================================================
    # Health & Status
    # =========================================================================
    
    def health_check(self) -> bool:
        """
        Check if Wingman API is healthy.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            r = self.session.get(f"{self.api_url}/health", timeout=5)
            return r.status_code == 200 and r.json().get("status") == "healthy"
        except Exception:
            return False
    
    def get_status(self) -> Dict:
        """
        Get detailed API status.
        
        Returns:
            Dict with status details
        """
        try:
            r = self.session.get(f"{self.api_url}/health", timeout=5)
            if r.status_code == 200:
                return {"success": True, **r.json()}
            return {"success": False, "error": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # Phase 2: Instruction Validation
    # =========================================================================
    
    def check_instruction(self, instruction: str) -> Dict:
        """
        Validate an instruction against the 10-point framework.
        
        Args:
            instruction: The instruction text with required sections
            
        Returns:
            Dict with: approved (bool), score (int), missing_sections (list), policy_checks (dict)
        """
        try:
            r = self.session.post(
                f"{self.api_url}/check",
                json={"instruction": instruction},
                timeout=self.timeout
            )
            return r.json()
        except Exception as e:
            return {"approved": False, "score": 0, "error": str(e)}
    
    # =========================================================================
    # Phase 3: Claims Logging & Verification
    # =========================================================================
    
    def log_claim(self, claim: str) -> bool:
        """
        Log a claim to the audit trail.
        
        Args:
            claim: What you're claiming to have done (e.g., "Created file /data/x.txt")
            
        Returns:
            True if logged successfully
        """
        try:
            r = self.session.post(
                f"{self.api_url}/log_claim",
                json={"worker_id": self.worker_id, "claim": claim},
                timeout=self.timeout
            )
            return r.status_code == 200
        except Exception:
            return False
    
    def verify_claim(self, claim: str, use_enhanced: bool = False) -> str:
        """
        Verify a claim against reality.
        
        Args:
            claim: The claim to verify
            use_enhanced: Use enhanced (LLM) verifier (slower but smarter)
            
        Returns:
            Verdict: "TRUE", "FALSE", "UNVERIFIABLE", or "ERROR"
        """
        try:
            r = self.session.post(
                f"{self.api_url}/verify",
                json={"claim": claim, "use_enhanced": use_enhanced},
                timeout=self.timeout
            )
            return r.json().get("verdict", "ERROR")
        except Exception:
            return "ERROR"
    
    def verify_claim_full(self, claim: str, use_enhanced: bool = False) -> Dict:
        """
        Verify a claim and return full response.
        
        Returns:
            Dict with: verdict, verifier, processing_time_ms, timestamp, details
        """
        try:
            r = self.session.post(
                f"{self.api_url}/verify",
                json={"claim": claim, "use_enhanced": use_enhanced},
                timeout=self.timeout
            )
            return r.json()
        except Exception as e:
            return {"verdict": "ERROR", "error": str(e)}
    
    # =========================================================================
    # Phase 4: Human Approval
    # =========================================================================
    
    def request_approval(
        self,
        task_name: str,
        instruction: str,
        wait: bool = True,
        timeout_seconds: int = 3600,
        poll_interval: float = 2.0
    ) -> bool:
        """
        Request human approval for a high-risk operation.
        
        Args:
            task_name: Short name for the task
            instruction: Full instruction text
            wait: If True, block until approved/rejected/timeout
            timeout_seconds: Max time to wait (default 1 hour)
            poll_interval: Seconds between status checks
            
        Returns:
            True if approved, False if rejected/timeout/error
        """
        try:
            r = self.session.post(
                f"{self.api_url}/approvals/request",
                json={
                    "worker_id": self.worker_id,
                    "task_name": task_name,
                    "instruction": instruction,
                    "deployment_env": self.deployment_env
                },
                timeout=self.timeout
            )
            
            if r.status_code != 200:
                return False
            
            result = r.json()
            
            # Auto-approved (low risk)
            if not result.get("needs_approval"):
                return True
            
            if not wait:
                # Return False but caller can poll themselves
                return False
            
            # Wait for human decision
            request_id = result["request"]["request_id"]
            deadline = time.time() + timeout_seconds
            
            while time.time() < deadline:
                time.sleep(poll_interval)
                
                status_r = self.session.get(
                    f"{self.api_url}/approvals/{request_id}",
                    timeout=self.timeout
                )
                
                if status_r.status_code != 200:
                    continue
                
                status = status_r.json().get("status")
                
                if status == "APPROVED":
                    return True
                if status == "REJECTED":
                    return False
            
            # Timeout
            return False
            
        except Exception:
            return False
    
    def request_approval_async(self, task_name: str, instruction: str) -> Optional[str]:
        """
        Request approval without waiting. Returns request_id for polling.
        
        Returns:
            request_id if approval needed, None if auto-approved or error
        """
        try:
            r = self.session.post(
                f"{self.api_url}/approvals/request",
                json={
                    "worker_id": self.worker_id,
                    "task_name": task_name,
                    "instruction": instruction,
                    "deployment_env": self.deployment_env
                },
                timeout=self.timeout
            )
            
            if r.status_code != 200:
                return None
            
            result = r.json()
            
            if not result.get("needs_approval"):
                return None  # Auto-approved
            
            return result["request"]["request_id"]
            
        except Exception:
            return None
    
    def get_approval_status(self, request_id: str) -> Optional[str]:
        """
        Check status of an approval request.
        
        Returns:
            Status: "PENDING", "APPROVED", "REJECTED", or None on error
        """
        try:
            r = self.session.get(
                f"{self.api_url}/approvals/{request_id}",
                timeout=self.timeout
            )
            if r.status_code == 200:
                return r.json().get("status")
            return None
        except Exception:
            return None
    
    def list_pending_approvals(self, limit: int = 20) -> list:
        """
        List pending approval requests.
        
        Returns:
            List of pending approval requests
        """
        try:
            r = self.session.get(
                f"{self.api_url}/approvals/pending",
                params={"limit": limit},
                timeout=self.timeout
            )
            if r.status_code == 200:
                return r.json().get("pending", [])
            return []
        except Exception:
            return []
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    def get_stats(self, time_range: str = "24h") -> Dict:
        """
        Get verification statistics.
        
        Args:
            time_range: "1h", "24h", "7d", or "30d"
            
        Returns:
            Dict with statistics
        """
        try:
            r = self.session.get(
                f"{self.api_url}/stats",
                params={"range": time_range},
                timeout=self.timeout
            )
            return r.json()
        except Exception as e:
            return {"error": str(e)}


# =============================================================================
# Convenience Functions
# =============================================================================

_default_client = None

def get_client() -> WingmanClient:
    """Get the default singleton client instance."""
    global _default_client
    if _default_client is None:
        _default_client = WingmanClient()
    return _default_client


def log_claim(claim: str) -> bool:
    """Log a claim using the default client."""
    return get_client().log_claim(claim)


def verify_claim(claim: str) -> str:
    """Verify a claim using the default client."""
    return get_client().verify_claim(claim)


def check_instruction(instruction: str) -> Dict:
    """Check an instruction using the default client."""
    return get_client().check_instruction(instruction)


# =============================================================================
# CLI for Testing
# =============================================================================

if __name__ == "__main__":
    import sys
    
    client = WingmanClient()
    print(f"Wingman URL: {client.api_url}")
    print(f"Worker ID: {client.worker_id}")
    print(f"Health: {client.health_check()}")
    
    if len(sys.argv) > 1:
        claim = " ".join(sys.argv[1:])
        print(f"\nVerifying: {claim}")
        result = client.verify_claim_full(claim)
        print(f"Verdict: {result.get('verdict')}")
        print(f"Details: {result}")
