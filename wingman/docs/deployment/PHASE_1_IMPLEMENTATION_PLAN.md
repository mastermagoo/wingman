# Phase 1 Implementation Plan: Core Validators

**Date**: 2026-01-22  
**Status**: 📋 PLANNING  
**Estimated Effort**: 14-18 hours (2-2.5 working days)  
**Priority**: HIGH (blocks Phase 2-6)

---

## Overview

Implement the 4 core validators that transform Wingman from "presence checks" to "substance validation":
1. Semantic Analyzer (LLM-based risk detection)
2. Code Scanner (pattern-based dangerous command detection)
3. Dependency Analyzer (LLM-based blast radius assessment)
4. Content Quality Validator (LLM-based quality scoring)

---

## Implementation Order (Critical Path)

### Phase 1.1: Code Scanner (First - No Dependencies)
**Estimated**: 4-5 hours  
**Why First**: 
- No LLM dependencies (pure pattern matching)
- Fastest to implement and test
- Provides immediate value (catches dangerous commands)
- Can be tested independently

**Tasks**:
1. Create `validation/code_scanner.py` (~200-250 lines)
2. Implement pattern matching for:
   - Dangerous commands: `rm -rf`, `DROP TABLE`, `docker system prune`, `chmod 777`
   - Dangerous flags: `--force`, `--no-verify`, `-rf`, `-f`
   - Privilege escalation: `sudo`, `su -`, `chmod 777`
   - Secret patterns: API keys, passwords, tokens (regex)
3. Write unit tests (10+ test cases)
4. Integration test with `instruction_validator.py`

**Deliverable**: `code_scanner.py` with 100% test coverage

---

### Phase 1.2: Semantic Analyzer (Second - LLM Required)
**Estimated**: 5-6 hours  
**Why Second**:
- Requires LLM (Mistral 7B via intel-system processor)
- More complex than code scanner
- Provides risk level detection (HIGH/MEDIUM/LOW)

