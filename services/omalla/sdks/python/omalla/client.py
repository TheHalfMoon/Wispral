"""Typed, dependency-free client for the Omalla HTTP API.

Only the Python standard library is used, so the SDK runs anywhere Python 3.9+
runs. Supports RFC 8785 JCS canonicalization (rejecting floats), durable
Idempotency-Key headers, raw-byte Standard Webhooks & Omalla HMAC verification,
streaming event parsing, and agent/workflow version rollback.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterable, Iterator, Mapping, Optional, Sequence, Union

__all__ = [
    "OmallaClient",
    "OmallaApiError",
    "__version__",
    "jcs_canonicalize",
    "jcs_sha256",
    "parse_stream_events",
    "verify_webhook_signature",
]

__version__ = "0.1.0"

JsonValue = Any


class OmallaApiError(Exception):
    """An error returned by the Omalla API (or a transport failure)."""

    def __init__(
        self,
        message: str,
        status: int = 0,
        code: str = "transport_error",
        body: JsonValue = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.body = body

    def __str__(self) -> str:
        prefix = f"{self.status} {self.code}" if self.status else self.code
        return f"{prefix}: {super().__str__()}"


def _utf16_units(text: str) -> list[int]:
    raw = text.encode("utf-16-le")
    return [int.from_bytes(raw[i : i + 2], "little") for i in range(0, len(raw), 2)]


def _jcs_escape_string(value: str) -> str:
    out = ['"']
    for ch in value:
        code = ord(ch)
        if 0xD800 <= code <= 0xDFFF:
            raise ValueError("lone UTF-16 surrogate rejected in JCS string")
        if code == 0x08:
            out.append("\\b")
        elif code == 0x09:
            out.append("\\t")
        elif code == 0x0A:
            out.append("\\n")
        elif code == 0x0C:
            out.append("\\f")
        elif code == 0x0D:
            out.append("\\r")
        elif code == 0x22:
            out.append('\\"')
        elif code == 0x5C:
            out.append("\\\\")
        elif code < 0x20:
            out.append(f"\\u{code:04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def jcs_canonicalize(value: Any) -> str:
    """Serialize a JSON-compatible Python value under RFC 8785 JCS, rejecting floats."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError("non-finite float rejected in JCS payload")
        raise ValueError("floating-point numbers are rejected in JCS idempotency payloads")
    if isinstance(value, int):
        if abs(value) > 9007199254740991:
            raise ValueError("integer exceeds IEEE-754 safe integer range in JCS payload")
        return str(value)
    if isinstance(value, str):
        return _jcs_escape_string(value)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(jcs_canonicalize(item) for item in value) + "]"
    if isinstance(value, Mapping):
        keys = sorted((str(k) for k in value.keys()), key=_utf16_units)
        pairs = [f"{_jcs_escape_string(k)}:{jcs_canonicalize(value[k])}" for k in keys]
        return "{" + ",".join(pairs) + "}"
    raise ValueError(f"unsupported JCS value type: {type(value).__name__}")


