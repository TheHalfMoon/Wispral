# SPDX-License-Identifier: Apache-2.0
"""Procedures SOP Engine: natural-language & structured SOP compiler, deterministic policy graphs,
immutable version history, 4-eyes approval (`author_id != approver_id`), and 1-click rollback.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from klaint.core.errors import AuthorityViolationError, FourEyesViolationError, KlaintError
from klaint.core.jcs import compute_args_digest, jcs_dumps, jcs_str
from klaint.core.models import (
    ActionClass,
    AuthenticatedSession,
    PolicyConfirmation,
    PolicyDecision,
    PolicyLayer,
    PolicyVerdict,
    iso_utc,
    new_id,
)
from klaint.storage.tenant_db import TenantDatabase

SOPDomain = Literal["refund", "shipping_delay", "booking_change", "account_recovery", "escalation"]


class PolicyGraphConfig(BaseModel):
    """Deterministic compiled policy graph parameters for an SOP domain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    domain: SOPDomain
    auto_allow_max_cents: int = Field(default=5000, ge=0)
    ask_max_cents: int = Field(default=25000, ge=0)
    return_window_days: int = Field(default=30, ge=0)
    min_delay_days_for_expedite: int = Field(default=3, ge=0)
    min_booking_notice_hours: int = Field(default=24, ge=0)
    max_booking_fee_cents: int = Field(default=5000, ge=0)
    require_step_up: bool = False
    allow_mfa_reset_auto: bool = False


@dataclass(frozen=True)
class SOPVersionRecord:
    sop_id: str
    version_num: int
    policy_version: str
    domain: SOPDomain
    title: str
    status: Literal["draft", "active", "archived"]
    author_id: str
    approver_id: str | None
    natural_language_text: str
    graph: PolicyGraphConfig
    created_at: str
    approved_at: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sop_id": self.sop_id,
            "version_num": self.version_num,
            "policy_version": self.policy_version,
            "domain": self.domain,
            "title": self.title,
            "status": self.status,
            "author_id": self.author_id,
            "approver_id": self.approver_id,
            "natural_language_text": self.natural_language_text,
            "graph": self.graph.model_dump(mode="json"),
            "created_at": self.created_at,
            "approved_at": self.approved_at,
        }


_AUTO_RE = re.compile(r"auto[-_\s]?allow[^\d]*(\d+)\s*cents", re.IGNORECASE)
_LE_ALLOW_RE = re.compile(r"<=\s*(\d+)\s*cents[^\n]*allow", re.IGNORECASE)
_ASK_RE = re.compile(r"(?:ask|approval)[^\d]*(?:\d+\s*(?:\.\.|to|-)\s*)?(\d+)\s*cents", re.IGNORECASE)
_WINDOW_RE = re.compile(r"(\d+)\s*[-_\s]?days?", re.IGNORECASE)
_DELAY_RE = re.compile(r"delay[^\d]*(\d+)\s*days?", re.IGNORECASE)
_NOTICE_RE = re.compile(r"(\d+)\s*hours?", re.IGNORECASE)
_STEP_UP_RE = re.compile(r"step[-_\s]?up", re.IGNORECASE)


def compile_natural_language_sop(domain: SOPDomain, text: str) -> PolicyGraphConfig:
    """Compile natural-language SOP statements into a deterministic `PolicyGraphConfig`."""
    kwargs: dict[str, Any] = {"domain": domain}
    if domain == "account_recovery" or _STEP_UP_RE.search(text):
        kwargs["require_step_up"] = True

    m_auto = _AUTO_RE.search(text) or _LE_ALLOW_RE.search(text)
    if m_auto:
        kwargs["auto_allow_max_cents"] = int(m_auto.group(1))

    m_ask = _ASK_RE.search(text)
    if m_ask:
        val = int(m_ask.group(1))
        if val >= kwargs.get("auto_allow_max_cents", 5000):
            kwargs["ask_max_cents"] = val

    if domain == "refund":
        m_win = _WINDOW_RE.search(text)
        if m_win:
            kwargs["return_window_days"] = int(m_win.group(1))
    elif domain == "shipping_delay":
        m_delay = _DELAY_RE.search(text)
        if m_delay:
            kwargs["min_delay_days_for_expedite"] = int(m_delay.group(1))
    elif domain == "booking_change":
        m_notice = _NOTICE_RE.search(text)
        if m_notice:
            kwargs["min_booking_notice_hours"] = int(m_notice.group(1))

    return PolicyGraphConfig(**kwargs)


