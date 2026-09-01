# Specification 000B1 — STT Benchmark Preregistration Contract

**Status:** frozen contract candidate; no primary decoding authorized  
**Canonical Wispral base:** `6b5696a6becc360948282712cc9339df9cb3a67c`  
**Contract version:** `000b1-contract-v1`

## 1. Purpose

This contract freezes the methodology required before the first Wispral local developer-speech comparison. It exists to prevent post-result model switching, hidden context bias, normalization inflation, synthetic-audio overclaim, dropped failures, hosted-runner performance claims, and post-hoc winner scoring.

The contract governs a future 000B2 attempt. It does not itself authorize 000B2 or create benchmark results.

## 2. Evidence planes

The benchmark has three non-interchangeable evidence planes.

### C0 — raw/unbiased local STT

Input:

`canonical audio -> exact candidate configuration -> raw transcript/events`

Repository/test-specific decoder context is OFF.

C0 is the only plane used for raw cross-backend STT comparison.

### C1 — engine-agnostic repository resolution

Input:

`frozen C0 transcript -> one deterministic bounded resolver -> resolved entity output`

The resolver is identical across candidate transcripts and cannot inspect the expected answer.

C1 measures the portable Wispral context layer. It does not rewrite C0 evidence.

### C2 — backend-native context/bias

Input:

`same backend + same canonical audio + frozen backend-native context rule -> contextualized output`

C2 is reported only as within-backend uplift/degradation against that backend's C0 result. It cannot replace C0 in cross-backend ranking.

## 3. Product resource envelope

The primary comparison uses two preregistered model-payload tiers.

| Tier | Primary C0 payload |
| --- | ---: |
| `COMPACT` | `<= 167772160` bytes (160 MiB) |
| `BALANCED` | `> 167772160` and `<= 536870912` bytes (512 MiB) |

Common eligibility:

- local/offline inference after artifact acquisition;
- CPU-only baseline path;
- English founding comparison;
- exact runtime/model provenance and license can be recorded;
- repository-specific context can be disabled for C0;
- research-only/reversible integration;
- no required hosted inference.

For each family/tier, admit at most one configuration: the largest qualifying English configuration that does not exceed the tier ceiling using pre-result metadata only. Tier boundaries and this rule cannot change after primary results are visible within an attempt.

## 4. Candidate freeze

The candidate manifest is `research/000b1/qualified-candidates.json`.

An actual B2 attempt must materialize the exact intended artifacts and replace every pending digest/byte placeholder with verified attempt-time values before freeze.

A candidate may be excluded before freeze only for a documented qualification failure such as unresolved license/provenance, artifact identity failure, mandatory hosted inference, unsupported local English path, or inability to preserve C0 fairness. Exclusion after observing primary accuracy requires invalidating the attempt.

## 5. Human-speech authority

### 5.1 Primary developer panel

Primary developer-speech ranking requires human recordings under explicit authority.

Before recording or accepting primary media, the evidence package must record:

- participant consent scope;
- recording purpose;
- whether public redistribution is allowed;
- repository storage policy;
- retention period or retention rule;
- deletion/revocation procedure before attempt freeze;
- derivative benchmark artifact permission;
- privacy constraints;
- prohibited content policy.

No credential, secret, private repository content, proprietary code, PHI, or other sensitive personal data may be intentionally recorded.

If suitable authority does not exist, primary execution is `BLOCKED_EXTERNAL`.

### 5.2 Synthetic/TTS boundary

Synthetic/TTS audio is permitted only for:

- installation smoke;
- harness validation;
- deterministic regression;
- scorer/schema validation.

Synthetic/TTS audio MUST NOT contribute to the primary human developer-speech ranking, human-speech accuracy claims, or speaker-diversity claims.

### 5.3 Collateral/general panel

A license-clear existing human-speech corpus may be used as a collateral/general panel when sampling, preprocessing, and licensing are frozen. It does not replace the human developer-entity panel.

## 6. Corpus composition

The human developer-entity panel must cover bounded examples of:

- file and directory paths;
- Rust, Python, TypeScript, shell, and mixed-style identifiers;
- camelCase, snake_case, SCREAMING_SNAKE_CASE, kebab-case where relevant;
- function, method, type, module, crate, package, and framework names;
- CLI commands and flags;
- Git branch names, refs, abbreviated SHAs, and versions;
- test names;
- database/table/field identifiers;
- numeric versions and line ranges;
- corrections, false starts, and abandoned phrases;
- ordinary surrounding language.

The corpus must include distractor/near-collision cases such as singular/plural paths, identifier capitalization differences, adjacent version numbers, and names separated by punctuation.

## 7. Speaker/sample design

Before primary recording begins, the attempt must freeze either:

1. a minimum speaker/utterance design with explicit counts; or
2. a written statistical/design rationale for another sampling plan.

The design must state targets for:

- speaker count;
- utterances per speaker;
- native/non-native English representation where ethically and practically authorized;
- cadence variation;
- microphone/environment variation or intentional control;
- speaker-disjoint split rules.

No sample-count target may be reduced after primary test outputs become visible merely to obtain a desired ranking.

## 8. Split discipline

At minimum use:

- `development` — scripts/context-resolver development only;
- `qualification` — non-primary operational checks and allowed methodology verification;
- `test` — frozen primary comparison.

The primary test manifest must be cryptographically frozen before any candidate decodes it.

Rules:

- test speakers must not be used to tune candidate-specific settings;
- candidate model/configuration selection freezes before test decoding;
- scoring and normalization freeze before test decoding;
- C0 settings freeze before test decoding;
- primary test transcript inspection ends the right to modify material attempt inputs;
- a material change after inspection requires a new attempt id and preserved old attempt.

## 9. Annotation schema

The canonical machine-readable annotation schema is `research/000b1/schemas/entity-annotation.schema.json`.

Each utterance must preserve:

- stable utterance id;
- panel and split;
- canonical reference transcript;
- speaker alias/id that does not unnecessarily identify a participant;
- entity spans and classes;
- exact expected entity text;
- allowed normalization, if any;
- spoken form/alias when material;
- bounded repository/archetype binding;
- ambiguity/distractor metadata.

Entity classes must distinguish at least:

- `FILE_PATH`
- `DIRECTORY_PATH`
- `IDENTIFIER`
- `FUNCTION`
- `TYPE`
- `PACKAGE_MODULE`
- `FRAMEWORK`
- `CLI_FLAG`
- `GIT_REF`
- `GIT_SHA`
- `VERSION`
- `TEST_NAME`
- `DATABASE_IDENTIFIER`
- `LINE_RANGE`
- `OTHER_DEVELOPER_ENTITY`

## 10. Canonical audio preprocessing

Every C0 candidate must receive audio derived from one frozen preprocessing pipeline.

The attempt manifest must record:

- source media digest;
- source format;
- canonical sample rate;
- channels;
- sample representation;
- resampler/tool name and exact version;
- amplitude/loudness transform or explicit `NONE`;
- silence trim policy or explicit `NONE`;
- resulting canonical file SHA-256;
- duration;
- streaming feed rule.

Default founding contract unless a later preregistered amendment is justified before test decoding:

- PCM WAV;
- mono;
- 16 kHz;
- signed 16-bit little-endian PCM;
- no denoising;
- no candidate-specific normalization;
- no semantic silence removal;
- one canonical file per utterance.

If an engine requires a different internal representation, its adapter may convert from the canonical PCM bytes but may not alter semantic audio content. The adapter and conversion are recorded.

## 11. C0 candidate configuration

For every candidate, explicitly freeze:

- exact runtime/build artifact;
- exact model files and SHA-256;
- language mode;
- threads;
- device/accelerator;
- precision/quantization;
- beam/search settings;
- temperature;
- VAD/endpointing;
- timestamps/partial settings;
- previous-text carryover;
- punctuation control if available;
- prompt/context/keyterm/hotword/grammar state.

Repository/test-specific prompt/context/keyterms/hotwords/grammar are OFF for C0.

Known family-specific requirements:

- Moonshine: `context` OFF; `keyterms` OFF;
- whisper.cpp: `initial_prompt` empty/OFF; prompt carryover OFF;
- sherpa-onnx: hotwords/context bias OFF.

If a backend cannot disable a material bias mechanism, record the limitation and decide eligibility before primary decoding.

## 12. Streaming-semantics taxonomy

A tested integration receives exactly one observed classification:

### `NATIVE_INCREMENTAL`

The recognizer consumes audio incrementally and exposes evolving recognition state/results without repeatedly decoding the complete configured audio window as its primary mechanism.

### `CHUNKED_REDECODE`

The integration periodically or at activity boundaries decodes/re-decodes a bounded accumulated/sliding window as its primary mechanism.

### `BATCH_ONLY`

The tested path offers no usable incremental/streaming operation for the benchmark contract.

### `UNKNOWN`

Raw observations are insufficient to classify it without inference.

Upstream documentation alone may be recorded as `DOCUMENTED_NOT_OBSERVED` but cannot establish the Wispral observed class.

The harness must preserve enough raw backend event/decode evidence to challenge classification. It must not fabricate partial/final semantics unavailable from the backend.

## 13. Streaming measurement fields

Where the backend semantics support the measurement, record raw per-utterance timestamps for:

- audio start;
- audio end;
- first non-empty partial;
- each partial revision;
- backend final event;
- final transcript availability.

Do not infer natural turn detection from pre-segmented audio.

Natural endpointing, pause semantics, microphone false-start behavior, barge-in, and interruption latency belong to 000C or later work.

## 14. C1 repository resolver contract

The C1 resolver must be deterministic and engine-agnostic.

Inputs:

- frozen C0 transcript;
- bounded repository snapshot/manifest independent of the expected answer;
- frozen resolver configuration.

Forbidden inputs:

- reference transcript;
- expected entity id/text;
- target-specific lookup tables derived from the test labels;
- backend identity as a scoring feature.

The repository candidate extractor must have an explicit candidate budget and deterministic ordering/tie-breaking. The resolver must be able to return `AMBIGUOUS`/`UNRESOLVED`; forced binding is forbidden when policy thresholds are not met.

Each proposed binding must expose inspectable evidence/score components sufficient to explain why the binding occurred.

The resolver implementation may be developed in B3, but its revision/configuration must freeze before B3 test evaluation.

## 15. C2 backend-native context contract

Backend-native features may be evaluated only after C0 is frozen.

C2 rules:

- derive vocabulary/context from the same bounded repository source contract;
- use no expected-answer-specific injection;
- freeze candidate budget and backend-specific configuration before C2 test decode;
- compare only to the same backend/configuration's C0 result;
- report target uplift and ordinary-language degradation;
- report false bias on distractor terms;
- never use C2 as a substitute for C0 cross-backend ranking.

## 16. Text normalization

Two entity views are preserved:

1. `EXACT` — byte-for-byte canonical entity target after explicitly defined Unicode representation;
2. `NORMALIZED` — optional secondary view under a frozen class-aware rule.

Exact developer entities remain primary where case/punctuation is semantically material.

Normalization MUST NOT silently:

- lowercase case-sensitive identifiers;
- remove `--` from CLI flags;
- collapse singular/plural path segments;
- remove path separators;
- rewrite versions;
- rewrite Git SHAs;
- convert one identifier style into another;
- correct an entity using expected-answer knowledge.

Ordinary WER normalization must be separately defined and cannot determine entity correctness.

## 17. Primary metrics

### 17.1 Developer Entity Exact Accuracy

`correct_exact_entities / total_reference_entities`

Every reference entity contributes once. A missing, substituted, or materially malformed entity is incorrect.

### 17.2 Developer Entity Normalized Accuracy

Same denominator, using only preregistered class-aware normalization. Always report next to exact accuracy, never instead of it.

### 17.3 Entity edit counts

Preserve:

- entity substitutions;
- entity deletions;
- false entity insertions.

### 17.4 Ordinary/collateral WER

Report a disclosed WER calculation on the collateral/general panel and/or non-entity transcript portions according to the frozen scorer contract.

### 17.5 Failure outcomes

Every attempted utterance must resolve to one of:

- `SUCCESS`
- `TIMEOUT`
- `RUNTIME_ERROR`
- `INVALID_OUTPUT`
- `MISSING_OUTPUT`

Failures remain in denominators according to the frozen metric definition. They cannot be dropped from a candidate's evaluated sample set.

### 17.6 C1 metrics

At minimum:

- repository-binding accuracy;
- ambiguity detection rate;
- unsafe false-binding rate;
- unresolved rate.

`unsafe false binding` means the resolver confidently binds to the wrong repository entity under the frozen policy rather than returning ambiguity/unresolved.

## 18. Performance evidence contract

Performance comparison requires controlled, disclosed hardware.

Record:

- machine identifier/model;
- CPU;
- GPU/NPU if used;
- RAM;
- OS/version/kernel where relevant;
- power/performance mode where material;
- runtime/model config;
- threads;
- cold/warm state;
- repetitions;
- run-level timing/resource measurements;
- temperature/throttling observations where material and available.

Shared GitHub-hosted runner timing is diagnostic only and cannot establish comparative latency, CPU, memory, battery, or performance superiority.

