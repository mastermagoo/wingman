"""
Instruction Composite Validator - Phase 6.3

Validates instruction documents against 10-point framework.
Provides early quality gates before expensive LLM execution.

Required Sections (10-point framework):
1. DELIVERABLES
2. SUCCESS_CRITERIA
3. BOUNDARIES
4. DEPENDENCIES
5. MITIGATION
6. TEST_PROCESS
7. TEST_RESULTS_FORMAT
8. TASK_CLASSIFICATION
9. RETROSPECTIVE
10. PERFORMANCE_REQUIREMENTS

Scoring:
- Each section: 0-10 points (100 points max)
- Penalties: -5 for missing section, -2 for incomplete section
- Threshold: ≥80 = APPROVED, 50-79 = MANUAL_REVIEW, <50 = REJECTED
"""

import os
import re
from typing import Any, Dict, List


class InstructionCompositeValidator:
    """Validates instruction documents against 10-point framework."""

    # 10-point framework sections (case-insensitive)
    REQUIRED_SECTIONS = [
        "DELIVERABLES",
        "SUCCESS_CRITERIA",
        "BOUNDARIES",
        "DEPENDENCIES",
        "MITIGATION",
        "TEST_PROCESS",
        "TEST_RESULTS_FORMAT",
        "TASK_CLASSIFICATION",
        "RETROSPECTIVE",
        "PERFORMANCE_REQUIREMENTS"
    ]

    def __init__(self):
        """Initialize instruction validator."""
        self.approve_threshold = 80  # ≥80 = APPROVED
        self.review_threshold = 50   # 50-79 = MANUAL_REVIEW

    def validate_instruction(
        self,
        instruction_file: str = None,
        instruction_content: str = None,
        worker_id: str = None
    ) -> Dict[str, Any]:
        """
        Validate instruction document against 10-point framework.

        Args:
            instruction_file: Path to instruction markdown file
            instruction_content: Raw markdown content (alternative to file)
            worker_id: Optional worker ID for tracking

        Returns:
            {
                "status": "APPROVED|REJECTED|MANUAL_REVIEW",
                "score": 85,
                "feedback": {...},
                "missing_sections": [],
                "quality_issues": []
            }
        """
        # Load instruction content
        if instruction_file and os.path.exists(instruction_file):
            with open(instruction_file, "r", encoding="utf-8") as f:
                content = f.read()
        elif instruction_content:
            content = instruction_content
        else:
            return {
                "status": "REJECTED",
                "score": 0,
                "feedback": {"error": "No instruction file or content provided"},
                "missing_sections": self.REQUIRED_SECTIONS,
                "quality_issues": ["No instruction content provided"]
            }

        # Validate framework completeness
        framework_result = self.validate_framework(content)

        # Score section quality
        section_scores = {}
        for section in self.REQUIRED_SECTIONS:
            section_scores[section] = self.score_section_quality(section, content)

        # Detect quality issues
        quality_issues = self.detect_issues(content)

        # Calculate overall score
        total_score = sum(section_scores.values())

        # Apply penalties for quality issues
        penalty = len(quality_issues) * 2
        total_score = max(0, total_score - penalty)

        # Determine status
        if total_score >= self.approve_threshold:
            status = "APPROVED"
        elif total_score >= self.review_threshold:
            status = "MANUAL_REVIEW"
        else:
            status = "REJECTED"

        return {
            "status": status,
            "score": total_score,
            "feedback": {
                "section_scores": section_scores,
                "framework_completeness": framework_result["completeness"],
                "total_sections": len(self.REQUIRED_SECTIONS),
                "found_sections": len(framework_result["found_sections"]),
                "missing_sections": len(framework_result["missing_sections"]),
            },
            "missing_sections": framework_result["missing_sections"],
            "quality_issues": quality_issues,
            "worker_id": worker_id
        }

    def validate_framework(self, content: str) -> Dict[str, Any]:
        """
        Check 10-point framework completeness.

        Args:
            content: Instruction document content

        Returns:
            {
                "completeness": 0.8,
                "found_sections": [...],
                "missing_sections": [...]
            }
        """
        content_upper = content.upper()

        found_sections = []
        missing_sections = []

        for section in self.REQUIRED_SECTIONS:
            # Look for section headers (case-insensitive)
            # Patterns: "## SECTION", "### SECTION", "**SECTION**", "SECTION —"
            patterns = [
                rf"##\s+\d*\.?\s*{section}",  # ## 1. SECTION or ## SECTION
                rf"###\s+\d*\.?\s*{section}",  # ### SECTION
                rf"\*\*{section}\*\*",         # **SECTION**
                rf"{section}\s*[—:-]",         # SECTION — or SECTION:
            ]

            found = False
            for pattern in patterns:
                if re.search(pattern, content_upper):
                    found = True
                    break

            if found:
                found_sections.append(section)
            else:
                missing_sections.append(section)

        completeness = len(found_sections) / len(self.REQUIRED_SECTIONS)

        return {
            "completeness": completeness,
            "found_sections": found_sections,
            "missing_sections": missing_sections
        }

    def score_section_quality(self, section_name: str, content: str) -> int:
        """
        Rate section quality (0-10 points).

        Criteria:
        - Section present: +5 points
        - Substantial content (>100 chars): +2 points
        - Structured (bullet points, code blocks): +2 points
        - Specific/measurable: +1 point

        Args:
            section_name: Section to evaluate
            content: Full instruction content

        Returns:
            Score 0-10
        """
        score = 0
        content_upper = content.upper()

        # Extract section content
        section_content = self._extract_section_content(section_name, content)

        if not section_content:
            return 0  # Section missing

        # Section present: +5 points
        score += 5

        # Substantial content (>100 chars): +2 points
        if len(section_content) > 100:
            score += 2

        # Structured (bullet points, code blocks, numbered lists): +2 points
        has_structure = (
            "```" in section_content or  # Code blocks
            "\n- " in section_content or  # Bullet points
            "\n* " in section_content or  # Bullet points
            re.search(r"\n\d+\.", section_content)  # Numbered lists
        )
        if has_structure:
            score += 2

        # Specific/measurable (numbers, percentages, concrete terms): +1 point
        has_specifics = (
            re.search(r"\d+%", section_content) or  # Percentages
            re.search(r"\d+\s*(hours?|days?|weeks?|minutes?)", section_content) or  # Time
            re.search(r"\d+\s*(files?|tests?|workers?|LOC)", section_content) or  # Counts
            "≥" in section_content or "≤" in section_content or  # Thresholds
            ">" in section_content or "<" in section_content
        )
        if has_specifics:
            score += 1

        return score

    def _extract_section_content(self, section_name: str, content: str) -> str:
        """
        Extract content of a specific section.

        Args:
            section_name: Section to extract
            content: Full instruction content

        Returns:
            Section content (empty string if not found)
        """
        content_lines = content.split("\n")

        # Find section start
        section_start = None
        for i, line in enumerate(content_lines):
            line_upper = line.upper()
            # Match section headers
            if (
                re.match(rf"##\s+\d*\.?\s*{section_name}", line_upper) or
                re.match(rf"###\s+\d*\.?\s*{section_name}", line_upper) or
                re.match(rf"\*\*{section_name}\*\*", line_upper) or
                re.match(rf"{section_name}\s*[—:-]", line_upper)
            ):
                section_start = i
                break

        if section_start is None:
            return ""

        # Find section end (next header or end of document)
        section_end = len(content_lines)
        for i in range(section_start + 1, len(content_lines)):
            line = content_lines[i]
            # Next section header (## or ###)
            if re.match(r"^##\s+", line) or re.match(r"^###\s+", line):
                section_end = i
                break

        # Extract section content
        section_lines = content_lines[section_start + 1:section_end]
        return "\n".join(section_lines)

    def detect_issues(self, content: str) -> List[str]:
        """
        Detect quality issues in instruction.

        Issues detected:
        - Empty or very short instruction (<100 chars)
        - Missing critical sections (DELIVERABLES, SUCCESS_CRITERIA)
        - Vague language ("something", "maybe", "probably")
        - No concrete examples or code blocks

        Args:
            content: Instruction content

        Returns:
            List of quality issue descriptions
        """
        issues = []

        # Empty or very short
        if len(content) < 100:
            issues.append("Instruction too short (<100 characters)")

        # Missing critical sections
        content_upper = content.upper()
        if "DELIVERABLES" not in content_upper:
            issues.append("Missing critical section: DELIVERABLES")
        if "SUCCESS_CRITERIA" not in content_upper:
            issues.append("Missing critical section: SUCCESS_CRITERIA")

        # Vague language
        vague_terms = ["something", "maybe", "probably", "might", "could", "should probably"]
        found_vague = [term for term in vague_terms if term in content.lower()]
        if found_vague:
            issues.append(f"Vague language detected: {', '.join(found_vague)}")

        # No concrete examples
        has_examples = (
            "```" in content or  # Code blocks
            "Example:" in content or
            "For example" in content.lower()
        )
        if not has_examples and len(content) > 500:
            issues.append("No concrete examples or code blocks (recommended for long instructions)")

        # No bullet points or structure (for medium-long instructions)
        has_structure = (
            "\n- " in content or
            "\n* " in content or
            re.search(r"\n\d+\.", content)
        )
        if not has_structure and len(content) > 300:
            issues.append("No bullet points or numbered lists (recommended for clarity)")

        return issues
