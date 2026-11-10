# Wispral KT-01: model calls per turn, turn latency (p50/p95) and process memory, on the
# deterministic fake provider. Run alone on an otherwise idle machine; results are machine-specific.
import json
import os
import statistics
import time
from typing import Any

import parlant.sdk as p
from parlant.core.tools import ToolContext, ToolResult

from tests.sdk.utils import Context, SDKTest

import fake_provider

fake_provider.install()
TURNS = int(os.environ.get("KT01_TURNS", "40"))


def rss_mb() -> float:
    # Working set of this process via the Windows API (no extra dependency).
    import ctypes
    from ctypes import wintypes

    class PMC(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t)]

    pmc = PMC(); pmc.cb = ctypes.sizeof(PMC)
    k32 = ctypes.WinDLL("kernel32"); psapi = ctypes.WinDLL("psapi")
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
    return round(pmc.WorkingSetSize / 2**20, 1)


def record(key: str, value: Any) -> None:
    print(f"KT01_RESULT {key} = {json.dumps(value, default=str)}")


class Test_kt01_perf_on_fake_backend(SDKTest):
    MODELS = {"*": "fake"}

    async def setup(self, server: p.Server) -> None:
        self.agent = await server.create_agent(id="kt01-perf", name="KT01", instructions="A synthetic test agent",
                                               output_mode=p.OutputMode.BLOCK)

        @p.tool
        async def lookup_order(context: ToolContext, order_ref: str) -> ToolResult:
            return ToolResult(data={"order_ref": order_ref, "status": "synthetic"})

        await self.agent.create_observation(condition="the customer asks about an order", tools=[lookup_order])

    async def _turns(self, ctx: Context, label: str, tool: str | None, propositions: float) -> None:
        fake_provider.SCRIPT.update(tool=tool, args={"order_ref": "SYN-1"}, reply="FAKE_REPLY", propositions=propositions)
        latencies, per_turn = [], []
        for i in range(TURNS):
            fake_provider.CALLS.clear()
            t0 = time.perf_counter()
            await ctx.send_and_receive_message(f"Where is my order SYN-{i}?", self.agent)
            latencies.append((time.perf_counter() - t0) * 1000)
            counts: dict[str, int] = {}
            for c in fake_provider.CALLS:
                counts[c["capability"]] = counts.get(c["capability"], 0) + 1
            per_turn.append(counts)
        q = statistics.quantiles(latencies, n=20)
        record(f"{label}_turns", TURNS)
        record(f"{label}_latency_ms_p50", round(statistics.median(latencies), 1))
        record(f"{label}_latency_ms_p95", round(q[18], 1))
        record(f"{label}_latency_ms_max", round(max(latencies), 1))
        keys = sorted({k for d in per_turn for k in d})
        record(f"{label}_model_calls_per_turn_median", {k: statistics.median([d.get(k, 0) for d in per_turn]) for k in keys})

    async def run(self, ctx: Context) -> None:
        time.sleep(2)
        record("rss_mb_idle_after_startup", rss_mb())
        await self._turns(ctx, "plain_reply", tool=None, propositions=0.0)
        await self._turns(ctx, "tool_turn", tool="lookup_order", propositions=1.0)
        time.sleep(2)
        record("rss_mb_idle_after_turns", rss_mb())
