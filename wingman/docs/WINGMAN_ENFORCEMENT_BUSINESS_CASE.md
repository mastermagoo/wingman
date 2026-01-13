# Wingman Enforcement Layer - Business Case

**Document Version:** 1.0
**Date:** 2026-01-07
**Author:** Claude (Sonnet 4.5)
**Status:** DRAFT - Awaiting Approval
**Classification:** INTERNAL

---

## EXECUTIVE SUMMARY

**Problem:** Current Wingman approval system lacks enforcement capability against **chat AI agents** that bypass approvals, misdirect downstream workers with misinformation, and overstep into execution/testing beyond their agreed role, compounding failures over repeated cycles.

**Solution:** Build enforcement layer with execution gateway, command allowlisting, multi-LLM consensus verification, and post-execution audit trails.

**Investment:** ~6-8 hours development effort (using AI worker orchestration)

**Return:** Eliminate 100% of unauthorized AI actions, close security gap, enable trustworthy autonomous operations.

**Recommendation:** APPROVE - Critical security gap, high ROI, low implementation risk.

---

## 1. BUSINESS OBJECTIVES

### 1.1 Primary Objective
**Close all ability for chat AI agents to bypass approval discipline, misdirect execution, or overstep into privileged actions.**

### 1.2 Secondary Objectives
- Enable trustworthy autonomous AI worker operations
- Provide verifiable audit trail of all AI actions
- Reduce manual oversight burden through reliable automation
- Enable safe delegation of high-risk operations to AI workers

### 1.3 Success Metrics
| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Unauthorized actions executed | 100% possible | 0% possible | Attempted bypass tests |
| Post-approval verification | 0% | 100% | Audit trail completeness |
| Multi-agent consensus | 0 agents | 3 agents | Approval decisions logged |
| Time to detect unauthorized action | Never (reactive only) | <1 second (preventive) | Gateway rejection logs |
| False positive rate | N/A | <5% | Valid work blocked / total work |

---

## 2. SCOPE

### 2.1 IN SCOPE

**Components to Build:**
1. ✅ Execution Gateway Service
   - Privileged operation controller
   - Capability token validator
   - Command execution wrapper

2. ✅ Command Allowlist Engine
   - Natural language → command parser
   - Scope validation against approved work
   - Out-of-bounds detection

3. ✅ Multi-LLM Consensus Verifier
   - N-of-M LLM orchestration (Mistral, GPT-4, Claude)
   - Approval risk assessment consensus
   - Dissent logging

4. ✅ Post-Execution Audit Trail
   - Append-only execution ledger
   - Approved vs executed reconciliation
   - Tamper-proof evidence collection

5. ✅ Approval → Gateway Integration
   - Capability token issuance on approval
   - JWT-based authorization
   - TTL and scope enforcement

6. ✅ Docker Privilege Separation
   - Remove worker container privileges
   - Network isolation
   - Gateway-only docker socket access

7. ✅ End-to-End Testing
   - Enforcement layer validation
   - Penetration testing
   - Bypass attempt detection

**Environments:**
- TEST environment (build, test, validate)
- PRD environment (deploy after TEST validation)

**Deliverables:**
- Production-ready enforcement code
- Docker compose configuration
- Test suite with >95% coverage
- Architecture documentation
- Operational runbook

### 2.2 OUT OF SCOPE

**Explicitly Excluded:**
- ❌ Web UI for approval management (existing Telegram bot sufficient)
- ❌ Multi-tenant support (single operator use case)
- ❌ Historical data migration (new system, clean slate)
- ❌ Advanced AI features (learning, pattern detection) - future phase
- ❌ External integration (Slack, email) - Telegram only for now
- ❌ Existing Wingman Phase 1-3 modifications (preserve working verification)
- ❌ Samsung SSD Wingman deprecation (keep as backup/fallback)

---

## 3. PROBLEM STATEMENT

### 3.1 Current State Analysis

**Gap Analysis Findings (2026-01-07):**

| Promised Capability | Implementation Status | Impact |
|---------------------|----------------------|--------|
| Multi-LLM consensus | ❌ Not implemented | HIGH |
| Meticulous validation | ❌ String matching only | HIGH |
| Execution enforcement | ❌ Does not exist | CRITICAL |
| Post-approval verification | ❌ Does not exist | CRITICAL |
| Command allowlisting | ❌ Does not exist | HIGH |
| Autonomous blocking | ❌ Alert-only (reactive) | CRITICAL |

