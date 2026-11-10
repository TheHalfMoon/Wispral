# Wispral KT-01: hook firing order around a tool call, on the deterministic fake provider.
from typing import Any

import parlant.sdk as p
from parlant.core.tools import ToolContext, ToolResult

from tests.sdk.utils import Context, SDKTest

import fake_provider

fake_provider.install()
LOG: list[str] = []


def _hook(name: str) -> Any:
    async def h(context: Any, payload: Any, exc: Any) -> p.CompassHookResult:
        LOG.append(name)
        return p.CompassHookResult.CALL_NEXT
    return h


class Test_kt01_hook_order_around_a_tool_call(SDKTest):
    MODELS = {"*": "fake"}

    async def configure_hooks(self, hooks: p.CompassHooks) -> p.CompassHooks:
        for name in ("on_preparing", "on_step_started", "on_reviewing_tool_calls", "on_tool_calls_reviewed",
                     "on_calling_tools", "on_tool_calls_completed", "on_step_completed",
                     "on_generating_messages", "on_reviewing_message", "on_message_generated", "on_messages_emitted"):
            getattr(hooks, name).append(_hook(name))
        return hooks

    async def setup(self, server: p.Server) -> None:
        self.tool_ran = False
        self.agent = await server.create_agent(id="kt01-hooks", name="KT01", instructions="A synthetic test agent")

        @p.tool
        async def lookup_order(context: ToolContext, order_ref: str) -> ToolResult:
            self.tool_ran = True
            return ToolResult(data={"order_ref": order_ref, "status": "synthetic"})

        await self.agent.create_observation(condition="the customer asks about an order", tools=[lookup_order])

    async def run(self, ctx: Context) -> None:
        LOG.clear(); fake_provider.CALLS.clear()
        fake_provider.SCRIPT.update(tool="lookup_order", args={"order_ref": "SYN-1"}, reply="FAKE_REPLY", propositions=1.0)
        reply = await ctx.send_and_receive_message("Where is my order SYN-1?", self.agent)
        print("REPLY", repr(reply)); print("TOOL_RAN", self.tool_ran)
        print("HOOKS", LOG)
        print("CALLS", [(c["capability"], c["detail"]) for c in fake_provider.CALLS])
