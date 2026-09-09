# Wispral Source Universe Implementation Plan

**Status:** implementation-ready planning; non-executable until canonical authority permits  
**Prepared:** 2026-09-07  
**Source universe:** `docs/research/source-universe-v2.json`  
**Permission attestation:** `docs/research/SOURCE_PERMISSION_ATTESTATION.md`  
**Architecture strategy:** `docs/research/SOURCE_ADOPTION_STRATEGY.md`  
**Existing gates:** `docs/research/source-adoption-gates.json`

## Purpose

This document converts the complete Wispral source universe into dependency-ordered implementation packets.

It does not authorize implementation. It defines exactly what should happen once the canonical roadmap opens the corresponding product Grain.

The implementation objective is not to combine whole donor applications. Wispral should own the contracts, state model, authority model, event model, and acceptance tests while selectively adopting the strongest mechanisms from permitted sources.

## Global implementation rule

Every donor import follows this pipeline:

```text
named Wispral job
  -> exact donor identity
  -> exact revision and paths
  -> rights/provenance package
  -> dependency and asset inventory
  -> security/platform qualification
  -> minimum transplant decision
  -> Wispral-owned contract
  -> isolated adaptation
  -> deterministic tests
  -> benchmark/evidence capture
  -> independent review
  -> guarded merge
```

A donor is never selected merely because permission exists.

## Source selection policy

For every named job, compare candidates in this order:

1. existing Wispral mechanism, if sufficient;
2. canonical protocol/SDK dependency, where interoperability requires it;
3. smallest direct donor transplant;
4. adapted transplant behind a Wispral-owned contract;
5. clean Wispral reimplementation informed by donor behavior;
6. defer the feature when none of the above can satisfy the acceptance gates.

The winner must minimize hidden state, dependency burden, platform coupling, and future replacement cost.

## Packet P0 — Source Lab and Provenance Runtime

### Goal

Create the repository machinery required to import donor code safely and repeatably.

### Deliverables

- source provenance record schema;
- donor snapshot manifest format;
- exact upstream revision/path/hash capture;
- permission-basis field supporting `FOUNDER_ATTESTED_BROAD_SOURCE_USE_PERMISSION`;
- public-license and notice capture;
- transitive dependency inventory;
- model/data/binary asset inventory;
- source-to-Wispral destination mapping;
- patch/delta summary;
- security/platform notes;
- attribution output;
- import acceptance-test list;
- rollback/removal plan.

### Acceptance

No direct donor code may enter product paths until P0 exists and can produce a complete provenance package for a fixture donor.

## Packet P1 — Capture and Activation Kernel

### Named jobs

- reliable explicit push-to-talk;
- microphone selection and device-loss recovery;
- global shortcut registration with visible failure reasons;
- deterministic press/release/toggle state;
- background lifecycle without invisible ambient authority.

### Primary donors

- `OpenWhispr/openwhispr`;
- `debpalash/VoiceStudio`;
- `Starmel/OpenSuperWhisper`;
- `Hankanman/Meetily-Local` for Linux/PipeWire/system-audio evidence;
- platform-native Rust libraries selected by qualification.

### Mechanisms to compare

- shortcut registration and fallback;
- modifier-only / right-side modifier semantics;
- mouse-button PTT on supported platforms;
- capture readiness acknowledgement;
- device hot-plug handling;
- stop barriers and capture-session ownership;
- tray/background lifecycle;
- launch-at-login repair only if separately authorized.

### Wispral-owned contracts

- `CaptureDevice`;
- `CaptureSession`;
- `ActivationBinding`;
- `ActivationEvent`;
- `CaptureState`;
- `CaptureCapabilityReport`.

### Exit gate

PTT lifecycle must be deterministic under repeated start/stop, device loss, shortcut conflict, cancellation, and application-focus changes on each supported platform.

## Packet P2 — Audio Conditioning and Turn Observation

### Named jobs

- deterministic framing/resampling;
- optional VAD/endpoint observations;
- future denoise/echo/bleed measurement;
- observable turn state without hidden execution authority.

### Candidate sources

- Silero VAD;
- TEN VAD;
- DeepFilterNet;
- RNNoise;
- OpenWhispr echo/bleed mechanisms;
- openWakeWord only for a later explicit wake-mode Grain;
- pyannote and MOSS Transcribe-Diarize only for future multi-speaker jobs.

### Rule

Measurement must remain separate from policy. VAD, denoise, echo detection, wake-word detection, and diarization cannot silently change authorization semantics.

### Exit gate

Each enabled conditioning mechanism must beat the no-conditioning baseline on its named metric without unacceptable transcript distortion or false activation cost.

## Packet P3 — STT Provider Contract and Selected Runtime

