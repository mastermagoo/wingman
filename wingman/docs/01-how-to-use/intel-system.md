# Intel System + Wingman Integration

> **Service**: Intel System (Email/Calendar Intelligence Pipeline)  
> **Integration Level**: Full (Phases 2, 3, 4)

---

## Overview

Intel System processes emails and calendar events to generate intelligence. Wingman provides:

1. **Instruction validation** before processing batches
2. **Audit logging** of all extraction/analysis claims
3. **Verification** that files were actually created
4. **Human approval** for sensitive operations (PRD deployments, schema changes)

---

## Configuration

Add to your Intel System `.env`:

```bash
# Wingman Integration
WINGMAN_URL=http://127.0.0.1:5001  # PRD
WINGMAN_WORKER_ID=intel-system-extractor

# For approval-protected endpoints (if enabled)
WINGMAN_APPROVAL_READ_KEY=<your-key>
WINGMAN_APPROVAL_DECIDE_KEY=<your-key>
```

---

## Integration Points

### 1. Email Extraction Pipeline

```python
# In your email extractor
from wingman_client import WingmanClient

wingman = WingmanClient()

def process_emails():
    # Log start
    wingman.log_claim("Started email extraction batch")
    
    # Process each email
    for email in fetch_new_emails():
        try:
            result = extract_intelligence(email)
            wingman.log_claim(f"Extracted intelligence from email {email.id}")
        except Exception as e:
            wingman.log_claim(f"Failed to process email {email.id}: {e}")
    
    # Log completion with verification
    summary_path = save_batch_summary()
    wingman.log_claim(f"Created batch summary at {summary_path}")
    
    # Verify the file actually exists
    verdict = wingman.verify_claim(f"Created file {summary_path}")
    if verdict == "FALSE":
        raise Exception("Summary file verification failed!")
```

### 2. Calendar Sync

```python
def sync_calendar():
    wingman.log_claim("Started calendar sync")
    
    events = fetch_calendar_events()
    wingman.log_claim(f"Fetched {len(events)} calendar events")
    
    for event in events:
        store_event(event)
    
    wingman.log_claim(f"Stored {len(events)} events to database")
    wingman.log_claim("Completed calendar sync")
```

### 3. Database Migrations (Requires Approval)

```python
def run_migration(migration_sql: str):
    # High-risk: requires human approval
    instruction = f"""
    DELIVERABLES: Execute database migration
    SUCCESS_CRITERIA: Schema updated, no data loss
    BOUNDARIES: Schema changes only, no data deletion
    DEPENDENCIES: Database connection, backup available
    MITIGATION: Rollback script ready
    TEST_PROCESS: Verify table structure after migration
    TEST_RESULTS_FORMAT: Schema diff output
    RESOURCE_REQUIREMENTS: Database write access
    RISK_ASSESSMENT: HIGH - schema modification
    QUALITY_METRICS: Zero data loss
    
    SQL: {migration_sql}
    """
    
    # This will block until human approves (or auto-approve in DEV)
    if not wingman.request_approval("Database Migration", instruction):
        raise Exception("Migration not approved")
    
    wingman.log_claim(f"Starting migration: {migration_sql[:50]}...")
    execute_sql(migration_sql)
    wingman.log_claim("Migration completed successfully")
```

---

## Recommended Claims to Log

| Operation | Claim Format |
|-----------|-------------|
| Batch start | `Started email extraction batch` |
| Email processed | `Extracted intelligence from email {id}` |
| File created | `Created file {path}` |
| Database write | `Stored {count} records to {table}` |
| Batch complete | `Completed {operation} with {count} items` |
| Error | `Failed to {operation}: {error}` |

---

## Verification Patterns

### Files Intel System Creates

```python
# These claims can be verified by Wingman's filesystem verifier
wingman.verify_claim("Created file /data/intel/summaries/2026-01-06.json")
wingman.verify_claim("Created file /data/intel/exports/emails.csv")
```

### Processes Intel System Runs

```python
# These can be verified by Wingman's process verifier
wingman.verify_claim("Process postgres is running")
wingman.verify_claim("Process redis-server is running")
```

---

## Error Handling

```python
def safe_operation():
    try:
        # Your operation
        result = do_work()
        wingman.log_claim(f"Completed work: {result}")
    except Exception as e:
        # Always log failures
        wingman.log_claim(f"Operation failed: {e}")
        raise
```

---

## Testing Integration

```bash
# Test from Intel System container/environment
export WINGMAN_URL=http://127.0.0.1:8101  # TEST environment
export WINGMAN_WORKER_ID=intel-system-test

python3 -c "
from wingman_client import WingmanClient
w = WingmanClient()
print('Health:', w.health_check())
w.log_claim('Test claim from Intel System')
print('Logged test claim')
"
```
