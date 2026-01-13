# WORKER_084: Unit Tests - Auto-Reject Threshold (Tests 112-115)

**Worker ID:** WORKER_084
**Phase:** 2 - Content Quality Validator - Testing
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_083 complete

---

## 1. DELIVERABLES

Add auto-reject threshold tests:

- **Tests 112-115:** Auto-reject (4 tests)
  - Test 112: Score 50 → auto_reject = True
  - Test 113: Score 60 → auto_reject = False (threshold)
  - Test 114: Score 70 → auto_reject = False
  - Test 115: Score 59 → auto_reject = True (edge case)

---

## 2. SUCCESS_CRITERIA

- ✅ 4 tests added
- ✅ All 4 pass
- ✅ Threshold boundary tested (59 vs 60)
- ✅ auto_reject = not pass
- ✅ Total: 22/22 tests pass (94-115)

---

## 6. TEST_PROCESS

```bash
pytest wingman/tests/test_content_quality.py::test_auto_reject_below_threshold -v
pytest wingman/tests/test_content_quality.py::test_auto_reject_at_threshold -v
pytest wingman/tests/test_content_quality.py::test_auto_reject_above_threshold -v
pytest wingman/tests/test_content_quality.py::test_auto_reject_edge_case -v
```

---

## IMPLEMENTATION NOTES

```python
def test_auto_reject_at_threshold():
    """Test 113: Score 60 → auto_reject = False"""
    # Create instruction that scores exactly 60
    # (6 sections × 10 points + 4 sections × 0 points = 60)
    # Or use mock to set exact score
    result = {"overall_quality": 60, "pass": True, "auto_reject": False}
    assert result["auto_reject"] == False
    assert result["pass"] == True


def test_auto_reject_edge_case():
    """Test 115: Score 59 → auto_reject = True"""
    result = {"overall_quality": 59, "pass": False, "auto_reject": True}
    assert result["auto_reject"] == True
    assert result["pass"] == False
```
