# WORKER_076: Section Score Weighting

**Worker ID:** WORKER_076
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_075 complete

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/content_quality_validator.py`
Add configurable section weights:

- **Constant:** `SECTION_WEIGHTS` dict with weight per section
- **Default:** All sections weight 1.0 (equal weighting, sum to 10)
- **Formula:** `weighted_score = sum(scores[s] * weights[s] for s in sections) / sum(weights.values()) * 10`
- **Customization:** Allow critical sections (DELIVERABLES, MITIGATION) to have higher weight

---

## 2. SUCCESS_CRITERIA

- ✅ `SECTION_WEIGHTS` constant defined (default: all 1.0)
- ✅ Weighted calculation function added
- ✅ Equal weights (all 1.0) → same as simple sum
- ✅ DELIVERABLES weight 2.0 → affects overall score
- ✅ Can adjust weights without code changes (configurable)
- ✅ Test: Equal weights = original formula
- ✅ Test: Custom weights change score correctly

---

## 3. BOUNDARIES

**CAN:** Add weighting system
**CANNOT:** Remove simple sum option (backward compatibility)

---

## 4. DEPENDENCIES

- ✅ WORKER_075 complete

---

## 5. MITIGATION

**Rollback:** `git checkout` file

---

## 6. TEST_PROCESS

```bash
python3 -c "
from wingman.validation.content_quality_validator import calculate_weighted_score

scores = {'S1': 8, 'S2': 8, 'S3': 8, 'S4': 8, 'S5': 8,
          'S6': 8, 'S7': 8, 'S8': 8, 'S9': 8, 'S10': 8}

# Equal weights -> 80
weights_equal = {s: 1.0 for s in scores.keys()}
assert calculate_weighted_score(scores, weights_equal) == 80

# Double weight on S1 -> different score
weights_custom = {s: 1.0 for s in scores.keys()}
weights_custom['S1'] = 2.0
result = calculate_weighted_score(scores, weights_custom)
assert result != 80  # Should be different with custom weights

print('Weighting tests PASSED')
"
```

---

## 7-10. [Standard sections]

**Type:** MECHANICAL

---

## IMPLEMENTATION NOTES

```python
# Default equal weights
SECTION_WEIGHTS = {
    "DELIVERABLES": 1.0,
    "SUCCESS_CRITERIA": 1.0,
    "BOUNDARIES": 1.0,
    "DEPENDENCIES": 1.0,
    "MITIGATION": 1.0,
    "TEST_PROCESS": 1.0,
    "TEST_RESULTS_FORMAT": 1.0,
    "RESOURCE_REQUIREMENTS": 1.0,
    "RISK_ASSESSMENT": 1.0,
    "QUALITY_METRICS": 1.0
}

def calculate_weighted_score(section_scores: Dict[str, int],
                             weights: Dict[str, float] = None) -> int:
    """Calculate weighted overall score."""
    if weights is None:
        weights = SECTION_WEIGHTS

    weighted_sum = sum(section_scores[s] * weights[s] for s in section_scores)
    weight_total = sum(weights.values())

    return int(weighted_sum / weight_total * 10)
```

**Reference:** Weighting logic for future customization
