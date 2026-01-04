#!/usr/bin/env bash
set -euo pipefail

# Phase 4 (Original) HITL promotion helper (TEST-safe).
#
# Usage:
#   ./sync_to_test_repo.sh /path/to/wingman-test-working-tree
#
# Notes:
# - This does NOT deploy anything.
# - It syncs the known-good Phase 4 files + env.test.example into the target tree.

TARGET_REPO="${1:-}"
if [[ -z "${TARGET_REPO}" ]]; then
  echo "Usage: $0 /path/to/wingman-test-working-tree"
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPT_DIR}/files"

if [[ ! -d "${SRC_DIR}" ]]; then
  echo "Missing bundle files dir: ${SRC_DIR}"
  exit 2
fi

if [[ ! -d "${TARGET_REPO}" ]]; then
  echo "Target repo directory not found: ${TARGET_REPO}"
  exit 2
fi

ts="$(date +%Y%m%d_%H%M%S)"
backup_dir="${TARGET_REPO}/.wingman_backups/phase4_hitl_test_${ts}"
mkdir -p "${backup_dir}"

copy_one() {
  local src="$1"
  local dst="$2"
  mkdir -p "$(dirname "${dst}")"
  if [[ -f "${dst}" ]]; then
    cp -f "${dst}" "${backup_dir}/$(basename "${dst}").bak" || true
  fi
  cp -f "${src}" "${dst}"
  echo "  - synced $(basename "${src}") -> ${dst}"
}

# Determine target layout (same logic as DEV)
layout=""
if [[ -f "${TARGET_REPO}/wingman/api_server.py" ]]; then
  layout="subdir"
elif [[ -f "${TARGET_REPO}/api_server.py" ]]; then
  layout="root"
else
  echo "Cannot locate api_server.py in:"
  echo "  - ${TARGET_REPO}/wingman/api_server.py"
  echo "  - ${TARGET_REPO}/api_server.py"
  exit 2
fi

echo "Detected layout: ${layout}"
echo "Backups: ${backup_dir}"

if [[ "${layout}" == "subdir" ]]; then
  copy_one "${SRC_DIR}/api_server.py" "${TARGET_REPO}/wingman/api_server.py"
  copy_one "${SRC_DIR}/approval_store.py" "${TARGET_REPO}/wingman/approval_store.py"
  copy_one "${SRC_DIR}/bot_api_client.py" "${TARGET_REPO}/wingman/bot_api_client.py"
  copy_one "${SRC_DIR}/telegram_bot.py" "${TARGET_REPO}/wingman/telegram_bot.py"
  copy_one "${SRC_DIR}/wingman_watcher.py" "${TARGET_REPO}/wingman/wingman_watcher.py"
  copy_one "${SRC_DIR}/proper_wingman_deployment.py" "${TARGET_REPO}/wingman/proper_wingman_deployment.py"
  copy_one "${SRC_DIR}/proper_wingman_deployment_prd.py" "${TARGET_REPO}/wingman/proper_wingman_deployment_prd.py"
  if [[ -f "${SRC_DIR}/env.test.example" ]]; then
    copy_one "${SRC_DIR}/env.test.example" "${TARGET_REPO}/wingman/env.test.example"
  fi
else
  copy_one "${SRC_DIR}/api_server.py" "${TARGET_REPO}/api_server.py"
  copy_one "${SRC_DIR}/approval_store.py" "${TARGET_REPO}/approval_store.py"
  copy_one "${SRC_DIR}/bot_api_client.py" "${TARGET_REPO}/bot_api_client.py"
  copy_one "${SRC_DIR}/telegram_bot.py" "${TARGET_REPO}/telegram_bot.py"
  copy_one "${SRC_DIR}/wingman_watcher.py" "${TARGET_REPO}/wingman_watcher.py"
  copy_one "${SRC_DIR}/proper_wingman_deployment.py" "${TARGET_REPO}/proper_wingman_deployment.py"
  copy_one "${SRC_DIR}/proper_wingman_deployment_prd.py" "${TARGET_REPO}/proper_wingman_deployment_prd.py"
  if [[ -f "${SRC_DIR}/env.test.example" ]]; then
    copy_one "${SRC_DIR}/env.test.example" "${TARGET_REPO}/env.test.example"
  fi
fi

echo ""
echo "✅ Phase 4 HITL files synced into TEST tree."
echo ""
echo "Next (TEST config):"
echo "  - Copy env: cp env.test.example .env.test (or wingman/env.test.example -> wingman/.env.test)"
echo "  - Set BOT_TOKEN/CHAT_ID/API_URL for TEST"
echo "  - Start API and bot, then validate /pending + /approve flow"



