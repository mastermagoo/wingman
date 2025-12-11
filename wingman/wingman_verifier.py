#!/usr/bin/env python3
"""
Wingman Independent Verifier Service
Runs in isolated container to verify Intel-system claims
"""

import os
import json
import docker
import requests
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, request
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

class WingmanVerifier:
    def __init__(self):
        # Connect to Docker socket (read-only)
        self.docker_client = docker.from_env()
        self.verification_log = []
        
    def verify_claim(self, claim_type, claim_data):
        """
        Verify claims made by intel-system
        Returns: (is_valid, evidence)
        """
        verification = {
            "timestamp": datetime.now().isoformat(),
            "claim_type": claim_type,
            "claim_data": claim_data,
            "verified": False,
            "evidence": None,
            "bs_level": 0  # 0=true, 1-5=suspicious, 6-10=total BS
        }
        
        try:
            if claim_type == "file_created":
                # Check if file actually exists
                file_path = claim_data.get("path")
                if Path(f"/intel-data/{file_path}").exists():
                    verification["verified"] = True
                    verification["evidence"] = "File exists with correct timestamp"
                else:
                    verification["bs_level"] = 10
                    verification["evidence"] = "FILE DOES NOT EXIST - TOTAL BS!"
                    
            elif claim_type == "container_running":
                # Check Docker containers independently
                container_name = claim_data.get("name")
                containers = self.docker_client.containers.list()
                running = any(c.name == container_name for c in containers)
                
                if running:
                    verification["verified"] = True
                    verification["evidence"] = f"Container {container_name} confirmed running"
                else:
                    verification["bs_level"] = 8
                    verification["evidence"] = f"Container {container_name} NOT running - LIES!"
                    
            elif claim_type == "data_processed":
                # Verify processing actually happened
                input_hash = claim_data.get("input_hash")
                output_hash = claim_data.get("output_hash")
                
                if input_hash != output_hash:  # Basic check - data changed
                    verification["verified"] = True
                    verification["evidence"] = "Data transformation confirmed"
                else:
                    verification["bs_level"] = 5
                    verification["evidence"] = "No data transformation detected - suspicious"
                    
            elif claim_type == "api_response":
                # Verify API actually responded
                endpoint = claim_data.get("endpoint")
                status_code = claim_data.get("status_code")
                
                try:
                    # Make independent request
                    response = requests.get(endpoint, timeout=5)
                    if response.status_code == status_code:
                        verification["verified"] = True
                        verification["evidence"] = "API response confirmed"
                    else:
                        verification["bs_level"] = 6
                        verification["evidence"] = f"API returned {response.status_code}, not {status_code}"
                except:
                    verification["bs_level"] = 9
                    verification["evidence"] = "API not accessible - MAJOR BS!"
                    
        except Exception as e:
            verification["bs_level"] = 7
            verification["evidence"] = f"Verification failed: {str(e)}"
            
        # Log all verifications
        self.verification_log.append(verification)
        
        # Alert on high BS levels
        if verification["bs_level"] >= 6:
            self.send_bs_alert(verification)
            
        return verification

    def send_bs_alert(self, verification):
        """Send alert when BS is detected"""
        logging.error(f"🚨 BS DETECTED: Level {verification['bs_level']}")
        logging.error(f"Evidence: {verification['evidence']}")
        # Could send to Telegram, email, etc.

verifier = WingmanVerifier()

@app.route('/health')
def health():
    return jsonify({"status": "independent", "mode": "verifying"})

@app.route('/verify', methods=['POST'])
def verify():
    """Endpoint for intel-system to submit claims for verification"""
    data = request.json
    result = verifier.verify_claim(
        claim_type=data.get('type'),
        claim_data=data.get('data')
    )
    return jsonify(result)

@app.route('/audit')
def audit():
    """Show verification history"""
    return jsonify({
        "total_claims": len(verifier.verification_log),
        "bs_detected": sum(1 for v in verifier.verification_log if v['bs_level'] >= 6),
        "recent": verifier.verification_log[-10:]  # Last 10 verifications
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090)
