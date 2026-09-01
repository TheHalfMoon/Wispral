# Specification 000B Tasks

This file tracks recursive child progression. It is not permission to execute later children early.

## Parent state

- [x] `000B1` benchmark/candidate qualification — `VERIFIED`; evidence merge `8df69835349f85d5ae6af9d6a62ef3af24f65f43`, canonical closeout merge `ed05ad9b0ef80ae4f6838e783188cf306c20391a`.
- [ ] `000B2` unbiased local STT bakeoff — `BLOCKED_EXTERNAL`; primary execution is not authorized.
- [ ] `000B3` repository-context uplift — intentionally coarse until B2 is canonical.
- [ ] `000B4` STT synthesis — intentionally coarse until prior evidence selects its exact inputs.

## Current child frontier

`000B1-benchmark-candidate-qualification` is canonically `VERIFIED`.

`000B2-unbiased-stt-bakeoff` is the dependency-ordered successor but remains `BLOCKED_EXTERNAL`, not `GRAIN`, `READY`, or `RUNNING`.

B2 primary developer-speech decoding MUST NOT begin while any B1 entry gate remains unsatisfied. Entry-preparation work may only remove non-primary readiness blockers without weakening the frozen B1 contract, inspecting the primary test split, or substituting synthetic/TTS media for the required human developer-speech authority.

The earlier `spec.md` sentence stating that only 000B1 was task-refined describes the refinement state created by the 000B refinement merge `6b5696a6becc360948282712cc9339df9cb3a67c`; canonical B1 evidence and closeout now supersede that statement for execution ordering. `specs/CURRENT.md` owns the executable frontier.

## 000B2 entry gate

Canonical B1 now establishes the required methodology inputs:

- candidate inclusion/exclusion rules;
- exact attempt-manifest schema;
- product configuration envelope/resource tiers;
- corpus/consent/license/split requirements;
- canonical audio preprocessing/digest contract;
- streaming-semantics taxonomy;
- C0 unbiased configuration rules;
- primary/secondary metrics and failure handling;
- test-set freeze/no-tuning rule;
- controlled performance-environment rule;
- human developer-speech availability requirements.

B2 nevertheless remains blocked until the concrete attempt-time readiness evidence required by the B1 contract exists. Current blockers are canonical in `research/000b1/canonical-closeout.json` and include:

- human developer-speech consent, retention, redistribution, withdrawal, and frozen-corpus authority;
- Moonshine material payload SHA-256 values;
- sherpa-onnx `tokens.txt` SHA-256;
- per-candidate bounded non-primary operational smoke PASS or an explicit canonical waiver;
- frozen scorer implementation/revision/configuration;
- attempt-time FFmpeg binary/version-output and preprocessing execution evidence;
- frozen execution environment/hardware fingerprint;
- a final B2 attempt manifest with `frozen=true` and matching freeze digest.

Do not refine B2 into primary decoding tasks or execute C0 until every required gate is satisfied and readiness is rechecked from canonical `main`.

## 000B3 entry gate

Do not refine 000B3 to executable tasks until B2 preserves frozen raw transcripts and exact C0 evidence sufficient to measure context uplift without silently changing the underlying STT comparison.

## 000B4 entry gate

Do not refine B4 until the evidence-selected preceding cells are canonical and the synthesis inputs are stable enough to challenge a recommendation.

## Parent closeout

000B closes only after required children are reconciled and a final recommendation or explicit insufficient-evidence result is canonical.

No 000B state authorizes production Rust/Cargo speech integration. Product-code authority remains with the later 000G selection gate.
