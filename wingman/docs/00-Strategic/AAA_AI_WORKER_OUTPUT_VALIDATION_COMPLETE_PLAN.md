# AI Worker Output Validation - Complete Plan

**Status**: DESIGN PHASE
**Version**: 1.0
**Date**: 2026-02-16
**Scope**: Wingman strategy/enhancement documentation (DEV/TEST/PRD)
**Purpose**: Address critical gaps preventing AI worker reliability through output validation and execution control

---

## EXECUTIVE SUMMARY

**Problem**: Previous AI worker attempts failed catastrophically (3 attempts, 0 working code, $30+ wasted, 5+ hours lost) despite Wingman's robust input validation system. Root cause: Wingman validates **instructions** but not **generated code output**.

**Critical Gaps Identified**:
1. **Gap 1: Code Quality Validation** ⚠️ CRITICAL - No validation of generated code (syntax, security, quality)
2. **Gap 2: Incremental Execution Control** - No enforcement of "test 1 before running 225"
3. **Gap 3: Environment Verification** - No pre-flight checks for dependencies/tools

**Solution**: Three-phase enhancement system:
- **Phase 6.1: Output Validation Pipeline** (PRIMARY FOCUS) - Validate generated code before deployment
- **Phase 6.2: Incremental Execution Control** (FUTURE) - Enforce checkpoint approvals during batch execution
- **Phase 6.3: Environment Verification** (FUTURE) - Pre-flight environment checks

**Impact**: Transforms AI workers from 0% success rate to reliable, audited code generation with multi-layer validation.

**Estimated Effort**:
- Phase 6.1: 16-24 hours (output validation)
- Phase 6.2: 8-12 hours (incremental control)
- Phase 6.3: 6-8 hours (environment verification)
- **Total: 30-44 hours** (realistic, incremental delivery)

---

## SECTION 1: PROBLEM STATEMENT & CRITICAL GAPS

### 1.1 Current State (What Works)

**Wingman Phases 1-5 Deployed** (as of 2026-02-16):
- ✅ **Phase 1**: Base integration (Docker, Postgres, Redis, Flask)
- ✅ **Phase 2**: Input validation (10-point framework + 5 validators, 990 LOC)
- ✅ **Phase 3**: Technical truth (claims logging, audit processor)
- ✅ **Phase 4**: Watcher (real-time monitoring, quarantine, Telegram alerts)
- ✅ **Phase 5**: Docker wrapper (infrastructure-level enforcement)

**Input Validation Capabilities** (Phase 2):
- 5 validators: CodeScanner, SemanticAnalyzer, DependencyAnalyzer, ContentQualityValidator, CompositeValidator
- Profile-based validation (operational vs deployment)
- Auto-approve/auto-reject decisions
- Detection of: secrets, dangerous patterns, poor quality instructions
- **Status**: PRODUCTION-READY, deployed to PRD

### 1.2 What's Missing (The Gaps)

#### **Gap 1: Code Quality Validation** ⚠️ CRITICAL PRIORITY

**The Problem**:
Wingman validates **what the AI worker is ASKED to do** (instruction) but not **what the AI worker ACTUALLY produces** (generated code).

**Real-World Failure** (from `AAA_AI_WORKER_FAILURE_ANALYSIS.md`):
- **Attempt 2**: 225 AI workers generated 3,755 lines of code
- **Result**: 209/225 workers failed validation (93% failure rate)
- **Issues**:
  - ❌ Wrong file paths (`wingman/wingman/` instead of `wingman/`)
  - ❌ Missing dependencies (`import nltk` without verification)
  - ❌ Never tested (assumed code worked)
  - ❌ Unknown security issues (no code scanning)
  - ❌ Unknown quality (syntax errors, logic bugs, edge cases)

**Current Flow** (NO output validation):
```
Instruction → Wingman validates instruction ✅
          ↓
AI worker generates 3,755 lines of code
          ↓
Code written to disk (NO VALIDATION ❌)
          ↓
Discover failures AFTER deployment/execution
```

**Impact**:
- Wasted API costs ($30+ per failed batch)
- Wasted time (80+ minutes per failed attempt)
- Repo contamination (3,755 lines of untested code)
- Zero confidence in AI worker output
- Manual cleanup required

**What's Needed**:
```
Instruction → Wingman validates instruction ✅
          ↓
AI worker generates code
          ↓
OUTPUT VALIDATION PIPELINE ⭐ NEW
  - Syntax validation (does it parse?)
  - Security scanning (secrets, dangerous patterns)
  - Dependency verification (imports available?)
  - Test execution (does it work?)
  - Quality scoring (meets standards?)
          ↓
APPROVED → Deploy  OR  REJECTED → Quarantine worker
```

#### **Gap 2: Incremental Execution Control**

**The Problem**:
No enforcement of "test 1 worker before running 225". Wingman allows all-or-nothing batch execution.

**Real-World Failure**:
- **Attempt 1**: Launched all 225 workers immediately
- **Result**: Discovered wrong paths/dependencies AFTER 189 workers failed
- **Should have**: Tested worker 1 → validate → adjust → continue

**Current Flow**:
```
User: "Run 225 workers"
     ↓
Wingman: "Instruction looks good ✅"
     ↓
Execute all 225 workers (no checkpoints)
     ↓
Discover systematic failure after 80 minutes
```

**What's Needed**:
```
User: "Run 225 workers"
     ↓
Wingman: "Running worker 1 (checkpoint mode)"
     ↓
Worker 1 completes → OUTPUT VALIDATION
     ↓
REQUEST APPROVAL: "Worker 1 passed, continue with 2-10?"
     ↓
If approved → Continue with checkpoints (10, 25, 50, 100, 225)
If rejected → Stop, investigate, adjust
```

#### **Gap 3: Environment Verification**

**The Problem**:
No pre-flight checks. Workers execute without verifying required tools/dependencies exist.

**Real-World Failure**:
- **Attempt 2**: Generated code with `import nltk`
- **Reality**: `nltk` not installed in environment
- **Result**: 209 workers "failed validation" because imports didn't work

**Current Flow**:
```
Instruction: "Generate code using nltk library"
     ↓
Wingman: "Instruction approved ✅"
     ↓
Worker generates code with `import nltk`
     ↓
Discover nltk missing AFTER code generated
```

**What's Needed**:
```
Instruction: "Generate code using nltk library"
     ↓
ENVIRONMENT CHECK ⭐ NEW
  - Parse required dependencies from instruction
  - Verify packages installed (pip list | grep nltk)
  - Verify import works (python -c "import nltk")
  - Check required tools (docker, git, curl)
     ↓
If environment ready → Approve execution
If missing deps → REJECT with instructions to install
```

### 1.3 Gap Priority & Dependencies

| Gap | Priority | Blocking? | Dependencies |
|-----|----------|-----------|--------------|
| **Gap 1: Output Validation** | 🔴 CRITICAL | YES - blocks AI worker reliability | None (can implement now) |
| **Gap 2: Incremental Execution** | 🟡 HIGH | NO - workaround: manual checkpoints | Depends on Gap 1 (needs output validation at checkpoints) |
| **Gap 3: Environment Verification** | 🟢 MEDIUM | NO - workaround: manual verification | None (independent of other gaps) |

