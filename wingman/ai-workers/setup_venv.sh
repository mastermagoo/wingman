#!/bin/bash
# Create and populate a venv for the AI workers orchestrator (avoids externally-managed-environment).
# Run from wingman repo root: ./ai-workers/setup_venv.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${1:-$ROOT/ai-workers/.venv}"

echo "Creating venv at: $VENV_DIR"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$ROOT/ai-workers/requirements.txt"
echo ""
echo "Venv ready. To use:"
echo "  source $VENV_DIR/bin/activate"
echo "  python ai-workers/scripts/wingman_orchestrator.py --phase 1a"
echo ""
