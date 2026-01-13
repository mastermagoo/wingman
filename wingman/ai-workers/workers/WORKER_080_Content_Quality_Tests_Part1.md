# WORKER_080: Unit Tests - Section Extraction (Tests 94-97)

**Worker ID:** WORKER_080
**Phase:** 2 - Content Quality Validator - Testing
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_079 complete (validator ready)

---

## 1. DELIVERABLES

Create first test file for content quality validator:

- **File:** `/Volumes/Data/ai_projects/wingman-system/wingman/wingman/tests/test_content_quality.py`
- **Tests 94-97:** Section extraction tests (4 tests)
  - Test 94: Valid 10-point instruction → all sections extracted
  - Test 95: Missing sections → empty strings for missing
  - Test 96: Empty sections → detected as empty
  - Test 97: Malformed instruction → no crashes, returns dict

---

## 2. SUCCESS_CRITERIA

- ✅ File `test_content_quality.py` created in `wingman/tests/`
- ✅ All 4 tests pass: `pytest wingman/tests/test_content_quality.py::test_parse_valid_instruction -v`
- ✅ Test 94: Extracts all 10 sections correctly
- ✅ Test 95: Missing sections return empty string
- ✅ Test 96: Empty sections handled
- ✅ Test 97: Malformed input doesn't crash
- ✅ All tests use proper fixtures and assertions
- ✅ Coverage: `parse_10_point_sections()` function

---

## 3. BOUNDARIES

**CAN:** Create test file, add fixtures, add first 4 tests
**CANNOT:** Modify validator code, add other tests (WORKER_081-087)
**Scope:** Tests 94-97 only (section extraction)

---

## 4. DEPENDENCIES

- ✅ WORKER_079 complete: validator ready for testing
- ✅ pytest installed
- ✅ `wingman/tests/` directory exists

---

## 5. MITIGATION

**Rollback:**
```bash
rm /Volumes/Data/ai_projects/wingman-system/wingman/wingman/tests/test_content_quality.py
```

**Recovery Time:** <2 minutes

---

## 6. TEST_PROCESS

```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

# Run specific tests
pytest wingman/tests/test_content_quality.py::test_parse_valid_instruction -v
pytest wingman/tests/test_content_quality.py::test_parse_missing_sections -v
pytest wingman/tests/test_content_quality.py::test_parse_empty_sections -v
pytest wingman/tests/test_content_quality.py::test_parse_malformed_instruction -v

# Run all 4 tests
pytest wingman/tests/test_content_quality.py -v -k "test_parse"

# Expected: 4/4 tests pass
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "WORKER_080",
  "status": "COMPLETE",
  "duration_minutes": 18,
  "tests_created": 4,
  "tests_passed": 4,
  "tests_failed": 0,
  "coverage": {
    "function": "parse_10_point_sections",
    "lines_covered": 25,
    "branch_coverage": "90%"
  }
}
```

---

## 8. TASK_CLASSIFICATION

**Type:** MECHANICAL
**Complexity:** Medium (test design)

---

## 9. RETROSPECTIVE

```python
{
  "worker_id": "WORKER_080",
  "task": "Tests 94-97 - Section extraction tests (4 tests)",
  "next_worker": "WORKER_081",
  "tests_created": ["test_parse_valid_instruction", "test_parse_missing_sections",
                    "test_parse_empty_sections", "test_parse_malformed_instruction"],
  "lessons_learned": [
    "Fixture-based tests improve readability",
    "Edge case testing catches regex issues"
  ]
}
```

---

## 10. PERFORMANCE_REQUIREMENTS

**Target:** ≤20 minutes
**Test Execution:** All 4 tests <1 second total

---

## IMPLEMENTATION NOTES

**Test File Structure:**

```python
"""
Unit tests for Content Quality Validator - Phase 2
Tests 94-97: Section extraction
"""

import pytest
from wingman.validation.content_quality_validator import parse_10_point_sections


@pytest.fixture
def valid_instruction():
    """Fixture: Complete 10-point instruction"""
    return """
DELIVERABLES: Deploy API v2.1.0 to production
SUCCESS_CRITERIA: All health checks return 200
BOUNDARIES: Do NOT modify database schema
DEPENDENCIES: Database v1.2+ (confirmed)
MITIGATION: Rollback: docker tag api:previous
TEST_PROCESS: pytest -v tests/
TEST_RESULTS_FORMAT: JSON {passed: N, failed: N}
RESOURCE_REQUIREMENTS: 4 CPU, 8GB RAM
RISK_ASSESSMENT: Low risk - TEST environment
QUALITY_METRICS: Error <0.1%, latency <200ms
"""


def test_parse_valid_instruction(valid_instruction):
    """Test 94: Parse valid 10-point instruction"""
    result = parse_10_point_sections(valid_instruction)

    assert len(result) == 10, "Should return 10 sections"
    assert "DELIVERABLES" in result
    assert "Deploy API" in result["DELIVERABLES"]
    assert all(section in result for section in [
        "DELIVERABLES", "SUCCESS_CRITERIA", "BOUNDARIES",
        "DEPENDENCIES", "MITIGATION", "TEST_PROCESS",
        "TEST_RESULTS_FORMAT", "RESOURCE_REQUIREMENTS",
        "RISK_ASSESSMENT", "QUALITY_METRICS"
    ])


def test_parse_missing_sections():
    """Test 95: Parse instruction with missing sections"""
    instruction = "DELIVERABLES: Deploy API\nSUCCESS_CRITERIA: Tests pass"
    result = parse_10_point_sections(instruction)

    assert len(result) == 10, "Should return dict with 10 keys"
    assert result["DELIVERABLES"] != "", "DELIVERABLES should not be empty"
    assert result["BOUNDARIES"] == "", "Missing sections should be empty string"


def test_parse_empty_sections():
    """Test 96: Parse instruction with empty sections"""
    instruction = "DELIVERABLES:\nSUCCESS_CRITERIA:\nBOUNDARIES:"
    result = parse_10_point_sections(instruction)

    assert len(result) == 10
    # Empty sections should be detected
    assert result["DELIVERABLES"] == "" or len(result["DELIVERABLES"]) < 5


def test_parse_malformed_instruction():
    """Test 97: Parse malformed instruction without crashes"""
    instruction = "This is not a 10-point instruction at all"
    result = parse_10_point_sections(instruction)

    assert isinstance(result, dict), "Should return dict"
    assert len(result) == 10, "Should have 10 keys even for malformed input"
```

**Reference:** Implementation Plan Lines 1429-1498 (Test 94-97 specifications)
