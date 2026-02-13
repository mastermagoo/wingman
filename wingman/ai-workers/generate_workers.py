#!/usr/bin/env python3
"""Generate remaining worker instruction files for META_WORKER_WINGMAN_01"""

import os
from pathlib import Path

# Worker definitions from META_WORKER_WINGMAN_01_INSTRUCTION.md
WORKERS = {
    # SEMANTIC ANALYZER (008-018 remaining)
    "008": ("Semantic_Completeness_Prompt", "Prompts", "Completeness scoring prompt template (10-point check)", "Prompt engineering"),
    "009": ("Semantic_Coherence_Prompt", "Prompts", "Coherence scoring prompt template (flow, logic)", "Prompt engineering"),
    "010": ("Semantic_Prompt_Parser", "Prompts", "Parse LLM JSON responses, extract scores", "JSON parsing"),
    "011": ("Semantic_Heuristic_Fallback", "Prompts", "Rule-based scoring (word count, sections) when LLM fails", "Heuristic logic"),
    "012": ("Semantic_Prompt_Consistency", "Prompts", "Run prompt 3x, check variance <10%", "Consistency validation"),
    "013": ("Semantic_Tests_Clarity", "Tests", "Tests 1-4: Clarity scoring (high/moderate/low/vague)", "pytest"),
    "014": ("Semantic_Tests_Completeness", "Tests", "Tests 5-8: Completeness (complete/missing DELIVERABLES/missing SUCCESS_CRITERIA/partial)", "pytest"),
    "015": ("Semantic_Tests_Coherence", "Tests", "Tests 9-12: Coherence (coherent/incoherent/mixed/jargon)", "pytest"),
    "016": ("Semantic_Tests_Edge_Cases", "Tests", "Tests 13-17: Edge cases (empty/single word/10K chars/special chars/multi-language)", "pytest"),
    "017": ("Semantic_Tests_Error_Handling", "Tests", "Tests 18-21: Error handling (timeout/invalid JSON/retry/fallback)", "pytest"),
    "018": ("Semantic_Tests_Integration", "Tests", "Tests 22-23: Integration (score range/performance benchmark)", "pytest"),

    # CODE SCANNER (019-036)
    "019": ("Code_Scanner_Class_Skeleton", "Structure", "Class skeleton + __init__", "Class creation"),
    "020": ("Code_Scanner_Scan_Method", "Structure", "scan() method structure + input validation", "Method implementation"),
    "021": ("Code_Scanner_Pattern_Engine", "Structure", "Pattern matching engine (regex compilation)", "Regex engine"),
    "022": ("Code_Scanner_Risk_Levels", "Structure", "Risk level assignment (LOW/MEDIUM/HIGH/CRITICAL)", "Risk logic"),
    "023": ("Code_Scanner_Detection_Format", "Structure", "Detection result formatting + JSON structure", "JSON formatter"),
    "024": ("Code_Scanner_Error_Handling", "Structure", "Error handling + malformed input", "Error handling"),
    "025": ("Code_Scanner_File_System_Patterns", "Patterns", "Patterns 1-5: File system ops (rm -rf, dd, mkfs)", "Pattern detection"),
    "026": ("Code_Scanner_Docker_Patterns", "Patterns", "Patterns 6-10: Docker socket, privileged mode", "Pattern detection"),
    "027": ("Code_Scanner_Network_Patterns", "Patterns", "Patterns 11-15: Network (iptables, nc, curl external)", "Pattern detection"),
    "028": ("Code_Scanner_System_Patterns", "Patterns", "Patterns 16-20: System (reboot, shutdown, kill -9)", "Pattern detection"),
    "029": ("Code_Scanner_Database_Patterns", "Patterns", "Patterns 21-25: Database (DROP, TRUNCATE)", "Pattern detection"),
    "030": ("Code_Scanner_Execution_Patterns", "Patterns", "Patterns 26-30: Code execution (eval, exec, os.system)", "Pattern detection"),
    "031": ("Code_Scanner_Secret_API_Patterns", "Secrets", "Secret patterns 1-5: API keys, tokens", "Pattern detection"),
    "032": ("Code_Scanner_Secret_Password_Patterns", "Secrets", "Secret patterns 6-10: Passwords, credentials", "Pattern detection"),
    "033": ("Code_Scanner_Secret_Key_Patterns", "Secrets", "Secret patterns 11-15: Private keys, certificates", "Pattern detection"),
    "034": ("Code_Scanner_Tests_Dangerous", "Tests", "Tests 54-58: Dangerous pattern tests (5 tests)", "pytest"),
    "035": ("Code_Scanner_Tests_Secrets", "Tests", "Tests 59-63: Secret detection tests (5 tests)", "pytest"),
    "036": ("Code_Scanner_Tests_Integration", "Tests", "Tests 64-73: Integration tests (10 tests, total: 20/20)", "pytest"),

    # DEPENDENCY ANALYZER (037-054)
    "037": ("Dependency_Analyzer_Class_Skeleton", "Structure", "Class skeleton + __init__", "Class creation"),
    "038": ("Dependency_Analyzer_Analyze_Method", "Structure", "analyze() method structure + input parsing", "Method implementation"),
    "039": ("Dependency_Graph_Builder", "Structure", "Service dependency graph builder", "Graph builder"),
    "040": ("Blast_Radius_Calculator", "Structure", "Blast radius calculation logic (0-100 scale)", "Calculation logic"),
    "041": ("Dependency_Tree_Formatter", "Structure", "Dependency tree formatting + JSON output", "JSON formatter"),
    "042": ("Dependency_Error_Handling", "Structure", "Error handling + unknown service handling", "Error handling"),
    "043": ("Service_Map_Wingman_API", "Topology", "Map service 1: wingman-api dependencies (postgres, redis)", "Service mapping"),
    "044": ("Service_Map_Execution_Gateway", "Topology", "Map service 2: execution-gateway (docker socket)", "Service mapping"),
    "045": ("Service_Map_Postgres", "Topology", "Map service 3: postgres (none, root service)", "Service mapping"),
    "046": ("Service_Map_Redis", "Topology", "Map service 4: redis (none, root service)", "Service mapping"),
    "047": ("Service_Map_Telegram_Bot", "Topology", "Map service 5: telegram-bot (wingman-api)", "Service mapping"),
    "048": ("Service_Map_Watcher_Ollama", "Topology", "Map services 6-7: watcher, ollama dependencies", "Service mapping"),
    "049": ("Cascade_Impact_Calculator", "Cascade", "Cascade impact calculator (if postgres down, what breaks?)", "Impact analysis"),
    "050": ("Critical_Path_Identifier", "Cascade", "Critical path identifier (single points of failure)", "Path analysis"),
    "051": ("Dependency_Tests_Service_Detection", "Tests", "Tests 74-78: Service detection tests (5 tests)", "pytest"),
    "052": ("Dependency_Tests_Blast_Radius", "Tests", "Tests 79-83: Blast radius tests (5 tests)", "pytest"),
    "053": ("Dependency_Tests_Cascade_Impact", "Tests", "Tests 84-88: Cascade impact tests (5 tests)", "pytest"),
    "054": ("Dependency_Tests_Integration", "Tests", "Tests 89-93: Integration tests (5 tests, total: 20/20)", "pytest"),
}

