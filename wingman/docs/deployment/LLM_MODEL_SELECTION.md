# LLM Model Selection for Wingman Verification System

**Date**: 2026-01-22  
**Status**: RECOMMENDATION  
**Environment**: Host Ollama (port 11434), accessed via `host.docker.internal:11434` from containers

---

## Wingman's Full Verification Scope

Wingman is not just an instruction validator - it's a comprehensive **AI Governance System** that verifies:

1. **Instruction Validation** (Phase 2) - 10-point framework quality
2. **Code Quality Verification** (Future phases) - Syntax, linting, security, best practices
3. **Test Results Verification** (Future phases) - Did tests pass? Are they comprehensive?
4. **Claim Verification** (Phase 3) - Did AI workers actually do what they claimed?
5. **Semantic Analysis** - Understanding what instructions actually do
6. **Dependency Analysis** - Blast radius and impact assessment
7. **Compliance Verification** - Alignment with standards and policies

**This document covers LLM model selection for ALL verification tasks**, not just instruction validation.

---

## Current State

**Wingman currently uses**: `mistral:7b` (unquantized, 4.4GB)  
**Environment**: Host Ollama, accessed from containers via `host.docker.internal:11434`  
**Current Scope**: Enhanced verifier (`enhanced_verifier.py`) uses Mistral for claim verification

---

## Available Quantized Models (Host Ollama)

| Model | Size | Speed | Best For | Status |
|-------|------|-------|----------|--------|
| `qwen2.5:3b` | 1.9GB | Fastest (4s) | Simple classification | ⚠️ May miss context |
| `llama3.1:8b-instruct-q4_K_M` | 4.9GB | Medium (10s) | Instruction following, structured output | ✅ Recommended |
| `deepseek-coder:6.7b-instruct-q4_K_M` | 4.1GB | Fast | Code analysis, code quality | ✅ For code verification |
| `mistral:7b-instruct-q4_K_M` | 4.4GB | Medium | General purpose | ✅ Fallback |
| `mistral:7b` (unquantized) | 4.4GB | Slower | Legacy | ❌ OTT for most tasks |

---

## Model Recommendations by Verification Task

### 1. Instruction Validation (Phase 2 Enhancement)

**Semantic Analyzer** (Risk Detection & Understanding):
- **Primary**: `llama3.1:8b-instruct-q4_K_M`
  - Better instruction following
  - Handles context better than qwen2.5:3b
  - Quantized (faster than unquantized Mistral 7B)
- **Fallback**: `mistral:7b-instruct-q4_K_M` (if llama3.1 unavailable)

**Content Quality Validator** (10-Point Framework Scoring):
- **Primary**: `llama3.1:8b-instruct-q4_K_M`
  - Multi-section analysis requires good instruction following
  - Better at structured output (JSON scoring per field)
- **Fallback**: `mistral:7b-instruct-q4_K_M`

**Dependency Analyzer** (Blast Radius Assessment):
- **Primary**: `llama3.1:8b-instruct-q4_K_M`
  - Needs to understand service relationships
  - Better reasoning than smaller models
- **Fallback**: `mistral:7b-instruct-q4_K_M`

---

### 2. Code Quality Verification (Future Phases) ⚠️ CRITICAL REQUIREMENT

**⚠️ CRITICAL CONCERN**: If a model cannot write high-quality Python code itself, it cannot reliably verify code written by more powerful models (GPT-4, Claude). Code quality verification requires **deep analysis**, not just pattern matching.

**Requirements:**
- Deep code analysis (not just syntax checking)
- 100% optimization verification
- Strategic recommendations
- Ability to review code written by GPT-4/Claude (more powerful models)
- Understanding of best practices, design patterns, performance optimization

**Code Quality Scanner** (Deep Analysis, Optimization, Strategic Recommendations):
- **Primary**: `codellama:13b` (unquantized, 7.4GB) or `codellama:13b-instruct-q4_K_M` (quantized, 7.9GB)
  - **13B parameters** - More capable than 6.7B/8B models
  - **Code-specialized** - Trained specifically for code tasks
  - **Better reasoning** - Can understand complex code patterns
  - **Handles Python, shell scripts, Dockerfiles, etc.**
- **Alternative**: `gemma3:12b-it-qat` (8.9GB) - Large, capable model
- **Fallback**: `deepseek-coder:6.7b-instruct-q4_K_M` (only for simple pattern matching)
- **⚠️ Limitation**: Even 13B models may struggle with code written by GPT-4/Claude. Consider external API for critical reviews.

**Security Vulnerability Scanning** (Dangerous Patterns, Secrets):
- **Primary**: Pattern-based (regex) + `codellama:13b` for context understanding
  - Most security issues detectable via patterns
  - LLM helps understand context (e.g., "rm -rf" in test cleanup vs production)
  - Larger model needed to catch subtle security issues
