# SPDX-License-Identifier: Apache-2.0
"""RFC 8785 JSON Canonicalization Scheme (JCS) with strict IEEE-754 float rejection."""

from __future__ import annotations

import hashlib
from typing import Any

from klaint.core.errors import CanonicalSerializationError

_ESCAPE_MAP: dict[int, str] = {
    0x08: "\\b",
    0x09: "\\t",
    0x0A: "\\n",
    0x0C: "\\f",
    0x0D: "\\r",
    0x22: '\\"',
    0x5C: "\\\\",
}


def _encode_jcs_string(value: str) -> str:
    out: list[str] = ['"']
    for ch in value:
        code = ord(ch)
        if 0xD800 <= code <= 0xDFFF:
            raise CanonicalSerializationError("Lone UTF-16 surrogates are invalid in RFC 8785 JCS strings")
        escaped = _ESCAPE_MAP.get(code)
        if escaped is not None:
            out.append(escaped)
        elif code < 0x20:
            out.append(f"\\u{code:04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _utf16_sort_key(key: str) -> bytes:
    for ch in key:
        if 0xD800 <= ord(ch) <= 0xDFFF:
            raise CanonicalSerializationError("Lone UTF-16 surrogates are invalid in RFC 8785 JCS object keys")
    return key.encode("utf-16-be")


def _serialize_jcs(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        raise CanonicalSerializationError(
            "IEEE-754 floats are forbidden in signed canonical JSON; use integer minor units (cents) or strings"
        )
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return _encode_jcs_string(value)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_serialize_jcs(item) for item in value) + "]"
    if isinstance(value, dict):
        items: list[tuple[bytes, str, Any]] = []
        for k, v in value.items():
            if not isinstance(k, str):
                raise CanonicalSerializationError(f"Object keys must be strings in JCS, got {type(k).__name__}")
            items.append((_utf16_sort_key(k), k, v))
        items.sort(key=lambda row: row[0])
        return "{" + ",".join(f"{_encode_jcs_string(k)}:{_serialize_jcs(v)}" for _, k, v in items) + "}"
    raise CanonicalSerializationError(f"Unsupported type for RFC 8785 JCS serialization: {type(value).__name__}")


def jcs_str(value: Any) -> str:
    """Serialize `value` to an RFC 8785 JCS canonical string, rejecting IEEE-754 floats."""
    return _serialize_jcs(value)


def jcs_dumps(value: Any) -> bytes:
    """Serialize `value` to UTF-8 bytes under RFC 8785 JCS, rejecting IEEE-754 floats."""
    return _serialize_jcs(value).encode("utf-8")


def compute_args_digest(args: dict[str, Any]) -> str:
    """Compute `sha256:<hex>` over the RFC 8785 JCS canonical encoding of `args`."""
    if not isinstance(args, dict):
        raise CanonicalSerializationError("Tool arguments must be a JSON object (dict)")
    digest = hashlib.sha256(jcs_dumps(args)).hexdigest()
    return f"sha256:{digest}"


def derive_idempotency_key(
    tenant_id: str,
    conversation_id: str,
    tool: str,
    args: dict[str, Any],
    turn_seq: int = 0,
) -> str:
    """Derive deterministic Klaint idempotency key `H(tenant, conversation, tool, canonical_args, turn_seq)`."""
    payload = {
        "tenant_id": tenant_id,
        "conversation_id": conversation_id,
        "tool": tool,
        "args": args,
        "turn_seq": turn_seq,
    }
    digest = hashlib.sha256(jcs_dumps(payload)).hexdigest()[:48]
    return f"idem-{digest}"
