# Specification 000B1 — Adversarial Preregistration Review

**Status:** B119 completed against preregistration evidence; no primary benchmark executed  
**Canonical Wispral base:** `6b5696a6becc360948282712cc9339df9cb3a67c`  
**Contract:** `000b1-contract-v1`

## Review objective

Challenge the preregistration package as though trying to obtain a preferred STT result without leaving an obvious trace.

This is an internal adversarial review of the contract. It is not a substitute for independent PR review, exact-head qualification, or canonical closeout.

## Threat review

### 1. Model switching

**Attack:** inspect primary results, then move one family to a larger/smaller model or different quantization.

**Control:** the COMPACT/BALANCED ceilings and the largest-qualifying configuration rule are frozen before primary results. Candidate membership, exact runtime/model artifacts, and SHA-256 are material attempt inputs. Any post-freeze change invalidates the attempt.

**Disposition:** `CONTROLLED_BY_CONTRACT`.

### 2. Test leakage

**Attack:** use expected entity text, test annotations, or target-specific repository vocabulary to tune candidate settings or the resolver.

**Control:** candidate selection, C0 settings, scorer/normalization, split manifest, and test digest freeze before primary decoding. C1 explicitly forbids the reference transcript, expected entity id/text, and target-specific lookup tables.

**Disposition:** `CONTROLLED_BY_CONTRACT`.

### 3. Normalization inflation

**Attack:** lowercase identifiers, strip CLI prefixes/path separators, rewrite versions, or otherwise normalize errors into matches.

**Control:** exact entity accuracy is primary. The optional normalized view is secondary and class-aware. The contract explicitly forbids semantic rewrites such as removing `--`, changing path separators, rewriting versions/SHAs, or changing identifier style.

**Disposition:** `CONTROLLED_BY_CONTRACT`.

### 4. Hidden context bias

**Attack:** enable prompts, keyterms, hotwords, grammar, previous-text carryover, or repository vocabulary for some candidates in the cross-backend comparison.

**Control:** C0 freezes repository/test-specific decoder context OFF. Moonshine context/keyterms, whisper.cpp initial prompt/prompt carryover, and sherpa-onnx hotwords are explicitly disabled. Backend-native context belongs only to later C2 within-backend evidence.

**Disposition:** `CONTROLLED_BY_CONTRACT`.

### 5. Synthetic-audio overclaim

**Attack:** use TTS or synthetic clips as part of the primary developer-speech ranking when human recordings are unavailable.

**Control:** synthetic/TTS is limited to smoke, harness/schema validation, and regression. Human developer-speech ranking requires explicit human authority and corpus manifests. If that authority is absent, B2 must be `BLOCKED_EXTERNAL`.

**Disposition:** `CONTROLLED_BY_CONTRACT`; current external human-corpus authority remains absent.

### 6. Hosted-runner performance overclaim

**Attack:** use shared CI timing to claim latency, CPU, memory, or resource superiority.

**Control:** hosted-runner timing is diagnostic only. Comparative performance claims require a named controlled environment with hardware fingerprint and run-level evidence.

**Disposition:** `CONTROLLED_BY_CONTRACT`; no controlled performance environment is currently qualified.

### 7. Dropped failures

**Attack:** remove timeout/runtime-error/missing-output utterances from denominators.

**Control:** every attempted utterance has a frozen failure outcome and failure handling is part of the scorer contract. Material changes after observation invalidate the attempt.

**Disposition:** `CONTROLLED_BY_CONTRACT`.

### 8. Post-hoc weighting

**Attack:** invent or change a weighted score after seeing results to force one winner.

**Control:** opaque weighted winner scoring is prohibited. Hard gates and Pareto/non-dominance logic are frozen before B2 results. `LEADING`, `CONTENDER`, `REJECTED`, and `INSUFFICIENT_EVIDENCE` are defined in advance.

**Disposition:** `CONTROLLED_BY_CONTRACT`.

## Additional challenge findings

### Artifact integrity incompleteness

Moonshine `quantized_26_08_21` payloads currently have exact upstream URL/size/CRC32C records but B1 has not materialized every file to capture SHA-256. sherpa-onnx `tokens.txt` also remains pending attempt-time SHA-256.

This is preserved as a B2 blocker, not represented as PASS.

### Operational qualification incompleteness

B106 is `NOT_RUN_NOT_REQUIRED` for B1 contract completion. No selected candidate is claimed operationally supported by Wispral. A later B2 entry gate requires bounded non-primary smoke or an explicit canonical waiver.

### Human corpus authority incompleteness

No human developer-speech consent/retention/redistribution package or frozen primary manifest exists.

This is a hard external blocker for primary ranking. Synthetic media cannot satisfy it.

## Adversarial conclusion

The preregistration package is sufficiently narrow to make the reviewed manipulation paths detectable and attempt-invalidating.

It does **not** make B2 executable today.

`B1_CONTRACT_REVIEW: PASS`

`PRIMARY_TEST_DECODING: NO`

`COMPARATIVE_RANKING: NO`

`B2_READY: NO`

Current B2 blockers include artifact materialization integrity, operational smoke/waiver, human developer-speech authority/corpus freeze, scorer/preprocessing freeze, and execution-environment freeze.
