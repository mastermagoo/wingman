# Worker 002: Command Allowlist Engine

**Date:** 2026-01-07
**Environment:** TEST
**Phase:** 1 (Core Components)
**Task Owner:** Human Operator (Mark)
**AI Assistant:** Claude (Sonnet 4.5) - Draft code only
**Status:** PENDING EXECUTION

---

## 1. DELIVERABLES

- [ ] `wingman/command_allowlist.py` - Command validation engine (AI draft, human reviews/applies)
- [ ] `wingman/command_parser.py` - Command parser (AI draft, human reviews/applies)
- [ ] `wingman/allowlist_rules.yaml` - Rule definitions (AI draft, human reviews/applies)
- [ ] `ai-workers/results/worker-002-results.json` - Execution results (human creates)

---

## 2. SUCCESS_CRITERIA

- [ ] Parses docker compose commands correctly
- [ ] Validates commands against YAML rules
- [ ] Blocks dangerous flags (`--force`, `--rm`, `-f`)
- [ ] Blocks out-of-scope files (e.g., prod compose files with test token)
- [ ] Blocks environment mismatches (test token, prd command)
- [ ] Returns clear rejection reasons
- [ ] Unit tests passing (>95% coverage)

---

## 3. BOUNDARIES

**CAN:**
- Create new files: `command_allowlist.py`, `command_parser.py`, `allowlist_rules.yaml`
- Add dependencies (PyYAML, regex)
- Create unit tests in `tests/test_allowlist.py`
- Define initial rule set for docker compose commands

**CANNOT:**
- Execute any commands (this is validation only)
- Modify gateway (Worker 001)
- Modify API server (Worker 005)
- Decide approval policy (rules are configuration, not enforcement logic)

**MUST:**
- Support docker compose command patterns
- Be extensible (easy to add new command types later)
- Provide detailed rejection reasons
- Handle malformed commands gracefully

---

## 4. DEPENDENCIES

**Hard Dependencies:**
- PyYAML library available
- None on other workers (independent, can run in parallel)

**Soft Dependencies:**
- Worker 001 will call this allowlist, but Worker 002 can be built independently

---

## 5. MITIGATION

**If rule file missing:**
- Load default restrictive rules (deny everything)
- Log warning
- Do not fail-open (security-first)

**If parse error:**
- Reject command with clear error
- Log parse failure
- Return "UNKNOWN_PATTERN" status

**If ambiguous rule match:**
- Apply most restrictive rule
- Log ambiguity for review
- Reject if unclear

**Rollback:**
- Delete 3 created files
- No database/state changes
- No stack restart needed

**Escalation:**
- If tests show false positives blocking valid work: review rules immediately
- If bypass found: block execution until fixed

**Risk Level:** MEDIUM (security-critical validation)

---

## 6. TEST_PROCESS

### Manual Testing (Human)
```bash
# After applying AI-drafted code:

# 1. Install dependencies
pip install PyYAML

# 2. Run unit tests
pytest tests/test_allowlist.py -v

# 3. Test allowlist manually
python -c "
from command_allowlist import CommandAllowlist
from capability_token import Token

allowlist = CommandAllowlist('allowlist_rules.yaml')

# Test 1: Valid docker compose command
token = Token(env='test', allowed_files=['docker-compose.yml'])
result = allowlist.validate('docker compose -f docker-compose.yml -p wingman-test ps', token)
print(f'Test 1 (valid): {result.allowed}')  # Should be True

# Test 2: Dangerous flag
result = allowlist.validate('docker compose -f docker-compose.yml --force', token)
print(f'Test 2 (dangerous): {result.allowed}')  # Should be False

# Test 3: Out of scope file
result = allowlist.validate('docker compose -f docker-compose.prd.yml ps', token)
print(f'Test 3 (out of scope): {result.allowed}')  # Should be False

# Test 4: Environment mismatch
token_prd = Token(env='prd', allowed_files=['docker-compose.prd.yml'])
result = allowlist.validate('docker compose -f docker-compose.yml ps', token_prd)
print(f'Test 4 (env mismatch): {result.allowed}')  # Should be False
"

# Expected output:
# Test 1 (valid): True
# Test 2 (dangerous): False
# Test 3 (out of scope): False
# Test 4 (env mismatch): False
```

