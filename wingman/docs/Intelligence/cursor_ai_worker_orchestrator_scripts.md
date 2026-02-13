# AI worker orchestrator scripts
_Exported on 13/01/2026 at 13:05:22 CET from Cursor (2.3.34)_

---

**User**

find me all the AI worker orchestroar scripts in this repo?

---

**Cursor**


Searching for AI worker orchestrator scripts.



Listing files in the orchestration directory and searching for additional orchestrator scripts:



Reviewing key orchestrator scripts to understand their structure:



Found all AI worker orchestrator scripts. Summary:

## Primary orchestrator scripts

### Main orchestration scripts (in `/tools/orchestration/`)

1. **`launch_massive_workforce.py`** — Main orchestrator
   - Uses AutoGen with `MassiveOrchestrator` class
   - 20+ autonomous workers
   - Hybrid LLM strategy (CodeLlama 13B + Mistral 7B)
   - Full infrastructure integration (ChromaDB, Redis, RAG)

2. **`launch_autogen_workers.py`** — AutoGen-based orchestrator
   - Specialized workers for Wingman development
   - Uses AutoGen GroupChat for coordination
   - 7 specialized workers (3×CodeLlama 13B + 4×Mistral 7B)

3. **`launch_intel_workers.py`** — Intel-system enhancement orchestrator
   - Focuses on enhancing intel-system infrastructure
   - Similar AutoGen setup to launch_autogen_workers.py

4. **`launch_intel_workers_fixed.py`** — Fixed version of intel workers

5. **`launch_autogen_massive.py`** — Massive AutoGen deployment

6. **`launch_max_local_workforce.py`** — Local worker orchestrator
   - Uses threading for local execution
   - `LocalWorker` class implementation

7. **`launch_20_agents.py`** — 20-agent orchestrator

8. **`launch_workforce_v2.py`** — Version 2 workforce launcher

9. **`launch_workforce_v3.py`** — Version 3 workforce launcher

10. **`REAL_WORKFORCE_BUILD.py`** — Direct Ollama execution
    - Uses Ollama directly (no AutoGen)
    - Simple, direct execution approach

11. **`optimal_autogen_workers.py`** — Optimized AutoGen configuration
    - Full infrastructure (RAG, Redis, ChromaDB)
    - CodeLlama 13B for quality tasks

12. **`simple_workers.py`** — Simple worker implementation

13. **`simple_massive_launch.py`** — Simple massive launch script

### Validation & deployment orchestrators

14. **`ORCHESTRATED_VALIDATION.py`** — Validation orchestrator
    - `ValidationOrchestrator` class

15. **`ORCHESTRATED_VALIDATION_VENV.py`** — Validation with venv support

16. **`AUTONOMOUS_DEPLOY_FIX.py`** — Deployment orchestrator
    - `DeploymentOrchestrator` class

17. **`AUTONOMOUS_BUILD.py`** — Autonomous build orchestrator

18. **`proper_deployment_system.py`** — Proper deployment system

19. **`deploy_phase1_sap_namespace.py`** — SAP Phase 1 deployment

20. **`deploy_phase2_multitenant.py`** — SAP Phase 2 multi-tenant deployment

### Supporting scripts

21. **`execute_workforce_now.py`** — Immediate workforce execution

22. **`test_and_commit_workforce.py`** — Test and commit workforce

23. **`monitor_dashboard.py`** — Monitoring dashboard

24. **`integrated_system.py`** — Integrated system orchestrator

25. **`fix_and_deploy.py`** — Fix and deploy script

26. **`fix_failed_components.py`** — Fix failed components

27. **`final_fix_components.py`** — Final fix components

28. **`identify_dependencies.py`** — Dependency identification

29. **`validate_generated_code.py`** — Code validation

30. **`prepare_test_environment.py`** — Test environment preparation

31. **`TEST_ALL_COMPONENTS.py`** — Component testing

32. **`compare_all_llms.py`** — LLM comparison tool

### Legacy scripts (in `/tools/orchestration/legacy/`)

All the above scripts also exist in the `legacy/` subdirectory as archived versions.

## Summary

- Total orchestrator scripts: 32+ active scripts
- Main orchestrators: 13 (various launch/worker scripts)
- Validation/deployment: 7
- Supporting utilities: 12+

The most important ones are:
- `launch_massive_workforce.py` — Main orchestrator with `MassiveOrchestrator` class
- `launch_autogen_workers.py` — AutoGen-based worker orchestration
- `REAL_WORKFORCE_BUILD.py` — Direct Ollama execution

Should I examine any specific script in detail or create a comparison of their capabilities?

---

**User**

or are they in the archive folder?

---

**Cursor**


Checking archive folders for orchestrator scripts:



Checking archive folders for orchestrator scripts:



Yes, there are orchestrator scripts in the archive folders. Summary:

## Active orchestrator scripts (in `/tools/orchestration/`)

32+ active scripts (as listed earlier)

## Archived orchestrator scripts

### 1. `/archive/old_scripts/` — 24 archived scripts
- `AUTONOMOUS_WORKFORCE_ORCHESTRATOR.py` — Main archived orchestrator
  - 50+ simultaneous agents
  - Self-coordinating with Redis
  - Auto-error recovery
  - Task redistribution
- `AUTONOMOUS_BUILD.py`
- `AUTONOMOUS_DEPLOY_FIX.py`
- `ORCHESTRATED_VALIDATION.py`
- `ORCHESTRATED_VALIDATION_VENV.py`
- `REAL_WORKFORCE_BUILD.py`
- `optimal_autogen_workers.py`
- `simple_workers.py`
- `simple_massive_launch.py`
- Plus 15 more supporting scripts

### 2. `/archive/old_workforce/` — 12 archived workforce scripts
- `launch_massive_workforce.py`
- `launch_autogen_workers.py`
- `launch_intel_workers.py`
- `launch_intel_workers_fixed.py`
- `launch_autogen_massive.py`
- `launch_20_agents.py`
- `launch_workforce_v2.py`
- `launch_workforce_v3.py`
- `launch_max_local_workforce.py`
- `execute_workforce_now.py`
- `test_and_commit_workforce.py`
- Plus documentation files

### 3. `/archive/2025-09-24_cleanup/` — Cleanup archive
- `launch_autogen_workers.py`
- `launch_intel_workers.py`
- `launch_intel_workers_fixed.py`
- `optimal_autogen_workers.py`
- `simple_workers.py`
- `REAL_WORKFORCE_BUILD.py`
- `ORCHESTRATED_VALIDATION.py`
- `ORCHESTRATED_VALIDATION_VENV.py`
- `AUTONOMOUS_DEPLOY_FIX.py`
- Plus documentation

### 4. `/archive/experiments/` — Experimental versions
- `launch_autogen_workers.py`
- `launch_intel_workers.py`
- `launch_intel_workers_fixed.py`
- `execute_workforce_now.py`

### 5. `/archive/old_deployments/` — Deployment orchestrators
- Docker orchestration implementations
- Production deployment scripts

## Summary

- Active: 32+ scripts in `/tools/orchestration/`
- Archived: 50+ scripts across multiple archive folders
- Total: 80+ orchestrator scripts in the repository

The most notable archived orchestrator is `AUTONOMOUS_WORKFORCE_ORCHESTRATOR.py` in `/archive/old_scripts/` — it supports 50+ simultaneous agents with self-coordination.

Should I compare the active vs archived versions, or examine a specific archived orchestrator?

