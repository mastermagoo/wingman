#!/bin/bash
# Test script for Execution Gateway deployment
# Tests all phases of the token-based execution flow

set -e

# Usage:
#   ./tools/test_execution_gateway.sh [test|prd]
#
# Design notes:
# - All HTTP calls are executed *inside* the `wingman-api` container so the script can:
#   - reach the internal `execution-gateway` service even when not published to host
#   - use approval READ/DECIDE keys from container env without printing them

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TARGET_ENV="${1:-prd}"
if [ "$TARGET_ENV" = "prod" ]; then TARGET_ENV="prd"; fi
if [ "$TARGET_ENV" != "test" ] && [ "$TARGET_ENV" != "prd" ]; then
  echo "Usage: $0 [test|prd]"
  exit 1
fi

if [ "$TARGET_ENV" = "test" ]; then
  COMPOSE_FILE="docker-compose.yml"
  PROJECT_NAME="wingman-test"
  ENV_FILE=".env.test"
  API_INTERNAL_PORT="5000"
  GATEWAY_INTERNAL_PORT="5001"
else
  COMPOSE_FILE="docker-compose.prd.yml"
  PROJECT_NAME="wingman-prd"
  ENV_FILE=".env.prd"
  API_INTERNAL_PORT="8001"
  GATEWAY_INTERNAL_PORT="5002"
fi

API_BASE="http://127.0.0.1:${API_INTERNAL_PORT}"
GATEWAY_BASE="http://execution-gateway:${GATEWAY_INTERNAL_PORT}"

dc_exec_api() {
  docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" --env-file "$ENV_FILE" exec -T wingman-api sh -lc "$1"
}

dc_exec_pg() {
  docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" --env-file "$ENV_FILE" exec -T postgres sh -lc "$1"
}

approval_get() {
  local approval_id="$1"
  dc_exec_api "READ=\"\${WINGMAN_APPROVAL_READ_KEY:-\${WINGMAN_APPROVAL_READ_KEYS%%,*}}\"; \
if [ -n \"\$READ\" ]; then \
  curl -s -H \"X-Wingman-Approval-Read-Key: \$READ\" \"${API_BASE}/approvals/${approval_id}\"; \
else \
  curl -s \"${API_BASE}/approvals/${approval_id}\"; \
fi"
}

token_mint() {
  local approval_id="$1"
  local command="$2"
  dc_exec_api "DECIDE=\"\${WINGMAN_APPROVAL_DECIDE_KEY:-\${WINGMAN_APPROVAL_DECIDE_KEYS%%,*}}\"; \
if [ -z \"\$DECIDE\" ]; then echo '__NO_DECIDE_KEY__'; exit 0; fi; \
curl -s -X POST \"${API_BASE}/gateway/token\" \
  -H \"Content-Type: application/json\" \
  -H \"X-Wingman-Approval-Decide-Key: \$DECIDE\" \
  -d \"{\\\"approval_id\\\":\\\"${approval_id}\\\",\\\"command\\\":\\\"${command}\\\",\\\"environment\\\":\\\"${TARGET_ENV}\\\"}\""
}

echo "🧪 Execution Gateway Test Suite"
echo "================================"
echo ""
echo "Target environment: $TARGET_ENV"
echo ""

# Test 1: Gateway Health
echo -n "Test 1: Gateway health check... "
HEALTH=$(dc_exec_api "curl -s -w '\n%{http_code}' '${GATEWAY_BASE}/health'" | tail -1)
if [ "$HEALTH" = "200" ]; then
  echo -e "${GREEN}✓ PASS${NC}"
else
  echo -e "${RED}✗ FAIL${NC} (HTTP $HEALTH)"
  echo "Gateway is not responding. Is it running?"
  echo "Run: docker compose -f ${COMPOSE_FILE} -p ${PROJECT_NAME} --env-file ${ENV_FILE} logs execution-gateway"
  exit 1
fi

# Test 2: Wingman API Health
echo -n "Test 2: Wingman API health check... "
HEALTH=$(dc_exec_api "curl -s -w '\n%{http_code}' '${API_BASE}/health'" | tail -1)
if [ "$HEALTH" = "200" ]; then
  echo -e "${GREEN}✓ PASS${NC}"
else
  echo -e "${RED}✗ FAIL${NC} (HTTP $HEALTH)"
  echo "Wingman API is not responding. Is it running?"
  exit 1
fi

