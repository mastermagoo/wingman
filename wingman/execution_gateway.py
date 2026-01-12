#!/usr/bin/env python3
"""
Execution Gateway - Single point of control for privileged operations
Flask service that validates capability tokens and executes approved commands
"""

from flask import Flask, request, jsonify
import subprocess
import os
import uuid
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Set
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from capability_token import validate_token, hash_token
except ImportError as e:
    print(f"Error importing capability_token: {e}")
    sys.exit(1)

app = Flask(__name__)

# Configuration
ALLOWED_ENVIRONMENTS = os.getenv("ALLOWED_ENVIRONMENTS", "test,prd").split(",")
AUDIT_STORAGE = os.getenv("AUDIT_STORAGE", "jsonl")  # "postgres" or "jsonl"
AUDIT_JSONL_PATH = os.path.join(os.path.dirname(__file__), "data", "execution_audit.jsonl")

# In-memory token replay prevention (production should use Redis/PostgreSQL)
# This tracks used token JTIs to prevent replay attacks
USED_TOKENS: Set[str] = set()


def ensure_audit_dir():
    """Ensure audit log directory exists"""
    os.makedirs(os.path.dirname(AUDIT_JSONL_PATH), exist_ok=True)


def log_execution_to_jsonl(audit_entry: Dict[str, Any]) -> None:
    """
    Write execution record to JSONL audit log (fallback when PostgreSQL unavailable).

    Args:
        audit_entry: Execution details to log
    """
    ensure_audit_dir()
    try:
        with open(AUDIT_JSONL_PATH, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")
    except Exception as e:
        # Log failure but don't block execution
        print(f"WARNING: Failed to write audit log: {e}", file=sys.stderr)


# --- PostgreSQL audit logging (append-only) ---------------------------------

def _pg_dsn() -> str:
    """Build Postgres DSN for the gateway audit store.

    Prefer Postgres-native env vars (POSTGRES_*) so the gateway matches the DB init credentials
    even after volume resets. Fall back to TIMESCALE_*/DB_* for legacy compatibility.
    No secrets are printed.
    """
    host = (os.getenv("DB_HOST") or os.getenv("TIMESCALE_HOST") or os.getenv("POSTGRES_HOST") or "postgres").strip()
    port = int((os.getenv("DB_PORT") or os.getenv("TIMESCALE_PORT") or os.getenv("POSTGRES_PORT") or "5432").strip())
    db = (os.getenv("POSTGRES_DB") or os.getenv("DB_NAME") or os.getenv("TIMESCALE_DB") or "wingman").strip()
    user = (os.getenv("POSTGRES_USER") or os.getenv("DB_USER") or os.getenv("TIMESCALE_USER") or "wingman").strip()
    pw = (os.getenv("POSTGRES_PASSWORD") or os.getenv("TIMESCALE_PASS") or os.getenv("DB_PASSWORD") or "").strip()
    if not pw:
        raise RuntimeError("Database password env var missing (POSTGRES_PASSWORD/TIMESCALE_PASS/DB_PASSWORD)")
    return f"host={host} port={port} dbname={db} user={user} password={pw} sslmode=disable"


def _ensure_audit_schema(conn) -> None:
    """Create append-only audit table + anti-tamper triggers if missing."""
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS execution_audit (
            execution_id TEXT PRIMARY KEY,
            approval_id TEXT NOT NULL,
            worker_id TEXT NOT NULL,
            command TEXT NOT NULL,
            environment TEXT NOT NULL,
            output TEXT,
            exit_code INTEGER NOT NULL,
            duration_ms INTEGER NOT NULL,
            token_hash TEXT NOT NULL,
            artifacts JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

    # Prevent UPDATE/DELETE (append-only). Superusers can still override; this is defense-in-depth.
    cur.execute(
        """
        CREATE OR REPLACE FUNCTION deny_update_delete_execution_audit() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'execution_audit is append-only';
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    cur.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'trg_no_update_execution_audit'
            ) THEN
                CREATE TRIGGER trg_no_update_execution_audit
                BEFORE UPDATE ON execution_audit
                FOR EACH ROW EXECUTE FUNCTION deny_update_delete_execution_audit();
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger WHERE tgname = 'trg_no_delete_execution_audit'
            ) THEN
                CREATE TRIGGER trg_no_delete_execution_audit
                BEFORE DELETE ON execution_audit
                FOR EACH ROW EXECUTE FUNCTION deny_update_delete_execution_audit();
            END IF;
        END $$;
        """
    )

    cur.close()


def log_execution_to_postgres(audit_entry: Dict[str, Any]) -> None:
    """Write execution record to PostgreSQL audit table (append-only)."""
    try:
        import psycopg2

        dsn = _pg_dsn()
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        _ensure_audit_schema(conn)

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO execution_audit (
                    execution_id, approval_id, worker_id, command, environment,
                    output, exit_code, duration_ms, token_hash, artifacts, created_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    audit_entry.get("execution_id"),
                    audit_entry.get("approval_id"),
                    audit_entry.get("worker_id"),
                    audit_entry.get("command"),
                    audit_entry.get("environment"),
                    audit_entry.get("output"),
                    int(audit_entry.get("exit_code", -1)),
                    int(audit_entry.get("duration_ms", 0)),
                    audit_entry.get("token_hash"),
                    json.dumps(audit_entry.get("artifacts") or []),
                    audit_entry.get("created_at"),
                ),
            )

        conn.close()

    except Exception as e:
        # Fail closed on DB logging? Business case wants enforcement, not logging fragility.
        # For TEST, fall back to JSONL but also emit a warning.
        print(f"WARNING: Postgres audit logging failed; falling back to JSONL ({type(e).__name__})", file=sys.stderr)
        log_execution_to_jsonl(audit_entry)

# ---------------------------------------------------------------------------




def log_execution(
    approval_id: str,
    worker_id: str,
    command: str,
    environment: str,
    output: str,
    exit_code: int,
    duration_ms: int,
    token_hash: str,
    artifacts: Optional[List[str]] = None
) -> str:
    """
    Log execution to audit trail.

    Args:
        approval_id: Approval request ID
        worker_id: Worker identifier
        command: Command that was executed
        environment: Deployment environment
        output: Command output (stdout + stderr)
        exit_code: Command exit code
        duration_ms: Execution duration in milliseconds
        token_hash: SHA256 hash of the capability token
        artifacts: Optional list of files created/modified

    Returns:
        Execution ID
    """
    execution_id = str(uuid.uuid4())

    audit_entry = {
        "execution_id": execution_id,
        "approval_id": approval_id,
        "worker_id": worker_id,
        "command": command,
        "environment": environment,
        "output": output[:10000],  # Truncate very large output
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "token_hash": token_hash,
        "artifacts": artifacts or [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # Log to configured storage
    if AUDIT_STORAGE == "postgres":
        log_execution_to_postgres(audit_entry)
    else:
        log_execution_to_jsonl(audit_entry)

    return execution_id


def execute_command(command: str, timeout: int = 300) -> Dict[str, Any]:
    """
    Execute a command safely using subprocess.

    Args:
        command: Command to execute (as string)
        timeout: Timeout in seconds (default 300)

    Returns:
        Dict with:
        - success: bool
        - output: str (stdout + stderr)
        - exit_code: int
        - error: str (if failed)
    """
    import time
    start_time = time.time()

    try:
        # Execute command in shell (with timeout)
        # Security note: Command validation happens BEFORE this point
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.dirname(os.path.abspath(__file__))  # Run from wingman/ directory
        )

        duration_ms = int((time.time() - start_time) * 1000)

        return {
            "success": result.returncode == 0,
            "output": result.stdout + result.stderr,
            "exit_code": result.returncode,
            "duration_ms": duration_ms
        }

    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "success": False,
            "output": "",
            "exit_code": -1,
            "error": f"Command timeout after {timeout}s",
            "duration_ms": duration_ms
        }
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "success": False,
            "output": "",
            "exit_code": -1,
            "error": f"Execution failed: {str(e)}",
            "duration_ms": duration_ms
        }


