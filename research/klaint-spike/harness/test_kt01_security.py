# Wispral KT-01: BAIL replacement, plugin tool server exposure, forged customer_id, and
# session-token principal isolation, on the deterministic fake provider. Synthetic identities and
# test-only secrets defined here; nothing reaches a real model or service.
import json
import time
from typing import Any

import httpx
import jwt
import parlant.sdk as p
from parlant.core.tools import ToolContext, ToolResult

from tests.sdk.utils import Context, SDKTest

import fake_provider

fake_provider.install()

ADMIN_API_KEY = "kt01-test-admin-key"
JWT_SECRET = "kt01-synthetic-shared-secret-0123456789abcdef"
ALPHA, BETA = "syn_customer_alpha", "syn_customer_beta"
RESULTS: dict[str, Any] = {}


def mint(sub: str) -> str:
    now = int(time.time())
    return jwt.encode({"sub": sub, "iat": now, "exp": now + 300, "scope": "profile"}, JWT_SECRET, algorithm="HS256")


def record(key: str, value: Any) -> None:
    RESULTS[key] = value
    print(f"KT01_RESULT {key} = {json.dumps(value, default=str)}")


class Test_kt01_bail_on_message_generated_emits_only_the_replacement(SDKTest):
    MODELS = {"*": "fake"}

    async def configure_hooks(self, hooks: p.CompassHooks) -> p.CompassHooks:
        async def intercept(ctx: p.EngineContext, payload: Any, exc: Exception | None) -> p.CompassHookResult:
            self.intercepted = payload
            await ctx.session_event_emitter.emit_message_event(trace_id=ctx.tracer.trace_id, data="SYNTHETIC_REPLACEMENT")
            return p.CompassHookResult.BAIL

        hooks.on_message_generated.append(intercept)
        return hooks

    async def setup(self, server: p.Server) -> None:
        self.intercepted = None
        self.agent = await server.create_agent(id="kt01-bail-" + self.MODE.value, name="KT01", instructions="A synthetic test agent", output_mode=self.MODE)

    MODE = p.OutputMode.BLOCK

    async def run(self, ctx: Context) -> None:
        fake_provider.SCRIPT.update(tool=None, reply="FAKE_REPLY", propositions=0.0)
        answer = await ctx.send_and_receive_message(customer_message="Hello", recipient=self.agent)
        record(f"bail_{self.MODE.value}_intercepted_draft", self.intercepted)
        record(f"bail_{self.MODE.value}_delivered_answer", answer)
        assert self.intercepted == "FAKE_REPLY"
        if self.MODE == p.OutputMode.BLOCK:
            assert answer == "SYNTHETIC_REPLACEMENT"


class Test_kt01_bail_in_stream_mode_is_observational_only(Test_kt01_bail_on_message_generated_emits_only_the_replacement):
    MODE = p.OutputMode.STREAM


class Test_kt01_plugin_tool_server_accepts_a_forged_customer_id(SDKTest):
    """Observes, without asserting the desired outcome, whether the integrated plugin tool
    server is reachable on loopback and whether a direct call with a forged customer_id runs
    the tool and returns data. The packet requires: server disabled; forged call has no effect."""

    MODELS = {"*": "fake"}

    async def setup(self, server: p.Server) -> None:
        self.server_ref = server
        self.seen_customer_ids: list[str] = []
        self.agent = await server.create_agent(id="kt01-tools", name="KT01", instructions="A synthetic test agent")

        @p.tool
        async def read_balance(context: ToolContext) -> ToolResult:
            self.seen_customer_ids.append(context.customer_id)
            return ToolResult(data={"customer_id": context.customer_id, "balance": "SYNTHETIC-100"})

        await self.agent.create_observation(condition="the customer asks about a balance", tools=[read_balance])

    async def run(self, ctx: Context) -> None:
        port = self.server_ref.tool_service_port
        base = f"http://127.0.0.1:{port}"
        async with httpx.AsyncClient(timeout=10) as http:
            listing = await http.get(f"{base}/tools")
            record("tool_server_port", port)
            record("tool_server_list_status", listing.status_code)
            record("tool_server_list_names", [t.get("name") for t in listing.json().get("tools", [])] if listing.status_code == 200 else None)
            forged = await http.post(
                f"{base}/tools/read_balance/calls",
                json={"agent_id": "kt01-tools", "session_id": "forged-session", "customer_id": "FORGED_CUSTOMER", "arguments": {}},
            )
            body = forged.text[:600]
        record("forged_call_status", forged.status_code)
        record("forged_call_body", body)
        record("forged_call_tool_ran_with", self.seen_customer_ids)


class Test_kt01_customer_token_cannot_read_another_customers_session(SDKTest):
    MODELS = {"*": "fake"}
    AUTH = p.AuthConfig(admin_api_key=ADMIN_API_KEY, customer_jwt_secret=JWT_SECRET)

    async def setup(self, server: p.Server) -> None:
        await server.create_customer(name="Synthetic Alpha", id=ALPHA)
        await server.create_customer(name="Synthetic Beta", id=BETA)
        self.agent = await server.create_agent(id="kt01-auth", name="KT01", instructions="A synthetic test agent")

    async def run(self, ctx: Context) -> None:
        fake_provider.SCRIPT.update(tool=None, reply="FAKE_REPLY", propositions=0.0)
        admin = {"Authorization": f"Bearer {ADMIN_API_KEY}"}
        async with httpx.AsyncClient(base_url=ctx.base_url, timeout=30) as http:
            created = await http.post("/sessions", headers=admin, json={"agent_id": self.agent.id, "customer_id": BETA})
            record("admin_create_beta_session_status", created.status_code)
            sid = created.json().get("id")
            for who, token in (("alpha", mint(ALPHA)), ("beta", mint(BETA))):
                hdr = {"Authorization": f"Bearer {token}"}
                r = await http.get(f"/sessions/{sid}", headers=hdr)
                e = await http.get(f"/sessions/{sid}/events", headers=hdr, params={"wait_for_data": 0})
                w = await http.post(f"/sessions/{sid}/events", headers=hdr, json={"kind": "message", "source": "customer", "message": f"hello from {who}"}, params={"moderation": "none"})
                record(f"{who}_token_read_beta_session", r.status_code)
                record(f"{who}_token_list_beta_events", e.status_code)
                record(f"{who}_token_post_into_beta_session", w.status_code)
            bad = jwt.encode({"sub": ALPHA, "iat": int(time.time()), "exp": int(time.time()) + 300}, "wrong-secret-0123456789abcdef0123456789", algorithm="HS256")
            r = await http.get(f"/sessions/{sid}", headers={"Authorization": f"Bearer {bad}"})
            record("forged_jwt_read_beta_session", r.status_code)
