# Specification 000B1 — Candidate Qualification Report

**Status:** preregistration evidence; no primary benchmark executed  
**Recorded:** 2026-09-01  
**Canonical Wispral base:** `6b5696a6becc360948282712cc9339df9cb3a67c`  
**Branch:** `research/000b1-benchmark-candidate-qualification`

## Scope

This report implements the research-only qualification portion of Specification 000B1. It records current authority, freezes a result-independent product configuration envelope, identifies exact candidate configurations, preserves missing integrity/runtime evidence, and establishes the entry conditions that a later 000B2 attempt must satisfy.

This report does **not** contain developer-speech accuracy results, comparative rankings, product support claims, controlled latency results, or production dependency selections.

## Readiness result

000B1 readiness is `PASS` for preregistration work only.

The readiness check found:

- Specification 000B and 000B1 are canonical on `main` at `6b5696a6becc360948282712cc9339df9cb3a67c`;
- Moonshine Voice, whisper.cpp, and sherpa-onnx source/release metadata remain publicly accessible;
- runtime/model licensing and provenance are sufficiently accessible to define exact preregistration candidates;
- B1 can complete without decoding the primary benchmark split;
- no task requires secrets, proprietary benchmark data, paid inference, or a permanent product dependency;
- research tooling can remain isolated from the future production architecture;
- no smoke decode is required to define the benchmark contract.

This readiness result does not authorize 000B2 and does not establish that any candidate is operationally supported by Wispral.

## Revalidated source pins

### Moonshine Voice

- repository: `moonshine-ai/moonshine`
- release: `v0.1.5`
- release commit: `234f60faa0eb388b01cdf7e60aca232af37aefda`
- project/runtime license: MIT
- current English streaming asset directory used by the pinned runtime: `quantized_26_08_21`
- official asset mirror: `moonshine-ai/moonshine-voice-assets`
- English STT asset license: MIT
- pinned runtime catalog records exact URLs, byte sizes, and CRC32C per file; the official mirror additionally records MD5 and CRC32C in `FILES.tsv`.

The current `quantized_26_08_21` runtime asset inventory does not expose SHA-256 for every selected file in the evidence available during this qualification. B1 therefore preserves a fail-closed distinction:

- the exact path set and upstream size/MD5/CRC32C metadata are sufficient to preregister which artifacts are intended;
- the B2 attempt manifest MUST capture SHA-256 for every materialized Moonshine payload file before primary test decoding;
- a historical SHA-256 from an older Moonshine asset revision MUST NOT be substituted for a current `quantized_26_08_21` file.

### whisper.cpp

- repository: `ggml-org/whisper.cpp`
- current source observation: `eacbd8234c6654cdbf2c377f72b2106875479bdc`
- selected runtime pin: GitHub release `b4938`, targeting source revision `371b5a7561823ab2bb32142d2751e35e7534727b`
- project/runtime license: MIT
- converted model source: `ggerganov/whisper.cpp`
- converted model license: MIT

The release is selected instead of mutable `master` to make the later attempt independently reproducible. Current `master` remains an observation only.

Selected converted model artifacts:

- Compact: `ggml-base.en.bin`, exact size `147964211` bytes, SHA-256 `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`;
- Balanced: `ggml-small.en.bin`, exact size `487614201` bytes, SHA-256 `c6138d6d58ecc8322097e0f987c32f1be8bb0a18532a3f88f734d1bbf9c41e5d`.

The shorter hashes published in the converted-model README are retained only as upstream legacy identifiers. B2 must verify the full SHA-256 values above against the materialized payloads.

### sherpa-onnx

- repository: `k2-fsa/sherpa-onnx`
- release: `v1.13.7`
- release commit: `917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e`
- project/runtime license: Apache-2.0
- model repository: `csukuangfj/sherpa-onnx-streaming-zipformer-en-2023-06-26`
- current model repository head observed: `672fbf1b30579d6585301139bb363f42a0ad4a24`
- selected ONNX artifact revision: `6037ea07e3abfe599ad00d418968bcf9656e7472`
- model license: Apache-2.0
- selected streaming configuration: chunk size 16, left-context frames 128

The selected compact INT8 and balanced FP32 encoder/decoder/joiner ONNX files have pinned SHA-256 values in `research/000b1/qualified-candidates.json`. `bpe.model` is also SHA-256 pinned. The small tracked `tokens.txt` remains bound by the model repository revision but its attempt-time SHA-256 is mandatory before B2 freeze.

## Product configuration envelope

The envelope is frozen from local product constraints before any Wispral primary test result exists.

### Common eligibility

Every primary C0 configuration must:

- run locally after artifact acquisition;
- have a CPU-only baseline path;
- use an English transcription path;
- have pinnable runtime/model licensing and provenance;
- disable repository/test-specific context for C0;
- remain a research dependency rather than a production dependency;
- fit one declared model-payload tier.

### Resource tiers

`COMPACT`

- primary C0 model payload: `<= 160 MiB` (`167772160` bytes)

`BALANCED`

- primary C0 model payload: `> 160 MiB` and `<= 512 MiB` (`536870912` bytes)

These are distribution/resource ceilings, not accuracy assumptions. The 512 MiB cap intentionally excludes multi-GiB first-pass configurations from the founding local terminal benchmark.

