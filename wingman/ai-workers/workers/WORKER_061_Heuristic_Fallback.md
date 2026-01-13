# WORKER_061: Content Quality Validator - Heuristic Fallback

**Worker ID:** WORKER_061
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_060 complete

---

## 1. DELIVERABLES

- **Function:** `_score_heuristic(section_name: str, section_content: str) -> Dict[str, Any]`
- **Purpose:** Rule-based scoring when LLM unavailable
- **Logic:**
  - Empty/short (<10 chars) → score 0
  - Placeholder (TBD, TODO) → score 0-2
  - Vague (generic words, no specifics) → score 3-5
  - Specific content → score 6-8
- **Return:** `{"score": 0-10, "reasoning": str, "method": "heuristic"}`

---

## 2. SUCCESS_CRITERIA

- ✅ Function returns scores without calling LLM
- ✅ Empty content → score 0
- ✅ Placeholder → score ≤2
- ✅ Specific content (version numbers, metrics) → score ≥6
- ✅ Test with 10+ examples (5 poor, 5 good)
- ✅ Consistent with validation logic (WORKER_058)

---

## 3. BOUNDARIES

**CAN:** Add heuristic scoring function
**CANNOT:** Call LLM, modify existing functions
**Scope:** Fallback scoring only

---

## 4. DEPENDENCIES

- ✅ WORKER_060 complete

---

## 5. MITIGATION

**Rollback:** `git checkout wingman/validation/content_quality_validator.py`
**Recovery Time:** <2 minutes

---

## 6. TEST_PROCESS

```bash
python3 -c "
from wingman.validation.content_quality_validator import _score_heuristic

# Empty -> 0
result = _score_heuristic('TEST', '')
assert result['score'] == 0

# Placeholder -> low score
result = _score_heuristic('TEST', 'TBD')
assert result['score'] <= 2

# Specific -> higher score
result = _score_heuristic('DELIVERABLES', 'Deploy API v2.1.0 to production')
assert result['score'] >= 6

print('Heuristic tests PASSED')
"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "WORKER_061",
  "status": "COMPLETE",
  "duration_minutes": 19,
  "tests": {
    "empty_content": true,
    "placeholder_detection": true,
    "specific_content": true
  }
}
```

---

## 8. TASK_CLASSIFICATION

**Type:** MECHANICAL
**Complexity:** Medium (heuristic rules)

---

## 9. RETROSPECTIVE

```python
{
  "worker_id": "WORKER_061",
  "task": "Heuristic fallback (when LLM fails)",
  "next_worker": "WORKER_062"
}
```

---

## 10. PERFORMANCE_REQUIREMENTS

**Target:** ≤20 minutes, <1ms execution

---

## IMPLEMENTATION NOTES

```python
def _score_heuristic(section_name: str, section_content: str) -> Dict[str, Any]:
    """
    Rule-based section scoring (fallback when LLM unavailable).
    """
    content = section_content.strip()

    # Empty/very short
    if len(content) < 10:
        return {"score": 0, "reasoning": "Section empty or too short", "method": "heuristic"}

    # Placeholder detection
    useless_phrases = ["tbd", "todo", "n/a", "none", "do it", "make it work"]
    if any(phrase in content.lower() for phrase in useless_phrases):
        return {"score": 1, "reasoning": "Placeholder text detected", "method": "heuristic"}

    # Check for specificity indicators
    specific_indicators = [
        r'v?\d+\.\d+',  # Version numbers
        r'\d+\s*(cpu|gb|mb|min|hour)',  # Resource numbers
        r'<|>|≤|≥',  # Comparison operators
        r'\d+%'  # Percentages
    ]

    import re
    specificity_count = sum(1 for pattern in specific_indicators if re.search(pattern, content.lower()))

    if specificity_count >= 2:
        return {"score": 7, "reasoning": "Specific measurable content", "method": "heuristic"}
    elif specificity_count == 1:
        return {"score": 5, "reasoning": "Some specificity", "method": "heuristic"}
    else:
        return {"score": 3, "reasoning": "Generic content, lacks specificity", "method": "heuristic"}
```

**Reference:** Implementation Plan Lines 781-790
