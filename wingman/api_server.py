#!/usr/bin/env python3
"""
Wingman Web API Server
Exposes verification endpoints for the Wingman system
Phases 1, 2, and 3 Integrated
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import sys
import os
import traceback
import time
from typing import Dict, Any, Optional

# Add current directory AND parent directory to path to support both layouts:
# - repo_root/wingman/api_server.py with sibling modules in repo_root/wingman/
# - repo_root/wingman/api_server.py with some legacy modules in repo_root/
_this_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_this_dir)
sys.path.insert(0, _this_dir)
sys.path.insert(0, _parent_dir)

try:
    from simple_verifier import verify_claim as simple_verify_claim
    from enhanced_verifier import EnhancedVerifier
    from intel_integration import IntelDatabase
    from instruction_validator import InstructionValidator
    from approval_store import default_store as approval_default_store
    from consensus_verifier import assess_risk_consensus
    from capability_token import generate_token
    from validation_store import store_validation_result
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

try:
    from validation.composite_validator import CompositeValidator
    composite_validator = CompositeValidator()
except ImportError:
    composite_validator = None

app = Flask(__name__)
CORS(app)  # Allow all origins for now

# Initialize verifiers and validators
enhanced_verifier = EnhancedVerifier()
instruction_validator = InstructionValidator()
# Path to audit log - using relative path from app root
AUDIT_LOG = os.path.join(os.path.dirname(__file__), "data", "claims_audit.jsonl")
approval_store = approval_default_store()

# ---------------------------------------------------------------------------
# Phase 4 (HITL) approval endpoint protection
#
# Goal: minimize exposure and allow key separation:
# - READ access (queue visibility, polling) can be restricted via READ keys
# - DECIDE access (approve/reject) can be restricted via DECIDE keys
# - REQUEST access (creating approvals) can be optionally restricted via REQUEST keys
#
# Backwards compatibility:
# - If WINGMAN_APPROVAL_API_KEY is set and no READ/DECIDE/REQUEST keys are configured,
#   require header X-Wingman-Approval-Key for protected endpoints.
# ---------------------------------------------------------------------------

LEGACY_APPROVAL_KEY = (os.getenv("WINGMAN_APPROVAL_API_KEY") or "").strip()


def _parse_keys(env_name: str) -> set[str]:
    raw = (os.getenv(env_name) or "").strip()
    if not raw:
        return set()
    return {p.strip() for p in raw.split(",") if p.strip()}


# Preferred (role-separated) keys (comma-separated lists allowed)
APPROVAL_READ_KEYS = _parse_keys("WINGMAN_APPROVAL_READ_KEYS") | _parse_keys("WINGMAN_APPROVAL_READ_KEY")
APPROVAL_DECIDE_KEYS = _parse_keys("WINGMAN_APPROVAL_DECIDE_KEYS") | _parse_keys("WINGMAN_APPROVAL_DECIDE_KEY")
APPROVAL_REQUEST_KEYS = _parse_keys("WINGMAN_APPROVAL_REQUEST_KEYS") | _parse_keys("WINGMAN_APPROVAL_REQUEST_KEY")


def _require_key(*, header: str, allowed: set[str]) -> Optional[tuple]:
    """
    If 'allowed' is non-empty, require the request to provide a matching key in the given header.
    """
    if not allowed:
        return None
    provided = (request.headers.get(header) or "").strip()
    if not provided or provided not in allowed:
        return jsonify({"error": "Unauthorized"}), 401
    return None


def _require_approval_read() -> Optional[tuple]:
    # If role-separated keys exist, enforce them.
    if APPROVAL_READ_KEYS:
        return _require_key(header="X-Wingman-Approval-Read-Key", allowed=APPROVAL_READ_KEYS)
    # Otherwise fall back to legacy key if set.
    if LEGACY_APPROVAL_KEY:
        return _require_key(header="X-Wingman-Approval-Key", allowed={LEGACY_APPROVAL_KEY})
    return None


def _require_approval_decide() -> Optional[tuple]:
    if APPROVAL_DECIDE_KEYS:
        return _require_key(header="X-Wingman-Approval-Decide-Key", allowed=APPROVAL_DECIDE_KEYS)
    if LEGACY_APPROVAL_KEY:
        return _require_key(header="X-Wingman-Approval-Key", allowed={LEGACY_APPROVAL_KEY})
    return None


def _require_approval_request() -> Optional[tuple]:
    # Request endpoint remains open unless explicitly configured.
    if APPROVAL_REQUEST_KEYS:
        return _require_key(header="X-Wingman-Approval-Request-Key", allowed=APPROVAL_REQUEST_KEYS)
    return None


def assess_risk(instruction_text: str, task_name: str = "", deployment_env: str = "") -> Dict[str, str]:
    """
    Heuristic risk scorer. Conservative by design:
    - PRD always requires approval unless explicitly disabled via WINGMAN_REQUIRE_APPROVAL=0
    - Mentions of PROD/production, destructive ops, secrets, forced operations => HIGH
    """
    require = os.getenv("WINGMAN_REQUIRE_APPROVAL", "").strip()
    if require == "0":
        return {"risk_level": "LOW", "risk_reason": "Approval disabled via WINGMAN_REQUIRE_APPROVAL=0"}

    txt = f"{task_name}\n{instruction_text}\n{deployment_env}".lower()
    env = (deployment_env or os.getenv("DEPLOYMENT_ENV", "")).lower()

    if env == "prd":
        return {"risk_level": "HIGH", "risk_reason": "Deployment environment is PRD"}

    high_terms = [
        "prod",
        "production",
        "drop ",
        "truncate ",
        "delete ",
        "rm -",
        "wipe",
        "format ",
        "rotate key",
        "secret",
        "token",
        "password",
        "client secret",
        "--force",
        "--delete",
    ]
    if any(t in txt for t in high_terms):
        return {"risk_level": "HIGH", "risk_reason": "High-risk keywords detected"}

    medium_terms = [
        "migration",
        "deploy",
        "release",
        "schema",
        "postgres",
        "redis",
        "firewall",
        "permissions",
        "iam",
        "sudo",
    ]
    if any(t in txt for t in medium_terms):
        return {"risk_level": "MEDIUM", "risk_reason": "Medium-risk keywords detected"}

    return {"risk_level": "LOW", "risk_reason": "No high-risk indicators detected"}

# Initialize database connection
try:
    db = IntelDatabase()
    db_available = True
except Exception as e:
    print(f"Warning: Database connection failed: {e}")
    print("Falling back to in-memory storage")
    db = None
    db_available = False

# In-memory fallback for stats
stats_fallback = {
    "total_verifications": 0,
    "verdicts": {
        "TRUE": 0,
        "FALSE": 0,
        "UNVERIFIABLE": 0
    }
}


@app.route('/verify', methods=['POST'])
def verify():
    """
    Phase 1/3: Verify a claim using simple or enhanced verifier
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "No JSON body provided",
                "timestamp": datetime.now().isoformat()
            }), 400

        claim = data.get('claim')
        use_enhanced = data.get('use_enhanced', False)

        if not claim:
            return jsonify({
                "error": "Missing 'claim' field",
                "timestamp": datetime.now().isoformat()
            }), 400

        # Track processing time
        start_time = time.time()

        # Choose verifier and run verification
        if use_enhanced:
            verdict = enhanced_verifier.verify_claim(claim)
            result = {
                'verdict': verdict,
                'details': f"Enhanced verification completed with verdict: {verdict}",
                'verifier': 'enhanced'
            }
        else:
            verdict = simple_verify_claim(claim)
            result = {
                'verdict': verdict,
                'details': f"Simple verification completed with verdict: {verdict}",
                'verifier': 'simple'
            }

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Log to database if available
        if db and db_available:
            try:
                db.log_verification(
                    claim=claim,
                    verdict=verdict,
                    verifier_type='enhanced' if use_enhanced else 'simple',
                    processing_time_ms=processing_time_ms,
                    source='api'
                )
            except Exception as e:
                print(f"Failed to log to database: {e}")
                stats_fallback["total_verifications"] += 1
                if verdict in stats_fallback["verdicts"]:
                    stats_fallback["verdicts"][verdict] += 1
        else:
            stats_fallback["total_verifications"] += 1
            if verdict in stats_fallback["verdicts"]:
                stats_fallback["verdicts"][verdict] += 1

        return jsonify({
            "verdict": verdict,
            "details": result.get('details', 'No details available'),
            "timestamp": datetime.now().isoformat(),
            "verifier": "enhanced" if use_enhanced else "simple",
            "processing_time_ms": processing_time_ms
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/check', methods=['POST'])
def check():
    """
    Phase 2: Validate instruction against 10-point framework.
    When validation package is available, also runs CompositeValidator (code, content, dependency, semantic).
    """
    try:
        data = request.get_json()
        if not data or 'instruction' not in data:
            return jsonify({
                "error": "Missing 'instruction' field",
                "approved": False,
                "score": 0
            }), 400

        instruction = data['instruction']
        task_name = data.get('task_name', '')
        result = instruction_validator.validate(instruction)

        if composite_validator is not None:
            composite_result = composite_validator.validate(instruction, task_name=task_name)
            result["composite_score"] = composite_result["overall_score"]
            result["composite_recommendation"] = composite_result["recommendation"]
            result["composite_risk_level"] = composite_result["risk_level"]
            result["composite_reasoning"] = composite_result["reasoning"]
            result["validator_scores"] = composite_result["validator_scores"]
            result["validation_profile"] = composite_result.get("profile")

        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "error": str(e),
            "approved": False,
            "score": 0
        }), 500


