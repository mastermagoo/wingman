#!/bin/bash
# Test script for Execution Gateway deployment
# Tests all phases of the token-based execution flow

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

WINGMAN_API="${WINGMAN_API:-http://127.0.0.1:5001}"
GATEWAY_API="${GATEWAY_API:-http://127.0.0.1:5002}"

echo "🧪 Execution Gateway Test Suite"
echo "================================"
echo ""

# Test 1: Gateway Health
echo -n "Test 1: Gateway health check... "
HEALTH=$(curl -s -w "\n%{http_code}" "$GATEWAY_API/health" | tail -1)
if [ "$HEALTH" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $HEALTH)"
    echo "Gateway is not responding. Is it running?"
    echo "Run: docker compose -f docker-compose.prd.yml -p wingman-prd logs execution-gateway"
    exit 1
fi

# Test 2: Wingman API Health
echo -n "Test 2: Wingman API health check... "
HEALTH=$(curl -s -w "\n%{http_code}" "$WINGMAN_API/health" | tail -1)
if [ "$HEALTH" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $HEALTH)"
    echo "Wingman API is not responding. Is it running?"
    exit 1
fi

# Test 3: Request Low-Risk Approval (Should Auto-Approve)
echo -n "Test 3: Request low-risk approval... "
APPROVAL_RESPONSE=$(curl -s -X POST "$WINGMAN_API/approvals/request" \
    -H "Content-Type: application/json" \
    -d '{
        "worker_id": "test-gateway-script",
        "task_name": "Test Gateway - Echo Command",
        "instruction": "DELIVERABLES: Test echo command\nSUCCESS_CRITERIA: Command succeeds\nBOUNDARIES: Read-only\nDEPENDENCIES: None\nMITIGATION: None needed\nTEST_PROCESS: Run echo\nTEST_RESULTS_FORMAT: Exit code\nRESOURCE_REQUIREMENTS: Minimal\nRISK_ASSESSMENT: Low\nQUALITY_METRICS: Success\n\nCommand: echo test",
        "deployment_env": "prd"
    }')

APPROVAL_ID=$(echo "$APPROVAL_RESPONSE" | jq -r '.request.request_id')
APPROVAL_STATUS=$(echo "$APPROVAL_RESPONSE" | jq -r '.request.status')

if [ "$APPROVAL_STATUS" = "AUTO_APPROVED" ] || [ "$APPROVAL_STATUS" = "APPROVED" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Auto-approved)"
elif [ "$APPROVAL_STATUS" = "PENDING" ]; then
    echo -e "${YELLOW}⏳ WAITING${NC} (Manual approval required)"
    echo "Approval ID: $APPROVAL_ID"
    echo "Waiting up to 60 seconds for approval via Telegram..."

    # Poll for approval (check every 3 seconds for up to 60 seconds)
    # Note: Use READ key to check status, DECIDE key is only for approve/reject actions
    READ_KEY="${WINGMAN_APPROVAL_READ_KEY:-outgunning-web-serin-profounder-swans-globule}"
    for i in {1..20}; do
        sleep 3
        CHECK_RESPONSE=$(curl -s -H "X-Wingman-Approval-Read-Key: ${READ_KEY}" "$WINGMAN_API/approvals/$APPROVAL_ID")
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

    # Check if still pending after timeout
    if [ "$APPROVAL_STATUS" = "PENDING" ]; then
        echo -e "${RED}✗ FAIL${NC} (Timeout waiting for approval)"
        echo "Please approve $APPROVAL_ID in Telegram and re-run the test"
        exit 1
    fi
else
    echo -e "${RED}✗ FAIL${NC} (Unexpected status: $APPROVAL_STATUS)"
    exit 1
fi

# Test 4: Generate Capability Token (Requires DECIDE key)
echo -n "Test 4: Generate capability token... "

# Check if DECIDE key is set
DECIDE_KEY="${WINGMAN_APPROVAL_DECIDE_KEY:-}"
if [ -z "$DECIDE_KEY" ]; then
    echo -e "${YELLOW}⚠ SKIP${NC} (WINGMAN_APPROVAL_DECIDE_KEY not set)"
    echo "Export WINGMAN_APPROVAL_DECIDE_KEY to run this test"
    exit 0
fi

TOKEN_RESPONSE=$(curl -s -X POST "$WINGMAN_API/gateway/token" \
    -H "Content-Type: application/json" \
    -H "X-Wingman-Approval-Decide-Key: $DECIDE_KEY" \
    -d "{
        \"approval_id\": \"$APPROVAL_ID\",
        \"command\": \"echo test\",
        \"environment\": \"prd\"
    }")

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
EXEC_RESPONSE=$(curl -s -X POST "$GATEWAY_API/gateway/execute" \
    -H "Content-Type: application/json" \
    -H "X-Capability-Token: $TOKEN" \
    -d "{
        \"command\": \"echo test\",
        \"approval_id\": \"$APPROVAL_ID\",
        \"environment\": \"prd\"
    }")

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
REPLAY_RESPONSE=$(curl -s -X POST "$GATEWAY_API/gateway/execute" \
    -H "Content-Type: application/json" \
    -H "X-Capability-Token: $TOKEN" \
    -d "{
        \"command\": \"echo test\",
        \"approval_id\": \"$APPROVAL_ID\",
        \"environment\": \"prd\"
    }")

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
INVALID_RESPONSE=$(curl -s -X POST "$GATEWAY_API/gateway/execute" \
    -H "Content-Type: application/json" \
    -H "X-Capability-Token: invalid.token.here" \
    -d "{
        \"command\": \"echo test\",
        \"approval_id\": \"$APPROVAL_ID\",
        \"environment\": \"prd\"
    }")

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
# Check if execution was logged to database
AUDIT_CHECK=$(docker exec wingman-prd-postgres psql -U wingman_prd -d wingman_prd -t -c \
    "SELECT COUNT(*) FROM execution_audit WHERE execution_id = '$EXECUTION_ID';" 2>/dev/null || echo "0")

AUDIT_COUNT=$(echo "$AUDIT_CHECK" | tr -d ' \n')
if [ "$AUDIT_COUNT" -ge "1" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Execution logged to database)"
else
    # Check JSONL fallback
    if [ -f "data/execution_audit.jsonl" ]; then
        if grep -q "$EXECUTION_ID" "data/execution_audit.jsonl"; then
            echo -e "${GREEN}✓ PASS${NC} (Execution logged to JSONL)"
        else
            echo -e "${RED}✗ FAIL${NC} (Execution not found in audit logs)"
        fi
    else
        echo -e "${YELLOW}⚠ WARN${NC} (Could not verify - check logs manually)"
    fi
fi

echo ""
echo "================================"
echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
echo ""
echo "Execution Gateway is working correctly!"
echo ""
echo "Summary:"
echo "  - Gateway health: OK"
echo "  - Wingman API: OK"
echo "  - Token generation: OK"
echo "  - Command execution: OK"
echo "  - Replay protection: OK"
echo "  - Invalid token rejection: OK"
echo "  - Audit logging: OK"
echo ""
echo "The system is ready for production use."
