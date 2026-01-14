# WORKER_059: Content Quality Validator - Score Aggregator

**Worker ID:** WORKER_059
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_058 complete

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/content_quality_validator.py`
- **Function:** `calculate_overall_score(section_scores: Dict[str, int]) -> int`
- **Purpose:** Aggregate 10 section scores (0-10 each) into overall score (0-100)
- **Formula:** Sum all section scores (max 100)
- **Return:** Integer 0-100
- **Location:** `content_quality_validator.py`

---

## 2. SUCCESS_CRITERIA

- ✅ Function calculates: `sum(section_scores.values())`
- ✅ Returns 100 when all sections score 10
- ✅ Returns 0 when all sections score 0
- ✅ Handles partial scores correctly (e.g., 5 sections × 8 = 40, 5 sections × 10 = 50 → total 90)
- ✅ Validates input dict has exactly 10 keys
- ✅ Raises ValueError if score out of range (0-10 per section)

---

## 3. BOUNDARIES

**CAN:** Add `calculate_overall_score()` function
**CANNOT:** Modify scoring logic for individual sections
**Scope:** Aggregation only

---

## 4. DEPENDENCIES

- ✅ WORKER_058 complete

---

## 5. MITIGATION

**Rollback:** `git checkout wingman/validation/content_quality_validator.py`
**Recovery Time:** <2 minutes

---

## 6. TEST_PROCESS

```bash
python3 -c "
from wingman.validation.content_quality_validator import calculate_overall_score

# All 10s -> 100
scores = {f'SECTION_{i}': 10 for i in range(10)}
assert calculate_overall_score(scores) == 100

# All 0s -> 0
scores = {f'SECTION_{i}': 0 for i in range(10)}
assert calculate_overall_score(scores) == 0

# Mixed scores
scores = {'S1': 9, 'S2': 8, 'S3': 7, 'S4': 6, 'S5': 10, 'S6': 9, 'S7': 8, 'S8': 7, 'S9': 6, 'S10': 10}
expected = 9+8+7+6+10+9+8+7+6+10
assert calculate_overall_score(scores) == expected

print('All tests PASSED')
"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "WORKER_059",
  "status": "COMPLETE",
  "duration_minutes": 15,
  "tests": {
    "all_tens": true,
    "all_zeros": true,
    "mixed_scores": true
  }
}
```

---

## 8. TASK_CLASSIFICATION

**Type:** MECHANICAL
**Complexity:** Low

---

## 9. RETROSPECTIVE

```python
{
  "worker_id": "WORKER_059",
  "task": "Score aggregator (combine 10 section scores)",
  "actual_duration_minutes": 0,
  "next_worker": "WORKER_060"
}
```

---

## 10. PERFORMANCE_REQUIREMENTS

**Target:** ≤20 minutes, <1ms execution time

---

## IMPLEMENTATION NOTES

```python
def calculate_overall_score(section_scores: Dict[str, int]) -> int:
    """
    Calculate overall quality score from section scores.

    Args:
        section_scores: Dict of section name -> score (0-10)

    Returns:
        Overall score 0-100 (sum of all section scores)
    """
    if len(section_scores) != 10:
        raise ValueError(f"Expected 10 sections, got {len(section_scores)}")

    for name, score in section_scores.items():
        if not 0 <= score <= 10:
            raise ValueError(f"Section {name} score {score} out of range 0-10")

    return sum(section_scores.values())
```

**Reference:** Implementation Plan Lines 676-678
