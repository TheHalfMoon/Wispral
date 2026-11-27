# Security model

Omalla handles phone calls, transcripts, credentials and automation that can
move money or send messages. This document states the assets, the trust
boundaries, the controls that exist, and the gaps that remain.

## Assets

| Asset | Where it lives | Sensitivity |
| --- | --- | --- |
| Carrier credentials | encrypted credential store or allowlisted single-tenant environment | critical |
| API keys | SHA-256 hashed in SQLite (`omalla.db` WAL mode) | critical |
| Transcripts and summaries | SQLite (`omalla.db` WAL mode) | personal data |
| Recordings | data directory (carrier-hosted when carrier recording is used) | personal data |
| Caller numbers | SQLite (`omalla.db`), logs (redacted) | personal data |
| Workflow secrets | encrypted credential store (`AES-256-GCM`) | critical |
| Tool destinations | workflow/agent config | integrity-critical |

## Trust boundaries

```
untrusted: caller audio, SMS text, carrier form fields
untrusted: model output, tool arguments, retrieved documents
untrusted: n8n response body, external HTTP responses
trusted:   server-resolved principal, tenant id, call id, destination allowlist
```

The rule that follows: **the model proposes, the server decides**. No tool
argument can set the tenant, the caller id, the transfer destination, the
idempotency key or an approval.

## Authentication and authorization

| Surface | Control |
| --- | --- |
| REST API | `Authorization: Bearer omk_...`; SHA-256 hash at rest; prefix index; constant-time compare; revocation timestamp |
| Roles | `owner > admin > operator > viewer`; number purchase requires owner; live tool dryRun bypass requires admin; search/send requires operator |
| Tenant scope (`OM-T1`) | Every query, KB attach, tool, task, webhook, and normalized inbound number filters strictly by `principal.tenantId`; cross-tenant ids return 404 |
| Caller ANI (`OM-T2`) | `callerNumberVerified` is `false` unless trunk attestation verified ANI; high-risk tools refuse unverified ANI and untrusted `variables` cannot spoof verification |
| Webhooks (`OM-T3`) | Twilio/SignalWire HMAC-SHA1, Telnyx Ed25519/HMAC, Vonage HS256 JWT (`iat` + `payload_hash`), Standard Webhooks, and Omalla HMAC (`x-omalla-timestamp` ±300s) + durable SQLite replay cache |
| Media & Realtime (`OM-T3`, `OM-T8`) | Short-lived single-use media tokens (`ommt_...` / `omrt_...`), verified STUN `MESSAGE-INTEGRITY`, and sink-confirmed `T2` (`observed_audio_halt` vs `stopped_unconfirmed`) |
| SIP & SRTP (`OM-T7`) | `127.0.0.1` default bind; non-loopback media requires SRTP (`AES_CM_128_HMAC_SHA1_80`), non-loopback SDES/`x-omalla-gateway-token` requires `sips:` TLS or attested tunnel; single-use Digest nonces |
| Rate limits | 600 requests/min per client; 30 auth attempts/min |
| Dashboard | Same API key; stored in `localStorage` on the operator's machine |

Carrier signatures are computed over `OMALLA_BASE_URL`, never over
`X-Forwarded-*`. A proxy that rewrites the URL must be configured to preserve
the public URL, or every webhook fails closed.

## Secrets

- AES-256-GCM envelope, 12-byte random IV, auth tag stored with the ciphertext.
- Master key from `OMALLA_MASTER_KEY` (32 bytes, base64) or a `0600` key file in
  the data directory.
- Credentials are write-only over the API: list returns names and timestamps,
  never values.
- Logs redact bearer tokens, `sk-` keys, `omk_` keys, Twilio `SK` keys, JWTs and
  E.164 numbers.
- Provider errors are surfaced without the auth token; a test asserts the token
  does not appear in the message.

## SSRF (`OM-T4`)

Every workflow HTTP node, n8n webhook, `api_request` tool, MCP URL, and BYOK/local
provider `baseUrl` goes through `evaluateUrl` and connect-time `createSsrfGuardedFetch`:

- only `http`/`https`;
- rejects loopback, RFC1918, link-local/IMDS, CGNAT, NAT64, ULA, and IPv4-mapped IPv6 addresses;
- resolves DNS at connect time, rejects mixed public+private A/AAAA answers, and pins the verified IP;
- strips `Authorization`, `Cookie`, `Proxy-Authorization`, and `x-omalla-signature` on cross-origin redirects and aborts responses exceeding 2 MiB;
- `OMALLA_ALLOW_PRIVATE_HTTP=1` is required for tenant-supplied private URLs.

