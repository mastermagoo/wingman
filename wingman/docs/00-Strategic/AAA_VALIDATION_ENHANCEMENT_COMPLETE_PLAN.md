# Validation Enhancement - Complete Development/Deployment/Test Plan

**Version**: 1.0  
**Scope**: Wingman strategy/business documentation (DEV/TEST/PRD)  

**Date**: 2026-01-14
**Status**: FINAL PLAN - Ready for Execution
**Estimated Duration**: 24-32 hours (incremental delivery)
**Confidence Level**: HIGH (realistic estimates, no shortcuts)

---

## EXECUTIVE SUMMARY

This plan delivers enhanced validation for Wingman's approval workflow:
- **4 Core Validators**: Semantic, Code Scanner, Dependency, Content Quality
- **Integration Layer**: Composite validator + API integration
- **Deployment**: Incremental TEST → PRD rollout with monitoring
- **Testing**: 50+ tests ensuring reliability

**Success Criteria**: Auto-approve LOW risk, auto-reject CRITICAL risk, manual review MEDIUM/HIGH risk

---

## SECTION 1: BASELINE STATE (CURRENT AS-IS)

### 1.1 Infrastructure (What Exists and Works)

**Docker Services (TEST Environment)**:
```bash
# Verify services running:
docker compose -f docker-compose.yml -p wingman-test ps

Expected services:
- wingman-api (Port 5001) - ✅ RUNNING
- postgres (Port 5432) - ✅ RUNNING
- redis (Port 6379) - ✅ RUNNING
- telegram-bot - ✅ RUNNING
- wingman-watcher - ✅ RUNNING
- ollama (Port 11434) - ✅ RUNNING
```

**Database Schema (Existing Tables)**:
```sql
-- Verify existing tables:
docker exec wingman-test-postgres-1 psql -U wingman -d wingman -c "\dt"

Existing tables:
- approvals (stores approval requests)
- approval_executions (stores execution results)
- workers (worker state tracking)
```

**Python Environment**:
```bash
# Check installed packages in API container:
docker exec wingman-test-wingman-api-1 pip list

Existing packages:
- Flask==2.3.3
- psycopg2-binary==2.9.9
- requests==2.31.0
- PyJWT==2.8.0
```

**Ollama Models**:
```bash
# Check available models:
curl http://localhost:11434/api/tags

Expected models:
- mistral:7b (for semantic analysis)
- Additional models available via Intel-system
```

### 1.2 Code Baseline (What Exists)

**API Server**:
- File: `wingman/proper_wingman_deployment_prd.py` (main API file)
- Approval endpoint: `/approvals/request`
- Current validation: ❌ NONE (stores request, waits for manual approval)

**Stub Files**:
```
wingman/validation/
├── __init__.py (exists, minimal exports)
├── semantic_analyzer.py (STUB - 54 lines, broken)
├── code_scanner.py (STUB - 26 lines, basic only)
├── dependency_analyzer.py (STUB - ~50 lines, skeleton)
├── content_quality_validator.py (STUB - 49 lines, skeleton)
├── composite_validator.py (STUB - ~50 lines, skeleton)
└── tuning_config.py (EMPTY - 0 lines)
```

**Verdict**: Stubs exist but contain no working validation logic.

### 1.3 Documentation (Supporting Files)

**Existing Documentation**:
1. `docs/VALIDATION_ENHANCEMENT_IMPLEMENTATION_PLAN.md` (3,685 lines)
   - Original 52-81 hour plan
   - Detailed requirements for each validator
   - Test specifications

2. `docs/VALIDATION_ENHANCEMENT_GAP_ANALYSIS.md`
   - Current state vs required state
   - Identifies 7 gaps

3. `docs/AI_WORKER_FAILURE_ANALYSIS.md`
   - Post-mortem of AI worker attempts
   - Lessons learned

4. `docs/EXECUTION_GATEWAY_DEPLOYMENT.md`
   - Execution gateway architecture (for reference)

---

## SECTION 2: REQUIREMENTS BASELINE

### 2.1 Functional Requirements

**FR-1: Semantic Analysis**
- Analyze instruction text for risk level (LOW/MEDIUM/HIGH/CRITICAL)
- Identify operation types (read/write/restart/delete)
- Calculate blast radius (MINIMAL/LOW/MEDIUM/HIGH)
- Provide reasoning for risk assessment
- Return confidence score (0.0-1.0)

**FR-2: Code Scanning**
- Detect 30 dangerous patterns (Docker socket, file system, network, etc.)
- Detect 15 secret patterns (API keys, tokens, certificates)
- Classify severity (CRITICAL/HIGH/MEDIUM/LOW)
- Provide context for each finding

**FR-3: Dependency Analysis**
- Map service dependencies (7 services: api, gateway, postgres, redis, telegram, watcher, ollama)
- Calculate blast radius (how many services affected)
- Detect cascade failures
- Identify critical paths

**FR-4: Content Quality Assessment**
- Score 10-point framework sections (DELIVERABLES, SUCCESS_CRITERIA, etc.)
- Each section scored 0-10
- Calculate overall quality score (0-100)
- Provide detailed feedback per section

**FR-5: Composite Validation**
- Combine results from all 4 validators
- Apply business rules:
  - AUTO_APPROVE: risk=LOW, quality>80, no dangerous patterns, blast_radius=MINIMAL
  - AUTO_REJECT: risk=CRITICAL, dangerous patterns found, secrets detected
  - MANUAL_REVIEW: Everything else
