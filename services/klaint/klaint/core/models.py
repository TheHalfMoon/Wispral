# SPDX-License-Identifier: Apache-2.0
"""Core Klaint authority, session, capability, policy-verdict, and effect-intent models."""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
import threading
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from klaint.core.errors import (
    AuthorityViolationError,
    ForgedIdentityError,
    IntentTransitionError,
    TenantIsolationError,
)
from klaint.core.jcs import jcs_dumps

TENANT_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,62}$")
SESSION_ID_RE = re.compile(r"^ses-[A-Za-z0-9_-]{8,64}$")
CAP_TOKEN_ID_RE = re.compile(r"^cap-[A-Za-z0-9_-]{8,64}$")
TOOL_NAME_RE = re.compile(r"^[a-z][a-z0-9_.]{1,63}$")

FORBIDDEN_UNTRUSTED_ARG_KEYS = frozenset(
    {
        "customer_id",
        "tenant_id",
        "principal_scope_ref",
        "authenticated_customer_id",
        "session_ref",
    }
)


def utc_now() -> datetime:
    """Return timezone-aware UTC `datetime`."""
    return datetime.now(timezone.utc)


def iso_utc(dt: datetime | None = None) -> str:
    """Format UTC `datetime` as ISO-8601 with trailing `Z` matching Wispral contract patterns."""
    target = (dt or utc_now()).astimezone(timezone.utc)
    return target.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_iso_utc(value: str) -> datetime:
    """Parse an ISO-8601 UTC timestamp string ending in `Z` or `+00:00`."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def new_id(prefix: str, nbytes: int = 12) -> str:
    """Generate a URL-safe prefixed identifier (e.g. `ses-...`, `cap-...`, `rcp-...`, `int-...`)."""
    token = base64.urlsafe_b64encode(secrets.token_bytes(nbytes)).decode("ascii").rstrip("=")
    return f"{prefix}-{token}"


def validate_tenant_id(tenant_id: str) -> str:
    """Validate `tenant_id` against strict slug regex `^[a-z0-9][a-z0-9_-]{1,62}$`."""
    if not isinstance(tenant_id, str) or "\x00" in tenant_id or not TENANT_SLUG_RE.fullmatch(tenant_id):
        raise TenantIsolationError(
            f"Invalid tenant_id {tenant_id!r}: must match ^[a-z0-9][a-z0-9_-]{{1,62}}$ with zero path separators"
        )
    return tenant_id


def tenant_db_path(data_dir: Path | str, tenant_id: str) -> Path:
    """Resolve physical per-tenant SQLite database path `<data_dir>/tenants/<tenant_id>/klaint.db` safely."""
    slug = validate_tenant_id(tenant_id)
    base_tenants = (Path(data_dir).resolve() / "tenants").resolve()
    candidate = (base_tenants / slug / "klaint.db").resolve()
    if not candidate.is_relative_to(base_tenants) or candidate.parent.parent != base_tenants:
        raise TenantIsolationError(f"Resolved tenant path escaped tenant root for {tenant_id!r}")
    return candidate


def reject_forged_identity_args(tool_args: dict[str, Any], session: AuthenticatedSession | None = None) -> None:
    """Reject any untrusted tool argument attempting to supply or override customer/tenant identity."""
    if not isinstance(tool_args, dict):
        raise AuthorityViolationError("Tool arguments must be a dictionary")
    for key in tool_args:
        if key in FORBIDDEN_UNTRUSTED_ARG_KEYS:
            supplied = tool_args.get(key)
            session_customer = session.customer_id if session is not None else "<unauthenticated>"
            raise ForgedIdentityError(
                f"Untrusted tool argument {key}={supplied!r} is forbidden; identity derives exclusively "
                f"from server-authenticated session (customer_id={session_customer!r})"
            )


class ActionClass(StrEnum):
    READ = "read"
    REVERSIBLE_WRITE = "reversible_write"
    IRREVERSIBLE_WRITE = "irreversible_write"
    MONEY = "money"
    CREDENTIAL_USE = "credential_use"
    PUBLICATION = "publication"
    TEXT_DELIVERY = "text_delivery"
    VOICE_RENDER = "voice_render"


class PolicyDecision(StrEnum):
    ALLOW = "ALLOW"
    ASK = "ASK"
    DENY = "DENY"
    UNDECIDABLE = "UNDECIDABLE"


class IntentState(StrEnum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    SETTLED = "settled"
    ABANDONED = "abandoned"
    UNKNOWN = "unknown"
    RECONCILED = "reconciled"


ALLOWED_INTENT_TRANSITIONS: dict[IntentState, frozenset[IntentState]] = {
    IntentState.PENDING: frozenset(
        {
            IntentState.DISPATCHED,
            IntentState.SETTLED,
            IntentState.ABANDONED,
            IntentState.RECONCILED,
        }
    ),
    IntentState.DISPATCHED: frozenset(
        {
            IntentState.SETTLED,
            IntentState.UNKNOWN,
            IntentState.RECONCILED,
        }
    ),
    IntentState.UNKNOWN: frozenset({IntentState.RECONCILED}),
    IntentState.SETTLED: frozenset(),
    IntentState.ABANDONED: frozenset(),
    IntentState.RECONCILED: frozenset(),
}

TERMINAL_INTENT_STATES: frozenset[IntentState] = frozenset(
    {IntentState.SETTLED, IntentState.ABANDONED, IntentState.RECONCILED}
)


def assert_intent_transition(current: IntentState, target: IntentState) -> None:
    """Enforce Orcel/Wispral `effect_intent` state-machine transitions."""
    if target not in ALLOWED_INTENT_TRANSITIONS.get(current, frozenset()):
        raise IntentTransitionError(f"Illegal effect_intent state transition: {current.value} -> {target.value}")


class AuthenticatedSession(BaseModel):
    """Server-authenticated customer session context (Principle XIX). Immutable once minted."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: str = Field(pattern=r"^ses-[A-Za-z0-9_-]{8,64}$")
    tenant_id: str
    customer_id: str = Field(min_length=2, max_length=128)
    principal_kind: Literal["customer", "operator"] = "customer"
    channel: Literal["web_widget", "chatwoot", "voice", "api", "simulation"] = "web_widget"
    step_up_verified: bool = False
    step_up_ref: str | None = None
    ownership_epoch: int = Field(default=0, ge=0)
    language: str = "en"
    acl_tags: tuple[str, ...] = ("public", "customer")
    authenticated_at: str = Field(default_factory=iso_utc)

    @property
    def principal_scope_ref(self) -> str:
        return f"tenant:{self.tenant_id}:customer:{self.customer_id}"


