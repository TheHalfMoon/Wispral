# Author response to the review of `de095ea`: new head `cabf4e5d96ab03d38a74ee4e5986be17a26f5e74`

The range is now `8d52a4579a0b1c6555cbe8443027c1950493b326..cabf4e5d96ab03d38a74ee4e5986be17a26f5e74`. The delta since your review is `c1_delta_de095ea_cabf4e5.diff` (one commit). The head is pushed to `governance/c1-b2r16-freeze-correction`, so you can fetch it.

## Finding 1 (BLOCKING): exact restore of the original workflow. Fixed.

- `verify_candidate` now calls `restores_original`. When the candidate's workflow equals the original `885307` blob, the original is accepted only if every `git merge-base --all <trusted HEAD> <candidate>` still has the original workflow. That is a branch that forked before the replacement. Restoring the original after the replacement is in the candidate's history is rejected: `Frozen workflow downgraded to the original identity`.
- **New test** `test_exact_original_workflow_restore_rejected`. It uses your exact construction (a descendant of the trusted head with the `885307` workflow blob) and is now rejected.
- **New test** `test_branch_predating_replacement_keeps_original_workflow`. A branch forked at `edacdf7` that does not touch the workflow still passes. A merge of such a branch keeps the base's replacement.
- **Why not your suggested rule.** Accepting the original only for ancestors of the trusted base would also reject such stale branches. The merge-base rule rejects exactly the downgrade.

## Finding 2 (BLOCKING): identical verdicts on the in-class corpus. Fixed.

- **Authorized class.** The original gate was assigned to B2R16 task candidates. That class ends at the freeze merge `885307`.
- **Delegation.** A candidate that does not contain `885307` is now judged by the frozen original verifier bytes (blob `c11714b`, the same bytes as on `main`), in a scratch clone of that candidate.
  - This is the canonical original program, so verdicts are identical by construction.
  - The candidate's own verifier never runs (the `pull_request_target` boundary). Its file is replaced by the frozen bytes and must be a regular `100644` blob in real directories.
  - `python -I` keeps the script directory off `sys.path`.
- **Corpus test** (`test_in_class_corpus_verdicts`). It covers all ten B2R16 candidates the original gate ever evaluated (`000B2 Public Corpus B2R16 Freeze` runs of 2026-09-08 and 2026-09-09), all reachable from `main`.
  - Running each candidate's own verifier reproduces all ten recorded verdicts: six passed, four failed.
  - Under the corrected control, all four previously rejected candidates (`adbc6f9`, `9c5d475`, `049e2e9`, `0b8c70a`) stay rejected, and the qualified head `ac9f7ce` passes.
  - Five superseded heads passed only under their own, superseded verifier bytes, bound to the superseded authority base `483484023087`. The canonical frozen verifier rejects them. That is stricter, never weaker.
- **Malformed in-class candidates** (`test_in_class_malformed_candidates_rejected`):
  - an extra path on `ac9f7ce` is rejected;
  - a manifest byte change is rejected;
  - a verifier symlink is rejected before execution.
- **Paths outside the freeze.** You listed `recovery-attempt-003-readiness.json`, `specs/CURRENT.md` and `docs/canonical/CURRENT_STATE.md`. These are not B2R16 frozen objects. After B2R16 they belong to the B2R17+ recovery lane and change legitimately (for example #118). The base-defined recovery and trusted-pr gates guard them with their completed-prefix and transition-proof checks. Freezing them is exactly the over-application this correction removes.

## Finding 3 (BLOCKING): negative fixtures for every rejecting branch. Fixed.

There are 20 tests now, all passing (author run: `Ran 20 tests in 120.834s`, `OK`). The new fixtures by branch:

| Rejecting branch | Fixture |
| --- | --- |
| `approved_workflow`: zero literals, two literals, wrong literal | each through `approved_workflow` and through `verify_candidate` |
| ancestry split | `test_candidate_predating_freeze_is_not_a_preservation_candidate` (`ac9f7ce`) |
| `identity`: gitlink and tree in place of a frozen blob | workflow and manifest |
| `identity`: missing, two records, malformed metadata, non-UTF-8 name | crafted `ls-tree` records |
| `historical_proof` failure | pinned head swapped to `edacdf7` |
| unexpected scratch root | |
| oversized workflow blob | new 64 KiB cap |

Tree-record parse errors now raise `PreservationError` instead of a traceback.

## Finding 4 (BLOCKING): item 5 evidence for the freeze gate. Evidence attached (`freeze_gate/`).

The harness `run_gate_steps.py` (SHA-256 `4198c25b…`; driver `freeze_gate_evidence.sh`, SHA-256 `136939c0…`) ran the pre-correction freeze gate as defined at `8d52a45` on the C1 head `cabf4e5` and on the base `8d52a45`.

| Run | C1 `cabf4e5` | base `8d52a45` |
| --- | --- | --- |
| plain | `FAIL: B2R16 actual candidate range scope drift` | the same |
| range classification neutralized | `FAIL: canonical recovery prefix drift` (B2R16 task-time authority classification) | the same |
| range and task-time authority neutralized | `B2R16_ATTEMPT_003_FREEZE=PASS` | the same |

- **Cause.** The failure is identical on the base, so C1 does not cause it. It is the reproduction of the defect itself (Principle XVII "Defect" (b)), and is preserved on exactly this pull request under the transitional clause. Item 5(a)'s counterfactual cannot apply: the candidate with the declared control bytes reverted is the base, and the failure occurs there too. That is why the transitional clause exists.
- **Non-concealment.** Every masked check of the gate was then run:
  - `verify_source_identities`;
  - `verify_preexecution_state`;
  - `verify_manifest`;
  - `verify_no_primary_output_surface`.

  They pass on C1 once only the two B2R16 task-time classifications are neutralized. The neutralizations are printed in the outputs, and the working-tree diff stat is recorded.

## Non-blocking findings

- **5.** The workflow comment now says that a dispatch trusts the ref a maintainer chose.
- **8.** The 64 KiB cap is added before reading the workflow blob.
- **9.** The `push` run on `main` re-verifies the merge commit (XVII item 9).
- **10.** Fixed, as described under finding 3.
- **11.** Each skipped job is gated by its own `if:` condition:
  - `bootstrap-self-test` runs only on `pull_request` events. That workflow receives them only for changes to `.github/trusted/verify_000b2_materialization.py` or to its own file, and this pull request changes neither;
  - `verify-pr-head-artifact-identity` runs only for pull request number 10;
  - `resolve-active-b2-head` and `reverify-active-b2-after-base-push` run only on `push`.

  None applies to this pull request.
- **12.** No specification changes. The B2R16 task specification (`specs/000B2-public-corpus-bakeoff/recovery-v2.md`, `recovery-v2-tasks.md`) is untouched.
- **13.** Harness and driver SHA-256 values are now recorded:
  - `run_gate_steps.py` `4198c25becfd81d98086bb4ac85566bad81276c7c7ac5e2216be47c42e661a6f`;
  - `c1_gate_evidence.sh` `a5825c17106b77aa31bc95f5ac18fa42e67604a229573644d4629523eca52413`;
  - `freeze_gate_evidence.sh` `136939c0fa1be2ffcd75aa8afaf16996beb07863d82620e041d63b18d554ea40`.
