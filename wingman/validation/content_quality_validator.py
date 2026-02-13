"""
Wingman Content Quality Validator - Per-section quality scoring.

Scores each of the 10-point framework sections for quality (not just presence).
"DELIVERABLES: TBD" scores 1/10.  A detailed deliverable with file paths and
method names scores 8-10/10.

Aggregate score: 0-100.
Thresholds: auto-reject < 60, manual review 60-89, auto-approve >= 90.

No external dependencies. Pure text analysis.
"""

import re
from typing import Any, Dict, List, Tuple


REQUIRED_SECTIONS = [
    "DELIVERABLES",
    "SUCCESS_CRITERIA",
    "BOUNDARIES",
    "DEPENDENCIES",
    "MITIGATION",
    "TEST_PROCESS",
    "TEST_RESULTS_FORMAT",
    "RESOURCE_REQUIREMENTS",
    "RISK_ASSESSMENT",
    "QUALITY_METRICS",
]

# Words/patterns that indicate vagueness (score penalty)
VAGUE_WORDS = {
    "tbd", "todo", "stuff", "things", "etc", "whatever",
    "something", "somehow", "later", "eventually", "n/a",
}

# Words/patterns that indicate specificity (score bonus)
SPECIFICITY_INDICATORS = [
    re.compile(r"`[^`]+`"),                        # backtick-quoted paths/code
    re.compile(r"\b\w+\.\w+\b"),                   # file.ext or module.func
    re.compile(r"\b(create|implement|add|update|remove|test|run|deploy)\b", re.IGNORECASE),  # action verbs
    re.compile(r"\b\d+(\.\d+)?(%|ms|s|min|MB|GB)\b"),  # quantified metrics
    re.compile(r"(http|https)://\S+"),             # URLs
    re.compile(r"\b[A-Z_]{2,}\b"),                 # CONSTANTS or ENV_VARS
]


