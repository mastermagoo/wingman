# Worker 002: Semantic Analyzer - Ollama Client Integration

**Date:** 2026-01-13
**Environment:** TEST
**Phase:** 1.1 - Semantic Analyzer Structure
**Duration:** 20 minutes
**Status:** READY FOR EXECUTION

---

## 1. DELIVERABLES

- [ ] Create/update file: `validation/semantic_analyzer.py`
- [ ] Add Ollama client setup in `SemanticAnalyzer.__init__`
- [ ] Implement `_test_ollama_connection()` method
- [ ] Add connection validation with timeout (10 seconds)
- [ ] Add simple test prompt to verify Ollama responds
- [ ] Test results file: `ai-workers/results/worker-002-results.json`

**Exact Methods:**
- `SemanticAnalyzer._test_ollama_connection() -> bool`

---

## 2. SUCCESS_CRITERIA

- [ ] `_test_ollama_connection()` returns True when Ollama is available
- [ ] `_test_ollama_connection()` returns False when Ollama is unavailable
- [ ] Connection test uses 10-second timeout (no infinite hangs)
- [ ] Test prompt sent to Ollama endpoint successfully
- [ ] Connection test runs in constructor (validates on instantiation)

---

## 3. BOUNDARIES

- **CAN modify:** `semantic_analyzer.py` - add connection test method
- **CAN add:** `requests` library for HTTP calls to Ollama
- **CANNOT modify:** Ollama service configuration or deployment
- **CANNOT add:** Full semantic analysis logic (only connection test)
- **Idempotency:** Connection test is read-only, safe to run multiple times

**Scope Limit:** Connection validation only - no actual semantic analysis prompts

---

## 4. DEPENDENCIES

- **Previous worker:** WORKER_001 (SemanticAnalyzer class exists)
- **Ollama service:** `docker ps | grep ollama` must show running container
- **Python library:** `requests` (should be in api_requirements.txt)
- **Network:** Container can reach ollama:11434

**Validation Command:**
```bash
docker exec wingman-test-ollama-1 ollama list
```

---

## 5. MITIGATION

- **If Ollama unavailable:** Return False from connection test, log warning (do not fail)
- **If timeout:** Return False, log "Ollama connection timeout after 10s"
- **If network error:** Return False, log error message
- **Rollback:** `git checkout validation/semantic_analyzer.py` (restore WORKER_001 version)
- **Escalation:** If Ollama service missing entirely, escalate to human (required dependency)
- **Risk Level:** LOW (read-only connection test, graceful failure)

---

## 6. TEST_PROCESS

```bash
# Test 1: Connection test method exists
python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; s = SemanticAnalyzer(); assert hasattr(s, '_test_ollama_connection'); print('PASS: Method exists')"

# Test 2: Connection test returns boolean
python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; s = SemanticAnalyzer(); result = s._test_ollama_connection(); assert isinstance(result, bool); print(f'PASS: Returns bool ({result})')"

# Test 3: Connection test with Ollama running (expect True)
docker exec wingman-test-ollama-1 ollama list && python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; s = SemanticAnalyzer(ollama_endpoint='http://ollama:11434'); assert s._test_ollama_connection() == True; print('PASS: Ollama connection successful')"

# Test 4: Connection test with invalid endpoint (expect False)
python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; s = SemanticAnalyzer(ollama_endpoint='http://invalid:11434'); assert s._test_ollama_connection() == False; print('PASS: Invalid endpoint handled gracefully')"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "002",
  "worker_name": "Semantic_Ollama_Client",
  "status": "pass|fail",
  "deliverables_created": [
    "SemanticAnalyzer._test_ollama_connection method"
  ],
  "test_results": {
    "method_exists": "pass|fail",
    "returns_boolean": "pass|fail",
    "valid_endpoint_success": "pass|fail",
    "invalid_endpoint_handled": "pass|fail"
  },
  "ollama_status": "available|unavailable",
  "duration_seconds": 0,
  "timestamp": "2026-01-13T00:00:00Z",
  "errors": []
}
```

---

## 8. RESOURCE_REQUIREMENTS

- **Time:** 20 minutes
- **Compute:** Local Python 3.9+ interpreter
- **Memory:** <10 MB
- **Storage:** <1 KB
- **Network:** Localhost connection to Ollama (optional for tests)
- **External Services:** None (Ollama optional)
- **Environment:** Python 3.9+ with standard library

---

## 9. RISK_ASSESSMENT

- **Risk Level:** LOW
- **Impact if Failed:** Semantic analyzer cannot connect to LLM (falls back to heuristics)
- **Probability of Failure:** <10% (Add Ollama client method)
- **Blast Radius:** Add Ollama client method only
- **Data Loss Risk:** None (code changes only)
- **Rollback Complexity:** Simple (git checkout)
- **Service Disruption:** None (no running services affected)

---

## 10. QUALITY_METRICS

- **Test Pass Rate:** All tests must pass (100%)
- **Code Quality:** PEP 8 compliant, type hints present
- **Documentation:** Docstrings present for all public methods
- **Functionality:** Semantic analyzer Ollama connectivity works as specified

---

## 11. TASK_CLASSIFICATION

- **Type:** MECHANICAL
- **Tool:** Python (requests library)
- **Reasoning:** HTTP connection test is deterministic
- **Local-first:** Yes - uses local Ollama service
- **AI Assistance:** Minimal - standard HTTP client pattern

---

## 12. RETROSPECTIVE

- **Time estimate:** 20 minutes
- **Actual time:** [To be filled after execution]
- **Challenges:** [To be filled after execution]
- **Lessons learned:** [To be filled after execution]
- **Store in mem0:**
  - Key: "wingman_worker_002_retrospective"
  - Namespace: "wingman"
  - Content: Ollama connection reliability, timeout tuning, network issues

---

## 13. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Manual execution time: 15 minutes (write connection test, test with Ollama)
- Current process: Manual testing with curl/requests

**Targets:**
- Automated execution: <20 minutes (includes Ollama validation)
- Accuracy: >95% (network-dependent)
- Quality: Graceful handling of Ollama unavailability

**Monitoring:**
- Before: Verify Ollama service running
- During: Track connection attempt, timeout behavior
- After: Run all 4 test commands, verify 4/4 pass
- Degradation limit: If execution takes >40 minutes (2x estimate), abort and escalate

---

**Reference:**
- Implementation Plan: Lines 148-154 (Semantic analyzer core structure)
- Meta-Worker: `META_WORKER_WINGMAN_01_INSTRUCTION.md` (Lines 70-72)

**Wingman Validation Score:** [To be filled]
**Wingman Status:** PENDING APPROVAL
