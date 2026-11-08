# Trusted-Control Repair Reconciliations

**Status:** canonical append-only governance/evidence ledger
**Authority:** `CONSTITUTION.md` Principle XVI
**Successor-state effect:** none unless a later independently authorized successor reconciliation changes successor state

This ledger records completed trusted-control repair sequences required by Constitution Principle XVI. A record here is not a successor task reconciliation, does not complete a B2 recovery task, does not mutate successor readiness, and cannot authorize decode, scoring, comparative claims, production selection, product code, or project completion.

Each repair record must preserve exact repository identities, failed-boundary evidence without relabeling it as success, deterministic positive/negative proof, independent review disposition, canonical merge ancestry, canonical-state exercise evidence, and the exact execution authority that remains after reconciliation.

## Repair 001 — ATTEMPT-003 successor exact-scope and deletion hardening

### Defect

The canonical common successor verifier in `research/000b2-public/verify_attempt_002_invalidation.py` had two related fail-open scope defects:

1. trusted task/reconciliation validation rejected paths outside an allowlist but accepted strict subsets instead of requiring exact canonical path-set equality;
2. trusted scope-derived Git diff queries used `--diff-filter=ACMRTUXB`, excluding deleted paths from the candidate scope input.

The second defect was found by fresh independent review after the first repair was already prepared. It was repaired forward-only before merge. The final verifier uses exact path-set equality and deletion-aware `--diff-filter=ACDMRTUXB` in the B2R13, B2R14, and general active-task/reconciliation scope queries.

### Canonical repair identity

- repair authority base: `a7b2179ade9825e4f280c5cf28aa72a3e361e970`
- exact independently reviewed repair head: `51891f584be26639e3cda427e4f61d46fe524b1a`
- repaired verifier blob: `b8ed65776c6d9b5ae313c34d91c221b13a25197e`
- repair PR: `#106`
- guarded normal repair merge: `003ed3a44b89779ff51df45cd1d015ef6da98370`
- canonical repair merge tree: `0e9e17fc1396971bd4e172a14bc2f82c67f1dadc`
- canonical repair merge first parent: `a7b2179ade9825e4f280c5cf28aa72a3e361e970`
- canonical repair merge second parent: `51891f584be26639e3cda427e4f61d46fe524b1a`
- GitHub commit verification: `verified=true`, reason `valid`

The final repair changed only `research/000b2-public/verify_attempt_002_invalidation.py` relative to its canonical authority base.

### Preserved pre-merge boundary evidence

The following exact-head non-successes are preserved as Principle XVI boundary evidence and are not counted as successful gates:

- `000B2 Public Corpus ATTEMPT-003 Trusted PR Gate` run `34402893952` failed only because the declared immutable trusted-control verifier bytes changed. Candidate common-verifier execution, pinned-source verification, and runtime-contract execution were skipped.
- `000B2 Public Corpus ATTEMPT-003 Recovery` run `34402895472` failed at the trusted pre-candidate boundary with `B2R16 task-candidate path scope violation` because the same trusted-control path is outside ordinary B2R16 task scope. Dependent candidate execution, material-drift verification, and transition-proof steps were skipped.

Other applicable exact-head repair checks succeeded:

- `000B2 Public Corpus Attempt Recovery` run `34402895470` — `success`;
- `000B2 Public Corpus Methodology` run `34402895445` — `success`.

`000B2 Trusted Materialization Authority` run `34402894009` was skipped and was not applicable to the repair candidate; it is not counted as success.

### Pre-merge deterministic proof

Evidence-only PR `#113` was closed unmerged after capture. Run `34403473885`, job `102640722781`, bound exact repair head `51891f584be26639e3cda427e4f61d46fe524b1a`, verifier blob `b8ed65776c6d9b5ae313c34d91c221b13a25197e`, and B2R16 source head `ee3b419bc2b5c32bc72ced1c777a07ebfc6f85f4`.

The run proved:

```text
TASK_EXACT_SCOPE_POSITIVE=PASS
TASK_INCOMPLETE_SCOPE_REJECTION=PASS
TASK_EXTRA_SCOPE_REJECTION=PASS
TASK_UNRELATED_DELETION_REJECTION=PASS
B2R13_UNRELATED_DELETION_REJECTION=PASS
RECONCILIATION_EXACT_SCOPE_POSITIVE=PASS
RECONCILIATION_INCOMPLETE_SCOPE_REJECTION=PASS
RECONCILIATION_EXTRA_SCOPE_REJECTION=PASS
RECONCILIATION_UNRELATED_DELETION_REJECTION=PASS
```

