# Worker 003: Multi-LLM Consensus Verifier

**Date:** 2026-01-07
**Environment:** TEST
**Phase:** 1 (Core Components)
**Task Owner:** Human Operator (Mark)
**AI Assistant:** Claude (Sonnet 4.5) - Draft code only
**Status:** PENDING EXECUTION

---

## 1. DELIVERABLES

- [ ] `wingman/consensus_verifier.py` - Orchestrates N-of-M LLM queries (AI draft, human reviews)
- [ ] `wingman/llm_clients.py` - Mistral/GPT-4/Claude client wrappers (AI draft, human reviews)
- [ ] `wingman/consensus_config.yaml` - Configuration (models, thresholds) (AI draft, human reviews)
- [ ] `ai-workers/results/worker-003-results.json` - Execution results (human creates)

---

## 2. SUCCESS_CRITERIA

- [ ] Queries 3 LLMs in parallel (Mistral, GPT-4, Claude)
- [ ] Aggregates votes with 2/3 threshold for HIGH risk
- [ ] Handles LLM timeouts gracefully (30s timeout per model)
- [ ] Falls back to Mistral-only if OpenAI/Anthropic APIs unavailable
- [ ] Logs dissenting opinions
- [ ] Returns consensus decision (APPROVED/REJECTED/REVIEW)
- [ ] Unit tests passing (>90% coverage, mocked LLM calls)

---

## 3. BOUNDARIES

**CAN:**
- Create new files: `consensus_verifier.py`, `llm_clients.py`, `consensus_config.yaml`
- Call external APIs (Ollama, OpenAI, Anthropic)
- Add dependencies (requests, openai, anthropic SDKs)
- Create unit tests with mocked LLM responses

**CANNOT:**
- Make approval decisions (only provides consensus recommendation)
- Modify approval_store.py (Worker 005 does integration)
- Execute any commands
- Store API keys in code (must use environment variables)

**MUST:**
- Handle API failures gracefully
- Timeout on slow LLM responses
- Log all LLM responses (for audit)
- Support configuration changes without code changes

---

## 4. DEPENDENCIES

**Hard Dependencies:**
- Ollama running (Mistral 7B)
- Python requests library
- PyYAML for config

**Soft Dependencies:**
- OpenAI API key (optional, falls back to Mistral-only)
- Anthropic API key (optional, falls back to Mistral-only)

**Note:** Independent worker, can run in parallel with 001/002/004

---

## 5. MITIGATION

**If all LLMs timeout:**
- Return "REVIEW" (require human decision)
- Log timeout event
- Do not block approval (fail-open for availability)

**If OpenAI/Anthropic unavailable:**
- Use Mistral-only consensus (1-of-1)
- Log fallback mode
- Continue operation

**If consensus split (1 HIGH, 1 MEDIUM, 1 LOW):**
- Apply conservative threshold (default to REVIEW)
- Log split decision
- Human decides

**Rollback:**
- Delete 3 created files
- No API side effects
- No database changes

**Escalation:**
- If LLM responses are nonsensical: review prompts
- If consensus disagrees with human judgment repeatedly: tune thresholds