@app.route('/log_claim', methods=['POST'])
def log_claim():
    """
    Phase 3: Record a claim for future verification
    """
    try:
        data = request.get_json()
        if not data or 'claim' not in data:
            return jsonify({"error": "Missing 'claim' field"}), 400

        claim_entry = {
            "timestamp": datetime.now().isoformat(),
            "worker_id": data.get("worker_id", "unknown"),
            "claim": data.get("claim"),
            "status": "PENDING_VERIFICATION"
        }
        
        # Log to local file (Audit Trail)
        with open(AUDIT_LOG, "a") as f:
            f.write(json.dumps(claim_entry) + "\n")
            
        print(f"📝 Claim Logged: {data.get('claim')[:50]}...")
        return jsonify({"status": "logged", "entry": claim_entry}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def is_quarantined(worker_id: str) -> dict:
    """
    Check if worker is quarantined (Phase 4 Watcher Enhancement).

    Returns:
        {"quarantined": False} if not quarantined
        {"quarantined": True, "reason": "...", "quarantined_at": "..."} if quarantined
    """
    try:
        import redis
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=0,
            decode_responses=True
        )

        if r.sismember("quarantined_workers", worker_id):
            metadata = r.hgetall(f"quarantine:{worker_id}")
            return {
                "quarantined": True,
                "reason": metadata.get("reason", "Unknown"),
                "quarantined_at": metadata.get("quarantined_at", "Unknown"),
                "environment": metadata.get("environment", "Unknown")
            }
        return {"quarantined": False}
    except Exception as e:
        print(f"⚠️ Quarantine check failed: {e}")
        # Fail open (allow request) to avoid breaking service
        return {"quarantined": False}


