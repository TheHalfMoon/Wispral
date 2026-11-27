# SPDX-License-Identifier: Apache-2.0
"""Customer profiles, built-in Inbox/Tickets with SLA timers, internal notes, structured handoff summaries,
and the monotonic `ownership_epoch` (`ai_owned` <-> `human_owned`) state machine.
"""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any, Literal

from klaint.core.errors import AuthorityViolationError, KlaintError, TenantIsolationError
from klaint.core.models import (
    SessionAuthenticator,
    iso_utc,
    new_id,
    parse_iso_utc,
    utc_now,
    validate_tenant_id,
)
from klaint.storage.tenant_db import TenantDatabase, TenantStorageRegistry

TicketStatus = Literal["open", "pending", "snoozed", "escalated", "resolved"]
TicketPriority = Literal["low", "normal", "high", "urgent"]

_SLA_MINUTES_BY_PRIORITY: dict[str, int] = {
    "urgent": 15,
    "high": 60,
    "normal": 240,
    "low": 1440,
}

_INBOX_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS customer_profiles (
    customer_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    preferred_language TEXT NOT NULL DEFAULT 'en',
    tier TEXT NOT NULL DEFAULT 'standard',
    tags_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    conversation_id TEXT,
    session_id TEXT,
    customer_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    priority TEXT NOT NULL DEFAULT 'normal',
    sla_due_at TEXT NOT NULL,
    assigned_operator_id TEXT,
    handoff_summary_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tickets_tenant_status ON tickets(tenant_id, status);

CREATE TABLE IF NOT EXISTS ticket_notes (
    note_id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    body TEXT NOT NULL,
    visibility TEXT NOT NULL DEFAULT 'internal',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS webhook_replay_cache (
    webhook_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    received_timestamp INTEGER NOT NULL,
    payload_sha256 TEXT NOT NULL,
    processed_at TEXT NOT NULL
);
"""

VALID_TICKET_STATUSES: frozenset[str] = frozenset({"open", "pending", "snoozed", "escalated", "resolved"})


def ensure_inbox_schema(db: TenantDatabase) -> None:
    db.exec_script(_INBOX_SCHEMA_SQL)


class InboxManager:
    """Manages customer profiles, tickets, SLAs, internal notes, handoff summaries, and `ownership_epoch`."""

    def __init__(
        self,
        storage: TenantStorageRegistry,
        session_auth: SessionAuthenticator | None = None,
    ) -> None:
        self.storage = storage
        self.session_auth = session_auth

    def _db(self, tenant_id: str) -> TenantDatabase:
        db = self.storage.for_tenant(validate_tenant_id(tenant_id))
        ensure_inbox_schema(db)
        return db

    # ------------------------------------------------------------------
    # Customer Profiles
    # ------------------------------------------------------------------

    def upsert_customer_profile(
        self,
        *,
        tenant_id: str,
        customer_id: str,
        display_name: str,
        email: str | None = None,
        phone: str | None = None,
        preferred_language: str = "en",
        tier: str = "standard",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        db = self._db(tenant_id)
        now = iso_utc()
        tags_list = sorted({str(t).strip() for t in (tags or []) if str(t).strip()})
        with db.immediate_transaction() as conn:
            existing = conn.execute(
                "SELECT created_at FROM customer_profiles WHERE tenant_id = ? AND customer_id = ?",
                (db.tenant_id, customer_id),
            ).fetchone()
            created_at = str(existing["created_at"]) if existing else now
            conn.execute(
                """
                INSERT OR REPLACE INTO customer_profiles (
                    customer_id, tenant_id, display_name, email, phone,
                    preferred_language, tier, tags_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    customer_id,
                    db.tenant_id,
                    display_name,
                    email,
                    phone,
                    preferred_language,
                    tier,
                    json.dumps(tags_list),
                    created_at,
                    now,
                ),
            )
        return self.get_customer_profile(db.tenant_id, customer_id)  # type: ignore[return-value]

    def get_customer_profile(self, tenant_id: str, customer_id: str) -> dict[str, Any] | None:
        db = self._db(tenant_id)
        with db.read_connection() as conn:
            row = conn.execute(
                "SELECT * FROM customer_profiles WHERE tenant_id = ? AND customer_id = ?",
                (db.tenant_id, customer_id),
            ).fetchone()
        if row is None:
            return None
        out = dict(row)
        out["tags"] = json.loads(str(row["tags_json"]))
        return out

    def list_customer_profiles(self, tenant_id: str) -> list[dict[str, Any]]:
        db = self._db(tenant_id)
        with db.read_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM customer_profiles WHERE tenant_id = ? ORDER BY updated_at DESC",
                (db.tenant_id,),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            item = dict(r)
            item["tags"] = json.loads(str(r["tags_json"]))
            out.append(item)
        return out

    # ------------------------------------------------------------------
    # Tickets, SLAs, Assignments, Internal Notes & Handoff Summaries
    # ------------------------------------------------------------------

    def create_ticket(
        self,
        *,
        tenant_id: str,
        customer_id: str,
        subject: str,
        priority: TicketPriority = "normal",
        status: TicketStatus = "open",
        conversation_id: str | None = None,
        session_id: str | None = None,
        assigned_operator_id: str | None = None,
    ) -> dict[str, Any]:
        if status not in VALID_TICKET_STATUSES:
            raise KlaintError(f"Invalid ticket status {status!r}")
        if priority not in _SLA_MINUTES_BY_PRIORITY:
            raise KlaintError(f"Invalid ticket priority {priority!r}")

        db = self._db(tenant_id)
        now_dt = utc_now()
        now = iso_utc(now_dt)
        sla_due = iso_utc(now_dt + timedelta(minutes=_SLA_MINUTES_BY_PRIORITY[priority]))
        ticket_id = new_id("tkt", 10)

        with db.immediate_transaction() as conn:
            conn.execute(
                """
                INSERT INTO tickets (
                    ticket_id, tenant_id, conversation_id, session_id, customer_id,
                    subject, status, priority, sla_due_at, assigned_operator_id,
                    handoff_summary_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (
                    ticket_id,
                    db.tenant_id,
                    conversation_id,
                    session_id,
                    customer_id,
                    subject,
                    status,
                    priority,
                    sla_due,
                    assigned_operator_id,
                    now,
                    now,
                ),
            )
            db.append_audit(
                event_kind="ticket_created",
                actor=assigned_operator_id or "klaint_inbox",
                session_id=session_id,
                payload={"ticket_id": ticket_id, "status": status, "priority": priority, "sla_due_at": sla_due},
                conn=conn,
            )
        return self.get_ticket(db.tenant_id, ticket_id)

    def update_ticket(
        self,
        *,
        tenant_id: str,
        ticket_id: str,
        operator_id: str,
        status: TicketStatus | None = None,
        assigned_operator_id: str | None = None,
        priority: TicketPriority | None = None,
    ) -> dict[str, Any]:
        db = self._db(tenant_id)
        if status is not None and status not in VALID_TICKET_STATUSES:
            raise KlaintError(f"Invalid ticket status {status!r}")
        if priority is not None and priority not in _SLA_MINUTES_BY_PRIORITY:
            raise KlaintError(f"Invalid ticket priority {priority!r}")

        now = iso_utc()
        with db.immediate_transaction() as conn:
            row = conn.execute(
                "SELECT * FROM tickets WHERE tenant_id = ? AND ticket_id = ?",
                (db.tenant_id, ticket_id),
            ).fetchone()
            if row is None:
                raise TenantIsolationError(f"Ticket {ticket_id!r} not found in tenant {db.tenant_id!r}")

            new_status = status or str(row["status"])
            new_assignee = assigned_operator_id if assigned_operator_id is not None else row["assigned_operator_id"]
            new_priority = priority or str(row["priority"])
            new_sla = (
                iso_utc(parse_iso_utc(str(row["created_at"])) + timedelta(minutes=_SLA_MINUTES_BY_PRIORITY[new_priority]))
                if priority is not None
                else str(row["sla_due_at"])
            )
            conn.execute(
                """
                UPDATE tickets
                SET status = ?, assigned_operator_id = ?, priority = ?, sla_due_at = ?, updated_at = ?
                WHERE ticket_id = ?
                """,
                (new_status, new_assignee, new_priority, new_sla, now, ticket_id),
            )
            db.append_audit(
                event_kind="ticket_updated",
                actor=operator_id,
                session_id=row["session_id"],
                payload={"ticket_id": ticket_id, "status": new_status, "assigned_operator_id": new_assignee},
                conn=conn,
            )
        return self.get_ticket(db.tenant_id, ticket_id)

    def add_internal_note(
        self,
        *,
        tenant_id: str,
        ticket_id: str,
        author_id: str,
        body: str,
    ) -> dict[str, Any]:
        if not author_id.strip():
            raise AuthorityViolationError("author_id is required for internal ticket notes")
        db = self._db(tenant_id)
        note_id = new_id("nte", 8)
        now = iso_utc()
        with db.immediate_transaction() as conn:
            tkt = conn.execute(
                "SELECT ticket_id FROM tickets WHERE tenant_id = ? AND ticket_id = ?",
                (db.tenant_id, ticket_id),
            ).fetchone()
            if tkt is None:
                raise TenantIsolationError(f"Ticket {ticket_id!r} not found in tenant {db.tenant_id!r}")
            conn.execute(
                """
                INSERT INTO ticket_notes (note_id, ticket_id, tenant_id, author_id, body, visibility, created_at)
                VALUES (?, ?, ?, ?, ?, 'internal', ?)
                """,
                (note_id, ticket_id, db.tenant_id, author_id.strip(), body, now),
            )
        return {
            "note_id": note_id,
            "ticket_id": ticket_id,
            "author_id": author_id.strip(),
            "body": body,
            "visibility": "internal",
            "created_at": now,
        }

    def build_handoff_summary(self, tenant_id: str, conversation_id: str) -> dict[str, Any]:
        """Build a transcript-linked structured handoff summary per KLAINT_UX_SPEC.md."""
        db = self._db(tenant_id)
        with db.read_connection() as conn:
            conv = conn.execute(
                "SELECT * FROM conversations WHERE tenant_id = ? AND conversation_id = ?",
                (db.tenant_id, conversation_id),
            ).fetchone()
            if conv is None:
                raise TenantIsolationError(f"Conversation {conversation_id!r} not found in tenant {db.tenant_id!r}")
            turns = conn.execute(
                "SELECT * FROM conversation_turns WHERE conversation_id = ? ORDER BY turn_index ASC",
                (conversation_id,),
            ).fetchall()
            approvals = conn.execute(
                "SELECT approval_id, tool, status, reason FROM approval_queue WHERE session_id = ?",
                (str(conv["session_id"]),),
            ).fetchall()

        linked_claims = [
            {
                "turn_id": str(t["turn_id"]),
                "turn_index": int(t["turn_index"]),
                "customer_excerpt": str(t["customer_text"])[:140],
                "resolution_status": str(t["resolution_status"]),
                "receipt_ids": json.loads(str(t["receipt_ids_json"])),
            }
            for t in turns
        ]
        summary = {
            "label": "AI summary — check before relying on it",
            "conversation_id": conversation_id,
            "customer_id": str(conv["customer_id"]),
            "owner_kind": str(conv["owner_kind"]),
            "ownership_epoch": int(conv["ownership_epoch"]),
            "turn_count": len(turns),
            "source_turns": linked_claims,
            "pending_approvals": [dict(a) for a in approvals],
            "generated_at": iso_utc(),
        }
        with db.immediate_transaction() as conn:
            conn.execute(
                "UPDATE tickets SET handoff_summary_json = ?, updated_at = ? WHERE tenant_id = ? AND conversation_id = ?",
                (json.dumps(summary, ensure_ascii=False), iso_utc(), db.tenant_id, conversation_id),
            )
        return summary

    def get_ticket(self, tenant_id: str, ticket_id: str, now_override: str | None = None) -> dict[str, Any]:
        db = self._db(tenant_id)
        eval_now = parse_iso_utc(now_override) if now_override else utc_now()
        with db.read_connection() as conn:
            row = conn.execute(
                "SELECT * FROM tickets WHERE tenant_id = ? AND ticket_id = ?",
                (db.tenant_id, ticket_id),
            ).fetchone()
            if row is None:
                raise TenantIsolationError(f"Ticket {ticket_id!r} not found in tenant {db.tenant_id!r}")
            notes = conn.execute(
                "SELECT * FROM ticket_notes WHERE ticket_id = ? ORDER BY created_at ASC",
                (ticket_id,),
            ).fetchall()

        out = dict(row)
        sla_dt = parse_iso_utc(str(row["sla_due_at"]))
        out["sla_breached"] = bool(out["status"] != "resolved" and eval_now > sla_dt)
        out["handoff_summary"] = (
            json.loads(str(row["handoff_summary_json"])) if row["handoff_summary_json"] else None
        )
        out["notes"] = [dict(n) for n in notes]
        return out

    def list_tickets(self, tenant_id: str, status: str | None = None) -> list[dict[str, Any]]:
        db = self._db(tenant_id)
        with db.read_connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT ticket_id FROM tickets WHERE tenant_id = ? AND status = ? ORDER BY updated_at DESC",
                    (db.tenant_id, status),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT ticket_id FROM tickets WHERE tenant_id = ? ORDER BY updated_at DESC",
                    (db.tenant_id,),
                ).fetchall()
        return [self.get_ticket(db.tenant_id, str(r["ticket_id"])) for r in rows]

    # ------------------------------------------------------------------
    # Monotonic `ownership_epoch` State Machine (`ai_owned` <-> `human_owned`)
    # ------------------------------------------------------------------

    def take_over_conversation(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        operator_id: str,
    ) -> dict[str, Any]:
        """Atomically increment `ownership_epoch` and transfer conversation ownership to `human_owned`."""
        clean_op = operator_id.strip()
        if not clean_op:
            raise AuthorityViolationError("Authenticated operator_id is required for human takeover")

        db = self._db(tenant_id)
        now = iso_utc()
        with db.immediate_transaction() as conn:
            conv = conn.execute(
                "SELECT * FROM conversations WHERE tenant_id = ? AND conversation_id = ?",
                (db.tenant_id, conversation_id),
            ).fetchone()
            if conv is None:
                raise TenantIsolationError(f"Conversation {conversation_id!r} not found in tenant {db.tenant_id!r}")

            new_epoch = int(conv["ownership_epoch"]) + 1
            conn.execute(
                """
                UPDATE conversations
                SET owner_kind = 'human_owned',
                    assigned_operator_id = ?,
                    ownership_epoch = ?,
                    status = 'escalated',
                    updated_at = ?
                WHERE conversation_id = ?
                """,
                (clean_op, new_epoch, now, conversation_id),
            )
            conn.execute(
                """
                UPDATE tickets
                SET status = 'escalated', assigned_operator_id = ?, updated_at = ?
                WHERE tenant_id = ? AND conversation_id = ?
                """,
                (clean_op, now, db.tenant_id, conversation_id),
            )
            db.append_audit(
                event_kind="ownership_epoch_human_takeover",
                actor=clean_op,
                session_id=str(conv["session_id"]),
                payload={
                    "conversation_id": conversation_id,
                    "previous_epoch": int(conv["ownership_epoch"]),
                    "ownership_epoch": new_epoch,
                    "owner_kind": "human_owned",
                    "assigned_operator_id": clean_op,
                },
                conn=conn,
            )

        handoff = self.build_handoff_summary(db.tenant_id, conversation_id)
        return {
            "conversation_id": conversation_id,
            "session_id": str(conv["session_id"]),
            "owner_kind": "human_owned",
            "assigned_operator_id": clean_op,
            "ownership_epoch": new_epoch,
            "banner": "AI paused — you own this conversation",
            "handoff_summary": handoff,
        }

    def return_to_ai(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        operator_id: str,
    ) -> dict[str, Any]:
        """Explicitly return conversation from `human_owned` to `ai_owned` with a fresh monotonic epoch."""
        clean_op = operator_id.strip()
        if not clean_op:
            raise AuthorityViolationError("Authenticated operator_id is required to return ownership to AI")

        db = self._db(tenant_id)
        now = iso_utc()
        with db.immediate_transaction() as conn:
            conv = conn.execute(
                "SELECT * FROM conversations WHERE tenant_id = ? AND conversation_id = ?",
                (db.tenant_id, conversation_id),
            ).fetchone()
            if conv is None:
                raise TenantIsolationError(f"Conversation {conversation_id!r} not found in tenant {db.tenant_id!r}")

            new_epoch = int(conv["ownership_epoch"]) + 1
            conn.execute(
                """
                UPDATE conversations
                SET owner_kind = 'ai_owned',
                    assigned_operator_id = NULL,
                    ownership_epoch = ?,
                    status = 'open',
                    updated_at = ?
                WHERE conversation_id = ?
                """,
                (new_epoch, now, conversation_id),
            )
            db.append_audit(
                event_kind="ownership_epoch_returned_to_ai",
                actor=clean_op,
                session_id=str(conv["session_id"]),
                payload={
                    "conversation_id": conversation_id,
                    "previous_epoch": int(conv["ownership_epoch"]),
                    "ownership_epoch": new_epoch,
                    "owner_kind": "ai_owned",
                },
                conn=conn,
            )

        if self.session_auth is not None:
            try:
                self.session_auth.update_epoch(str(conv["session_id"]), new_epoch)
            except AuthorityViolationError:
                pass

        return {
            "conversation_id": conversation_id,
            "session_id": str(conv["session_id"]),
            "owner_kind": "ai_owned",
            "assigned_operator_id": None,
            "ownership_epoch": new_epoch,
        }

    def list_conversations(self, tenant_id: str) -> list[dict[str, Any]]:
        db = self._db(tenant_id)
        with db.read_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM conversations WHERE tenant_id = ? ORDER BY updated_at DESC",
                (db.tenant_id,),
            ).fetchall()
            out: list[dict[str, Any]] = []
            for r in rows:
                item = dict(r)
                turns = conn.execute(
                    "SELECT * FROM conversation_turns WHERE conversation_id = ? ORDER BY turn_index ASC",
                    (str(r["conversation_id"]),),
                ).fetchall()
                parsed_turns: list[dict[str, Any]] = []
                for t in turns:
                    td = dict(t)
                    td["receipt_ids"] = json.loads(str(t["receipt_ids_json"]))
                    td["why"] = json.loads(str(t["trace_json"]))
                    parsed_turns.append(td)
                item["turns"] = parsed_turns
                out.append(item)
        return out
