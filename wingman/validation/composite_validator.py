"""
Wingman Composite Validator - Profile-based validation.

Supports multiple validation profiles:
- OPERATIONAL: For read-only, low-risk commands (docker logs, curl, status checks)
- DEPLOYMENT: For write operations, deployments, schema changes (requires 10-point framework)

Each profile selects appropriate validators, weights, and thresholds.
Profile detection is automatic based on instruction content and task type.
"""

import re
from typing import Any, Dict, List

from validation.code_scanner import CodeScanner
from validation.content_quality_validator import ContentQualityValidator
from validation.dependency_analyzer import DependencyAnalyzer
from validation.semantic_analyzer import SemanticAnalyzer


# Map dependency/semantic risk_level to a 0-100 score for weighting
RISK_TO_SCORE = {"LOW": 90, "MEDIUM": 60, "HIGH": 30, "CRITICAL": 10}


# Validation profiles: define which validators to use and how to weight them
VALIDATION_PROFILES = {
    "operational": {
        "description": "Read-only, low-risk operational commands",
        "validators": ["code_scanner", "semantic_analyzer"],  # Skip content_quality (no framework needed)
        "weights": {
            "code_scanner": 0.6,      # Primary focus: safety (secrets, dangerous patterns)
            "semantic_analyzer": 0.4  # Secondary: intent analysis
        },
        "hard_floor": 30,              # Minimum score for any included validator
        "auto_approve_threshold": 85,  # Lower threshold for operational commands
        "auto_reject_threshold": 30
    },
    "deployment": {
        "description": "Deployments, schema changes, high-risk operations",
        "validators": ["code_scanner", "content_quality", "dependency_analyzer", "semantic_analyzer"],
        "weights": {
            "code_scanner": 0.3,
            "content_quality": 0.25,
            "dependency_analyzer": 0.2,
            "semantic_analyzer": 0.25
        },
        "hard_floor": 30,
        "auto_approve_threshold": 90,  # Strict threshold for deployments
        "auto_reject_threshold": 30
    }
}


# Keywords for profile detection
OPERATIONAL_KEYWORDS = [
    # Read operations
    r"\bdocker\s+(logs|ps|inspect|images|network|volume)\b",
    r"\bcurl\b.*\b(health|status|metrics|ping)\b",
    r"\b(cat|tail|head|less|grep|awk|sed)\b",
    r"\b(ls|pwd|whoami|date|uptime)\b",
    r"\bkubectl\s+get\b",
    r"\bkubectl\s+describe\b",
    # Status checks
    r"\b(health|status|check|verify|test|validate)\b.*\b(endpoint|api|service|container)\b",
    # Monitoring
    r"\b(show|display|list|view|read|fetch|query)\b",
]

DEPLOYMENT_KEYWORDS = [
    # Deployments
    r"\b(deploy|release|rollout|publish)\b",
    r"\bmigrat(e|ion)\b",
    r"\b(create|alter|drop)\s+(table|database|schema|index)\b",
    # Write operations
    r"\b(restart|stop|kill|remove|delete|rm)\b.*\b(container|service|pod)\b",
    r"\bdocker\s+(stop|kill|rm|restart|down)\b",
    r"\bkubectl\s+(apply|create|delete|patch|replace)\b",
    # Config changes
    r"\b(update|modify|change|set)\s+(config|env|variable|setting)\b",
    # Infrastructure
    r"\b(scale|resize|provision|destroy)\b",
]