**Recommendation**: Implement **Gap 1 (Output Validation) FIRST**, then Gap 3, then Gap 2.

**Rationale**:
- Gap 1 is foundational - both Gap 2 and Gap 3 benefit from output validation
- Gap 3 can be implemented in parallel (independent)
- Gap 2 requires Gap 1 (checkpoints need validation to decide continue/stop)

---

## SECTION 2: PHASE 6.1 - OUTPUT VALIDATION PIPELINE (PRIMARY FOCUS)

### 2.1 Requirements

#### **FR-1: Syntax & Parse Validation**

**Functional Requirement**:
- Validate generated code parses correctly (Python, JavaScript, YAML, JSON, etc.)
- Detect syntax errors before code is deployed
- Support multiple file types

**Acceptance Criteria**:
- Python code: `python -m py_compile <file>` succeeds
- JavaScript: `node --check <file>` succeeds
- YAML/JSON: Parse with standard library, detect malformed files
- Return: `{valid: true/false, errors: [list], line_numbers: [int]}`

**Example**:
```python
# Generated code with syntax error
def calculate(x:
    return x * 2  # Missing closing paren

# Output Validator detects:
{
  "valid": false,
  "errors": ["SyntaxError: invalid syntax at line 1"],
  "line_numbers": [1]
}
```

#### **FR-2: Security Code Scanning**

**Functional Requirement**:
- Scan generated code for secrets, dangerous patterns, security vulnerabilities
- Reuse existing CodeScanner patterns from Phase 2
- Block deployment if CRITICAL findings

**Acceptance Criteria**:
- Detect: hardcoded passwords, API keys, tokens, certificates
- Detect: dangerous commands (`rm -rf`, `DROP TABLE`, `eval()`, `exec()`)
- Detect: SQL injection patterns, XSS vulnerabilities
- Return: `{severity: CRITICAL/HIGH/MEDIUM/LOW, findings: [{pattern, line, context}]}`

**Example**:
```python
# Generated code with hardcoded secret
API_KEY = "sk-1234567890abcdef"  # ❌ CRITICAL

# Output Validator detects:
{
  "severity": "CRITICAL",
  "findings": [{
    "pattern": "hardcoded_api_key",
    "line": 1,
    "context": "API_KEY = \"sk-1234...\"",
    "recommendation": "Use environment variable"
  }]
}
```

#### **FR-3: Dependency Verification**

**Functional Requirement**:
- Extract imports/dependencies from generated code
- Verify all imports are available in target environment
- Detect missing packages before deployment

**Acceptance Criteria**:
- Parse imports: `import X`, `from X import Y`, `require('X')`, etc.
- Check availability: Run import test in target container
- Return: `{missing: [list], available: [list], unknown: [list]}`

**Example**:
```python
# Generated code imports nltk
import nltk
from transformers import pipeline

# Output Validator checks:
# docker exec wingman-test-api python -c "import nltk; import transformers"

# If nltk missing:
{
  "missing": ["nltk"],
  "available": ["transformers"],
  "recommendation": "pip install nltk before deployment"
}
```

#### **FR-4: Automated Test Execution**

**Functional Requirement**:
- Execute tests for generated code (if tests provided)
- Run code in sandboxed environment (no side effects)
- Capture test results, coverage, failures

**Acceptance Criteria**:
- Pytest: `pytest <test_file> --tb=short --no-cov` → capture results
- Unittest: `python -m unittest <test_module>` → capture results
- Return: `{passed: int, failed: int, errors: [list], duration: float}`

**Example**:
```bash
# Worker generated: semantic_analyzer.py + test_semantic_analyzer.py
# Output Validator runs:
docker exec wingman-test-api pytest tests/test_semantic_analyzer.py

# Results:
{
  "passed": 8,
  "failed": 2,
  "errors": [
    "test_risk_assessment: AssertionError at line 45",
    "test_blast_radius: TypeError: missing argument"
  ],
  "duration": 1.2
}
```

#### **FR-5: Quality Scoring**

**Functional Requirement**:
- Score generated code quality (0-100)
- Consider: complexity, documentation, best practices, maintainability
- Use heuristics (no LLM dependency for performance)

**Acceptance Criteria**:
- Complexity: Cyclomatic complexity < 10 (good), > 20 (bad)
- Documentation: Docstrings present (good), missing (penalty)
- Best practices: Type hints, error handling, logging
- Return: `{score: 0-100, issues: [list], recommendations: [list]}`

**Example**:
```python
# Generated code (no docstrings, high complexity)
def process(x, y, z, a, b):
    if x:
        if y:
            if z:
                return a + b
            else:
                return a - b
        else:
            return 0
    else:
        return None

# Quality Scorer:
{
  "score": 45,
  "issues": [
    "Missing docstring",
    "High cyclomatic complexity (8 branches)",
    "No type hints",
    "No error handling"
  ],
  "recommendations": [
    "Add function docstring with parameters",
    "Reduce nesting depth",
    "Add type annotations"
  ]
}
```

#### **FR-6: Integration with Approval Flow**

**Functional Requirement**:
- Output validation runs AFTER code generation, BEFORE deployment
- Create approval request for human review if validation fails
- Store validation results in database (audit trail)

**Acceptance Criteria**:
- Validation triggers automatically after worker completion
- If validation fails → Create `/approvals/request` with validation report
- If validation passes → Auto-approve or continue workflow
- All validation results logged to Postgres (`output_validations` table)

**Example Flow**:
```
Worker completes → Generates 3 files (semantic_analyzer.py + tests + docs)
                ↓
Output Validator runs all checks
                ↓
Validation result: 2 syntax errors, 1 missing dependency
                ↓
POST /approvals/request {
  "worker_id": "WORKER_001",
  "task_name": "Semantic Analyzer Implementation",
  "validation_result": {
    "passed": false,
    "syntax_errors": 2,
    "missing_deps": ["nltk"],
    "recommendation": "MANUAL_REVIEW"
  }
}
                ↓
Telegram notification to Mark with validation report
                ↓
Mark reviews → Approves fix → Worker corrects errors
```

### 2.2 Architecture

#### **High-Level Design**

```
┌─────────────────────────────────────────────────────────────┐
│                    WINGMAN API (Flask)                       │
├─────────────────────────────────────────────────────────────┤
│  Existing:                                                   │
│  - Input Validation (Phase 2) ✅                            │
│  - Approval Flow (Phase 4) ✅                               │
│  - Watcher (Phase 4) ✅                                      │
│                                                              │
│  NEW - Phase 6.1:                                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │     OUTPUT VALIDATION PIPELINE                      │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │ 1. Syntax Validator                          │  │    │
│  │  │    - Python: py_compile                       │  │    │
│  │  │    - JS: node --check                         │  │    │
│  │  │    - YAML/JSON: parse test                    │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │ 2. Security Scanner (reuse CodeScanner)      │  │    │
│  │  │    - Secrets detection                        │  │    │
│  │  │    - Dangerous patterns                       │  │    │
│  │  │    - Vulnerability scanning                   │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │ 3. Dependency Verifier                       │  │    │
│  │  │    - Extract imports                          │  │    │
│  │  │    - Check availability                       │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │ 4. Test Executor                             │  │    │
│  │  │    - Run pytest/unittest                      │  │    │
│  │  │    - Capture results                          │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │ 5. Quality Scorer                            │  │    │
│  │  │    - Complexity analysis                      │  │    │
│  │  │    - Best practices check                     │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │ 6. Output Composite Validator                │  │    │
│  │  │    - Combine results                          │  │    │
│  │  │    - Decision: APPROVE/REJECT/MANUAL_REVIEW   │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           ↓
              ┌────────────────────────┐
              │  Postgres Database     │
              │  - output_validations  │  ⭐ NEW TABLE
              │  - approval_requests   │  (existing)
              └────────────────────────┘
                           ↓
              ┌────────────────────────┐
              │  Telegram Notifications │
              │  - Validation reports   │
              │  - Approval requests    │
              └────────────────────────┘
```

