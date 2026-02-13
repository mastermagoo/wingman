"""
Wingman Code Scanner - Pattern-based dangerous command and secret detection.

Scans instruction text for:
- 30 dangerous command/operation patterns (rm -rf, DROP TABLE, docker rm, etc.)
- 15 secret/credential patterns (API keys, passwords, tokens, AWS keys, etc.)

No external dependencies. Pure regex-based.
"""

import re
from typing import Any, Dict, List, Tuple


# --- Dangerous command patterns ---
# Each tuple: (pattern_name, compiled_regex, severity, description)
DANGEROUS_PATTERNS: List[Tuple[str, re.Pattern, str, str]] = [
    # Filesystem destruction
    ("rm_rf", re.compile(r"\brm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+|--force\s+|-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force)", re.IGNORECASE), "CRITICAL", "Recursive forced file deletion"),
    ("rm_wildcard", re.compile(r"\brm\s+.*\*", re.IGNORECASE), "HIGH", "Wildcard file deletion"),
    ("shred", re.compile(r"\bshred\b", re.IGNORECASE), "CRITICAL", "Secure file destruction"),
    ("mkfs", re.compile(r"\bmkfs\b", re.IGNORECASE), "CRITICAL", "Filesystem formatting"),
    ("dd_if", re.compile(r"\bdd\s+if=", re.IGNORECASE), "HIGH", "Raw disk write"),
    ("format_disk", re.compile(r"\bformat\s+(c:|d:|/dev/)", re.IGNORECASE), "CRITICAL", "Disk formatting"),
    # Database destruction
    ("drop_table", re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE), "CRITICAL", "Database object deletion"),
    ("truncate_table", re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE), "HIGH", "Table data wipe"),
    ("delete_all", re.compile(r"\bDELETE\s+FROM\s+\w+\s*(;|\s*$)", re.IGNORECASE | re.MULTILINE), "HIGH", "Unfiltered DELETE (no WHERE)"),
    ("alter_drop", re.compile(r"\bALTER\s+TABLE\s+\w+\s+DROP\b", re.IGNORECASE), "HIGH", "Column/constraint removal"),
    # Docker/container operations
    ("docker_rm", re.compile(r"\bdocker\s+(rm|remove)\b", re.IGNORECASE), "HIGH", "Container removal"),
    ("docker_rmi", re.compile(r"\bdocker\s+rmi\b", re.IGNORECASE), "MEDIUM", "Image removal"),
    ("docker_prune", re.compile(r"\bdocker\s+(system\s+)?prune\b", re.IGNORECASE), "CRITICAL", "Docker system prune"),
    ("docker_stop", re.compile(r"\bdocker\s+(stop|kill)\b", re.IGNORECASE), "MEDIUM", "Container stop/kill"),
    ("docker_compose_down", re.compile(r"\bdocker\s+compose\s+down\b", re.IGNORECASE), "HIGH", "Stack teardown"),
    ("docker_volume_rm", re.compile(r"\bdocker\s+volume\s+rm\b", re.IGNORECASE), "CRITICAL", "Volume deletion (data loss)"),
    # System/privilege escalation
    ("sudo", re.compile(r"\bsudo\b", re.IGNORECASE), "HIGH", "Privilege escalation"),
    ("chmod_777", re.compile(r"\bchmod\s+777\b", re.IGNORECASE), "HIGH", "World-writable permissions"),
    ("chown_root", re.compile(r"\bchown\s+root\b", re.IGNORECASE), "MEDIUM", "Root ownership change"),
    ("systemctl_stop", re.compile(r"\bsystemctl\s+(stop|disable|mask)\b", re.IGNORECASE), "HIGH", "Service disruption"),
    ("iptables", re.compile(r"\biptables\s+.*(-F|-X|FLUSH|DELETE)\b", re.IGNORECASE), "CRITICAL", "Firewall rule deletion"),
    # Network/security
    ("curl_pipe_sh", re.compile(r"\bcurl\b.*\|\s*(ba)?sh\b", re.IGNORECASE), "CRITICAL", "Remote code execution"),
    ("wget_pipe_sh", re.compile(r"\bwget\b.*\|\s*(ba)?sh\b", re.IGNORECASE), "CRITICAL", "Remote code execution"),
    ("ssh_force", re.compile(r"\bssh\b.*-o\s*StrictHostKeyChecking=no", re.IGNORECASE), "HIGH", "SSH without host verification"),
    # Kubernetes
    ("kubectl_delete", re.compile(r"\bkubectl\s+delete\b", re.IGNORECASE), "HIGH", "Kubernetes resource deletion"),
    ("helm_uninstall", re.compile(r"\bhelm\s+(uninstall|delete)\b", re.IGNORECASE), "HIGH", "Helm release removal"),
    # Force flags
    ("force_flag", re.compile(r"\b--force\b", re.IGNORECASE), "MEDIUM", "Forced operation (bypasses safety)"),
    ("no_verify", re.compile(r"\b--no-verify\b", re.IGNORECASE), "MEDIUM", "Verification bypass"),
    # Data manipulation
    ("wipe", re.compile(r"\bwipe\b", re.IGNORECASE), "HIGH", "Data wipe operation"),
    ("purge", re.compile(r"\bpurge\s+(all|--all|-a)\b", re.IGNORECASE), "HIGH", "Purge all data"),
]

