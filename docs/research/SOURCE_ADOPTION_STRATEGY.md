# Wispral Source Adoption Strategy

**Status:** research / architecture planning artifact; non-executable  
**Authority:** does not change `specs/CURRENT.md`, the active `000B2` recovery frontier, or any product-code authorization  
**Prepared:** 2026-09-06  
**Base:** canonical `main` at `16104eacf2d571276452d173ddb54c089faccd0e`

## Purpose

Wispral has accumulated a large set of useful external source projects across speech recognition, desktop capture, hotkeys, agent protocols, terminal integration, audio processing, context engines, diagnostics, packaging, and product UX.

The goal is **not** to combine those applications wholesale. The goal is to extract proven mechanisms behind Wispral-owned interfaces while preserving:

- the founding product boundary: trustworthy voice control for independent AI coding agents;
- Rust-first runtime ownership;
- explicit authority and provenance;
- local-first operation;
- cross-agent portability;
- independently testable capture, speech, context, policy, and agent-control seams;
- reproducible evidence before product claims.

This document makes the source pool implementation-ready without granting implementation authority ahead of the canonical roadmap.

## Founder source-use authorization

The Founder states that separate permission exists to use the source code of all previously discussed source projects for Wispral.

For repository governance, that statement is treated as **project-level authorization to evaluate, adapt, and reuse donor code where the rights basis is valid**. It is not used as a substitute for provenance evidence.

Before copied or adapted implementation enters canonical product code, the responsible task must record:

1. exact upstream repository identity;
2. exact upstream commit or release;
3. exact source paths used;
4. upstream license at that revision;
5. any separate permission or exception relied upon when ordinary license terms would otherwise be incompatible;
6. required notices/attribution;
7. model/weight/data licenses separately from application code;
8. imported transitive dependencies and native binaries, if any;
9. a patch/delta description showing what Wispral changed;
10. Wispral-owned acceptance tests for the adopted behavior.

This keeps future relicensing, security review, contributor review, and supply-chain analysis possible even when broad source-use permission exists.

## Core decision: adopt mechanisms, not applications

Wispral should not become a source-code collage.

Every donor mechanism must terminate at a Wispral-owned contract. The contract belongs to Wispral even when an implementation is partly adapted from an external project.

The preferred pattern is:

```text
external source mechanism
        │
        ▼
exact donor qualification
        │
        ▼
small adapted implementation
        │
        ▼
Wispral-owned typed contract
        │
        ├── deterministic tests
        ├── provenance record
        ├── platform evidence
        └── replaceable implementation
```

Avoid:

```text
copy complete application
        │
        ▼
inherit its state model + UI + dependencies + product assumptions
        │
        ▼
try to reshape it into Wispral later
```

That path would weaken the founding thesis and make provenance, portability, and authority harder to reason about.

## Target architecture boundaries

The source-adoption plan assumes the following future **logical** boundaries. These are planning interfaces, not implementation authorization.

### A1 — Capture Runtime

Responsibilities:

- microphone device selection;
- explicit capture state;
- push-to-talk lifecycle;
- later background/hands-free lifecycle;
- bounded PCM delivery;
- permission state;
- device-loss recovery;
- no transcription semantics.

Likely donors/references: OpenWhispr, VoiceStudio, Meetily-Local.

### A2 — Activation / Hotkey Runtime

Responsibilities:

- global activation;
- push/release/toggle semantics;
- platform-specific shortcut registration;
- modifier-only handling where supported;
- registration failure reason;
- deterministic fallback;
- no speech or agent semantics.

Likely donors/references: OpenWhispr, VoiceStudio.

### A3 — Audio Conditioning Runtime

Responsibilities:

- resampling and framing;
- optional denoise/enhancement only when separately qualified;
- VAD/endpoint observations;
- echo/render-bleed observations for duplex modes;
- source labels (`mic`, `system`, future explicit sources);
- measurements separated from policy.

Likely donors/references: Silero VAD, TEN VAD, DeepFilterNet, RNNoise, OpenWhispr echo/gating seams, Meetily-Local.

### A4 — STT Provider Contract

Responsibilities:

- streaming session lifecycle;
- partial/final transcript events;
- exact model/runtime identity;
- context/keyterm capability advertisement;
- cancellation;
- timing/resource instrumentation;
- provider-specific behavior isolated behind a typed boundary.

Primary currently qualified candidate families: Moonshine, whisper.cpp, sherpa-onnx.

Future references/candidates remain evidence-gated and include Parakeet/NeMo, Omnilingual ASR, medical/other specialized ASR projects previously discussed, and any later model that wins a named Wispral job.

### A5 — Turn / Interaction Engine

Responsibilities:

- speech start/end observations;
- pause tolerance;
- push-to-talk baseline;
- future semantic endpointing;
- barge-in observation;
- explicit turn state machine;
- no agent authorization decisions.

Likely donors/references: VAD projects, OpenWhispr capture state machines, speech-to-CLI prototypes, backtalk, VoiceStudio delivery-race patterns.

### A6 — Interpretation Engine

Responsibilities:

- raw transcript preservation;
- developer entity candidates;
- ambiguity;
- `Command` versus `Aside` semantics;
- bounded contextual interpretation;
- no silent authorization from retrieved context.

Likely donors/references: Graphify, code-graph-rag, repository/context systems previously discussed, Berkeley Aside research.

### A7 — Context Resolver

Responsibilities:

- files, symbols, packages, flags, branches, tests;
- bounded repository indexes;
- source-scoped context packs;
- recency and provenance;
- correction/deletion boundaries for persistent context;
- no execution authority.

Likely donors/references: Graphify-Labs/graphify, vitali87/code-graph-rag, Zed project/thread organization, later qualified memory/context projects.

### A8 — Agent Transport

Responsibilities:

- structured agent lifecycle through ACP when supported;
- PTY fallback where separately qualified;
- typed stream updates;
- cancellation;
- permissions and requests;
- adapter-specific capability advertisement.

Likely donors/references: agentclientprotocol/rust-sdk, agentclientprotocol/registry, anomalyco/opencode, Zed ACP integration, representative agents, voice-to-CLI prototypes.

### A9 — Trust / Policy Plane

Responsibilities:

- distinguish heard text, resolved entities, interpreted intent, agent request, and authorization decision;
- deterministic risk classes;
- explicit approval/deny state;
- no historical context as silent authority;
- auditable decision events.

Likely references: ACP permission semantics, OpenCode permission engine, Wispral's own threat model and Diffcipline principles.

### A10 — Session Event Journal

Responsibilities:

- typed monotonic events;
- raw/derived provenance;
- cancellation timeline;
- correction events;
- bounded retention;
- safe diagnostics export.

Likely references: OpenCode event/server patterns, Zed threads, OpenWhispr session segmentation, VoiceStudio diagnostics.

### A11 — Surface Adapters

Responsibilities:

- terminal/CLI first;
- later tray/overlay only when justified;
- future MCP/API/SDK surfaces over the same semantic model;
- UI state must not become execution authority.

Likely references: VoiceStudio Tauri boundary, OpenWhispr desktop UX, ACP clients, Circleback interface convergence as a product reference.

### A12 — Diagnostics / Distribution

Responsibilities:

- self-check;
- safe support bundle;
- platform capability report;
- model/runtime integrity;
- shortcut/microphone/agent transport diagnostics;
- packaging/update lifecycle;
- launch-at-login only when later authorized.

Likely references: VoiceStudio diagnostics/packaging, OpenWhispr autostart and platform handling.

## Donor maturity states

Every source or source fragment progresses through these states independently.

### `REFERENCE`

Architecture or UX may inform research. No code is copied.

### `DONOR_CANDIDATE`

Exact repository and plausible useful paths are known, but no adoption decision exists.

### `QUALIFIED_DONOR`

The responsible task has pinned source revision, rights basis, dependencies, security concerns, platform behavior, and exact candidate paths.

### `ADAPTATION_CANDIDATE`

A bounded Wispral implementation exists on a non-canonical branch with provenance and tests.

### `PRODUCT_ADOPTED`

The adaptation has passed the active specification's acceptance gates and merged through normal review.

No source advances automatically because another part of the same repository was qualified.

## Per-import evidence package

Any direct code adoption should create a small evidence package, ideally under a future `docs/provenance/` or task-owned evidence path:

