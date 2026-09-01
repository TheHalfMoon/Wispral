# Specification 000B1 Tasks

## Readiness

000B1 becomes eligible for execution only after this refinement authority is canonical and the following are rechecked:

- 000B parent and B1 Grain are canonical;
- current Moonshine, whisper.cpp, and sherpa-onnx source/release metadata remain accessible;
- candidate model provenance/license data can be pinned;
- B1 can complete without decoding the primary benchmark test split;
- any smoke media is license-clear and excluded from future primary scoring;
- research tooling can remain non-product and reversible;
- no task requires secrets, proprietary benchmark data, or a permanent runtime dependency.

A readiness failure must be recorded rather than bypassed.

Readiness disposition for the current B1 evidence unit: `PASS` for preregistration/qualification work only. This does not authorize B2 primary decoding.

## Grain tasks

- [x] **B101 — Revalidate canonical and external authority.** Recorded in `docs/research/stt/000b1-qualification-report.md`.
- [x] **B102 — Define product configuration envelope.** COMPACT/BALANCED ceilings and mechanical selection rule frozen in the qualification report and benchmark contract.
- [x] **B103 — Qualify Moonshine configurations.** Exact current runtime/asset paths, sizes, licenses, C0 state, and pending B2 SHA-256 materialization gate recorded without ranking developer accuracy.
- [x] **B104 — Qualify whisper.cpp configurations.** Release `b4938`, exact model artifacts/digests, C0 state, and documented-not-observed streaming posture recorded without ranking developer accuracy.
- [x] **B105 — Qualify sherpa-onnx configurations.** Exact runtime/model revisions, chunk-16/left-128 INT8/FP32 artifacts, digests, license/provenance, and C0 state recorded without ranking developer accuracy.
- [x] **B106 — Run bounded qualification smoke if needed.** Disposition: `NOT_RUN_NOT_REQUIRED`; B1 contract/provenance completion does not require a decode. B2 still requires smoke or an explicit canonical waiver.
- [x] **B107 — Define corpus and speaker contract.** Frozen in `docs/research/stt/000b1-benchmark-contract.md`.
- [x] **B108 — Define entity annotation schema.** `research/000b1/schemas/entity-annotation.schema.json`.
- [x] **B109 — Define split and anti-tuning contract.** Frozen in the benchmark contract and attempt validator.
- [x] **B110 — Define canonical audio preprocessing.** PCM WAV / mono / 16 kHz / PCM_S16LE baseline and digest rules frozen in the benchmark contract and attempt schema.
- [x] **B111 — Define C0 unbiased configuration contract.** Context/prompt/keyterm/hotword/grammar rules frozen and machine-checked by the verifier.
- [x] **B112 — Define streaming semantics and measurement schema.** `NATIVE_INCREMENTAL`, `CHUNKED_REDECODE`, `BATCH_ONLY`, and `UNKNOWN` criteria frozen in the benchmark contract.
- [x] **B113 — Define C1 repository-resolution contract.** Engine-agnostic bounded resolver and anti-answer-leakage contract frozen.
- [x] **B114 — Define C2 native-context contract.** Within-backend uplift/degradation methodology frozen; C2 remains excluded from C0.
- [x] **B115 — Define scoring and failure contract.** Entity exact/normalized views, WER/collateral evidence, failures, and C1 metrics frozen.
- [x] **B116 — Define performance evidence contract.** Controlled hardware requirements and hosted-runner diagnostic-only boundary frozen.
- [x] **B117 — Define recommendation rule.** Hard gates plus Pareto/non-dominance and disposition vocabulary frozen before B2 results.
- [x] **B118 — Define B2 attempt manifest and validator.** `research/000b1/schemas/attempt-manifest.schema.json` and `research/000b1/validate_attempt_manifest.py`.
- [x] **B119 — Adversarial preregistration review.** `docs/research/stt/000b1-adversarial-review.md`; manipulation paths challenged before any primary decoding.
- [ ] **B120 — Canonical B1 closeout.** Only after exact-head qualification/review/merge, reread canonical truth, mark B1 with its justified disposition, and evaluate whether B2 is `GRAIN`/`READY`, `BLOCKED_EXTERNAL`, or still requires refinement.

## Stop conditions

Stop dependent B1 tasks and record the exact blocker if:

- runtime/model identity or license cannot be made reproducible;
- the product envelope would have to be selected from Wispral primary test results;
- primary test audio is accidentally decoded before configuration/scoring freeze;
- a smoke clip is discovered to overlap future primary scoring;
- a candidate requires mandatory network inference for C0;
- canonical audio equivalence cannot be maintained;
- human-audio consent/redistribution requirements are weakened merely to make B2 runnable;
- a performance claim would depend on uncontrolled hardware;
- product code/permanent dependencies become necessary to finish B1.

## Completion evidence

B1 completion requires at minimum:

- exact changed paths and canonical base/head;
- pinned external source/runtime/model/license records;
- product-envelope decision with rationale;
- qualified/excluded candidate manifest;
- corpus/consent/split/annotation contracts;
- canonical preprocessing contract;
- C0/C1/C2 condition contract;
- streaming-semantics taxonomy;
- scoring/failure/recommendation rules;
- performance-environment contract;
- B2 attempt-manifest schema/validation;
- any smoke evidence clearly labeled non-comparative;
- adversarial preregistration review;
- exact-head verification and canonical closeout.

B1 completion contains no primary benchmark ranking.
