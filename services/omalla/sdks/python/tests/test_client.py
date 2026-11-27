"""Unit tests for the Omalla Python SDK against a local fake server."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from omalla import (
    OmallaApiError,
    OmallaClient,
    jcs_canonicalize,
    jcs_sha256,
    parse_stream_events,
    verify_webhook_signature,
)

Handler = Callable[[str, str, dict[str, str], bytes], tuple[int, Any]]


class _FakeServer:
    """Threaded HTTP server that answers with whatever the test queued."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.responses: list[tuple[int, Any]] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args: object) -> None:
                pass

            def _handle(self) -> None:
                length = int(self.headers.get("content-length") or 0)
                raw = self.rfile.read(length) if length else b""
                outer.requests.append(
                    {
                        "method": self.command,
                        "path": self.path,
                        "headers": {key.lower(): value for key, value in self.headers.items()},
                        "body": raw,
                    }
                )
                status, payload = outer.responses.pop(0) if outer.responses else (200, {})
                encoded = b"" if payload is None else json.dumps(payload).encode("utf-8")
                self.send_response(status)
                if encoded:
                    self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(encoded)))
                self.end_headers()
                if encoded:
                    self.wfile.write(encoded)

            do_GET = _handle
            do_POST = _handle
            do_PATCH = _handle
            do_PUT = _handle
            do_DELETE = _handle

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self.httpd.server_address[:2]
        return f"http://{host}:{port}"

    def queue(self, status: int, payload: Any) -> "_FakeServer":
        self.responses.append((status, payload))
        return self

    def start(self) -> "_FakeServer":
        self.thread.start()
        return self

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


