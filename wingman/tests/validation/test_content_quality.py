"""
Unit tests for content_quality_validator
"""

import pytest
from validation.content_quality_validator import ContentQualityValidator
from tests.validation.fixtures import (
    GOOD_INSTRUCTION,
    BAD_INSTRUCTION_VAGUE,
    MEDIUM_QUALITY_INSTRUCTION,
    CONTENT_QUALITY_TEST_CASES,
)


@pytest.fixture
def validator():
    return ContentQualityValidator()


class TestContentQualityValidator:
    """Test content quality validator scoring"""

    @pytest.mark.unit
    def test_high_quality_scoring(self, validator):
        """Good instruction should score well"""
        result = validator.validate(GOOD_INSTRUCTION)
        assert result["score"] >= 60
        assert result["recommendation"] in ("APPROVE", "MANUAL_REVIEW")

    @pytest.mark.unit
    def test_low_quality_scoring(self, validator):
        """Vague instruction should score poorly"""
        result = validator.validate(BAD_INSTRUCTION_VAGUE)
        assert result["score"] < 60
        assert result["recommendation"] == "REJECT"

    @pytest.mark.unit
    def test_medium_quality_scoring(self, validator):
        """Medium quality instruction should be in the middle range"""
        result = validator.validate(MEDIUM_QUALITY_INSTRUCTION)
        assert 20 <= result["score"] <= 70

    @pytest.mark.unit
    def test_section_by_section_scoring(self, validator):
        """Each 10-point section should be scored individually"""
        result = validator.validate(GOOD_INSTRUCTION)
        assert "section_scores" in result
        assert len(result["section_scores"]) == 10
        for section_name, score in result["section_scores"].items():
            assert 0 <= score <= 10, f"{section_name} score {score} out of range"

    @pytest.mark.unit
    def test_empty_instruction(self, validator):
        """Empty instruction should score 0"""
        result = validator.validate("")
        assert result["score"] == 0
        assert result["recommendation"] == "REJECT"

    @pytest.mark.unit
    def test_tbd_instruction_scores_low(self, validator):
        """Instruction with only TBD content should score very low"""
        tbd_instruction = (
            "DELIVERABLES: TBD\n"
            "SUCCESS_CRITERIA: TBD\n"
            "BOUNDARIES: TBD\n"
            "DEPENDENCIES: TBD\n"
            "MITIGATION: TBD\n"
            "TEST_PROCESS: TBD\n"
            "TEST_RESULTS_FORMAT: TBD\n"
            "RESOURCE_REQUIREMENTS: TBD\n"
            "RISK_ASSESSMENT: TBD\n"
            "QUALITY_METRICS: TBD\n"
        )
        result = validator.validate(tbd_instruction)
        assert result["score"] < 30
        assert result["recommendation"] == "REJECT"

    @pytest.mark.unit
    def test_weakest_sections_identified(self, validator):
        """Weakest sections should be identified"""
        result = validator.validate(BAD_INSTRUCTION_VAGUE)
        assert "weakest_sections" in result
        assert len(result["weakest_sections"]) > 0

    @pytest.mark.unit
    def test_output_structure(self, validator):
        """Output should have all expected keys"""
        result = validator.validate("anything")
        assert "score" in result
        assert "section_scores" in result
        assert "weakest_sections" in result
        assert "recommendation" in result
        assert "reasoning" in result
        assert isinstance(result["score"], int)
        assert result["recommendation"] in ("REJECT", "MANUAL_REVIEW", "APPROVE")

    @pytest.mark.unit
    def test_detailed_beats_vague(self, validator):
        """A detailed instruction should always score higher than a vague one"""
        detailed = validator.validate(GOOD_INSTRUCTION)
        vague = validator.validate(BAD_INSTRUCTION_VAGUE)
        assert detailed["score"] > vague["score"]

    @pytest.mark.unit
    def test_missing_sections_score_zero(self, validator):
        """Sections not present in text should score 0"""
        partial = "DELIVERABLES:\n- Create a file\n- Test it"
        result = validator.validate(partial)
        for section, score in result["section_scores"].items():
            if section != "DELIVERABLES":
                assert score == 0, f"{section} should be 0 for partial instruction"

    @pytest.mark.unit
    def test_fixture_test_cases(self, validator):
        """Validate against fixture test cases"""
        for case in CONTENT_QUALITY_TEST_CASES:
            result = validator.validate(case["instruction"])
            if "min_score" in case:
                assert result["score"] >= case["min_score"], \
                    f"Case '{case['name']}': score {result['score']} < min {case['min_score']}"
            if "max_score" in case:
                assert result["score"] <= case["max_score"], \
                    f"Case '{case['name']}': score {result['score']} > max {case['max_score']}"

    @pytest.mark.unit
    def test_specificity_rewarded(self, validator):
        """Instructions with file paths and code refs should score higher"""
        specific = (
            "DELIVERABLES:\n"
            "- Create `validation/code_scanner.py` with `CodeScanner` class\n"
            "- Implement `scan()` method returning dict with score 0-100\n"
        )
        generic = (
            "DELIVERABLES:\n"
            "- Create a file\n"
            "- Implement a method\n"
        )
        specific_result = validator.validate(specific)
        generic_result = validator.validate(generic)
        assert specific_result["section_scores"]["DELIVERABLES"] > \
               generic_result["section_scores"]["DELIVERABLES"]
