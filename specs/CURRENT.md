# Wispral Specification Frontier

**Status:** founding research active; ACP verified; B1 historical preregistration verified; public-corpus B2 methodology canonical; public-corpus B2 execution frontier `READY` only after the qualification-chronology remediation below is canonical

**Canonical public-corpus methodology merge:** `cfb883311c1acb45cb8422ab6b2c02443dc1b62c` from PR #28, merged from exact head `875b0e4be76e8fc0eb753af189255b38ce3dc7ca` against exact base `c54e09a2d1cca5929bb7cd5571e84ad9698d4f73`. Live chronology does not prove the required independent semantic review before that merge; the forward-only remediation below must become canonical before execution begins.

This file owns the executable specification frontier. Historical proof and merge chronology live in `docs/canonical/CURRENT_STATE.md` and immutable Git history.

## Active parent specification

`000-founding-research`

State: `REFINING`

Purpose: replace founding technical assumptions with reproducible evidence sufficient to select the first bounded product implementation Grain or explicitly conclude that no implementation is justified yet.

## Verified ACP child

`000A-acp-qualification`

State: `VERIFIED`

Disposition:

- ACP recommendation: `PARTIAL`;
- confidence: `MODERATE`;
- authenticated prompt/stream/cancellation/permission behavior and representative ACP v2 runtime behavior remain incompletely verified;
- no broad named-agent support claim is authorized.

## Active speech research parent

`000B-stt-entity-bakeoff`

State: `REFINING`

The parent separates:

- C0 raw local STT with repository/test-specific decoder context disabled;
- C1 engine-agnostic deterministic repository resolution on frozen C0 transcripts;
- C2 backend-native context/bias as separate within-backend evidence.

## Historical B1 preregistration

`000B1-benchmark-candidate-qualification`

State: `VERIFIED`

Canonical 000B refinement/base merge: `6b5696a6becc360948282712cc9339df9cb3a67c`

Canonical evidence merge: `8df69835349f85d5ae6af9d6a62ef3af24f65f43` from PR #7.

B1 remains immutable historical evidence. It froze the candidate/configuration envelope, six candidate cells, model/runtime provenance expectations, scorer/manifest contracts, FFmpeg `9.0.1` preprocessing requirement, and a private 20-speaker / 720-utterance human developer-speech design.

No primary human developer-speech decoding occurred under that design. No comparative ranking or production STT dependency was selected.

## Historical private B2 entry-preparation lane

The repository contains canonical preparation for the old private collection path under `research/000b2-entry/`, including participant policy/materials, authority structure, artifact materialization, scorer preparation, preprocessing capture tooling, and environment capture tooling.

That lane remains historically truthful:

- `authority_status=NOT_AUTHORIZED`;
- `participant_count=0`;
- no private human corpus was accepted;
- no primary developer-speech decoding occurred;
- no comparative ranking occurred.

Those records MUST NOT be rewritten to pretend consent or corpus evidence existed.

## Historical blocked successor — preserved and superseded as the active route

`000B2-unbiased-stt-bakeoff`

State: `BLOCKED_EXTERNAL`

This exact historical lane remains blocked. Its private participant/media authority gate is intentionally preserved, and the old entry-preparation validators continue to fail closed against it.

The public-corpus successor below is canonical as repository bytes, but dependent execution remains held until the qualification-chronology remediation becomes canonical. Nothing in the amendment converts this historical lane to `READY`, authorizes its primary human decode, or fabricates its missing participant/media evidence.

## Active execution successor

The intended active B2 execution route is:

`000B2-public-corpus-bakeoff`

State: `READY`, subject to the qualification-chronology remediation gate below.

The bounded methodology amendment became canonical at merge `cfb883311c1acb45cb8422ab6b2c02443dc1b62c`, and the current-view reconciliation became canonical at merge `94e3b50009b5054db6ccd9bb3276facd1399399c`. Comparative decoding remains prohibited until the chronology remediation is canonical, then until the ordered pre-decode tasks `B2P01` through `B2P08` are genuinely complete and the final attempt manifest is frozen with `primary_decoding_started=false`.

Rationale:

