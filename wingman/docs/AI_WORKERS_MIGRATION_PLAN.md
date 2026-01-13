# AI Workers Infrastructure Migration Plan

**Date**: 2026-01-12
**Purpose**: Copy intel-system ai-workers infrastructure to wingman for imperial separation
**Goal**: Zero cross-contamination between repos

---

## WHY THIS IS NECESSARY

### Problem
- Intel-system ai-workers proven with 200 workers
- Wingman needs same infrastructure for validation enhancement (35 workers)
- **Risk**: If we use intel-system ai-workers directly, we'll contaminate both repos
- **Solution**: Copy infrastructure to wingman, keep repos completely separate

### Benefits
✅ **Imperial separation** - Each repo has own ai-workers infrastructure
✅ **No cross-contamination** - Git commits stay clean
✅ **Independent evolution** - Intel-system and wingman can diverge
✅ **Clear ownership** - wingman/ai-workers belongs to wingman only

---

## WHAT TO COPY (Infrastructure Only)

### ✅ COPY THESE (Templates & Structure)

#### 1. Meta-Worker Templates
**Source**: `/Volumes/Data/ai_projects/intel-system/ai-workers/workers/meta-workers/`
**Destination**: `/Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/meta-workers/`
**Files**:
- `META_WORKER_01_INSTRUCTION.md` through `META_WORKER_20_INSTRUCTION.md`
- `META_WORKER_INDEX.md` (if exists)

**Why**: These are template instructions for generating workers - generic and reusable

#### 2. Worker Instruction Template
**Source**: Search intel-system for `WORKER_INSTRUCTION_TEMPLATE.md` or similar
**Destination**: `/Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/templates/`
**Files**:
- Worker instruction template (10-point framework)
- Meta-worker template

**Why**: Standardized template ensures all workers follow same structure

#### 3. Results Structure
**Source**: `/Volumes/Data/ai_projects/intel-system/ai-workers/results/` (structure only)
**Destination**: `/Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/results/`
**Files**:
- Create empty directory structure
- Add README.md explaining structure
- **DO NOT** copy actual intel-system results

**Why**: Need consistent results storage format

#### 4. Scripts (If Exist)
**Source**: `/Volumes/Data/ai_projects/intel-system/ai-workers/scripts/`
**Destination**: `/Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/scripts/`
**Files**:
- Orchestration scripts (Python/Bash)
- Execution scripts
- Validation scripts
- Result aggregation scripts

**Why**: Automation tools for executing workers in parallel

#### 5. Documentation
**Source**: `/Volumes/Data/ai_projects/intel-system/ai-workers/README.md`
**Destination**: `/Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/README.md`
**Content**: Adapt for wingman context (change references from intel-system to wingman)

**Why**: Documents how to use ai-workers infrastructure

---

## ❌ DO NOT COPY (Intel-System Specific)

### ❌ EXCLUDE THESE

#### 1. Intel-System Worker Definitions
**Source**: `/Volumes/Data/ai_projects/intel-system/ai-workers/workers/WORKER_*.md` (200 workers)
**Reason**: These are intel-system specific (PostgreSQL schemas, Neo4j, SAP, etc.)
**Action**: Skip entirely - we'll generate new wingman-specific workers

#### 2. Intel-System Results
**Source**: `/Volumes/Data/ai_projects/intel-system/ai-workers/results/*` (actual JSON/MD files)
**Reason**: These contain intel-system execution data
**Action**: Create empty directory structure only

#### 3. Intel-System Plans
**Source**: `/Volumes/Data/ai_projects/intel-system/docs/00-strategic/Environment Strategy/MEGA_DELEGATION_200_WORKERS_PLAN.md`
**Reason**: Intel-system specific task list
**Action**: Reference but don't copy - we have our own validation enhancement plan

#### 4. Intel-System Secrets
**Source**: Any `.env`, `config.json`, credentials
**Reason**: Security
**Action**: Absolutely exclude

---

## DIRECTORY STRUCTURE (After Copy)

