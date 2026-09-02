# Specification 000B2 — Reproducible Public-Corpus STT Bakeoff

**State:** `READY` candidate; executable only after this specification and its frontier reconciliation are canonical on `main`  
**Parent:** `000B-stt-entity-bakeoff`  
**Type:** research / benchmark execution Grain  
**Supersedes for active execution:** the unstarted private 20-speaker collection path preregistered by `000B1`

## Outcome

Produce bounded, reproducible local-STT evidence without collecting new private participant media.

The execution uses openly distributed, pre-existing human speech for ordinary recognition evidence and a separately labeled deterministic synthetic developer-term stress lane for developer-token diagnostics. It may produce a candidate shortlist, reject candidates, or conclude `INSUFFICIENT_EVIDENCE`.

It MUST NOT claim human developer-speech accuracy, accent coverage, developer productivity, or general STT superiority from synthetic developer-term media.

## Why this supersession is valid

`000B1` remains canonical historical preregistration and is not rewritten. Its private 20-speaker / 720-utterance panel was never recorded and no primary attempt began.

The parent `000B` acceptance conditions already permit closure when human developer-speech evidence is absent, provided the absence is explicit enough to prevent a false ranking. The previous B2 execution path became externally blocked on private participant/media authority. This specification resolves that conflict explicitly by superseding only the unstarted active execution path, not prior evidence.

The historical human-authority files under `research/000b2-entry/authority/` remain preserved as evidence of the abandoned private-collection path. They are no longer an entry gate for this public-corpus execution lane.

## Human-speech baseline

The public-human lane uses LibriSpeech ASR corpus SLR12 from OpenSLR.

Canonical upstream facts at specification time:

- source page: `https://www.openslr.org/12/`;
- license: `CC BY 4.0`;
- `test-clean.tar.gz` official MD5: `32fa31d27d2e1cad72775fee3f4849a9`;
- `test-other.tar.gz` official MD5: `fb5a50374b501bb3bac4815ee91d3135`.

The execution MUST fetch from the documented OpenSLR resource surface or a separately recorded official mirror, verify the official archive checksum before extraction, compute and record SHA-256 for the exact fetched archive bytes, and freeze the selected utterance manifest before candidate decoding.

### Deterministic bounded subset

To keep the founding bakeoff tractable, the execution MUST derive one deterministic speaker-disjoint evaluation subset from `test-clean` and `test-other` before any candidate result is observed.

The subset-selection implementation, selection seed/material, selected speaker IDs, selected utterance IDs, transcript references, per-audio SHA-256 values, and resulting manifest SHA-256 MUST be committed and independently reviewable before comparative decoding.

No candidate-specific sample filtering is allowed.

## Developer-term diagnostic lane

A frozen developer-term panel MAY be rendered to deterministic synthetic speech only after the text panel, renderer identity, renderer configuration, voices, and output-file digests are frozen.

Synthetic developer-term results are `DIAGNOSTIC_ONLY`.

They MAY expose catastrophic vocabulary/tokenization behavior and MAY inform risk discussion, but they MUST NOT:

- be called human developer-speech accuracy;
- satisfy a human-accent or cadence claim;
- be mixed into ordinary public-human WER as if the populations were equivalent;
- authorize a general developer-speech superiority claim.

If no suitably reproducible synthetic renderer is qualified, the lane may be omitted and recorded as `NOT_RUN` without blocking the public-human baseline.

## Candidate scope

Reuse the six candidate cells and exact artifact/runtime provenance materialized by canonical B1/B2 entry preparation unless a separately reviewed pre-attempt amendment changes candidate membership.

C0 remains repository/test-specific decoder context OFF.

## Evidence lanes

### P0 — public-human ordinary speech

For the frozen LibriSpeech subset, preserve at minimum:

- exact reference transcript;
- exact candidate transcript;
- WER inputs and outputs;
- failure/timeout count;
- runtime/model/config identity;
- streaming-semantics classification where observed;
- startup/resource observations only with their environment limitations.

This lane supports only bounded ordinary read-English recognition evidence on the exact public subset.

### D0 — synthetic developer-term stress

If executed, preserve exact prompt text, renderer provenance, audio digest, candidate output, entity/token diagnostic scoring, and failures.

This lane supports diagnostic developer-term robustness observations only.

### C1/C2 boundary

Repository-context uplift remains a later child. B2 freezes raw C0 transcripts first. B3 may use those transcripts and separately frozen developer diagnostic material, while maintaining the same no-human-developer-accuracy boundary.

## Preprocessing

All candidate cells MUST consume audio derived through the same frozen preprocessing contract. FFmpeg `9.0.1` remains the required canonical normalizer where preprocessing is needed.

Attempt-bound preprocessing identity and execution-environment evidence MUST be captured before comparative decoding. The old external participant-authority gate is not part of this public-corpus lane.

## Performance boundary

GitHub-hosted runner timing is diagnostic only. General latency, CPU, memory, battery, or performance-superiority claims require separately controlled and disclosed hardware evidence.

## Decision rule

B2 MUST NOT manufacture a single opaque weighted winner.

The result may classify candidate cells as:

- `LEADING_PUBLIC_BASELINE`;
- `CONTENDER_PUBLIC_BASELINE`;
- `REJECTED`;
- `INSUFFICIENT_EVIDENCE`.

A leading public-baseline result is not a production dependency selection and is not a human developer-speech superiority claim.

B4 and later 000G must preserve the uncertainty created by the missing human developer-speech panel.

## Acceptance conditions

B2 may become `VERIFIED` only when:

1. the public corpus source/license/checksum facts are frozen and independently challengeable;
2. the deterministic subset manifest is frozen before comparative decode;
3. all included candidates consume the same canonical audio bytes for the same lane;
4. exact candidate/runtime/model/config provenance is preserved;
5. C0 repository-specific decoder context is disabled;
6. failures and losing results remain visible;
7. scorer/configuration identity is frozen before result interpretation;
8. attempt-bound preprocessing and execution-environment evidence is captured before comparative decode;
9. synthetic developer-term evidence, if present, remains explicitly diagnostic and separate;
10. the result explicitly states `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`;
11. no product/runtime code or permanent STT dependency is added;
12. exact-head CI, independent substantive semantic review, review-thread reconciliation, guarded merge, and post-merge verification are complete.

## Non-claims

This specification does not establish:

- human developer-speech accuracy;
- non-native developer-speech accuracy;
- Arabic support;
- microphone UX quality;
- conversational turn detection;
- general performance superiority;
- production STT selection;
- product implementation authority.

## Recovery

Material drift after attempt freeze invalidates the attempt. Preserve the old attempt and start a new pinned attempt. Historical B1 and private-authority preparation remain immutable evidence rather than being rewritten to match this supersession.