It also preserved:

```text
ATTEMPT_002_INVALIDATION=PASS
ATTEMPT_002_HISTORICAL_BYTES=PASS
ACTIVE_SUCCESSOR_RECOVERY_UNIT=B2R16
COMPARATIVE_RESULT_AVAILABLE=NO
PRODUCTION_STT_SELECTED=NO
PRODUCT_CODE_AUTHORIZED=NO
HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT
```

### Independent review

Review-only PR `#114` pointed to the exact same canonical base and final repair head and was closed unmerged after review. Fresh independent CodeRabbit review inspected exact range `a7b2179ade9825e4f280c5cf28aa72a3e361e970..51891f584be26639e3cda427e4f61d46fe524b1a`, the full one-file repair, Principle XVI authority, exact workflow evidence, and the repaired deletion-bypass finding. It reported no blocking governance, security, correctness, compatibility, historical-state, scope, or authority-expansion issue.

Earlier review-only PR `#112` is preserved as the source of the deletion-filter finding on stale head `70aa5e91d9f1b3e1cab7e97b32e61d9a7d3107a5`; that finding was repaired forward-only and resolved before the final review.

### Canonical merge and push observation

Guarded normal merge `003ed3a44b89779ff51df45cd1d015ef6da98370` preserved the exact canonical base and independently reviewed repair head as its two parents.

Exact-merge push workflows succeeded for:

- `000B2 Trusted Participant Policy` run `34404010596`;
- `000B2 Public Corpus Methodology` run `34404010647`;
- `000B2 Trusted Human Authority Structure` run `34404010595`;
- `000B2 Trusted Materialization Authority` run `34404010722`;
- `000B2 Trusted Participant Materials` run `34404010572`;
- `000B2 Public Corpus Attempt Recovery` run `34404010576`;
- `000B2 Public Corpus Candidate Revalidation` run `34404010579`, with both static and live jobs successful.

`000B2 Public Corpus ATTEMPT-003 Recovery` run `34404010547` failed at `Trusted pre-candidate execution boundary` with `B2R16 task-candidate path scope violation`. The repair merge is not a B2R16 task candidate. The failure occurred before successor candidate verification, material-drift verification, or transition-proof execution. It is preserved as observed post-merge behavior, was not rerun-to-green, and is not counted as success.

### Canonical-state repaired-control exercise

Evidence-only PR `#115` was closed unmerged after capture. `Trusted Control Repair 003ED Canonical State Evidence` run `34404224592`, job `102643205076`, completed successfully.

The workflow bound and exercised the verifier from exact canonical repair merge `003ed3a44b89779ff51df45cd1d015ef6da98370` and exact verifier blob `b8ed65776c6d9b5ae313c34d91c221b13a25197e`. It reset each deterministic candidate sandbox to that exact canonical merge and reproduced all nine pre-merge exact/missing/extra/deletion positive/negative results, including B2R16 task deletion rejection, B2R13 activation deletion rejection, and reconciliation deletion rejection.

This satisfies the Principle XVI requirement to exercise the repaired control against the exact canonical state after merge.

### Reconciled authority

This repair reconciliation does not change `research/000b2-public/recovery-attempt-003-readiness.json`, does not append a successor transition proof, and does not complete or advance any B2 recovery task.

After this reconciliation becomes canonical:

- the trusted-control repair dependency freeze is closed;
- `B2R16` remains the sole active successor recovery unit;
- ATTEMPT-003 remains required and unfrozen;
- primary decode and scoring remain closed;
- B2R17 and every later successor remain unauthorized;
- comparative publication/ranking, production selection, product code, and project completion remain closed;
- any B2R16 candidate must be freshly qualified against the then-current canonical base; evidence from a pre-repair base or earlier candidate head is stale.

This record authorizes only resumption of fresh B2R16 qualification under the ordinary successor gates. It does not authorize B2R16 merge, primary decode, B2R17, scoring, or any later project state.

## Reconciliation 002 — B2R16/ATTEMPT-003 lane: G1 waivers, corrections C1 and C2, and the #118 exception

**Authority:** `CONSTITUTION.md` 0.4.0, Principle XVII item 10 (combined reconciliation of a declared lane after its last correction) and Governance items 2 and 7. This record is not a successor task reconciliation. It changes records only: no authority, freeze, decode, scoring, readiness, task-scope or completion field changes (see "Records-only proof").

