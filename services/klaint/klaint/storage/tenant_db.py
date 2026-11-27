# SPDX-License-Identifier: Apache-2.0
"""Per-tenant SQLite WAL storage, atomic BEGIN IMMEDIATE helpers, and SHA-256 hash-chained audit log."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from klaint.core.jcs import jcs_dumps, jcs_str
from klaint.core.models import iso_utc, tenant_db_path, validate_tenant_id

GENESIS_PREV_DIGEST = "sha256:" + ("0" * 64)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS consumed_nonces (
    nonce TEXT PRIMARY KEY,
    token_id TEXT NOT NULL,
    session_ref TEXT NOT NULL,
    tool TEXT NOT NULL,
    args_digest TEXT NOT NULL,
    consumed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS action_ledger (
    intent_id TEXT PRIMARY KEY,
    receipt_id TEXT UNIQUE NOT NULL,
    tenant_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    owner TEXT NOT NULL DEFAULT 'klaint_broker',
    action_class TEXT NOT NULL,
    tool TEXT NOT NULL,
    args_json TEXT NOT NULL,
    args_digest TEXT NOT NULL,
    state TEXT NOT NULL,
    verdict_id TEXT NOT NULL,
    principal_scope_ref TEXT NOT NULL,
    epoch INTEGER NOT NULL,
    reconcile_probe TEXT,
    reconciled_result TEXT,
    capability_json TEXT NOT NULL,
    result_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ledger_session_class
    ON action_ledger(tenant_id, session_id, action_class, state);
CREATE INDEX IF NOT EXISTS idx_ledger_idempotency
    ON action_ledger(principal_scope_ref, owner, idempotency_key);

CREATE TABLE IF NOT EXISTS audit_log (
    seq INTEGER PRIMARY KEY,
    prev_digest TEXT NOT NULL,
    entry_digest TEXT NOT NULL,
    event_kind TEXT NOT NULL,
    actor TEXT NOT NULL,
    session_id TEXT,
    policy_version TEXT,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sop_versions (
    sop_id TEXT NOT NULL,
    version_num INTEGER NOT NULL,
    policy_version TEXT NOT NULL,
    domain TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    author_id TEXT NOT NULL,
    approver_id TEXT,
    natural_language_text TEXT NOT NULL,
    definition_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    approved_at TEXT,
    PRIMARY KEY (sop_id, version_num)
);

CREATE TABLE IF NOT EXISTS approval_queue (
    approval_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    domain TEXT NOT NULL,
    tool TEXT NOT NULL,
    args_json TEXT NOT NULL,
    action_class TEXT NOT NULL,
    verdict_json TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    decided_by TEXT,
    decision_note TEXT,
    receipt_id TEXT,
    created_at TEXT NOT NULL,
    decided_at TEXT
);

CREATE TABLE IF NOT EXISTS knowledge_docs (
    doc_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    title TEXT NOT NULL,
    language TEXT NOT NULL,
    acl_tags_json TEXT NOT NULL,
    polarity TEXT NOT NULL DEFAULT 'affirmative',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES knowledge_docs(doc_id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    normalized_content TEXT NOT NULL,
    polarity TEXT NOT NULL DEFAULT 'affirmative',
    embedding_json TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_chunks_fts USING fts5(
    chunk_id UNINDEXED,
    doc_id UNINDEXED,
    normalized_content
);

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    session_id TEXT UNIQUE NOT NULL,
    customer_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    owner_kind TEXT NOT NULL DEFAULT 'ai_owned',
    assigned_operator_id TEXT,
    ownership_epoch INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'open',
    recontact_of TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversation_turns (
    turn_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    turn_index INTEGER NOT NULL,
    language_variety TEXT NOT NULL,
    customer_text TEXT NOT NULL,
    assistant_text TEXT NOT NULL,
    resolution_status TEXT NOT NULL,
    ownership_epoch INTEGER NOT NULL,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    gate_blocked INTEGER NOT NULL DEFAULT 0,
    receipt_ids_json TEXT NOT NULL DEFAULT '[]',
    trace_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS biz_orders (
    order_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    status TEXT NOT NULL,
    total_cents INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    days_since_delivery INTEGER NOT NULL DEFAULT 0,
    items_json TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL,
    last_idempotency_key TEXT
);

CREATE TABLE IF NOT EXISTS biz_shipments (
    shipment_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    carrier TEXT NOT NULL,
    status TEXT NOT NULL,
    delay_days INTEGER NOT NULL DEFAULT 0,
    expedited INTEGER NOT NULL DEFAULT 0,
    tracking_code TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_idempotency_key TEXT
);

CREATE TABLE IF NOT EXISTS biz_refunds (
    refund_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    reason TEXT NOT NULL,
    status TEXT NOT NULL,
    idempotency_key TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS biz_bookings (
    booking_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    service_name TEXT NOT NULL,
    slot_iso TEXT NOT NULL,
    hours_until_slot INTEGER NOT NULL,
    fee_cents INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_idempotency_key TEXT
);

CREATE TABLE IF NOT EXISTS biz_accounts (
    account_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    email TEXT NOT NULL,
    locked INTEGER NOT NULL DEFAULT 0,
    mfa_reset_count INTEGER NOT NULL DEFAULT 0,
    tier TEXT NOT NULL DEFAULT 'standard',
    updated_at TEXT NOT NULL,
    last_idempotency_key TEXT
);

CREATE TABLE IF NOT EXISTS connector_faults (
    tool TEXT PRIMARY KEY,
    fail_mode TEXT NOT NULL,
    remaining_triggers INTEGER NOT NULL DEFAULT 1
);
"""


