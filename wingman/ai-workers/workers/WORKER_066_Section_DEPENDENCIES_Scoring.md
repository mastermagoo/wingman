# WORKER_066: Section Scoring - DEPENDENCIES (0-10)

**Worker ID:** WORKER_066
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_065 complete

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/content_quality_validator.py`
- **Criteria:**
  - 0-2: Missing or "None"
  - 3-5: Lists dependencies but no versions
  - 6-8: Versions specified but not verified
  - 9-10: Specific versions, verification status included

---

## 2. SUCCESS_CRITERIA

- ✅ Test excellent: "Database v1.2+ (confirmed), Redis 6.2+ (confirmed)" → 9-10
- ✅ Test poor: "None" → 0-2

---

## 3-5. [Standard sections]

---

## 6. TEST_PROCESS

```bash
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
from wingman.validation.semantic_analyzer import SemanticAnalyzer

excellent = 'DEPENDENCIES: Database v1.2+ (confirmed), Redis 6.2+ (confirmed), Python 3.8+'
poor = 'DEPENDENCIES: None'

validator = ContentQualityValidator(SemanticAnalyzer())
assert validator.analyze_section('DEPENDENCIES', excellent)['score'] >= 8
assert validator.analyze_section('DEPENDENCIES', poor)['score'] <= 2
print('DEPENDENCIES scoring PASSED')
"
```

---

## 7-10. [Standard sections]

**Type:** MECHANICAL
**Target:** ≤20 minutes

---

## IMPLEMENTATION NOTES

```python
"DEPENDENCIES": """
DEPENDENCIES Scoring Criteria (0-10):

0-2: POOR - Missing or "None"
3-5: FAIR - Lists dependencies but no versions
6-8: GOOD - Versions specified but not verified
9-10: EXCELLENT - Specific versions with verification status

Examples:
- "None" → 0
- "Database, Redis" → 4
- "Database v1.2+, Redis 6.2+" → 7
- "Database v1.2+ (confirmed), Redis 6.2+ (confirmed)" → 9
"""
```