### Declared lane

Constitution 0.4.0 declares the B2R16/ATTEMPT-003 lane. The owner confirmed #135 as its further correction on 2026-11-08 ([owner act](https://github.com/TheHalfMoon/Wispral/pull/135#issuecomment-6724624778)). The lane is closed and complete:

| Correction | PR | Annex items | Exact reviewed head | Canonical merge | First parent |
| --- | --- | --- | --- | --- | --- |
| C1 | #130 | 1 (B2R16 freeze gate) | `cabf4e5d96ab03d38a74ee4e5986be17a26f5e74` | `5879c43c7a389bd460955f2e181e8bd70f0ecee5` | `8d52a4579a0b1c6555cbe8443027c1950493b326` |
| C2 | #135 | 3 and 4 (B2 scope gates and common verifier) | `64a7bb7b360dd472abfda645925ca4886cf3f104` | `d78ecb540d97ff07b6788339177e9d63ed4dfca3` | `76fe651a41eaf73e12f6ac85d7f159427ada1447` |

Both merges are guarded normal merges bound to the reviewed head (`--match-head-commit`), whose second parent is that head. The tree of `d78ecb5` equals the tree of `64a7bb7` (`15f3680de47e07f0b6b2d8debd29bf558e864a7b`).

### Constitutional amendments the lane depends on

