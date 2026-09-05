# Wispral Specification Frontier

**Status:** founding research active; ACP verified; B1 historical preregistration verified; public-corpus B2 methodology canonical; qualification-chronology gate `SATISFIED`; public-corpus B2 recovery active; B2R01 through B2R03 canonical and post-merge verified; active recovery unit `B2R04`; ATTEMPT-001 B2E03 and all later primary decoding closed

**Canonical public-corpus methodology merge:** `cfb883311c1acb45cb8422ab6b2c02443dc1b62c` from PR #28, merged from exact head `875b0e4be76e8fc0eb753af189255b38ce3dc7ca` against exact base `c54e09a2d1cca5929bb7cd5571e84ad9698d4f73`. Live chronology did not prove the required independent semantic review before that merge; the resulting qualification debt was repaired forward-only by PR #32 at canonical merge `44b8e5ee5fe72aa0054af1493e2fffc60f0cf0fc`, and machine readiness was reconciled by PR #33 at canonical merge `ea2d8a09a47a47b202f0bbb0871c362c0b26e1e7`.

**Canonical B2P01 provenance merge:** `2d2937b0da1dc9b4d7278fe6bfb778eb6a75d129` from PR #34, merged by guarded squash from exact qualified head `dbc499dc3e24c247b95260631558eec825672fbf` against exact base `ea2d8a09a47a47b202f0bbb0871c362c0b26e1e7`. All six applicable exact-head workflows succeeded, fresh independent CodeRabbit review reported no actionable findings, all six post-merge workflows on the canonical merge succeeded, and the canonical authority/readiness reread authorized B2P02 as the next bounded unit.

**Canonical B2P02 archive-byte merge:** `1ba4e42561cc53f574d5d35689e2ae499a398b5c` from PR #35, merged by guarded squash from exact qualified head `06bbd50676edcf87fc3e85b73bc6b7f17d3161ff` against exact base `2d2937b0da1dc9b4d7278fe6bfb778eb6a75d129`. All seven applicable exact-head workflows succeeded and fresh independent CodeRabbit review covered all 11 changed files with no actionable findings. Post-merge archive materialization run `33751302416`, job `100635230794`, checked out the canonical merge, passed exact workflow-structure verification before archive access, re-fetched both official OpenSLR archives, reproduced both recorded byte counts, official MD5 values, and SHA-256 identities, emitted `B2P02_REDIRECT_POLICY=PASS` and `B2P02_MATERIALIZATION=PASS`, and uploaded artifact `9891735545` with ZIP digest `sha256:b0187d8b664a212a100d6d1515773891315d5af9e137178507c3b079d9edca6b`. The required canonical reread therefore authorized B2P03 as the sole next bounded unit.

**Canonical B2P03 deterministic-subset merge:** `83eca872148f329033c299f6671d275edf2d7b58` from PR #37, merged by guarded expected-head squash from exact qualified head `e642500c7ba6c5935a94da42cf638c01f9366913` against exact base `2f9517bf34342f7e02697024c32ed2a16f61cf29`. Exact-head `000B2 Public Corpus Subset Selection` run `33774852016` and `000B2 Public Corpus Methodology` run `33774852021` succeeded. Fresh independent CodeRabbit semantic review covered the complete four-file exact base/head diff and reported no actionable semantic findings after forward-only repair of valid correctness and source-integrity findings. Post-merge subset-selection run `33775647508`, job `100716549752`, and methodology run `33775647539`, job `100716550502`, succeeded on the exact canonical merge; all six applicable push workflows on that SHA succeeded. No subset manifest was frozen and no candidate or primary decoding began. The required canonical reread therefore authorized B2P04 as the sole next bounded unit.

