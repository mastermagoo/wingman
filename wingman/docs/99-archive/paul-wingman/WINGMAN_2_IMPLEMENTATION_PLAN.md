## WINGMAN 2 – IMPLEMENTATION PLAN (DEV → TEST → PRD)

### Phase 0 – Reality Check (Complete)

- ✅ Wingman codebase split into its own repo: `/Volumes/Data/ai_projects/wingman-system`.  
- ✅ DEV copy created on MBP: `~/Projects/wingman-system-dev`.  
- ✅ API server (`api_server.py`) runs on MBP at `http://127.0.0.1:8001`.  
- ✅ `GET /health` and `POST /verify` working with simple verifier and in-memory stats.

---

### Phase 1 – Stabilise Core Service (DEV on MBP)

**Goal:** Make Wingman 2 a small, honest, stable service in DEV.

- **1.1 API Contract (DONE / TRACKED IN ARCH DOC)**
  - `GET /health` – already implemented.
  - `POST /verify` – already implemented using `simple_verifier`.

- **1.2 Simple Verifier Hardening**
  - Confirm supported checks and document them:
    - File existence and basic attributes.
    - Process existence (`pgrep`/`ps` style checks).
    - Basic service checks where safe (e.g. `docker ps` presence).
  - Ensure all simple checks:
    - Are **read-only**.
    - Fail as `UNVERIFIABLE` rather than crashing.

- **1.3 Logging & Audit (MINIMUM FOR DEV)**
  - Ensure each `/verify` request and response is logged to stdout and a simple log file (e.g. `wingman/logs/api_dev.log`).
  - Include: timestamp, claim, verdict, processing_time_ms.

**Exit criteria (Phase 1):**
- Wingman API on MBP reliably serves `/health` and `/verify` using simple verifier only.  
- No DB or LLM required for basic operation.  
- Logs contain enough information to reconstruct what happened.

---

### Phase 2 – Integrate intel-system as a Client (DEV)

**Goal:** Stop intel-system faking “Wingman validation” and wire it to the real service.

- **2.1 Create a Thin Client Wrapper (DEV)**
  - New file in `wingman/`: `wingman_client.py` (CLI + importable helper).
  - Responsibilities:
    - Send `POST /verify` to `WINGMAN_API_URL` (default `http://127.0.0.1:8001`).
    - Return parsed verdict + details.
    - Provide a simple CLI:
      - `python wingman_client.py "I created /tmp/test.txt"` → prints verdict.

- **2.2 Use Client Wrapper in intel-system (DEV)**
  - In `intel-system` DEV environment:
    - Identify one concrete flow (e.g. mega-delegation orchestrator) where AI claims are made.
    - Replace internal “Wingman validation” helpers with calls to `wingman_client`:
      - Before marking a worker as “success”, send claim(s) to Wingman and respect verdict.
  - Document this integration clearly so it can be reproduced in TEST/PRD.

- **2.3 Remove “Fake Wingman Validation” Labels**
  - In intel-system code and docs:
    - Rename internal 10-point checkers from `validate_with_wingman` to neutral names (e.g. `validate_instruction_framework`).
    - Update docs to say “instruction framework validation” instead of “Wingman validation” unless the real API is called.

**Exit criteria (Phase 2):**
- At least one real intel-system path uses the live Wingman API in DEV.  
- No new code in intel-system is allowed to call anything labelled “Wingman” unless it talks to the real service.

---

### Phase 3 – TEST Environment Deployment (Studio / NAS)

**Goal:** Run Wingman 2 alongside intel-system TEST and verify integration under realistic conditions.

- **3.1 Containerise Wingman Service**
  - Use existing `docker-compose-wingman.yml` as a starting point.
  - Build a Wingman API image and run it on a TEST port (e.g. `8001` or `18001`).
  - Configure environment variables for:
    - `WINGMAN_MODE=test`
    - DB connection (if Postgres TEST is available), otherwise keep in-memory stats.

- **3.2 Point intel-system TEST at Wingman TEST**
  - Configure intel-system TEST to use `WINGMAN_API_URL` pointing to the TEST Wingman service.
  - Re-run the Phase 2 integration scenarios:
    - Ensure the same behaviour as DEV but with containerised networking.

- **3.3 Monitoring & Health**
  - Add simple health checks (curl or script) to ensure:
    - Wingman TEST `/health` responds.
    - Basic `/verify` works against a known claim.

**Exit criteria (Phase 3):**
- Wingman runs in TEST via Docker, reachable from intel-system TEST.  
- The key integration path works end-to-end in TEST without code changes.

---

### Phase 4 – Production Hardening (PRD)

**Goal:** Make Wingman safe and reliable enough to protect real deployments and communications.

- **4.1 Hardened Deployment**
  - Move from Flask dev server to Gunicorn behind a reverse proxy or similar.
  - Ensure logging to a persistent PRD location with rotation.

- **4.2 Database & Metrics**
  - Connect Wingman to a PRD Postgres instance for:
    - Storing verification history.
    - Aggregating metrics for `/stats`.
  - Keep sensitive data appropriately masked or summarised.

- **4.3 Formal Policies**
  - Define when a **FALSE** or **UNVERIFIABLE** verdict:
    - Blocks actions automatically (pre-commit, deployment).
    - Triggers warnings but allows override (with audit trail).

- **4.4 Security Review**
  - Ensure no secrets are logged.  
  - Ensure network exposure is appropriate (localhost, VPN, or controlled internal network).

**Exit criteria (Phase 4):**
- Wingman 2 is a stable PRD service with clear SLOs and a well-defined integration pattern for intel-system and other environments.

---

### Phase 5 – Communication Safety (Future)

**Goal:** Extend Wingman from technical claim verification into **message and commitment review**.

- Add `POST /review_message` endpoint for:
  - Analysing draft emails/updates for over-promising, liability, and misalignment with reality.
  - Flagging high-risk language before messages leave Mark’s environment.
- Integrate with mail / chat workflows as an optional-but-encouraged gate.

This phase builds on the same core service and trust model, and should only begin once Phases 1–4 are reliably in place.


