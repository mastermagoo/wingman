#!/bin/bash
#
# Docker Wrapper Script - Blocks Destructive Commands
# Purpose: Prevent AI assistants from executing destructive docker commands without Wingman approval
#
# Usage: This script intercepts docker commands and blocks destructive operations
# Installation: Add to PATH before actual docker binary
#

set -euo pipefail

# Destructive commands that require Wingman approval
DESTRUCTIVE_COMMANDS=(
    "stop"
    "rm"
    "down"
    "kill"
    "restart"
    "build"
    "compose down"
    "compose stop"
    "compose rm"
    "compose kill"
    "system prune"
    "volume rm"
    "network rm"
    "image rm"
    "container rm"
    "container stop"
    "container kill"
)

# Get full command string
FULL_CMD="$*"
CMD_LOWER=$(echo "$FULL_CMD" | tr '[:upper:]' '[:lower:]')

# Check if command is destructive
# Check first argument (main command) and full command string
FIRST_ARG="${1:-}"
FIRST_ARG_LOWER=$(echo "$FIRST_ARG" | tr '[:upper:]' '[:lower:]')

for destructive_cmd in "${DESTRUCTIVE_COMMANDS[@]}"; do
    # Check if first argument matches destructive command
    if [[ "$FIRST_ARG_LOWER" == "$destructive_cmd" ]] || [[ " $CMD_LOWER " == *" $destructive_cmd "* ]]; then
        echo "❌ BLOCKED: Destructive docker command requires Wingman approval" >&2
        echo "" >&2
        echo "   Command: docker $*" >&2
        echo "   Reason: '$destructive_cmd' is a destructive operation" >&2
        echo "" >&2
        echo "   Action Required:" >&2
        echo "   1. Submit approval request to Wingman API" >&2
        echo "      POST http://127.0.0.1:8101/approvals/request (TEST) or :5001 (PRD)" >&2
        echo "   2. Wait for approval via Telegram" >&2
        echo "   3. Execute via Wingman Execution Gateway with capability token" >&2
        echo "" >&2
        echo "   See: wingman/docs/PRD_DEPLOYMENT_TEST_PLAN_COMPLETE.md" >&2
        exit 1
    fi
done

# Safe command - allow through to actual docker binary (avoid recursion)
if [[ -n "${DOCKER_BIN:-}" ]]; then
    exec "$DOCKER_BIN" "$@"
fi
# Fallback: common locations (no PATH search - would find this wrapper)
# Docker Desktop first, then other locations
for candidate in /usr/local/bin/docker /Applications/Docker.app/Contents/Resources/bin/docker /opt/homebrew/bin/docker /usr/bin/docker; do
    if [[ -x "$candidate" ]]; then
        exec "$candidate" "$@"
    fi
done
echo "❌ DOCKER_BIN not set and no docker binary found in standard locations. Set DOCKER_BIN to the real docker path." >&2
exit 1
