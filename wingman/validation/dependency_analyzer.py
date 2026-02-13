"""
Wingman Dependency Analyzer - Service/resource detection and blast radius.

Identifies what services/resources an instruction touches via pattern matching:
- Docker, database, network, filesystem references
- Classifies: container, database, network, filesystem, external_api
- Blast radius: LOW (single file), MEDIUM (single service), HIGH (multiple services), CRITICAL (data/infra)

No external dependencies. Pure regex-based.
"""

import re
from typing import Any, Dict, List, Set, Tuple


# Patterns: (category, regex, description)
CONTAINER_PATTERNS = [
    ("container", re.compile(r"\bdocker\s+(stop|start|restart|rm|kill|compose)\b", re.IGNORECASE), "Docker container/compose"),
    ("container", re.compile(r"\b(kubectl|helm)\s+", re.IGNORECASE), "Kubernetes/Helm"),
    ("container", re.compile(r"\b(podman|containerd)\b", re.IGNORECASE), "Container runtime"),
]
DATABASE_PATTERNS = [
    ("database", re.compile(r"\b(postgres|postgresql|mysql|redis|mongodb)\b", re.IGNORECASE), "Database service"),
    ("database", re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE), "Database DDL"),
    ("database", re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE), "Table truncate"),
    ("database", re.compile(r"\b(migrate|migration|schema)\b", re.IGNORECASE), "Schema/migration"),
]
NETWORK_PATTERNS = [
    ("network", re.compile(r"\b(curl|wget|http|https|api\.)\b", re.IGNORECASE), "HTTP/API"),
    ("network", re.compile(r"\b(port|listen|bind|0\.0\.0\.0)\b", re.IGNORECASE), "Network binding"),
    ("network", re.compile(r"\b(firewall|iptables|ufw)\b", re.IGNORECASE), "Firewall"),
]
FILESYSTEM_PATTERNS = [
    ("filesystem", re.compile(r"\b(rm\s+-|delete\s+file|unlink|remove\s+file)\b", re.IGNORECASE), "File deletion"),
    ("filesystem", re.compile(r"\b(mkdir|chmod|chown|/dev/)\b", re.IGNORECASE), "Filesystem operation"),
    ("filesystem", re.compile(r"\b(create\s+file|write\s+to\s+file|\.py|\.json|\.yaml)\b", re.IGNORECASE), "File create/write"),
]
EXTERNAL_API_PATTERNS = [
    ("external_api", re.compile(r"\b(openai|ollama|telegram|slack|webhook)\b", re.IGNORECASE), "External API"),
    ("external_api", re.compile(r"\b(api\s+key|webhook|callback)\b", re.IGNORECASE), "API integration"),
]


class DependencyAnalyzer:
    """Identifies dependencies and computes blast radius from instruction text."""

    def analyze(self, instruction_text: str) -> Dict[str, Any]:
        """Analyze instruction for dependencies and blast radius.

        Args:
            instruction_text: The instruction text to analyze.

        Returns:
            dict with keys: dependencies, blast_radius, affected_services, risk_level.
        """
        if not instruction_text or not instruction_text.strip():
            return {
                "dependencies": [],
                "blast_radius": "LOW",
                "affected_services": [],
                "risk_level": "LOW",
            }

        dependencies: List[Dict[str, str]] = []
        seen: Set[Tuple[str, str]] = set()

        for category, pattern, desc in (
            CONTAINER_PATTERNS + DATABASE_PATTERNS + NETWORK_PATTERNS +
            FILESYSTEM_PATTERNS + EXTERNAL_API_PATTERNS
        ):
            for m in pattern.finditer(instruction_text):
                key = (category, desc)
                if key not in seen:
                    seen.add(key)
                    dependencies.append({"type": category, "description": desc})

        affected_services = self._extract_affected_services(instruction_text, dependencies)
        blast_radius = self._compute_blast_radius(dependencies, affected_services, instruction_text)
        risk_level = self._risk_from_blast_radius(blast_radius)

        return {
            "dependencies": dependencies,
            "blast_radius": blast_radius,
            "affected_services": affected_services,
            "risk_level": risk_level,
        }

    def _extract_affected_services(self, text: str, dependencies: List[Dict[str, str]]) -> List[str]:
        """Extract service names mentioned (e.g. postgres, wingman-api)."""
        services: List[str] = []
        # Known service names (from compose / common usage)
        service_pattern = re.compile(
            r"\b(wingman-api|execution-gateway|telegram-bot|postgres|redis|ollama|mem0|intel-system)\b",
            re.IGNORECASE,
        )
        for m in service_pattern.finditer(text):
            s = m.group(1).lower()
            if s not in services:
                services.append(s)
        # Also add generic "postgres" if database ops mentioned
        if any(d["type"] == "database" for d in dependencies) and "postgres" not in [s.lower() for s in services]:
            if re.search(r"\bpostgres\b", text, re.IGNORECASE):
                services.append("postgres")
        return services

    def _compute_blast_radius(self, dependencies: List[Dict[str, str]], affected_services: List[str], instruction_text: str = "") -> str:
        """Compute blast radius from dependency types and affected services."""
        types = {d["type"] for d in dependencies}
        text_lower = instruction_text.lower()

        # CRITICAL: data/infra destruction (DROP/TRUNCATE)
        if "database" in types and ("drop" in text_lower or "truncate" in text_lower):
            return "CRITICAL"
        if len(types) >= 3 and "container" in types:
            return "CRITICAL"

        # HIGH: multiple services or container stop/rm + database
        if len(affected_services) >= 2:
            return "HIGH"
        if "container" in types and ("database" in types or len(affected_services) >= 1):
            return "HIGH"
        if "container" in types and any("rm" in d.get("description", "") or "stop" in d.get("description", "") for d in dependencies):
            return "HIGH"

        # MEDIUM: single service or network
        if "container" in types or "database" in types or len(affected_services) >= 1:
            return "MEDIUM"
        if "network" in types or "external_api" in types:
            return "MEDIUM"

        # LOW: filesystem only or nothing
        if "filesystem" in types and len(types) == 1:
            return "LOW"
        return "LOW"

    def _risk_from_blast_radius(self, blast_radius: str) -> str:
        """Map blast radius to risk level."""
        return {"LOW": "LOW", "MEDIUM": "MEDIUM", "HIGH": "HIGH", "CRITICAL": "CRITICAL"}.get(blast_radius, "LOW")
