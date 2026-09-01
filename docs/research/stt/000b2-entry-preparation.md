# 000B2 Entry-Preparation Evidence

**Specification:** `000B-stt-entity-bakeoff` successor `000B2-unbiased-stt-bakeoff`  
**Canonical starting main:** `db0a10ab4c9ee2436a5b921d0ff8af96f58cef38`  
**Current disposition:** `BLOCKED_EXTERNAL`  
**Primary test decoding performed:** `NO`  
**Human speech used in entry preparation:** `NO`

## Purpose

This record documents bounded, non-primary work that removes technical entry blockers for a future 000B2 attempt without converting missing human-recording authority into repository-owner approval and without generating benchmark accuracy, ranking, performance, or product claims.

It does not authorize a primary B2 attempt.

## Artifact materialization

The B1 preregistration intentionally left attempt-time SHA-256 values pending for Moonshine payloads and `sherpa-onnx` `tokens.txt`.

The first exact-source materialization failed closed because the historical B1 registry recorded `tokens.txt` as 5050 bytes while the exact pinned source revision returned 5048 bytes. The historical B1 record remains unchanged. `research/000b2-entry/artifact-size-amendment.json` records the factual pre-attempt correction and projects 5048 bytes into B2 entry evidence only.

A fresh materialization then succeeded:

- workflow: `000B2 Entry Materialization`;
- run id: `33519579512`;
- evidence head: `3d4325b7c9b13e6696326f3d2c8a6cfe501d9e12`;
- durable evidence: `research/000b2-entry/materialized-artifacts.json`;
- live/committed comparison verifier: `research/000b2-entry/verify_materialization.py`.

The observed `sherpa-onnx` `tokens.txt` identity is:

- size: `5048` bytes;
- SHA-256: `49e3c2646595fd907228b3c6787069658f67b17377c60aeb8619c4551b2316fb`.

All pending Moonshine payload SHA-256 values were also materialized. Model payloads are not committed to Wispral.

## Bounded operational qualification

The operational smoke uses one deterministic synthetic **non-speech** PCM WAV. It exists only to demonstrate that each exact candidate cell can load its pinned runtime/artifacts and complete one bounded decode path.

The input is not TTS and is not eligible for primary ranking.

Successful evidence:

- workflow: `000B2 Operational Smoke`;
- run id: `33522881549`;
- run number: `2`;
- evidence head: `3cdaea6f0c5867a9595e70c50c130f375b25ac2c`;
- aggregate evidence: `research/000b2-entry/operational-smoke-evidence.json`;
- verifier: `research/000b2-entry/verify_operational_smoke.py`;
- synthetic input SHA-256: `860debf008a4702098968ca7b113ea8df7ee0188c9ca08c7c1e9437466876c38`.

All six preregistered cells passed:

| Family | COMPACT | BALANCED |
| --- | --- | --- |
| Moonshine Voice | `SMOKE_PASS` | `SMOKE_PASS` |
| whisper.cpp | `SMOKE_PASS` | `SMOKE_PASS` |
| sherpa-onnx | `SMOKE_PASS` | `SMOKE_PASS` |

The evidence explicitly records:

- primary test decoding: `NO`;
- human speech: `NO`;
- transcript text retention: `NO`;
- repository context: `NO`;
- accuracy scoring: `NO`;
- comparative ranking: `NO`;
- comparative performance claim: `NO`.

## Deterministic scorer

The future scorer implementation and configuration are present at:

- `research/000b2-entry/scorer.py`;
- `research/000b2-entry/scorer-config.json`;
- `research/000b2-entry/verify_scorer.py`.

The implementation is CI-tested before primary results exist. The founding B2 configuration keeps entity normalization disabled so normalized entity accuracy cannot silently exceed exact entity accuracy. Failures remain in denominators. Collateral WER is separated from developer-entity correctness.

The scorer's **canonical revision is not frozen yet**. It can only be named after this entry-preparation branch merges and canonical main is reread.

## Attempt-manifest preparation

`research/000b2-entry/prepare_attempt_manifest.py` deterministically projects:

- the immutable B1 registry;
- the explicit B2 artifact-size amendment;
- durable materialized SHA-256 evidence;
- the frozen B1 methodology;
- the current scorer configuration.

`research/000b2-entry/validate_entry_manifest.py` validates the real B2 values while preserving the historical B1 structural audit. The generated entry draft remains intentionally:

- `frozen=false`;
- human ranking unauthorized;
- primary decoding not started;
- `B2_READY=NO`.

## Preprocessing identity

The canonical preprocessing contract remains FFmpeg `9.0.1`, source commit `bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa`.

The repository contains a fail-closed capture tool at `research/000b2-entry/preprocessing/capture.py`. It rejects any FFmpeg version other than `9.0.1` and records binary, version-output, and contract digests.

A separate CI workflow qualifies that exact source/toolchain path. Toolchain qualification is not equivalent to attempt-time evidence. A future authorized B2 attempt must capture the FFmpeg identity again **before primary decoding in the same attempt environment**.

## Execution-environment identity

`research/000b2-entry/environment/capture.py` records a deterministic environment/hardware fingerprint. `research/000b2-entry/environment/verify_capture.py` rejects declaring a GitHub-hosted Actions runner as `CONTROLLED`.

GitHub-hosted execution is therefore `DIAGNOSTIC_ONLY` for performance evidence. No comparative latency, CPU, memory, energy, or product-efficiency claim may be established from hosted-runner timings.

The actual B2 environment fingerprint remains a same-attempt gate and does not exist yet because an authorized primary B2 attempt does not exist.

## Current readiness

Machine-readable readiness is recorded in `research/000b2-entry/readiness.json` and verified by `research/000b2-entry/verify_readiness.py`.

Technical entry work has removed two former blockers:

1. pending model-payload SHA-256 materialization;
2. bounded non-primary operational qualification.

The following gates remain real:

1. participant/media authority for human developer-speech recordings;
2. authorized human recordings, consent evidence, speaker-disjoint split manifests, and a frozen primary test manifest;
3. canonical scorer revision after entry-preparation merge;
4. same-attempt FFmpeg 9.0.1 binary/version/config capture;
5. same-attempt execution-environment and hardware fingerprint;
6. a final `frozen=true` B2 attempt manifest.

## External authority boundary

Repository-owner approval cannot substitute for participant consent, recording/retention/redistribution/withdrawal authority, or a real human corpus.

Until those external evidence artifacts exist, `000B2-unbiased-stt-bakeoff` remains `BLOCKED_EXTERNAL`. No primary human-speech decoding, STT ranking, candidate winner, product STT integration, or product runtime is authorized by this entry-preparation work.