- **Fallback**: `deepseek-coder:6.7b-instruct-q4_K_M` (basic context only)

**Code Complexity Analysis** (Cyclomatic Complexity, Best Practices, Optimization):
- **Primary**: `codellama:13b` or `codellama:13b-instruct-q4_K_M`
  - **Deep understanding** required for optimization recommendations
  - **Strategic recommendations** need larger model capacity
  - Better at identifying code smells and anti-patterns
- **Fallback**: `deepseek-coder:6.7b-instruct-q4_K_M` (basic analysis only)

**⚠️ EXTERNAL API OPTION**: For critical code reviews (production deployments, security-sensitive code), consider using external APIs:
- **GPT-4** or **Claude Sonnet** via API for deep code review
- **Cost**: ~$2-10 per million tokens (vs free local models)
- **Benefit**: Can verify code written by GPT-4/Claude with equal or greater capability
- **Implementation**: Add optional external API integration for critical paths

---

### 3. Test Results Verification (Future Phases)

**Test Result Analysis** (Did Tests Pass? Are They Comprehensive?):
- **Primary**: `llama3.1:8b-instruct-q4_K_M`
  - Needs to parse test output (JSON, XML, plain text)
  - Understand test coverage metrics
  - Assess test comprehensiveness
- **Fallback**: `mistral:7b-instruct-q4_K_M`

**Test Process Validation** (Is Testing Automated? Repeatable?):
- **Primary**: `llama3.1:8b-instruct-q4_K_M`
  - Instruction following for structured assessment
  - Can evaluate test process quality

---

### 4. Claim Verification (Phase 3 - Current)

**Enhanced Verifier** (Current: `enhanced_verifier.py`):
- **Current**: `mistral:7b` (unquantized)
- **Recommended**: `llama3.1:8b-instruct-q4_K_M`
  - Better instruction following
  - Faster (quantized)
  - Better structured output parsing
- **Fallback**: `mistral:7b-instruct-q4_K_M`

---

### 5. Compliance Verification (Future Phases)

**Policy Compliance Checker** (CLAUDE.md rules, standards):
- **Primary**: `llama3.1:8b-instruct-q4_K_M`
  - Needs to understand policy rules
  - Better at structured compliance assessment
- **Fallback**: `mistral:7b-instruct-q4_K_M`

---

## Why Not Mistral 7B (Unquantized)?

1. **Overkill**: Most verification tasks don't need full 7B capability
2. **Slower**: Unquantized models are slower than quantized (10s+ vs 4-10s)
3. **Memory**: Uses more RAM unnecessarily
4. **Better Options**: Newer quantized models (llama3.1, deepseek-coder) are better optimized
5. **Exception**: Enhanced verifier currently uses it, but should migrate to quantized

---

## Implementation Strategy

### Phase 1: Instruction Validation (Current Priority)
1. **Start with `llama3.1:8b-instruct-q4_K_M`** for semantic analyzer, content quality, dependency analysis
2. **Fallback to `mistral:7b-instruct-q4_K_M`** if llama3.1 unavailable
3. **Test `qwen2.5:3b`** for speed-critical paths (if accuracy acceptable)

### Phase 2: Code Quality Verification (Future) ⚠️ RESOURCE-CONSTRAINED ENVIRONMENT
**⚠️ CRITICAL**: Intel-system already uses `codellama:13b` (18-22GB RAM). Adding another 13B model would exceed 32GB RAM.

1. **Primary**: Use **External API (GPT-4/Claude)** for deep code analysis
   - **No local RAM usage** - Critical for resource-constrained environment
   - **Better quality** - Can verify code written by GPT-4/Claude
   - **Cost**: ~$2-10 per million tokens (acceptable for critical reviews)
   
2. **Routine checks**: Use `deepseek-coder:6.7b-instruct-q4_K_M` (4-5GB RAM)
   - **Basic pattern matching** and obvious issues
   - **Low RAM footprint** - Works with intel-system running
   - **Fallback** when external API unavailable
   
3. **⚠️ NOT RECOMMENDED**: `codellama:13b` for Wingman
   - Would cause RAM exhaustion with intel-system running
   - Ollama can share model instances, but concurrent requests compete
   - Better to use external API for deep analysis
   
4. **Hybrid Strategy**:
   - Routine code checks: `deepseek-coder:6.7b-instruct-q4_K_M` (local, fast, low RAM)
   - Critical reviews: External API (GPT-4/Claude) - No RAM usage, best quality
   - Production deployments: Always use external API