### Canonical research inputs

- `moonshine-ai/moonshine`;
- `ggml-org/whisper.cpp`;
- `k2-fsa/sherpa-onnx`.

### Future candidates

- Parakeet/NeMo;
- Omnilingual ASR;
- specialized ASR only when a named developer-speech job exists.

### Wispral-owned contract

A provider must expose:

- exact runtime/model identity;
- session lifecycle;
- partial/final transcript events when supported;
- cancellation;
- optional context/hotword capability advertisement;
- deterministic error classes;
- diagnostic timing/resource events;
- no provider-specific type leakage beyond the adapter.

### Exit gate

Product adoption follows canonical 000B evidence. External donor benchmarks cannot override Wispral results.

## Packet P4 — Agent Transport and Harness Kernel

### Goal

Separate **agent transport compatibility** from **agent execution/harness mechanics**.

ACP remains the structured transport baseline where supported. Harness sources may contribute internal execution-loop, tool, sandbox, tracing, retry, and evaluation mechanisms without replacing Wispral's transport and authority model.

### Structured transport sources

- `agentclientprotocol/rust-sdk`;
- `agentclientprotocol/registry`;
- `anomalyco/opencode`;
- `zed-industries/zed`;
- `portable-pty` family for separately qualified fallback.

### Harness mechanism sources

- `deepseek-ai/deepseek-harness`;
- `HKUDS/HELIX`;
- `HKUDS/OpenHarness`;
- `SWE-agent/mini-swe-agent`;
- `SWE-agent/SWE-agent`;
- `earendil-works/pi`;
- `OpenHands/OpenHands`;
- `OpenHands/software-agent-sdk`;
- `openai/openai-agents-python`;
- `langchain-ai/deepagents`;
- `SAIL-Research-Lab/cheetahclaws`;
- `DeepExperience/Harness-R1`;
- `MLEARNER701/ouroboros-harness`;
- `harness/harness`;
- `harness/harness-ai`.

### Benchmark/research references

- `Qihoo360/harness-bench`;
- `china-qijizhifeng/agentic-harness-engineering`;
- One Recipe, Many Harnesses;
- Scaffold Effects;
- SBCO;
- Co-Harness;
- Proof-Carrying Agent Actions;
- Agent Safety Should Be a Runtime Contract;
- Code as Agent Harness.

### Identity-blocked references

- Cordis;
- Harbor.

These remain non-importable until their exact original identities are reconfirmed.

### Mechanisms to compare

- minimal agent loop;
- typed tool invocation;
- tool result/error envelopes;
- context budgeting/compaction;
- checkpoint/retry semantics;
- sandbox boundaries;
- cancellation propagation;
- approval interrupts;
- subagent delegation;
- event/tracing model;
- proof/evidence attached to consequential actions;
- evaluation adapter separation.

### Wispral-owned contracts

- `AgentTransport`;
- `AgentSession`;
- `HarnessRunner`;
- `ToolRequest` / `ToolResult`;
- `CancellationToken` / `CancellationAck`;
- `ApprovalRequest` / `ApprovalDecision`;
- `SandboxCapability`;
- `HarnessEvent`.

### Critical rule

Do not import a donor's complete agent framework simply because a useful tool loop exists. The implementation packet should transplant the smallest mechanism that closes a measured Wispral gap.

## Packet P5 — Trust, Policy, and Proof-Carrying Actions

### Sources

- ACP permission semantics;
- OpenCode permission/request state;
- OpenHands sandbox/action boundaries;
- OpenAI Agents SDK tracing/tool semantics as reference;
- Proof-Carrying Agent Actions;
- Agent Safety Should Be a Runtime Contract;
- Wispral threat model;
- Diffcipline evidence discipline.

### Required semantic layers

```text
heard speech
  -> raw transcript
  -> resolved entities
  -> interpreted intent
  -> requested agent action
  -> policy decision
  -> transport/tool request
  -> acknowledgement
  -> result/evidence
```

No layer may be skipped merely because a donor framework combines them.

### Exit gate

Consequential actions must be explainable from typed events and must preserve exactly where human authority entered the chain.

## Packet P6 — Developer Context Resolver

### Primary donors

- `Graphify-Labs/graphify`;
- `vitali87/code-graph-rag`;
- selective Zed project/worktree patterns;
- future memory/context providers only after separate qualification.

### Jobs

- file/symbol/package/branch/test resolution;
- incremental invalidation;
- source-scoped context packs;
- recency and provenance;
- ambiguity preservation;
- context capture-time identity.

### Rule

Retrieved context can strengthen interpretation evidence. It cannot silently authorize actions.

### Exit gate

