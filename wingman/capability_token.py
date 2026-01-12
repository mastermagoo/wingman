#!/usr/bin/env python3
"""
Capability Token Management
JWT-based token generation and validation for Execution Gateway
"""

import os
import hashlib
import jwt
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List, Any
from dataclasses import dataclass


@dataclass
class TokenPayload:
    """Structured token claims"""
    approval_id: str
    worker_id: str
    environment: str
    allowed_commands: List[str]
    exp: int
    iat: int
    jti: str


# JWT secret key from environment (must be shared between API and Gateway)
def _jwt_secret() -> str:
    """Fetch the gateway JWT secret from env; required for all environments.

    NOTE: Do NOT provide insecure defaults. If this is missing, the gateway/auth must fail closed.
    """
    key = (os.getenv("GATEWAY_JWT_SECRET") or "").strip()
    if not key:
        raise RuntimeError("GATEWAY_JWT_SECRET is not set (required)")
    return key



def generate_token(
    approval_id: str,
    worker_id: str = "worker-001",
    environment: str = "test",
    allowed_commands: Optional[List[str]] = None,
    ttl_minutes: int = 60
) -> str:
    """
    Generate a JWT capability token.

    Args:
        approval_id: Unique approval request ID
        worker_id: Worker identifier
        environment: Deployment environment (test/prd)
        allowed_commands: List of allowed command patterns (None = allow all)
        ttl_minutes: Token lifetime in minutes (default 60)

    Returns:
        JWT token string

    Example:
        >>> token = generate_token("approval-123", "worker-001", "test")
        >>> # token is a signed JWT with 1 hour TTL
    """
    now = datetime.now(timezone.utc)
    iat = int(now.timestamp())
    exp = int((now + timedelta(minutes=ttl_minutes)).timestamp())

    # Unique token ID (for replay prevention)
    jti = hashlib.sha256(f"{approval_id}:{iat}:{os.urandom(16).hex()}".encode()).hexdigest()

    payload = {
        "iss": "wingman-api",
        "sub": worker_id,
        "exp": exp,
        "iat": iat,
        "jti": jti,
        "approval_id": approval_id,
        "worker_id": worker_id,
        "environment": environment,
        "allowed_commands": allowed_commands or [],
    }

    token = jwt.encode(payload, _jwt_secret(), algorithm="HS256")
    return token


def validate_token(token: str, used_tokens: Optional[set] = None) -> Dict[str, Any]:
    """
    Validate a JWT capability token.

    Args:
        token: JWT token string
        used_tokens: Set of previously used token JTIs (for replay prevention)

    Returns:
        Dict with validation result:
        {
            "valid": bool,
            "payload": dict (if valid),
            "error": str (if invalid)
        }

    Validation checks:
        1. Signature valid (HMAC-SHA256)
        2. Not expired
        3. Not replayed (jti not in used_tokens)

    Example:
        >>> result = validate_token(token, used_tokens=set())
        >>> if result["valid"]:
        ...     print(f"Approved for: {result['payload']['approval_id']}")
        ... else:
        ...     print(f"Invalid: {result['error']}")
    """
    if used_tokens is None:
        used_tokens = set()

    try:
        # Decode and verify signature + expiration
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
            }
        )

        # Check for replay (single-use token)
        jti = payload.get("jti")
        if not jti:
            return {
                "valid": False,
                "error": "Token missing jti (unique ID)"
            }

        if jti in used_tokens:
            return {
                "valid": False,
                "error": "Token has already been used (replay detected)"
            }

        # All checks passed
        return {
            "valid": True,
            "payload": payload,
            "jti": jti
        }

    except jwt.ExpiredSignatureError:
        return {
            "valid": False,
            "error": "Token expired"
        }
    except jwt.InvalidSignatureError:
        return {
            "valid": False,
            "error": "Invalid token signature (forged)"
        }
    except jwt.DecodeError:
        return {
            "valid": False,
            "error": "Malformed token"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Token validation failed: {str(e)}"
        }


def hash_token(token: str) -> str:
    """
    Hash a token for audit logging (prevent token leakage in logs).

    Args:
        token: JWT token string

    Returns:
        SHA256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()