### Phase 3: Test Results Verification (Future)
1. **Use `llama3.1:8b-instruct-q4_K_M`** for test output analysis
2. **Pattern-based validation** for simple pass/fail checks (no LLM needed)

### Migration Path
1. **Immediate**: Migrate enhanced verifier from `mistral:7b` to `llama3.1:8b-instruct-q4_K_M`
2. **Short-term**: Deploy instruction validation validators with `llama3.1:8b-instruct-q4_K_M`
3. **Medium-term**: Add code quality verification with `deepseek-coder:6.7b-instruct-q4_K_M`
4. **Long-term**: Add test result verification with `llama3.1:8b-instruct-q4_K_M`

---

## Model Capability Testing

**Before deploying code quality verification, test model capabilities:**

1. **Test Code Writing**: Ask model to write production-quality Python code
   - If model cannot write quality code, it cannot verify code written by GPT-4/Claude
   - Test with complex requirements (async, error handling, type hints, etc.)

2. **Test Code Review**: Give model code written by GPT-4/Claude
   - Can it identify optimization opportunities?
   - Can it catch subtle bugs?
   - Can it provide strategic recommendations?

3. **Test Optimization**: Give model suboptimal code
   - Can it suggest improvements?
   - Are recommendations actually better?

**Expected Results:**
- **6.7B-8B models**: May catch obvious issues, but miss subtle problems
- **13B models**: Better at deep analysis, but may still struggle with GPT-4/Claude code
- **External APIs (GPT-4/Claude)**: Can verify code written by equally powerful models

---

## External API Integration (Optional, for Critical Code Reviews)

**When to Use External APIs:**
- Production deployments
- Security-sensitive code
- Code written by GPT-4/Claude (need equal or greater capability)
- Strategic code reviews requiring optimization recommendations

**Implementation Options:**

1. **OpenAI GPT-4**:
   - Model: `gpt-4` or `gpt-4-turbo`
   - Cost: ~$10 per million tokens (input), ~$30 per million tokens (output)
   - Best for: Deep code analysis, optimization recommendations

2. **Anthropic Claude**:
   - Model: `claude-3-5-sonnet` or `claude-3-opus`
   - Cost: ~$3-15 per million tokens
   - Best for: Code review, strategic recommendations

3. **Hybrid Approach**:
   - Use local `codellama:13b` for routine checks
   - Use external API for critical reviews (configurable threshold)
   - Cost optimization: Only use external API when risk level is HIGH

**Configuration Example:**
```python
# Use external API for:
# - Production deployments (deployment_env == "prd")
# - High-risk operations (risk_level == "HIGH")
# - Code quality score below threshold (< 70)
# - Explicit flag: use_external_api=True
```

---

## Resource Requirements & Constraints ⚠️ CRITICAL: CONCURRENT USAGE

**Your System Resources:**
- **RAM**: 32 GB total
- **Disk**: 181 GB available ✅ (Plenty of space)
- **Current Models**: `codellama:13b` (7.4GB) and `codellama:13b-instruct-q4_K_M` (7.9GB) already installed ✅

**⚠️ CRITICAL CONSTRAINT: Concurrent Systems Running:**
- **Intel-system**: Uses `codellama:13b` (14-16GB RAM) + `mistral:7b` (4-6GB RAM) = **18-22GB RAM**
- **Mem0 TEST**: Running (LLM usage unknown, check mem0 config)
- **Mem0 PRD**: Running (LLM usage unknown, check mem0 config)
- **Wingman TEST**: Uses `mistral:7b` (4-6GB RAM)
- **Wingman PRD**: Uses `mistral:7b` (4-6GB RAM)
- **System overhead**: ~2-4GB RAM

**Current RAM Usage Estimate:**
- Intel-system: 18-22GB
- Wingman TEST: 4-6GB
- Wingman PRD: 4-6GB
- Mem0 (TEST + PRD): Unknown (estimate 2-4GB if using LLMs)
- System: 2-4GB
- **Total**: **30-36GB** (already near/at capacity!)

**⚠️ PROBLEM**: If Wingman adds `codellama:13b` for code quality verification:
- **Quantized** (`codellama:13b-instruct-q4_K_M`): +8-10GB RAM
- **Unquantized** (`codellama:13b`): +14-16GB RAM
- **Total potential**: **38-52GB** (exceeds 32GB RAM!)

**Model Memory Requirements:**
- **codellama:13b** (unquantized): ~7.4GB disk, ~14-16GB RAM when loaded
- **codellama:13b-instruct-q4_K_M** (quantized): ~7.9GB disk, ~8-10GB RAM when loaded
- **mistral:7b** (unquantized): ~4.4GB disk, ~4-6GB RAM when loaded
- **llama3.1:8b-instruct-q4_K_M** (quantized): ~4.9GB disk, ~5-7GB RAM when loaded