def jcs_sha256(value: Any) -> str:
    """Compute the hex SHA-256 digest of a JCS-canonicalized value."""
    canonical = jcs_canonicalize(value)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_webhook_signature(
    raw_body: Union[bytes, str],
    headers: Mapping[str, str],
    secret: str,
    now_sec: Optional[int] = None,
    max_skew_sec: int = 300,
) -> dict[str, Any]:
    """Constant-time raw-byte HMAC verifier for Standard Webhooks and Omalla signatures."""
    body_bytes = raw_body.encode("utf-8") if isinstance(raw_body, str) else bytes(raw_body)
    lower = {k.lower(): v for k, v in headers.items() if v is not None}
    current_sec = int(time.time()) if now_sec is None else int(now_sec)

    std_id = lower.get("webhook-id") or lower.get("svix-id")
    std_ts = lower.get("webhook-timestamp") or lower.get("svix-timestamp")
    std_sig = lower.get("webhook-signature") or lower.get("svix-signature")

    if std_id or std_ts or std_sig:
        if not (std_id and std_ts and std_sig):
            return {"valid": False, "reason": "incomplete Standard Webhooks headers"}
        try:
            ts_int = int(std_ts)
        except ValueError:
            return {"valid": False, "reason": "invalid webhook-timestamp"}
        if abs(current_sec - ts_int) > max_skew_sec:
            return {"valid": False, "reason": "webhook timestamp outside ±300s window"}
        key_bytes = base64.b64decode(secret[6:]) if secret.startswith("whsec_") else secret.encode("utf-8")
        signed = f"{std_id}.{std_ts}.".encode("utf-8") + body_bytes
        expected = hmac.new(key_bytes, signed, hashlib.sha256).digest()
        for part in std_sig.split():
            if "," not in part:
                continue
            ver, b64 = part.split(",", 1)
            if ver != "v1" or not b64:
                continue
            try:
                provided = base64.b64decode(b64)
            except Exception:
                continue
            if len(provided) == len(expected) and hmac.compare_digest(provided, expected):
                return {"valid": True, "event_key": std_id, "scheme": "standard-webhooks"}
        return {"valid": False, "reason": "Standard Webhooks v1 signature mismatch"}

    omalla_sig = lower.get("x-omalla-signature")
    if not omalla_sig:
        return {"valid": False, "reason": "missing webhook signature header"}
    omalla_ts = lower.get("x-omalla-timestamp")
    if omalla_ts is None:
        return {"valid": False, "reason": "missing or invalid x-omalla-timestamp header"}
    ts_clean = omalla_ts.strip()
    if not ts_clean or not (ts_clean.isdigit() or (ts_clean.startswith("-") and ts_clean[1:].isdigit())):
        return {"valid": False, "reason": "invalid x-omalla-timestamp"}
    ts_int = int(ts_clean)
    if abs(current_sec - ts_int) > max_skew_sec:
        return {"valid": False, "reason": "x-omalla-timestamp outside ±300s window"}
    signed_payload = f"{ts_clean}.".encode("utf-8") + body_bytes

    hex_part = omalla_sig[7:] if omalla_sig.startswith("sha256=") else omalla_sig
    if len(hex_part) != 64:
        return {"valid": False, "reason": "malformed sha256 signature"}
    try:
        provided_digest = bytes.fromhex(hex_part)
    except ValueError:
        return {"valid": False, "reason": "malformed sha256 signature"}
    expected_digest = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).digest()
    if len(provided_digest) != len(expected_digest) or not hmac.compare_digest(provided_digest, expected_digest):
        return {"valid": False, "reason": "signature mismatch"}
    body_sha = hashlib.sha256(body_bytes).hexdigest()
    event_key = f"omalla:{ts_clean}:{body_sha}"
    return {"valid": True, "event_key": event_key, "scheme": "omalla-hmac"}


def parse_stream_events(frames: Iterable[Union[str, bytes]]) -> Iterator[dict[str, Any]]:
    """Yield decoded call/realtime stream events from JSON lines, SSE data lines, or WS frames."""
    for raw in frames:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        for line in text.splitlines():
            cleaned = line.strip()
            if not cleaned or cleaned.startswith(":"):
                continue
            if cleaned.startswith("data:"):
                cleaned = cleaned[5:].strip()
            if not cleaned:
                continue
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                yield parsed


class _Namespace:
    def __init__(self, client: "OmallaClient") -> None:
        self._client = client


