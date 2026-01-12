#!/bin/bash
################################################################################
# Wingman TEST → PRD Deployment Script
# Purpose: Clone/promote wingman-test environment to wingman-prd
# Usage: ./deploy_test_to_prd.sh [--force] [--skip-validation]
# Author: Claude Code
# Date: 2025-12-16
################################################################################

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/wingman_test_to_prd_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"; }
success() { echo -e "${GREEN}✅ $*${NC}" | tee -a "$LOG_FILE"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}❌ $*${NC}" | tee -a "$LOG_FILE"; }
die() { error "$*"; exit 1; }

# Parse arguments
FORCE=false
SKIP_VALIDATION=false
SKIP_HITL=false
for arg in "$@"; do
    case $arg in
        --force) FORCE=true ;;
        --skip-validation) SKIP_VALIDATION=true ;;
        --skip-hitl) SKIP_HITL=true ;;
        *) warn "Unknown argument: $arg" ;;
    esac
done

log "Starting Wingman TEST → PRD deployment"
log "Log file: $LOG_FILE"
log "Working directory: $SCRIPT_DIR"

################################################################################
# Shared: Contract + Health Gates (Unavoidable “build complete” guardrails)
################################################################################

# IMPORTANT:
# - We may allow the deployment to proceed with --force, but we will NOT print a
#   "✅ deployment completed successfully" message unless ALL gates pass.
# - These checks validate API contracts (shape) + system health (not just files).

GATES_OK=true

contract_check_api() {
    local label="$1"
    local base_url="$2"

    log "Contract gate (${label}): validating API contracts at ${base_url} (no secrets printed)..."

    python3 - "$label" "$base_url" <<'PY'
import json, sys, urllib.request, urllib.error

label = sys.argv[1]
base = sys.argv[2].rstrip("/")

def _req(method: str, path: str, body: dict | None = None):
    url = base + path
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url=url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        return e.code, raw

def _must_json(status: int, raw: str):
    try:
        return json.loads(raw)
    except Exception as e:
        raise AssertionError(f"expected JSON, got status={status} body={raw[:200]!r}") from e

# /health must be 200 JSON with required keys
st, raw = _req("GET", "/health")
assert st == 200, f"{label} /health status={st}"
j = _must_json(st, raw)
for k in ("status", "phase", "timestamp"):
    assert k in j, f"{label} /health missing key: {k}"
assert j.get("status") == "healthy", f"{label} /health status field not healthy: {j.get('status')}"

# /check contract: must return approved/score/missing_sections/policy_checks
good_instruction = (
    "DELIVERABLES: x\nSUCCESS_CRITERIA: x\nBOUNDARIES: x\nDEPENDENCIES: x\nMITIGATION: x\n"
    "TEST_PROCESS: x\nTEST_RESULTS_FORMAT: x\nRESOURCE_REQUIREMENTS: x\nRISK_ASSESSMENT: x\nQUALITY_METRICS: x\n"
)
st, raw = _req("POST", "/check", {"instruction": good_instruction})
assert st == 200, f"{label} /check status={st}"
j = _must_json(st, raw)
for k in ("approved", "score", "missing_sections", "policy_checks"):
    assert k in j, f"{label} /check missing key: {k}"
assert isinstance(j.get("approved"), bool), f"{label} /check approved not bool"
assert isinstance(j.get("score"), int), f"{label} /check score not int"

# /verify contract: must return verdict + verifier + processing_time_ms
st, raw = _req("POST", "/verify", {"claim": "health contract probe"})
assert st == 200, f"{label} /verify status={st}"
j = _must_json(st, raw)
for k in ("verdict", "verifier", "processing_time_ms", "timestamp"):
    assert k in j, f"{label} /verify missing key: {k}"
assert j.get("verdict") in ("TRUE", "FALSE", "UNVERIFIABLE", "ERROR"), f"{label} /verify unexpected verdict={j.get('verdict')}"

print(f"{label} contract gate: OK")
PY
}

################################################################################
# Shared: Stage-by-stage HITL approval gate (unavoidable for "build complete")
################################################################################