**Canonical B2P04 subset-manifest freeze merge:** `4c4e758f22b54fa62256e57bfbd344adc817df8e` from PR #39, merged by guarded expected-head squash from exact qualified head `0d83d277cc2544f63613e674d60bae07ad24dc26` against exact base `c1a576db2adf67cb4b830c280e6cba80b0ae3b43`. Exact-head methodology run `33793696076` and subset-freeze run `33793696006`, job `100776173700`, succeeded; the latter reproduced the committed manifest byte-for-byte from exact official archive identities under pinned Python `3.12`. Fresh independent CodeRabbit semantic audit comment `5530776500` covered the complete five-file exact base/head diff and reported no actionable findings after forward-only hardening. The frozen manifest byte SHA-256 is `5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb` and freeze digest `f75a1084e8414e56a47b00350d5a7c1295445e2c52b03a0f591c40c041c9f242`. Post-merge subset-freeze run `33794854765`, job `100779961908`, reproduced the canonical freeze and uploaded artifact `9908811632` with ZIP digest `sha256:bad9a31cea1a3a51b6ecbf9053f4941b1ae8a5d88cb97b747703166fe9444578`; methodology run `33794854595`, job `100779960182`, and the four trusted push lanes also succeeded. No candidate revalidation or decoding began. The required canonical reread therefore authorized B2P05 as the sole next bounded unit.

**Canonical B2P05 candidate-revalidation merge:** `49538990fb4cf8223e9321261925206ed7ff5cee` from PR #41, merged by guarded expected-head squash from exact qualified head `c62a7fa2998cd5292da78a66deb4a6d2044691b3` against exact base `6135cd67c1b31e0be0b82ba202b6a6770d34b68d`. Final exact-head `000B2 Public Corpus Candidate Revalidation` run `33802435769` and `000B2 Public Corpus Methodology` run `33802435851` succeeded after forward-only repairs for synthetic-merge-ref checkout, tautological authority comparison, and the `execution_environment` schema key. Fresh independent CodeRabbit semantic review covered the complete final three-file exact base/head diff and reported no actionable findings. Post-merge candidate-revalidation run `33803832655` succeeded on the canonical SHA: static job `100809416957` passed exact canonical-base/head trust-boundary and closed-later-gate checks, live job `100809480949` reproduced all 18 pending artifact identities from canonical trusted authority and revalidated runtime plus pre-pinned model identities. Post-merge methodology run `33803832693`, job `100809418067`, and trusted materialization/participant-materials/participant-policy/human-authority runs `33803832706`, `33803832711`, `33803832717`, and `33803832657` also succeeded. Candidate decoding, B2P06 preprocessing capture, B2P07 environment capture, B2P08 attempt freeze, production selection, and product code remained closed. The required canonical reread therefore authorizes B2P06 as the sole next bounded unit.
**Canonical B2P07 execution-environment merge:** `4bd5306fa1d274d7b822b73e26172dd9c7058319` from PR #45, merged by guarded expected-head merge commit from exact qualified head `422ea2d7f0945437ea271412b2f2e33c85256f2e` against exact base `a45e69f3f03094c947104438ac1f0b2aa124b295`. Exact-head environment run `33863710225` and methodology run `33863710318` succeeded. Fresh independent CodeRabbit semantic review covered the complete final four-file diff and reported no actionable findings after forward-only provenance repairs. The merge preserved raw-capture and provenance-seal ancestry. Canonical post-merge environment run `33864082394`, job `100994833527`, and methodology run `33864082358`, job `100994833254`, succeeded on the exact merge; candidate revalidation run `33864082439` and trusted materialization/participant-materials/participant-policy/human-authority runs `33864082418`, `33864082356`, `33864082410`, and `33864082452` also succeeded. Raw capture commit `aa4711c083b652dfdb7a5d29a39a222125000131` / blob `d84e3e55d45a937a09e5898727b60c635144ac5c` and provenance-seal commit `b8268cb4316a0d05c898bbf5b8bb3f7fe82d4937` / blob `caf814bcb5e42fd769e6df1d9a54c1164535f86c` remain verified. GitHub-hosted timing remains `DIAGNOSTIC`; comparative performance is not authorized. B2P08 remained unfrozen and candidate/primary decoding remained unstarted.