# --- Secret/credential patterns ---
# Each tuple: (pattern_name, compiled_regex, description)
SECRET_PATTERNS: List[Tuple[str, re.Pattern, str]] = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
    ("aws_secret_key", re.compile(r"(?i)(aws_secret_access_key|aws_secret)\s*[=:]\s*\S+"), "AWS Secret Key"),
    ("generic_api_key", re.compile(r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"]?\S{8,}"), "Generic API key"),
    ("generic_secret", re.compile(r"(?i)(client[_-]?secret|app[_-]?secret)\s*[=:]\s*['\"]?\S{8,}"), "Client/app secret"),
    ("generic_password", re.compile(r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"]?\S{4,}"), "Hardcoded password"),
    ("generic_token", re.compile(r"(?i)(auth[_-]?token|access[_-]?token|bearer)\s*[=:]\s*['\"]?\S{8,}"), "Auth/access token"),
    ("private_key", re.compile(r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----"), "Private key"),
    ("github_token", re.compile(r"gh[ps]_[A-Za-z0-9_]{36,}"), "GitHub personal access token"),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{20,}"), "OpenAI API key"),
    ("slack_token", re.compile(r"xox[bpoas]-[0-9]{10,}"), "Slack token"),
    ("telegram_token", re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"), "Telegram bot token"),
    ("jwt_token", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}"), "JWT token"),
    ("connection_string", re.compile(r"(?i)(postgres|mysql|mongodb|redis)://\S+:\S+@"), "Database connection string with credentials"),
    ("env_secret_assign", re.compile(r"(?i)(SECRET|TOKEN|KEY|PASSWORD|CREDENTIAL)\s*=\s*['\"]?[A-Za-z0-9+/=_-]{16,}"), "Environment variable with secret value"),
    ("base64_secret", re.compile(r"(?i)(secret|password|key)\s*[=:]\s*['\"]?[A-Za-z0-9+/]{40,}={0,2}['\"]?"), "Base64-encoded secret"),
]


class CodeScanner:
    """Scans instruction text for dangerous patterns and embedded secrets."""

    def scan(self, instruction_text: str) -> Dict[str, Any]:
        """Scan instruction text and return risk assessment.

        Args:
            instruction_text: The instruction text to scan.

        Returns:
            dict with keys: score, risk_level, dangerous_patterns,
            secrets_found, reasoning.
        """
        if not instruction_text or not instruction_text.strip():
            return {
                "score": 100,
                "risk_level": "LOW",
                "dangerous_patterns": [],
                "secrets_found": [],
                "reasoning": "Empty instruction text.",
            }

        dangerous = self._scan_dangerous(instruction_text)
        secrets = self._scan_secrets(instruction_text)

        score = self._calculate_score(dangerous, secrets)
        risk_level = self._determine_risk(dangerous, secrets)
        reasoning = self._build_reasoning(dangerous, secrets, score)

        return {
            "score": score,
            "risk_level": risk_level,
            "dangerous_patterns": dangerous,
            "secrets_found": secrets,
            "reasoning": reasoning,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _scan_dangerous(self, text: str) -> List[Dict[str, str]]:
        found: List[Dict[str, str]] = []
        for name, pattern, severity, description in DANGEROUS_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                found.append({
                    "pattern": name,
                    "severity": severity,
                    "description": description,
                    "match_count": len(matches),
                })
        return found

    def _scan_secrets(self, text: str) -> List[Dict[str, str]]:
        found: List[Dict[str, str]] = []
        for name, pattern, description in SECRET_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                found.append({
                    "pattern": name,
                    "description": description,
                    "match_count": len(matches),
                })
        return found

    def _calculate_score(
        self,
        dangerous: List[Dict[str, str]],
        secrets: List[Dict[str, str]],
    ) -> int:
        """Calculate a 0-100 score. 100 = safe, 0 = extremely dangerous."""
        score = 100

        severity_penalties = {
            "CRITICAL": 30,
            "HIGH": 20,
            "MEDIUM": 10,
        }

        for d in dangerous:
            penalty = severity_penalties.get(d["severity"], 5)
            score -= penalty

        # Secrets are always a hard penalty
        for _s in secrets:
            score -= 25

        return max(0, score)

    def _determine_risk(
        self,
        dangerous: List[Dict[str, str]],
        secrets: List[Dict[str, str]],
    ) -> str:
        """Determine overall risk level from findings."""
        if secrets:
            return "CRITICAL"

        severities = [d["severity"] for d in dangerous]
        if "CRITICAL" in severities:
            return "CRITICAL"
        if "HIGH" in severities:
            return "HIGH"
        if "MEDIUM" in severities:
            return "MEDIUM"
        return "LOW"

    def _build_reasoning(
        self,
        dangerous: List[Dict[str, str]],
        secrets: List[Dict[str, str]],
        score: int,
    ) -> str:
        parts: List[str] = []

        if not dangerous and not secrets:
            return "No dangerous patterns or secrets detected."

        if dangerous:
            names = [d["pattern"] for d in dangerous]
            parts.append(f"Dangerous patterns found: {', '.join(names)}.")

        if secrets:
            names = [s["pattern"] for s in secrets]
            parts.append(f"Secrets/credentials detected: {', '.join(names)}.")

        parts.append(f"Score: {score}/100.")
        return " ".join(parts)
