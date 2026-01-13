# WORKER_085: Unit Tests - Weighting (Tests 116-119)

**Worker ID:** WORKER_085
**Phase:** 2 - Content Quality Validator - Testing
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_084 complete

---

## 1. DELIVERABLES

Add section weighting tests:

- **Tests 116-119:** Weighting (4 tests)
  - Test 116: Equal weights → same as simple sum
  - Test 117: DELIVERABLES 2x weight → higher overall
  - Test 118: Custom weights (3 sections 2x) → calculated correctly
  - Test 119: Weight validation (reject negative/zero weights)

---

## 2. SUCCESS_CRITERIA

- ✅ 4 tests added
- ✅ All 4 pass
- ✅ Weighted formula verified
- ✅ Validation tested
- ✅ Total: 26/26 tests pass (94-119)

---

## 6. TEST_PROCESS

```bash
pytest wingman/tests/test_content_quality.py::test_weighting_equal -v
pytest wingman/tests/test_content_quality.py::test_weighting_deliverables_2x -v
pytest wingman/tests/test_content_quality.py::test_weighting_custom -v
pytest wingman/tests/test_content_quality.py::test_weighting_validation -v
```

---

## IMPLEMENTATION NOTES

```python
def test_weighting_equal():
    """Test 116: Equal weights = simple sum"""
    from wingman.validation.content_quality_validator import calculate_weighted_score

    scores = {f"S{i}": 8 for i in range(10)}
    weights = {f"S{i}": 1.0 for i in range(10)}

    result = calculate_weighted_score(scores, weights)
    assert result == 80  # 10 sections × 8 points


def test_weighting_deliverables_2x():
    """Test 117: DELIVERABLES 2x weight increases overall"""
    from wingman.validation.content_quality_validator import calculate_weighted_score

    scores = {"DELIVERABLES": 10, **{f"S{i}": 5 for i in range(9)}}

    # Equal weights
    weights_equal = {s: 1.0 for s in scores.keys()}
    result_equal = calculate_weighted_score(scores, weights_equal)

    # DELIVERABLES 2x
    weights_2x = {s: 1.0 for s in scores.keys()}
    weights_2x["DELIVERABLES"] = 2.0
    result_2x = calculate_weighted_score(scores, weights_2x)

    assert result_2x > result_equal  # 2x weight increases score
```