**Canonical B2P08 pre-decode attempt-freeze merge:** `dd65e23d29e7f83b9a94aba9c018928c7f9cc41d` from exact qualified head `a5ee2ccb48a301b623f775970c23434d3a50ccba`. PR #47 froze `000B2-PUBLIC-ATTEMPT-001` before any candidate or primary decode, with exact B2P04 subset, B2P05 candidate registry, B2P06 preprocessing, B2P07 execution-environment, scorer/config, and public P0 WER adapter identities bound. The frozen manifest digest is `af4d5009e293daef5d8f629ca91af653f5f591448cd94d4555473a51e2d1da86`. Fresh exact-head runs `33872999455` (attempt freeze) and `33872999311` (public methodology) succeeded after forward-only repair of all substantive review findings, and the fresh independent exact-head semantic review reported no actionable findings. The guarded expected-head squash merge produced the canonical commit above. Post-merge exact-SHA push verification completed 7/7 successfully: attempt-freeze run `33873343952`, public-methodology run `33873344061`, candidate-revalidation run `33873344096`, trusted-materialization run `33873344252`, trusted-participant-materials run `33873344071`, trusted-participant-policy run `33873344118`, and trusted-human-authority run `33873344044`. `candidate_decoding_started=false`, `primary_decoding_started=false`, `comparative_performance_authorized=false`, `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, `production_stt_selected=false`, and `product_code_authorized=false` remained preserved.

**Canonical B2E01 moonshine-compact execution merge:** `bb3acfae1f39669d74118a564e57a131731484d3` from PR #50, merged by guarded expected-head merge commit from exact qualified head `9a2b4dd2d79c445d31a09a6c435af6cbe43e6808` against exact base `6607b1b1a13daebe1c267f82e3295be9b3bdea32`. The merge preserved capture/seal/provenance ancestry. Fresh exact-head B2E01 Evidence and Methodology qualification succeeded before merge, fresh independent CodeRabbit exact-range challenge comment `5551111214` reported no actionable substantive findings, and all seven exact-merge-head push workflows succeeded after merge: Methodology run `33960299269`, B2E01 Evidence run `33960299255`, Candidate Revalidation run `33960299308`, Trusted Materialization run `33960299258`, Trusted Participant Materials run `33960299257`, Trusted Participant Policy run `33960299252`, and Trusted Human Authority run `33960299250`. Canonical B2E01 Evidence run `33960299255`, job `101290913708`, checked out exact merge `bb3acfae1f39669d74118a564e57a131731484d3`, passed both fail-closed malformed freeze-digest regressions, reproduced `B2E01_EVIDENCE=PASS`, 240/240 decoded with 0 failures, duplicate semantic equivalence PASS, and raw-data boundary PASS. B2E02 was still unauthorized during that post-merge verification.

**Canonical B2E02 moonshine-balanced execution merge:** `91588babc1f738c4284f53d40b4cd96dc13bfd50` from PR #53, merged by guarded expected-head merge commit from exact qualified head `1c4db3f5f857f7a813f4fbb8bc4593c5c5f066c1` against exact base `116dbd1734e01ec1280d6b530f0cb1dec867feb1`. The merge preserved execution/evidence ancestry. Fresh exact-head B2E02 Evidence and Methodology qualification succeeded before merge; all actionable review findings were resolved; and the fresh independent CodeRabbit exact-range review reported no actionable substantive findings. The canonical evidence source remained non-result-driven despite a later preserved duplicate capture whose frozen input/status identities matched while 10 raw transcripts differed. All seven exact-merge-head push workflows succeeded after merge: B2E02 Evidence run `33964134856`, Methodology run `33964134899`, Candidate Revalidation run `33964134921`, Trusted Materialization run `33964134877`, Trusted Participant Materials run `33964134889`, Trusted Participant Policy run `33964134896`, and Trusted Human Authority run `33964134937`. B2E03 remained unauthorized during that post-merge verification.

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

