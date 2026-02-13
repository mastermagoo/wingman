# WORKER_057: Content Quality Validator - Section Extractor

**Worker ID:** WORKER_057
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_056 complete (analyze_section method exists)

---

## 1. DELIVERABLES

Create function to parse 10-point instruction sections:

- **Function:** `parse_10_point_sections(instruction: str) -> Dict[str, str]`
- **Purpose:** Extract all 10 sections from instruction text
- **Return:** Dict mapping section names to content: `{"DELIVERABLES": "text", "SUCCESS_CRITERIA": "text", ...}`
- **Location:** Add to `content_quality_validator.py` (module-level function or class method)
- **Handle:** Missing sections (return empty string), varying formats, case-insensitive matching

**Output:** Parsing function that extracts all 10 sections reliably

---

## 2. SUCCESS_CRITERIA

- ✅ Function `parse_10_point_sections()` created
- ✅ Returns dict with all 10 section keys: `DELIVERABLES`, `SUCCESS_CRITERIA`, `BOUNDARIES`, `DEPENDENCIES`, `MITIGATION`, `TEST_PROCESS`, `TEST_RESULTS_FORMAT`, `RESOURCE_REQUIREMENTS`, `RISK_ASSESSMENT`, `QUALITY_METRICS`
- ✅ Missing sections return empty string `""`
- ✅ Handles sections in any order
- ✅ Case-insensitive matching (e.g., "deliverables:" matches "DELIVERABLES:")
- ✅ Extracts multi-line section content correctly
- ✅ Stops at next section header or end of text
- ✅ Test with good_instruction.txt: all 10 sections extracted
- ✅ Test with malformed instruction: no crashes, returns dict with empty strings

---

## 3. BOUNDARIES

**CAN modify:**
- `wingman/validation/content_quality_validator.py` - add parsing function
- Add regex patterns for section extraction
- Add test fixtures for validation

**CANNOT modify:**
- Existing methods (`__init__`, `analyze_section`)
- Any other validation files
- Database or API

**Scope:** Section parsing only - no scoring logic

---

## 4. DEPENDENCIES

**Required (must exist):**
- ✅ WORKER_056 complete: `analyze_section()` method exists
- ✅ File exists: `wingman/validation/content_quality_validator.py`
- ✅ Python `re` module (standard library)

**Optional:**
- Test fixtures (can create sample instructions for testing)

**Verification:**
```bash
# Verify previous worker complete
python3 -c "from wingman.validation.content_quality_validator import ContentQualityValidator; import inspect; print('analyze_section' in dir(ContentQualityValidator))"
```

---

## 5. MITIGATION

**Rollback Plan:**
```bash
# If parsing breaks, revert changes
cd /Volumes/Data/ai_projects/wingman-system/wingman
git diff wingman/validation/content_quality_validator.py
git checkout wingman/validation/content_quality_validator.py  # If needed
```

**Triggers for rollback:**
- Regex errors causing crashes
- Function doesn't return dict
- Takes >20 minutes
- Cannot handle basic instruction format

**Escalation:**
- If regex fails on all inputs: Review implementation plan (lines 691-726)
- If blocked >30 minutes: Escalate to user

**Recovery Time:** <2 minutes (revert via git)

---

## 6. TEST_PROCESS

**Manual Testing:**
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

# Test 1: Can import function
python3 -c "
from wingman.validation.content_quality_validator import parse_10_point_sections
print('Import successful')
"

# Test 2: Parse valid instruction
python3 -c "
from wingman.validation.content_quality_validator import parse_10_point_sections

instruction = '''
DELIVERABLES: Deploy API v2.1.0
SUCCESS_CRITERIA: Health checks return 200
BOUNDARIES: TEST environment only
DEPENDENCIES: Database v1.2+
MITIGATION: Rollback available
TEST_PROCESS: pytest suite
TEST_RESULTS_FORMAT: JSON output
RESOURCE_REQUIREMENTS: 4 CPU, 8GB RAM
RISK_ASSESSMENT: Low risk
QUALITY_METRICS: Error <0.1%
'''

result = parse_10_point_sections(instruction)
assert len(result) == 10, f'Expected 10 sections, got {len(result)}'
assert 'DELIVERABLES' in result
assert 'Deploy API' in result['DELIVERABLES']
print('Valid instruction test PASSED')
print(f'Sections found: {list(result.keys())}')
"

# Test 3: Parse instruction with missing sections
python3 -c "
from wingman.validation.content_quality_validator import parse_10_point_sections

