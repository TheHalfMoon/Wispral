# Specification 000B — Local Streaming STT and Developer-Entity Evidence

**State:** `REFINING` candidate  
**Parent:** `000-founding-research`  
**Type:** research / benchmark parent specification

## Outcome

Produce reproducible evidence about local speech-to-text configurations and bounded repository-context value for developer speech, sufficient to recommend a first-product STT shortlist or explicitly conclude that no selection is justified yet.

000B does not select a production speech engine by preference. It establishes a controlled evidence program in which raw recognition quality, streaming semantics, repository-context uplift, resource cost, provenance, and limitations remain separable.

## Canonical input

000B is refined only after Specification `000A-acp-qualification` became canonical `VERIFIED` at merge `354695c9f4d406147cbdc425d8f59e841a2f96a3` and its closeout was reconciled at `99dd6290ee01ce566d32b92df6d469b66b56520a`.

The 000A result does not directly select an STT engine. It does, however, reinforce two architectural constraints relevant here:

- probabilistic speech components must remain behind replaceable boundaries;
- benchmark evidence must be narrow enough that unobserved semantics are not promoted into product claims.

The benchmark authority is `docs/benchmarks/WISPRALBENCH.md`.

## Why 000B requires recursive refinement

A single Grain containing corpus design, runtime/model selection, multiple backend integrations, human recording, unbiased decoding, context biasing, deterministic entity resolution, latency/resource measurement, and final recommendation would be too large to verify independently.

000B is therefore a bounded research parent with sequential evidence children:

1. `000B1-benchmark-candidate-qualification` — freeze the benchmark contract, candidate inclusion rules, provenance requirements, streaming-semantics taxonomy, corpus rules, scoring schema, execution-environment rules, and attempt-freeze protocol before comparative decoding;
2. `000B2-unbiased-stt-bakeoff` — execute the primary local STT comparison with repository context disabled;
3. `000B3-context-uplift` — measure engine-agnostic deterministic repository resolution and backend-native context/bias features as separate conditions using frozen evidence from 000B2;
4. `000B4-stt-synthesis` — reconcile the evidence into a bounded recommendation or an explicit insufficient-evidence result.

Only 000B1 is refined to task-level execution by the current authority update. 000B2–000B4 remain intentionally coarse until preceding canonical evidence can change their shape.

## Research questions

000B may answer:

1. Which local configurations produce the strongest developer-entity recognition under a disclosed product-relevant envelope?
2. What ordinary-language accuracy is lost or gained by those configurations?
3. Which candidates expose genuinely incremental streaming behavior versus chunked or repeated re-decode behavior?
4. What first-partial, finalization, resource, and startup observations are measurable without conflating STT with turn detection?
5. Does deterministic bounded repository resolution improve exact developer-entity correctness from the same raw transcript?
6. Where a backend exposes native keyterms, prompts, hotwords, or context biasing, what uplift and false-bias cost does that feature produce under its own explicitly separate condition?
7. Is the evidence strong enough to recommend one configuration, a Pareto shortlist, or no first-product selection?

## Current candidate families

The current refinement evidence identifies three mandatory candidate families for qualification, subject to live revalidation before any benchmark attempt:

- Moonshine Voice streaming STT;
- `whisper.cpp` using an exact OpenAI Whisper model artifact;
- `sherpa-onnx` using an exact online/streaming English ASR model artifact.

This list is a qualification set, not a winner list and not a support claim.

An additional local candidate may be added only through a documented pre-attempt amendment that explains why it materially changes the evidence. A cloud STT system may be used only as an optional reference cell when separately authorized; it must never become required for 000B verification or the local-first product path.

## Streaming-semantics taxonomy

000B MUST NOT collapse every product using the word `streaming` into one behavior.

Each qualified configuration must be classified from observed/documented implementation behavior as one of:

- `NATIVE_INCREMENTAL` — the recognizer consumes audio incrementally and exposes evolving partial/final results without repeatedly decoding the entire configured window as its primary mechanism;
- `CHUNKED_REDECODE` — the integration periodically or on activity boundaries re-runs decoding over a bounded audio window;
- `BATCH_ONLY` — no usable streaming path exists for the tested configuration;
- `UNKNOWN` — evidence is insufficient to classify the behavior.

A classification based only on upstream documentation is `DOCUMENTED_NOT_OBSERVED` until Wispral reproduces it.

