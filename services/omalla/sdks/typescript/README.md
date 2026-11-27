# Omalla TypeScript SDK

Official TypeScript client for **Omalla** (part of **Wispral** by **Halfmoon**).

## Features

- Zero runtime dependencies beyond platform `fetch` and `WebSocket`.
- RFC 8785 JCS canonicalization (`jcsSha256`) with strict float rejection and `Idempotency-Key` support.
- Raw-byte Standard Webhooks & Omalla HMAC signature verification (`verifyWebhookSignature`).
- Async-iterable live call streaming (`client.iterateCallEvents(callId)`).
- Immutable agent & workflow version inspection, dry-run evaluation, and 1-call rollback (`agents.rollback`, `workflows.rollback`).

Licensed under Apache-2.0.