class SessionAuthenticator:
    """Server-side HMAC-SHA256 session authenticator ensuring customer_id is never forged by callers."""

    def __init__(self, server_secret: bytes | str | None = None) -> None:
        if server_secret is None:
            self._secret = secrets.token_bytes(32)
        elif isinstance(server_secret, str):
            self._secret = server_secret.encode("utf-8")
        else:
            self._secret = bytes(server_secret)
        if len(self._secret) < 16:
            raise ValueError("SessionAuthenticator secret must be at least 16 bytes")
        self._lock = threading.RLock()
        self._sessions: dict[str, AuthenticatedSession] = {}

    @staticmethod
    def _token_mac_payload(session: AuthenticatedSession) -> bytes:
        return jcs_dumps(
            {
                "session_id": session.session_id,
                "tenant_id": session.tenant_id,
                "customer_id": session.customer_id,
                "channel": session.channel,
                "authenticated_at": session.authenticated_at,
            }
        )

    def create_session(
        self,
        *,
        tenant_id: str,
        customer_id: str,
        channel: Literal["web_widget", "chatwoot", "voice", "api", "simulation"] = "web_widget",
        step_up_verified: bool = False,
        step_up_ref: str | None = None,
        ownership_epoch: int = 0,
        language: str = "en",
        acl_tags: tuple[str, ...] = ("public", "customer"),
        session_id: str | None = None,
    ) -> tuple[AuthenticatedSession, str]:
        slug = validate_tenant_id(tenant_id)
        sid = session_id or new_id("ses")
        session = AuthenticatedSession(
            session_id=sid,
            tenant_id=slug,
            customer_id=customer_id,
            channel=channel,
            step_up_verified=step_up_verified,
            step_up_ref=step_up_ref,
            ownership_epoch=ownership_epoch,
            language=language,
            acl_tags=acl_tags,
        )
        with self._lock:
            self._sessions[sid] = session
        mac = hmac.new(self._secret, self._token_mac_payload(session), hashlib.sha256).hexdigest()
        return session, f"{sid}.{mac}"

    def verify_token(self, token: str, expected_tenant_id: str | None = None) -> AuthenticatedSession:
        if "." not in token:
            raise AuthorityViolationError("Malformed session token")
        sid, provided_mac = token.split(".", 1)
        with self._lock:
            session = self._sessions.get(sid)
        if session is None:
            raise AuthorityViolationError(f"Unknown or revoked session_id {sid!r}")
        expected_mac = hmac.new(
            self._secret,
            self._token_mac_payload(session),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(provided_mac, expected_mac):
            raise AuthorityViolationError("Session token HMAC verification failed")
        if expected_tenant_id is not None and session.tenant_id != validate_tenant_id(expected_tenant_id):
            raise TenantIsolationError(
                f"Cross-tenant session access denied: session belongs to {session.tenant_id!r}, not {expected_tenant_id!r}"
            )
        return session

    def elevate_step_up(self, session_id: str, step_up_ref: str) -> tuple[AuthenticatedSession, str]:
        if len(step_up_ref) < 8:
            raise AuthorityViolationError("step_up_ref must be at least 8 characters")
        with self._lock:
            current = self._sessions.get(session_id)
            if current is None:
                raise AuthorityViolationError(f"Unknown session_id {session_id!r}")
            updated = current.model_copy(update={"step_up_verified": True, "step_up_ref": step_up_ref})
            self._sessions[session_id] = updated
        mac = hmac.new(self._secret, self._token_mac_payload(updated), hashlib.sha256).hexdigest()
        return updated, f"{session_id}.{mac}"

    def update_epoch(self, session_id: str, new_epoch: int) -> AuthenticatedSession:
        with self._lock:
            current = self._sessions.get(session_id)
            if current is None:
                raise AuthorityViolationError(f"Unknown session_id {session_id!r}")
            updated = current.model_copy(update={"ownership_epoch": new_epoch})
            self._sessions[session_id] = updated
        return updated


class CapabilitySignature(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    alg: Literal["ed25519"] = "ed25519"
    key_id: str = Field(pattern=r"^[A-Za-z0-9:._-]{3,64}$")
    value: str = Field(pattern=r"^[A-Za-z0-9_-]{86}$")


class CapabilityToken(BaseModel):
    """Exact match for `capability` in `docs/engineering/contracts/effect_intent.schema.json`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    token_id: str = Field(pattern=r"^cap-[A-Za-z0-9_-]{8,64}$")
    issuer: Literal["klaint_broker"] = "klaint_broker"
    session_ref: str = Field(pattern=r"^ses-[A-Za-z0-9_-]{8,64}$")
    tool: str = Field(pattern=r"^[a-z][a-z0-9_.]{1,63}$")
    args_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    nonce: str = Field(pattern=r"^[A-Za-z0-9_-]{22,64}$")
    issued_at: str
    expires_at: str
    single_use: Literal[True] = True
    signature: CapabilitySignature

    def unsigned_payload(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        data.pop("signature", None)
        return data


class DispatchSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tool: str = Field(pattern=r"^[a-z][a-z0-9_.]{1,63}$")
    args_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class EffectIntentRecord(BaseModel):
    """Exact match for `docs/engineering/contracts/effect_intent.schema.json`."""

    model_config = ConfigDict(extra="forbid")

    intent_id: str = Field(min_length=8, max_length=128)
    idempotency_key: str = Field(pattern=r"^[A-Za-z0-9._:-]{16,128}$")
    owner: Literal["klaint_broker"] = "klaint_broker"
    action_class: Literal[
        "reversible_write",
        "irreversible_write",
        "money",
        "credential_use",
        "publication",
    ]
    state: IntentState
    verdict_id: str = Field(min_length=8, max_length=128)
    principal_scope_ref: str = Field(min_length=1, max_length=128)
    epoch: int = Field(ge=0)
    reconcile_probe: str | None = None
    reconciled_result: Literal["effect_present", "effect_absent"] | None = None
    detail_ref: str | None = None
    dispatch: DispatchSpec
    capability: CapabilityToken

    def to_contract_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class PolicyLayer(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source: Literal["base", "product", "tenant", "repository", "user"]
    decision: PolicyDecision


class PolicyConfirmation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    confirmer_kind: Literal["operator", "step_up_verified_holder"]
    verification_ref: str = Field(min_length=8, max_length=256)
    confirmed_at: str


class PolicyVerdict(BaseModel):
    """Exact match for `docs/engineering/contracts/policy_verdict.schema.json`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    verdict_id: str = Field(min_length=8, max_length=128)
    request_id: str = Field(min_length=8, max_length=128)
    epoch: int = Field(ge=0)
    candidate_decision: PolicyDecision
    enforced_decision: Literal["ALLOW", "ASK", "DENY"]
    undecidable_resolution: Literal["ASK", "DENY"] | None = None
    human_present: bool = True
    action_class: ActionClass
    rule_ids: list[str]
    layers: list[PolicyLayer]
    policy_version: str
    inputs_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    principal_scope_ref: str = Field(min_length=1, max_length=128)
    reason: str | None = None
    confirmation: PolicyConfirmation | None = None

    def to_contract_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)
