#!/usr/bin/env bash
set -euo pipefail

# Phase 4 (Original) HITL promotion helper.
# Applies the included patch into a target DEV repo working tree.
#
# Usage:
#   ./apply_to_dev_repo.sh /Users/mark/Projects/wingman-system-dev
#
# Notes:
# - This script does NOT deploy anything.
# - It only modifies files in the target working tree.

TARGET_REPO="${1:-}"
if [[ -z "${TARGET_REPO}" ]]; then
  echo "Usage: $0 /path/to/wingman-system-dev"
  exit 2
fi

PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_FILE="${PATCH_DIR}/phase4_hitl_dev.patch"

if [[ ! -f "${PATCH_FILE}" ]]; then
  echo "Missing patch file: ${PATCH_FILE}"
  exit 2
fi

if [[ ! -d "${TARGET_REPO}" ]]; then
  echo "Target repo directory not found: ${TARGET_REPO}"
  exit 2
fi

cd "${TARGET_REPO}"

if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Applying patch via git apply..."
  git apply --verbose "${PATCH_FILE}"
else
  echo "Target is not a git repo; applying patch via patch(1)..."
  patch -p1 < "${PATCH_FILE}"
fi

echo ""
echo "✅ Patch applied to: ${TARGET_REPO}"
echo ""
echo "Next (DEV verification):"
echo "  - Start DEV API (your existing process/compose)"
echo "  - Run: API_URL=http://localhost:8002 python3 wingman/dev_e2e_phase4.py"