- the private 20-speaker path is externally dependent and no primary attempt began;
- the parent 000B acceptance conditions already permit closure when human developer-speech evidence is absent, provided the absence is explicit enough to prevent false ranking;
- the founding product decision needs a reproducible shortlist/viability signal, not unnecessary new private data collection;
- public human speech can provide bounded ordinary-recognition evidence while synthetic developer-term material remains diagnostic only.

This is a prospective methodology successor that is canonical as repository bytes, not a retroactive rewrite of B1 or a transition of the historical `000B2-unbiased-stt-bakeoff` lane.

## Qualification chronology remediation

Live GitHub chronology overrides earlier merge-message and current-view claims.

For PR #28:

- exact candidate head `875b0e4be76e8fc0eb753af189255b38ce3dc7ca` had all six applicable exact-head workflows successful;
- owner-authored COMMENT reviews at `2026-09-02T18:56:33Z` and `2026-09-02T18:57:04Z` explicitly recorded that independent review remained pending and self-review did not satisfy the gate;
- PR #28 merged at `2026-09-02T19:02:21Z`;
- the persistent CodeRabbit comment that now records exact-head review of all 12 paths was updated at `2026-09-02T19:06:58Z`, after merge;
- no independently authored submitted PR review exists before merge;
- therefore `PR28_PREMERGE_INDEPENDENT_REVIEW=NOT_PROVEN`;
- the later exact-head CodeRabbit review reported no actionable comments and is retained only as post-merge semantic defect-screening evidence, not retroactive pre-merge qualification.

For PR #29:

- exact candidate head `1a736b62490f48bb02285f841bb833b985b8483d` had all six applicable exact-head workflows successful and zero unresolved review threads;
- the CodeRabbit exact-head response before merge said `No actionable findings` but also explicitly `Action not completed — Review rate limited`;
- rate-limited/status output is not review evidence under `AGENTS.md` and the active gate contract;
- PR #29 has no independently authored submitted PR review;
- PR #29 nevertheless merged at canonical commit `94e3b50009b5054db6ccd9bb3276facd1399399c`;
- therefore `PR29_PREMERGE_INDEPENDENT_REVIEW=NOT_SATISFIED` and the merge-message assertion that a fresh independent review completed is inaccurate metadata rather than evidence.

The first push verification on `94e3b50009b5054db6ccd9bb3276facd1399399c` had three trusted-gate failures caused only by stale open PR #30. PR #30 was closed without merge, and the failed jobs for `000B2 Trusted Participant Policy` run `33674332834`, `000B2 Trusted Participant Materials` run `33674332663`, and `000B2 Trusted Human Authority Structure` run `33674332691` were rerun on the unchanged canonical SHA and completed successfully. The other three post-merge workflow lanes were already successful. Stale readiness successor PR #31 was also closed without merge before it could promote the machine readiness state.

No `B2P01` provenance work, public archive materialization, fetched-byte SHA-256 capture, subset freeze, candidate decoding, comparative ranking, or product selection began before this remediation.

This remediation is forward-only: it does not rewrite or revert canonical commits. Before any `B2P01` execution, this exact remediation candidate must itself pass applicable exact-head CI, obtain a fresh genuinely independent substantive semantic review on the exact unchanged head, have zero unresolved actionable review threads, merge with expected-head protection, and pass post-merge verification. Once this remediation is canonical, the gate is satisfied and `B2P01` becomes the next execution task.

## Public-human P0 baseline

The public B2 lane uses LibriSpeech ASR corpus SLR12 from OpenSLR.

Frozen upstream facts for entry:

- source: `https://www.openslr.org/12/`;
- license: `CC BY 4.0`;
- `test-clean.tar.gz` official MD5: `32fa31d27d2e1cad72775fee3f4849a9`;
- `test-other.tar.gz` official MD5: `fb5a50374b501bb3bac4815ee91d3135`.

Execution MUST reverify upstream facts, verify upstream checksums, compute exact archive SHA-256 values from the materialized bytes, deterministically freeze a bounded speaker-disjoint subset before candidate decoding, and use identical canonical audio bytes across all included candidate cells.

P0 supports only bounded ordinary read-English recognition evidence on the exact frozen public subset. It MUST NOT be described as developer speech.

## Developer-term D0 diagnostic

A deterministic synthetic developer-term lane may be executed only after its prompt material, renderer provenance/configuration, voices, commands, and output audio digests are frozen.

