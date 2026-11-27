# Donor transplant map

What Omalla took from each donor, and in what mode. **Nothing in this table is a
code copy.** Modes:

- **SPEC** - the donor's public protocol or documentation defined a wire format.
- **REFERENCE** - the donor's design informed Omalla's own implementation.
- **EXTERNAL** - the donor runs as a separate process or service over HTTP.
- **REJECTED** - considered and deliberately not used.

| Omalla mechanism | Donor | Mode | Omalla location | Evidence / notes |
| --- | --- | --- | --- | --- |
| Twilio webhook signature | Twilio docs + `twilio-node` | SPEC | `packages/telephony/src/providers/twilio.ts` | HMAC-SHA1, sorted form fields, constant-time compare; vector `NGAgWNhdnsLF8j385frvrQoi9sg=` |
| Media Streams framing | Twilio Media Streams docs | SPEC | `packages/telephony/src/audio.ts`, `providers/twilio.ts` | base64 μ-law, 8 kHz mono, 20 ms; `connected/start/media/mark/stop` |
| TwiML responses | Twilio docs | SPEC | `providers/twilio.ts` | `<Say>`, `<Gather>`, `<Dial>`, `<Record>`, `<Connect><Stream>` |
| Carrier-neutral provider contract | Vocode, TEN, Jambonz | REFERENCE | `packages/telephony/src/provider.ts` | Capability-gated optional methods; no fake success |
| Media bridge and barge-in | Pipecat, LiveKit | REFERENCE | `packages/telephony/src/media-bridge.ts` | VAD, playback queue, clear-on-interrupt |
| Turn-taking and sentence chunking | Pipecat | REFERENCE | `packages/core/src/conversation.ts`, `sentence.ts` | Own implementation; no frames copied |
| Simulated carrier | Dograh (self-host shape) | REFERENCE | `packages/telephony/src/providers/simulator.ts` | Same event shape as a carrier, no network |
| IVR menus | Asterisk, Jambonz | REFERENCE | `packages/telephony/src/ivr.ts`, `server/telephony-routes.ts` | Digit gather, retry, transfer, voicemail |
| Workflow graph and expressions | n8n, Activepieces, Node-RED | REFERENCE | `packages/workflow/src/{engine,expressions,nodes}.ts` | Deterministic graph; no JS evaluation |
| n8n import/export | n8n public node schema | SPEC | `packages/workflow/src/n8n.ts` | Known nodes mapped; `Code` rejected |
| n8n live tool | n8n webhook docs + reference video | SPEC | `packages/server/src/tools.ts` | Signed POST, JSON response → speech |
| Local automation store | none | ORIGINAL | `packages/server/src/automation-store.ts` | Tasks, bookings, contacts, escalations |
| JSON document store | none | ORIGINAL | `packages/core/src/store.ts` | Atomic writes, debounced flush |
| Speech adapters | Whisper, Silero, Kokoro, Moshi | EXTERNAL | `packages/providers/src/*` | Interfaces only; no weights or code bundled |
| SAPI speech | Windows | EXTERNAL | `packages/providers/src/sapi.ts` | `powershell.exe`, timeouts, no network |
| SIP gateway contract | Asterisk, FreeSWITCH, LiveKit, Jambonz | SPEC | `packages/telephony/src/sip.ts` | URLs, token header, media format; **not run** |
| Dashboard | none | ORIGINAL | `apps/dashboard/public/*` | Vanilla ES modules, no framework |
| MCP surface | Model Context Protocol | SPEC | `packages/mcp/src/server.ts` | Tools over stdio |

## Rejected transplants

| Candidate | Why rejected |
| --- | --- |
| Vapi backend | Closed source; no authorised access. Requests for source/secrets declined. |
| n8n `Code` node | Arbitrary code execution inside a tenant workflow, plus licence boundary |
| n8n engine embedding | Sustainable Use License incompatible with Apache-2.0 distribution |
| Piper GPL binary | GPL-3.0 linking obligations; optional external process at most |
| Windmill / Twenty embedding | AGPL-3.0 and commercial carve-outs |
| Asterisk/FreeSWITCH libraries | GPL/MPL engines must stay separate processes |
| Python pipeline transplant | Would add a second runtime for no capability gain; contracts reimplemented in TypeScript |
| Trello as core | The reference architecture is Vapi + Twilio + n8n; Trello is an optional node |

## Provenance rules used

1. A donor is recorded with repository, SPDX licence and the revision examined.
2. If the licence is copyleft or source-available, the donor is external or
   reference only.
3. Protocols (Twilio signatures, Media Streams, n8n webhooks) are implemented
   from documentation, not copied from SDK source.
4. Any future copy requires a new row, a licence check and a NOTICE update.
5. Marketing claims are not evidence. A mechanism is "done" only with a test or
   a recorded manual run.

## What this buys

- A defensible licence position for an Apache-2.0 release.
- A small dependency surface: eight packages, five runtime dependencies.
- The ability to swap n8n, Twilio or a speech model without rewriting the call
  path.
- No hidden obligation to publish Omalla's source because a GPL binary was
  linked into it.
