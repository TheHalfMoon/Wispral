# SPDX-License-Identifier: Apache-2.0
"""Klaint error hierarchy for deterministic security, authority, and ledger boundaries."""

from __future__ import annotations


class KlaintError(Exception):
    """Base exception for all deterministic Klaint platform errors."""


class TenantIsolationError(KlaintError, ValueError):
    """Raised on invalid tenant slug, path traversal attempt, or cross-tenant access."""


class AuthorityViolationError(KlaintError, PermissionError):
    """Raised when untrusted input attempts to forge or override server-derived authority."""


class ForgedIdentityError(AuthorityViolationError):
    """Raised when tool arguments or untrusted payloads supply or spoof customer_id/tenant_id."""


class CanonicalSerializationError(KlaintError, TypeError):
    """Raised when canonical JCS serialization encounters forbidden types such as IEEE-754 floats."""


class CapabilityError(KlaintError, PermissionError):
    """Raised when an Ed25519 capability token fails issuance or verification."""


class ExpiredCapabilityError(CapabilityError):
    """Raised when a capability token exceeds its <= 60s TTL or is used after expires_at."""


class ReplayNonceError(CapabilityError):
    """Raised when a single-use capability nonce has already been consumed."""


class StaleEpochError(KlaintError):
    """Raised when an AI generation or broker dispatch carries a superseded ownership_epoch."""


class IntentTransitionError(KlaintError):
    """Raised on an illegal effect_intent state transition."""


class FourEyesViolationError(AuthorityViolationError):
    """Raised when an SOP author attempts to approve their own SOP version."""


class ConnectorTimeoutError(KlaintError, TimeoutError):
    """Raised when an external or synthetic business connector times out mid-flight."""


class WebhookVerificationError(KlaintError, PermissionError):
    """Raised when a Standard Webhooks HMAC signature, timestamp skew, or replay check fails."""