The public-corpus successor below is canonical and executable in ordered bounded units because the qualification-chronology remediation is now canonical and the machine readiness reconciliation is canonical. Nothing in those changes converts this historical lane to `READY`, authorizes its primary human decode, or fabricates its missing participant/media evidence.

## Active execution successor

The intended active B2 execution route is:

`000B2-public-corpus-bakeoff`

State: `READY`

The bounded methodology amendment became canonical at merge `cfb883311c1acb45cb8422ab6b2c02443dc1b62c`, the public-frontier reconciliation became canonical at merge `94e3b50009b5054db6ccd9bb3276facd1399399c`, the qualification-chronology remediation became canonical at merge `44b8e5ee5fe72aa0054af1493e2fffc60f0cf0fc`, the machine readiness reconciliation became canonical at merge `ea2d8a09a47a47b202f0bbb0871c362c0b26e1e7`, B2P01 provenance became canonical at merge `2d2937b0da1dc9b4d7278fe6bfb778eb6a75d129`, B2P02 archive-byte verification became canonical at merge `1ba4e42561cc53f574d5d35689e2ae499a398b5c`, B2P03 deterministic subset selection became canonical at merge `83eca872148f329033c299f6671d275edf2d7b58`, B2P04 subset-manifest freeze became canonical at merge `4c4e758f22b54fa62256e57bfbd344adc817df8e`, B2P05 candidate revalidation became canonical at merge `49538990fb4cf8223e9321261925206ed7ff5cee`, B2P06 preprocessing capture became canonical at merge `3dceadd984ff307ce55745bf5f289890a2fac261`, B2P07 execution-environment capture became canonical at merge `4bd5306fa1d274d7b822b73e26172dd9c7058319`, and B2P08 pre-decode attempt freeze became canonical at merge `dd65e23d29e7f83b9a94aba9c018928c7f9cc41d`. `QUALIFICATION_CHRONOLOGY_GATE=SATISFIED`. B2P01 through B2P08, B2E01, and B2E02 are complete. The final pre-decode attempt manifest remains historically frozen with `primary_decoding_started=false`. B2E01 is canonical at merge `bb3acfae1f39669d74118a564e57a131731484d3`. ATTEMPT-001 is now historical and ineligible for comparative scoring because B2R01 is canonical at merge `715efc4855fb52187ed250b11f0c28bb2c2c0660`; B2E03 and every later ATTEMPT-001 primary decode are closed. `research/000b2-public/recovery-readiness.json` is the active machine-readable execution authority. B2R03 is canonical and post-merge verified at task merge `6904fa7dd55e35c08e76044a18ebf9a95c65e038`; this reconciliation makes B2R04 the sole current bounded recovery unit, and all ATTEMPT-002 primary decoding remains closed until B2R04 is canonically reconciled.

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

No `B2P01` provenance work, public archive materialization, fetched-byte SHA-256 capture, subset freeze, candidate decoding, comparative ranking, or product selection began before the remediation was canonical.

The forward-only remediation was independently qualified and canonically merged by PR #32 as `44b8e5ee5fe72aa0054af1493e2fffc60f0cf0fc`, from exact qualified head `596b5e4d6654c4d562de51d8a047c8196ce52c7d` against exact base `94e3b50009b5054db6ccd9bb3276facd1399399c`. Its applicable exact-head workflow lanes completed successfully, fresh independent CodeRabbit substantive review reported no actionable findings, no actionable review threads remained, guarded expected-head merge completed, and post-merge verification succeeded. Therefore `QUALIFICATION_CHRONOLOGY_GATE=SATISFIED`.

