# WORKER_058: Content Quality Validator - Section Validation

**Worker ID:** WORKER_058
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_057 complete (section extractor exists)

---

## 1. DELIVERABLES

Create function to validate section presence and quality:

- **Function:** `validate_section(section_name: str, section_content: str) -> bool`
- **Purpose:** Check if section is present, not empty, not placeholder
- **Logic:** Return False if empty, "TBD", "TODO", "N/A", "None", or <10 characters
- **Location:** Add to `content_quality_validator.py`
- **Use Case:** Pre-filter before LLM scoring

**Output:** Validation function that detects useless/missing sections

---

## 2. SUCCESS_CRITERIA

- ✅ Function `validate_section()` created with correct signature
- ✅ Returns `False` for empty strings: `validate_section("TEST", "") == False`
- ✅ Returns `False` for placeholder text: "TBD", "TODO", "N/A", "None"
- ✅ Returns `False` for very short content: `<10 characters`
- ✅ Returns `True` for valid content: meaningful text ≥10 characters
- ✅ Case-insensitive placeholder detection: "tbd", "TBD", "Tbd" all detected
- ✅ Function is pure (no side effects)
- ✅ Test with 5+ valid and 5+ invalid inputs

---

## 3. BOUNDARIES

**CAN modify:**
- `wingman/validation/content_quality_validator.py` - add validation function
- Adjust placeholder list (add more useless phrases)
- Adjust minimum character threshold (currently 10)

**CANNOT modify:**
- Existing functions (parse_10_point_sections, analyze_section)
- Scoring logic (not yet implemented)
- Any other files

**Scope:** Boolean validation only - no scoring

---

## 4. DEPENDENCIES

**Required (must exist):**
- ✅ WORKER_057 complete: `parse_10_point_sections()` exists
- ✅ File exists: `wingman/validation/content_quality_validator.py`

**Optional:**
- None

**Verification:**
```bash
python3 -c "from wingman.validation.content_quality_validator import parse_10_point_sections; print('Parser exists')"
```

---

## 5. MITIGATION

**Rollback Plan:**
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman
git checkout wingman/validation/content_quality_validator.py
```

**Triggers for rollback:**
- Function crashes on valid input
- Boolean logic incorrect
- Takes >20 minutes

**Escalation:**
- If logic unclear: Reference implementation plan lines 782-790
- If blocked >30 minutes: Escalate to user

**Recovery Time:** <2 minutes

---

## 6. TEST_PROCESS

**Manual Testing:**
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

# Test validation function
python3 -c "
from wingman.validation.content_quality_validator import validate_section

# Test 1: Empty string -> False
assert validate_section('TEST', '') == False, 'Empty should be invalid'

# Test 2: Placeholder -> False
assert validate_section('TEST', 'TBD') == False, 'TBD should be invalid'
assert validate_section('TEST', 'TODO') == False, 'TODO should be invalid'
assert validate_section('TEST', 'N/A') == False, 'N/A should be invalid'
assert validate_section('TEST', 'none') == False, 'none should be invalid'

# Test 3: Too short -> False
assert validate_section('TEST', 'test') == False, 'Short text should be invalid'

# Test 4: Valid content -> True
assert validate_section('DELIVERABLES', 'Deploy API v2.1.0 to production') == True
assert validate_section('SUCCESS_CRITERIA', 'Health checks return 200 for 5 minutes') == True

print('All validation tests PASSED')
"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "WORKER_058",
  "status": "COMPLETE",
  "duration_minutes": 17,
  "tests": {
    "empty_string": true,
    "placeholder_detection": true,
    "short_text": true,
    "valid_content": true
  },
  "deliverable": {
    "function": "validate_section",
    "placeholders_detected": ["TBD", "TODO", "N/A", "None"],
    "min_length": 10
  },
  "issues": []
}
```

---

## 8. TASK_CLASSIFICATION

**Type:** MECHANICAL

**Justification:** Simple boolean logic, clear validation rules

**Complexity:** Low
**Creativity Required:** Minimal

---

## 9. RETROSPECTIVE

```python
{
  "worker_id": "WORKER_058",
  "phase": "Phase 2 - Content Quality Validator",
  "task": "Section validation (check if section present)",
  "actual_duration_minutes": 0,
  "planned_duration_minutes": 20,
  "status": "COMPLETE",
  "lessons_learned": [
    "Simple validation catches most useless sections",
    "Placeholder detection prevents wasted LLM calls"
  ],
  "next_worker": "WORKER_059"
}
```

---

## 10. PERFORMANCE_REQUIREMENTS

**Target:** ≤20 minutes, 100% accuracy on test cases

**Monitoring:** Validation speed <1ms per call

---

## IMPLEMENTATION NOTES

```python
def validate_section(section_name: str, section_content: str) -> bool:
    """
    Validate section is present and not placeholder.

    Returns False if section is:
    - Empty or whitespace only
    - Placeholder text (TBD, TODO, N/A, None)
    - Too short (<10 characters)
    """
    if not section_content or len(section_content.strip()) < 10:
        return False

    useless_phrases = ["tbd", "todo", "n/a", "none", "do it", "make it work"]
    content_lower = section_content.lower().strip()

    if any(phrase in content_lower for phrase in useless_phrases):
        return False

    return True
```

**Reference:** Implementation Plan Lines 782-790
