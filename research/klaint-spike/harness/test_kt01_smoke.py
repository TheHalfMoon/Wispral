# Wispral KT-01 smoke: can a Parlant v4 SDK server answer one turn on the fake provider alone?
from typing import Any

import parlant.sdk as p

from tests.sdk.utils import Context, SDKTest

import fake_provider

fake_provider.install()


class Test_kt01_smoke_fake_provider_answers_one_turn(SDKTest):
    MODELS = {"*": "fake"}

    async def setup(self, server: p.Server) -> None:
        self.agent = await server.create_agent(id="kt01-smoke", name="KT01", instructions="A synthetic test agent")

    async def run(self, ctx: Context) -> None:
        fake_provider.CALLS.clear()
        fake_provider.SCRIPT.update(tool=None, reply="FAKE_REPLY")
        reply = await ctx.send_and_receive_message("Hello", self.agent)
        print("REPLY", repr(reply))
        print("CALLS", [(c["capability"], c["detail"]) for c in fake_provider.CALLS])
        assert reply.strip()