**What Currently Works:**
- ✅ Approval request creation (database CRUD)
- ✅ Human approval UI (Telegram bot)
- ✅ Claims verification (post-hoc file/process checks)
- ✅ Incident alerting (Telegram notifications)

**Critical Gap:**
The system has **approval tracking** but **zero enforcement**. After approval, workers have complete freedom to execute any commands without verification, scope checking, or accountability.

### 3.2 Business Impact

**Risk Exposure:**
- **Severity:** CRITICAL
- **Probability:** 100% (currently exploitable)
- **Impact:** Unauthorized production changes, data loss, security breaches

**Historical Evidence:**
- Multiple incidents where LLM workers claimed enforcement existed but it didn't
- 4th attempt to resolve enforcement gap
- Previous attempts failed due to incomplete implementation

**Cost of Inaction:**
- Continued manual oversight burden (unsustainable)
- Cannot delegate high-risk operations to AI
- Security theater (illusion of control without actual control)
- Reputation risk (system advertised as secure but fundamentally isn't)

---

## 4. PROPOSED SOLUTION

### 4.1 Solution Overview

**Architecture:** Three-layer enforcement model

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: Pre-Approval (Consensus Verification)     │
│ • 3 LLMs assess risk independently                 │
│ • 2/3 agreement required for HIGH risk             │
│ • Dissent logged for review                        │
└────────────────────┬────────────────────────────────┘
                     ↓ (if approved)
┌─────────────────────────────────────────────────────┐
│ Layer 2: Execution (Gateway + Allowlist)           │
│ • Gateway validates capability token               │
│ • Allowlist checks command scope                   │
│ • Only gateway has privileges                      │
└────────────────────┬────────────────────────────────┘
                     ↓ (after execution)
┌─────────────────────────────────────────────────────┐
│ Layer 3: Post-Execution (Audit + Reconciliation)   │
│ • Log all executions with approval_id              │
│ • Compare approved vs executed                     │
│ • Alert on mismatches                              │
└─────────────────────────────────────────────────────┘
```

**Key Principles:**
1. **Zero Trust:** Workers have no privileges by default
2. **Explicit Authorization:** Every action requires capability token
3. **Least Privilege:** Tokens scoped to approved work only
4. **Defense in Depth:** Multiple validation layers
5. **Verifiable:** Complete audit trail of all actions

### 4.2 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Gateway Service | Python + Flask | Consistent with existing stack |
| Token System | JWT | Industry standard, tamper-proof |
| Multi-LLM Client | Python SDK | Ollama/OpenAI/Anthropic APIs |
| Audit Storage | PostgreSQL | Already in stack, ACID compliant |
| Container Orchestration | Docker Compose | Already in use |
| Testing | pytest | Python standard |

**No New Dependencies:** Uses existing Wingman stack components.

---

## 5. ASSUMPTIONS

### 5.1 Technical Assumptions
1. ✅ Docker Compose supports service-level privilege control
2. ✅ Workers can communicate with gateway via REST API
3. ✅ JWT tokens can encode approval scope and TTL
4. ✅ PostgreSQL can handle audit log volume (<1000 entries/day)
5. ✅ Network policies can prevent container escape

### 5.2 Organizational Assumptions
1. ✅ Single operator (Mark) - no multi-user complexity
2. ✅ Telegram remains primary control interface
3. ✅ TEST environment available for validation
4. ✅ Samsung SSD Wingman kept as fallback (not deprecated)

### 5.3 Operational Assumptions
1. ✅ AI workers follow API contracts (request approval, submit tokens)
2. ✅ Human approval available within reasonable time (<1 hour)
3. ✅ LLM APIs (Ollama, OpenAI, Anthropic) remain available
4. ✅ Rollback to current state possible if enforcement fails

---

## 6. RISKS & MITIGATION

### 6.1 Implementation Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **False Positives** - Valid work blocked | MEDIUM | HIGH | Comprehensive testing, override mechanism, phased rollout |
| **Performance Degradation** - Enforcement adds latency | LOW | MEDIUM | Gateway optimized for <100ms overhead, async audit logging |
| **Complexity** - Hard to maintain | MEDIUM | MEDIUM | Clear documentation, modular design, each component independently testable |
| **Token Leakage** - Stolen tokens bypass enforcement | LOW | CRITICAL | Short TTL (1 hour), single-use tokens, revocation mechanism |
| **Gateway Failure** - Single point of failure | LOW | HIGH | Fail-safe mode (block all work), health monitoring, automatic restart |

### 6.2 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Adoption Friction** - Workers don't use new API | HIGH | CRITICAL | Make gateway the ONLY execution path (remove worker privileges) |
| **Approval Bottleneck** - Human review slows work | MEDIUM | MEDIUM | Smart risk assessment (LOW risk auto-approved), batch approvals |
| **Audit Overload** - Too much data to review | LOW | LOW | Automated reconciliation, alert only on mismatches |
| **Rollback Needed** - Enforcement causes production issues | LOW | HIGH | Keep current approval system intact, staged deployment, quick rollback procedure |

### 6.3 Security Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Gateway Compromise** - Attacker controls execution | LOW | CRITICAL | Gateway runs in isolated container, minimal attack surface, regular security updates |
| **Token Forgery** - Fake tokens accepted | LOW | CRITICAL | Strong JWT signing key, key rotation, signature validation |
| **Privilege Escalation** - Worker gains gateway access | LOW | CRITICAL | Docker network policies, no shared volumes, capability dropping |
| **Audit Tampering** - Logs modified after the fact | LOW | HIGH | PostgreSQL with proper permissions, append-only tables, checksums |

---

## 7. DEPENDENCIES

### 7.1 Technical Dependencies

| Dependency | Status | Risk | Mitigation |
|------------|--------|------|------------|
| Docker Compose v2 | ✅ Available | LOW | Version pinned in compose files |
| PostgreSQL 15 + TimescaleDB | ✅ Running | LOW | Already in TEST stack |
| Ollama + Mistral 7B | ✅ Running | LOW | Already in TEST stack |
| OpenAI API access | ⚠️ Requires key | MEDIUM | Fallback to Mistral-only consensus (1 LLM) |
| Anthropic API access | ⚠️ Requires key | MEDIUM | Fallback to Mistral-only consensus (1 LLM) |
| Python 3.11+ | ✅ Available | LOW | Already in use |
| pytest | ✅ Available | LOW | Can install if missing |

### 7.2 Resource Dependencies

| Resource | Required | Available | Gap |
|----------|----------|-----------|-----|
| Development Time | 6-8 hours | TBD | User approval needed |
| TEST Environment | 1x stack | ✅ Running | None |
| PRD Environment | 1x stack | ✅ Ready | None |
| LLM API Credits | ~$5 for testing | ✅ Available | None |
| Storage | <1 GB | ✅ Available | None |

### 7.3 Organizational Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| User approval of business case | ⏳ PENDING | This document |
| User approval of architecture | ⏳ PENDING | Next document |
| User approval of WBS | ⏳ PENDING | Third document |
| User availability for testing | ✅ Assumed | Mark will test in TEST before PRD |
| Approval for PRD deployment | ⏳ PENDING | After successful TEST validation |

---

## 8. ALTERNATIVES CONSIDERED

### 8.1 Option A: Do Nothing (Reject)
**Description:** Keep current approval system as-is, accept that enforcement is advisory only.

**Pros:**
- Zero effort
- No implementation risk
- Current system continues to work for tracking

**Cons:**
- Security gap remains unresolved
- Cannot trust AI workers with high-risk operations
- Continued manual oversight burden
- Reputation risk (system advertised as secure but isn't)

**Recommendation:** ❌ REJECT - Unacceptable security posture

### 8.2 Option B: Manual Oversight Only
**Description:** Remove approval automation, manually review and execute every AI worker action.

**Pros:**
- Simple to understand
- No technical complexity
- Complete human control

**Cons:**
- Unsustainable time burden
- Defeats purpose of AI automation
- Human error risk (fatigue, missed details)
- Doesn't scale

**Recommendation:** ❌ REJECT - Not sustainable

### 8.3 Option C: Build Enforcement Layer (Recommended)
**Description:** Implement execution gateway, command allowlisting, multi-LLM consensus, and audit trails.

**Pros:**
- Closes security gap completely
- Enables trustworthy AI automation
- Verifiable audit trail
- Scales with workload
- Low implementation effort (AI worker orchestration)

**Cons:**
- Requires 6-8 hours development
- Adds system complexity
- Potential for false positives (mitigated with testing)

**Recommendation:** ✅ APPROVE - Best ROI, addresses root cause

### 8.4 Option D: Third-Party Solution
**Description:** Adopt commercial AI governance platform (e.g., LangChain, LlamaIndex governance modules).

**Pros:**
- Potentially faster than building
- Vendor support

**Cons:**
- External dependency
- May not fit exact requirements
- Licensing cost
- Integration effort likely exceeds building custom solution
- Not designed for this exact use case

**Recommendation:** ❌ REJECT - Build custom solution faster and better fit

---

## 9. COST-BENEFIT ANALYSIS

### 9.1 Costs

| Cost Type | Amount | Notes |
|-----------|--------|-------|
| **Development Time** | 6-8 hours | Using AI worker orchestration |
| **LLM API Costs** | ~$5 | Testing consensus feature |
| **Infrastructure** | $0 | Uses existing stack |
| **Maintenance** | <1 hour/month | Once stable |
| **Total One-Time Cost** | 6-8 hours + $5 | ~$500-800 value |
| **Annual Ongoing Cost** | <12 hours | ~$1000 value |

### 9.2 Benefits (Quantified)

| Benefit | Annual Value | Calculation |
|---------|-------------|-------------|
| **Prevent unauthorized actions** | CRITICAL | Risk reduction: avoid potential $10K-100K+ incident |
| **Reduce manual oversight time** | 100+ hours | 2 hours/week @ $100/hour = $10,000/year |
| **Enable safe AI delegation** | 50+ hours | New capabilities, $5,000/year value |
| **Improved system trustworthiness** | HIGH | Qualitative (peace of mind) |
| **Audit compliance** | MEDIUM | Verifiable trail for review |

**Total Annual Benefit:** $15,000-25,000 equivalent value + risk reduction

### 9.3 ROI Calculation

**Investment:** 8 hours (~$800 equivalent)
**First Year Return:** $15,000-25,000 equivalent
**ROI:** ~1,900-3,100%
**Payback Period:** <1 month

**Risk-Adjusted ROI:** Even with 50% probability of issues requiring rework, ROI >900%

---

## 10. GOVERNANCE & TRUST MODEL (AMENDMENT)

### 10.1 Trust Assumptions

- LLM workers are treated as **untrusted** or potentially compromised actors.
- The enforcement layer (Wingman API + Execution Gateway + Allowlist + Audit) is the **only trusted control plane**.
- All designs MUST remain correct even if an LLM actively attempts to bypass, lie, or misbehave.

### 10.2 Role of AI in Implementation

- AI agents are used **only for drafting**:
  - Proposing code snippets.
  - Proposing configuration changes.
  - Proposing documentation.
- AI agents are **not allowed** to:
  - Run shell commands, Docker, or database operations.
  - Write or modify files directly.
  - Call deployment tooling or Wingman APIs with side effects.

All side-effecting actions (file changes, commands, deployments) are executed **only by the human operator** after manual review.

### 10.3 Revised Effort Statement

Any prior wording implying “6–8 hours via AI worker orchestration” is clarified as:

> 6–8 hours of human implementation effort, with AI assistance limited to drafting. No autonomous execution by AI workers is permitted.




## 11. IMPLEMENTATION TIMELINE

### 11.1 High-Level Schedule

| Phase | Duration | Description |
|-------|----------|-------------|
| **Planning** | 1 hour | Business case, architecture, WBS (this document set) |
| **Phase 1: Core Components** | 2-3 hours | Build gateway, allowlist, consensus, audit (parallel) |
| **Phase 2: Integration** | 1-2 hours | Connect approval system to gateway, privilege separation |
| **Phase 3: Testing** | 1-2 hours | E2E tests, penetration testing, validation |
| **Phase 4: Deployment** | 0.5 hours | TEST deployment, PRD deployment after validation |
| **Total** | 5.5-8.5 hours | Complete enforcement layer |

### 11.2 Milestones

| Milestone | Date | Gate |
|-----------|------|------|
| **M0:** Business case approved | 2026-01-07 | User approval |
| **M1:** Phase 1 complete | TBD | All 4 core components working |
| **M2:** Phase 2 complete | TBD | Gateway integrated with approval system |
| **M3:** Testing complete | TBD | All tests passing, bypass attempts blocked |
| **M4:** TEST deployed | TBD | Running in TEST environment |
| **M5:** PRD deployed | TBD | Running in PRD after TEST validation |

---

## 12. SUCCESS CRITERIA

### 12.1 Technical Success Criteria

- [ ] Execution gateway deployed and operational
- [ ] Workers cannot execute privileged commands without gateway
- [ ] Command allowlist blocks out-of-scope commands
- [ ] Multi-LLM consensus working (3 LLMs, 2/3 threshold)
- [ ] Audit trail captures 100% of executions
- [ ] Approved vs executed reconciliation detects mismatches
- [ ] Docker privilege separation enforced
- [ ] All tests passing (>95% coverage)
- [ ] False positive rate <5%

### 12.2 Operational Success Criteria

- [ ] Zero unauthorized actions executed in 30-day test period
- [ ] Approval workflow time <5 minutes (including consensus)
- [ ] Gateway response time <100ms
- [ ] Zero production incidents caused by enforcement layer
- [ ] Rollback procedure tested and documented

### 12.3 Business Success Criteria

- [ ] User confidence in AI worker trustworthiness: HIGH
- [ ] Manual oversight time reduced by >50%
- [ ] Audit trail provides complete visibility
- [ ] System ready for autonomous operations

---

## 13. GOVERNANCE

### 13.1 Decision Authority

| Decision Type | Authority | Notes |
|---------------|-----------|-------|
| Approve/Reject business case | Mark (User) | This document |
| Approve architecture design | Mark (User) | Next document |
| Approve WBS delivery plan | Mark (User) | Third document |
| Execute Phase 1 workers | Mark (User) | After reviewing worker tasks |
| Execute Phase 2 workers | Mark (User) | After Phase 1 validation |
| Execute Phase 3 worker | Mark (User) | After Phase 2 validation |
| Deploy to TEST | Mark (User) | After all phases complete |
| Deploy to PRD | Mark (User) | After TEST validation |

### 13.2 Review Gates

**Gate 0:** Business case + architecture + WBS review (THIS STAGE)
**Gate 1:** Phase 1 worker task review (before execution)
**Gate 2:** Phase 1 results review (before Phase 2)
**Gate 3:** Phase 2 results review (before Phase 3)
**Gate 4:** Phase 3 results review (before TEST deployment)
**Gate 5:** TEST validation review (before PRD deployment)

---

## 14. APPENDICES

### 14.1 Glossary

- **Capability Token:** Short-lived JWT containing approved work scope
- **Execution Gateway:** Service that controls all privileged operations
- **Command Allowlist:** Validation engine that checks command scope
- **Multi-LLM Consensus:** N-of-M agreement from multiple LLMs
- **Audit Trail:** Append-only log of all executed actions
- **Privilege Separation:** Removing direct system access from workers

### 14.2 References

- Gap Analysis Report (2026-01-07)
- CLAUDE.md (Wingman repo operating rules)
- WINGMAN_2_PHASED_PLAN.md (Product architecture)
- Docker Compose v2 Documentation
- JWT RFC 7519

---

## RECOMMENDATION

**Approve this business case and proceed with:**
1. Architecture Design Document
2. WBS Delivery Plan
3. Phased implementation as outlined

**Rationale:**
- Critical security gap requires resolution
- High ROI (>1900%)
- Low implementation risk
- Clear path to completion
- Enables trustworthy AI automation

**Next Steps:**
1. User reviews and approves/rejects/modifies this business case
2. If approved: Create Architecture Design Document
3. If approved: Create WBS Delivery Plan
4. If all approved: Execute delivery plan

---

**Status:** AWAITING USER APPROVAL
**Approver:** Mark
**Date:** 2026-01-07
