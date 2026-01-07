# CV Automation + Wingman Integration

> **Service**: CV Automation (Document Processing & Job Application System)  
> **Integration Level**: Full (Phases 2, 3, 4)

---

## Overview

CV Automation processes CVs/resumes and automates job applications. Wingman integration provides:

1. **Instruction validation** before document processing
2. **Audit logging** of all CV operations
3. **Verification** of generated documents
4. **Human approval** for job submissions and bulk operations

---

## Configuration

Add to your CV Automation `.env`:

```bash
# Wingman Integration
WINGMAN_URL=http://127.0.0.1:5001  # PRD
WINGMAN_WORKER_ID=cv-automation
```

---

## Integration Points

### 1. CV Processing Pipeline

```python
from wingman_client import WingmanClient

wingman = WingmanClient()
wingman.worker_id = "cv-automation"

def process_cv(cv_path: str, output_format: str = "pdf"):
    # Validate the processing instruction
    instruction = f"""
    DELIVERABLES: Process CV and generate {output_format}
    SUCCESS_CRITERIA: Output file created, all sections parsed
    BOUNDARIES: Read input file only, write to output directory
    DEPENDENCIES: PDF libraries, template system
    MITIGATION: Keep original file unchanged
    TEST_PROCESS: Verify output file is valid {output_format}
    TEST_RESULTS_FORMAT: File validation result
    RESOURCE_REQUIREMENTS: 512MB RAM
    RISK_ASSESSMENT: Low - document transformation
    QUALITY_METRICS: All required fields extracted
    """
    
    result = wingman.check_instruction(instruction)
    if not result.get("approved"):
        raise Exception(f"Instruction rejected: {result.get('missing_sections')}")
    
    wingman.log_claim(f"Started CV processing: {cv_path}")
    
    # Process the CV
    output_path = transform_cv(cv_path, output_format)
    
    wingman.log_claim(f"Created file {output_path}")
    
    # Verify output was created
    verdict = wingman.verify_claim(f"Created file {output_path}")
    if verdict == "FALSE":
        raise Exception("CV output file not created!")
    
    wingman.log_claim(f"Completed CV processing: {output_path}")
    return output_path
```

### 2. Job Application Submission (Requires Approval)

```python
def submit_application(job_id: str, cv_path: str, cover_letter: str):
    """Job submissions are high-risk and require human approval"""
    
    instruction = f"""
    DELIVERABLES: Submit job application to {job_id}
    SUCCESS_CRITERIA: Application confirmed submitted
    BOUNDARIES: Single application, no duplicate submissions
    DEPENDENCIES: Job portal API access
    MITIGATION: Retry on failure, log all attempts
    TEST_PROCESS: Verify submission confirmation received
    TEST_RESULTS_FORMAT: Confirmation ID or error
    RESOURCE_REQUIREMENTS: Network access
    RISK_ASSESSMENT: HIGH - external submission on behalf of user
    QUALITY_METRICS: Successful submission or clear error
    
    Job ID: {job_id}
    CV: {cv_path}
    """
    
    # This WILL block until human approves
    if not wingman.request_approval("Job Application Submission", instruction):
        raise Exception("Application submission not approved")
    
    wingman.log_claim(f"Starting job application for {job_id}")
    
    # Submit the application
    confirmation = job_portal.submit(job_id, cv_path, cover_letter)
    
    wingman.log_claim(f"Submitted application to {job_id}, confirmation: {confirmation}")
    
    return confirmation
```

### 3. Bulk CV Generation

```python
def generate_tailored_cvs(base_cv: str, job_listings: list):
    """Generate multiple tailored CVs for different jobs"""
    
    wingman.log_claim(f"Starting bulk CV generation for {len(job_listings)} jobs")
    
    results = []
    for job in job_listings:
        try:
            tailored_cv = tailor_cv_for_job(base_cv, job)
            output_path = f"/data/cvs/tailored_{job['id']}.pdf"
            save_cv(tailored_cv, output_path)
            
            wingman.log_claim(f"Created tailored CV for job {job['id']}: {output_path}")
            results.append({"job_id": job['id'], "cv_path": output_path, "status": "success"})
            
        except Exception as e:
            wingman.log_claim(f"Failed to generate CV for job {job['id']}: {e}")
            results.append({"job_id": job['id'], "status": "failed", "error": str(e)})
    
    wingman.log_claim(f"Completed bulk CV generation: {len([r for r in results if r['status'] == 'success'])} successful")
    
    return results
```

---

## High-Risk Operations (Always Require Approval)

These operations in CV Automation should **always** go through Wingman approval:

| Operation | Risk Level | Why |
|-----------|------------|-----|
| Job submission | HIGH | External action on user's behalf |
| Cover letter auto-send | HIGH | Sends email to potential employers |
| Profile update | MEDIUM | Modifies user's public presence |
| Bulk operations | HIGH | Large-scale changes |

---

## Recommended Claims

| Operation | Claim Format |
|-----------|-------------|
| CV processing start | `Started CV processing: {path}` |
| CV output created | `Created file {output_path}` |
| Job application | `Submitted application to {job_id}, confirmation: {id}` |
| Bulk generation | `Generated {count} tailored CVs` |
| Error | `Failed to {operation}: {error}` |

---

## Verification Patterns

```python
# Verify generated files exist
wingman.verify_claim("Created file /data/cvs/output.pdf")

# Verify PDF is valid (enhanced verifier)
wingman.verify_claim("Created valid PDF at /data/cvs/output.pdf", use_enhanced=True)
```

---

## Testing

```bash
export WINGMAN_URL=http://127.0.0.1:8101  # TEST
export WINGMAN_WORKER_ID=cv-automation-test

python3 -c "
from wingman_client import WingmanClient
w = WingmanClient()

# Test instruction validation
result = w.check_instruction('''
DELIVERABLES: Test CV processing
SUCCESS_CRITERIA: Output created
BOUNDARIES: Read only
DEPENDENCIES: None
MITIGATION: None
TEST_PROCESS: Manual check
TEST_RESULTS_FORMAT: Text
RESOURCE_REQUIREMENTS: Low
RISK_ASSESSMENT: Low
QUALITY_METRICS: None
''')
print('Instruction check:', result)

# Test claim logging
w.log_claim('Test claim from CV Automation')
print('Logged successfully')
"
```

---

## Security Considerations

1. **Never auto-submit** job applications without human approval
2. **Log but don't expose** personal details in claims
3. **Verify all file outputs** before proceeding to next step
4. **Use PRD approval gates** for all external-facing operations
