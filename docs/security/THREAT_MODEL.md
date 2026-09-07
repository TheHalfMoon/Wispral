# Wispral Founding Threat Model

**Status:** founding threat-model candidate  
**Scope:** product architecture and research; no production-security claim

## 1. Security objective

Voice convenience must not create an authority channel that is easier to trigger accidentally, remotely, or ambiguously than the underlying coding agent.

Wispral should preserve user control when microphone input, speech recognition, repository context, agent output, permissions, plugins, external providers, security scanners, or supply-chain components behave unexpectedly.

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
- benchmark/private corpus data;
- tool, skill, server, adapter, and provider identities;
- security evidence, scanner findings, and provenance records;
- dependency, model, ruleset, and release provenance.

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
11. persistent state -> local filesystem/keychain/config;
12. repository bytes/filesystem metadata -> content identification and parser selection;
13. extension/tool/server discovery -> capability admission and identity binding;
14. security scanner/evaluator -> normalized security evidence;
15. package/model/ruleset source -> locally admitted dependency or runtime artifact;
16. mutable remote provider identity -> evidence and policy assumptions bound to that provider.

Each boundary requires explicit data-flow and failure behavior before production qualification. A probabilistic classifier, LLM reviewer, scanner score, or absence of findings must not directly become authorization.

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

### T13 — Content-type confusion and parser mismatch

A repository object can be named or extended like one file type while containing another, causing Wispral, an agent, or a parser to interpret different semantics.

Examples:

- executable or binary content named with a text/source extension;
- an archive presented as an ordinary document;
- a symlink followed when the user believed the link itself was being inspected;
- a parser selected from extension alone despite conflicting content evidence.

Required posture:

- extension, content-type observation, executable bit, symlink state, size, and parser choice remain distinct provenance fields;
- parser/execution selection must not trust filename extension alone;
- ambiguous or low-confidence content identity must have a bounded safe fallback;
- content-identity models or heuristics inform deterministic policy but do not authorize execution.

### T14 — Encoding, bytecode, Unicode, or content smuggling

Different decoders or tools may see materially different instructions in the same bytes.

Examples:

- malformed or ambiguous text encoding;
- mojibake that changes visible security-relevant text;
- hidden Unicode control characters;
- bytecode/generated artifacts presented as source;
- mixed binary/text or polyglot files;
- oversized/compressed input used to bypass inspection or exhaust resources.

Required posture:

- preserve raw-byte digest separately from decoded text;
- decoding is size-bounded and records the selected encoding/recovery path;
- suspicious controls, decode ambiguity, bytecode, archive expansion, and parser differentials are explicit signals;
- unsafe/unknown decoding fails to a non-executing path rather than silently coercing bytes into trusted text.

### T15 — Tool/skill identity confusion, shadowing, poisoning, or rug pull

Display names and stable-looking tool identifiers can conceal a changed implementation or conflicting capability.

Examples:

- a malicious tool uses a confusingly similar name;
- a later extension shadows a previously trusted tool;
- a tool description remains stable while implementation behavior changes;
- a previously approved skill changes its code after gaining trust;
- declared functionality omits hidden network, credential, or process behavior.

Required posture:

- bind admission and consequential approval to exact identity/capability evidence, not display name alone;
- compare declared and observed capabilities where feasible;
- material implementation, dependency, or capability drift invalidates affected prior approval;
- ambiguity, shadowing, and identity collisions fail closed for high-risk actions.

### T16 — Extension, dependency, model, or ruleset supply-chain substitution

A trusted component may be replaced or altered between qualification and use.

Required posture:

- record the strongest available source revision, artifact digest, package/model version, dependency lock, license/NOTICE identity, and release/signer provenance;
- mutable aliases are identified as such;
- material source/artifact drift triggers re-qualification where evidence depended on the old identity;
- native/FFI dependencies require their own security evidence rather than inheriting trust from Rust orchestration;
- third-party scanner/rule/model updates do not silently change policy semantics.

### T17 — Context over-sharing and cross-session leakage