#### **Component Design**

##### **Component 1: SyntaxValidator**

**Purpose**: Validate code parses correctly, no syntax errors

**Location**: `wingman/output_validation/syntax_validator.py`

**Interface**:
```python
class SyntaxValidator:
    def validate(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        Args:
            file_path: Path to generated file
            file_type: "python", "javascript", "yaml", "json", etc.

        Returns:
            {
                "valid": bool,
                "errors": List[str],
                "line_numbers": List[int],
                "error_details": List[Dict]
            }
        """
```

**Implementation**:
- Python: Use `py_compile.compile()` or `ast.parse()`
- JavaScript: Subprocess call to `node --check`
- YAML: `yaml.safe_load()` with error handling
- JSON: `json.loads()` with error handling

##### **Component 2: OutputSecurityScanner**

**Purpose**: Scan generated code for security issues (reuse Phase 2 CodeScanner patterns)

**Location**: `wingman/output_validation/output_security_scanner.py`

**Interface**:
```python
class OutputSecurityScanner:
    def __init__(self):
        # Reuse CodeScanner patterns from validation/code_scanner.py
        self.code_scanner = CodeScanner()

    def scan(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Returns:
            {
                "severity": "CRITICAL/HIGH/MEDIUM/LOW",
                "findings": List[Dict],
                "safe": bool
            }
        """
```

**Reuses**:
- Secret patterns from `validation/code_scanner.py`
- Dangerous command patterns
- Vulnerability patterns

##### **Component 3: DependencyVerifier**

**Purpose**: Extract imports, verify availability in target environment

**Location**: `wingman/output_validation/dependency_verifier.py`

**Interface**:
```python
class DependencyVerifier:
    def verify(self, file_path: str, target_env: str = "wingman-api") -> Dict[str, Any]:
        """
        Args:
            file_path: Path to generated file
            target_env: Docker container name to check against

        Returns:
            {
                "all_available": bool,
                "missing": List[str],
                "available": List[str],
                "unknown": List[str]  # Can't determine (e.g., relative imports)
            }
        """
```

**Implementation**:
- Parse imports using `ast` module (Python) or regex (other languages)
- Test imports: `docker exec <container> python -c "import X"`
- Cache results (avoid repeated checks)

##### **Component 4: TestExecutor**

**Purpose**: Run tests for generated code, capture results

**Location**: `wingman/output_validation/test_executor.py`

**Interface**:
```python
class TestExecutor:
    def execute_tests(self, test_file_path: str, target_env: str = "wingman-api") -> Dict[str, Any]:
        """
        Returns:
            {
                "passed": int,
                "failed": int,
                "errors": List[Dict],
                "duration": float,
                "coverage": float  # Optional
            }
        """
```

**Implementation**:
- Pytest: `docker exec <container> pytest <file> --tb=short -v`
- Parse output, extract pass/fail counts
- Timeout: 60 seconds (prevent hanging tests)

##### **Component 5: QualityScorer**

**Purpose**: Score code quality using heuristics

**Location**: `wingman/output_validation/quality_scorer.py`

**Interface**:
```python
class QualityScorer:
    def score(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Returns:
            {
                "score": int (0-100),
                "complexity": int,  # Cyclomatic complexity
                "issues": List[str],
                "recommendations": List[str]
            }
        """
```

**Scoring Criteria**:
| Metric | Weight | Good | Bad |
|--------|--------|------|-----|
| Cyclomatic Complexity | 25% | < 10 | > 20 |
| Documentation | 20% | Docstrings present | Missing |
| Type Hints | 15% | Present | Missing |
| Error Handling | 15% | try/except present | None |
| Line Length | 10% | < 120 chars | > 150 |
| Function Length | 10% | < 50 lines | > 100 |
| Naming Conventions | 5% | PEP8 | Violations |

##### **Component 6: OutputCompositeValidator**

**Purpose**: Orchestrate all validators, make final decision

**Location**: `wingman/output_validation/output_composite_validator.py`

**Interface**:
```python
class OutputCompositeValidator:
    def validate_output(self, worker_id: str, generated_files: List[str]) -> Dict[str, Any]:
        """
        Args:
            worker_id: Worker that generated code
            generated_files: List of file paths

        Returns:
            {
                "decision": "APPROVE" | "REJECT" | "MANUAL_REVIEW",
                "overall_score": int (0-100),
                "validation_results": {
                    "syntax": {...},
                    "security": {...},
                    "dependencies": {...},
                    "tests": {...},
                    "quality": {...}
                },
                "recommendation": str,
                "blocking_issues": List[str]
            }
        """
```

**Decision Logic**:
```python
# AUTO-REJECT if:
- Syntax errors found
- CRITICAL security findings
- Missing critical dependencies
- Tests failed (if tests provided)
- Quality score < 30

# MANUAL_REVIEW if:
- HIGH security findings
- Some dependencies missing (non-critical)
- Tests failed (some failures)
- Quality score 30-70

# AUTO-APPROVE if:
- No syntax errors
- No security issues (or LOW only)
- All dependencies available
- Tests passed (if tests provided)
- Quality score >= 70
```

#### **Integration Points**

##### **Integration with Approval Flow**

**New Endpoint**: `POST /output_validation/validate`

```python
# In api_server.py

@app.route("/output_validation/validate", methods=["POST"])
def validate_output():
    """
    Called after AI worker completes code generation.
    Validates generated code before deployment.
    """
    data = request.json
    worker_id = data["worker_id"]
    generated_files = data["generated_files"]  # List of file paths
    task_name = data.get("task_name", "Code Generation")

    # Run output validation pipeline
    output_validator = OutputCompositeValidator()
    result = output_validator.validate_output(worker_id, generated_files)

    # Store validation results in database
    store_validation_result(worker_id, result)

    # Decision logic
    if result["decision"] == "REJECT":
        # Auto-reject, quarantine worker if critical issues
        if has_critical_issues(result):
            quarantine_worker(worker_id, reason=result["blocking_issues"])

        return jsonify({
            "status": "REJECTED",
            "reason": result["recommendation"],
            "validation_report": result
        }), 403

    elif result["decision"] == "MANUAL_REVIEW":
        # Create approval request for human review
        approval_id = create_approval_request(
            worker_id=worker_id,
            task_name=task_name,
            instruction=f"Review generated code from {worker_id}",
            validation_result=result
        )

        # Send Telegram notification with validation report
        send_telegram_validation_report(approval_id, result)

        return jsonify({
            "status": "PENDING",
            "approval_id": approval_id,
            "validation_report": result
        }), 200

    else:  # APPROVE
        return jsonify({
            "status": "APPROVED",
            "validation_report": result
        }), 200
```

