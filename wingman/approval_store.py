#!/usr/bin/env python3
"""
Phase 4 (HITL): Approval Store

SQLite-backed queue for human approval decisions.
Designed to be usable in DEV/TEST/PRD without additional dependencies.
"""

from __future__ import annotations

import os
import sqlite3
import uuid
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_parent_dir(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class ApprovalRequest:
    request_id: str
    created_at: str
    status: str  # PENDING|APPROVED|REJECTED|AUTO_APPROVED|EXPIRED
    worker_id: str
    task_name: str
    instruction: str
    risk_level: str  # LOW|MEDIUM|HIGH
    risk_reason: str
    fingerprint: Optional[str] = None
    decided_at: Optional[str] = None
    decided_by: Optional[str] = None
    decision_note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ApprovalStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        _ensure_parent_dir(self.db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        # Use a longer timeout + WAL to reduce intermittent "database is locked"
        # errors when multiple processes/threads (api + bot + watcher) access sqlite.
        conn = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
        except Exception:
            # Best-effort; do not fail if underlying FS/driver rejects PRAGMAs.
            pass
        return conn

    @staticmethod
    def _is_locked_error(e: Exception) -> bool:
        msg = (str(e) or "").lower()
        return (
            "database is locked" in msg
            or "database table is locked" in msg
            or "database is busy" in msg
        )

    def _with_retry(self, fn, *, retries: int = 6) -> Any:
        """
        Retry wrapper for sqlite operations that can transiently fail with lock contention.
        """
        last: Optional[Exception] = None
        for i in range(max(1, int(retries))):
            try:
                return fn()
            except sqlite3.OperationalError as e:
                last = e
                if not self._is_locked_error(e):
                    raise
                import time as _time

                _time.sleep(0.05 * (2**i))
        if last:
            raise last
        raise sqlite3.OperationalError("sqlite operation failed")

    def _init_db(self) -> None:
        def _do():
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS approvals (
                        request_id TEXT PRIMARY KEY,
                        created_at TEXT NOT NULL,
                        status TEXT NOT NULL,
                        fingerprint TEXT,
                        worker_id TEXT NOT NULL,
                        task_name TEXT NOT NULL,
                        instruction TEXT NOT NULL,
                        risk_level TEXT NOT NULL,
                        risk_reason TEXT NOT NULL,
                        decided_at TEXT,
                        decided_by TEXT,
                        decision_note TEXT
                    )
                    """
                )
                # Lightweight migration for older DBs missing fingerprint column
                cols = [r["name"] for r in conn.execute("PRAGMA table_info(approvals)").fetchall()]
                if "fingerprint" not in cols:
                    conn.execute("ALTER TABLE approvals ADD COLUMN fingerprint TEXT")

                # Indexes (create after migration so referenced columns exist)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_approvals_status_created ON approvals(status, created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_approvals_fingerprint_status ON approvals(fingerprint, status)")

        self._with_retry(_do)

    @staticmethod
    def compute_fingerprint(*, worker_id: str, task_name: str, instruction: str, risk_level: str) -> str:
        raw = f"{worker_id}\n{task_name}\n{risk_level}\n{instruction}".encode("utf-8", errors="ignore")
        return hashlib.sha256(raw).hexdigest()

    def find_pending_by_fingerprint(self, fingerprint: str) -> Optional[ApprovalRequest]:
        if not fingerprint:
            return None
        def _do():
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM approvals WHERE fingerprint = ? AND status = 'PENDING' ORDER BY created_at DESC LIMIT 1",
                    (fingerprint,),
                ).fetchone()
                if not row:
                    return None
                return ApprovalRequest(**dict(row))

        return self._with_retry(_do)

    def expire_stale_pending(self, ttl_sec: int) -> int:
        """
        Mark pending approvals older than ttl_sec as EXPIRED.
        Returns number of rows updated.
        """
        if ttl_sec <= 0:
            return 0
        now = datetime.now(timezone.utc)
        updated = 0
        def _do():
            nonlocal updated
            with self._connect() as conn:
                rows = conn.execute("SELECT request_id, created_at FROM approvals WHERE status='PENDING'").fetchall()
                for r in rows:
                    try:
                        created = datetime.fromisoformat(r["created_at"])
                        if created.tzinfo is None:
                            created = created.replace(tzinfo=timezone.utc)
                    except Exception:
                        continue
                    if (now - created).total_seconds() > ttl_sec:
                        conn.execute(
                            "UPDATE approvals SET status='EXPIRED', decided_at=? WHERE request_id=? AND status='PENDING'",
                            (_utc_now_iso(), r["request_id"]),
                        )
                        updated += 1

        self._with_retry(_do)
        return updated

    def create_request(
        self,
        *,
        worker_id: str,
        task_name: str,
        instruction: str,
        risk_level: str,
        risk_reason: str,
        status: str = "PENDING",
    ) -> ApprovalRequest:
        fingerprint = self.compute_fingerprint(
            worker_id=str(worker_id),
            task_name=task_name or "",
            instruction=instruction or "",
            risk_level=risk_level,
        )
        req = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            created_at=_utc_now_iso(),
            status=status,
            fingerprint=fingerprint,
            worker_id=str(worker_id),
            task_name=task_name or "",
            instruction=instruction or "",
            risk_level=risk_level,
            risk_reason=risk_reason,
        )
        def _do():
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO approvals (
                        request_id, created_at, status, fingerprint, worker_id, task_name, instruction,
                        risk_level, risk_reason, decided_at, decided_by, decision_note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        req.request_id,
                        req.created_at,
                        req.status,
                        req.fingerprint,
                        req.worker_id,
                        req.task_name,
                        req.instruction,
                        req.risk_level,
                        req.risk_reason,
                        req.decided_at,
                        req.decided_by,
                        req.decision_note,
                    ),
                )

        self._with_retry(_do)
        return req

    def get(self, request_id: str) -> Optional[ApprovalRequest]:
        def _do():
            with self._connect() as conn:
                row = conn.execute("SELECT * FROM approvals WHERE request_id = ?", (request_id,)).fetchone()
                if not row:
                    return None
                return ApprovalRequest(**dict(row))

        return self._with_retry(_do)

    def list_pending(self, limit: int = 20) -> List[ApprovalRequest]:
        # Be defensive: env vars sometimes get set to non-integers (e.g. "600s").
        # A bad value should never take down the approval queue.
        raw_ttl = (os.getenv("WINGMAN_APPROVAL_PENDING_TTL_SEC", "0") or "0").strip()
        try:
            ttl = int(raw_ttl)
        except Exception:
            ttl = 0
        if ttl > 0:
            try:
                self.expire_stale_pending(ttl)
            except Exception:
                pass
        def _do():
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM approvals WHERE status = 'PENDING' ORDER BY created_at ASC LIMIT ?",
                    (int(limit),),
                ).fetchall()
                return [ApprovalRequest(**dict(r)) for r in rows]

        return self._with_retry(_do)

    def decide(
        self,
        request_id: str,
        *,
        decision: str,  # APPROVED|REJECTED
        decided_by: Optional[str] = None,
        decision_note: Optional[str] = None,
    ) -> Optional[ApprovalRequest]:
        decided_at = _utc_now_iso()
        def _do():
            with self._connect() as conn:
                row = conn.execute("SELECT * FROM approvals WHERE request_id = ?", (request_id,)).fetchone()
                if not row:
                    return None
                current = dict(row)
                if current.get("status") != "PENDING":
                    # Idempotent: return current state if already decided
                    return ApprovalRequest(**current)
                conn.execute(
                    """
                    UPDATE approvals
                    SET status = ?, decided_at = ?, decided_by = ?, decision_note = ?
                    WHERE request_id = ?
                    """,
                    (decision, decided_at, decided_by, decision_note, request_id),
                )
            return self.get(request_id)

        return self._with_retry(_do)


def default_store() -> ApprovalStore:
    db_path = os.getenv("WINGMAN_APPROVAL_DB", os.path.join(os.path.dirname(__file__), "data", "approvals.db"))
    try:
        return ApprovalStore(db_path=db_path)
    except Exception as e:
        # Fail-open for availability: if the configured path is not writable/mountable
        # (common with container volume permission edge cases), fall back to /tmp.
        # This keeps PRD/TEST API alive and avoids 500s due to startup crashes.
        fallback = os.getenv("WINGMAN_APPROVAL_DB_FALLBACK", "/tmp/approvals.db")
        try:
            print(f"⚠️  Approval DB init failed at {db_path}: {e}. Falling back to {fallback}")
        except Exception:
            pass
        return ApprovalStore(db_path=fallback)


