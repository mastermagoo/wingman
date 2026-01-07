# Mem0 + Wingman Integration

> **Service**: Mem0 (Memory/Context Management System)  
> **Integration Level**: Audit (Phase 3)

---

## Overview

Mem0 manages persistent memory and context for AI systems. Wingman integration provides:

1. **Audit logging** of memory operations (create, update, delete)
2. **Verification** of memory state claims
3. **Approval gates** for bulk memory operations or sensitive data handling

---

## Configuration

Add to your Mem0 `.env`:

```bash
# Wingman Integration
WINGMAN_URL=http://127.0.0.1:5001  # PRD
WINGMAN_WORKER_ID=mem0-service
```

---

## Integration Points

### 1. Memory Creation/Updates

```python
from wingman_client import WingmanClient

wingman = WingmanClient()
wingman.worker_id = "mem0-service"

def store_memory(key: str, value: dict, user_id: str):
    # Store in Mem0
    mem0.add(key, value, user_id=user_id)
    
    # Log to Wingman (no PII in claim!)
    wingman.log_claim(f"Stored memory {key} for user {user_id[:8]}...")

def update_memory(key: str, value: dict):
    mem0.update(key, value)
    wingman.log_claim(f"Updated memory {key}")

def delete_memory(key: str):
    mem0.delete(key)
    wingman.log_claim(f"Deleted memory {key}")
```

### 2. Bulk Operations (Requires Approval)

```python
def bulk_delete_memories(user_id: str, reason: str):
    """Bulk delete requires human approval"""
    
    instruction = f"""
    DELIVERABLES: Delete all memories for user
    SUCCESS_CRITERIA: All user memories removed
    BOUNDARIES: Single user only, no cascade
    DEPENDENCIES: Mem0 connection
    MITIGATION: Backup created before deletion
    TEST_PROCESS: Verify memory count is zero
    TEST_RESULTS_FORMAT: Deletion count
    RESOURCE_REQUIREMENTS: Standard
    RISK_ASSESSMENT: HIGH - data deletion
    QUALITY_METRICS: Complete deletion, no orphans
    
    User: {user_id[:8]}...
    Reason: {reason}
    """
    
    if not wingman.request_approval("Bulk Memory Deletion", instruction):
        raise Exception("Bulk deletion not approved")
    
    wingman.log_claim(f"Starting bulk delete for user {user_id[:8]}...")
    count = mem0.delete_all(user_id=user_id)
    wingman.log_claim(f"Deleted {count} memories for user {user_id[:8]}...")
    
    return count
```

### 3. Memory Export

```python
def export_user_memories(user_id: str, output_path: str):
    wingman.log_claim(f"Starting memory export for user {user_id[:8]}...")
    
    memories = mem0.get_all(user_id=user_id)
    
    with open(output_path, 'w') as f:
        json.dump(memories, f)
    
    wingman.log_claim(f"Created file {output_path}")
    
    # Verify the export actually happened
    verdict = wingman.verify_claim(f"Created file {output_path}")
    if verdict == "FALSE":
        raise Exception("Export file not created!")
    
    wingman.log_claim(f"Exported {len(memories)} memories")
```

---

## Privacy Considerations

**Never log PII in claims!**

```python
# ❌ BAD - Contains PII
wingman.log_claim(f"Stored memory for user john.doe@example.com")

# ✅ GOOD - Anonymized
wingman.log_claim(f"Stored memory for user a1b2c3d4...")

# ✅ GOOD - Hash or truncate IDs
wingman.log_claim(f"Stored memory {key} for user {user_id[:8]}...")
```

---

## Recommended Claims

| Operation | Claim Format |
|-----------|-------------|
| Memory create | `Stored memory {key} for user {id[:8]}...` |
| Memory update | `Updated memory {key}` |
| Memory delete | `Deleted memory {key}` |
| Bulk operation | `Bulk {operation} for user {id[:8]}...: {count} items` |
| Export | `Exported {count} memories to {path}` |

---

## Testing

```bash
export WINGMAN_URL=http://127.0.0.1:8101  # TEST
export WINGMAN_WORKER_ID=mem0-test

python3 -c "
from wingman_client import WingmanClient
w = WingmanClient()
w.log_claim('Test memory operation from Mem0')
print('Logged successfully')
"
```
