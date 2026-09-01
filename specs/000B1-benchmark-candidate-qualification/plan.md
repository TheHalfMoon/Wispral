# Specification 000B1 Plan

## Execution model

B1 is a preregistration/qualification Grain. It may inspect candidate metadata and perform bounded non-comparative smoke qualification, but it ends before any primary developer test split is decoded.

The plan uses a hard observation boundary: once the B2 attempt manifest freezes, configuration changes require a new attempt.

## Phase 1 — Revalidate live authority

Re-read canonical Wispral authority and current external candidate truth.

Record exact current:

- Moonshine runtime release/source revision/model catalog/license context;
- whisper.cpp release/source revision/model-artifact catalog/license context;
- sherpa-onnx runtime release/source revision and selected online-model provenance/license context;
- any material deprecation, security, license, or distribution change since refinement.

Do not silently substitute a new candidate family.

## Phase 2 — Define product configuration envelope

Before examining any primary developer benchmark outputs, decide the local product constraints used to qualify exact models.

Possible dimensions include:

- artifact-download footprint;
- memory envelope;
- CPU-only expectation;
- optional acceleration tier;
- redistribution/license eligibility;
- local inference after artifact download;
- maximum configurations per family/tier.

Document why the envelope is plausible for Wispral's terminal-native first-product hypothesis.

## Phase 3 — Qualify exact runtime/model configurations

For each mandatory family:

1. enumerate candidate model configurations that satisfy the envelope;
2. apply the preregistered tie/selection rule;
3. pin exact runtime/model artifacts and digests;
4. record build/install instructions;
5. record C0 settings;
6. record native context capabilities separately for future C2;
7. classify provenance/license confidence;
8. preserve any exclusion reason.

Do not use Wispral primary test audio for this phase.

## Phase 4 — Optional non-comparative smoke

Where needed to prove a qualified path is actually executable:

- use one or more public/license-clear smoke clips excluded from all primary scoring;
- validate install/model load/decode/artifact parsing;
- preserve exact commands and outputs;
- do not compare smoke transcripts across candidates as a ranking.

A smoke failure may reveal an invalid pin/build path. Correcting it before attempt freeze is allowed when the correction and prior failure are preserved.

## Phase 5 — Freeze corpus/consent contract

Define:

- panels and intended use;
- minimum sample/speaker rationale;
- speaker diversity/recording instructions;
- human consent and redistribution terms;
- test content exclusions;
- split generation/freeze;
- entity annotation schema;
- general/collateral panel source and license;
- smoke panel separation.

If human developer speech cannot be made available under the required evidence terms, B1 should still complete the contract and make B2's blocker machine-readable rather than weakening the primary evidence standard.

## Phase 6 — Freeze audio preprocessing contract

Select and pin the canonical preprocessing path and per-file digest scheme.

The same canonical output bytes must feed every C0 candidate.

## Phase 7 — Freeze C0/C1/C2 methodology

### C0

Define unbiased settings for each candidate and the cross-backend metrics.

### C1

Define the engine-agnostic repository resolver evaluation contract, candidate extraction budget, ambiguity/unsafe-binding metrics, and anti-leakage rules. The algorithm itself may be implemented in B3, but it cannot be tuned after B2 test labels/outputs reveal the desired answers.

### C2

Record available backend-native mechanisms and define the within-backend uplift/degradation contract without executing it yet.

## Phase 8 — Freeze streaming/performance taxonomy

Define observable criteria for:

- native incremental behavior;
- chunked re-decode;
- batch-only behavior;
- unknown behavior.

Define which timing/resource metrics are comparable in which environment. Hosted-runner timing remains diagnostic unless explicitly qualified.

## Phase 9 — Freeze scoring and recommendation rules

Produce deterministic scorer/schema contracts for:

- exact developer-entity accuracy;
- permitted normalized accuracy;
- insertion/deletion/substitution outcomes;
- ordinary WER/collateral error;
- failure/timeout handling;
- false entity insertion;
- future C1 binding/ambiguity/unsafe binding.

Define the future `LEADING`, `CONTENDER`, `REJECTED`, and `INSUFFICIENT_EVIDENCE` meanings before B2 results exist.

## Phase 10 — Freeze B2 attempt-manifest schema

The schema must bind all material benchmark inputs and define invalidation triggers.

Create a validation mechanism or deterministic checklist strong enough that B2 can fail closed when a frozen input drifts.

## Verification

Before B1 can be called complete:

- verify all candidate/source/model/license references against exact pinned sources;
- verify schemas parse deterministically;
- verify example manifests/corpus annotations satisfy the schema without containing primary benchmark results;
- verify no file contains a candidate ranking;
- verify no primary test audio/transcript output was decoded or scored;
- challenge whether the rules could permit post-result cherry-picking;
- independently reread candidate truth before final B1 closeout because the speech ecosystem is fast-moving.

## Handoff to B2

B1 does not automatically start B2.

After B1 evidence merges and canonical closeout is complete, re-read current authority and evaluate B2 readiness, including actual human-audio availability, exact artifact accessibility, and execution-environment availability.