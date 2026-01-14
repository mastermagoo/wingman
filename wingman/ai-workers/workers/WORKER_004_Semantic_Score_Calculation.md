# Worker 004: Semantic Analyzer - Score Calculation Logic

**Date:** 2026-01-13
**Environment:** TEST
**Phase:** 1.1 - Semantic Analyzer Structure
**Duration:** 20 minutes
**Status:** READY FOR EXECUTION

---

## 1. DELIVERABLES

- [ ] Create/update file: `wingman/validation/semantic_analyzer.py`
- [ ] Implement `_calculate_final_score(responses: List[Dict]) -> int` method
- [ ] Add score normalization to 0-100 range
- [ ] Add weighted averaging logic (clarity 40%, completeness 40%, coherence 20%)
- [ ] Add bounds checking (ensure score never <0 or >100)
- [ ] Test results file: `ai-workers/results/worker-004-results.json`

**Exact Method:**
```python
def _calculate_final_score(self, responses: List[Dict[str, Any]]) -> int:
    """Calculate final semantic score from LLM responses.
    Returns: Integer 0-100
    """
```

---

## 2. SUCCESS_CRITERIA

- [ ] Method accepts list of dicts with 'score' keys
- [ ] Returns integer in range 0-100 (inclusive)
- [ ] Empty list returns 0
- [ ] Single response score correctly normalized
- [ ] Multiple response scores correctly averaged with weights
- [ ] Handles out-of-range input scores gracefully (clip to 0-100)

---

## 3. BOUNDARIES

- **CAN modify:** `semantic_analyzer.py` - add score calculation method
- **CAN add:** Math logic for averaging and normalization
- **CANNOT modify:** Input validation or analyze() structure from WORKER_003
- **CANNOT add:** LLM response parsing (next workers)
- **Idempotency:** Pure function, no side effects

**Scope Limit:** Score calculation only - no LLM interaction

---

## 4. DEPENDENCIES

- **Previous workers:** WORKER_001-003 (class structure and analyze method)
- **Python libraries:** Standard library only (no external dependencies)
- **No external services:** Pure math calculation

---

## 5. MITIGATION

- **If invalid input:** Return 0 and log warning
- **If score out of range:** Clip to 0-100 bounds
- **If empty responses:** Return 0 (safest default)
- **Rollback:** `git checkout wingman/validation/semantic_analyzer.py` (restore WORKER_003 version)
- **Escalation:** None needed (pure calculation, low risk)
- **Risk Level:** MINIMAL (deterministic math, no external dependencies)

---

## 6. TEST_PROCESS

```bash
# Test 1: Method exists
cd wingman && python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; s = SemanticAnalyzer(); assert hasattr(s, '_calculate_final_score'); print('PASS: Method exists')"

# Test 2: Empty list returns 0
cd wingman && python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; s = SemanticAnalyzer(); result = s._calculate_final_score([]); assert result == 0; print('PASS: Empty list returns 0')"

# Test 3: Single score normalized
cd wingman && python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; s = SemanticAnalyzer(); result = s._calculate_final_score([{'score': 85}]); assert 0 <= result <= 100; print(f'PASS: Single score normalized ({result})')"

# Test 4: Multiple scores averaged
cd wingman && python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; s = SemanticAnalyzer(); result = s._calculate_final_score([{'score': 80}, {'score': 90}]); assert 80 <= result <= 90; print(f'PASS: Multiple scores averaged ({result})')"

# Test 5: Out of range clipped
cd wingman && python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; s = SemanticAnalyzer(); result = s._calculate_final_score([{'score': 150}]); assert result == 100; print('PASS: High score clipped to 100')"

# Test 6: Negative score clipped
cd wingman && python3 -c "from validation.semantic_analyzer import SemanticAnalyzer; s = SemanticAnalyzer(); result = s._calculate_final_score([{'score': -50}]); assert result == 0; print('PASS: Negative score clipped to 0')"
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "004",
  "worker_name": "Semantic_Score_Calculation",
  "status": "pass|fail",
  "deliverables_created": [
    "SemanticAnalyzer._calculate_final_score() method"
  ],
  "test_results": {
    "method_exists": "pass|fail",
    "empty_list_handled": "pass|fail",
    "single_score_normalized": "pass|fail",
    "multiple_scores_averaged": "pass|fail",
    "high_score_clipped": "pass|fail",
    "negative_score_clipped": "pass|fail"
  },
  "duration_seconds": 0,
  "timestamp": "2026-01-13T00:00:00Z",
  "errors": []
}
```

---

## 8. TASK_CLASSIFICATION

- **Type:** MECHANICAL
- **Tool:** Python math operations
- **Reasoning:** Score calculation is deterministic arithmetic
- **Local-first:** Yes - pure calculation, no I/O
- **AI Assistance:** None - standard math formula

---

## 9. RETROSPECTIVE

- **Time estimate:** 20 minutes
- **Actual time:** [To be filled after execution]
- **Challenges:** [To be filled after execution]
- **Lessons learned:** [To be filled after execution]
- **Store in mem0:**
  - Key: "wingman_worker_004_retrospective"
  - Namespace: "wingman"
  - Content: Score calculation formula, edge cases handled, weighting rationale

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Manual execution time: 15 minutes (write calculation, test edge cases)
- Current process: Manual implementation and testing

**Targets:**
- Automated execution: <20 minutes
- Accuracy: 100% (deterministic math)
- Quality: All 6 tests pass, proper bounds checking

**Monitoring:**
- Before: Verify WORKER_003 complete
- During: Track calculation logic, edge case handling
- After: Run all 6 test commands, verify 6/6 pass
- Degradation limit: If execution takes >40 minutes (2x estimate), abort and escalate

---

**Reference:**
- Implementation Plan: Lines 148-154 (Score calculation logic)
- Meta-Worker: `META_WORKER_WINGMAN_01_INSTRUCTION.md` (Lines 76-78)

**Wingman Validation Score:** [To be filled]
**Wingman Status:** PENDING APPROVAL
