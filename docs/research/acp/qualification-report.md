# Specification 000A — ACP Qualification Report

**Attempt:** `WISPRAL-000A-ATTEMPT-001`  
**Date:** 2026-09-01  
**Canonical base:** `25acbcc29bab262223315a55826e77396cc35822`  
**Evidence head initially executed:** `4880c9d2d1d5091bdb4f4ee6acc998826a3bdde4`  
**GitHub PR test merge executed:** `378e1192837ec02733419fb077e8101d37cd292c`  
**Workflow:** `000A ACP Qualification` run `33501999725` — `completed/success`  
**Recommendation:** `PARTIAL`  
**Confidence:** `MODERATE`

## Executive finding

ACP is a credible and currently executable structured control surface for Wispral, but Attempt 001 does not justify calling it fully qualified as the primary product path yet.

Two deliberately different representative distributions — native ACP through Gemini CLI and adapter-mediated ACP through Codex ACP — both completed a real protocol-version-1 `initialize` handshake in a clean GitHub-hosted environment without provider credentials. Both returned structured identity, authentication, and capability metadata.

That establishes more than documentation-only feasibility.

However, both representatives required provider authentication before `session/new`. Because this attempt intentionally supplied no credentials, no session/prompt, streaming update, active cancellation, steering behavior, or structured permission request could be observed. Those central Wispral semantics therefore remain unqualified rather than inferred.

`PARTIAL` is the strongest evidence-supported classification.

## Exact attempt method

The attempt used:

- the research-only Python standard-library probe in `research/000a/acp_probe.py`;
- synthetic fixture `fixtures/acp-probe`;
- GitHub-hosted Linux X64;
- Node `v22.23.2`;
- npm `10.9.8`;
- Python `3.12.14`;
- no repository secrets;
- removal of known `*_API_KEY`/`*_TOKEN` variables from the child environment;
- `NO_BROWSER=1`;
- pinned npm package versions and captured npm integrity/shasum metadata.

The fixture tree digest was:

`sha256:83ecabe8dedba88d5a208927e09e035f2b591b7c3ca259e315937880e070028e`

The raw sanitized traces are committed under `docs/research/acp/evidence/000a-attempt-001/`.

## Gemini CLI observation

Command:

```text
npx -y @google/gemini-cli@0.57.0 --acp
```

Observed:

- `initialize`: `SUCCESS`;
- negotiated `protocolVersion`: `1`;
- agent identity: `gemini-cli` `0.57.0`;
- four authentication methods were returned;
- `loadSession` was advertised;
- prompt capabilities advertised image, audio, and embedded context;
- MCP capabilities advertised HTTP and SSE;
- `session/new`: `AUTH_REQUIRED`, with `Gemini API key is missing or not configured.`;
- `session/list`: `METHOD_NOT_FOUND`.

Not observed:

- authenticated session creation;
- prompt execution;
- streaming updates;
- permissions;
- active cancellation;
- graceful ACP shutdown semantics.

The stderr trace also reported the synthetic folder as untrusted and disabled project agents/hooks. That behavior is preserved as evidence and was not bypassed.

## Codex ACP observation

Command:

```text
npx -y @agentclientprotocol/codex-acp@1.7.0
```

Observed:

- `initialize`: `SUCCESS`;
- negotiated `protocolVersion`: `1`;
- agent identity: `@agentclientprotocol/codex-acp` `1.7.0`;
- API-key authentication was returned;
- `loadSession` was advertised;
- session capabilities advertised list, resume, close, delete, additional directories, and subagents;
- `_meta.steering.supported` was `true`;
- prompt capabilities advertised image and embedded context;
- `session/new`: `AUTH_REQUIRED`;
- `session/list`: `AUTH_REQUIRED` rather than method-not-found.

Not observed:

- authenticated session creation;
- prompt execution;
- session-list behavior after authentication;
- streaming updates;
- steering behavior;
- permissions;
- active cancellation;
- graceful ACP shutdown semantics.

## Protocol-version finding

This attempt found a material compatibility constraint before product implementation exists.

