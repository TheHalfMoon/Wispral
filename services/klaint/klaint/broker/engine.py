# SPDX-License-Identifier: Apache-2.0
"""Core capability broker runtime (executed inside the isolated `python -m klaint.broker` OS process)."""

from __future__ import annotations

import base64
import json
import os
import secrets
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from klaint.connectors.business import TOOL_ACTION_CLASS, BusinessConnectorSuite
from klaint.core.errors import (
    AuthorityViolationError,
    CapabilityError,
    ConnectorTimeoutError,
    ExpiredCapabilityError,
    KlaintError,
    ReplayNonceError,
    StaleEpochError,
    TenantIsolationError,
)
from klaint.core.jcs import compute_args_digest, derive_idempotency_key, jcs_dumps, jcs_str
from klaint.core.models import (
    TOOL_NAME_RE,
    ActionClass,
    AuthenticatedSession,
    CapabilitySignature,
    CapabilityToken,
    DispatchSpec,
    EffectIntentRecord,
    IntentState,
    PolicyVerdict,
    assert_intent_transition,
    iso_utc,
    new_id,
    parse_iso_utc,
    reject_forged_identity_args,
    utc_now,
    validate_tenant_id,
)
from klaint.storage.tenant_db import TenantStorageRegistry

MAX_CAPABILITY_TTL_SECONDS = 60


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(encoded: str) -> bytes:
    pad = "=" * ((4 - (len(encoded) % 4)) % 4)
    return base64.urlsafe_b64decode(encoded + pad)


@dataclass(frozen=True)
class _BoundTokenMeta:
    tenant_id: str
    customer_id: str
    session_id: str
    verdict_id: str
    action_class: str
    epoch: int
    operator_confirmed: bool = False


@dataclass(frozen=True)
class BrokerExecutionResult:
    intent: EffectIntentRecord
    receipt_id: str | None
    state_history: list[str]
    connector_output: dict[str, Any] | None
    reconciled_from_unknown: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent.to_contract_dict(),
            "receipt_id": self.receipt_id,
            "state_history": list(self.state_history),
            "connector_output": self.connector_output,
            "reconciled_from_unknown": self.reconciled_from_unknown,
        }