Different semantics may be measured, but unlike categories must not be reported as equivalent implementation behavior.

## Benchmark condition separation

### C0 — Unbiased local STT

The primary cross-backend comparison.

- repository vocabulary/context disabled;
- no test-utterance-specific prompt or hotword injection;
- same canonical audio bytes for every candidate;
- deterministic decoding settings where supported and recorded;
- backend-specific necessities remain documented rather than hidden.

C0 establishes raw recognition evidence only.

### C1 — Engine-agnostic deterministic repository resolution

Applied to frozen C0 transcripts, not to audio decoding.

- one common resolver contract across backend transcripts;
- candidate repository data comes from a bounded deterministic extraction rule independent of the expected test answer;
- resolver code/config is frozen before evaluation on the test split;
- exact binding, ambiguity, and unsafe false-binding outcomes are preserved.

C1 measures the value of a portable Wispral context layer rather than native decoder bias.

### C2 — Backend-native context/bias features

Secondary backend-specific evidence only.

Examples may include Moonshine keyterms/context, whisper decoder prompt context, or sherpa-onnx hotword/bias mechanisms where the exact tested model supports them.

C2 MUST NOT replace C0 in the cross-backend raw STT comparison. Native features may use different mechanisms and budgets; results are reported as backend-specific uplift/degradation relative to that backend's own C0 result.

## Model/configuration selection discipline

Runtime family and model configuration are separate decisions.

Before any primary test decoding, 000B1 must freeze an attempt manifest containing for every candidate:

- runtime repository/release/version and exact source revision;
- model name and source;
- exact model/configuration artifact digests;
- model/runtime licenses and provenance;
- quantization/precision;
- language;
- thread count and acceleration settings;
- streaming mode and chunk/decode scheduling;
- VAD/endpointing state;
- prompt/context/hotword state for C0;
- installation/build commands;
- expected artifact footprint;
- exclusions and known incompatibilities.

After the primary test split is decoded, model size, quantization, decoding parameters, prompts, candidate membership, or context budget may not be changed within that attempt. A material change requires preserving the prior attempt and starting a newly pinned attempt.

## Product-relevant configuration envelope

000B1 must define an explicit local configuration envelope before choosing exact candidate models. It should prefer configurations that are plausible for a terminal-native local-first product rather than unconstrained leaderboard models.

The envelope must at minimum bound:

- downloadable model/artifact footprint;
- runtime memory expectations or a rule for measuring them;
- local/offline inference after artifact acquisition;
- redistribution/license acceptability for a future open-source product path;
- CPU-only viability or an explicitly recorded accelerator requirement;
- supported English transcription path for the founding comparison.

If more than one meaningful footprint tier is needed, use a small preregistered set of tiers and compare configurations within clearly labeled tiers rather than pretending materially different resource envelopes are one fair model-size contest.

## Corpus contract

### Primary evidence requires human speech

Synthetic/TTS-generated audio may be used for installation smoke tests, schema validation, and deterministic harness regression. It MUST NOT be the sole basis for ranking candidate STT configurations or making human developer-speech accuracy claims.

The primary developer-entity panel requires recorded human speech with:

- explicit informed consent;
- documented retention policy;
- documented redistribution permission if the resulting audio will support a public reproducibility claim;
- no secret, proprietary, credential, or sensitive repository content;
- speaker and recording metadata sufficient to state limitations without unnecessarily identifying participants.

If suitable human audio is unavailable, the primary comparative execution is `BLOCKED_EXTERNAL`; a synthetic smoke result must not be upgraded into a ranking.

### Corpus composition

The frozen corpus design should cover at least:

- file and directory paths;
- Rust, Python, TypeScript, shell, and mixed-style identifiers;
- package/crate/module names;
- CLI commands and flags;
- Git branches, refs, abbreviated SHAs, and versions;
- test names;
- database/table/field names;
- corrections and abandoned phrases;
- pronunciation variation and non-native English cadence;
- ordinary non-entity language used to measure collateral degradation.

English is the founding comparison language. Arabic remains a planned qualification target, not a support claim and not a mandatory 000B ranking panel unless a later preregistered extension has comparable candidate coverage.

## Audio normalization

All primary candidates must consume audio derived from one frozen canonical preprocessing pipeline.

The contract must record:

