# Architecture

## One process, eight packages

Omalla runs as a single Node.js process (Node >= 22.6, built and tested on
24.19). Fastify serves the REST API, the dashboard and the WebSocket endpoints.
There is no database server, no message broker and no container requirement.

```
apps/dashboard/public          vanilla ES modules, no build step
packages/core                  types, ids, errors, events, redaction, logging,
                               secrets, JSON store, provider contracts,
                               conversation engine, policy, audio primitives
packages/providers             mock | SAPI | OpenAI-compatible | HTTP | failover
packages/workflow              expressions, nodes, engine, n8n import/export,
                               templates, local automation store
packages/telephony             G.711 μ-law, resampling, WAV, VAD, provider
                               contract, Twilio/SignalWire, simulator,
                               registry, MediaBridge, SIP contract
packages/sdk                   typed HTTP client
packages/server                config, credentials, runtime, tools, routes
packages/cli                   omalla command
packages/mcp                   MCP stdio server
```

Dependency direction is one-way: `core` is imported by everything; `server`
composes `providers`, `workflow` and `telephony`; `sdk` talks HTTP only;
`cli` and `mcp` use the SDK or the runtime.

## Call paths

### Simulated inbound (default, free)

```
POST /v1/calls { from, say?, digits? }
  → runtime.startInbound()
  → SimulatedTelephonyProvider.receiveInbound()
  → ConversationEngine.turn() per utterance
  → tool calls (transfer | booking | workflow | n8n_workflow | …)
  → call.ended, post-call workflow triggered
```

Audio events are synthesized into the same shape a carrier uses, so the
conversation path is identical whether the caller is a test or a phone.

### Carrier inbound (Twilio / SignalWire)

```
carrier → POST /telephony/twilio/voice (form, X-Twilio-Signature)
  → verify signature over the exact public URL + sorted form fields
  → match PhoneNumber by `To` → agent or IVR menu
  → respond TwiML: <Connect><Stream url="wss://…/telephony/twilio/media">
carrier → WS /telephony/twilio/media
  → connected → start → media frames (base64 μ-law 8 kHz mono)
  → MediaBridge: decode → VAD → STT → ConversationEngine → TTS → resample → encode
  → mark/clear frames for barge-in
carrier → POST /telephony/twilio/status → canonical CallStatusEvent
```

Recording is opt-in per agent (`recording.enabled`) and consent is announced
before the stream starts. The adapter never records silently.

### Outbound

```
POST /v1/calls/outbound { to, agentId, consent: true }
  → policy: tenant.outboundEnabled, daily cap, quiet hours, consent
  → provider.createCall() with answer/status/recording callbacks
  → same media path as inbound
```

Carrier outbound requires `allowCarrierPurchases` only for *number purchases*;
placing a call requires a configured carrier and explicit consent.

## Media pipeline

| Stage | Detail |
| --- | --- |
| Wire format | base64 μ-law, 8 kHz, mono, 20 ms frames (160 bytes) |
| Decode | μ-law → PCM16, then resample to the provider's rate |
| VAD | energy + zero-crossing heuristic with hangover; no model required |
| STT | provider interface; SAPI on Windows, OpenAI-compatible otherwise |
| TTS | provider interface; SAPI, mock, OpenAI-compatible |
| Barge-in | caller speech during playback cancels queued audio and emits `barge_in` |
| Backpressure | bounded playback queue; a slow consumer drops frames instead of growing memory |
| Metrics | caller speech end → first assistant audio, recorded per turn |

The `MediaBridge` is transport-neutral. Twilio's JSON socket, a future SIP
gateway socket and the simulator all feed the same methods.

## Conversation engine

- System prompt + first message from the agent version.
- Retrieval over local knowledge bases, tenant-scoped, citations kept.
- Tool loop bounded by `maxToolRounds`; each call carries a principal resolved
  by the server, never by the model.
- Policy checks before outbound actions: consent, quiet hours, daily cap,
  transfer destinations.
- Sentence chunking so TTS starts before the full reply exists.
- Transcript turns are persisted with latency and token metrics.

## Workflow engine

Deterministic graph execution, not an LLM planner.

| Concern | Implementation |
| --- | --- |
| Triggers | `manual`, `webhook`, `call_ended`, `schedule`, `event` |
| Nodes | `trigger`, `condition`, `http`, `transform`, `delay`, `end`, `local.*`, `sms.send`, `email.send`, `calendar.create_event`, `crm.upsert_contact`, `human.escalate`, `call.start`, `n8n.webhook`, Trello/Google/Slack/WhatsApp integrations |
| Expressions | `{{trigger.payload.x}}`, `{{trigger.x}}` shorthand, `{{nodes.id.output.y}}`, `exists(...)`, comparisons |
| Retries | per-node `retry` with bounded backoff; attempts recorded |
| Idempotency | trigger key remembered for `idempotencyWindowSec`; duplicates return `skipped` |
| Dry run | HTTP is recorded, never sent; a synthetic response is returned |
| SSRF | `evaluateUrl` rejects private/link-local targets unless `allowPrivateHttp` |
| Secrets | integration nodes read from the encrypted credential store |
| n8n import | known node types map to Omalla nodes; `Code` nodes are **not** executed |
| n8n export | Omalla workflows render to an n8n-compatible JSON skeleton |

