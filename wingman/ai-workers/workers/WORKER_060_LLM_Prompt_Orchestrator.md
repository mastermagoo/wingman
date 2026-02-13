# WORKER_060: Content Quality Validator - LLM Prompt Orchestrator

**Worker ID:** WORKER_060
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_059 complete, semantic_analyzer available

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/content_quality_validator.py`
- **Method:** `_score_with_llm(section_name: str, section_content: str) -> Dict[str, Any]`
- **Purpose:** Use semantic_analyzer to score section via LLM
- **Location:** Private method in `ContentQualityValidator` class
- **Return:** `{"score": 0-10, "reasoning": str}` or raises exception if LLM fails

---

## 2. SUCCESS_CRITERIA

- ✅ Method calls `self.semantic_analyzer.analyze()` with scoring prompt
- ✅ Constructs prompt with section name and content
- ✅ Parses LLM response JSON: `{"score": int, "reasoning": str}`
- ✅ Validates score is 0-10
- ✅ Raises exception on LLM failure (for fallback handling)
- ✅ Test with mock semantic_analyzer

---

## 3. BOUNDARIES

**CAN:** Add `_score_with_llm()` private method
**CANNOT:** Modify semantic_analyzer, change prompt structure (defined in WORKER_063-072)
**Scope:** LLM orchestration only

---

## 4. DEPENDENCIES

- ✅ WORKER_059 complete
- ✅ Phase 1: semantic_analyzer.py exists and functional

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
        return '{\"score\": 8, \"reasoning\": \"Good quality\"}'

validator = ContentQualityValidator(MockAnalyzer())
result = validator._score_with_llm('DELIVERABLES', 'Deploy API v2.1.0')
assert result['score'] == 8
assert 'reasoning' in result
print('LLM orchestrator test PASSED')
"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "WORKER_060",
  "status": "COMPLETE",
  "duration_minutes": 18,
  "tests": {
    "calls_semantic_analyzer": true,
    "parses_json_response": true,
    "validates_score_range": true
  }
}
```

---

## 8. TASK_CLASSIFICATION

**Type:** MECHANICAL
**Complexity:** Medium (JSON parsing, error handling)

---

## 9. RETROSPECTIVE

```python
{
  "worker_id": "WORKER_060",
  "task": "LLM prompt orchestrator",
  "next_worker": "WORKER_061"
}
```

---

## 10. PERFORMANCE_REQUIREMENTS

**Target:** ≤20 minutes, LLM call <5s typical

---

## IMPLEMENTATION NOTES

```python
import json

def _score_with_llm(self, section_name: str, section_content: str) -> Dict[str, Any]:
    """
    Score section using LLM via semantic_analyzer.

    Raises exception if LLM fails (for fallback handling).
    """
    prompt = f"""Score this {section_name} section (0-10):

CONTENT:
{section_content}

Return JSON: {{"score": 0-10, "reasoning": "explanation"}}
"""

    response = self.semantic_analyzer.analyze(prompt, model='qwen2.5-coder:7b')

    # Parse JSON response
    result = json.loads(response)

    score = result.get('score')
    if not isinstance(score, int) or not 0 <= score <= 10:
        raise ValueError(f"Invalid score: {score}")

    return {
        "score": score,
        "reasoning": result.get('reasoning', 'No reasoning provided')
    }
```

**Reference:** Implementation Plan Lines 729-779
