# Specification 000B Plan

## Execution model

000B is a recursive research specification. Each child becomes executable only after the previous canonical evidence is reread and the child independently satisfies Definition of Grain and readiness.

The ordering deliberately prevents model/configuration tuning after primary benchmark outputs are visible.

## Phase B1 — Benchmark and candidate qualification

Child: `000B1-benchmark-candidate-qualification`

Purpose:

- freeze the measurement contract before comparative decoding;
- qualify candidate runtime/model provenance without choosing a winner;
- define a bounded product configuration envelope;
- define human-audio, consent, licensing, split, preprocessing, and digest rules;
- define the C0/C1/C2 condition separation;
- define streaming-semantics states;
- define metric/scoring/selection rules and failure handling;
- define controlled performance-environment requirements;
- define the attempt-manifest freeze procedure.

B1 may inspect upstream distributions, model metadata, licenses, build/install paths, and small non-comparative fixtures where needed for qualification. It must not decode the primary benchmark test split or report a comparative STT ranking.

## Phase B2 — Unbiased local STT bakeoff

Child: `000B2-unbiased-stt-bakeoff` — coarse until B1 is canonical.

Purpose:

- instantiate the B1 contract;
- freeze exact runtime/model artifacts and attempt manifest;
- validate corpus availability and consent/licensing;
- run C0 with repository/test-specific decoder context disabled;
- preserve raw transcripts, timing events that B1 qualifies, failures, resource records, and scoring outputs;
- produce a raw-STT evidence matrix without context-resolution uplift.

If B1's human-audio readiness requirement cannot be satisfied, B2 must remain `BLOCKED_EXTERNAL` rather than promote synthetic smoke evidence into the primary ranking.

## Phase B3 — Repository-context uplift

Child: `000B3-context-uplift` — coarse until B2 is canonical.

Purpose:

- consume frozen C0 transcripts rather than silently re-running a tuned STT configuration;
- execute the engine-agnostic deterministic C1 repository resolver;
- measure entity-binding improvement, ambiguity behavior, and unsafe false binding;
- optionally execute backend-native C2 context/hotword/prompt conditions where supported and preregistered;
- report C2 only as within-backend uplift/degradation relative to the same backend C0.

B3 must not hide context-induced false positives or ordinary-language degradation.

## Phase B4 — STT synthesis

Child: `000B4-stt-synthesis` — coarse until B3 or the evidence-selected terminal child is canonical.

Purpose:

- reconcile raw recognition, streaming semantics, context value, resource/performance evidence, provenance, licensing, and failure modes;
- identify non-dominated configurations;
- classify configurations using the B1 preregistered recommendation vocabulary;
- recommend a bounded first-product shortlist or `INSUFFICIENT_EVIDENCE`;
- record what additional evidence 000G would still need.

B4 cannot authorize product implementation. It supplies evidence to the founding parent and 000G.

## Attempt discipline

A comparative attempt has two boundaries:

### Qualification boundary

Before primary test decoding:

- candidate families are fixed;
- exact runtime/model artifacts are fixed;
- build/install configuration is fixed;
- C0 decoding configuration is fixed;
- corpus preprocessing and test manifest are fixed;
- scoring code/config is fixed;
- hardware/performance panel configuration is fixed where applicable.

### Observation boundary

After primary test outputs are inspected:

- do not change model size, quantization, prompts, hotwords, thresholds, beam settings, threads, VAD/endpointing configuration, preprocessing, normalization, or scoring rules within the same attempt;
- preserve losing and failed cells;
- any material correction creates a new attempt with a new manifest/digest.

## Evidence states

Use explicit states when applicable:

- `OBSERVED`
- `DOCUMENTED_NOT_OBSERVED`
- `UNSUPPORTED`
- `NOT_TESTED`
- `BLOCKED_EXTERNAL`
- `FAILED`
- `INVALID`
- `UNKNOWN`

A candidate excluded by the preregistered product envelope is not a benchmark loser; record it as an exclusion with rationale.

## Reproducibility hierarchy

Prefer, in order:

1. immutable runtime/model/corpus artifacts with cryptographic digests;
2. tagged releases plus exact commit/model identifiers;
3. pinned source revisions with reproducible build commands;
4. mutable URLs only as discovery inputs, never as sole attempt identity.

## Performance evidence rule

Accuracy and deterministic transcript reproduction may run in environments that do not provide stable performance timing, provided exact runtime/configuration is preserved and the claim does not depend on speed.

Latency/resource comparisons require a controlled named machine/environment. Shared hosted-runner timing is diagnostic only unless a separately justified methodology demonstrates comparability.

## Stop conditions

Stop and record the exact state rather than improvising if:

- model/runtime provenance or licensing cannot be established;
- candidate artifacts cannot be pinned;
- the primary human-audio panel lacks required consent/redistribution authority;
- a candidate requires network inference for the local C0 path;
- the same canonical audio cannot be supplied without materially different backend-specific preprocessing;
- primary test content/configuration was inspected and then tuned without starting a new attempt;
- benchmark code changes after a frozen attempt without invalidating/restarting it;
- resource/performance claims would rely on uncontrolled timing;
- execution would require product architecture or permanent dependencies not authorized by Specification 000.

## Closeout

After each child merges:

1. reread canonical `main` and the complete active authority chain;
2. reconcile `specs/CURRENT.md` and parent state as a separate closeout when required;
3. refine only the next evidence-selected child;
4. keep later children coarse if new evidence can materially alter them.