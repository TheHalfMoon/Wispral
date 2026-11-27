# SPDX-License-Identifier: Apache-2.0
"""8-Stage Deterministic Resolution Engine (`klaint.resolution`).

Explicit state machine:
  IDENTIFY -> INVESTIGATE -> UNDERSTAND -> DECIDE -> AUTHORIZE -> EXECUTE -> VERIFY -> RESOLVE
with `AWAITING_APPROVAL` and `ESCALATED` branches, structured per-stage traces (powering the Studio "Why" panel),
synthetic business connector wiring, Hybrid RAG citations, out-of-process broker dispatch, and Commitment Output Gate.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Callable

from klaint.broker.client import BrokerClient
from klaint.connectors.business import TOOL_ACTION_CLASS, BusinessConnectorSuite
from klaint.conversation.gate import CommitmentOutputGate, GateDecision
from klaint.core.arabic import contains_arabic, detect_language_variety, normalize_arabic, normalize_digits
from klaint.core.errors import AuthorityViolationError, StaleEpochError, TenantIsolationError
from klaint.core.jcs import jcs_str
from klaint.core.models import (
    ActionClass,
    AuthenticatedSession,
    PolicyConfirmation,
    PolicyVerdict,
    iso_utc,
    new_id,
    reject_forged_identity_args,
    validate_tenant_id,
)
from klaint.knowledge.rag import HybridKnowledgeEngine, KnowledgeSearchResult, KnowledgeStatus
from klaint.procedures.engine import ProceduresEngine, SOPDomain
from klaint.storage.tenant_db import TenantStorageRegistry


class ResolutionStage(StrEnum):
    IDENTIFY = "IDENTIFY"
    INVESTIGATE = "INVESTIGATE"
    UNDERSTAND = "UNDERSTAND"
    DECIDE = "DECIDE"
    AUTHORIZE = "AUTHORIZE"
    EXECUTE = "EXECUTE"
    VERIFY = "VERIFY"
    RESOLVE = "RESOLVE"


STAGE_ORDER: tuple[ResolutionStage, ...] = (
    ResolutionStage.IDENTIFY,
    ResolutionStage.INVESTIGATE,
    ResolutionStage.UNDERSTAND,
    ResolutionStage.DECIDE,
    ResolutionStage.AUTHORIZE,
    ResolutionStage.EXECUTE,
    ResolutionStage.VERIFY,
    ResolutionStage.RESOLVE,
)


@dataclass(frozen=True)
class StageStepTrace:
    stage: ResolutionStage
    status: str
    summary: str
    details: dict[str, Any]
    duration_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage.value,
            "status": self.status,
            "summary": self.summary,
            "details": self.details,
            "duration_ms": self.duration_ms,
        }


@dataclass(frozen=True)
class ResolutionTurnResult:
    turn_id: str
    conversation_id: str
    tenant_id: str
    session_id: str
    customer_id: str
    language_variety: str
    resolution_status: str
    assistant_text: str
    stages: list[StageStepTrace]
    policy_verdict: dict[str, Any] | None
    matched_rules: list[str]
    rag_status: str
    citations: list[dict[str, Any]]
    capability_token_id: str | None
    capability_args_digest: str | None
    receipt_ids: list[str]
    approval_id: str | None
    ownership_epoch: int
    latency_ms: int

    def to_why_panel(self) -> dict[str, Any]:
        """Structured explainability view consumed directly by Klaint Studio's 'Why' panel."""
        verdict_decision = (
            self.policy_verdict.get("enforced_decision", "READ_ONLY")
            if self.policy_verdict
            else "READ_ONLY"
        )
        localized_verdict = {
            "ALLOW": {"en": "Allowed", "ar": "مسموح"},
            "ASK": {"en": "Needs approval", "ar": "يحتاج موافقة"},
            "DENY": {"en": "Blocked", "ar": "مرفوض"},
            "READ_ONLY": {"en": "Informational", "ar": "معلوماتي"},
        }.get(verdict_decision, {"en": "Blocked", "ar": "مرفوض"})

        return {
            "turn_id": self.turn_id,
            "plain_summary": self.stages[-1].summary if self.stages else self.resolution_status,
            "resolution_status": self.resolution_status,
            "verdict_chip": localized_verdict,
            "matched_rules": self.matched_rules,
            "policy_verdict": self.policy_verdict,
            "rag_status": self.rag_status,
            "citations": self.citations,
            "capability_token_id": self.capability_token_id,
            "capability_args_digest": self.capability_args_digest,
            "receipt_ids": self.receipt_ids,
            "approval_id": self.approval_id,
            "ownership_epoch": self.ownership_epoch,
            "stages": [s.to_dict() for s in self.stages],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "conversation_id": self.conversation_id,
            "tenant_id": self.tenant_id,
            "session_id": self.session_id,
            "customer_id": self.customer_id,
            "language_variety": self.language_variety,
            "resolution_status": self.resolution_status,
            "assistant_text": self.assistant_text,
            "stages": [s.to_dict() for s in self.stages],
            "policy_verdict": self.policy_verdict,
            "matched_rules": self.matched_rules,
            "rag_status": self.rag_status,
            "citations": self.citations,
            "capability_token_id": self.capability_token_id,
            "capability_args_digest": self.capability_args_digest,
            "receipt_ids": self.receipt_ids,
            "approval_id": self.approval_id,
            "ownership_epoch": self.ownership_epoch,
            "latency_ms": self.latency_ms,
            "why": self.to_why_panel(),
        }


