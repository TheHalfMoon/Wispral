# SPDX-License-Identifier: Apache-2.0
"""BLOCK / clause-buffered Commitment Output Gate covering English and Arabic commitment claims.

Blocks or rewrites any assistant response claiming an external state change unless a committed
`settled` (or `reconciled: effect_present`) `action_ledger` receipt exists for `(tenant_id, session_id, action_class)`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from klaint.core.arabic import contains_arabic, normalize_arabic
from klaint.core.errors import TenantIsolationError
from klaint.core.models import ActionClass, AuthenticatedSession, validate_tenant_id
from klaint.storage.tenant_db import TenantDatabase

_EN_NEGATION_PREFIX = re.compile(
    r"\b(?:not|never|cannot|can't|couldn't|unable\s+to|haven't|hasn't|will\s+not|won't|no|without)\s+"
    r"(?:been\s+|yet\s+|be\s+)?$",
    re.IGNORECASE,
)
_AR_NEGATION_PREFIX = re.compile(r"(?:لم|لن|لا|غير|دون|بدون|ما)\s+(?:يتم\s+|نقم\s+)?$")

_ENTITY_ID_RE = re.compile(r"\b((?:ord|bkg|shp|acc)-[A-Za-z0-9_-]+)\b", re.IGNORECASE)

# (claim_label, ActionClass, tool_prefix, compiled_regex, normalized_arabic_mode)
_COMMITMENT_RULES: tuple[tuple[str, ActionClass, str, re.Pattern[str], bool], ...] = (
    (
        "en_refund_committed",
        ActionClass.MONEY,
        "refunds.",
        re.compile(
            r"\b(?:issued\s+(?:a|your)\s+refund|processed\s+(?:a|your)\s+refund|refunded(?:\s+your)?|"
            r"refund\s+has\s+been\s+(?:issued|processed|sent)|credited\s+back\s+your|"
            r"(?:i|we)\s+will\s+refund|(?:i'll|we'll)\s+refund|"
            r"(?:i|we)\s+will\s+(?:issue|process)\s+(?:a|your)\s+refund)\b",
            re.IGNORECASE,
        ),
        False,
    ),
    (
        "en_order_cancelled",
        ActionClass.REVERSIBLE_WRITE,
        "orders.cancel_order",
        re.compile(
            r"\b(?:cancell?ed\s+your\s+order|cancell?ed\s+order\b|order\s+has\s+been\s+cancell?ed|"
            r"order\s+#?[A-Za-z0-9_-]+\s+is\s+now\s+cancell?ed|"
            r"(?:i|we)\s+will\s+cancel\s+(?:your\s+)?order|(?:i'll|we'll)\s+cancel\s+(?:your\s+)?order)\b",
            re.IGNORECASE,
        ),
        False,
    ),
    (
        "en_shipment_expedited",
        ActionClass.REVERSIBLE_WRITE,
        "shipments.expedite_shipment",
        re.compile(
            r"\b(?:expedited\s+your\s+shipment|upgraded\s+your\s+shipping|shipment\s+has\s+been\s+expedited|"
            r"(?:i|we)\s+will\s+expedite\s+your\s+shipment)\b",
            re.IGNORECASE,
        ),
        False,
    ),
    (
        "en_booking_committed",
        ActionClass.REVERSIBLE_WRITE,
        "bookings.",
        re.compile(
            r"\b(?:rescheduled\s+your\s+booking|changed\s+your\s+booking|cancell?ed\s+your\s+booking|"
            r"confirmed\s+your\s+booking|booked\s+your\s+(?:appointment|slot)|booking\s+is\s+confirmed|"
            r"(?:i|we)\s+will\s+(?:book|reschedule|cancel)\s+your\s+(?:booking|appointment))\b",
            re.IGNORECASE,
        ),
        False,
    ),
    (
        "en_account_committed",
        ActionClass.CREDENTIAL_USE,
        "accounts.",
        re.compile(
            r"\b(?:unlocked\s+your\s+account|account\s+has\s+been\s+unlocked|reset\s+your\s+mfa|"
            r"(?:i|we)\s+will\s+(?:unlock|reset)\s+your\s+(?:account|mfa))\b",
            re.IGNORECASE,
        ),
        False,
    ),
    # Level-3 normalized Arabic commitment patterns (past + future-tense commitments)
    (
        "ar_refund_committed",
        ActionClass.MONEY,
        "refunds.",
        re.compile(
            r"(?:تم\s+استرداد|اعدنا\s+المبلغ|تم\s+ارجاع\s+المبلغ|تم\s+رد\s+المبلغ|"
            r"قمنا\s+باسترداد|تم\s+تحويل\s+مبلغ\s+الاسترداد|"
            r"ساقوم\s+باسترداد|سنقوم\s+باسترداد|سوف\s+نعيد\s+المبلغ|سنعيد\s+المبلغ|سيتم\s+استرداد)"
        ),
        True,
    ),
    (
        "ar_order_cancelled",
        ActionClass.REVERSIBLE_WRITE,
        "orders.cancel_order",
        re.compile(
            r"(?:تم\s+الغاء\s+الطلب|تم\s+الغاء\s+طلبك|الغينا\s+الطلب|الغينا\s+طلبك|"
            r"ساقوم\s+بالغاء|سنقوم\s+بالغاء|سوف\s+نلغي\s+الطلب|سنلغي\s+الطلب|سيتم\s+الغاء\s+الطلب)"
        ),
        True,
    ),
    (
        "ar_shipment_expedited",
        ActionClass.REVERSIBLE_WRITE,
        "shipments.expedite_shipment",
        re.compile(r"(?:تم\s+تسريع\s+الشحنه|سرعنا\s+الشحنه|ساقوم\s+بتسريع\s+الشحنه|سنقوم\s+بتسريع\s+الشحنه)"),
        True,
    ),
    (
        "ar_booking_committed",
        ActionClass.REVERSIBLE_WRITE,
        "bookings.",
        re.compile(
            r"(?:تم\s+الحجز|تم\s+تاكيد\s+الحجز|تم\s+تعديل\s+الحجز|تم\s+الغاء\s+الحجز|حجزنا\s+لك|"
            r"ساقوم\s+بتعديل\s+الحجز|سنقوم\s+بتعديل\s+الحجز|سنقوم\s+بالحجز|سيتم\s+الحجز)"
        ),
        True,
    ),
    (
        "ar_account_committed",
        ActionClass.CREDENTIAL_USE,
        "accounts.",
        re.compile(
            r"(?:تم\s+فتح\s+حسابك|تم\s+فتح\s+الحساب|تم\s+استعاده\s+الحساب|"
            r"ساقوم\s+بفتح\s+حسابك|سنقوم\s+بفتح\s+حسابك)"
        ),
        True,
    ),
)

_SAFE_REPLACEMENT_EN = (
    "I have not completed that external action yet. Let me verify the policy status or connect you with a team member."
)
_SAFE_REPLACEMENT_AR = (
    "لم يتم تنفيذ هذا الإجراء الفعلي في النظام بعد. دعني أتحقق من حالة الطلب وفق السياسة أو أحولك إلى أحد المختصين."
)


@dataclass(frozen=True)
class DetectedCommitment:
    label: str
    action_class: ActionClass
    tool_prefix: str
    matched_span: str


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    output_text: str
    detected_claims: list[str]
    blocked_claims: list[str]
    receipt_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "output_text": self.output_text,
            "detected_claims": list(self.detected_claims),
            "blocked_claims": list(self.blocked_claims),
            "receipt_ids": list(self.receipt_ids),
        }


def detect_commitments(text: str) -> list[DetectedCommitment]:
    """Scan `text` (both raw English and Level-3 normalized Arabic) for affirmative commitment claims."""
    found: list[DetectedCommitment] = []
    norm_ar = normalize_arabic(text, level=3)

    for label, act_cls, tool_prefix, pattern, is_ar in _COMMITMENT_RULES:
        haystack = norm_ar if is_ar else text
        for match in pattern.finditer(haystack):
            prefix_window = haystack[max(0, match.start() - 28) : match.start()]
            neg_re = _AR_NEGATION_PREFIX if is_ar else _EN_NEGATION_PREFIX
            if neg_re.search(prefix_window):
                continue
            found.append(
                DetectedCommitment(
                    label=label,
                    action_class=act_cls,
                    tool_prefix=tool_prefix,
                    matched_span=match.group(0),
                )
            )
    return found


def split_into_clauses(text: str) -> list[str]:
    """Split text into deterministic clause units for clause-buffered voice/text gating."""
    parts = [p.strip() for p in re.split(r"(?<=[.!?;،؟\n])\s+", text.strip()) if p.strip()]
    return parts if parts else ([text.strip()] if text.strip() else [])


class CommitmentOutputGate:
    """Deterministic BLOCK / clause-buffered output gate backed by per-tenant `action_ledger` receipts."""

    def __init__(self, db: TenantDatabase) -> None:
        self.db = db

    def _find_committed_receipt(
        self,
        session: AuthenticatedSession,
        action_class: ActionClass,
        tool_prefix: str,
        *,
        allowed_receipt_ids: set[str] | None = None,
        target_entities: set[str] | None = None,
    ) -> str | None:
        with self.db.read_connection() as conn:
            rows = conn.execute(
                """
                SELECT receipt_id, tool, args_json, state, reconciled_result
                FROM action_ledger
                WHERE tenant_id = ? AND session_id = ? AND customer_id = ? AND action_class = ?
                ORDER BY created_at DESC
                """,
                (self.db.tenant_id, session.session_id, session.customer_id, action_class.value),
            ).fetchall()

        for row in rows:
            rcp_id = str(row["receipt_id"])
            if allowed_receipt_ids is not None and rcp_id not in allowed_receipt_ids:
                continue
            state = str(row["state"])
            rec_res = row["reconciled_result"]
            is_committed = state == "settled" or (state == "reconciled" and rec_res == "effect_present")
            if not is_committed:
                continue
            tool = str(row["tool"])
            if not tool.startswith(tool_prefix):
                continue
            if target_entities:
                try:
                    args_dict = json.loads(str(row["args_json"]))
                except json.JSONDecodeError:
                    args_dict = {}
                row_entities = {
                    str(args_dict.get(k, "")).lower()
                    for k in ("order_id", "booking_id", "shipment_id", "account_id")
                    if args_dict.get(k)
                }
                if not (target_entities & row_entities):
                    continue
            return rcp_id
        return None

    def evaluate(
        self,
        *,
        session: AuthenticatedSession,
        draft_text: str,
        mode: str = "BLOCK",
        turn_receipt_ids: list[str] | tuple[str, ...] | None = None,
    ) -> GateDecision:
        """Evaluate a full BLOCK response draft against committed `action_ledger` receipts."""
        if mode != "BLOCK":
            raise ValueError(
                f"CommitmentOutputGate requires BLOCK or clause-buffered evaluation (got {mode!r}); "
                "unbuffered token STREAM mode cannot intercept premature commitments."
            )

        validate_tenant_id(session.tenant_id)
        if session.tenant_id != self.db.tenant_id:
            raise TenantIsolationError("Session tenant_id does not match CommitmentOutputGate database")

        claims = detect_commitments(draft_text)
        if not claims:
            return GateDecision(
                allowed=True,
                output_text=draft_text,
                detected_claims=[],
                blocked_claims=[],
                receipt_ids=[],
            )

        allowed_set = set(turn_receipt_ids) if turn_receipt_ids is not None else None
        mentioned_entities = {m.group(1).lower() for m in _ENTITY_ID_RE.finditer(draft_text)}
        detected_labels = [c.label for c in claims]
        blocked_labels: list[str] = []
        receipt_ids: list[str] = []

        for claim in claims:
            rcp = self._find_committed_receipt(
                session,
                claim.action_class,
                claim.tool_prefix,
                allowed_receipt_ids=allowed_set,
                target_entities=mentioned_entities or None,
            )
            if rcp is None:
                blocked_labels.append(claim.label)
            elif rcp not in receipt_ids:
                receipt_ids.append(rcp)

        if blocked_labels:
            is_ar = contains_arabic(draft_text) or session.language.startswith("ar")
            replacement = _SAFE_REPLACEMENT_AR if is_ar else _SAFE_REPLACEMENT_EN
            self.db.append_audit(
                event_kind="commitment_gate_blocked",
                actor="commitment_output_gate",
                session_id=session.session_id,
                payload={
                    "blocked_claims": blocked_labels,
                    "draft_preview": draft_text[:160],
                },
            )
            return GateDecision(
                allowed=False,
                output_text=replacement,
                detected_claims=detected_labels,
                blocked_claims=blocked_labels,
                receipt_ids=[],
            )

        # Cite verified ledger receipt ID if not already cited in the outgoing text
        final_text = draft_text
        primary_rcp = receipt_ids[0]
        if primary_rcp not in final_text:
            final_text = f"{draft_text.rstrip()} [Receipt: {primary_rcp}]"

        return GateDecision(
            allowed=True,
            output_text=final_text,
            detected_claims=detected_labels,
            blocked_claims=[],
            receipt_ids=receipt_ids,
        )

    def evaluate_clauses(
        self,
        *,
        session: AuthenticatedSession,
        text: str,
        turn_receipt_ids: list[str] | tuple[str, ...] | None = None,
    ) -> list[GateDecision]:
        """Clause-buffered evaluation used by voice TTS rendering (`klaint.voice.omalla_bridge`)."""
        clauses = split_into_clauses(text)
        decisions: list[GateDecision] = []
        for clause in clauses:
            decision = self.evaluate(
                session=session,
                draft_text=clause,
                mode="BLOCK",
                turn_receipt_ids=turn_receipt_ids,
            )
            decisions.append(decision)
            if not decision.allowed:
                # Halt remaining clauses on first unbacked commitment
                break
        return decisions
