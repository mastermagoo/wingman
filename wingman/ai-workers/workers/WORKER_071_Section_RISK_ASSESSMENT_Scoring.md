# WORKER_071: Section Scoring - RISK_ASSESSMENT (0-10)

**Worker ID:** WORKER_071
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_070 complete

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/content_quality_validator.py`
- **Criteria:**
  - 0-2: Just a word ("low") or missing
  - 3-5: Brief statement without justification
  - 6-8: Analysis but missing some factors
  - 9-10: Detailed reasoning with risk factors identified

---

## 2. SUCCESS_CRITERIA

- ✅ Test excellent: "Low risk - TEST environment, rollback automated, no data loss risk" → 9-10
- ✅ Test poor: "low" → 0-2

---

## 6. TEST_PROCESS

```bash
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
from wingman.validation.semantic_analyzer import SemanticAnalyzer

excellent = 'RISK_ASSESSMENT: Low risk - TEST environment only, automated rollback available, no production data affected, recovery time <2 min'
poor = 'RISK_ASSESSMENT: low'

validator = ContentQualityValidator(SemanticAnalyzer())
assert validator.analyze_section('RISK_ASSESSMENT', excellent)['score'] >= 8
assert validator.analyze_section('RISK_ASSESSMENT', poor)['score'] <= 2
print('RISK_ASSESSMENT scoring PASSED')
"
```

---

## IMPLEMENTATION NOTES

```python
"RISK_ASSESSMENT": """
RISK_ASSESSMENT Scoring Criteria (0-10):

0-2: POOR - Just a word ("low", "medium") or missing
3-5: FAIR - Brief statement without justification
6-8: GOOD - Analysis but missing some factors
9-10: EXCELLENT - Detailed reasoning with risk factors identified

Examples:
- "low" → 1
- "Low risk deployment" → 4
- "Low risk - TEST environment only" → 7
- "Low risk - TEST environment, automated rollback, no data loss risk, recovery <2 min" → 9
"""
```
