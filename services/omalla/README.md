# Omalla

Local-first, agent-native voice AI and business automation. Omalla answers
calls, runs a conversation, calls tools, and executes workflows after the call.
Everything runs on one machine by default, with no paid API and no carrier.

**Status: v0.1.0 release candidate, not published.** Simulated telephony and
local providers are verified. Real PSTN calls are implemented but **not run**:
no carrier credentials exist in this environment.

## Quick start

```bash
npm install
npm run build
npm run dev
```

Open <http://127.0.0.1:8787>. The first run seeds a demo workspace and writes an
`omk_...` key to `.omalla/api-key.txt`; paste it into the login screen. The demo
contains one dental-reception agent, one simulated number, an IVR menu and
eleven workflow templates.

```bash
npm run verify        # build + typecheck + 64 tests + licence and docs gates
npm run smoke         # starts a real server and walks the HTTP surface (33 checks)
```

## What actually works

| Capability | State |
| --- | --- |
| Simulated inbound/outbound calls with transcript and audio events | verified |
| Barge-in, VAD, sentence chunking, conversation policies | unit-tested |
| Local TTS/STT through Windows SAPI (David/Zira/Mark; en-US, zh-TW, fr-FR, zh-CN) | verified offline |
| Mock and OpenAI-compatible LLM/TTS/STT adapters, failover | unit-tested |
| Native workflow engine with retries, idempotency, dry-run, SSRF guard | verified |
| n8n import/export and signed live-call webhook tool | unit-tested |
| Twilio/SignalWire webhooks, TwiML, Media Streams, REST control plane | unit-tested offline |
| Number search/provision/release, SMS, recording consent fields | unit-tested |
| Dashboard for calls, workflows, automations, numbers, SMS, providers | served and smoke-tested over HTTP; not opened in a browser |
| SDK, CLI, MCP server | built; smoke-tested |
| OpenAPI 3.1 document | served at `/openapi.json`, drift-tested against the routes |
| TypeScript and Python SDKs | built; Python has 12 unit tests and a 20-check live smoke |

## Clients

The TypeScript SDK is a workspace package (`@omalla/sdk`). The Python SDK is
standard-library only, so it needs no `pip install`:

```python
import sys; sys.path.insert(0, "sdks/python")
from omalla import OmallaClient

client = OmallaClient(api_key="omk_...", base_url="http://127.0.0.1:8787")
call = client.calls.simulate(say=["I would like to book a cleaning on Tuesday."])
print(client.calls.get(call["id"])["transcript"])
```

```bash
npm run test:python    # unit tests against a fake server
npm run smoke:python   # boots a real server, 20 checks
omalla openapi --out openapi.json
```

## What does not work yet

- **Real phone calls.** Twilio and SignalWire adapters have never talked to a
  live carrier. No credentials, no numbers, no PSTN test.
- **Telnyx and Vonage.** Listed as unavailable; adapters do not exist.
- **SIP gateways.** Contract and compose skeletons exist; no engine has been run.
- **Arabic speech.** No local Arabic voice or recogniser is installed. The data
  model is multilingual; the audio path is not.
- **Docker-based donors.** Docker was not running, so Asterisk, FreeSWITCH,
  LiveKit and Jambonz were not started.
- **Publishing.** Nothing is published, deployed or sold.

## Zero-cost doctrine

Simulated telephony is the default. A carrier is used only when its credentials
exist and a caller explicitly selects it. Number purchases are disabled unless
`OMALLA_ALLOW_CARRIER_PURCHASES=1`, and every purchase requires `confirm: true`
plus an owner role. Omalla never bills for telephony; carrier charges are the
carrier's and are disclosed in the UI and API.

## Shape of the system

```
carrier / SIP / simulator
        │ webhook + media WebSocket
        ▼
   @omalla/telephony  ──  MediaBridge (μ-law, VAD, barge-in)
        │
        ▼
   @omalla/server  ──  ConversationEngine  ──  @omalla/providers
        │                    │
        │                    └── tools ──► n8n webhook | native workflow
        ▼
   @omalla/workflow  ──  local stores | HTTP nodes | integrations
        │
        ▼
   JSON store under .omalla/ (single machine, no database)
```

Packages: `core`, `providers`, `workflow`, `telephony`, `sdk`, `server`, `cli`,
`mcp`. Dashboard: `apps/dashboard/public` (vanilla ES modules, no build step).

## Documentation

- [MASTER_PLAN.md](docs/MASTER_PLAN.md) - scope, phases, non-goals
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - components and data flow
- [REA_VAPI.md](docs/REA_VAPI.md) - what public artifacts show about Vapi
- [REA_TELEPHONY.md](docs/REA_TELEPHONY.md) - Twilio, SIP and carrier protocols
- [REA_AUTOMATION.md](docs/REA_AUTOMATION.md) - n8n and the automation landscape
- [COMPETITIVE_MATRIX.md](docs/COMPETITIVE_MATRIX.md) - positioning
- [SOURCE_INVENTORY.md](docs/SOURCE_INVENTORY.md) - donors, licences, revisions
- [DONOR_TRANSPLANT_MAP.md](docs/DONOR_TRANSPLANT_MAP.md) - what was reused
- [SECURITY_MODEL.md](docs/SECURITY_MODEL.md) - threats and controls
- [AUTOMATION_EXPANSION.md](docs/AUTOMATION_EXPANSION.md) - automation roadmap
- [IMPLEMENTATION_LEDGER.md](docs/IMPLEMENTATION_LEDGER.md) - what was built, when
- [TEST_MATRIX.md](docs/TEST_MATRIX.md) - evidence per capability
- [RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md) - v0.1.0 gates

## Licence

Apache-2.0. No donor code has been copied into this repository. See
[SOURCE_INVENTORY.md](docs/SOURCE_INVENTORY.md) for the distinction between
reference material and Omalla's own implementation.
