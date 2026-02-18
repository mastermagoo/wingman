#!/bin/bash
set -euo pipefail

echo "🧪 Testing Instruction Validation Endpoint (Phase 6.3)"
echo "=================================================="
echo ""

BASE_URL="http://127.0.0.1:8101"

# Test 1: Health check
echo "Test 1: Health check (verify instruction_validation is available)"
curl -s "$BASE_URL/health" | jq '.validators.instruction_validation'
if [ "$(curl -s "$BASE_URL/health" | jq -r '.validators.instruction_validation')" = "available" ]; then
    echo "✅ Test 1 PASSED: instruction_validation is available"
else
    echo "❌ Test 1 FAILED: instruction_validation not available"
    exit 1
fi
echo ""

# Test 2: Validate complete instruction (Master Work Instruction)
echo "Test 2: Validate complete instruction (should APPROVE with score ≥80)"
MASTER_INSTRUCTION_PATH="/Volumes/Data/ai_projects/intel-system/docs/00-strategic/planning/MASTER_WORK_INSTRUCTION_THIN_SLICE_PILOT.md"
if [ -f "$MASTER_INSTRUCTION_PATH" ]; then
    INSTRUCTION_CONTENT=$(cat "$MASTER_INSTRUCTION_PATH" | jq -Rs .)
    RESPONSE=$(curl -s -X POST "$BASE_URL/instruction_validation/validate" \
        -H "Content-Type: application/json" \
        -d "{\"instruction_content\": $INSTRUCTION_CONTENT}")

    STATUS=$(echo "$RESPONSE" | jq -r '.status')
    SCORE=$(echo "$RESPONSE" | jq -r '.score')

    if [ "$STATUS" = "APPROVED" ] && [ "$SCORE" -ge 80 ]; then
        echo "✅ Test 2 PASSED: Status=$STATUS, Score=$SCORE"
    else
        echo "❌ Test 2 FAILED: Status=$STATUS, Score=$SCORE (expected APPROVED with score ≥80)"
        echo "$RESPONSE" | jq .
        exit 1
    fi
else
    echo "⚠️ Test 2 SKIPPED: Master Work Instruction file not found"
fi
echo ""

# Test 3: Validate incomplete instruction (should REJECT)
echo "Test 3: Validate incomplete instruction (should REJECT with score <50)"
INCOMPLETE_INSTRUCTION='# Incomplete Instruction\n\n## DELIVERABLES\nBuild something.\n\n## SUCCESS_CRITERIA\nIt works.'
RESPONSE=$(curl -s -X POST "$BASE_URL/instruction_validation/validate" \
    -H "Content-Type: application/json" \
    -d "{\"instruction_content\": \"$INCOMPLETE_INSTRUCTION\"}")

STATUS=$(echo "$RESPONSE" | jq -r '.status')
SCORE=$(echo "$RESPONSE" | jq -r '.score')
MISSING_COUNT=$(echo "$RESPONSE" | jq -r '.missing_sections | length')

if [ "$STATUS" = "REJECTED" ] && [ "$SCORE" -lt 50 ] && [ "$MISSING_COUNT" -ge 8 ]; then
    echo "✅ Test 3 PASSED: Status=$STATUS, Score=$SCORE, Missing=$MISSING_COUNT"
else
    echo "❌ Test 3 FAILED: Status=$STATUS, Score=$SCORE, Missing=$MISSING_COUNT"
    echo "$RESPONSE" | jq .
    exit 1
fi
echo ""

# Test 4: Validate medium-quality instruction (should MANUAL_REVIEW)
echo "Test 4: Validate medium-quality instruction (should MANUAL_REVIEW with score 50-79)"
MEDIUM_INSTRUCTION='# Medium Quality Instruction\n\n## DELIVERABLES\n- Build API endpoint for user management\n- Add database schema with migrations\n- Write comprehensive test suite with >80% coverage\n\n## SUCCESS_CRITERIA\n- All tests pass (pytest)\n- Code coverage >80%\n- No security vulnerabilities\n- Performance: <100ms response time\n\n## BOUNDARIES\n- Only modify backend code\n- No frontend changes\n- No breaking changes to existing API\n\n## DEPENDENCIES\n- PostgreSQL 15\n- Python 3.11\n- FastAPI framework\n\n## MITIGATION\n- Database backups before migrations\n- Rollback plan documented\n- Monitoring alerts configured\n\n## TEST_PROCESS\n```bash\npytest tests/ --cov=app --cov-report=html\n```\n\n## TEST_RESULTS_FORMAT\nJSON output with coverage report\n\n## TASK_CLASSIFICATION\nType: Backend Development\nRisk: Medium\nDuration: 4 hours\n\n## PERFORMANCE_REQUIREMENTS\n- Response time <100ms\n- Throughput: 1000 req/sec'

RESPONSE=$(curl -s -X POST "$BASE_URL/instruction_validation/validate" \
    -H "Content-Type: application/json" \
    -d "{\"instruction_content\": \"$MEDIUM_INSTRUCTION\"}")

STATUS=$(echo "$RESPONSE" | jq -r '.status')
SCORE=$(echo "$RESPONSE" | jq -r '.score')

if [ "$STATUS" = "MANUAL_REVIEW" ] && [ "$SCORE" -ge 50 ] && [ "$SCORE" -lt 80 ]; then
    echo "✅ Test 4 PASSED: Status=$STATUS, Score=$SCORE"
else
    echo "❌ Test 4 FAILED: Status=$STATUS, Score=$SCORE (expected MANUAL_REVIEW with score 50-79)"
    echo "$RESPONSE" | jq .
    exit 1
fi
echo ""

# Test 5: Error handling (missing both file and content)
echo "Test 5: Error handling (missing both instruction_file and instruction_content)"
RESPONSE=$(curl -s -X POST "$BASE_URL/instruction_validation/validate" \
    -H "Content-Type: application/json" \
    -d '{"worker_id": "test"}')

if echo "$RESPONSE" | jq -e '.error' > /dev/null; then
    echo "✅ Test 5 PASSED: Error returned for missing input"
else
    echo "❌ Test 5 FAILED: Should return error for missing input"
    echo "$RESPONSE" | jq .
    exit 1
fi
echo ""

echo "=================================================="
echo "🎉 All tests PASSED!"
echo "=================================================="
echo ""
echo "Summary:"
echo "- ✅ Health check: instruction_validation available"
echo "- ✅ Complete instruction: APPROVED (score ≥80)"
echo "- ✅ Incomplete instruction: REJECTED (score <50)"
echo "- ✅ Medium-quality instruction: MANUAL_REVIEW (score 50-79)"
echo "- ✅ Error handling: Proper error response"
echo ""
echo "Instruction Validation (Phase 6.3) is working correctly!"