Current ACP authority contains v1 and v2 wire/schema surfaces. The current representative registry packages used here negotiated v1 and expose v1-shaped initialization fields. The official registry's own daily protocol matrix also currently probes `PROTOCOL_VERSION = 1`.

Therefore Wispral must not equate "current ACP" with one immutable wire shape.

A future ACP runtime boundary should:

1. negotiate/detect supported protocol versions explicitly;
2. keep version-specific decoding and lifecycle mapping isolated;
3. normalize only semantics that are actually equivalent;
4. preserve unknown/extension metadata instead of discarding it;
5. expose per-agent capability differences to higher policy layers;
6. avoid advertising a control semantic merely because another ACP agent exposes it.

A v2-only implementation would be premature based on current registry reality.

## Independent upstream comparison

The official ACP Registry revision pinned for this attempt runs its own unauthenticated protocol adaptation matrix. Its 2026-09-01 snapshot reports 32 agents probed, 31 successful initialization probes, and 18 `session/new` authentication requirements.

For the two Wispral representatives it independently reports successful initialization for Gemini CLI `0.57.0` and Codex ACP `1.7.0`.

The Wispral observations are directionally consistent with that independent upstream reference. The upstream matrix is not treated as Wispral `OBSERVED` evidence and does not replace the committed Wispral traces.

## Recommendation

### Classification: `PARTIAL`

ACP should remain Wispral's **leading structured integration candidate**, but should not yet be elevated to an unconditional `PRIMARY` architecture decision.

Evidence supports:

- real launchability of two current pinned distributions;
- structured handshake and capability discovery;
- agent-neutral JSON-RPC/stdin-stdout framing across native and adapter-mediated paths;
- explicit authentication surfaces;
- meaningful per-agent capability differentiation;
- ecosystem breadth sufficient to justify continued protocol investment.

Evidence does **not** yet support:

- real prompt-turn portability;
- streaming behavior portability;
- cancellation latency or cancellation completion semantics;
- permission-request portability;
- steering portability;
- ACP v2 runtime interoperability;
- replacing a PTY compatibility fallback;
- claiming support for Gemini, Codex, or any other agent as a complete Wispral integration.

## Conditions to promote ACP from `PARTIAL` to `PRIMARY`

Before the founding program selects a production ACP runtime Grain, evidence should establish at minimum:

1. one authenticated non-destructive session/prompt flow on a native ACP agent;
2. one authenticated non-destructive session/prompt flow on an adapter-mediated ACP agent, or an explicit reason one representative class is deferred;
3. observed streaming/update behavior;
4. observed active-turn cancellation and terminal stop result;
5. observed structured permission behavior on a safe synthetic action, or an explicit bounded design for agents that do not expose it;
6. a deliberate v1/v2 compatibility decision backed by current registry reality.

Provider credentials or interactive provider authorization are external evidence inputs. Ordinary repository approval does not substitute for them.

## Impact on the Wispral architecture hypothesis

Attempt 001 strengthens these hypotheses:

- protocol-first integration remains preferable to terminal text scraping where ACP exposes the needed semantics;
- the product needs a version-aware ACP compatibility layer rather than a single generated latest-schema client;
- per-session/per-agent capabilities must be runtime data, not compile-time assumptions;
- deterministic Wispral permission policy must remain separate from provider-specific auth and agent-specific permission semantics;
- extension metadata such as Codex steering may be useful but cannot define the portable core contract.

Attempt 001 does **not** weaken the PTY fallback hypothesis. It makes the fallback boundary more important because structured semantics vary and some agents/features remain inaccessible or absent.

## Scope and claim limits

This report does not establish:

- full Gemini CLI support;
- full Codex support;
- Claude, OpenCode, Goose, Copilot, Cursor, or other registry-agent support;
- prompt latency;
- cancellation latency;
- permission safety;
- ACP v2 support;
- production reliability;
- macOS or Windows behavior;
- any speech/audio behavior.

## Review gate

The research execution is complete enough to enter `VERIFYING`.

The recommendation must not become `VERIFIED` until the exact evidence head is reconciled, an independent evidence review is obtained where available (or the unavailable review surfaces are recorded explicitly according to repository governance), and the final PR/head/evidence scope is rechecked.