class Agents(_Namespace):
    def list(self) -> list[dict]:
        return self._client.get("/v1/agents")

    def get(self, agent_id: str) -> dict:
        return self._client.get(f"/v1/agents/{_seg(agent_id)}")

    def create(self, name: str, description: str = "", config: Optional[Mapping[str, Any]] = None) -> dict:
        return self._client.post(
            "/v1/agents",
            {"name": name, "description": description, "config": dict(config or {})},
        )

    def update(self, agent_id: str, **fields: Any) -> dict:
        return self._client.patch(f"/v1/agents/{_seg(agent_id)}", fields)

    def publish(self, agent_id: str) -> dict:
        return self._client.post(f"/v1/agents/{_seg(agent_id)}/publish", {})

    def versions(self, agent_id: str) -> list[dict]:
        return self._client.get(f"/v1/agents/{_seg(agent_id)}/versions")

    def test(
        self,
        agent_id: str,
        caller_turns: Optional[Sequence[str]] = None,
        variables: Optional[Mapping[str, Any]] = None,
        version: Optional[int] = None,
        compare_version: Optional[int] = None,
        expectations: Optional[Mapping[str, Any]] = None,
    ) -> dict:
        body: dict[str, Any] = {
            "callerTurns": list(caller_turns or []),
            "variables": dict(variables or {}),
        }
        if version is not None:
            body["version"] = version
        if compare_version is not None:
            body["compareVersion"] = compare_version
        if expectations is not None:
            body["expectations"] = dict(expectations)
        return self._client.post(f"/v1/agents/{_seg(agent_id)}/test", body)

    def rollback(self, agent_id: str, version: int, note: Optional[str] = None) -> dict:
        body: dict[str, Any] = {"version": version}
        if note is not None:
            body["note"] = note
        return self._client.post(f"/v1/agents/{_seg(agent_id)}/rollback", body)

    def delete(self, agent_id: str) -> None:
        self._client.delete(f"/v1/agents/{_seg(agent_id)}")


class Tools(_Namespace):
    def list(self) -> list[dict]:
        return self._client.get("/v1/tools")

    def create(self, **definition: Any) -> dict:
        return self._client.post("/v1/tools", definition)

    def update(self, tool_id: str, **fields: Any) -> dict:
        return self._client.patch(f"/v1/tools/{_seg(tool_id)}", fields)

    def delete(self, tool_id: str) -> None:
        self._client.delete(f"/v1/tools/{_seg(tool_id)}")

    def test(self, tool_id: str, args: Optional[Mapping[str, Any]] = None, dry_run: bool = True) -> dict:
        return self._client.post(
            f"/v1/tools/{_seg(tool_id)}/test",
            {"args": dict(args or {}), "dryRun": dry_run},
        )


