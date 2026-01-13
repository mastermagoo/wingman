# WORKER_064: Section Scoring - SUCCESS_CRITERIA (0-10)

**Worker ID:** WORKER_064
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_063 complete

---

## 1. DELIVERABLES

Create LLM prompt for scoring SUCCESS_CRITERIA section:

- **Criteria:**
  - 0-2: Not measurable ("it works") or missing
  - 3-5: Some criteria but vague
  - 6-8: Measurable but missing edge cases
  - 9-10: Clear pass/fail conditions, all scenarios covered

---

## 2. SUCCESS_CRITERIA

- ✅ SUCCESS_CRITERIA scoring criteria added to prompt
- ✅ Test excellent: "All health checks return 200 for 5 consecutive checks" → 9-10
- ✅ Test poor: "Make it work" → 0-2
- ✅ Consistent scoring (±1 point variance)

---

## 3. BOUNDARIES

**Scope:** SUCCESS_CRITERIA section only

---

## 4. DEPENDENCIES

- ✅ WORKER_063 complete

---

## 5. MITIGATION

**Rollback:** `git checkout` file
**Recovery:** <2 minutes

---

## 6. TEST_PROCESS

```bash
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
from wingman.validation.semantic_analyzer import SemanticAnalyzer

excellent = 'SUCCESS_CRITERIA: All health checks return HTTP 200 for 5 consecutive checks, zero errors in logs for 10 minutes, API latency p99 < 200ms'
poor = 'SUCCESS_CRITERIA: Make it work'

validator = ContentQualityValidator(SemanticAnalyzer())
result_good = validator.analyze_section('SUCCESS_CRITERIA', excellent)
result_poor = validator.analyze_section('SUCCESS_CRITERIA', poor)

assert result_good['score'] >= 8
assert result_poor['score'] <= 3
print('SUCCESS_CRITERIA scoring PASSED')
"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "WORKER_064",
  "status": "COMPLETE",
  "tests": {"excellent": true, "poor": true}
}
```

---

## 8. TASK_CLASSIFICATION

**Type:** MECHANICAL

---

## 9. RETROSPECTIVE

```python
{"worker_id": "WORKER_064", "next_worker": "WORKER_065"}
```

---

## 10. PERFORMANCE_REQUIREMENTS

**Target:** ≤20 minutes

---

## IMPLEMENTATION NOTES

```python
"SUCCESS_CRITERIA": """
SUCCESS_CRITERIA Scoring Criteria (0-10):

0-2: POOR - Not measurable ("it works", "looks good") or missing
3-5: FAIR - Some criteria but vague or incomplete
6-8: GOOD - Measurable criteria but missing edge cases
9-10: EXCELLENT - Clear pass/fail conditions, covers all scenarios, specific metrics

Examples:
- "Make it work" → 1
- "Tests pass" → 4
- "All health checks return 200" → 7
- "All health checks return 200 for 5 consecutive checks, zero errors in logs for 10 minutes" → 9
"""
```

**Reference:** Implementation Plan Lines 754-758