##### **Integration with Watcher**

**Enhancement**: Watcher monitors output validation results

```python
# In wingman_watcher.py

# NEW: Monitor for repeated validation failures
def check_output_validation_failures():
    """
    If worker has 3+ consecutive validation failures:
    - Alert Mark via Telegram
    - Consider auto-quarantine
    """
    cursor = db.execute("""
        SELECT worker_id, COUNT(*) as failure_count
        FROM output_validations
        WHERE decision = 'REJECT'
          AND created_at > NOW() - INTERVAL '24 hours'
        GROUP BY worker_id
        HAVING COUNT(*) >= 3
    """)

    for row in cursor:
        worker_id = row[0]
        failure_count = row[1]

        alert_message = f"""
        🚨 WORKER VALIDATION FAILURES

        Worker: {worker_id}
        Failures: {failure_count} in last 24 hours

        Recommendation: Review worker quality or quarantine
        """

        send_telegram_alert(alert_message)
```

### 2.3 Database Schema

#### **New Table: output_validations**

```sql
CREATE TABLE output_validations (
    validation_id SERIAL PRIMARY KEY,
    worker_id VARCHAR(255) NOT NULL,
    task_name VARCHAR(255),
    generated_files JSONB NOT NULL,  -- Array of file paths

    -- Validation results
    decision VARCHAR(50) NOT NULL,  -- APPROVE, REJECT, MANUAL_REVIEW
    overall_score INTEGER,  -- 0-100

    -- Individual validator results
    syntax_result JSONB,
    security_result JSONB,
    dependency_result JSONB,
    test_result JSONB,
    quality_result JSONB,

    -- Metadata
    blocking_issues JSONB,  -- Array of critical issues
    recommendation TEXT,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    validated_by VARCHAR(255) DEFAULT 'output_validator',

    -- Foreign key to approval if manual review created
    approval_id INTEGER REFERENCES approval_requests(id)
);

-- Indexes
CREATE INDEX idx_output_validations_worker ON output_validations(worker_id);
CREATE INDEX idx_output_validations_decision ON output_validations(decision);
CREATE INDEX idx_output_validations_created ON output_validations(created_at DESC);
```

#### **Schema Migration**

**File**: `wingman/migrations/006_output_validations.sql`

```sql
-- Migration: Add output validation tracking

-- Create output_validations table
CREATE TABLE IF NOT EXISTS output_validations (
    -- (schema above)
);

-- Add validation result tracking to approval_requests
ALTER TABLE approval_requests
ADD COLUMN IF NOT EXISTS output_validation_id INTEGER REFERENCES output_validations(validation_id);

-- Track validation history
CREATE TABLE IF NOT EXISTS worker_validation_history (
    history_id SERIAL PRIMARY KEY,
    worker_id VARCHAR(255) NOT NULL,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_success_at TIMESTAMP,
    last_failure_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2.4 Implementation Plan

#### **Phase 6.1.1: Core Validators** (8-10 hours)

**Task 6.1.1.1: SyntaxValidator** (2-3 hours)
- Create `wingman/output_validation/syntax_validator.py`
- Implement Python syntax validation using `ast.parse()`
- Implement JavaScript validation (subprocess to node)
- Implement YAML/JSON validation
- Write 15+ tests covering edge cases
- **Deliverable**: Working syntax validator with comprehensive tests
- **Success Criteria**: All tests pass, validates Python/JS/YAML/JSON correctly

**Task 6.1.1.2: OutputSecurityScanner** (2-3 hours)
- Create `wingman/output_validation/output_security_scanner.py`
- Reuse CodeScanner patterns from Phase 2
- Adapt for file scanning (vs instruction scanning)
- Add code-specific patterns (eval, exec, pickle vulnerabilities)
- Write 20+ tests covering secret types and dangerous patterns
- **Deliverable**: Security scanner adapted for output validation
- **Success Criteria**: Detects secrets and vulnerabilities in generated code

**Task 6.1.1.3: DependencyVerifier** (2-3 hours)
- Create `wingman/output_validation/dependency_verifier.py`
- Implement import extraction (ast module for Python)
- Implement availability checking (docker exec import test)
- Add caching (avoid repeated checks)
- Write 15+ tests with mock docker responses
- **Deliverable**: Dependency verifier with TEST container integration
- **Success Criteria**: Correctly identifies missing dependencies

**Task 6.1.1.4: QualityScorer** (2-3 hours)
- Create `wingman/output_validation/quality_scorer.py`
- Implement complexity calculation (cyclomatic complexity)
- Implement documentation checks (docstrings)
- Implement best practices scoring (type hints, error handling)
- Write 20+ tests with good/bad code examples
- **Deliverable**: Quality scorer with heuristic-based scoring
- **Success Criteria**: Scores 0-100 match expected ranges for test cases

#### **Phase 6.1.2: Integration & Orchestration** (4-6 hours)

**Task 6.1.2.1: OutputCompositeValidator** (2-3 hours)
- Create `wingman/output_validation/output_composite_validator.py`
- Implement orchestration of all 4 validators
- Implement decision logic (APPROVE/REJECT/MANUAL_REVIEW)
- Add weighting and threshold configuration
- Write 15+ integration tests
- **Deliverable**: Composite validator orchestrating all validators
- **Success Criteria**: Correctly combines validator results and makes decisions

**Task 6.1.2.2: API Endpoint Integration** (2-3 hours)
- Add `/output_validation/validate` endpoint to `api_server.py`
- Integrate with approval flow
- Add database storage (output_validations table)
- Add Telegram notification for validation reports
- Write 10+ endpoint tests
- **Deliverable**: Working API endpoint integrated with approval flow
- **Success Criteria**: Endpoint accepts validation requests, stores results, creates approvals

#### **Phase 6.1.3: Database & Migration** (2-3 hours)

**Task 6.1.3.1: Database Schema** (1 hour)
- Create migration: `migrations/006_output_validations.sql`
- Define output_validations table
- Define worker_validation_history table
- Add foreign keys to approval_requests
- **Deliverable**: Migration script
- **Success Criteria**: Migration runs cleanly on TEST database

**Task 6.1.3.2: Database Functions** (1-2 hours)
- Implement `store_validation_result()`
- Implement `get_validation_history(worker_id)`
- Implement `update_worker_validation_stats()`
- Write 10+ database integration tests
- **Deliverable**: Database access layer for output validations
- **Success Criteria**: CRUD operations work correctly

#### **Phase 6.1.4: Testing & Validation** (2-4 hours)

**Task 6.1.4.1: Unit Tests** (1-2 hours)
- Complete test coverage for all validators (target: 80%+)
- Test edge cases (empty files, large files, malformed code)
- Test error handling (timeouts, docker unavailable)
- **Deliverable**: 80+ unit tests
- **Success Criteria**: All tests pass, coverage >= 80%

**Task 6.1.4.2: Integration Tests** (1-2 hours)
- Test full output validation pipeline
- Test with real generated code samples
- Test API endpoint end-to-end
- Test Telegram notifications
- **Deliverable**: 20+ integration tests
- **Success Criteria**: Full pipeline works in TEST environment

#### **Phase 6.1.5: Documentation** (2-3 hours)

**Task 6.1.5.1: Technical Documentation** (1-2 hours)
- Update `AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md`
- Create `OUTPUT_VALIDATION_USER_GUIDE.md`
- Document validation thresholds and tuning
- Document how to interpret validation reports
- **Deliverable**: User-facing documentation
- **Success Criteria**: Documentation explains how to use output validation

**Task 6.1.5.2: Operational Guide** (1 hour)
- Create `OUTPUT_VALIDATION_OPERATIONS_GUIDE.md`
- Document how to deploy to TEST/PRD
- Document monitoring and troubleshooting
- Document threshold tuning procedures
- **Deliverable**: Operations guide
- **Success Criteria**: Operators can deploy and maintain output validation

### 2.5 Testing Strategy

#### **Unit Test Coverage**

**Target**: 80%+ code coverage across all validators

**Test Categories**:
1. **Syntax Validator** (15 tests)
   - Valid Python/JS/YAML/JSON files
   - Syntax errors (missing parens, brackets, quotes)
   - Edge cases (empty files, very large files)
   - Error message parsing

2. **Output Security Scanner** (20 tests)
   - Secret detection (API keys, passwords, tokens)
   - Dangerous patterns (eval, exec, rm -rf)
   - Vulnerability patterns (SQL injection, XSS)
   - False positive handling

3. **Dependency Verifier** (15 tests)
   - Import extraction (Python, JS)
   - Availability checking (mocked docker exec)
   - Caching behavior
   - Missing dependency detection

4. **Quality Scorer** (20 tests)
   - Complexity calculation (simple, complex, nested)
   - Documentation scoring (docstrings, comments)
   - Best practices (type hints, error handling)
   - Edge cases (empty functions, generators)

5. **Output Composite Validator** (15 tests)
   - Decision logic (APPROVE/REJECT/MANUAL_REVIEW)
   - Threshold enforcement
   - Blocking issue detection
   - Integration with all validators

#### **Integration Test Scenarios**

**Scenario 1: Perfect Code** (Expected: AUTO-APPROVE)
```python
# Generated code: semantic_analyzer.py (perfect quality)
"""Semantic analyzer for risk assessment."""
from typing import Dict, Any

