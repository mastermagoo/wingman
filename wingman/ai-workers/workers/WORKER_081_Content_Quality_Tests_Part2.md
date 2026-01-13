# WORKER_081: Unit Tests - Per-Section Scoring (Tests 98-102)

**Worker ID:** WORKER_081
**Phase:** 2 - Content Quality Validator - Testing
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_080 complete

---

## 1. DELIVERABLES

Add per-section scoring tests to test_content_quality.py:

- **Tests 98-102:** Per-section scoring (5 tests)
  - Test 98: Excellent DELIVERABLES → score 9-10
  - Test 99: Poor SUCCESS_CRITERIA → score 0-3
  - Test 100: Good MITIGATION → score 6-8
  - Test 101: Fair BOUNDARIES → score 4-6
  - Test 102: Excellent TEST_PROCESS → score 9-10

---

## 2. SUCCESS_CRITERIA

- ✅ 5 tests added to test_content_quality.py
- ✅ All 5 tests pass
- ✅ Tests cover different score ranges (0-3, 4-6, 6-8, 9-10)
- ✅ Tests cover 5 different sections
- ✅ LLM or heuristic scoring works correctly
- ✅ Total: 9/9 tests pass (94-102)

---

## 3. BOUNDARIES

**CAN:** Add tests 98-102
**CANNOT:** Modify validator, add other tests
**Scope:** Per-section scoring tests only

---

## 4. DEPENDENCIES

- ✅ WORKER_080 complete

---

## 5. MITIGATION

**Rollback:** `git checkout wingman/tests/test_content_quality.py`

---

## 6. TEST_PROCESS

```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

pytest wingman/tests/test_content_quality.py::test_score_excellent_deliverables -v
pytest wingman/tests/test_content_quality.py::test_score_poor_success_criteria -v
pytest wingman/tests/test_content_quality.py::test_score_good_mitigation -v
pytest wingman/tests/test_content_quality.py::test_score_fair_boundaries -v
pytest wingman/tests/test_content_quality.py::test_score_excellent_test_process -v

# Expected: 5/5 pass, total 9/9 pass
```

---

## 7-10. [Standard sections]

**Type:** MECHANICAL
**Target:** ≤20 minutes

---

## IMPLEMENTATION NOTES

```python
def test_score_excellent_deliverables():
    """Test 98: Excellent DELIVERABLES section scores 9-10"""
    from wingman.validation.content_quality_validator import ContentQualityValidator
    from wingman.validation.semantic_analyzer import SemanticAnalyzer

    excellent = """Deploy API v2.1.0 to production using blue-green deployment,
    update documentation for /v2/users endpoint, complete in 2-hour window"""

    validator = ContentQualityValidator(SemanticAnalyzer())
    result = validator.analyze_section("DELIVERABLES", excellent)

    assert result["score"] >= 8, f"Expected ≥8, got {result['score']}"


def test_score_poor_success_criteria():
    """Test 99: Poor SUCCESS_CRITERIA scores 0-3"""
    from wingman.validation.content_quality_validator import ContentQualityValidator
    from wingman.validation.semantic_analyzer import SemanticAnalyzer

    poor = "Make it work"
    validator = ContentQualityValidator(SemanticAnalyzer())
    result = validator.analyze_section("SUCCESS_CRITERIA", poor)

    assert result["score"] <= 3, f"Expected ≤3, got {result['score']}"


# Tests 100-102 follow same pattern for MITIGATION, BOUNDARIES, TEST_PROCESS
```

**Reference:** Implementation Plan Lines 1429-1498
