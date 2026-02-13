"""
Wingman Semantic Analyzer - LLM-assisted intent and risk analysis.

Sends instruction to Ollama via intel-system LLM Processor (localhost:18027).
Asks: What does this instruction do? What is the risk level? Could it cause harm?
Fallback: heuristic-only score when Ollama unavailable (graceful degradation).

Output: {score: int, risk_level: str, intent_summary: str, concerns: list, reasoning: str}
"""

import json
import os
import re
from typing import Any, Dict, List

try:
    import requests
except ImportError:
    requests = None  # optional: fallback only when LLM not used


# Default: intel-system LLM Processor (plan: localhost:18027)
DEFAULT_LLM_URL = os.getenv("INTEL_LLM_PROCESSOR", "http://localhost:18027")
DEFAULT_MODEL = os.getenv("WINGMAN_SEMANTIC_LLM_MODEL", "llama3.1:8b")

PROMPT_TEMPLATE = """You are a security and intent analyst for infrastructure instructions.

Analyze this instruction and respond with ONLY valid JSON (no markdown, no extra text) with these keys:
- risk_level: one of LOW, MEDIUM, HIGH, CRITICAL
- score: integer 0-100 (100 = safe, 0 = very dangerous)
- intent_summary: one sentence describing what the instruction does
- concerns: list of strings (potential harms or risks, empty if none)
- reasoning: one sentence explaining the risk_level

Instruction:
---
{instruction}
---
JSON:"""


class SemanticAnalyzer:
    """LLM-assisted analysis of what an instruction actually does; heuristic fallback when LLM unavailable."""

    def __init__(self, llm_url: str = "", model: str = ""):
        self.llm_url = (llm_url or DEFAULT_LLM_URL).rstrip("/")
        self.model = model or DEFAULT_MODEL

    def analyze(self, instruction_text: str) -> Dict[str, Any]:
        """Analyze instruction semantics. Returns score, risk_level, intent_summary, concerns, reasoning."""
        if not instruction_text or not instruction_text.strip():
            return self._fallback(instruction_text or "", "Empty instruction.")

        instruction_text = instruction_text.strip()
        if len(instruction_text) > 10000:
            return self._fallback(instruction_text[:1000], "Instruction too long; truncated for analysis.")

        try:
            return self._call_llm(instruction_text)
        except Exception:
            return self._fallback(instruction_text, "LLM unavailable or error.")

    def _call_llm(self, instruction_text: str) -> Dict[str, Any]:
        """Call intel-system LLM Processor. Raises on failure."""
        if requests is None:
            raise RuntimeError("requests not installed; cannot call LLM")
        prompt = PROMPT_TEMPLATE.format(instruction=instruction_text)
        # intel-system often exposes /generate or /api/generate
        url = f"{self.llm_url}/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json() or {}
        raw = (data.get("response") or data.get("text") or "").strip()
        return self._parse_llm_response(raw, instruction_text)

    def _parse_llm_response(self, raw: str, instruction_text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response; fallback on parse failure."""
        # Try to find JSON block
        match = re.search(r"\{[^{}]*\"risk_level\"[^{}]*\}", raw, re.DOTALL)
        if not match:
            match = re.search(r"\{[^{}]+\}", raw)
        if match:
            try:
                obj = json.loads(match.group(0))
                score = int(obj.get("score", 50))
                score = max(0, min(100, score))
                risk = str(obj.get("risk_level", "MEDIUM")).upper()
                if risk not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
                    risk = "MEDIUM"
                return {
                    "score": score,
                    "risk_level": risk,
                    "intent_summary": str(obj.get("intent_summary", "Unknown."))[:500],
                    "concerns": obj.get("concerns") if isinstance(obj.get("concerns"), list) else [],
                    "reasoning": str(obj.get("reasoning", ""))[:500],
                }
            except (json.JSONDecodeError, TypeError):
                pass
        return self._fallback(instruction_text, "Could not parse LLM response.")

    def _fallback(self, instruction_text: str, reason: str) -> Dict[str, Any]:
        """Heuristic-only result when LLM is unavailable."""
        text_lower = (instruction_text or "").lower()
        score = 70
        risk_level = "LOW"

        # Avoid flagging negated context (e.g. "No PRD changes")
        high_terms = ["rm -rf", "drop table", "truncate", "wipe", "docker prune", "docker rm", "delete all"]
        if any(t in text_lower for t in high_terms):
            score = 30
            risk_level = "HIGH"
        elif " prd " in text_lower or " prd." in text_lower or text_lower.strip().startswith("prd") or "production" in text_lower:
            if "no prd" not in text_lower and "not prd" not in text_lower and "no production" not in text_lower:
                score = 30
                risk_level = "HIGH"
        if risk_level == "LOW":
            med_terms = ["restart", "docker stop", "docker kill", "migrate", "deploy"]
            if any(t in text_lower for t in med_terms):
                score = 55
                risk_level = "MEDIUM"

        return {
            "score": score,
            "risk_level": risk_level,
            "intent_summary": "Fallback: heuristic analysis only.",
            "concerns": [] if risk_level == "LOW" else ["Heuristic risk indicators present."],
            "reasoning": reason + " Using heuristic fallback.",
        }
