# WORKER_068: Section Scoring - TEST_PROCESS (0-10)

**Worker ID:** WORKER_068
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_067 complete

---

## 1. DELIVERABLES

- **Criteria:**
  - 0-2: Missing or "test it"
  - 3-5: Generic ("run tests")
  - 6-8: Specific commands but no coverage requirements
  - 9-10: Exact pytest commands, coverage thresholds, multiple test types

---

## 2. SUCCESS_CRITERIA

- ✅ Test excellent: "pytest -v (350 tests), load test k6, security scan bandit" → 9-10
- ✅ Test poor: "test it" → 0-2

---

## 6. TEST_PROCESS

```bash
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
from wingman.validation.semantic_analyzer import SemanticAnalyzer

excellent = 'TEST_PROCESS: pytest -v tests/ (350 tests), load test with k6, security scan with bandit, coverage >90%'
poor = 'TEST_PROCESS: test it'

validator = ContentQualityValidator(SemanticAnalyzer())
assert validator.analyze_section('TEST_PROCESS', excellent)['score'] >= 8
assert validator.analyze_section('TEST_PROCESS', poor)['score'] <= 2
print('TEST_PROCESS scoring PASSED')
"
```

---

## IMPLEMENTATION NOTES

```python
"TEST_PROCESS": """
TEST_PROCESS Scoring Criteria (0-10):

0-2: POOR - Missing or "test it"
3-5: FAIR - Generic ("run tests")
6-8: GOOD - Specific commands but no coverage
9-10: EXCELLENT - Exact commands, coverage thresholds, multiple test types

Examples:
- "test it" → 1
- "run tests" → 3
- "pytest tests/" → 6
- "pytest -v tests/ (350 tests), load test k6, coverage >90%" → 9
"""
```
