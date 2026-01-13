# WORKER_069: Section Scoring - TEST_RESULTS_FORMAT (0-10)

**Worker ID:** WORKER_069
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_068 complete

---

## 1. DELIVERABLES

- **Criteria:**
  - 0-2: Missing or "show results"
  - 3-5: Generic format description
  - 6-8: Structure defined but incomplete
  - 9-10: Exact JSON schema with all required fields

---

## 2. SUCCESS_CRITERIA

- ✅ Test excellent: "JSON {passed: N, failed: N, coverage: X%}" → 9-10
- ✅ Test poor: "show results" → 0-2

---

## 6. TEST_PROCESS

```bash
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
from wingman.validation.semantic_analyzer import SemanticAnalyzer

excellent = 'TEST_RESULTS_FORMAT: JSON {passed: N, failed: N, coverage: X%, duration_sec: N}'
poor = 'TEST_RESULTS_FORMAT: show results'

validator = ContentQualityValidator(SemanticAnalyzer())
assert validator.analyze_section('TEST_RESULTS_FORMAT', excellent)['score'] >= 8
assert validator.analyze_section('TEST_RESULTS_FORMAT', poor)['score'] <= 2
print('TEST_RESULTS_FORMAT scoring PASSED')
"
```

---

## IMPLEMENTATION NOTES

```python
"TEST_RESULTS_FORMAT": """
TEST_RESULTS_FORMAT Scoring Criteria (0-10):

0-2: POOR - Missing or "show results"
3-5: FAIR - Generic format description
6-8: GOOD - Structure defined but incomplete
9-10: EXCELLENT - Exact JSON/structured format with all fields

Examples:
- "show results" → 1
- "JSON format" → 4
- "JSON with passed/failed counts" → 7
- "JSON {passed: N, failed: N, coverage: X%, duration_sec: N}" → 9
"""
```
