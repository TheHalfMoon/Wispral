# Wispral KT-01 on Parlant v3.3.2 (fallback pin): one turn on the fake NLPService, BAIL on
# on_message_generated, and the integrated tool server's handling of a forged customer_id.
# Synthetic identities only.
import json
import time
from typing import Any, Callable

import httpx
import parlant.sdk as p
from parlant.core.engines.alpha.perceived_performance_policy import (
    NullPerceivedPerformancePolicy, PerceivedPerformancePolicy,
)
from parlant.core.tools import ToolContext, ToolResult

from tests.sdk.utils import Context, SDKTest, get_random_port

import fake_provider_v3


def record(key: str, value: Any) -> None:
    print(f"KT01V3_RESULT {key} = {json.dumps(value, default=str)}")


class _FakeV3Test(SDKTest):
    async def create_server(self, port: int) -> tuple[p.Server, Callable[[], p.Container]]:
        test_container: p.Container = p.Container()

        async def configure_container(container: p.Container) -> p.Container:
            nonlocal test_container
            test_container = container.clone()
            test_container[PerceivedPerformancePolicy] = NullPerceivedPerformancePolicy()
            return test_container

        self.tool_port = get_random_port()
        return p.Server(
            port=port,
            tool_service_port=self.tool_port,
            log_level=p.LogLevel.TRACE,
            configure_container=configure_container,
            configure_hooks=self.configure_hooks,
            nlp_service=fake_provider_v3.factory,
        ), lambda: test_container


class Test_kt01_v3_one_turn_and_bail(_FakeV3Test):
    async def configure_hooks(self, hooks: p.EngineHooks) -> p.EngineHooks:
        async def intercept(ctx: Any, payload: Any, exc: Exception | None) -> Any:
            self.intercepted = True
            await ctx.session_event_emitter.emit_message_event(trace_id=ctx.tracer.trace_id, data="SYNTHETIC_REPLACEMENT")
            return p.EngineHookResult.BAIL

        hooks.on_message_generated.append(intercept)
        return hooks

    async def setup(self, server: p.Server) -> None:
        self.intercepted = False
        self.agent = await server.create_agent(name="KT01v3", description="A synthetic test agent")

    async def run(self, ctx: Context) -> None:
        fake_provider_v3.CALLS.clear()
        t0 = time.perf_counter()
        answer = await ctx.send_and_receive_message(customer_message="Hello", recipient=self.agent)
        record("v3_turn_ms", round((time.perf_counter() - t0) * 1000, 1))
        record("v3_bail_hook_fired", self.intercepted)
        record("v3_delivered_answer", answer)
        counts: dict[str, int] = {}
        for c in fake_provider_v3.CALLS:
            counts[c["capability"] + ":" + c["detail"]] = counts.get(c["capability"] + ":" + c["detail"], 0) + 1
        record("v3_model_calls_in_turn", counts)


class Test_kt01_v3_tool_server_forged_customer_id(_FakeV3Test):
    async def setup(self, server: p.Server) -> None:
        self.seen: list[str] = []
        self.agent = await server.create_agent(name="KT01v3tools", description="A synthetic test agent")

        @p.tool
        async def read_balance(context: ToolContext) -> ToolResult:
            self.seen.append(context.customer_id)
            return ToolResult(data={"customer_id": context.customer_id, "balance": "SYNTHETIC-100"})

        await self.agent.create_guideline(condition="the customer asks about a balance", action="look up the balance", tools=[read_balance])

    async def run(self, ctx: Context) -> None:
        base = f"http://127.0.0.1:{self.tool_port}"
        async with httpx.AsyncClient(timeout=10) as http:
            listing = await http.get(f"{base}/tools")
            forged = await http.post(f"{base}/tools/read_balance/calls",
                                     json={"agent_id": "x", "session_id": "forged-session", "customer_id": "FORGED_CUSTOMER", "arguments": {}})
        record("v3_tool_server_list_status", listing.status_code)
        record("v3_forged_call_status", forged.status_code)
        record("v3_forged_call_body", forged.text[:400])
        record("v3_forged_call_tool_ran_with", self.seen)