class BrokerRuntime:
    """Holds Ed25519 signing keys and connector secrets strictly in broker process memory."""

    def __init__(
        self,
        data_dir: Path | str,
        *,
        key_id: str = "klaint-broker-ed25519-v1",
        connector_secrets: dict[str, str] | None = None,
    ) -> None:
        self.storage = TenantStorageRegistry(data_dir)
        self.key_id = key_id
        self._private_key = Ed25519PrivateKey.generate()
        self._public_key: Ed25519PublicKey = self._private_key.public_key()
        self._connector_secrets: dict[str, str] = dict(
            connector_secrets
            or {
                "orders": secrets.token_hex(32),
                "shipments": secrets.token_hex(32),
                "refunds": secrets.token_hex(32),
                "bookings": secrets.token_hex(32),
                "accounts": secrets.token_hex(32),
            }
        )
        self._lock = threading.RLock()
        self._bound_tokens: dict[str, _BoundTokenMeta] = {}

    @property
    def public_key_b64(self) -> str:
        raw = self._public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
        return _b64url_encode(raw)

    def info(self) -> dict[str, Any]:
        return {
            "pid": os.getpid(),
            "key_id": self.key_id,
            "public_key_b64": self.public_key_b64,
            "connector_count": len(self._connector_secrets),
        }

    def issue_capability(
        self,
        *,
        session: AuthenticatedSession,
        tool: str,
        tool_args: dict[str, Any],
        verdict: PolicyVerdict,
        ttl_seconds: int = 30,
        issued_at_override: str | None = None,
    ) -> CapabilityToken:
        validate_tenant_id(session.tenant_id)
        reject_forged_identity_args(tool_args, session)

        if not TOOL_NAME_RE.fullmatch(tool):
            raise CapabilityError(f"Invalid tool identifier {tool!r}")

        expected_class = TOOL_ACTION_CLASS.get(tool)
        if expected_class is None or expected_class == ActionClass.READ:
            raise CapabilityError(f"Tool {tool!r} is not a broker-dispatched mutation tool")

        if verdict.enforced_decision != "ALLOW":
            raise CapabilityError(
                f"Cannot issue capability without enforced ALLOW verdict (got {verdict.enforced_decision!r})"
            )
        if verdict.principal_scope_ref != session.principal_scope_ref:
            raise TenantIsolationError("Policy verdict principal_scope_ref does not match authenticated session")
        if verdict.action_class != expected_class:
            raise CapabilityError(
                f"Policy verdict action_class {verdict.action_class.value!r} does not match tool class {expected_class.value!r}"
            )

        if ttl_seconds <= 0 or ttl_seconds > MAX_CAPABILITY_TTL_SECONDS:
            raise ExpiredCapabilityError(
                f"Capability TTL must be in (0, {MAX_CAPABILITY_TTL_SECONDS}] seconds, got {ttl_seconds}"
            )

        # Rejects IEEE-754 floats inside `tool_args` via RFC 8785 JCS
        digest = compute_args_digest(tool_args)

        now_dt = parse_iso_utc(issued_at_override) if issued_at_override else utc_now()
        exp_dt = now_dt + timedelta(seconds=ttl_seconds)
        token_id = new_id("cap", 12)
        nonce = _b64url_encode(secrets.token_bytes(16))  # 128-bit base64url (22 chars)

        unsigned_fields = {
            "token_id": token_id,
            "issuer": "klaint_broker",
            "session_ref": session.session_id,
            "tool": tool,
            "args_digest": digest,
            "nonce": nonce,
            "issued_at": iso_utc(now_dt),
            "expires_at": iso_utc(exp_dt),
            "single_use": True,
        }
        sig_bytes = self._private_key.sign(jcs_dumps(unsigned_fields))
        sig_b64 = _b64url_encode(sig_bytes)  # 64 bytes -> 86 base64url chars without padding

        token = CapabilityToken(
            **unsigned_fields,
            signature=CapabilitySignature(alg="ed25519", key_id=self.key_id, value=sig_b64),
        )
        is_op_confirmed = bool(
            session.principal_kind == "operator"
            or (verdict.confirmation is not None and verdict.confirmation.confirmer_kind == "operator")
        )
        with self._lock:
            self._bound_tokens[token_id] = _BoundTokenMeta(
                tenant_id=session.tenant_id,
                customer_id=session.customer_id,
                session_id=session.session_id,
                verdict_id=verdict.verdict_id,
                action_class=expected_class.value,
                epoch=session.ownership_epoch,
                operator_confirmed=is_op_confirmed,
            )

        db = self.storage.for_tenant(session.tenant_id)
        db.append_audit(
            event_kind="capability_issued",
            actor="klaint_broker",
            session_id=session.session_id,
            policy_version=verdict.policy_version,
            payload={
                "token_id": token.token_id,
                "tool": tool,
                "args_digest": digest,
                "verdict_id": verdict.verdict_id,
                "expires_at": token.expires_at,
            },
        )
        return token

    def verify_capability(
        self,
        *,
        capability: CapabilityToken,
        session: AuthenticatedSession,
        tool: str,
        tool_args: dict[str, Any],
        now_override: datetime | None = None,
    ) -> str:
        """Verify Ed25519 signature, TTL <= 60s, freshness, session binding, tool name, and JCS args_digest."""
        validate_tenant_id(session.tenant_id)
        reject_forged_identity_args(tool_args, session)

        # Always compute canonical digest first so float arguments deterministically fail with CanonicalSerializationError
        computed_digest = compute_args_digest(tool_args)

        if capability.issuer != "klaint_broker" or capability.single_use is not True:
            raise CapabilityError("Invalid capability issuer or single_use flag")
        if capability.signature.alg != "ed25519" or capability.signature.key_id != self.key_id:
            raise CapabilityError("Untrusted capability key_id or signature algorithm")

        try:
            sig_raw = _b64url_decode(capability.signature.value)
            self._public_key.verify(sig_raw, jcs_dumps(capability.unsigned_payload()))
        except (InvalidSignature, ValueError) as exc:
            raise CapabilityError("Ed25519 capability signature verification failed") from exc

        issued_dt = parse_iso_utc(capability.issued_at)
        expires_dt = parse_iso_utc(capability.expires_at)
        lifetime = (expires_dt - issued_dt).total_seconds()
        if lifetime <= 0 or lifetime > MAX_CAPABILITY_TTL_SECONDS:
            raise ExpiredCapabilityError(
                f"Capability lifetime {lifetime:.3f}s violates (0, {MAX_CAPABILITY_TTL_SECONDS}]s ceiling"
            )

        eval_now = now_override or utc_now()
        if eval_now > expires_dt:
            raise ExpiredCapabilityError(
                f"Capability {capability.token_id} expired at {capability.expires_at} (now={iso_utc(eval_now)})"
            )

        if capability.session_ref != session.session_id:
            raise TenantIsolationError(
                f"Capability session_ref {capability.session_ref!r} does not match session {session.session_id!r}"
            )
        if capability.tool != tool:
            raise CapabilityError(
                f"Swapped tool rejected: capability bound to {capability.tool!r}, dispatch requested {tool!r}"
            )
        if capability.args_digest != computed_digest:
            raise CapabilityError(
                f"Mutated arguments rejected: capability bound to {capability.args_digest}, got {computed_digest}"
            )

        with self._lock:
            meta = self._bound_tokens.get(capability.token_id)
        if meta is not None:
            if meta.tenant_id != session.tenant_id or meta.customer_id != session.customer_id:
                raise TenantIsolationError("Cross-tenant or cross-customer capability use denied")

        return computed_digest

    def execute_capability(
        self,
        *,
        capability: CapabilityToken,
        session: AuthenticatedSession,
        tool: str,
        tool_args: dict[str, Any],
        idempotency_key: str | None = None,
        verdict_id: str | None = None,
        policy_version: str | None = None,
        now_override: str | None = None,
        operator_confirmed: bool = False,
    ) -> BrokerExecutionResult:
        eval_now = parse_iso_utc(now_override) if now_override else None
        computed_digest = self.verify_capability(
            capability=capability,
            session=session,
            tool=tool,
            tool_args=tool_args,
            now_override=eval_now,
        )

        with self._lock:
            meta = self._bound_tokens.get(capability.token_id)
        resolved_verdict_id = verdict_id or (meta.verdict_id if meta else new_id("vrd", 8))
        is_op_confirmed = bool(
            operator_confirmed
            or session.principal_kind == "operator"
            or (meta is not None and meta.operator_confirmed)
        )
        expected_class = TOOL_ACTION_CLASS.get(tool)
        if expected_class is None or expected_class == ActionClass.READ:
            raise CapabilityError(f"Tool {tool!r} cannot be executed as a mutation")

        idem_key = idempotency_key or derive_idempotency_key(
            session.tenant_id,
            session.session_id,
            tool,
            tool_args,
        )

        db = self.storage.for_tenant(session.tenant_id)
        connectors = BusinessConnectorSuite(db)
        intent_id = new_id("int", 10)
        receipt_id = new_id("rcp", 10)
        state_history: list[str] = []
        pre_dispatch_abort: Exception | None = None

        # Atomic BEGIN IMMEDIATE: consume single-use nonce, record pending, validate epoch/idempotency -> dispatched | abandoned
        with db.immediate_transaction() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO consumed_nonces (nonce, token_id, session_ref, tool, args_digest, consumed_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        capability.nonce,
                        capability.token_id,
                        capability.session_ref,
                        tool,
                        computed_digest,
                        iso_utc(),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ReplayNonceError(f"Replay detected: capability nonce {capability.nonce!r} already consumed") from exc

            existing_rows = conn.execute(
                """
                SELECT * FROM action_ledger
                WHERE principal_scope_ref = ? AND owner = 'klaint_broker' AND idempotency_key = ?
                ORDER BY created_at DESC
                """,
                (session.principal_scope_ref, idem_key),
            ).fetchall()

            has_non_terminal_collision: str | None = None
            for row in existing_rows:
                prev_state = str(row["state"])
                if prev_state in ("pending", "dispatched", "unknown"):
                    has_non_terminal_collision = (
                        f"Refusing duplicate dispatch while non-terminal intent {row['intent_id']} is in state {prev_state!r}"
                    )
                    break
                if prev_state == "settled" or (
                    prev_state == "reconciled" and row["reconciled_result"] == "effect_present"
                ):
                    cached_intent = EffectIntentRecord(
                        intent_id=str(row["intent_id"]),
                        idempotency_key=str(row["idempotency_key"]),
                        owner="klaint_broker",
                        action_class=row["action_class"],
                        state=IntentState(prev_state),
                        verdict_id=str(row["verdict_id"]),
                        principal_scope_ref=str(row["principal_scope_ref"]),
                        epoch=int(row["epoch"]),
                        reconcile_probe=row["reconcile_probe"],
                        reconciled_result=row["reconciled_result"],
                        detail_ref=str(row["receipt_id"]),
                        dispatch=DispatchSpec(tool=str(row["tool"]), args_digest=str(row["args_digest"])),
                        capability=CapabilityToken.model_validate(json.loads(str(row["capability_json"]))),
                    )
                    return BrokerExecutionResult(
                        intent=cached_intent,
                        receipt_id=str(row["receipt_id"]),
                        state_history=[prev_state],
                        connector_output=json.loads(str(row["result_json"])) if row["result_json"] else {},
                    )

            now_str = iso_utc()
            state_history.append(IntentState.PENDING.value)
            conn.execute(
                """
                INSERT INTO action_ledger (
                    intent_id, receipt_id, tenant_id, session_id, customer_id,
                    idempotency_key, owner, action_class, tool, args_json, args_digest,
                    state, verdict_id, principal_scope_ref, epoch,
                    reconcile_probe, reconciled_result, capability_json, result_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'klaint_broker', ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, NULL, ?, ?)
                """,
                (
                    intent_id,
                    receipt_id,
                    session.tenant_id,
                    session.session_id,
                    session.customer_id,
                    idem_key,
                    expected_class.value,
                    tool,
                    jcs_str(tool_args),
                    computed_digest,
                    IntentState.PENDING.value,
                    resolved_verdict_id,
                    session.principal_scope_ref,
                    session.ownership_epoch,
                    jcs_str(capability.model_dump(mode="json")),
                    now_str,
                    now_str,
                ),
            )

            conv = conn.execute(
                "SELECT ownership_epoch, owner_kind FROM conversations WHERE tenant_id = ? AND session_id = ?",
                (session.tenant_id, session.session_id),
            ).fetchone()
            if conv is not None:
                db_epoch = int(conv["ownership_epoch"])
                owner_kind = str(conv["owner_kind"])
                if db_epoch != session.ownership_epoch or (owner_kind == "human_owned" and not is_op_confirmed):
                    pre_dispatch_abort = StaleEpochError(
                        f"Stale ownership_epoch={session.ownership_epoch} (active={db_epoch}, owner={owner_kind})"
                    )
            if pre_dispatch_abort is None and has_non_terminal_collision is not None:
                pre_dispatch_abort = KlaintError(has_non_terminal_collision)

            if pre_dispatch_abort is not None:
                assert_intent_transition(IntentState.PENDING, IntentState.ABANDONED)
                conn.execute(
                    "UPDATE action_ledger SET state = ?, updated_at = ? WHERE intent_id = ?",
                    (IntentState.ABANDONED.value, iso_utc(), intent_id),
                )
                state_history.append(IntentState.ABANDONED.value)
                db.append_audit(
                    event_kind="intent_abandoned",
                    actor="klaint_broker",
                    session_id=session.session_id,
                    policy_version=policy_version,
                    payload={
                        "intent_id": intent_id,
                        "tool": tool,
                        "idempotency_key": idem_key,
                        "abort_reason": str(pre_dispatch_abort),
                    },
                    conn=conn,
                )
            else:
                assert_intent_transition(IntentState.PENDING, IntentState.DISPATCHED)
                conn.execute(
                    "UPDATE action_ledger SET state = ?, updated_at = ? WHERE intent_id = ?",
                    (IntentState.DISPATCHED.value, iso_utc(), intent_id),
                )
                state_history.append(IntentState.DISPATCHED.value)
                db.append_audit(
                    event_kind="intent_dispatched",
                    actor="klaint_broker",
                    session_id=session.session_id,
                    policy_version=policy_version,
                    payload={
                        "intent_id": intent_id,
                        "receipt_id": receipt_id,
                        "tool": tool,
                        "idempotency_key": idem_key,
                        "args_digest": computed_digest,
                    },
                    conn=conn,
                )

        if pre_dispatch_abort is not None:
            raise pre_dispatch_abort

        def _reconcile_dispatched_failure(reason_text: str) -> BrokerExecutionResult:
            probe_uri = f"GET /connectors/{tool}/by-idempotency/{idem_key}"
            assert_intent_transition(IntentState.DISPATCHED, IntentState.UNKNOWN)
            with db.immediate_transaction() as conn:
                conn.execute(
                    "UPDATE action_ledger SET state = ?, reconcile_probe = ?, updated_at = ? WHERE intent_id = ?",
                    (IntentState.UNKNOWN.value, probe_uri, iso_utc(), intent_id),
                )
                db.append_audit(
                    event_kind="intent_unknown",
                    actor="klaint_broker",
                    session_id=session.session_id,
                    policy_version=policy_version,
                    payload={
                        "intent_id": intent_id,
                        "tool": tool,
                        "idempotency_key": idem_key,
                        "reconcile_probe": probe_uri,
                        "failure_reason": reason_text,
                    },
                    conn=conn,
                )
            state_history.append(IntentState.UNKNOWN.value)

            # NEVER blind retry! Run read-only GET reconcile_probe by idempotency_key
            probe_res = connectors.reconcile_probe(tool, idem_key)
            reconciled_outcome = "effect_present" if probe_res.effect_present else "effect_absent"
            assert_intent_transition(IntentState.UNKNOWN, IntentState.RECONCILED)
            with db.immediate_transaction() as conn:
                conn.execute(
                    """
                    UPDATE action_ledger
                    SET state = ?, reconcile_probe = ?, reconciled_result = ?, result_json = ?, updated_at = ?
                    WHERE intent_id = ?
                    """,
                    (
                        IntentState.RECONCILED.value,
                        probe_res.probe_uri,
                        reconciled_outcome,
                        json.dumps(probe_res.record) if probe_res.record is not None else None,
                        iso_utc(),
                        intent_id,
                    ),
                )
                db.append_audit(
                    event_kind="intent_reconciled",
                    actor="klaint_broker",
                    session_id=session.session_id,
                    policy_version=policy_version,
                    payload={
                        "intent_id": intent_id,
                        "receipt_id": receipt_id if probe_res.effect_present else None,
                        "reconcile_probe": probe_res.probe_uri,
                        "reconciled_result": reconciled_outcome,
                    },
                    conn=conn,
                )
            state_history.append(IntentState.RECONCILED.value)

            reconciled_record = EffectIntentRecord(
                intent_id=intent_id,
                idempotency_key=idem_key,
                owner="klaint_broker",
                action_class=expected_class.value,  # type: ignore[arg-type]
                state=IntentState.RECONCILED,
                verdict_id=resolved_verdict_id,
                principal_scope_ref=session.principal_scope_ref,
                epoch=session.ownership_epoch,
                reconcile_probe=probe_res.probe_uri,
                reconciled_result=reconciled_outcome,  # type: ignore[arg-type]
                detail_ref=receipt_id if probe_res.effect_present else None,
                dispatch=DispatchSpec(tool=tool, args_digest=computed_digest),
                capability=capability,
            )
            return BrokerExecutionResult(
                intent=reconciled_record,
                receipt_id=receipt_id if probe_res.effect_present else None,
                state_history=state_history,
                connector_output=probe_res.record,
                reconciled_from_unknown=True,
            )

        # Execute connector outside the ledger lock; reconcile both timeouts and deterministic post-dispatch failures
        try:
            output = connectors.mutate(
                session=session,
                tool=tool,
                args=tool_args,
                idempotency_key=idem_key,
            )
        except ConnectorTimeoutError as exc:
            return _reconcile_dispatched_failure(str(exc))
        except Exception as exc:
            _reconcile_dispatched_failure(str(exc))
            raise

        assert_intent_transition(IntentState.DISPATCHED, IntentState.SETTLED)
        with db.immediate_transaction() as conn:
            conn.execute(
                "UPDATE action_ledger SET state = ?, result_json = ?, updated_at = ? WHERE intent_id = ?",
                (IntentState.SETTLED.value, json.dumps(output), iso_utc(), intent_id),
            )
            db.append_audit(
                event_kind="intent_settled",
                actor="klaint_broker",
                session_id=session.session_id,
                policy_version=policy_version,
                payload={
                    "intent_id": intent_id,
                    "receipt_id": receipt_id,
                    "tool": tool,
                    "idempotency_key": idem_key,
                },
                conn=conn,
            )
        state_history.append(IntentState.SETTLED.value)

        intent_record = EffectIntentRecord(
            intent_id=intent_id,
            idempotency_key=idem_key,
            owner="klaint_broker",
            action_class=expected_class.value,  # type: ignore[arg-type]
            state=IntentState.SETTLED,
            verdict_id=resolved_verdict_id,
            principal_scope_ref=session.principal_scope_ref,
            epoch=session.ownership_epoch,
            detail_ref=receipt_id,
            dispatch=DispatchSpec(tool=tool, args_digest=computed_digest),
            capability=capability,
        )
        return BrokerExecutionResult(
            intent=intent_record,
            receipt_id=receipt_id,
            state_history=state_history,
            connector_output=output,
            reconciled_from_unknown=False,
        )

    def close(self) -> None:
        self.storage.close_all()