stage_instruction() {
    local stage="$1"
    cat <<EOF
DELIVERABLES: Promote TEST → PRD stage executed: ${stage}
SUCCESS_CRITERIA: Stage completes; PRD health+contract gates pass; Telegram bot stays authorized; no secrets printed
BOUNDARIES: Do not print secrets; do not modify unrelated repos; localhost-bound ports only
DEPENDENCIES: Wingman TEST API reachable; PRD .env.prd present; docker compose v2
MITIGATION: If a stage fails, stop and surface logs; do not proceed
TEST_PROCESS: contract gate (/health,/check,/verify); docker compose ps; PRD health+contract gate after deploy
TEST_RESULTS_FORMAT: exit codes + concise status lines (no secret values)
RESOURCE_REQUIREMENTS: moderate CPU/RAM; disk for volumes
RISK_ASSESSMENT: High (production deployment stage: ${stage})
QUALITY_METRICS: 100% gates pass; deterministic stage-by-stage human approval
EOF
}

request_hitl_stage() {
    local stage="$1"
    local api_url="$2"

    # If HITL is skipped, we still allow the script to run, but it must NEVER claim success.
    if [[ "$SKIP_HITL" == true ]]; then
        warn "HITL stage approval skipped for stage '${stage}' (--skip-hitl) — will NOT claim 'build complete'."
        GATES_OK=false
        return 0
    fi

    log "HITL gate: requesting human approval for stage '${stage}' via ${api_url} ..."

    local instr
    instr="$(stage_instruction "$stage")"

    python3 - "$stage" "$api_url" "$instr" <<'PY'
import json, os, sys, time, urllib.request, urllib.error

stage = sys.argv[1]
api = sys.argv[2].rstrip("/")
instruction = sys.argv[3]

def _headers(request=False, read=False):
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    # Optional least-privilege headers. Do NOT print values.
    if request:
        v = (os.getenv("WINGMAN_APPROVAL_REQUEST_KEY") or "").strip()
        if v:
            h["X-Wingman-Approval-Request-Key"] = v
    if read:
        v = (os.getenv("WINGMAN_APPROVAL_READ_KEY") or "").strip()
        if v:
            h["X-Wingman-Approval-Read-Key"] = v
    legacy = (os.getenv("WINGMAN_APPROVAL_API_KEY") or "").strip()
    if legacy:
        h["X-Wingman-Approval-Key"] = legacy
    return h

def _post(path, body, headers):
    url = api + path
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url=url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return resp.status, raw

def _get(path, headers):
    url = api + path
    req = urllib.request.Request(url=url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        return e.code, raw

st, raw = _post(
    "/approvals/request",
    {
        "worker_id": "deploy_test_to_prd",
        "task_name": f"PROMOTE TEST→PRD: {stage}",
        "instruction": instruction,
        "deployment_env": "prd",
    },
    _headers(request=True),
)
if st != 200:
    raise SystemExit(f"HITL request failed: HTTP {st} body={raw[:200]!r}")

j = json.loads(raw) if raw else {}
if not j.get("needs_approval", False):
    # Auto-approved (policy/risk); proceed.
    raise SystemExit(0)

req = j.get("request") or {}
request_id = (req.get("request_id") or "").strip()
if not request_id:
    raise SystemExit("HITL response missing request_id")

poll = float(os.getenv("WINGMAN_APPROVAL_POLL_SEC", "2.0"))
timeout = float(os.getenv("WINGMAN_APPROVAL_TIMEOUT_SEC", "86400"))
deadline = time.time() + timeout

while time.time() < deadline:
    time.sleep(poll)
    st, raw = _get(f"/approvals/{request_id}", _headers(read=True))
    if st != 200:
        continue
    cur = json.loads(raw) if raw else {}
    status = cur.get("status", "")
    if status == "APPROVED":
        raise SystemExit(0)
    if status == "REJECTED":
        raise SystemExit(f"HITL rejected: request_id={request_id}")

raise SystemExit(f"HITL timed out: request_id={request_id}")
PY
}

################################################################################
# Phase 1: Pre-Flight Validation
################################################################################

log "=== Phase 1: Pre-Flight Validation ==="

# Check we're in wingman directory
if [[ ! -f "$SCRIPT_DIR/docker-compose.yml" ]]; then
    die "Not in wingman directory. PWD: $(pwd)"
fi

# Validate TEST is running (use compose, not hardcoded container name patterns)
log "Checking TEST containers status (docker compose)..."
TEST_RUNNING=$(docker compose -f "$SCRIPT_DIR/docker-compose.yml" ps -q 2>/dev/null | wc -l | tr -d ' ')
success "TEST Status: $TEST_RUNNING containers in compose state"

# Determine TEST API port (prefer .env.test if present)
TEST_API_PORT="5002"
if [[ -f "$SCRIPT_DIR/.env.test" ]]; then
    # shellcheck disable=SC1090
    source "$SCRIPT_DIR/.env.test" 2>/dev/null || true
    TEST_API_PORT="${API_PORT:-5002}"
fi

# Check TEST API health + contracts (no secrets printed)
if [[ $SKIP_VALIDATION == false ]]; then
    log "Checking TEST API health on 127.0.0.1:${TEST_API_PORT}..."
    if curl -f -s "http://127.0.0.1:${TEST_API_PORT}/health" > /dev/null 2>&1; then
        success "TEST API is healthy"
    else
        warn "TEST API health check failed"
        GATES_OK=false
        if [[ $FORCE != true ]]; then
            die "TEST API must be healthy. Use --force to proceed anyway (will still NOT print success if gates fail)."
        fi
    fi

    if contract_check_api "TEST" "http://127.0.0.1:${TEST_API_PORT}" > /dev/null 2>&1; then
        success "TEST API contract gate passed"
    else
        warn "TEST API contract gate FAILED"
        GATES_OK=false
        if [[ $FORCE != true ]]; then
            die "TEST API contract gate failed. Use --force to proceed anyway (will still NOT print success if gates fail)."
        fi
    fi
fi

# Check required files
log "Validating required files..."
REQUIRED_FILES=(
    "docker-compose.yml"
    "docker-compose.prd.yml"
    "Dockerfile.api"
    "Dockerfile.bot"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$SCRIPT_DIR/$file" ]]; then
        die "Required file missing: $file"
    fi
    success "Found: $file"
done

# Check .env.prd exists
if [[ ! -f "$SCRIPT_DIR/.env.prd" ]]; then
    warn ".env.prd not found. Creating from env.prd.example..."
    if [[ -f "$SCRIPT_DIR/env.prd.example" ]]; then
        cp "$SCRIPT_DIR/env.prd.example" "$SCRIPT_DIR/.env.prd"
        warn "Created .env.prd from env.prd.example. Please edit it with production values before deploying."
        warn "Required: DB_PASSWORD, BOT_TOKEN, CHAT_ID"
        die "Edit .env.prd then rerun: ./deploy_test_to_prd.sh --force"
    fi
    die ".env.prd not found and env.prd.example missing. Please create .env.prd manually."
fi

# Validate .env.prd has required values
log "Validating .env.prd configuration..."
source "$SCRIPT_DIR/.env.prd" 2>/dev/null || true

if [[ "${DB_PASSWORD:-}" == "CHANGE_ME_TO_SECURE_PASSWORD" ]] || [[ -z "${DB_PASSWORD:-}" ]]; then
    die "DB_PASSWORD must be set in .env.prd"
fi

if [[ "${BOT_TOKEN:-}" == "CHANGE_ME_TO_PRODUCTION_BOT_TOKEN" ]] || [[ -z "${BOT_TOKEN:-}" ]]; then
    die "BOT_TOKEN must be set in .env.prd"
fi

if [[ "${CHAT_ID:-}" == "CHANGE_ME_TO_PRODUCTION_CHAT_ID" ]] || [[ -z "${CHAT_ID:-}" ]]; then
    die "CHAT_ID must be set in .env.prd"
fi

success ".env.prd validated"

# Ensure Phase 4 approval keys exist (optional but recommended).
# We generate keys only if missing, without printing them.
if [[ -z "${WINGMAN_APPROVAL_READ_KEYS:-}" ]] || [[ -z "${WINGMAN_APPROVAL_DECIDE_KEYS:-}" ]] || [[ -z "${WINGMAN_APPROVAL_READ_KEY:-}" ]] || [[ -z "${WINGMAN_APPROVAL_DECIDE_KEY:-}" ]] || [[ -z "${WINGMAN_APPROVAL_REQUEST_KEYS:-}" ]] || [[ -z "${WINGMAN_APPROVAL_REQUEST_KEY:-}" ]]; then
    log "Ensuring Phase 4 approval keys exist in .env.prd (no secrets printed)..."
    python3 - <<'PY'
import secrets
from pathlib import Path

p = Path(".env.prd")
lines = p.read_text(encoding="utf-8").splitlines()

def parse(lines):
    d = {}
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        d[k.strip()] = v.strip()
    return d

d = parse(lines)
changed = False

def ensure(key, value, comment=None):
    global changed
    if d.get(key):
        return
    if comment:
        lines.append(comment)
    lines.append(f"{key}={value}")
    changed = True

# Generate least-privilege keys:
# - API gets READ_KEYS + DECIDE_KEYS (lists)
# - Bot gets READ_KEY + DECIDE_KEY (single)
# - Script/orchestrators get REQUEST_KEYS + REQUEST_KEY (request-only)
bot_read = secrets.token_urlsafe(32)
orch_read = secrets.token_urlsafe(32)
bot_decide = secrets.token_urlsafe(32)
orch_decide = secrets.token_urlsafe(32)
orch_request = secrets.token_urlsafe(32)

ensure("WINGMAN_APPROVAL_READ_KEYS", f"{bot_read},{orch_read}", comment="\n# Phase 4 (HITL) approval protection (role-separated)")
ensure("WINGMAN_APPROVAL_DECIDE_KEYS", f"{bot_decide},{orch_decide}")
ensure("WINGMAN_APPROVAL_READ_KEY", bot_read)
ensure("WINGMAN_APPROVAL_DECIDE_KEY", bot_decide)
ensure("WINGMAN_APPROVAL_REQUEST_KEYS", orch_request, comment="\n# Optional: allow a client/script to call POST /approvals/request when request keys are enabled")
ensure("WINGMAN_APPROVAL_REQUEST_KEY", orch_request)
ensure("WINGMAN_APPROVAL_PENDING_TTL_SEC", "86400")

if changed:
    p.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
PY
    success "Phase 4 approval keys ensured in .env.prd"
fi

# PRD approvals must go through PRD Wingman (separation from TEST).
# We do NOT fall back to TEST for approvals.
PRD_API_PORT_EFFECTIVE="${API_PORT:-5000}"
PRD_API_URL="http://127.0.0.1:${PRD_API_PORT_EFFECTIVE}"

require_prd_gatekeeper() {
    if [[ "$SKIP_HITL" == true ]]; then
        return 0
    fi
    if curl -f -s "${PRD_API_URL}/health" >/dev/null 2>&1; then
        return 0
    fi
    die "PRD Wingman gatekeeper not reachable at ${PRD_API_URL}. Start PRD Wingman first (e.g. 'docker compose -f docker-compose.prd.yml --env-file .env.prd up -d --build wingman-api postgres redis') then rerun."
}

# HITL stage approvals (PRD-only): pre-flight (before touching PRD)
require_prd_gatekeeper
request_hitl_stage "A-preflight" "$PRD_API_URL"

################################################################################
# Phase 2: Stop Existing PRD (if any)
################################################################################

log "=== Phase 2: Stop Existing PRD ==="

PRD_CONTAINERS=$(docker ps -a --filter "name=wingman.*-prd" --format "{{.Names}}")

if [[ -n "$PRD_CONTAINERS" ]]; then
    # HITL stage approval: before stopping/removing PRD containers
    require_prd_gatekeeper
    request_hitl_stage "B-stop-prd" "$PRD_API_URL"

    log "Found existing PRD containers:"
    echo "$PRD_CONTAINERS" | while read -r container; do
        log "  - $container"
    done
    
    if [[ $FORCE == true ]]; then
        log "Stopping and removing existing PRD containers..."
        docker ps -a --filter "name=wingman.*-prd" -q | xargs -r docker rm -f
        success "Removed existing PRD containers"
    else
        warn "Existing PRD containers found. Refusing to remove without --force (non-interactive safety)."
        die "Rerun with --force to remove existing PRD containers."
    fi
else
    success "No existing PRD containers found"
fi

################################################################################
# Phase 3: Create Data Directories
################################################################################

log "=== Phase 3: Create Data Directories ==="

mkdir -p "$SCRIPT_DIR/logs/prd"
mkdir -p "$SCRIPT_DIR/data/prd"
success "Created data directories: logs/prd, data/prd"

################################################################################
# Phase 4: Deploy PRD Environment
################################################################################

log "=== Phase 4: Deploy PRD Environment ==="

cd "$SCRIPT_DIR"

# HITL stage approval: before starting PRD containers
require_prd_gatekeeper
request_hitl_stage "C-deploy-prd" "$PRD_API_URL"

log "Starting PRD containers..."
# Force rebuild so PRD runs the exact code in this working tree (avoids stale images).
docker compose -f docker-compose.prd.yml --env-file .env.prd up -d --build

success "PRD containers started"

################################################################################
# Phase 5: Wait for Startup
################################################################################

log "=== Phase 5: Wait for Startup ==="

log "Waiting for containers to start (30s)..."
sleep 30

# Check container status
log "Checking container status..."
PRD_RUNNING=$(docker ps --filter "name=wingman.*-prd" --format "{{.Names}}" | wc -l | tr -d ' ')

log "PRD Containers Running: $PRD_RUNNING"

if [[ $PRD_RUNNING -lt 3 ]]; then
    warn "Expected at least 3 PRD containers, found: $PRD_RUNNING"
    log "Checking container logs..."
    docker ps -a --filter "name=wingman.*-prd" --format "{{.Names}}" | while read -r container; do
        log "Logs for $container:"
        docker logs "$container" --tail 20 2>&1 | sed 's/^/  /'
    done
fi

################################################################################
# Phase 6: Validation
################################################################################

log "=== Phase 6: Validation ==="

# Check health endpoints
log "Checking API health endpoint..."
MAX_RETRIES=10
RETRY_COUNT=0
API_HEALTHY=false
API_PORT_EFFECTIVE="${API_PORT:-5000}"

while [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; do
    # PRD API is bound to 127.0.0.1:${API_PORT_EFFECTIVE} (see docker-compose.prd.yml)
    if curl -f -s "http://127.0.0.1:${API_PORT_EFFECTIVE}/health" > /dev/null 2>&1; then
        API_HEALTHY=true
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    log "  Retry $RETRY_COUNT/$MAX_RETRIES: API not ready yet..."
    sleep 5
done

if [[ $API_HEALTHY == true ]]; then
    success "API health check passed"
else
    error "API health check failed after $MAX_RETRIES retries"
    log "API logs:"
    docker logs wingman-prd-api --tail 50 2>&1 | sed 's/^/  /'
    GATES_OK=false
fi

# Check database
log "Checking database..."
if docker exec wingman-prd-postgres pg_isready -U "${DB_USER:-wingman_prd}" > /dev/null 2>&1; then
    success "Database is ready"
else
    error "Database health check failed"
    log "Database logs:"
    docker logs wingman-prd-postgres --tail 20 2>&1 | sed 's/^/  /'
    GATES_OK=false
fi

# Check Redis
log "Checking Redis..."
if docker exec wingman-prd-redis redis-cli ping > /dev/null 2>&1; then
    success "Redis is ready"
else
    error "Redis health check failed"
    GATES_OK=false
fi

# Check Ollama
log "Checking Ollama..."
if curl -f -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    success "Ollama is ready"
else
    warn "Ollama health check failed (may need time to start)"
    # Ollama may be optional in PRD; do not fail the full gate here.
fi

# PRD API contract gate (no secrets printed)
log "Checking PRD API contract gate..."
if contract_check_api "PRD" "http://127.0.0.1:${API_PORT_EFFECTIVE}" > /dev/null 2>&1; then
    success "PRD API contract gate passed"
else
    warn "PRD API contract gate FAILED"
    GATES_OK=false
fi

# HITL stage approval: post-validation (before any "build complete" claim)
require_prd_gatekeeper
request_hitl_stage "D-post-validate" "$PRD_API_URL"

# List all PRD containers
log "PRD Container Status:"
docker ps --filter "name=wingman.*-prd" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | tee -a "$LOG_FILE"

################################################################################
# Phase 7: Summary
################################################################################

log "=== Phase 7: Deployment Summary ==="

PRD_HEALTHY=$(docker ps --filter "name=wingman.*-prd" --filter "health=healthy" --format "{{.Names}}" | wc -l | tr -d ' ')
PRD_RUNNING=$(docker ps --filter "name=wingman.*-prd" --format "{{.Names}}" | wc -l | tr -d ' ')

log "Deployment Summary:"
log "  PRD Containers Running: $PRD_RUNNING"
log "  PRD Containers Healthy: $PRD_HEALTHY"
log "  API Endpoint: http://127.0.0.1:${API_PORT_EFFECTIVE}/health"
log "  Log File: $LOG_FILE"

if [[ $API_HEALTHY == true ]] && [[ $PRD_RUNNING -ge 3 ]]; then
    if [[ $GATES_OK == true ]]; then
        success "✅ Wingman PRD deployment completed successfully (ALL GATES PASSED)!"
    else
        warn "⚠️  PRD deployment finished but gating FAILED — do NOT treat as verified."
        warn "⚠️  This script will not claim 'build complete' unless all gates pass."
    fi
    log ""
    log "Next steps:"
    # API_PORT_EFFECTIVE is the validated host port for PRD API (see Phase 6)
    log "  1. Test API: curl http://127.0.0.1:${API_PORT_EFFECTIVE}/health"
    log "  2. Test Telegram bot: Send message to production bot"
    log "  3. Monitor logs: docker logs -f wingman-prd-api"
    log "  4. Check container status: docker ps --filter 'name=wingman.*-prd'"
else
    warn "⚠️  Deployment completed with warnings. Please review logs."
    log "Check logs: docker logs wingman-prd-api"
fi

log ""
log "Deployment completed. Log file: $LOG_FILE"