def validate_command_scope(command: str, allowed_commands: List[str]) -> Dict[str, Any]:
    """
    Validate that command is within approved scope.

    Args:
        command: Command to validate
        allowed_commands: List of allowed command patterns

    Returns:
        Dict with:
        - valid: bool
        - error: str (if invalid)

    Note: Simple pattern matching for now. Could be enhanced with:
    - Regex pattern matching
    - Command parsing and allowlist validation
    - Dangerous flag detection
    """
    # Harden against obvious shell injection / redirection.
    # This is intentionally conservative: privileged execution should use explicit, reviewable commands.
    FORBIDDEN_SHELL_CHARS = [';', '&&', '||', '|', '`', '$(', ')', '>', '<', '\n', '\r']
    cmd = command.strip()
    for bad in FORBIDDEN_SHELL_CHARS:
        if bad in cmd:
            return {"valid": False, "error": f"Command contains forbidden shell operator: {bad!r}"}

    # If no restrictions, allow all commands
    if not allowed_commands or len(allowed_commands) == 0:
        return {"valid": True}

    # Check if command matches any allowed pattern
    command_normalized = command.strip()
    for allowed in allowed_commands:
        # Simple exact match for now (can be enhanced with regex)
        if command_normalized == allowed.strip():
            return {"valid": True}

        # Prefix match for commands with arguments
        if command_normalized.startswith(allowed.strip()):
            return {"valid": True}

    return {
        "valid": False,
        "error": f"Command not in approved scope. Allowed: {allowed_commands}"
    }


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "execution-gateway",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.route('/gateway/execute', methods=['POST'])
def gateway_execute():
    """
    Execute a command with capability token validation.

    Request:
        Headers:
            X-Capability-Token: JWT token

        Body:
            {
                "command": "docker compose ps",
                "approval_id": "uuid",
                "environment": "test"  # optional, will validate against token
            }

    Response (success):
        {
            "success": true,
            "output": "...",
            "exit_code": 0,
            "execution_id": "uuid",
            "duration_ms": 1234
        }

    Response (failure):
        {
            "success": false,
            "error": "error message"
        }
    """
    # Extract token from header
    token = request.headers.get("X-Capability-Token", "").strip()
    if not token:
        return jsonify({
            "success": False,
            "error": "Missing X-Capability-Token header"
        }), 401

    # Validate token
    validation_result = validate_token(token, USED_TOKENS)
    if not validation_result["valid"]:
        return jsonify({
            "success": False,
            "error": validation_result["error"]
        }), 401

    payload = validation_result["payload"]
    jti = validation_result["jti"]

    # Mark token as used (prevent replay)
    USED_TOKENS.add(jti)

    # Extract request body
    try:
        body = request.get_json()
        if not body:
            return jsonify({
                "success": False,
                "error": "Missing request body"
            }), 400

        command = body.get("command", "").strip()
        approval_id = body.get("approval_id", "").strip()
        requested_env = body.get("environment", "").strip()

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Invalid request body: {str(e)}"
        }), 400

    # Validate required fields
    if not command:
        return jsonify({
            "success": False,
            "error": "Missing 'command' field"
        }), 400

    if not approval_id:
        return jsonify({
            "success": False,
            "error": "Missing 'approval_id' field"
        }), 400

    # Validate approval_id matches token
    if approval_id != payload.get("approval_id"):
        return jsonify({
            "success": False,
            "error": "approval_id does not match token"
        }), 403

    # Validate environment (if specified)
    token_env = payload.get("environment", "")
    if requested_env and requested_env != token_env:
        return jsonify({
            "success": False,
            "error": f"Environment mismatch: requested '{requested_env}', token allows '{token_env}'"
        }), 403

    # Validate environment is allowed by gateway
    if token_env not in ALLOWED_ENVIRONMENTS:
        return jsonify({
            "success": False,
            "error": f"Environment '{token_env}' not allowed by gateway. Allowed: {ALLOWED_ENVIRONMENTS}"
        }), 403

    # Validate command is in approved scope
    allowed_commands = payload.get("allowed_commands", [])
    scope_validation = validate_command_scope(command, allowed_commands)
    if not scope_validation["valid"]:
        return jsonify({
            "success": False,
            "error": scope_validation["error"]
        }), 403

    # Execute command
    execution_result = execute_command(command)

    # Log to audit trail
    token_hashed = hash_token(token)
    worker_id = payload.get("worker_id", "unknown")
    duration_ms = execution_result.get("duration_ms", 0)

    execution_id = log_execution(
        approval_id=approval_id,
        worker_id=worker_id,
        command=command,
        environment=token_env,
        output=execution_result.get("output", ""),
        exit_code=execution_result.get("exit_code", -1),
        duration_ms=duration_ms,
        token_hash=token_hashed,
        artifacts=[]
    )

    # Return result
    if execution_result["success"]:
        return jsonify({
            "success": True,
            "output": execution_result["output"],
            "exit_code": execution_result["exit_code"],
            "execution_id": execution_id,
            "duration_ms": duration_ms
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": execution_result.get("error", "Command execution failed"),
            "output": execution_result.get("output", ""),
            "exit_code": execution_result["exit_code"],
            "execution_id": execution_id
        }), 200  # Still 200 because execution happened, just failed


if __name__ == '__main__':
    print("Starting Execution Gateway...")
    print(f"Allowed environments: {ALLOWED_ENVIRONMENTS}")
    print(f"Audit storage: {AUDIT_STORAGE}")

    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('GATEWAY_PORT', '5001')),
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )
