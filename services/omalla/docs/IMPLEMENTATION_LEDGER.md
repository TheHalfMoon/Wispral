# Implementation ledger

Chronological record of what was built, what was verified, and what failed.
Statuses: **VERIFIED** (command run, output observed), **UNIT-TESTED** (covered
by an automated test), **MANUAL** (exercised by hand, not automated),
**NOT RUN** (implemented but never executed), **BLOCKED** (cannot proceed here).

## 2026-11-20

### 1. Environment and donor audit

| Item | Result |
| --- | --- |
| Node / npm | Node 24.19.0, npm 11.17.0 — VERIFIED |
| Disk | C: ~20 GB free, D: 116.7 GB free — VERIFIED |
| Docker daemon | not running — BLOCKED for Asterisk/FreeSWITCH/LiveKit/Jambonz |
| Local speech | SAPI TTS David/Zira/Mark; STT en-US, zh-TW, fr-FR, zh-CN — VERIFIED |
| Local Arabic | no voice, no recogniser — BLOCKED |
| Donor licences | GitHub API + licence files, 20 repositories — VERIFIED |

No Vapi source, customer data or credentials were obtained. Requests to extract
them were declined and remain declined.

### 2. Twilio protocol verification

| Item | Result |
| --- | --- |
| Signature algorithm | HMAC-SHA1 over URL + sorted form fields — VERIFIED against `twilio-node` source reading and an independent Python implementation |
| Test vector | `https://example.com/myapp`, token `12345`, five form fields → `NGAgWNhdnsLF8j385frvrQoi9sg=` — VERIFIED |
| Media Streams | base64 μ-law, 8 kHz mono, 20 ms; `connected/start/media/mark/stop` — documented, encoded in tests |
| TwiML | `<Say>`, `<Gather>`, `<Dial>`, `<Record>`, `<Connect><Stream>` — UNIT-TESTED |

### 3. Repository skeleton

- npm workspaces, TypeScript strict, Node 24, Apache-2.0.
- Eight packages: core, providers, workflow, telephony, sdk, server, cli, mcp.
- `npm run build` and `npm run typecheck` pass — VERIFIED.

### 4. `@omalla/core`

Types, ids, errors, events, redaction, logging, secrets, JSON store, provider
contracts, sentence chunking, retrieval, conversation engine, policy, audio.

- AES-256-GCM credential envelope with `0600` key file — VERIFIED by unit tests
  in the server suite.
- Redaction of bearer keys, `sk-`, `omk_`, Twilio `SK`, JWT and E.164 — UNIT-TESTED.
- Redaction regex narrowed to E.164 after the first version redacted any long
  digit run (would have hidden order numbers) — FIXED.

### 5. `@omalla/providers`

mock, SAPI, OpenAI-compatible, generic HTTP, failover chain, registry.

- SAPI TTS/STT invoked through `powershell.exe` with timeouts — VERIFIED offline.
- No local Arabic provider — documented gap.

### 6. `@omalla/workflow`

Expressions, nodes, engine, n8n import/export, 11 templates.

Defects found and fixed while testing:

| Defect | Fix |
| --- | --- |
| `{{trigger.title}}` returned undefined because payload lives under `trigger.payload` | shorthand fallback added; both spellings tested |
| `exists(x) == true` was not parsed | comparison form supported |
| A condition step overwrote its branch when storing output | branch preserved when output is attached |
| Live tool returned `{ ended: true }` from the `end` node | last non-`end` output returned |
| Core templates still referenced Trello | all four default templates use local stores; test asserts no `trello.*` |

- 11 templates build a well-formed graph — VERIFIED.
- AI receptionist happy path and no-booking branch — VERIFIED.
- n8n bridge dry run never touches the network — VERIFIED.

### 7. `@omalla/telephony`

- G.711 μ-law, resampling, WAV chunk walking, 20 ms frames, VAD — UNIT-TESTED.
- Twilio/SignalWire adapter: signature, TwiML, media parsing, REST, numbers, SMS
  — UNIT-TESTED with injected fetch; **live carrier NOT RUN**.
- Simulated provider: same event shape, no network — VERIFIED.
- Registry: simulator default; carriers only with credentials; Telnyx/Vonage
  reported unimplemented even with credentials — UNIT-TESTED.
