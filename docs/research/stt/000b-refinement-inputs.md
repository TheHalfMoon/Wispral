# Specification 000B — Refinement Inputs

**Status:** research input record, not benchmark evidence  
**Recorded:** 2026-09-01  
**Wispral canonical base:** `99dd6290ee01ce566d32b92df6d469b66b56520a`

This document records current external facts used to shape Specification 000B. Upstream documentation is not Wispral behavioral evidence. All candidate behavior remains `DOCUMENTED_NOT_OBSERVED` until a Wispral attempt reproduces it.

## Canonical Wispral inputs

- `AGENTS.md`
- `CONSTITUTION.md`
- `docs/canonical/ARCHITECTURE_INVARIANTS.md`
- `docs/benchmarks/WISPRALBENCH.md`
- `specs/000-founding-research/spec.md`
- `specs/000-founding-research/tasks.md`
- `specs/CURRENT.md`
- verified Specification 000A evidence and closeout

The most relevant existing constraints are:

- speech engines must remain replaceable;
- repository context must be bounded and inspectable;
- benchmark instrumentation is part of architecture;
- comparative accuracy/latency claims require reproducible public evidence;
- product code remains unauthorized until 000G selects the first product Grain.

## Candidate family 1 — Moonshine Voice

### Pin observed during refinement

- Repository: `moonshine-ai/moonshine`
- Release: `v0.1.5`
- Release tag object: `bf6ae1590d0928fd704772d0e80d6fef39424be8`
- Release commit: `234f60faa0eb388b01cdf7e60aca232af37aefda`
- Runtime/project license: MIT

### Upstream-documented current model surface

At the pinned revision, Moonshine documents English streaming models:

| Architecture | Parameters | Upstream listed English aggregate WER | License |
| --- | ---: | ---: | --- |
| Tiny Streaming | 34M | 12.00% | MIT |
| Small Streaming | 123M | 7.84% | MIT |
| Medium Streaming | 245M | 6.65% | MIT |

The same current model table also lists an Arabic Tiny Streaming model under MIT. That fact does not establish Wispral Arabic support and does not make Arabic a mandatory 000B ranking panel.

Moonshine's accuracy documentation distinguishes floating-point paper numbers from the quantized `.ort` models shipped by its runtime. 000B therefore must benchmark the exact artifact actually executed, not quote paper or leaderboard numbers as though they describe Wispral's runtime configuration.

### Upstream-documented streaming/context behavior

Moonshine currently describes its toolkit as on-device and optimized for live streaming. Its domain-customization documentation exposes streaming-only runtime context mechanisms:

- `context`: supply a passage and deterministically extract uncommon terms;
- `keyterms`: supply explicit words or multi-word phrases;
- both can be updated while audio is streaming;
- `keyterm_boost` controls a term-accuracy versus collateral-error tradeoff.

Moonshine publishes its own measurements for keyterm uplift, false alarms, list-size effects, and latency. Those values are upstream evidence only and MUST NOT be represented as Wispral results.

### 000B implication

Moonshine is mandatory for candidate qualification because it combines a current local streaming path with a current native context-bias mechanism directly relevant to WB-ENTITY/WB-CONTEXT.

Native context bias must be a secondary backend-specific condition. It cannot be enabled in the unbiased C0 head-to-head comparison.

## Candidate family 2 — whisper.cpp

### Pin observed during refinement

- Repository: `ggml-org/whisper.cpp`
- Current source revision observed: `eacbd8234c6654cdbf2c377f72b2106875479bdc`
- Latest GitHub binary release observed: `b4938`, targeting source revision `371b5a7561823ab2bb32142d2751e35e7534727b`
- Project license: MIT

The source revision and latest binary release are not the same revision. 000B1 must choose and pin one exact runtime revision for an execution attempt rather than silently mixing source and release artifacts.

### Upstream-documented model surface

The pinned source documents converted OpenAI Whisper model artifacts including:

| Model | Disk size listed upstream | SHA listed upstream |
| --- | ---: | --- |
| `tiny.en` | 75 MiB | `c78c86eb1a8faa21b369bcd33207cc90d64ae9df` |
| `base.en` | 142 MiB | `137c40403d78fd54d454da0f9bd998f78703390c` |
| `small.en` | 466 MiB | `db8a495a91d927739e50b3fc1cc4c6b8f6c2d022` |
| `large-v3-turbo-q5_0` | 547 MiB | `e050f7970618a659205450ad97eb95a18d69c9ee` |

The table is an upstream artifact list, not an authorization to choose the largest model after seeing results. Exact model selection must be frozen before primary test decoding.

### Upstream-documented real-time behavior