- Generate validation report for Telegram

**FR-6: API Integration**
- Call validation on every approval request
- Store validation results in database
- Send formatted report to Telegram
- Handle auto-approve/reject decisions
- Fallback to manual review on validation errors

### 2.2 Non-Functional Requirements

**NFR-1: Performance**
- Validation completes within 10 seconds
- LLM timeout: 30 seconds (with retry)
- No blocking of approval submission

**NFR-2: Reliability**
- Validation errors don't block approvals (fallback to manual review)
- Retry logic for LLM failures (3 attempts)
- Graceful degradation if Ollama unavailable

**NFR-3: Observability**
- Log all validation attempts
- Store validation history in database
- Include execution time in logs

**NFR-4: Security**
- No secrets in validation logs
- Validation runs in API container (no new attack surface)
- Pattern matching doesn't execute code

### 2.3 Acceptance Criteria

**AC-1**: Submit LOW risk request → Auto-approved within 10 seconds
**AC-2**: Submit CRITICAL risk request → Auto-rejected with explanation
**AC-3**: Submit MEDIUM risk request → Manual review with detailed report
**AC-4**: Submit malformed request → Validation fails gracefully, manual review triggered
**AC-5**: Ollama timeout → Fallback heuristics work, request processed
**AC-6**: All validation results visible in Telegram notification
**AC-7**: Validation history queryable from database

---

## SECTION 3: DEVELOPMENT PLAN (INCREMENTAL DELIVERY)

### Phase 1: Core Validators (16-20 hours)

#### Task 1.1: Semantic Analyzer (4-5 hours)

**Objective**: Build LLM-based semantic analysis with fallback heuristics

**File**: `wingman/validation/semantic_analyzer.py`

**Implementation Steps**:

1. **Environment Verification** (30 minutes)
```bash
# Test Ollama access from API container
docker exec wingman-test-wingman-api-1 python3 -c "
import requests
resp = requests.post('http://ollama:11434/api/generate',
    json={'model': 'mistral', 'prompt': 'Say OK', 'stream': False},
    timeout=10)
print(resp.json())
"
```

2. **Write Core Function** (2 hours)
```python
# Function signature:
def analyze_instruction(instruction: str, task_name: str, deployment_env: str) -> Dict[str, Any]:
    """
    Analyze instruction semantics using LLM with fallback.

    Returns:
    {
        "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
        "operation_types": ["read", "write", "restart", ...],
        "blast_radius": "MINIMAL|LOW|MEDIUM|HIGH",
        "reasoning": "why this risk level",
        "confidence": 0.0-1.0,
        "method": "llm|heuristic"
    }
    """
```

**LLM Prompt Template**:
```python
SEMANTIC_ANALYSIS_PROMPT = """Analyze this deployment instruction for risk:

INSTRUCTION:
{instruction}

TASK: {task_name}
ENVIRONMENT: {deployment_env}

Provide JSON response:
{{
    "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "operation_types": ["read", "write", "restart", "delete", "network"],
    "blast_radius": "MINIMAL|LOW|MEDIUM|HIGH",
    "reasoning": "Brief explanation of risk assessment"
}}

Rules:
- CRITICAL: Affects production data, deletes volumes, exposes secrets
- HIGH: Restarts services, modifies configs, network changes
- MEDIUM: Reads sensitive data, modifies non-critical configs
- LOW: Read-only operations, test environment changes
"""
```

3. **Add Retry Logic** (1 hour)
```python
def _call_llm_with_retry(prompt: str, max_attempts: int = 3) -> Dict:
    for attempt in range(max_attempts):
        try:
            response = requests.post(
                'http://ollama:11434/api/generate',
                json={
                    'model': 'mistral',
                    'prompt': prompt,
                    'stream': False,
                    'options': {'temperature': 0.1}
                },
                timeout=30
            )
            result = response.json()
            return _extract_json(result['response'])
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

4. **Add Fallback Heuristics** (1 hour)
```python
def _fallback_heuristic_analysis(instruction: str, deployment_env: str) -> Dict:
    """Heuristic analysis when LLM unavailable"""
    risk_keywords = {
        'CRITICAL': ['rm -rf', 'drop table', 'delete', '--force', 'prod', 'production'],
        'HIGH': ['restart', 'stop', 'kill', 'down', 'rebuild'],
        'MEDIUM': ['modify', 'update', 'change', 'edit'],
        'LOW': ['read', 'list', 'show', 'get', 'test']
    }
    # Simple keyword matching logic
```

5. **Write Unit Tests** (1.5 hours)
```python
# File: wingman/tests/test_semantic_analyzer.py

def test_analyze_low_risk():
    result = analyze_instruction(
        "List all Docker containers",
        "Status Check",
        "test"
    )
    assert result['risk_level'] == 'LOW'

def test_analyze_critical_risk():
    result = analyze_instruction(
        "docker compose down -v --remove-orphans",
        "Delete Production Volumes",
        "prd"
    )
    assert result['risk_level'] == 'CRITICAL'

def test_llm_timeout_fallback():
    # Mock Ollama timeout, verify heuristics work
    pass