- source recording format;
- canonical sample rate/channel/PCM representation;
- resampler/tool versions;
- loudness or amplitude transformations, if any;
- per-file digest before decoding;
- whether silence trimming is forbidden or preregistered;
- the exact real-time feed schedule used by streaming tests.

Do not perform backend-specific denoising, resampling, normalization, or test-set cleanup unless the condition is explicitly isolated and cannot influence the primary C0 ranking.

## STT-versus-turn-detection boundary

000B is not the turn-taking experiment.

For primary pre-segmented accuracy cells, disable VAD/endpointing where the backend permits it so recognition quality is not silently scored together with segmentation quality. If a backend cannot operate without its segmentation path, record that constraint explicitly.

Streaming measurements may use known audio timing and pre-segmented utterances to observe:

- first non-empty partial transcript time;
- final transcript availability after known audio end;
- real-time factor where methodologically valid;
- partial hypothesis revision/stability;
- startup/model-load observations.

Natural pause detection, semantic endpointing, microphone false starts, and barge-in belong to 000C or later evidence.

## Hosted-runner limitation

Shared GitHub-hosted runners may be used for installation, deterministic schema tests, smoke decoding, and accuracy reproduction where the result is not materially hardware-dependent.

They MUST NOT be used to make general comparative latency, CPU, memory, battery, or performance-superiority claims unless the methodology separately demonstrates that the environment is sufficiently controlled. Product-relevant performance evidence should use explicitly identified hardware and OS and preserve run-level observations.

## Primary metrics

The minimum C0/C1 evidence set includes:

- developer entity exact-match accuracy;
- normalized entity accuracy only under preregistered normalization rules;
- entity deletion/substitution/insertion counts;
- ordinary WER or an equivalent disclosed general-language metric;
- false entity insertion rate;
- repository-binding accuracy for C1;
- ambiguity detection rate for C1;
- unsafe false-binding rate for C1;
- sample count and failure/timeout count.

Where meaningful and methodologically qualified, also preserve:

- first-partial timing;
- finalization timing;
- real-time factor;
- model-load/startup time;
- peak resident memory;
- CPU/GPU/accelerator configuration;
- partial revision count or stability measure.

C2 additionally reports native-context uplift and degradation relative to the same backend's C0, including false-bias behavior on distractor terms.

## Scoring and selection discipline

000B must not manufacture one opaque weighted score merely to produce a winner.

Before the primary attempt, 000B1 must define:

- hard eligibility gates;
- primary and secondary metrics;
- treatment of failures/timeouts;
- configuration/resource tiers if any;
- a Pareto/dominance or other transparent decision rule;
- what result is sufficient to recommend `LEADING`, `CONTENDER`, `REJECTED`, or `INSUFFICIENT_EVIDENCE`.

The final 000B recommendation may retain multiple non-dominated candidates for 000G. A forced single winner is not required when the evidence shows a real accuracy/resource/latency tradeoff.

## Out of scope

000B does NOT authorize:

- production speech integration;
- a production Cargo workspace or permanent runtime dependency;
- microphone UX or push-to-talk implementation;
- always-listening behavior;
- turn detection or barge-in product work;
- TTS, acoustic echo cancellation, wake-word, or noise-suppression product work;
- cloud STT as a required dependency;
- model fine-tuning or training as part of the founding comparison;
- public superiority claims before the benchmark claim gate is satisfied;
- support claims for English, Arabic, an operating system, or a hardware class merely because a candidate advertises them upstream.

## Acceptance conditions

000B can close only when its evidence-selected children are `VERIFIED`, `SUPERSEDED`, or `CANCELLED` with explicit rationale and:

1. exact candidate runtime/model provenance is preserved;
2. the primary C0 comparison uses one frozen corpus and frozen configurations;
3. human developer-speech evidence exists or the absence of it is explicit enough to prevent a false ranking;
4. C0 raw STT results remain separate from C1/C2 context conditions;
5. failures and losing metrics remain visible;
6. streaming-semantics differences are reported rather than hidden;
7. hardware-dependent performance claims use controlled, disclosed hardware or remain unclaimed;
8. context benefit includes unsafe false-binding and collateral-degradation evidence;
9. a final recommendation states what is and is not justified for 000G;
10. no README/roadmap/product claim exceeds the evidence.

## Recovery

Research attempts are additive. If a runtime, model artifact, corpus, scoring rule, or configuration changes materially after an attempt freezes, preserve the old attempt and start a new one. Do not rewrite historical results to match a new candidate configuration.