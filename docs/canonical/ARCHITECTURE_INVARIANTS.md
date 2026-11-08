# Wispral Architecture Invariants

**Status:** Founding candidate  
**Authority:** subordinate only to `CONSTITUTION.md` (1.0.0)

These invariants constrain architecture without prematurely selecting every implementation detail. A durable architectural decision that changes an invariant requires an explicit ADR and, when necessary, a constitution amendment.

## A1. The core is an event-driven control plane

Wispral must model voice interaction as a sequence of typed events and state transitions rather than a monolithic `audio -> text -> shell` pipeline.

The conceptual event families include:

- audio capture state;
- speech-start and speech-end observations;
- partial and final transcription;
- repository-entity candidates and bindings;
- interpreted utterance class;
- agent session lifecycle;
- agent stream updates;
- permission requests;
- cancellation and steering;
- user confirmation/denial;
- generation, rendering, and playback jobs;
- target and context snapshots;
- consent state and revocation;
- tenant, account, and channel sessions;
- external actions and their observed outcomes;
- evidence and diagnostic events.

Exact schemas are deferred until evidence selects them.

## A2. Audio and agent execution must be independently cancellable

Microphone capture, STT, TTS, playback, generation workers, agent requests, agent streaming, external actions, and UI rendering must not share one irreversible task lifecycle. A cancellation reports one of: stopped, completed before cancel, or stopped-unconfirmed.

A user interruption must be able to stop audible output and request agent cancellation without waiting for final transcription of the interrupting utterance.

## A3. Provenance is preserved across interpretation

The architecture must keep separable representations for:

1. source audio metadata or an explicit non-persistence marker;
2. raw transcript;
3. normalized transcript;
4. domain entity candidates (repository, application, project, or tenant-authorized knowledge);
5. selected entity bindings and confidence/evidence;
6. utterance semantic class;
7. final instruction, generation request, or action payload, with its target;
8. authorization decision, including the consent and tenant authority it relied on.

A polished prompt must never be the only surviving representation of what the user said.

## A4. `COMMAND` and `ASIDE` are semantic concepts, not necessarily one classifier

The architecture must permit speech that contributes context without authorizing execution. The exact UX may use explicit modes, hold gestures, spoken markers, deterministic controls, probabilistic classification, or a hybrid.

Any probabilistic classifier must feed deterministic policy before consequential action.

## A5. Agent integration is protocol-first

The preferred integration boundary is a structured protocol that exposes session lifecycle, streaming updates, permissions, and cancellation.

ACP is the leading founding hypothesis because it standardizes agent/client communication and has an official Rust SDK with client, agent, proxy, and conductor roles. This remains a hypothesis until compatibility experiments verify the exact agents and semantics Wispral needs.

PTY integration is a compatibility boundary, not the semantic source of truth for the core when a structured protocol is available.

## A6. Protocol adapters do not own product policy

Agent-, engine-, and channel-specific adapters may translate capabilities and events. They must not independently decide:

- whether an utterance is authorized;
- whether a risky action is approved;
- whether a transcript is sufficiently confident;
- whether telemetry is emitted;
- whether persistent recording is allowed;
- whether voice or asset consent is valid;
- which tenant, account, or credential applies;
- whether an action may bypass the user.

Those decisions belong to deterministic Wispral policy.

## A7. Speech engines are replaceable

No STT, VAD, TTS, wake-word, noise suppression, AEC, or speech provider may become inseparable from the control-plane contract.

The architecture must permit controlled bakeoffs and per-platform backends without changing agent semantics.

## A8. Context is bounded and inspectable

Context collection must expose why data was selected and must observe explicit budgets. A repository context engine may use Git, file paths, symbol indexes, LSP, tree-sitter, build metadata, recent agent events, shell output, or user dictionaries, but must not silently ingest unbounded repository content. Application, project, and tenant-knowledge context follow the same rule, each within its own authorized scope.

Context must improve interpretation without becoming an implicit data-exfiltration channel.

## A9. High-risk authorization fails closed

Unknown capability, malformed permission request, ambiguous destructive intent, missing policy, low-confidence high-impact target, or policy-engine failure must not become approval by default.

Risk tiers and exact confirmation mechanisms are selected by security specifications, not ad hoc adapter code.

## A10. Local-first does not mean local-only

The core must support a useful local path. Optional cloud speech or agent services may exist behind explicit configuration and observable network boundaries.

Cloud failure must not silently switch to a provider with weaker privacy or authorization semantics.

## A11. Rust owns concurrency and policy boundaries

Rust is the preferred home for:

- runtime orchestration;
- audio state and framing;
- cancellation;
- agent protocol/client logic;
- permission policy;
- context orchestration;
- TUI/CLI;
- benchmark harness control;
- configuration and provenance records.

Native speech libraries or other-language tooling may sit behind bounded interfaces when justified by evidence. Isolated donor-native or Python workers, such as speech engines or a dialogue service, may own their own processes when their exact dependency closure and resource and stop behavior are evidenced. Rust-first is a justified boundary, not a mandate to rewrite them.

## A12. Each product surface is qualified on its own; core diagnostics stay text-accessible

Core contracts and diagnostics retain CLI/text accessibility. WisprSide may retain its donor's desktop surface; WisprStudio may retain its donor's desktop production surface; Klaint uses its service and an optional, unmodified inbox through its API. Each surface requires its own authority and accessibility evidence, and graphical surfaces consume the same core contracts.

No new core daemon, custom IDE, avatar environment, or compulsory heavyweight shell is required. This replaces the earlier rule that the first product surface is terminal-native; it is an explicit change, not a reinterpretation.

## A13. Push-to-talk is the reliability baseline

The founding product should establish a deterministic, visible push-to-talk path before attempting always-listening or full-duplex behavior.

Hands-free capture, semantic endpointing, TTS, barge-in over speakers, and acoustic echo cancellation are separate capability horizons with independent evidence requirements.

## A14. Accessibility cannot depend on voice alone

Every consequential control path must have a non-voice fallback. Every product surface must expose visible state for listening, interpreting, waiting, acting, asking permission, cancelling, and failure.

## A15. Benchmark instrumentation is part of architecture

The runtime must eventually expose timestamps and typed diagnostic events sufficient to measure at least:

- speech onset;
- end-of-turn decision;
- partial/final transcript availability;
- entity-resolution completion;
- instruction dispatch;
- agent acknowledgement/first update;
- cancellation request;
- TTS, playback, or worker stop where applicable;
- external action outcome where applicable.

Performance claims must be derivable from instrumented events rather than screen recordings or manual stopwatch estimates.