DEFAULT_SOPS: dict[SOPDomain, tuple[str, str, PolicyGraphConfig]] = {
    "refund": (
        "Standard Order Refund Policy",
        (
            "1. Verify order belongs to authenticated customer and days_since_delivery <= 30 days.\n"
            "2. Auto-allow refunds <= 5000 cents.\n"
            "3. Require human operator approval (ASK) for 5001..25000 cents.\n"
            "4. Deny refunds > 25000 cents or outside the 30-day return window."
        ),
        PolicyGraphConfig(
            domain="refund",
            auto_allow_max_cents=5000,
            ask_max_cents=25000,
            return_window_days=30,
        ),
    ),
    "shipping_delay": (
        "Carrier Shipping Delay SOP",
        (
            "1. Inspect carrier tracking for customer order.\n"
            "2. When shipment delay >= 3 days and status != delivered, auto-allow expedite_shipment.\n"
            "3. Otherwise provide status or ASK operator."
        ),
        PolicyGraphConfig(domain="shipping_delay", min_delay_days_for_expedite=3),
    ),
    "booking_change": (
        "Appointment & Booking Modification SOP",
        (
            "1. Verify booking ownership.\n"
            "2. When >= 24 hours remain before slot and fee <= 5000 cents, auto-allow reschedule or cancel.\n"
            "3. Inside 24 hours, ASK human operator approval."
        ),
        PolicyGraphConfig(domain="booking_change", min_booking_notice_hours=24, max_booking_fee_cents=5000),
    ),
    "account_recovery": (
        "Account Unlock & Step-Up Recovery SOP",
        (
            "1. Require out-of-band step-up verification on AuthenticatedSession (never chat text).\n"
            "2. Allow unlock_account only after step-up verification.\n"
            "3. Always ASK human approval for reset_mfa."
        ),
        PolicyGraphConfig(domain="account_recovery", require_step_up=True, allow_mfa_reset_auto=False),
    ),
    "escalation": (
        "Safety & Human Escalation SOP",
        "1. Escalate immediately to human operator on customer request, safety signal, or unavailable policy.",
        PolicyGraphConfig(domain="escalation"),
    ),
}


def _compute_policy_version(sop_id: str, version_num: int, graph: PolicyGraphConfig) -> str:
    digest = hashlib.sha256(
        jcs_dumps({"sop_id": sop_id, "version_num": version_num, "graph": graph.model_dump(mode="json")})
    ).hexdigest()
    return f"sha256:{digest}"


def _build_monotone_layers(tenant_decision: PolicyDecision) -> list[PolicyLayer]:
    """Construct monotone narrowing layers (`ALLOW <= ASK <= DENY`) satisfying `policy_verdict.schema.json`."""
    return [
        PolicyLayer(source="base", decision=PolicyDecision.ALLOW),
        PolicyLayer(source="product", decision=PolicyDecision.ALLOW),
        PolicyLayer(source="tenant", decision=tenant_decision),
    ]


