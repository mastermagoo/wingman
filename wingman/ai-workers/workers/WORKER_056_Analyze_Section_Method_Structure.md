# WORKER_056: Content Quality Validator - analyze_section() Method Structure

**Worker ID:** WORKER_056
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_055 complete (class skeleton exists)

---

## 1. DELIVERABLES

Add the main method for per-section scoring to ContentQualityValidator:

- **Method:** `analyze_section(section_name: str, section_content: str) -> Dict[str, Any]`
- **Purpose:** Score a single section (0-10) with reasoning
- **Return:** Dict with `{"score": 0-10, "reasoning": "explanation", "section_name": str}`
- **Location:** Add to `ContentQualityValidator` class in `content_quality_validator.py`
- **Signature:** Complete type hints for parameters and return type

**Output:** Method structure with docstring (implementation placeholder for now)

---

## 2. SUCCESS_CRITERIA

- ✅ Method `analyze_section()` added to `ContentQualityValidator` class
- ✅ Method signature: `def analyze_section(self, section_name: str, section_content: str) -> Dict[str, Any]:`
- ✅ Complete docstring with Args, Returns, and Examples
- ✅ Type hints present for all parameters and return type
- ✅ Method returns dict with required keys: `score`, `reasoning`, `section_name`
- ✅ Placeholder implementation returns default values (score=5, reasoning="Not implemented yet")
- ✅ Can be called: `result = validator.analyze_section("DELIVERABLES", "Deploy API")`
- ✅ No errors when calling method

---

## 3. BOUNDARIES

**CAN modify:**
- `wingman/validation/content_quality_validator.py` - add `analyze_section()` method
- Class docstring (update to reflect new method)

**CANNOT modify:**
- `__init__` method (from WORKER_055)
- Any other files
- Method implementation (scoring logic comes in WORKER_063-072)

**Scope:** Method structure only - placeholder implementation for now

---

## 4. DEPENDENCIES

**Required (must exist):**
- ✅ WORKER_055 complete: `ContentQualityValidator` class exists
- ✅ File exists: `wingman/validation/content_quality_validator.py`
- ✅ Class can be instantiated

**Optional:**
- None

**Verification:**
```bash
# Verify class exists
python3 -c "from wingman.validation.content_quality_validator import ContentQualityValidator; print('Class exists')"
```

---

## 5. MITIGATION

**Rollback Plan:**
```bash
# If method breaks class, restore from WORKER_055 backup
cd /Volumes/Data/ai_projects/wingman-system/wingman
git diff wingman/validation/content_quality_validator.py
git checkout wingman/validation/content_quality_validator.py  # If needed
```

**Triggers for rollback:**
- Method syntax errors
- Class instantiation fails after adding method
- Return type doesn't match type hint
- Takes >20 minutes

**Escalation:**
- If class missing: STOP, run WORKER_055 first
- If type hint errors: Check Python version (must support Dict from typing)
- If blocked >30 minutes: Escalate to user

**Recovery Time:** <2 minutes (revert changes via git)

---

## 6. TEST_PROCESS

**Manual Testing:**
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

# Test 1: No syntax errors after adding method
python3 -m py_compile wingman/validation/content_quality_validator.py

# Test 2: Can import class with new method
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
print('Import successful')
"

# Test 3: Can call method
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
class MockAnalyzer: pass
validator = ContentQualityValidator(MockAnalyzer())
result = validator.analyze_section('DELIVERABLES', 'Deploy API v2.1.0')
print(f'Result: {result}')
assert 'score' in result, 'Missing score key'
assert 'reasoning' in result, 'Missing reasoning key'
assert 'section_name' in result, 'Missing section_name key'
assert isinstance(result['score'], (int, float)), 'Score not numeric'
assert 0 <= result['score'] <= 10, 'Score out of range'
print('All assertions passed')
"

