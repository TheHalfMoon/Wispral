# Wispral Founding Research Register

**Date:** 2026-09-01  
**Status:** founding evidence register; not a substitute for executable qualification

## Research question

What product and architecture position gives Wispral a defensible chance to become the open voice-control layer for coding agents rather than another dictation wrapper?

## Current evidence-backed observations

### R1 — General voice input is moving toward voice-to-action

Wispr Flow publicly describes a three-phase path from reliable voice input to voice-to-action and ultimately broader device ubiquity. This means a product whose primary differentiation is `speech -> text insertion` competes with a well-funded category leader moving toward actions.

Source: `https://wisprflow.ai/post/the-master-plan` (published 2026-03-03; accessed 2026-09-01).

**Implication:** Wispral should own agent-control semantics rather than generic operating-system dictation.

### R2 — ACP is an active interoperability surface, not only a proposal

The Agent Client Protocol standardizes communication between clients/editors and coding agents. The official ACP organization publishes a registry and official SDKs. The official Rust SDK provides client, agent, proxy, and conductor roles; the conductor can compose proxy chains without modifying the final agent.

Sources:

- `https://github.com/agentclientprotocol/rust-sdk`
- `https://github.com/agentclientprotocol/registry`
- `https://zed.dev/blog/acp-registry`
- `https://zed.dev/acp`

Accessed 2026-09-01.

**Implication:** ACP is the leading structured integration hypothesis for Wispral. It still requires exact compatibility experiments for the agents and protocol behaviors Wispral needs.

### R3 — Existing coding-agent voice modes expose interaction gaps beyond transcription

Public Claude Code issues in 2026 document real user demand and friction around voice mode, including push-to-talk-only interaction, fixed pause/silence behavior that can cut off deliberate speakers, IDE surface gaps, lack of bidirectional readback, and desire to think aloud during planning.

Representative sources:

- `https://github.com/anthropics/claude-code/issues/45082`
- `https://github.com/anthropics/claude-code/issues/33792`
- `https://github.com/anthropics/claude-code/issues/34743`
- `https://github.com/anthropics/claude-code/issues/42700`
- `https://github.com/anthropics/claude-code/issues/27908`

Accessed 2026-09-01.

**Implication:** turn-taking, interruption, context, cross-surface portability, and selective voice output are product problems in their own right.

### R4 — Think-aloud speech carries useful programming context but creates authority risk

UC Berkeley technical report UCB/EECS-2026-274, *Aside: Think-Aloud Speech as Context for AI-Assisted Programming* (2026-08-14), reports a formative within-subjects study with 11 developers. Think-aloud speech exposed preferences and design goals not present in written prompts, but the study also found visibility problems and cases where tentative ideas were treated as confirmed goals.

Source: `https://www2.eecs.berkeley.edu/Pubs/TechRpts/2026/EECS-2026-274.html`.

**Implication:** Wispral should treat actionable commands and speculative/contextual speech as distinct semantic classes and keep retained context visible/correctable.

### R5 — Streaming local STT is an active technical space

Moonshine Voice publishes streaming speech-recognition work, including an August 2026 release note reporting speculative decoding latency reductions on its own measured platforms. Its current documentation also exposes runtime domain customization through keyterms/context for streaming architectures.

Sources:

- `https://github.com/moonshine-ai/moonshine`
- `https://github.com/moonshine-ai/moonshine/blob/main/CHANGELOGS.md`

Accessed 2026-09-01.

**Implication:** do not hard-code Whisper as the default merely because it is familiar. Run a controlled local STT bakeoff using developer-specific speech and exact hardware/configuration records.

## Competitive reference classes

The founding research distinguishes several reference classes instead of treating every voice product as the same competitor.

### Generic/developer dictation

Examples include Wispr Flow, Superwhisper, Aqua, and related system-wide speech-input tools.

What to learn:

- low-friction activation;
- correction/backtracking;
- technical vocabulary;
- cross-application ergonomics;
- onboarding and reliability.

What not to copy as the product boundary:

- focused-text-field insertion as the core abstraction.

### Agent-specific voice layers

Examples include Claude Code voice mode and `jaredrhod/backtalk`.

What to learn:

- push-to-talk reliability;
- local speech paths;
- permission conversation;
- spoken control commands;
- interruption expectations;
- session continuity.

What not to copy as the product boundary:

- dependence on one agent runtime.

### Multi-agent harnesses

Example: `chaitanyagiri/munder-difflin`.

What to learn:

- provider/agent breadth;
- agent lifecycle visibility;
- human gates;
- memorable product demos and identity;
- community extensibility.

What not to copy as the founding scope:

- office simulation;
- multi-agent orchestration as the primary product;
- custom IDE/dashboard expansion before the voice-control thesis is proven.

### Voice-to-CLI prototypes

Examples include `techempower-org/speech-to-cli` and `vidhan66/voice-interface-terminal-agent`.

What to learn:

- MCP/CLI interoperability ideas;
- VAD and duplex modes;
- wake-word and local-STT experiments;
- explicit measured failure modes such as technical token recognition.

What not to assume:

- prototype benchmark numbers generalize to Wispral hardware, corpus, architecture, or agents.

## Founding product hypothesis

Wispral's strongest differentiation is the combination of:

1. **agent-native control** — structured session, stream, cancellation, and permission semantics;
2. **developer-context interpretation** — repository-aware resolution of technical entities;
3. **command/context separation** — tentative thought does not automatically become authority;
4. **interruptibility** — immediate user steering is a runtime primitive;
5. **cross-agent portability** — one interaction model across independent coding agents;
6. **local-first operation** — useful operation without a mandatory Wispral cloud account;
7. **open evidence** — public benchmarks and explicit non-claims.

Each item remains a hypothesis until a specification supplies evidence.

## Founding falsification questions

Wispral should be willing to change direction if controlled experiments show any of the following:

- structured protocols do not expose enough lifecycle/permission/cancellation semantics for a portable control plane;
- PTY integration requires so much vendor-specific parsing that portability is not maintainable;
- repository context does not materially improve developer-entity accuracy over a strong STT baseline;
- command/context separation creates more interaction burden than value in realistic use;
- local streaming speech cannot meet acceptable latency/resource/accuracy bounds on target machines;
- agent cancellation cannot be made predictable enough to support trustworthy barge-in;
- microphone/privacy constraints make the desired hands-free interaction unacceptable without platform-specific redesign.

A failed hypothesis is research progress. It must not be hidden to protect the original product story.

## Research gaps selected for Specification 000

The first specification must produce reproducible evidence for:

- exact ACP capability matrix and at least two representative agent probes where feasible;
- PTY fallback constraints;
- local STT bakeoff protocol and first controlled results;
- developer entity corpus and scoring contract;
- turn-taking/pause corpus and scoring contract;
- interruption instrumentation design;
- permission/privacy threat model;
- dependency and license decision record sufficient to select the first implementation Grain;
- platform feasibility boundaries;
- brand/provenance/legal-risk notes sufficient for repository naming decisions without pretending to provide legal advice.

## Provenance rule

This document records ideas and public observations. Copying or adapting implementation material from any reference project requires a separate license/provenance review before code enters Wispral.