class Calls(_Namespace):
    def list(self, status: Optional[str] = None, limit: Optional[int] = None) -> list[dict]:
        return self._client.get("/v1/calls", {"status": status, "limit": limit})

    def get(self, call_id: str) -> dict:
        return self._client.get(f"/v1/calls/{_seg(call_id)}")

    def simulate(
        self,
        to: str = "+15550001234",
        from_: str = "+15550009999",
        say: Optional[Sequence[str]] = None,
        press: Optional[Sequence[str]] = None,
        variables: Optional[Mapping[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> dict:
        """Place a free in-process call. No carrier, no PSTN, no charge."""
        return self._client.post(
            "/v1/calls",
            {
                "to": to,
                "from": from_,
                "say": list(say or []),
                "press": list(press or []),
                "variables": dict(variables or {}),
            },
            idempotency_key=idempotency_key,
        )

    def outbound(
        self,
        to: str,
        agent_id: str,
        consent: bool,
        variables: Optional[Mapping[str, Any]] = None,
        provider: Optional[str] = None,
        from_: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> dict:
        """Start a carrier or simulated outbound call. Consent is mandatory."""
        body: dict[str, Any] = {
            "to": to,
            "agentId": agent_id,
            "consent": consent,
            "variables": dict(variables or {}),
            "mode": "carrier" if provider else "simulated",
        }
        if provider:
            body["provider"] = provider
        if from_:
            body["from"] = from_
        return self._client.post("/v1/calls/outbound", body, idempotency_key=idempotency_key)

    def say(self, call_id: str, text: str) -> dict:
        return self._client.post(f"/v1/calls/{_seg(call_id)}/say", {"text": text})

    def dtmf(self, call_id: str, digits: str) -> dict:
        return self._client.post(f"/v1/calls/{_seg(call_id)}/dtmf", {"digits": digits})

    def hangup(self, call_id: str) -> dict:
        return self._client.post(f"/v1/calls/{_seg(call_id)}/hangup", {})

    def stream_url(self, call_id: str) -> str:
        ws_base = "ws" + self._client.base_url[4:] if self._client.base_url.startswith("http") else self._client.base_url
        token = urllib.parse.quote(self._client.api_key, safe="")
        return f"{ws_base}/v1/calls/{_seg(call_id)}/stream?token={token}"


class Workflows(_Namespace):
    def list(self) -> list[dict]:
        return self._client.get("/v1/workflows")

    def get(self, workflow_id: str) -> dict:
        return self._client.get(f"/v1/workflows/{_seg(workflow_id)}")

    def create(self, **definition: Any) -> dict:
        return self._client.post("/v1/workflows", definition)

    def update(self, workflow_id: str, **fields: Any) -> dict:
        return self._client.patch(f"/v1/workflows/{_seg(workflow_id)}", fields)

    def versions(self, workflow_id: str) -> list[dict]:
        return self._client.get(f"/v1/workflows/{_seg(workflow_id)}/versions")

    def test(
        self,
        workflow_id: str,
        payload: Optional[Mapping[str, Any]] = None,
        version: Optional[int] = None,
        compare_version: Optional[int] = None,
    ) -> dict:
        body: dict[str, Any] = {"payload": dict(payload or {})}
        if version is not None:
            body["version"] = version
        if compare_version is not None:
            body["compareVersion"] = compare_version
        return self._client.post(f"/v1/workflows/{_seg(workflow_id)}/test", body)

    def rollback(self, workflow_id: str, version: int, note: Optional[str] = None) -> dict:
        body: dict[str, Any] = {"version": version}
        if note is not None:
            body["note"] = note
        return self._client.post(f"/v1/workflows/{_seg(workflow_id)}/rollback", body)

    def delete(self, workflow_id: str) -> None:
        self._client.delete(f"/v1/workflows/{_seg(workflow_id)}")

    def run(
        self,
        workflow_id: str,
        payload: Optional[Mapping[str, Any]] = None,
        dry_run: bool = False,
        idempotency_key: Optional[str] = None,
    ) -> dict:
        body: dict[str, Any] = {"payload": dict(payload or {}), "dryRun": dry_run}
        if idempotency_key:
            body["idempotencyKey"] = idempotency_key
        return self._client.post(
            f"/v1/workflows/{_seg(workflow_id)}/run",
            body,
            idempotency_key=idempotency_key,
        )

    def runs(self, workflow_id: str) -> list[dict]:
        return self._client.get(f"/v1/workflows/{_seg(workflow_id)}/runs")


class Runs(_Namespace):
    def list(self) -> list[dict]:
        return self._client.get("/v1/runs")


class Templates(_Namespace):
    def list(self) -> list[dict]:
        return self._client.get("/v1/templates")

    def install(self, template_id: str, activate: bool = False) -> dict:
        return self._client.post(
            f"/v1/templates/{_seg(template_id)}/install",
            {"activate": activate},
        )


class Tasks(_Namespace):
    def list(self) -> list[dict]:
        return self._client.get("/v1/tasks")

    def create(self, title: str, **fields: Any) -> dict:
        return self._client.post("/v1/tasks", {"title": title, **fields})

    def update(self, task_id: str, **fields: Any) -> dict:
        return self._client.patch(f"/v1/tasks/{_seg(task_id)}", fields)


class Bookings(_Namespace):
    def list(self) -> list[dict]:
        return self._client.get("/v1/bookings")

    def create(self, **fields: Any) -> dict:
        return self._client.post("/v1/bookings", fields)

    def update(self, booking_id: str, **fields: Any) -> dict:
        return self._client.patch(f"/v1/bookings/{_seg(booking_id)}", fields)


class Contacts(_Namespace):
    def list(self) -> list[dict]:
        return self._client.get("/v1/contacts")


class Escalations(_Namespace):
    def list(self) -> list[dict]:
        return self._client.get("/v1/escalations")

    def update(self, escalation_id: str, **fields: Any) -> dict:
        return self._client.patch(f"/v1/escalations/{_seg(escalation_id)}", fields)


class Knowledge(_Namespace):
    def list(self) -> list[dict]:
        return self._client.get("/v1/knowledge-bases")

    def create(self, name: str, **fields: Any) -> dict:
        return self._client.post("/v1/knowledge-bases", {"name": name, **fields})

    def add_document(self, knowledge_id: str, title: str, text: str) -> dict:
        return self._client.post(
            f"/v1/knowledge-bases/{_seg(knowledge_id)}/documents",
            {"title": title, "text": text},
        )

    def search(self, knowledge_id: str, query: str, limit: int = 5) -> dict:
        return self._client.post(
            f"/v1/knowledge-bases/{_seg(knowledge_id)}/search",
            {"query": query, "limit": limit},
        )


class Keys(_Namespace):
    def list(self) -> list[dict]:
        return self._client.get("/v1/keys")

    def create(self, name: str, role: str = "operator") -> dict:
        return self._client.post("/v1/keys", {"name": name, "role": role})

    def revoke(self, key_id: str) -> None:
        self._client.delete(f"/v1/keys/{_seg(key_id)}")


class Credentials(_Namespace):
    def list(self) -> list[dict]:
        return self._client.get("/v1/credentials")

    def put(self, name: str, value: str, provider: str = "custom") -> dict:
        return self._client.put(
            f"/v1/credentials/{_seg(name)}",
            {"value": value, "provider": provider},
        )

    def delete(self, name: str) -> None:
        self._client.delete(f"/v1/credentials/{_seg(name)}")


class Numbers(_Namespace):
    def list(self) -> list[dict]:
        return self._client.get("/v1/numbers")

    def search(
        self,
        provider: str = "simulated",
        country_code: str = "US",
        area_code: Optional[str] = None,
        contains: Optional[str] = None,
        limit: int = 8,
    ) -> dict:
        body: dict[str, Any] = {
            "provider": provider,
            "countryCode": country_code,
            "limit": limit,
        }
        if area_code:
            body["areaCode"] = area_code
        if contains:
            body["contains"] = contains
        return self._client.post("/v1/numbers/search", body)

    def provision(
        self,
        e164: str,
        provider: Optional[str] = None,
        label: Optional[str] = None,
        agent_id: Optional[str] = None,
        ivr_menu_id: Optional[str] = None,
    ) -> dict:
        body: dict[str, Any] = {"e164": e164, "confirm": True}
        if provider:
            body["provider"] = provider
        if label:
            body["label"] = label
        if agent_id:
            body["agentId"] = agent_id
        if ivr_menu_id:
            body["ivrMenuId"] = ivr_menu_id
        return self._client.post("/v1/numbers/provision", body)

    def release(self, number_id: str) -> dict:
        return self._client.request(
            "DELETE",
            f"/v1/numbers/{_seg(number_id)}",
            query={"confirm": "true"},
        )


class Sms(_Namespace):
    def list(self, direction: Optional[str] = None, limit: Optional[int] = None) -> list[dict]:
        return self._client.get("/v1/sms", {"direction": direction, "limit": limit})

    def send(
        self,
        to: str,
        body: str,
        consent: bool,
        from_: Optional[str] = None,
        provider: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> dict:
        payload: dict[str, Any] = {"to": to, "body": body, "consent": consent}
        if from_:
            payload["from"] = from_
        if provider:
            payload["provider"] = provider
        return self._client.post("/v1/sms", payload, idempotency_key=idempotency_key)


class Telephony(_Namespace):
    def providers(self) -> list[dict]:
        return self._client.get("/v1/telephony/providers")


class OmallaClient:
    """Client for one Omalla server and one API key."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://127.0.0.1:8787",
        timeout: float = 30.0,
        retries: int = 2,
        user_agent: str = f"omalla-python/{__version__}",
    ) -> None:
        if not api_key:
            raise ValueError("an API key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = max(0, retries)
        self.user_agent = user_agent

        self.agents = Agents(self)
        self.tools = Tools(self)
        self.calls = Calls(self)
        self.workflows = Workflows(self)
        self.runs = Runs(self)
        self.templates = Templates(self)
        self.tasks = Tasks(self)
        self.bookings = Bookings(self)
        self.contacts = Contacts(self)
        self.escalations = Escalations(self)
        self.knowledge = Knowledge(self)
        self.keys = Keys(self)
        self.credentials = Credentials(self)
        self.numbers = Numbers(self)
        self.sms = Sms(self)
        self.telephony = Telephony(self)

    def __enter__(self) -> "OmallaClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Present for symmetry with session-based clients; urllib keeps none."""

    def request(
        self,
        method: str,
        path: str,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        idempotency_key: Optional[str] = None,
    ) -> JsonValue:
        url = f"{self.base_url}{path if path.startswith('/') else '/' + path}"
        if query:
            encoded = {key: value for key, value in query.items() if value is not None}
            if encoded:
                url = f"{url}?{urllib.parse.urlencode(encoded)}"

        args_digest: Optional[str] = None
        if idempotency_key and body is not None:
            args_digest = jcs_sha256(body)

        payload = None if body is None else json.dumps(body).encode("utf-8")
        attempts = self.retries + 1 if method == "GET" else 1
        last: Optional[OmallaApiError] = None

        for attempt in range(attempts):
            request = urllib.request.Request(url, data=payload, method=method)
            request.add_header("authorization", f"Bearer {self.api_key}")
            request.add_header("accept", "application/json")
            request.add_header("user-agent", self.user_agent)
            if payload is not None:
                request.add_header("content-type", "application/json")
            if idempotency_key:
                request.add_header("idempotency-key", idempotency_key)
            if args_digest:
                request.add_header("x-omalla-args-digest", args_digest)
            if headers:
                for hdr_key, hdr_val in headers.items():
                    request.add_header(hdr_key, hdr_val)
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return _decode(response.read(), response.status)
            except urllib.error.HTTPError as error:
                try:
                    parsed = _decode(error.read(), error.code)
                finally:
                    error.close()
                message = _error_message(parsed, error.reason)
                api_error = OmallaApiError(message, error.code, _error_code(parsed), parsed)
                if error.code >= 500 and method == "GET" and attempt + 1 < attempts:
                    last = api_error
                    time.sleep(0.2 * (attempt + 1))
                    continue
                raise api_error from None
            except urllib.error.URLError as error:
                api_error = OmallaApiError(f"cannot reach {self.base_url}: {error.reason}")
                if method == "GET" and attempt + 1 < attempts:
                    last = api_error
                    time.sleep(0.2 * (attempt + 1))
                    continue
                raise api_error from None

        raise last or OmallaApiError("request failed")

    def get(self, path: str, query: Optional[Mapping[str, Any]] = None) -> JsonValue:
        return self.request("GET", path, query=query)

    def post(
        self,
        path: str,
        body: Optional[Mapping[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> JsonValue:
        return self.request("POST", path, body=body, idempotency_key=idempotency_key)

    def patch(self, path: str, body: Optional[Mapping[str, Any]] = None) -> JsonValue:
        return self.request("PATCH", path, body=body)

    def put(self, path: str, body: Optional[Mapping[str, Any]] = None) -> JsonValue:
        return self.request("PUT", path, body=body)

    def delete(self, path: str) -> JsonValue:
        return self.request("DELETE", path)

    def health(self) -> dict:
        return self.get("/v1/health")

    def me(self) -> dict:
        return self.get("/v1/me")

    def metrics(self) -> dict:
        return self.get("/v1/metrics")

    def openapi(self) -> dict:
        return self.get("/openapi.json")

    def webhook(
        self,
        path: str,
        payload: Mapping[str, Any],
        idempotency_key: Optional[str] = None,
        signature: Optional[str] = None,
        timestamp: Optional[Union[int, str]] = None,
    ) -> JsonValue:
        extra: dict[str, str] = {}
        if signature:
            extra["x-omalla-signature"] = signature
        if timestamp is not None:
            extra["x-omalla-timestamp"] = str(timestamp)
        return self.request(
            "POST",
            f"/v1/hooks/{_seg(path)}",
            body=payload,
            headers=extra,
            idempotency_key=idempotency_key,
        )


def _seg(value: str) -> str:
    if not value:
        raise ValueError("id must not be empty")
    return urllib.parse.quote(value, safe="")


def _decode(raw: bytes, status: int) -> JsonValue:
    if status == 204 or not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return raw.decode("utf-8", errors="replace")


def _error_message(parsed: JsonValue, fallback: str) -> str:
    if isinstance(parsed, dict):
        error = parsed.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"]
        if isinstance(parsed.get("message"), str):
            return parsed["message"]
    return str(fallback)


def _error_code(parsed: JsonValue) -> str:
    if isinstance(parsed, dict):
        error = parsed.get("error")
        if isinstance(error, dict) and isinstance(error.get("code"), str):
            return error["code"]
    return "http_error"
