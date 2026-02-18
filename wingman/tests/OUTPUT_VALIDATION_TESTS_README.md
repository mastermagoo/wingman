# Output Validation Integration Tests

**Location**: `/Volumes/Data/ai_projects/wingman-system/wingman/tests/test_output_validation_integration.py`

**Purpose**: Comprehensive integration tests for Phase 6.1 Output Validation system as specified in `AAA_AI_WORKER_OUTPUT_VALIDATION_COMPLETE_PLAN.md` Section 2.5.

---

## Test Coverage

### Core Test Scenarios (13 tests)

1. **test_perfect_code_auto_approve**
   - Validates perfect Python code with good syntax, no security issues, all dependencies available
   - Expected: `decision=APPROVE`, `score >= 70`

2. **test_syntax_errors_auto_reject**
   - Validates Python code with syntax errors (missing parenthesis)
   - Expected: `decision=REJECT`, `blocking_issues` contains "Syntax error"

3. **test_security_issues_auto_reject**
   - Validates code with hardcoded API key
   - Expected: `decision=REJECT`, `severity=CRITICAL`

4. **test_missing_dependencies_manual_review**
   - Validates code importing missing library (`nltk`)
   - Expected: `decision=MANUAL_REVIEW`, missing dependencies listed

5. **test_test_failures_manual_review** (SKIPPED - requires docker exec)
   - Validates code with failing test suite
   - Expected: `decision=MANUAL_REVIEW`, failed test count > 0

6. **test_api_endpoint_integration** (SKIPPED - requires API server)
   - Tests POST `/output_validation/validate` endpoint
   - Verifies response structure and database insertion

7. **test_batch_validation**
   - Validates multiple files at once (3 files: 2 code + 1 test)
   - Verifies all files processed correctly

8. **test_empty_file_list**
   - Edge case: validation with empty file list
   - Expected: graceful handling

9. **test_nonexistent_file**
   - Edge case: validation with nonexistent file path
   - Expected: `decision=REJECT` or `MANUAL_REVIEW`

10. **test_mixed_quality_files**
    - Edge case: mix of good and bad files
    - Expected: `decision=REJECT` due to bad file

11-14. **test_individual_validators** (4 tests)
    - Tests SyntaxValidator in isolation
    - Tests OutputSecurityScanner in isolation
    - Validates valid and invalid code for each

15. **test_validation_performance**
    - Performance test: validates code completes within 30 seconds
    - Verifies no performance regressions

---

## Running Tests

### Option 1: Using pytest (Recommended)

```bash
# From host machine (if pytest installed)
cd /Volumes/Data/ai_projects/wingman-system/wingman
pytest tests/test_output_validation_integration.py -v

# Run specific test
pytest tests/test_output_validation_integration.py::TestPerfectCodeAutoApprove::test_perfect_code_auto_approve -v

# Run with output
pytest tests/test_output_validation_integration.py -v -s

# Skip slow/integration tests
pytest tests/test_output_validation_integration.py -v -m "not skip"
```

### Option 2: Using standalone test runner

```bash
# From host machine
cd /Volumes/Data/ai_projects/wingman-system/wingman
python tests/run_output_validation_tests.py

# Verbose mode
python tests/run_output_validation_tests.py --verbose

# Run specific test
python tests/run_output_validation_tests.py --test perfect
python tests/run_output_validation_tests.py --test syntax
python tests/run_output_validation_tests.py --test security
```

### Option 3: Inside Docker container (TEST environment)

```bash
# Copy files to container (if needed)
docker cp tests/test_output_validation_integration.py wingman-test-wingman-api-1:/app/tests/
docker cp tests/run_output_validation_tests.py wingman-test-wingman-api-1:/app/tests/

# Run tests inside container
docker exec -w /app wingman-test-wingman-api-1 python tests/run_output_validation_tests.py

# Or with pytest (if installed in container)
docker exec -w /app wingman-test-wingman-api-1 pytest tests/test_output_validation_integration.py -v
```

### Option 4: Direct Python execution (no pytest)

```bash
# Run as standalone script
cd /Volumes/Data/ai_projects/wingman-system/wingman
python tests/test_output_validation_integration.py
```

---

## Test Fixtures and Sample Code

The test file includes embedded sample code for various scenarios:

### Sample Code Files

1. **PERFECT_CODE**
   - Well-documented Python module with type hints, docstrings, error handling
   - Passes all validation checks
   - Expected result: APPROVE

2. **SYNTAX_ERROR_CODE**
   - Python code with missing closing parenthesis
   - Expected result: REJECT (syntax error)

3. **SECURITY_ISSUE_CODE**
   - Python code with hardcoded API key
   - Expected result: REJECT (CRITICAL security finding)

4. **MISSING_DEPENDENCY_CODE**
   - Python code importing `nltk` (not installed)
   - Expected result: MANUAL_REVIEW (missing dependency)

