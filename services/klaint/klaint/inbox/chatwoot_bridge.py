# SPDX-License-Identifier: Apache-2.0
"""Chatwoot MIT Core API Webhook Bridge using Standard Webhooks HMAC-SHA256 verification.

Compatibility & Provenance:
- Standard Webhooks (`standard-webhooks/standard-webhooks@ab6844147ce9cdb0d2dbf2e60d1ea85001fd2554`, Apache-2.0):
  raw-byte `v1,<base64(HMAC-SHA256(secret, "{id}.{timestamp}.{raw_body}"))>`, +/- 300s timestamp skew check,
  and SQLite atomic `webhook-id` replay cache.
- Chatwoot Core API (`chatwoot/chatwoot@caab07a8f00032d5205b5a5d7e2eb0ba2f3d2d82`, MIT):
  strictly MIT Core webhook events (`conversation_updated`, `message_created`, `conversation_status_changed`).
  Zero Chatwoot Enterprise Edition (`enterprise/`) paths or features are used or accepted.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import sqlite3
import time
from typing import Any

from klaint.core.errors import WebhookVerificationError
from klaint.core.models import iso_utc, new_id, validate_tenant_id
from klaint.inbox.profiles_tickets import InboxManager, ensure_inbox_schema

WEBHOOK_TOLERANCE_SECONDS = 300
_SECRET_PREFIX = "whsec_"
ALLOWED_CHATWOOT_CORE_EVENTS: frozenset[str] = frozenset(
    {
        "conversation_created",
        "conversation_updated",
        "conversation_status_changed",
        "message_created",
    }
)


def decode_standard_webhook_secret(secret: str | bytes) -> bytes:
    if isinstance(secret, bytes):
        if len(secret) < 16:
            raise ValueError("Webhook secret must be at least 16 bytes")
        return secret
    if secret.startswith(_SECRET_PREFIX):
        b64_part = secret[len(_SECRET_PREFIX) :]
        pad = "=" * ((4 - (len(b64_part) % 4)) % 4)
        decoded = base64.b64decode(b64_part + pad)
        if len(decoded) < 16:
            raise ValueError("Decoded whsec_ secret must be at least 16 bytes")
        return decoded
    raw = secret.encode("utf-8")
    if len(raw) < 16:
        raise ValueError("Webhook secret must be at least 16 bytes")
    return raw


def sign_standard_webhook(
    *,
    secret: str | bytes,
    webhook_id: str,
    webhook_timestamp: int | str,
    raw_body: bytes,
) -> str:
    """Compute a Standard Webhooks `v1,<base64>` header value over exact `raw_body` bytes."""
    key = decode_standard_webhook_secret(secret)
    prefix = f"{webhook_id}.{webhook_timestamp}.".encode("ascii")
    digest = hmac.new(key, prefix + raw_body, hashlib.sha256).digest()
    return "v1," + base64.b64encode(digest).decode("ascii")


class ChatwootCoreWebhookBridge:
    """Verifies Standard Webhooks signatures and synchronizes Chatwoot MIT Core events with `InboxManager`."""

    def __init__(
        self,
        *,
        inbox: InboxManager,
        tenant_secrets: dict[str, str | bytes],
        tolerance_seconds: int = WEBHOOK_TOLERANCE_SECONDS,
    ) -> None:
        self.inbox = inbox
        self._secrets: dict[str, bytes] = {
            validate_tenant_id(tid): decode_standard_webhook_secret(sec)
            for tid, sec in tenant_secrets.items()
        }
        self.tolerance_seconds = tolerance_seconds

    def register_tenant_secret(self, tenant_id: str, secret: str | bytes) -> None:
        self._secrets[validate_tenant_id(tenant_id)] = decode_standard_webhook_secret(secret)

    def handle_webhook(
        self,
        *,
        tenant_id: str,
        headers: dict[str, str],
        raw_body: bytes,
        now_unix: int | None = None,
    ) -> dict[str, Any]:
        """Verify Standard Webhooks headers + raw_body HMAC + +/-300s skew + SQLite replay cache, then process."""
        slug = validate_tenant_id(tenant_id)
        secret_bytes = self._secrets.get(slug)
        if secret_bytes is None:
            raise WebhookVerificationError(f"No webhook signing secret configured for tenant {slug!r}")

        if not isinstance(raw_body, (bytes, bytearray)):
            raise WebhookVerificationError("Webhook verification requires exact raw HTTP body bytes")
        raw_bytes = bytes(raw_body)

        lower_headers = {k.lower(): v.strip() for k, v in headers.items()}
        msg_id = lower_headers.get("webhook-id", "")
        msg_ts_str = lower_headers.get("webhook-timestamp", "")
        msg_sig_header = lower_headers.get("webhook-signature", "")

        if not msg_id or not msg_ts_str or not msg_sig_header:
            raise WebhookVerificationError(
                "Missing required Standard Webhooks headers (webhook-id, webhook-timestamp, webhook-signature)"
            )

        try:
            msg_ts = int(msg_ts_str)
        except ValueError as exc:
            raise WebhookVerificationError("Invalid non-integer webhook-timestamp header") from exc

        eval_unix = int(time.time()) if now_unix is None else int(now_unix)
        if abs(eval_unix - msg_ts) > self.tolerance_seconds:
            raise WebhookVerificationError(
                f"Stale or future webhook-timestamp={msg_ts} outside +/-{self.tolerance_seconds}s window (now={eval_unix})"
            )

        signed_payload = f"{msg_id}.{msg_ts}.".encode("ascii") + raw_bytes
        expected_b64 = base64.b64encode(hmac.new(secret_bytes, signed_payload, hashlib.sha256).digest()).decode("ascii")

        matched_sig = False
        for candidate in msg_sig_header.split(" "):
            candidate = candidate.strip()
            if not candidate:
                continue
            parts = candidate.split(",", 1)
            if len(parts) == 2 and parts[0] == "v1":
                if hmac.compare_digest(parts[1], expected_b64):
                    matched_sig = True
                    break

        if not matched_sig:
            raise WebhookVerificationError("Standard Webhooks HMAC-SHA256 signature verification failed")

        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WebhookVerificationError("Malformed UTF-8 JSON body in verified webhook") from exc

        # Strictly forbid Chatwoot Enterprise Edition (`enterprise/`) paths/attributes
        if "enterprise" in payload or str(payload.get("source_path", "")).startswith("enterprise/"):
            raise WebhookVerificationError("Chatwoot Enterprise Edition payloads are unsupported; MIT Core API only")

        event_name = str(payload.get("event", ""))
        if event_name not in ALLOWED_CHATWOOT_CORE_EVENTS:
            raise WebhookVerificationError(
                f"Unsupported Chatwoot webhook event {event_name!r}; only MIT Core allowlisted events are accepted"
            )

        db = self.inbox.storage.for_tenant(slug)
        ensure_inbox_schema(db)
        body_sha = hashlib.sha256(raw_bytes).hexdigest()

        # Atomic replay-cache insert inside BEGIN IMMEDIATE
        with db.immediate_transaction() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO webhook_replay_cache (webhook_id, tenant_id, received_timestamp, payload_sha256, processed_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (msg_id, slug, msg_ts, body_sha, iso_utc()),
                )
            except sqlite3.IntegrityError as exc:
                raise WebhookVerificationError(f"Replay detected: webhook-id {msg_id!r} was already processed") from exc

            db.append_audit(
                event_kind="chatwoot_webhook_verified",
                actor="chatwoot_core_bridge",
                payload={"webhook_id": msg_id, "event": str(payload.get("event", "unknown"))},
                conn=conn,
            )

        return self._apply_core_event(slug, payload)

    def _apply_core_event(self, tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        event = str(payload.get("event", ""))
        conv_meta = payload.get("conversation") or {}
        klaint_conv_id = str(
            conv_meta.get("custom_attributes", {}).get("klaint_conversation_id")
            or payload.get("klaint_conversation_id")
            or ""
        )
        sender = payload.get("sender") or conv_meta.get("meta", {}).get("sender") or {}
        customer_id = str(sender.get("identifier") or f"cw-contact-{sender.get('id', 'unknown')}")

        if sender.get("name") or sender.get("email"):
            self.inbox.upsert_customer_profile(
                tenant_id=tenant_id,
                customer_id=customer_id,
                display_name=str(sender.get("name") or customer_id),
                email=sender.get("email"),
                phone=sender.get("phone_number"),
            )

        if event in ("conversation_updated", "conversation_status_changed") and klaint_conv_id:
            assignee = conv_meta.get("meta", {}).get("assignee") or payload.get("assignee")
            if assignee and assignee.get("id"):
                operator_id = f"chatwoot_agent_{assignee['id']}"
                state = self.inbox.take_over_conversation(
                    tenant_id=tenant_id,
                    conversation_id=klaint_conv_id,
                    operator_id=operator_id,
                )
                return {"handled": True, "action": "human_takeover", **state}
            if payload.get("return_to_ai") is True:
                operator_id = str(payload.get("operator_id", "chatwoot_bot_handoff"))
                state = self.inbox.return_to_ai(
                    tenant_id=tenant_id,
                    conversation_id=klaint_conv_id,
                    operator_id=operator_id,
                )
                return {"handled": True, "action": "returned_to_ai", **state}

        if event in ("message_created", "conversation_created"):
            subject = str(payload.get("content", "Chatwoot Core conversation"))[:80] or "Chatwoot Core conversation"
            ticket = self.inbox.create_ticket(
                tenant_id=tenant_id,
                customer_id=customer_id,
                subject=subject,
                conversation_id=klaint_conv_id or None,
                session_id=new_id("ses", 8) if not klaint_conv_id else None,
            )
            return {"handled": True, "action": "ticket_synced", "ticket_id": ticket["ticket_id"]}

        return {"handled": True, "action": "acknowledged", "event": event}