```

**Deliverables**:
- ✅ `wingman/validation/semantic_analyzer.py` (150-200 lines)
- ✅ `wingman/tests/test_semantic_analyzer.py` (10 tests)
- ✅ Verified working in TEST environment

**Validation**:
```bash
cd wingman
python3 -c "from validation.semantic_analyzer import analyze_instruction; print(analyze_instruction('docker ps', 'test', 'test'))"
pytest tests/test_semantic_analyzer.py -v
```

**Checkpoint**: If this fails, STOP and debug before continuing.

---

#### Task 1.2: Code Scanner (3-4 hours)

**Objective**: Detect dangerous patterns and secrets in instruction text

**File**: `wingman/validation/code_scanner.py`

**Implementation Steps**:

1. **Define Pattern Database** (1.5 hours)
```python
DANGEROUS_PATTERNS = {
    # Docker socket access
    'DOCKER_SOCKET': {
        'pattern': r'/var/run/docker\.sock',
        'severity': 'CRITICAL',
        'description': 'Direct Docker socket access'
    },
    # File system operations
    'FILE_DELETE': {
        'pattern': r'rm\s+-rf|rmdir|del\s+/s',
        'severity': 'HIGH',
        'description': 'Recursive file deletion'
    },
    # Network operations
    'NETWORK_EXPOSE': {
        'pattern': r'0\.0\.0\.0|EXPOSE\s+\d+',
        'severity': 'MEDIUM',
        'description': 'Network exposure'
    },
    # ... 27 more patterns
}

SECRET_PATTERNS = {
    'API_KEY': r'api[_-]?key[\s:=]+[\'"]?[\w-]{20,}',
    'AWS_KEY': r'AKIA[0-9A-Z]{16}',
    'PRIVATE_KEY': r'-----BEGIN .* PRIVATE KEY-----',
    # ... 12 more patterns
}
```

2. **Implement Scanner** (1 hour)
```python
def scan_instruction(instruction: str) -> Dict[str, Any]:
    """
    Scan instruction for dangerous patterns and secrets.

    Returns:
    {
        "dangerous_patterns": [
            {
                "type": "DOCKER_SOCKET",
                "severity": "CRITICAL",
                "match": "/var/run/docker.sock",
                "line": 5,
                "context": "... -v /var/run/docker.sock:/var/run/docker.sock ..."
            }
        ],
        "secrets_found": [
            {
                "type": "API_KEY",
                "severity": "CRITICAL",
                "location": "line 10",
                "redacted": "api_key=XXX...XXX"
            }
        ],
        "risk_score": 0-100,
        "auto_reject": True/False
    }
    """
```

3. **Write Tests** (1-1.5 hours)
```python
def test_detect_docker_socket():
    result = scan_instruction("docker run -v /var/run/docker.sock:/var/run/docker.sock")
    assert len(result['dangerous_patterns']) > 0
    assert result['dangerous_patterns'][0]['type'] == 'DOCKER_SOCKET'

def test_detect_api_key():
    result = scan_instruction("export API_KEY=sk_test_abcdef123456")
    assert len(result['secrets_found']) > 0

def test_clean_instruction():
    result = scan_instruction("docker ps")
    assert len(result['dangerous_patterns']) == 0
    assert result['auto_reject'] == False
```

**Deliverables**:
- ✅ `wingman/validation/code_scanner.py` (200-250 lines)
- ✅ `wingman/tests/test_code_scanner.py` (10 tests)

**Validation**:
```bash
cd wingman
pytest tests/test_code_scanner.py -v
```

---

#### Task 1.3: Dependency Analyzer (4-5 hours)

**Objective**: Map service dependencies and calculate blast radius

**File**: `wingman/validation/dependency_analyzer.py`

**Implementation Steps**:

1. **Define Service Topology** (1 hour)
```python
SERVICE_TOPOLOGY = {
    'wingman-api': {
        'depends_on': ['postgres', 'redis', 'ollama'],
        'critical': True,
        'blast_radius_weight': 10
    },
    'execution-gateway': {
        'depends_on': ['postgres', 'redis'],
        'critical': True,
        'blast_radius_weight': 8
    },
    'postgres': {
        'depends_on': [],
        'critical': True,
        'blast_radius_weight': 10
    },
    'redis': {
        'depends_on': [],
        'critical': False,
        'blast_radius_weight': 5
    },
    'telegram-bot': {
        'depends_on': ['wingman-api'],
        'critical': False,
        'blast_radius_weight': 3
    },
    'wingman-watcher': {
        'depends_on': ['wingman-api'],
        'critical': False,
        'blast_radius_weight': 3
    },
    'ollama': {
        'depends_on': [],
        'critical': False,
        'blast_radius_weight': 5
    }
}
```

2. **Implement Dependency Detection** (1.5 hours)
```python
def analyze_dependencies(instruction: str, deployment_env: str) -> Dict[str, Any]:
    """
    Analyze service dependencies affected by instruction.

    Returns:
    {
        "affected_services": ["postgres", "wingman-api"],
        "blast_radius": "HIGH",
        "cascade_risk": True/False,
        "critical_services_affected": ["postgres"],
        "dependency_tree": {...},
        "risk_score": 0-100
    }
    """
    # Parse instruction for service names
    # Build dependency graph
    # Calculate blast radius
```

3. **Implement Blast Radius Calculator** (1.5 hours)
```python
def calculate_blast_radius(affected_services: List[str]) -> str:
    """
    Calculate blast radius based on affected services.

    Rules:
    - MINIMAL: 1 non-critical service
    - LOW: 1-2 non-critical services
    - MEDIUM: 1 critical service OR 3+ non-critical
    - HIGH: 2+ critical services
    """
    total_weight = sum(
        SERVICE_TOPOLOGY[svc]['blast_radius_weight']
        for svc in affected_services
    )

    if total_weight >= 20:
        return 'HIGH'
    elif total_weight >= 10:
        return 'MEDIUM'
    elif total_weight >= 5:
        return 'LOW'
    else:
        return 'MINIMAL'
