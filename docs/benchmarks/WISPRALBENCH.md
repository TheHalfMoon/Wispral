# WispralBench — Founding Benchmark Contract

**Status:** methodology candidate; no benchmark result exists yet

WispralBench measures the parts of voice-agent control that ordinary word-error-rate benchmarks miss. It is intended first as Wispral's internal evidence harness and, only after methodology hardening, as a public benchmark for the broader ecosystem.

## 1. Principles

1. A benchmark must measure a user-relevant contract, not merely a convenient model metric.
2. Developer entities are scored separately from ordinary words.
3. Latency is decomposed into instrumented stages.
4. Warm and cold conditions are reported separately.
5. Hardware, OS, model/runtime versions, configuration, and network conditions are recorded.
6. Raw outputs and scoring code must be preserved for independently reproducible public claims.
7. Failed runs, timeouts, and losing metrics remain visible.
8. No hidden test content may be inspected or tuned against after a preregistered comparison begins.

## 2. Benchmark families

### WB-ENTITY — Developer Entity Accuracy

Measures exact or contract-defined recognition/resolution of developer-specific entities.

Entity classes include:

- file and directory paths;
- Rust/Python/TypeScript and mixed-language identifiers;
- camelCase, PascalCase, snake_case, kebab-case, SCREAMING_SNAKE_CASE;
- package/crate/module names;
- CLI commands and flags;
- Git branches, tags, refs, and abbreviated SHAs;
- versions and semantic-version ranges;
- test names;
- database/table/field names;
- URLs and issue/PR references where appropriate.

Example fixtures may contain terms such as:

```text
src/auth/middleware.rs
validate_token
serde_json
--no-default-features
feature/auth-refresh
HEAD~2
AuthMiddleware
NEXT_PUBLIC_API_URL
```

Metrics:

- entity exact-match accuracy;
- normalized entity accuracy where a normalization rule is preregistered;
- entity deletion/substitution/insertion rate;
- entity confidence calibration where available;
- repository-binding accuracy;
- ambiguity detection rate;
- unsafe false-binding rate.

### WB-CONTEXT — Repository Context Value

Compares controlled conditions such as:

- STT without repository vocabulary;
- STT with bounded vocabulary/keyterms;
- transcript plus deterministic repository candidate resolution;
- full proposed Wispral context path.

Primary question:

> Does bounded repository context improve developer-entity correctness enough to justify its latency, complexity, privacy surface, and maintenance cost?

The experiment must prevent test-corpus leakage into runtime dictionaries beyond the preregistered context-generation rule.

### WB-TURN — Turn Detection and Pause Robustness

Measures whether Wispral distinguishes a natural thinking pause from an actual end of turn.

Corpus classes include:

- short commands;
- long technical instructions;
- deliberate mid-sentence pauses;
- self-correction after a pause;
- filler words;
- non-native cadence;
- quiet speech;
- background noise;
- no-speech activation;
- accidental ambient speech.

Metrics:

- premature-end rate;
- late-end latency;
- missed-speech-start rate;
- false-speech-start rate;
- end-of-turn decision latency;
- user-correction preservation.

### WB-INTERRUPT — Barge-in and Cancellation

Requires event timestamps from the Wispral runtime.

Candidate timestamps:

```text
T0 user speech onset observed
T1 local output suppression requested
T2 local output becomes inaudible/stopped
T3 agent cancellation request emitted
T4 agent cancellation acknowledged, if protocol exposes it
T5 new utterance finalization
T6 new instruction dispatched
```

Metrics:

- T0 -> T2 audible-stop latency;
- T0 -> T3 cancellation-request latency;
- T0 -> T4 acknowledged cancellation latency where observable;
- stale agent output emitted after cancellation request;
- session continuity success;
- cancellation failure classification.

A protocol that cannot acknowledge cancellation must be reported as such rather than assigned fabricated acknowledgement latency.

### WB-LATENCY — End-to-End Spoken Instruction Latency

Candidate timestamps:

```text
speech onset
speech end
end-of-turn decision
first partial transcript
final transcript
entity resolution complete
policy complete
instruction dispatch
agent acknowledgement
first agent update/token/event
```

Report distributions, not only averages. At minimum include median, p90, p95, sample count, and failure count where sample size supports them.

### WB-RESOURCE — Local Runtime Cost

Measures:

- idle CPU;
- active capture CPU;
- STT CPU/GPU utilization where observable;
- memory resident set;
- model footprint;
- startup time;
- battery/power proxy only if a defensible method is available.

### WB-AGENT — Agent Compatibility

For each tested agent/version/protocol path, record capabilities rather than a single `supported=yes/no` label.

Candidate capability fields:

- discovery/startup;
- authentication path;
- new session;
- resume session;
- prompt dispatch;
- streaming updates;
- tool/action events;
- structured permission requests;
- cancellation request;
- cancellation acknowledgement/observable stop;
- attachments/context;
- error propagation;
- graceful shutdown;
- protocol version.

### WB-INSTALL — Time to First Voice Turn

Measures a clean supported environment from documented installation start to the first successfully dispatched and acknowledged spoken instruction.

Must separate download/model-fetch time, authentication time, setup interaction time, and first runtime startup.

## 3. STT bakeoff

Specification 000 should evaluate candidate local backends without preselecting a winner. Initial candidates may include:

- Moonshine streaming models;
- whisper.cpp;
- sherpa-onnx or another justified on-device baseline;
- one strong cloud streaming reference when permitted, as a quality/latency reference rather than a mandatory dependency.

Each backend must be pinned to exact versions/model artifacts and run under comparable capture/resampling conditions where technically possible.

A backend may win one dimension and lose another. Selection uses a documented decision function rather than a single leaderboard number.

## 4. Corpus design

The founding corpus should include:

- synthetic, license-clear utterance scripts;
- multiple repository archetypes;
- technical tokens not present in generic conversational corpora;
- command and aside-like speech;
- corrections and abandoned phrases;
- pronunciation variants;
- English baseline plus an explicit path to multilingual evaluation;
- Arabic as a planned language qualification target, not an unverified founding support claim.

Recorded human audio, if used, requires explicit consent, retention rules, and redistribution permission appropriate to the benchmark artifact.

## 5. Hardware matrix

Do not imply cross-platform performance from one development machine.

The eventual matrix should include representative:

- Apple Silicon macOS;
- x86_64 Linux;
- Windows 11;
- CPU-only local inference;
- accelerated local inference where supported.

Specification 000 may begin with fewer machines if limitations are explicit.

## 6. Statistical and reporting rules

- State sample size.
- Preserve run-level data.
- Separate warm/cold results.
- Do not silently remove outliers; document and justify exclusion rules before the run when possible.
- Report errors/timeouts as outcomes.
- Do not compare numbers produced by materially different corpora as though they were one head-to-head result.
- Distinguish measured values from estimates.

## 7. Claim gate

A README or launch claim derived from WispralBench requires:

1. committed methodology;
2. exact source/model/config revisions;
3. raw machine-readable results;
4. scoring implementation;
5. limitations;
6. a statement of what the result does NOT prove;
7. review that the marketing wording does not exceed the benchmark evidence.

## 8. Founding non-results

As of this document, WispralBench has run zero qualifying benchmark cells. There is no winning STT backend, latency result, accuracy result, compatibility result, or comparative superiority claim.