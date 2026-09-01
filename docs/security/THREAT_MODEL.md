# Wispral Founding Threat Model

**Status:** founding threat-model candidate  
**Scope:** product architecture and research; no production-security claim

## 1. Security objective

Voice convenience must not create an authority channel that is easier to trigger accidentally, remotely, or ambiguously than the underlying coding agent.

Wispral should preserve user control when microphone input, speech recognition, repository context, agent output, permissions, plugins, or external providers behave unexpectedly.

## 2. Protected assets

Potentially protected assets include:

- source code and repository contents;
- credentials, tokens, SSH material, keychains, and environment secrets;
- filesystem state outside the active repository;
- Git history and remote branches;
- package registries and release channels;
- cloud accounts and spending authority;
- production systems and deployment controls;
- microphone audio and transcripts;
- developer design reasoning captured as `ASIDE` context;
- agent session history;
- policy configuration;
- benchmark/private corpus data.

## 3. Trust boundaries

Founding trust boundaries include:

1. microphone/audio device -> Wispral audio runtime;
2. audio runtime -> STT backend;
3. STT backend -> interpretation/context engine;
4. repository/context providers -> interpretation engine;
5. interpretation engine -> deterministic policy;
6. Wispral -> agent protocol/PTY adapter;
7. agent -> Wispral permission/event handling;
8. optional TTS/output -> physical acoustic environment;
9. local process -> optional cloud provider;
10. plugin/extension -> core runtime;
11. persistent state -> local filesystem/keychain/config.

Each boundary requires explicit data-flow and failure behavior before production qualification.

## 4. Threat classes

### T1 — Ambient or remote speech triggers authority

Examples:

- another person says "yes";
- a video/podcast says an approval phrase;
- the agent's own TTS leaks into the microphone;
- a conference call contains command-like language;
- background conversation becomes a prompt.

Required posture:

- push-to-talk baseline before hands-free authority;
- visible listening state;
- no high-risk approval from unscoped ambient speech;
- full-duplex work requires echo/self-output defenses and separate qualification;
- high-risk operations may require a stronger confirmation modality than ordinary speech.

### T2 — STT substitution changes action meaning

Examples:

- `staging` becomes `production`;
- `do not delete` becomes `delete`;
- one branch/path/symbol is substituted for another;
- a negative constraint is dropped.

Required posture:

- preserve raw and normalized transcripts;
- treat destructive terms, negation, targets, quantities, credentials, and environment names as high-impact entities;
- risk-aware confirmation when interpretation materially changes authority;
- avoid silent transcript beautification that erases uncertainty.

### T3 — Repository entity false binding

Example:

User says "auth worker" and the resolver binds confidently to the wrong similarly named file/symbol.

Required posture:

- confidence/ambiguity is observable;
- low-confidence high-impact targets fail closed or require disambiguation;
- benchmark unsafe false-binding rate separately from overall accuracy.

### T4 — Tentative reasoning becomes command

Example:

User says, "Maybe we should drop the migration and recreate it," while thinking aloud, and the system executes deletion.

Required posture:

- `COMMAND` and `ASIDE` semantics remain distinct;
- speculative context cannot independently authorize a consequential action;
- retained asides are visible/correctable when persistence is introduced.

### T5 — Agent permission confusion

Examples:

- adapter misclassifies a structured permission request;
- permission scope changes between request and execution;
- generic spoken "yes" approves a different pending action;
- stale approval is reused.

Required posture:

- bind approval to a specific request identity and normalized action summary;
- do not reuse approval across changed requests;
- malformed/unknown permission forms fail closed;
- display exact or sufficiently precise details before high-risk approval.

### T6 — Cancellation failure creates false user confidence

Example:

Wispral displays "stopped" while the underlying agent or subprocess continues mutating state.

Required posture:

- distinguish `cancellation requested`, `cancellation acknowledged`, and `execution observed stopped` when the protocol exposes those states;
- do not claim STOPPED based only on local UI silence;
- unsupported cancellation semantics are a compatibility limitation.

### T7 — Prompt injection through agent/repository output

Repository files, command output, dependency text, or agent messages may contain instructions designed to influence Wispral policy or speech handling.

Required posture:

- deterministic policy does not delegate authorization to arbitrary model/repository text;
- context providers label provenance;
- untrusted content cannot change microphone, network, permission, telemetry, or persistence policy by being read as text.

### T8 — Cloud speech/provider data leakage

Required posture:

- local and cloud paths are explicit;
- network use is observable;
- provider selection is not silently changed on failure;
- data retention/provider terms are documented before support claims;
- secrets are not embedded in repository config examples.

### T9 — Sensitive transcript persistence

Think-aloud speech may contain credentials, customer names, personal information, architecture secrets, or unreleased product decisions.

Required posture:

- founding default should minimize persistence;
- transcript/history retention requires an explicit contract;
- deletion/export behavior must be defined before durable storage becomes a product feature;
- logging must not accidentally become a second transcript database.

### T10 — Plugin/adapter compromise

Required posture:

- extension points are not introduced until repeated real use justifies them;
- future plugins require explicit capability boundaries;
- adapters do not receive unrelated credentials or policy authority;
- dependency provenance and supply-chain security are part of acceptance.

### T11 — Shell/PTY injection and terminal ambiguity

PTY compatibility may expose escape sequences, shell quoting, prompt detection errors, or spoofed UI text.

Required posture:

- PTY output is untrusted data;
- do not infer destructive permission authority solely from terminal prose when a structured protocol exists;
- terminal escape/control handling requires explicit hardening;
- command construction must avoid shell interpolation where process APIs can pass arguments directly.

### T12 — Benchmark/privacy collision

Captured benchmark audio may become sensitive research data.

Required posture:

- synthetic scripts are preferred for public text fixtures;
- recorded voices require consent and redistribution/retention terms;
- private evaluation audio must not be committed accidentally;
- benchmark reproducibility must not override participant privacy.

## 5. Founding risk tiers

The exact policy remains a later specification, but research should test at least these conceptual tiers:

- **R0 Observational:** read/list/search, no mutation.
- **R1 Reversible local:** bounded local edits with clear recovery.
- **R2 Consequential repository:** commits, branch mutation, dependency changes, broad filesystem writes.
- **R3 External/public:** push, PR/release publication, deployment, external messaging, hosted mutations.
- **R4 Destructive/security/spend:** deletion with material loss, credentials/security policy, production effects, money/spend, irreversible operations.

A later ADR/spec must define actual policy. These tiers do not authorize actions by themselves.

## 6. Privacy baseline hypothesis

Before a separate privacy specification says otherwise:

- no mandatory Wispral account;
- no content telemetry;
- no hidden background recording;
- no persistent raw audio by default;
- diagnostic logs must avoid transcript content unless explicitly enabled for a bounded debugging session;
- cloud speech requires explicit configuration;
- microphone/listening state must be visible.

These are founding design requirements, not a production privacy certification.

## 7. Security evidence required before v1

At minimum, later qualification should include:

- permission negative-path tests;
- stale/mismatched approval tests;
- cancellation-state tests;
- ambiguous entity-binding tests;
- negation/target-substitution speech fixtures;
- ambient/TTS self-trigger tests for any hands-free mode;
- malformed protocol-event tests;
- terminal escape/PTY adversarial fixtures where PTY is supported;
- credential/logging review;
- dependency/supply-chain review;
- platform permission behavior review;
- documented residual risks.

## 8. Non-claim

This document is a threat-model starting point. Wispral is not security-qualified, production-hardened, or safe for consequential autonomous operation merely because these threats are documented.