`examples/stream/README.md` explicitly calls `whisper-stream` a **naive real-time inference example**. The documented default samples microphone audio every 500 ms and runs transcription continuously. Its sliding-window mode with `--step 0` waits for speech activity and transcribes a bounded recent window after silence.

Therefore 000B must not equate the whisper.cpp demonstration path with a native incremental streaming recognizer before behavioral qualification. Its final streaming-semantics classification may be `CHUNKED_REDECODE` or another state only after the exact tested integration is observed.

### Upstream-documented context surface

The whisper.cpp API exposes `initial_prompt`/prompt tokens and `carry_initial_prompt`; examples use prompt context for constrained voice-command domains. This provides a possible backend-native C2 condition. It is not equivalent to Moonshine keyterm bias and must not be folded into C0.

## Candidate family 3 — sherpa-onnx

### Pin observed during refinement

- Repository: `k2-fsa/sherpa-onnx`
- Current release: `v1.13.7`
- Release/current revision: `917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e`
- Runtime/project license: Apache-2.0

### Upstream-documented platform/runtime surface

The pinned README states that sherpa-onnx supports local streaming and non-streaming ASR across Linux, macOS, Windows, mobile, WebAssembly, and multiple architectures, and exposes APIs including Rust.

This is useful future integration context but remains documentation, not a Wispral portability claim.

### Candidate English online model

Current sherpa-onnx documentation/examples repeatedly reference `sherpa-onnx-streaming-zipformer-en-2023-06-26` for English online recognition. The model card is Apache-2.0 and describes a LibriSpeech-trained English streaming Zipformer. Current runtime examples use it in real-time microphone/online recognizer paths.

The model is a **candidate for qualification**, not yet the frozen 000B model. B1 must record exact model files/digests/configuration before an execution attempt.

### Upstream-documented native bias surface

The current repository contains streaming Zipformer hotword examples/APIs. If the exact B1-qualified model/configuration supports them, hotwords may become a secondary C2 condition. They are not enabled in C0.

## Why these three families are mandatory for B1 qualification

Together they exercise materially different local architectures:

- Moonshine: current streaming-first ASR with explicit runtime keyterms/context;
- whisper.cpp: widely deployed local Whisper inference with a documented naive/sliding real-time example and prompt-context surface;
- sherpa-onnx: current online recognizer framework with native streaming model families, broad native bindings, and hotword mechanisms.

This diversity is more informative than comparing several wrappers around the same Whisper model family.

## Configuration fairness problem

A model-family comparison is not automatically fair when configurations have different parameter counts, artifact sizes, quantization, memory use, or acceleration.

000B therefore treats the unit of comparison as an **exact local product configuration**, not a brand name. B1 must define a bounded product envelope and, if needed, a small number of explicit resource tiers before freezing model artifacts.

The benchmark may produce multiple non-dominated configurations rather than a single winner.

## Context fairness problem

Native context mechanisms are not equivalent:

- Moonshine keyterms/context biases decoder paths;
- whisper.cpp prompt context conditions the decoder differently;
- sherpa-onnx may expose hotword mechanisms depending on the exact online model/configuration.

Therefore:

1. C0 compares every candidate with repository/test-specific context disabled.
2. C1 applies one deterministic engine-agnostic repository resolver to frozen C0 transcripts.
3. C2 evaluates backend-native context features only as within-backend uplift/degradation relative to that backend's C0.

No C2 result may replace the C0 raw STT result in cross-backend ranking.

## Human-audio requirement

The founding WispralBench contract already requires consent and redistribution rules for recorded human audio. B1 should strengthen that into a readiness gate: synthetic/TTS audio is acceptable for smoke tests but cannot be the sole evidence for ranking human developer-speech recognition.

If a redistributable human developer-speech panel is unavailable, the primary bakeoff must remain blocked rather than creating a public comparative claim from synthetic voices.

## Performance-environment requirement

GitHub-hosted runners are useful for reproducibility and smoke checks but are shared, variable hardware. 000B must not use their timings to support general latency/resource superiority claims.

A performance panel needs explicitly identified hardware, OS, runtime configuration, power/acceleration state where material, repetitions, and run-level outputs. Accuracy evidence may use a broader reproducible environment when hardware does not materially change decoding output, subject to exact configuration records.

## Current non-decisions

This refinement does **not** establish:

- a winning STT runtime;
- a winning model size;
- an approved permanent dependency;
- a production Rust binding;
- English or Arabic product support;
- a latency target being met;
- repository-context uplift;
- a public benchmark score;
- superiority over Wispr Flow, Superwhisper, Aqua, or another product;
- permission to execute the primary 000B bakeoff.

Those require later canonical specification/readiness/evidence gates.