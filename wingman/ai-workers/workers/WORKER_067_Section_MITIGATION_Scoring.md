# WORKER_067: Section Scoring - MITIGATION (0-10)

**Worker ID:** WORKER_067
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_066 complete

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/content_quality_validator.py`
- **Criteria:**
  - 0-2: "None" or missing
  - 3-5: Generic ("rollback if needed")
  - 6-8: Specific steps but incomplete
  - 9-10: Detailed plan with exact commands and fallback

---

## 2. SUCCESS_CRITERIA

- ✅ Test excellent: "Rollback: docker tag api:previous && restart (< 2 min), triggers: health fail 3x" → 9-10
- ✅ Test poor: "None" → 0-2

---

## 6. TEST_PROCESS

```bash
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
from wingman.validation.semantic_analyzer import SemanticAnalyzer

excellent = 'MITIGATION: Rollback: docker tag api:previous && restart (< 2 min), triggers: health fail 3x, backup available'
poor = 'MITIGATION: None'

validator = ContentQualityValidator(SemanticAnalyzer())
assert validator.analyze_section('MITIGATION', excellent)['score'] >= 8
assert validator.analyze_section('MITIGATION', poor)['score'] <= 2
print('MITIGATION scoring PASSED')
"
```

---

## IMPLEMENTATION NOTES

```python
"MITIGATION": """
MITIGATION Scoring Criteria (0-10):

0-2: POOR - "None" or missing
3-5: FAIR - Generic ("rollback if needed")
6-8: GOOD - Specific steps but incomplete
9-10: EXCELLENT - Detailed plan with exact commands, triggers, time estimates

Examples:
- "None" → 0
- "Rollback if needed" → 3
- "Rollback: docker restart" → 6
- "Rollback: docker tag api:previous && restart (< 2 min), triggers: health fail 3x" → 9
"""
```