def generate_worker_file(worker_id, title, phase, description, task_type):
    """Generate a complete worker instruction file"""

    # Determine component and test info based on worker ID
    if int(worker_id) <= 18:
        component = "Semantic Analyzer"
        phase_num = "1.1"
    elif int(worker_id) <= 36:
        component = "Code Scanner"
        phase_num = "1.2"
    else:
        component = "Dependency Analyzer"
        phase_num = "1.3"

    # Determine if this is a test worker
    is_test_worker = "Tests" in title

    template = f"""# Worker {worker_id}: {component} - {title.replace('_', ' ')}

**Date:** 2026-01-13
**Environment:** TEST
**Phase:** {phase_num} - {component} {phase}
**Duration:** 20 minutes
**Status:** READY FOR EXECUTION

---

## 1. DELIVERABLES

- [ ] {description}
- [ ] Test results file: `ai-workers/results/worker-{worker_id}-results.json`

**Focus:** {task_type} for {component}

---

## 2. SUCCESS_CRITERIA

- [ ] Deliverable implemented according to specification
- [ ] All required functionality working
- [ ] {"Tests pass" if is_test_worker else "Unit tests pass"}
- [ ] No regression in previous workers' functionality

---

## 3. BOUNDARIES

- **CAN modify:** Implementation files for this specific deliverable
- **CANNOT modify:** Previous workers' deliverables without approval
- **CAN add:** Helper functions and utilities as needed
- **CANNOT add:** Out-of-scope features
- **Idempotency:** Safe to re-run if failure occurs

**Scope Limit:** This worker only - dependencies handled by other workers

---

## 4. DEPENDENCIES

- **Previous workers:** WORKER_{str(int(worker_id) - 1).zfill(3)} (prior deliverable complete)
- **Python environment:** Python 3.9+ with required libraries
- **Services:** {"pytest framework" if is_test_worker else "None required for this worker"}

---

## 5. MITIGATION

- **If implementation fails:** Check dependencies, verify prerequisites
- **If tests fail:** Debug and fix, or escalate if blocking
- **Rollback:** `git checkout` affected files to restore previous state
- **Escalation:** If blocked >30 minutes, escalate to human
- **Risk Level:** {"MEDIUM (tests must pass)" if is_test_worker else "LOW (implementation only)"}

---

## 6. TEST_PROCESS

```bash
# Validation command for WORKER_{worker_id}
{"cd wingman && pytest tests/test_semantic_analyzer.py -v" if is_test_worker and int(worker_id) <= 18 else ""}
{"cd wingman && pytest tests/test_code_scanner.py -v" if is_test_worker and 18 < int(worker_id) <= 36 else ""}
{"cd wingman && pytest tests/test_dependency_analyzer.py -v" if is_test_worker and int(worker_id) > 36 else ""}
{"cd wingman && python3 -c 'from validation import *; print(\"PASS: Module imports\")'" if not is_test_worker else ""}
```

---

## 7. TEST_RESULTS_FORMAT

```json
{{
  "worker_id": "{worker_id}",
  "worker_name": "{title}",
  "status": "pass|fail",
  "deliverables_created": [
    "{description}"
  ],
  "test_results": {{
    "implementation": "pass|fail",
    "validation": "pass|fail"
  }},
  "duration_seconds": 0,
  "timestamp": "2026-01-13T00:00:00Z",
  "errors": []
}}
```

---

## 8. TASK_CLASSIFICATION

- **Type:** {"MECHANICAL" if not is_test_worker and "Pattern" not in phase else "MECHANICAL"}
- **Tool:** {"pytest" if is_test_worker else "Python implementation"}
- **Reasoning:** {task_type} is {"deterministic testing" if is_test_worker else "structured implementation"}
- **Local-first:** Yes - local development and testing

---

## 9. RETROSPECTIVE

- **Time estimate:** 20 minutes
- **Actual time:** [To be filled after execution]
- **Challenges:** [To be filled after execution]
- **Lessons learned:** [To be filled after execution]
- **Store in mem0:**
  - Key: "wingman_worker_{worker_id}_retrospective"
  - Namespace: "wingman_system"
  - Content: Implementation notes, test results, lessons learned

---

## 10. PERFORMANCE_REQUIREMENTS

**Baseline:**
- Manual execution time: 20-30 minutes
- Current process: Manual implementation and testing

**Targets:**
- Automated execution: <20 minutes
- Accuracy: >95%
- Quality: All success criteria met

**Monitoring:**
- Before: Verify dependencies complete
- During: Track progress, log issues
- After: Validate deliverables, run tests
- Degradation limit: If execution takes >40 minutes (2x estimate), abort and escalate

---

**Reference:**
- Implementation Plan: `/Volumes/Data/ai_projects/wingman-system/wingman/docs/VALIDATION_ENHANCEMENT_IMPLEMENTATION_PLAN.md`
- Meta-Worker: `META_WORKER_WINGMAN_01_INSTRUCTION.md`

**Wingman Validation Score:** [To be filled]
**Wingman Status:** PENDING APPROVAL
"""
    return template

def main():
    """Generate all remaining worker files"""
    workers_dir = Path("ai-workers/workers")
    workers_dir.mkdir(parents=True, exist_ok=True)

    created = []
    for worker_id, (title, phase, description, task_type) in WORKERS.items():
        filename = f"WORKER_{worker_id}_{title}.md"
        filepath = workers_dir / filename

        content = generate_worker_file(worker_id, title, phase, description, task_type)
        filepath.write_text(content)
        created.append(filename)
        print(f"✓ Created {filename}")

    print(f"\n✅ Generated {len(created)} worker instruction files (008-054)")
    return created

if __name__ == "__main__":
    main()
