# Master plan

## Product

Omalla is a local-first, agent-native voice AI and business automation platform.
It answers and places calls, holds a real-time conversation, calls tools mid-call,
and runs workflows after the call. The reference architecture is the one shown in
Ed Hill's Vapi video: **Vapi + Twilio + n8n**. Omalla reproduces that shape with
three differences:

1. **Local first.** The default telephony provider is a simulator, the default
   models are local or mock, and storage is a JSON file on disk.
2. **Native automation.** n8n is optional. The same call can trigger an Omalla
   workflow without installing anything else.
3. **Honest availability.** A provider that has not been tested is reported as
   unavailable rather than silently faked.

Trello appears in the workflow node palette as an optional integration. It is
not a core requirement and no bundled template depends on it.

## Non-goals for v0.1.0

- A hosted multi-region service, billing, or usage metering.
- A softswitch. Omalla terminates webhooks and media streams; it does not route
  SIP itself.
- Speech model training. Omalla wraps local or BYOK models.
- Copying Vapi's backend. It is closed source and was not obtained. See
  [REA_VAPI.md](REA_VAPI.md).
- Free PSTN. Real calls cost money and Omalla says so.

## Zero-cost rules

| Rule | Implementation |
| --- | --- |
| No mandatory paid API | mock + SAPI providers; simulated carrier |
| No mandatory cloud | JSON store, localhost bind by default |
| No mandatory n8n | native workflow engine and `workflow` voice tool |
| No accidental spend | carrier purchases off by default, owner role, `confirm: true` |
| No hidden carrier cost | `carrierCharges` in every search/provision response and in the UI |
| No false claims | provider availability, verification level and test matrix are explicit |

## Phases

| Phase | Scope | State |
| --- | --- | --- |
| 0 | Environment audit, donor research, licence register, architecture correction (Twilio, not Trello) | done |
| 1 | `@omalla/core`: types, ids, errors, events, redaction, logging, secrets, store, provider contracts, conversation engine, policy, audio | done |
| 2 | `@omalla/providers`: mock, SAPI, OpenAI-compatible, HTTP, failover, registry | done |
| 3 | `@omalla/workflow`: expressions, nodes, engine, n8n import/export, templates | done |
| 4 | `@omalla/telephony`: μ-law/resampling/WAV/VAD, provider contract, Twilio/SignalWire, simulator, registry, media bridge | done; live carrier **NOT RUN** |
| 5 | `@omalla/server`: config, credentials, automation store, tools, runtime, REST/WS, dashboard, telephony routes | done |
| 6 | Live automation: `n8n_workflow` and native `workflow` tools, post-call runs, idempotency | done |
| 7 | SDK (TypeScript and Python), CLI, MCP server, OpenAPI 3.1 document | done; unit-tested and smoke-tested |
| 8 | Security model, docs, test matrix, release checklist | done |
| 9 | RC hardening: SIP adapter, Arabic audio, live carrier qualification | not started |

## Release target

`v0.1.0` is a **local development release**. It qualifies when:

- `npm run verify` passes from a clean checkout;
- `npm run smoke` boots the built server and passes its HTTP checks;
- `npm run test:python` and `npm run smoke:python` pass;
- the OpenAPI document and the route table do not drift (`tests/openapi.test.ts`);
- every claim in the README maps to a row in [TEST_MATRIX.md](TEST_MATRIX.md);
- no document implies a live PSTN call was made;
- the security model's known gaps are listed, not hidden.

It does **not** require a live carrier, a published package, or a paid model.

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Carrier APIs drift | Twilio adapter breaks | Contract tests with injected fetch; version-pinned docs; live qualification gate |
| Webhook forgery | Caller impersonation, toll fraud | HMAC verification, public URL reconstruction, replay window, token for SIP |
| Prompt injection through tools/knowledge | Unauthorised actions | Tool authority outside the model, SSRF guard, no model-supplied principals |
| n8n licence restrictions | Cannot embed n8n code | Integrate over HTTP only; never copy n8n source |
| Arabic gap | Product unusable for Arabic calls | Stated as a known limit; model-agnostic adapters ready |
| Windows-only local speech | Portability | SAPI is one provider; HTTP/OpenAI-compatible adapters cover other hosts |
| Cost confusion | User blames Omalla for carrier bill | Explicit `carrierCharges`, UI warning, purchase disabled by default |

## Next increments

1. Finish docs and ledger, run full verification, commit. **Done.**
2. Add a SIP bridge adapter that turns gateway webhooks into `TelephonyProvider`
   events; run one gateway under Docker and record the result.
3. Add Telnyx and Vonage only when they can be tested against a sandbox.
4. Qualify one live Twilio number with an explicit owner authorization and a
   spend cap. Until then the matrix stays `NOT RUN`.
5. Add an Arabic STT/TTS model download path, with size and licence disclosed.
