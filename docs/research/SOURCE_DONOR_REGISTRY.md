# Wispral Source Donor and Reference Registry

**Status:** source inventory and adoption-planning register; non-executable  
**Prepared:** 2026-09-06  
**Companion:** `docs/research/SOURCE_ADOPTION_STRATEGY.md`

## Registry semantics

The registry distinguishes:

- `QUALIFIED_EXISTING` — already pinned/qualified by canonical Wispral research for a specific purpose;
- `DONOR_CANDIDATE` — source code may be adapted after exact revision/path/rights/dependency review;
- `PERMISSION_REPORTED_DONOR_CANDIDATE` — Founder reports separate permission to use the code; exact permission basis still belongs in the per-import provenance record;
- `ARCHITECTURE_REFERENCE` — useful architecture patterns, no direct-code decision yet;
- `PRODUCT_REFERENCE` — product/UX lesson only unless separately promoted;
- `BENCHMARK_REFERENCE` — external evidence may shape experiments but cannot establish Wispral claims;
- `IDENTITY_PIN_REQUIRED` — a project family was discussed, but exact canonical repository/revision must be resolved before adoption;
- `DEFERRED` — potentially useful but outside the current product horizon.

All direct imports remain gated by the active specification.

## A. Structured agent control and protocol sources

### Agent Client Protocol Rust SDK

- Repository: `https://github.com/agentclientprotocol/rust-sdk`
- Role: canonical structured agent protocol implementation reference / SDK dependency candidate.
- Wispral boundaries: `Agent Transport`, `Trust / Policy Plane`.
- Horizons: H0, H2, H3, H8.
- Status: `QUALIFIED_EXISTING` for founding ACP research; product adoption remains specification-gated.
- Candidate mechanisms: typed protocol lifecycle, client/agent/proxy/conductor roles, cancellation/permission/session semantics where exact SDK revision supports them.
- Rule: prefer canonical SDK use over locally reimplementing wire types unless measured constraints justify otherwise.

### Agent Client Protocol Registry

- Repository: `https://github.com/agentclientprotocol/registry`
- Role: compatibility/discovery reference.
- Horizons: H0, H8.
- Status: `QUALIFIED_EXISTING` as research input.
- Do not treat registry presence as proof of full Wispral compatibility.

### OpenCode

- Repository: `https://github.com/anomalyco/opencode`
- Role: agent runtime/process/permission/event architecture donor/reference.
- Wispral boundaries: `Agent Transport`, `Trust / Policy Plane`, `Session Event Journal`.
- Horizons: H2, H3, H7, H8.
- Status: `DONOR_CANDIDATE`.
- Candidate mechanisms:
  - typed allow/ask/deny permission model;
  - pending-request lifecycle;
  - PTY/process lifecycle;
  - bounded output/event replay;
  - client/server separation.
- Avoid: inheriting OpenCode's complete product/runtime architecture when a smaller adapter mechanism is sufficient.

### Zed

- Repository: `https://github.com/zed-industries/zed`
- Role: ACP/client architecture and developer-workspace UX reference; code donor only after exact license/path review.
- Wispral boundaries: `Agent Transport`, `Context Resolver`, `Session Event Journal`, `Surface Adapters`.
- Horizons: H2, H3, H4, H8.
- Status: `ARCHITECTURE_REFERENCE` / selective `DONOR_CANDIDATE`.
- Candidate mechanisms:
  - agent-thread/session organization;
  - project/worktree context boundaries;
  - attention/notification semantics;
  - ACP integration patterns.
- Avoid: editor/IDE architecture becoming Wispral's product shell.

### Backtalk

- Repository: `https://github.com/jaredrhod/backtalk`
- Role: agent-specific voice-layer reference.
- Boundaries: `Activation`, `Turn / Interaction`, `Agent Transport`.
- Horizons: H1, H2, H6.
- Status: `DONOR_CANDIDATE` pending exact revision/license/path qualification.

### Munder Difflin

- Repository: `https://github.com/chaitanyagiri/munder-difflin`
- Role: multi-agent lifecycle/human-gate/product-reference source.
- Horizons: H3, H8; category lessons only.
- Status: `PRODUCT_REFERENCE` / selective mechanism candidate.
- Avoid: office simulation or multi-agent fleet UX as founding Wispral scope.

### Speech-to-CLI

- Repository: `https://github.com/techempower-org/speech-to-cli`
- Role: voice-to-terminal interoperability prototype.
- Boundaries: `Turn / Interaction`, `Agent Transport`.
- Horizons: H1, H2, H9.
- Status: `DONOR_CANDIDATE` pending exact pin/rights/dependency review.