**Performance Considerations:**
- **13B unquantized**: Slower inference (~15-30s per request), higher quality
- **13B quantized (q4_K_M)**: Faster inference (~8-15s per request), slightly lower quality
- **Recommendation**: Use quantized version (`codellama:13b-instruct-q4_K_M`) for better performance while maintaining quality

**⚠️ RECOMMENDATION: Resource-Constrained Environment**

Given concurrent usage with intel-system and mem0, **codellama:13b is NOT feasible** for Wingman code quality verification without:
1. **External API option** (GPT-4/Claude) - No local RAM usage
2. **Model sharing** - Intel-system and Wingman share same `codellama:13b` instance (Ollama handles this, but concurrent requests compete)
3. **Smaller models** - Use `deepseek-coder:6.7b-instruct-q4_K_M` (4-5GB RAM) for basic code scanning, external API for deep analysis
4. **Sequential usage** - Queue code quality checks when intel-system is idle

**Best Strategy for Resource-Constrained Environment:**
- **Routine code checks**: `deepseek-coder:6.7b-instruct-q4_K_M` (4-5GB RAM, acceptable for basic scanning)
- **Critical code reviews**: External API (GPT-4/Claude) - No local RAM usage, better quality
- **Avoid**: `codellama:13b` for Wingman (would cause RAM exhaustion with intel-system running)

---

**Current**: Host Ollama (port 11434)  
**Access**: Containers use `host.docker.internal:11434`  
**Models**: Available on host, shared across all containers

**No changes needed** - validators will use `ollama run <model>` directly from containers, which accesses host Ollama automatically.

---

## Model Selection Summary

| Verification Task | Primary Model | Fallback Model | External API Option | When |
|------------------|---------------|----------------|---------------------|------|
| Semantic Analysis | `llama3.1:8b-instruct-q4_K_M` | `mistral:7b-instruct-q4_K_M` | N/A | Phase 1 |
| Content Quality | `llama3.1:8b-instruct-q4_K_M` | `mistral:7b-instruct-q4_K_M` | N/A | Phase 1 |
| Dependency Analysis | `llama3.1:8b-instruct-q4_K_M` | `mistral:7b-instruct-q4_K_M` | N/A | Phase 1 |
| **Code Quality** | **`deepseek-coder:6.7b-instruct-q4_K_M`** (resource-constrained) | `llama3.1:8b-instruct-q4_K_M` | **GPT-4/Claude** (critical, recommended) | Future |
| **Code Optimization** | **External API (GPT-4/Claude)** (no local RAM) | `deepseek-coder:6.7b-instruct-q4_K_M` | **GPT-4/Claude** (critical) | Future |
| Security Scanning | Pattern + `deepseek-coder:6.7b-instruct-q4_K_M` | `llama3.1:8b-instruct-q4_K_M` | GPT-4/Claude (critical) | Future |
| Test Results | `llama3.1:8b-instruct-q4_K_M` | `mistral:7b-instruct-q4_K_M` | N/A | Future |
| Claim Verification | `llama3.1:8b-instruct-q4_K_M` | `mistral:7b-instruct-q4_K_M` | N/A | Migrate from mistral:7b |
| Compliance | `llama3.1:8b-instruct-q4_K_M` | `mistral:7b-instruct-q4_K_M` | N/A | Future |

---

**Last Updated**: 2026-01-22  
**Recommendation**: 
- **Phase 1 (Current)**: Use `llama3.1:8b-instruct-q4_K_M` as primary for all instruction validation tasks
- **Phase 2 (Code Quality)**: **⚠️ RESOURCE-CONSTRAINED** - Use **External API (GPT-4/Claude)** for deep code analysis
  - **Reason**: Intel-system already uses `codellama:13b` (18-22GB RAM). Adding another 13B model would exceed 32GB RAM.
  - **Routine checks**: `deepseek-coder:6.7b-instruct-q4_K_M` (4-5GB RAM, acceptable for basic scanning)
  - **Critical reviews**: External API (GPT-4/Claude) - No local RAM usage, better quality
  - **⚠️ NOT RECOMMENDED**: `codellama:13b` for Wingman (would cause RAM exhaustion)
- **Migration**: Replace `mistral:7b` (unquantized) with quantized models across all verification tasks

**Key Insight**: 
1. Code quality verification requires models that can **write** high-quality code themselves
2. **Resource constraints matter**: With intel-system using `codellama:13b`, Wingman cannot add another 13B model
3. **Solution**: External API (GPT-4/Claude) for deep analysis, smaller local models for routine checks
4. **Cost-benefit**: External API cost (~$2-10 per million tokens) is acceptable for critical code reviews vs RAM exhaustion
