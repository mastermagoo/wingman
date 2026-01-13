# WORKER_082: Unit Tests - Overall Score Calculation (Tests 103-107)

**Worker ID:** WORKER_082
**Phase:** 2 - Content Quality Validator - Testing
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_081 complete

---

## 1. DELIVERABLES

Add overall score calculation tests:

- **Tests 103-107:** Overall score calculation (5 tests)
  - Test 103: All sections 10 → overall 100
  - Test 104: All sections 0 → overall 0
  - Test 105: Mixed scores (5×8 + 5×6) → overall 70
  - Test 106: Single low score affects overall
  - Test 107: Weighted average calculation correct

---

## 2. SUCCESS_CRITERIA

- ✅ 5 tests added
- ✅ All 5 pass
- ✅ Tests verify formula: sum(section_scores)
- ✅ Edge cases covered
- ✅ Total: 14/14 tests pass (94-107)

---

## 6. TEST_PROCESS

```bash
pytest wingman/tests/test_content_quality.py::test_overall_score_perfect -v
pytest wingman/tests/test_content_quality.py::test_overall_score_zero -v
pytest wingman/tests/test_content_quality.py::test_overall_score_mixed -v
pytest wingman/tests/test_content_quality.py::test_overall_score_single_low -v
pytest wingman/tests/test_content_quality.py::test_overall_score_weighted -v
```

---

## IMPLEMENTATION NOTES

```python
def test_overall_score_perfect():
    """Test 103: All sections 10 → overall 100"""
    scores = {f"SECTION_{i}": 10 for i in range(10)}
    overall = calculate_overall_score(scores)
    assert overall == 100


def test_overall_score_mixed():
    """Test 105: Mixed scores calculated correctly"""
    from wingman.validation.content_quality_validator import ContentQualityValidator
    from wingman.validation.semantic_analyzer import SemanticAnalyzer

    # Create instruction with known quality levels
    instruction = """
DELIVERABLES: Deploy API v2.1.0  # Should score ~8
SUCCESS_CRITERIA: Tests pass  # Should score ~4
... (all 10 sections)
"""

    validator = ContentQualityValidator(SemanticAnalyzer())
    result = validator.assess_content_quality(instruction)

    assert 0 <= result["overall_quality"] <= 100
    # Sum of individual scores should equal overall
    assert result["overall_quality"] == sum(result["section_scores"].values())
```