```

4. **Write Tests** (1 hour)
```python
def test_detect_postgres_dependency():
    result = analyze_dependencies(
        "docker compose restart postgres",
        "prd"
    )
    assert 'postgres' in result['affected_services']
    assert result['blast_radius'] in ['MEDIUM', 'HIGH']

def test_cascade_detection():
    result = analyze_dependencies(
        "docker compose down postgres",
        "prd"
    )
    assert result['cascade_risk'] == True
    assert 'wingman-api' in result['affected_services']  # Cascades
```

**Deliverables**:
- ✅ `wingman/validation/dependency_analyzer.py` (200-250 lines)
- ✅ `wingman/tests/test_dependency_analyzer.py` (10 tests)

---

#### Task 1.4: Content Quality Validator (4-5 hours)

**Objective**: Score 10-point framework sections

**File**: `wingman/validation/content_quality_validator.py`

**Implementation Steps**:

1. **Define Section Scoring Criteria** (1 hour)
```python
SECTION_CRITERIA = {
    'DELIVERABLES': {
        'weight': 15,
        'checks': [
            'has_file_paths',
            'has_measurable_outputs',
            'uses_checkboxes',
            'specific_not_vague'
        ]
    },
    'SUCCESS_CRITERIA': {
        'weight': 15,
        'checks': [
            'measurable_metrics',
            'testable_conditions',
            'clear_thresholds'
        ]
    },
    # ... 8 more sections
}
```

2. **Implement Parser** (1.5 hours)
```python
def parse_instruction_sections(instruction: str) -> Dict[str, str]:
    """
    Parse instruction into 10-point framework sections.

    Returns:
    {
        "DELIVERABLES": "text content",
        "SUCCESS_CRITERIA": "text content",
        ... 10 sections total
    }
    """
    sections = {}
    current_section = None

    for line in instruction.split('\n'):
        if line.startswith('## '):
            current_section = line[3:].strip()
        elif current_section:
            sections[current_section] = sections.get(current_section, '') + line + '\n'

    return sections
```

3. **Implement Scoring** (2 hours)
```python
def assess_content_quality(instruction: str) -> Dict[str, Any]:
    """
    Assess quality of 10-point framework sections.

    Returns:
    {
        "section_scores": {
            "DELIVERABLES": 8,
            "SUCCESS_CRITERIA": 7,
            ... 10 sections
        },
        "overall_quality": 75,
        "detailed_feedback": {
            "DELIVERABLES": "Good specificity, could add more measurable outputs"
        },
        "pass": True,  # overall_quality >= 60
        "auto_reject": False  # overall_quality < 40
    }
    """
```

4. **Write Tests** (1 hour)
```python
def test_high_quality_instruction():
    instruction = """
    ## 1. DELIVERABLES
    - [ ] Create file: `wingman/validation/test.py`
    - [ ] Implement function with >80% test coverage

    ## 2. SUCCESS_CRITERIA
    - File exists at specified path
    - All 10 tests pass
    - Code coverage >= 80%
    """
    result = assess_content_quality(instruction)
    assert result['overall_quality'] >= 70
    assert result['pass'] == True

def test_poor_quality_instruction():
    instruction = "Do something with Docker"
    result = assess_content_quality(instruction)
    assert result['overall_quality'] < 50
    assert result['auto_reject'] == True
```

**Deliverables**:
- ✅ `wingman/validation/content_quality_validator.py` (250-300 lines)
- ✅ `wingman/tests/test_content_quality_validator.py` (10 tests)

---

### Phase 2: Integration Layer (4-5 hours)

#### Task 2.1: Composite Validator (2-3 hours)

**Objective**: Combine all 4 validators and apply business rules

**File**: `wingman/validation/composite_validator.py`

**Implementation Steps**:

1. **Define Business Rules** (1 hour)
```python
BUSINESS_RULES = {
    'AUTO_APPROVE': {
        'risk_level': 'LOW',
        'min_quality': 80,
        'max_dangerous_patterns': 0,
        'max_secrets': 0,
        'max_blast_radius': 'LOW'
    },
    'AUTO_REJECT': {
        'risk_level': 'CRITICAL',
        'OR': [
            {'dangerous_patterns': '>0'},
            {'secrets_found': '>0'},
            {'blast_radius': 'HIGH'},
            {'quality_score': '<40'}
        ]
    }
}
```

2. **Implement Composite Logic** (1-1.5 hours)
```python
def validate_approval_request(
    instruction: str,
    task_name: str,
    deployment_env: str
) -> Dict[str, Any]:
    """
    Run all validators and combine results.

    Returns:
    {
        "decision": "AUTO_APPROVED|AUTO_REJECTED|MANUAL_REVIEW",
        "composite_score": 0-100,
        "validation_details": {
            "semantic": {...},
            "code_scan": {...},
            "dependencies": {...},
            "quality": {...}
        },
        "reason": "Why this decision was made",
        "telegram_report": "Formatted text for Telegram"
    }
    """
    try:
        # Run all 4 validators
        semantic = analyze_instruction(instruction, task_name, deployment_env)
        code_scan = scan_instruction(instruction)
        dependencies = analyze_dependencies(instruction, deployment_env)
        quality = assess_content_quality(instruction)

        # Apply business rules
        decision = _apply_business_rules(semantic, code_scan, dependencies, quality)

        # Generate report
        report = _format_telegram_report(decision, semantic, code_scan, dependencies, quality)

        return {
            "decision": decision,
            "validation_details": {...},
            "telegram_report": report
        }
    except Exception as e:
        # Fallback to manual review on any error
        return {
            "decision": "MANUAL_REVIEW",
            "reason": f"Validation error: {str(e)}"
        }
