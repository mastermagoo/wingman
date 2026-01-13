#!/usr/bin/env python3
"""
Wingman cron-safe health check WITHOUT hardcoded host ports.

This script discovers the published host port via `docker port`, then probes /health.
It is designed for cron usage where Wingman may be redeployed with different host ports.

Exit codes:
  0 -> healthy
  1 -> unhealthy/unreachable
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request


def _run(cmd: list[str], timeout_sec: int = 10) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec, check=False)
        return int(p.returncode), (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return 1, f"ERROR running {cmd}: {e}"


def _discover_host_bind(container: str, private_port: str) -> str | None:
    """
    Returns host bind like '127.0.0.1:5001' or None.
    Docker output can be either:
      - '8001/tcp -> 127.0.0.1:5001'
      - '127.0.0.1:5001'
    """
    code, out = _run(["docker", "port", container, private_port], timeout_sec=10)
    if code != 0:
        return None
    m = re.search(r"([0-9.]+:\d+)", out)
    return m.group(1) if m else None


def _probe_health(url: str, timeout_sec: int = 5) -> tuple[bool, dict | None, str]:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(body)
        except Exception:
            data = None
        return True, data, body[:500]
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return False, None, body[:500]
    except Exception as e:
        return False, None, str(e)[:500]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--container", required=True, help="Wingman API container name (e.g. wingman-prd-api)")
    ap.add_argument("--container-port", required=True, help="Private container port (e.g. 8001 or 5000)")
    ap.add_argument("--env", default=os.getenv("WINGMAN_ENV", ""), help="Label for logs (PRD/TEST/etc)")
    args = ap.parse_args()

    bind = _discover_host_bind(args.container, args.container_port)
    if not bind:
        print(f"[wingman:{args.env}] ERROR: cannot discover port for {args.container}:{args.container_port}")
        return 1

    url = f"http://{bind}/health"
    ok, data, sample = _probe_health(url, timeout_sec=5)
    if ok and isinstance(data, dict) and data.get("status") in ("healthy", "ok"):
        db = data.get("database")
        print(f"[wingman:{args.env}] OK {url} database={db}")
        return 0

    print(f"[wingman:{args.env}] FAIL {url} sample={sample}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
