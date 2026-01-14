# WORKER_079: API Integration Preparation

**Worker ID:** WORKER_079
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_078 complete

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/content_quality_validator.py`
Prepare validator for api_server.py integration:

- **Export:** Add `__all__` to module for clean imports
- **Documentation:** Module-level usage example
- **Initialization:** Add convenience function `create_content_quality_validator()`
- **Validation:** Ensure no circular imports with api_server

---

## 2. SUCCESS_CRITERIA

- ✅ Can import: `from wingman.validation.content_quality_validator import ContentQualityValidator`
- ✅ `__all__` defined with public API
- ✅ Module docstring has usage example
- ✅ Convenience function creates validator with semantic_analyzer
- ✅ No circular imports when imported by api_server.py
- ✅ Ready for Phase 3 integration (no code changes needed)

---

## 3. BOUNDARIES

**CAN:** Add exports, documentation, convenience functions
**CANNOT:** Modify core validator logic, change API

---

## 4. DEPENDENCIES

- ✅ WORKER_078 complete (all Phase 2 functionality done)

---

## 5. MITIGATION

**Rollback:** `git checkout` file

---

## 6. TEST_PROCESS

```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

# Test import from api_server context
python3 -c "
import sys
sys.path.insert(0, 'wingman')

from wingman.validation.content_quality_validator import (
    ContentQualityValidator,
    create_content_quality_validator
)

# Test convenience function
validator = create_content_quality_validator()
assert validator is not None

print('API integration preparation PASSED')
"

# Test no circular imports
python3 -c "
import sys
sys.path.insert(0, 'wingman')

# Simulate api_server import
from wingman.validation import content_quality_validator
print('No circular import issues')
"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "WORKER_079",
  "status": "COMPLETE",
  "duration_minutes": 17,
  "tests": {
    "import_clean": true,
    "no_circular_imports": true,
    "convenience_function": true
  },
  "readiness": {
    "phase_2_complete": true,
    "ready_for_phase_3": true
  }
}
```

---

## 8. TASK_CLASSIFICATION

**Type:** MECHANICAL
**Complexity:** Low

---

## 9. RETROSPECTIVE

```python
{
  "worker_id": "WORKER_079",
  "task": "Integration with api_server (endpoint preparation)",
  "next_worker": "WORKER_080",
  "phase_2_complete": true,
  "lessons_learned": [
    "Clean module interface simplifies integration",
    "Convenience functions reduce boilerplate in API code"
  ],
  "readiness": {
    "content_quality_validator": "COMPLETE",
    "ready_for_testing": true,
    "ready_for_api_integration": true
  }
}
```

---

## 10. PERFORMANCE_REQUIREMENTS

**Target:** ≤20 minutes
**Monitoring:** Import time <100ms

---

## IMPLEMENTATION NOTES

```python
# Add to top of content_quality_validator.py

"""
Content Quality Validator - Per-section quality assessment for 10-point framework

Usage:
    from wingman.validation.content_quality_validator import create_content_quality_validator

    validator = create_content_quality_validator()
    result = validator.assess_content_quality(instruction_text)

    if result['auto_reject']:
        # Reject poor quality instruction
        return 400, result
    elif result['pass']:
        # Accept good quality instruction
        return 200, result
"""

__all__ = [
    'ContentQualityValidator',
    'create_content_quality_validator',
    'parse_10_point_sections',
    'assign_quality_category',
    'AUTO_REJECT_THRESHOLD'
]

def create_content_quality_validator():
    """Create ContentQualityValidator with SemanticAnalyzer."""
    from wingman.validation.semantic_analyzer import SemanticAnalyzer
    return ContentQualityValidator(SemanticAnalyzer())
```

**Reference:** Prepare for Phase 3 API integration
**Next Phase:** WORKER_080-087 (Unit Tests)
