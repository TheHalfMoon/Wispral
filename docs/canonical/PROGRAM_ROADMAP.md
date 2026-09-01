# Wispral Program Roadmap

**Status:** Founding candidate  
**Planning model:** progressive refinement; only the active frontier may be decomposed to execution-level tasks

## Mission

Make voice a trustworthy, low-friction control surface for independent AI coding agents.

A successful Wispral experience should eventually let a developer:

- start or attach to an agent session;
- speak developer-specific instructions naturally;
- resolve paths, symbols, flags, packages, branches, and tests against repository context;
- think aloud without accidentally authorizing action;
- interrupt and redirect an active agent immediately;
- inspect what Wispral heard and how it interpreted it;
- approve or deny consequential operations through explicit risk-aware policy;
- use multiple independent agents without relearning the voice interface;
- choose a local speech path without requiring a Wispral account;
- fall back to keyboard/text controls at any time.

## Program north stars

Engineering north stars are measured independently from adoption ambitions.

### Experience north star

`fresh install -> first successful spoken agent instruction`

The long-term product target is less than 60 seconds on a supported clean environment. No threshold becomes a public claim until measured by a reproducible install benchmark.

### Control north star

A deliberate interrupt must feel immediate and must stop further agent/audible progress before a user reasonably perceives the system as ignoring them.

Specific latency thresholds are benchmark targets, not founding claims.

### Trust north star

For every consequential action, the user must be able to determine:

- what Wispral heard;
- what Wispral resolved;
- what Wispral interpreted;
- what the agent requested;
- what policy authorized or denied.

### Interoperability north star

The core interaction model must survive changes in agent vendor, model vendor, and speech backend.

## Horizon model

A horizon describes durable direction and entry conditions. It does not authorize implementation by itself.

### H0 — Founding research and qualification

**Purpose:** replace architecture assumptions with reproducible evidence and establish governance.

Research surfaces include:

- ACP lifecycle, permissions, streaming, cancellation, authentication, and Rust SDK behavior;
- actual ACP behavior of representative coding agents;
- PTY fallback requirements;
- local streaming STT bakeoff;
- developer entity recognition methodology;
- turn detection and pause behavior;
- interruption instrumentation;
- microphone/privacy threat model;
- dependency/license/provenance review;
- macOS/Linux/Windows feasibility boundaries;
- brand/legal namespace risks sufficient for an open-source engineering decision.

**Exit:** evidence selects the first bounded product Grain. No broad architecture is considered proven merely by completing H0.

### H1 — Minimal Rust voice runtime

**Purpose:** establish the smallest reliable terminal-native capture/control skeleton selected by H0.

Expected capability class:

- Rust CLI/runtime;
- explicit microphone state;
- push-to-talk baseline;
- one selected STT path behind a replaceable boundary;
- typed event instrumentation;
- no agent mutation beyond the exact first integration contract.

**Entry:** H0 evidence selects concrete dependencies and one narrow runtime slice.

### H2 — First structured agent control

**Purpose:** prove that speech can drive a real independent coding agent through a structured lifecycle without collapsing Wispral into vendor-specific UI scraping.

Expected capability class:

- create/attach a session where supported;
- dispatch one spoken instruction;
- render agent updates;
- cancel an active request;
- preserve raw/interpreted provenance.

**Entry:** exact agent and protocol semantics are experimentally qualified.

### H3 — Independent second-agent portability

**Purpose:** prove the product contract is not accidentally one-agent architecture.

A second materially independent agent must exercise the same core interaction model with adapter-specific differences isolated.

**Entry:** H2 is verified and portability gaps are known.

### H4 — Developer context engine

**Purpose:** improve technical speech interpretation using bounded repository context.

Expected capability class:

- file/path candidate resolution;
- symbol/package/flag vocabulary support;
- visible confidence and ambiguity;
- context budgets;
- deterministic fallback when no safe binding exists.

**Entry:** WispralBench demonstrates a measurable baseline and a reproducible context-resolution hypothesis.

### H5 — Command / Aside semantics

**Purpose:** let users separate actionable instructions from tentative reasoning/context.

The exact control mechanism is deliberately not preselected.

**Entry:** research and user fixtures define failure cases, authority risks, and measurable acceptance criteria.

### H6 — Interruption and steering

**Purpose:** make barge-in a product primitive rather than a stop button layered on top.

Expected capability class:

