# Wispral governance and CI reconciliation research

Date: 2026-11-08. Repository `TheHalfMoon/Wispral`. Canonical main `edacdf7504302cc91ff7138bc6ac2d391e4df1f4`. All GitHub access was read-only (`gh api` GET, `gh pr view/checks`, `gh run view --log-failed`). Nothing was pushed, commented, reviewed, labeled, dispatched or changed.

Unless a different ref is named, file:line citations refer to `main@edacdf7`.

Evidence tags:

- `SOURCE_VERIFIED`: read in the file at the cited sha and line.
- `RUNTIME_OBSERVED`: seen in GitHub check runs or logs.
- `REPRODUCED`: run locally, with output saved under `scratchpad\gov\`.
- `DOCUMENTED`: stated in a repository document but not independently verified.
- `NOT_RUN`: not executed.
- `BLOCKED_EXTERNAL`: needs the owner or an outside system.
- `REJECTED`: an option evaluated and turned down.

## 0. Environment notes

- Worktrees could not live inside the scratchpad. The scratchpad path plus the repository's file paths exceed Windows MAX_PATH (`LongPathsEnabled=0`). Detached worktrees and two isolated `--shared` clones were therefore created under `<local-temp>\wg\`:
  - worktrees `main`, `pr120`, `pr124`, `pr126`;
  - clone `c126` at the #126 head;
  - clone `csim` holding the synthetic candidate commits `sim-a`, `sim-b` and `sim-bmin`.
- Synthetic commits and test-fixture Git objects were written only into the isolated clones. They were never written into the shared clone.
- **Concurrent actor observation.** During this session the shared clone's checked-out branch changed from `main` to `planning/wispral-world-class-master-plan-20261108` (HEAD `d7d55e5`, which has local merges of pr123, pr124 and pr125, plus untracked `docs/design/`, `docs/engineering/` and two `docs/strategy/*.md` files). Reflog: `checkout: moving from main to planning/...` then `merge pr123/pr124/pr125`. **This was not done by this agent.** The coordinator should know that this local branch contains unmerged PR content.
- Saved evidence files:
  - `scratchpad\gov\wfsum_main.txt`: parsed workflow summary.
  - `trigger_match.py` and `trigger_matrix.txt`: path-filter simulation.
  - `run_inline_gate.py` and `scope_gate_sim.txt`: trusted-gate simulation.
  - `content_verifiers.sh` and `content_verifiers.txt`.
  - `verify_b2r16_repro.txt`.
  - `pr126_failed_logs.txt` and `pr126_tests.txt`.

## 1. Executive summary

1. **Every open PR fails `verify-b2r16-freeze`.**
   - `RUNTIME_OBSERVED` on #120, #121, #123, #124 and #125 with `B2R16_ATTEMPT_003_FREEZE=FAIL: B2R16 actual candidate range scope drift`.
   - `REPRODUCED` on canonical main, pr124, pr126 and pr120.
   - Cause (`SOURCE_VERIFIED`): the workflow runs on every `pull_request` (`.github/workflows/000b2-public-b2r16-freeze.yml:3-5`). The verifier diffs the fixed base `4834840…` against HEAD and requires exactly the four B2R16 paths (`research/000b2-public/verify_b2r16.py:35,46-51,123-130`).
   - Without `--require-git` it still fails, because it requires `completed_recovery_tasks == [B2R13,B2R14,B2R15]` (`verify_b2r16.py:138-140`). The verifier can therefore never pass on its own B2R16 reconciliation (#118) or on any later state.
   - Classification: **fail-closed over-application**. I agree with Opus M1. Principle XVI (fail-open only) does not apply.
2. **Larger finding: the freeze check is not the only blocker.** The two B2 trusted scope gates reject every non-B2 PR that touches `specs/CURRENT.md`, `docs/canonical/CURRENT_STATE.md`, `research/000b2-public/**`, `specs/000B2-public-corpus-bakeoff/**`, `.github/workflows/000b2-public-*.yml` or `research/000b1/frozen-methodology.json`.
   - The gates are `verify-successor-recovery` and `verify-successor-pr-from-canonical-base`. The paths above are their path filters (`000b2-public-attempt-003-recovery.yml:4-21`, `000b2-public-attempt-003-trusted-pr.yml:4-11`).
   - This is `REPRODUCED` with a harness that runs the exact inline programs from main. The harness was validated against #126 (both fail with the same text as CI) and #120 (both pass, as in CI).
   - A synthetic constitutional amendment that edits `specs/CURRENT.md` and `CURRENT_STATE.md` fails both gates with `B2R17 candidate path scope violation`.
   - The common verifier also fails it: `ATTEMPT_002_INVALIDATION=FAIL: B2R17 candidate must match the exact canonical task path set`.
   - **The lock is permanent, not temporary.** After ATTEMPT-003 completes, `active_recovery_unit` becomes `None`. `scopes.get(None)` is `None`, so the trusted gate raises `None candidate path scope violation` (`000b2-public-attempt-003-trusted-pr.yml:153-158`, `SOURCE_VERIFIED`, not simulated). Waiting for B2 to finish does **not** unlock the frontier files.
3. **#126 cannot legitimately merge under current authority.**
   - It fails `verify-successor-recovery` (`TRUSTED_BOUNDARY=FAIL: B2R17 task-candidate path scope violation`, run 39605446769) and `verify-successor-pr-from-canonical-base` (`TRUSTED_PR_GATE=FAIL: B2R17 candidate path scope violation`, run 39605446875).
   - It calls itself an "ordinary" correction, but no current authority allows an ordinary PR to preserve those red results. Principle XVI item 5 allows preserved non-successes only for fail-open repairs.
   - Its preservation checker is technically sound. Its test suite passed 7/7 locally (`REPRODUCED`, 366 s on Windows; 3.5 s in CI).
4. **#118 merged with a red check that was never recorded.** It merged with `verify-b2r16-freeze` red (run 34416457849) and no submitted approving review. CodeRabbit left two `COMMENTED` reviews and `reviewDecision` is empty.
   - `grep` for `34416457849`, `verify-b2r16-freeze`, `B2R16 Freeze` and `#118` across canonical docs finds no record (`REPRODUCED`).
   - Every other check triggered on #118 passed, including both B2 trusted gates.
5. **Recommendation: Option B (lane first). Five PRs: G1 → C → R → G2 → F.**
   - **G1:** narrow constitutional minor amendment adding a fail-closed over-application correction lane, with a transitional clause.
   - **C:** one control-correction PR that both preserves the B2R16 freeze and adds a strictly bounded non-successor classification to the B2 trusted gates.
   - **R:** ledger reconciliation, which also records #118.
   - **G2:** platform major amendment touching only paths outside every path filter.
   - **F:** frontier reconciliation of `specs/CURRENT.md`, `CURRENT_STATE.md` and the 000 `tasks.md`.
   - B2 stays frozen and resumable. #120 must be requalified after C.

## 2. Task 1: workflow inventory on main

Source: the 27 files under `.github/workflows` at `edacdf7` (`SOURCE_VERIFIED`, parsed with PyYAML; full dump in `gov\wfsum_main.txt`).

- "PR" means the `pull_request` event and "PRT" means `pull_request_target`.
- The "Trusted" column means the job calls `.github/trusted/*`.

| # | Workflow | Events and filters | Jobs and `if:` | Trusted | What it verifies |
|---|---|---|---|---|---|
| 1 | 000a-acp-probe | PR paths: wf, `research/000a/**`, `fixtures/acp-probe/**`, `docs/research/acp/**`, `specs/000A-acp-qualification/**`; dispatch | evidence-verifier; protocol-probe (matrix) | no | 000A ACP evidence and probe |
| 2 | 000b1-preregistration | push on 3 research branches; PR paths: `docs/research/stt/000b1-*`, `CURRENT_STATE.md`, `research/000b1/**`, `specs/CURRENT.md`, `specs/000-founding-research/tasks.md`, `specs/000B-stt-entity-bakeoff/tasks.md`, `specs/000B1-…/**`, wf | verify-preregistration | no | 8 `research/000b1/*` verifiers, including document and parent-frontier reconciliation |
| 3 | 000b2-corpus-manifest-format | PR and push(main) paths: `research/000b2-entry/corpus/**`, wf | verify-corpus-manifest-format | no | Corpus manifest format |
| 4 | 000b2-entry-contracts | push (main, entry branch) and PR paths: entry scorer/smoke/readiness/closeout/authority/preprocessing/environment, `specs/CURRENT.md`, 000B `tasks.md`, `CURRENT_STATE.md`, wf | verify-entry-contracts | no | Scorer, smoke, authority, consent, policy freeze, capture boundaries, entry draft (fetches origin main), closeout/readiness |
| 5 | 000b2-entry-materialization | push (entry branch) and PR paths: materialization files, `research/000b1/qualified-candidates.json` | materialize-pending-artifacts | no | Pending artifact materialization |
| 6 | 000b2-operational-smoke | push (entry branch), PR paths, dispatch | moonshine, whisper, sherpa, aggregate (needs all 3) | no | Non-primary smoke |
| 7 | 000b2-preprocessing-toolchain | push (entry branch), PR paths `preprocessing/**`, dispatch | qualify-ffmpeg | no | FFmpeg toolchain |
| 8 | **000b2-public-attempt-003-recovery** | PR and push(main) paths: `.github/workflows/000b2-public-*.yml`, `research/000b1/frozen-methodology.json`, `research/000b2-public/**`, `specs/000B2-public-corpus-bakeoff/**`, `specs/CURRENT.md`, `docs/canonical/CURRENT_STATE.md`; dispatch | **verify-successor-recovery** | no | Trusted pre-candidate boundary (scope/delta: lines 92-162); common verifier `--static-only`; pinned sherpa API; recovery invariants and transition proofs via the GitHub API (362-547) |
| 9 | **000b2-public-attempt-003-trusted-pr** | **PRT** with the same paths as #8 | **verify-successor-pr-from-canonical-base**, `if: base.ref=='main'` | no (inline Python from the base definition) | Immutable policy fields (83-94), immutable control blobs (110-119), delta/scope (121-160), common-verifier exact bytes (162-164), common verifier static plus sherpa |
| 10 | 000b2-public-attempt-freeze | PR and push(main) paths: attempt-manifest/WER/readiness/qualified-candidates/frozen-methodology/scorer, 000B2 `tasks.md`, `specs/CURRENT.md`, wf | verify-b2p08-attempt-freeze | no | B2P08 attempt freeze reproduction; requires Python 3.12 |
| 11 | 000b2-public-attempt-recovery | PR and push(main) paths: wf, frozen-methodology, `research/000b2-public/**`, `specs/000B2-…/**`, `specs/CURRENT.md`, `CURRENT_STATE.md` | verify-legacy-recovery-boundary | no | ATTEMPT-001/002 historical blobs; `verify_attempt_001_invalidation.py` |
| 12 | 000b2-public-b2e01 | PR and push(main) paths: b2e01 files, attempt-manifest, readiness, `specs/CURRENT.md`, 000B2 `tasks.md` | verify-b2e01-evidence | no | B2E01 evidence |
| 13 | 000b2-public-b2e02 | Same pattern as #12 | verify-b2e02-evidence | no | B2E02 evidence |
| 14 | 000b2-public-b2r14-harness | dispatch only | qualify-b2r14-harness | no | B2R14 harness |
| 15 | 000b2-public-b2r15-rebinding | PR paths: b2r15 files, wf; dispatch | verify-b2r15-rebinding | no | B2R15 rebinding |
| 16 | **000b2-public-b2r16-freeze** | **PR with no filter**; dispatch | **verify-b2r16-freeze** | no | `verify_b2r16.py --require-git` (exact B2R16 task range and frozen identities) |
| 17 | 000b2-public-candidate-revalidation | PR paths (includes `.github/trusted/verify_000b2_materialization.py`); push(main) with **no** path filter | static-candidate-revalidation; live-candidate-revalidation (needs static) | **yes** (`trusted-base/.github/trusted/verify_000b2_materialization.py`, line 94) | Six-cell candidate identity revalidation |
| 18 | 000b2-public-environment | PR and push(main) paths: env capture files | verify-public-corpus-environment | no | Environment evidence |
| 19 | 000b2-public-materialization | PR and push(main) paths: corpus-source, readiness, materialize/verify scripts, 000B2 `tasks.md`, `specs/CURRENT.md`, `CURRENT_STATE.md`, wf | materialize-official-archives | no | Re-fetches the official OpenSLR archives (network) |
| 20 | 000b2-public-methodology | PR and push(main) paths: `specs/000B-…/**`, `specs/000B2-public-corpus-bakeoff/**`, `specs/000-founding-research/tasks.md`, `specs/CURRENT.md`, `CURRENT_STATE.md`, `research/000b2-public/**`, wf | verify-public-corpus-methodology | no | `verify_workflow_contracts.py`, `verify_methodology.py` |
| 21 | 000b2-public-preprocessing | PR and push(main) paths: preprocessing files | capture-public-corpus-preprocessing | no | Preprocessing capture |
| 22 | 000b2-public-subset-freeze | PR and push(main) paths: subset files, 000B2 `tasks.md`, `specs/CURRENT.md`, wf | freeze-public-corpus-subset | no | B2P04 subset reproduction (re-fetches archives) |
| 23 | 000b2-public-subset-selection | PR and push(main) paths: subset policy/select, readiness, 000B2 `tasks.md`, `specs/CURRENT.md`, `CURRENT_STATE.md`, wf | verify-public-corpus-subset-selection | no | Deterministic selection |
| 24 | 000b2-trusted-human-authority | PR and PRT paths: trusted verifier, wf, authority/**, entry readiness, `validate_entry_manifest.py`, `specs/CURRENT.md`, `CURRENT_STATE.md`; push(main) with no filter | bootstrap-self-test (`if event==pull_request`); verify-candidate-structure-from-live-base (`if PRT && base==main`); verify-canonical-and-open-prs-after-base-push (`if push`, with `--reverify-open-prs`) | **yes** | Human-authority structure remains blocked |
| 25 | 000b2-trusted-materialization-authority | PR paths: trusted verifier and wf; **PRT with no filter**; push(main) | bootstrap-self-test (pull_request); verify-pr-head-artifact-identity (`if PRT && pull_request.number == 10`, so skipped on every other PR); resolve-active-b2-head and reverify-active-b2-after-base-push (push) | **yes** | Materialization identity; reverify active B2 head |
| 26 | 000b2-trusted-participant-materials | Same pattern as #24 (materials paths) | candidate-self-test; verify-candidate-materials-from-live-base; verify-canonical-and-open-prs-after-base-push | **yes** | Participant materials remain non-authorizing |
| 27 | 000b2-trusted-participant-policy | Same pattern as #24 (policy paths) | bootstrap-self-test; verify-candidate-policy-from-live-base; verify-canonical-and-open-prs-after-base-push | **yes** | Participant policy remains non-authorizing |

Additional notes:

- `pull_request` workflows run from the PR merge-commit definition, so they are candidate-controllable. #126's own `verify-b2r16-freeze` passes because it uses its edited workflow (`RUNTIME_OBSERVED`, run 39605446815).
- The `pull_request_target` gates (#9, plus the live-base jobs in #24, #26 and #27) run from the base definition.
- Every B2 workflow except #16 already defines applicability through path filters.

## 3. Task 2: applicability matrix

Method:

- `trigger_match.py` applies the main workflows' path filters to the actual diff. It is validated against the observed check lists of #126 and #120. Both matched, except that #120 also ran `verify-b2r17-capture` from its own new workflow file.
- Gate outcomes come from `run_inline_gate.py`, which runs the exact inline Python of `main@edacdf7` against each candidate.
- Content verifiers come from `content_verifiers.sh`, run on main as a baseline and on the candidate.

### (a) Planning PR adding only new files under `docs/strategy`, `docs/design`, `docs/engineering` and `research/wispral-world-class` (synthetic `sim-a` = `478c771`)

| Job | Expected | Why |
|---|---|---|
| verify-b2r16-freeze | **FAIL** `B2R16 actual candidate range scope drift` (`REPRODUCED` on equivalent heads; `RUNTIME_OBSERVED` on #121/#123/#124) | No path filter (`b2r16-freeze.yml:3-5`); range check at `verify_b2r16.py:123-130` |
| trusted-materialization-authority (4 jobs) | skipped | `if:` conditions (#25); not applicable (precedent at `TRUSTED_CONTROL_REPAIRS.md:48`) |
| All other workflows | not triggered | No path match (`trigger_matrix.txt`) |

The B2 scope logic would also reject `sim-a` if it ran (`scope_gate_sim.txt`), but its path filters keep it from running.

**Verdict:** class (a) is blocked only by the over-applied freeze check.

### (b) Constitutional amendment touching `CONSTITUTION.md`, `AGENTS.md`, `docs/canonical/*.md`, `specs/CURRENT.md` and `specs/000-founding-research/*` (synthetic `sim-b` = `d88023d`, append-only edits)

Triggered:

- verify-preregistration
- verify-entry-contracts
- **verify-successor-recovery**
- **verify-successor-pr-from-canonical-base**
- verify-b2p08-attempt-freeze
- verify-legacy-recovery-boundary
- b2e01 and b2e02
- **verify-b2r16-freeze**
- materialize-official-archives
- methodology
- subset-freeze
- subset-selection
- 3 trusted bootstrap/self-test jobs plus 3 live-base PRT jobs
- materialization-authority (skipped)

Results:

| Job | Expected | Evidence |
|---|---|---|
| verify-successor-pr-from-canonical-base | **FAIL** `TRUSTED_PR_GATE=FAIL: B2R17 candidate path scope violation` | `REPRODUCED` (`scope_gate_sim.txt`); `trusted-pr.yml:152-158`; scope source is readiness `task_candidate_scopes.B2R17` (`recovery-attempt-003-readiness.json:35`) |
| verify-successor-recovery | **FAIL** `TRUSTED_BOUNDARY=FAIL: B2R17 task-candidate path scope violation` | `REPRODUCED`; `recovery.yml:159-162` |
| Common verifier (inside both gates) | **FAIL** `ATTEMPT_002_INVALIDATION=FAIL: B2R17 candidate must match the exact canonical task path set` | `REPRODUCED`; `verify_attempt_002_invalidation.py:409-420` |
| verify-b2r16-freeze | **FAIL** (range drift) | as above |
| 18 other locally runnable static verifiers | Same result as on the main baseline (no candidate-caused change) | `REPRODUCED` (`content_verifiers.txt`) |
| materialize-official-archives, subset-freeze reproduction | `NOT_RUN` (network re-fetch) | passed on main push 34421260127 / 34421260191 |

The 18 static verifiers in the middle row are:

- methodology: 2;
- preregistration: 7 of 8;
- entry-contracts: 3;
- b2e01 and b2e02;
- attempt-freeze: 2;
- trusted-human, trusted-materials and trusted-policy.

Some local baseline failures are environmental and identical on main: `-I` import failures in `verify_closeout_regressions` and the subset verifiers, and the local `verify_attempt_001_invalidation` marker failure. These are `NOT_RUN`-equivalent and were not diagnosed further.

`sim-bmin` (`8420cc6`) changes only `CONSTITUTION.md`, `AGENTS.md`, `ARCHITECTURE_INVARIANTS.md`, `PROGRAM_ROADMAP.md`, `TRUSTED_CONTROL_REPAIRS.md` and the 000 `spec.md` and `plan.md`. It triggers **only** verify-b2r16-freeze plus the skipped materialization jobs (`REPRODUCED`).

Precedent: the earlier amendments #107 and #110 (CONSTITUTION-only) and ledger reconciliation #116 ran no applicable gates (`RUNTIME_OBSERVED` check-runs on `4530ae3`, `ff19e04` and `e54e483`).

### (c) PR #126 (head `a97d596`, draft)

`RUNTIME_OBSERVED` (`gh pr checks 126`):

- verify-b2r16-freeze: pass (candidate definition)
- verify-legacy-recovery-boundary: pass
- verify-public-corpus-methodology: pass
- materialization-authority: skipped
- **verify-successor-recovery: fail** (run 39605446769)
- **verify-successor-pr-from-canonical-base: fail** (run 39605446875)

Exact failing assertions, from the logs in `gov\pr126_failed_logs.txt`:

- Run 39605446875, step "Verify trusted-base event and immutable control boundary":
  - Output: `TRUSTED_PR_GATE=FAIL: B2R17 candidate path scope violation`
  - Env: `EXACT_REVISION=a97d596…`, `AUTHORITY_BASE_REVISION=edacdf7…`
  - Assertion at `trusted-pr.yml:156-158`: `allowed = scopes.get(active); if not isinstance(allowed, list) or not changed <= set(allowed): raise …`
  - Authority: readiness `task_candidate_scopes.B2R17` (json:35), made immutable by `trusted-pr.yml:83-94`. The gate's mandate is `recovery-v2.md:112-116,185`.
- Run 39605446769, step "Trusted pre-candidate execution boundary":
  - Output: `TRUSTED_BOUNDARY=FAIL: B2R17 task-candidate path scope violation`
  - Assertion at `recovery.yml:159-162`, with scope immutability at `recovery.yml:133-134`.

Both failures are reproduced bit-for-bit by the local harness (`REPRODUCED`). The sole cause is that #126 changes `.github/workflows/000b2-public-b2r16-freeze.yml` and adds `research/000b2-public/*preservation.py` and `research/control-repairs/**`. These paths are outside the B2R17 scope. Neither gate reached later steps.

**Authority status:** no canonical clause lets these two red results be preserved for a fail-closed correction. Principle XVI items 4 and 5 (`CONSTITUTION.md:118-119`) cover only XVI repairs, which require a fail-open defect (`CONSTITUTION.md:111`). Verdict: **blocked; requires a new lane** (§6).

### (d) B2R17 PR #120 (head `85fe810`)

`RUNTIME_OBSERVED`:

- verify-b2r17-capture: pass
- verify-successor-recovery: pass (34423115301)
- verify-successor-pr-from-canonical-base: pass (34423115482)
- legacy-recovery: pass
- methodology: pass
- **verify-b2r16-freeze: fail** (34423115319, `B2R16 actual candidate range scope drift`)

`REPRODUCED`: both trusted gates pass locally.

The owner's comment (2026-09-10T00:54:46Z) says "MUST NOT MERGE". It names the freeze failure, and states that the remaining gate is a fresh, non-rate-limited, independent substantive review.

The freeze verifier is the **B2R16** task's required verifier (readiness `task_content_policies.B2R16.required_verifier`). Applying it to B2R17 is over-application.

**Expected after correction C:** freeze passes once #120 merges main into its branch, because the corrected workflow reads the checker from the candidate checkout. Trusted gates should be unchanged, but #120 must be fully requalified at the new head. Stale evidence does not transfer (`recovery-v2.md:106`).

## 4. Task 3: reproduction

All runs used `python -I` with `PYTHONDONTWRITEBYTECODE=1`, Python 3.14.7 on Windows, and Git with `core.autocrlf=false`.

**`verify_b2r16.py`** (CLI is argparse with the single flag `--require-git`; `verify_b2r16.py:271-273`). Output saved in `gov\verify_b2r16_repro.txt`. Results are identical on all four heads:

| Head | `--require-git` | Without the flag |
|---|---|---|
| main `edacdf7` | `B2R16_ATTEMPT_003_FREEZE=FAIL: B2R16 actual candidate range scope drift` EXIT=1 | `…FAIL: canonical recovery prefix drift` EXIT=1 |
| pr124 `e7064c7` | same | same |
| pr126 `a97d596` | same | same |
| pr120 `85fe810` | same | same |

**#126 checker and test suite** (from isolated clone `c126`; output in `gov\pr126_tests.txt`):

- `verify_b2r16_preservation.py --candidate` passes for `a97d596`, `edacdf7` and `e7064c7`. Each run prints the historical `B2R16_ATTEMPT_003_FREEZE=PASS` block, then `B2R16_FROZEN_OBJECT_PRESERVATION=PASS`, exit 0.
- `test_b2r16_preservation.py`: **7/7 OK, 366.3 s locally**. That is slightly over the 5-minute budget; it ran to completion. CI took 3.5 s (run 39605446815).
- The checker and test SHA-256 values match the workflow literals `b4ad0f3e…` and `3b144f15…`.

**Trusted-gate harness** (`gov\scope_gate_sim.txt`), using main's inline programs:

| Candidate | Trusted PR gate | Recovery boundary |
|---|---|---|
| #126 | FAIL (scope) | FAIL (scope) |
| #120 | PASS (delta 0, control bytes PASS) | PASS |
| sim-a | FAIL | FAIL |
| sim-b | FAIL | FAIL |
| sim-bmin | FAIL | FAIL |
| main vs main | `FAIL: empty successor candidate` (expected) | PASS |

The full recovery-workflow transition-proof step needs a GitHub token and was `NOT_RUN`.

## 5. Task 4: where authority defines required and applicable checks

| PR class | Authority found | Content |
|---|---|---|
| (i) Ordinary PRs | **None defines a required-check list.** `AGENTS.md:113-126` (§10) says PRs list "checks run and checks not run" and asks to "Reconcile head, base, CI, reviews…before merge". `specs/CURRENT.md:253-264` (Global evidence gate) requires "exact-head CI" before a **child becomes VERIFIED**. | Applicability is never defined. In practice it comes from workflow path filters, plus the always-on freeze check. |
| (ii) B2 task and reconciliation PRs | `specs/000B2-public-corpus-bakeoff/recovery-v2.md` | Line 97: "all applicable repository CI pass on the exact final head". Lines 112-116: the trusted PR gate is mandatory for B2R14+ tasks and **every successor reconciliation**. Lines 174-187: merge gates, including line 185 ("exact-head applicable CI necessarily includes a successful … Trusted PR Gate") and line 187 ("If no independent reviewer is available, the PR remains blocked"). Readiness `transition_policy` (json:74-87) gives immutable controls and reconciliation scope. |
| (iii) Amendment PRs | `CONSTITUTION.md:127-133` | Governance: dedicated PR with motivation, compatibility, security/privacy and affected specs; semver. **No CI or review requirement is stated.** Precedent: #107 and #110 had no submitted reviews and no applicable gates. |
| (iv) Control repairs | `CONSTITUTION.md:107-125` (Principle XVI); `docs/canonical/TRUSTED_CONTROL_REPAIRS.md` (ledger and the Repair 001 precedent) | **Fail-open only** (line 111). Item 5 (line 119) requires "every exact-head gate required by canonical repository authority and applicable to the repair candidate" to succeed, except preserved boundary results caused only by the declared trusted-control byte change. Items 7-9 (lines 121-123) require independent review, a guarded normal merge, a post-merge exercise and a separate reconciliation. The last paragraph (line 125) forbids using XVI as a substitute for an ordinary gate. Repair 001 preserved exactly the two boundary failures (`TRUSTED_CONTROL_REPAIRS.md:38-48`) and treated the skipped materialization job as not applicable. |
| Fail-closed over-application | **None.** | Gap confirmed: no lane exists. `research/000b2-public/recovery-attempt-003-readiness.json` adds no applicability rules for non-B2 PRs. |

Additional authority notes:

- Governance PRs #107 (0.1.0→0.2.0, adds XVI) and #110 (0.2.0→0.2.1, item 5 clarified to allow the scope-boundary companion failure) are `SOURCE_VERIFIED` via their PR bodies.
- The #107 body cites "Governance §6", but the current Governance section has only items 1-5 (`CONSTITUTION.md:129-133`). This is a stale reference.
- **The #118 red-check merge is not recorded anywhere canonical** (`REPRODUCED` grep over the main tree for `34416457849`, `verify-b2r16-freeze`, `B2R16 Freeze` and `#118`). Facts:
  - merged 2026-09-10T00:25:52Z by TheHalfMoon;
  - merge `edacdf7`, head `b7824b3`;
  - 4 files, all within the reconciliation scope;
  - verify-b2r16-freeze failed (34416457849);
  - every other triggered check, including both trusted gates, succeeded;
  - reviews: two CodeRabbit `COMMENTED`, decision empty;
  - post-merge push checks on `edacdf7` were all green; the freeze workflow has no push trigger.
- The owner's PR #124 proposal (`docs/strategy/WISPRAL_GOVERNANCE_AMENDMENT_PROPOSAL.md:74`, pr124@e7064c7) and Opus M1 (pr125, `INDEPENDENT_REVIEW.md:42-67`) both say this must be reconciled factually and not treated as an exemption.
- Branch settings (`DOCUMENTED` in pr126 `settings-access.json`, 2026-10-21): `protected=false`, classic protection 404, rulesets `[]`. Not re-queried. Per instructions, missing protection is not treated as permission.

## 6. Task 5: founding children 000C-000G

The 000 parent is `REFINING` (`specs/000-founding-research/spec.md:3`).

Closure condition (`spec.md:89-99`): every required child must be VERIFIED, SUPERSEDED or CANCELLED with rationale. `000G` "records a decision matrix and selects exactly one bounded first product Grain, or records that evidence is insufficient" (`spec.md:98`).

| Child | Definition (`plan.md`) | Status (`tasks.md`) | Frontier (`specs/CURRENT.md:241-251`) |
|---|---|---|---|
| 000C | Turn-taking and interruption measurement using 000A event boundaries and 000B timing (`plan.md:30-34`) | `[ ]` "intentionally coarse" (`tasks.md:9`) | Anticipated "after the evidence-selected B chain stabilizes"; "Do not refine distant children merely to create activity" |
| 000D | PTY compatibility boundary, after ACP gaps are known (`plan.md:36-38`) | coarse (`tasks.md:10`) | same |
| 000E | Platform audio and privacy feasibility: microphone permissions, devices, capture, runtime constraints (`plan.md:40-42`) | coarse (`tasks.md:11`) | same |
| 000F | Dependency, license and provenance decision inputs (`plan.md:44-46`) | coarse (`tasks.md:12`) | same |
| 000G | Founding synthesis; decision matrix; one first product Grain or explicitly none (`plan.md:48-52`; criteria at 54-67; closeout at 92-100) | coarse (`tasks.md:13`) | "founding synthesis and first product-Grain selection" |

**What "000G selects first bounded Grain" requires** (`CURRENT_STATE.md:432-436`, `specs/CURRENT.md:266-270`, `tasks.md:70-72`):

1. 000G is reached.
2. 000G selects a bounded first implementation Grain from reproducible evidence.
3. That Grain independently satisfies readiness (`AGENTS.md:37-43`, where the lifecycle runs GRAIN→READY).
4. The closeout updates `CURRENT_STATE.md` and `specs/CURRENT.md` (`plan.md:94-100`).

Further constraints:

- `plan.md:71-73`: only 000A was task-refined; 000B-G "must be shaped from canonical evidence after preceding children merge".
- 000B remains open: B2 ATTEMPT-003 is at B2R17; B3 and B4 are coarse (`specs/CURRENT.md:233-239`).
- The product thesis is coding-agent control (`spec.md` out-of-scope line 79 excludes "TTS/full duplex/AEC product work"; `AGENTS.md:3`; `CURRENT_STATE.md:397-403`).
- WisprStudio (TTS) is therefore explicitly out of scope until amended.

## 7. Task 6: option evaluation

The common constraint, established above: **every** route must change at least one control that is currently untouchable.

- The always-on freeze workflow and its four files sit outside every remaining B2 task scope and outside the reconciliation scope, so changing them fails both B2 gates.
- For F, the immutable B2 trusted controls (`readiness.json:74-79`) must also change. Otherwise `specs/CURRENT.md` and `CURRENT_STATE.md` can never be edited outside a B2 reconciliation, even after B2 completes.
- No current clause authorizes a fail-closed correction. **The first PR in any sequence will carry at least one red check that no existing authority covers.** The only legitimate way to resolve that is an explicit constitutional act by the owner, recorded openly, not a silent merge like #118.

| Option | Sequence | PRs | Red on each PR | Preserved evidence or unaddressed blocker? | Review | Rollback | Verdict |
|---|---|---|---|---|---|---|---|
| **A**: amendment first, then repair | A1 platform amendment (full class (b)) → A2 #126-style repair → reconciliation | 3+ | A1: freeze plus both B2 scope gates plus the common verifier. A2: both B2 scope gates. | **Unaddressed on both.** No clause covers A1's B2-gate failures or A2's. XVI cannot be used (not fail-open). | Owner ratification plus independent review | A1 revert is a major amendment revert | **REJECTED** as stated. Feasible only if A1 adds the lane, which turns it into Option C. |
| **B**: lane first (recommended) | **G1** CONSTITUTION-only minor 0.3.0 (new fail-closed over-application correction principle plus transitional clause) → **C** control correction → **R** ledger reconciliation (records C and #118) → **G2** platform major 1.0.0 (sim-bmin paths only) → **F** frontier reconciliation | 5 | G1: freeze only. C: both B2 gates. R, G2 and F: none expected. | G1: preserved under its own transitional clause, which takes effect only through explicit owner ratification after independent review. The red is identical on canonical main itself. C: preserved under G1's lane (mirrors XVI.4-5 as amended by #110). R, G2, F: green. | Independent review of G1 and of the exact C range; ordinary review of R, G2 and F; the founder ratifies G1 and G2 | Each step is separately reversible by a governed revert PR. Reverting C restores the original controls; the evidence stays. | **RECOMMENDED** |
| **C**: one combined amendment that also adds the lane | (G1+G2) → C → R → F | 4 | (G1+G2): freeze only (sim-bmin class). C: as in B. | Same as B | One large review mixing the platform pivot with integrity rules | Reverting the pivot also removes the correction lane | Legitimate but **second choice**. It couples the contested platform decision to CI integrity, and #120/B2 unblocking waits on the platform debate. |
| **D**: path-scope the benchmark workflows to the B2 lane | Change the freeze `on:` to B2 paths (all 16 frozen inputs plus the B2 lane) | Needs the same lane as B | Changing the trigger touches `.github/workflows/000b2-public-*.yml`, so both B2 gates fail (as #126 shows) | Same need for G1 | Same | Same | **REJECTED as primary.** It is itself a control change, does not unlock `specs/CURRENT.md`, produces "absent" checks (deadlocks if the owner later requires the check), and gives no tamper detection on PRs outside the filter. Acceptable only as a fallback inside lane C. |
| E: relocate the platform frontier to a new spec file to avoid the lock | AGENTS §9 split | 1-2 | freeze | Path-dodging; leaves `specs/CURRENT.md:24` ("This file owns the executable specification frontier") and the product-code gates stale and contradictory | n/a | n/a | **REJECTED** |
| F': wait for B2 completion | n/a | n/a | n/a | The trusted gate stays locked when `active_recovery_unit` is `None` (`trusted-pr.yml:153-158`) | n/a | n/a | **REJECTED** |

### Recommended sequence in detail (Option B)

**G1: Constitution 0.2.1 → 0.3.0 (minor: new authority).** Path: `CONSTITUTION.md` only. Adds "Principle XVII — Fail-closed over-application correction".

- **Defect class:** a trusted or frozen control that (a) rejects canonical main itself or candidates outside the class it was authorized for, or (b) permanently blocks a change class that canonical authority never assigned to it.
- **Requirements,** mirroring XVI items 1-9:
  - exact paths only;
  - 100% preservation of the control's authorized detection on its authorized class, proved by tamper-negative tests;
  - no broadening of B2 task or reconciliation scope, or of execution, decode, scoring, claim, product or completion authority;
  - newly accepted classes carry zero execution authority;
  - pre-correction red results preserved and never rerun to green;
  - fresh independent review;
  - guarded normal merge;
  - post-merge canonical exercise;
  - separate ledger reconciliation.
- **Transitional clause:** the specific pre-existing `verify-b2r16-freeze` failure may be preserved on G1 itself and on candidates up to and including C's merge. The conditions are:
  - the failure is individually evidenced;
  - its text is `B2R16 actual candidate range scope drift`;
  - it is reproduced on canonical `edacdf7`;
  - no other failure is present.
- **Founder decision written into the text:** whether non-B2 governance PRs may edit `specs/CURRENT.md` and `CURRENT_STATE.md` outside the B2-owned sections while ATTEMPT-003 is active, and after it completes.

**C: one correction PR** (two declared defects, both "B2 controls lack a non-successor classification").

- **Paths:**
  - `.github/workflows/000b2-public-b2r16-freeze.yml`
  - `research/000b2-public/verify_b2r16_preservation.py` and `test_b2r16_preservation.py` (from #126, with the fixes below)
  - `.github/workflows/000b2-public-attempt-003-recovery.yml`, `.github/workflows/000b2-public-attempt-003-trusted-pr.yml` and `research/000b2-public/verify_attempt_002_invalidation.py` (immutable controls)
  - evidence under `research/control-repairs/…`
- **New non-successor class,** recognized only when **all** of the following hold:
  - the candidate's readiness JSON blob equals the authority-base blob;
  - no changed path is under `.github/**`, `research/000b1/**`, `research/000b2-entry/**`, `research/000b2-public/**`, `specs/000B*/**` or `fixtures/**`;
  - the common verifier's existing successor-marker checks (`verify_attempt_002_invalidation.py:694-711`) pass;
  - the B2-owned sections of `specs/CURRENT.md` and `CURRENT_STATE.md` (headings "Canonical ATTEMPT-003 …", the B2R16 reconciliation block, and the product-code-gate text until F changes it under its own authority) are byte-identical to the base.
- **Behavior:** B2 task and reconciliation classification stays byte-for-byte unchanged in effect. The transition-proof step still runs.
- **Optional strengthening:** run the B2R16 preservation check from a base-defined `pull_request_target` job. Note that tampering with the freeze workflow is already caught, because any change to `.github/workflows/000b2-public-*.yml` triggers both B2 gates.
- C could be split into C1 (freeze) and C2 (B2 gates) for reviewability. That adds one PR.

**R: ledger.** Paths: `docs/canonical/TRUSTED_CONTROL_REPAIRS.md` (or a new `CONTROL_CORRECTIONS.md` that G1 designates) and `AGENTS.md` reading order. Neither path triggers B2 workflows (precedent #116).

- Records C's identities, preserved reds, positive and negative proof, review, merge ancestry and canonical exercise.
- **Records the #118 facts in §5.**
- States explicitly whether the B2R17 frontier stands. Recommendation: it stands, because every B2-applicable gate passed. The decision belongs to the founder.

**G2: platform major amendment 1.0.0.** Paths: `CONSTITUTION.md`, `AGENTS.md`, `ARCHITECTURE_INVARIANTS.md`, `PROGRAM_ROADMAP.md`, and 000 `spec.md` and `plan.md` (sim-bmin class; only the corrected freeze check triggers).

- Carries the #124 proposal content: mission replacement, anti-roadmap rows, A12, and the 000C-G re-scope (000C/000D gate only the developer-agent capability; 000E is the platform-feasibility stream; 000F ingests the REA bundle as evidence; 000G does capability-specific Grain selection).
- **Clarifies that readiness `claim_guards.product_code_authorized=false` scopes B2-lane authority only.**

**F: frontier reconciliation.** Paths: `specs/CURRENT.md`, `docs/canonical/CURRENT_STATE.md`, `specs/000-founding-research/tasks.md`.

- Opens only named research Grains (for example 000E and 000F intake).
- Product code stays closed until a 000G decision PR.
- All triggered gates should pass: the B2 gates through the non-successor class; content verifiers unaffected (`REPRODUCED` for 18 static verifiers on append-only edits).

### B2R17 and B2 coexistence

- ATTEMPT-003 stays frozen and intact. G1, C, R, G2 and F must not change readiness, task scopes, task order, frozen inputs, `recovery-v2*.md` or any B2 evidence. C's tamper-negative tests prove that B2 task and reconciliation behavior is unchanged: #120 still passes, and extra-path, missing-path and deletion candidates still fail.
- B2 resumes after C: merge main into #120, run fresh exact-head CI and a fresh independent non-rate-limited review, then guarded normal merge, post-merge recovery run, and B2R17→B2R18 reconciliation. These steps are independent of G2 and F.
- Product lanes must not depend on an STT winner. Only speech-bearing packets (for example I-01 and speech release cells) depend on canonical B2/B4 disposition. G2/F's dependency graph (#124 `research/rea/2026-10-21/packet-authorities.json`) must state this explicitly. No packet becomes READY without F or 000G authority.

### Defects to fix in #126 before it becomes part of C

1. `test_b2r16_preservation.py:77` pins `f36338138f4b…`. That commit is reachable only from unmerged branches `origin/research/rea-copy-first-master-replan-20261021` and `origin/review/opus-independent-audit-pr124` (`REPRODUCED` via `git branch -r --contains`). If those branches are deleted, the check goes red on every PR again. Replace it with commits reachable from main, or with synthetic commits.
2. The freeze workflow has no `push` trigger. The post-merge canonical exercise therefore needs a `workflow_dispatch` on main or a recorded local deterministic run.
3. #126 calls itself an "ordinary" correction (`REPAIR.md`). Without G1 its two red trusted gates have no authority.
4. The checker reads candidate bytes. That is acceptable only because the B2 gates reject changes to `000b2-public-*.yml`. State this in the C record.

## 8. Task 7: blocking-gate register (recommended sequence)

| ID | Gate | Authority (file:line) | Exact failure text | Why it fails | Applies to the candidate? | Proposed authorized correction | Review | Reproduction | Positive and tamper-negative tests | Rollback | Position |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GATE-1 | verify-b2r16-freeze | `000b2-public-b2r16-freeze.yml:3-5,26-37`; `verify_b2r16.py:35,46-51,123-130,138-140`; readiness `task_content_policies.B2R16.required_verifier` | `B2R16_ATTEMPT_003_FREEZE=FAIL: B2R16 actual candidate range scope drift` | Fixed-base exact-range and prefix checks valid only for the B2R16 task candidate | **No.** It is the B2R16 task's required verifier, and it is structurally incompatible with its own reconciliation (#118) and with main. | G1 transitional preservation, then C replaces the invocation with the preservation checker plus the historical PASS at `ac9f7ce` | Independent review (Jev/Opus or non-rate-limited CodeRabbit) of the exact G1 and C ranges; d1-local not acceptable | `python -I research/000b2-public/verify_b2r16.py --require-git` on `edacdf7`; #126 `verify_b2r16_preservation.py --candidate <sha>` | Positive: main, pr124 and C head pass; the `ac9f7ce` output is byte-identical. Negative: 16 byte mutations, 48 delete/mode/symlink cases, forged checker/test, hashlib shadowing, invalid refs (#126 suite, 7/7 `REPRODUCED`) | Governed revert PR restoring the original workflow; reds stay preserved | G1 (preserved red), fixed by C |
| GATE-2 | verify-successor-recovery, trusted pre-candidate boundary | `000b2-public-attempt-003-recovery.yml:4-21,133-162`; readiness json:35 (B2R17 scope); `recovery-v2.md:97` | `TRUSTED_BOUNDARY=FAIL: B2R17 task-candidate path scope violation` | Every changed set is forced into the B2R17 task scope or the reconciliation scope; there is no third class | On C: yes, and it must fail closed (C touches B2 control paths), so it is preserved. On F before C: **no** (not a B2 candidate), which is the over-application. | C adds the non-successor class (§7) | Same as GATE-1, plus owner ratification of the class in G1 | `run_inline_gate.py` with main's step "Trusted pre-candidate execution boundary" | Positive: #120 passes (unchanged); an F-like candidate (sim-b) passes after C. Negative: sim-b plus any of a `research/000b2-public` path, a readiness change, a `.github/**` change, or a B2-section edit or deletion fails; extra, missing and deletion task candidates fail; exact reconciliation passes, extra fails | Revert C | Preserved on C; must pass on F |
| GATE-3 | verify-successor-pr-from-canonical-base (PRT, base definition) | `000b2-public-attempt-003-trusted-pr.yml:83-94,110-119,152-160`; readiness json:74-79; `recovery-v2.md:112-116,185` | On C: `TRUSTED_PR_GATE=FAIL: immutable execution control changed: .github/workflows/000b2-public-attempt-003-recovery.yml` (predicted; `NOT_RUN`). On F before C, and on #126: `TRUSTED_PR_GATE=FAIL: B2R17 candidate path scope violation` | Immutable control bytes and scope; on a terminal B2 state it raises `None candidate path scope violation` | C: preserved (sole cause is the declared control bytes). F: should pass after C | Same as GATE-2 | Same | `run_inline_gate.py` with step "Verify trusted-base event and immutable control boundary" | Same as GATE-2; plus a terminal-state fixture (`active_recovery_unit: null`) where a non-successor candidate passes and a B2-path candidate fails | Revert C | Preserved on C; must pass on F |
| GATE-4 | Common verifier `verify_attempt_002_invalidation.py --static-only` (inside GATE-2 and GATE-3) | `verify_attempt_002_invalidation.py:370-423` (scope), `694-711` (markers) | `ATTEMPT_002_INVALIDATION=FAIL: B2R17 candidate must match the exact canonical task path set` | Same missing class | F: no | Part of C (immutable path; exact bytes pinned by `trusted-pr.yml:162-164`) | Same | `AUTHORITY_BASE_REVISION=edacdf7 python -I …/verify_attempt_002_invalidation.py --static-only` on sim-b (`REPRODUCED`) | Keep the existing 9 exact/missing/extra/deletion regressions from Repair 001; add non-successor positive and negative cases | Revert C | C |
| GATE-5 | Independent substantive review | `CONSTITUTION.md:121` (XVI.7, mirrored by G1); `recovery-v2.md:176-187`; `CURRENT_STATE.md:192,211` (rate-limited or self-review is not review) | n/a | No independent review exists on #126 (its own `PATCH_REVIEW.md` disclaims approval) or on #120 | Yes for G1, C and #120 | Obtain a fresh exact-range review | **Founder must source the reviewer** | n/a | n/a | n/a | Before each merge |
| GATE-6 | Guarded merge and post-merge exercise | `CONSTITUTION.md:122-123`; `AGENTS.md:126` | n/a | The freeze workflow has no push trigger | Yes for C | `workflow_dispatch` of the corrected freeze workflow on the merge SHA, plus a local deterministic run; push runs of the recovery and trusted workflows on main | n/a | `gh run` evidence | Canonical-state re-run of all tamper fixtures | n/a | After C, before R |
| GATE-7 | Product-code gate | `CURRENT_STATE.md:432-436`; `specs/CURRENT.md:266-270`; `tasks.md:70-72`; `spec.md:67-85` | n/a (governance) | 000G not reached | Yes for any product code | G2 re-scope, F opens research Grains, then a 000G decision PR selects a Grain | Owner plus independent review | n/a | n/a | n/a | After F |
| GATE-8 | #118 unrecorded red merge | `CONSTITUTION.md:130` (no hidden exceptions); `recovery-v2.md:185` | Run 34416457849 `…range scope drift` | Merged without a record | Governance debt | R records the facts; the founder determines whether the B2R17 frontier stands | Owner | `gh run view 34416457849 --log-failed` | n/a | n/a | R |

Not blocking, but must be re-observed:

- On C: `verify-legacy-recovery-boundary` and `verify-public-corpus-methodology`. Both were observed PASS on #126; for C they are `NOT_RUN`.
- On F: `materialize-official-archives` and `freeze-public-corpus-subset`, which re-fetch over the network (`NOT_RUN`).
- After every merge: the push-time `--reverify-open-prs` jobs in workflows #24, #26 and #27. Stale open PRs can turn these red; precedent at `specs/CURRENT.md:139`.

## 9. Task 8: founder versus engineering agent

**Founder (repository owner) only:**

1. Decide the platform pivot. Ratify G1 (0.3.0) and later G2 (1.0.0). These are constitutional authority acts under `CONSTITUTION.md:129-131`.
2. Decide the class question written into G1: may non-B2 governance PRs edit `specs/CURRENT.md` and `CURRENT_STATE.md` outside B2 sections?
3. Explicitly accept the G1 transitional preserved red. Without this there is no legitimate first step.
4. Source a fresh independent reviewer for G1, C and #120 (`BLOCKED_EXTERNAL`). Agents and d1-local cannot approve.
5. Perform, or explicitly authorize, each guarded merge. Record live branch-protection and ruleset settings from the UI or API at merge time, and mark them UNKNOWN if unreadable.
6. Decide the #118 disposition (does the B2R17 frontier stand?).
7. Decide whether to enable branch protection after the repair. Do not make path-filtered checks required.
8. Decide the dispositions of #121, #123, #124, #125 and #126 (supersede #126 with C, or update it).

**Engineering agent** (once explicitly authorized; this run was read-only):

1. Draft the G1 text and prepare C: port #126 with fixes 1-4, implement the non-successor class in the three immutable controls, and extend the regression fixtures.
2. Run all local positive and negative tests, and the trusted-gate harness, on the exact C head.
3. Open draft PRs with full XVI-style descriptions: defect, base, exact paths, expected conflicts, compatibility, security/privacy, affected specs.
4. Capture run IDs and logs and preserve the red results.
5. After merge: dispatch and exercise on the merge SHA (with permission), then draft R.
6. Prepare the #120 base update and requalification evidence.
7. Draft G2 and F from the #124 proposal, with a contradiction table and dependency graph.
8. Keep `NOT_RUN` honest.

## 10. Residual risks and unknowns

- The exact C failure text on the base-defined trusted gate is predicted, not observed (`NOT_RUN`).
- The legacy-recovery and subset verifiers fail locally on the main baseline for environmental reasons (`-I` imports, ref layout); CI on main is green. They were not diagnosed.
- Branch settings were not re-queried in this run.
- Markdown section-preservation checks in C are inherently textual. They need adversarial review: reordered sections, Unicode look-alikes, and duplicated headings.
- Network-dependent workflows triggered by F were not run.