# Test 4: Verify return type structure
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
class MockAnalyzer: pass
validator = ContentQualityValidator(MockAnalyzer())
result = validator.analyze_section('TEST', 'test content')
assert isinstance(result, dict), 'Return type not dict'
print('Return type correct')
"
```

**Expected Results:**
- All 4 tests pass
- Method returns dict with 3 required keys
- Score is numeric 0-10
- No errors during execution

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "WORKER_056",
  "status": "COMPLETE",
  "duration_minutes": 18,
  "tests": {
    "no_syntax_errors": true,
    "can_import": true,
    "can_call_method": true,
    "return_type_correct": true,
    "score_in_range": true
  },
  "deliverable": {
    "method": "analyze_section",
    "signature": "analyze_section(self, section_name: str, section_content: str) -> Dict[str, Any]",
    "return_keys": ["score", "reasoning", "section_name"],
    "implementation_status": "placeholder"
  },
  "issues": []
}
```

---

## 8. TASK_CLASSIFICATION

**Type:** MECHANICAL

**Justification:**
- Straightforward method signature creation
- Clear structure from implementation plan
- No algorithm design needed yet (placeholder implementation)
- Template-based docstring
- 20-minute time box appropriate for mechanical task

**Complexity:** Low
**Creativity Required:** Minimal
**Automation Potential:** High

---

## 9. RETROSPECTIVE

**Store in mem0 after completion:**

```python
{
  "worker_id": "WORKER_056",
  "phase": "Phase 2 - Content Quality Validator",
  "task": "Add analyze_section() method structure",
  "actual_duration_minutes": 0,  # Fill in actual time
  "planned_duration_minutes": 20,
  "status": "COMPLETE|BLOCKED|FAILED",
  "blockers": [],
  "lessons_learned": [
    "Method signature straightforward from implementation plan",
    "Placeholder implementation allows testing structure before logic",
    "Type hints catch issues early"
  ],
  "code_quality": {
    "syntax_errors": 0,
    "method_callable": true,
    "return_type_matches_hint": true
  },
  "next_worker": "WORKER_057",
  "recommendations": [
    "Placeholder implementation useful for testing downstream workers",
    "Ensure return dict has all required keys"
  ]
}
```

**Store to mem0:**
```bash
curl -X POST http://127.0.0.1:18888/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "WORKER_056 retrospective: [JSON above]"}],
    "user_id": "wingman"
  }'
```

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline (manual implementation):**
- Human developer: 20-30 minutes
- Includes: method signature, docstring, placeholder, testing
- Error rate: ~5% (signature mistakes)

**Target (autonomous AI execution):**
- AI execution time: ≤20 minutes
- Success rate: ≥95%
- Zero syntax errors

**Monitoring:**
- Track actual duration vs 20-minute target
- Monitor method call success rate
- Track type hint compliance

**Performance Metrics:**
```json
{
  "target_duration_minutes": 20,
  "actual_duration_minutes": 0,
  "efficiency_ratio": 0.0,
  "quality_score": 10,
  "automation_level": "full"
}
```

**Success Threshold:** Complete in ≤20 minutes, method callable with correct return structure

---

## IMPLEMENTATION NOTES

**Method Template:**
```python
def analyze_section(self, section_name: str, section_content: str) -> Dict[str, Any]:
    """
    Analyze quality of a single 10-point framework section.

    Scores the section on a 0-10 scale based on content quality criteria.
    Implementation will use LLM-based scoring with heuristic fallback.

    Args:
        section_name: Name of section (e.g., "DELIVERABLES", "SUCCESS_CRITERIA")
        section_content: Text content of the section

    Returns:
        Dict with keys:
        - score (int): Quality score 0-10
        - reasoning (str): Explanation for the score
        - section_name (str): Name of section analyzed

    Example:
        >>> result = validator.analyze_section("DELIVERABLES", "Deploy API v2.1.0")
        >>> result["score"]
        8
        >>> result["reasoning"]
        "Specific deliverable with version number, clear and measurable"
    """
    # Placeholder implementation - actual scoring logic in WORKER_063-072
    return {
        "score": 5,
        "reasoning": "Placeholder implementation - not yet scoring actual content",
        "section_name": section_name
    }
```

**Reference:** Implementation Plan Lines 650-688