```

3. **Write Tests** (1 hour)
```python
def test_auto_approve_decision():
    # LOW risk, high quality, no issues
    result = validate_approval_request(
        "docker ps",
        "List containers",
        "test"
    )
    assert result['decision'] == 'AUTO_APPROVED'

def test_auto_reject_decision():
    # CRITICAL risk with secrets
    result = validate_approval_request(
        "export API_KEY=sk_test_123 && docker rm -rf /data",
        "Delete production data",
        "prd"
    )
    assert result['decision'] == 'AUTO_REJECTED'

def test_manual_review_fallback():
    # Validation error should trigger manual review
    # Mock validator exception
    pass
```

**Deliverables**:
- ✅ `wingman/validation/composite_validator.py` (200-250 lines)
- ✅ `wingman/tests/test_composite_validator.py` (10 tests)

---

#### Task 2.2: API Integration (2-3 hours)

**Objective**: Connect validation to approval flow

**File**: `wingman/proper_wingman_deployment_prd.py` (modify existing)

**Implementation Steps**:

1. **Add Database Table** (30 minutes)
```sql
-- Create validation results table
CREATE TABLE validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_id UUID REFERENCES approvals(id),
    decision VARCHAR(20) NOT NULL,  -- AUTO_APPROVED, AUTO_REJECTED, MANUAL_REVIEW
    composite_score INTEGER,
    semantic_analysis JSONB,
    code_scan_results JSONB,
    dependency_analysis JSONB,
    quality_assessment JSONB,
    telegram_report TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_validation_approval ON validation_results(approval_id);
```

2. **Modify Approval Endpoint** (1 hour)
```python
# In proper_wingman_deployment_prd.py:

from validation.composite_validator import validate_approval_request

@app.route('/approvals/request', methods=['POST'])
def request_approval():
    data = request.json
    instruction = data['instruction']
    task_name = data['task_name']
    deployment_env = data['deployment_env']

    # Store approval request
    approval_id = _store_approval_request(data)

    # NEW: Run validation
    try:
        validation_result = validate_approval_request(
            instruction,
            task_name,
            deployment_env
        )

        # Store validation results
        _store_validation_result(approval_id, validation_result)

        # Handle auto-approve/reject
        if validation_result['decision'] == 'AUTO_APPROVED':
            _auto_approve(approval_id)
        elif validation_result['decision'] == 'AUTO_REJECTED':
            _auto_reject(approval_id, validation_result['reason'])

        # Send to Telegram (always, with validation report)
        _send_telegram_notification(
            approval_id,
            validation_result['telegram_report']
        )

    except Exception as e:
        # Validation error - fallback to manual review
        logger.error(f"Validation error: {e}")
        _send_telegram_notification(
            approval_id,
            "⚠️ Validation error - Manual review required"
        )

    return jsonify({
        "approval_id": approval_id,
        "validation": validation_result.get('decision', 'MANUAL_REVIEW')
    })