@app.route("/approvals/request", methods=["POST"])
def approvals_request():
    """
    Phase 4 (Enhanced): Request human approval before proceeding with high-risk work.

    Enhanced with quarantine check (Phase 4 Watcher).

    Body:
      {
        "worker_id": "123",
        "task_name": "Deploy schema changes",
        "instruction": "....",
        "deployment_env": "dev|test|prd" (optional)
      }
    """
    try:
        auth = _require_approval_request()
        if auth is not None:
            return auth

        data = request.get_json() or {}
        instruction = (data.get("instruction") or "").strip()
        worker_id = str(data.get("worker_id", "unknown"))
        task_name = (data.get("task_name") or "").strip()
        deployment_env = (data.get("deployment_env") or os.getenv("DEPLOYMENT_ENV", "")).strip()

        # Phase 4 Enhancement: Check quarantine FIRST
        quarantine_status = is_quarantined(worker_id)
        if quarantine_status["quarantined"]:
            return jsonify({
                "needs_approval": False,
                "status": "AUTO_REJECTED",
                "rejection_reason": "WORKER_QUARANTINED",
                "reason": f"Worker quarantined: {quarantine_status['reason']}",
                "quarantined_at": quarantine_status["quarantined_at"],
                "environment": quarantine_status.get("environment", "Unknown"),
                "message": "Contact Mark to release this worker via /release_worker command or POST /watcher/release/{worker_id}"
            }), 403

        if not instruction:
            return jsonify({"error": "Missing 'instruction' field"}), 400

        # Feature flag: Check if validation is enabled
        validation_enabled = (os.getenv("VALIDATION_ENABLED") or "1").strip() == "1"
        validation_rollout_pct = int(os.getenv("VALIDATION_ROLLOUT_PERCENT") or "100")

        # Generate request fingerprint for rollout decision
        import hashlib
        rollout_hash = int(hashlib.sha256(f"{worker_id}{instruction}".encode()).hexdigest(), 16) % 100
        use_validation = validation_enabled and (rollout_hash < validation_rollout_pct)

        # Run composite validation if enabled and validator available
        validation_result = None
        if use_validation and composite_validator is not None:
            try:
                validation_result = composite_validator.validate(instruction, task_name=task_name)
            except Exception as e:
                print(f"Warning: Validation failed: {e}")
                validation_result = None

        # Auto-reject if validation recommends it (secrets, dangerous patterns, low quality)
        if validation_result and validation_result.get("recommendation") == "REJECT":
            req = approval_store.create_request(
                worker_id=worker_id,
                task_name=task_name,
                instruction=instruction,
                risk_level="CRITICAL",
                risk_reason=validation_result.get("reasoning", "Validation rejected"),
                status="AUTO_REJECTED",
            )
            # Store validation result
            if validation_result:
                store_validation_result(req.request_id, validation_result)

            return jsonify({
                "needs_approval": False,
                "status": "AUTO_REJECTED",
                "rejection_reason": "VALIDATION_FAILED",
                "request": req.to_dict(),
                "validation": {
                    "overall_score": validation_result.get("overall_score"),
                    "recommendation": validation_result.get("recommendation"),
                    "risk_level": validation_result.get("risk_level"),
                    "reasoning": validation_result.get("reasoning"),
                    "validator_scores": validation_result.get("validator_scores", {}),
                    "profile": validation_result.get("profile"),
                    "active_validators": validation_result.get("active_validators")
                }
            }), 422

        # Run heuristic risk assessment
        use_consensus = (os.getenv("WINGMAN_CONSENSUS_ENABLED") or "").strip() == "1"
        if use_consensus:
            risk = assess_risk_consensus(instruction, task_name=task_name, deployment_env=deployment_env)
        else:
            risk = assess_risk(instruction, task_name=task_name, deployment_env=deployment_env)
        risk_level = risk["risk_level"]
        risk_reason = risk["risk_reason"]

        # Auto-approve if: LOW risk AND (no validation OR validation score >= 90)
        auto_approve = False
        if risk_level == "LOW":
            if validation_result:
                # Require high validation score for auto-approve
                if (validation_result.get("overall_score", 0) >= 90 and
                    validation_result.get("recommendation") == "APPROVE"):
                    auto_approve = True
            else:
                # No validation available, use heuristic only
                auto_approve = True

        if auto_approve:
            req = approval_store.create_request(
                worker_id=worker_id,
                task_name=task_name,
                instruction=instruction,
                risk_level=risk_level,
                risk_reason=risk_reason,
                status="AUTO_APPROVED",
            )
            # Store validation result
            if validation_result:
                store_validation_result(req.request_id, validation_result)

            response_data = {
                "needs_approval": False,
                "status": "AUTO_APPROVED",
                "request": req.to_dict(),
                "risk": risk,
            }
            # Include validation details if available
            if validation_result:
                response_data["validation"] = {
                    "overall_score": validation_result.get("overall_score"),
                    "recommendation": validation_result.get("recommendation"),
                    "risk_level": validation_result.get("risk_level"),
                    "reasoning": validation_result.get("reasoning"),
                    "validator_scores": validation_result.get("validator_scores", {}),
                    "profile": validation_result.get("profile"),
                    "active_validators": validation_result.get("active_validators")
                }
            return jsonify(response_data), 200

        # De-dup: reuse an existing pending request for the same (worker/task/instruction/risk)
        try:
            fp = approval_store.compute_fingerprint(
                worker_id=worker_id,
                task_name=task_name,
                instruction=instruction,
                risk_level=risk_level,
            )
            existing = approval_store.find_pending_by_fingerprint(fp)
            if existing:
                return jsonify(
                    {
                        "needs_approval": True,
                        "status": "PENDING",
                        "request": existing.to_dict(),
                        "risk": risk,
                        "deduped": True,
                    }
                ), 200
        except Exception:
            pass

        req = approval_store.create_request(
            worker_id=worker_id,
            task_name=task_name,
            instruction=instruction,
            risk_level=risk_level,
            risk_reason=risk_reason,
            status="PENDING",
        )
        # Store validation result
        if validation_result:
            store_validation_result(req.request_id, validation_result)

        response_data = {
            "needs_approval": True,
            "status": "PENDING",
            "request": req.to_dict(),
            "risk": risk,
        }
        # Include validation details if available
        if validation_result:
            response_data["validation"] = {
                "overall_score": validation_result.get("overall_score"),
                "recommendation": validation_result.get("recommendation"),
                "risk_level": validation_result.get("risk_level"),
                "reasoning": validation_result.get("reasoning"),
                "validator_scores": validation_result.get("validator_scores", {}),
                "profile": validation_result.get("profile"),
                "active_validators": validation_result.get("active_validators")
            }
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/approvals/pending", methods=["GET"])
def approvals_pending():
    auth = _require_approval_read()
    if auth is not None:
        return auth
    try:
        limit = int(request.args.get("limit", "20"))
        pending = approval_store.list_pending(limit=limit)
        return jsonify({"pending": [p.to_dict() for p in pending], "count": len(pending)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/approvals/<request_id>", methods=["GET"])
def approvals_get(request_id: str):
    auth = _require_approval_read()
    if auth is not None:
        return auth
    try:
        req = approval_store.get(request_id)
        if not req:
            return jsonify({"error": "Not found"}), 404
        return jsonify(req.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/approvals/<request_id>/approve", methods=["POST"])
def approvals_approve(request_id: str):
    auth = _require_approval_decide()
    if auth is not None:
        return auth
    try:
        data = request.get_json() or {}
        decided_by = (data.get("decided_by") or "").strip() or None
        note = (data.get("note") or "").strip() or None
        req = approval_store.decide(request_id, decision="APPROVED", decided_by=decided_by, decision_note=note)
        if not req:
            return jsonify({"error": "Not found"}), 404
        return jsonify(req.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/approvals/<request_id>/reject", methods=["POST"])
def approvals_reject(request_id: str):
    auth = _require_approval_decide()
    if auth is not None:
        return auth
    try:
        data = request.get_json() or {}
        decided_by = (data.get("decided_by") or "").strip() or None
        note = (data.get("note") or "").strip() or None
        req = approval_store.decide(request_id, decision="REJECTED", decided_by=decided_by, decision_note=note)
        if not req:
            return jsonify({"error": "Not found"}), 404
        return jsonify(req.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/gateway/token", methods=["POST"]) 
def gateway_token():
    """Mint a one-time capability token for the Execution Gateway.

    Security properties:
    - Requires DECIDE key (same authority that can approve/reject)
    - Requires approval_id to be APPROVED or AUTO_APPROVED
    - Requires the exact command string to be present in the approved instruction text
      (prevents minting tokens for commands Mark did not see/approve)

    Body:
      {
        "approval_id": "uuid",
        "command": "docker compose ps",
        "environment": "test"  # optional; defaults to DEPLOYMENT_ENV
      }
    """
    auth = _require_approval_decide()
    if auth is not None:
        return auth

    data = request.get_json() or {}
    approval_id = (data.get("approval_id") or "").strip()
    command = (data.get("command") or "").strip()
    env = (data.get("environment") or os.getenv("DEPLOYMENT_ENV", "test")).strip()

    if not approval_id:
        return jsonify({"error": "Missing approval_id"}), 400
    if not command:
        return jsonify({"error": "Missing command"}), 400

    req = approval_store.get(approval_id)
    if not req:
        return jsonify({"error": "Approval not found"}), 404

    if req.status not in ("APPROVED", "AUTO_APPROVED"):
        return jsonify({"error": f"Approval not approved (status={req.status})"}), 403

    # Enforce: command must be included in the approved instruction text
    # (simple substring match; conservative)
    instr = (req.instruction or "")
    if command not in instr:
        return jsonify({
            "error": "Command not present in approved instruction text; include the exact command in the approval instruction.",
        }), 403

    try:
        token = generate_token(
            approval_id=approval_id,
            worker_id="telegram-bot",
            environment=env,
            allowed_commands=[command],
            ttl_minutes=int(os.getenv("GATEWAY_TOKEN_TTL_MIN", "60")),
        )
    except Exception as e:
        # Fail closed; do not leak internals
        return jsonify({"error": "Token minting failed"}), 500

    return jsonify({"success": True, "token": token, "environment": env}), 200


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    """
    return jsonify(
        {
            "status": "healthy",
            "phase": "3",
            "verifiers": {
                "simple": "available",
                "enhanced": (
                    "available"
                    if hasattr(enhanced_verifier, "mistral_available") and enhanced_verifier.mistral_available
                    else "unavailable"
                ),
            },
            "database": "connected" if db and db_available else "memory",
            "timestamp": datetime.now().isoformat(),
        }
    ), 200


@app.route('/stats', methods=['GET'])
def get_stats():
    """
    Get verification statistics
    """
    try:
        time_range = request.args.get('range', '24h')
        range_hours = {'24h': 24, '7d': 168, '30d': 720}.get(time_range, 24)

        if db and db_available:
                db_stats = db.get_stats(hours=range_hours)
                return jsonify({
                    "total_verifications": db_stats.get('total_verifications', 0),
                    "verdicts": db_stats.get('verdicts', {}),
                    "avg_processing_time_ms": db_stats.get('avg_processing_time_ms', 0),
                    "time_range": time_range,
                    "source": "database",
                    "timestamp": datetime.now().isoformat()
                }), 200

        return jsonify({
            "total_verifications": stats_fallback["total_verifications"],
            "verdicts": stats_fallback["verdicts"],
            "time_range": "all_time",
            "source": "memory",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/watcher/acknowledge/<alert_id>", methods=["POST"])
def watcher_acknowledge(alert_id: str):
    """
    Acknowledge a watcher alert (Phase 4 Watcher Enhancement).

    Body:
      {
        "acknowledged_by": "mark@example.com"  # optional
      }
    """
    auth = _require_approval_decide()  # Require DECIDE key
    if auth is not None:
        return auth

    try:
        data = request.get_json() or {}
        acknowledged_by = (data.get("acknowledged_by") or "").strip() or None

        # Update database
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "wingman"),
            user=os.getenv("DB_USER", "wingman"),
            password=os.getenv("DB_PASSWORD", "")
        )
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE watcher_alerts
            SET acknowledged_at = NOW(), acknowledged_by = %s
            WHERE alert_id = %s AND acknowledged_at IS NULL
            RETURNING alert_id, acknowledged_at
        """, (acknowledged_by, alert_id))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        if not result:
            return jsonify({"error": "Alert not found or already acknowledged"}), 404

        return jsonify({
            "success": True,
            "alert_id": str(result[0]),
            "acknowledged_at": result[1].isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/watcher/alerts", methods=["GET"])
def watcher_alerts():
    """
    Get watcher alert history (Phase 4 Watcher Enhancement).

    Query params:
      - severity: Filter by severity (CRITICAL/HIGH/MEDIUM/LOW)
      - since: ISO timestamp (e.g., 2026-02-01T00:00:00)
      - limit: Max results (default 50, max 500)
      - worker_id: Filter by worker
      - unacknowledged: Only unacknowledged alerts (true/false)
    """
    auth = _require_approval_read()  # Require READ key
    if auth is not None:
        return auth

    try:
        severity = request.args.get("severity", "").upper()
        since = request.args.get("since", "")
        limit = min(int(request.args.get("limit", "50")), 500)
        worker_id = request.args.get("worker_id", "")
        unacknowledged = request.args.get("unacknowledged", "").lower() == "true"

        # Build query
        query = "SELECT alert_id, event_type, worker_id, severity, message, sent_at, acknowledged_at, acknowledged_by, environment FROM watcher_alerts WHERE 1=1"
        params = []

        if severity and severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            query += " AND severity = %s"
            params.append(severity)

        if since:
            query += " AND sent_at >= %s"
            params.append(since)

        if worker_id:
            query += " AND worker_id = %s"
            params.append(worker_id)

        if unacknowledged:
            query += " AND acknowledged_at IS NULL"

        query += " ORDER BY sent_at DESC LIMIT %s"
        params.append(limit)

        # Execute query
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "wingman"),
            user=os.getenv("DB_USER", "wingman"),
            password=os.getenv("DB_PASSWORD", "")
        )
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        alerts = []
        for row in rows:
            alerts.append({
                "alert_id": str(row[0]),
                "event_type": row[1],
                "worker_id": row[2],
                "severity": row[3],
                "message": row[4],
                "sent_at": row[5].isoformat() if row[5] else None,
                "acknowledged_at": row[6].isoformat() if row[6] else None,
                "acknowledged_by": row[7],
                "environment": row[8]
            })

        return jsonify({
            "alerts": alerts,
            "count": len(alerts),
            "filters": {
                "severity": severity or "all",
                "since": since or "all_time",
                "worker_id": worker_id or "all",
                "unacknowledged": unacknowledged
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/watcher/release/<worker_id>", methods=["POST"])
def watcher_release(worker_id: str):
    """
    Release a quarantined worker (Phase 4 Watcher Enhancement).

    Body:
      {
        "released_by": "mark@example.com",  # optional
        "reason": "False positive investigation complete"  # optional
      }
    """
    auth = _require_approval_decide()  # Require DECIDE key
    if auth is not None:
        return auth

    try:
        data = request.get_json() or {}
        released_by = (data.get("released_by") or "").strip() or None
        reason = (data.get("reason") or "").strip() or None

        # Import release function from watcher
        # (For production, this should be refactored into a shared module)
        import redis
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=0,
            decode_responses=True
        )

        # Check if worker is quarantined
        if not r.sismember("quarantined_workers", worker_id):
            return jsonify({"success": False, "message": "Worker not quarantined"}), 404

        # Remove from quarantine set
        r.srem("quarantined_workers", worker_id)

        # Delete quarantine metadata
        r.delete(f"quarantine:{worker_id}")

        # Log release event to database
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "wingman"),
            user=os.getenv("DB_USER", "wingman"),
            password=os.getenv("DB_PASSWORD", "")
        )
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO watcher_alerts
            (event_type, worker_id, severity, message, environment, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING alert_id, sent_at
        """, (
            "WORKER_RELEASED",
            worker_id,
            "LOW",
            f"Released by {released_by or 'unknown'}: {reason or 'No reason provided'}",
            os.getenv("DEPLOYMENT_ENV", "test"),
            json.dumps({"released_by": released_by, "reason": reason})
        ))
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": f"Worker {worker_id} released from quarantine",
            "released_at": result[1].isoformat() if result else datetime.now().isoformat(),
            "alert_id": str(result[0]) if result else None
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/', methods=['GET'])
def index():
    """
    Root endpoint - API documentation
    """
    return jsonify({
        "name": "Wingman Verification API",
        "version": "4.0.0",
        "phase": "4_enhanced",
        "endpoints": {
            "POST /check": "Validate instruction (Phase 2)",
            "POST /log_claim": "Record worker claim (Phase 3)",
            "POST /verify": "Verify a claim (Phase 1/3)",
            "POST /approvals/request": "Request human approval (Phase 4)",
            "GET /approvals/pending": "List pending approvals (Phase 4)",
            "GET /approvals/<id>": "Get approval request (Phase 4)",
            "POST /approvals/<id>/approve": "Approve (Phase 4)",
            "POST /approvals/<id>/reject": "Reject (Phase 4)",
            "POST /watcher/acknowledge/<alert_id>": "Acknowledge watcher alert (Phase 4 Enhanced)",
            "GET /watcher/alerts": "Get alert history (Phase 4 Enhanced)",
            "POST /watcher/release/<worker_id>": "Release quarantined worker (Phase 4 Enhanced)",
            "GET /health": "Check API status",
            "GET /stats": "Get verification statistics"
        },
        "timestamp": datetime.now().isoformat()
    }), 200


if __name__ == '__main__':
    # Use API_PORT if set (from docker-compose), otherwise fall back to API_INTERNAL_PORT or 5000
    internal_port = int(os.getenv('API_PORT') or os.getenv('API_INTERNAL_PORT', 5000))

    print(f"🚀 Starting Wingman Phase 3 API Server on port {internal_port}...")
    app.run(host='0.0.0.0', port=internal_port, debug=False)