A context provider, extension, or agent may receive more repository/session/history data than its task requires.

Required posture:

- context budgets and source scopes are explicit;
- historical/session context remains distinct from current-command authority;
- sensitive repository or transcript material is not shared merely because a provider can accept larger context;
- cross-session or cross-agent context transfer requires an explicit contract and visible provenance;
- security findings should identify over-sharing without themselves receiving unrestricted context.

### T18 — Provider/model endpoint substitution or material behavior drift

A remote service can preserve the same public model/provider alias while changing the implementation, routing, filtering, or model behind it.

Required posture:

- bind evidence to the strongest observable provider/model identity available;
- disclose when only a mutable service alias is known;
- do not carry exact-model claims across unverified provider drift;
- security/privacy fallback must not silently route to a materially different provider;
- benchmark or qualification evidence is stale when its relevant remote identity can no longer be reproduced or bounded.

### T19 — Security scanner false assurance or compromised evidence provider

A security tool can be wrong, stale, unavailable, non-deterministic, compromised, or itself exposed to prompt injection.

Required posture:

- scanner output is `SecurityObservation`/`SecurityFinding` evidence, not direct authorization;
- bind findings to scanner identity/version/configuration and raw-report digest where feasible;
- preserve `NOT_RUN`, `UNAVAILABLE`, `INCONCLUSIVE`, `STALE`, and equivalent non-success states;
- absence of findings is not automatically a security `PASS` unless the exact test contract defines that interpretation;
- probabilistic/LLM-based reviewer text cannot override deterministic Wispral policy;
- disagreement between evidence providers must remain visible rather than being silently majority-voted into authority.

### T20 — Agent-generated security regression hidden by task success

An independent coding agent can complete the requested functional task while introducing or preserving a vulnerability.

Required posture:

- repository-level security evaluation must be separable from functional task completion;
- future security benchmarks should combine deterministic policy assertions with static and dynamic evidence where justified;
- known vulnerable fixtures, negative controls, and losing results are preserved;
- Wispral must not claim that successful control-plane dispatch implies secure generated code;
- when security evidence is configured as an execution gate, its exact scope and failure semantics must be deterministic and observable.

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
- file-extension/content mismatch and low-confidence content-identity fixtures for repository ingestion;
- symlink/path traversal and bounded archive/oversized-input behavior where those inputs are supported;
- malformed encoding, Unicode-control, mojibake, bytecode, mixed binary/text, and parser-differential fixtures;
- tool/skill/server name-confusion, shadowing, declared-capability mismatch, and post-approval identity-drift tests for any extension surface;
- exact security-scanner/provider identity and unavailable/inconclusive/stale-result behavior;
- scanner-disagreement tests that prove deterministic policy does not collapse uncertainty into approval;
- repository-level security-regression fixtures for representative agent-driven changes;
- provider/model mutable-alias drift disclosure where remote services participate in a security, benchmark, or privacy claim;
- documented residual risks.

## 8. Source-informed planning note

`docs/research/AI_SECURITY_SOURCE_SYNTHESIS.md` and `docs/research/AI_SECURITY_SOURCE_REGISTRY.json` record the current study of:

- `Tencent/AI-Infra-Guard`;
- `google/magika`;
- `Tencent/AICGSecEval`;
- `Tencent/secguide`;
- `Tencent/TscanCode`.

The useful source-derived patterns include MCP/Skill/agent threat taxonomies, local content identification, bounded text decoding, SARIF finding interchange, repository-level hybrid security evaluation, secure-coding rule design, and native-code static-analysis boundaries.

Those sources do not establish Wispral security. They do not authorize a mandatory scanner service, generic plugin system, remote LLM security dependency, linked GPL component, or any change to the current executable specification frontier. Exact code adoption remains subject to path/blob/license/NOTICE provenance and the active specification that later selects it.

## 9. Non-claim

This document is a threat-model starting point. Wispral is not security-qualified, production-hardened, or safe for consequential autonomous operation merely because these threats are documented.