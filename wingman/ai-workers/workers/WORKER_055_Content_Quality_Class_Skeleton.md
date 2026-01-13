# WORKER_055: Content Quality Validator - Class Skeleton

**Worker ID:** WORKER_055
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** Phase 1 complete (WORKER_001-054), semantic_analyzer.py available

---

## 1. DELIVERABLES

Create the foundational class structure for Content Quality Validator:

- **File:** `/Volumes/Data/ai_projects/wingman-system/wingman/wingman/validation/content_quality_validator.py`
- **Class:** `ContentQualityValidator`
- **Method:** `__init__(self, semantic_analyzer)` - Accept reference to semantic analyzer
- **Docstrings:** Complete module and class docstrings
- **Imports:** Required imports (typing, Dict, Any, semantic_analyzer)

**Output:** Python file with class skeleton that can be instantiated

---

## 2. SUCCESS_CRITERIA

- ✅ File `content_quality_validator.py` created in `wingman/validation/` directory
- ✅ `ContentQualityValidator` class defined with complete docstring
- ✅ `__init__` method accepts `semantic_analyzer` parameter and stores reference
- ✅ Class can be instantiated: `validator = ContentQualityValidator(semantic_analyzer)`
- ✅ No syntax errors when imported: `from wingman.validation.content_quality_validator import ContentQualityValidator`
- ✅ Type hints present for all parameters and return types
- ✅ Module docstring describes purpose: "Per-section quality assessment for 10-point framework"

---

## 3. BOUNDARIES

**CAN modify:**
- Create new file `wingman/validation/content_quality_validator.py`
- Add class structure, `__init__` method, and docstrings
- Add necessary imports

**CANNOT modify:**
- Any existing validation files
- `semantic_analyzer.py` (dependency from Phase 1)
- Database schema
- API endpoints

**Scope:** Class skeleton only - no scoring logic yet (that's WORKER_056-072)

---

## 4. DEPENDENCIES

**Required (must exist):**
- ✅ Phase 1 complete: `wingman/validation/semantic_analyzer.py` exists and functional
- ✅ Directory exists: `wingman/validation/`
- ✅ Python 3.8+ environment

**Optional:**
- None

**Verification:**
```bash
# Verify semantic_analyzer exists
ls -l /Volumes/Data/ai_projects/wingman-system/wingman/wingman/validation/semantic_analyzer.py

# Verify validation directory
ls -ld /Volumes/Data/ai_projects/wingman-system/wingman/wingman/validation/
```

---

## 5. MITIGATION

**Rollback Plan:**
```bash
# If file is broken, delete it
rm /Volumes/Data/ai_projects/wingman-system/wingman/wingman/validation/content_quality_validator.py
```

**Triggers for rollback:**
- Syntax errors prevent import
- Class instantiation fails
- Takes >20 minutes

**Escalation:**
- If semantic_analyzer missing: STOP, Phase 1 not complete
- If Python import errors: Check Python version (must be 3.8+)
- If blocked >30 minutes: Escalate to user

**Recovery Time:** <2 minutes (delete file and restart)

---

## 6. TEST_PROCESS

**Manual Testing:**
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

# Test 1: File exists
ls -l wingman/validation/content_quality_validator.py

# Test 2: No syntax errors
python3 -m py_compile wingman/validation/content_quality_validator.py

# Test 3: Can import
python3 -c "from wingman.validation.content_quality_validator import ContentQualityValidator; print('Import successful')"

# Test 4: Can instantiate (mock semantic_analyzer)
python3 -c "
from wingman.validation.content_quality_validator import ContentQualityValidator
class MockAnalyzer: pass
validator = ContentQualityValidator(MockAnalyzer())
print('Instantiation successful')
print(f'Validator type: {type(validator).__name__}')
"
```

**Expected Results:**
- All 4 tests pass
- No ImportError or SyntaxError
- Instantiation completes in <1 second

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "WORKER_055",
  "status": "COMPLETE",
  "duration_minutes": 15,
  "tests": {
    "file_exists": true,
    "no_syntax_errors": true,
    "can_import": true,
    "can_instantiate": true
  },
  "deliverable": {
    "file": "wingman/validation/content_quality_validator.py",
    "class": "ContentQualityValidator",
    "methods": ["__init__"],
    "lines_of_code": 25
  },
  "issues": []
}
```

---

## 8. TASK_CLASSIFICATION

**Type:** MECHANICAL

**Justification:**
- Straightforward class skeleton creation
- Clear structure: class definition + `__init__` method
- No creative design decisions needed
- Template-based implementation
- 20-minute time box appropriate for mechanical task

**Complexity:** Low
**Creativity Required:** Minimal
**Automation Potential:** High (could be code-generated from template)

---

## 9. RETROSPECTIVE

**Store in mem0 after completion:**

```python
{
  "worker_id": "WORKER_055",
  "phase": "Phase 2 - Content Quality Validator",
  "task": "Create class skeleton with __init__ method",
  "actual_duration_minutes": 0,  # Fill in actual time
  "planned_duration_minutes": 20,
  "status": "COMPLETE|BLOCKED|FAILED",
  "blockers": [],  # List any blockers encountered
  "lessons_learned": [
    "Class skeleton creation straightforward",
    "Directory structure already exists from Phase 1",
    "Import testing caught early issues"
  ],
  "code_quality": {
    "syntax_errors": 0,
    "import_errors": 0,
    "instantiation_successful": true
  },
  "next_worker": "WORKER_056",
  "recommendations": [
    "Ensure semantic_analyzer reference is stored correctly",
    "Validate directory exists before creating file"
  ]
}
```

**Store to mem0:**
```bash
curl -X POST http://127.0.0.1:18888/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "WORKER_055 retrospective: [JSON above]"}],
    "user_id": "wingman"
  }'
```

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline (manual implementation):**
- Human developer: 30-45 minutes
- Includes: class creation, docstrings, basic testing
- Error rate: ~10% (typos, import issues)

**Target (autonomous AI execution):**
- AI execution time: ≤20 minutes
- Success rate: ≥95% (automated testing catches issues)
- Zero syntax errors (automated validation)

**Monitoring:**
- Track actual duration vs 20-minute target
- Monitor import success rate
- Track instantiation errors

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

**Success Threshold:** Complete in ≤20 minutes with 0 syntax errors

---

## IMPLEMENTATION NOTES

**Code Template:**
```python
"""
Content Quality Validator - Per-section quality assessment for 10-point framework

This module assesses the quality of each section in a 10-point instruction,
scoring each section 0-10 and calculating an overall quality score 0-100.
"""

from typing import Dict, Any, Optional
from wingman.validation.semantic_analyzer import SemanticAnalyzer


class ContentQualityValidator:
    """
    Assesses content quality of 10-point framework instructions.

    Scores each of the 10 required sections (DELIVERABLES, SUCCESS_CRITERIA,
    BOUNDARIES, DEPENDENCIES, MITIGATION, TEST_PROCESS, TEST_RESULTS_FORMAT,
    RESOURCE_REQUIREMENTS, RISK_ASSESSMENT, QUALITY_METRICS) on a 0-10 scale.

    Overall quality score = sum of section scores (0-100 total).
    """

    def __init__(self, semantic_analyzer: SemanticAnalyzer):
        """
        Initialize Content Quality Validator.

        Args:
            semantic_analyzer: Instance of SemanticAnalyzer for LLM-based scoring
        """
        self.semantic_analyzer = semantic_analyzer
```

**Reference:** Implementation Plan Lines 636-688