class ProceduresEngine:
    """Manages versioned SOPs, 4-eyes approval, 1-click rollback, and deterministic policy evaluation."""

    def __init__(self, db: TenantDatabase) -> None:
        self.db = db

    def bootstrap_defaults(
        self,
        *,
        author_id: str = "system_bootstrap_author",
        approver_id: str = "system_bootstrap_reviewer",
    ) -> list[SOPVersionRecord]:
        """Ensure baseline active SOPs exist for all 5 domains using 4-eyes distinct principals."""
        if author_id == approver_id:
            raise FourEyesViolationError("Bootstrap author_id and approver_id must be distinct")

        created: list[SOPVersionRecord] = []
        for domain, (title, nl_text, graph) in DEFAULT_SOPS.items():
            sop_id = f"sop-{domain}"
            existing = self.get_active_sop(domain)
            if existing is not None:
                created.append(existing)
                continue
            draft = self.create_sop_draft(
                sop_id=sop_id,
                domain=domain,
                title=title,
                author_id=author_id,
                natural_language_text=nl_text,
                graph=graph,
            )
            active = self.approve_sop_version(
                sop_id=sop_id,
                version_num=draft.version_num,
                approver_id=approver_id,
            )
            created.append(active)
        return created

    def create_sop_draft(
        self,
        *,
        domain: SOPDomain,
        title: str,
        author_id: str,
        natural_language_text: str,
        sop_id: str | None = None,
        graph: PolicyGraphConfig | None = None,
    ) -> SOPVersionRecord:
        if not author_id or not author_id.strip():
            raise AuthorityViolationError("author_id is required to author an SOP draft")

        resolved_id = sop_id or f"sop-{domain}"
        compiled_graph = graph or compile_natural_language_sop(domain, natural_language_text)
        now = iso_utc()

        with self.db.immediate_transaction() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(version_num), 0) AS max_ver FROM sop_versions WHERE sop_id = ?",
                (resolved_id,),
            ).fetchone()
            next_ver = int(row["max_ver"]) + 1
            pol_ver = _compute_policy_version(resolved_id, next_ver, compiled_graph)
            conn.execute(
                """
                INSERT INTO sop_versions (
                    sop_id, version_num, policy_version, domain, title, status,
                    author_id, approver_id, natural_language_text, definition_json,
                    created_at, approved_at
                ) VALUES (?, ?, ?, ?, ?, 'draft', ?, NULL, ?, ?, ?, NULL)
                """,
                (
                    resolved_id,
                    next_ver,
                    pol_ver,
                    domain,
                    title,
                    author_id.strip(),
                    natural_language_text,
                    jcs_str(compiled_graph.model_dump(mode="json")),
                    now,
                ),
            )
            self.db.append_audit(
                event_kind="sop_draft_created",
                actor=author_id.strip(),
                policy_version=pol_ver,
                payload={"sop_id": resolved_id, "version_num": next_ver, "domain": domain},
                conn=conn,
            )

        return SOPVersionRecord(
            sop_id=resolved_id,
            version_num=next_ver,
            policy_version=pol_ver,
            domain=domain,
            title=title,
            status="draft",
            author_id=author_id.strip(),
            approver_id=None,
            natural_language_text=natural_language_text,
            graph=compiled_graph,
            created_at=now,
            approved_at=None,
        )

    def approve_sop_version(
        self,
        *,
        sop_id: str,
        version_num: int,
        approver_id: str,
    ) -> SOPVersionRecord:
        """Promote `draft -> active` enforcing draft-only promotion and strict 4-eyes separation (`author_id != approver_id`)."""
        clean_approver = approver_id.strip() if approver_id else ""
        if not clean_approver:
            raise AuthorityViolationError("approver_id is required to approve an SOP version")

        with self.db.read_connection() as conn:
            existing = conn.execute(
                "SELECT * FROM sop_versions WHERE sop_id = ? AND version_num = ?",
                (sop_id, int(version_num)),
            ).fetchone()
        if existing is None:
            raise KlaintError(f"SOP version {sop_id} v{version_num} not found")

        if str(existing["status"]) != "draft":
            raise KlaintError(
                f"Only draft SOP versions can be approved (got status={existing['status']!r} for {sop_id} v{version_num})"
            )

        author_id = str(existing["author_id"])
        if author_id == clean_approver:
            # Commit 4-eyes rejection audit outside any rolled-back transaction so the security event persists!
            self.db.append_audit(
                event_kind="sop_four_eyes_rejected",
                actor=clean_approver,
                policy_version=str(existing["policy_version"]),
                payload={
                    "sop_id": sop_id,
                    "version_num": int(version_num),
                    "author_id": author_id,
                    "approver_id": clean_approver,
                },
            )
            raise FourEyesViolationError(
                f"4-eyes violation: author {author_id!r} cannot self-approve {sop_id} v{version_num}"
            )

        now = iso_utc()
        with self.db.immediate_transaction() as conn:
            row = conn.execute(
                "SELECT * FROM sop_versions WHERE sop_id = ? AND version_num = ?",
                (sop_id, int(version_num)),
            ).fetchone()
            if row is None or str(row["status"]) != "draft":
                raise KlaintError(f"SOP version {sop_id} v{version_num} is no longer in draft state")

            domain = str(row["domain"])
            conn.execute(
                "UPDATE sop_versions SET status = 'archived' WHERE domain = ? AND status = 'active'",
                (domain,),
            )
            conn.execute(
                """
                UPDATE sop_versions
                SET status = 'active', approver_id = ?, approved_at = ?
                WHERE sop_id = ? AND version_num = ?
                """,
                (clean_approver, now, sop_id, int(version_num)),
            )
            self.db.append_audit(
                event_kind="sop_version_approved",
                actor=clean_approver,
                policy_version=str(row["policy_version"]),
                payload={
                    "sop_id": sop_id,
                    "version_num": int(version_num),
                    "author_id": author_id,
                    "approver_id": clean_approver,
                },
                conn=conn,
            )
            updated = conn.execute(
                "SELECT * FROM sop_versions WHERE sop_id = ? AND version_num = ?",
                (sop_id, int(version_num)),
            ).fetchone()

        return self._row_to_record(updated)

    def rollback_sop(
        self,
        *,
        sop_id: str,
        target_version_num: int,
        operator_id: str,
    ) -> SOPVersionRecord:
        """Instant 1-click rollback to a previously 4-eyes-approved SOP version."""
        clean_op = operator_id.strip()
        if not clean_op:
            raise AuthorityViolationError("operator_id is required for SOP rollback")

        with self.db.immediate_transaction() as conn:
            target = conn.execute(
                "SELECT * FROM sop_versions WHERE sop_id = ? AND version_num = ?",
                (sop_id, int(target_version_num)),
            ).fetchone()
            if target is None:
                raise KlaintError(f"Target SOP version {sop_id} v{target_version_num} does not exist")
            if target["approver_id"] is None:
                raise AuthorityViolationError(
                    f"Cannot roll back to unapproved draft {sop_id} v{target_version_num}"
                )

            domain = str(target["domain"])
            conn.execute(
                "UPDATE sop_versions SET status = 'archived' WHERE domain = ? AND status = 'active'",
                (domain,),
            )
            conn.execute(
                "UPDATE sop_versions SET status = 'active' WHERE sop_id = ? AND version_num = ?",
                (sop_id, int(target_version_num)),
            )
            self.db.append_audit(
                event_kind="sop_rolled_back",
                actor=clean_op,
                policy_version=str(target["policy_version"]),
                payload={"sop_id": sop_id, "restored_version_num": int(target_version_num)},
                conn=conn,
            )
            restored = conn.execute(
                "SELECT * FROM sop_versions WHERE sop_id = ? AND version_num = ?",
                (sop_id, int(target_version_num)),
            ).fetchone()

        return self._row_to_record(restored)

    def get_active_sop(self, domain: SOPDomain) -> SOPVersionRecord | None:
        with self.db.read_connection() as conn:
            row = conn.execute(
                "SELECT * FROM sop_versions WHERE domain = ? AND status = 'active' ORDER BY version_num DESC LIMIT 1",
                (domain,),
            ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def list_sop_versions(self, sop_id: str | None = None) -> list[SOPVersionRecord]:
        with self.db.read_connection() as conn:
            if sop_id:
                rows = conn.execute(
                    "SELECT * FROM sop_versions WHERE sop_id = ? ORDER BY version_num DESC",
                    (sop_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM sop_versions ORDER BY sop_id ASC, version_num DESC"
                ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def evaluate(
        self,
        *,
        session: AuthenticatedSession,
        domain: SOPDomain,
        action_class: ActionClass,
        facts: dict[str, Any],
        human_present: bool = True,
        operator_confirmation: PolicyConfirmation | None = None,
    ) -> PolicyVerdict:
        """Deterministically evaluate the active SOP graph for `domain` against server-verified `facts`."""
        active = self.get_active_sop(domain)
        if active is None:
            self.bootstrap_defaults()
            active = self.get_active_sop(domain)
            if active is None:
                raise KlaintError(f"Failed to bootstrap active SOP for domain {domain!r}")

        cfg = active.graph
        rule_ids: list[str] = []
        reason = ""
        decision: PolicyDecision

        if domain == "refund":
            order_verified = bool(facts.get("order_verified", False))
            order_status = str(facts.get("order_status", ""))
            amount_cents = int(facts.get("amount_cents", 0))
            days_since_delivery = int(facts.get("days_since_delivery", 999))

            if not order_verified:
                decision = PolicyDecision.DENY
                rule_ids = ["sop.refund.deny_unverified_order"]
                reason = "Order was not found under authenticated customer account."
            elif order_status == "refunded":
                decision = PolicyDecision.DENY
                rule_ids = ["sop.refund.deny_already_refunded"]
                reason = "Order has already been refunded."
            elif days_since_delivery > cfg.return_window_days:
                decision = PolicyDecision.DENY
                rule_ids = ["sop.refund.deny_outside_return_window"]
                reason = f"Delivery age ({days_since_delivery}d) exceeds {cfg.return_window_days}-day return window."
            elif amount_cents <= 0:
                decision = PolicyDecision.DENY
                rule_ids = ["sop.refund.deny_invalid_amount"]
                reason = "Refund amount must be positive."
            elif amount_cents <= cfg.auto_allow_max_cents:
                decision = PolicyDecision.ALLOW
                rule_ids = ["sop.refund.auto_allow_threshold"]
                reason = f"Verified order within {cfg.return_window_days}d and amount {amount_cents} <= {cfg.auto_allow_max_cents} cents."
            elif amount_cents <= cfg.ask_max_cents:
                decision = PolicyDecision.ASK
                rule_ids = ["sop.refund.ask_operator_threshold"]
                reason = f"Refund {amount_cents} cents falls in operator-approval band ({cfg.auto_allow_max_cents + 1}..{cfg.ask_max_cents})."
            else:
                decision = PolicyDecision.DENY
                rule_ids = ["sop.refund.deny_above_max_threshold"]
                reason = f"Refund {amount_cents} cents exceeds maximum automated/operator tier ({cfg.ask_max_cents} cents)."

        elif domain == "shipping_delay":
            shipment_verified = bool(facts.get("shipment_verified", False))
            delay_days = int(facts.get("delay_days", 0))
            status = str(facts.get("shipment_status", ""))
            if not shipment_verified:
                decision = PolicyDecision.DENY
                rule_ids = ["sop.shipping.deny_unverified_shipment"]
                reason = "No matching shipment found for authenticated customer."
            elif status == "delivered":
                decision = PolicyDecision.DENY
                rule_ids = ["sop.shipping.deny_already_delivered"]
                reason = "Shipment is already marked delivered."
            elif delay_days >= cfg.min_delay_days_for_expedite:
                decision = PolicyDecision.ALLOW
                rule_ids = ["sop.shipping.allow_expedite_delayed"]
                reason = f"Carrier delay {delay_days}d >= {cfg.min_delay_days_for_expedite}d threshold."
            else:
                decision = PolicyDecision.ASK
                rule_ids = ["sop.shipping.ask_below_delay_threshold"]
                reason = f"Carrier delay {delay_days}d is below {cfg.min_delay_days_for_expedite}d auto-expedite threshold."

        elif domain == "booking_change":
            booking_verified = bool(facts.get("booking_verified", False))
            hours_until_slot = int(facts.get("hours_until_slot", 0))
            fee_cents = int(facts.get("fee_cents", 0))
            if not booking_verified:
                decision = PolicyDecision.DENY
                rule_ids = ["sop.booking.deny_unverified_booking"]
                reason = "Booking not found under authenticated customer."
            elif hours_until_slot >= cfg.min_booking_notice_hours and fee_cents <= cfg.max_booking_fee_cents:
                decision = PolicyDecision.ALLOW
                rule_ids = ["sop.booking.allow_within_notice_window"]
                reason = f"Booking modification has {hours_until_slot}h notice (>= {cfg.min_booking_notice_hours}h)."
            else:
                decision = PolicyDecision.ASK
                rule_ids = ["sop.booking.ask_short_notice"]
                reason = f"Booking modification inside {cfg.min_booking_notice_hours}h window requires operator review."

        elif domain == "account_recovery":
            account_verified = bool(facts.get("account_verified", False))
            requested_tool = str(facts.get("tool", "accounts.unlock_account"))
            if not account_verified:
                decision = PolicyDecision.DENY
                rule_ids = ["sop.account.deny_unverified_account"]
                reason = "Account not found under authenticated customer."
            elif cfg.require_step_up and not session.step_up_verified:
                decision = PolicyDecision.DENY
                rule_ids = ["sop.account.deny_missing_step_up"]
                reason = "Out-of-band step-up verification is required before account recovery."
            elif requested_tool == "accounts.reset_mfa" and not cfg.allow_mfa_reset_auto:
                decision = PolicyDecision.ASK
                rule_ids = ["sop.account.ask_mfa_reset"]
                reason = "MFA reset always requires human security operator approval."
            else:
                decision = PolicyDecision.ALLOW
                rule_ids = ["sop.account.allow_verified_unlock"]
                reason = "Step-up verified session authorized to unlock account."

        else:  # escalation
            decision = PolicyDecision.ASK if human_present else PolicyDecision.DENY
            rule_ids = ["sop.escalation.route_to_human"]
            reason = str(facts.get("reason", "Conversation escalated to human operator."))

        enforced: Literal["ALLOW", "ASK", "DENY"]
        confirmation = operator_confirmation
        if decision == PolicyDecision.ALLOW:
            enforced = "ALLOW"
        elif decision == PolicyDecision.ASK:
            if confirmation is not None and human_present:
                enforced = "ALLOW"
            elif human_present:
                enforced = "ASK"
            else:
                enforced = "DENY"
        else:
            enforced = "DENY"

        inputs_digest = compute_args_digest(
            {
                "domain": domain,
                "action_class": action_class.value,
                "principal": session.principal_scope_ref,
                "step_up": session.step_up_verified,
                "facts": facts,
            }
        )

        return PolicyVerdict(
            verdict_id=new_id("vrd", 10),
            request_id=new_id("req", 10),
            epoch=session.ownership_epoch,
            candidate_decision=decision,
            enforced_decision=enforced,
            human_present=human_present,
            action_class=action_class,
            rule_ids=rule_ids,
            layers=_build_monotone_layers(decision),
            policy_version=active.policy_version,
            inputs_digest=inputs_digest,
            principal_scope_ref=session.principal_scope_ref,
            reason=reason,
            confirmation=confirmation,
        )

    @staticmethod
    def _row_to_record(row: Any) -> SOPVersionRecord:
        return SOPVersionRecord(
            sop_id=str(row["sop_id"]),
            version_num=int(row["version_num"]),
            policy_version=str(row["policy_version"]),
            domain=row["domain"],
            title=str(row["title"]),
            status=row["status"],
            author_id=str(row["author_id"]),
            approver_id=row["approver_id"],
            natural_language_text=str(row["natural_language_text"]),
            graph=PolicyGraphConfig.model_validate(json.loads(str(row["definition_json"]))),
            created_at=str(row["created_at"]),
            approved_at=row["approved_at"],
        )
