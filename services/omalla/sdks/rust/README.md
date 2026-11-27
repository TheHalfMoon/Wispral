# Omalla Rust SDK (`omalla-sdk`)

Pure-Rust, zero-external-dependency client and security primitives for **Omalla** (part of **Wispral** by **Halfmoon**).

## Capabilities

- `#![forbid(unsafe_code)]`, Rust 2021 edition, zero third-party crates.
- RFC 8785 JSON Canonicalization Scheme (`canonicalize_jcs`, `args_digest`, `args_digest_json`) with UTF-16 code-unit key ordering and strict floating-point rejection (`OM-T5`).
- Constant-time raw-byte Standard Webhooks (`±300 s` skew) and Omalla HMAC signature verification (`verify_webhook_signature`, `OM-T3`).
- Strongly-typed `OmallaClientBuilder`, `OutboundCallRequest`, `SmsRequest`, `RollbackRequest`, and pluggable `HttpTransport`.

Licensed under Apache-2.0.
