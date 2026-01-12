#!/bin/bash
# Wingman PRD backup (local-first).
# Backs up Wingman runtime data (sqlite DB, etc) to /Volumes/Data/backups/wingman/.
set -euo pipefail

WINGMAN_ENV="${WINGMAN_ENV:-PRD}"
timestamp="$(date +%Y%m%d_%H%M%S)"

BACKUP_ROOT="${WINGMAN_BACKUP_ROOT:-/Volumes/Data/backups/wingman}"
ENV_LC="$(printf '%s' "${WINGMAN_ENV}" | tr '[:upper:]' '[:lower:]')"
OUT_DIR="${BACKUP_ROOT}/${ENV_LC}/daily/${timestamp}"
mkdir -p "${OUT_DIR}"

SRC_DIR="/Volumes/Data/ai_projects/wingman-system/wingman/data"
if [[ ! -d "${SRC_DIR}" ]]; then
  echo "Missing wingman data dir: ${SRC_DIR}" >&2
  exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backing up Wingman data from ${SRC_DIR} -> ${OUT_DIR}"

tar -C "/Volumes/Data/ai_projects/wingman-system/wingman" -czf "${OUT_DIR}/wingman_data_${timestamp}.tar.gz" "data"

if command -v shasum >/dev/null 2>&1; then
  shasum -a 256 "${OUT_DIR}/wingman_data_${timestamp}.tar.gz" > "${OUT_DIR}/wingman_data_${timestamp}.tar.gz.sha256"
elif command -v sha256sum >/dev/null 2>&1; then
  sha256sum "${OUT_DIR}/wingman_data_${timestamp}.tar.gz" > "${OUT_DIR}/wingman_data_${timestamp}.tar.gz.sha256"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Wingman backup complete: ${OUT_DIR}"

