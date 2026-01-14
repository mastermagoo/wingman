# Worker 006: Semantic Analyzer - Error Handling

**Date:** 2026-01-13
**Environment:** TEST
**Phase:** 1.1 - Semantic Analyzer Structure
**Duration:** 20 minutes
**Status:** READY FOR EXECUTION

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/semantic_analyzer.py`
- [ ] Add timeout handling for LLM calls (30 second timeout)
- [ ] Add invalid JSON response handling with fallback
- [ ] Add connection error handling (network failures)
- [ ] Implement fallback to heuristic scoring when LLM fails
- [ ] Add error logging for all failure cases
- [ ] Test results file: `ai-workers/results/worker-006-results.json`

---

## 2. SUCCESS_CRITERIA

- [ ] LLM timeout triggers fallback (not crash)
- [ ] Invalid JSON from LLM handled gracefully
- [ ] Network errors logged and handled
- [ ] Fallback returns valid response dict
- [ ] All error cases return valid structure (never None or exception)

---

## 3. BOUNDARIES

- **CAN modify:** `semantic_analyzer.py` - add error handling
- **CAN add:** Try/except blocks, timeout parameters, logging
- **CANNOT modify:** Core logic from WORKER_001-005
- **CANNOT add:** Full heuristic implementation (placeholder OK)
- **Idempotency:** Error handlers are idempotent

**Scope Limit:** Error handling structure only - heuristic details in later workers

---

## 4. DEPENDENCIES

- **Previous workers:** WORKER_001-005 (full class structure)
- **Python libraries:** logging, requests (timeout parameter)
- **No external services:** Error handling is local logic

---

## 5. MITIGATION

- **If timeout too short:** Increase to 30s (conservative)
- **If fallback fails:** Return minimal safe dict with LOW confidence
- **Rollback:** `git checkout wingman/validation/semantic_analyzer.py`
- **Escalation:** If all error paths fail, escalate (critical bug)
- **Risk Level:** LOW (improves reliability, no breaking changes)

---

## 6. TEST_PROCESS

```bash
# Test 1: Timeout handled (mock)
cd wingman && python3 -c "
from validation.semantic_analyzer import SemanticAnalyzer
import requests
from unittest.mock import patch

s = SemanticAnalyzer()
with patch('requests.post', side_effect=requests.Timeout('timeout')):
    result = s.analyze('test instruction')
    assert result is not None
    assert 'risk_level' in result
    print('PASS: Timeout handled gracefully')
"

# Test 2: Invalid JSON handled
cd wingman && python3 -c "
from validation.semantic_analyzer import SemanticAnalyzer
from unittest.mock import Mock, patch

s = SemanticAnalyzer()
mock_response = Mock()
mock_response.json.return_value = {'response': 'not valid json format'}
with patch('requests.post', return_value=mock_response):
    result = s.analyze('test')
    assert result is not None
    print('PASS: Invalid JSON handled')
"

# Test 3: Connection error handled
cd wingman && python3 -c "
from validation.semantic_analyzer import SemanticAnalyzer
import requests
from unittest.mock import patch

s = SemanticAnalyzer()
with patch('requests.post', side_effect=requests.ConnectionError('network error')):
    result = s.analyze('test instruction')
    assert result is not None
    assert 'confidence' in result
    assert result['confidence'] < 0.5  # Low confidence for fallback
    print('PASS: Connection error handled')
"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "006",
  "worker_name": "Semantic_Error_Handling",
  "status": "pass|fail",
  "deliverables_created": [
    "Error handling in SemanticAnalyzer"
  ],
  "test_results": {
    "timeout_handled": "pass|fail",
    "invalid_json_handled": "pass|fail",
    "connection_error_handled": "pass|fail"
  },
  "duration_seconds": 0,
  "timestamp": "2026-01-13T00:00:00Z",
  "errors": []
}
```

---

## 8. TASK_CLASSIFICATION

- **Type:** MECHANICAL
- **Tool:** Python exception handling
- **Reasoning:** Error handling patterns are standard
- **Local-first:** Yes - error handling logic
- **AI Assistance:** Minimal - standard try/except patterns

---

## 9. RETROSPECTIVE

- **Time estimate:** 20 minutes
- **Actual time:** [To be filled after execution]
- **Challenges:** [To be filled after execution]
- **Lessons learned:** [To be filled after execution]
- **Store in mem0:**
  - Key: "wingman_worker_006_retrospective"
  - Namespace: "wingman"
  - Content: Error types encountered, timeout tuning, fallback effectiveness

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Manual execution time: 20 minutes (add error handling, test edge cases)
- Current process: Manual implementation and testing

**Targets:**
- Automated execution: <20 minutes
- Accuracy: 100% (error handling must be reliable)
- Quality: All 3 error scenarios handled gracefully

**Monitoring:**
- Before: Verify WORKER_005 complete
- During: Track error path coverage
- After: Run all 3 test commands with mocks, verify 3/3 pass
- Degradation limit: If execution takes >40 minutes (2x estimate), abort and escalate

---

**Reference:**
- Implementation Plan: Lines 148-190 (Error handling and retry logic)
- Meta-Worker: `META_WORKER_WINGMAN_01_INSTRUCTION.md` (Lines 82-84)

**Wingman Validation Score:** [To be filled]
**Wingman Status:** PENDING APPROVAL
