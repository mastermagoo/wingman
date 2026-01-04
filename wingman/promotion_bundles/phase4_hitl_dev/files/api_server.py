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
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

app = Flask(__name__)
CORS(app)  # Allow all origins for now

# Initialize verifiers and validators
enhanced_verifier = EnhancedVerifier()
instruction_validator = InstructionValidator()
# Path to audit log - using relative path from app root
AUDIT_LOG = os.path.join(os.path.dirname(__file__), "data", "claims_audit.jsonl")
approval_store = approval_default_store()

APPROVAL_API_KEY = os.getenv("WINGMAN_APPROVAL_API_KEY", "").strip()


def _require_approval_key() -> Optional[tuple]:
    """
    Optional protection for approve/reject endpoints.
    If WINGMAN_APPROVAL_API_KEY is set, require header X-Wingman-Approval-Key to match.
    """
    if not APPROVAL_API_KEY:
        return None
    provided = (request.headers.get("X-Wingman-Approval-Key") or "").strip()
    if not provided or provided != APPROVAL_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
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
    Phase 2: Validate instruction against 10-point framework
    """
    try:
        data = request.get_json()
        if not data or 'instruction' not in data:
            return jsonify({
                "error": "Missing 'instruction' field",
                "approved": False,
                "score": 0
            }), 400
        
        result = instruction_validator.validate(data['instruction'])
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


@app.route("/approvals/request", methods=["POST"])
def approvals_request():
    """
    Phase 4 (Original): Request human approval before proceeding with high-risk work.

    Body:
      {
        "worker_id": "123",
        "task_name": "Deploy schema changes",
        "instruction": "....",
        "deployment_env": "dev|test|prd" (optional)
      }
    """
    try:
        data = request.get_json() or {}
        instruction = (data.get("instruction") or "").strip()
        worker_id = str(data.get("worker_id", "unknown"))
        task_name = (data.get("task_name") or "").strip()
        deployment_env = (data.get("deployment_env") or os.getenv("DEPLOYMENT_ENV", "")).strip()

        if not instruction:
            return jsonify({"error": "Missing 'instruction' field"}), 400

        risk = assess_risk(instruction, task_name=task_name, deployment_env=deployment_env)
        risk_level = risk["risk_level"]
        risk_reason = risk["risk_reason"]

        if risk_level == "LOW":
            req = approval_store.create_request(
                worker_id=worker_id,
                task_name=task_name,
                instruction=instruction,
                risk_level=risk_level,
                risk_reason=risk_reason,
                status="AUTO_APPROVED",
            )
            return jsonify(
                {
                    "needs_approval": False,
                    "status": "AUTO_APPROVED",
                    "request": req.to_dict(),
                    "risk": risk,
                }
            ), 200

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
        return jsonify(
            {
                "needs_approval": True,
                "status": "PENDING",
                "request": req.to_dict(),
                "risk": risk,
            }
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/approvals/pending", methods=["GET"])
def approvals_pending():
    try:
        limit = int(request.args.get("limit", "20"))
        pending = approval_store.list_pending(limit=limit)
        return jsonify({"pending": [p.to_dict() for p in pending], "count": len(pending)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/approvals/<request_id>", methods=["GET"])
def approvals_get(request_id: str):
    try:
        req = approval_store.get(request_id)
        if not req:
            return jsonify({"error": "Not found"}), 404
        return jsonify(req.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/approvals/<request_id>/approve", methods=["POST"])
def approvals_approve(request_id: str):
    auth = _require_approval_key()
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
    auth = _require_approval_key()
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


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    """
    return jsonify({
        "status": "healthy",
        "phase": "3",
        "verifiers": {
            "simple": "available",
            "enhanced": "available" if hasattr(enhanced_verifier, 'mistral_available') and enhanced_verifier.mistral_available else "unavailable"
        },
        "database": "connected" if db and db_available else "memory",
        "timestamp": datetime.now().isoformat()
    }), 200


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


@app.route('/', methods=['GET'])
def index():
    """
    Root endpoint - API documentation
    """
    return jsonify({
        "name": "Wingman Verification API",
        "version": "3.0.0",
        "phase": "3",
        "endpoints": {
            "POST /check": "Validate instruction (Phase 2)",
            "POST /log_claim": "Record worker claim (Phase 3)",
            "POST /verify": "Verify a claim (Phase 1/3)",
            "POST /approvals/request": "Request human approval (Phase 4)",
            "GET /approvals/pending": "List pending approvals (Phase 4)",
            "GET /approvals/<id>": "Get approval request (Phase 4)",
            "POST /approvals/<id>/approve": "Approve (Phase 4)",
            "POST /approvals/<id>/reject": "Reject (Phase 4)",
            "GET /health": "Check API status",
            "GET /stats": "Get verification statistics"
        },
        "timestamp": datetime.now().isoformat()
    }), 200


if __name__ == '__main__':
    internal_port = int(os.getenv('API_INTERNAL_PORT', 5000))
    # Fallback for PRD compose which uses 8001 mapping
    if os.getenv('DEPLOYMENT_ENV') == 'prd':
        internal_port = 8001
        
    print(f"🚀 Starting Wingman Phase 3 API Server on port {internal_port}...")
    app.run(host='0.0.0.0', port=internal_port, debug=False)
