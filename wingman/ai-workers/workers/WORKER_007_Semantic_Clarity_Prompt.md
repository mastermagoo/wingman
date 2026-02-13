# Worker 007: Semantic Analyzer - Clarity Scoring Prompt

**Date:** 2026-01-13
**Environment:** TEST
**Phase:** 1.1 - Semantic Analyzer Prompts
**Duration:** 20 minutes
**Status:** READY FOR EXECUTION

---

## 1. DELIVERABLES

- [ ] Create/update file: `validation/semantic_analyzer.py`
- [ ] Create clarity scoring prompt template
- [ ] Add prompt that returns JSON {score: int, reasoning: str}
- [ ] Add examples for low/medium/high clarity
- [ ] Implement `_get_clarity_prompt(instruction: str) -> str` method
- [ ] Test results file: `ai-workers/results/worker-007-results.json`

---

## 2. SUCCESS_CRITERIA

- [ ] Prompt returns JSON with score (0-100) and reasoning
- [ ] High clarity instruction gets score >80
- [ ] Low clarity (vague) instruction gets score <40
- [ ] Moderate clarity instruction gets score 40-80
- [ ] Prompt is <2000 chars (LLM efficiency)

---

## 3. BOUNDARIES

- **CAN modify:** `semantic_analyzer.py` - add clarity prompt method
- **CAN add:** Prompt template string with examples
- **CANNOT modify:** Error handling or core methods
- **CANNOT test:** With real LLM (use mock - actual LLM testing in WORKER_013)
- **Idempotency:** Pure prompt generation, no side effects

**Scope Limit:** Prompt template only - LLM integration tested in later workers

---

## 4. DEPENDENCIES

- **Previous workers:** WORKER_001-006 (class structure complete)
- **Python libraries:** String formatting only
- **No external services:** Prompt generation is local

---

## 5. MITIGATION

- **If prompt too long:** Trim examples to fit <2000 chars
- **If LLM returns wrong format:** Error handling from WORKER_006 handles this
- **Rollback:** `git checkout validation/semantic_analyzer.py`
- **Escalation:** None needed (prompt is just text)
- **Risk Level:** MINIMAL (text generation only)

---

## 6. TEST_PROCESS

```bash
# Test 1: Method exists
python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; s = SemanticAnalyzer(); assert hasattr(s, '_get_clarity_prompt'); print('PASS: Method exists')"

# Test 2: Returns string
python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; s = SemanticAnalyzer(); result = s._get_clarity_prompt('test'); assert isinstance(result, str); print('PASS: Returns string')"

# Test 3: Contains instruction
python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; s = SemanticAnalyzer(); result = s._get_clarity_prompt('test instruction'); assert 'test instruction' in result; print('PASS: Contains instruction')"

# Test 4: Prompt length reasonable
python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; s = SemanticAnalyzer(); result = s._get_clarity_prompt('test'); assert len(result) < 2000; print('PASS: Prompt length OK')"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "007",
  "worker_name": "Semantic_Clarity_Prompt",
  "status": "pass|fail",
  "deliverables_created": [
    "SemanticAnalyzer._get_clarity_prompt() method"
  ],
  "test_results": {
    "method_exists": "pass|fail",
    "returns_string": "pass|fail",
    "contains_instruction": "pass|fail",
    "prompt_length_ok": "pass|fail"
  },
  "duration_seconds": 0,
  "timestamp": "2026-01-13T00:00:00Z",
  "errors": []
}
```

---

## 8. RESOURCE_REQUIREMENTS

- **Time:** 20 minutes
- **Compute:** Local Python 3.9+ interpreter
- **Memory:** <5 MB
- **Storage:** None
- **Network:** None
- **External Services:** None
- **Environment:** Python 3.9+ with standard library

---

## 9. RISK_ASSESSMENT

- **Risk Level:** MINIMAL
- **Impact if Failed:** Clarity scoring unavailable
- **Probability of Failure:** <5% (Create clarity prompt)
- **Blast Radius:** Create clarity prompt only
- **Data Loss Risk:** None (code changes only)
- **Rollback Complexity:** Simple (git checkout)
- **Service Disruption:** None (no running services affected)

---

## 10. QUALITY_METRICS

- **Test Pass Rate:** All tests must pass (100%)
- **Code Quality:** PEP 8 compliant, type hints present
- **Documentation:** Docstrings present for all public methods
- **Functionality:** Semantic clarity assessment works as specified

---

## 11. TASK_CLASSIFICATION

- **Type:** CREATIVE
- **Tool:** Prompt engineering
- **Reasoning:** Crafting effective LLM prompt requires creativity
- **Local-first:** Yes - text generation
- **AI Assistance:** Medium - prompt design requires LLM understanding

---

## 12. RETROSPECTIVE

- **Time estimate:** 20 minutes
- **Actual time:** [To be filled after execution]
- **Challenges:** [To be filled after execution]
- **Lessons learned:** [To be filled after execution]
- **Store in mem0:**
  - Key: "wingman_worker_007_retrospective"
  - Namespace: "wingman"
  - Content: Clarity prompt design, examples effectiveness, LLM response format

---

## 13. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Manual execution time: 20 minutes (design prompt, add examples, test format)
- Current process: Manual prompt engineering

**Targets:**
- Automated execution: <20 minutes
- Accuracy: Prompt quality validated in WORKER_013
- Quality: Clear instructions, JSON format specified, examples included

**Monitoring:**
- Before: Verify WORKER_006 complete
- During: Track prompt design, format specification
- After: Run all 4 test commands, verify 4/4 pass
- Degradation limit: If execution takes >40 minutes (2x estimate), abort and escalate

---

**Reference:**
- Implementation Plan: Lines 200-242 (LLM prompt engineering)
- Meta-Worker: `META_WORKER_WINGMAN_01_INSTRUCTION.md` (Lines 90-94)

**Wingman Validation Score:** [To be filled]
**Wingman Status:** PENDING APPROVAL
