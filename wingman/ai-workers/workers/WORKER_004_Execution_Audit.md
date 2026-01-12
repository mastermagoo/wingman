# Worker 004: Execution Audit Trail

**Date:** 2026-01-07
**Environment:** TEST
**Phase:** 1 (Core Components)
**Task Owner:** Human Operator (Mark)
**AI Assistant:** Claude (Sonnet 4.5) - Draft code only
**Status:** PENDING EXECUTION

---

## 1. DELIVERABLES

- [ ] `wingman/execution_logger.py` - Audit logger (AI draft, human reviews)
- [ ] `wingman/approval_reconciliation.py` - Reconciliation engine (AI draft, human reviews)
- [ ] `wingman/audit_schema.sql` - PostgreSQL schema (AI draft, human reviews)
- [ ] `ai-workers/results/worker-004-results.json` - Execution results (human creates)

---

## 2. SUCCESS_CRITERIA

- [ ] Appends execution records to PostgreSQL `execution_audit` table
- [ ] Records: approval_id, command, output, artifacts, timestamps
- [ ] Audit records are immutable (no updates/deletes)
- [ ] Reconciliation compares approved instructions vs executed commands
- [ ] Alerts on mismatches (executed work ≠ approved work)
- [ ] Unit tests passing (>95% coverage)

---

## 3. BOUNDARIES

**CAN:**
- Create new files: `execution_logger.py`, `approval_reconciliation.py`, `audit_schema.sql`
- Create new PostgreSQL table: `execution_audit`
- Query existing `approvals` table for reconciliation
- Use Mistral for natural language comparison (approved vs executed)

**CANNOT:**
- Modify existing `approvals` table schema
- Delete audit records (append-only)
- Execute commands (logging only)
- Block executions (alerting only)

**MUST:**
- Use append-only pattern (no UPDATE/DELETE on audit table)
- Handle PostgreSQL connection failures gracefully (fallback to JSONL)
- Preserve audit records across system restarts
- Include token hash for replay detection

---

## 4. DEPENDENCIES

**Hard Dependencies:**
- PostgreSQL running and accessible
- Existing `approvals` table (from approval_store.py)

**Soft Dependencies:**
- Worker 001 (Gateway) will call logger, but logger can be built independently
- Mistral (for reconciliation NLP comparison)

**Note:** Independent worker, can run in parallel with 001/002/003

---

## 5. MITIGATION

**If PostgreSQL unavailable:**
- Fallback to JSONL file: `data/execution_audit.jsonl`
- Log warning
- Graceful degradation (no execution blocking)

**If reconciliation fails:**
- Log error
- Continue operation (reconciliation is async/batch)
- Alert human for manual review

**If audit table full:**
- PostgreSQL handles growth (TimescaleDB optional for compression)
- Archival strategy: move old records to cold storage (>1 year)

**Rollback:**
- Delete 3 created files
- Drop `execution_audit` table (if created)
- No impact on running system

**Escalation:**
- If audit log shows tampering: immediate security review
- If reconciliation finds systematic mismatches: halt deployments

**Risk Level:** MEDIUM (critical for accountability)

---

## 6. TEST_PROCESS

### Manual Testing (Human)
```bash
# After applying AI-drafted code:

# 1. Create audit table
psql -h localhost -p 6432 -U admin -d wingman_test -f audit_schema.sql

# 2. Run unit tests
pytest tests/test_audit.py -v

# 3. Test logger manually
python -c "
from execution_logger import ExecutionLogger

logger = ExecutionLogger(db_url='postgresql://admin:pass@localhost:6432/wingman_test')

# Log execution
execution_id = logger.log_execution(
    approval_id='test-approval-123',
    worker_id='claude-test',
    command='docker compose ps',
    output='NAME STATUS...',
    exit_code=0,
    artifacts=[],
    duration_ms=2000,
    token_hash='sha256abcdef'
)

print(f'Logged execution: {execution_id}')
"

# 4. Verify record in database
psql -h localhost -p 6432 -U admin -d wingman_test -c "SELECT * FROM execution_audit ORDER BY created_at DESC LIMIT 1;"

# Expected: See logged execution with all fields

# 5. Test reconciliation
python -c "
from approval_reconciliation import reconcile_approval

# Assumes approval exists with id='test-approval-123'
result = reconcile_approval('test-approval-123')
print(f'Reconciliation: {result.status}')  # MATCH | MISMATCH | UNCLEAR
if result.status == 'MISMATCH':
    print(f'Reason: {result.explanation}')
"
```

