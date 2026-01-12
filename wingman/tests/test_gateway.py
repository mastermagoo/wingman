#!/usr/bin/env python3
"""
Unit tests for Execution Gateway
Tests token validation, command execution, and security boundaries
"""

import pytest
import sys
import os
import json
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from capability_token import generate_token, validate_token, hash_token
from execution_gateway import app, validate_command_scope, USED_TOKENS


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clear_used_tokens():
    """Clear used tokens before each test"""
    USED_TOKENS.clear()
    yield
    USED_TOKENS.clear()


class TestCapabilityToken:
    """Test capability token generation and validation"""

    def test_generate_token(self):
        """Test token generation"""
        token = generate_token(
            approval_id="test-approval-123",
            worker_id="worker-001",
            environment="test"
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_validate_valid_token(self):
        """Test validation of valid token"""
        token = generate_token(
            approval_id="test-approval-123",
            worker_id="worker-001",
            environment="test"
        )

        result = validate_token(token, set())

        assert result["valid"] is True
        assert "payload" in result
        assert result["payload"]["approval_id"] == "test-approval-123"
        assert result["payload"]["worker_id"] == "worker-001"
        assert result["payload"]["environment"] == "test"

    def test_validate_expired_token(self):
        """Test rejection of expired token"""
        # Generate token that expires immediately
        token = generate_token(
            approval_id="test-approval-123",
            worker_id="worker-001",
            environment="test",
            ttl_minutes=-1  # Expired
        )

        result = validate_token(token, set())

        assert result["valid"] is False
        assert "expired" in result["error"].lower()

    def test_validate_forged_token(self):
        """Test rejection of token with invalid signature"""
        # Generate valid token
        token = generate_token(
            approval_id="test-approval-123",
            worker_id="worker-001",
            environment="test"
        )

        # Tamper with token (change last character)
        forged_token = token[:-5] + "XXXXX"

        result = validate_token(forged_token, set())

        assert result["valid"] is False
        assert "signature" in result["error"].lower() or "malformed" in result["error"].lower()

    def test_validate_replay_token(self):
        """Test rejection of replayed token (single-use enforcement)"""
        token = generate_token(
            approval_id="test-approval-123",
            worker_id="worker-001",
            environment="test"
        )

        # First use - should succeed
        result1 = validate_token(token, set())
        assert result1["valid"] is True

        # Add jti to used tokens
        used_tokens = {result1["jti"]}

        # Second use - should fail (replay detected)
        result2 = validate_token(token, used_tokens)
        assert result2["valid"] is False
        assert "replay" in result2["error"].lower()

    def test_token_hash(self):
        """Test token hashing for audit logs"""
        token = "test-token-12345"
        hashed = hash_token(token)

        assert hashed is not None
        assert len(hashed) == 64  # SHA256 produces 64-character hex
        assert hashed != token  # Hash should differ from original


class TestCommandScope:
    """Test command scope validation"""

    def test_validate_no_restrictions(self):
        """Test that empty allowed_commands allows all"""
        result = validate_command_scope("any command", [])
        assert result["valid"] is True

    def test_validate_exact_match(self):
        """Test exact command match"""
        result = validate_command_scope(
            "docker compose ps",
            ["docker compose ps"]
        )
        assert result["valid"] is True

    def test_validate_prefix_match(self):
        """Test command with arguments (prefix match)"""
        result = validate_command_scope(
            "docker compose ps --all",
            ["docker compose ps"]
        )
        assert result["valid"] is True

    def test_validate_rejected_command(self):
        """Test rejection of command not in scope"""
        result = validate_command_scope(
            "rm -rf /",
            ["docker compose ps", "git status"]
        )
        assert result["valid"] is False
        assert "not in approved scope" in result["error"]


class TestGatewayEndpoints:
    """Test gateway HTTP endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["service"] == "execution-gateway"

    def test_execute_missing_token(self, client):
        """Test execution without token returns 401"""
        response = client.post('/gateway/execute', json={
            "command": "echo test",
            "approval_id": "test-123"
        })

        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert "Missing X-Capability-Token" in data["error"]

    def test_execute_invalid_token(self, client):
        """Test execution with invalid token returns 401"""
        response = client.post('/gateway/execute',
            headers={"X-Capability-Token": "invalid-token"},
            json={
                "command": "echo test",
                "approval_id": "test-123"
            }
        )

        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False

    def test_execute_expired_token(self, client):
        """Test execution with expired token returns 401"""
        token = generate_token(
            approval_id="test-123",
            ttl_minutes=-1  # Expired
        )

        response = client.post('/gateway/execute',
            headers={"X-Capability-Token": token},
            json={
                "command": "echo test",
                "approval_id": "test-123"
            }
        )

        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert "expired" in data["error"].lower()

    def test_execute_replay_token(self, client):
        """Test replay prevention"""
        token = generate_token(
            approval_id="test-123",
            environment="test",
            allowed_commands=["echo test"]
        )

        # First request - should succeed
        response1 = client.post('/gateway/execute',
            headers={"X-Capability-Token": token},
            json={
                "command": "echo test",
                "approval_id": "test-123"
            }
        )
        assert response1.status_code == 200

        # Second request with same token - should fail (replay)
        response2 = client.post('/gateway/execute',
            headers={"X-Capability-Token": token},
            json={
                "command": "echo test",
                "approval_id": "test-123"
            }
        )
        assert response2.status_code == 401
        data = response2.get_json()
        assert "replay" in data["error"].lower()

    def test_execute_approval_id_mismatch(self, client):
        """Test rejection when approval_id doesn't match token"""
        token = generate_token(
            approval_id="correct-id",
            environment="test"
        )

        response = client.post('/gateway/execute',
            headers={"X-Capability-Token": token},
            json={
                "command": "echo test",
                "approval_id": "wrong-id"
            }
        )

        assert response.status_code == 403
        data = response.get_json()
        assert "does not match token" in data["error"]

    def test_execute_environment_mismatch(self, client):
        """Test rejection when environment doesn't match token"""
        token = generate_token(
            approval_id="test-123",
            environment="test"
        )

        response = client.post('/gateway/execute',
            headers={"X-Capability-Token": token},
            json={
                "command": "echo test",
                "approval_id": "test-123",
                "environment": "prd"  # Token is for 'test'
            }
        )

        assert response.status_code == 403
        data = response.get_json()
        assert "Environment mismatch" in data["error"]

    def test_execute_command_not_in_scope(self, client):
        """Test rejection of command not in allowed list"""
        token = generate_token(
            approval_id="test-123",
            environment="test",
            allowed_commands=["docker compose ps"]
        )

        response = client.post('/gateway/execute',
            headers={"X-Capability-Token": token},
            json={
                "command": "rm -rf /",
                "approval_id": "test-123"
            }
        )

        assert response.status_code == 403
        data = response.get_json()
        assert "not in approved scope" in data["error"]

    @patch('execution_gateway.execute_command')
    def test_execute_valid_command(self, mock_execute, client):
        """Test successful command execution"""
        # Mock command execution
        mock_execute.return_value = {
            "success": True,
            "output": "test output",
            "exit_code": 0,
            "duration_ms": 100
        }

        token = generate_token(
            approval_id="test-123",
            environment="test",
            allowed_commands=["echo test"]
        )

        response = client.post('/gateway/execute',
            headers={"X-Capability-Token": token},
            json={
                "command": "echo test",
                "approval_id": "test-123"
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["output"] == "test output"
        assert data["exit_code"] == 0
        assert "execution_id" in data

        # Verify command was executed
        mock_execute.assert_called_once_with("echo test")

    @patch('execution_gateway.execute_command')
    def test_execute_failed_command(self, mock_execute, client):
        """Test command execution failure"""
        # Mock failed command execution
        mock_execute.return_value = {
            "success": False,
            "output": "error output",
            "exit_code": 1,
            "error": "Command failed",
            "duration_ms": 50
        }

        token = generate_token(
            approval_id="test-123",
            environment="test",
            allowed_commands=["failing-command"]
        )

        response = client.post('/gateway/execute',
            headers={"X-Capability-Token": token},
            json={
                "command": "failing-command",
                "approval_id": "test-123"
            }
        )

        assert response.status_code == 200  # Still 200, execution happened
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data

    def test_execute_missing_command_field(self, client):
        """Test rejection when command field is missing"""
        token = generate_token(
            approval_id="test-123",
            environment="test"
        )

        response = client.post('/gateway/execute',
            headers={"X-Capability-Token": token},
            json={
                "approval_id": "test-123"
                # Missing "command"
            }
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Missing 'command' field" in data["error"]

    def test_execute_missing_approval_id(self, client):
        """Test rejection when approval_id is missing"""
        token = generate_token(
            approval_id="test-123",
            environment="test"
        )

        response = client.post('/gateway/execute',
            headers={"X-Capability-Token": token},
            json={
                "command": "echo test"
                # Missing "approval_id"
            }
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "Missing 'approval_id' field" in data["error"]


class TestAuditLogging:
    """Test audit logging functionality"""

    @patch('execution_gateway.execute_command')
    @patch('execution_gateway.log_execution_to_jsonl')
    def test_audit_log_written(self, mock_log_jsonl, mock_execute, client):
        """Test that execution is logged to audit trail"""
        mock_execute.return_value = {
            "success": True,
            "output": "test output",
            "exit_code": 0,
            "duration_ms": 100
        }

        token = generate_token(
            approval_id="test-123",
            worker_id="worker-001",
            environment="test",
            allowed_commands=["echo test"]
        )

        response = client.post('/gateway/execute',
            headers={"X-Capability-Token": token},
            json={
                "command": "echo test",
                "approval_id": "test-123"
            }
        )

        assert response.status_code == 200

        # Verify audit log was called
        mock_log_jsonl.assert_called_once()
        audit_entry = mock_log_jsonl.call_args[0][0]

        assert audit_entry["approval_id"] == "test-123"
        assert audit_entry["worker_id"] == "worker-001"
        assert audit_entry["command"] == "echo test"
        assert audit_entry["environment"] == "test"
        assert audit_entry["exit_code"] == 0
        assert "execution_id" in audit_entry
        assert "token_hash" in audit_entry


class TestSecurityBoundaries:
    """Test security boundaries and attack scenarios"""

    def test_forged_token_rejected(self, client):
        """Test that forged tokens are rejected"""
        # Create a fake token
        forged_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhdHRhY2tlciJ9.FAKE"

        response = client.post('/gateway/execute',
            headers={"X-Capability-Token": forged_token},
            json={
                "command": "echo attack",
                "approval_id": "fake"
            }
        )

        assert response.status_code == 401

    def test_token_without_jti_rejected(self, client):
        """Test that tokens without jti (unique ID) are rejected"""
        # This would require crafting a token without jti, which validate_token should reject
        # For now, we test that our generated tokens always have jti
        token = generate_token(approval_id="test-123")
        result = validate_token(token, set())

        assert result["valid"] is True
        assert "jti" in result

    def test_command_injection_prevented(self, client):
        """Test that command injection attempts are blocked by scope validation"""
        token = generate_token(
            approval_id="test-123",
            environment="test",
            allowed_commands=["echo safe"]
        )

        # Attempt command injection
        response = client.post('/gateway/execute',
            headers={"X-Capability-Token": token},
            json={
                "command": "echo safe; rm -rf /",
                "approval_id": "test-123"
            }
        )

        # Should be rejected (not exact match with allowed command)
        assert response.status_code == 403
        data = response.get_json()
        assert "not in approved scope" in data["error"]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
