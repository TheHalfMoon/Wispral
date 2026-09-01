#!/usr/bin/env python3
"""Minimal unauthenticated ACP v1 research probe for Specification 000A.

This is research instrumentation, not Wispral product code. It intentionally uses
only the Python standard library and exercises only non-destructive protocol
surfaces that can be observed without provider credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import selectors
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = 1
SENSITIVE_ENV_NAMES = {
    "ANTHROPIC_API_KEY",
    "CODEX_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "OPENAI_API_KEY",
}


def compact(value: str, limit: int = 1200) -> str:
    normalized = " ".join(value.split())
    return normalized if len(normalized) <= limit else normalized[: limit - 3] + "..."


def sanitized_env() -> dict[str, str]:
    env = dict(os.environ)
    for name in list(env):
        upper = name.upper()
        if name in SENSITIVE_ENV_NAMES or upper.endswith("_API_KEY") or upper.endswith("_TOKEN"):
            env.pop(name, None)
    env["NO_BROWSER"] = "1"
    return env


def sanitize(value: Any, fixture: Path) -> Any:
    home = str(Path.home())
    fixture_text = str(fixture.resolve())
    if isinstance(value, str):
        return value.replace(fixture_text, "<FIXTURE_CWD>").replace(home, "<HOME>")
    if isinstance(value, list):
        return [sanitize(item, fixture) for item in value]
    if isinstance(value, dict):
        return {key: sanitize(item, fixture) for key, item in value.items()}
    return value


def fixture_digest(root: Path) -> tuple[str, list[dict[str, str]]]:
    records: list[dict[str, str]] = []
    aggregate = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        records.append({"path": relative, "sha256": digest})
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(digest.encode("ascii"))
        aggregate.update(b"\n")
    return aggregate.hexdigest(), records


class Probe:
    def __init__(self, command: list[str], fixture: Path, timeout: float) -> None:
        self.command = command
        self.fixture = fixture.resolve()
        self.timeout = timeout
        self.messages: list[dict[str, Any]] = []
        self.next_id = 1
        self.proc: subprocess.Popen[str] | None = None

    def record(self, direction: str, message: Any) -> None:
        self.messages.append(
            {
                "sequence": len(self.messages) + 1,
                "direction": direction,
                "message": sanitize(message, self.fixture),
            }
        )

    def start(self) -> None:
        kwargs: dict[str, Any] = {}
        if os.name != "nt":
            kwargs["start_new_session"] = True
        self.proc = subprocess.Popen(
            self.command,
            cwd=self.fixture,
            env=sanitized_env(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            **kwargs,
        )

    def send_request(self, method: str, params: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
        assert self.proc is not None and self.proc.stdin is not None
        request_id = self.next_id
        self.next_id += 1
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        self.record("client_to_agent", payload)
        self.proc.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
        self.proc.stdin.flush()
        return self.wait_for_response(request_id)

    def wait_for_response(self, request_id: int) -> tuple[str, dict[str, Any] | None]:
        assert self.proc is not None and self.proc.stdout is not None
        selector = selectors.DefaultSelector()
        selector.register(self.proc.stdout, selectors.EVENT_READ)
        deadline = time.monotonic() + self.timeout
        try:
            while time.monotonic() < deadline:
                if self.proc.poll() is not None:
                    return "PROCESS_EXITED", None
                remaining = max(0.0, deadline - time.monotonic())
                events = selector.select(timeout=min(0.25, remaining))
                if not events:
                    continue
                line = self.proc.stdout.readline()
                if not line:
                    continue
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    self.record("agent_to_client_decode_error", compact(line))
                    return "DECODE_ERROR", None
                self.record("agent_to_client", message)
                if isinstance(message, dict) and message.get("id") == request_id:
                    if "result" in message:
                        return "SUCCESS", message
                    error = message.get("error")
                    if isinstance(error, dict):
                        code = error.get("code")
                        text = str(error.get("message", "")).lower()
                        if code == -32601:
                            return "METHOD_NOT_FOUND", message
                        if code == -32602:
                            return "INVALID_PARAMS", message
                        if code == -32002:
                            return "RESOURCE_NOT_FOUND", message
                        if code == -32800:
                            return "CANCELLED", message
                        if code == -32000 or "auth_required" in text or "authentication" in text:
                            return "AUTH_REQUIRED", message
                    return "ERROR", message
            return "NO_RESPONSE", None
        finally:
            selector.close()

    def send_notification(self, method: str, params: dict[str, Any]) -> str:
        assert self.proc is not None and self.proc.stdin is not None
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        self.record("client_to_agent", payload)
        self.proc.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
        self.proc.stdin.flush()
        return "SENT"

    def stderr_tail(self) -> str | None:
        if self.proc is None or self.proc.stderr is None or self.proc.poll() is None:
            return None
        data = self.proc.stderr.read()
        return compact(sanitize(data, self.fixture)) if data else None

    def stop(self) -> int | None:
        if self.proc is None:
            return None
        if self.proc.poll() is None:
            try:
                if os.name != "nt":
                    os.killpg(self.proc.pid, signal.SIGTERM)
                else:
                    self.proc.terminate()
                self.proc.wait(timeout=2)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                if self.proc.poll() is None:
                    self.proc.kill()
                    self.proc.wait(timeout=2)
        return self.proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("agent command required after --")
    if not args.fixture.is_dir():
        parser.error("fixture must be an existing directory")

    tree_digest, files = fixture_digest(args.fixture)
    probe = Probe(command, args.fixture, args.timeout)
    outcomes: dict[str, Any] = {}
    init_response: dict[str, Any] | None = None
    session_id: str | None = None
    process_error: str | None = None

    started = time.time()
    try:
        probe.start()
        init_status, init_response = probe.send_request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "clientInfo": {"name": "Wispral 000A Research Probe", "version": "0.1.0"},
                "clientCapabilities": {
                    "terminal": False,
                    "fs": {"readTextFile": False, "writeTextFile": False},
                },
            },
        )
        outcomes["initialize"] = init_status

        if init_status == "SUCCESS":
            session_status, session_response = probe.send_request(
                "session/new",
                {"cwd": str(args.fixture.resolve()), "mcpServers": []},
            )
            outcomes["session_new"] = session_status
            if session_status == "SUCCESS" and session_response:
                result = session_response.get("result")
                if isinstance(result, dict) and isinstance(result.get("sessionId"), str):
                    session_id = result["sessionId"]
            list_status, _ = probe.send_request("session/list", {})
            outcomes["session_list"] = list_status
        else:
            outcomes["session_new"] = "NOT_TESTED"
            outcomes["session_list"] = "NOT_TESTED"

        if session_id:
            outcomes["cancel_notification"] = probe.send_notification(
                "session/cancel", {"sessionId": session_id}
            )
            outcomes["cancel_semantics"] = "NOT_TESTED_NO_ACTIVE_PROMPT"
        else:
            outcomes["cancel_notification"] = "NOT_TESTED"
            outcomes["cancel_semantics"] = "NOT_TESTED"
        outcomes["permission_semantics"] = "NOT_TESTED_NO_AUTHENTICATED_SAFE_ACTION"
    except Exception as exc:  # research evidence must preserve unexpected failures
        process_error = f"{type(exc).__name__}: {exc}"
        outcomes.setdefault("initialize", "PROBE_ERROR")
    finally:
        exit_code = probe.stop()

    init_result = init_response.get("result") if isinstance(init_response, dict) else None
    record = {
        "schema_version": 1,
        "attempt_kind": "unauthenticated-acp-v1",
        "agent_id": args.agent_id,
        "protocol_version_requested": PROTOCOL_VERSION,
        "command": command,
        "started_unix": started,
        "duration_seconds": round(time.time() - started, 3),
        "fixture": {"tree_sha256": tree_digest, "files": files},
        "initialize_result": sanitize(init_result, args.fixture),
        "outcomes": outcomes,
        "process": {
            "exit_code": exit_code,
            "probe_error": process_error,
            "stderr_tail": probe.stderr_tail(),
        },
        "trace": probe.messages,
        "credential_policy": "known API-key/token environment variables removed; NO_BROWSER=1",
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"agent_id": args.agent_id, "outcomes": outcomes, "output": str(args.output)}))
    return 0 if outcomes.get("initialize") == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
