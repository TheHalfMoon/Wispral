# Specification 000B Tasks

This file tracks recursive child progression. It is not permission to execute later children early.

## Parent state

- [x] `000B1` benchmark/candidate qualification — `VERIFIED`; evidence merge `8df69835349f85d5ae6af9d6a62ef3af24f65f43`, canonical closeout merge `ed05ad9b0ef80ae4f6838e783188cf306c20391a`.
- [x] `000B2` bounded entry preparation — `CLOSED_CANONICAL`; evidence merge `49d0f31408ab36f285f5e61228b54a72ca0aec07`; this is not primary B2 execution.
- [ ] `000B2` unbiased local STT bakeoff — `BLOCKED_EXTERNAL`; primary execution is not authorized.
- [ ] `000B3` repository-context uplift — intentionally coarse until B2 is canonical.
- [ ] `000B4` STT synthesis — intentionally coarse until prior evidence selects its exact inputs.

## Current child frontier

`000B1-benchmark-candidate-qualification` is canonically `VERIFIED`.

The bounded non-primary `000B2` entry-preparation unit is canonically closed. It removed the materialization, non-primary smoke, and scorer-canonicalization blockers without creating participant/media authority or authorizing primary decoding.

`000B2-unbiased-stt-bakeoff` remains the dependency-ordered successor but is `BLOCKED_EXTERNAL`, not `GRAIN`, `READY`, or `RUNNING`.

B2 primary developer-speech decoding MUST NOT begin while any current readiness gate remains unsatisfied. Synthetic/TTS media may support smoke/harness/regression only and cannot substitute for the required human developer-speech authority or frozen primary corpus.

`specs/CURRENT.md`, `research/000b2-entry/readiness.json`, and `research/000b2-entry/canonical-closeout.json` own the current executable frontier and blocker set. `research/000b1/canonical-closeout.json` remains historical B1 authority and must not be rewritten to pretend its original blocker snapshot is current.

## 000B2 entry-preparation closeout

Canonical evidence now establishes:

- all 18 B1-pending candidate artifact SHA-256 identities are materialized and canonically reproduced;
- all six selected candidate cells have bounded deterministic synthetic non-speech `SMOKE_PASS` evidence;
- the deterministic scorer implementation, configuration, and verifier are canonical at merge `49d0f31408ab36f285f5e61228b54a72ca0aec07`;
- FFmpeg `9.0.1` qualification and attempt-state-bound preprocessing capture tooling are prepared;
- attempt-state-bound execution-environment capture tooling is prepared;
- canonical trusted artifact-identity run `33537242680` passed against live base `248208cffa666a485fe58b7467fdbb2ec7e8b820` and exact candidate head `69b66bc433a146c2146e2b7fec264a8f4ed50ae9`.

The trusted artifact gate explicitly provides no process chronology attestation.

## 000B2 remaining entry gate

B2 remains blocked until all of the following become real:

- human developer-speech participant/media authority, including consent, purpose, retention, redistribution, withdrawal, derivative-artifact permission, privacy, and prohibited-content policy;
- authorized human recordings, consent records, speaker-disjoint split manifests, and a frozen primary test manifest;
- accepted attempt-bound FFmpeg `9.0.1` binary/version/config identity and preprocessing execution evidence under separately reviewable execution chronology;
- accepted attempt-bound execution-environment and hardware-fingerprint evidence under separately reviewable chronology/control evidence;
- a final B2 attempt manifest with `frozen=true` and matching freeze digest.

Do not refine B2 into primary decoding tasks or execute C0 until every required gate is satisfied and readiness is rechecked from canonical `main`.

## 000B3 entry gate

Do not refine 000B3 to executable tasks until B2 preserves frozen raw transcripts and exact C0 evidence sufficient to measure context uplift without silently changing the underlying STT comparison.

## 000B4 entry gate

Do not refine B4 until the evidence-selected preceding cells are canonical and the synthesis inputs are stable enough to challenge a recommendation.

## Parent closeout

000B closes only after required children are reconciled and a final recommendation or explicit insufficient-evidence result is canonical.

No 000B state authorizes production Rust/Cargo speech integration. Product-code authority remains with the later 000G selection gate.
