#!/bin/bash
# Test script for /output_validation/validate endpoint
# Usage: ./test_output_validation_endpoint.sh [test|prd]

set -euo pipefail

ENVIRONMENT="${1:-test}"

if [ "$ENVIRONMENT" = "prd" ]; then
    API_URL="http://localhost:5001"
else
    API_URL="http://localhost:8101"
fi

echo "Testing Output Validation Endpoint"
echo "Environment: $ENVIRONMENT"
echo "API URL: $API_URL"
echo ""

# Test 1: Valid request with syntax-valid Python files
echo "Test 1: Valid Python files (expected: APPROVE or MANUAL_REVIEW)"
echo "-----------------------------------------------------------"
curl -X POST "$API_URL/output_validation/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "TEST_WORKER_001",
    "task_name": "Test Semantic Analyzer",
    "generated_files": [
      "/Volumes/Data/ai_projects/wingman-system/wingman/validation/semantic_analyzer.py",
      "/Volumes/Data/ai_projects/wingman-system/wingman/tests/test_semantic_analyzer.py"
    ]
  }' | jq .

echo ""
echo ""

# Test 2: Missing files (expected: REJECT or ERROR)
echo "Test 2: Non-existent files (expected: REJECT or ERROR)"
echo "-------------------------------------------------------"
curl -X POST "$API_URL/output_validation/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "TEST_WORKER_002",
    "task_name": "Test Missing Files",
    "generated_files": [
      "/nonexistent/file1.py",
      "/nonexistent/file2.py"
    ]
  }' | jq .

echo ""
echo ""

# Test 3: Missing worker_id (expected: 400 Bad Request)
echo "Test 3: Missing generated_files (expected: 400 Bad Request)"
echo "------------------------------------------------------------"
curl -X POST "$API_URL/output_validation/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "TEST_WORKER_003",
    "task_name": "Test Missing Files Field"
  }' | jq .

echo ""
echo ""

# Test 4: Health check to verify output validation is available
echo "Test 4: Health check (verify output validation available)"
echo "----------------------------------------------------------"
curl -s "$API_URL/health" | jq '.validators'

echo ""
echo ""
echo "✅ All tests completed"