class ContentQualityValidator:
    """Scores each 10-point framework section for quality, not just presence."""

    def validate(self, instruction_text: str) -> Dict[str, Any]:
        """Score instruction quality across all 10 framework sections.

        Args:
            instruction_text: The instruction text to validate.

        Returns:
            dict with keys: score, section_scores, weakest_sections,
            recommendation, reasoning.
        """
        if not instruction_text or not instruction_text.strip():
            return {
                "score": 0,
                "section_scores": {s: 0 for s in REQUIRED_SECTIONS},
                "weakest_sections": REQUIRED_SECTIONS[:],
                "recommendation": "REJECT",
                "reasoning": "Empty instruction text.",
            }

        sections = self._extract_sections(instruction_text)
        section_scores: Dict[str, int] = {}

        for section_name in REQUIRED_SECTIONS:
            content = sections.get(section_name, "")
            section_scores[section_name] = self._score_section(section_name, content)

        total_score = sum(section_scores.values())  # 0-100 (10 sections * max 10)
        weakest = self._find_weakest(section_scores)
        recommendation = self._recommend(total_score)
        reasoning = self._build_reasoning(section_scores, total_score, recommendation)

        return {
            "score": total_score,
            "section_scores": section_scores,
            "weakest_sections": weakest,
            "recommendation": recommendation,
            "reasoning": reasoning,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract content for each section from the instruction text."""
        sections: Dict[str, str] = {}
        upper_text = text.upper()

        for i, section in enumerate(REQUIRED_SECTIONS):
            # Find section header (case-insensitive)
            pattern = re.compile(
                rf"(?:^|\n)\s*(?:##?\s*\d*\.?\s*)?{re.escape(section)}\s*:?\s*\n?",
                re.IGNORECASE | re.MULTILINE,
            )
            match = pattern.search(text)
            if not match:
                sections[section] = ""
                continue

            start = match.end()

            # Find the next section header or end of text
            next_start = len(text)
            for other_section in REQUIRED_SECTIONS:
                if other_section == section:
                    continue
                other_pattern = re.compile(
                    rf"(?:^|\n)\s*(?:##?\s*\d*\.?\s*)?{re.escape(other_section)}\s*:?\s*\n?",
                    re.IGNORECASE | re.MULTILINE,
                )
                other_match = other_pattern.search(text, start)
                if other_match and other_match.start() < next_start:
                    next_start = other_match.start()

            content = text[start:next_start].strip()
            sections[section] = content

        return sections

    def _score_section(self, section_name: str, content: str) -> int:
        """Score a single section 0-10 based on quality indicators."""
        if not content:
            return 0

        score = 0.0

        # 1. Length score (0-3 points)
        word_count = len(content.split())
        if word_count >= 20:
            score += 3.0
        elif word_count >= 10:
            score += 2.0
        elif word_count >= 3:
            score += 1.0

        # 2. Specificity score (0-3 points)
        specificity_hits = 0
        for pattern in SPECIFICITY_INDICATORS:
            if pattern.search(content):
                specificity_hits += 1
        score += min(3.0, specificity_hits)

        # 3. Structure score (0-3 points) -- bullet points, numbered lists, substantive lists
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        bullet_lines = sum(1 for l in lines if l.startswith(("-", "*", "+")))
        numbered_lines = sum(1 for l in lines if re.match(r"^\d+[\.\)]\s", l))
        if bullet_lines >= 2 or numbered_lines >= 2:
            score += 2.0
            # Bonus for substantive list (multiple bullets + enough words)
            if word_count >= 5:
                score += 1.0
        elif bullet_lines >= 1 or numbered_lines >= 1:
            score += 1.0
            if word_count >= 3:
                score += 0.5  # Short but structured content (medium-quality instructions)

        # 4. Vagueness penalty (0 to -2 points)
        lower_content = content.lower()
        vague_hits = sum(1 for w in VAGUE_WORDS if w in lower_content)
        score -= min(2.0, vague_hits)

        # 5. Section-specific bonus (0-2 points)
        score += self._section_specific_bonus(section_name, content)

        return max(0, min(10, int(round(score))))

    def _section_specific_bonus(self, section_name: str, content: str) -> float:
        """Award bonus points for section-appropriate content."""
        bonus = 0.0
        lower = content.lower()

        if section_name == "DELIVERABLES":
            # Bonus for file paths or module names
            if re.search(r"`[^`]*\.(py|js|ts|yaml|yml|json|sh)`", content):
                bonus += 1.0
            if re.search(r"\b(create|implement|write|build)\b", lower):
                bonus += 1.0

        elif section_name == "SUCCESS_CRITERIA":
            # Bonus for measurable criteria
            if re.search(r"\b\d+\s*%", content) or re.search(r"\b(pass|coverage|complete)\b", lower):
                bonus += 1.0
            if re.search(r"\b(all|every|100%|zero)\b", lower):
                bonus += 1.0

        elif section_name == "BOUNDARIES":
            # Bonus for explicit environment mentions
            if re.search(r"\b(test|prd|prod|staging)\b", lower):
                bonus += 1.0
            if re.search(r"\b(no |not |never |only )\b", lower):
                bonus += 1.0

        elif section_name == "TEST_PROCESS":
            # Bonus for actual test commands
            if re.search(r"\b(pytest|python|curl|bash|run)\b", lower):
                bonus += 1.0
            if re.search(r"`[^`]+`", content):
                bonus += 1.0

        elif section_name == "MITIGATION":
            # Bonus for concrete rollback/fallback plans
            if re.search(r"\b(rollback|fallback|revert|restore|if .* fail)\b", lower):
                bonus += 1.0
            if re.search(r"\b(before|after|backup)\b", lower):
                bonus += 1.0

        elif section_name == "RISK_ASSESSMENT":
            # Bonus for explicit risk level
            if re.search(r"\b(low|medium|high|critical)\b", lower):
                bonus += 1.0
            if re.search(r"\b(because|since|due to|reason)\b", lower):
                bonus += 1.0

        elif section_name == "QUALITY_METRICS":
            # Bonus for quantified metrics
            if re.search(r"\b\d+\s*%", content):
                bonus += 1.0
            if re.search(r"\b(coverage|latency|throughput|accuracy)\b", lower):
                bonus += 1.0

        elif section_name == "DEPENDENCIES":
            # Bonus for named resources (Ollama, API, Docker, etc.)
            if re.search(r"\b(ollama|api|docker|test|postgres|redis)\b", lower):
                bonus += 1.0
            if re.search(r"\b(available|running|accessible)\b", lower):
                bonus += 1.0

        elif section_name == "TEST_RESULTS_FORMAT":
            # Bonus for concrete format (pytest, coverage, json)
            if re.search(r"\b(pytest|coverage|pass|fail|json)\b", lower):
                bonus += 1.0
            if re.search(r"\b\d+\s*%", content):
                bonus += 1.0

        elif section_name == "RESOURCE_REQUIREMENTS":
            # Bonus for specific resources
            if re.search(r"\b(local|test|api|instance)\b", lower):
                bonus += 1.0
            if re.search(r"\b(accessible|available)\b", lower):
                bonus += 1.0

        return min(2.0, bonus)

    def _find_weakest(self, section_scores: Dict[str, int], threshold: int = 4) -> List[str]:
        """Return section names scoring below threshold."""
        return [name for name, score in section_scores.items() if score < threshold]

    def _recommend(self, total_score: int) -> str:
        """Determine recommendation based on total score."""
        if total_score < 60:
            return "REJECT"
        if total_score >= 90:
            return "APPROVE"
        return "MANUAL_REVIEW"

    def _build_reasoning(
        self,
        section_scores: Dict[str, int],
        total_score: int,
        recommendation: str,
    ) -> str:
        parts: List[str] = [f"Total quality score: {total_score}/100."]

        weak = [n for n, s in section_scores.items() if s < 4]
        strong = [n for n, s in section_scores.items() if s >= 8]

        if strong:
            parts.append(f"Strong sections: {', '.join(strong)}.")
        if weak:
            parts.append(f"Weak sections: {', '.join(weak)}.")

        parts.append(f"Recommendation: {recommendation}.")
        return " ".join(parts)