_INJECTION_RE = re.compile(
    r"(?:ignore\s+(?:all\s+)?(?:previous|prior|sops?|policies|instructions|rules)|"
    r"system\s+override|developer\s+mode|bypass\s+policy|i\s+am\s+the\s+ceo|i\s+am\s+admin|"
    r"تجاهل\s+(?:كل|جميع)\s+(?:السياسات|التعليمات)|انا\s+المدير\s+التنفيذي|تجاوز\s+النظام)",
    re.IGNORECASE,
)
_ORDER_ID_RE = re.compile(r"\b(ord-[A-Za-z0-9_-]+)\b", re.IGNORECASE)
_BOOKING_ID_RE = re.compile(r"\b(bkg-[A-Za-z0-9_-]+)\b", re.IGNORECASE)
_SHIPMENT_ID_RE = re.compile(r"\b(shp-[A-Za-z0-9_-]+)\b", re.IGNORECASE)
_DOLLAR_RE = re.compile(r"\$\s*(\d+)(?:\.(\d{1,2}))?")
_CENTS_RE = re.compile(r"\b(\d+)\s*cents\b", re.IGNORECASE)
_CURRENCY_NUM_RE = re.compile(r"\b(\d+)\s*(?:usd|dollars?|sar|ريال|دولار|جنيه)\b", re.IGNORECASE)


def _extract_requested_cents(text: str) -> int | None:
    norm = normalize_digits(text)
    m_cents = _CENTS_RE.search(norm)
    if m_cents:
        return int(m_cents.group(1))
    m_dollar = _DOLLAR_RE.search(norm)
    if m_dollar:
        whole = int(m_dollar.group(1))
        frac_str = (m_dollar.group(2) or "0").ljust(2, "0")
        return whole * 100 + int(frac_str)
    m_cur = _CURRENCY_NUM_RE.search(norm)
    if m_cur:
        return int(m_cur.group(1)) * 100
    return None


def _classify_intent(text: str) -> tuple[SOPDomain | Literal["knowledge_query"], str | None]:
    norm = normalize_arabic(text, level=3)
    lower = normalize_digits(text).lower()

    # Explicit human escalation requests
    if any(
        kw in lower or kw in norm
        for kw in (
            "talk to a human",
            "speak to a person",
            "human agent",
            "live operator",
            "اريد التحدث مع موظف",
            "حولني لموظف",
            "عميل بشري",
            "موظف خدمة",
        )
    ):
        return "escalation", None

    # Refund intent (EN + MSA + Gulf + EG + Levantine + code-switch)
    if any(
        kw in lower or kw in norm
        for kw in (
            "refund",
            "money back",
            "return my order",
            "استرداد",
            "ترجيع",
            "ارجاع",
            "رد المبلغ",
            "فلوسي",
            "مصاري",
            "ابغى ارجع",
            "ابي ارجع",
            "عايز ارجع",
            "بدي ارجع",
        )
    ):
        return "refund", "refunds.issue_refund"

    # Cancel order intent
    if any(
        kw in lower or kw in norm
        for kw in ("cancel order", "cancel my order", "الغاء الطلب", "الغاء طلبي", "الغي الطلب", "كنسل الطلب")
    ):
        return "refund", "orders.cancel_order"

    # Shipping delay intent
    if any(
        kw in lower or kw in norm
        for kw in (
            "shipment",
            "shipping delay",
            "delayed",
            "where is my package",
            "expedite",
            "شحنه",
            "الشحن",
            "متاخره",
            "تاخير",
            "تاخرت",
            "وين الطلبيه",
            "فين الاوردر",
            "وين طلبي",
        )
    ):
        return "shipping_delay", "shipments.expedite_shipment"

    # Booking change intent
    if any(
        kw in lower or kw in norm
        for kw in (
            "reschedule",
            "booking",
            "appointment",
            "change slot",
            "حجز",
            "موعد",
            "تعديل الحجز",
            "تغيير الموعد",
            "اجل الموعد",
        )
    ):
        return "booking_change", "bookings.reschedule_booking"

    # Account recovery intent
    if any(
        kw in lower or kw in norm
        for kw in (
            "unlock",
            "locked out",
            "account recovery",
            "reset mfa",
            "حسابي مقفل",
            "فتح الحساب",
            "استعاده الحساب",
            "مقفل",
        )
    ):
        tool = "accounts.reset_mfa" if ("mfa" in lower or "مصادقه" in norm) else "accounts.unlock_account"
        return "account_recovery", tool

    return "knowledge_query", None