### Automated Testing
```bash
pytest tests/test_audit.py -v --cov=execution_logger --cov-report=term
```

---

## 7. TEST_RESULTS_FORMAT

```json
{
  "worker_id": "004",
  "task": "Execution Audit Trail",
  "status": "pass|fail",
  "deliverables_created": [
    "wingman/execution_logger.py",
    "wingman/approval_reconciliation.py",
    "wingman/audit_schema.sql",
    "wingman/tests/test_audit.py"
  ],
  "test_results": {
    "unit_tests_pass": true,
    "coverage_percent": 96,
    "audit_log_write": "pass",
    "audit_immutability": "pass",
    "reconciliation_match": "pass",
    "reconciliation_mismatch_detection": "pass",
    "postgresql_fallback_to_jsonl": "pass"
  },
  "evidence": {
    "pytest_output": "14 passed, 0 failed",
    "audit_record_sample": "execution_id=abc, approval_id=test, command=docker ps",
    "reconciliation_test": "MATCH"
  },
  "duration_minutes": 30,
  "timestamp": "2026-01-07T...",
  "human_operator": "Mark",
  "ai_assistance": "Claude drafted code, human reviewed and applied"
}
```

---

## 8. TASK_CLASSIFICATION

- **Type:** IMPLEMENTATION (database schema + logging)
- **Complexity:** MEDIUM (PostgreSQL, append-only, reconciliation NLP)
- **Tool:** Python + PostgreSQL + SQL
- **Reasoning:** Database operations, NLP comparison
- **Human-Led:** YES - AI drafts code, human reviews ALL code before applying
- **AI Role:** Code generation assistant only, no autonomous execution

---

## 9. RETROSPECTIVE

**Time estimate:** 20 minutes (AI draft) + 10 minutes (human review/test) = 30 minutes total

**Actual time:** [To be filled after execution]

**Challenges:** [To be filled after execution]

**Database performance:** [To be filled - audit log write latency]

**Reconciliation accuracy:** [To be filled - does NLP comparison work?]

**Store in mem0:**
- Append-only audit log pattern
- PostgreSQL schema for execution audit
- Natural language reconciliation (approved vs executed)

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Manual audit log: N/A (doesn't exist)
- Current process: No post-execution verification

**Targets:**
- AI code generation: <20 minutes
- Human review/testing: <15 minutes
- Audit log write latency: <50ms
- Reconciliation batch job: <5 minutes for 100 approvals

**Quality:**
- 100% of executions logged (no missing records)
- Audit records immutable (verified with test)
- Reconciliation accuracy >90% (validated with human review)

**Monitoring:**
- Before: Verify PostgreSQL accessible, table created
- During: Track write latency, record count
- After: Verify no missing records, reconciliation works
- Degradation limit: If audit log fails, execution should still work (but alert)

---

## EXECUTION INSTRUCTIONS (HUMAN OPERATOR)

### Step 1: Request AI Code Draft
Ask AI to generate:
1. `execution_logger.py` (logs to PostgreSQL, fallback to JSONL)
2. `approval_reconciliation.py` (compares approved vs executed using Mistral)
3. `audit_schema.sql` (CREATE TABLE with appropriate indexes)
4. `tests/test_audit.py` (unit tests for logger and reconciliation)

### Step 2: Human Review
Review AI-generated code for:
- [ ] Append-only enforcement (no UPDATE/DELETE)
- [ ] All required fields captured
- [ ] Token hash stored (for replay detection)
- [ ] Timestamps are UTC
- [ ] Indexes on approval_id, worker_id, token_hash
- [ ] Reconciliation handles edge cases (no executions, multiple executions)

### Step 3: Apply Code (Manual)
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman
nano execution_logger.py
nano approval_reconciliation.py
nano audit_schema.sql
nano tests/test_audit.py
```

### Step 4: Create Database Table
```bash
psql -h localhost -p 6432 -U admin -d wingman_test -f audit_schema.sql
```

### Step 5: Run Tests
```bash
pytest tests/test_audit.py -v
```

### Step 6: Manual Validation
Follow TEST_PROCESS section, verify logging and reconciliation work.

### Step 7: Record Results
Create `ai-workers/results/worker-004-results.json`.

### Step 8: Gate Decision
- **PASS:** Proceed to next phase
- **FAIL:** Fix issues or rollback

---

**Wingman Validation Score:** N/A
**Human Approval Required:** YES
**Security Review Required:** MEDIUM (audit immutability critical)
**Status:** AWAITING HUMAN EXECUTION