### Mechanical family selection

For each candidate family and tier, select at most one configuration: the **largest qualifying English configuration that does not exceed the tier ceiling**, based only on pre-result artifact metadata.

This rule spends the declared resource budget without selecting models from observed Wispral accuracy. A family with no configuration inside a tier is absent from that tier; the tier is not moved to admit it.

Precision is part of the exact configuration. Prefer the upstream default/full-precision artifact when it fits the tier. An upstream quantized artifact is eligible when it is the runtime-distributed default or when the full-precision variant belongs to a different tier.

## Preregistered candidate cells

### Compact

- Moonshine Voice: `small-streaming-en/quantized_26_08_21`, `142300974` primary C0 bytes;
- whisper.cpp: `ggml-base.en.bin`, `147964211` bytes;
- sherpa-onnx: Zipformer chunk-16/left-128 INT8, `72899649` bytes including decoder, encoder, joiner, `bpe.model`, and `tokens.txt` inventory allowance.

### Balanced

- Moonshine Voice: `medium-streaming-en/quantized_26_08_21`, `269141623` primary C0 bytes;
- whisper.cpp: `ggml-small.en.bin`, `487614201` bytes;
- sherpa-onnx: Zipformer chunk-16/left-128 FP32, `265495984` bytes including decoder, encoder, joiner, `bpe.model`, and `tokens.txt` inventory allowance.

Moonshine's attention decoder is excluded from the primary C0 payload because word timestamps are disabled for the base accuracy condition. Enabling a timestamp-specific artifact later would be a separately declared measurement condition.

## C0 context freeze

For all six preregistered cells, repository/test-specific bias is OFF.

At minimum:

- Moonshine `context` OFF and `keyterms` OFF;
- whisper.cpp `initial_prompt` empty/OFF and prompt carryover OFF;
- sherpa-onnx hotwords/context bias OFF;
- no grammar or expected-answer vocabulary injection;
- no target-utterance-specific decoding changes.

Backend-native context belongs only to later C2 within-backend uplift/degradation evidence.

## Streaming semantics

Current upstream behavior remains `DOCUMENTED_NOT_OBSERVED` until a Wispral execution reproduces it.

The later attempt may classify a tested integration only as:

- `NATIVE_INCREMENTAL`;
- `CHUNKED_REDECODE`;
- `BATCH_ONLY`;
- `UNKNOWN`.

The classification must be derived from raw backend event/decode behavior, not marketing terminology.

## Qualification smoke

B106 disposition for this evidence package: `NOT_RUN_NOT_REQUIRED`.

No runtime/model decode is claimed. B1's contract and provenance work can complete without a smoke decode. Before a B2 primary attempt freezes, each selected configuration must either pass a bounded non-comparative materialization/install/load/decode smoke on license-clear non-primary audio or have an explicit canonical waiver explaining why the operational qualification is unnecessary.

A later smoke PASS will mean only that the exact path installed/loaded/decoded its smoke contract. It will not establish accuracy, streaming quality, or comparative performance.

## Negative evidence and unresolved B2 gates

The following are intentionally unresolved and MUST NOT be promoted to PASS:

1. Current Moonshine `quantized_26_08_21` payload SHA-256 values have not yet been captured for every selected file.
2. sherpa-onnx `tokens.txt` attempt-time SHA-256 has not yet been captured.
3. No candidate has been operationally smoke-qualified by this B1 evidence package.
4. No human developer-speech corpus authority, consent record, retention decision, redistribution permission, or frozen primary manifest exists yet.
5. No controlled hardware performance environment has been qualified.
6. No primary transcript has been decoded and no comparative metric has been observed.

These gaps do not block the B1 preregistration contract. They do block any B2 primary attempt until its own entry gate is satisfied.

## B2 materialization gate

Before any primary B2 decoding, the attempt must prove all of the following:

- exact runtime/source pins still resolve;
- exact payload byte counts are recorded after materialization;
- SHA-256 is recorded and verified for every model/tokenizer/config payload file;
- licenses/provenance are rechecked for the exact materialized artifacts;
- C0 settings are frozen and repository-specific bias is OFF;
- a bounded non-primary smoke has passed or a canonical waiver exists;
- human developer-speech authority and corpus manifests satisfy the contract;
- scorer/preprocessing/environment revisions are frozen;
- the attempt manifest validates before the primary test split is decoded.

If any required human-audio authority is absent, the primary developer-speech ranking is `BLOCKED_EXTERNAL`. Synthetic/TTS media cannot substitute for that ranking.

## Explicit non-claims

This report does not establish:

- a winning STT engine or model;
- any developer-speech accuracy result;
- any latency/resource superiority result;
- native incremental streaming support for a tested Wispral integration;
- repository-context uplift;
- English or Arabic product support;
- production compatibility with any candidate;
- a permanent Rust/native dependency;
- B2 readiness.

## Evidence disposition

B101–B105 can be satisfied by this report plus the machine-readable candidate manifest and benchmark contract once exact-head verification succeeds. B106 is intentionally not run. B107–B118 are governed by the companion preregistration contract and schemas. B119 is recorded separately as an adversarial preregistration review.

B120 remains out of scope for this implementation/evidence PR. Canonical task completion and B1 disposition must be reconciled only after merge and post-merge proof.