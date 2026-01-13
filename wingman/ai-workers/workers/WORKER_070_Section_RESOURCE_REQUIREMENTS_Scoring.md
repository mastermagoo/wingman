# WORKER_070: Section Scoring - RESOURCE_REQUIREMENTS (0-10)

**Worker ID:** WORKER_070
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_069 complete

---

## 1. DELIVERABLES

- **Criteria:**
  - 0-2: Missing or "normal"
  - 3-5: Vague ("some CPU")
  - 6-8: Specific but missing time estimate
  - 9-10: CPU, RAM, disk, time all specified with units

---

## 2. SUCCESS_CRITERIA

- ✅ Test excellent: "4 CPU, 8GB RAM, 20GB disk, 2 hours" → 9-10
- ✅ Test poor: "normal" → 0-2

---

## 6. TEST_PROCESS

```bash
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
from wingman.validation.semantic_analyzer import SemanticAnalyzer

excellent = 'RESOURCE_REQUIREMENTS: 4 CPU, 8GB RAM, 20GB disk, 2 hours execution time'
poor = 'RESOURCE_REQUIREMENTS: normal'

validator = ContentQualityValidator(SemanticAnalyzer())
assert validator.analyze_section('RESOURCE_REQUIREMENTS', excellent)['score'] >= 8
assert validator.analyze_section('RESOURCE_REQUIREMENTS', poor)['score'] <= 2
print('RESOURCE_REQUIREMENTS scoring PASSED')
"
```

---

## IMPLEMENTATION NOTES

```python
"RESOURCE_REQUIREMENTS": """
RESOURCE_REQUIREMENTS Scoring Criteria (0-10):

0-2: POOR - Missing or "normal"
3-5: FAIR - Vague ("some CPU", "enough RAM")
6-8: GOOD - Specific but missing time estimate
9-10: EXCELLENT - CPU, RAM, disk, time all specified with units

Examples:
- "normal" → 1
- "some CPU" → 3
- "4 CPU, 8GB RAM" → 7
- "4 CPU, 8GB RAM, 20GB disk, 2 hours" → 9
"""
```