## Prompt injection and tool authority

- `ToolDefinition.trustedFields` are merged server-side after the model's
  arguments; the model cannot override them.
- Tool execution receives a `ToolContext` with tenant, call and principal from
  the runtime, not from JSON.
- Knowledge retrieval is tenant-scoped; documents are data, never instructions.
- A workflow tool must be `active`; a draft returns a policy error.
- n8n responses are parsed for text only; unexpected fields are ignored.
- Tool output is never executed as code or as a new tool call.

Residual risk: a malicious document can still influence what the model *says*.
It cannot change which tenant is charged, which number is dialled, or whether a
purchase is confirmed.

## Telephony fraud and spend

| Control | Behaviour |
| --- | --- |
| Outbound disabled by default | `tenant.settings.outboundEnabled` must be true |
| Consent required (`OM-T6`) | outbound calls and SMS (REST + workflow `sms.send`) require `consent: true` |
| DNC & allowlist (`OM-T6`) | `dncList` and `outboundAllowlist` enforced on simulated calls, carrier calls, and SMS |
| Daily cap & minute quotas (`OM-T6`) | `dailyOutboundCap`, `maxConcurrentCalls`, `dailyMinuteQuota`, and `monthlyMinuteQuota` enforced |
| Quiet hours (`OM-T6`) | local-time `callingWindow` + `timezone` enforced on calls and SMS |
| Idempotency (`OM-T5`) | Durable SQLite `(tenant_id, scope, idem_key)` + RFC 8785 JCS SHA-256 `args_digest` (floats rejected) |
| Number purchase | `OMALLA_ALLOW_CARRIER_PURCHASES=1`, owner role, `confirm: true` |
| Release | owner role, `confirm: true`, warning that it may be irreversible |
| Cost disclosure | `carrierCharges` and `costNote` in every search/provision response |
| No silent fallback | a misconfigured carrier never falls back to the simulator and claims success |

Toll fraud is still possible if an operator enables outbound with a weak policy
and a stolen API key. The cap and consent are the mitigations; there is no
per-destination allowlist yet.

## Recording and privacy

- Recording is opt-in per agent.
- The agent announces recording before the media stream starts when enabled.
- Voicemail recordings are stored with the call, not in a public directory.
- Transcripts are retained in the JSON store until deleted; there is no automatic
  retention job in v0.1.0.
- Deleting a call removes the record but not carrier-side recordings; the UI
  says so.

## Dependencies and supply chain

- Five runtime dependencies: Fastify, `@fastify/cors`, `@fastify/websocket`,
  zod, and the workspace packages.
- `npm run audit:licenses` reads the installed production tree and fails on
  GPL/AGPL/SSPL. Current result: 71 packages, 0 disallowed, 0 unknown.
- `npm audit --omit=dev` reports 0 vulnerabilities. `zod` is pinned at
  `4.6.7` or newer because `3.x` carried GHSA-mrhx-c7xc-m3w5 (memory exhaustion
  when validating oversized constrained collections).
- No install script from a dependency is executed beyond npm's normal build
  lifecycle, and no native module is required.

## Logging and audit

- Structured JSON logs with redaction.
- Call events (started, turn, tool, barge-in, ended) are emitted on the event bus
  and persisted in the call record.
- Workflow runs record per-node status, attempts and errors.
- There is no tamper-evident audit log. A local operator with disk access can
  edit the JSON store. This is acceptable for a single-machine developer build
  and unacceptable for regulated use; it is listed as a gap.

## Known gaps

| Gap | Impact | Planned mitigation |
| --- | --- | --- |
| No HTTP TLS termination built in | API keys and WS audio in clear text if exposed | Run behind a TLS proxy; HTTP binds loopback `127.0.0.1` by default (`sips:` TLS is supported on `SipStack`) |
| SQLite store unencrypted at table level | Transcripts readable on disk (`credentials` column uses AES-256-GCM) | OS disk encryption; field-level transcript encryption later |
| No automatic retention | Personal data accumulates | Retention policy and delete job |
| No tamper-evident audit | Local DB edits undetectable | Append-only log with hash chain |
| Rate limit is per process | Multi-process deployment bypasses it | Shared limiter |
| Live PSTN carrier edge cases | Proxy/NAT differences in production | Live carrier qualification run |
| SIP gateway token rotation | Shared secret without automated rotation | Per-gateway key rotation |

## Reporting

This is a local build with no hosted service and no security contact yet. Before
any public release, add `SECURITY.md` with a private reporting channel and a
response window. Do not publish carrier credentials, call recordings or customer
transcripts in an issue.