```text
source_id
upstream_url
upstream_commit
upstream_paths[]
upstream_license
permission_basis
required_notices[]
source_hashes[]
transitive_dependencies[]
model_or_data_assets[]
adaptation_paths[]
adaptation_summary
security_notes
platform_notes
tests[]
review_status
```

Large source trees should not be vendored merely to preserve provenance; pin exact upstream identities and retain only the minimum adopted implementation unless offline/reproducible build requirements later justify vendoring.

## Adoption rules

### Rule 1 — One donor must solve one named Wispral job

Do not add an engine, library, or subsystem because it is impressive or popular.

Each adoption must state a user/engineering job such as:

- reliable modifier-only push-to-talk on Windows;
- GNOME Wayland global shortcut support;
- lowest-latency CPU streaming STT under a defined hardware envelope;
- explicit ACP cancellation support;
- bounded repository symbol resolution;
- safe launch-at-login repair;
- deterministic echo/bleed observation for future duplex capture.

### Rule 2 — Prefer the smallest transplant

If 200 lines from a project solve the job, do not import a 200,000-line architecture.

### Rule 3 — Preserve donor independence

Do not rewrite an adapted source so completely during the first import that provenance becomes impossible to audit. Prefer:

1. exact donor snapshot/port commit;
2. separate Wispral adaptation commit;
3. tests showing behavior before and after adaptation.

### Rule 4 — No hidden dependency inheritance

External lockfiles, CI workflows, model downloads, binary helpers, analytics, cloud services, update channels, and telemetry do not enter Wispral automatically with copied code.

Each is a separate dependency decision.

### Rule 5 — Models and datasets are separate products

Permission for application code does not imply permission for model weights, tokenizers, training data, benchmark audio, voices, or generated assets.

### Rule 6 — Platform behavior is part of correctness

Any desktop/capture/hotkey donor must explicitly document macOS, Windows, Linux/X11, and Linux/Wayland behavior relevant to the adopted job. Unsupported paths must fail visibly.

### Rule 7 — External benchmark results never become Wispral claims

Donor benchmarks may shape experiment design. Wispral claims require Wispral evidence.

### Rule 8 — Context never becomes silent authority

Copied memory, notes, graph, screen, meeting, or context mechanisms may supply evidence to interpretation. They may not authorize consequential actions merely because they were retrieved.

### Rule 9 — Product boundaries survive donor breadth

Do not let meeting capture, dictation, TTS, voice cloning, note taking, CRM automation, or IDE features displace the core category before H15 explicitly permits expansion.

### Rule 10 — A donor must remain replaceable

The Wispral contract must not expose donor-specific types outside the adapter unless the active specification proves that coupling is a durable requirement.

## Implementation order

This is a dependency order, not an authorization schedule.

### Stage S0 — Source lab and provenance system

Deliverables when authorized:

- canonical source registry;
- exact permission/license evidence format;
- import checklist;
- minimal attribution policy;
- donor test fixture convention;
- decision on Wispral's own repository license during 000F.

### Stage S1 — H1 capture + activation

Highest-value donor research:

- OpenWhispr hotkey platform matrix;
- VoiceStudio native delivery/readiness race patterns;
- Meetily-Local platform capture behavior;
- native Rust audio/capture libraries selected by Wispral evidence.

Target: smallest reliable PTT runtime with explicit microphone state.

### Stage S2 — H1 STT adapter

Use the winner selected by canonical 000B evidence. Keep Moonshine, whisper.cpp, and sherpa-onnx behind one provider contract even if only one ships initially.

### Stage S3 — H2 structured agent control

Use ACP Rust SDK and exact representative-agent evidence. Borrow server/event/permission mechanisms from OpenCode or Zed only where they close a measured gap.

### Stage S4 — H3 portability

Add a materially independent second agent through the same Wispral contracts. Any vendor-specific behavior stays in adapters.

### Stage S5 — H4 developer context

Qualify Graphify/code-graph mechanisms against WispralBench developer-entity tasks. Adopt only the index/invalidation/resolution primitives that measurably improve safe entity binding.

### Stage S6 — H5 Command / Aside

