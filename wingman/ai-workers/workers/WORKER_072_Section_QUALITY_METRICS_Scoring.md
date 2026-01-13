# WORKER_072: Section Scoring - QUALITY_METRICS (0-10)

**Worker ID:** WORKER_072
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_071 complete

---

## 1. DELIVERABLES

- **Criteria:**
  - 0-2: Missing or "good quality"
  - 3-5: Generic metrics ("fast", "reliable")
  - 6-8: Some numbers but incomplete
  - 9-10: Specific measurable thresholds (error %, latency, coverage)

---

## 2. SUCCESS_CRITERIA

- ✅ Test excellent: "Error <0.1%, latency <200ms, coverage >90%" → 9-10
- ✅ Test poor: "good quality" → 0-2

---

## 6. TEST_PROCESS

```bash
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
from wingman.validation.semantic_analyzer import SemanticAnalyzer

excellent = 'QUALITY_METRICS: Error rate <0.1%, p99 latency <200ms, test coverage >90%, uptime >99.9%'
poor = 'QUALITY_METRICS: good quality'

validator = ContentQualityValidator(SemanticAnalyzer())
assert validator.analyze_section('QUALITY_METRICS', excellent)['score'] >= 8
assert validator.analyze_section('QUALITY_METRICS', poor)['score'] <= 2
print('QUALITY_METRICS scoring PASSED')
"
```

---

## IMPLEMENTATION NOTES

```python
"QUALITY_METRICS": """
QUALITY_METRICS Scoring Criteria (0-10):

0-2: POOR - Missing or "good quality"
3-5: FAIR - Generic metrics ("fast", "reliable")
6-8: GOOD - Some numbers but incomplete
9-10: EXCELLENT - Specific measurable thresholds with units

Examples:
- "good quality" → 1
- "fast and reliable" → 3
- "Error rate <0.1%" → 6
- "Error <0.1%, latency <200ms, coverage >90%" → 9
"""
```

**Reference:** Implementation Plan Lines 738-779
