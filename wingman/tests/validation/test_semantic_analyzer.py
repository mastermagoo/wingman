"""
Unit tests for semantic_analyzer - Ollama integration and fallback.
Plan: With Ollama mock verify prompt structure and response parsing; without Ollama verify fallback.
"""

import json
import pytest
from unittest.mock import patch, Mock

# requests is optional at runtime (fallback when missing); needed for LLM tests
try:
    import requests as _requests
except ImportError:
    _requests = None

from validation.semantic_analyzer import SemanticAnalyzer, PROMPT_TEMPLATE
from tests.validation.fixtures import GOOD_INSTRUCTION, BAD_INSTRUCTION_DANGEROUS, SEMANTIC_ANALYZER_TEST_CASES


@pytest.fixture
def analyzer():
    return SemanticAnalyzer()


class TestSemanticAnalyzer:
    """Test semantic analyzer analyze() and fallback."""

    @pytest.mark.unit
    def test_analyze_returns_required_keys(self, analyzer):
        """Output has score, risk_level, intent_summary, concerns, reasoning"""
        result = analyzer.analyze("Create a new file validation/foo.py")
        assert "score" in result
        assert "risk_level" in result
        assert "intent_summary" in result
        assert "concerns" in result
        assert "reasoning" in result
        assert isinstance(result["score"], int)
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert isinstance(result["concerns"], list)

    @pytest.mark.unit
    def test_fallback_on_empty_instruction(self, analyzer):
        """Empty instruction uses fallback"""
        result = analyzer.analyze("")
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert 0 <= result["score"] <= 100

    @pytest.mark.unit
    def test_fallback_without_ollama(self, analyzer):
        """Without Ollama (request fails or requests missing), fallback is used"""
        if _requests is not None:
            with patch("validation.semantic_analyzer.requests.post") as mock_post:
                mock_post.side_effect = Exception("Connection refused")
                result = analyzer.analyze("Run docker system prune --all")
        else:
            result = analyzer.analyze("Run docker system prune --all")
        assert "score" in result
        assert "reasoning" in result
        assert "fallback" in result["reasoning"].lower() or "heuristic" in result["reasoning"].lower()

    @pytest.mark.unit
    def test_fallback_high_risk_keywords(self, analyzer):
        """Dangerous instruction gets high risk in fallback"""
        if _requests is not None:
            with patch("validation.semantic_analyzer.requests.post", side_effect=Exception("Unavailable")):
                result = analyzer.analyze("Run rm -rf / and DROP TABLE users")
        else:
            result = analyzer.analyze("Run rm -rf / and DROP TABLE users")
        assert result["risk_level"] == "HIGH"
        assert result["score"] <= 40

    @pytest.mark.unit
    def test_fallback_low_risk_safe_text(self, analyzer):
        """Safe instruction gets low risk in fallback"""
        if _requests is not None:
            with patch("validation.semantic_analyzer.requests.post", side_effect=Exception("Unavailable")):
                result = analyzer.analyze("Create file README.md with project description")
        else:
            result = analyzer.analyze("Create file README.md with project description")
        assert result["risk_level"] == "LOW"
        assert result["score"] >= 60

    @pytest.mark.unit
    @pytest.mark.skipif(_requests is None, reason="requests not installed")
    def test_mock_ollama_response_parsing(self, analyzer):
        """With Ollama mock, response is parsed and returned"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": json.dumps({
                "risk_level": "LOW",
                "score": 85,
                "intent_summary": "Add a validation module.",
                "concerns": [],
                "reasoning": "Development-only change.",
            })
        }
        mock_response.raise_for_status = Mock()
        with patch("validation.semantic_analyzer.requests.post", return_value=mock_response):
            result = analyzer.analyze("Add validation/code_scanner.py")
        assert result["score"] == 85
        assert result["risk_level"] == "LOW"
        assert "validation" in result["intent_summary"].lower() or result["intent_summary"]
        assert result["concerns"] == []

    @pytest.mark.unit
    def test_prompt_structure_includes_instruction(self):
        """Prompt template includes the instruction and asks for JSON"""
        instruction = "Stop the postgres container"
        prompt = PROMPT_TEMPLATE.format(instruction=instruction)
        assert "Stop the postgres container" in prompt
        assert "risk_level" in prompt
        assert "score" in prompt
        assert "JSON" in prompt

    @pytest.mark.unit
    def test_parse_handles_embedded_json(self, analyzer):
        """LLM response with extra text still parses JSON"""
        raw = 'Here is the analysis: {"risk_level": "HIGH", "score": 25, "intent_summary": "Danger.", "concerns": ["Data loss"], "reasoning": "Destructive."}'
        result = analyzer._parse_llm_response(raw, "docker rm -f all")
        assert result["score"] == 25
        assert result["risk_level"] == "HIGH"
        assert result["concerns"] == ["Data loss"]

    @pytest.mark.unit
    def test_parse_invalid_json_uses_fallback(self, analyzer):
        """Invalid JSON in response triggers fallback"""
        result = analyzer._parse_llm_response("not json at all", "do something")
        assert "score" in result
        assert "reasoning" in result

    @pytest.mark.unit
    def test_fixture_test_cases(self, analyzer):
        """Semantic analyzer test cases from fixtures (fallback path)"""
        if _requests is not None:
            with patch("validation.semantic_analyzer.requests.post", side_effect=Exception("Unavailable")):
                for case in SEMANTIC_ANALYZER_TEST_CASES:
                    result = analyzer.analyze(case["instruction"])
                    assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
                    if case.get("expected_risk"):
                        assert result["risk_level"] == case["expected_risk"], f"Case {case['name']}"
        else:
            for case in SEMANTIC_ANALYZER_TEST_CASES:
                result = analyzer.analyze(case["instruction"])
                assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
                if case.get("expected_risk"):
                    assert result["risk_level"] == case["expected_risk"], f"Case {case['name']}"
