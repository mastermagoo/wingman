# WORKER_075: Auto-Reject Logic (Quality < 60)

**Worker ID:** WORKER_075
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_074 complete

---

## 1. DELIVERABLES

Add auto-reject flag to assessment:

- **Field:** `auto_reject: bool` in return dict
- **Logic:** `auto_reject = (overall_quality < 60)`
- **Purpose:** Flag instructions for automatic rejection by API
- **Integration:** Add to `assess_content_quality()` return

---

## 2. SUCCESS_CRITERIA

- ✅ `assess_content_quality()` returns `auto_reject` field
- ✅ Score 59 → `auto_reject = True`
- ✅ Score 60 → `auto_reject = False`
- ✅ Score 0 → `auto_reject = True`
- ✅ Score 100 → `auto_reject = False`
- ✅ `auto_reject` matches `pass` field: `auto_reject = not pass`

---

## 3. BOUNDARIES

**CAN:** Add auto_reject field
**CANNOT:** Change threshold (60 is from plan)

---

## 4. DEPENDENCIES

- ✅ WORKER_074 complete

---

## 5. MITIGATION

**Rollback:** `git checkout` file

---

## 6. TEST_PROCESS

```bash
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
from wingman.validation.semantic_analyzer import SemanticAnalyzer

# Poor instruction (should auto-reject)
poor = '''
DELIVERABLES: TBD
SUCCESS_CRITERIA: Make it work
BOUNDARIES: None
DEPENDENCIES: None
MITIGATION: None
TEST_PROCESS: test it
TEST_RESULTS_FORMAT: show results
RESOURCE_REQUIREMENTS: normal
RISK_ASSESSMENT: low
QUALITY_METRICS: good
'''

validator = ContentQualityValidator(SemanticAnalyzer())
result = validator.assess_content_quality(poor)

assert 'auto_reject' in result
assert result['auto_reject'] == True
assert result['overall_quality'] < 60
assert result['pass'] == False

print('Auto-reject test PASSED')
"
```

---

## 7-10. [Standard sections]

**Type:** MECHANICAL

---

## IMPLEMENTATION NOTES

```python
# In assess_content_quality(), add:
return {
    "section_scores": scores,
    "overall_quality": overall,
    "quality_category": assign_quality_category(overall),
    "detailed_feedback": feedback,
    "pass": overall >= 60,
    "auto_reject": overall < 60  # Auto-reject if quality too low
}
```

**Reference:** Auto-reject logic from implementation plan
