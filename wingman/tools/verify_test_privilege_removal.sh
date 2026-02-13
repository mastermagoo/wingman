#!/bin/bash
#
# Verify Privilege Separation in Wingman TEST Environment
# 
# Purpose: Ensure ONLY execution-gateway has Docker socket access.
# All other services must NOT have docker socket or DOCKER_HOST.
#
# Exit codes:
#   0 = All checks pass (privilege separation correct)
#   1 = Violation found (privilege separation broken)
#   2 = Cannot determine (services not running or inspection failed)
#

set -euo pipefail

PROJECT="wingman-test"
COMPOSE_FILE="docker-compose.yml"
COMPOSE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track violations
VIOLATIONS=0
WARNINGS=0

echo "🔍 Verifying privilege separation for ${PROJECT}..."
echo ""

# Check if services are running
if ! docker compose -f "${COMPOSE_DIR}/${COMPOSE_FILE}" -p "${PROJECT}" ps --format json 2>/dev/null | grep -q '"State":"running"'; then
    echo -e "${YELLOW}⚠️  No running services found. Start TEST stack first:${NC}"
    echo "   docker compose -f ${COMPOSE_DIR}/${COMPOSE_FILE} -p ${PROJECT} up -d"
    exit 2
fi

# Services that should NOT have docker socket
NON_PRIVILEGED_SERVICES=(
    "wingman-api"
    "telegram-bot"
    "watcher"
    "postgres"
)

# Service that SHOULD have docker socket
PRIVILEGED_SERVICE="execution-gateway"

# Function to check if container has docker socket
check_docker_socket() {
    local container_name="$1"
    local container_id
    
    # Get container ID
    container_id=$(docker compose -f "${COMPOSE_DIR}/${COMPOSE_FILE}" -p "${PROJECT}" ps -q "${container_name}" 2>/dev/null || echo "")
    
    if [ -z "${container_id}" ]; then
        echo -e "${YELLOW}⚠️  Container ${container_name} not found (may not be running)${NC}"
        return 2
    fi
    
    # Check for docker socket mount
    if docker inspect "${container_id}" --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} {{end}}' 2>/dev/null | grep -q "docker.sock"; then
        return 0  # Has socket
    else
        return 1  # No socket
    fi
}

# Function to check for DOCKER_HOST env var
check_docker_host() {
    local container_name="$1"
    local container_id
    
    container_id=$(docker compose -f "${COMPOSE_DIR}/${COMPOSE_FILE}" -p "${PROJECT}" ps -q "${container_name}" 2>/dev/null || echo "")
    
    if [ -z "${container_id}" ]; then
        return 2
    fi
    
    # Check environment variables
    if docker inspect "${container_id}" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep -q "^DOCKER_HOST="; then
        return 0  # Has DOCKER_HOST
    else
        return 1  # No DOCKER_HOST
    fi
}

# Check non-privileged services (should NOT have socket)
echo "📋 Checking non-privileged services (should NOT have docker socket)..."
for service in "${NON_PRIVILEGED_SERVICES[@]}"; do
    full_name="${PROJECT}-${service}-1"
    
    # Check docker socket
    if check_docker_socket "${service}"; then
        echo -e "${RED}❌ VIOLATION: ${full_name} has docker socket mount${NC}"
        VIOLATIONS=$((VIOLATIONS + 1))
    else
        echo -e "${GREEN}✅ ${full_name} has no docker socket${NC}"
    fi
    
    # Check DOCKER_HOST
    if check_docker_host "${service}"; then
        echo -e "${RED}❌ VIOLATION: ${full_name} has DOCKER_HOST env var${NC}"
        VIOLATIONS=$((VIOLATIONS + 1))
    else
        echo -e "${GREEN}✅ ${full_name} has no DOCKER_HOST${NC}"
    fi
done

echo ""

# Check privileged service (SHOULD have socket)
echo "📋 Checking privileged service (SHOULD have docker socket)..."
if check_docker_socket "${PRIVILEGED_SERVICE}"; then
    echo -e "${GREEN}✅ ${PROJECT}-${PRIVILEGED_SERVICE}-1 has docker socket (CORRECT)${NC}"
else
    echo -e "${RED}❌ VIOLATION: ${PROJECT}-${PRIVILEGED_SERVICE}-1 missing docker socket${NC}"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

echo ""

# Summary
if [ ${VIOLATIONS} -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED: Privilege separation is correct${NC}"
    echo "   - Only execution-gateway has docker socket"
    echo "   - All other services have no privileged access"
    exit 0
else
    echo -e "${RED}❌ FAILED: Found ${VIOLATIONS} violation(s)${NC}"
    echo "   Privilege separation is BROKEN. Fix docker-compose.yml to remove docker socket from non-gateway services."
    exit 1
fi