PR #33 then reconciled the machine-readable public readiness state and canonically merged as `ea2d8a09a47a47b202f0bbb0871c362c0b26e1e7` from exact qualified head `990f7260475822839f1fe748f70460643de9b8ad` against exact base `44b8e5ee5fe72aa0054af1493e2fffc60f0cf0fc`. Exact-head `000B2 Public Corpus Methodology` run `33677613666` succeeded, a prior review finding was repaired forward-only, and fresh independent review of the repaired head completed clean. Canonical `research/000b2-public/readiness.json` became `READY` and made `B2P01` the sole next action until B2P01 itself became canonical.

PR #34 then executed and canonically qualified B2P01 source/checksum provenance. It merged by guarded expected-head squash as `2d2937b0da1dc9b4d7278fe6bfb778eb6a75d129` from exact qualified head `dbc499dc3e24c247b95260631558eec825672fbf` against exact base `ea2d8a09a47a47b202f0bbb0871c362c0b26e1e7`. The exact candidate had all six applicable workflows successful and a fresh independent CodeRabbit review with no actionable findings after a prior canonical-authority defect was repaired. All six push workflows on the canonical merge then completed successfully. No archive bytes were fetched by B2P01. The required canonical reread therefore satisfied the B2P02 entry condition.

PR #35 then executed and canonically qualified B2P02 archive materialization. It merged by guarded expected-head squash as `1ba4e42561cc53f574d5d35689e2ae499a398b5c` from exact qualified head `06bbd50676edcf87fc3e85b73bc6b7f17d3161ff` against exact base `2d2937b0da1dc9b4d7278fe6bfb778eb6a75d129`. The final 11-file candidate had all seven applicable exact-head workflows successful and a fresh independent CodeRabbit substantive review with no actionable findings after forward-only redirect and workflow-structure hardening. Post-merge materialization run `33751302416`, job `100635230794`, revalidated the canonical merge SHA and reproduced both archive byte counts, official MD5 values, and SHA-256 identities. The required canonical reread therefore satisfied the B2P03 entry condition.

PR #37 then executed and canonically qualified B2P03 deterministic source-only subset selection. It merged by guarded expected-head squash as `83eca872148f329033c299f6671d275edf2d7b58` from exact qualified head `e642500c7ba6c5935a94da42cf638c01f9366913` against exact base `2f9517bf34342f7e02697024c32ed2a16f61cf29`. The final four-file candidate had exact-head subset-selection run `33774852016` and methodology run `33774852021` successful. Fresh independent CodeRabbit semantic review inspected all four changed files across the complete exact range and reported no actionable findings. The canonical merge is GitHub-signature verified with parent equal to the qualified base. Post-merge subset-selection run `33775647508`, job `100716549752`, and methodology run `33775647539`, job `100716550502`, succeeded on the exact merge, together with four trusted push lanes for six of six successful push workflows. The canonical reread therefore satisfied the B2P04 entry condition while preserving every pre-decode guard.

PR #39 then executed and canonically qualified B2P04 deterministic public-human source-membership freeze. It merged by guarded expected-head squash as `4c4e758f22b54fa62256e57bfbd344adc817df8e` from exact qualified head `0d83d277cc2544f63613e674d60bae07ad24dc26` against exact base `c1a576db2adf67cb4b830c280e6cba80b0ae3b43`. The final five-file candidate had exact-head methodology run `33793696076` and subset-freeze run `33793696006`, job `100776173700`, successful. Fresh independent CodeRabbit semantic audit comment `5530776500` reviewed the complete exact five-file range and reported no actionable findings after valid negative-size, root-metadata allowlist, and runtime-reproducibility findings were repaired forward-only. Post-merge subset-freeze run `33794854765`, job `100779961908`, methodology run `33794854595`, job `100779960182`, and the four trusted push lanes all succeeded on the exact canonical merge. The canonical freeze contains 24 speakers / 240 utterances, manifest byte SHA-256 `5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb`, and freeze digest `f75a1084e8414e56a47b00350d5a7c1295445e2c52b03a0f591c40c041c9f242`. No candidate revalidation, candidate decoding, primary decoding, or B2P06 preprocessing capture began. The canonical reread therefore satisfied the B2P05 entry condition while preserving every pre-decode guard.