### Voice Interface Terminal Agent

- Repository: `https://github.com/vidhan66/voice-interface-terminal-agent`
- Role: voice-to-terminal prototype and failure-mode reference.
- Boundaries: `Turn / Interaction`, `Agent Transport`.
- Horizons: H1, H2, H9.
- Status: `DONOR_CANDIDATE` pending exact pin/rights/dependency review.

## B. Local STT and speech runtime sources

### Moonshine

- Repository: `https://github.com/moonshine-ai/moonshine`
- Qualified release/runtime revision: `234f60faa0eb388b01cdf7e60aca232af37aefda`
- Project/runtime license recorded by Wispral: MIT.
- Role: local streaming STT candidate, keyterms/context research.
- Boundary: `STT Provider`.
- Horizons: H0/H1 and later provider extensibility.
- Status: `QUALIFIED_EXISTING` under the active 000B research program.
- Exact product disposition must come from canonical bakeoff evidence, not this registry.

### whisper.cpp

- Repository: `https://github.com/ggml-org/whisper.cpp`
- Selected qualified release line: `b4938`.
- Selected runtime revision: `371b5a7561823ab2bb32142d2751e35e7534727b`.
- Project/runtime license recorded by Wispral: MIT.
- Role: local CPU-capable ASR / streaming adapter candidate.
- Boundary: `STT Provider`.
- Status: `QUALIFIED_EXISTING` under 000B.

### sherpa-onnx

- Repository: `https://github.com/k2-fsa/sherpa-onnx`
- Qualified release: `v1.13.7`.
- Qualified release revision: `917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e`.
- Project/runtime license recorded by Wispral: Apache-2.0.
- Role: cross-platform streaming ASR, Rust API, context/hotword-capable runtime depending on selected model.
- Boundary: `STT Provider`.
- Status: `QUALIFIED_EXISTING` under 000B.

### Parakeet / NVIDIA NeMo

- Source family: NVIDIA Parakeet / NeMo speech stack.
- Role: future local ASR quality/latency candidate, especially hardware-accelerated paths.
- Boundary: `STT Provider`.
- Horizons: H11 provider expansion after first product path is proven.
- Status: `IDENTITY_PIN_REQUIRED` for any direct donor use; no product adoption implied by external benchmark claims.

### Omnilingual ASR

- Source family: Omnilingual ASR.
- Role: broad-language fallback research.
- Boundary: `STT Provider`.
- Status: `IDENTITY_PIN_REQUIRED`, `DEFERRED` until language breadth becomes a named Wispral job.

### Omi medical STT / Google MedASR and other specialized ASR sources previously discussed

- Role: specialized-domain ASR research references.
- Status: `IDENTITY_PIN_REQUIRED`, `DEFERRED`.
- Rule: medical-domain performance is not automatically relevant to developer speech; these sources enter only if they solve a named Wispral job under WispralBench.

## C. Desktop capture, background lifecycle, hotkeys, and local-first UX

### OpenWhispr

- Repository: `https://github.com/OpenWhispr/openwhispr`
- Reviewed revision: `a9cf27b49bdcc9069922641ec39ac06d3483a125`.
- License observed: MIT.
- Role: strongest current desktop donor candidate.
- Boundaries: `Capture Runtime`, `Activation / Hotkey Runtime`, `Audio Conditioning`, `Turn / Interaction`, `Diagnostics / Distribution`.
- Horizons: H1, H9, H10, H12.
- Status: `DONOR_CANDIDATE`.
- High-value candidate mechanisms:
  - platform-specific global shortcut managers for GNOME/KDE/Hyprland/Windows/macOS;
  - modifier-only and right-side key handling;
  - deterministic shortcut fallbacks and failure reasons;
  - launch-at-login/tray lifecycle and stale executable repair;
  - system-audio permission/capture handling;
  - long-lived audio pipeline outside view-local UI lifecycle;
  - explicit capture session coordination and stop barriers;
  - echo/render-bleed analysis and mic gating as pure testable seams;
  - source-tagged transcript/session segments;
  - local/cloud provider routing patterns where relevant.
- Avoid importing cloud/team/note product scope into Wispral.

### VoiceStudio