```
wingman/
├── ai-workers/
│   ├── README.md                    ← Copied & adapted
│   ├── templates/
│   │   ├── WORKER_TEMPLATE.md      ← Copied from intel-system
│   │   └── META_WORKER_TEMPLATE.md ← Copied from intel-system
│   ├── meta-workers/
│   │   ├── META_WORKER_01_INSTRUCTION.md  ← Copied (generic template)
│   │   ├── META_WORKER_02_INSTRUCTION.md  ← Copied (generic template)
│   │   └── ... (20 total)
│   ├── workers/
│   │   ├── WORKER_001_Execution_Gateway.md  ← KEEP (wingman-specific, already exists)
│   │   ├── WORKER_002_Command_Allowlist.md  ← KEEP (wingman-specific)
│   │   └── ... (wingman workers, will add 35 more for validation)
│   ├── results/
│   │   ├── README.md               ← Create new (explains structure)
│   │   ├── meta-workers/           ← Empty directory
│   │   └── workers/                ← Empty directory
│   └── scripts/
│       ├── orchestrate.py          ← Copy from intel-system (if exists)
│       ├── validate.py             ← Copy from intel-system (if exists)
│       └── aggregate_results.py    ← Copy from intel-system (if exists)
```

---

## COPY PROCEDURE (Step-by-Step)

### Step 1: Verify Source Files Exist
```bash
# Check what exists in intel-system
ls -la /Volumes/Data/ai_projects/intel-system/ai-workers/
ls -la /Volumes/Data/ai_projects/intel-system/ai-workers/scripts/
ls -la /Volumes/Data/ai_projects/intel-system/ai-workers/workers/meta-workers/
```

### Step 2: Create Wingman Directory Structure
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman/ai-workers

# Create directories
mkdir -p templates
mkdir -p meta-workers
mkdir -p results/meta-workers
mkdir -p results/workers
mkdir -p scripts

# workers/ already exists, skip
```

### Step 3: Copy Meta-Worker Templates
```bash
# Copy meta-worker instruction templates (generic, reusable)
cp /Volumes/Data/ai_projects/intel-system/ai-workers/workers/meta-workers/META_WORKER_*.md \
   /Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/meta-workers/
