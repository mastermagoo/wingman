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

# Add current directory to path to import verifiers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from simple_verifier import verify_claim as simple_verify_claim
    from enhanced_verifier import EnhancedVerifier
    from intel_integration import IntelDatabase
    from instruction_validator import InstructionValidator
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

app = Flask(__name__)
CORS(app)  # Allow all origins for now

# Initialize verifiers and validators
enhanced_verifier = EnhancedVerifier()
instruction_validator = InstructionValidator()
AUDIT_LOG = "claims_audit.jsonl"

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
