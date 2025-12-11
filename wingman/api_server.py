#!/usr/bin/env python3
"""
Wingman Web API Server
Exposes verification endpoints for the Wingman system
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
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

app = Flask(__name__)
CORS(app)  # Allow all origins for now

# Initialize enhanced verifier
enhanced_verifier = EnhancedVerifier()

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
    Verify a claim using simple or enhanced verifier

    Request body:
    {
        "claim": "I created /tmp/test.txt",
        "use_enhanced": false
    }
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
            # Enhanced verifier returns verdict string directly
            verdict = enhanced_verifier.verify_claim(claim)
            result = {
                'verdict': verdict,
                'details': f"Enhanced verification completed with verdict: {verdict}",
                'verifier': 'enhanced'
            }
        else:
            # Simple verifier is a function that returns verdict
            verdict = simple_verify_claim(claim)
            result = {
                'verdict': verdict,
                'details': f"Simple verification completed with verdict: {verdict}",
                'verifier': 'simple'
            }

        # Calculate processing time
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
                # Fall back to in-memory stats
                stats_fallback["total_verifications"] += 1
                if verdict in stats_fallback["verdicts"]:
                    stats_fallback["verdicts"][verdict] += 1
        else:
            # Update in-memory stats
            stats_fallback["total_verifications"] += 1
            verdict = result.get('verdict', 'UNVERIFIABLE')
            if verdict in stats_fallback["verdicts"]:
                stats_fallback["verdicts"][verdict] += 1

        # Prepare response
        response = {
            "verdict": verdict,
            "details": result.get('details', 'No details available'),
            "timestamp": datetime.now().isoformat(),
            "verifier": "enhanced" if use_enhanced else "simple",
            "processing_time_ms": processing_time_ms
        }

        # Add additional fields from result if present
        if 'evidence' in result:
            response['evidence'] = result['evidence']
        if 'llm_response' in result:
            response['llm_analysis'] = result['llm_response']

        return jsonify(response), 200

    except Exception as e:
        error_msg = f"Internal error: {str(e)}"
        print(f"Error in /verify: {error_msg}")
        print(traceback.format_exc())

        return jsonify({
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    Returns status of the API and verifiers
    """
    try:
        # Check if verifiers are available
        simple_status = "available"  # Simple verifier is always available (it's a function)
        enhanced_status = "unavailable"
        database_status = "disconnected"

        # Test enhanced verifier availability
        try:
            # Check if Mistral is available via Ollama
            if hasattr(enhanced_verifier, 'mistral_available') and enhanced_verifier.mistral_available:
                enhanced_status = "available"
        except:
            pass

        # Test database connectivity
        if db and db_available:
            try:
                # Try to get stats to test connection
                db.get_stats()
                database_status = "connected"
            except Exception as e:
                database_status = f"error: {str(e)}"

        return jsonify({
            "status": "healthy",
            "verifiers": {
                "simple": simple_status,
                "enhanced": enhanced_status
            },
            "database": database_status,
            "timestamp": datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/stats', methods=['GET'])
def get_stats():
    """
    Get verification statistics
    Returns counts of verifications and verdict distributions
    Supports time ranges: ?range=24h, 7d, 30d
    """
    try:
        # Get time range from query params
        time_range = request.args.get('range', '24h')

        # Convert range to hours
        range_hours = {
            '24h': 24,
            '7d': 168,
            '30d': 720
        }.get(time_range, 24)

        # Try to get stats from database
        if db and db_available:
            try:
                db_stats = db.get_stats(hours=range_hours)
                return jsonify({
                    "total_verifications": db_stats.get('total_verifications', 0),
                    "verdicts": db_stats.get('verdicts', {}),
                    "avg_processing_time_ms": db_stats.get('avg_processing_time_ms', 0),
                    "time_range": time_range,
                    "source": "database",
                    "timestamp": datetime.now().isoformat()
                }), 200
            except Exception as e:
                print(f"Failed to get stats from database: {e}")
                # Fall back to in-memory stats

        # Use in-memory fallback
        return jsonify({
            "total_verifications": stats_fallback["total_verifications"],
            "verdicts": stats_fallback["verdicts"],
            "time_range": "all_time",
            "source": "memory",
            "timestamp": datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            "error": f"Failed to retrieve stats: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/history', methods=['GET'])
def get_history():
    """
    Get paginated verification history
    Query params: ?page=1&limit=50
    """
    try:
        # Get pagination params
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        limit = min(limit, 100)  # Cap at 100 per page

        if db and db_available:
            try:
                history = db.get_verification_history(page=page, limit=limit)
                return jsonify({
                    "verifications": history.get('verifications', []),
                    "total": history.get('total', 0),
                    "page": page,
                    "limit": limit,
                    "timestamp": datetime.now().isoformat()
                }), 200
            except Exception as e:
                print(f"Failed to get history from database: {e}")
                # Return empty history on error
                return jsonify({
                    "verifications": [],
                    "total": 0,
                    "page": page,
                    "limit": limit,
                    "error": "Database not available",
                    "timestamp": datetime.now().isoformat()
                }), 200
        else:
            return jsonify({
                "verifications": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "error": "Database not available",
                "timestamp": datetime.now().isoformat()
            }), 200

    except Exception as e:
        return jsonify({
            "error": f"Failed to retrieve history: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/false-claims', methods=['GET'])
def get_false_claims():
    """
    Get analytics on false claims
    Returns most common false claims
    """
    try:
        if db and db_available:
            try:
                false_claims = db.get_false_claims_analytics()
                return jsonify({
                    "false_claims": false_claims.get('false_claims', []),
                    "total_false": false_claims.get('total_false', 0),
                    "timestamp": datetime.now().isoformat()
                }), 200
            except Exception as e:
                print(f"Failed to get false claims from database: {e}")
                return jsonify({
                    "false_claims": [],
                    "total_false": 0,
                    "error": "Database not available",
                    "timestamp": datetime.now().isoformat()
                }), 200
        else:
            return jsonify({
                "false_claims": [],
                "total_false": 0,
                "error": "Database not available",
                "timestamp": datetime.now().isoformat()
            }), 200

    except Exception as e:
        return jsonify({
            "error": f"Failed to retrieve false claims: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/', methods=['GET'])
def index():
    """
    Root endpoint - API documentation
    """
    return jsonify({
        "name": "Wingman Verification API",
        "version": "1.0.0",
        "endpoints": {
            "POST /verify": "Verify a claim using simple or enhanced verifier",
            "GET /health": "Check API and verifier health",
            "GET /stats": "Get verification statistics (supports ?range=24h|7d|30d)",
            "GET /history": "Get paginated verification history",
            "GET /false-claims": "Get analytics on false claims"
        },
        "example": {
            "endpoint": "POST /verify",
            "body": {
                "claim": "I created /tmp/test.txt",
                "use_enhanced": False
            }
        },
        "timestamp": datetime.now().isoformat()
    }), 200


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "timestamp": datetime.now().isoformat()
    }), 404


@app.errorhandler(405)
def method_not_allowed(e):
    """Handle 405 errors"""
    return jsonify({
        "error": "Method not allowed",
        "timestamp": datetime.now().isoformat()
    }), 405


if __name__ == '__main__':
    """
    Lightweight CLI runner for local/dev use.

    Port selection priority:
    1) Command-line:  --port 8101  or  -p 8101
    2) Env var:       WINGMAN_PORT=8101
    3) Default:       8001
    """
    # Default port
    port = 8001

    # Env var override
    env_port = os.environ.get("WINGMAN_PORT")
    if env_port:
        try:
            port = int(env_port)
        except ValueError:
            print(f"Invalid WINGMAN_PORT '{env_port}', falling back to {port}")

    # Simple CLI arg parsing for --port / -p
    args = sys.argv[1:]
    for idx, arg in enumerate(args):
        if arg in ("--port", "-p") and idx + 1 < len(args):
            candidate = args[idx + 1]
            try:
                port = int(candidate)
            except ValueError:
                print(f"Invalid port '{candidate}' after {arg}, keeping {port}")
            break

    print("Starting Wingman API Server...")
    print(f"Server running at http://localhost:{port}")
    print("Press Ctrl+C to stop")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )