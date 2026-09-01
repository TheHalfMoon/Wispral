# Wispral Constitution

**Version:** 0.1.0  
**Status:** Founding candidate  
**Ratified:** pending canonical merge

## Preamble

Wispral exists to make speaking to AI coding agents a trustworthy control interface rather than a transcription shortcut. The product should let a developer speak, think aloud, interrupt, steer, inspect, approve, and recover while preserving the authority boundaries of the underlying agent and repository.

The project optimizes for durable usefulness, interoperability, trust, speed, and open evidence. Popularity is a desired consequence of exceptional utility, not a substitute for it.

## Principle I — Control plane, not another agent

Wispral MUST remain primarily an interface and control plane around independent agents. It MUST NOT require users to adopt a Wispral-owned foundation model, coding agent, IDE, or hosted reasoning service for the core product to work.

Agent-specific adapters MAY improve compatibility but MUST remain outside the portable core contract.

## Principle II — Speech is evidence, not authority by default

Raw audio, transcripts, interpreted intent, resolved repository entities, and authorized actions are distinct states.

Wispral MUST NOT silently transform ambiguous or tentative speech into consequential authority. The system MUST preserve enough provenance to explain what was heard, what was resolved, what was interpreted, and what was sent to an agent.

## Principle III — Interruptibility is a first-class primitive

A voice interface that cannot be interrupted cannot be a trustworthy control plane.

Cancellation, barge-in, steering, pause, denial, and recovery MUST be designed as core runtime semantics rather than UI conveniences added after execution.

## Principle IV — Command and context are different

Wispral MUST support the product distinction between speech intended to cause action and speech intended to provide context, exploration, preference, or tentative reasoning.

The project MAY evolve the exact interaction mechanism, but it MUST NOT assume that every spoken utterance is an executable command.

## Principle V — Repository-aware meaning outranks generic dictation

Wispral SHOULD use bounded repository context to improve interpretation of paths, symbols, package names, flags, branches, tests, and other developer entities.

Context resolution MUST remain inspectable, confidence-aware, bounded, and reversible. A low-confidence entity binding MUST NOT be hidden behind polished text.

## Principle VI — Agent and protocol neutrality

No single commercial agent, model vendor, editor, speech provider, or proprietary protocol may become necessary for the core workflow.

Open protocols SHOULD be preferred when they provide the required semantics. Compatibility fallbacks MAY exist, but protocol-specific behavior MUST not leak into the portable product contract without explicit justification.

## Principle VII — Local-first, cloud-optional

A useful core path MUST be possible without a Wispral account or mandatory Wispral-hosted service.

Cloud speech, model, synchronization, or enterprise services MAY be supported as optional adapters. Their failure MUST NOT silently weaken privacy, authorization, or evidence guarantees.

## Principle VIII — Deterministic trust boundaries

Speech recognition, language models, entity resolution, and ranking may be probabilistic. Authorization, policy evaluation, state transitions, evidence binding, safety escalation, and destructive-action gates MUST be deterministic and testable.

Probabilistic confidence MAY inform a deterministic rule; it MUST NOT itself become the sole authority for a high-risk action.

## Principle IX — Risk changes rigor

Verification and user confirmation MUST scale with blast radius.

Read-only inspection, reversible edits, repository writes, external side effects, credential use, spending, destructive operations, and publication actions MUST NOT share one undifferentiated approval policy.

High-risk paths require explicit negative-path, cancellation, provenance, and recovery evidence.

## Principle X — Rust owns the runtime, not the ideology

The product runtime SHOULD be Rust-first for latency, concurrency, cancellation, portability, memory safety, and single-binary distribution.

Other languages and native libraries MAY be used when evidence demonstrates a better engineering boundary. Language purity MUST NOT outrank product correctness, accessibility, portability, or maintainability.

## Principle XI — Open benchmarks before comparative claims

Wispral MUST NOT claim superiority in latency, accuracy, developer speech recognition, interruption, privacy, compatibility, or productivity without a reproducible public method and artifacts sufficient for independent challenge.

Benchmarks MUST include adverse and losing results where material. Hidden scorer knowledge, cherry-picked devices, or undocumented prompt/model changes invalidate a general comparative claim.

## Principle XII — Progressive refinement over speculative scale

Program ambition may be large, but executable work MUST remain small enough to understand and prove.

Distant roadmap horizons MUST remain intentionally coarse. Near-term work is recursively refined until it satisfies the Definition of Grain. Evidence, not enthusiasm, selects the next implementation frontier.

## Principle XIII — Accessibility is a product contract

Voice interaction can materially improve or harm accessibility. Wispral MUST treat configurable input behavior, speech pacing, visible state, non-voice fallback, keyboard control, captions/transcripts, and failure recovery as product requirements rather than polish.

The product MUST NOT assume one accent, speaking cadence, language, microphone setup, hearing ability, or motor interaction pattern.

## Principle XIV — Privacy is observable behavior

Microphone state, recording state, network use, transcript persistence, telemetry, model routing, and credential access MUST be observable and documented.

Core behavior MUST NOT depend on hidden background recording or undisclosed content telemetry. Telemetry, when introduced, MUST be opt-in or otherwise governed by an explicit approved privacy contract.

## Principle XV — Adoption claims are separate from engineering truth

GitHub stars, trending position, press, social reach, downloads, and community size are meaningful distribution signals but do not establish product correctness or technical superiority.

The project MAY pursue ambitious adoption goals, including category leadership, while keeping engineering acceptance criteria evidence-based and independently verifiable.

## Governance

1. This constitution is the highest product-governance document in the repository.
2. An implementation that violates a principle requires an explicit constitution amendment, not a hidden exception.
3. Amendments require a dedicated pull request describing motivation, compatibility impact, security/privacy impact, and affected specifications.
4. Semantic versioning applies to this constitution: major for incompatible principle changes, minor for new or materially stronger principles, patch for clarification.
5. ADRs govern durable architectural decisions. Specs govern bounded outcomes. Tasks govern execution order. Evidence governs verified state.
6. When these authorities conflict, the conflict must be resolved explicitly before dependent work proceeds.