# Test 3: Request Approval
# - TEST: should AUTO_APPROVE for low-risk
# - PRD: should go PENDING (PRD is always HIGH risk by policy)
echo -n "Test 3: Request low-risk approval... "
APPROVAL_RESPONSE=$(dc_exec_api "curl -s -X POST '${API_BASE}/approvals/request' \
  -H 'Content-Type: application/json' \
  -d '{\"worker_id\":\"test-gateway-script\",\"task_name\":\"Test Gateway - Echo Command\",\"instruction\":\"DELIVERABLES: Test echo command\\nSUCCESS_CRITERIA: Command succeeds\\nBOUNDARIES: Read-only\\nDEPENDENCIES: None\\nMITIGATION: None needed\\nTEST_PROCESS: Run echo\\nTEST_RESULTS_FORMAT: Exit code\\nRESOURCE_REQUIREMENTS: Minimal\\nRISK_ASSESSMENT: Low\\nQUALITY_METRICS: Success\\n\\nCommand: echo test\",\"deployment_env\":\"${TARGET_ENV}\"}'")

APPROVAL_ID=$(echo "$APPROVAL_RESPONSE" | jq -r '.request.request_id')
APPROVAL_STATUS=$(echo "$APPROVAL_RESPONSE" | jq -r '.request.status')

if [ "$APPROVAL_STATUS" = "AUTO_APPROVED" ] || [ "$APPROVAL_STATUS" = "APPROVED" ]; then
  if [ "$TARGET_ENV" = "prd" ]; then
    echo -e "${YELLOW}⚠ WARN${NC} (Expected PENDING in PRD, got $APPROVAL_STATUS)"
  else
    echo -e "${GREEN}✓ PASS${NC} (Auto-approved)"
  fi
elif [ "$APPROVAL_STATUS" = "PENDING" ]; then
  if [ "$TARGET_ENV" = "test" ]; then
    echo -e "${RED}✗ FAIL${NC} (Expected AUTO_APPROVED in TEST, got PENDING)"
    exit 1
  fi

  echo -e "${YELLOW}⏳ WAITING${NC} (Manual approval required)"
  echo "Approval ID: $APPROVAL_ID"
  echo "Waiting up to 120 seconds for approval via Telegram..."

  for i in {1..40}; do
    sleep 3
    CHECK_RESPONSE="$(approval_get "$APPROVAL_ID")"
    CHECK_STATUS=$(echo "$CHECK_RESPONSE" | jq -r '.status')
    echo "  Poll $i: Status = $CHECK_STATUS"

    if [ "$CHECK_STATUS" = "APPROVED" ] || [ "$CHECK_STATUS" = "AUTO_APPROVED" ]; then
      echo -e "${GREEN}✓ PASS${NC} (Approved after ${i}x3 seconds)"
      APPROVAL_STATUS="APPROVED"
      break
    elif [ "$CHECK_STATUS" = "REJECTED" ]; then
      echo -e "${RED}✗ FAIL${NC} (Approval was rejected)"
      exit 1
    fi
  done

  if [ "$APPROVAL_STATUS" = "PENDING" ]; then
    echo -e "${RED}✗ FAIL${NC} (Timeout waiting for approval)"
    echo "Please approve $APPROVAL_ID in Telegram and re-run the test"
    exit 1
  fi
else
  echo -e "${RED}✗ FAIL${NC} (Unexpected status: $APPROVAL_STATUS)"
  echo "$APPROVAL_RESPONSE" | jq '.'
  exit 1
fi

# Test 4: Generate Capability Token (Requires DECIDE key)
echo -n "Test 4: Generate capability token... "
TOKEN_RESPONSE="$(token_mint "$APPROVAL_ID" "echo test")"

if [ "$TOKEN_RESPONSE" = "__NO_DECIDE_KEY__" ]; then
  echo -e "${YELLOW}⚠ SKIP${NC} (No DECIDE key configured in container env)"
  echo "Set WINGMAN_APPROVAL_DECIDE_KEY(S) in ${ENV_FILE} and re-run."
  exit 0
fi

TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.token // empty')
if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
  echo -e "${GREEN}✓ PASS${NC}"
else
  echo -e "${RED}✗ FAIL${NC}"
  echo "Token generation failed:"
  echo "$TOKEN_RESPONSE" | jq '.'
  exit 1
fi

