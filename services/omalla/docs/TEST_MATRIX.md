# Test matrix

Evidence per capability. Run everything with `npm run verify`; run one file with
`node --test --test-reporter=spec tests/<file>.test.ts`.

Status vocabulary:

- **VERIFIED** - command run, output observed.
- **UNIT-TESTED** - automated test with injected transport; no live service.
- **MANUAL** - exercised by hand, not automated.
- **NOT RUN** - implemented, never executed.
- **BLOCKED** - cannot execute in this environment.

## Audio and media

| Capability | Test | Status |
| --- | --- | --- |
| μ-law silence encodes to `0xFF`, decodes to zero | `telephony-audio` | UNIT-TESTED |
| μ-law speech round-trip within telephone tolerance | `telephony-audio` | UNIT-TESTED |
| 16 kHz → 8 kHz resampling preserves energy | `telephony-audio` | UNIT-TESTED |
| WAV decode walks extra chunks, not a fixed 44-byte header | `telephony-audio` | UNIT-TESTED |
| WAV becomes 20 ms μ-law frames | `telephony-audio` | UNIT-TESTED |
| Last frame padded with μ-law silence | `telephony-audio` | UNIT-TESTED |
| VAD needs speech then silence | `telephony-audio` | UNIT-TESTED |
| Silent line never finalizes an utterance | `telephony-audio` | UNIT-TESTED |

## Media bridge

| Capability | Test | Status |
| --- | --- | --- |
| Utterance → STT → conversation engine | `telephony-media-bridge` | UNIT-TESTED |
| TTS WAV → 20 ms frames + mark | `telephony-media-bridge` | UNIT-TESTED |
| Barge-in clears carrier queue | `telephony-media-bridge` | UNIT-TESTED |
| Socket close ends the call once | `telephony-media-bridge` | UNIT-TESTED |
| DTMF reaches the controller | `telephony-media-bridge` | UNIT-TESTED |
| Unsupported audio refused | `telephony-media-bridge` | UNIT-TESTED |

## Twilio and SignalWire

| Capability | Test | Status |
| --- | --- | --- |
| Signature matches documented HMAC-SHA1 vector | `telephony-twilio` | UNIT-TESTED |
| Tampered param, missing header, wrong URL rejected | `telephony-twilio` | UNIT-TESTED |
| Port present/absent tolerated | `telephony-twilio` | UNIT-TESTED |
| Inbound/status webhooks → canonical events | `telephony-twilio` | UNIT-TESTED |
| TwiML media stream with escaped parameters | `telephony-twilio` | UNIT-TESTED |
| TwiML gather for DTMF | `telephony-twilio` | UNIT-TESTED |
| Media messages round-trip | `telephony-twilio` | UNIT-TESTED |
| Outbound REST call, credentials not in URL | `telephony-twilio` | UNIT-TESTED |
| Hangup redirect + SMS Messages endpoint | `telephony-twilio` | UNIT-TESTED |
| Number search/provision/release mapping | `telephony-twilio` | UNIT-TESTED |
| Carrier error does not leak auth token | `telephony-twilio` | UNIT-TESTED |
| Live carrier call | none | **NOT RUN** |
| Live number purchase/release | none | **NOT RUN** |
| Live SMS delivery | none | **NOT RUN** |

## Provider registry

| Capability | Test | Status |
| --- | --- | --- |
| Simulator always available, default | `telephony-registry` | UNIT-TESTED |
| Carriers appear only with credentials | `telephony-registry` | UNIT-TESTED |
| Unknown requested provider falls back to simulator | `telephony-registry` | UNIT-TESTED |
| SignalWire via Twilio-compatible credentials | `telephony-registry` | UNIT-TESTED |
| Telnyx Ed25519/HMAC + Vonage HS256 JWT (`iat` + `payload_hash`) + `SipTelephonyProvider` | `telephony-registry`, `sip-srtp-loopback` | UNIT-TESTED |
| Missing SIP gateway never pretends to be a carrier | `telephony-registry` | UNIT-TESTED |

## SIP, SRTP, and Realtime Duplex (`OM-T7`, `OM-T8`)

