# LLM Model Selection for Wingman Validators

**Date**: 2026-01-22  
**Status**: RECOMMENDATION  
**Environment**: Host Ollama (port 11434), accessed via `host.docker.internal:11434` from containers

---

## Current State

**Wingman currently uses**: `mistral:7b` (unquantized, 4.4GB)  
**Environment**: Host Ollama, accessed from containers via `host.docker.internal:11434`

---

## Available Quantized Models (Intel System)

| Model | Size | Speed | Best For | Status |
|-------|------|-------|----------|--------|
| `qwen2.5:3b` | 1.9GB | Fastest (4s) | Simple classification | ⚠️ May miss context |
| `llama3.1:8b-instruct-q4_K_M` | 4.9GB | Medium (10s) | Instruction following | ✅ Recommended |
| `deepseek-coder:6.7b-instruct-q4_K_M` | 4.1GB | Fast | Code analysis | ✅ For code scanner |
| `mistral:7b-instruct-q4_K_M` | 4.4GB | Medium | General purpose | ✅ Fallback |
| `mistral:7b` (unquantized) | 4.4GB | Slower | Legacy | ❌ OTT for validation |

---

## Recommendations

### For Semantic Analyzer (Risk Detection)
**Primary**: `llama3.1:8b-instruct-q4_K_M`
- Better instruction following
- Handles context better than qwen2.5:3b
- Quantized (faster than unquantized Mistral 7B)

**Fallback**: `mistral:7b-instruct-q4_K_M` (if llama3.1 unavailable)

### For Dependency Analyzer (Blast Radius)
**Primary**: `llama3.1:8b-instruct-q4_K_M`
- Needs to understand service relationships
- Better reasoning than smaller models

### For Content Quality Validator (Section Scoring)
**Primary**: `llama3.1:8b-instruct-q4_K_M`
- Multi-section analysis requires good instruction following
- Better at structured output

### For Code Scanner (Pattern Matching)
**Primary**: `deepseek-coder:6.7b-instruct-q4_K_M` (if using LLM for complex patterns)
- Code-specialized
- Better at understanding code context
- **Note**: Code scanner should be mostly pattern-based, LLM optional

---

## Why Not Mistral 7B (Unquantized)?

1. **Overkill**: Validation tasks don't need full 7B capability
2. **Slower**: Unquantized models are slower than quantized
3. **Memory**: Uses more RAM unnecessarily
4. **Better Options**: Newer quantized models (llama3.1, qwen2.5) are better optimized

---

## Implementation Strategy

1. **Start with `llama3.1:8b-instruct-q4_K_M`** (best balance)
2. **Fallback to `mistral:7b-instruct-q4_K_M`** if llama3.1 unavailable
3. **Test `qwen2.5:3b`** for speed-critical paths (if accuracy acceptable)
4. **Avoid `mistral:7b`** (unquantized) - OTT for validation

---

## Environment Configuration

**Current**: Host Ollama (port 11434)  
**Access**: Containers use `host.docker.internal:11434`  
**Models**: Available on host, shared across all containers

**No changes needed** - validators will use `ollama run <model>` directly from containers, which accesses host Ollama automatically.

---

**Last Updated**: 2026-01-22  
**Recommendation**: Use `llama3.1:8b-instruct-q4_K_M` as primary, `mistral:7b-instruct-q4_K_M` as fallback