PR #41 then executed and canonically qualified B2P05 candidate identity revalidation. It merged by guarded expected-head squash as `49538990fb4cf8223e9321261925206ed7ff5cee` from exact qualified head `c62a7fa2998cd5292da78a66deb4a6d2044691b3` against exact base `6135cd67c1b31e0be0b82ba202b6a6770d34b68d`. The final three-file candidate had exact-head candidate-revalidation run `33802435769` and methodology run `33802435851` successful. Fresh independent CodeRabbit semantic review covered the exact final three-file range and reported no actionable findings after all valid earlier findings had been repaired forward-only. Post-merge candidate-revalidation run `33803832655` succeeded with static job `100809416957` and live job `100809480949`; the live job reproduced the trusted pending artifact identities and revalidated exact runtime and pre-pinned model identities. Methodology run `33803832693`, job `100809418067`, and the four trusted push lanes also succeeded on exact canonical merge `49538990fb4cf8223e9321261925206ed7ff5cee`. No B2P06 preprocessing capture, B2P07 environment capture, B2P08 attempt freeze, candidate decoding, production STT selection, or product-code authorization occurred. The canonical reread therefore satisfies the B2P06 entry condition while preserving every pre-decode guard.

PR #43 then completed B2P06 attempt-bound preprocessing capture and merged by guarded expected-head squash as canonical commit `3dceadd984ff307ce55745bf5f289890a2fac261` from exact qualified head `c5501daf14038ced0ba3ad2de1cad92cfb38302a` against exact base `e8841a68a7e37c7e4dd26ff73fe2566661c468b0`. Exact-head methodology run `33814334825` and preprocessing run `33814334967`, job `100843002336`, succeeded after forward-only repair of the mutable FFmpeg build environment. Fresh independent CodeRabbit semantic review covered the final exact five-file diff and reported no actionable findings; zero actionable review threads remained before merge.

Canonical post-merge preprocessing run `33814736588`, job `100844238206`, checked out exact merge `3dceadd984ff307ce55745bf5f289890a2fac261`, rebuilt FFmpeg `n9.0.1` source commit `bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa` inside digest-pinned `python:3.12.11-bookworm@sha256:13c9584604a99ca134c4f41800f74ffc64ee6ac8cf555cf1e704a6087fc84f12`, reprocessed all 240 frozen source identities, reproduced committed evidence SHA-256 `d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011`, uploaded bounded artifact `9916141620` with digest `sha256:d0a6918fc7bf48e93053fab4fb3286c250a6c980456d893bb9c286f9697130b9`, and removed transient corpus/audio/toolchain state. Candidate-revalidation run `33814736795`, methodology run `33814736759`, trusted-materialization run `33814736691`, participant-materials run `33814736716`, participant-policy run `33814736734`, and human-authority run `33814736663` also succeeded on the same canonical merge. B2P07 environment capture and B2P08 attempt freeze remained unresolved/unfrozen; candidate and primary decoding remained false; `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`, no production STT selection, and no product-code authority were preserved. The canonical authority/readiness reread therefore completes B2P06 and authorizes B2P07 only.

## Public-human P0 baseline

The public B2 lane uses LibriSpeech ASR corpus SLR12 from OpenSLR.

Frozen upstream facts for entry:

- source: `https://www.openslr.org/12/`;
- license: `CC BY 4.0`;
- `test-clean.tar.gz` official MD5: `32fa31d27d2e1cad72775fee3f4849a9`;
- `test-other.tar.gz` official MD5: `fb5a50374b501bb3bac4815ee91d3135`.

