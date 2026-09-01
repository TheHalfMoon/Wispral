# Specification 000A — Qualification Inputs

**Status:** execution input record  
**Recorded:** 2026-09-01  
**Wispral canonical base:** `25acbcc29bab262223315a55826e77396cc35822`

This record pins the external authority used by the first ACP qualification attempt. It is not behavioral evidence for Wispral support.

## Pinned ACP authority

| Surface | Revision / version | Role |
| --- | --- | --- |
| `agentclientprotocol/agent-client-protocol` | `01b9d6e9c094d31cdea6d88768a9dd31b089ccef` | protocol specification and generated v1/v2 schemas |
| `agentclientprotocol/rust-sdk` | `754d5aa1ce2cfa54ba2c2a6d3edc7e7b6bce28eb` | official Rust SDK implementation reference |
| `agentclientprotocol/registry` | `c7f1825666fb0008172e5fb93a58071a9618041e` | agent distribution manifests and protocol matrix |
| registry CDN schema | `1.0.0` at observation time | distribution index format; mutable `latest` endpoint is not itself a reproducible revision |

The Git revision of `agentclientprotocol/registry`, rather than the mutable CDN response, is the canonical registry pin for this attempt.

## Representative distributions

### Gemini CLI — native ACP

- Registry id: `gemini`
- Registry version: `0.57.0`
- Distribution: `npx -y @google/gemini-cli@0.57.0 --acp`
- Upstream tag: `v0.57.0`
- Upstream tag commit: `6b0ae9a6c37aa117cc8b070d8b41c5bb4fa6d253`
- ACP SDK dependency at the pinned package source: `@agentclientprotocol/sdk` `0.16.1`
- License recorded upstream: Apache-2.0

### Codex ACP — adapter-mediated ACP

- Registry id: `codex-acp`
- Registry version: `1.7.0`
- Distribution: `npx -y @agentclientprotocol/codex-acp@1.7.0`
- Upstream tag: `v1.7.0`
- Upstream tag commit: `2b48e9822330fc09f3a94a81563e5c4bb779601a`
- ACP SDK dependency at the pinned package source: `@agentclientprotocol/sdk` `^1.4.0`
- Bundled Codex dependency at the pinned package source: `@openai/codex` `^0.148.0`
- License recorded upstream: Apache-2.0

## Protocol-version finding

The current ACP repository contains both v1 and v2 protocol surfaces. The representative registry distributions are not evidence that all registry agents have moved to the newest schema shape.

The pinned Gemini implementation exposes the v1-style API surface, including `clientCapabilities`, `agentInfo`, `agentCapabilities`, `authenticate`, `session/new`, `session/load`, `session/prompt`, and `session/cancel`. The current registry protocol matrix also intentionally probes `PROTOCOL_VERSION = 1`.

Therefore Specification 000A treats protocol-version negotiation and compatibility as a first-order product requirement. Wispral must not hard-code an assumption that "current registry agent" means "current ACP v2 wire shape".

## Independent registry reference

At registry revision `c7f1825666fb0008172e5fb93a58071a9618041e`, `.protocol-matrix/latest.md` was generated on 2026-09-01 and reports:

- 32 registered agents probed;
- 31 successful unauthenticated `initialize` probes;
- 18 `session/new` probes returning `auth_required`;
- Gemini CLI `0.57.0`: `initialize` `ok`, authentication type `agent`, `loadSession` advertised;
- Codex ACP `1.7.0`: `initialize` `ok`, authentication type `agent`, `loadSession`, `session/list`, and `session/resume` advertised/probed by that matrix.

This is independent upstream evidence and is used only as a comparison reference. Wispral still runs its own pinned probe and will not convert upstream results into `OBSERVED` Wispral evidence.

## Wispral probe method

The first Wispral attempt is intentionally unauthenticated and runs on a GitHub-hosted Linux runner with no repository secrets supplied.

It:

1. launches the exact pinned distribution;
2. requests ACP protocol version 1;
3. records the `initialize` response;
4. attempts a synthetic `session/new` against `fixtures/acp-probe`;
5. probes `session/list` to distinguish an exposed method from an inferred capability;
6. records cancellation/permission semantics as `NOT_TESTED` unless a real safe session exists;
7. removes known API-key/token environment variables and sets `NO_BROWSER=1`;
8. preserves a sanitized JSON trace and package-integrity metadata as a workflow artifact.

No login, provider credential, destructive action, production repository, or permission bypass is used.

## Evidence-state rule

The following states remain distinct in the final matrix:

- `OBSERVED`
- `DOCUMENTED_NOT_OBSERVED`
- `UNSUPPORTED`
- `NOT_TESTED`
- `BLOCKED_EXTERNAL`
- `UNKNOWN`

A source-code implementation or upstream matrix may support `DOCUMENTED_NOT_OBSERVED`; only the Wispral probe may establish `OBSERVED` for this attempt.