@dataclass(frozen=True)
class AuditVerificationResult:
    tenant_id: str
    valid: bool
    total_entries: int
    head_digest: str
    broken_at_seq: int | None = None
    reason: str | None = None


def _compute_audit_entry_digest(
    *,
    seq: int,
    prev_digest: str,
    event_kind: str,
    actor: str,
    session_id: str | None,
    policy_version: str | None,
    payload_json: str,
    created_at: str,
) -> str:
    material = {
        "seq": seq,
        "prev_digest": prev_digest,
        "event_kind": event_kind,
        "actor": actor,
        "session_id": session_id,
        "policy_version": policy_version,
        "payload_json": payload_json,
        "created_at": created_at,
    }
    return "sha256:" + hashlib.sha256(jcs_dumps(material)).hexdigest()


def _sanitize_for_jcs(obj: Any) -> Any:
    """Convert floats in informational audit payloads to scaled strings if present; preserve ints/dicts/lists."""
    if isinstance(obj, float):
        return f"{obj:.6f}"
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_jcs(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_jcs(v) for v in obj]
    return obj


class TenantDatabase:
    """Thread-safe and multi-process WAL-safe SQLite database wrapper for a single tenant."""

    def __init__(self, data_dir: Path | str, tenant_id: str) -> None:
        self.tenant_id = validate_tenant_id(tenant_id)
        self.db_path = tenant_db_path(data_dir, self.tenant_id)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._closed = False
        self._conn = sqlite3.connect(
            str(self.db_path),
            timeout=5.0,
            isolation_level=None,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._configure_pragmas()
        self._ensure_schema()

    def _configure_pragmas(self) -> None:
        with self._lock:
            journal = self._conn.execute("PRAGMA journal_mode=WAL;").fetchone()[0]
            if str(journal).lower() != "wal":
                raise RuntimeError(f"Expected SQLite WAL mode, got {journal!r}")
            self._conn.execute("PRAGMA busy_timeout=5000;")
            self._conn.execute("PRAGMA foreign_keys=ON;")
            self._conn.execute("PRAGMA synchronous=NORMAL;")

    def _ensure_schema(self) -> None:
        with self._lock:
            self._conn.executescript(_SCHEMA_SQL)

    def get_pragmas(self) -> dict[str, Any]:
        with self._lock:
            journal = self._conn.execute("PRAGMA journal_mode;").fetchone()[0]
            busy = self._conn.execute("PRAGMA busy_timeout;").fetchone()[0]
            fk = self._conn.execute("PRAGMA foreign_keys;").fetchone()[0]
            return {"journal_mode": str(journal).lower(), "busy_timeout": int(busy), "foreign_keys": int(fk)}

    @contextmanager
    def immediate_transaction(self) -> Iterator[sqlite3.Connection]:
        """Execute an atomic `BEGIN IMMEDIATE` write transaction."""
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE;")
            try:
                yield self._conn
                self._conn.execute("COMMIT;")
            except BaseException:
                if self._conn.in_transaction:
                    self._conn.execute("ROLLBACK;")
                raise

    @contextmanager
    def read_connection(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            yield self._conn

    def exec_script(self, sql: str) -> None:
        with self._lock:
            self._conn.executescript(sql)

    def append_audit(
        self,
        *,
        event_kind: str,
        actor: str,
        payload: dict[str, Any],
        session_id: str | None = None,
        policy_version: str | None = None,
        conn: sqlite3.Connection | None = None,
    ) -> dict[str, Any]:
        """Append a SHA-256 hash-chained event to `audit_log`."""
        payload_json = jcs_str(_sanitize_for_jcs(payload))
        created_at = iso_utc()

        def _insert(active_conn: sqlite3.Connection) -> dict[str, Any]:
            last = active_conn.execute(
                "SELECT seq, entry_digest FROM audit_log ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            seq = 1 if last is None else int(last["seq"]) + 1
            prev_digest = GENESIS_PREV_DIGEST if last is None else str(last["entry_digest"])
            entry_digest = _compute_audit_entry_digest(
                seq=seq,
                prev_digest=prev_digest,
                event_kind=event_kind,
                actor=actor,
                session_id=session_id,
                policy_version=policy_version,
                payload_json=payload_json,
                created_at=created_at,
            )
            active_conn.execute(
                """
                INSERT INTO audit_log (
                    seq, prev_digest, entry_digest, event_kind, actor,
                    session_id, policy_version, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    seq,
                    prev_digest,
                    entry_digest,
                    event_kind,
                    actor,
                    session_id,
                    policy_version,
                    payload_json,
                    created_at,
                ),
            )
            return {
                "seq": seq,
                "prev_digest": prev_digest,
                "entry_digest": entry_digest,
                "event_kind": event_kind,
                "actor": actor,
                "session_id": session_id,
                "policy_version": policy_version,
                "payload": json.loads(payload_json),
                "created_at": created_at,
            }

        if conn is not None:
            return _insert(conn)
        with self.immediate_transaction() as tx:
            return _insert(tx)

    def verify_audit_chain(self) -> AuditVerificationResult:
        """Verify continuity and cryptographic SHA-256 hash chain of `audit_log`."""
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT seq, prev_digest, entry_digest, event_kind, actor,
                       session_id, policy_version, payload_json, created_at
                FROM audit_log
                ORDER BY seq ASC
                """
            ).fetchall()

        expected_seq = 1
        expected_prev = GENESIS_PREV_DIGEST
        for row in rows:
            seq = int(row["seq"])
            if seq != expected_seq:
                return AuditVerificationResult(
                    tenant_id=self.tenant_id,
                    valid=False,
                    total_entries=len(rows),
                    head_digest=expected_prev,
                    broken_at_seq=seq,
                    reason=f"Sequence gap or out-of-order audit row: expected seq={expected_seq}, got seq={seq}",
                )
            if str(row["prev_digest"]) != expected_prev:
                return AuditVerificationResult(
                    tenant_id=self.tenant_id,
                    valid=False,
                    total_entries=len(rows),
                    head_digest=expected_prev,
                    broken_at_seq=seq,
                    reason=f"prev_digest mismatch at seq={seq}",
                )
            recomputed = _compute_audit_entry_digest(
                seq=seq,
                prev_digest=str(row["prev_digest"]),
                event_kind=str(row["event_kind"]),
                actor=str(row["actor"]),
                session_id=row["session_id"],
                policy_version=row["policy_version"],
                payload_json=str(row["payload_json"]),
                created_at=str(row["created_at"]),
            )
            if recomputed != str(row["entry_digest"]):
                return AuditVerificationResult(
                    tenant_id=self.tenant_id,
                    valid=False,
                    total_entries=len(rows),
                    head_digest=expected_prev,
                    broken_at_seq=seq,
                    reason=f"entry_digest tamper detected at seq={seq}",
                )
            expected_prev = recomputed
            expected_seq += 1

        return AuditVerificationResult(
            tenant_id=self.tenant_id,
            valid=True,
            total_entries=len(rows),
            head_digest=expected_prev,
        )

    def list_audit_events(self, limit: int = 200, event_kind: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            if event_kind:
                rows = self._conn.execute(
                    "SELECT * FROM audit_log WHERE event_kind = ? ORDER BY seq DESC LIMIT ?",
                    (event_kind, limit),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM audit_log ORDER BY seq DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            item = dict(r)
            item["payload"] = json.loads(item["payload_json"])
            out.append(item)
        return out

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                try:
                    self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                except sqlite3.Error:
                    pass
                self._conn.close()
                self._closed = True


class TenantStorageRegistry:
    """Manages isolated per-tenant `TenantDatabase` handles rooted at `<data_dir>/tenants/<tenant_id>/klaint.db`."""

    def __init__(self, data_dir: Path | str) -> None:
        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._dbs: dict[str, TenantDatabase] = {}

    def for_tenant(self, tenant_id: str) -> TenantDatabase:
        slug = validate_tenant_id(tenant_id)
        with self._lock:
            db = self._dbs.get(slug)
            if db is None or db._closed:
                db = TenantDatabase(self.data_dir, slug)
                self._dbs[slug] = db
            return db

    def verify_audit_chain(self, tenant_id: str) -> AuditVerificationResult:
        return self.for_tenant(tenant_id).verify_audit_chain()

    def list_tenants(self) -> list[str]:
        tenants_root = self.data_dir / "tenants"
        if not tenants_root.exists():
            return []
        result: list[str] = []
        for child in sorted(tenants_root.iterdir()):
            if child.is_dir() and (child / "klaint.db").exists():
                result.append(child.name)
        return result

    def close_all(self) -> None:
        with self._lock:
            for db in list(self._dbs.values()):
                db.close()
            self._dbs.clear()
