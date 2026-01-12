#!/usr/bin/env python3
"""Advisory consensus verifier for approval risk assessment.

Goal:
- Record multiple independent "votes" on risk.
- Keep enforcement in the Execution Gateway; consensus is advisory but logged.

Design:
- Provides N evaluators (some may be unavailable).
- Produces a consensus risk_level and a structured dissent log.
- Never requires external network access; optionally uses local Ollama if configured.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


RISK_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


@dataclass(frozen=True)
class Vote:
    source: str
    risk_level: str
    reason: str
    available: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "risk_level": self.risk_level,
            "reason": self.reason,
            "available": self.available,
        }


def _max_risk(levels: List[str]) -> str:
    if not levels:
        return "LOW"
    return max(levels, key=lambda x: RISK_ORDER.get(x, 0))


def _heuristic_vote(instruction: str, task_name: str, deployment_env: str) -> Vote:
    # Simple conservative keyword classifier (no LLM). Aligns with existing assess_risk behavior.
    txt = f"{task_name}\n{instruction}\n{deployment_env}".lower()
    env = (deployment_env or "").lower()

    if env == "prd":
        return Vote("heuristic", "HIGH", "DEPLOYMENT_ENV=prd")

    high_terms = [
        "prod",
        "production",
        "drop ",
        "truncate ",
        "delete ",
        "rm -",
        "wipe",
        "format ",
        "rotate key",
        "secret",
        "token",
        "password",
        "docker",
        "compose",
        "kubectl",
        "deploy",
        "migration",
    ]
    if any(t in txt for t in high_terms):
        return Vote("heuristic", "HIGH", "keyword match")

    med_terms = ["restart", "update", "install", "config", "env", "schema", "database"]
    if any(t in txt for t in med_terms):
        return Vote("heuristic", "MEDIUM", "keyword match")

    return Vote("heuristic", "LOW", "no risky keywords")


def _strict_structural_vote(instruction: str, task_name: str, deployment_env: str) -> Vote:
    # More strict than heuristic: if instruction lacks explicit boundaries/testing, bump risk.
    txt = instruction or ""
    missing = []
    for field in ["DELIVERABLES", "SUCCESS_CRITERIA", "BOUNDARIES", "TEST_PROCESS"]:
        if re.search(rf"(?im)^\s*{re.escape(field)}\s*:\s*", txt) is None:
            missing.append(field)
    if missing:
        return Vote("structure", "MEDIUM", f"missing required fields: {', '.join(missing)}")
    return Vote("structure", "LOW", "required instruction fields present")


def _ollama_vote(instruction: str, task_name: str, deployment_env: str) -> Vote:
    """Optional local Ollama vote.

    Controlled by env:
    - WINGMAN_CONSENSUS_OLLAMA_ENABLED=1
    - OLLAMA_HOST/OLLAMA_PORT or OLLAMA_URL
    """
    if (os.getenv("WINGMAN_CONSENSUS_OLLAMA_ENABLED") or "").strip() != "1":
        return Vote("ollama", "LOW", "disabled", available=False)

    try:
        import requests

        base = (os.getenv("OLLAMA_URL") or "").strip()
        if not base:
            host = (os.getenv("OLLAMA_HOST") or "ollama").strip()
            port = (os.getenv("OLLAMA_PORT") or "11434").strip()
            base = f"http://{host}:{port}"

        prompt = (
            "You are a security risk classifier for infrastructure operations.\n"
            "Return ONLY valid JSON with keys risk_level (LOW|MEDIUM|HIGH) and reason.\n\n"
            f"deployment_env: {deployment_env}\n"
            f"task_name: {task_name}\n"
            f"instruction:\n{instruction}\n"
        )

        # Prefer a lightweight model name if provided; default to mistral.
        model = (os.getenv("WINGMAN_CONSENSUS_OLLAMA_MODEL") or "mistral").strip()
        r = requests.post(
            base.rstrip("/") + "/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=15,
        )
        if not r.ok:
            return Vote("ollama", "LOW", f"unavailable (http {r.status_code})", available=False)

        data = r.json() or {}
        txt = (data.get("response") or "").strip()
        obj = json.loads(txt)
        lvl = str(obj.get("risk_level") or "LOW").upper()
        if lvl not in ("LOW", "MEDIUM", "HIGH"):
            lvl = "LOW"
        reason = str(obj.get("reason") or "no reason")
        return Vote("ollama", lvl, reason, available=True)

    except Exception as e:
        return Vote("ollama", "LOW", f"unavailable ({type(e).__name__})", available=False)


def assess_risk_consensus(instruction: str, task_name: str = "", deployment_env: str = "") -> Dict[str, Any]:
    """Return consensus risk + dissent details.

    Output:
      {
        risk_level: LOW|MEDIUM|HIGH,
        risk_reason: str,
        consensus: {
          votes: [...],
          dissent: [...],
          decided_at: iso,
        }
      }
    """
    instruction = (instruction or "").strip()

    votes: List[Vote] = [
        _heuristic_vote(instruction, task_name, deployment_env),
        _strict_structural_vote(instruction, task_name, deployment_env),
        _ollama_vote(instruction, task_name, deployment_env),
    ]

    available_votes = [v for v in votes if v.available]
    levels = [v.risk_level for v in available_votes]

    # Consensus rule (conservative): take max risk among available sources.
    consensus_level = _max_risk(levels)

    dissent = [v for v in available_votes if v.risk_level != consensus_level]

    consensus_blob = {
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "votes": [v.to_dict() for v in votes],
        "dissent": [v.to_dict() for v in dissent],
        "rule": "max_risk_of_available_sources",
    }

    # Human-readable reason: include top vote(s) and note dissent.
    top_sources = [v for v in available_votes if v.risk_level == consensus_level]
    top_reason = "; ".join([f"{v.source}: {v.reason}" for v in top_sources[:3]])
    dissent_note = f" dissent={len(dissent)}" if dissent else ""

    return {
        "risk_level": consensus_level,
        "risk_reason": f"CONSENSUS({consensus_level}) {top_reason}{dissent_note}",
        "consensus": consensus_blob,
    }