instruction = 'DELIVERABLES: Test only'
result = parse_10_point_sections(instruction)
assert len(result) == 10, 'Should return dict with 10 keys'
assert result['DELIVERABLES'] != '', 'DELIVERABLES should not be empty'
assert result['SUCCESS_CRITERIA'] == '', 'Missing sections should be empty'
print('Missing sections test PASSED')
"

# Test 4: Parse malformed instruction
python3 -c "
from wingman.validation.content_quality_validator import parse_10_point_sections

instruction = 'This is not a 10-point instruction'
result = parse_10_point_sections(instruction)
assert isinstance(result, dict), 'Should return dict'
assert len(result) == 10, 'Should have 10 keys'
print('Malformed instruction test PASSED')
"
```

**Expected Results:**
- All 4 tests pass
- Function returns dict with 10 keys
- No crashes on malformed input

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "WORKER_057",
  "status": "COMPLETE",
  "duration_minutes": 19,
  "tests": {
    "can_import": true,
    "valid_instruction": true,
    "missing_sections": true,
    "malformed_instruction": true
  },
  "deliverable": {
    "function": "parse_10_point_sections",
    "sections_supported": 10,
    "handles_missing": true,
    "case_insensitive": true
  },
  "issues": []
}
```

---

## 8. TASK_CLASSIFICATION

**Type:** MECHANICAL

**Justification:**
- Clear regex-based parsing task
- Well-defined section names (10 required sections)
- Implementation pattern provided in plan (lines 701-723)
- No creative design needed
- 20-minute time box appropriate

**Complexity:** Medium (regex patterns)
**Creativity Required:** Minimal
**Automation Potential:** High

---

## 9. RETROSPECTIVE

**Store in mem0 after completion:**

```python
{
  "worker_id": "WORKER_057",
  "phase": "Phase 2 - Content Quality Validator",
  "task": "Create section extractor (parse 10-point instruction)",
  "actual_duration_minutes": 0,
  "planned_duration_minutes": 20,
  "status": "COMPLETE|BLOCKED|FAILED",
  "blockers": [],
  "lessons_learned": [
    "Regex pattern handles section extraction reliably",
    "Missing sections handled gracefully with empty strings",
    "Case-insensitive matching improves robustness"
  ],
  "code_quality": {
    "handles_valid_instructions": true,
    "handles_missing_sections": true,
    "handles_malformed_input": true,
    "no_crashes": true
  },
  "next_worker": "WORKER_058",
  "recommendations": [
    "Test with real instruction fixtures",
    "Consider caching parsed sections for repeated calls"
  ]
}
```

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline (manual implementation):**
- Human developer: 30-40 minutes (regex design + testing)
- Error rate: ~15% (regex edge cases)

**Target (autonomous AI execution):**
- AI execution time: ≤20 minutes
- Success rate: ≥90% (regex patterns can be tricky)
- Parsing accuracy: 100% for well-formed instructions

**Monitoring:**
- Track parsing success rate
- Monitor edge case handling
- Measure parsing speed (<100ms per instruction)

**Performance Metrics:**
```json
{
  "target_duration_minutes": 20,
  "actual_duration_minutes": 0,
  "parsing_speed_ms": 50,
  "accuracy_rate": 1.0,
  "automation_level": "full"
}
```

---

## IMPLEMENTATION NOTES

**Function Template:**
```python
import re
from typing import Dict

REQUIRED_SECTIONS = [
    "DELIVERABLES", "SUCCESS_CRITERIA", "BOUNDARIES",
    "DEPENDENCIES", "MITIGATION", "TEST_PROCESS",
    "TEST_RESULTS_FORMAT", "RESOURCE_REQUIREMENTS",
    "RISK_ASSESSMENT", "QUALITY_METRICS"
]

def parse_10_point_sections(instruction: str) -> Dict[str, str]:
    """
    Extract 10-point framework sections from instruction text.

    Args:
        instruction: Full instruction text with 10-point sections

    Returns:
        Dict mapping section names to content (empty string if missing)
    """
    sections = {}

    for section in REQUIRED_SECTIONS:
        # Try exact match first (case-insensitive)
        pattern = rf'{section}:\s*(.+?)(?=\n[A-Z_]+:|$)'
        match = re.search(pattern, instruction, re.DOTALL | re.IGNORECASE)

        if match:
            sections[section] = match.group(1).strip()
        else:
            sections[section] = ""  # Missing section

    return sections
```

**Reference:** Implementation Plan Lines 691-726