### Automated Testing
```bash
pytest tests/test_allowlist.py -v --cov=command_allowlist --cov-report=term
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "002",
  "task": "Command Allowlist Engine",
  "status": "pass|fail",
  "deliverables_created": [
    "wingman/command_allowlist.py",
    "wingman/command_parser.py",
    "wingman/allowlist_rules.yaml",
    "wingman/tests/test_allowlist.py"
  ],
  "test_results": {
    "unit_tests_pass": true,
    "coverage_percent": 97,
    "valid_command_allowed": "pass",
    "dangerous_flag_blocked": "pass",
    "out_of_scope_blocked": "pass",
    "environment_mismatch_blocked": "pass",
    "malformed_command_handled": "pass"
  },
  "evidence": {
    "pytest_output": "18 passed, 0 failed",
    "false_positive_rate": "0%",
    "false_negative_rate": "0%"
  },
  "duration_minutes": 30,
  "timestamp": "2026-01-07T...",
  "human_operator": "Mark",
  "ai_assistance": "Claude drafted code, human reviewed and applied"
}
```

---

## 8. TASK_CLASSIFICATION

- **Type:** IMPLEMENTATION (security validation)
- **Complexity:** MEDIUM (pattern matching, rule engine)
- **Tool:** Python + PyYAML + regex
- **Reasoning:** Deterministic pattern matching, clear rules
- **Human-Led:** YES - AI drafts code, human reviews ALL code before applying
- **AI Role:** Code generation assistant only, no autonomous execution

---

## 9. RETROSPECTIVE

**Time estimate:** 20 minutes (AI draft) + 10 minutes (human review/test) = 30 minutes total

**Actual time:** [To be filled after execution]

**Challenges:** [To be filled after execution]

**Lessons learned:** [To be filled after execution]

**Rule tuning notes:** [To be filled - may need rule adjustments after testing]

**Store in mem0:**
- Command allowlist patterns for docker compose
- YAML-based rule engine pattern
- Security validation with clear rejection reasons

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Manual allowlist build: 1-2 hours
- Current process: No allowlist exists, all commands allowed

**Targets:**
- AI code generation: <20 minutes
- Human review/testing: <15 minutes
- Validation latency: <20ms per command
- Rule parsing: <5ms (on load)

**Quality:**
- Zero false negatives (no bypass)
- <5% false positives (valid work blocked)
- >95% test coverage
- Clear rejection reasons for all blocks

**Monitoring:**
- Before: Verify PyYAML installed
- During: Track false positive/negative rates
- After: Review all blocked commands, verify correctness
- Degradation limit: If false positive rate >10%, pause and review rules

---

## EXECUTION INSTRUCTIONS (HUMAN OPERATOR)

### Step 1: Request AI Code Draft
Ask AI to generate:
1. `command_allowlist.py` (validation engine, loads rules from YAML)
2. `command_parser.py` (parses docker compose commands into structured form)
3. `allowlist_rules.yaml` (initial rules for docker compose)
4. `tests/test_allowlist.py` (comprehensive unit tests)

### Step 2: Human Security Review
Review AI-generated code for:
- [ ] Parser correctly extracts flags, files, projects
- [ ] Rule matching logic is sound (no bypass)
- [ ] Dangerous flags list is comprehensive
- [ ] Environment validation is enforced
- [ ] Error messages don't leak sensitive info
- [ ] Rules are readable and maintainable

### Step 3: Apply Code (Manual)
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman
nano command_allowlist.py
nano command_parser.py
nano allowlist_rules.yaml
nano tests/test_allowlist.py
```

### Step 4: Run Tests (Manual)
```bash
pytest tests/test_allowlist.py -v
```

### Step 5: Manual Validation (Human)
Follow TEST_PROCESS section, verify all scenarios work.

### Step 6: Record Results (Human)
Create `ai-workers/results/worker-002-results.json`.

### Step 7: Gate Decision (Human)
- **PASS:** Proceed to next worker
- **FAIL:** Fix issues or rollback

---

**Wingman Validation Score:** N/A
**Human Approval Required:** YES
**Security Review Required:** YES
**Status:** AWAITING HUMAN EXECUTION