**G1, Constitution 0.3.0 (#129).**

- Exact head `447d7da42edc3f719e94deae7de9d5c20d7f719c`, merged as `8d52a4579a0b1c6555cbe8443027c1950493b326` on base `edacdf7504302cc91ff7138bc6ac2d391e4df1f4`.
- The owner instruction "skip review and go ahead" is recorded in the [owner act](https://github.com/TheHalfMoon/Wispral/pull/129#issuecomment-6716186954).
- Three waivers are recorded here as an explicit exception, not relabeled:
  1. **No qualifying independent review.** Version 0.2.1, then in force, did not require one for amendments.
  2. **Transitional condition 3 partly met.** The pinned checker at `a97d596` (SHA-256 `b4ad0f3e…`) and its tests (`3b144f15…`) ran author-side only, and the reviewer did not reproduce them.
  3. **`verify-b2r16-freeze` red** ([run 42437922052](https://github.com/TheHalfMoon/Wispral/actions/runs/42437922052)), with the same over-application that `main` had before C1.
- **Ratified by A040.** The qualifying review of Constitution 0.4.0 (#133, Nemotron) covered the full amended Principle XVII and reproduced the transitional checker and its 7 tests at `a97d596`: APPROVE, 0 blocking ([record](https://github.com/TheHalfMoon/Wispral/pull/133#issuecomment-6723009224)). Waivers 1 and 2 are thereby ratified. Waiver 3 is closed by C1 (below).

**A040, Constitution 0.4.0 (#133).** Exact head `73fcfd8c32cda585c1ed103bd032cee6da826f63`, merged as `76fe651a41eaf73e12f6ac85d7f159427ada1447` on base `abcdb86e4950a1dbdbe823e28f59398517110e33`. Its qualifying review is NVIDIA Nemotron 3.5 Super, APPROVE, 0 blocking. A DeepSeek attempt that hit the 429 free-usage limit is disclosed and was not counted.

### Correction C1 — base-defined B2R16 freeze preservation (#130)

- **Defect.** `verify-b2r16-freeze` applied the B2R16 task-candidate range check to every later pull request: `B2R16 actual candidate range scope drift`.
- **Changed paths (3).**
  - `.github/workflows/000b2-public-b2r16-freeze.yml`: the annexed control. It is now base-defined: `pull_request_target`, which checks out base code.
  - `research/000b2-public/verify_b2r16_preservation.py`: the new verifier, now SHA-256 `fb7b75c840692c563e2455fd74c1e3363c45389c903d1d494c573871699bdd50` on `main`.
  - `research/000b2-public/test_b2r16_preservation.py`: the new tests.
- **Preserved pre-merge failures (item 5).** Each was evidenced with cause and non-concealment; the evidence is in #130's description and in `research/wispral-world-class/evidence/governance/c1/` on `main`.
  - `verify-successor-pr-from-canonical-base`: `TRUSTED_PR_GATE=FAIL: B2R17 candidate path scope violation` ([run 42443952651](https://github.com/TheHalfMoon/Wispral/actions/runs/42443952651)).
  - `verify-successor-recovery`: `TRUSTED_BOUNDARY=FAIL: B2R17 task-candidate path scope violation` ([run 42443954505](https://github.com/TheHalfMoon/Wispral/actions/runs/42443954505)).
  - The freeze job was absent on its own pull request because of the trigger change. It was replaced by `workflow_dispatch` [run 42443952258](https://github.com/TheHalfMoon/Wispral/actions/runs/42443952258) on the exact head: success, `B2R16_FROZEN_OBJECT_PRESERVATION=PASS`, 20 tests OK.
- **Qualifying review.** DeepSeek V4.1 Flash through OpenCode v2.2.5, read-only `plan` agent:
  - [round 1](https://github.com/TheHalfMoon/Wispral/pull/130#issuecomment-6717064649) on head `de095ea`: REQUEST_CHANGES, 4 blocking;
  - [round 2](https://github.com/TheHalfMoon/Wispral/pull/130#issuecomment-6717064922) on head `cabf4e5`: APPROVE, 0 blocking.
- **Post-merge (item 9)** ([record](https://github.com/TheHalfMoon/Wispral/pull/130#issuecomment-6717148669)).
  - The freeze push [run 42446197959](https://github.com/TheHalfMoon/Wispral/actions/runs/42446197959) on `5879c43` succeeded.
  - `000B2 Public Corpus ATTEMPT-003 Recovery` push [run 42446198003](https://github.com/TheHalfMoon/Wispral/actions/runs/42446198003) **failed** with `TRUSTED_BOUNDARY=FAIL: B2R17 task-candidate path scope violation`. It was preserved conflict evidence under item 5 until this reconciliation, and was never rerun to green.
  - The other seven push runs succeeded.
- **Open from C1, closed by C2.** Item 3a protection of #130's checker and tests: they are B2-owned paths under C2's non-successor class, and are covered by C2's negative fixture `neg_c1_checker`.

### Correction C2 — non-successor class for the B2 scope gates (#135)

- **Defect.** Both B2 scope gates treated every pull request touching their path filters as a B2R17 task candidate. This blocked every non-B2 governance pull request that edits the frontier files.
- **Changed paths.**
  - `.github/workflows/000b2-public-attempt-003-trusted-pr.yml`: annexed step "Verify trusted-base event and immutable control boundary";
  - `.github/workflows/000b2-public-attempt-003-recovery.yml`: annexed step "Trusted pre-candidate execution boundary";
  - `research/000b2-public/verify_attempt_002_invalidation.py`: the new function `nonsuccessor_violations` and the early returns in `verify_active_task_candidate_content`;
  - the evidence directory `research/control-repairs/2026-11-08-c2-nonsuccessor-class/`.
- **Item 3, in-class corpus.** The manifest has SHA-256 `867c0b9fa00462d6825d02be47be9d4c3aa3804c956efccd1e37018ef427b716` and covers 114 historical candidates. Every one has non-empty violations, so every historical verdict is preserved.
- **Item 5, A3 immutable boundary.**
  - `A3_BOUNDARY=PASS`;
  - the per-blob revert clears the boundary;
  - the immutable list is unchanged;
  - the neutralization diff is pinned in the evidence directory, and the skipped checks were run separately.
- **Preserved exact-head failures** ([record](https://github.com/TheHalfMoon/Wispral/pull/135#issuecomment-6724448501)):
  - `verify-successor-pr-from-canonical-base`: `TRUSTED_PR_GATE=FAIL: immutable execution control changed: .github/workflows/000b2-public-attempt-003-recovery.yml` ([run 42498837525](https://github.com/TheHalfMoon/Wispral/actions/runs/42498837525));
  - `verify-successor-recovery`: `TRUSTED_BOUNDARY=FAIL: B2R17 task-candidate path scope violation` ([run 42498837653](https://github.com/TheHalfMoon/Wispral/actions/runs/42498837653)).
- **Other exact-head checks.** Freeze, methodology and legacy recovery passed. Four materialization-authority jobs were skipped by their own conditions.
- **Qualifying review.** NVIDIA Nemotron 3.5 Super through OpenCode v2.2.5, read-only `plan` agent ([record](https://github.com/TheHalfMoon/Wispral/pull/135#issuecomment-6724319490)):
  - round 1: REQUEST_CHANGES, 1 blocking;
  - round 2, same head after the author's evidence: APPROVE, 0 blocking.
- **Follow-ups (non-blocking, not part of this lane):**
  - confusables folding of marker text inside allowlisted sections;
  - the trusted-coverage path-filter extension of plan §4.2 item 4, which is outside A3.

### Lane-end exercise on canonical `main` (items 5 and 9)

**Push runs on the C2 merge `d78ecb5`.** Eight succeeded:

- [`000B2 Public Corpus B2R16 Freeze`](https://github.com/TheHalfMoon/Wispral/actions/runs/42504703558);
- `000B2 Public Corpus Methodology` (run 42504703567);
- `000B2 Public Corpus Attempt Recovery` (run 42504703583);
- `000B2 Public Corpus Candidate Revalidation` (run 42504703644);
- `000B2 Trusted Materialization Authority` (run 42504703594);
- `000B2 Trusted Participant Materials` (run 42504703595);
- `000B2 Trusted Participant Policy` (run 42504703873);
- `000B2 Trusted Human Authority Structure` (run 42504703701).

**The ATTEMPT-003 recovery gate failed again on the C2 merge.** Push [run 42504703566](https://github.com/TheHalfMoon/Wispral/actions/runs/42504703566) failed at `Trusted pre-candidate execution boundary` with `TRUSTED_BOUNDARY=FAIL: B2R17 task-candidate path scope violation`.

- **Why.** A push run takes `github.event.before` as its authority base. Here that is `76fe651`, before C2, which has no non-successor classification. So the run judged C2's own merge diff with the uncorrected classification.
- **Same failure.** The gate, the step and the exact failure line are identical to C2's preserved pre-merge failure (run 42498837653) and to the post-C1 push failure (run 42446198003). Under item 5 it remains preserved conflict evidence until this reconciliation merges. It was not rerun to green.

**The recovery gate passes on canonical `main`, as item 5 requires of this reconciliation.** [`workflow_dispatch` run 42508548479](https://github.com/TheHalfMoon/Wispral/actions/runs/42508548479) on `main` at `d78ecb5` makes the authority base and the exact revision both `d78ecb5`, so the corrected classification judges the canonical state. Result: **success**. Every step passed, including `Trusted pre-candidate execution boundary`, the successor frontier, the material-drift check and the transition proofs. The run printed:

```text
AUTHORITY_BASE_REVISION=d78ecb540d97ff07b6788339177e9d63ed4dfca3
EXACT_REVISION=d78ecb540d97ff07b6788339177e9d63ed4dfca3
TRUSTED_PRE_CANDIDATE_BOUNDARY=PASS
ACTIVE_SUCCESSOR_RECOVERY_UNIT=B2R17
VALIDATED_SUCCESSOR_TRANSITIONS=4
ATTEMPT_003_PRIMARY_DECODE_AUTHORIZED=YES
COMPARATIVE_RESULT_AVAILABLE=NO
PRODUCTION_STT_SELECTED=NO
PRODUCT_CODE_AUTHORIZED=NO
HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT
```

The full key-line output is in [`runs/recovery_dispatch_42508548479.txt`](../../research/control-repairs/2026-11-08-lane-reconciliation/runs/recovery_dispatch_42508548479.txt). The first push run on `main` after this reconciliation merges will use `d78ecb5` or later as its base, and will judge only its own diff.

### Exception: #118 merged with a red required verifier and no approving review

- **#118** ("docs(000b2): reconcile B2R16 to B2R17") had exact final range `885307429ec8b1aa0fe173169a8c2918714c06b0..b7824b353594857b1700442584fa7734ad1b1c70`. It merged as `edacdf7504302cc91ff7138bc6ac2d391e4df1f4` on 2026-09-10.
- **What it changed.** Four paths:
  - `docs/canonical/CURRENT_STATE.md`;
  - `research/000b2-public/recovery-attempt-003-readiness.json`;
  - `specs/000B2-public-corpus-bakeoff/recovery-v2-tasks.md`;
  - `specs/CURRENT.md`.

  It marked B2R16 complete, kept ATTEMPT-003 frozen (digest `b92d0a88bb50ebde517f560878a26d0ef796abdaf931278f5bc43e372ff1ac8d`), and opened primary-decode entry for B2R17 only.
- **The exception, recorded as is.** It merged while `verify-b2r16-freeze` was red ([run 34416457849](https://github.com/TheHalfMoon/Wispral/actions/runs/34416457849), `B2R16 actual candidate range scope drift`). It also merged without an approving review: CodeRabbit only commented. Its own pre-merge status comment required a fresh independent review of the final range first. All other applicable checks passed, including both B2 scope gates.
- **Fresh evidence (2026-11-08).** The trusted base-defined checker from C1 (`verify_b2r16_preservation.py` on `main` at `d78ecb5`, SHA-256 `fb7b75c8…`) was run with `--candidate` set to both `b7824b3…` and `edacdf7…`. Both runs printed:
  - `B2R16_ATTEMPT_003_FREEZE=PASS`;
  - `B2R16_FREEZE_DIGEST=b92d0a88…`;
  - `B2R16_FROZEN_OBJECT_PRESERVATION=PASS`.

  The red check was the over-application that C1 corrected (annex item 1). The frozen B2R16 objects were preserved.
- **Qualifying retrospective review:** APPROVE, 0 blocking findings.

  - **Reviewer.** NVIDIA Nemotron 3.5 Super (vendor: NVIDIA), a different vendor from the author's model (Anthropic Claude).
  - **Route.** OpenCode v2.2.5, model `opencode/nemotron-3.5-super-vl-free`, read-only `plan` agent, fresh session, cost 0.
  - **What it did.** In 13 read-only tool calls it:
    - re-ran the trusted checker on both SHAs, with the same PASS result;
    - verified the B2R16 binding (`ac9f7ce…`, `885307429…`, run 34415906199) and the readiness transition;
    - verified the four-path scope and that only B2R17 primary-decode entry was opened.
  - **Disclosed defect.** The output's own header mislabels the reviewer as "Anthropic Claude model". That is wrong: the reviewer's identity is the route above.
  - The prompt and the verbatim output are in [`review-118/`](../../research/control-repairs/2026-11-08-lane-reconciliation/review-118/).

  This review satisfies the condition #118 set for itself: a fresh independent review of the exact final range that resolves the applicability of the red check.
- **Founder decision on the B2R17 frontier:** **the B2R17 frontier stands** (owner, 2026-11-08). The owner chose "Frontier stands" when given the evidence above, against the alternative of suspending B2R17. B2R17 (`moonshine-compact`, candidate cell 1) remains the active successor recovery unit. #118 stays recorded as an exception, not relabeled as a passing merge.

### Records-only proof (item 10)

`research/control-repairs/2026-11-08-lane-reconciliation/r_field_diff.py` compares three revisions:

- the pre-correction base `8d52a45` (before C1);
- the pre-reconciliation base `d78ecb5`;
- this reconciliation's head.

It requires all of the following:

- every authority-bearing path and tree is byte-identical across all three: `docs/canonical/CURRENT_STATE.md`, `specs/CURRENT.md`, the ATTEMPT-003 readiness file, the B2R16 pre-execution state and manifest, `research/000b1/**`, `research/000b2-entry/**` and `specs/000B2-public-corpus-bakeoff/**`;
- every readiness field is equal;
- this reconciliation changes only this ledger (append-only), one reading-order line of `AGENTS.md`, and its own evidence directory.

Its output is in [`runs/field_diff.txt`](../../research/control-repairs/2026-11-08-lane-reconciliation/runs/field_diff.txt).

### Independent review of this reconciliation

Item 10 requires a qualifying review. It covers this reconciliation's exact final head, and is recorded on its pull request with the reviewer's identity, the prompt, the verbatim output and that head SHA. The owner's merge act on that pull request names the review it relies on.

### Reconciled authority

After this reconciliation becomes canonical:

- **Corrections C1 and C2 are reconciled.** Work outside the lane may rely on them (Principle XVII item 10).
- **Preserved failures end.** The preserved failures of C1 and C2, including the post-C1 recovery push failure on `main`, are recorded above and end with this reconciliation. Any later failure of those gates is a new failure.
- **Non-B2 governance pull requests.** They may pass both B2 scope gates as non-successor candidates. They still edit frontier sections only where a constitutional amendment designates them, and no amendment has designated them yet (G2 does).
- **B2 state is unchanged:**
  - ATTEMPT-003 remains frozen;
  - B2R17 is the active successor recovery unit, as the owner confirmed above;
  - scoring, B2R18+, comparative publication or ranking, production selection, product code and project completion remain closed;
  - any B2R17 candidate, including #120, must be freshly requalified against the then-current canonical base.

This reconciliation authorizes no decode, scoring, product code or later project state.