def analyze_risk(instruction: str) -> Dict[str, Any]:
    """Analyze instruction risk level.

    Args:
        instruction: User instruction text

    Returns:
        Risk assessment dictionary
    """
    # Implementation...
    return {"risk": "LOW", "confidence": 0.9}

# Expected validation result:
{
  "decision": "APPROVE",
  "overall_score": 95,
  "syntax": {"valid": true},
  "security": {"severity": "LOW", "findings": []},
  "dependencies": {"all_available": true},
  "quality": {"score": 95, "issues": []}
}
```

**Scenario 2: Syntax Errors** (Expected: AUTO-REJECT)
```python
# Generated code with syntax error
def calculate(x:  # Missing closing paren
    return x * 2

# Expected validation result:
{
  "decision": "REJECT",
  "overall_score": 0,
  "syntax": {
    "valid": false,
    "errors": ["SyntaxError: invalid syntax at line 1"]
  },
  "blocking_issues": ["Syntax errors prevent deployment"]
}
```

**Scenario 3: Security Issues** (Expected: AUTO-REJECT)
```python
# Generated code with hardcoded secret
API_KEY = "sk-1234567890abcdef"

def call_api():
    return requests.get("https://api.example.com", headers={"Authorization": API_KEY})

# Expected validation result:
{
  "decision": "REJECT",
  "overall_score": 20,
  "security": {
    "severity": "CRITICAL",
    "findings": [{
      "pattern": "hardcoded_api_key",
      "line": 1,
      "context": "API_KEY = \"sk-1234...\""
    }]
  },
  "blocking_issues": ["CRITICAL security finding: hardcoded secret"]
}
```

**Scenario 4: Missing Dependencies** (Expected: MANUAL_REVIEW)
```python
# Generated code with missing dependency
import nltk  # Not installed in environment

def analyze_text(text: str):
    tokens = nltk.word_tokenize(text)
    return tokens

# Expected validation result:
{
  "decision": "MANUAL_REVIEW",
  "overall_score": 60,
  "dependencies": {
    "all_available": false,
    "missing": ["nltk"]
  },
  "recommendation": "Install missing dependency: pip install nltk"
}
```

**Scenario 5: Test Failures** (Expected: MANUAL_REVIEW)
```python
# Generated code passes all checks except tests fail
# semantic_analyzer.py (good code)
# test_semantic_analyzer.py (2 tests fail)

# Expected validation result:
{
  "decision": "MANUAL_REVIEW",
  "overall_score": 65,
  "tests": {
    "passed": 8,
    "failed": 2,
    "errors": [
      "test_risk_assessment: AssertionError",
      "test_blast_radius: TypeError"
    ]
  },
  "recommendation": "Fix 2 failing tests before deployment"
}
```

#### **Performance Testing**

**Requirements**:
- Validation completes within 30 seconds for typical code (< 500 lines)
- Validation completes within 60 seconds for large code (500-2000 lines)
- No memory leaks during repeated validations
- Supports concurrent validations (up to 5 workers simultaneously)

**Test Cases**:
1. Small file (100 lines) → < 5 seconds
2. Medium file (500 lines) → < 30 seconds
3. Large file (2000 lines) → < 60 seconds
4. 10 concurrent validations → No failures, queue handled

#### **End-to-End Test**

**Full AI Worker Pipeline Test**:
```bash
# 1. Create test worker instruction
cat > test_worker.md <<EOF
TASK: Generate semantic analyzer
DELIVERABLES:
- wingman/validation/test_semantic.py (100 lines)
- wingman/tests/test_semantic.py (50 lines)
SUCCESS_CRITERIA:
- All tests pass
- No security issues
EOF

# 2. Simulate worker execution (manual for testing)
# Generate code → Save to files

# 3. Call output validation endpoint
curl -X POST http://localhost:8101/output_validation/validate \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "TEST_WORKER_001",
    "generated_files": [
      "wingman/validation/test_semantic.py",
      "wingman/tests/test_semantic.py"
    ],
    "task_name": "Test Semantic Analyzer"
  }'

# 4. Verify response
# Expected: validation_report with decision

# 5. Check database
docker exec wingman-test-postgres psql -U wingman -d wingman \
  -c "SELECT * FROM output_validations WHERE worker_id = 'TEST_WORKER_001';"