5. **GOOD_CODE_WITH_TESTS**
   - Calculator module with test suite
   - Expected result: APPROVE

6. **TEST_FILE_PASSING**
   - Test suite with all tests passing
   - Expected result: tests pass

7. **TEST_FILE_FAILING**
   - Test suite with 2/4 tests failing
   - Expected result: MANUAL_REVIEW (test failures)

---

## Prerequisites

### Required Components

1. **Output Validation Modules**:
   - `output_validation/syntax_validator.py`
   - `output_validation/output_security_scanner.py`
   - `output_validation/dependency_verifier.py`
   - `output_validation/test_executor.py`
   - `output_validation/output_composite_validator.py`

2. **Docker Containers**:
   - `wingman-test-wingman-api-1` (for TEST environment)
   - Container must be running for dependency verification tests

3. **Python Dependencies**:
   - pytest (optional, for pytest runner)
   - All dependencies from output validation modules

### Environment Setup

```bash
# Verify TEST container is running
docker ps | grep wingman-test

# Verify output validation modules exist
ls -la output_validation/

# Verify test files exist
ls -la tests/test_output_validation_integration.py
```

---

## Test Results Format

### Successful Test Output

```
============================================================
Running: test_perfect_code_auto_approve
============================================================
✅ Test passed - Score: 95, Decision: APPROVE
✅ PASSED: test_perfect_code_auto_approve
```

### Failed Test Output

```
============================================================
Running: test_syntax_errors_auto_reject
============================================================
❌ FAILED: test_syntax_errors_auto_reject
   Assertion Error: Expected REJECT, got APPROVE
```

### Summary Output

```
============================================================
TEST SUMMARY
============================================================
Total Tests:   13
✅ Passed:     11
❌ Failed:     1
⏭️  Skipped:    1
============================================================
```

---

## Skipped Tests

Some tests are skipped by default and require specific setup:

### test_test_failures_manual_review
- **Reason**: Requires docker container for test execution
- **Enable**: Remove `@pytest.mark.skip` decorator
- **Requirement**: Docker container must have pytest installed

### test_api_endpoint_integration
- **Reason**: Requires running API server
- **Enable**: Remove `@pytest.mark.skip` decorator
- **Requirement**: Wingman API server running on port 8101

---

## Expected Results

### Minimum Success Criteria

- ✅ At least 11/15 tests passing (skipped tests excluded)
- ✅ All core scenarios (1-4, 7-10) passing
- ✅ No blocking errors in test execution
- ✅ Validation completes within 30 seconds per test

### Known Limitations

1. **Dependency Verification**: May fail if Docker container not accessible
2. **Test Execution**: May fail if pytest not installed in container
3. **API Endpoint**: Skipped if API server not running

---

## Troubleshooting

### Issue: "No module named 'output_validation'"

**Solution**: Ensure Python path includes wingman directory
```bash
export PYTHONPATH="/Volumes/Data/ai_projects/wingman-system/wingman:$PYTHONPATH"
```

### Issue: "Docker container not found"

**Solution**: Start TEST environment
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman
docker compose -f docker-compose.yml -p wingman-test up -d
```

### Issue: "pytest not found"

**Solution**: Use standalone test runner
```bash
python tests/run_output_validation_tests.py
```

### Issue: "Permission denied" on temp files

**Solution**: Check temp directory permissions
```bash
ls -la /tmp/wingman_output_test_*
```

---

## Integration with CI/CD

### Automated Test Execution

```bash
# In CI pipeline
docker compose -f docker-compose.yml -p wingman-test up -d
sleep 10  # Wait for containers to be ready
docker exec wingman-test-wingman-api-1 python tests/run_output_validation_tests.py
```

### Test Reporting

Tests output JUnit-compatible results when using pytest:
```bash
pytest tests/test_output_validation_integration.py --junitxml=test-results.xml
```

---

## Maintenance

### Adding New Tests

1. Create test class inheriting from appropriate base class
2. Add test method with descriptive name
3. Include sample code fixtures
4. Document expected results
5. Update this README with new test description

### Updating Thresholds

Validation thresholds are configurable in `OutputCompositeValidator`:
- `auto_approve_threshold`: Default 70 (score >= 70 → APPROVE)
- `auto_reject_threshold`: Default 30 (score < 30 → REJECT)

---

## References

- **Design Document**: `docs/00-Strategic/AAA_AI_WORKER_OUTPUT_VALIDATION_COMPLETE_PLAN.md`
- **Architecture**: `docs/02-design/AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md`
- **Operations Guide**: `docs/03-operations/AAA_WINGMAN_OPERATIONS_DEPLOYMENT_RUNBOOK.md`

---

**Document Status**: COMPLETE
**Last Updated**: 2026-02-16
**Maintainer**: Wingman Development Team