B2P02 exact archive-byte evidence records:

- `test-clean.tar.gz` — 346663984 bytes, SHA-256 `39fde525e59672dc6d1551919b1478f724438a95aa55f874b576be21967e6c23`;
- `test-other.tar.gz` — 328757843 bytes, SHA-256 `d09c181bba5cf717b3dee7d4d592af11a3ee3a09e08ae025c5506f6ebe961c29`;
- official MD5 was reverified against the same fetched bytes on the final PR #35 exact head and again after canonical merge `1ba4e42561cc53f574d5d35689e2ae499a398b5c` in GitHub Actions run `33751302416`, job `100635230794`;
- post-merge bounded observation artifact `9891735545` has ZIP digest `sha256:b0187d8b664a212a100d6d1515773891315d5af9e137178507c3b079d9edca6b`;
- the large upstream archive bytes were deleted after hashing and are not committed to the repository.

B2P02 is canonical and post-merge verified. B2P03 deterministic subset-selection logic is canonical and post-merge verified at merge `83eca872148f329033c299f6671d275edf2d7b58`. B2P04 deterministic source-membership freeze is canonical and post-merge verified at merge `4c4e758f22b54fa62256e57bfbd344adc817df8e` with manifest byte SHA-256 `5fa108dc623760f194fdde463cbfb819288fe8f2a10279d25ec889f221b389bb` and freeze digest `f75a1084e8414e56a47b00350d5a7c1295445e2c52b03a0f591c40c041c9f242`. B2P05 candidate identity revalidation is canonical and post-merge verified at merge `49538990fb4cf8223e9321261925206ed7ff5cee`. B2P06 attempt-bound preprocessing capture is canonical and post-merge verified at merge `3dceadd984ff307ce55745bf5f289890a2fac261` with evidence SHA-256 `d90e5215081191134d8e714778140bfeee8080eb77aedc3a159b2dfed6e2d011`. B2P07 attempt-bound execution-environment capture is canonical and post-merge verified at merge `4bd5306fa1d274d7b822b73e26172dd9c7058319` with preserved raw/seal ancestry and `DIAGNOSTIC` performance semantics. B2P08 is canonical and post-merge verified. B2E01 and B2E02 remain canonical historical ATTEMPT-001 executions. B2R01 invalidated ATTEMPT-001 for material execution drift, so B2E03 and every later ATTEMPT-001 primary decode are closed; B2R03 is canonical and post-merge verified at task merge `6904fa7dd55e35c08e76044a18ebf9a95c65e038`, and this reconciliation advances current recovery authority to B2R04 only.

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

With `QUALIFICATION_CHRONOLOGY_GATE=SATISFIED`, B2P01 through B2P05 are canonical and the authorized order remains the task order in `specs/000B2-public-corpus-bakeoff/tasks.md`:

1. freeze public corpus provenance;
2. materialize exact archives and record official MD5 plus fetched-byte SHA-256;
3. implement deterministic subset-selection logic before candidate outputs exist;
4. freeze the selected public-human source-membership manifest and deterministic digest;
5. revalidate the six canonical candidate cells;
6. capture attempt-bound FFmpeg `9.0.1` preprocessing identity/configuration;
7. capture attempt-bound environment/hardware evidence;
8. freeze the pre-decode public-lane attempt manifest;
9. execute P0 C0 decoding against identical public-human audio;
10. optionally freeze and execute D0 diagnostic material;
11. score without result-driven methodology changes;
12. produce bounded results/report/closeout;
13. exact-head CI and independent substantive semantic review;
14. review-thread reconciliation and guarded expected-head merge;
15. post-merge verification and canonical reread.

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

The public-corpus amendment and canonical chronology remediation do not weaken this gate.

## Historical B2R01 recovery reconciliation — superseded predecessor record

The following B2R01 block is retained only as transition chronology. It is **not current execution authority**. The latest B2R03 reconciliation block below supersedes its former successor/action state.

