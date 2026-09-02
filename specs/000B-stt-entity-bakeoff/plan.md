# Specification 000B Plan

## Execution model

000B is a recursive research specification. Each child becomes executable only after the previous canonical evidence is reread and the child independently satisfies Definition of Grain and readiness.

The ordering deliberately prevents model/configuration tuning after comparative benchmark outputs are visible.

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

## Phase B2A — Historical private developer-speech route

Child: `000B2-unbiased-stt-bakeoff` — preserved historical route.

Purpose:

- instantiate the original B1 private human developer-speech contract;
- freeze exact runtime/model artifacts and attempt manifest;
- validate corpus availability and consent/licensing;
- run C0 with repository/test-specific decoder context disabled;
- preserve raw transcripts, timing events that B1 qualifies, failures, resource records, and scoring outputs;
- produce a raw-STT developer-speech evidence matrix without context-resolution uplift.

This route remains `BLOCKED_EXTERNAL` while its real participant/media authority and human-corpus gates are unsatisfied. Public audiobook speech or synthetic/TTS media must not be promoted into this route's human developer-speech ranking.

## Phase B2B — Public-corpus execution successor

Child: `000B2-public-corpus-bakeoff` — executable only after its bounded amendment becomes canonical.

Purpose:

- preserve B1 candidate/runtime/model provenance while changing only the evidence population and claim boundary prospectively;
- freeze exact OpenSLR LibriSpeech source/license/checksum and fetched-byte provenance;
- freeze a deterministic public-human ordinary read-English subset before any candidate output is observed;
- freeze exact runtime/model artifacts, preprocessing, environment capture, scorer/configuration, and attempt manifest before comparative decoding;
- run C0 with repository/test-specific decoder context disabled and identical canonical audio across candidates;
- preserve raw transcripts, failures, runtime observations, and ordinary-speech scoring outputs;
- optionally execute a separately frozen synthetic developer-term lane as `DIAGNOSTIC_ONLY`;
- preserve `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT` throughout synthesis.

This public successor may produce a bounded public-baseline shortlist or `INSUFFICIENT_EVIDENCE`. It cannot satisfy, rewrite, or silently cancel the missing private human developer-speech evidence.

## Phase B3 — Repository-context uplift

Child: `000B3-context-uplift` — coarse until evidence-selected B2 output is canonical.

Purpose:

- consume frozen C0 transcripts rather than silently re-running a tuned STT configuration;
- execute the engine-agnostic deterministic C1 repository resolver only on evidence whose population/claim boundary remains explicit;
- measure entity-binding improvement, ambiguity behavior, and unsafe false binding where the underlying material supports those metrics;
- optionally execute backend-native C2 context/hotword/prompt conditions where supported and preregistered;
- report C2 only as within-backend uplift/degradation relative to the same backend C0.

B3 must inherit the limitations of its B2 inputs. Public audiobook transcripts and synthetic developer-term diagnostics cannot be relabeled as genuine human developer-speech accuracy.

## Phase B4 — STT synthesis

Child: `000B4-stt-synthesis` — coarse until B3 or the evidence-selected terminal child is canonical.

Purpose:

- reconcile raw recognition, streaming semantics, context value, resource/performance evidence, provenance, licensing, and failure modes;
- identify non-dominated configurations only within supported evidence populations;
- recommend a bounded first-product shortlist or `INSUFFICIENT_EVIDENCE`;
- record what additional evidence 000G would still need;
- explicitly preserve missing human developer-speech evidence when it remains absent.

B4 cannot authorize product implementation. It supplies evidence to the founding parent and 000G.

## Attempt discipline

A comparative attempt has two boundaries:

### Qualification boundary

Before comparative decoding:

- candidate families are fixed;
- exact runtime/model artifacts are fixed;
- build/install configuration is fixed;
- C0 decoding configuration is fixed;
- corpus source, preprocessing, and test manifest are fixed;
- scoring code/config is fixed;
- hardware/performance panel configuration is fixed where applicable.

### Observation boundary

After comparative outputs are inspected:

- do not change model size, quantization, prompts, hotwords, thresholds, beam settings, threads, VAD/endpointing configuration, corpus membership, preprocessing, normalization, or scoring rules within the same attempt;
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
- the selected route's corpus source/authority requirements cannot be satisfied;
- the historical private route lacks its required participant/media authority;
- the public successor lacks exact public source/license/checksum provenance or a pre-output deterministic subset freeze;
- a candidate requires network inference for the local C0 path;
- the same canonical audio cannot be supplied without materially different backend-specific preprocessing;
- comparative content/configuration was inspected and then tuned without starting a new attempt;
- benchmark code changes after a frozen attempt without invalidating/restarting it;
- resource/performance claims would rely on uncontrolled timing;
- execution would require product architecture or permanent dependencies not authorized by Specification 000.

## Closeout

After each child merges:

1. reread canonical `main` and the complete active authority chain;
2. reconcile `specs/CURRENT.md` and parent state as a separate closeout when required;
3. refine only the next evidence-selected child;
4. keep later children coarse if new evidence can materially alter them.