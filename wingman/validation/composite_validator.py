"""
Wingman Composite Validator - Aggregates all 4 validators.

Runs code_scanner, content_quality_validator, dependency_analyzer, semantic_analyzer.
Weighted scoring: code_scanner 30%, content_quality 25%, dependency 20%, semantic 25%.
Auto-reject if ANY validator score < 30 (hard floor).
Auto-reject if code_scanner finds secrets (immediate fail).
Auto-approve if ALL validators score >= 90 AND risk_level is LOW.
Otherwise: manual review (HITL).
"""

from typing import Any, Dict

from validation.code_scanner import CodeScanner
from validation.content_quality_validator import ContentQualityValidator
from validation.dependency_analyzer import DependencyAnalyzer
from validation.semantic_analyzer import SemanticAnalyzer


# Map dependency/semantic risk_level to a 0-100 score for weighting
RISK_TO_SCORE = {"LOW": 90, "MEDIUM": 60, "HIGH": 30, "CRITICAL": 10}


class CompositeValidator:
    """Runs all four validators and produces overall score and recommendation."""

    def __init__(self):
        self.code_scanner = CodeScanner()
        self.content_quality = ContentQualityValidator()
        self.dependency_analyzer = DependencyAnalyzer()
        self.semantic_analyzer = SemanticAnalyzer()

    def _risk_rank(self, r: str) -> int:
        return ("LOW", "MEDIUM", "HIGH", "CRITICAL").index(r) if r in ("LOW", "MEDIUM", "HIGH", "CRITICAL") else 0

    def validate(self, instruction_text: str) -> Dict[str, Any]:
        """Run all validators and return overall_score, recommendation, validator_scores, risk_level, reasoning."""
        code_result = self.code_scanner.scan(instruction_text)
        content_result = self.content_quality.validate(instruction_text)
        dep_result = self.dependency_analyzer.analyze(instruction_text)
        semantic_result = self.semantic_analyzer.analyze(instruction_text)

        code_score = code_result["score"]
        content_score = content_result["score"]
        dep_score = RISK_TO_SCORE.get(dep_result["risk_level"], 50)
        semantic_score = semantic_result["score"]

        validator_scores = {
            "code_scanner": code_score,
            "content_quality": content_score,
            "dependency_analyzer": dep_score,
            "semantic_analyzer": semantic_score,
        }

        # Hard floor: any validator below 30 -> REJECT
        if min(validator_scores.values()) < 30:
            overall_score = int(0.3 * code_score + 0.25 * content_score + 0.2 * dep_score + 0.25 * semantic_score)
            overall_score = max(0, min(100, overall_score))
            return {
                "overall_score": overall_score,
                "recommendation": "REJECT",
                "validator_scores": validator_scores,
                "risk_level": max(
                    [code_result.get("risk_level", "LOW"), dep_result["risk_level"], semantic_result["risk_level"]],
                    key=self._risk_rank,
                ),
                "reasoning": "One or more validators scored below 30 (hard floor).",
            }

        # Secrets found -> REJECT
        if code_result.get("secrets_found"):
            overall_score = int(0.3 * code_score + 0.25 * content_score + 0.2 * dep_score + 0.25 * semantic_score)
            overall_score = max(0, min(100, overall_score))
            return {
                "overall_score": overall_score,
                "recommendation": "REJECT",
                "validator_scores": validator_scores,
                "risk_level": "CRITICAL",
                "reasoning": "Code scanner found secrets or credentials; immediate reject.",
            }

        overall_score = int(0.3 * code_score + 0.25 * content_score + 0.2 * dep_score + 0.25 * semantic_score)
        overall_score = max(0, min(100, overall_score))

        risk_levels = [
            code_result.get("risk_level", "LOW"),
            dep_result["risk_level"],
            semantic_result["risk_level"],
        ]
        risk_level = max(risk_levels, key=self._risk_rank)

        # Auto-approve only if all >= 90 and risk is LOW
        if all(s >= 90 for s in validator_scores.values()) and risk_level == "LOW":
            recommendation = "APPROVE"
            reasoning = "All validators passed with score >= 90 and risk LOW."
        else:
            recommendation = "MANUAL_REVIEW"
            reasoning = f"Overall score {overall_score}; risk {risk_level}. Manual review required."

        return {
            "overall_score": overall_score,
            "recommendation": recommendation,
            "validator_scores": validator_scores,
            "risk_level": risk_level,
            "reasoning": reasoning,
        }
