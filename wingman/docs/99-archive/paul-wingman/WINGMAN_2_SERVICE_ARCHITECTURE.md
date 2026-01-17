## WINGMAN 2 – SERVICE ARCHITECTURE (DEV)

### 1. Purpose

Wingman 2 is an **independent verification and safety service** that runs as its own process and exposes a small HTTP API.  
All other systems (intel-system, SAP, Synovia, local tools, AI agents) are **clients** of this service – they cannot redefine what "Wingman validation" means.

Core goals:
- Verify **technical truth** of claims against real system state.
- Protect **professional and legal safety** in communications and commitments.
- Preserve a **human interpretation layer** (Mark) with clear evidence and audit trail.

---

### 2. High-Level Architecture (DEV on MBP)

```text
┌────────────────────────────┐
│   Clients (Untrusted)      │
│  - intel-system (DEV)      │
│  - IDE helpers / scripts   │
│  - AI agents (Claude etc.) │
└───────────────┬────────────┘
                │ HTTP (localhost)
                ▼
┌──────────────────────────────────────┐
│         WINGMAN SERVICE (DEV)       │
│ Location: ~/Projects/wingman-system-dev/wingman │
├──────────────────────────────────────┤
│  Flask API (api_server.py)          │
│  - GET /health                      │
│  - POST /verify                     │
│                                      │
│  Verifier Engine                     │
│  - simple_verifier.py (files, procs) │
│  - enhanced_verifier.py (LLM, later) │
│                                      │
│  Storage                             │
│  - In-memory stats (DEV)             │
│  - Postgres (TEST/PRD, later)        │
└──────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────┐
│ Monitored System (DEV)              │
│ - Local filesystem (/tmp, project)  │
│ - Local processes (ps, pgrep)       │
│ - Local services (Docker, DB, etc.) │
└──────────────────────────────────────┘
```

---

### 3. API Contract (Initial)

#### 3.1 `GET /health`

Returns current status of the Wingman service and its components.

Response (example):

```json
{
  "status": "healthy",
  "verifiers": {
    "simple": "available",
    "enhanced": "unavailable"
  },
  "database": "disconnected",
  "timestamp": "2025-12-05T18:26:36.900752"
}
```

- **`status`**: `"healthy"` or `"unhealthy"`.
- **`verifiers.simple`**: `"available"` when `simple_verifier` is callable.
- **`verifiers.enhanced`**: `"available"` only when LLM path is ready.
- **`database`**: `"connected"` or `"disconnected"` (DEV is disconnected).

#### 3.2 `POST /verify`

Verify a single natural-language claim.

Request:

```json
{
  "claim": "I created /tmp/test.txt",
  "use_enhanced": false
}
```

Response (example):

```json
{
  "verdict": "FALSE",
  "details": "Simple verification completed with verdict: FALSE",
  "verifier": "simple",
  "processing_time_ms": 0,
  "timestamp": "2025-12-05T18:26:36.914728"
}
```

- **`verdict`**: `"TRUE"`, `"FALSE"`, or `"UNVERIFIABLE"`.
- **`verifier`**: `"simple"` (current DEV default) or `"enhanced"` when enabled.
- **`details`**: human-readable explanation of what was checked.

> Note: A future `POST /review_message` endpoint will extend Wingman into communication safety (professional / legal checks) using a similar pattern.

---

### 4. Environment Model

- **DEV (MacBook Pro)**  
  - Code: `~/Projects/wingman-system-dev`.  
  - Engine: `python api_server.py` in `wingman/`.  
  - DB + LLM: optional, typically **not** running (falls back to in-memory + simple verifier).

- **TEST (Studio / NAS)** – future:
  - Same code from `wingman-system` repo deployed via Docker (`docker-compose-wingman.yml`).  
  - Used for integration tests with intel-system TEST and other clients.

- **PRD (Studio / NAS)** – future:
  - Hardened deployment (Gunicorn, Postgres stats DB, monitoring).  
  - Access-controlled; used by production intel-system and, later, external clients.

---

### 5. Trust & Responsibility

- Wingman service is **authoritative** for verification verdicts.  
- Clients may **request** decisions but must not override verdicts silently.  
- Human (Mark) always has the final say, with Wingman providing:
  - Clear verdicts (`TRUE` / `FALSE` / `UNVERIFIABLE`).  
  - Evidence in logs and (later) DB records.