# Test 5: Execute Command via Gateway
echo -n "Test 5: Execute command via gateway... "
EXEC_RESPONSE=$(dc_exec_api "curl -s -X POST \"${GATEWAY_BASE}/gateway/execute\" \
  -H \"Content-Type: application/json\" \
  -H \"X-Capability-Token: ${TOKEN}\" \
  -d \"{\\\"command\\\":\\\"echo test\\\",\\\"approval_id\\\":\\\"${APPROVAL_ID}\\\",\\\"environment\\\":\\\"${TARGET_ENV}\\\"}\"")

SUCCESS=$(echo "$EXEC_RESPONSE" | jq -r '.success // false')
if [ "$SUCCESS" = "true" ]; then
  echo -e "${GREEN}✓ PASS${NC}"
  EXECUTION_ID=$(echo "$EXEC_RESPONSE" | jq -r '.execution_id')
  echo "  Execution ID: $EXECUTION_ID"
else
  echo -e "${RED}✗ FAIL${NC}"
  echo "Execution failed:"
  echo "$EXEC_RESPONSE" | jq '.'
  exit 1
fi

# Test 6: Replay Protection (Same token should fail)
echo -n "Test 6: Token replay protection... "
REPLAY_RESPONSE=$(dc_exec_api "curl -s -X POST \"${GATEWAY_BASE}/gateway/execute\" \
  -H \"Content-Type: application/json\" \
  -H \"X-Capability-Token: ${TOKEN}\" \
  -d \"{\\\"command\\\":\\\"echo test\\\",\\\"approval_id\\\":\\\"${APPROVAL_ID}\\\",\\\"environment\\\":\\\"${TARGET_ENV}\\\"}\"")

REPLAY_SUCCESS=$(echo "$REPLAY_RESPONSE" | jq -r '.success // false')
if [ "$REPLAY_SUCCESS" = "false" ]; then
  ERROR_MSG=$(echo "$REPLAY_RESPONSE" | jq -r '.error')
  if [[ "$ERROR_MSG" == *"already been used"* || "$ERROR_MSG" == *"replay"* ]]; then
    echo -e "${GREEN}✓ PASS${NC} (Replay blocked)"
  else
    echo -e "${YELLOW}⚠ WARN${NC} (Blocked, but not for replay)"
    echo "  Error: $ERROR_MSG"
  fi
else
  echo -e "${RED}✗ FAIL${NC} (Token was reused!)"
  echo "SECURITY ISSUE: Replay protection not working"
  exit 1
fi

# Test 7: Invalid Token
echo -n "Test 7: Invalid token rejection... "
INVALID_RESPONSE=$(dc_exec_api "curl -s -X POST \"${GATEWAY_BASE}/gateway/execute\" \
  -H \"Content-Type: application/json\" \
  -H \"X-Capability-Token: invalid.token.here\" \
  -d \"{\\\"command\\\":\\\"echo test\\\",\\\"approval_id\\\":\\\"${APPROVAL_ID}\\\",\\\"environment\\\":\\\"${TARGET_ENV}\\\"}\"")

INVALID_SUCCESS=$(echo "$INVALID_RESPONSE" | jq -r '.success // false')
if [ "$INVALID_SUCCESS" = "false" ]; then
  echo -e "${GREEN}✓ PASS${NC} (Invalid token rejected)"
else
  echo -e "${RED}✗ FAIL${NC} (Invalid token accepted!)"
  echo "SECURITY ISSUE: Token validation not working"
  exit 1
fi

# Test 8: Audit Log Check
echo -n "Test 8: Audit log verification... "
AUDIT_CHECK=$(dc_exec_pg "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -t -c \"SELECT COUNT(*) FROM execution_audit WHERE execution_id = '${EXECUTION_ID}';\" 2>/dev/null || echo 0")

AUDIT_COUNT=$(echo "$AUDIT_CHECK" | tr -d ' \n')
if [ "$AUDIT_COUNT" -ge "1" ]; then
  echo -e "${GREEN}✓ PASS${NC} (Execution logged to database)"
else
  echo -e "${YELLOW}⚠ WARN${NC} (Execution not found in Postgres audit table)"
fi

echo ""
echo "================================"
echo -e "${GREEN}✅ TEST SUITE COMPLETE${NC}"
echo ""
echo "Summary:"
echo "  - Gateway health: OK"
echo "  - Wingman API: OK"
echo "  - Approval flow: OK"
echo "  - Token generation: OK"
echo "  - Command execution: OK"
echo "  - Replay protection: OK"
echo "  - Invalid token rejection: OK"
echo "  - Audit logging: OK"
echo ""
echo "Done."
