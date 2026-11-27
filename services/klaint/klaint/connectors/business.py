# SPDX-License-Identifier: Apache-2.0
"""Synthetic self-hosted business connectors (`orders`, `shipments`, `refunds`, `bookings`, `accounts`).

All reads and writes derive `tenant_id` and `customer_id` exclusively from server-authenticated session state,
support deterministic `idempotency_key` deduplication, expose read-only `reconcile_probe` (`GET` by idempotency key),
and support cross-process fault injection (`timeout_before_commit`, `timeout_after_commit`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from klaint.core.errors import AuthorityViolationError, ConnectorTimeoutError, KlaintError
from klaint.core.models import (
    ActionClass,
    AuthenticatedSession,
    iso_utc,
    new_id,
    reject_forged_identity_args,
)
from klaint.storage.tenant_db import TenantDatabase

FaultMode = Literal["timeout_before_commit", "timeout_after_commit"]

TOOL_ACTION_CLASS: dict[str, ActionClass] = {
    "orders.get_order": ActionClass.READ,
    "orders.list_orders": ActionClass.READ,
    "orders.cancel_order": ActionClass.REVERSIBLE_WRITE,
    "shipments.get_shipment": ActionClass.READ,
    "shipments.expedite_shipment": ActionClass.REVERSIBLE_WRITE,
    "refunds.issue_refund": ActionClass.MONEY,
    "bookings.get_booking": ActionClass.READ,
    "bookings.reschedule_booking": ActionClass.REVERSIBLE_WRITE,
    "bookings.cancel_booking": ActionClass.REVERSIBLE_WRITE,
    "accounts.get_account": ActionClass.READ,
    "accounts.unlock_account": ActionClass.CREDENTIAL_USE,
    "accounts.reset_mfa": ActionClass.CREDENTIAL_USE,
}


@dataclass(frozen=True)
class ReconcileProbeResult:
    probe_uri: str
    effect_present: bool
    record: dict[str, Any] | None = None


class BusinessConnectorSuite:
    """Deterministic SQLite-backed enterprise connector suite for a single tenant."""

    def __init__(self, db: TenantDatabase) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Seeding & Fault Injection Helpers
    # ------------------------------------------------------------------

    def seed_order(
        self,
        *,
        order_id: str,
        customer_id: str,
        total_cents: int,
        status: str = "delivered",
        currency: str = "USD",
        days_since_delivery: int = 5,
        items: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        now = iso_utc()
        with self.db.immediate_transaction() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO biz_orders (
                    order_id, tenant_id, customer_id, status, total_cents,
                    currency, days_since_delivery, items_json, updated_at, last_idempotency_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    order_id,
                    self.db.tenant_id,
                    customer_id,
                    status,
                    int(total_cents),
                    currency,
                    int(days_since_delivery),
                    json.dumps(items or []),
                    now,
                ),
            )
        return {
            "order_id": order_id,
            "tenant_id": self.db.tenant_id,
            "customer_id": customer_id,
            "status": status,
            "total_cents": int(total_cents),
            "currency": currency,
            "days_since_delivery": int(days_since_delivery),
        }

    def seed_shipment(
        self,
        *,
        shipment_id: str,
        customer_id: str,
        order_id: str,
        carrier: str = "DHL",
        status: str = "delayed",
        delay_days: int = 4,
        tracking_code: str = "TRK-1001",
    ) -> dict[str, Any]:
        now = iso_utc()
        with self.db.immediate_transaction() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO biz_shipments (
                    shipment_id, tenant_id, customer_id, order_id, carrier,
                    status, delay_days, expedited, tracking_code, updated_at, last_idempotency_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, NULL)
                """,
                (
                    shipment_id,
                    self.db.tenant_id,
                    customer_id,
                    order_id,
                    carrier,
                    status,
                    int(delay_days),
                    tracking_code,
                    now,
                ),
            )
        return {"shipment_id": shipment_id, "order_id": order_id, "status": status, "delay_days": delay_days}

    def seed_booking(
        self,
        *,
        booking_id: str,
        customer_id: str,
        service_name: str,
        slot_iso: str,
        hours_until_slot: int = 48,
        fee_cents: int = 0,
        status: str = "confirmed",
    ) -> dict[str, Any]:
        now = iso_utc()
        with self.db.immediate_transaction() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO biz_bookings (
                    booking_id, tenant_id, customer_id, service_name, slot_iso,
                    hours_until_slot, fee_cents, status, updated_at, last_idempotency_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    booking_id,
                    self.db.tenant_id,
                    customer_id,
                    service_name,
                    slot_iso,
                    int(hours_until_slot),
                    int(fee_cents),
                    status,
                    now,
                ),
            )
        return {"booking_id": booking_id, "customer_id": customer_id, "slot_iso": slot_iso, "status": status}

    def seed_account(
        self,
        *,
        account_id: str,
        customer_id: str,
        email: str,
        locked: bool = True,
        tier: str = "standard",
    ) -> dict[str, Any]:
        now = iso_utc()
        with self.db.immediate_transaction() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO biz_accounts (
                    account_id, tenant_id, customer_id, email, locked,
                    mfa_reset_count, tier, updated_at, last_idempotency_key
                ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, NULL)
                """,
                (account_id, self.db.tenant_id, customer_id, email, 1 if locked else 0, tier, now),
            )
        return {"account_id": account_id, "customer_id": customer_id, "locked": locked, "tier": tier}

    def inject_fault(self, tool: str, fail_mode: FaultMode, count: int = 1) -> None:
        """Register deterministic fault injection persisted in SQLite so out-of-process broker observes it."""
        with self.db.immediate_transaction() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO connector_faults(tool, fail_mode, remaining_triggers) VALUES (?, ?, ?)",
                (tool, fail_mode, int(count)),
            )

    def clear_faults(self) -> None:
        with self.db.immediate_transaction() as conn:
            conn.execute("DELETE FROM connector_faults")

    def _consume_fault(self, tool: str) -> str | None:
        with self.db.immediate_transaction() as conn:
            row = conn.execute(
                "SELECT fail_mode, remaining_triggers FROM connector_faults WHERE tool = ?",
                (tool,),
            ).fetchone()
            if row is None or int(row["remaining_triggers"]) <= 0:
                return None
            rem = int(row["remaining_triggers"]) - 1
            if rem <= 0:
                conn.execute("DELETE FROM connector_faults WHERE tool = ?", (tool,))
            else:
                conn.execute("UPDATE connector_faults SET remaining_triggers = ? WHERE tool = ?", (rem, tool))
            return str(row["fail_mode"])

    # ------------------------------------------------------------------
    # Read-only Investigations (Scoped to AuthenticatedSession)
    # ------------------------------------------------------------------

    def read(self, session: AuthenticatedSession, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if session.tenant_id != self.db.tenant_id:
            raise AuthorityViolationError("Session tenant_id mismatch on connector read")
        reject_forged_identity_args(args, session)

        with self.db.read_connection() as conn:
            if tool == "orders.get_order":
                row = conn.execute(
                    "SELECT * FROM biz_orders WHERE tenant_id = ? AND customer_id = ? AND order_id = ?",
                    (self.db.tenant_id, session.customer_id, str(args["order_id"])),
                ).fetchone()
                return {"found": row is not None, "order": dict(row) if row else None}

            if tool == "orders.list_orders":
                rows = conn.execute(
                    "SELECT * FROM biz_orders WHERE tenant_id = ? AND customer_id = ? ORDER BY order_id ASC",
                    (self.db.tenant_id, session.customer_id),
                ).fetchall()
                return {"orders": [dict(r) for r in rows]}

            if tool == "shipments.get_shipment":
                order_id = args.get("order_id")
                shipment_id = args.get("shipment_id")
                if shipment_id:
                    row = conn.execute(
                        "SELECT * FROM biz_shipments WHERE tenant_id = ? AND customer_id = ? AND shipment_id = ?",
                        (self.db.tenant_id, session.customer_id, str(shipment_id)),
                    ).fetchone()
                else:
                    row = conn.execute(
                        "SELECT * FROM biz_shipments WHERE tenant_id = ? AND customer_id = ? AND order_id = ?",
                        (self.db.tenant_id, session.customer_id, str(order_id)),
                    ).fetchone()
                return {"found": row is not None, "shipment": dict(row) if row else None}

            if tool == "bookings.get_booking":
                row = conn.execute(
                    "SELECT * FROM biz_bookings WHERE tenant_id = ? AND customer_id = ? AND booking_id = ?",
                    (self.db.tenant_id, session.customer_id, str(args["booking_id"])),
                ).fetchone()
                return {"found": row is not None, "booking": dict(row) if row else None}

            if tool == "accounts.get_account":
                row = conn.execute(
                    "SELECT * FROM biz_accounts WHERE tenant_id = ? AND customer_id = ?",
                    (self.db.tenant_id, session.customer_id),
                ).fetchone()
                return {"found": row is not None, "account": dict(row) if row else None}

        raise KlaintError(f"Unsupported read connector tool: {tool!r}")

    # ------------------------------------------------------------------
    # Consequential Mutations (Invoked ONLY by Out-of-Process Broker)
    # ------------------------------------------------------------------

    def mutate(
        self,
        *,
        session: AuthenticatedSession,
        tool: str,
        args: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        if session.tenant_id != self.db.tenant_id:
            raise AuthorityViolationError("Session tenant_id mismatch on connector mutation")
        reject_forged_identity_args(args, session)

        fault = self._consume_fault(tool)
        if fault == "timeout_before_commit":
            raise ConnectorTimeoutError(f"Connector timeout before commit on {tool} (idempotency={idempotency_key})")

        now = iso_utc()
        result: dict[str, Any]

        if tool == "refunds.issue_refund":
            order_id = str(args["order_id"])
            amount_cents = int(args["amount_cents"])
            reason = str(args.get("reason", "customer_request"))
            with self.db.immediate_transaction() as conn:
                existing = conn.execute(
                    "SELECT * FROM biz_refunds WHERE tenant_id = ? AND idempotency_key = ?",
                    (self.db.tenant_id, idempotency_key),
                ).fetchone()
                if existing is not None:
                    result = dict(existing)
                else:
                    order = conn.execute(
                        "SELECT * FROM biz_orders WHERE tenant_id = ? AND customer_id = ? AND order_id = ?",
                        (self.db.tenant_id, session.customer_id, order_id),
                    ).fetchone()
                    if order is None:
                        raise AuthorityViolationError(
                            f"Order {order_id!r} does not belong to authenticated customer {session.customer_id!r}"
                        )
                    if amount_cents <= 0 or amount_cents > int(order["total_cents"]):
                        raise KlaintError(
                            f"Invalid refund amount_cents={amount_cents} for order total {order['total_cents']}"
                        )
                    refund_id = new_id("ref", 8)
                    conn.execute(
                        """
                        INSERT INTO biz_refunds (
                            refund_id, tenant_id, customer_id, order_id,
                            amount_cents, currency, reason, status, idempotency_key, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'issued', ?, ?)
                        """,
                        (
                            refund_id,
                            self.db.tenant_id,
                            session.customer_id,
                            order_id,
                            amount_cents,
                            str(order["currency"]),
                            reason,
                            idempotency_key,
                            now,
                        ),
                    )
                    conn.execute(
                        "UPDATE biz_orders SET status = 'refunded', updated_at = ?, last_idempotency_key = ? WHERE order_id = ?",
                        (now, idempotency_key, order_id),
                    )
                    result = {
                        "refund_id": refund_id,
                        "order_id": order_id,
                        "amount_cents": amount_cents,
                        "currency": str(order["currency"]),
                        "status": "issued",
                        "idempotency_key": idempotency_key,
                    }

        elif tool == "orders.cancel_order":
            order_id = str(args["order_id"])
            with self.db.immediate_transaction() as conn:
                order = conn.execute(
                    "SELECT * FROM biz_orders WHERE tenant_id = ? AND customer_id = ? AND order_id = ?",
                    (self.db.tenant_id, session.customer_id, order_id),
                ).fetchone()
                if order is None:
                    raise AuthorityViolationError(
                        f"Order {order_id!r} does not belong to authenticated customer {session.customer_id!r}"
                    )
                conn.execute(
                    "UPDATE biz_orders SET status = 'cancelled', updated_at = ?, last_idempotency_key = ? WHERE order_id = ?",
                    (now, idempotency_key, order_id),
                )
                result = {"order_id": order_id, "status": "cancelled", "idempotency_key": idempotency_key}

        elif tool == "shipments.expedite_shipment":
            shipment_id = str(args["shipment_id"])
            with self.db.immediate_transaction() as conn:
                ship = conn.execute(
                    "SELECT * FROM biz_shipments WHERE tenant_id = ? AND customer_id = ? AND shipment_id = ?",
                    (self.db.tenant_id, session.customer_id, shipment_id),
                ).fetchone()
                if ship is None:
                    raise AuthorityViolationError(
                        f"Shipment {shipment_id!r} does not belong to authenticated customer {session.customer_id!r}"
                    )
                conn.execute(
                    """
                    UPDATE biz_shipments
                    SET expedited = 1, status = 'expedited', updated_at = ?, last_idempotency_key = ?
                    WHERE shipment_id = ?
                    """,
                    (now, idempotency_key, shipment_id),
                )
                result = {"shipment_id": shipment_id, "status": "expedited", "expedited": True}

        elif tool == "bookings.reschedule_booking":
            booking_id = str(args["booking_id"])
            new_slot_iso = str(args["new_slot_iso"])
            with self.db.immediate_transaction() as conn:
                booking = conn.execute(
                    "SELECT * FROM biz_bookings WHERE tenant_id = ? AND customer_id = ? AND booking_id = ?",
                    (self.db.tenant_id, session.customer_id, booking_id),
                ).fetchone()
                if booking is None:
                    raise AuthorityViolationError(
                        f"Booking {booking_id!r} does not belong to authenticated customer {session.customer_id!r}"
                    )
                conn.execute(
                    """
                    UPDATE biz_bookings
                    SET slot_iso = ?, status = 'rescheduled', updated_at = ?, last_idempotency_key = ?
                    WHERE booking_id = ?
                    """,
                    (new_slot_iso, now, idempotency_key, booking_id),
                )
                result = {"booking_id": booking_id, "slot_iso": new_slot_iso, "status": "rescheduled"}

        elif tool == "bookings.cancel_booking":
            booking_id = str(args["booking_id"])
            with self.db.immediate_transaction() as conn:
                booking = conn.execute(
                    "SELECT * FROM biz_bookings WHERE tenant_id = ? AND customer_id = ? AND booking_id = ?",
                    (self.db.tenant_id, session.customer_id, booking_id),
                ).fetchone()
                if booking is None:
                    raise AuthorityViolationError(
                        f"Booking {booking_id!r} does not belong to authenticated customer {session.customer_id!r}"
                    )
                conn.execute(
                    "UPDATE biz_bookings SET status = 'cancelled', updated_at = ?, last_idempotency_key = ? WHERE booking_id = ?",
                    (now, idempotency_key, booking_id),
                )
                result = {"booking_id": booking_id, "status": "cancelled"}

        elif tool == "accounts.unlock_account":
            account_id = str(args["account_id"])
            with self.db.immediate_transaction() as conn:
                acc = conn.execute(
                    "SELECT * FROM biz_accounts WHERE tenant_id = ? AND customer_id = ? AND account_id = ?",
                    (self.db.tenant_id, session.customer_id, account_id),
                ).fetchone()
                if acc is None:
                    raise AuthorityViolationError(
                        f"Account {account_id!r} does not belong to authenticated customer {session.customer_id!r}"
                    )
                conn.execute(
                    "UPDATE biz_accounts SET locked = 0, updated_at = ?, last_idempotency_key = ? WHERE account_id = ?",
                    (now, idempotency_key, account_id),
                )
                result = {"account_id": account_id, "locked": False, "status": "unlocked"}

        elif tool == "accounts.reset_mfa":
            account_id = str(args["account_id"])
            with self.db.immediate_transaction() as conn:
                acc = conn.execute(
                    "SELECT * FROM biz_accounts WHERE tenant_id = ? AND customer_id = ? AND account_id = ?",
                    (self.db.tenant_id, session.customer_id, account_id),
                ).fetchone()
                if acc is None:
                    raise AuthorityViolationError(
                        f"Account {account_id!r} does not belong to authenticated customer {session.customer_id!r}"
                    )
                new_count = int(acc["mfa_reset_count"]) + 1
                conn.execute(
                    """
                    UPDATE biz_accounts
                    SET mfa_reset_count = ?, updated_at = ?, last_idempotency_key = ?
                    WHERE account_id = ?
                    """,
                    (new_count, now, idempotency_key, account_id),
                )
                result = {"account_id": account_id, "mfa_reset_count": new_count, "status": "mfa_reset"}

        else:
            raise KlaintError(f"Unsupported mutation connector tool: {tool!r}")

        if fault == "timeout_after_commit":
            raise ConnectorTimeoutError(
                f"Connector timeout after commit on {tool} (idempotency={idempotency_key})"
            )

        return result

    # ------------------------------------------------------------------
    # Read-only Reconcile Probe (GET by idempotency_key; NEVER mutates)
    # ------------------------------------------------------------------

    def reconcile_probe(self, tool: str, idempotency_key: str) -> ReconcileProbeResult:
        """Read-only GET probe deciding whether an `unknown` dispatched intent actually committed."""
        probe_uri = f"GET /connectors/{tool}/by-idempotency/{idempotency_key}"
        with self.db.read_connection() as conn:
            if tool == "refunds.issue_refund":
                row = conn.execute(
                    "SELECT * FROM biz_refunds WHERE tenant_id = ? AND idempotency_key = ?",
                    (self.db.tenant_id, idempotency_key),
                ).fetchone()
            elif tool == "orders.cancel_order":
                row = conn.execute(
                    "SELECT * FROM biz_orders WHERE tenant_id = ? AND last_idempotency_key = ? AND status = 'cancelled'",
                    (self.db.tenant_id, idempotency_key),
                ).fetchone()
            elif tool == "shipments.expedite_shipment":
                row = conn.execute(
                    "SELECT * FROM biz_shipments WHERE tenant_id = ? AND last_idempotency_key = ? AND expedited = 1",
                    (self.db.tenant_id, idempotency_key),
                ).fetchone()
            elif tool in ("bookings.reschedule_booking", "bookings.cancel_booking"):
                row = conn.execute(
                    "SELECT * FROM biz_bookings WHERE tenant_id = ? AND last_idempotency_key = ?",
                    (self.db.tenant_id, idempotency_key),
                ).fetchone()
            elif tool in ("accounts.unlock_account", "accounts.reset_mfa"):
                row = conn.execute(
                    "SELECT * FROM biz_accounts WHERE tenant_id = ? AND last_idempotency_key = ?",
                    (self.db.tenant_id, idempotency_key),
                ).fetchone()
            else:
                row = None

        return ReconcileProbeResult(
            probe_uri=probe_uri,
            effect_present=row is not None,
            record=dict(row) if row is not None else None,
        )