**Tasks**:
1. Create `validation/semantic_analyzer.py` (~250-300 lines)
2. Implement LLM integration:
   - Connect to `INTEL_LLM_PROCESSOR` (http://127.0.0.1:18027)
   - Use Mistral 7B for semantic analysis
   - Prompt engineering for risk detection
   - JSON output parsing with retry logic
3. Implement fallback to heuristic if LLM times out
4. Detect HIGH risk even if labeled "low" (e.g., "docker restart" on PRD)
5. Write unit tests (10+ test cases, including LLM timeout scenarios)
6. Integration test with approval flow

**Deliverable**: `semantic_analyzer.py` with LLM integration and fallback

**Blockers**: None - All dependencies resolved ✅

---

### Phase 1.3: Dependency Analyzer (Third - LLM Required)
**Estimated**: 3-4 hours  
**Why Third**:
- Builds on semantic analyzer patterns
- Requires LLM for blast radius assessment
- Less critical than semantic analyzer

**Tasks**:
1. Create `validation/dependency_analyzer.py` (~250-300 lines)
2. Implement LLM-based dependency analysis:
   - Identify affected services from instruction text
   - Calculate blast radius (LOW/MEDIUM/HIGH)
   - Detect cascading failure risks
   - Single point of failure detection
3. Use same LLM integration pattern as semantic analyzer
4. Write unit tests (10+ test cases)
5. Integration test with approval flow

**Deliverable**: `dependency_analyzer.py` with blast radius assessment

---

### Phase 1.4: Content Quality Validator (Fourth - LLM Required)
**Estimated**: 2-3 hours  
**Why Last**:
- Builds on all previous validators
- Most complex (quality scoring per section)
- Requires understanding of all 10-point framework sections

**Tasks**:
1. Create `validation/content_quality_validator.py` (~300-350 lines)
2. Implement LLM-based quality assessment:
   - Score each 10-point section (0-10)
   - Detect vague language ("do it", "make it work")
   - Verify measurable success criteria
   - Ensure mitigation plans have actual steps
3. Calculate overall quality score (0-100)
4. Write unit tests (10+ test cases)
5. Integration test with approval flow

**Deliverable**: `content_quality_validator.py` with section-by-section scoring

---

## Hour-by-Hour Breakdown

| Task | Hours | Cumulative |
|------|-------|------------|
| **Phase 1.1: Code Scanner** | | |
| - Implementation | 3.0 | 3.0 |
| - Unit tests | 1.0 | 4.0 |
| - Integration test | 0.5 | 4.5 |
| **Phase 1.2: Semantic Analyzer** | | |
| - LLM endpoint investigation | 0.5 | 5.0 |
| - Implementation | 3.5 | 8.5 |
| - Unit tests | 1.0 | 9.5 |
| - Integration test | 0.5 | 10.0 |
| **Phase 1.3: Dependency Analyzer** | | |
| - Implementation | 2.5 | 12.5 |
| - Unit tests | 0.5 | 13.0 |
| - Integration test | 0.5 | 13.5 |
| **Phase 1.4: Content Quality Validator** | | |
| - Implementation | 2.0 | 15.5 |
| - Unit tests | 0.5 | 16.0 |
| - Integration test | 0.5 | 16.5 |
| **Buffer for LLM prompt iteration** | 1.5 | 18.0 |

**Total**: 14-18 hours (realistic: 16-18 hours with prompt iteration)

---

## LLM Prompt Iteration Plan

**Time Allocation**: 1.5 hours buffer

**Iteration Strategy**:
1. Start with simple prompts (30 min)
2. Test with real approval requests (30 min)
3. Refine based on false positives/negatives (30 min)

**Prompt Templates Needed**:
- Semantic analyzer: Risk detection prompt
- Dependency analyzer: Blast radius assessment prompt
- Content quality: Section-by-section scoring prompt

**Success Criteria**:
- Semantic analyzer: Detects HIGH risk correctly 90%+ of the time
- Dependency analyzer: Identifies affected services correctly 85%+ of the time
- Content quality: Scores correlate with manual assessment 80%+ of the time

---

## Testing Strategy

### Unit Tests (Per Validator)
- 10+ test cases covering:
  - Happy path (good instructions)
  - Edge cases (vague instructions)
  - Error cases (malformed input)
  - LLM timeout scenarios (for LLM-based validators)

### Integration Tests
- Test each validator with `instruction_validator.py`
- Test composite scoring logic
- Test auto-reject logic (quality < 60)
- Test auto-approve logic (LOW risk + quality ≥ 90)

### Test Data
- Use real approval requests from approval store
- Create synthetic test cases for edge cases
- Include TEST 6 scenario (Cursor-style vague request)

---

## Dependencies & Blockers

### Resolved ✅
- TEST environment ready
- Execution gateway tested
- Approval routing fixed

### Blockers ⚠️
- **LLM Processor Endpoint**: `/generate` returns 404
  - Need to verify correct endpoint
  - May need to check intel-system LLM processor API docs
  - Fallback: Use direct Ollama if processor unavailable

### External Dependencies
- Mistral 7B model available ✅ (via Ollama direct)
- Ollama available ✅ (validators use `ollama run mistral` directly)
- TEST API running ✅
- LLM validation complete ✅ (response time: avg 1.62s, max 6.16s, all <30s)

---

## Success Criteria

1. ✅ All 4 validators implemented
2. ✅ 100% unit test coverage
3. ✅ Integration tests passing
4. ✅ LLM prompts validated with real data
5. ✅ False positive rate < 10% (after tuning)
6. ✅ False negative rate < 5% (after tuning)

---

## Next Steps After Phase 1

1. **Phase 2**: Integration into approval flow
2. **Phase 3**: Composite scoring logic
3. **Phase 4**: Full test suite (203 tests)
4. **Phase 5**: Deployment to TEST with feature flag

---

**Last Updated**: 2026-01-22  
**Owner**: AI Worker (Cursor)  
**Status**: Ready for implementation
