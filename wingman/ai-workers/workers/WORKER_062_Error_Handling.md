# WORKER_062: Content Quality Validator - Error Handling

**Worker ID:** WORKER_062
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_061 complete

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/content_quality_validator.py`
- **Update:** `analyze_section()` method with try/except blocks
- **Error Handling:**
  - LLM failures → fallback to heuristic
  - Missing sections → score 0
  - Invalid input → raise ValueError with clear message
  - Timeout → fallback to heuristic
- **Logging:** Log errors but don't crash

---

## 2. SUCCESS_CRITERIA

- ✅ `analyze_section()` wraps `_score_with_llm()` in try/except
- ✅ On LLM exception → calls `_score_heuristic()` automatically
- ✅ Empty section → returns score 0
- ✅ Invalid section_name → raises ValueError
- ✅ No uncaught exceptions during normal operation
- ✅ Test with LLM failure simulation

---

## 3. BOUNDARIES

**CAN:** Add error handling to `analyze_section()`
**CANNOT:** Modify scoring logic
**Scope:** Error handling only

---

## 4. DEPENDENCIES

- ✅ WORKER_061 complete (heuristic fallback exists)

---

## 5. MITIGATION

**Rollback:** `git checkout wingman/validation/content_quality_validator.py`
**Recovery Time:** <2 minutes

---

## 6. TEST_PROCESS

```bash
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator

class MockAnalyzer:
    def analyze(self, prompt, model='qwen2.5-coder:7b'):
        raise Exception('LLM unavailable')

validator = ContentQualityValidator(MockAnalyzer())
result = validator.analyze_section('DELIVERABLES', 'Deploy API')
assert 'score' in result, 'Should return score even on LLM failure'
assert result.get('method') == 'heuristic', 'Should use fallback'
print('Error handling test PASSED')
"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "WORKER_062",
  "status": "COMPLETE",
  "duration_minutes": 18,
  "tests": {
    "llm_failure_handled": true,
    "fallback_triggered": true,
    "no_crashes": true
  }
}
```

---

## 8. TASK_CLASSIFICATION

**Type:** MECHANICAL
**Complexity:** Medium

---

## 9. RETROSPECTIVE

```python
{
  "worker_id": "WORKER_062",
  "task": "Error handling (missing sections, LLM errors)",
  "next_worker": "WORKER_063"
}
```

---

## 10. PERFORMANCE_REQUIREMENTS

**Target:** ≤20 minutes, graceful degradation on errors

---

## IMPLEMENTATION NOTES

```python
def analyze_section(self, section_name: str, section_content: str) -> Dict[str, Any]:
    """
    Analyze quality of a single section with error handling.
    """
    # Validate input
    if section_name not in REQUIRED_SECTIONS:
        raise ValueError(f"Invalid section name: {section_name}")

    # Handle empty sections
    if not section_content or len(section_content.strip()) < 10:
        return {
            "score": 0,
            "reasoning": "Section empty or too short",
            "section_name": section_name,
            "method": "validation"
        }

    # Try LLM scoring first
    try:
        result = self._score_with_llm(section_name, section_content)
        result["section_name"] = section_name
        result["method"] = "llm"
        return result
    except Exception as e:
        # Fallback to heuristic
        result = self._score_heuristic(section_name, section_content)
        result["section_name"] = section_name
        result["llm_error"] = str(e)
        return result
```

**Reference:** Implementation Plan error handling patterns
