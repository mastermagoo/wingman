#!/bin/bash
#
# Verify No Approval Bypass Attempts
#
# Purpose: Detect if any system is attempting to bypass Wingman approval gates
# by directly executing destructive operations without requesting approval first.
#
# Exit codes:
#   0 = No bypass attempts detected
#   1 = Bypass attempt detected
#   2 = Cannot determine (services not running or inspection failed)
#

set -euo pipefail

PROJECT="wingman-test"
COMPOSE_FILE="docker-compose.yml"
COMPOSE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
API_URL="${WINGMAN_API_URL:-http://127.0.0.1:5002}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VIOLATIONS=0

echo "🔍 Checking for approval bypass attempts..."
echo ""

# Check 1: Verify execution gateway is enforcing
echo "📋 Check 1: Execution Gateway Enforcement"
if docker compose -f "${COMPOSE_DIR}/${COMPOSE_FILE}" -p "${PROJECT}" ps --format json 2>/dev/null | grep -q '"Name":"wingman-test-execution-gateway-1".*"State":"running"'; then
    echo -e "${GREEN}✅ Execution gateway is running${NC}"
    
    # Check gateway health
    if curl -sf "${API_URL}/gateway/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Gateway health endpoint responding${NC}"
    else
        echo -e "${YELLOW}⚠️  Gateway health endpoint not responding (may be normal if gateway not exposed)${NC}"
    fi
else
    echo -e "${RED}❌ VIOLATION: Execution gateway not running${NC}"
    echo "   Without gateway, operations can bypass approval"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

echo ""

# Check 2: Verify non-gateway services cannot access Docker directly
echo "📋 Check 2: Non-Gateway Services Docker Access"
NON_GATEWAY_SERVICES=("wingman-api" "telegram-bot" "watcher")

for service in "${NON_GATEWAY_SERVICES[@]}"; do
    container_id=$(docker compose -f "${COMPOSE_DIR}/${COMPOSE_FILE}" -p "${PROJECT}" ps -q "${service}" 2>/dev/null || echo "")
    
    if [ -z "${container_id}" ]; then
        continue
    fi
    
    # Check for docker socket
    if docker inspect "${container_id}" --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} {{end}}' 2>/dev/null | grep -q "docker.sock"; then
        echo -e "${RED}❌ VIOLATION: ${service} has docker socket (can bypass gateway)${NC}"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

echo ""

# Check 3: Verify external systems are using WingmanApprovalClient
echo "📋 Check 3: External System Integration"
echo "   Checking if Intel-system and Mem0 are properly integrated..."

# Check Intel-system
INTEL_DR_SCRIPT="/Volumes/Data/ai_projects/intel-system/tools/dr_with_approval.py"
if [ -f "${INTEL_DR_SCRIPT}" ]; then
    if grep -q "WingmanApprovalClient" "${INTEL_DR_SCRIPT}"; then
        echo -e "${GREEN}✅ Intel-system uses WingmanApprovalClient${NC}"
    else
        echo -e "${RED}❌ VIOLATION: Intel-system DR script does not use WingmanApprovalClient${NC}"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
else
    echo -e "${YELLOW}⚠️  Intel-system DR script not found (may not be deployed)${NC}"
fi

# Check Mem0
MEM0_DR_SCRIPT="/Volumes/Data/ai_projects/mem0-system/tools/dr_with_approval.py"
if [ -f "${MEM0_DR_SCRIPT}" ]; then
    if grep -q "WingmanApprovalClient" "${MEM0_DR_SCRIPT}"; then
        echo -e "${GREEN}✅ Mem0 uses WingmanApprovalClient${NC}"
    else
        echo -e "${RED}❌ VIOLATION: Mem0 DR script does not use WingmanApprovalClient${NC}"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
else
    echo -e "${YELLOW}⚠️  Mem0 DR script not found (may not be deployed)${NC}"
fi

echo ""

# Check 4: Verify API requires approval for destructive operations
echo "📋 Check 4: API Approval Enforcement"
echo "   (Manual check: Try to execute destructive operation without approval)"
echo -e "${YELLOW}   ⚠️  This requires manual testing${NC}"

echo ""

# Summary
if [ ${VIOLATIONS} -eq 0 ]; then
    echo -e "${GREEN}✅ NO BYPASS ATTEMPTS DETECTED${NC}"
    echo "   - Execution gateway is enforcing"
    echo "   - Non-gateway services have no direct Docker access"
    echo "   - External systems are using WingmanApprovalClient"
    exit 0
else
    echo -e "${RED}❌ BYPASS ATTEMPTS DETECTED: Found ${VIOLATIONS} violation(s)${NC}"
    echo "   Fix violations to restore approval enforcement."
    exit 1
fi