```

3. **Add Helper Functions** (1 hour)
```python
def _store_validation_result(approval_id: str, result: Dict):
    """Store validation result in database"""
    cursor.execute("""
        INSERT INTO validation_results
        (approval_id, decision, composite_score, semantic_analysis,
         code_scan_results, dependency_analysis, quality_assessment, telegram_report)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        approval_id,
        result['decision'],
        result.get('composite_score'),
        json.dumps(result['validation_details']['semantic']),
        json.dumps(result['validation_details']['code_scan']),
        json.dumps(result['validation_details']['dependencies']),
        json.dumps(result['validation_details']['quality']),
        result['telegram_report']
    ))

def _auto_approve(approval_id: str):
    """Auto-approve request"""
    cursor.execute("""
        UPDATE approvals
        SET status = 'AUTO_APPROVED', approved_at = NOW()
        WHERE id = %s
    """, (approval_id,))

def _auto_reject(approval_id: str, reason: str):
    """Auto-reject request"""
    cursor.execute("""
        UPDATE approvals
        SET status = 'AUTO_REJECTED', rejected_at = NOW(), rejection_reason = %s
        WHERE id = %s
    """, (reason, approval_id))
```

4. **Write Integration Tests** (1 hour)
```bash
# Test full approval flow
curl -X POST http://localhost:5001/approvals/request \
  -H "Content-Type: application/json" \
  -d @test_approval_low_risk.json

# Verify validation result stored
docker exec wingman-test-postgres-1 psql -U wingman -d wingman \
  -c "SELECT decision, composite_score FROM validation_results ORDER BY created_at DESC LIMIT 1;"

# Verify Telegram notification sent
# Check Telegram for message with validation report
```

**Deliverables**:
- ✅ Modified `proper_wingman_deployment_prd.py` (+150 lines)
- ✅ Database migration SQL script
- ✅ Integration test scripts
- ✅ Verified end-to-end in TEST environment

---

### Phase 3: Testing & Deployment (4-7 hours)

#### Task 3.1: Integration Testing (2-3 hours)

**Test Scenarios**:

1. **Low Risk Auto-Approve** (30 min)
```bash
# Test case: List containers (read-only, test env)
curl -X POST http://localhost:5001/approvals/request -d '{
  "instruction": "docker ps",
  "task_name": "List containers",
  "deployment_env": "test"
}'

# Expected: AUTO_APPROVED within 5 seconds
```

2. **Critical Risk Auto-Reject** (30 min)
```bash
# Test case: Delete production volumes with secrets
curl -X POST http://localhost:5001/approvals/request -d '{
  "instruction": "export API_KEY=sk_test_123 && docker volume rm wingman_postgres_data_prd",
  "task_name": "Delete production data",
  "deployment_env": "prd"
}'

# Expected: AUTO_REJECTED immediately
```

3. **Medium Risk Manual Review** (30 min)
```bash
# Test case: Restart service (medium risk)
curl -X POST http://localhost:5001/approvals/request -d '{
  "instruction": "docker compose restart wingman-api",
  "task_name": "Restart API",
  "deployment_env": "prd"
}'

# Expected: MANUAL_REVIEW with detailed report
```

4. **Validation Error Handling** (30 min)
```bash
# Test case: Malformed instruction
curl -X POST http://localhost:5001/approvals/request -d '{
  "instruction": "",
  "task_name": null,
  "deployment_env": "invalid"
}'

# Expected: MANUAL_REVIEW (fallback)
```

5. **Ollama Timeout** (30 min)
```bash
# Stop Ollama temporarily
docker stop wingman-test-ollama

# Submit request
curl -X POST http://localhost:5001/approvals/request -d '{...}'

# Expected: Fallback heuristics work, request processed

# Restart Ollama
docker start wingman-test-ollama
```

**Deliverables**:
- ✅ Test script: `wingman/tests/integration/test_approval_flow.sh`
- ✅ Test data: `wingman/tests/integration/test_cases.json`
- ✅ All 5 scenarios pass

---

#### Task 3.2: Deployment (2-4 hours)

**Step 1: Deploy to TEST** (1 hour)
```bash
# 1. Backup TEST database
docker exec wingman-test-postgres-1 pg_dump -U wingman wingman > backup_test_$(date +%Y%m%d).sql

# 2. Apply database migration
docker exec -i wingman-test-postgres-1 psql -U wingman -d wingman < migration_add_validation_results.sql

# 3. Deploy updated code
cd wingman
docker compose -f docker-compose.yml -p wingman-test stop wingman-api
docker compose -f docker-compose.yml -p wingman-test up -d --build wingman-api

# 4. Verify health
curl http://localhost:5001/health

# 5. Run smoke tests
./tests/integration/test_approval_flow.sh
```

**Step 2: Monitor TEST** (1 hour)
```bash
# Watch logs for validation activity
docker logs wingman-test-wingman-api-1 -f | grep "validation"

# Check validation results in database
watch -n 5 "docker exec wingman-test-postgres-1 psql -U wingman -d wingman \
  -c 'SELECT decision, COUNT(*) FROM validation_results GROUP BY decision;'"

# Verify Telegram notifications include validation reports
```

**Step 3: Deploy to PRD (Gradual Rollout)** (2 hours)

**Phase 3.2.1: PRD Deploy with Flag OFF** (30 min)
```bash
# Add feature flag to .env.prd
echo "VALIDATION_ENABLED=false" >> .env.prd

# Deploy code
cd wingman
docker compose -f docker-compose.prd.yml -p wingman-prd stop wingman-api
docker compose -f docker-compose.prd.yml -p wingman-prd --env-file .env.prd up -d --build wingman-api

# Verify deployment
curl http://localhost:5001/health
```

**Phase 3.2.2: Enable for 10% Traffic** (30 min)
```python
# In proper_wingman_deployment_prd.py:
VALIDATION_ENABLED = os.getenv('VALIDATION_ENABLED', 'false') == 'true'
VALIDATION_ROLLOUT_PERCENT = int(os.getenv('VALIDATION_ROLLOUT_PERCENT', '0'))

def should_run_validation() -> bool:
    if not VALIDATION_ENABLED:
        return False
    return random.randint(1, 100) <= VALIDATION_ROLLOUT_PERCENT
```

```bash
# Update environment
echo "VALIDATION_ENABLED=true" > .env.prd
echo "VALIDATION_ROLLOUT_PERCENT=10" >> .env.prd

# Restart
docker compose -f docker-compose.prd.yml -p wingman-prd restart wingman-api

# Monitor for 2 hours
docker logs wingman-prd-wingman-api-1 -f
```

**Phase 3.2.3: Increase to 50%** (30 min)
```bash
# If no errors after 2 hours at 10%
echo "VALIDATION_ROLLOUT_PERCENT=50" > .env.prd
docker compose -f docker-compose.prd.yml -p wingman-prd restart wingman-api

# Monitor for 2 hours
```

**Phase 3.2.4: Full Rollout 100%** (30 min)
```bash
# If no errors after 2 hours at 50%
echo "VALIDATION_ROLLOUT_PERCENT=100" > .env.prd
docker compose -f docker-compose.prd.yml -p wingman-prd restart wingman-api

# Monitor for 24 hours
```

**Deliverables**:
- ✅ TEST deployment complete and monitored
- ✅ PRD gradual rollout (10% → 50% → 100%)
- ✅ Rollback procedure documented
- ✅ Monitoring dashboards showing validation metrics

---

## SECTION 4: SUPPORTING DOCUMENTATION

### 4.1 Reference Documents

**Primary Documents**:
1. `docs/VALIDATION_ENHANCEMENT_IMPLEMENTATION_PLAN.md`
   - Original detailed implementation plan
   - Reference for validator specifications

2. `docs/VALIDATION_ENHANCEMENT_GAP_ANALYSIS.md`
   - Current state vs required state
   - Identifies missing pieces

3. `docs/AI_WORKER_FAILURE_ANALYSIS.md`
   - Lessons learned from AI worker attempts
   - What NOT to do

4. `docs/VALIDATION_ENHANCEMENT_COMPLETE_PLAN.md` (this document)
   - Complete development plan
   - Step-by-step implementation guide

### 4.2 Code Structure

**Directory Layout**:
```
wingman/
├── validation/
│   ├── __init__.py
│   ├── semantic_analyzer.py (NEW - 150-200 lines)
│   ├── code_scanner.py (NEW - 200-250 lines)
│   ├── dependency_analyzer.py (NEW - 200-250 lines)
│   ├── content_quality_validator.py (NEW - 250-300 lines)
│   └── composite_validator.py (NEW - 200-250 lines)
├── tests/
│   ├── test_semantic_analyzer.py (NEW - 10 tests)
│   ├── test_code_scanner.py (NEW - 10 tests)
│   ├── test_dependency_analyzer.py (NEW - 10 tests)
│   ├── test_content_quality_validator.py (NEW - 10 tests)
│   ├── test_composite_validator.py (NEW - 10 tests)
│   └── integration/
│       ├── test_approval_flow.sh (NEW)
│       └── test_cases.json (NEW)
├── proper_wingman_deployment_prd.py (MODIFY - +150 lines)
└── migrations/
    └── 001_add_validation_results.sql (NEW)
```

### 4.3 Testing Matrix

| Test Category | Count | Duration | Status |
|---------------|-------|----------|--------|
| Unit Tests - Semantic | 10 | 30s | ⏳ Pending |
| Unit Tests - Code Scanner | 10 | 30s | ⏳ Pending |
| Unit Tests - Dependency | 10 | 30s | ⏳ Pending |
| Unit Tests - Quality | 10 | 30s | ⏳ Pending |
| Unit Tests - Composite | 10 | 30s | ⏳ Pending |
| Integration Tests | 5 | 5 min | ⏳ Pending |
| End-to-End Tests | 3 | 10 min | ⏳ Pending |
| **Total** | **58** | **~15 min** | ⏳ |

### 4.4 Rollback Procedures

**If Validation Causes Issues**:

```bash
# Quick rollback: Disable validation
echo "VALIDATION_ENABLED=false" > .env.prd
docker compose -f docker-compose.prd.yml -p wingman-prd restart wingman-api

# Full rollback: Restore previous code
git revert HEAD
docker compose -f docker-compose.prd.yml -p wingman-prd up -d --build wingman-api

# Database rollback (if needed)
docker exec -i wingman-prd-postgres-1 psql -U wingman -d wingman \
  -c "DROP TABLE validation_results;"
```

### 4.5 Monitoring & Metrics

**Key Metrics to Track**:

```sql
-- Validation decision distribution
SELECT decision, COUNT(*) as count
FROM validation_results
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY decision;

-- Average validation time
SELECT AVG(EXTRACT(EPOCH FROM (created_at - approval_created_at))) as avg_seconds
FROM validation_results vr
JOIN approvals a ON vr.approval_id = a.id
WHERE vr.created_at > NOW() - INTERVAL '24 hours';

-- Error rate
SELECT COUNT(*) as errors
FROM validation_results
WHERE decision = 'MANUAL_REVIEW'
  AND telegram_report LIKE '%error%'
  AND created_at > NOW() - INTERVAL '24 hours';
```

**Alerts**:
- Validation time > 15 seconds (performance issue)
- Error rate > 5% (validation failures)
- Auto-reject rate > 50% (too aggressive)

---

## SECTION 5: EXECUTION CHECKLIST

### Pre-Implementation Checklist

- [ ] TEST environment verified running
- [ ] Ollama accessible from API container
- [ ] PostgreSQL accessible with correct credentials
- [ ] Git branch created: `validation-enhancement`
- [ ] Baseline backup of TEST database created
- [ ] All supporting documentation reviewed

### Phase 1 Checklist (Core Validators)

- [ ] Task 1.1: Semantic Analyzer implemented and tested
- [ ] Task 1.2: Code Scanner implemented and tested
- [ ] Task 1.3: Dependency Analyzer implemented and tested
- [ ] Task 1.4: Content Quality Validator implemented and tested
- [ ] All 40 unit tests passing
- [ ] Manual testing of each validator complete

### Phase 2 Checklist (Integration)

- [ ] Task 2.1: Composite Validator implemented and tested
- [ ] Task 2.2: API Integration complete
- [ ] Database migration applied to TEST
- [ ] All 50 unit tests passing
- [ ] Integration tests passing

### Phase 3 Checklist (Deployment)

- [ ] TEST deployment complete
- [ ] Smoke tests passing in TEST
- [ ] 24 hour monitoring in TEST shows no issues
- [ ] PRD deployment (flag OFF) complete
- [ ] Gradual rollout: 10% → 50% → 100%
- [ ] 7-day monitoring in PRD shows acceptable metrics
- [ ] Documentation updated with actual results

### Post-Deployment Checklist

- [ ] Monitoring dashboards configured
- [ ] Alert thresholds set
- [ ] Team trained on validation reports
- [ ] Rollback procedures tested
- [ ] Success metrics documented

---

## SECTION 6: SUCCESS CRITERIA & ACCEPTANCE

### Technical Success Criteria

✅ **TSC-1**: All 4 validators implemented with 100% test coverage
✅ **TSC-2**: Composite validator correctly combines results
✅ **TSC-3**: API integration complete with error handling
✅ **TSC-4**: All 58 tests passing (50 unit + 5 integration + 3 E2E)
✅ **TSC-5**: Validation completes within 10 seconds (95th percentile)
✅ **TSC-6**: Error rate < 2% (validation failures)
✅ **TSC-7**: Zero production incidents caused by validation

### Business Success Criteria

✅ **BSC-1**: 30% of LOW risk requests auto-approved
✅ **BSC-2**: 100% of CRITICAL risk requests auto-rejected
✅ **BSC-3**: Validation reports improve approval decision quality
✅ **BSC-4**: Manual review time reduced by 20% (better context)
✅ **BSC-5**: Zero false positives in auto-reject (precision > 99%)

### Acceptance Tests (User Acceptance)

✅ **AT-1**: Submit 10 LOW risk requests → All auto-approved correctly
✅ **AT-2**: Submit 5 CRITICAL risk requests → All auto-rejected correctly
✅ **AT-3**: Submit 10 MEDIUM risk requests → All manual review with useful reports
✅ **AT-4**: Submit malformed request → Graceful fallback to manual review
✅ **AT-5**: Simulate Ollama failure → System continues operating (fallback works)

---

## SECTION 7: RISK MANAGEMENT

### High Risks & Mitigations

**Risk 1: Validation Blocks Approvals**
- **Mitigation**: All validation errors fallback to manual review
- **Testing**: Simulate all error scenarios in integration tests

**Risk 2: False Positives in Auto-Reject**
- **Mitigation**: Conservative rules, gradual rollout, manual override available
- **Monitoring**: Track false positive rate, adjust thresholds

**Risk 3: Performance Degradation**
- **Mitigation**: Async validation, 30s timeout, performance testing
- **Monitoring**: Track 95th percentile validation time

**Risk 4: Ollama Unavailability**
- **Mitigation**: Fallback heuristics, retry logic, graceful degradation
- **Testing**: Test all fallback scenarios

**Risk 5: Integration Breaks Existing Flow**
- **Mitigation**: Feature flag, gradual rollout, comprehensive testing
- **Rollback**: Instant rollback via feature flag

### Medium Risks

- Database migration fails → Pre-tested migration, backups ready
- LLM response format changes → Robust JSON parsing, fallback
- Pattern matching false negatives → Iterative tuning, user feedback

---

## SECTION 8: TIMELINE & EFFORT

### Estimated Timeline

| Phase | Duration | Dependencies | Risk |
|-------|----------|--------------|------|
| Phase 1: Core Validators | 16-20 hours | None | LOW |
| Phase 2: Integration | 4-5 hours | Phase 1 complete | MEDIUM |
| Phase 3: Testing & Deployment | 4-7 hours | Phase 2 complete | MEDIUM |
| **Total** | **24-32 hours** | Sequential | **LOW** |

### Resource Requirements

- **Development**: 1 developer (Claude or human)
- **Testing**: TEST environment (already available)
- **Deployment**: PRD environment (already available)
- **Infrastructure**: No new services required

---

## SECTION 9: SIGN-OFF

### Pre-Implementation Approval

- [ ] User approves plan structure and approach
- [ ] User approves estimated timeline (24-32 hours)
- [ ] User approves incremental delivery approach
- [ ] User commits to checkpoint reviews after each phase

### Phase Completion Sign-Off

- [ ] Phase 1 complete (all validators working)
- [ ] Phase 2 complete (integration working)
- [ ] Phase 3 complete (deployed to PRD)

### Final Acceptance

- [ ] All acceptance tests passing
- [ ] 7-day PRD monitoring shows acceptable metrics
- [ ] User accepts solution as complete
- [ ] Documentation updated with lessons learned

---

## APPENDIX A: QUICK START GUIDE

**For Developer Starting Fresh**:

```bash
# 1. Setup
cd /Volumes/Data/ai_projects/wingman-system/wingman
git checkout -b validation-enhancement
source .env.test

# 2. Verify environment
docker compose -f docker-compose.yml -p wingman-test ps
curl http://localhost:11434/api/tags

# 3. Start with Phase 1, Task 1.1
# Read: docs/VALIDATION_ENHANCEMENT_COMPLETE_PLAN.md Section 3, Task 1.1
# Implement: wingman/validation/semantic_analyzer.py
# Test: cd wingman && pytest tests/test_semantic_analyzer.py -v

# 4. Continue sequentially through all tasks
# After each task: Test → Review → Proceed

# 5. Deploy to TEST after Phase 2
# Deploy to PRD after Phase 3
```

---

**STATUS**: ✅ PLAN COMPLETE - READY FOR EXECUTION
**CONFIDENCE**: HIGH - Realistic estimates, no shortcuts, proven approach
**NEXT ACTION**: User approval to proceed with Phase 1

---

**Document Version**: 1.0
**Last Updated**: 2026-01-14
**Author**: Claude (Sonnet 4.5)
**Reviewed By**: [Pending user review]