- speech-onset observation during agent activity;
- immediate local output suppression where applicable;
- structured cancellation when supported;
- continuation with new instruction and preserved session context;
- explicit failure mode when an underlying agent cannot cancel safely.

**Entry:** instrumentation can measure the complete cancellation path.

### H7 — Permission and trust plane

**Purpose:** apply deterministic risk-aware authorization to structured agent requests and Wispral-originated actions.

Expected risk classes include read-only, reversible local writes, consequential repository/external writes, destructive/security-sensitive operations, and spending/publication actions.

**Entry:** threat model and agent permission semantics are verified.

### H8 — Compatibility expansion

**Purpose:** broaden support without weakening the portable core.

Candidate integrations may include Codex, Claude Code, Gemini CLI, OpenCode, Goose, GitHub Copilot CLI, Cursor, Aider, and future ACP agents. Inclusion depends on current protocol/runtime evidence, licensing, and maintainability.

**Entry:** two-agent portability contract is verified.

### H9 — Hands-free capture and semantic turn taking

**Purpose:** move beyond push-to-talk while preserving explicit microphone state and interruption safety.

Candidate research includes VAD, semantic endpointing, wake modes, configurable pause tolerance, and accessibility behavior.

**Entry:** push-to-talk is reliable and benchmark instrumentation distinguishes speech start, pause, end-of-turn, and false endpointing.

### H10 — Selective voice output and duplex control

**Purpose:** add spoken system/agent feedback where voice is useful without reading the terminal aloud.

Candidate capability class:

- concise spoken status and questions;
- interruptible TTS;
- half-duplex baseline;
- optional full-duplex/AEC only after separate qualification.

**Entry:** audio output cannot compromise capture, privacy, or cancellation semantics.

### H11 — Wispral SDK and extension model

**Purpose:** make the control plane reusable beyond the first CLI surface.

Potential extension boundaries include agents, speech engines, context providers, policy providers, TTS, and UI clients.

**Entry:** real repeated integrations justify extension points. No plugin system is authorized solely for architectural elegance.

### H12 — Cross-platform hardening and distribution

**Purpose:** make installation and updates boring on supported platforms.

Potential surfaces include Cargo, Homebrew, shell installer, signed binaries, package manager channels, completion scripts, diagnostics, and upgrade compatibility.

**Entry:** platform support claims are backed by native CI and, where hardware is required, explicit qualification evidence.

### H13 — Public WispralBench

**Purpose:** publish a reproducible benchmark suite useful to the wider voice-agent ecosystem.

Benchmark families may include developer entity accuracy, turn detection, end-to-end latency, cancellation, context resolution, CPU/memory, offline behavior, and cross-platform variance.

**Entry:** methodology has survived internal use without benchmark leakage or claim inflation.

### H14 — v1 trust and compatibility contract

**Purpose:** establish a stable product surface with documented compatibility, migration, security, privacy, accessibility, and support boundaries.

**Entry:** the project has enough real use and evidence to know what deserves stability.

### H15 — Category expansion

**Purpose:** evaluate whether the proven control plane should extend beyond coding agents to broader agentic software.

**Entry:** coding-agent product-market evidence exists. This horizon must not distract from establishing the core category.

## Adoption ambition

Wispral is intentionally designed for category-scale open-source adoption. Desired external outcomes include:

- GitHub Trending leadership;
- major developer-community launches;
- a contributor ecosystem around agents/speech/context;
- reference-quality benchmark usage;
- 10k, 25k, 50k, 100k, and ultimately 200k+ GitHub stars if product utility earns them;
- credible contention for high-profile repository-of-the-month/year recognition.

These are strategic ambitions, not engineering acceptance gates.

## Anti-roadmap

The following are explicitly not justified by the founding thesis and require separate evidence before entering the roadmap:

- a Wispral foundation model;
- a custom coding agent replacing existing agents;
- an Electron IDE;
- a multi-agent office/fleet visualizer;
- avatars or animated agent personas;
- a proprietary cloud account requirement;
- a hosted vector-memory platform;
- a generic project-management suite;
- a social network;
- mobile clients before the terminal control plane is proven;
- enterprise dashboards before core user value is established.

## Refinement rule

Only `specs/CURRENT.md` may authorize the next executable specification. H1 through H15 stay coarse until fresh evidence and completed dependencies make detailed refinement useful.

A roadmap horizon is not a task list.