# REA: Telephony

Public documentation and protocol analysis for the carriers and gateways Omalla
targets. Every claim below is either quoted from public docs or verified by a
local test; live carrier behaviour is marked **NOT RUN**.

## Twilio Programmable Voice

### Webhooks and TwiML

- Twilio POSTs form-encoded parameters to the number's Voice URL and expects
  TwiML (XML) back.
- `<Say>`, `<Gather>`, `<Dial>`, `<Record>`, `<Hangup>` cover the IVR and transfer
  surface Omalla needs.
- `<Connect><Stream url="wss://…">` starts bidirectional Media Streams. Custom
  `<Parameter name value>` elements arrive in the stream `start` message, which
  is how Omalla carries `callId` and tenant context without trusting the caller.

### Media Streams

| Property | Value |
| --- | --- |
| Encoding | `audio/x-mulaw` |
| Sample rate | 8000 Hz |
| Channels | 1 |
| Frame | 20 ms (160 bytes) before base64 |
| Transport | WebSocket, JSON text messages |
| Inbound messages | `connected`, `start`, `media`, `mark`, `stop` |
| Outbound messages | `media` (base64 payload), `mark`, `clear` |

Omalla's parser tolerates unknown message types by returning `unknown` rather
than throwing, and its encoder emits the documented `{ event, streamSid, media }`
shape. Barge-in sends `clear` and then new audio.

### Signatures

`X-Twilio-Signature` is HMAC-SHA1 over:

1. the exact URL Twilio requested, including scheme, host, path and query;
2. every POST parameter, sorted by key, appended as `key + value`;
3. the account auth token as the HMAC key;
4. base64 of the digest.

Omalla reconstructs the URL from `OMALLA_BASE_URL`, not from proxy headers,
because a signature over the wrong URL fails closed. Comparison is constant
time. The standard HTTPS port is tolerated both with and without `:443` because
proxies disagree.

Verified against a known vector: URL `https://example.com/myapp`, token
`12345`, form fields `CallSid=CA1234567890ABCDE`, `Caller=+12349013030`,
`Digits=1234`, `From=+12349013030`, `To=+18005551212` →
`NGAgWNhdnsLF8j385frvrQoi9sg=`. The same vector was reproduced independently in
Python before being encoded as a test.

### REST control plane

- `POST /2010-04-01/Accounts/{sid}/Calls.json` for outbound calls.
- `POST …/Calls/{sid}.json` with `Url` or `Status=completed` for redirect/hangup.
- `GET/POST …/IncomingPhoneNumbers.json` for search, provision and release.
- `POST …/Messages.json` for SMS.
- Basic auth with account SID and auth token; credentials never appear in a URL
  or a log line.

## SIP

Twilio SIP trunking terminates SIP and exposes the same webhook model. Omalla
does not implement a SIP stack. `packages/telephony/src/sip.ts` defines what a
self-hosted gateway must send: form-encoded call events, a shared
`x-omalla-gateway-token`, and 20 ms base64 μ-law frames on a WebSocket. The
`deploy/sip/` compose files are skeletons; **no gateway has been run**.

## Other carriers

| Provider | Public interface | Omalla state |
| --- | --- | --- |
| SignalWire | Twilio-compatible LaML, own REST base per space | adapter reuses `TwilioProvider` with `variant: "signalwire"`; **not run** |
| Telnyx | Call Control API, webhooks, media streaming over WebSocket | adapter not implemented; reported unavailable |
| Vonage | Voice API with NCCO JSON, WebSocket audio | adapter not implemented; reported unavailable |
| Jambonz | Webhook-driven applications, own SIP stack | SIP contract only; **not run** |
| Asterisk | GPL-2.0-or-later, dialplan/ARI | compose skeleton; **not run** |
| FreeSWITCH | MPL-1.1, dialplan/Event Socket | compose skeleton; **not run** |
| LiveKit SIP | Apache-2.0, SIP terminated into WebRTC rooms | compose skeleton; needs a room adapter that does not exist |

The adapter contract is capability-gated: a provider that says `sms: false` also
omits `sendSms`, and callers must check first. Missing capabilities raise
`TelephonyCapabilityError` instead of returning fake success.

## Number provisioning and cost

Carrier numbers cost money: monthly rental, inbound minutes, outbound minutes,
SMS. Omalla's search response includes `carrierCharges` and a `costNote` that
never invents a price. Provisioning requires:

1. the server started with `OMALLA_ALLOW_CARRIER_PURCHASES=1`;
2. an owner-role API key;
3. `confirm: true` in the request;
4. a carrier provider with credentials.

Releases require the same confirmation because they may be irreversible.

## Recording and consent

Twilio records only when asked. Omalla's `InboundResponseOptions.startRecording`
is populated only when the agent has recording enabled, and the IVR/agent
announces recording first. Consent law varies by jurisdiction; Omalla implements
the mechanism and documents the duty rather than claiming compliance.

## Failure modes handled

- Signature mismatch → 403, no call record.
- Unknown `To` number → polite hangup.
- Unpublished agent → polite hangup.
- Media socket opened without a valid call → close with a policy code.
- Duplicate status callbacks → idempotent status update.
- Carrier 4xx/5xx → surfaced as `OmallaError("provider_error")` with the
  token redacted.

## What remains unverified

Everything that requires a real carrier: signature delivery by Twilio's edge,
media jitter and packet loss, DTMF timing, transfer completion, recording
availability, SMS delivery receipts, number purchase and release. These are
`NOT RUN`, not "passing".
