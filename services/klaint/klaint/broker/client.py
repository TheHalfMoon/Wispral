# SPDX-License-Identifier: Apache-2.0
"""Host-side client spawning and communicating with `python -m klaint.broker` over stdio."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

from klaint.broker.engine import BrokerExecutionResult
from klaint.core.errors import (
    AuthorityViolationError,
    CanonicalSerializationError,
    CapabilityError,
    ConnectorTimeoutError,
    ExpiredCapabilityError,
    ForgedIdentityError,
    IntentTransitionError,
    KlaintError,
    ReplayNonceError,
    StaleEpochError,
    TenantIsolationError,
)
from klaint.core.models import (
    AuthenticatedSession,
    CapabilityToken,
    EffectIntentRecord,
    PolicyVerdict,
    new_id,
)

_ERROR_REGISTRY: dict[str, type[Exception]] = {
    "AuthorityViolationError": AuthorityViolationError,
    "CanonicalSerializationError": CanonicalSerializationError,
    "CapabilityError": CapabilityError,
    "ConnectorTimeoutError": ConnectorTimeoutError,
    "ExpiredCapabilityError": ExpiredCapabilityError,
    "ForgedIdentityError": ForgedIdentityError,
    "IntentTransitionError": IntentTransitionError,
    "KlaintError": KlaintError,
    "ReplayNonceError": ReplayNonceError,
    "StaleEpochError": StaleEpochError,
    "TenantIsolationError": TenantIsolationError,
    "ValidationError": CapabilityError,
}

_PACKAGE_ROOT = Path(__file__).resolve().parents[2]


class BrokerClient:
    """Thread-safe IPC client to the isolated `python -m klaint.broker` subprocess."""

    def __init__(
        self,
        data_dir: Path | str,
        *,
        issuance_secret_hex: str | None = None,
        connector_secrets: dict[str, str] | None = None,
    ) -> None:
        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._secret_hex = issuance_secret_hex or secrets.token_hex(32)
        if len(self._secret_hex) != 64:
            raise ValueError("broker_issuance_secret must be a 64-character (256-bit) hex string")
        self._secret_bytes = bytes.fromhex(self._secret_hex)
        self._lock = threading.RLock()
        self._closed = False

        # Sanitize child environment: pass OS/Python runtime vars (Windows + POSIX) only, NEVER any secret!
        clean_env: dict[str, str] = {}
        for key in (
            "SYSTEMROOT",
            "WINDIR",
            "COMSPEC",
            "PATH",
            "PATHEXT",
            "TEMP",
            "TMP",
            "TMPDIR",
            "USERPROFILE",
            "HOMEDRIVE",
            "HOMEPATH",
            "HOME",
            "LANG",
            "LC_ALL",
            "LC_CTYPE",
            "LD_LIBRARY_PATH",
            "DYLD_LIBRARY_PATH",
            "PYTHONPATH",
            "XDG_CACHE_HOME",
        ):
            val = os.environ.get(key)
            if val is not None:
                clean_env[key] = val
        clean_env["PYTHONDONTWRITEBYTECODE"] = "1"
        clean_env["PYTHONUTF8"] = "1"

        self._proc = subprocess.Popen(
            [sys.executable, "-B", "-m", "klaint.broker", "--data-dir", str(self.data_dir)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(_PACKAGE_ROOT),
            env=clean_env,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        if self._proc.stdin is None or self._proc.stdout is None:
            raise KlaintError("Failed to open stdio pipes to klaint.broker subprocess")

        if connector_secrets:
            bootstrap = json.dumps(
                {"broker_issuance_secret": self._secret_hex, "connector_secrets": connector_secrets},
                separators=(",", ":"),
            )
        else:
            bootstrap = self._secret_hex
        self._proc.stdin.write(bootstrap + "\n")
        self._proc.stdin.flush()

        ready_line = self._proc.stdout.readline().strip()
        if not ready_line:
            stderr_out = self._proc.stderr.read() if self._proc.stderr else ""
            raise KlaintError(f"klaint.broker subprocess failed to start: {stderr_out}")
        ready = json.loads(ready_line)
        if ready.get("status") != "ready":
            raise KlaintError(f"Unexpected broker handshake frame: {ready!r}")
        self.broker_pid: int = int(ready["pid"])
        self.key_id: str = str(ready["key_id"])
        self.public_key_b64: str = str(ready["public_key_b64"])

    def _rpc(self, method: str, params: dict[str, Any]) -> Any:
        with self._lock:
            if self._closed or self._proc.poll() is not None:
                raise KlaintError("Broker subprocess is not running")
            req_id = new_id("rpc", 6)
            body = json.dumps(
                {"id": req_id, "method": method, "params": params},
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
            mac_hex = hmac.new(self._secret_bytes, body, hashlib.sha256).hexdigest()
            wire = json.dumps(
                {"id": req_id, "method": method, "params": params, "auth_mac": mac_hex},
                separators=(",", ":"),
                ensure_ascii=False,
            )
            if self._proc.stdin is None or self._proc.stdout is None:
                raise KlaintError("Failed to open stdio pipes to klaint.broker subprocess")
            self._proc.stdin.write(wire + "\n")
            self._proc.stdin.flush()

            resp_line = self._proc.stdout.readline().strip()
            if not resp_line:
                stderr_out = self._proc.stderr.read() if self._proc.stderr else ""
                raise KlaintError(f"Broker subprocess closed pipe unexpectedly: {stderr_out}")
            resp = json.loads(resp_line)
            if not resp.get("ok"):
                err_type = str(resp.get("error_type", "KlaintError"))
                err_msg = str(resp.get("error", "Unknown broker error"))
                exc_cls = _ERROR_REGISTRY.get(err_type, KlaintError)
                raise exc_cls(err_msg)
            return resp["result"]

    def info(self) -> dict[str, Any]:
        return dict(self._rpc("info", {}))

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
        res = self._rpc(
            "issue_capability",
            {
                "session": session.model_dump(mode="json"),
                "tool": tool,
                "tool_args": tool_args,
                "verdict": verdict.model_dump(mode="json", exclude_none=True),
                "ttl_seconds": ttl_seconds,
                "issued_at_override": issued_at_override,
            },
        )
        return CapabilityToken.model_validate(res)

    def verify_capability(
        self,
        *,
        capability: CapabilityToken,
        session: AuthenticatedSession,
        tool: str,
        tool_args: dict[str, Any],
    ) -> dict[str, Any]:
        return dict(
            self._rpc(
                "verify_capability",
                {
                    "capability": capability.model_dump(mode="json"),
                    "session": session.model_dump(mode="json"),
                    "tool": tool,
                    "tool_args": tool_args,
                },
            )
        )

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
        res = self._rpc(
            "execute_capability",
            {
                "capability": capability.model_dump(mode="json"),
                "session": session.model_dump(mode="json"),
                "tool": tool,
                "tool_args": tool_args,
                "idempotency_key": idempotency_key,
                "verdict_id": verdict_id,
                "policy_version": policy_version,
                "now_override": now_override,
                "operator_confirmed": operator_confirmed,
            },
        )
        return BrokerExecutionResult(
            intent=EffectIntentRecord.model_validate(res["intent"]),
            receipt_id=res.get("receipt_id"),
            state_history=list(res.get("state_history", [])),
            connector_output=res.get("connector_output"),
            reconciled_from_unknown=bool(res.get("reconciled_from_unknown", False)),
        )

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            try:
                if self._proc.poll() is None:
                    self._rpc("shutdown", {})
                    self._proc.wait(timeout=5)
            except Exception:
                if self._proc.poll() is None:
                    self._proc.kill()
                    self._proc.wait(timeout=2)
            finally:
                self._closed = True
                for stream in (self._proc.stdin, self._proc.stdout, self._proc.stderr):
                    if stream is not None:
                        try:
                            stream.close()
                        except Exception:
                            pass

    def __enter__(self) -> BrokerClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
