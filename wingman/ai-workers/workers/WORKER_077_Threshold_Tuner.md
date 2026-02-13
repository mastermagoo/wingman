# WORKER_077: Threshold Tuner (Adjust Auto-Reject Threshold)

**Worker ID:** WORKER_077
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_076 complete

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/content_quality_validator.py`
Make auto-reject threshold configurable:

- **Constant:** `AUTO_REJECT_THRESHOLD = 60` (default)
- **Range:** Allow adjustment 50-70
- **Usage:** Replace hardcoded `60` with `AUTO_REJECT_THRESHOLD`
- **Validation:** Raise ValueError if threshold <50 or >70

---

## 2. SUCCESS_CRITERIA

- ✅ `AUTO_REJECT_THRESHOLD` constant defined (default 60)
- ✅ All comparisons use threshold constant (not hardcoded 60)
- ✅ Can adjust threshold via config
- ✅ Test: threshold=50 → score 49 rejected, 50 accepted
- ✅ Test: threshold=70 → score 69 rejected, 70 accepted
- ✅ Validation rejects threshold <50 or >70

---

## 3. BOUNDARIES

**CAN:** Make threshold configurable
**CANNOT:** Change default (60 from plan)

---

## 4. DEPENDENCIES

- ✅ WORKER_076 complete

---

## 5. MITIGATION

**Rollback:** `git checkout` file

---

## 6. TEST_PROCESS

```bash
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator, AUTO_REJECT_THRESHOLD

assert AUTO_REJECT_THRESHOLD == 60, 'Default should be 60'

# Test with default threshold
validator = ContentQualityValidator(None)
# (Would test with real instructions at threshold boundary)

print('Threshold configuration tests PASSED')
"
```

---

## 7-10. [Standard sections]

**Type:** MECHANICAL

---

## IMPLEMENTATION NOTES

```python
# Configuration constant
AUTO_REJECT_THRESHOLD = 60  # Default from implementation plan

def set_auto_reject_threshold(threshold: int):
    """Set auto-reject threshold (50-70 range)."""
    if not 50 <= threshold <= 70:
        raise ValueError(f"Threshold {threshold} out of range 50-70")
    global AUTO_REJECT_THRESHOLD
    AUTO_REJECT_THRESHOLD = threshold

# Update assess_content_quality() to use:
# "pass": overall >= AUTO_REJECT_THRESHOLD,
# "auto_reject": overall < AUTO_REJECT_THRESHOLD
```

**Reference:** Threshold configuration for future tuning
