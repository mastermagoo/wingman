#!/bin/bash
################################################################################
# Docker Wrapper Enforcement Verification Script
# Purpose: Verify Docker wrapper blocks destructive commands and allows safe ones
# Author: Claude Code (Phase 5)
# Date: 2026-02-14
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER_DIR="${SCRIPT_DIR}"

# Test counters
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test result tracking
FAILED_TESTS=()

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $*"; }
success() { echo -e "${GREEN}✅ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }
error() { echo -e "${RED}❌ $*${NC}"; }

test_start() {
    ((TESTS_TOTAL++))
    log "Test $TESTS_TOTAL: $1"
}

test_pass() {
    ((TESTS_PASSED++))
    success "$1"
}

test_fail() {
    ((TESTS_FAILED++))
    FAILED_TESTS+=("Test $TESTS_TOTAL: $1")
    error "$1"
}

################################################################################
# Test Setup
################################################################################

log "=== Docker Wrapper Enforcement Verification ==="
log "Wrapper directory: ${WRAPPER_DIR}"

# Backup original PATH
ORIGINAL_PATH="$PATH"

################################################################################
# Test 1: Wrapper exists and is executable
################################################################################

test_start "Verify wrapper script exists"
if [[ -x "${WRAPPER_DIR}/docker-wrapper.sh" ]]; then
    test_pass "Wrapper script exists and is executable"
else
    test_fail "Wrapper script not found or not executable: ${WRAPPER_DIR}/docker-wrapper.sh"
    exit 1
fi

################################################################################
# Test 2: Wrapper shim exists and is executable
################################################################################

test_start "Verify wrapper shim exists"
if [[ -x "${WRAPPER_DIR}/docker" ]]; then
    test_pass "Wrapper shim exists and is executable"
else
    test_fail "Wrapper shim not found or not executable: ${WRAPPER_DIR}/docker"
    exit 1
fi

################################################################################
# Test 3: Wrapper in PATH resolves correctly
################################################################################

test_start "Verify wrapper resolves when in PATH"
export PATH="${WRAPPER_DIR}:${ORIGINAL_PATH}"

DOCKER_CMD="$(command -v docker 2>/dev/null || echo '')"
if [[ "$DOCKER_CMD" == *"/tools/docker"* ]] || [[ "$DOCKER_CMD" == "${WRAPPER_DIR}/docker" ]]; then
    test_pass "Wrapper resolves correctly: $DOCKER_CMD"
else
    test_fail "Wrapper not resolving. Expected ${WRAPPER_DIR}/docker, got: $DOCKER_CMD"
fi

################################################################################
# Test 4: Set DOCKER_BIN for wrapper fallback
################################################################################

test_start "Set DOCKER_BIN for wrapper fallback"
for candidate in /usr/local/bin/docker /opt/homebrew/bin/docker "${HOME}/.orbstack/bin/docker" /usr/bin/docker; do
    if [[ -x "$candidate" ]]; then
        export DOCKER_BIN="$candidate"
        test_pass "DOCKER_BIN set to: $DOCKER_BIN"
        break
    fi
done

if [[ -z "${DOCKER_BIN:-}" ]]; then
    test_fail "Could not find real docker binary for DOCKER_BIN"
    exit 1
fi

################################################################################
# Test 5: Safe command passes through wrapper
################################################################################

test_start "Verify safe command (docker ps) works through wrapper"
if docker ps >/dev/null 2>&1; then
    test_pass "Safe command 'docker ps' passed through wrapper successfully"
else
    test_fail "Safe command 'docker ps' failed through wrapper"
fi

################################################################################
# Test 6: Safe command (docker version) works
################################################################################

test_start "Verify safe command (docker version) works through wrapper"
if docker version >/dev/null 2>&1; then
    test_pass "Safe command 'docker version' passed through wrapper successfully"
else
    test_fail "Safe command 'docker version' failed through wrapper"
fi

################################################################################
# Test 7: Destructive command is blocked (docker stop)
################################################################################

test_start "Verify destructive command (docker stop) is blocked"
output=$(docker stop fake-container 2>&1 || true)
if echo "$output" | grep -q "BLOCKED"; then
    test_pass "Destructive command 'docker stop' correctly blocked by wrapper"
else
    test_fail "Destructive command 'docker stop' NOT blocked by wrapper (output: ${output:0:100})"
fi

################################################################################
# Test 8: Destructive command is blocked (docker rm)
################################################################################

test_start "Verify destructive command (docker rm) is blocked"
output=$(docker rm fake-container 2>&1 || true)
if echo "$output" | grep -q "BLOCKED"; then
    test_pass "Destructive command 'docker rm' correctly blocked by wrapper"
else
    test_fail "Destructive command 'docker rm' NOT blocked by wrapper (output: ${output:0:100})"
fi

################################################################################
# Test 9: Destructive compose command is blocked (docker compose down)
################################################################################

test_start "Verify destructive compose command (docker compose down) is blocked"
output=$(docker compose down 2>&1 || true)
if echo "$output" | grep -q "BLOCKED"; then
    test_pass "Destructive command 'docker compose down' correctly blocked by wrapper"
else
    test_fail "Destructive command 'docker compose down' NOT blocked by wrapper (output: ${output:0:100})"
fi

################################################################################
# Test 10: Safe compose command works (docker compose ps)
################################################################################

test_start "Verify safe compose command (docker compose ps) works"
# This may fail if no compose file in current directory, but should NOT be blocked
output=$(docker compose ps 2>&1 || true)
if echo "$output" | grep -q "BLOCKED"; then
    test_fail "Safe command 'docker compose ps' incorrectly blocked by wrapper"
elif echo "$output" | grep -qi "no configuration file"; then
    test_pass "Safe command 'docker compose ps' passed through wrapper (no config file is expected)"
else
    test_pass "Safe command 'docker compose ps' passed through wrapper successfully"
fi

################################################################################
# Test 11: Wrapper without PATH (direct invocation)
################################################################################

test_start "Verify wrapper works when invoked directly"
if "${WRAPPER_DIR}/docker-wrapper.sh" ps >/dev/null 2>&1; then
    test_pass "Wrapper works when invoked directly"
else
    test_fail "Wrapper failed when invoked directly"
fi

################################################################################
# Test 12: Bypass attempt with absolute path (awareness test)
################################################################################

test_start "Verify absolute path bypass is possible (known limitation)"
# This test demonstrates the bypass - we document it as prohibited
if [[ -x "$DOCKER_BIN" ]]; then
    if "$DOCKER_BIN" ps >/dev/null 2>&1; then
        warn "Absolute path bypass is possible: $DOCKER_BIN ps (DOCUMENTED LIMITATION)"
        test_pass "Bypass test passed (limitation documented in CLAUDE.md)"
    else
        test_fail "Unexpected: Real docker binary doesn't work"
    fi
else
    warn "Cannot test bypass: DOCKER_BIN not executable"
fi

################################################################################
# Summary
################################################################################

# Restore original PATH
export PATH="$ORIGINAL_PATH"

log ""
log "=== Verification Summary ==="
log "Total tests: $TESTS_TOTAL"
success "Passed: $TESTS_PASSED"
if [[ $TESTS_FAILED -gt 0 ]]; then
    error "Failed: $TESTS_FAILED"
    log ""
    error "Failed tests:"
    for failed_test in "${FAILED_TESTS[@]}"; do
        echo "  - $failed_test"
    done
    log ""
    exit 1
else
    log ""
    success "ALL TESTS PASSED!"
    log ""
    log "Docker wrapper enforcement is working correctly."
    log ""
    log "Next steps:"
    log "  1. Add wrapper to shell profile for permanent setup"
    log "  2. Verify all deployment scripts use wrapper"
    log "  3. Document bypass prevention in code reviews"
    log ""
    exit 0
fi