class ClientTests(unittest.TestCase):
    server: _FakeServer
    client: OmallaClient

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = _FakeServer().start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.stop()

    def setUp(self) -> None:
        self.server.responses.clear()
        self.server.requests.clear()
        self.client = OmallaClient(api_key="omk_test_key", base_url=self.server.base_url, retries=1)

    def test_health_sends_bearer_and_returns_json(self) -> None:
        self.server.queue(200, {"ok": True, "telephonyDefault": "simulated"})
        health = self.client.health()
        self.assertTrue(health["ok"])
        request = self.server.requests[0]
        self.assertEqual(request["headers"]["authorization"], "Bearer omk_test_key")
        self.assertEqual(request["headers"]["user-agent"], "omalla-python/0.1.0")
        self.assertEqual(request["path"], "/v1/health")

    def test_query_parameters_skip_none_and_are_encoded(self) -> None:
        self.server.queue(200, [])
        self.client.calls.list(status="completed", limit=5)
        self.assertEqual(self.server.requests[0]["path"], "/v1/calls?status=completed&limit=5")

    def test_simulated_call_posts_json_body(self) -> None:
        self.server.queue(201, {"id": "call_1", "simulation": True})
        call = self.client.calls.simulate(say=["hello"], press=["1"])
        self.assertEqual(call["id"], "call_1")
        request = self.server.requests[0]
        self.assertEqual(request["method"], "POST")
        self.assertEqual(request["path"], "/v1/calls")
        body = json.loads(request["body"])
        self.assertEqual(body["say"], ["hello"])
        self.assertEqual(body["press"], ["1"])
        self.assertEqual(body["from"], "+15550009999")

    def test_idempotency_key_and_jcs_args_digest_sent_on_outbound_and_sms(self) -> None:
        self.server.queue(201, {"id": "call_out_1", "simulation": True})
        self.client.calls.outbound(
            to="+15550002222",
            agent_id="agt_1",
            consent=True,
            variables={"attempt": 1},
            idempotency_key="idem_call_1",
        )
        req = self.server.requests[0]
        self.assertEqual(req["headers"]["idempotency-key"], "idem_call_1")
        self.assertEqual(len(req["headers"]["x-omalla-args-digest"]), 64)

        self.server.queue(201, {"id": "sms_1", "simulated": True})
        self.client.sms.send(
            to="+15550002222",
            body="مرحبا",
            consent=True,
            idempotency_key="idem_sms_1",
        )
        sms_req = self.server.requests[1]
        self.assertEqual(sms_req["headers"]["idempotency-key"], "idem_sms_1")

    def test_jcs_canonicalize_orders_keys_and_rejects_floats(self) -> None:
        canonical = jcs_canonicalize({"b": 2, "a": [True, False, None, "غداً"]})
        self.assertEqual(canonical, '{"a":[true,false,null,"غداً"],"b":2}')
        self.assertEqual(len(jcs_sha256({"b": 2, "a": 1})), 64)
        self.assertEqual(jcs_sha256({"b": 2, "a": 1}), jcs_sha256({"a": 1, "b": 2}))
        with self.assertRaises(ValueError):
            jcs_canonicalize({"amount": 12.5})
        with self.assertRaises(ValueError):
            jcs_canonicalize({"bad": "\ud800"})

    def test_agent_and_workflow_rollback_and_versions(self) -> None:
        self.server.queue(200, [{"version": 2}, {"version": 1}])
        versions = self.client.agents.versions("agt_1")
        self.assertEqual(len(versions), 2)
        self.assertEqual(self.server.requests[0]["path"], "/v1/agents/agt_1/versions")

        self.server.queue(200, {"id": "agt_1", "version": 3})
        rolled = self.client.agents.rollback("agt_1", version=1, note="revert prompt")
        self.assertEqual(rolled["version"], 3)
        self.assertEqual(self.server.requests[1]["path"], "/v1/agents/agt_1/rollback")
        self.assertEqual(json.loads(self.server.requests[1]["body"]), {"version": 1, "note": "revert prompt"})

        self.server.queue(200, {"id": "wf_1", "version": 4})
        wf_rolled = self.client.workflows.rollback("wf_1", version=2)
        self.assertEqual(wf_rolled["version"], 4)
        self.assertEqual(self.server.requests[2]["path"], "/v1/workflows/wf_1/rollback")

    def test_webhook_hmac_and_standard_webhooks_verification(self) -> None:
        raw = b'{"event":"call.ended","ok":true}'
        key = base64.b64encode(b"0123456789abcdef0123456789abcdef").decode("ascii")
        secret = f"whsec_{key}"
        ts = "1700000000"
        msg_id = "msg_abc123"
        sig = base64.b64encode(
            hmac.new(base64.b64decode(key), f"{msg_id}.{ts}.".encode("utf-8") + raw, hashlib.sha256).digest()
        ).decode("ascii")
        ok = verify_webhook_signature(
            raw,
            {"webhook-id": msg_id, "webhook-timestamp": ts, "webhook-signature": f"v1,{sig}"},
            secret,
            now_sec=1700000120,
        )
        self.assertTrue(ok["valid"])
        self.assertEqual(ok["event_key"], msg_id)

        expired = verify_webhook_signature(
            raw,
            {"webhook-id": msg_id, "webhook-timestamp": ts, "webhook-signature": f"v1,{sig}"},
            secret,
            now_sec=1700000400,
        )
        self.assertFalse(expired["valid"])

        om_secret = "om_sec_py"
        om_sig = hmac.new(om_secret.encode("utf-8"), f"{ts}.".encode("utf-8") + raw, hashlib.sha256).hexdigest()
        timeless = verify_webhook_signature(
            raw,
            {"x-omalla-signature": f"sha256={om_sig}"},
            om_secret,
            now_sec=1700000120,
        )
        self.assertFalse(timeless["valid"])

        om_ok = verify_webhook_signature(
            raw,
            {
                "x-omalla-signature": f"sha256={om_sig}",
                "x-omalla-timestamp": ts,
                "x-omalla-delivery-id": "unsigned_forged_id",
            },
            om_secret,
            now_sec=1700000120,
        )
        self.assertTrue(om_ok["valid"])
        self.assertTrue(str(om_ok["event_key"]).startswith(f"omalla:{ts}:"))

    def test_streaming_event_parser_and_stream_url(self) -> None:
        frames = [
            'data: {"type":"snapshot","call":{"id":"call_1"}}\n',
            '{"type":"assistant.delta","callId":"call_1","data":{"text":"مرحبا"}}',
        ]
        events = list(parse_stream_events(frames))
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["type"], "snapshot")
        self.assertEqual(events[1]["type"], "assistant.delta")
        self.assertIn("/v1/calls/call_1/stream?token=omk_test_key", self.client.calls.stream_url("call_1"))

    def test_api_error_carries_status_and_code(self) -> None:
        self.server.queue(
            403,
            {"error": {"code": "blocked_by_policy", "message": "sending SMS requires recorded consent"}},
        )
        with self.assertRaises(OmallaApiError) as caught:
            self.client.sms.send(to="+15550002222", body="hi", consent=False)
        self.assertEqual(caught.exception.status, 403)
        self.assertEqual(caught.exception.code, "blocked_by_policy")
        self.assertIn("consent", str(caught.exception))

    def test_get_retries_on_5xx(self) -> None:
        self.server.queue(500, {"error": {"code": "internal", "message": "boom"}})
        self.server.queue(200, {"ok": True})
        self.assertEqual(self.client.health()["ok"], True)
        self.assertEqual(len(self.server.requests), 2)

    def test_post_is_not_retried(self) -> None:
        self.server.queue(500, {"error": {"code": "internal", "message": "boom"}})
        with self.assertRaises(OmallaApiError):
            self.client.calls.simulate()
        self.assertEqual(len(self.server.requests), 1)

    def test_release_sends_confirmation_query(self) -> None:
        self.server.queue(200, {"released": True, "id": "num_1"})
        self.client.numbers.release("num_1")
        request = self.server.requests[0]
        self.assertEqual(request["method"], "DELETE")
        self.assertEqual(request["path"], "/v1/numbers/num_1?confirm=true")

    def test_no_content_returns_none(self) -> None:
        self.server.queue(204, None)
        self.assertIsNone(self.client.keys.revoke("key_1"))

    def test_openapi_is_fetched_outside_the_v1_prefix(self) -> None:
        self.server.queue(200, {"openapi": "3.1.0", "paths": {}})
        self.assertEqual(self.client.openapi()["openapi"], "3.1.0")
        self.assertEqual(self.server.requests[0]["path"], "/openapi.json")

    def test_path_segments_are_escaped(self) -> None:
        self.server.queue(200, {"ok": True})
        self.client.credentials.put("MY KEY", "secret")
        self.assertEqual(self.server.requests[0]["path"], "/v1/credentials/MY%20KEY")

    def test_empty_key_is_refused_before_any_request(self) -> None:
        with self.assertRaises(ValueError):
            OmallaClient(api_key="")
        self.assertEqual(self.server.requests, [])

    def test_unreachable_server_raises_transport_error(self) -> None:
        client = OmallaClient(api_key="omk_x", base_url="http://127.0.0.1:1", retries=0, timeout=1)
        with self.assertRaises(OmallaApiError) as caught:
            client.health()
        self.assertEqual(caught.exception.status, 0)
        self.assertEqual(caught.exception.code, "transport_error")


if __name__ == "__main__":
    unittest.main()