| Capability | Test | Status |
| --- | --- | --- |
| Webhook and wss URLs derived from public base | `telephony-sip` | UNIT-TESTED |
| http base downgrades ws and is called out | `telephony-sip` | UNIT-TESTED |
| Weak token and relative URL rejected | `telephony-sip` | UNIT-TESTED |
| Four external B2BUA engines described (`not-run` without daemon) | `telephony-sip` | UNIT-TESTED |
| RFC 3261 `SipStack` (`REGISTER`, `INVITE`, `ACK`, `REFER`, `CANCEL`, `BYE`) over loopback UDP & `sips:` TLS | `sip-srtp-loopback` | VERIFIED |
| RFC 3711 SRTP `AES_CM_128_HMAC_SHA1_80` (including `P=1` padded RTP) + 64-pkt anti-replay + RFC 4733 DTMF `E=1` dedup | `sip-srtp-loopback` | VERIFIED |
| `OM-T7` non-loopback cleartext SDES / gateway-token / plain-RTP / empty-INVITE rejection | `sip-srtp-loopback` | UNIT-TESTED |
| Bounded jitter buffer (PLC + max-depth) & 20 ms outbound pacer (`turnEpoch` + watermarks) | `realtime-duplex` | UNIT-TESTED |
| `OM-T8` sink-confirmed `T2` (`observed_audio_halt` on `clear.ack` vs `stopped_unconfirmed`) | `realtime-duplex` | VERIFIED |
| Live `/v1/realtime/ws` single-use media token + `/v1/realtime/webrtc/offer` ICE-lite STUN (`MESSAGE-INTEGRITY`) + SRTP | `realtime-duplex` | VERIFIED |
| Studio Quiet Signal (`#7E22CE` / `#D8B4FE`), RTL/LTR `dir="auto"`, AudioWorklet, 1-click rollback | `studio-console` | VERIFIED |
| External carrier PSTN / Docker B2BUA live call | none | **NOT RUN** |

## Server lifecycle

| Capability | Test | Status |
| --- | --- | --- |
| One loopback listener; health answers over real HTTP | `server-boot` | VERIFIED |
| `resolveHosts` returns one host, not two | `server-boot` | UNIT-TESTED |
| Boot regression (`Fastify is already listening`) | fixed; regression test added | VERIFIED |

## Server telephony

| Capability | Test | Status |
| --- | --- | --- |
| Health reports carrier + honest default | `server-telephony` | UNIT-TESTED |
| Unsigned/wrongly signed webhook rejected | `server-telephony` | UNIT-TESTED |
| Signed inbound call → TwiML + durable record | `server-telephony` | UNIT-TESTED |
| Unconfigured destination refused | `server-telephony` | UNIT-TESTED |
| IVR gathers and routes to agent | `server-telephony` | UNIT-TESTED |
| Status callback ends call once | `server-telephony` | UNIT-TESTED |
| Recording callback stores metadata only | `server-telephony` | UNIT-TESTED |
| Free search; provisioning needs confirmation | `server-telephony` | UNIT-TESTED |
| Simulated SMS requires consent and is labelled | `server-telephony` | UNIT-TESTED |
| Inbound SMS stored per tenant | `server-telephony` | UNIT-TESTED |
| Carrier outbound passes policy | `server-telephony` | UNIT-TESTED |
| Simulator has no public webhook surface | `server-telephony` | UNIT-TESTED |

## Automation

| Capability | Test | Status |
| --- | --- | --- |
| n8n tool signs payload, returns speech | `server-automation-tools` | UNIT-TESTED |
| n8n HTTP failure is retryable | `server-automation-tools` | UNIT-TESTED |
| Native workflow runs live, idempotent | `server-automation-tools` | UNIT-TESTED |
| Draft workflow refused | `server-automation-tools` | UNIT-TESTED |
| Every template builds a valid graph | `workflow-templates` | VERIFIED |
| Core templates do not require Trello | `workflow-templates` | VERIFIED |
| Receptionist books, saves contact, texts | `workflow-templates` | VERIFIED |
| No-booking branch creates task + escalation | `workflow-templates` | VERIFIED |
| n8n bridge dry run has no network | `workflow-templates` | VERIFIED |
| Trigger expression shorthand | `workflow-templates` | VERIFIED |
| Real n8n instance | none | **NOT RUN** |
| Google/Slack/WhatsApp live nodes | none | **NOT RUN** |

## Core

| Capability | Test | Status |
| --- | --- | --- |
| E.164 and credentials redacted | `core-redact` | UNIT-TESTED |
| Short business ids not redacted | `core-redact` | UNIT-TESTED |
| Secret object keys dropped | `core-redact` | UNIT-TESTED |
| AES-256-GCM credential round-trip | covered in server tests | UNIT-TESTED |
| Constant-time API key compare | code review; auth tests exercise lookup | UNIT-TESTED |
| Failed background save surfaces on `flush`, not as an unhandled rejection | `core-store` | UNIT-TESTED |
| Durable write survives close and reload | `core-store` | UNIT-TESTED |

