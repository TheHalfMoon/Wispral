# SPDX-License-Identifier: Apache-2.0
"""Optional Parlant v4 adapter enforcing Klaint's trust boundaries (KT-01 remediation).

Remediates both KT-01 spike findings on `emcie-co/parlant@2a463ccd10ea` (v4.0.2, Apache-2.0):
1. Forces `BLOCK` output mode (refuses `STREAM`, where `on_message_generated` BAIL only observes).
2. Never trusts Parlant's unauthenticated `:8818` integrated plugin tool server `context.customer_id`;
   every tool call must resolve its `AuthenticatedSession` from Klaint's server-side `SessionAuthenticator`,
   reject forged `customer_id` arguments, and execute mutations strictly via `BrokerClient` capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from klaint.broker.client import BrokerClient
from klaint.conversation.gate import CommitmentOutputGate, GateDecision
from klaint.core.errors import AuthorityViolationError, ForgedIdentityError
from klaint.core.models import (
    AuthenticatedSession,
    PolicyVerdict,
    SessionAuthenticator,
    reject_forged_identity_args,
)


@dataclass(frozen=True)
class ParlantTurnOutcome:
    hook_sequence: list[str]
    final_message: str
    gate_decision: GateDecision
    receipt_ids: list[str]
    bailed_on_draft: bool


class ParlantAdapter:
    """Wraps Parlant v4 hook lifecycle (`on_reviewing_tool_calls`, `on_calling_tools`, `on_message_generated`)
    behind Klaint's server-authenticated session store, out-of-process broker, and Commitment Output Gate.
    """

    def __init__(
        self,
        *,
        session_auth: SessionAuthenticator,
        broker: BrokerClient,
        output_mode: str = "BLOCK",
    ) -> None:
        if output_mode != "BLOCK":
            raise ValueError(
                "ParlantAdapter strictly requires output_mode='BLOCK'; Parlant v4 STREAM mode cannot suppress "
                "messages when CommitmentOutputGate BAILs in on_message_generated."
            )
        self.session_auth = session_auth
        self.broker = broker
        self.output_mode = output_mode

    def guarded_tool_endpoint(
        self,
        *,
        session_token: str | None,
        tool: str,
        tool_args: dict[str, Any],
        verdict: PolicyVerdict,
        untrusted_context_customer_id: str | None = None,
    ) -> dict[str, Any]:
        """Replacement for Parlant's unauthenticated `:8818` plugin tool endpoint."""
        if not session_token:
            raise AuthorityViolationError("Unauthenticated loopback tool call rejected (missing server session_token)")

        session = self.session_auth.verify_token(session_token)
        if untrusted_context_customer_id is not None and untrusted_context_customer_id != session.customer_id:
            raise ForgedIdentityError(
                f"Rejected forged Parlant context.customer_id={untrusted_context_customer_id!r} "
                f"(authenticated session is {session.customer_id!r})"
            )
        reject_forged_identity_args(tool_args, session)

        cap = self.broker.issue_capability(
            session=session,
            tool=tool,
            tool_args=tool_args,
            verdict=verdict,
        )
        exec_res = self.broker.execute_capability(
            capability=cap,
            session=session,
            tool=tool,
            tool_args=tool_args,
            verdict_id=verdict.verdict_id,
            policy_version=verdict.policy_version,
        )
        return {
            "receipt_id": exec_res.receipt_id,
            "state": exec_res.intent.state.value,
            "output": exec_res.connector_output,
        }

    def run_hooked_turn(
        self,
        *,
        session: AuthenticatedSession,
        gate: CommitmentOutputGate,
        proposed_tool: tuple[str, dict[str, Any], Callable[[], PolicyVerdict]] | None,
        draft_generator: Callable[[dict[str, Any] | None], str],
    ) -> ParlantTurnOutcome:
        """Execute Parlant v4 Compass hook order in BLOCK mode with brokered tool execution and message gating."""
        hooks: list[str] = ["on_preparing", "on_generating_messages"]
        tool_result: dict[str, Any] | None = None
        receipts: list[str] = []

        if proposed_tool is not None:
            tool_name, tool_args, verdict_fn = proposed_tool
            hooks.append("on_step_started")
            hooks.append("on_reviewing_tool_calls")
            reject_forged_identity_args(tool_args, session)
            verdict = verdict_fn()
            hooks.append("on_tool_calls_reviewed")

            if verdict.enforced_decision == "ALLOW":
                hooks.append("on_calling_tools")
                cap = self.broker.issue_capability(
                    session=session,
                    tool=tool_name,
                    tool_args=tool_args,
                    verdict=verdict,
                )
                exec_res = self.broker.execute_capability(
                    capability=cap,
                    session=session,
                    tool=tool_name,
                    tool_args=tool_args,
                    verdict_id=verdict.verdict_id,
                    policy_version=verdict.policy_version,
                )
                if exec_res.receipt_id:
                    receipts.append(exec_res.receipt_id)
                tool_result = exec_res.connector_output
                hooks.append("on_tool_calls_completed")
            hooks.append("on_step_completed")

        hooks.append("on_step_started")
        draft = draft_generator(tool_result)
        hooks.append("on_message_generated")
        gate_decision = gate.evaluate(session=session, draft_text=draft, mode=self.output_mode)
        hooks.append("on_step_completed")
        hooks.append("on_messages_emitted")

        return ParlantTurnOutcome(
            hook_sequence=hooks,
            final_message=gate_decision.output_text,
            gate_decision=gate_decision,
            receipt_ids=gate_decision.receipt_ids or receipts,
            bailed_on_draft=not gate_decision.allowed,
        )
