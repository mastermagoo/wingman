# WORKER_065: Section Scoring - BOUNDARIES (0-10)

**Worker ID:** WORKER_065
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_064 complete

---

## 1. DELIVERABLES

- **Criteria:**
  - 0-2: Missing or "None"
  - 3-5: Generic ("be careful")
  - 6-8: Specific constraints but incomplete
  - 9-10: Clear CAN/CANNOT lists, protects critical systems

---

## 2. SUCCESS_CRITERIA

- ✅ BOUNDARIES scoring criteria added
- ✅ Test excellent: "Do NOT modify database schema, TEST environment only" → 8-10
- ✅ Test poor: "None" → 0-2

---

## 3. BOUNDARIES

**Scope:** BOUNDARIES section only

---

## 4. DEPENDENCIES

- ✅ WORKER_064 complete

---

## 5. MITIGATION

**Rollback:** `git checkout` file

---

## 6. TEST_PROCESS

```bash
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
from wingman.validation.semantic_analyzer import SemanticAnalyzer

excellent = 'BOUNDARIES: Do NOT modify database schema, Do NOT touch production data, TEST environment only, Can modify API code'
poor = 'BOUNDARIES: None'

validator = ContentQualityValidator(SemanticAnalyzer())
assert validator.analyze_section('BOUNDARIES', excellent)['score'] >= 8
assert validator.analyze_section('BOUNDARIES', poor)['score'] <= 2
print('BOUNDARIES scoring PASSED')
"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{"worker_id": "WORKER_065", "status": "COMPLETE"}
```

---

## 8-10. [Standard sections]

**Type:** MECHANICAL
**Target:** ≤20 minutes

---

## IMPLEMENTATION NOTES

```python
"BOUNDARIES": """
BOUNDARIES Scoring Criteria (0-10):

0-2: POOR - Missing, "None", or no constraints specified
3-5: FAIR - Generic warnings ("be careful")
6-8: GOOD - Specific constraints but incomplete
9-10: EXCELLENT - Clear CAN/CANNOT lists, protects critical systems

Examples:
- "None" → 0
- "Be careful" → 3
- "Do NOT modify database" → 7
- "Do NOT modify database schema, Do NOT touch production data, TEST environment only" → 9
"""
```
