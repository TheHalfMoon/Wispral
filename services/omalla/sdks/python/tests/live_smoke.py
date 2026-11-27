"""Live smoke test: the Python SDK against a real Omalla server.

Run by ``npm run smoke:python`` (or by hand with a server already running)::

    OMALLA_BASE_URL=http://127.0.0.1:8787 \
    OMALLA_API_KEY=$(cat .omalla/api-key.txt) \
    python sdks/python/tests/live_smoke.py

Exercises only the simulated provider: no carrier, no number purchase, no cost.
"""

from __future__ import annotations

import os
import sys

from omalla import OmallaClient


def main() -> int:
    base_url = os.environ.get("OMALLA_BASE_URL", "http://127.0.0.1:8787")
    api_key = os.environ.get("OMALLA_API_KEY", "")
    if not api_key:
        print("OMALLA_API_KEY is required", file=sys.stderr)
        return 2

    checks: list[tuple[str, bool, str]] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        checks.append((name, condition, detail))
        print(f"  {'PASS' if condition else 'FAIL'}  {name}{f'  ({detail})' if detail else ''}")

    with OmallaClient(api_key=api_key, base_url=base_url, user_agent="omalla-python-smoke/0.1.0") as client:
        print("\nhealth and identity")
        health = client.health()
        check("health ok", health.get("ok") is True)
        check("simulated default", health.get("telephonyDefault") == "simulated")
        me = client.me()
        check("me returns a principal", bool(me.get("principal", {}).get("tenantId")))
        spec = client.openapi()
        check("openapi is 3.1", spec.get("openapi") == "3.1.0")
        check("openapi documents calls", "/v1/calls" in spec.get("paths", {}))

        print("\ntelephony")
        providers = client.telephony.providers()
        simulated = next((item for item in providers if item["id"] == "simulated"), None)
        check("provider list is a list", isinstance(providers, list))
        check("simulator available", bool(simulated and simulated["available"]))
        check(
            "carriers honestly unavailable",
            all(not item["available"] for item in providers if item["id"] != "simulated"),
        )
        numbers = client.numbers.list()
        check("seeded number listed", len(numbers) >= 1, f"{len(numbers)} number(s)")
        search = client.numbers.search(area_code="555")
        check("free number search", search.get("carrierCharges") is False, f"{len(search.get('offers', []))} offers")

        print("\nsimulated call")
        call = client.calls.simulate(say=["I would like to book a cleaning for Tuesday at 10am."])
        check("call created", bool(call.get("id")))
        check("call labelled simulated", call.get("simulation") is True)
        detail = client.calls.get(call["id"])
        turns = detail.get("transcript", [])
        check("transcript captured", len(turns) >= 2, f"{len(turns)} turns")
        check("assistant spoke", any(turn["role"] == "assistant" for turn in turns))

        print("\nsms")
        sms = client.sms.send(to="+15550002222", body="Omalla Python smoke", consent=True)
        check("sms accepted", bool(sms.get("id")))
        check("sms simulated", sms.get("simulated") is True)
        try:
            client.sms.send(to="+15550002222", body="no", consent=False)
        except Exception as error:  # OmallaApiError, imported lazily for the message
            check("sms without consent refused", "consent" in str(error).lower())
        else:
            check("sms without consent refused", False)

        print("\nautomation")
        templates = client.templates.list()
        check("templates available", len(templates) >= 10, f"{len(templates)} templates")
        workflows = client.workflows.list()
        check("workflow list", isinstance(workflows, list))
        check("run history", isinstance(client.runs.list(), list))

    failed = [name for name, ok, _ in checks if not ok]
    print("\nresult")
    if failed:
        print(f"  {len(failed)} check(s) failed: {', '.join(failed)}")
        return 1
    print(f"  all {len(checks)} Python smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
