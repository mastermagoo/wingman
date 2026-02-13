# WORKER_063: Section Scoring - DELIVERABLES (0-10)

**Worker ID:** WORKER_063
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_062 complete (error handling in place)

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/content_quality_validator.py`
Create LLM prompt for scoring DELIVERABLES section:

- **Prompt Template:** Scoring criteria for DELIVERABLES (0-10 scale)
- **Integration:** Add to `_score_with_llm()` method's prompt construction
- **Criteria:**
  - 0-2: Vague ("do it", "make it work") or missing
  - 3-5: General description but not specific/measurable
  - 6-8: Specific but missing some details
  - 9-10: Precise, measurable, clear acceptance criteria

---

## 2. SUCCESS_CRITERIA

- ✅ Prompt template for DELIVERABLES section created
- ✅ Scoring criteria 0-10 clearly defined in prompt
- ✅ Test with excellent DELIVERABLES → score 9-10
- ✅ Test with poor DELIVERABLES → score 0-2
- ✅ Test with medium DELIVERABLES → score 4-6
- ✅ LLM returns consistent scores (±1 point on repeated calls)
- ✅ Reasoning explains score

---

## 3. BOUNDARIES

**CAN:** Add DELIVERABLES scoring prompt, update `_score_with_llm()` to include section-specific criteria
**CANNOT:** Modify other sections' scoring, change overall structure
**Scope:** DELIVERABLES section only

---

## 4. DEPENDENCIES

- ✅ WORKER_062 complete: error handling in place
- ✅ `_score_with_llm()` method exists

---

## 5. MITIGATION

**Rollback:** `git checkout wingman/validation/content_quality_validator.py`
**Recovery Time:** <2 minutes

---

## 6. TEST_PROCESS

```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
from wingman.validation.semantic_analyzer import SemanticAnalyzer

# Test excellent DELIVERABLES
excellent = '''
DELIVERABLES:
- Deploy API v2.1.0 to production
- Update documentation to reflect new /v2/users endpoint
- Complete deployment within 2-hour maintenance window
- Zero downtime using blue-green deployment
'''

analyzer = SemanticAnalyzer()
validator = ContentQualityValidator(analyzer)
result = validator.analyze_section('DELIVERABLES', excellent)
print(f'Excellent DELIVERABLES score: {result[\"score\"]}')
assert result['score'] >= 8, f'Expected ≥8, got {result[\"score\"]}'

# Test poor DELIVERABLES
poor = 'DELIVERABLES: TBD'
result = validator.analyze_section('DELIVERABLES', poor)
print(f'Poor DELIVERABLES score: {result[\"score\"]}')
assert result['score'] <= 3, f'Expected ≤3, got {result[\"score\"]}'

print('DELIVERABLES scoring tests PASSED')
"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "WORKER_063",
  "status": "COMPLETE",
  "duration_minutes": 19,
  "tests": {
    "excellent_deliverables": true,
    "poor_deliverables": true,
    "llm_consistency": true
  },
  "scoring": {
    "excellent_score": 9,
    "poor_score": 1,
    "medium_score": 5
  }
}
```

---

## 8. TASK_CLASSIFICATION

**Type:** MECHANICAL
**Complexity:** Medium (LLM prompt engineering)

---

## 9. RETROSPECTIVE

```python
{
  "worker_id": "WORKER_063",
  "task": "Section 1 - DELIVERABLES scoring (0-10)",
  "next_worker": "WORKER_064",
  "lessons_learned": [
    "Clear scoring criteria improve LLM consistency",
    "Examples in prompt help calibrate scores"
  ]
}
```

---

## 10. PERFORMANCE_REQUIREMENTS

**Target:** ≤20 minutes, LLM response <5s

---

## IMPLEMENTATION NOTES

**Prompt Template (add to `_score_with_llm()`):**

```python
SECTION_CRITERIA = {
    "DELIVERABLES": """
DELIVERABLES Scoring Criteria (0-10):

0-2: POOR
- Vague or missing ("do it", "make it work", "TBD")
- No specific outputs defined
- Cannot determine what will be delivered

3-5: FAIR
- General description but not specific
- Missing measurable outcomes
- Ambiguous scope

6-8: GOOD
- Specific deliverables listed
- Measurable but missing some details
- Clear outputs but incomplete acceptance criteria

9-10: EXCELLENT
- Precise, measurable deliverables
- Clear acceptance criteria for each item
- Version numbers, specific files, or concrete outputs
- Time-bound when relevant
- Unambiguous scope

Examples:
- "Deploy API" → 4 (too vague)
- "Deploy API v2.1.0 to production" → 7 (specific but could be more detailed)
- "Deploy API v2.1.0 to production using blue-green deployment, update docs, complete in 2-hour window" → 9 (excellent)
"""
}

def _score_with_llm(self, section_name: str, section_content: str) -> Dict[str, Any]:
    criteria = SECTION_CRITERIA.get(section_name, "")

    prompt = f"""You are assessing the quality of a {section_name} section in an automation request.

{criteria}

SECTION CONTENT:
{section_content}

Score this section from 0-10 based on the criteria above.

Return ONLY a JSON object:
{{
  "score": 0-10,
  "reasoning": "1-2 sentences explaining the score based on criteria"
}}
"""

    # ... rest of LLM call logic ...
```

**Reference:** Implementation Plan Lines 738-779