**Risk Level:** LOW (advisory only, doesn't block execution)

---

## 6. TEST_PROCESS

### Manual Testing (Human)
```bash
# After applying AI-drafted code:

# 1. Install dependencies
pip install openai anthropic requests PyYAML

# 2. Set API keys (if available)
export OPENAI_API_KEY="sk-..."  # optional
export ANTHROPIC_API_KEY="sk-ant-..."  # optional

# 3. Run unit tests (mocked)
pytest tests/test_consensus.py -v

# 4. Test with real APIs
python -c "
from consensus_verifier import ConsensusVerifier

verifier = ConsensusVerifier('consensus_config.yaml')

# Test 1: HIGH risk instruction
result = verifier.verify_approval_request(
    instruction='Deploy to production and drop all tables',
    task_name='Deploy',
    deployment_env='prd'
)
print(f'Test 1 (HIGH risk): {result.risk_level}, Decision: {result.decision}')
# Expected: risk_level=HIGH, decision=REJECTED or REVIEW

# Test 2: LOW risk instruction
result = verifier.verify_approval_request(
    instruction='List docker containers in test environment',
    task_name='Status check',
    deployment_env='test'
)
print(f'Test 2 (LOW risk): {result.risk_level}, Decision: {result.decision}')
# Expected: risk_level=LOW, decision=APPROVED

# Test 3: Verify all 3 LLMs were queried
print(f'Votes: {result.votes}')
# Expected: 3 votes (or fallback to 1 if APIs unavailable)
"
```

### Automated Testing (Mocked)
```bash
pytest tests/test_consensus.py -v --cov=consensus_verifier --cov-report=term
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "003",
  "task": "Multi-LLM Consensus Verifier",
  "status": "pass|fail",
  "deliverables_created": [
    "wingman/consensus_verifier.py",
    "wingman/llm_clients.py",
    "wingman/consensus_config.yaml",
    "wingman/tests/test_consensus.py"
  ],
  "test_results": {
    "unit_tests_pass": true,
    "coverage_percent": 92,
    "three_llm_query": "pass",
    "timeout_handling": "pass",
    "fallback_to_mistral": "pass",
    "consensus_threshold": "pass",
    "high_risk_rejected": "pass",
    "low_risk_approved": "pass"
  },
  "evidence": {
    "pytest_output": "15 passed, 0 failed",
    "real_api_test_votes": [
      {"model": "mistral", "risk": "HIGH"},
      {"model": "gpt-4", "risk": "HIGH"},
      {"model": "claude", "risk": "MEDIUM"}
    ],
    "consensus_decision": "REJECTED",
    "average_latency_ms": 2400
  },
  "duration_minutes": 45,
  "timestamp": "2026-01-07T...",
  "human_operator": "Mark",
  "ai_assistance": "Claude drafted code, human reviewed and applied",
  "api_costs": "$2.50"
}
```

---

## 8. TASK_CLASSIFICATION

- **Type:** IMPLEMENTATION (LLM orchestration)
- **Complexity:** MEDIUM (parallel async calls, consensus logic)
- **Tool:** Python + OpenAI/Anthropic SDKs
- **Reasoning:** Multiple API calls, aggregation logic
- **Human-Led:** YES - AI drafts code, human reviews ALL code before applying
- **AI Role:** Code generation assistant only, no autonomous execution

---

## 9. RETROSPECTIVE

**Time estimate:** 30 minutes (AI draft) + 15 minutes (human review/test) = 45 minutes total

**Actual time:** [To be filled after execution]

**Challenges:** [To be filled after execution]

**LLM API reliability:** [To be filled - track failures/timeouts]

**Consensus accuracy:** [To be filled - does consensus match human judgment?]

**Store in mem0:**
- Multi-LLM consensus pattern
- Parallel API call orchestration
- Fallback strategies for external API dependencies

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Manual multi-LLM consensus: N/A (doesn't exist)
- Current process: Single keyword-based risk assessment

**Targets:**
- AI code generation: <30 minutes
- Human review/testing: <15 minutes
- Consensus query latency: <30s (all 3 LLMs in parallel)
- Fallback to Mistral-only: <5s

**Quality:**
- >90% agreement with human risk assessment (validate on 20 test cases)
- <5s timeout per LLM (fail-fast)
- Graceful degradation (Mistral-only fallback works)

**Monitoring:**
- Before: Verify Ollama running, API keys set (optional)
- During: Track LLM response times, timeout rate
- After: Review consensus decisions, compare with human judgment
- Degradation limit: If consensus consistently wrong, disable and use single LLM

---

## EXECUTION INSTRUCTIONS (HUMAN OPERATOR)

### Step 1: Request AI Code Draft
Ask AI to generate:
1. `consensus_verifier.py` (orchestrator, queries 3 LLMs, aggregates)
2. `llm_clients.py` (wrappers for Ollama, OpenAI, Anthropic APIs)
3. `consensus_config.yaml` (model endpoints, thresholds)
4. `tests/test_consensus.py` (unit tests with mocked LLM responses)

### Step 2: Human Review
Review AI-generated code for:
- [ ] API keys loaded from environment (not hardcoded)
- [ ] Timeout handling is correct
- [ ] Parallel queries work correctly
- [ ] Consensus logic (2/3 threshold) is implemented
- [ ] Fallback to Mistral-only works
- [ ] Error handling doesn't expose API keys in logs

### Step 3: Apply Code (Manual)
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman
nano consensus_verifier.py
nano llm_clients.py
nano consensus_config.yaml
nano tests/test_consensus.py
```

### Step 4: Set API Keys (Optional)
```bash
# Add to .env.test (not committed)
echo "OPENAI_API_KEY=sk-..." >> .env.test
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env.test
```

### Step 5: Run Tests
```bash
pytest tests/test_consensus.py -v
```

### Step 6: Manual Validation
Follow TEST_PROCESS section, test with real APIs if keys available.

### Step 7: Record Results
Create `ai-workers/results/worker-003-results.json`.

### Step 8: Gate Decision
- **PASS:** Proceed to next worker
- **FAIL:** Fix issues or rollback

---

**Wingman Validation Score:** N/A
**Human Approval Required:** YES
**Security Review Required:** MEDIUM (API key handling)
**Status:** AWAITING HUMAN EXECUTION
