# Specification 000B2 Tasks — Reproducible Public-Corpus STT Bakeoff

## Authority condition

These execution tasks become authorized only after the public-corpus amendment and frontier reconciliation are canonical on `main`.

## Phase P — public corpus and attempt freeze

- [x] `B2P01` Record exact OpenSLR SLR12 source/license facts and official checksums in machine-readable provenance.
- [x] `B2P02` Materialize `test-clean.tar.gz` and `test-other.tar.gz` from an approved source or official mirror; verify official MD5 and record exact archive SHA-256.
- [x] `B2P03` Implement deterministic speaker/utterance subset selection independent of candidate outputs.
- [x] `B2P04` Freeze selected public-human subset manifest and manifest digest before candidate decoding.
- [x] `B2P05` Revalidate the six canonical candidate cells and artifact/runtime/model identities against live canonical evidence.
- [x] `B2P06` Capture attempt-bound FFmpeg `9.0.1` preprocessing identity/configuration and execution evidence.
- [x] `B2P07` Capture attempt-bound execution environment/hardware facts and preserve `CONTROLLED` versus `DIAGNOSTIC` semantics.
- [x] `B2P08` Freeze final pre-decode attempt manifest and verify `primary_decoding_started=false` at freeze.

## Phase E — public-human C0 execution

- [ ] `B2E01` Decode the frozen P0 public-human subset with candidate cell 1 under C0.
- [ ] `B2E02` Decode the identical frozen P0 subset with candidate cell 2 under C0.
- [ ] `B2E03` Decode the identical frozen P0 subset with candidate cell 3 under C0.
- [ ] `B2E04` Decode the identical frozen P0 subset with candidate cell 4 under C0.
- [ ] `B2E05` Decode the identical frozen P0 subset with candidate cell 5 under C0.
- [ ] `B2E06` Decode the identical frozen P0 subset with candidate cell 6 under C0.
- [ ] `B2E07` Preserve raw transcripts, failures, timeouts, runtime observations, and exact run identities for every cell.
- [ ] `B2E08` Score frozen P0 outputs using the preregistered normalization/scoring contract without result-driven changes.

## Phase D — optional developer-term diagnostic

- [ ] `B2D01` Decide whether a deterministic synthetic renderer can be qualified without adding a product dependency.
- [ ] `B2D02` If qualified, freeze renderer provenance/configuration, developer prompt material, and rendered-audio digests before candidate decoding; otherwise record `NOT_RUN`.
- [ ] `B2D03` If qualified, execute D0 for every included candidate using identical rendered audio.
- [ ] `B2D04` Preserve D0 raw outputs and diagnostic entity/token scores separately from P0.

## Phase S — synthesis and closeout

- [ ] `B2S01` Produce machine-readable results with P0 and D0 strictly separated.
- [ ] `B2S02` Classify cells as `LEADING_PUBLIC_BASELINE`, `CONTENDER_PUBLIC_BASELINE`, `REJECTED`, or `INSUFFICIENT_EVIDENCE` under the frozen rule.
- [ ] `B2S03` Publish the bounded report with failures, losing metrics, environment limitations, and `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`.
- [ ] `B2S04` Produce canonical closeout candidate with exact evidence references and no product selection claim.
- [ ] `B2S05` Run exact-head applicable CI and evidence verification.
- [ ] `B2S06` Obtain fresh independent substantive semantic review on exact head.
- [ ] `B2S07` Resolve all actionable review threads and reconcile head/base/mergeability.
- [ ] `B2S08` Guarded expected-head merge.
- [ ] `B2S09` Verify post-merge workflows and reread canonical authority before refining B3.

## Explicitly prohibited during B2

- collecting new private participant recordings as a requirement for this execution lane;
- representing public audiobook speech as developer speech;
- representing synthetic developer speech as human speech;
- changing subset membership after candidate results are visible;
- changing scorer/normalization rules after result inspection within the same attempt;
- production STT integration;
- permanent Rust/Cargo speech dependency;
- README/product superiority claims beyond the exact evidence.