class ResolutionEngine:
    """Deterministic 8-stage customer resolution state machine."""

    def __init__(
        self,
        *,
        storage: TenantStorageRegistry,
        broker: BrokerClient,
    ) -> None:
        self.storage = storage
        self.broker = broker

    def ensure_conversation(self, session: AuthenticatedSession, recontact_of: str | None = None) -> dict[str, Any]:
        db = self.storage.for_tenant(session.tenant_id)
        now = iso_utc()
        with db.immediate_transaction() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE tenant_id = ? AND session_id = ?",
                (session.tenant_id, session.session_id),
            ).fetchone()
            if row is not None:
                return dict(row)
            conv_id = new_id("cnv", 10)
            conn.execute(
                """
                INSERT INTO conversations (
                    conversation_id, tenant_id, session_id, customer_id, channel,
                    language, owner_kind, assigned_operator_id, ownership_epoch,
                    status, recontact_of, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'ai_owned', NULL, ?, 'open', ?, ?, ?)
                """,
                (
                    conv_id,
                    session.tenant_id,
                    session.session_id,
                    session.customer_id,
                    session.channel,
                    session.language,
                    session.ownership_epoch,
                    recontact_of,
                    now,
                    now,
                ),
            )
            created = conn.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?",
                (conv_id,),
            ).fetchone()
            return dict(created)

    def resolve_turn(
        self,
        *,
        session: AuthenticatedSession,
        customer_text: str,
        explicit_tool_args: dict[str, Any] | None = None,
        draft_override: str | None = None,
        pre_commit_hook: Callable[[], None] | None = None,
    ) -> ResolutionTurnResult:
        """Run the full 8-stage deterministic resolution pipeline for a customer utterance."""
        turn_start = time.perf_counter()
        validate_tenant_id(session.tenant_id)
        if explicit_tool_args is not None:
            reject_forged_identity_args(explicit_tool_args, session)

        db = self.storage.for_tenant(session.tenant_id)
        procedures = ProceduresEngine(db)
        procedures.bootstrap_defaults()
        knowledge = HybridKnowledgeEngine(db)
        connectors = BusinessConnectorSuite(db)
        gate = CommitmentOutputGate(db)

        conv = self.ensure_conversation(session)
        conversation_id = str(conv["conversation_id"])
        active_epoch = int(conv["ownership_epoch"])
        if conv["owner_kind"] == "human_owned" or session.ownership_epoch != active_epoch:
            raise StaleEpochError(
                f"AI turn refused: conversation {conversation_id} is at ownership_epoch={active_epoch} "
                f"(owner={conv['owner_kind']}), turn carried epoch={session.ownership_epoch}"
            )

        stages: list[StageStepTrace] = []

        # ------------------------------------------------------------------
        # Stage 1: IDENTIFY
        # ------------------------------------------------------------------
        t0 = time.perf_counter()
        variety = detect_language_variety(customer_text)
        is_ar = contains_arabic(customer_text) or session.language.startswith("ar")
        injection_detected = bool(_INJECTION_RE.search(customer_text) or _INJECTION_RE.search(normalize_arabic(customer_text, 3)))
        spoofed_id_in_text = "customer_id" in customer_text.lower() or "cust-" in customer_text.lower()

        stages.append(
            StageStepTrace(
                stage=ResolutionStage.IDENTIFY,
                status="completed",
                summary=f"Authenticated customer {session.customer_id} in tenant {session.tenant_id} ({variety}).",
                details={
                    "tenant_id": session.tenant_id,
                    "customer_id": session.customer_id,
                    "session_id": session.session_id,
                    "step_up_verified": session.step_up_verified,
                    "language_variety": variety,
                    "prompt_injection_flagged": injection_detected,
                    "text_id_claim_ignored": spoofed_id_in_text,
                    "ownership_epoch": session.ownership_epoch,
                },
                duration_ms=max(1, int((time.perf_counter() - t0) * 1000)),
            )
        )

        # ------------------------------------------------------------------
        # Stage 2: INVESTIGATE
        # ------------------------------------------------------------------
        t0 = time.perf_counter()
        orders_list = connectors.read(session, "orders.list_orders", {})["orders"]
        account_info = connectors.read(session, "accounts.get_account", {})["account"]

        m_ord = _ORDER_ID_RE.search(customer_text)
        requested_order_id = (
            str(explicit_tool_args["order_id"])
            if explicit_tool_args and "order_id" in explicit_tool_args
            else (m_ord.group(1) if m_ord else (orders_list[0]["order_id"] if orders_list else None))
        )
        target_order: dict[str, Any] | None = None
        target_shipment: dict[str, Any] | None = None
        if requested_order_id:
            target_order = connectors.read(session, "orders.get_order", {"order_id": requested_order_id})["order"]
            target_shipment = connectors.read(session, "shipments.get_shipment", {"order_id": requested_order_id})["shipment"]

        m_shp = _SHIPMENT_ID_RE.search(customer_text)
        if target_shipment is None and m_shp:
            target_shipment = connectors.read(session, "shipments.get_shipment", {"shipment_id": m_shp.group(1)})["shipment"]

        m_bkg = _BOOKING_ID_RE.search(customer_text)
        requested_booking_id = (
            str(explicit_tool_args["booking_id"])
            if explicit_tool_args and "booking_id" in explicit_tool_args
            else (m_bkg.group(1) if m_bkg else None)
        )
        target_booking: dict[str, Any] | None = None
        if requested_booking_id:
            target_booking = connectors.read(session, "bookings.get_booking", {"booking_id": requested_booking_id})["booking"]

        rag_result: KnowledgeSearchResult = knowledge.search(session=session, query=customer_text, top_k=3)
        stages.append(
            StageStepTrace(
                stage=ResolutionStage.INVESTIGATE,
                status="completed",
                summary=f"Queried tenant connectors and RAG ({rag_result.status.value}, {len(rag_result.citations)} citations).",
                details={
                    "order_found": target_order is not None,
                    "order_id": requested_order_id,
                    "shipment_found": target_shipment is not None,
                    "booking_found": target_booking is not None,
                    "account_found": account_info is not None,
                    "rag_status": rag_result.status.value,
                    "citation_ids": [c.chunk_id for c in rag_result.citations],
                },
                duration_ms=max(1, int((time.perf_counter() - t0) * 1000)),
            )
        )

        # ------------------------------------------------------------------
        # Stage 3: UNDERSTAND
        # ------------------------------------------------------------------
        t0 = time.perf_counter()
        intent_domain, candidate_tool = _classify_intent(customer_text)
        parsed_cents = (
            int(explicit_tool_args["amount_cents"])
            if explicit_tool_args and "amount_cents" in explicit_tool_args
            else _extract_requested_cents(customer_text)
        )

        stages.append(
            StageStepTrace(
                stage=ResolutionStage.UNDERSTAND,
                status="completed",
                summary=f"Classified intent as {intent_domain!r} (tool={candidate_tool!r}).",
                details={
                    "intent_domain": intent_domain,
                    "candidate_tool": candidate_tool,
                    "parsed_amount_cents": parsed_cents,
                    "rag_epistemic_status": rag_result.status.value,
                },
                duration_ms=max(1, int((time.perf_counter() - t0) * 1000)),
            )
        )

        # ------------------------------------------------------------------
        # Stage 4: DECIDE
        # ------------------------------------------------------------------
        t0 = time.perf_counter()
        tool_args: dict[str, Any] = {}
        sop_facts: dict[str, Any] = {}
        verdict: PolicyVerdict | None = None
        decision_plan = "informational"

        if intent_domain == "escalation":
            sop_facts = {"reason": "Customer requested human specialist"}
            decision_plan = "escalate_human"
        elif intent_domain == "knowledge_query":
            if rag_result.status == KnowledgeStatus.UNAVAILABLE:
                decision_plan = "abstain_unavailable_escalate"
            elif rag_result.status == KnowledgeStatus.CONFIRMED_NEGATIVE:
                decision_plan = "answer_confirmed_negative"
            else:
                decision_plan = "answer_cited_knowledge"
        elif intent_domain == "refund":
            if candidate_tool == "orders.cancel_order":
                order_verified = target_order is not None
                order_total = int(target_order["total_cents"]) if target_order else 0
                days_age = int(target_order["days_since_delivery"]) if target_order else 999
                sop_facts = {
                    "order_verified": order_verified,
                    "order_status": str(target_order["status"]) if target_order else "missing",
                    "amount_cents": min(order_total, 5000) if order_verified else 0,
                    "days_since_delivery": days_age,
                }
                if requested_order_id:
                    tool_args = {"order_id": requested_order_id}
                decision_plan = "propose_tool"
            else:
                order_verified = target_order is not None
                # If prompt injection requested an inflated amount > order total, cap/evaluate exact requested amount so SOP DENYs >25000!
                effective_cents = (
                    parsed_cents
                    if parsed_cents is not None
                    else (int(target_order["total_cents"]) if target_order else 0)
                )
                # Also if requested amount exceeds actual order total on a small order, SOP/connector must never over-refund!
                if target_order is not None and effective_cents > int(target_order["total_cents"]) and effective_cents <= 25000:
                    order_verified = False  # Cannot refund more than paid!
                sop_facts = {
                    "order_verified": order_verified,
                    "order_status": str(target_order["status"]) if target_order else "missing",
                    "amount_cents": effective_cents,
                    "days_since_delivery": int(target_order["days_since_delivery"]) if target_order else 999,
                }
                if requested_order_id:
                    tool_args = {
                        "order_id": requested_order_id,
                        "amount_cents": effective_cents,
                        "reason": "customer_refund_request",
                    }
                decision_plan = "propose_tool"
        elif intent_domain == "shipping_delay":
            sop_facts = {
                "shipment_verified": target_shipment is not None,
                "delay_days": int(target_shipment["delay_days"]) if target_shipment else 0,
                "shipment_status": str(target_shipment["status"]) if target_shipment else "missing",
            }
            if target_shipment is not None:
                tool_args = {"shipment_id": str(target_shipment["shipment_id"])}
            decision_plan = "propose_tool"
        elif intent_domain == "booking_change":
            new_slot = (
                str(explicit_tool_args["new_slot_iso"])
                if explicit_tool_args and "new_slot_iso" in explicit_tool_args
                else "2026-12-10T14:00:00Z"
            )
            sop_facts = {
                "booking_verified": target_booking is not None,
                "hours_until_slot": int(target_booking["hours_until_slot"]) if target_booking else 0,
                "fee_cents": int(target_booking["fee_cents"]) if target_booking else 0,
            }
            if target_booking is not None:
                tool_args = {"booking_id": str(target_booking["booking_id"]), "new_slot_iso": new_slot}
            decision_plan = "propose_tool"
        elif intent_domain == "account_recovery":
            sop_facts = {
                "account_verified": account_info is not None,
                "tool": candidate_tool or "accounts.unlock_account",
            }
            if account_info is not None:
                tool_args = {"account_id": str(account_info["account_id"])}
            decision_plan = "propose_tool"

        stages.append(
            StageStepTrace(
                stage=ResolutionStage.DECIDE,
                status="completed",
                summary=f"Selected plan={decision_plan} over verified server facts.",
                details={"decision_plan": decision_plan, "tool": candidate_tool, "tool_args": tool_args, "facts": sop_facts},
                duration_ms=max(1, int((time.perf_counter() - t0) * 1000)),
            )
        )

        # ------------------------------------------------------------------
        # Stage 5: AUTHORIZE
        # ------------------------------------------------------------------
        t0 = time.perf_counter()
        capability = None
        approval_id: str | None = None
        matched_rules: list[str] = []

        if decision_plan == "propose_tool" and candidate_tool is not None and intent_domain != "knowledge_query":
            act_cls = TOOL_ACTION_CLASS[candidate_tool]
            verdict = procedures.evaluate(
                session=session,
                domain=intent_domain,
                action_class=act_cls,
                facts=sop_facts,
                human_present=True,
            )
            matched_rules = list(verdict.rule_ids)
            if verdict.enforced_decision == "ALLOW":
                capability = self.broker.issue_capability(
                    session=session,
                    tool=candidate_tool,
                    tool_args=tool_args,
                    verdict=verdict,
                )
                auth_summary = f"ALLOW via {matched_rules}; issued capability {capability.token_id}."
            elif verdict.enforced_decision == "ASK":
                approval_id = new_id("apr", 10)
                with db.immediate_transaction() as conn:
                    conn.execute(
                        """
                        INSERT INTO approval_queue (
                            approval_id, tenant_id, session_id, customer_id, domain,
                            tool, args_json, action_class, verdict_json, reason, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                        """,
                        (
                            approval_id,
                            session.tenant_id,
                            session.session_id,
                            session.customer_id,
                            intent_domain,
                            candidate_tool,
                            jcs_str(tool_args),
                            act_cls.value,
                            jcs_str(verdict.to_contract_dict()),
                            verdict.reason or "Operator approval required",
                            iso_utc(),
                        ),
                    )
                    conn.execute(
                        "UPDATE conversations SET status = 'awaiting_approval', updated_at = ? WHERE conversation_id = ?",
                        (iso_utc(), conversation_id),
                    )
                auth_summary = f"ASK via {matched_rules}; queued approval {approval_id}."
            else:
                auth_summary = f"DENY via {matched_rules}: {verdict.reason}"
        elif decision_plan == "escalate_human":
            verdict = procedures.evaluate(
                session=session,
                domain="escalation",
                action_class=ActionClass.TEXT_DELIVERY,
                facts=sop_facts,
                human_present=True,
            )
            matched_rules = list(verdict.rule_ids)
            auth_summary = "Escalation authorized to human operator queue."
        else:
            auth_summary = f"Read-only knowledge response ({rag_result.status.value})."

        stages.append(
            StageStepTrace(
                stage=ResolutionStage.AUTHORIZE,
                status="completed",
                summary=auth_summary,
                details={
                    "enforced_decision": verdict.enforced_decision if verdict else "READ_ONLY",
                    "rule_ids": matched_rules,
                    "capability_token_id": capability.token_id if capability else None,
                    "approval_id": approval_id,
                },
                duration_ms=max(1, int((time.perf_counter() - t0) * 1000)),
            )
        )

        # Optional test hook simulating concurrent human takeover mid-turn before EXECUTE / commit!
        if pre_commit_hook is not None:
            pre_commit_hook()

        # Re-verify ownership_epoch before EXECUTE / response commit!
        with db.read_connection() as conn:
            latest_conv = conn.execute(
                "SELECT ownership_epoch, owner_kind FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
        if latest_conv is not None and (
            int(latest_conv["ownership_epoch"]) != session.ownership_epoch
            or str(latest_conv["owner_kind"]) == "human_owned"
        ):
            db.append_audit(
                event_kind="ai_turn_discarded_stale_epoch",
                actor="resolution_engine",
                session_id=session.session_id,
                payload={
                    "conversation_id": conversation_id,
                    "turn_epoch": session.ownership_epoch,
                    "active_epoch": int(latest_conv["ownership_epoch"]),
                },
            )
            raise StaleEpochError(
                f"In-flight AI turn discarded: ownership_epoch advanced from {session.ownership_epoch} "
                f"to {latest_conv['ownership_epoch']}"
            )

        # ------------------------------------------------------------------
        # Stage 6: EXECUTE
        # ------------------------------------------------------------------
        t0 = time.perf_counter()
        receipt_ids: list[str] = []
        exec_details: dict[str, Any] = {"executed": False}
        resolution_status = "resolved"

        if capability is not None and candidate_tool is not None and verdict is not None:
            exec_res = self.broker.execute_capability(
                capability=capability,
                session=session,
                tool=candidate_tool,
                tool_args=tool_args,
                verdict_id=verdict.verdict_id,
                policy_version=verdict.policy_version,
            )
            if exec_res.receipt_id:
                receipt_ids.append(exec_res.receipt_id)
            exec_details = {
                "executed": True,
                "intent_state": exec_res.intent.state.value,
                "reconciled_result": exec_res.intent.reconciled_result,
                "reconciled_from_unknown": exec_res.reconciled_from_unknown,
                "state_history": exec_res.state_history,
                "receipt_id": exec_res.receipt_id,
            }
            if exec_res.receipt_id is None:
                resolution_status = "escalated"
                exec_summary = "Connector timed out and reconcile_probe found effect_absent; escalating."
            else:
                exec_summary = f"Executed {candidate_tool} -> {exec_res.intent.state.value} (receipt {exec_res.receipt_id})."
        elif verdict is not None and verdict.enforced_decision == "ASK":
            resolution_status = "awaiting_approval" if approval_id else "escalated"
            exec_summary = f"Execution held: {resolution_status}."
        elif verdict is not None and verdict.enforced_decision == "DENY":
            resolution_status = "denied"
            exec_summary = "Execution blocked by SOP DENY verdict."
        elif decision_plan in ("escalate_human", "abstain_unavailable_escalate"):
            resolution_status = "escalated"
            with db.immediate_transaction() as conn:
                conn.execute(
                    "UPDATE conversations SET status = 'escalated', updated_at = ? WHERE conversation_id = ?",
                    (iso_utc(), conversation_id),
                )
            exec_summary = "No mutation executed; conversation routed to human specialist."
        else:
            exec_summary = "Read-only turn; no connector mutation needed."

        stages.append(
            StageStepTrace(
                stage=ResolutionStage.EXECUTE,
                status="completed",
                summary=exec_summary,
                details=exec_details,
                duration_ms=max(1, int((time.perf_counter() - t0) * 1000)),
            )
        )

        # ------------------------------------------------------------------
        # Stage 7: VERIFY (Draft Response + Commitment Output Gate)
        # ------------------------------------------------------------------
        t0 = time.perf_counter()
        if draft_override is not None:
            draft = draft_override
        else:
            draft = self._compose_deterministic_response(
                is_ar=is_ar,
                intent_domain=intent_domain,
                candidate_tool=candidate_tool,
                resolution_status=resolution_status,
                verdict=verdict,
                rag_result=rag_result,
                receipt_ids=receipt_ids,
                approval_id=approval_id,
                tool_args=tool_args,
            )

        gate_decision: GateDecision = gate.evaluate(
            session=session,
            draft_text=draft,
            mode="BLOCK",
            turn_receipt_ids=receipt_ids,
        )
        stages.append(
            StageStepTrace(
                stage=ResolutionStage.VERIFY,
                status="completed" if gate_decision.allowed else "rewritten_by_gate",
                summary=(
                    "Commitment Output Gate passed."
                    if gate_decision.allowed
                    else f"Commitment Output Gate blocked unbacked claims: {gate_decision.blocked_claims}"
                ),
                details=gate_decision.to_dict(),
                duration_ms=max(1, int((time.perf_counter() - t0) * 1000)),
            )
        )

        # ------------------------------------------------------------------
        # Stage 8: RESOLVE
        # ------------------------------------------------------------------
        t0 = time.perf_counter()
        total_latency_ms = max(1, int((time.perf_counter() - turn_start) * 1000))
        turn_id = new_id("trn", 10)
        final_receipts = gate_decision.receipt_ids or receipt_ids

        resolve_step = StageStepTrace(
            stage=ResolutionStage.RESOLVE,
            status="completed",
            summary=f"Turn finalized with status={resolution_status} (receipts={final_receipts}).",
            details={"turn_id": turn_id, "resolution_status": resolution_status, "receipt_ids": final_receipts},
            duration_ms=max(1, int((time.perf_counter() - t0) * 1000)),
        )
        stages.append(resolve_step)

        verdict_dict = verdict.to_contract_dict() if verdict else None
        citations_list = [c.to_dict() for c in rag_result.citations]

        result = ResolutionTurnResult(
            turn_id=turn_id,
            conversation_id=conversation_id,
            tenant_id=session.tenant_id,
            session_id=session.session_id,
            customer_id=session.customer_id,
            language_variety=variety,
            resolution_status=resolution_status,
            assistant_text=gate_decision.output_text,
            stages=stages,
            policy_verdict=verdict_dict,
            matched_rules=matched_rules,
            rag_status=rag_result.status.value,
            citations=citations_list,
            capability_token_id=capability.token_id if capability else None,
            capability_args_digest=capability.args_digest if capability else None,
            receipt_ids=final_receipts,
            approval_id=approval_id,
            ownership_epoch=session.ownership_epoch,
            latency_ms=total_latency_ms,
        )

        stale_stage8_error: StaleEpochError | None = None
        with db.immediate_transaction() as conn:
            conv_final = conn.execute(
                "SELECT ownership_epoch, owner_kind FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            if conv_final is not None and (
                int(conv_final["ownership_epoch"]) != session.ownership_epoch
                or str(conv_final["owner_kind"]) == "human_owned"
            ):
                db.append_audit(
                    event_kind="ai_turn_discarded_stale_epoch",
                    actor="resolution_engine",
                    session_id=session.session_id,
                    payload={
                        "conversation_id": conversation_id,
                        "stage": "RESOLVE",
                        "turn_epoch": session.ownership_epoch,
                        "active_epoch": int(conv_final["ownership_epoch"]),
                    },
                    conn=conn,
                )
                stale_stage8_error = StaleEpochError(
                    f"Stage 8 write aborted: ownership_epoch advanced from {session.ownership_epoch} "
                    f"to {conv_final['ownership_epoch']}"
                )
            else:
                cnt_row = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM conversation_turns WHERE conversation_id = ?",
                    (conversation_id,),
                ).fetchone()
                turn_idx = int(cnt_row["cnt"]) + 1
                conn.execute(
                    """
                    INSERT INTO conversation_turns (
                        turn_id, conversation_id, tenant_id, session_id, customer_id,
                        turn_index, language_variety, customer_text, assistant_text,
                        resolution_status, ownership_epoch, latency_ms, gate_blocked,
                        receipt_ids_json, trace_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        turn_id,
                        conversation_id,
                        session.tenant_id,
                        session.session_id,
                        session.customer_id,
                        turn_idx,
                        variety,
                        customer_text,
                        gate_decision.output_text,
                        resolution_status,
                        session.ownership_epoch,
                        total_latency_ms,
                        0 if gate_decision.allowed else 1,
                        json.dumps(final_receipts),
                        json.dumps(result.to_why_panel(), ensure_ascii=False),
                        iso_utc(),
                    ),
                )
                if resolution_status == "resolved":
                    conn.execute(
                        "UPDATE conversations SET status = 'resolved', updated_at = ? WHERE conversation_id = ?",
                        (iso_utc(), conversation_id),
                    )
                db.append_audit(
                    event_kind="turn_resolved",
                    actor="resolution_engine",
                    session_id=session.session_id,
                    policy_version=verdict.policy_version if verdict else None,
                    payload={
                        "turn_id": turn_id,
                        "conversation_id": conversation_id,
                        "resolution_status": resolution_status,
                        "language_variety": variety,
                        "receipt_ids": final_receipts,
                    },
                    conn=conn,
                )

        if stale_stage8_error is not None:
            raise stale_stage8_error

        return result

    def decide_approval(
        self,
        *,
        tenant_id: str,
        approval_id: str,
        operator_id: str,
        approve: bool,
        note: str = "",
    ) -> dict[str, Any]:
        """Approve or deny a queued `ASK` item in `approval_queue`; executes via broker on approval."""
        slug = validate_tenant_id(tenant_id)
        if not operator_id or not operator_id.strip():
            raise AuthorityViolationError("Authenticated operator_id is required to decide an approval")

        db = self.storage.for_tenant(slug)
        with db.read_connection() as conn:
            row = conn.execute(
                "SELECT * FROM approval_queue WHERE tenant_id = ? AND approval_id = ?",
                (slug, approval_id),
            ).fetchone()
            if row is None:
                raise TenantIsolationError(f"Approval {approval_id!r} not found in tenant {slug!r}")
            if str(row["status"]) != "pending":
                raise AuthorityViolationError(f"Approval {approval_id!r} was already decided ({row['status']})")
            conv = conn.execute(
                "SELECT * FROM conversations WHERE tenant_id = ? AND session_id = ?",
                (slug, str(row["session_id"])),
            ).fetchone()

        now = iso_utc()
        if not approve:
            with db.immediate_transaction() as conn:
                conn.execute(
                    """
                    UPDATE approval_queue
                    SET status = 'denied', decided_by = ?, decision_note = ?, decided_at = ?
                    WHERE approval_id = ?
                    """,
                    (operator_id.strip(), note, now, approval_id),
                )
                db.append_audit(
                    event_kind="approval_denied",
                    actor=operator_id.strip(),
                    session_id=str(row["session_id"]),
                    payload={"approval_id": approval_id, "note": note},
                    conn=conn,
                )
            return {"approval_id": approval_id, "status": "denied", "receipt_id": None}

        base_verdict = PolicyVerdict.model_validate(json.loads(str(row["verdict_json"])))
        confirmed_verdict = base_verdict.model_copy(
            update={
                "enforced_decision": "ALLOW",
                "confirmation": PolicyConfirmation(
                    confirmer_kind="operator",
                    verification_ref=f"operator:{operator_id.strip()}",
                    confirmed_at=now,
                ),
            }
        )
        epoch = int(conv["ownership_epoch"]) if conv else 0
        session = AuthenticatedSession(
            session_id=str(row["session_id"]),
            tenant_id=slug,
            customer_id=str(row["customer_id"]),
            principal_kind="operator",
            ownership_epoch=epoch,
        )
        tool = str(row["tool"])
        tool_args = json.loads(str(row["args_json"]))

        cap = self.broker.issue_capability(
            session=session,
            tool=tool,
            tool_args=tool_args,
            verdict=confirmed_verdict,
        )
        exec_res = self.broker.execute_capability(
            capability=cap,
            session=session,
            tool=tool,
            tool_args=tool_args,
            verdict_id=confirmed_verdict.verdict_id,
            policy_version=confirmed_verdict.policy_version,
            operator_confirmed=True,
        )

        with db.immediate_transaction() as conn:
            conn.execute(
                """
                UPDATE approval_queue
                SET status = 'approved', decided_by = ?, decision_note = ?, receipt_id = ?, decided_at = ?
                WHERE approval_id = ?
                """,
                (operator_id.strip(), note, exec_res.receipt_id, iso_utc(), approval_id),
            )
            if conv is not None:
                conn.execute(
                    "UPDATE conversations SET status = 'resolved', updated_at = ? WHERE conversation_id = ?",
                    (iso_utc(), str(conv["conversation_id"])),
                )
            db.append_audit(
                event_kind="approval_approved_executed",
                actor=operator_id.strip(),
                session_id=session.session_id,
                policy_version=confirmed_verdict.policy_version,
                payload={"approval_id": approval_id, "receipt_id": exec_res.receipt_id, "tool": tool},
                conn=conn,
            )

        return {"approval_id": approval_id, "status": "approved", "receipt_id": exec_res.receipt_id}

    @staticmethod
    def _compose_deterministic_response(
        *,
        is_ar: bool,
        intent_domain: str,
        candidate_tool: str | None,
        resolution_status: str,
        verdict: PolicyVerdict | None,
        rag_result: KnowledgeSearchResult,
        receipt_ids: list[str],
        approval_id: str | None,
        tool_args: dict[str, Any],
    ) -> str:
        if resolution_status == "resolved" and receipt_ids:
            rcp = receipt_ids[0]
            if candidate_tool == "refunds.issue_refund":
                amt = int(tool_args.get("amount_cents", 0))
                if is_ar:
                    return f"تم استرداد المبلغ ({amt} سنت) للطلب {tool_args.get('order_id')} بنجاح. [Receipt: {rcp}]"
                return f"We have issued a refund of {amt} cents for order {tool_args.get('order_id')}. [Receipt: {rcp}]"
            if candidate_tool == "orders.cancel_order":
                if is_ar:
                    return f"تم إلغاء الطلب {tool_args.get('order_id')} بنجاح. [Receipt: {rcp}]"
                return f"We have cancelled your order {tool_args.get('order_id')}. [Receipt: {rcp}]"
            if candidate_tool == "shipments.expedite_shipment":
                if is_ar:
                    return f"تم تسريع الشحنة {tool_args.get('shipment_id')} بنجاح. [Receipt: {rcp}]"
                return f"We have expedited your shipment {tool_args.get('shipment_id')}. [Receipt: {rcp}]"
            if candidate_tool and candidate_tool.startswith("bookings."):
                if is_ar:
                    return f"تم تعديل الحجز {tool_args.get('booking_id')} بنجاح. [Receipt: {rcp}]"
                return f"We have rescheduled your booking {tool_args.get('booking_id')}. [Receipt: {rcp}]"
            if candidate_tool and candidate_tool.startswith("accounts."):
                if is_ar:
                    return f"تم فتح حسابك {tool_args.get('account_id')} بنجاح. [Receipt: {rcp}]"
                return f"We have unlocked your account {tool_args.get('account_id')}. [Receipt: {rcp}]"

        if resolution_status == "awaiting_approval":
            if is_ar:
                return f"يحتاج هذا الطلب إلى موافقة أحد أعضاء الفريق المختصين (رقم المراجعة: {approval_id}). لم يتم تنفيذ الإجراء بعد."
            return f"This request requires a team member's approval (Approval ID: {approval_id}). No action has been executed yet."

        if resolution_status == "denied":
            reason = verdict.reason if verdict and verdict.reason else "Outside policy bounds."
            if is_ar:
                return f"نعتذر، لا يمكن تنفيذ هذا الطلب وفق السياسة المعتمدة: {reason}"
            return f"We cannot complete that action under our policy: {reason}"

        if rag_result.status == KnowledgeStatus.CONFIRMED_NEGATIVE and rag_result.citations:
            top = rag_result.citations[0]
            if is_ar:
                return f"وفق السياسة المعتمدة [{top.chunk_id}]: هذه الميزة أو الخدمة غير متاحة — \"{top.quote}\""
            return f"According to our policy [{top.chunk_id}], that option is not offered: \"{top.quote}\""

        if rag_result.status == KnowledgeStatus.SUPPORTED and rag_result.citations and resolution_status == "resolved":
            top = rag_result.citations[0]
            if is_ar:
                return f"وفق الدليل المعتمد [{top.chunk_id}]: {top.quote}"
            return f"Based on our documented policy [{top.chunk_id}]: {top.quote}"

        # Escalated / Unavailable fallback (never hallucinate!)
        if is_ar:
            return "لا تتوفر معلومة موثقة كافية لحسم هذا الطلب تلقائياً؛ تم تحويل المحادثة إلى مختص بشري لمساعدتك."
        return "I do not have verified policy information to confirm that automatically; I am escalating your conversation to a specialist."