WispralBench must show measurable developer-entity resolution gain without unacceptable false binding.

## Packet P7 — Session Event Journal, Cancellation, and Interruption

### Sources

- OpenCode events;
- Zed thread/session organization;
- Pi tool/event patterns;
- OpenHands runtime events;
- OpenWhispr session segmentation;
- VoiceStudio diagnostics/race handling;
- harness sources with explicit cancellation/checkpoint semantics.

### Required event identities

- capture start/stop;
- speech onset/end;
- transcript revision;
- context snapshot;
- interpretation;
- approval request/decision;
- tool/agent dispatch;
- cancellation request;
- cancellation acknowledgement;
- stale-output boundary;
- result/error;
- correction/retry.

### Exit gate

A complete interrupted turn must be reconstructible deterministically from the journal without relying on UI state.

## Packet P8 — Surface Adapters and Visible Background Operation

### Sources/references

- VoiceStudio Tauri/native boundary;
- OpenWhispr desktop lifecycle;
- OpenSuperWhisper activation UX;
- ACP client patterns;
- Superwhisper, Wispr Flow, Aqua, Circleback as product references only.

### Rule

CLI/terminal remains the founding surface. Tray/overlay surfaces may expose the same semantic state but cannot become authority themselves.

### Exit gate

Recording, context capture, waiting, cancellation, approval, and failure state must always be visible through at least one non-voice surface.

## Packet P9 — Diagnostics, Packaging, and Supply Chain

### Sources

- VoiceStudio diagnostics/packaging patterns;
- OpenWhispr platform/autostart handling;
- Harness platform observability ideas where useful;
- project-native Rust/package tooling.

### Required outputs

- capability/self-check report;
- microphone/shortcut/transport health;
- runtime/model integrity;
- network/cloud-path disclosure;
- safe support bundle;
- source provenance manifest;
- SBOM/dependency inventory;
- update/rollback evidence when distribution is authorized.

## Packet P10 — Source/Harness Evaluation Layer

### Sources/references

- Harness-Bench;
- Agentic Harness Engineering;
- SWE-agent evaluation patterns;
- OpenHands benchmark interfaces;
- OpenHarness evaluation adapters;
- DeepSeek Harness evaluation patterns;
- Harness-R1 research;
- google-research/timesfm only if future runtime telemetry forecasting/modeling becomes a separately named job.

### Goal

Build evaluation adapters that compare mechanisms rather than brands.

Example dimensions:

- task success;
- tool-call correctness;
- cancellation latency;
- permission correctness;
- context efficiency;
- recovery after tool failure;
- sandbox escapes / forbidden effects;
- event completeness;
- cross-agent portability;
- dependency/runtime cost.

External scores are experiment-design inputs only. Wispral claims require Wispral evidence.

## Source quarantine rules

Before any donor code executes in a trusted Wispral environment:

- clone/fetch at exact revision into a quarantine workspace;
- do not run donor CI;
- do not expose repository secrets;
- inventory network calls, package scripts, hooks, binaries, submodules, and generated code;
- verify expected repository identity;
- inspect licenses/notices and transitive assets;
- prohibit silent telemetry/cloud fallback;
- run only the minimum bounded qualification command needed by the active task.

## Transplant shape

Every code-carrying adoption should prefer a two-commit provenance shape:

1. **donor transplant commit** — minimum faithful source adaptation with explicit origin/path/hash record;
2. **Wispral adaptation commit** — contract integration, naming, error model, tests, and policy hardening.

When exact source preservation would create unsafe or unnecessary coupling, a clean reimplementation may be preferable, but the source behavior and provenance references must still be recorded.

## Ready-to-implement definition

A packet is implementation-ready when:

- canonical authority opens the corresponding Grain;
- every selected donor has exact repository + revision + source paths;
- permission/provenance package is complete;
- transitive assets are classified;
- the Wispral-owned interface is frozen for the packet;
- acceptance tests are written before transplant;
- platform/security failure cases are enumerated;
- the implementation diff can remain bounded to the named job.

The planning artifacts in PR #73 satisfy the design/dependency/source-universe portion of this definition. They intentionally do not satisfy canonical implementation authority.

## Current repository disposition

Keep this plan in the planning-only source-adoption branch while active 000B2 recovery/reconciliation work requires canonical-main stability.

When canonical governance permits source adoption:

1. recreate or reconcile these planning artifacts from then-current `main`;
2. re-read canonical authority;
3. select only the first authorized packet;
4. pin exact donor revisions/paths for that packet;
5. create acceptance tests and provenance package;
6. implement forward-only through normal exact-head CI/review/merge governance.

Do not merge this planning PR merely to make the documents visible on `main` if doing so would violate the active research frontier.
