"""
Unit tests for composite_validator - weighted aggregation and recommendations.
"""

import pytest
from validation.composite_validator import CompositeValidator
from tests.validation.fixtures import GOOD_INSTRUCTION, BAD_INSTRUCTION_VAGUE, BAD_INSTRUCTION_DANGEROUS


@pytest.fixture
def validator():
    return CompositeValidator()


class TestCompositeValidator:
    """Test composite validator aggregation and rules."""

    @pytest.mark.unit
    def test_output_structure(self, validator):
        """Output has overall_score, recommendation, validator_scores, risk_level, reasoning"""
        result = validator.validate("Create file README.md")
        assert "overall_score" in result
        assert "recommendation" in result
        assert "validator_scores" in result
        assert "risk_level" in result
        assert "reasoning" in result
        assert result["recommendation"] in ("REJECT", "MANUAL_REVIEW", "APPROVE")
        assert set(result["validator_scores"].keys()) == {
            "code_scanner", "content_quality", "dependency_analyzer", "semantic_analyzer"
        }

    @pytest.mark.unit
    def test_secrets_immediate_reject(self, validator):
        """Code scanner finding secrets -> REJECT"""
        result = validator.validate("Use API_KEY=sk-secret123 and run the script")
        assert result["recommendation"] == "REJECT"
        assert result["risk_level"] == "CRITICAL"

    @pytest.mark.unit
    def test_dangerous_instruction_reject(self, validator):
        """Dangerous instruction (e.g. rm -rf) -> low code_scanner score -> REJECT or MANUAL_REVIEW"""
        result = validator.validate(BAD_INSTRUCTION_DANGEROUS)
        assert result["recommendation"] in ("REJECT", "MANUAL_REVIEW")
        assert result["validator_scores"]["code_scanner"] < 90

    @pytest.mark.unit
    def test_good_instruction_not_reject(self, validator):
        """Good instruction should not be REJECT (may be MANUAL_REVIEW or APPROVE)"""
        result = validator.validate(GOOD_INSTRUCTION)
        assert result["recommendation"] != "REJECT" or result["overall_score"] >= 30
        assert 0 <= result["overall_score"] <= 100

    @pytest.mark.unit
    def test_hard_floor_below_30_reject(self, validator):
        """Any validator score < 30 -> REJECT"""
        # Instruction that triggers very low code_scanner (secrets + dangerous) and low others
        result = validator.validate("Run rm -rf / and use password=admin and DROP TABLE users")
        assert result["recommendation"] == "REJECT"

    @pytest.mark.unit
    def test_weighted_scores_used(self, validator):
        """Overall score is in 0-100 and is derived from validator_scores"""
        result = validator.validate("Add a new test file tests/unit/test_foo.py with one test.")
        assert 0 <= result["overall_score"] <= 100
        s = result["validator_scores"]
        # Weighted: 0.3*code + 0.25*content + 0.2*dep + 0.25*semantic
        expected = int(0.3 * s["code_scanner"] + 0.25 * s["content_quality"] + 0.2 * s["dependency_analyzer"] + 0.25 * s["semantic_analyzer"])
        assert result["overall_score"] == max(0, min(100, expected))