# 6. Check Telegram notification received
```

### 2.6 Success Criteria

#### **Technical Success Criteria**

- ✅ **SR-1**: All 4 core validators implemented and tested (80%+ coverage)
- ✅ **SR-2**: OutputCompositeValidator makes correct decisions (95%+ accuracy on test cases)
- ✅ **SR-3**: API endpoint integrated with approval flow
- ✅ **SR-4**: Database schema deployed to TEST
- ✅ **SR-5**: All integration tests pass in TEST environment
- ✅ **SR-6**: Validation completes within 30 seconds for typical code
- ✅ **SR-7**: No false positives on known-good code samples
- ✅ **SR-8**: Documentation complete (user guide + ops guide)

#### **Business Success Criteria**

- ✅ **BSR-1**: Prevents repeat of previous AI worker failures (syntax errors, missing deps)
- ✅ **BSR-2**: Reduces manual code review time (auto-approve safe code)
- ✅ **BSR-3**: Increases confidence in AI worker output (validated before deployment)
- ✅ **BSR-4**: Provides actionable feedback to workers (specific error messages)
- ✅ **BSR-5**: Maintains security standards (blocks secrets, dangerous patterns)

#### **Operational Success Criteria**

- ✅ **OSR-1**: System runs in TEST for 48 hours without errors
- ✅ **OSR-2**: Validation reports are clear and actionable
- ✅ **OSR-3**: Operators can tune thresholds without code changes
- ✅ **OSR-4**: Rollback plan exists and tested
- ✅ **OSR-5**: Monitoring alerts work (Watcher integration)

---

## SECTION 3: PHASE 6.2 - INCREMENTAL EXECUTION CONTROL (FUTURE)

### 3.1 Overview

**Purpose**: Enforce "test 1 worker before running 225" pattern to prevent batch failures

**Current Problem**: No checkpoints during batch execution. If first worker fails, all 225 workers repeat the same mistake.

**Solution**: Checkpoint-based execution with mandatory approvals at milestones.

### 3.2 High-Level Requirements

**FR-1: Execution Checkpoints**
- Define checkpoints: Worker 1, 10, 25, 50, 100, 225
- At each checkpoint, require approval to continue
- Store checkpoint state (can resume if interrupted)

**FR-2: Checkpoint Validation**
- At each checkpoint, run output validation on completed workers
- Calculate success rate (passed / total)
- If success rate < 80% → STOP, require manual intervention

**FR-3: Approval Integration**
- Create approval request at each checkpoint
- Telegram notification: "Checkpoint 10: 9/10 passed, continue?"
- Mark approves → Continue to next checkpoint
- Mark rejects → Stop execution, debug failures

### 3.3 Architecture Overview

```
Batch Request: "Run 225 workers"
         ↓
┌────────────────────────────────────┐
│  Execution Controller               │
│  - Tracks progress (0/225)          │
│  - Identifies checkpoints           │
│  - Requests approvals               │
└────────────────────────────────────┘
         ↓
Checkpoint 1: Worker 1 complete
         ↓
Run Output Validation → Result?
         ↓
If PASS → Request approval "Continue to workers 2-10?"
If FAIL → STOP, create approval "Worker 1 failed, debug?"
         ↓
Mark approves → Continue
         ↓
Checkpoint 2: Workers 2-10 complete (9/10 passed)
         ↓
Request approval "9/10 passed (90%), continue to 25?"
         ↓
... (repeat for checkpoints 25, 50, 100, 225)
```

### 3.4 Dependencies

**Depends on Phase 6.1**: Output validation must exist to validate checkpoints

**Estimated Effort**: 8-12 hours
- Task 6.2.1: Execution controller (4-6 hours)
- Task 6.2.2: Checkpoint approval integration (2-3 hours)
- Task 6.2.3: Progress tracking & resume (2-3 hours)

---

## SECTION 4: PHASE 6.3 - ENVIRONMENT VERIFICATION (FUTURE)

### 4.1 Overview

**Purpose**: Pre-flight checks before execution (verify dependencies, tools, access)

**Current Problem**: Workers execute without verifying required tools exist, leading to failures after code generation.

**Solution**: Environment verification endpoint that checks prerequisites before approval.

### 4.2 High-Level Requirements

**FR-1: Dependency Parsing**
- Parse instruction for required dependencies (libraries, tools, services)
- Extract from DELIVERABLES and SUCCESS_CRITERIA sections
- Support: pip packages, npm packages, system tools

**FR-2: Availability Checking**
- Check pip packages: `pip list | grep <package>`
- Check npm packages: `npm list <package>`
- Check system tools: `which <tool>`
- Check services: `curl <service>/health`

**FR-3: Pre-Approval Integration**
- Run environment checks BEFORE instruction approval
- If environment ready → Approve
- If missing deps → REJECT with instructions to install

### 4.3 Architecture Overview

```
Approval Request: "Install nltk and generate code"
         ↓
┌────────────────────────────────────┐
│  Environment Verifier               │
│  - Parse required dependencies      │
│  - Check availability               │
│  - Generate install instructions    │
└────────────────────────────────────┘
         ↓
Check: pip list | grep nltk
         ↓
If NOT FOUND → REJECT with:
  "Missing dependency: nltk
   Install: pip install nltk
   Then re-submit approval request"
         ↓
If FOUND → Continue with normal approval flow
```

### 4.4 Dependencies

**Independent of Phase 6.1/6.2**: Can be implemented in parallel

**Estimated Effort**: 6-8 hours
- Task 6.3.1: Dependency parser (2-3 hours)
- Task 6.3.2: Availability checker (2-3 hours)
- Task 6.3.3: Pre-approval integration (2-3 hours)

---

## SECTION 5: DEPLOYMENT & ROLLOUT

### 5.1 Phase 6.1 Deployment Plan

#### **Stage 1: Development (DEV Environment)**

**Prerequisites**:
- DEV environment available (local or separate container)
- Python 3.9+ with pip

**Steps**:
1. Create output_validation directory structure
2. Implement validators (SyntaxValidator, OutputSecurityScanner, etc.)
3. Write unit tests (80%+ coverage target)
4. Test locally with sample generated code

**Duration**: During development (parallel with implementation)

#### **Stage 2: TEST Environment Deployment**

**Prerequisites**:
- ✅ All unit tests pass (80%+ coverage)
- ✅ Integration tests written
- ✅ TEST environment healthy (6/6 containers)
- ✅ Database migration ready

**Steps**:

1. **Deploy Database Migration** (REQUIRES APPROVAL)
   ```bash
   # Run migration
   docker exec wingman-test-postgres psql -U wingman -d wingman \
     -f /app/migrations/006_output_validations.sql

   # Verify tables created
   docker exec wingman-test-postgres psql -U wingman -d wingman \
     -c "\dt output_validations"
   ```

2. **Deploy Code to TEST**
   ```bash
   # Build TEST containers with new code
   docker compose -f docker-compose.yml -p wingman-test build wingman-api

   # Restart API container
   docker compose -f docker-compose.yml -p wingman-test up -d wingman-api

   # Verify health
   curl http://localhost:8101/health
   ```

3. **Run Integration Tests**
   ```bash
   # Test output validation endpoint
   pytest tests/integration/test_output_validation.py -v

   # Test with sample generated code
   curl -X POST http://localhost:8101/output_validation/validate \
     -H "Content-Type: application/json" \
     -d @test_data/sample_validation_request.json
   ```

4. **Monitor for 48 Hours**
   - Check logs for errors
   - Verify Telegram notifications work
   - Test validation with real AI worker output
   - Tune thresholds if needed

**Success Criteria**:
- ✅ All integration tests pass
- ✅ Endpoint responds correctly
- ✅ Database writes successful
- ✅ Telegram notifications delivered
- ✅ No errors in 48-hour monitoring period

#### **Stage 3: PRD Environment Deployment**

**Prerequisites**:
- ✅ TEST deployment successful (48 hours stable)
- ✅ All success criteria met
- ✅ User approval for PRD deployment

**Steps**:

1. **Database Migration (REQUIRES APPROVAL)**
   ```bash
   # Backup PRD database first
   docker exec wingman-prd-postgres pg_dump -U wingman wingman > backup_prd_$(date +%Y%m%d).sql

   # Run migration
   docker exec wingman-prd-postgres psql -U wingman -d wingman \
     -f /app/migrations/006_output_validations.sql
   ```

2. **Deploy to PRD (REQUIRES APPROVAL)**
   ```bash
   # Build PRD containers
   docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd build wingman-api

   # Restart API (brief downtime)
   docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d wingman-api
   ```

3. **Validation Smoke Test**
   ```bash
   # Health check
   curl http://localhost:5001/health

   # Test validation endpoint
   curl -X POST http://localhost:5001/output_validation/validate \
     -H "Content-Type: application/json" \
     -d @test_data/sample_validation_request.json
   ```

4. **Monitor PRD for 7 Days**
   - Watch for validation errors
   - Monitor approval flow integration
   - Collect metrics (auto-approve rate, auto-reject rate)
   - Tune thresholds based on real usage

**Rollback Plan**:
If deployment fails:
1. Stop PRD API container
2. Restore previous image (git checkout previous commit)
3. Rebuild and restart
4. Restore database from backup (if migration failed)

### 5.2 Feature Flags

**Environment Variables** (for gradual rollout):

```bash
# .env.test / .env.prd

