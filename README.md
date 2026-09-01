<div align="center">

# Wispral

### Voice-native control for AI agents.

**Talk. Think aloud. Interrupt. Steer. Approve. Stay in the terminal.**

</div>

---

Wispral is an open-source, local-first project exploring a universal voice control plane for AI coding agents.

The goal is not to build another coding agent and not to turn speech into text for a focused input box. The goal is to make voice a trustworthy control surface around the agents developers already use: preserving session state, repository context, interruption, permissions, and visible user authority.

> [!IMPORTANT]
> **Wispral is in the founding research and specification phase.** There is no installable product or supported-agent matrix yet. No latency, accuracy, compatibility, privacy, security, or superiority claim is considered established until reproducible evidence exists in this repository.

## The product thesis

A mature Wispral interaction should eventually feel like this:

```text
You speak
   │
   ▼
Wispral hears the raw utterance
   │
   ├── resolves repository entities
   ├── preserves ambiguity and provenance
   └── distinguishes action from tentative context
   │
   ▼
Deterministic policy
   │
   ▼
Structured agent session
   │
   ├── stream progress
   ├── ask permission
   ├── cancel
   └── steer
   │
   ▼
You remain in control
```

Wispral is designed around several ideas that the founding research must prove or falsify:

- **Agent control, not dictation.** Voice should interact with agent lifecycle and permission semantics, not merely paste text.
- **Repository-aware speech.** Paths, symbols, flags, packages, branches, and tests should be interpreted using bounded project context.
- **Command vs. Aside.** Thinking aloud should be able to provide context without automatically authorizing execution.
- **Interruptibility.** A user must be able to stop and redirect an active agent without waiting for it to finish.
- **Agent neutrality.** The interaction model should survive changes in agent/model vendor.
- **Local-first operation.** A useful core path should not require a Wispral cloud account.
- **Open evidence.** Performance and compatibility claims should be independently reproducible.

## Why this repository starts with research

Voice-agent UX combines uncertain boundaries: audio capture, streaming speech recognition, technical vocabulary, turn detection, agent protocols, permissions, cancellation, repository context, privacy, and cross-platform behavior.

Choosing a stack first and proving it later would optimize for familiarity instead of correctness.

The initial program therefore follows two disciplines already developed in the broader TheHalfMoon ecosystem:

- **SpecGrain:** recursively refine work until each executable unit is independently understandable, bounded, recoverable, and verifiable.
- **Diffcipline:** proof before done; repository truth outranks narrative; risk changes verification rigor; benchmarks publish reproducible evidence.

Wispral adopts those principles directly in its own constitution and repository rules rather than depending on either project at runtime.

## Current frontier

The active parent research program is **Specification 000 — Founding Research and Qualification**.

Only its first near-term child is refined to execution level:

**000A — ACP Capability and Representative-Agent Qualification**

The purpose is to determine whether the Agent Client Protocol can provide the structured session, streaming, permission, and cancellation semantics Wispral needs before product code is shaped around it.

Future research children remain intentionally coarse until earlier evidence arrives.

## Program direction

The current roadmap horizons are:

```text
H0   founding research and qualification
H1   minimal Rust voice runtime
H2   first structured agent control
H3   independent second-agent portability
H4   developer context engine
H5   Command / Aside semantics
H6   interruption and steering
H7   permission and trust plane
H8   compatibility expansion
H9   hands-free turn taking
H10  selective voice output / duplex
H11  SDK and extension model
H12  cross-platform hardening and distribution
H13  public WispralBench
H14  v1 trust and compatibility contract
H15  category expansion, only if the coding-agent thesis is proven
```

A horizon is not an implementation task. `specs/CURRENT.md` owns the executable frontier.

## WispralBench

Generic word error rate is not enough for developer voice control.

The founding benchmark contract is designed to measure:

- developer entity accuracy;
- unsafe repository-entity false bindings;
- repository-context value;
- natural pause and end-of-turn behavior;
- barge-in/cancellation stages;
- end-to-end spoken-instruction latency;
- local CPU/memory/model footprint;
- per-agent capability rather than a misleading yes/no support badge;
- clean-install to first successful voice turn.

**No qualifying WispralBench result exists yet.**

## Rust-first, evidence-selected

Rust is the preferred product runtime for concurrency, cancellation, portability, memory safety, audio orchestration, and terminal-native distribution.

That preference is not permission to choose every dependency up front. Speech engines, audio primitives, protocol SDKs, PTY libraries, parsers, and other dependencies must be selected through explicit capability/licensing/maintenance evidence.

Other languages or native libraries may be used behind bounded interfaces when they provide a materially better engineering boundary.

## Repository authority

Read in this order before changing the project:

1. [`AGENTS.md`](./AGENTS.md)
2. [`CONSTITUTION.md`](./CONSTITUTION.md)
3. [`docs/canonical/CURRENT_STATE.md`](./docs/canonical/CURRENT_STATE.md)
4. [`docs/canonical/ARCHITECTURE_INVARIANTS.md`](./docs/canonical/ARCHITECTURE_INVARIANTS.md)
5. [`docs/canonical/PROGRAM_ROADMAP.md`](./docs/canonical/PROGRAM_ROADMAP.md)
6. [`specs/CURRENT.md`](./specs/CURRENT.md)
7. the complete active specification authority chain

Supporting foundations:

- [`docs/research/FOUNDING_RESEARCH.md`](./docs/research/FOUNDING_RESEARCH.md)
- [`docs/benchmarks/WISPRALBENCH.md`](./docs/benchmarks/WISPRALBENCH.md)
- [`docs/security/THREAT_MODEL.md`](./docs/security/THREAT_MODEL.md)
- [`docs/strategy/CATEGORY_AND_ADOPTION.md`](./docs/strategy/CATEGORY_AND_ADOPTION.md)

## Ambition

The project is being designed for category-scale open-source adoption. GitHub Trending leadership, a world-class contributor community, and 200k+ stars are legitimate ambitions.

They are not engineering acceptance criteria.

Wispral will earn the right to make strong claims only through a product that feels obvious after use and evidence that survives independent challenge.

## Contributing

The project is not yet accepting broad implementation work because foundational choices are still under qualification. Research reproductions, source corrections, benchmark-methodology criticism, accessibility input, protocol expertise, and security review will become valuable contribution surfaces as the founding authority becomes canonical.

Do not submit production architecture or large feature implementations ahead of the active specification frontier.

## License

License selection is intentionally part of Specification 000 dependency/provenance work. No license choice is implied until a canonical decision is recorded.