D0 is `DIAGNOSTIC_ONLY` and may be omitted as `NOT_RUN`.

D0 MUST NOT:

- be represented as human developer-speech evidence;
- be merged numerically into P0 as one human accuracy score;
- support accent/cadence or general developer-speech superiority claims.

All B2 synthesis MUST preserve:

`HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`

## Public B2 executable ordering

After the qualification-chronology remediation is canonical, the authorized order is the task order in `specs/000B2-public-corpus-bakeoff/tasks.md`:

1. freeze public corpus provenance;
2. materialize exact archives and record official MD5 plus fetched-byte SHA-256;
3. implement and freeze deterministic subset selection before candidate outputs exist;
4. revalidate the six canonical candidate cells;
5. capture attempt-bound FFmpeg `9.0.1` preprocessing identity/configuration;
6. capture attempt-bound environment/hardware evidence;
7. freeze the pre-decode public-lane attempt manifest;
8. execute P0 C0 decoding against identical public-human audio;
9. optionally freeze and execute D0 diagnostic material;
10. score without result-driven methodology changes;
11. produce bounded results/report/closeout;
12. exact-head CI and independent substantive semantic review;
13. review-thread reconciliation and guarded expected-head merge;
14. post-merge verification and canonical reread.

The historical private-lane attempt generator remains bound to the historical `BLOCKED_EXTERNAL` lane and is not reused to self-authorize the public successor.

## Public B2 decision boundary

The amended B2 may classify candidates only as:

- `LEADING_PUBLIC_BASELINE`;
- `CONTENDER_PUBLIC_BASELINE`;
- `REJECTED`;
- `INSUFFICIENT_EVIDENCE`.

A leading public-baseline candidate is not a production dependency selection and not a proven best engine for human developer speech.

## B3/B4 boundary

`000B3` repository-context uplift remains coarse until amended B2 evidence is canonical.

B3 may use frozen public-B2 C0 transcripts and separately frozen diagnostic developer material, but it must inherit the same missing-human-developer-evidence limitation.

`000B4` STT synthesis remains coarse until B2/B3 settle its inputs.

## Remaining founding children

After the evidence-selected B chain stabilizes, the parent currently anticipates:

- `000C` — turn-taking, pause, and interruption measurement;
- `000D` — PTY compatibility and fallback threat/maintenance boundary;
- `000E` — platform audio feasibility and privacy/permission observations;
- `000F` — dependency, licensing, provenance, and distribution decision inputs;
- `000G` — founding synthesis and first product-Grain selection.

Do not refine distant children merely to create activity. Fresh canonical evidence must shape them.

## Global evidence gate

Before any child becomes `VERIFIED`:

- exact artifacts and source revisions are recorded;
- failures and unsupported behavior remain visible;
- unavailable systems remain unavailable rather than becoming PASS;
- claims remain narrower than raw observations;
- material methodology drift invalidates/restarts the attempt;
- evidence is sufficient for independent challenge;
- exact-head CI and fresh independent substantive semantic review are complete;
- review threads are reconciled before guarded merge.

## Product-code gate

No Rust product implementation, Cargo workspace, permanent speech engine integration, ACP production client, PTY adapter, TUI, installer, or release is authorized until `000G` selects a bounded first implementation Grain and that Grain independently satisfies readiness.

The public-corpus amendment and this chronology remediation do not weaken this gate.

## Live-truth rule

Live canonical GitHub/repository truth overrides this file. After every merged research/refinement unit, re-read current authority before starting dependent work.

## Next canonical action

Canonicalize this qualification-chronology remediation first. Do not execute `B2P01` while this remediation remains non-canonical. After it is canonically merged and post-merge verified, execute `B2P01` only: reverify and record exact OpenSLR SLR12 source/license facts and official archive checksums in machine-readable provenance. Continue to `B2P02` and later tasks only in canonical task order. Do not begin comparative candidate decoding until `B2P01` through `B2P08` are complete and the pre-decode attempt manifest is frozen with `primary_decoding_started=false`. Preserve `000B2-unbiased-stt-bakeoff` as historical `BLOCKED_EXTERNAL`, do not fabricate private consent, and do not represent public or synthetic media as human developer-speech evidence.