Accuracy/correctness reproduction may use hosted runners only when hardware differences are not asserted to establish a comparative performance claim.

## 19. Recommendation rule

No opaque weighted winner score is allowed.

### Hard eligibility gates

A configuration is ineligible for `LEADING`/`CONTENDER` if any required condition fails, including:

- unresolved artifact/license/provenance;
- C0 fairness violation;
- excessive missing/invalid execution evidence;
- primary test contamination;
- unrecorded material configuration drift.

### Pareto comparison

Among eligible configurations within a tier, use transparent metric vectors and Pareto/non-dominance reasoning across at least:

- Developer Entity Exact Accuracy;
- collateral/general error;
- failure rate;
- controlled performance/resource evidence where valid.

Do not mix uncontrolled performance fields into Pareto claims.

### Dispositions

`LEADING`

An eligible configuration is non-dominated in its tier and the available evidence supports using it as the strongest current candidate under the declared envelope, with limitations stated.

`CONTENDER`

An eligible configuration remains non-dominated or materially competitive but evidence does not justify calling it leading, or it represents a meaningful alternative resource/behavior tradeoff.

`REJECTED`

The configuration fails a hard gate or is materially dominated under the preregistered evidence contract with sufficient evidence to justify exclusion from the founding shortlist.

`INSUFFICIENT_EVIDENCE`

The available evidence cannot justify one of the other dispositions without inventing missing observations.

A final single winner is not required.

## 20. Attempt manifest and freeze order

The machine-readable schema is `research/000b1/schemas/attempt-manifest.schema.json`.

Freeze sequence:

1. canonical Wispral revision;
2. B1 contract revision;
3. exact runtime/model artifact materialization and SHA-256;
4. corpus authority and split manifests;
5. preprocessing revision/configuration;
6. candidate C0 settings;
7. scorer revision/configuration;
8. execution environment;
9. attempt id;
10. manifest SHA-256;
11. only then decode the primary test split.

The manifest must have `frozen=true` before primary decode.

## 21. Invalidation rules

Invalidate the current attempt and start a new id if, after freeze or primary test inspection, any material input changes, including:

- runtime revision;
- model artifact or digest;
- candidate membership;
- tier selection rule;
- audio bytes/preprocessing;
- split membership;
- reference annotation;
- C0 context/search settings;
- scorer/normalization;
- failure handling;
- recommendation logic;
- controlled performance environment when the claim depends on it.

Preserve the invalidated attempt and reason. Do not overwrite history.

A correction to a factual typo that provably does not change material execution/scoring may be amended only with a documented diff and rationale.

## 22. Anti-tuning rules

Within a frozen attempt, forbidden after primary output visibility:

- switching to a different model size/quantization;
- adding candidate-specific vocabulary;
- changing decoding/search parameters;
- changing context budget;
- changing normalization to rescue specific errors;
- deleting hard utterances;
- changing weights/metric priorities;
- converting failures to missing samples;
- selecting a different performance subset because it is faster.

Exploratory work after visibility requires a new development analysis and cannot retroactively change the frozen primary attempt.

## 23. Evidence retention

A qualifying attempt must retain enough material to reproduce/challenge claims, subject to human-audio authority.

Retain at minimum:

- attempt manifest and its digest;
- artifact digests;
- corpus/split manifests;
- consent/redistribution authority records in an appropriate privacy-preserving form;
- preprocessing/scorer source revision;
- raw candidate outputs/events;
- normalized/scored outputs;
- failure logs;
- run-level controlled performance outputs where used;
- exact commands/configuration;
- invalidation/amendment records.

If raw human audio cannot legally be redistributed, the benchmark must state the reproducibility limitation and must not imply fully public reproduction.

## 24. B2 entry gate

000B2 primary decoding is authorized only when canonical governance independently says B2 is executable and the exact attempt proves:

- all material runtime/model payloads have verified SHA-256 and exact byte counts;
- current licenses/provenance remain acceptable;
- non-primary operational smoke has passed or a canonical waiver exists;
- human primary recordings have explicit authority;
- split/corpus/annotation manifests are complete and frozen;
- preprocessing/C0/scoring/recommendation rules are frozen;
- the manifest validator passes;
- no primary test output has yet been inspected.

If human recording authority is absent, the correct state is `BLOCKED_EXTERNAL`.

## 25. Non-claims

This contract contains zero qualifying benchmark results. It does not establish accuracy, streaming support, latency, resource superiority, context uplift, platform support, product readiness, or a permanent STT selection.