# Enable/disable output validation
OUTPUT_VALIDATION_ENABLED=1  # 1=enabled, 0=disabled

# Rollout percentage (for gradual deployment)
OUTPUT_VALIDATION_ROLLOUT_PERCENT=100  # 0-100

# Validation strictness
OUTPUT_VALIDATION_AUTO_APPROVE_THRESHOLD=70  # 0-100
OUTPUT_VALIDATION_AUTO_REJECT_THRESHOLD=30   # 0-100

# Timeout settings
OUTPUT_VALIDATION_TIMEOUT=30  # seconds
```

**Gradual Rollout Strategy**:
1. Deploy to PRD with `OUTPUT_VALIDATION_ENABLED=0` (disabled, code deployed but not active)
2. Enable for 10% of requests (`ROLLOUT_PERCENT=10`)
3. Monitor for 48 hours
4. Increase to 50% if no issues
5. Increase to 100% after 7 days of stability

### 5.3 Monitoring & Metrics

**Key Metrics to Track**:

1. **Validation Volume**
   ```sql
   SELECT COUNT(*), decision
   FROM output_validations
   WHERE created_at > NOW() - INTERVAL '24 hours'
   GROUP BY decision;
   ```

2. **Auto-Approve Rate**
   ```sql
   SELECT COUNT(*) FILTER (WHERE decision = 'APPROVE') * 100.0 / COUNT(*)
   FROM output_validations
   WHERE created_at > NOW() - INTERVAL '24 hours';
   ```
   - **Expected**: 20-40% (good code auto-approved)
   - **Alert if**: <10% (too strict) or >60% (too lenient)

3. **Auto-Reject Rate**
   ```sql
   SELECT COUNT(*) FILTER (WHERE decision = 'REJECT') * 100.0 / COUNT(*)
   FROM output_validations
   WHERE created_at > NOW() - INTERVAL '24 hours';
   ```
   - **Expected**: 10-30% (catching bad code)
   - **Alert if**: >50% (too many rejections, tune thresholds)

4. **Validation Duration**
   ```sql
   SELECT AVG(validation_duration), MAX(validation_duration)
   FROM output_validations
   WHERE created_at > NOW() - INTERVAL '24 hours';
   ```
   - **Expected**: <10 seconds average
   - **Alert if**: >30 seconds average (performance issue)

5. **Security Findings**
   ```sql
   SELECT COUNT(*), security_result->>'severity'
   FROM output_validations
   WHERE security_result->>'severity' IN ('CRITICAL', 'HIGH')
     AND created_at > NOW() - INTERVAL '7 days'
   GROUP BY security_result->>'severity';
   ```
   - **Alert if**: Any CRITICAL findings

**Watcher Integration**:
- Watcher monitors `output_validations` table
- Alerts if validation failure rate >50% in 1 hour
- Alerts if any CRITICAL security findings
- Weekly digest of validation metrics

---

## SECTION 6: RISK ASSESSMENT & MITIGATION

### 6.1 Technical Risks

#### **Risk 1: Validation Performance** (MEDIUM)

**Description**: Output validation may be slow for large generated code (>1000 lines), blocking approval flow.

**Impact**: Delays in approval, user frustration

**Mitigation**:
- Set timeout (30 seconds default, configurable)
- Run validation asynchronously (return immediately, notify when complete)
- Optimize syntax validation (cache parsed AST)
- Use threading for parallel validator execution

**Monitoring**: Track validation duration, alert if >30 seconds average

#### **Risk 2: False Positives** (HIGH)

**Description**: Validators may incorrectly flag safe code as dangerous (e.g., legitimate use of `eval()` in sandbox).

**Impact**: Good code rejected, manual review burden increases

**Mitigation**:
- Tune thresholds conservatively (start strict, loosen based on data)
- Add whitelist/exception mechanism (mark patterns as safe)
- Detailed validation reports (help users understand why rejected)
- Track false positive rate (metric: rejected code manually approved)

**Monitoring**: Weekly review of auto-rejected code that was manually approved

#### **Risk 3: Dependency Verification False Negatives** (MEDIUM)

**Description**: DependencyVerifier may miss imports (e.g., dynamic imports, relative imports).

**Impact**: Missing dependencies not detected, code fails at runtime

**Mitigation**:
- Conservative approach: Flag unknown imports for manual review
- Improve import extraction (handle relative imports, __import__, importlib)
- Add manual override (user confirms dependencies available)

**Monitoring**: Track runtime failures due to missing dependencies

#### **Risk 4: Docker Exec Failures** (LOW)

**Description**: Dependency checking relies on `docker exec` which may fail (container down, network issues).

**Impact**: Validation fails, blocks approval

**Mitigation**:
- Retry logic (3 attempts with exponential backoff)
- Fallback to manual review if docker unavailable
- Clear error messages ("Validation failed: docker unavailable, manual review required")

**Monitoring**: Track validation errors, alert if docker exec fails repeatedly

### 6.2 Operational Risks

#### **Risk 5: Database Growth** (LOW)

**Description**: `output_validations` table may grow large over time (1000+ validations/day).

**Impact**: Slower queries, increased storage

**Mitigation**:
- Add retention policy (delete validations >30 days old)
- Partition table by date (if growth >10K rows/day)
- Archive old validations to separate table

**Monitoring**: Weekly check of table size, alert if >100K rows

#### **Risk 6: Threshold Tuning Required** (MEDIUM)

**Description**: Initial thresholds (auto-approve 70, auto-reject 30) may not match real-world usage.

**Impact**: Too many manual reviews (low auto-approve rate) or too many false approvals (high auto-approve rate)

**Mitigation**:
- Gradual rollout (collect data before full deployment)
- Document tuning procedure (adjust thresholds based on metrics)
- A/B testing (test different thresholds on subset of requests)

**Monitoring**: Weekly review of auto-approve/reject rates, adjust thresholds as needed

### 6.3 Security Risks

#### **Risk 7: Malicious Code Bypass** (HIGH)

**Description**: Sophisticated attacker may craft code that passes validation but contains hidden vulnerabilities.

**Impact**: Malicious code deployed, security breach

**Mitigation**:
- Multiple validation layers (syntax + security + quality)
- Conservative auto-approve (high threshold 70+)
- Manual review for complex/unusual code patterns
- Output validation is defense-in-depth (not sole security measure)
- Execution Gateway still enforces approval for privileged operations

**Monitoring**: Security team review of auto-approved code (sample audits)

#### **Risk 8: Secrets Leak Through Comments** (MEDIUM)

**Description**: OutputSecurityScanner may miss secrets in comments or docstrings.

**Impact**: Secrets committed to repo

**Mitigation**:
- Scan comments and docstrings (not just code)
- Entropy-based detection (high-entropy strings likely secrets)
- Pre-commit hooks (backup layer)

**Monitoring**: Quarterly audit of committed code for secrets

### 6.4 Business Risks

#### **Risk 9: User Resistance** (LOW)

**Description**: Users may view output validation as "slowing them down" or "blocking productivity".

**Impact**: Workarounds, bypassing validation

**Mitigation**:
- Clear communication (why validation helps)
- Fast validation (<10 seconds typical)
- Actionable error messages (help users fix issues)
- Auto-approve safe code (reduce manual review burden)

**Monitoring**: User feedback, approval rejection rate

#### **Risk 10: Implementation Delay** (MEDIUM)

**Description**: Implementation may take longer than estimated (16-24 hours), delaying AI worker reliability improvements.

**Impact**: AI workers remain unreliable, continued failures

**Mitigation**:
- Incremental delivery (Phase 6.1.1 → 6.1.2 → 6.1.3)
- MVP first (core validators, basic integration)
- Defer nice-to-haves (quality scorer can be simplified)

**Monitoring**: Daily progress tracking, adjust scope if behind schedule

---

## SECTION 7: ALTERNATIVE APPROACHES CONSIDERED

### 7.1 Alternative 1: LLM-Based Code Review

**Approach**: Use LLM (e.g., GPT-4, Claude) to review generated code quality.

**Pros**:
- More sophisticated analysis (understands context, logic)
- Can provide detailed feedback (refactoring suggestions)

**Cons**:
- Slow (5-15 seconds per review)
- Expensive ($0.01-0.10 per review)
- Non-deterministic (same code may get different scores)
- Requires external API dependency

**Decision**: NOT CHOSEN
- Heuristic-based validation is faster, cheaper, deterministic
- Can add LLM review as optional enhancement later (Phase 6.4)

### 7.2 Alternative 2: Static Analysis Tools (Pylint, Flake8)

**Approach**: Use existing static analysis tools for validation.

**Pros**:
- Battle-tested (Pylint, Flake8, Bandit mature tools)
- Comprehensive (many rules built-in)

**Cons**:
- Heavyweight (slow for large code)
- Noisy (many false positives)
- Requires configuration (tune rules for our use case)
- Adds dependencies (install tools in container)

**Decision**: PARTIALLY ADOPTED
- Use static analysis as optional enhancement (Phase 6.5)
- Start with lightweight heuristic validation (Phase 6.1)

### 7.3 Alternative 3: Sandboxed Execution

**Approach**: Execute generated code in sandbox, observe behavior.

**Pros**:
- Detects runtime issues (not just static issues)
- Tests actual functionality

**Cons**:
- Complex (requires secure sandbox infrastructure)
- Slow (code execution takes time)
- Dangerous (malicious code may escape sandbox)
- False negatives (code may behave differently in prod)

**Decision**: NOT CHOSEN
- Risk/complexity too high for Phase 6.1
- Test execution (FR-4) provides similar benefit with less risk

---

## SECTION 8: SUCCESS METRICS & KPIs

### 8.1 Phase 6.1 Success Metrics

**After 30 Days of Production Use**:

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Auto-Approve Rate** | 20-40% | % of validations with decision=APPROVE |
| **Auto-Reject Rate** | 10-30% | % of validations with decision=REJECT |
| **False Positive Rate** | <5% | % of rejected code manually approved |
| **Validation Duration** | <10s avg | Average validation time |
| **AI Worker Success Rate** | >80% | % of workers passing validation on first attempt |
| **Security Findings** | >0 CRITICAL | Count of secrets/vulnerabilities detected |
| **Manual Review Reduction** | 30%+ | Reduction in manual code reviews (vs pre-validation) |

### 8.2 Business Impact Metrics

**Cost Savings**:
- **Time Saved**: Avg 30 min/worker (no manual code review for auto-approved)
- **Money Saved**: $0 wasted on failed workers (validation catches issues before API costs)
- **Quality Improved**: 80%+ first-attempt success rate (vs 7% previously)

**Example Calculation** (225 workers):
- **Before**: 3 attempts × 225 workers × 80 min/attempt = 900 hours wasted
- **After**: 1 attempt × 225 workers × 5 min validation = 19 hours
- **Savings**: 881 hours (~110 work days)

### 8.3 Continuous Improvement

**Quarterly Reviews**:
1. Analyze false positive rate → Tune thresholds
2. Review auto-rejected code → Improve validators
3. Collect user feedback → Address pain points
4. Security audit → Validate no secrets leaked

---

## APPENDIX A: GLOSSARY

| Term | Definition |
|------|------------|
| **Output Validation** | Validation of AI worker generated code (vs input instruction validation) |
| **Auto-Approve** | Decision to deploy code without human review (high confidence) |
| **Auto-Reject** | Decision to block code deployment (critical issues detected) |
| **Manual Review** | Decision to request human approval (uncertain quality) |
| **Checkpoint** | Milestone in batch execution requiring approval to continue |
| **Blocking Issue** | Critical problem preventing auto-approval (syntax error, secret, etc.) |
| **Validation Pipeline** | Sequence of validators run to assess code quality |
| **False Positive** | Safe code incorrectly flagged as dangerous |
| **False Negative** | Dangerous code incorrectly flagged as safe |

---

## APPENDIX B: REFERENCES

**Related Documents**:
- [AAA_AI_WORKER_FAILURE_ANALYSIS.md](../07-analysis/AAA_AI_WORKER_FAILURE_ANALYSIS.md) - Post-mortem of previous failures
- [AAA_VALIDATION_ENHANCEMENT_COMPLETE_PLAN.md](AAA_VALIDATION_ENHANCEMENT_COMPLETE_PLAN.md) - Input validation (Phase 2)
- [AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md](../02-architecture/AAA_WINGMAN_ARCHITECTURE_CURRENT_BUILD.md) - Current architecture
- [AAA_WINGMAN_STRATEGY_ROADMAP.md](AAA_WINGMAN_STRATEGY_ROADMAP.md) - Overall roadmap

**Code References**:
- Phase 2 Validators: `wingman/validation/` (990 LOC)
- API Server: `wingman/api_server.py`
- Database Schema: `wingman/migrations/`

---

**Document Status**: DESIGN PHASE - Ready for User Review
**Next Steps**: User approval → Begin Phase 6.1.1 implementation
**Estimated Timeline**: 16-24 hours for Phase 6.1 (output validation)
**Contact**: Mark (Wingman product owner)

---

**END OF DOCUMENT**
