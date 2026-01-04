# Wingman AI Verification System

## Overview
Wingman is an AI claim verification system that validates whether AI agents actually performed the actions they claim.

## Wingman 1 vs Wingman 2 (Product Architecture)

- **Wingman 1 (Verifier Service)**: deterministic “Truth as a Service” API (`/verify`) + evidence capture.  
- **Wingman 2 (Governance Layer)**: policy gates + claims ledger + approvals + autonomous response, built on Wingman 1.

Authoritative docs:
- `DEPLOYMENT_PLAN.md` (master roadmap + current environment reality)
- `WINGMAN_2_PHASED_PLAN.md` (Wingman 1 vs 2 product architecture)
- `DEPLOYMENT_COMPLETE.md` (execution log / change record)

## Components

### 1. Simple Verifier (`simple_verifier.py`)
- Lightweight, no dependencies beyond Python stdlib
- Verifies file existence and process status
- Pattern-based extraction of targets
- Fast and reliable for basic verification

**Usage:**
```bash
python3 simple_verifier.py "I created /tmp/test.txt"
```

### 2. Enhanced Verifier (`enhanced_verifier.py`)
- Integrates Mistral 7B via Ollama for intelligent analysis
- Structured JSON parsing of LLM responses
- Combines AI understanding with real verification
- Provides confidence scores and explanations

**Usage:**
```bash
# Requires Ollama with Mistral installed
ollama pull mistral
python3 enhanced_verifier.py "I started Docker and created backup.tar"
```

## Features

### Supported Verifications:
- **Files**: Creation, deletion, modification
- **Processes**: Start, stop, running status
- **Extensions**: txt, json, py, md, log, csv, sql, db, tar, zip, yaml, etc.
- **Services**: Docker, nginx, MySQL, PostgreSQL, Redis, MongoDB, etc.

### Verdicts:
- **TRUE**: Claim verified against system state
- **FALSE**: Claim disproven by system check
- **UNVERIFIABLE**: Cannot determine validity

## Development Status

**Current (Mac Studio TEST + PRD):**
- ✅ Phase 2: Instruction Gate (`POST /check`)
- ✅ Phase 3: Claims Logger + Auditor (`POST /log_claim`, `POST /verify`)
- 🟡 Phase 4: Watcher / Incident Response (implementation in progress, see roadmap)

## Documentation

See `/docs/03-business/consulting/product/paul-wingman/truth-build/` for:
- Build process and lessons learned
- Step-by-step results
- Architecture decisions

## Future Enhancements

- Time-based verification ("I did X 5 minutes ago")
- Database operation verification
- API call verification
- Web interface
- Integration with Intel System for persistent logs