- Repository: `https://github.com/debpalash/VoiceStudio`
- Reviewed revision: `53ff367c1fdde695f17673707cd46e2b27d41546`.
- Public application license observed: AGPL-3.0-only.
- Founder statement: separate permission is reported to exist for source use.
- Role: Rust/Tauri desktop and diagnostics donor/reference candidate.
- Boundaries: `Capture Runtime`, `Activation`, `Surface Adapters`, `Diagnostics / Distribution`, future provider governance.
- Horizons: H1, H11, H12.
- Status: `PERMISSION_REPORTED_DONOR_CANDIDATE`.
- High-value candidate mechanisms:
  - native Rust shortcut/capture boundary;
  - capture registration/readiness/acknowledgement race handling;
  - widget/shortcut lifecycle tests;
  - one-shot capability-style host-path authorization pattern;
  - engine acceptance by named job;
  - subprocess isolation for dependency-conflicting engines;
  - diagnostics/self-check/support-bundle patterns;
  - packaging/desktop lifecycle patterns.
- Import gate: before copying AGPL-covered implementation into a differently licensed Wispral tree, record the exact separate permission terms/rights basis used for that import.

### Meetily-Local

- Repository resolved from the previously discussed project name: `https://github.com/Hankanman/Meetily-Local`.
- Role: Linux/PipeWire/system-audio/local meeting capture reference and donor candidate.
- Boundaries: `Capture Runtime`, `Audio Conditioning`.
- Horizons: H0 platform feasibility, H9/H10 if later authorized.
- Status: `DONOR_CANDIDATE` pending exact revision/license/path qualification.
- Avoid: meeting-notes product scope.

### Circleback

- Product reference recorded separately in `docs/research/CIRCLEBACK_REFERENCE.md`.
- Role: conversation/context infrastructure, visible capture, interface convergence, source-scoped context.
- Horizons: H4, H11, H15.
- Status: `PRODUCT_REFERENCE`, not a current code donor.

### Wispr Flow, Superwhisper, Aqua

- Role: category/product references for low-friction activation, correction, technical vocabulary, onboarding, and cross-app ergonomics.
- Status: `PRODUCT_REFERENCE`.
- Rule: do not let generic text insertion become Wispral's core abstraction.

## D. VAD, endpointing, enhancement, duplex, diarization, and wake-word sources

### Silero VAD

- Source family: Silero VAD.
- Role: speech activity / endpoint observation candidate.
- Boundary: `Audio Conditioning`, `Turn / Interaction`.
- Horizon: H9.
- Status: `DONOR_CANDIDATE` after exact repository/revision/license pin.

### TEN VAD

- Source family: TEN VAD.
- Role: VAD/endpoint research candidate.
- Boundary: `Audio Conditioning`, `Turn / Interaction`.
- Horizon: H9.
- Status: `IDENTITY_PIN_REQUIRED`.

### DeepFilterNet

- Source family: DeepFilterNet.
- Role: optional local speech enhancement/denoise research.
- Boundary: `Audio Conditioning`.
- Horizons: H9/H10 only if measured benefit exceeds distortion/risk.
- Status: `DONOR_CANDIDATE` pending exact pin and speech-quality evaluation.

### RNNoise

- Source family: RNNoise.
- Role: optional denoise reference/candidate.
- Boundary: `Audio Conditioning`.
- Status: `DONOR_CANDIDATE` pending exact pin; must be compared against no-denoise baseline.

### pyannote

- Source family: pyannote audio/diarization.
- Role: diarization research reference, not core founding voice-control requirement.
- Horizon: H15 or explicit multi-speaker use case.
- Status: `DEFERRED`.

### MOSS Transcribe-Diarize

- Source family: MOSS Transcribe-Diarize.
- Role: combined transcription/diarization reference.
- Status: `IDENTITY_PIN_REQUIRED`, `DEFERRED`.

### openWakeWord

- Source family: openWakeWord.
- Role: optional wake-mode research.
- Boundary: `Activation / Turn`.
- Horizon: H9 only after PTT and visible capture state are proven.
- Status: `DONOR_CANDIDATE` pending exact pin/license/model review.

### OpenWhispr echo / bleed detector

- Repository/path family: `OpenWhispr/openwhispr`, `src/helpers/meetingEchoLeakDetector.js` and related pure helpers at the reviewed revision.
- Role: render-bleed measurement/classification reference and possible donor mechanism.
- Boundary: `Audio Conditioning`.
- Horizon: H10.
- Status: `DONOR_CANDIDATE`.
- Rule: measurement/classification must remain separate from suppression policy.

## E. Developer context, graph, memory, and repository intelligence

### Graphify

- Repository: `https://github.com/Graphify-Labs/graphify`
- Role: repository graph/index/invalidation/context-pack donor candidate and compatibility oracle.
- Boundary: `Context Resolver`.
- Horizons: H4, possibly H11.
- Status: `DONOR_CANDIDATE`.
- Candidate mechanisms:
  - graph storage/index structures;
  - incremental invalidation;
  - extraction/resolver fixtures;
  - context-pack construction;
  - validator patterns.
