# Specification 000B1 — STT Benchmark and Candidate Qualification

**State:** `GRAIN` candidate after 000B refinement authority becomes canonical  
**Parent:** `000B-stt-entity-bakeoff`  
**Type:** research / preregistration / candidate qualification

## Outcome

Produce a frozen, reproducible pre-comparison contract for the first local developer-speech bakeoff, including exact candidate qualification rules, model/runtime provenance, corpus and consent requirements, audio normalization, scoring, streaming-semantics classification rules, performance-environment rules, and an attempt-manifest schema.

000B1 ends **before primary comparative test decoding**. Its job is to make 000B2 difficult to cherry-pick.

## Why this is a separate Grain

The following behavior notes are upstream-documented refinement inputs, not Wispral observations. At the pinned sources recorded in `docs/research/stt/000b-refinement-inputs.md`, each remains `DOCUMENTED_NOT_OBSERVED` until reproduced by a Wispral attempt:

- Moonshine exposes streaming architectures and native runtime keyterms/context;
- whisper.cpp exposes local Whisper inference but documents its microphone stream example as naive periodic/sliding re-decode behavior;
- sherpa-onnx exposes online recognizers and multiple streaming model families/hotword mechanisms.

If Wispral selects models, context settings, streaming definitions, or scoring after seeing developer test outputs, a public comparison would be weak evidence. B1 therefore freezes those decisions first.

## Canonical inputs

Before execution, reread:

- `AGENTS.md`
- `CONSTITUTION.md`
- `docs/canonical/CURRENT_STATE.md`
- `docs/canonical/ARCHITECTURE_INVARIANTS.md`
- `docs/benchmarks/WISPRALBENCH.md`
- `specs/CURRENT.md`
- `specs/000-founding-research/`
- `specs/000B-stt-entity-bakeoff/`
- `docs/research/stt/000b-refinement-inputs.md`

Live external truth overrides the refinement-time pins if a runtime/model changes before B1 execution. Any replacement must be explicit and documented rather than silent.

## Mandatory candidate families to qualify

Subject to readiness-time revalidation:

1. Moonshine Voice streaming STT;
2. `whisper.cpp` with an exact OpenAI Whisper model artifact;
3. `sherpa-onnx` with an exact online English ASR model artifact.

B1 does not require every family to survive qualification. Exclusion is a valid result when exact reasons are preserved.

Examples of valid exclusion reasons:

- unresolvable runtime/model license or provenance;
- inability to pin/download exact artifacts;
- no local English inference path under the product envelope;
- no reproducible build/install path for the selected execution environment;
- artifact/runtime requirements outside the preregistered local product envelope;
- execution would require a hosted inference dependency for C0.

An excluded candidate is not labeled `FAILED` unless an authorized qualification attempt actually fails; distinguish policy exclusion from runtime failure.

## Configuration qualification

B1 must define the exact unit that B2 will compare.

For each surviving configuration record:

- candidate family;
- runtime release/version;
- source repository and exact revision;
- install/build artifact identity and digest where available;
- exact model artifact identity and cryptographic digest;
- model provenance/training source where known;
- runtime and model licenses;
- quantization/precision;
- model artifact bytes;
- language;
- local/offline inference requirement;
- CPU/accelerator requirements;
- expected/observed architecture support relevant to the planned B2 environment;
- streaming integration path;
- C0 context/prompt/hotword state;
- deterministic/seed controls where applicable;
- thread/decode settings;
- VAD/endpointing settings;
- known limitations.

### Product configuration envelope

B1 must define a justified first-product envelope before selecting exact model configurations.

The envelope may use one or a small number of explicit resource tiers. It must be based on local terminal-product constraints, not on which candidate appears likely to win.

At minimum define:

- maximum model/download artifact footprint per tier;
- whether CPU-only operation is mandatory for the tier;
- treatment of hardware acceleration;
- memory/resource qualification rule;
- whether a configuration requiring a non-redistributable or non-commercial model is eligible for first-product recommendation;
- maximum number of configurations admitted per family/tier;
- tie/exclusion rule if multiple models satisfy the same tier.

Do not choose a resource tier from primary developer test results.

## Non-comparative qualification smoke

B1 may perform a small public/synthetic smoke decode only to establish that a pinned configuration can be installed, launched, and produce a parseable transcript in the proposed harness environment.

Smoke requirements:

- the audio must be explicitly outside the future primary benchmark test split;
- smoke output must not be used to rank candidates;
- no per-candidate tuning based on smoke wording beyond correcting an invalid/nonfunctional configuration;
- any material configuration correction must be recorded before the B2 attempt manifest freezes.

