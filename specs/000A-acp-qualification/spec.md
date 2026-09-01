# Specification 000A — ACP Capability and Representative-Agent Qualification

**State:** `GRAIN` candidate after founding authority becomes canonical and readiness is rechecked  
**Parent:** `000-founding-research`  
**Type:** research / protocol qualification

## Outcome

Produce a reproducible ACP capability matrix and representative-agent observations sufficient to decide whether ACP should be Wispral's primary structured agent-control path for the first product implementation.

## Why this is first

Wispral's central value depends on session control, streaming, permission visibility, and interruption. Those semantics should be established before speech/runtime code is shaped around a transport that may not expose them.

## In scope

- pin and inspect the current ACP specification and official Rust SDK versions;
- record protocol lifecycle relevant to Wispral;
- inspect the current official ACP registry;
- qualify two representative agent paths where executable access is available:
  - one native ACP implementation, initially Gemini CLI (`gemini --acp`) unless current registry truth changes;
  - one adapter-mediated implementation, initially Codex via the current ACP registry adapter unless current registry truth changes;
- record handshake/authentication behavior;
- exercise or otherwise qualify new session, prompt dispatch, streaming update, permission request shape, cancellation, error propagation, and shutdown to the extent the implementation exposes them;
- preserve sanitized traces/command logs sufficient to reproduce observations;
- identify semantic gaps Wispral must bridge or expose as limitations;
- recommend `PRIMARY`, `PARTIAL`, or `REJECTED` for ACP as the first structured integration path.

## Out of scope

- production ACP client code;
- permanent crate/dependency adoption;
- a Wispral Cargo workspace;
- speech/audio code;
- PTY implementation;
- broad compatibility claims for untested registry agents;
- automatic destructive agent actions;
- bypassing agent permission systems;
- benchmarking model reasoning quality;
- comparing Codex versus Gemini as coding models.

## Representative-agent rationale

The initial pair intentionally exercises different integration modes:

- Gemini CLI is currently documented/registered with native ACP invocation;
- Codex is currently represented through an ACP adapter in the registry ecosystem.

This creates better portability evidence than testing two adapters with the same packaging model.

If canonical registry or upstream documentation changes before execution, replace the pair only through a documented pre-execution amendment rather than silently changing the experiment.

## Required capability fields

For ACP itself and each representative implementation, record:

- protocol/package version;
- launch command/distribution;
- authentication methods exposed;
- initialization/handshake;
- session creation;
- session resume if available;
- prompt dispatch;
- streaming content/update events;
- tool/action visibility;
- structured permission requests;
- permission response binding;
- cancellation request;
- cancellation acknowledgement or observable stop semantics;
- client capabilities required by agent;
- filesystem/context requests relevant to Wispral;
- graceful shutdown;
- malformed/error behavior encountered;
- unsupported/unknown fields.

## Acceptance conditions

000A is `VERIFIED` only when:

1. the exact ACP spec/SDK/registry revisions used are pinned;
2. a machine-readable or tabular capability matrix exists;
3. at least one executable representative-agent ACP path completes initialization and a non-destructive session/prompt flow, unless an external authorization/access blocker is recorded explicitly;
4. cancellation semantics are observed experimentally where access permits, or marked `NOT TESTED`/`UNSUPPORTED` without inference;
5. permission semantics are observed experimentally where a safe non-destructive fixture can trigger them, or marked `NOT TESTED`/`UNSUPPORTED`;
6. no untested registry agent is labeled supported;
7. the final recommendation states limitations and confidence;
8. all commands/traces are sanitized for credentials before commit;
9. the evidence is sufficient to shape 000B/000C without inventing protocol behavior.

## Risk

- authentication may require subscriptions or interactive browser state not available in CI;
- registry adapters can change quickly;
- live agent/model behavior can introduce nondeterministic content unrelated to protocol qualification;
- a session may request filesystem/tool access with side effects.

## Safety constraints

- use a disposable fixture repository;
- do not point agents at sensitive repositories;
- no production credentials beyond the normal provider authentication required for the user's own authorized account;
- do not disable permission/sandbox protections merely to make the probe pass;
- prefer non-destructive prompts;
- if a permission request cannot be triggered safely, record `NOT TESTED`.

## Recovery

All work is research-only. If an adapter or protocol version changes mid-run, invalidate comparability, preserve the prior attempt, pin the new version, and start a new attempt. Do not rewrite old evidence to match the new implementation.