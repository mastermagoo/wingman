# instruction_validator.py - Phase 2: 10-Point Framework Validator
class InstructionValidator:
    REQUIRED_SECTIONS = [
        "DELIVERABLES", "SUCCESS_CRITERIA", "BOUNDARIES",
        "DEPENDENCIES", "MITIGATION", "TEST_PROCESS",
        "TEST_RESULTS_FORMAT", "RESOURCE_REQUIREMENTS",
        "RISK_ASSESSMENT", "QUALITY_METRICS"
    ]
    
    def validate(self, instruction_text):
        score = 0
        missing = []
        validation = {}
        
        # Convert to upper for case-insensitive matching
        upper_text = instruction_text.upper()
        
        for section in self.REQUIRED_SECTIONS:
            if section in upper_text:
                score += 10
                validation[section] = "✅ Found"
            else:
                missing.append(section)
                validation[section] = "❌ Missing"
        
        # Policy checks
        policy_checks = {
            "no_hardcoded_secrets": "password" not in instruction_text.lower(),
            "no_forbidden_actions": "--force" not in instruction_text.lower(),
            "has_mitigation_plan": "MITIGATION" in upper_text
        }
        
        return {
            "approved": score >= 80,
            "score": score,
            "missing_sections": missing,
            "validation": validation,
            "policy_checks": policy_checks
        }