A smoke PASS means only that the qualified path executed the smoke contract. It does not establish developer-speech accuracy or streaming quality.

## Streaming-semantics qualification contract

For each surviving configuration, B1 defines how B2 will classify observed behavior:

- `NATIVE_INCREMENTAL`
- `CHUNKED_REDECODE`
- `BATCH_ONLY`
- `UNKNOWN`

B1 must document the observable criteria used to distinguish the states. Upstream marketing or a package name containing `streaming` is insufficient by itself.

Where an adapter is required to normalize events for research, it must expose raw backend events/timestamps and must not fabricate a partial/final distinction unavailable from the backend.

## Corpus design contract

B1 must freeze the corpus methodology before B2 decodes the primary test split.

### Panels

The methodology should distinguish at least:

1. **Developer Entity Panel** — human speech containing technical entities and ordinary surrounding language;
2. **General/Collateral Panel** — human speech useful for detecting context/model improvements that damage ordinary language;
3. **Smoke Panel** — synthetic/public audio used only for harness/install regression, excluded from primary ranking.

A public existing corpus may contribute to the collateral panel if licensing, preprocessing, and sampling are frozen. It does not replace the human developer-entity panel.

### Human recording requirements

B1 must define:

- minimum speaker and utterance counts or an explicit statistical rationale for another design;
- speaker/cadence/accent diversity targets;
- recording instructions and microphone/environment metadata;
- informed-consent record format;
- raw-audio retention policy;
- redistribution license/permission required for public reproducibility;
- withdrawal/correction policy before an attempt freezes;
- prohibition on credentials, secrets, proprietary repository content, or sensitive material.

If public redistribution permission is unavailable for the primary audio, B1 must state what claims become impossible or require a different corpus.

### Split discipline

Define development/qualification/test separation before decoding.

The primary test manifest must be cryptographically frozen. Exact candidate configuration and scoring rules must freeze before primary test outputs are inspected.

The repository may contain the test scripts/content publicly; the discipline is that an attempt cannot tune itself after its own test observations.

## Developer-entity annotation contract

B1 must define a machine-readable annotation schema capable of representing:

- utterance id;
- canonical reference transcript;
- entity spans/classes;
- exact expected entity text including case/punctuation where semantically material;
- permitted preregistered normalization, if any;
- spoken form/alias when needed to explain the script;
- repository/archetype binding;
- ambiguity/distractor metadata;
- panel/split identity.

Entity classes must cover the founding WB-ENTITY contract, including paths, identifiers, packages/modules, CLI flags, Git refs/SHAs/versions, tests, database identifiers, and other bounded developer entities.

## Canonical audio preprocessing contract

B1 must specify a one-time preprocessing path that produces the exact audio consumed by candidates.

Record at minimum:

- source file format;
- canonical sample rate;
- channel count;
- sample/PCM representation;
- resampling tool/library and exact version;
- amplitude/loudness operation, if any;
- silence-trimming policy;
- per-file cryptographic digest;
- canonical duration;
- streaming feed/chunk schedule or the rule by which backend scheduling is derived.

Backend-specific preprocessing that changes primary audio content is forbidden in C0 unless isolated as a separate non-primary condition.

## C0 contract — unbiased local STT

B1 freezes how repository/test-specific decoder context is disabled for every candidate.

For each candidate explicitly record the C0 state of:

- prompt/initial prompt;
- hotwords/keyterms/context;
- grammar/constrained decoding;
- previous-text carryover;
- VAD/endpointing;
- temperature/beam/search settings;
- language selection/detection;
- punctuation behavior where configurable;
- timestamps/partial-result settings.

If a candidate cannot disable a feature that materially changes the comparison, preserve that limitation and decide before B2 whether the configuration remains eligible.

## C1 contract — deterministic repository resolver

B1 must define the interface and freeze procedure for the future engine-agnostic resolver without implementing/tuning it against B2 test outputs.

The contract must require:

- one resolver implementation/config across C0 transcripts;
- a deterministic bounded repository-candidate extraction rule;
- no expected-answer lookup or target-specific context injection;
- explicit candidate budgets;
- inspectable score/evidence per proposed binding;
- ambiguity state rather than forced binding;
- unsafe false-binding measurement;
- frozen resolver/scoring revision before B3 test evaluation.

The exact resolver algorithm may be implemented/refined in B3 after B2, but its evaluation contract and anti-leakage boundary are defined here.

## C2 contract — backend-native context

B1 records which qualified candidates expose documented/observable native context mechanisms but does not enable them in C0.

