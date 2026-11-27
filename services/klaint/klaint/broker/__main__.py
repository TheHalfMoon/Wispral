# SPDX-License-Identifier: Apache-2.0
"""Separate OS subprocess entrypoint: `python -m klaint.broker --data-dir <path>`.

Receives the 256-bit hex `broker_issuance_secret` exclusively via `stdin` line 1 (never CLI args or env vars).
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import sys
from typing import Any

_HEX_256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_FORBIDDEN_ENV_KEYS = ("BROKER_ISSUANCE_SECRET", "KLAINT_BROKER_SECRET", "ISSUANCE_SECRET")


def _check_no_secret_leak_surfaces(argv: list[str]) -> None:
    for arg in argv:
        lower = arg.lower()
        if "secret" in lower or "issuance" in lower:
            sys.stderr.write("SECURITY_ERROR: broker_issuance_secret must never be passed via CLI arguments\n")
            sys.stderr.flush()
            os._exit(2)
    for env_key in os.environ:
        upper = env_key.upper()
        if upper in _FORBIDDEN_ENV_KEYS or "BROKER_ISSUANCE_SECRET" in upper:
            sys.stderr.write("SECURITY_ERROR: broker_issuance_secret must never be passed via environment variables\n")
            sys.stderr.flush()
            os._exit(2)


def _read_bootstrap_secret() -> tuple[bytes, dict[str, str] | None]:
    first_line = sys.stdin.readline()
    if not first_line:
        raise SystemExit("SECURITY_ERROR: missing stdin bootstrap frame for broker_issuance_secret")
    raw = first_line.strip()
    connector_secrets: dict[str, str] | None = None
    if raw.startswith("{"):
        parsed = json.loads(raw)
        secret_hex = str(parsed.get("broker_issuance_secret", ""))
        if isinstance(parsed.get("connector_secrets"), dict):
            connector_secrets = {str(k): str(v) for k, v in parsed["connector_secrets"].items()}
    else:
        secret_hex = raw

    if not _HEX_256_RE.fullmatch(secret_hex):
        raise SystemExit("SECURITY_ERROR: broker_issuance_secret must be a 256-bit (64-char) hex string")
    return bytes.fromhex(secret_hex), connector_secrets


def _verify_rpc_hmac(secret: bytes, req_id: str, method: str, params: dict[str, Any], mac_hex: str) -> bool:
    # Note: params may deliberately contain floats in negative tests (C5), so serialize raw JSON canonically with json.dumps
    body = json.dumps(
        {"id": req_id, "method": method, "params": params},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, mac_hex)


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    _check_no_secret_leak_surfaces(args_list)

    from klaint.broker.engine import BrokerRuntime
    from klaint.core.errors import KlaintError
    from klaint.core.jcs import jcs_dumps
    from klaint.core.models import AuthenticatedSession, CapabilityToken, PolicyVerdict

    parser = argparse.ArgumentParser(prog="python -m klaint.broker")
    parser.add_argument("--data-dir", required=True, help="Root data directory for per-tenant SQLite WAL DBs")
    ns = parser.parse_args(args_list)

    issuance_secret, connector_secrets = _read_bootstrap_secret()
    runtime = BrokerRuntime(ns.data_dir, connector_secrets=connector_secrets)

    ready_frame = {"status": "ready", **runtime.info()}
    sys.stdout.write(json.dumps(ready_frame, separators=(",", ":")) + "\n")
    sys.stdout.flush()

    try:
        for raw_line in sys.stdin:
            line = raw_line.strip()
            if not line:
                continue
            try:
                frame = json.loads(line)
                req_id = str(frame.get("id", "0"))
                method = str(frame.get("method", ""))
                params = frame.get("params") or {}
                mac_hex = str(frame.get("auth_mac", ""))

                if not _verify_rpc_hmac(issuance_secret, req_id, method, params, mac_hex):
                    resp = {
                        "id": req_id,
                        "ok": False,
                        "error_type": "AuthorityViolationError",
                        "error": "Broker RPC HMAC authentication failed",
                    }
                    sys.stdout.write(json.dumps(resp, separators=(",", ":")) + "\n")
                    sys.stdout.flush()
                    continue

                if method == "info":
                    result = runtime.info()
                elif method == "shutdown":
                    runtime.close()
                    resp = {"id": req_id, "ok": True, "result": {"shutdown": True}}
                    sys.stdout.write(json.dumps(resp, separators=(",", ":")) + "\n")
                    sys.stdout.flush()
                    return 0
                elif method == "issue_capability":
                    session = AuthenticatedSession.model_validate(params["session"])
                    verdict = PolicyVerdict.model_validate(params["verdict"])
                    token = runtime.issue_capability(
                        session=session,
                        tool=str(params["tool"]),
                        tool_args=params["tool_args"],
                        verdict=verdict,
                        ttl_seconds=int(params.get("ttl_seconds", 30)),
                        issued_at_override=params.get("issued_at_override"),
                    )
                    result = json.loads(jcs_dumps(token.model_dump(mode="json")).decode("utf-8"))
                elif method == "verify_capability":
                    session = AuthenticatedSession.model_validate(params["session"])
                    cap = CapabilityToken.model_validate(params["capability"])
                    digest = runtime.verify_capability(
                        capability=cap,
                        session=session,
                        tool=str(params["tool"]),
                        tool_args=params["tool_args"],
                    )
                    result = {"valid": True, "args_digest": digest}
                elif method == "execute_capability":
                    session = AuthenticatedSession.model_validate(params["session"])
                    cap = CapabilityToken.model_validate(params["capability"])
                    exec_res = runtime.execute_capability(
                        capability=cap,
                        session=session,
                        tool=str(params["tool"]),
                        tool_args=params["tool_args"],
                        idempotency_key=params.get("idempotency_key"),
                        verdict_id=params.get("verdict_id"),
                        policy_version=params.get("policy_version"),
                        now_override=params.get("now_override"),
                        operator_confirmed=bool(params.get("operator_confirmed", False)),
                    )
                    result = exec_res.to_dict()
                else:
                    raise KlaintError(f"Unknown broker RPC method {method!r}")

                resp = {"id": req_id, "ok": True, "result": result}
            except Exception as exc:
                resp = {
                    "id": req_id if "req_id" in locals() else "0",
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }

            sys.stdout.write(json.dumps(resp, separators=(",", ":"), ensure_ascii=False) + "\n")
            sys.stdout.flush()
    finally:
        runtime.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