- Rule: do not import global hooks or MCP/product infrastructure merely because graph primitives are useful.

### code-graph-rag

- Repository: `https://github.com/vitali87/code-graph-rag`
- Role: code-graph retrieval/reference source.
- Boundary: `Context Resolver`.
- Horizon: H4.
- Status: `DONOR_CANDIDATE` pending exact revision/license/dependency qualification.
- Acceptance: measurable improvement in developer-entity resolution without unsafe false binding.

### External agent-memory/context projects previously discussed

- Role: possible future persistent context providers.
- Horizons: H4/H11.
- Status: `DEFERRED` unless a named source is separately pinned and a persistent-context specification proves utility/privacy/retention/correction/authority safety.
- Rule: memory can inform interpretation; it never silently authorizes action.

## F. Governance and execution-discipline references

### TheHalfMoon/SpecGrain

- Role: progressive task refinement and bounded executable-unit discipline.
- Status: `GOVERNANCE_REFERENCE` already reflected in Wispral repository rules.
- No runtime dependency required.

### TheHalfMoon/Diffcipline

- Role: proof-before-done, repository truth, risk-scaled verification, evidence discipline.
- Status: `GOVERNANCE_REFERENCE` already reflected in Wispral repository rules.
- No runtime dependency required.

## G. Research/product sources that must remain references unless separately promoted

### Berkeley Aside / think-aloud research

- Role: Command/Aside semantics, context value, visibility and authority-risk evidence.
- Horizon: H5.
- Status: `BENCHMARK_REFERENCE` / research evidence, not a code donor.

### Claude Code voice-mode issues and representative agent UX reports

- Role: demand/failure-mode evidence for PTT, pause handling, bidirectional feedback, IDE/cross-surface behavior, and think-aloud interaction.
- Status: `PRODUCT_REFERENCE` / research evidence.

## Source priority tiers

### Tier 0 — already active/qualified research

1. Moonshine
2. whisper.cpp
3. sherpa-onnx
4. ACP Rust SDK / registry

These must complete their current canonical evidence path before product selection.

### Tier 1 — highest-value implementation donors after H0 selects the first Grain

1. OpenWhispr — shortcut/background/capture/platform mechanisms
2. VoiceStudio — Rust desktop delivery/race/diagnostics mechanisms, subject to recorded permission basis
3. ACP Rust SDK — structured agent transport
4. OpenCode — permission/event/process mechanisms
5. Meetily-Local — Linux/system-audio capture patterns where needed

### Tier 2 — likely H4/H9/H10 accelerators

1. Graphify
2. code-graph-rag
3. Silero VAD
4. TEN VAD
5. DeepFilterNet / RNNoise
6. openWakeWord
7. OpenWhispr echo/bleed seams

### Tier 3 — deferred breadth/category sources

1. Parakeet/NeMo and other ASR families
2. Omnilingual ASR
3. specialized medical ASR sources
4. pyannote / MOSS diarization
5. broad meeting-note/product systems
6. generic persistent-memory platforms

Tier 3 is not lower quality; it is lower dependency priority for the founding coding-agent thesis.

## Promotion checklist

Before any `DONOR_CANDIDATE` becomes `QUALIFIED_DONOR`, the task must answer:

- [ ] Exact upstream repository and immutable commit pinned.
- [ ] Exact source paths pinned.
- [ ] Source/license/permission basis recorded.
- [ ] Required copyright/notices recorded.
- [ ] Transitive runtime dependencies enumerated.
- [ ] Model/data/binary assets enumerated separately.
- [ ] Security-sensitive behavior identified.
- [ ] Platform assumptions identified.
- [ ] Wispral job named.
- [ ] Wispral architecture boundary named.
- [ ] Minimal adaptation surface selected.
- [ ] Deterministic or bounded acceptance test defined.
- [ ] Fallback/removal behavior defined.
- [ ] No unrelated donor workflow/telemetry/cloud/update subsystem imported.
- [ ] No external benchmark claim promoted to a Wispral claim.
- [ ] Independent review completed before canonical adoption.

## Current conclusion

The source pool is broad enough that lack of implementation examples should not be Wispral's bottleneck. The bottleneck should deliberately remain **evidence-based selection and clean integration**.

The highest-leverage design choice is to keep Wispral's contracts small and owned by Wispral, then use this registry to select the best existing mechanism for each proven job instead of rebuilding everything or inheriting any one donor application's architecture.