For B3, any C2 condition must:

- derive terms/context from the same bounded repository source contract;
- freeze native feature configuration before C2 test decoding;
- compare against the same backend's C0 configuration/audio;
- report target-entity uplift and non-target degradation;
- report false bias on distractors;
- remain backend-specific rather than being used as if equivalent across engines.

## Metrics and normalization

B1 must define exact scoring code/contract for at least:

- developer entity exact-match accuracy;
- entity normalized accuracy, if normalization is permitted;
- entity insertion/deletion/substitution counts;
- ordinary WER/collateral error;
- failure/timeout count;
- false entity insertion rate.

For C1 also define:

- repository-binding accuracy;
- ambiguity detection rate;
- unsafe false-binding rate.

For qualified streaming/performance panels, define timestamps/statistics only when the environment and backend semantics make them comparable.

Normalization rules must not turn case-sensitive identifiers, flags, paths, or other semantically distinct entities into false matches unless the specific normalization is explicitly justified and reported separately from exact match.

## Performance methodology contract

B1 must distinguish correctness/accuracy environments from performance environments.

A performance panel must record:

- machine model/CPU/GPU/NPU;
- RAM;
- OS/version;
- power mode where material;
- runtime/model configuration;
- thread count;
- cold/warm state;
- repetition count;
- raw run-level timing/resource outputs.

Shared GitHub-hosted runner timings are diagnostic by default and cannot establish general comparative superiority.

## Attempt manifest

B1 must define a machine-readable manifest schema that binds one B2 attempt to:

- canonical Wispral commit;
- B1 contract revision;
- candidate runtime/model digests;
- corpus manifests/digests;
- preprocessing revision/config;
- C0 configuration for every candidate;
- scorer revision/config;
- execution environment(s);
- allowed/excluded panels;
- attempt id;
- freeze timestamp;
- invalidation rules.

The manifest must make it possible to determine whether a later run changed a material input.

## Recommendation discipline

B1 defines the vocabulary and selection rule before results exist.

At minimum the future synthesis can classify exact configurations as:

- `LEADING`
- `CONTENDER`
- `REJECTED`
- `INSUFFICIENT_EVIDENCE`

B1 must define what those words mean. It should prefer transparent hard gates plus Pareto/non-dominance reasoning over one opaque weighted score.

A final single winner is not mandatory if evidence shows an irreducible resource/accuracy/latency tradeoff.

## In scope

- current candidate/source/license/model metadata research;
- runtime/model pinning rules;
- non-comparative install/smoke qualification where useful;
- corpus/schema/consent/license contract;
- preprocessing contract;
- score/metric schema;
- context-condition separation;
- streaming-semantics taxonomy;
- performance methodology;
- attempt-manifest/invalidation contract;
- B2 readiness gate.

## Out of scope

- primary developer test-set decoding;
- comparative candidate ranking;
- production microphone/audio code;
- production Rust speech adapter or permanent dependency;
- repository resolver implementation tuned against primary outputs;
- C2 native-bias comparative execution;
- turn detection or barge-in;
- TTS/AEC/wake word;
- training/fine-tuning;
- public accuracy/latency superiority claims;
- permanent STT selection.

## Acceptance conditions

000B1 is `VERIFIED` only when:

1. the live candidate families are revalidated and exact qualification inputs are pinned;
2. runtime/model provenance and license requirements are explicit;
3. product configuration envelope/tier rules are fixed before primary test decoding;
4. corpus panels, human-audio requirements, consent/redistribution rules, and split discipline are fixed;
5. canonical audio preprocessing/digest rules are fixed;
6. C0/C1/C2 separation is unambiguous;
7. streaming-semantics observable criteria are fixed;
8. metric/scorer schemas and normalization rules are fixed;
9. performance-environment and hosted-runner limitations are fixed;
10. attempt manifest and invalidation rules are machine-readable or deterministically specified;
11. any qualification smoke is clearly non-comparative and preserved with exact inputs;
12. the resulting B2 entry gate can be evaluated without inventing missing information;
13. no primary benchmark ranking or product support claim has been made.

## Readiness gate

Before B1 itself can move from `GRAIN` to `READY`, recheck:

- this specification and 000B parent are canonical;
- current candidate repositories/releases remain publicly accessible;
- required license/provenance information can be obtained without accepting undisclosed terms;
- no task requires proprietary benchmark data or secrets;
- any smoke audio is license-clear and outside the future primary test split;
- research tooling can remain isolated from production architecture;
- no primary test decoding is required to complete B1.

If a condition fails, record `BLOCKED` and refine rather than silently broadening B1.