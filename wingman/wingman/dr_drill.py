#!/usr/bin/env python3
"""
DR Drill Runner (TEST + PRD) with enforced Wingman gates.

Enforces, per stage:
  0) Contract gate (health + core API contracts)
  1) Phase 2 gate: 10-point instruction framework (/check)
  2) Phase 4 gate: human approval (/approvals/request -> wait until APPROVED/REJECTED)
  3) Execute the stage action (docker compose)
  4) Validate (compose ps + API health + Telegram getMe)

Security:
  - Does NOT print secrets (tokens/keys/passwords).
  - Uses docker compose config --quiet.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

import requests


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WINGMAN_DIR = os.path.join(REPO_ROOT, "wingman")


@dataclass(frozen=True)
class EnvCfg:
    name: str  # test|prd
    api_url: str
    compose_file: str
    project: str
    env_file: Optional[str] = None


def _sh(cmd: list[str], *, cwd: str, quiet: bool = False) -> None:
    """
    Run a command and stream output. Use quiet=True for commands that can dump config.
    """
    if quiet:
        subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.DEVNULL)
        return
    subprocess.run(cmd, cwd=cwd, check=True)


def _approval_headers(*, read: bool = False, request: bool = False) -> dict:
    """
    Optional headers for approval endpoints.
    We deliberately do NOT support DECIDE here; humans decide via Telegram bot.
    """
    h = {"Content-Type": "application/json"}
    if read:
        v = (os.getenv("WINGMAN_APPROVAL_READ_KEY") or "").strip()
        if v:
            h["X-Wingman-Approval-Read-Key"] = v
    if request:
        v = (os.getenv("WINGMAN_APPROVAL_REQUEST_KEY") or "").strip()
        if v:
            h["X-Wingman-Approval-Request-Key"] = v
    legacy = (os.getenv("WINGMAN_APPROVAL_API_KEY") or "").strip()
    if legacy:
        h["X-Wingman-Approval-Key"] = legacy
    return h


def contract_gate(api_url: str, *, label: str) -> None:
    """
    Hard gate: /health ok + /check + /verify contract shapes.
    """
    r = requests.get(f"{api_url}/health", timeout=10)
    r.raise_for_status()
    j = r.json()
    if j.get("status") != "healthy":
        raise RuntimeError(f"{label} contract gate failed: /health status={j.get('status')}")

    good_instruction = (
        "DELIVERABLES: x\nSUCCESS_CRITERIA: x\nBOUNDARIES: x\nDEPENDENCIES: x\nMITIGATION: x\n"
        "TEST_PROCESS: x\nTEST_RESULTS_FORMAT: x\nRESOURCE_REQUIREMENTS: x\nRISK_ASSESSMENT: x\nQUALITY_METRICS: x\n"
    )
    r = requests.post(f"{api_url}/check", json={"instruction": good_instruction}, timeout=10)
    r.raise_for_status()
    j = r.json()
    for k in ("approved", "score", "missing_sections", "policy_checks"):
        if k not in j:
            raise RuntimeError(f"{label} contract gate failed: /check missing key={k}")

    r = requests.post(f"{api_url}/verify", json={"claim": "contract probe"}, timeout=10)
    r.raise_for_status()
    j = r.json()
    for k in ("verdict", "verifier", "processing_time_ms", "timestamp"):
        if k not in j:
            raise RuntimeError(f"{label} contract gate failed: /verify missing key={k}")


def gate_10_point(api_url: str, *, instruction: str, label: str) -> None:
    r = requests.post(f"{api_url}/check", json={"instruction": instruction}, timeout=15)
    r.raise_for_status()
    j = r.json() or {}
    if not j.get("approved"):
        missing = j.get("missing_sections", []) or []
        score = j.get("score")
        raise RuntimeError(f"{label} Phase 2 gate rejected instruction (score={score}) missing={missing}")


def request_approval(api_url: str, *, env: str, stage: str, instruction: str) -> None:
    r = requests.post(
        f"{api_url}/approvals/request",
        headers=_approval_headers(request=True),
        json={
            "worker_id": f"dr-{env}",
            "task_name": f"DR {env.upper()} {stage}",
            "instruction": instruction,
            "deployment_env": env,
        },
        timeout=15,
    )
    r.raise_for_status()
    j = r.json() or {}
    if not j.get("needs_approval", False):
        return

    req = j.get("request", {}) or {}
    request_id = (req.get("request_id") or "").strip()
    if not request_id:
        raise RuntimeError("approval response missing request_id")

    poll_sec = float(os.getenv("WINGMAN_APPROVAL_POLL_SEC", "2.0"))
    timeout_sec = float(os.getenv("WINGMAN_APPROVAL_TIMEOUT_SEC", "86400"))
    deadline = time.time() + timeout_sec

    while time.time() < deadline:
        time.sleep(poll_sec)
        g = requests.get(f"{api_url}/approvals/{request_id}", headers=_approval_headers(read=True), timeout=15)
        if g.status_code != 200:
            continue
        cur = g.json() or {}
        status = cur.get("status", "")
        if status == "APPROVED":
            return
        if status == "REJECTED":
            raise RuntimeError(f"approval rejected for request_id={request_id}")

    raise RuntimeError(f"approval timed out for request_id={request_id}")


def validate_telegram(cfg: EnvCfg) -> None:
    cmd = ["docker", "compose", "-f", cfg.compose_file, "-p", cfg.project]
    if cfg.env_file:
        cmd += ["--env-file", cfg.env_file]
    cmd += [
        "exec",
        "-T",
        "telegram-bot",
        "python",
        "-c",
        (
            "import os,requests; "
            "t=os.environ.get('BOT_TOKEN'); assert t; "
            "r=requests.get(f'https://api.telegram.org/bot{t}/getMe',timeout=10); "
            "print('ok' if r.ok else r.status_code)"
        ),
    ]
    _sh(cmd, cwd=WINGMAN_DIR)


def validate_stack(cfg: EnvCfg) -> None:
    cmd = ["docker", "compose", "-f", cfg.compose_file, "-p", cfg.project]
    if cfg.env_file:
        cmd += ["--env-file", cfg.env_file]
    cmd += ["config", "--quiet"]
    _sh(cmd, cwd=WINGMAN_DIR, quiet=True)

    cmd = ["docker", "compose", "-f", cfg.compose_file, "-p", cfg.project]
    if cfg.env_file:
        cmd += ["--env-file", cfg.env_file]
    cmd += ["ps"]
    _sh(cmd, cwd=WINGMAN_DIR)

    r = requests.get(f"{cfg.api_url}/health", timeout=10)
    r.raise_for_status()

    validate_telegram(cfg)


def stage_instruction(*, env: str, stage: str) -> str:
    return "\n".join(
        [
            f"DELIVERABLES: DR stage executed: {stage} ({env})",
            "SUCCESS_CRITERIA: Compose action completes; stack state matches expected; health endpoints respond; Telegram getMe ok",
            "BOUNDARIES: No secrets printed; localhost-bound ports only; do not wipe volumes unless explicitly stated",
            "DEPENDENCIES: docker compose v2; local .env.test/.env.prd present (PRD); Wingman API reachable",
            "MITIGATION: If a stage fails, stop and surface logs/status; do not proceed to next stage",
            "TEST_PROCESS: docker compose config --quiet; docker compose ps; curl /health; telegram getMe inside bot container",
            "TEST_RESULTS_FORMAT: Command exit codes + concise status lines (no secret values)",
            "RESOURCE_REQUIREMENTS: CPU moderate; RAM depends on Ollama model pull; disk for volumes",
            f"RISK_ASSESSMENT: High (DR operation {stage} on {env})",
            "QUALITY_METRICS: 100% of gates pass; 0 secrets leaked; deterministic stage-by-stage approval",
        ]
    ) + "\n"


def run_stage(cfg: EnvCfg, *, stage: str, action_cmd: list[str], do_validate: bool) -> None:
    label = f"{cfg.name.upper()}:{stage}"
    contract_gate(cfg.api_url, label=label)
    instr = stage_instruction(env=cfg.name, stage=stage)
    gate_10_point(cfg.api_url, instruction=instr, label=label)
    request_approval(cfg.api_url, env=cfg.name, stage=stage, instruction=instr)
    _sh(action_cmd, cwd=WINGMAN_DIR)
    if do_validate:
        validate_stack(cfg)


def main() -> int:
    p = argparse.ArgumentParser(description="Wingman DR drill runner with enforced gates (TEST + PRD).")
    p.add_argument("--skip-prd", action="store_true", help="Run TEST only.")
    p.add_argument("--skip-test", action="store_true", help="Run PRD only.")
    args = p.parse_args()

    test = EnvCfg(
        name="test",
        api_url="http://127.0.0.1:5002",
        compose_file=os.path.join(WINGMAN_DIR, "docker-compose.yml"),
        project="wingman-test",
        env_file=None,
    )
    prd = EnvCfg(
        name="prd",
        api_url="http://127.0.0.1:5000",
        compose_file=os.path.join(WINGMAN_DIR, "docker-compose.prd.yml"),
        project="wingman-prd",
        env_file=os.path.join(WINGMAN_DIR, ".env.prd"),
    )

    if args.skip_prd and args.skip_test:
        print("Nothing to do (both --skip-test and --skip-prd set).")
        return 2

    if not args.skip_test:
        run_stage(
            test,
            stage="A-stop",
            action_cmd=["docker", "compose", "-f", test.compose_file, "-p", test.project, "down", "--remove-orphans"],
            do_validate=False,
        )
        run_stage(
            test,
            stage="C-cold-start",
            action_cmd=["docker", "compose", "-f", test.compose_file, "-p", test.project, "up", "-d", "--build"],
            do_validate=True,
        )

    if not args.skip_prd:
        # Stage A: Stop only
        run_stage(
            prd,
            stage="A-stop",
            action_cmd=[
                "docker",
                "compose",
                "-f",
                prd.compose_file,
                "-p",
                prd.project,
                "--env-file",
                prd.env_file,
                "stop",
            ],
            do_validate=False,
        )
        # Stage B: Remove only
        run_stage(
            prd,
            stage="B-remove",
            action_cmd=[
                "docker",
                "compose",
                "-f",
                prd.compose_file,
                "-p",
                prd.project,
                "--env-file",
                prd.env_file,
                "rm",
                "-f",
            ],
            do_validate=False,
        )
        # Stage C: Rebuild + start
        run_stage(
            prd,
            stage="C-rebuild",
            action_cmd=[
                "docker",
                "compose",
                "-f",
                prd.compose_file,
                "-p",
                prd.project,
                "--env-file",
                prd.env_file,
                "up",
                "-d",
                "--build",
            ],
            do_validate=False,
        )
        # Stage D: Validate only
        run_stage(
            prd,
            stage="D-validate",
            action_cmd=[
                "docker",
                "compose",
                "-f",
                prd.compose_file,
                "-p",
                prd.project,
                "--env-file",
                prd.env_file,
                "ps",
            ],
            do_validate=True,
        )

    print("DR drill complete (all executed stages passed gates + validations).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
DR Drill Runner (TEST + PRD) with enforced Wingman gates.

Enforces, per stage:
  0) Contract gate (health + core API contracts)
  1) Phase 2 gate: 10-point instruction framework (/check)
  2) Phase 4 gate: human approval (/approvals/request -> wait until APPROVED/REJECTED)
  3) Execute the stage action (docker compose)
  4) Validate (compose ps + API health + Telegram getMe)

Security:
  - Does NOT print secrets (tokens/keys/passwords).
  - Uses docker compose config --quiet.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Optional

import requests


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WINGMAN_DIR = os.path.join(REPO_ROOT, "wingman")


@dataclass(frozen=True)
class EnvCfg:
    name: str  # test|prd
    api_url: str
    compose_file: str
    project: str
    env_file: Optional[str] = None


def _sh(cmd: list[str], *, cwd: str, quiet: bool = False) -> None:
    """
    Run a command and stream output. Use quiet=True for commands that can dump config.
    """
    if quiet:
        # Still show stderr if it fails, but do not spam stdout.
        subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.DEVNULL)
        return
    subprocess.run(cmd, cwd=cwd, check=True)


def _approval_headers(*, read: bool = False, request: bool = False) -> dict:
    """
    Optional headers for approval endpoints.
    We deliberately do NOT support DECIDE here; humans decide via Telegram bot.
    """
    h = {"Content-Type": "application/json"}
    if read:
        v = (os.getenv("WINGMAN_APPROVAL_READ_KEY") or "").strip()
        if v:
            h["X-Wingman-Approval-Read-Key"] = v
    if request:
        v = (os.getenv("WINGMAN_APPROVAL_REQUEST_KEY") or "").strip()
        if v:
            h["X-Wingman-Approval-Request-Key"] = v
    legacy = (os.getenv("WINGMAN_APPROVAL_API_KEY") or "").strip()
    if legacy:
        h["X-Wingman-Approval-Key"] = legacy
    return h


def contract_gate(api_url: str, *, label: str) -> None:
    """
    Hard gate: /health ok + /check + /verify contract shapes.
    """
    # /health
    r = requests.get(f"{api_url}/health", timeout=10)
    r.raise_for_status()
    j = r.json()
    if j.get("status") != "healthy":
        raise RuntimeError(f"{label} contract gate failed: /health status={j.get('status')}")

    # /check
    good_instruction = (
        "DELIVERABLES: x\nSUCCESS_CRITERIA: x\nBOUNDARIES: x\nDEPENDENCIES: x\nMITIGATION: x\n"
        "TEST_PROCESS: x\nTEST_RESULTS_FORMAT: x\nRESOURCE_REQUIREMENTS: x\nRISK_ASSESSMENT: x\nQUALITY_METRICS: x\n"
    )
    r = requests.post(f"{api_url}/check", json={"instruction": good_instruction}, timeout=10)
    r.raise_for_status()
    j = r.json()
    for k in ("approved", "score", "missing_sections", "policy_checks"):
        if k not in j:
            raise RuntimeError(f"{label} contract gate failed: /check missing key={k}")

    # /verify
    r = requests.post(f"{api_url}/verify", json={"claim": "contract probe"}, timeout=10)
    r.raise_for_status()
    j = r.json()
    for k in ("verdict", "verifier", "processing_time_ms", "timestamp"):
        if k not in j:
            raise RuntimeError(f"{label} contract gate failed: /verify missing key={k}")


def gate_10_point(api_url: str, *, instruction: str, label: str) -> None:
    r = requests.post(f"{api_url}/check", json={"instruction": instruction}, timeout=15)
    r.raise_for_status()
    j = r.json() or {}
    if not j.get("approved"):
        missing = j.get("missing_sections", []) or []
        score = j.get("score")
        raise RuntimeError(f"{label} Phase 2 gate rejected instruction (score={score}) missing={missing}")


def request_approval(api_url: str, *, env: str, stage: str, instruction: str) -> None:
    r = requests.post(
        f"{api_url}/approvals/request",
        headers=_approval_headers(request=True),
        json={
            "worker_id": f"dr-{env}",
            "task_name": f"DR {env.upper()} {stage}",
            "instruction": instruction,
            "deployment_env": env,
        },
        timeout=15,
    )
    r.raise_for_status()
    j = r.json() or {}
    if not j.get("needs_approval", False):
        return

    req = j.get("request", {}) or {}
    request_id = (req.get("request_id") or "").strip()
    if not request_id:
        raise RuntimeError("approval response missing request_id")

    poll_sec = float(os.getenv("WINGMAN_APPROVAL_POLL_SEC", "2.0"))
    timeout_sec = float(os.getenv("WINGMAN_APPROVAL_TIMEOUT_SEC", "86400"))
    deadline = time.time() + timeout_sec

    while time.time() < deadline:
        time.sleep(poll_sec)
        g = requests.get(f"{api_url}/approvals/{request_id}", headers=_approval_headers(read=True), timeout=15)
        if g.status_code != 200:
            continue
        cur = g.json() or {}
        status = cur.get("status", "")
        if status == "APPROVED":
            return
        if status == "REJECTED":
            raise RuntimeError(f"approval rejected for request_id={request_id}")

    raise RuntimeError(f"approval timed out for request_id={request_id}")


def validate_telegram(cfg: EnvCfg) -> None:
    # Must run inside the bot container; do not print token.
    cmd = [
        "docker",
        "compose",
        "-f",
        cfg.compose_file,
        "-p",
        cfg.project,
    ]
    if cfg.env_file:
        cmd += ["--env-file", cfg.env_file]
    cmd += [
        "exec",
        "-T",
        "telegram-bot",
        "python",
        "-c",
        (
            "import os,requests; "
            "t=os.environ.get('BOT_TOKEN'); assert t; "
            "r=requests.get(f'https://api.telegram.org/bot{t}/getMe',timeout=10); "
            "print('ok' if r.ok else r.status_code)"
        ),
    ]
    _sh(cmd, cwd=WINGMAN_DIR)


def validate_stack(cfg: EnvCfg) -> None:
    # Compose config validation (quiet)
    cmd = ["docker", "compose", "-f", cfg.compose_file, "-p", cfg.project]
    if cfg.env_file:
        cmd += ["--env-file", cfg.env_file]
    cmd += ["config", "--quiet"]
    _sh(cmd, cwd=WINGMAN_DIR, quiet=True)

    # Basic container listing
    cmd = ["docker", "compose", "-f", cfg.compose_file, "-p", cfg.project]
    if cfg.env_file:
        cmd += ["--env-file", cfg.env_file]
    cmd += ["ps"]
    _sh(cmd, cwd=WINGMAN_DIR)

    # API health
    r = requests.get(f"{cfg.api_url}/health", timeout=10)
    r.raise_for_status()

    # Telegram reachability
    validate_telegram(cfg)


def stage_instruction(*, env: str, stage: str) -> str:
    """
    10-point instruction packet for Wingman Phase 2 gate.
    Avoid forbidden ops markers like '--force' unless explicitly needed.
    """
    return "\n".join(
        [
            f"DELIVERABLES: DR stage executed: {stage} ({env})",
            "SUCCESS_CRITERIA: Compose action completes; stack state matches expected; health endpoints respond; Telegram getMe ok",
            "BOUNDARIES: No secrets printed; localhost-bound ports only; do not wipe volumes unless explicitly stated",
            "DEPENDENCIES: docker compose v2; local .env.test/.env.prd present (PRD); Wingman API reachable",
            "MITIGATION: If a stage fails, stop and surface logs/status; do not proceed to next stage",
            "TEST_PROCESS: docker compose config --quiet; docker compose ps; curl /health; telegram getMe inside bot container",
            "TEST_RESULTS_FORMAT: Command exit codes + concise status lines (no secret values)",
            "RESOURCE_REQUIREMENTS: CPU moderate; RAM depends on Ollama model pull; disk for volumes",
            f"RISK_ASSESSMENT: High (DR operation {stage} on {env})",
            "QUALITY_METRICS: 100% of gates pass; 0 secrets leaked; deterministic stage-by-stage approval",
        ]
    ) + "\n"


def run_stage(cfg: EnvCfg, *, stage: str, action_cmd: list[str], do_validate: bool) -> None:
    label = f"{cfg.name.upper()}:{stage}"
    contract_gate(cfg.api_url, label=label)
    instr = stage_instruction(env=cfg.name, stage=stage)
    gate_10_point(cfg.api_url, instruction=instr, label=label)
    request_approval(cfg.api_url, env=cfg.name, stage=stage, instruction=instr)
    _sh(action_cmd, cwd=WINGMAN_DIR)
    if do_validate:
        validate_stack(cfg)


def main() -> int:
    p = argparse.ArgumentParser(description="Wingman DR drill runner with enforced gates (TEST + PRD).")
    p.add_argument("--skip-prd", action="store_true", help="Run TEST only.")
    p.add_argument("--skip-test", action="store_true", help="Run PRD only.")
    args = p.parse_args()

    test = EnvCfg(
        name="test",
        api_url="http://127.0.0.1:5002",
        compose_file=os.path.join(WINGMAN_DIR, "docker-compose.yml"),
        project="wingman-test",
        env_file=None,
    )
    prd = EnvCfg(
        name="prd",
        api_url="http://127.0.0.1:5000",
        compose_file=os.path.join(WINGMAN_DIR, "docker-compose.prd.yml"),
        project="wingman-prd",
        env_file=os.path.join(WINGMAN_DIR, ".env.prd"),
    )

    if args.skip_prd and args.skip_test:
        print("Nothing to do (both --skip-test and --skip-prd set).")
        return 2

    # TEST stages
    if not args.skip_test:
        # Stage A: Stop only
        run_stage(
            test,
            stage="A-stop",
            action_cmd=["docker", "compose", "-f", test.compose_file, "-p", test.project, "stop"],
            do_validate=False,
        )
        # Stage B: Remove only
        run_stage(
            test,
            stage="B-remove",
            action_cmd=["docker", "compose", "-f", test.compose_file, "-p", test.project, "rm", "-f"],
            do_validate=False,
        )
        # Stage C: Rebuild + start
        run_stage(
            test,
            stage="C-rebuild",
            action_cmd=["docker", "compose", "-f", test.compose_file, "-p", test.project, "up", "-d", "--build"],
            do_validate=False,
        )
        # Stage D: Validate only
        run_stage(
            test,
            stage="D-validate",
            action_cmd=["docker", "compose", "-f", test.compose_file, "-p", test.project, "ps"],
            do_validate=True,
        )

    # PRD stages
    if not args.skip_prd:
        run_stage(
            prd,
            stage="A-stop",
            action_cmd=["docker", "compose", "-f", prd.compose_file, "-p", prd.project, "--env-file", prd.env_file, "down", "--remove-orphans"],
            do_validate=False,
        )
        run_stage(
            prd,
            stage="C-cold-start",
            action_cmd=["docker", "compose", "-f", prd.compose_file, "-p", prd.project, "--env-file", prd.env_file, "up", "-d", "--build"],
            do_validate=True,
        )

    print("DR drill complete (all executed stages passed gates + validations).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