`end` is structural and outputs `{ ended: true }`. The live tool result reports
the last non-`end` node output so the agent says something useful.

## Automation entry points

1. **Post-call**: `call_ended` workflow receives call id, transcript, summary,
   caller number, extracted fields.
2. **Mid-call, native**: `workflow` tool runs an active workflow by id,
   idempotent per call + tool, and returns its last meaningful output as speech.
3. **Mid-call, external**: `n8n_workflow` tool POSTs a signed payload to a
   production webhook URL and extracts spoken text from the JSON response.
4. **Agent-driven**: MCP server exposes calls, workflows, tasks, bookings,
   knowledge and webhooks as tools for an external agent.
5. **Webhook**: `POST /v1/hooks/:path` with the tenant API key.

## Storage

A JSON document store under `OMALLA_DATA_DIR` (default `.omalla/`). Collections:
`tenants`, `apiKeys`, `agents`, `tools`, `calls`, `workflows`, `workflowRuns`,
`tasks`, `bookings`, `escalations`, `knowledgeBases`, `phoneNumbers`,
`ivrMenus`, `credentials`, `contacts`, `sms`.

Writes are debounced and atomic (write temp + rename). This is appropriate for
one machine and a handful of concurrent calls. It is **not** a multi-writer
database; the store documents that limit rather than pretending otherwise.

## API surface

- `/v1/health`, `/v1/me`, `/v1/metrics`
- agents, tools, calls, workflows, runs, templates, keys, credentials
- tasks, bookings, contacts, escalations, knowledge bases
- numbers, SMS, telephony providers
- `/v1/hooks/:path` inbound webhooks
- `/v1/calls/:id/stream` live event WebSocket
- `/telephony/:provider/{voice,dtmf,status,recording,sms}` carrier webhooks
- `/telephony/:provider/media` carrier media WebSocket
- `/openapi.json` the OpenAPI 3.1 document (public, no key)

The document is generated from `packages/server/src/openapi.ts`, not from the
route handlers, so `tests/openapi.test.ts` fails if the two drift in either
direction. Carrier webhooks and the WebSocket are declared as exclusions rather
than half-described, and the test requires every exclusion to still exist.
TypeScript and Python SDK clients mirror the same surface.

Auth: `Authorization: Bearer omk_...`, hashed at rest, tenant-scoped, roles
`owner > admin > operator > viewer`. Carrier webhooks authenticate with the
carrier's signature; the SIP path (not enabled) uses a shared gateway token.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `OMALLA_DATA_DIR` | `.omalla` | store, key file, recordings |
| `OMALLA_HOST` / `OMALLA_PORT` | `127.0.0.1` / `8787` | bind address |
| `OMALLA_ALLOW_REMOTE` | `0` | bind non-loopback |
| `OMALLA_SEED_DEMO` | `1` | create the demo workspace |
| `OMALLA_ALLOW_PRIVATE_HTTP` | `0` | allow workflow HTTP to private IPs |
| `OMALLA_ALLOW_CARRIER_PURCHASES` | `0` | enable carrier number purchases |
| `OMALLA_MASTER_KEY` | generated | 32-byte base64 key for credentials |
| `OMALLA_BASE_URL` | `http://127.0.0.1:8787` | public URL signed by carriers |
| `OMALLA_TELEPHONY_PROVIDER` | `simulated` | default provider when configured |

Carrier credentials are stored encrypted (`TWILIO_ACCOUNT_SID`,
`TWILIO_AUTH_TOKEN`, `SIGNALWIRE_*`, …) or supplied by the environment.

## Failure behaviour

| Failure | Behaviour |
| --- | --- |
| Carrier signature invalid | 403, no call created, no transcript written |
| Unknown number | polite TwiML hangup, event logged |
| Agent unpublished | polite hangup, no conversation |
| STT/TTS provider down | failover chain if configured; otherwise call ends with a visible error |
| Workflow node fails | retry, then run marked `failed` with the node id and error |
| n8n webhook 5xx | tool returns a retryable error; the agent apologises instead of inventing success |
| Duplicate workflow trigger | `skipped` run, no duplicate side effects |
| Store write fails | request fails loudly; no in-memory-only success |

## Deliberate boundaries

- No SIP stack inside Omalla. A gateway translates SIP to the webhook/media
  contract.
- No n8n code embedded. Integration is HTTP, because n8n's licence is not
  compatible with copying it into an Apache-2.0 product.
- No model-driven authorization. The model proposes; the server decides.
- No claim of PSTN readiness without a live qualification run.
