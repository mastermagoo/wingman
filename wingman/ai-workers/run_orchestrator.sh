#!/bin/bash
# Run the orchestrator using the ai-workers venv (no need to activate first).
# Usage: ./ai-workers/run_orchestrator.sh [--phase 1a] [--workers 001-018] [--batch-size 5]
# Run from wingman repo root.
#
# Required: OPENAI_API_KEY in environment (Phase 1A uses OpenAI for all workers).
# Env loading (repo root): .env.ai-workers, then .env.test, then .env (later override earlier).
# For Phase 1A (TEST), .env.test is used when present. No PRD env is loaded by this script.

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$ROOT/ai-workers/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Venv not found. Run first: ./ai-workers/setup_venv.sh"
  exit 1
fi

# Load env from repo root (OPENAI_API_KEY etc.). Order: .env.ai-workers, then .env.test (TEST/Phase 1A), then .env.
# Later files override earlier; .env.test is where OPENAI_API_KEY/ANTHROPIC often live for TEST.
if [ -f "$ROOT/.env.ai-workers" ]; then
  set -a
  # shellcheck source=/dev/null
  . "$ROOT/.env.ai-workers"
  set +a
fi
if [ -f "$ROOT/.env.test" ]; then
  set -a
  # shellcheck source=/dev/null
  . "$ROOT/.env.test"
  set +a
fi
if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck source=/dev/null
  . "$ROOT/.env"
  set +a
fi

exec "$VENV_PYTHON" "$ROOT/ai-workers/scripts/wingman_orchestrator.py" "$@"