```

### Step 4: Copy Scripts (If They Exist)
```bash
# Check if scripts exist first
if [ -d "/Volumes/Data/ai_projects/intel-system/ai-workers/scripts" ]; then
    cp /Volumes/Data/ai_projects/intel-system/ai-workers/scripts/*.py \
       /Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/scripts/ 2>/dev/null || true
    cp /Volumes/Data/ai_projects/intel-system/ai-workers/scripts/*.sh \
       /Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/scripts/ 2>/dev/null || true
fi
```

### Step 5: Find and Copy Worker Template
```bash
# Search for worker template in intel-system
find /Volumes/Data/ai_projects/intel-system -name "*WORKER*TEMPLATE*.md" -o -name "*template*.md" | grep -i worker

# Copy to wingman templates/ directory (do this manually after finding it)
```

### Step 6: Copy and Adapt README
```bash
# Copy README
cp /Volumes/Data/ai_projects/intel-system/ai-workers/README.md \
   /Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/README.md

# Edit to change all "intel-system" references to "wingman"
# (Do this manually or with sed)
```

### Step 7: Create Results README
```bash
cat > /Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/results/README.md << 'EOF'
# AI Workers Results (Wingman-Specific)

This directory stores execution results from wingman ai-workers.

## Structure

- `meta-workers/` - Results from meta-workers that generate worker instructions
- `workers/` - Results from individual worker executions

## Format

All results are stored in JSON format following this schema:

```json
{
  "worker_id": "001",
  "status": "pass/fail",
  "deliverables_created": ["file1.py", "file2.md"],
  "test_results": {
    "test1": "pass",
    "test2": "pass"
  },
  "evidence": "Validation output",
  "duration": 120,
  "timestamp": "2026-01-12T22:00:00Z"
}
```

## Rules

- Do NOT commit results to git (add to .gitignore)
- Results are local-only artifacts
- Keep results for retrospectives and debugging
EOF
```

### Step 8: Update .gitignore
```bash
# Add to wingman/.gitignore
cat >> /Volumes/Data/ai_projects/wingman-system/wingman/.gitignore << 'EOF'

# AI Workers results (local only)
ai-workers/results/*
!ai-workers/results/README.md
EOF
```

### Step 9: Verify No Intel-System Content
```bash
# Search for intel-system references in copied files
grep -r "intel-system" /Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/

# Search for SAP, Neo4j, ChromaDB (intel-system specific terms)
grep -r "SAP\|Neo4j\|ChromaDB" /Volumes/Data/ai_projects/wingman-system/wingman/ai-workers/

# If found, replace with wingman-specific terms or remove
```

### Step 10: Git Add Only ai-workers Infrastructure
```bash
cd /Volumes/Data/ai_projects/wingman-system/wingman

# Stage ONLY ai-workers infrastructure (not results)
git add ai-workers/templates/
git add ai-workers/meta-workers/
git add ai-workers/scripts/
git add ai-workers/README.md
git add ai-workers/results/README.md
git add .gitignore

# Verify no intel-system content staged
git diff --cached | grep -i "intel-system\|sap\|neo4j"
# (Should return nothing)

# Commit
git commit -m "infra: copy ai-workers infrastructure from intel-system

- Added meta-worker templates (generic, reusable)
- Added orchestration scripts (if exist)
- Added directory structure (results, templates)
- Updated .gitignore to exclude results
- No intel-system specific content included
- Imperial separation maintained

From: intel-system ai-workers (proven at 200 workers)
For: wingman validation enhancement (35 workers planned)
"
```

---

## VERIFICATION CHECKLIST

After copying, verify:

- [ ] ✅ All files are in wingman/ai-workers/ (not intel-system/)
- [ ] ✅ No intel-system worker definitions copied (WORKER_001-200)
- [ ] ✅ No intel-system results copied
- [ ] ✅ No references to "intel-system", "SAP", "Neo4j", "ChromaDB" in copied files
- [ ] ✅ README.md adapted for wingman context
- [ ] ✅ .gitignore updated to exclude results
- [ ] ✅ Git status shows only wingman/ files staged
- [ ] ✅ Meta-worker templates are generic (not intel-system specific)
- [ ] ✅ Scripts (if copied) don't reference intel-system paths
- [ ] ✅ No secrets or credentials copied

---

## ANTI-CONTAMINATION RULES

### Rule 1: One-Way Copy Only
- Copy FROM intel-system TO wingman (initial setup)
- After copy, the two diverge completely
- Never sync changes back and forth

### Rule 2: No Intel-System References
- Search all copied files for "intel-system"
- Replace with "wingman" or generic terms
- No intel-system specific terminology

### Rule 3: No Shared Workers
- Intel-system has WORKER_001-200 (their tasks)
- Wingman will have WORKER_001-035 (our tasks)
- Even if numbers overlap, content is completely different

### Rule 4: Separate Results
- intel-system/ai-workers/results/ → intel-system data
- wingman/ai-workers/results/ → wingman data
- Never mix or reference

### Rule 5: Git Boundaries
- intel-system commits never touch wingman/
- wingman commits never touch intel-system/
- Pre-commit hook already enforces this

---

## POST-COPY: NEXT STEPS

After copying infrastructure:

1. **Create Wingman Meta-Workers** (3 meta-workers)
   - META_WORKER_WINGMAN_01: Generate Phase 1 validators workers
   - META_WORKER_WINGMAN_02: Generate Phase 2 quality validator workers
   - META_WORKER_WINGMAN_03: Generate Phase 4 testing workers

2. **Execute Meta-Workers** (generates 35 worker instructions)
   - Run META_WORKER_WINGMAN_01 → outputs WORKER_001-010
   - Run META_WORKER_WINGMAN_02 → outputs WORKER_011-015
   - Run META_WORKER_WINGMAN_03 → outputs WORKER_016-035

3. **Submit to Wingman for Approval** (all 35 workers)
   - Each worker instruction validated by Wingman (≥80% score)
   - Rejected workers revised and resubmitted

4. **Execute Approved Workers** (parallel batches)
   - Batch 1: WORKER_001-005 (5 parallel)
   - Batch 2: WORKER_006-010 (5 parallel)
   - ... continue through all 35 workers

5. **Store Retrospectives in mem0**
   - Each worker writes lessons learned to mem0
   - Future workers learn from past executions

---

## SUCCESS CRITERIA

Migration successful when:
- ✅ All infrastructure copied to wingman/ai-workers/
- ✅ No intel-system specific content in copied files
- ✅ Git commit shows only wingman/ changes
- ✅ .gitignore prevents results from being committed
- ✅ Directory structure matches plan
- ✅ No cross-contamination detectable
- ✅ Ready to create wingman-specific meta-workers

---

**Migration Status**: PENDING
**Next Action**: Execute copy procedure (Steps 1-10)
