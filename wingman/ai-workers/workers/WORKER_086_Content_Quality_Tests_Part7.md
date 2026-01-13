# WORKER_086: Unit Tests - Error Handling (Tests 120-122)

**Worker ID:** WORKER_086
**Phase:** 2 - Content Quality Validator - Testing
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_085 complete

---

## 1. DELIVERABLES

Add error handling tests:

- **Tests 120-122:** Error handling (3 tests)
  - Test 120: Missing section handled gracefully
  - Test 121: LLM timeout → fallback to heuristic
  - Test 122: Invalid input (null, empty) → no crashes

---

## 2. SUCCESS_CRITERIA

- ✅ 3 tests added
- ✅ All 3 pass
- ✅ No uncaught exceptions
- ✅ Fallback behavior verified
- ✅ Total: 29/29 tests pass (94-122)

---

## 6. TEST_PROCESS

```bash
pytest wingman/tests/test_content_quality.py::test_error_missing_section -v
pytest wingman/tests/test_content_quality.py::test_error_llm_timeout -v
pytest wingman/tests/test_content_quality.py::test_error_invalid_input -v
```

---

## IMPLEMENTATION NOTES

```python
def test_error_missing_section():
    """Test 120: Missing section handled gracefully"""
    from wingman.validation.content_quality_validator import ContentQualityValidator
    from wingman.validation.semantic_analyzer import SemanticAnalyzer

    # Instruction missing half the sections
    instruction = """
DELIVERABLES: Deploy API
SUCCESS_CRITERIA: Tests pass
BOUNDARIES: TEST only
DEPENDENCIES: Database
MITIGATION: Rollback
"""

    validator = ContentQualityValidator(SemanticAnalyzer())
    result = validator.assess_content_quality(instruction)

    # Should not crash
    assert "overall_quality" in result
    # Missing sections should score 0
    assert result["section_scores"]["TEST_PROCESS"] == 0


def test_error_llm_timeout():
    """Test 121: LLM timeout → fallback"""
    from unittest.mock import Mock
    from wingman.validation.content_quality_validator import ContentQualityValidator

    # Mock analyzer that times out
    mock_analyzer = Mock()
    mock_analyzer.analyze.side_effect = TimeoutError("LLM timeout")

    validator = ContentQualityValidator(mock_analyzer)
    result = validator.analyze_section("DELIVERABLES", "Deploy API")

    # Should fallback to heuristic
    assert "score" in result
    assert result.get("method") == "heuristic"


def test_error_invalid_input():
    """Test 122: Invalid input handled"""
    from wingman.validation.content_quality_validator import ContentQualityValidator
    from wingman.validation.semantic_analyzer import SemanticAnalyzer

    validator = ContentQualityValidator(SemanticAnalyzer())

    # Empty string
    result1 = validator.assess_content_quality("")
    assert "overall_quality" in result1

    # Whitespace only
    result2 = validator.assess_content_quality("   \n\t  ")
    assert "overall_quality" in result2
```