Implement semantic separation using Wispral-owned typed intent/provenance events. External think-aloud and conversation systems are references, not authority systems.

### Stage S7 — H6 interruption

Measure full barge-in path. Reuse transport cancellation primitives and capture state-machine lessons, not UI-specific assumptions.

### Stage S8 — H7 trust plane

Promote deterministic allow/ask/deny patterns only after exact permission semantics are proven. Preserve all layers of provenance.

### Stage S9 — H9 hands-free capture

Evaluate VAD/endpoint/wake-word donors only after PTT reliability is proven. Visible capture state remains mandatory.

### Stage S10 — H10 duplex / selective voice output

Evaluate OpenWhispr echo/bleed seams, audio enhancement projects, and TTS only under a separate duplex measurement spec. Never add full-duplex because a donor already implements it.

### Stage S11 — H11 extension model

Generalize provider interfaces only after repeated integrations prove the seams. Apply a job-based engine/provider acceptance policy.

### Stage S12 — H12 distribution

Adopt proven packaging, self-check, launch-at-login, update repair, and support-bundle mechanisms with platform-native evidence.

## What should be copied versus reimplemented

### Strong direct-adoption candidates

Prefer direct adaptation when rights/provenance are clear and the code is a small isolated mechanism:

- protocol message types/adapters where using the canonical SDK is preferable to reimplementation;
- small platform shortcut helpers;
- pure audio-analysis helpers with deterministic tests;
- parsers/normalizers with stable contracts;
- platform capability probes;
- pure graph/index algorithms;
- small diagnostics collectors.

### Prefer clean Wispral reimplementation

Prefer independent implementation when donor code is tightly coupled to another application's state model or framework:

- complete React/Electron/Tauri screens;
- meeting-note stores;
- broad application state containers;
- cloud account/sync systems;
- proprietary product-specific workflow logic;
- donor-specific permission UI;
- complete application bootstraps.

The implementation can reproduce the mechanism while preserving Wispral's runtime architecture.

## Deep architectural conclusions

### 1. Wispral should be a control kernel, not a desktop application architecture

The durable asset is a typed authority-aware event model that can sit behind CLI, tray, overlay, MCP, or future SDK surfaces.

### 2. Capture and interpretation must be independently replaceable

Microphone capture, STT, turn detection, context resolution, and intent classification should not share hidden mutable state.

### 3. Raw evidence must survive every semantic layer

The system should retain inspectable links:

```text
raw audio/utterance identity
  -> raw transcript
  -> transcript revisions
  -> resolved developer entities
  -> interpreted Command/Aside
  -> agent request
  -> policy decision
  -> agent event/result
```

### 4. Cancellation is an end-to-end protocol

Barge-in is not one function call. The event journal must distinguish:

- speech onset;
- local output suppression;
- cancellation request;
- transport acknowledgement;
- final stale-output boundary;
- new instruction dispatch.

### 5. Background operation must remain visible

OpenWhispr/VoiceStudio demonstrate the usefulness of tray/background capture. Wispral should adopt lifecycle reliability but reject invisible ambient authority.

### 6. Context systems need source-scoped trust

Graph, memory, prior conversation, screen, terminal, and repository sources must remain distinguishable. Retrieval increases evidence; it does not increase authority.

### 7. Provider breadth should be earned

Use a job-based acceptance model: each new STT, agent, context provider, or TTS provider must own a named capability job, pass smoke tests, have a maintainer/stewardship story, and survive deprecation rules.

## Readiness criteria for future implementation

This source-adoption plan is considered implementation-ready when a future executable specification can select a source and answer, without rediscovery:

- what Wispral job the source solves;
- which architecture boundary receives it;
- exact source identity and rights basis;
- which paths are candidates for direct adaptation;
- which behavior must be reimplemented instead;
- what tests prove the adapted behavior;
- what platform evidence is required;
- what provenance artifacts must be preserved;
- what claim remains forbidden until Wispral qualification.

The companion source registry provides the source-by-source map.

## Non-effect on current `000B2`

Nothing in this document changes:

- ATTEMPT-002;
- B2R07 or later recovery authorization;
- the frozen candidate set;
- C0 controls;
- scoring;
- comparative claim guards;
- product-code authorization.

The active specification remains the only executable authority.