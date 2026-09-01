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

## Grain tasks

- [ ] **B101 — Revalidate canonical and external authority.** Record current Wispral base plus exact candidate repository/release/model-source revisions; preserve material drift from `docs/research/stt/000b-refinement-inputs.md`.
- [ ] **B102 — Define product configuration envelope.** Freeze justified artifact/resource/license/local-inference tiers and maximum configurations per family before primary test decoding.
- [ ] **B103 — Qualify Moonshine configurations.** Apply the B102 rule to current streaming English models; pin exact runtime/model artifacts, digests, license/provenance, C0 settings, and native context capabilities without ranking developer accuracy.
- [ ] **B104 — Qualify whisper.cpp configurations.** Resolve source-versus-release choice, apply B102, pin exact Whisper model artifact(s)/digests/configuration, record real-time integration semantics and prompt-context capability without ranking developer accuracy.
- [ ] **B105 — Qualify sherpa-onnx configurations.** Apply B102 to an exact current English online model path, pin runtime/model artifacts/digests/license/provenance/configuration, and record hotword capability where supported without ranking developer accuracy.
- [ ] **B106 — Run bounded qualification smoke if needed.** Use only public/license-clear non-primary audio to prove selected paths install/load/decode and produce parseable evidence. Preserve failures and do not score candidates against one another.
- [ ] **B107 — Define corpus and speaker contract.** Freeze primary developer-entity, collateral/general, and smoke panel rules; minimum sample/speaker rationale; diversity targets; recording instructions; consent; retention; redistribution; withdrawal-before-freeze; and prohibited content.
- [ ] **B108 — Define entity annotation schema.** Create deterministic machine-readable representation for references, entity spans/classes, exact target text, allowed normalization, spoken forms, repository bindings, ambiguity/distractors, panel, and split.
- [ ] **B109 — Define split and anti-tuning contract.** Freeze development/qualification/test rules, manifest hashing, configuration freeze ordering, and new-attempt requirements after primary test observation.
- [ ] **B110 — Define canonical audio preprocessing.** Pin sample rate/channel/sample representation, resampling implementation/version, amplitude/silence policy, per-file digests, and real-time feed semantics so C0 candidates receive identical canonical audio.
- [ ] **B111 — Define C0 unbiased configuration contract.** Freeze prompt/keyterm/hotword/grammar/context, previous-text, language, search/temperature, VAD/endpointing, punctuation, and partial/timestamp settings for each candidate.
- [ ] **B112 — Define streaming semantics and measurement schema.** Freeze observable criteria for `NATIVE_INCREMENTAL`, `CHUNKED_REDECODE`, `BATCH_ONLY`, and `UNKNOWN`, plus any comparable partial/final timing fields without turning B1 into turn-detection research.
- [ ] **B113 — Define C1 repository-resolution contract.** Freeze engine-agnostic resolver inputs, bounded candidate extraction, ambiguity and unsafe-binding requirements, anti-answer-leakage rules, and future B3 freeze boundary.
- [ ] **B114 — Define C2 native-context contract.** Record backend-native bias/context mechanisms and freeze the future within-backend uplift/degradation methodology; do not enable them in C0.
- [ ] **B115 — Define scoring and failure contract.** Freeze developer entity exact/normalized scoring, edit counts, ordinary WER/collateral error, false insertion, timeout/failure treatment, and future C1 binding metrics.
- [ ] **B116 — Define performance evidence contract.** Freeze hardware/OS/runtime/repetition/warm-cold records and explicitly separate hosted-runner diagnostic timing from controlled comparative performance evidence.
- [ ] **B117 — Define recommendation rule.** Freeze hard gates and transparent Pareto/non-dominance logic plus exact meanings of `LEADING`, `CONTENDER`, `REJECTED`, and `INSUFFICIENT_EVIDENCE` before B2 results exist.
- [ ] **B118 — Define B2 attempt manifest and validator.** Create a machine-readable or deterministically validated schema binding Wispral revision, candidate/model digests, corpus/preprocessing/scorer revisions, C0 configuration, environment, freeze timestamp, and invalidation rules.
- [ ] **B119 — Adversarial preregistration review.** Challenge whether the contract permits model switching, test leakage, normalization inflation, hidden context bias, synthetic-audio overclaim, hosted-runner performance claims, dropped failures, or post-hoc weighting.
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