## OpenAPI and SDK parity

| Capability | Test | Status |
| --- | --- | --- |
| Document is OpenAPI 3.1 with responses and tags per operation | `openapi` | UNIT-TESTED |
| Every documented operation is served by Fastify | `openapi` | UNIT-TESTED |
| Every `/v1` route is documented or explicitly excluded | `openapi` | UNIT-TESTED |
| Every excluded route exists (lists cannot rot) | `openapi` | UNIT-TESTED |
| Every component `$ref` resolves | `openapi` | UNIT-TESTED |
| Served document equals the module's document | `openapi` | VERIFIED |
| `GET /openapi.json` answers without a key | `smoke` | VERIFIED |
| `omalla openapi --out` writes 45 paths | CLI run | MANUAL |
| Python SDK unit tests (fake server) | `npm run test:python` | VERIFIED |
| Python SDK against a real server | `npm run smoke:python` | VERIFIED |
| OpenAPI validator (external tool) | none | **NOT RUN** |

## Manual and environment checks

| Check | Result | Status |
| --- | --- | --- |
| `npm run build` | 9 workspace packages + TS SDK, ok | VERIFIED |
| `npm run typecheck` | no errors | VERIFIED |
| `npm test` | 85+ tests across 14 suites (SQLite WAL, `OM-T1..OM-T8`, SIP/SRTP, Realtime, Studio), 0 fail | VERIFIED |
| `npm run audit:licenses` | 73 packages, 0 disallowed, 0 unknown | VERIFIED |
| `npm audit --omit=dev` | 0 vulnerabilities after zod 4.6.7 | VERIFIED |
| `npm run check:docs` | 14 required files, links resolve | VERIFIED |
| `npm run openapi:check` | 58 OpenAPI 3.1 paths verified in sync with Fastify routes | VERIFIED |
| `npm run smoke` | end-to-end checks against a real server process | VERIFIED |
| `pytest sdks/python` | 17 tests, OK | VERIFIED |
| `cargo test` (`sdks/rust`) | 5 pure-Rust SDK tests, OK | VERIFIED |
| `omalla sip engines` | table printed | MANUAL |
| `omalla sip contract` | contract printed, `not run` warning | MANUAL |
| Dashboard `node --check` | syntax ok | VERIFIED |
| Dashboard in a browser | not opened | **NOT RUN** |
| SAPI TTS/STT offline | voices enumerated and invoked | VERIFIED |
| Arabic local speech | no voice/recogniser | **BLOCKED** |
| Docker gateways | daemon not running | **BLOCKED** |
| Live PSTN | no credentials | **NOT RUN** |

## End-to-end smoke run

`npm run smoke` starts `packages/server/dist/bin/serve.js` on a random loopback
port with a throwaway data directory, a fixed master key and mock voice
providers. It then asserts over real HTTP:

| Group | Checks |
| --- | --- |
| Health and auth | health ok; simulated default; `omk_` key issued; unauthenticated request 401 |
| Telephony | provider list is an array; simulator available; every carrier unavailable; simulator says "no PSTN"; seeded number present; free search returns 8 offers with `carrierCharges: false` |
| Simulated call | 201 created; `simulation: true`; agent attached; 3 transcript turns; assistant text; `metrics.turnCount >= 1` |
| SMS | 201 with consent; `simulated: true`; `consent: false` → 403; missing field → 400 |
| Automation | workflow list; 11 templates; run history |
| Dashboard | HTML served as `text/html`; Telephony nav present; `app.js` served with `renderTelephony` |
| OpenAPI | document served without a key; 3.1.0; `/v1/calls` present; 45 paths; bearer scheme |

What it does **not** prove: speech quality, carrier delivery, browser rendering
or concurrency. It proves the process boots, the routes answer and the seeded
data is coherent.

## Coverage limits

- Tests inject `fetch`; no test opens a real socket to a carrier.
- No load test, no concurrency test beyond a few parallel calls.
- No browser automation; the dashboard is checked by syntax and API contract.
- No fuzzing of the webhook parsers; malformed input is handled but not
  exhaustively explored.
- The Python SDK is tested against the local server only; no PyPI publish and
  no matrix of Python versions (3.14 exercised).
- The OpenAPI document is structurally checked and route-drift checked, but not
  validated by a third-party OpenAPI validator.
- No security scan; the security model lists gaps rather than claiming a clean
  audit.