- MediaBridge: VAD → STT → engine → TTS → frames, barge-in clear, DTMF, close
  once, unsupported audio refused — UNIT-TESTED.
- SIP contract: URLs, ws downgrade, token length, four engine descriptors —
  UNIT-TESTED; compose skeletons **NOT RUN**.

### 8. `@omalla/server`

- Config, credentials, automation store, tools, runtime, REST/WS, dashboard.
- Carrier webhooks, media socket, numbers/SMS/providers API — UNIT-TESTED.
- Signed webhook rejection, IVR gather, status idempotency, recording metadata,
  number confirmation, SMS consent, outbound policy — UNIT-TESTED.
- API key authentication switched to constant-time hash comparison — FIXED.

### 9. Live automation

- `n8n_workflow` tool: HMAC-SHA256 body signature, trusted `omalla` block, SSRF
  guard, speech extraction — UNIT-TESTED.
- Native `workflow` tool: active-only, idempotent per call+tool, last meaningful
  output — UNIT-TESTED.
- Draft workflow refused from a live call — UNIT-TESTED.

### 10. SDK, CLI, MCP, dashboard

- SDK: numbers, SMS, telephony providers added; typed errors and retries.
- CLI: `numbers`, `sms`, `telephony`, `sip engines`, `sip contract` added; help
  updated.
- MCP: 15 tools over stdio (calls, workflows, tasks, bookings, knowledge,
  webhooks).
- Dashboard: Telephony view with Numbers, Messages and Providers tabs; search,
  provision with explicit confirmation and cost warning, release, SMS compose
  with consent, provider availability.
- CLI `sip engines` and `sip contract` — MANUAL, output observed.
- Dashboard — MANUAL, syntax checked with `node --check`; not opened in a browser
  during this session.

### 11. Documentation

Created `README.md` and thirteen documents under `docs/`. Every capability is
marked verified, unit-tested, manual or not run. Donor revisions and licences are
recorded from live GitHub metadata.

### 12. Verification

```
npm run verify
  build      ok (8 packages)
  typecheck  ok
  tests      63 pass, 0 fail
  licences   71 production packages, none disallowed
  docs       14 required files, links resolve
```

`npm audit --omit=dev` reports **0 vulnerabilities** after the zod 4.6.7 upgrade.

Command output observed on 2026-11-20. The suite covers audio, Twilio, media
bridge, registry, SIP contract, server telephony and boot, automation tools,
templates, store durability and redaction.

### 13. Defects found during hardening

| Defect | Fix |
| --- | --- |
| Server refused to start: `Fastify is already listening` | `resolveHosts` returned both `127.0.0.1` and `::1` and the entry point called `listen` per host. It now returns one host and the entry point listens once. |
| Flaky test file: one run in nine reported 62 tests, 61 pass, 1 fail at file level | A background store save could reject after its caller returned (teardown removed the temp directory), producing an unhandled rejection. `Database` now captures a failed background save and rethrows it on the next explicit `flush()`/`close()`; it retries instead of discarding dirty data. Test cleanup also closes the runtime and retries `rm` on Windows. Ten consecutive suite runs passed after the change. |
| `zod@3.25.76` carried GHSA-mrhx-c7xc-m3w5 (high: memory exhaustion on oversized constrained collections) | Upgraded to `zod@4.6.7` across the workspace. Migration was mechanical: `z.record(value)` became `z.record(z.string(), value)`. All 63 tests and the smoke run pass; `npm audit --omit=dev` reports 0 vulnerabilities. |
| Number redaction hid order numbers | Narrowed to E.164 only. |
| `check-licenses.mjs` spawned `npm.cmd` via `execFileSync` and got `EINVAL` on Windows | Runs through `cmd.exe /c`; the gate now reads 71 packages. |
| `npm ls` reported workspace licences as UNKNOWN | Added `"license": "Apache-2.0"` to all eight package manifests. |

Regression evidence: `tests/server-boot.test.ts` binds a real port and fetches
health; `tests/core-store.test.ts` forces a failing save and asserts the error
surfaces on `flush()` instead of crashing the process.

### 14. Gates and smoke test

