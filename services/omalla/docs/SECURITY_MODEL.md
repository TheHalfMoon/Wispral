# Security model

Omalla handles phone calls, transcripts, credentials and automation that can
move money or send messages. This document states the assets, the trust
boundaries, the controls that exist, and the gaps that remain.

## Assets

| Asset | Where it lives | Sensitivity |
| --- | --- | --- |
| Carrier credentials | encrypted credential store or environment | critical |
| API keys | hashed in the JSON store | critical |
| Transcripts and summaries | JSON store | personal data |
| Recordings | data directory (carrier-hosted when carrier recording is used) | personal data |
| Caller numbers | JSON store, logs (redacted) | personal data |
| Workflow secrets | encrypted credential store | critical |
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
| Roles | `owner > admin > operator > viewer`; number purchase requires owner; search/send requires operator |
| Tenant scope | Every query filters by `principal.tenantId`; cross-tenant ids return 404, not 403 |
| Carrier webhooks | Twilio HMAC-SHA1 over exact URL + sorted form; constant-time compare; no signature means reject |
| Media WebSocket | HMAC-SHA256 token bound to `callId`, verified before audio is accepted |
| SIP gateway (future) | `x-omalla-gateway-token`, minimum 16 chars, compared as a secret |
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

## SSRF

Every workflow HTTP node, n8n webhook, `api_request` tool and MCP URL goes
through `evaluateUrl`:

- only `http`/`https`;
- rejects loopback, private, link-local, multicast and unique-local addresses;
- rejects credentials in the URL;
- `OMALLA_ALLOW_PRIVATE_HTTP=1` is required to reach a local n8n or Ollama;
- redirects are not followed by default.

DNS rebinding is not fully solved: the check resolves the hostname, then fetch
resolves again. A production deployment should pin the resolved address or use
an egress proxy. This is a known gap, listed below.

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
| Consent required | outbound call and SMS require `consent: true` |
| Daily cap | `dailyOutboundCap`, enforced before dialling |
| Quiet hours | local-time window, enforced |
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
| No TLS termination | API keys and audio in clear text if exposed | Run behind a TLS proxy; bind loopback by default |
| DNS rebinding after SSRF check | Reach internal services | Pin resolved IP or egress proxy |
| JSON store unencrypted | Transcripts readable on disk | OS disk encryption; field-level encryption later |
| No automatic retention | Personal data accumulates | Retention policy and delete job |
| No tamper-evident audit | Local edits undetectable | Append-only log with hash chain |
| Rate limit is per process | Multi-process deployment bypasses it | Shared limiter |
| No destination allowlist | Outbound toll fraud via stolen key | Per-tenant allowlist |
| Carrier live behaviour unverified | Signature/proxy edge cases | Live qualification run |
| SIP token comparison | Shared secret, no rotation | Rotation and per-gateway keys |

## Reporting

This is a local build with no hosted service and no security contact yet. Before
any public release, add `SECURITY.md` with a private reporting channel and a
response window. Do not publish carrier credentials, call recordings or customer
transcripts in an issue.
