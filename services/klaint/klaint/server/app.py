# SPDX-License-Identifier: Apache-2.0
"""Klaint Multi-Threaded HTTP REST Server (`klaint-server`, default `127.0.0.1:8090`).

Serves Klaint Studio (`/`), Customer Web Chat Widget (`/widget`), static assets (`/static/*`),
tenant API-key + HMAC operator session authenticated Studio APIs (`/api/v1/*`), and the raw-byte
Standard Webhooks Chatwoot MIT Core endpoint (`/api/v1/webhooks/chatwoot/{tenant_id}`).
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import tempfile
import threading
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from klaint.analytics.metrics import AnalyticsEngine
from klaint.broker.client import BrokerClient
from klaint.connectors.business import BusinessConnectorSuite
from klaint.core.errors import (
    AuthorityViolationError,
    FourEyesViolationError,
    KlaintError,
    StaleEpochError,
    TenantIsolationError,
    WebhookVerificationError,
)
from klaint.core.jcs import jcs_dumps
from klaint.core.models import (
    AuthenticatedSession,
    SessionAuthenticator,
    iso_utc,
    new_id,
    validate_tenant_id,
)
from klaint.inbox.chatwoot_bridge import ChatwootCoreWebhookBridge
from klaint.inbox.profiles_tickets import InboxManager
from klaint.knowledge.rag import HybridKnowledgeEngine
from klaint.procedures.engine import ProceduresEngine
from klaint.resolution.engine import ResolutionEngine
from klaint.simulation.suite import KlaintSimulationRunner
from klaint.storage.tenant_db import TenantStorageRegistry
from klaint.ui import load_static_asset, load_studio_html, load_widget_html


@dataclass(frozen=True)
class OperatorPrincipal:
    session_id: str
    tenant_id: str
    operator_id: str
    role: str
    issued_at: str


MAX_HTTP_BODY_BYTES = 2 * 1024 * 1024


class OperatorAuthenticator:
    """HMAC-SHA256 operator session manager binding authenticated operators to a specific tenant."""

    def __init__(self, secret: bytes | None = None) -> None:
        self._secret = secret or secrets.token_bytes(32)
        self._lock = threading.RLock()
        self._sessions: dict[str, OperatorPrincipal] = {}

    def login(self, *, tenant_id: str, operator_id: str, role: str = "operator") -> tuple[OperatorPrincipal, str]:
        slug = validate_tenant_id(tenant_id)
        clean_op = operator_id.strip()
        if not clean_op:
            raise AuthorityViolationError("operator_id cannot be empty")
        op_sid = new_id("ops", 10)
        principal = OperatorPrincipal(
            session_id=op_sid,
            tenant_id=slug,
            operator_id=clean_op,
            role=role,
            issued_at=iso_utc(),
        )
        with self._lock:
            self._sessions[op_sid] = principal
        payload = {
            "session_id": principal.session_id,
            "tenant_id": principal.tenant_id,
            "operator_id": principal.operator_id,
            "role": principal.role,
            "issued_at": principal.issued_at,
        }
        mac = hmac.new(self._secret, jcs_dumps(payload), hashlib.sha256).hexdigest()
        return principal, f"{op_sid}.{mac}"

    def verify(self, token: str, expected_tenant_id: str) -> OperatorPrincipal:
        if "." not in token:
            raise AuthorityViolationError("Malformed operator session token")
        op_sid, mac = token.split(".", 1)
        with self._lock:
            principal = self._sessions.get(op_sid)
        if principal is None:
            raise AuthorityViolationError("Unknown or expired operator session")
        payload = {
            "session_id": principal.session_id,
            "tenant_id": principal.tenant_id,
            "operator_id": principal.operator_id,
            "role": principal.role,
            "issued_at": principal.issued_at,
        }
        expected_mac = hmac.new(self._secret, jcs_dumps(payload), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(mac, expected_mac):
            raise AuthorityViolationError("Operator session token HMAC mismatch")
        if principal.tenant_id != validate_tenant_id(expected_tenant_id):
            raise TenantIsolationError(
                f"Cross-tenant operator token denied: token bound to {principal.tenant_id!r}, requested {expected_tenant_id!r}"
            )
        return principal


class KlaintApplication:
    """Self-contained Klaint application container wiring storage, broker subprocess, inbox, analytics, and webhooks."""

    def __init__(
        self,
        data_dir: Path | str,
        *,
        default_tenant_id: str = "default-tenant",
        default_api_key: str | None = None,
        webhook_secrets: dict[str, str | bytes] | None = None,
    ) -> None:
        self.data_dir = Path(data_dir).resolve()
        self.default_tenant_id = validate_tenant_id(default_tenant_id)
        resolved_api_key = default_api_key or f"klaint-{secrets.token_urlsafe(24)}"
        if len(resolved_api_key) < 12:
            raise ValueError("default_api_key must be at least 12 characters")
        self.default_api_key = resolved_api_key
        ephemeral_wh_secret = "whsec_" + base64.b64encode(secrets.token_bytes(32)).decode("ascii")
        self.storage = TenantStorageRegistry(self.data_dir)
        self.broker = BrokerClient(self.data_dir)
        self.customer_auth = SessionAuthenticator()
        self.operator_auth = OperatorAuthenticator()
        self.resolution = ResolutionEngine(storage=self.storage, broker=self.broker)
        self.inbox = InboxManager(self.storage, session_auth=self.customer_auth)
        self.analytics = AnalyticsEngine(self.storage)
        self.webhooks = ChatwootCoreWebhookBridge(
            inbox=self.inbox,
            tenant_secrets=webhook_secrets or {self.default_tenant_id: ephemeral_wh_secret},
        )
        self._key_lock = threading.RLock()
        self._api_keys: dict[str, str] = {self.default_api_key: self.default_tenant_id}
        self._closed = False

        # Ensure baseline SOPs for default tenant
        ProceduresEngine(self.storage.for_tenant(self.default_tenant_id)).bootstrap_defaults()

    def is_registered_tenant(self, tenant_id: str) -> bool:
        slug = validate_tenant_id(tenant_id)
        with self._key_lock:
            return slug in set(self._api_keys.values())

    def register_tenant_api_key(self, tenant_id: str, api_key: str) -> None:
        slug = validate_tenant_id(tenant_id)
        if not api_key or len(api_key) < 12:
            raise ValueError("Tenant API key must be at least 12 characters")
        with self._key_lock:
            self._api_keys[api_key] = slug
        ProceduresEngine(self.storage.for_tenant(slug)).bootstrap_defaults()

    def authenticate_api_key(self, api_key: str | None, requested_tenant: str | None = None) -> str:
        if not api_key:
            raise AuthorityViolationError("Missing X-Klaint-Api-Key header")
        with self._key_lock:
            bound_tenant = self._api_keys.get(api_key)
        if bound_tenant is None:
            raise AuthorityViolationError("Invalid tenant API key")
        if requested_tenant is not None and validate_tenant_id(requested_tenant) != bound_tenant:
            raise TenantIsolationError(
                f"API key bound to tenant {bound_tenant!r} cannot access tenant {requested_tenant!r}"
            )
        return bound_tenant

    def connectors(self, tenant_id: str) -> BusinessConnectorSuite:
        return BusinessConnectorSuite(self.storage.for_tenant(validate_tenant_id(tenant_id)))

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self.broker.close()
            self.storage.close_all()


_CONV_ACTION_RE = re.compile(r"^/api/v1/conversations/([A-Za-z0-9_-]+)/(takeover|return-to-ai)$")
_TURN_WHY_RE = re.compile(r"^/api/v1/turns/([A-Za-z0-9_-]+)/why$")
_APPROVAL_DECIDE_RE = re.compile(r"^/api/v1/approvals/([A-Za-z0-9_-]+)/decide$")
_TICKET_ID_RE = re.compile(r"^/api/v1/tickets/([A-Za-z0-9_-]+)(/notes)?$")
_WEBHOOK_RE = re.compile(r"^/api/v1/webhooks/chatwoot/([^/]+)$")


class KlaintHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, server_address: tuple[str, int], app: KlaintApplication) -> None:
        self.app = app
        super().__init__(server_address, _KlaintRequestHandler)


class _KlaintRequestHandler(BaseHTTPRequestHandler):
    server: KlaintHTTPServer

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return  # Keep test & console output clean and structured

    def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, raw, "application/json; charset=utf-8")

    def _read_raw_body(self) -> bytes:
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
        except ValueError as exc:
            raise KlaintError("Invalid Content-Length header") from exc
        if length < 0 or length > MAX_HTTP_BODY_BYTES:
            raise KlaintError(f"Request body size {length} exceeds maximum {MAX_HTTP_BODY_BYTES} bytes")
        return self.rfile.read(length) if length > 0 else b""

    def _read_json_body(self) -> dict[str, Any]:
        raw = self._read_raw_body()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise KlaintError("Malformed UTF-8 JSON request body") from exc
        if not isinstance(parsed, dict):
            raise KlaintError("JSON request body must be an object")
        return parsed

    def _require_tenant_key(self) -> str:
        key = self.headers.get("X-Klaint-Api-Key")
        if not key:
            auth = self.headers.get("Authorization", "")
            if auth.lower().startswith("bearer "):
                key = auth[7:].strip()
        requested_tenant = self.headers.get("X-Klaint-Tenant")
        return self.server.app.authenticate_api_key(key, requested_tenant=requested_tenant)

    def _require_operator(self, tenant_id: str) -> OperatorPrincipal:
        tok = self.headers.get("X-Klaint-Operator-Token", "")
        if not tok:
            raise AuthorityViolationError("Missing X-Klaint-Operator-Token header")
        return self.server.app.operator_auth.verify(tok, expected_tenant_id=tenant_id)

    def _handle_error(self, exc: Exception) -> None:
        if isinstance(exc, WebhookVerificationError):
            self._send_json(HTTPStatus.UNAUTHORIZED, {"ok": False, "error_type": type(exc).__name__, "error": str(exc)})
        elif isinstance(exc, TenantIsolationError):
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error_type": type(exc).__name__, "error": str(exc)})
        elif isinstance(exc, FourEyesViolationError):
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error_type": type(exc).__name__, "error": str(exc)})
        elif isinstance(exc, AuthorityViolationError):
            self._send_json(HTTPStatus.UNAUTHORIZED, {"ok": False, "error_type": type(exc).__name__, "error": str(exc)})
        elif isinstance(exc, StaleEpochError):
            self._send_json(HTTPStatus.CONFLICT, {"ok": False, "error_type": type(exc).__name__, "error": str(exc)})
        elif isinstance(exc, KlaintError):
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error_type": type(exc).__name__, "error": str(exc)})
        else:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "error_type": type(exc).__name__, "error": str(exc)},
            )

    # ------------------------------------------------------------------
    # HTTP GET
    # ------------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        app = self.server.app

        try:
            if path == "/":
                self._send_bytes(HTTPStatus.OK, load_studio_html(), "text/html; charset=utf-8")
                return
            if path == "/widget":
                self._send_bytes(HTTPStatus.OK, load_widget_html(), "text/html; charset=utf-8")
                return
            if path.startswith("/static/"):
                asset_name = path[len("/static/") :]
                asset = load_static_asset(asset_name)
                if asset is None:
                    self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Static asset not found"})
                else:
                    self._send_bytes(HTTPStatus.OK, asset[0], asset[1])
                return
            if path == "/api/v1/health":
                b_info = app.broker.info()
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "healthy",
                        "product": "Klaint",
                        "ecosystem": "Wispral",
                        "broker_pid": b_info["pid"],
                        "output_gate_mode": "BLOCK",
                    },
                )
                return

            tenant_id = self._require_tenant_key()
            db = app.storage.for_tenant(tenant_id)
            qs = parse_qs(parsed.query)

            if path == "/api/v1/overview":
                self._send_json(HTTPStatus.OK, app.analytics.compute_overview(tenant_id))
                return

            if path == "/api/v1/conversations":
                self._send_json(HTTPStatus.OK, {"conversations": app.inbox.list_conversations(tenant_id)})
                return

            m_why = _TURN_WHY_RE.match(path)
            if m_why:
                turn_id = m_why.group(1)
                with db.read_connection() as conn:
                    row = conn.execute(
                        "SELECT trace_json FROM conversation_turns WHERE tenant_id = ? AND turn_id = ?",
                        (tenant_id, turn_id),
                    ).fetchone()
                if row is None:
                    raise TenantIsolationError(f"Turn {turn_id!r} not found in tenant {tenant_id!r}")
                self._send_json(HTTPStatus.OK, json.loads(str(row["trace_json"])))
                return

            if path == "/api/v1/tickets":
                status_filter = qs.get("status", [None])[0]
                self._send_json(HTTPStatus.OK, {"tickets": app.inbox.list_tickets(tenant_id, status=status_filter)})
                return

            if path == "/api/v1/procedures":
                versions = [v.to_dict() for v in ProceduresEngine(db).list_sop_versions()]
                self._send_json(HTTPStatus.OK, {"versions": versions})
                return

            if path == "/api/v1/knowledge":
                docs = HybridKnowledgeEngine(db).list_documents()
                self._send_json(HTTPStatus.OK, {"documents": docs})
                return

            if path == "/api/v1/approvals":
                with db.read_connection() as conn:
                    rows = conn.execute(
                        "SELECT * FROM approval_queue WHERE tenant_id = ? ORDER BY created_at DESC",
                        (tenant_id,),
                    ).fetchall()
                self._send_json(HTTPStatus.OK, {"approvals": [dict(r) for r in rows]})
                return

            if path == "/api/v1/audit":
                events = db.list_audit_events(limit=200)
                if qs.get("format", ["json"])[0] == "csv":
                    buf = io.StringIO()
                    writer = csv.writer(buf)
                    writer.writerow(["seq", "event_kind", "actor", "session_id", "policy_version", "entry_digest", "created_at"])
                    for ev in events:
                        writer.writerow(
                            [
                                ev.get("seq"),
                                ev.get("event_kind"),
                                ev.get("actor"),
                                ev.get("session_id") or "",
                                ev.get("policy_version") or "",
                                ev.get("entry_digest"),
                                ev.get("created_at"),
                            ]
                        )
                    self._send_bytes(HTTPStatus.OK, buf.getvalue().encode("utf-8"), "text/csv; charset=utf-8")
                else:
                    self._send_json(HTTPStatus.OK, {"events": events})
                return

            if path == "/api/v1/audit/verify":
                v = db.verify_audit_chain()
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "tenant_id": v.tenant_id,
                        "valid": v.valid,
                        "total_entries": v.total_entries,
                        "head_digest": v.head_digest,
                        "broken_at_seq": v.broken_at_seq,
                        "reason": v.reason,
                    },
                )
                return

            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": f"Unknown route {path!r}"})
        except Exception as exc:
            self._handle_error(exc)

    # ------------------------------------------------------------------
    # HTTP POST & PATCH
    # ------------------------------------------------------------------

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        app = self.server.app

        try:
            # 1. Raw-byte Chatwoot Standard Webhooks endpoint (uses webhook HMAC, not Studio API key)
            m_wh = _WEBHOOK_RE.match(path)
            if m_wh:
                wh_tenant = m_wh.group(1)
                raw_body = self._read_raw_body()
                hdrs = {k: v for k, v in self.headers.items()}
                result = app.webhooks.handle_webhook(tenant_id=wh_tenant, headers=hdrs, raw_body=raw_body)
                self._send_json(HTTPStatus.OK, {"ok": True, **result})
                return

            # 2. Customer Web Chat Widget endpoints
            if path == "/api/v1/widget/session":
                body = self._read_json_body()
                supplied_customer = body.get("customer_id")
                lang = str(body.get("language", "en"))

                if supplied_customer is not None and str(supplied_customer).strip() != "":
                    # Caller-supplied customer_id strictly requires tenant API key authentication!
                    auth_tenant = self._require_tenant_key()
                    requested_tenant = validate_tenant_id(str(body.get("tenant_id", auth_tenant)))
                    if requested_tenant != auth_tenant:
                        raise TenantIsolationError(
                            f"API key bound to {auth_tenant!r} cannot mint customer session for {requested_tenant!r}"
                        )
                    tenant_id = auth_tenant
                    customer_id = str(supplied_customer).strip()
                else:
                    # Unauthenticated public widget: registered tenants ONLY + fresh server-minted anonymous ID
                    tenant_id = validate_tenant_id(str(body.get("tenant_id", app.default_tenant_id)))
                    if not app.is_registered_tenant(tenant_id):
                        raise TenantIsolationError(f"Tenant {tenant_id!r} is not registered for widget sessions")
                    customer_id = new_id("anon", 8)

                session, cust_token = app.customer_auth.create_session(
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    channel="web_widget",
                    language=lang,
                )
                conv = app.resolution.ensure_conversation(session)
                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "session_id": session.session_id,
                        "customer_id": session.customer_id,
                        "conversation_id": conv["conversation_id"],
                        "customer_token": cust_token,
                        "ownership_epoch": conv["ownership_epoch"],
                    },
                )
                return

            if path == "/api/v1/widget/messages":
                cust_token = self.headers.get("X-Klaint-Customer-Token", "")
                session = app.customer_auth.verify_token(cust_token)
                body = self._read_json_body()
                message = str(body.get("message", ""))

                raw_delay = body.get("simulate_ai_delay_ms")
                raw_draft_override = body.get("draft_override")
                if raw_draft_override is not None or (raw_delay is not None and int(raw_delay) != 0):
                    auth_tenant = self._require_tenant_key()
                    if auth_tenant != session.tenant_id:
                        raise TenantIsolationError("API key tenant mismatch on privileged widget test parameters")
                    sim_delay_ms = max(0, min(5000, int(raw_delay or 0)))
                    draft_override = str(raw_draft_override) if raw_draft_override is not None else None
                else:
                    sim_delay_ms = 0
                    draft_override = None

                def _pre_commit() -> None:
                    if sim_delay_ms > 0:
                        time.sleep(sim_delay_ms / 1000.0)

                turn_res = app.resolution.resolve_turn(
                    session=session,
                    customer_text=message,
                    draft_override=draft_override,
                    pre_commit_hook=_pre_commit if sim_delay_ms > 0 else None,
                )
                self._send_json(HTTPStatus.OK, turn_res.to_dict())
                return

            if path == "/api/v1/widget/escalate":
                cust_token = self.headers.get("X-Klaint-Customer-Token", "")
                session = app.customer_auth.verify_token(cust_token)
                turn_res = app.resolution.resolve_turn(
                    session=session,
                    customer_text="Talk to a human specialist",
                )
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "resolution_status": turn_res.resolution_status,
                        "message": turn_res.assistant_text,
                    },
                )
                return

            # 3. Authenticated Studio Tenant & Operator endpoints
            tenant_id = self._require_tenant_key()
            db = app.storage.for_tenant(tenant_id)
            body = self._read_json_body()

            if path == "/api/v1/auth/operator-login":
                principal, op_token = app.operator_auth.login(
                    tenant_id=tenant_id,
                    operator_id=str(body.get("operator_id", "")),
                    role=str(body.get("role", "operator")),
                )
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "operator_token": op_token,
                        "operator_id": principal.operator_id,
                        "tenant_id": principal.tenant_id,
                        "role": principal.role,
                    },
                )
                return

            m_conv = _CONV_ACTION_RE.match(path)
            if m_conv:
                op = self._require_operator(tenant_id)
                conv_id, action = m_conv.group(1), m_conv.group(2)
                if action == "takeover":
                    out = app.inbox.take_over_conversation(
                        tenant_id=tenant_id,
                        conversation_id=conv_id,
                        operator_id=op.operator_id,
                    )
                else:
                    out = app.inbox.return_to_ai(
                        tenant_id=tenant_id,
                        conversation_id=conv_id,
                        operator_id=op.operator_id,
                    )
                self._send_json(HTTPStatus.OK, out)
                return

            if path == "/api/v1/tickets":
                op = self._require_operator(tenant_id)
                tkt = app.inbox.create_ticket(
                    tenant_id=tenant_id,
                    customer_id=str(body["customer_id"]),
                    subject=str(body["subject"]),
                    priority=body.get("priority", "normal"),
                    status=body.get("status", "open"),
                    conversation_id=body.get("conversation_id"),
                    assigned_operator_id=body.get("assigned_operator_id", op.operator_id),
                )
                self._send_json(HTTPStatus.CREATED, tkt)
                return

            m_tkt_notes = _TICKET_ID_RE.match(path)
            if m_tkt_notes and m_tkt_notes.group(2) == "/notes":
                op = self._require_operator(tenant_id)
                note = app.inbox.add_internal_note(
                    tenant_id=tenant_id,
                    ticket_id=m_tkt_notes.group(1),
                    author_id=op.operator_id,
                    body=str(body.get("body", "")),
                )
                self._send_json(HTTPStatus.CREATED, note)
                return

            if path == "/api/v1/procedures/drafts":
                op = self._require_operator(tenant_id)
                rec = ProceduresEngine(db).create_sop_draft(
                    domain=body["domain"],
                    title=str(body["title"]),
                    author_id=op.operator_id,
                    natural_language_text=str(body["natural_language_text"]),
                    sop_id=body.get("sop_id"),
                )
                self._send_json(HTTPStatus.CREATED, rec.to_dict())
                return

            if path == "/api/v1/procedures/approve":
                op = self._require_operator(tenant_id)
                rec = ProceduresEngine(db).approve_sop_version(
                    sop_id=str(body["sop_id"]),
                    version_num=int(body["version_num"]),
                    approver_id=op.operator_id,
                )
                self._send_json(HTTPStatus.OK, rec.to_dict())
                return

            if path == "/api/v1/procedures/rollback":
                op = self._require_operator(tenant_id)
                rec = ProceduresEngine(db).rollback_sop(
                    sop_id=str(body["sop_id"]),
                    target_version_num=int(body["target_version_num"]),
                    operator_id=op.operator_id,
                )
                self._send_json(HTTPStatus.OK, rec.to_dict())
                return

            if path == "/api/v1/knowledge/ingest":
                self._require_operator(tenant_id)
                ingested = HybridKnowledgeEngine(db).ingest_document(
                    title=str(body["title"]),
                    content=str(body["content"]),
                    language=str(body.get("language", "en")),
                    acl_tags=body.get("acl_tags", ["public", "customer"]),
                    doc_id=body.get("doc_id"),
                )
                self._send_json(HTTPStatus.CREATED, ingested)
                return

            if path == "/api/v1/knowledge/search":
                acl_tags = tuple(body.get("acl_tags", ["public", "customer"]))
                probe_session = AuthenticatedSession(
                    session_id=new_id("ses", 8),
                    tenant_id=tenant_id,
                    customer_id="studio-operator-preview",
                    acl_tags=acl_tags,
                )
                search_res = HybridKnowledgeEngine(db).search(
                    session=probe_session,
                    query=str(body.get("query", "")),
                )
                self._send_json(HTTPStatus.OK, search_res.to_dict())
                return

            m_apr = _APPROVAL_DECIDE_RE.match(path)
            if m_apr:
                op = self._require_operator(tenant_id)
                decided = app.resolution.decide_approval(
                    tenant_id=tenant_id,
                    approval_id=m_apr.group(1),
                    operator_id=op.operator_id,
                    approve=bool(body.get("approve", False)),
                    note=str(body.get("note", "")),
                )
                self._send_json(HTTPStatus.OK, decided)
                return

            if path == "/api/v1/simulation/run":
                self._require_operator(tenant_id)
                # Run simulation in an isolated temporary directory so live tenant data_dir is never polluted!
                with tempfile.TemporaryDirectory(prefix="klaint_sim_isolated_") as tmp_sim_dir:
                    runner = KlaintSimulationRunner(data_dir=Path(tmp_sim_dir))
                    report = runner.run_suite()
                self._send_json(HTTPStatus.OK, report)
                return

            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": f"Unknown POST route {path!r}"})
        except Exception as exc:
            self._handle_error(exc)

    def do_PATCH(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        app = self.server.app
        try:
            tenant_id = self._require_tenant_key()
            op = self._require_operator(tenant_id)
            m_tkt = _TICKET_ID_RE.match(path)
            if m_tkt and m_tkt.group(2) is None:
                body = self._read_json_body()
                updated = app.inbox.update_ticket(
                    tenant_id=tenant_id,
                    ticket_id=m_tkt.group(1),
                    operator_id=op.operator_id,
                    status=body.get("status"),
                    assigned_operator_id=body.get("assigned_operator_id"),
                    priority=body.get("priority"),
                )
                self._send_json(HTTPStatus.OK, updated)
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": f"Unknown PATCH route {path!r}"})
        except Exception as exc:
            self._handle_error(exc)


def start_background_server(
    app: KlaintApplication,
    host: str = "127.0.0.1",
    port: int = 0,
) -> tuple[KlaintHTTPServer, threading.Thread, str]:
    """Start `KlaintHTTPServer` in a daemon thread and return `(server, thread, base_url)`."""
    httpd = KlaintHTTPServer((host, port), app)
    bound_host, bound_port = httpd.server_address[0], httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, name="klaint-http-server", daemon=True)
    thread.start()
    return httpd, thread, f"http://{bound_host}:{bound_port}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="klaint-server", description="Klaint Studio & Verified Resolution Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument("--data-dir", default=".klaint_data")
    parser.add_argument("--tenant-id", default="default-tenant")
    ns = parser.parse_args(argv)

    env_api_key = os.environ.get("KLAINT_API_KEY") or f"klaint-{secrets.token_urlsafe(24)}"
    env_wh_secret = os.environ.get("KLAINT_WEBHOOK_SECRET") or (
        "whsec_" + base64.b64encode(secrets.token_bytes(32)).decode("ascii")
    )
    app = KlaintApplication(
        ns.data_dir,
        default_tenant_id=ns.tenant_id,
        default_api_key=env_api_key,
        webhook_secrets={ns.tenant_id: env_wh_secret},
    )
    httpd = KlaintHTTPServer((ns.host, ns.port), app)
    try:
        print(f"Klaint Studio listening on http://{ns.host}:{ns.port} (broker_pid={app.broker.broker_pid})")
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        app.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
