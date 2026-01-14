# WORKER_078: Result Formatter (JSON Output Structure)

**Worker ID:** WORKER_078
**Phase:** 2 - Content Quality Validator
**Estimated Time:** 20 minutes
**Dependencies:** WORKER_077 complete

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/content_quality_validator.py`
Formalize JSON output structure:

- **Function:** `format_content_quality_result()` - ensures consistent output
- **Schema:**
```json
{
  "section_scores": {
    "DELIVERABLES": 0-10,
    ...all 10 sections...
  },
  "overall_quality": 0-100,
  "quality_category": "EXCELLENT|GOOD|FAIR|POOR",
  "detailed_feedback": {
    "DELIVERABLES": "reasoning",
    ...all 10 sections...
  },
  "pass": true|false,
  "auto_reject": true|false,
  "timestamp": "ISO 8601",
  "validator_version": "2.0"
}
```

---

## 2. SUCCESS_CRITERIA

- ✅ Output matches schema exactly
- ✅ All fields present and correct types
- ✅ Timestamp in ISO 8601 format
- ✅ Version field for tracking
- ✅ JSON serializable (no Python objects)
- ✅ Test with json.dumps() - no errors

---

## 3. BOUNDARIES

**CAN:** Add formatting function, add metadata fields
**CANNOT:** Change core assessment logic

---

## 4. DEPENDENCIES

- ✅ WORKER_077 complete

---

## 5. MITIGATION

**Rollback:** `git checkout` file

---

## 6. TEST_PROCESS

```bash
python3 -c "
import json
from wingman.validation.content_quality_validator import ContentQualityValidator
from wingman.validation.semantic_analyzer import SemanticAnalyzer

instruction = '''
DELIVERABLES: Deploy API
SUCCESS_CRITERIA: Health checks pass
BOUNDARIES: TEST only
DEPENDENCIES: Database v1.2+
MITIGATION: Rollback available
TEST_PROCESS: pytest
TEST_RESULTS_FORMAT: JSON
RESOURCE_REQUIREMENTS: 4 CPU
RISK_ASSESSMENT: Low risk
QUALITY_METRICS: Error <0.1%
'''

validator = ContentQualityValidator(SemanticAnalyzer())
result = validator.assess_content_quality(instruction)

# Test JSON serialization
json_str = json.dumps(result, indent=2)
assert len(json_str) > 0

# Test required fields
assert 'timestamp' in result
assert 'validator_version' in result
assert result['validator_version'] == '2.0'

print('Result formatter tests PASSED')
"
```

---

## 7-10. [Standard sections]

**Type:** MECHANICAL

---

## IMPLEMENTATION NOTES

```python
from datetime import datetime

VALIDATOR_VERSION = "2.0"

def format_content_quality_result(section_scores, overall, category,
                                   feedback, pass_flag, auto_reject):
    """Format result with metadata."""
    return {
        "section_scores": section_scores,
        "overall_quality": overall,
        "quality_category": category,
        "detailed_feedback": feedback,
        "pass": pass_flag,
        "auto_reject": auto_reject,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "validator_version": VALIDATOR_VERSION
    }

# Update assess_content_quality() to use formatter
```

**Reference:** Consistent output structure for API integration
