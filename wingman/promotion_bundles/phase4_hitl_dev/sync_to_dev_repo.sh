#!/usr/bin/env bash
set -euo pipefail

# Phase 4 (Original) HITL promotion helper (DEV-safe).
#
# This script avoids patch hunks and instead syncs the known-good files from this bundle
# into the target DEV working tree, creating timestamped backups first.
#
# Usage:
#   ./sync_to_dev_repo.sh /path/to/wingman-system-dev
#
# What it does:
# - Detects whether the DEV tree uses:
#     A) repo-root layout (api_server.py at repo root), OR
#     B) subdir layout (wingman/api_server.py)
# - Copies the Phase 4 files accordingly.
# - Does NOT deploy anything (no docker compose up, no restarts).

TARGET_REPO="${1:-}"
if [[ -z "${TARGET_REPO}" ]]; then
  echo "Usage: $0 /path/to/wingman-system-dev"
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
backup_dir="${TARGET_REPO}/.wingman_backups/phase4_hitl_${ts}"
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

# Determine target layout
layout=""
if [[ -f "${TARGET_REPO}/wingman/api_server.py" ]]; then
  layout="subdir"
elif [[ -f "${TARGET_REPO}/api_server.py" ]]; then
  layout="root"
else
  echo "Cannot locate api_server.py in:"
  echo "  - ${TARGET_REPO}/wingman/api_server.py"
  echo "  - ${TARGET_REPO}/api_server.py"
  echo ""
  echo "Run these and paste output:"
  echo "  cd \"${TARGET_REPO}\""
  echo "  find . -maxdepth 3 -name api_server.py -print"
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
  copy_one "${SRC_DIR}/docker-compose.yml" "${TARGET_REPO}/wingman/docker-compose.yml"
  if [[ -f "${SRC_DIR}/env.dev.example" ]]; then
    copy_one "${SRC_DIR}/env.dev.example" "${TARGET_REPO}/wingman/env.dev.example"
  fi
  # dev_e2e_phase4.py lives outside the files folder (added later)
  if [[ -f "${SCRIPT_DIR}/files/dev_e2e_phase4.py" ]]; then
    copy_one "${SCRIPT_DIR}/files/dev_e2e_phase4.py" "${TARGET_REPO}/wingman/dev_e2e_phase4.py"
  fi
else
  copy_one "${SRC_DIR}/api_server.py" "${TARGET_REPO}/api_server.py"
  copy_one "${SRC_DIR}/approval_store.py" "${TARGET_REPO}/approval_store.py"
  copy_one "${SRC_DIR}/bot_api_client.py" "${TARGET_REPO}/bot_api_client.py"
  copy_one "${SRC_DIR}/telegram_bot.py" "${TARGET_REPO}/telegram_bot.py"
  copy_one "${SRC_DIR}/wingman_watcher.py" "${TARGET_REPO}/wingman_watcher.py"
  copy_one "${SRC_DIR}/proper_wingman_deployment.py" "${TARGET_REPO}/proper_wingman_deployment.py"
  copy_one "${SRC_DIR}/proper_wingman_deployment_prd.py" "${TARGET_REPO}/proper_wingman_deployment_prd.py"
  copy_one "${SRC_DIR}/docker-compose.yml" "${TARGET_REPO}/docker-compose.yml"
  if [[ -f "${SRC_DIR}/env.dev.example" ]]; then
    copy_one "${SRC_DIR}/env.dev.example" "${TARGET_REPO}/env.dev.example"
  fi
  if [[ -f "${SCRIPT_DIR}/files/dev_e2e_phase4.py" ]]; then
    copy_one "${SCRIPT_DIR}/files/dev_e2e_phase4.py" "${TARGET_REPO}/dev_e2e_phase4.py"
  fi
fi

echo ""
echo "✅ Phase 4 HITL files synced into DEV tree."
echo ""
echo "DEV verification (once DEV API is running):"
echo "  API_URL=http://localhost:8002 python3 wingman/dev_e2e_phase4.py"


