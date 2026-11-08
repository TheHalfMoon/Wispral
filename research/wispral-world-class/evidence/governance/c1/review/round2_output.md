I'll independently verify the new head before writing the re-review. Fetching it and checking the delta and digests first.


The new checker adds ancestry gating, a frozen-verifier delegation path, and a downgrade check. I'll set up a worktree at the new head and verify the digests, the checker run, and the exact-restore experiment.


Digests and the main path check out. Now the downgrade experiment and the new branch rules, then the full suite.


Finding 1's exact construction is now rejected. Running the full new suite to confirm the author's claim of 20 passing tests.




Suite passes (20/20). Two remaining checks: whether the in-class corpus really covers every historical evaluation, and whether the item-5(b) non-concealment list covers every check after the first failure.


The corpus test passed, but I need to confirm those ten historical commits are actually reachable from `main` (otherwise the post-merge `push` run's tests would fail), and check the PR body against Principle XVII item 1.


All ten corpus commits are ancestors of `main`, so the post-merge `push` run can resolve them. Checking the current head's checks and the `cabf4e5` dispatch run.


## Findings

**Earlier blocking findings**

1. **NON-BLOCKING (was BLOCKING — RESOLVED): exact restore of the original workflow.**
   `research/000b2-public/verify_b2r16_preservation.py:112-113, 128-135`; `research/000b2-public/test_b2r16_preservation.py:118-126`.
   I reproduced my original construction on the new head: a descendant of `cabf4e5` whose workflow is the `885307` blob `c22eeb0` is now rejected with `Frozen workflow downgraded to the original identity` (synthetic candidate `a35a1166eebdc476016b183bc74f2f5531e3e7f2`). The accepted-original path is now only a branch whose merge base still has the original: I confirmed `candidate_with("README.md", base=edacdf7)` and even an explicit original-workflow tree at `edacdf7` are accepted, which is correct because that tree equals the fork point's tree, so a three-way, squash or rebase merge cannot change `main`'s replacement workflow. A real downgrade (restoring the original on a descendant of the replacement) is rejected. The `test_candidate_defined_trigger_rejected` modified-trigger case still passes. **Resolved.**

2. **NON-BLOCKING (was BLOCKING — RESOLVED): in-class corpus / frozen-verifier delegation.**
   `research/000b2-public/verify_b2r16_preservation.py:89-103, 152-174, 197-212`; `research/000b2-public/test_b2r16_preservation.py:14-33, 183-233`.
   Candidates that do not contain the freeze merge are now judged by the frozen `885307` verifier bytes, so the class verdicts are identical to the pre-correction control by construction, and the candidate's own verifier is replaced before execution. I verified all ten corpus commits (`7db0ffb…`, `adbc6f9…`, `9c5d475…`, `049e2e9…`, `d9528e3…`, `e152503…`, `17b5264…`, `ee3b419…`, `0b8c70a…`, `ac9f7ce…`) are ancestors of `8d52a45`, so the post-merge `push` run can resolve them. The four previously rejected candidates stay rejected and `ac9f7ce` passes. The five superseded heads that historically passed under *older* verifier bytes are rejected by the frozen verifier — stricter, not weaker, and not the pre-correction control's verdict. My original hole (changing `recovery-attempt-003-readiness.json`, `specs/CURRENT.md` or `docs/canonical/CURRENT_STATE.md` and still being accepted) is closed for the class by the delegation, because the frozen verifier's `verify_exact_task_range`/`verify_authority` read those files. **Resolved.**

3. **NON-BLOCKING (was BLOCKING — RESOLVED): negative fixtures for the rejecting branches.**
   `research/000b2-public/test_b2r16_preservation.py:118-233`.
   The suite is now 20 tests; I reproduced `Ran 20 tests in 130.336s ... OK`, and the `cabf4e5` dispatch run 42443952258 also reports `Ran 20 tests ... OK`. The new fixtures cover zero/two/wrong digest literals, ancestry split, gitlink/tree, missing/ambiguous/malformed/non-UTF-8 tree records, oversized blob, historical-proof failure, unexpected scratch root, and the exact-original restore. The only raises without a dedicated fixture are defensive/environmental paths (`No merge base with the trusted revision`, `:133-134`; `Workflow blob size unreadable`, `:119-122`; `Original verifier setup failed`, `:175-181`), which fail closed rather than decide candidate class. **Resolved.**

4. **NON-BLOCKING (was BLOCKING — RESOLVED): item 5 evidence for the freeze gate.**
   `freeze_c1.txt`, `freeze_base.txt`, `freeze_c1-neutralized-1.txt`, `freeze_c1-neutralized-2.txt`; `research/000b2-public/verify_b2r16.py:271-286`.
   The attached harness outputs show the pre-correction gate failing identically on `cabf4e5` and `8d52a45` (`B2R16 actual candidate range scope drift`), then failing on `canonical recovery prefix drift` with only the range classification neutralized, then `B2R16_ATTEMPT_003_FREEZE=PASS` with both classifications neutralized. The verifier's `main()` order is `verify_exact_task_range` → `verify_authority` → `verify_source_identities` → `verify_preexecution_state` → `verify_manifest` → `verify_no_primary_output_surface`, so the neutralized PASS covers every later check: non-concealment is shown. The literal item 5(a) counterfactual is not met (the failure also occurs on the reverted base), but the transitional clause is the authority for preserving this specific failure on this PR, and the evidence is consistent with that reading. The harness/driver source is in #128 and I did not re-run it; the raw outputs are attached and the claimed hashes are recorded. **Resolved.**

**New findings in the delta**

5. **NON-BLOCKING — the PR description is stale for the reviewed head.**
   PR #130 description, “Exact canonical base, head and paths” and “Pinned digests on this head” (not a file in the diff).
   The body still says `exact head: de095ea`, `Ran 9 tests`, and lists `c60955b8…` / `17709526…` / `9d524363…` / `5815b4ec…`, while the reviewed head is `cabf4e5` with workflow `69c7d001974e6e6c2e4903b64d709f61b69376e646168d931475ee577a4f785c`, checker `fb7b75c8…`, tests `823bc17…`, and normalized template `0befa88c…`. Concrete risk: the owner or a later reviewer checking the body's table against the final head would verify the wrong bytes. The author response carries the new checker/test digests but not the workflow/template. Documentation only; I verified the actual head bytes independently. Fix before the merge record.

6. **NON-BLOCKING — `restores_original` trusts `HEAD`, which makes the `push` run self-trusting.**
   `research/000b2-public/verify_b2r16_preservation.py:128-135`; `.github/workflows/000b2-public-b2r16-freeze.yml:23-27, 69-74`.
   In the defined CI contexts `HEAD` is the base tip (`pull_request_target`) or the pushed/dispatched commit, so the check is correct, and I verified the exact-original restore on a descendant of `cabf4e5` is rejected. Residual: if `main` were ever changed to the original workflow by a direct owner push (or a merge that somehow lands it), the `push` run would accept it (`actual == expected`; the only merge base is `HEAD`, which has the original). The control cannot detect a downgrade of `main` from `main` itself. This is not reachable through a normal PR merge (the stale-branch acceptance is merge-neutral), and it is not a regression from the pre-fix checker, which accepted the original unconditionally. Also, `test_exact_original_workflow_restore_rejected` would fail if the suite were run on a checkout whose `HEAD` still has the original workflow; that does not happen on the dispatch or post-merge runs. Note only.

7. **NON-BLOCKING — the `workflow_dispatch` path runs the dispatched ref's own code.**
   `.github/workflows/000b2-public-b2r16-freeze.yml:3-7, 13, 23-27, 31-35, 52-59`.
   On dispatch, `github.sha` is the dispatched ref, so the checkout, checker, test and digest literals all come from that ref. The new comment now says “a dispatch trusts the ref that a maintainer chose”, which scopes the earlier “never executes candidate code” claim correctly. This path is manually triggered and is required by transitional condition 3(c); the `pull_request_target` path remains base-defined and data-only. No blocking security defect.

8. **NON-BLOCKING — skipped jobs under transitional condition 2.**
   `gh pr checks 130` on `cabf4e5`.
   The two scope gates fail (preserved), `verify-public-corpus-methodology` and `verify-legacy-recovery-boundary` pass, and `bootstrap-self-test`, `resolve-active-b2-head`, `reverify-active-b2-after-base-push`, `verify-pr-head-artifact-identity` are skipped. The author response explains each `if:` condition (path filter, PR number 10, push-only). I did not independently inspect those `if:` conditions; if any skipped job is actually applicable, transitional condition 2 (`principle_xvii.md:32`) is not satisfied. Note only.

9. **NON-BLOCKING — positive verifications that support approval.**
   `research/000b2-public/verify_b2r16_preservation.py`, `.github/workflows/000b2-public-b2r16-freeze.yml`, `research/000b2-public/test_b2r16_preservation.py`.
   I independently confirmed: `python -I research/000b2-public/verify_b2r16_preservation.py --candidate cabf4e5…` → the exact historical stdout plus `B2R16_FROZEN_OBJECT_PRESERVATION=PASS`, exit 0; the normalized workflow hash `0befa88c…` equals the checker's template constant; the workflow's `CHECKER_SHA256`/`TEST_SHA256` literals equal the actual checker/test bytes; 15 of 16 frozen paths are `SAME` as `885307` with the workflow the only declared migration; all ten corpus commits are ancestors of `8d52a45`; the `cabf4e5` dispatch run 42443952258 succeeded with `B2R16_FROZEN_OBJECT_PRESERVATION=PASS` and `Ran 20 tests ... OK`; and the 20-test suite passes locally. The `pull_request_target` security properties I checked earlier still hold: base checkout, `persist-credentials: false`, `contents: read`, quoted env values, and the frozen verifier's only subprocess use is `git -C …` (no candidate code execution).

## Verdict

BLOCKING_FINDINGS=0
VERDICT=APPROVE