class CompositeValidator:
    """Profile-based validator that selects appropriate validation strategy."""

    def __init__(self):
        self.code_scanner = CodeScanner()
        self.content_quality = ContentQualityValidator()
        self.dependency_analyzer = DependencyAnalyzer()
        self.semantic_analyzer = SemanticAnalyzer()

    def _risk_rank(self, r: str) -> int:
        return ("LOW", "MEDIUM", "HIGH", "CRITICAL").index(r) if r in ("LOW", "MEDIUM", "HIGH", "CRITICAL") else 0

    def detect_profile(self, instruction_text: str, task_name: str = "") -> str:
        """Detect which validation profile to use based on instruction content.

        Args:
            instruction_text: The instruction to classify
            task_name: Optional task name for additional context

        Returns:
            Profile name ("operational" or "deployment")
        """
        combined_text = f"{task_name} {instruction_text}".lower()

        # Check for deployment keywords first (stricter profile takes precedence)
        for pattern in DEPLOYMENT_KEYWORDS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return "deployment"

        # Check for operational keywords
        for pattern in OPERATIONAL_KEYWORDS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return "operational"

        # Default to deployment (safer/stricter) if uncertain
        return "deployment"

    def validate(self, instruction_text: str, task_name: str = "", profile_override: str = None) -> Dict[str, Any]:
        """Run validators based on detected profile and return overall_score, recommendation, etc.

        Args:
            instruction_text: The instruction to validate
            task_name: Optional task name for profile detection
            profile_override: Optional profile name to force a specific profile

        Returns:
            dict with keys: overall_score, recommendation, validator_scores, risk_level, reasoning, profile
        """
        # Detect or use override profile
        profile_name = profile_override if profile_override else self.detect_profile(instruction_text, task_name)
        profile = VALIDATION_PROFILES[profile_name]

        # Run all validators (even if not used in profile, for logging/visibility)
        code_result = self.code_scanner.scan(instruction_text)
        content_result = self.content_quality.validate(instruction_text)
        dep_result = self.dependency_analyzer.analyze(instruction_text)
        semantic_result = self.semantic_analyzer.analyze(instruction_text)

        all_scores = {
            "code_scanner": code_result["score"],
            "content_quality": content_result["score"],
            "dependency_analyzer": RISK_TO_SCORE.get(dep_result["risk_level"], 50),
            "semantic_analyzer": semantic_result["score"],
        }

        # Filter to profile-selected validators
        active_validators = profile["validators"]
        validator_scores = {k: v for k, v in all_scores.items() if k in active_validators}

        # Hard floor: any ACTIVE validator below threshold -> REJECT
        if min(validator_scores.values()) < profile["hard_floor"]:
            overall_score = self._calculate_weighted_score(validator_scores, profile["weights"])
            return {
                "overall_score": overall_score,
                "recommendation": "REJECT",
                "validator_scores": all_scores,  # Return all scores for visibility
                "active_validators": active_validators,
                "profile": profile_name,
                "risk_level": self._determine_risk_level(code_result, dep_result, semantic_result),
                "reasoning": f"Profile '{profile_name}': One or more validators scored below {profile['hard_floor']} (hard floor).",
            }

        # Secrets found -> IMMEDIATE REJECT (regardless of profile)
        if code_result.get("secrets_found"):
            overall_score = self._calculate_weighted_score(validator_scores, profile["weights"])
            return {
                "overall_score": overall_score,
                "recommendation": "REJECT",
                "validator_scores": all_scores,
                "active_validators": active_validators,
                "profile": profile_name,
                "risk_level": "CRITICAL",
                "reasoning": "Code scanner found secrets or credentials; immediate reject.",
            }

        # Calculate weighted score based on profile
        overall_score = self._calculate_weighted_score(validator_scores, profile["weights"])
        risk_level = self._determine_risk_level(code_result, dep_result, semantic_result)

        # Auto-approve if all ACTIVE validators meet threshold and risk is LOW
        if all(s >= profile["auto_approve_threshold"] for s in validator_scores.values()) and risk_level == "LOW":
            recommendation = "APPROVE"
            reasoning = f"Profile '{profile_name}': All validators passed with score >= {profile['auto_approve_threshold']} and risk LOW."
        else:
            recommendation = "MANUAL_REVIEW"
            reasoning = f"Profile '{profile_name}': Overall score {overall_score}; risk {risk_level}. Manual review required."

        return {
            "overall_score": overall_score,
            "recommendation": recommendation,
            "validator_scores": all_scores,
            "active_validators": active_validators,
            "profile": profile_name,
            "risk_level": risk_level,
            "reasoning": reasoning,
        }

    def _calculate_weighted_score(self, scores: Dict[str, int], weights: Dict[str, float]) -> int:
        """Calculate weighted average score based on profile weights."""
        total_score = sum(scores.get(validator, 0) * weights.get(validator, 0) for validator in weights.keys())
        return max(0, min(100, int(total_score)))

    def _determine_risk_level(self, code_result, dep_result, semantic_result) -> str:
        """Determine overall risk level from validator results."""
        risk_levels = [
            code_result.get("risk_level", "LOW"),
            dep_result["risk_level"],
            semantic_result["risk_level"],
        ]
        return max(risk_levels, key=self._risk_rank)
