# Specification 000B2 Plan — Reproducible Public-Corpus STT Bakeoff

## Execution order

1. Freeze upstream corpus provenance.
2. Materialize and verify exact archive bytes.
3. Freeze deterministic public-human subset selection logic and manifest.
4. Freeze the attempt state, scorer/configuration, preprocessing identity, and execution-environment capture.
5. Revalidate all candidate artifact/runtime identities from canonical evidence.
6. Execute P0 public-human C0 decoding for every included candidate against identical audio bytes.
7. Optionally execute D0 deterministic synthetic developer-term stress after its renderer/material freeze.
8. Score without changing candidate membership, decoding settings, corpus membership, or scorer rules.
9. Preserve raw outputs, failures, and losing metrics.
10. Produce a bounded B2 report and machine-readable closeout.
11. Qualify exact head with applicable CI and independent substantive semantic review.
12. Guarded merge, post-merge verification, canonical reread, then refine B3 only from the settled evidence.

## Corpus provenance freeze

Use OpenSLR SLR12 LibriSpeech test material:

- `test-clean.tar.gz` — official MD5 `32fa31d27d2e1cad72775fee3f4849a9`;
- `test-other.tar.gz` — official MD5 `fb5a50374b501bb3bac4815ee91d3135`;
- license recorded as `CC BY 4.0` from the OpenSLR resource page.

Execution must also record SHA-256 of the exact fetched bytes.

## Deterministic subset

The subset builder must operate before candidate decoding and must not use candidate outputs.

The selection algorithm must:

- enumerate speakers and utterances deterministically from extracted corpus metadata;
- select a bounded number of speakers from both clean and other partitions using a frozen deterministic hash ordering;
- select a bounded number of utterances per selected speaker using the same frozen ordering;
- reject overlap or missing transcript/audio pairs;
- emit a manifest containing source partition, speaker ID, chapter ID, utterance ID, reference transcript, source file path, source-file SHA-256, and canonical preprocessed-file SHA-256 once preprocessing is captured;
- emit a deterministic manifest digest.

The exact counts belong to the execution task and must be frozen before comparative decode. A target of 12 speakers from each public partition with up to 10 utterances per speaker is the default bounded design, subject only to pre-decode structural validation.

## Candidate execution

Reuse the canonical six candidate cells from B1/B2 entry preparation. Revalidation must fail closed on identity or material drift.

All candidates receive identical P0 audio bytes and no repository/test-specific C0 decoder context.

## Scoring

Use the canonical scorer where its contract applies. Add only the minimum public-corpus WER adapter needed to transform LibriSpeech reference/candidate transcript pairs into deterministic scorer inputs.

Any new normalization must be frozen and regression-tested before comparative decoding.

## Developer-term stress

D0 is optional and diagnostic. If executed, create a separately reviewed material freeze containing:

- developer prompt list;
- renderer project/version/source revision;
- exact voice/configuration identity;
- renderer license/provenance;
- deterministic rendering commands;
- output WAV SHA-256 values.

D0 must never be merged numerically into P0 as one human accuracy score.

## Environment and chronology

Before comparative candidate decoding, capture:

- attempt state = `PRE_PRIMARY_CAPTURE`;
- FFmpeg `9.0.1` identity/configuration when preprocessing is used;
- OS, architecture, CPU, memory, accelerator visibility, runtime versions, and relevant environment facts;
- whether the environment is `CONTROLLED` or `DIAGNOSTIC` according to the existing contract.

Do not infer control merely because metadata was captured.

## Evidence outputs

Expected bounded evidence surfaces include:

- `research/000b2-public/corpus-source.json`;
- `research/000b2-public/subset-manifest.json`;
- `research/000b2-public/attempt-manifest.json`;
- `research/000b2-public/raw/<candidate>/...` or an equivalent bounded artifact index;
- `research/000b2-public/results.json`;
- `docs/research/stt/000b2-public-corpus-report.md`;
- `research/000b2-public/canonical-closeout.json`.

Large upstream audio/model binaries must not be committed merely for reproducibility; record exact source identities and cryptographic digests instead.

## Merge gates

Before merge of comparative evidence:

- candidate head is immutable and reconciled;
- all applicable checks succeed on exact head;
- a fresh independent reviewer examines the exact comparative evidence and claim boundaries;
- all actionable review threads are resolved;
- no late result-driven methodology change is introduced;
- expected-head guarded merge is used where available.
