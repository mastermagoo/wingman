# Output Validation Integration Tests - Quick Start

**TL;DR**: Run tests with one command, no setup required.

---

## Quick Run (Copy-Paste)

```bash
# From wingman directory
cd /Volumes/Data/ai_projects/wingman-system/wingman

# Run all tests (no pytest required)
python tests/run_output_validation_tests.py

# Run specific test
python tests/run_output_validation_tests.py --test perfect

# Verbose mode
python tests/run_output_validation_tests.py --verbose
```

---

## Expected Output

```
============================================================
WINGMAN OUTPUT VALIDATION INTEGRATION TESTS
============================================================

============================================================
Running: test_perfect_code_auto_approve
============================================================
✅ Test passed - Score: 95, Decision: APPROVE
✅ PASSED: test_perfect_code_auto_approve

[... more tests ...]

============================================================
TEST SUMMARY
============================================================
Total Tests:   13
✅ Passed:     13
❌ Failed:     0
⏭️  Skipped:    0
============================================================
✅ ALL TESTS PASSED!
```

---

## Available Tests

| Filter | Tests Run | Description |
|--------|-----------|-------------|
| `--test perfect` | 1 | Perfect code auto-approve |
| `--test syntax` | 2 | Syntax error detection |
| `--test security` | 2 | Security issue detection |
| `--test batch` | 1 | Batch validation (3 files) |
| `--test edge` | 3 | Edge cases |
| `--test individual` | 4 | Individual validators |
| (no filter) | 13 | All tests |

---

## Files Created

- ✅ `test_output_validation_integration.py` (787 lines) - Main test suite
- ✅ `run_output_validation_tests.py` (329 lines) - Standalone runner
- ✅ `OUTPUT_VALIDATION_TESTS_README.md` - Full documentation
- ✅ `OUTPUT_VALIDATION_TEST_SUMMARY.md` - Test results
- ✅ `INTEGRATION_TESTS_DELIVERABLE_REPORT.md` - Complete report

---

## Troubleshooting

### "No module named 'output_validation'"
```bash
# Set PYTHONPATH
export PYTHONPATH="/Volumes/Data/ai_projects/wingman-system/wingman:$PYTHONPATH"
python tests/run_output_validation_tests.py
```

### "Docker container not found"
Tests will run anyway - docker is optional for most tests.

---

## Smoke Test (30 seconds)

```bash
python -c "
import sys
sys.path.insert(0, '.')
from tests.test_output_validation_integration import OutputCompositeValidator
validator = OutputCompositeValidator()
print('✅ Tests are ready to run!')
"
```

---

## Full Documentation

See `OUTPUT_VALIDATION_TESTS_README.md` for complete details.

---

**Status**: ✅ READY TO USE
**Last Updated**: 2026-02-16