| Item | Result |
| --- | --- |
| Runtime licence gate | `scripts/check-licenses.mjs` reads the production tree, fails on GPL/AGPL/SSPL, reports unknowns — VERIFIED (71 packages, 0 disallowed, 0 unknown) |
| Documentation gate | `scripts/check-docs.mjs` requires 14 documents and resolves README links — VERIFIED |
| End-to-end smoke script | `scripts/smoke-server.mjs` starts the built server, creates a simulated call, sends simulated SMS, reads templates, dashboard assets and the OpenAPI document - VERIFIED, 33 checks |
| Dashboard in a browser | still **NOT RUN**; only HTTP responses and `node --check` |
| Git repository | initialised; `.omalla/`, keys, recordings and `dist/` ignored |

The smoke run confirmed that a missing consent field fails validation (400)
while explicit `consent: false` is refused by policy (403). Both are refusals;
the distinction is recorded so the schema is not later "fixed" into a policy
hole.

### 15. First commits

```
88b3830 chore: scaffold workspaces, build, licence and docs gates
07c9dfa feat: local-first voice AI and automation platform
786611a test: cover audio, telephony, workflows, automation and redaction
1d259b1 docs: record architecture, REA, donors, security and release state
0b68489 fix: listen once and surface failed background saves
43f56c9 test: smoke the built server end to end and record evidence
3ea9dc4 fix: upgrade zod to 4.6.7 for the collection-exhaustion advisory
```

Nothing was pushed, published, deployed or purchased.

## 2026-11-21

### 16. Python SDK

A standard-library-only client at `sdks/python` (`omalla` package), so the SDK
needs no `pip install` and no virtualenv.

| Item | Result |
| --- | --- |
| Client (`omalla/client.py`) | namespaces mirroring the TypeScript SDK; bearer auth, JSON, query encoding, timeouts, `OmallaApiError` carrying `status`, `code` and `body` |
| Retries | GET retries transport errors and 5xx with backoff; mutations are never retried automatically |
| Unit tests | 12 tests against a local `ThreadingHTTPServer` — VERIFIED |
| Live smoke | 20 checks against a real server process via `npm run smoke:python` — VERIFIED |
| Packaging | `pyproject.toml`, Apache-2.0 metadata, README — written, not published |

The live smoke proved the client and server agree on the wire format. Two
defects were found and fixed on the way: a `ResourceWarning` from unclosed
`HTTPError` responses, and number search posting `null` fields that the server
schema rejected. Number search now omits unset fields.

### 17. OpenAPI 3.1

`packages/server/src/openapi.ts` is the hand-written document; `GET
/openapi.json` serves it without an API key, `omalla openapi [--out file]`
prints it locally, and both SDKs expose `openapi()`.

| Item | Result |
| --- | --- |
| Document | 45 paths, bearer security, component schemas, per-tag operations — served |
| Drift test | `tests/openapi.test.ts` collects routes through a Fastify `onRoute` hook: every documented operation must be served, and every `/v1` route must be documented or explicitly listed as provider-facing/non-JSON — VERIFIED |
| Exclusion check | the provider-facing and WebSocket exclusions must themselves exist, so the lists cannot rot |
| `$ref` check | every reference resolves to a declared component |
| Smoke | the built server serves the document unauthenticated; 4 checks added — VERIFIED |

Adding the route hook exposed that Fastify derives `HEAD` from every `GET`;
the drift test ignores derived `HEAD` rather than listing it by hand.

## Known defects and gaps at this point

| Item | State |
| --- | --- |
| Live Twilio/SignalWire call | NOT RUN — no credentials |
| Telnyx / Vonage adapters | not implemented, reported unavailable |
| SIP bridge adapter | contract only; no adapter, no gateway run |
| Arabic STT/TTS | not available locally |
| Campaign execution | data model only |
| Visual workflow editor | not built |
| Docker verification | BLOCKED — daemon not running |
| Browser check of dashboard | not performed |
| Publishing | not performed and not authorised |

## Next ledger entries

1. Docker gateway run with a recorded call and media trace.
2. Live carrier qualification with an owner-authorised spend cap.
3. Arabic model download with licence and size recorded.
4. Browser-based dashboard smoke test with screenshots.
5. Tag `v0.1.0-rc.1` after the documentation commit.