B2R01 invalidation is canonical at merge `715efc4855fb52187ed250b11f0c28bb2c2c0660` and exact-merge-head recovery workflow run `33979925715` succeeded. The historical ATTEMPT-001 `readiness.json` remains byte-preserved evidence only; `recovery-readiness.json` overrides it for every new execution decision.

**Historical recovery predecessor:** `B2R01`
**Historical B2R01 recovery merge:** `715efc4855fb52187ed250b11f0c28bb2c2c0660`
**Historical B2R01 post-merge recovery run:** `33979925715`
**Historical successor at B2R01 reconciliation:** `B2R02`

At that historical transition, ATTEMPT-001 became ineligible for comparative scoring and candidate-superiority claims, no new ATTEMPT-001 primary decode was authorized, and B2R02 was the next bounded recovery unit. B2R02 has since been separately qualified, merged, and post-merge verified; this historical paragraph grants no present authority.

### Historical ATTEMPT-001 post-B2E02 snapshot wording — non-authoritative

The following strings are retained only as a literal description of the superseded ATTEMPT-001 post-B2E02 snapshot so historical evidence verifiers can continue proving what the old snapshot said. They MUST NOT be interpreted as current execution authority; `recovery-readiness.json` and the latest B2R03 recovery markers below supersede them for new execution:

```text
current bounded execution unit `B2E03`
B2E01 and B2E02 are canonical. B2E03 (`whispercpp-compact`) is now the only authorized bounded unit
B2P01 through B2P08, B2E01, and B2E02 are complete.
B2P08 pre-decode attempt freeze became canonical at merge `dd65e23d29e7f83b9a94aba9c018928c7f9cc41d`
B2E03 (`whispercpp-compact`) is the sole current bounded execution unit.
Execute and canonically qualify `B2E03` only: decode the identical frozen P0 public-human subset with candidate cell 3 (`whispercpp-compact`) under unchanged frozen C0
B2E04 and all later candidate cells remain unauthorized
```

## Live-truth rule

Live canonical GitHub/repository truth overrides this file. After every merged research/refinement unit, re-read current authority before starting dependent work.

## Canonical B2R03 recovery reconciliation — latest authority

This section is the sole current recovery-action authority in this document. B2R03 is canonically implemented at task merge `6904fa7dd55e35c08e76044a18ebf9a95c65e038`. Exact task-merge push run `33995766496` of workflow `000B2 Public Corpus Attempt Recovery` (`workflow_id=350986920`, path `.github/workflows/000b2-public-attempt-recovery.yml`) completed successfully on that exact merge. Historical ATTEMPT-001 bytes and the immutable recovery proof mechanism remain unchanged.

**Canonical recovery predecessor:** `B2R03`
**Canonical B2R03 recovery merge:** `6904fa7dd55e35c08e76044a18ebf9a95c65e038`
**Canonical B2R03 post-merge recovery run:** `33995766496`
**Active recovery unit:** `B2R04`

ATTEMPT-002 remains required and unfrozen, and `primary_decode_entry_open=false`. B2R04 alone is authorized after this reconciliation becomes canonical: freeze `000B2-PUBLIC-ATTEMPT-002` before any new primary candidate decode while preserving the frozen subset, candidate set, scorer, normalization, corrected C0, and B2R03 preexecution evidence identities. B2R05 and every primary candidate decode remain unauthorized until B2R04 is separately qualified, merged, post-merge verified, and reconciled.

## Next canonical action

Qualify `B2R04` only: freeze `000B2-PUBLIC-ATTEMPT-002` before any new primary candidate decode. Preserve the frozen subset, candidate set, scorer, normalization, corrected C0, and B2R03 preexecution evidence identities unchanged. Keep B2R05 and every ATTEMPT-002 primary candidate decode closed until B2R04 is separately qualified, merged, post-merge verified, and reconciled.
