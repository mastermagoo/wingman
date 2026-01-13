# WORKER_073: Overall Score Formula (Weighted Average)

**Worker ID:** WORKER_073
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_072 complete (all section scoring logic in place)

---

## 1. DELIVERABLES

Create main quality assessment function:

- **Method:** `assess_content_quality(instruction: str) -> Dict[str, Any]`
- **Purpose:** Parse instruction, score all 10 sections, calculate overall score
- **Formula:** `overall_score = sum(section_scores.values())` (0-100)
- **Return:** Complete analysis dict with section scores, overall score, pass/fail

---

## 2. SUCCESS_CRITERIA

- ✅ Method `assess_content_quality()` added to `ContentQualityValidator`
- ✅ Calls `parse_10_point_sections()` to extract sections
- ✅ Calls `analyze_section()` for each of 10 sections
- ✅ Calls `calculate_overall_score()` to aggregate
- ✅ Returns dict with keys: `section_scores`, `overall_quality`, `detailed_feedback`, `pass`
- ✅ `pass` = True if `overall_quality >= 60`, else False
- ✅ Test with complete instruction → returns all fields
- ✅ Test with poor instruction → pass = False

---

## 3. BOUNDARIES

**CAN:** Add `assess_content_quality()` main method
**CANNOT:** Modify section scoring logic, change threshold (60 is from plan)
**Scope:** Integration of all previous workers into main method

---

## 4. DEPENDENCIES

- ✅ WORKER_072 complete: All section scoring prompts ready
- ✅ Functions exist: `parse_10_point_sections`, `analyze_section`, `calculate_overall_score`

---

## 5. MITIGATION

**Rollback:** `git checkout wingman/validation/content_quality_validator.py`
**Recovery Time:** <2 minutes

---

## 6. TEST_PROCESS

```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
from wingman.validation.semantic_analyzer import SemanticAnalyzer

excellent_instruction = '''
DELIVERABLES: Deploy API v2.1.0 to production
SUCCESS_CRITERIA: All health checks return 200 for 5 minutes
BOUNDARIES: Do NOT modify database schema
DEPENDENCIES: Database v1.2+ (confirmed)
MITIGATION: Rollback: docker tag api:previous && restart
TEST_PROCESS: pytest -v tests/ (350 tests)
TEST_RESULTS_FORMAT: JSON {passed: N, failed: N}
RESOURCE_REQUIREMENTS: 4 CPU, 8GB RAM, 2 hours
RISK_ASSESSMENT: Low risk - TEST environment only
QUALITY_METRICS: Error <0.1%, latency <200ms
'''

validator = ContentQualityValidator(SemanticAnalyzer())
result = validator.assess_content_quality(excellent_instruction)

assert 'section_scores' in result
assert 'overall_quality' in result
assert 'detailed_feedback' in result
assert 'pass' in result
assert len(result['section_scores']) == 10
assert 0 <= result['overall_quality'] <= 100
assert result['pass'] == (result['overall_quality'] >= 60)

print(f'Overall quality: {result[\"overall_quality\"]}/100')
print(f'Pass: {result[\"pass\"]}')
print('assess_content_quality test PASSED')
"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "WORKER_073",
  "status": "COMPLETE",
  "duration_minutes": 18,
  "tests": {
    "excellent_instruction": true,
    "poor_instruction": true,
    "return_structure_correct": true
  },
  "sample_output": {
    "overall_quality": 85,
    "pass": true,
    "section_count": 10
  }
}
```

---

## 8. TASK_CLASSIFICATION

**Type:** MECHANICAL
**Complexity:** Medium (integration of multiple components)

---

## 9. RETROSPECTIVE

```python
{
  "worker_id": "WORKER_073",
  "task": "Overall score formula (weighted average)",
  "next_worker": "WORKER_074",
  "lessons_learned": [
    "Integration method brings together all section scoring",
    "Pass/fail threshold of 60 from implementation plan"
  ]
}
```

---

## 10. PERFORMANCE_REQUIREMENTS

**Target:** ≤20 minutes
**Monitoring:** End-to-end assessment time <30s per instruction

---

## IMPLEMENTATION NOTES

```python
def assess_content_quality(self, instruction: str) -> Dict[str, Any]:
    """
    Assess quality of 10-point framework instruction.

    Returns:
        {
            "section_scores": {"DELIVERABLES": 8, ...},
            "overall_quality": 75,
            "detailed_feedback": {"DELIVERABLES": "reasoning", ...},
            "pass": True
        }
    """
    # Parse sections
    sections = parse_10_point_sections(instruction)

    # Score each section
    scores = {}
    feedback = {}

    for section_name, section_content in sections.items():
        result = self.analyze_section(section_name, section_content)
        scores[section_name] = result['score']
        feedback[section_name] = result['reasoning']

    # Calculate overall score
    overall = calculate_overall_score(scores)

    return {
        "section_scores": scores,
        "overall_quality": overall,
        "detailed_feedback": feedback,
        "pass": overall >= 60
    }
```

**Reference:** Implementation Plan Lines 650-688
