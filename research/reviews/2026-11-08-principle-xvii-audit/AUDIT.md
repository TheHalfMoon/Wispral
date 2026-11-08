# Post-merge audit of Principle XVII (#129) and correction C1 (#130)

- **Date:** 2026-11-08.
- **Audited:**
  - Constitution 0.3.0 as merged by #129, merge `8d52a4579a0b1c6555cbe8443027c1950493b326`. Its pre-merge qualifying review was waived by the owner.
  - Draft #130 at head `de095ea3260698a84332ffd6cf708e336c645d51`.
- **Auditor:** a fresh-context Claude reviewer launched from the Claude Code session that authored #124/#125/#131. It had no involvement in #129 or #130.
- **Status: NON-QUALIFYING.** Under Governance item 7, reviewers from the author's model vendor "may assist but never qualify". This audit is assisting evidence only. It does not satisfy item 7 for #129, #130 or any patch amendment.
- **Method:**
  - Read-only reading of the merged text and the #130 diff.
  - Inspection of the local clone.
  - Read-only `gh` queries of check runs.
  - Nothing was edited, commented on through this audit, or merged.

## Verdicts

- **Principle XVII as adopted: NEEDS A PATCH AMENDMENT.** Findings A1–A4 are blocking.
- **#130 at `de095ea`: NOT MERGEABLE.** Findings B1–B4 are blocking. Resolving B2 needs either the A7 patch or an explicit qualifying-reviewer ruling on item 3.

## A. Principle XVII as merged

### A1. BLOCKING: frozen-object protection for later out-of-class candidates is not required

- **Quoted:** "detection on the authorized class is preserved in full".
- **Problem:** item 3 protects only in-class candidates. A correction that adds a path filter, or retires the gate, would satisfy XVII and leave the frozen objects unprotected on every later pull request. #130 happens to keep that protection, but XVII does not require it.
- **Proposed new item 3a:**

  > Every invariant the pre-correction control enforced other than the over-applied classification, including frozen-object identity, MUST remain enforced on every later candidate of every class, proven by negative fixtures on at least one out-of-class candidate.

### A2. BLOCKING: the item 10 reconciliation and the "Frontier sections" clause can change authority

- **Problem, item 10:** it places no limit on what the reconciliation may change.
- **Problem, "Frontier sections":** a correction, whose diff is limited to annexed paths, can still widen what non-B2 pull requests may edit in `specs/CURRENT.md` and `docs/canonical/CURRENT_STATE.md`. That conflicts with item 4 and can be repeated with every correction.
- **Proposed replacement for item 10:**

  > The reconciliation changes only records of the correction (merge SHA, preserved failures, verifier outputs). It MUST NOT change any authority, freeze, decode, scoring, readiness, task-scope or completion field, proven by a deterministic diff of those fields against the pre-correction base. It requires a qualifying review.

- **Proposed change to "Frontier sections":** replace "that an adopted correction under this principle designates" with "that a constitutional amendment designates".

### A3. BLOCKING: the lane cannot close at its second correction because of Principle XVI immutable controls

- **Problem:** annex items 3 and 4 name three paths that are also listed in `immutable_execution_control_paths` (`research/000b2-public/recovery-attempt-003-readiness.json`, lines 74–79):
  - the ATTEMPT-003 recovery workflow;
  - the trusted-PR workflow;
  - `verify_attempt_002_invalidation.py`.
- **Why that blocks:**
  - The trusted-PR gate checks those blobs before it checks scope, so a second correction (C2) will fail with "immutable execution control changed".
  - The annex excludes that boundary.
  - Item 5(b) can only neutralize the over-applied classification, so this failure can never "conclude successfully".
  - Principle XVI does not apply either, because it requires a fail-open defect.
- **Proposed text:**

  > Where an annexed path is also a XVI immutable control, the immutable-control boundary failure whose only failing condition is the declared annexed byte change MAY be preserved under item 5, provided that reverting only that blob makes the boundary pass and the immutable path list is not changed. XVI is not otherwise invoked.

### A4. BLOCKING, to verify: possible ordering deadlock between reconciliation and the second correction

- **Problem:**
  - Item 10 requires C1's reconciliation (R1) to merge before dependent work relies on it, and C2 relies on C1 for a passing freeze gate.
  - R1 edits files covered by the trusted-PR path filter, so it probably hits the over-applied scope gate.
  - R1 is not a correction pull request, so it cannot preserve failures.
  - If that holds, nothing can merge after C1.
- **Not run:** R1 was not run through the gates.
- **Proposed text:**

  > Reconciliations of corrections within one declared deadlock lane MAY be combined into one reconciliation after the lane's last correction. Until then no non-correction work may rely on any of them.

### A5–A9. NON-BLOCKING

- **A5 (non-concealment is underspecified):** "neutralized by a declared minimal change" cannot be tested. C1's neutralization, an early return, also skipped the decode, scoring, publish-authority and delete checks. Require:
  - the neutralization diff published byte-exact and pinned by commit SHA;
  - changes limited to the statements whose failure line is preserved;
  - every check skipped by the resulting control flow run separately and passing.
- **A6 (untestable terms):**
  - Define "the same failure" as the same gate, step and exact failure line.
  - Define "required by canonical repository authority": `main` has no branch protection and no rulesets.
  - Require a hash-pinned manifest for the "in-class corpus".
  - Define "applicable".
- **A7 (closed historical classes):** item 3's "identical verdicts" cannot be met for a class that has already completed, such as B2R16. Allow a pinned re-run of the original verifier at the qualified head with byte-identical output, together with A1.
- **A8 (unbounded red `main`):** a preserved failure that recurs on `main` stays red with no expiry. Bound it to "until the next correction in the declared lane merges". Also name #130 explicitly in the transitional clause.
- **A9 (waived review):**
  - Transitional condition 3 says the checker and test bytes are "part of this amendment's qualifying review", but that review was waived. A patch amendment with a qualifying review should ratify those bytes and 0.3.0 retroactively.
  - Item 4 lacks XVI's explicit rule on trigger and permission changes. Add: "changing a gate's trigger, trust root or permissions is permitted only if it moves execution to base-defined code and does not widen token permissions".

## B. #130 at `de095ea` against Principle XVII

### Verified

- The workflow digest `c60955b8…` and checker digest `1770952607…` match the pin in the workflow.
- Exactly the three declared paths change.
- `workflow_dispatch` run `42438889737` on `de095ea` succeeded.
- Both scope gates fail with the expected messages.
- `verify-legacy-recovery-boundary` and `verify-public-corpus-methodology` pass.
- `verify-b2r16-freeze` is absent, as predicted.
- Preserved-failure cause holds by exact failure line. Reverting C1's paths yields different messages, and the #120 base versus #120-plus-C1 surrogate pair confirms it.
- Item 1 (description), item 2 (paths), item 4 (non-broadening) and transitional conditions 1, 3(a) and 3(c) are met.

### Blocking

- **B1. No qualifying review of `de095ea` (item 7).** A qualifying review needs the owner, a human the owner names, or a reviewer from a different vendor. That reviewer must also reproduce transitional condition 3(b), which only the author has run so far.
- **B2. Item 3 evidence is missing.**
  - There is no in-class corpus.
  - The new control does not give identical verdicts: it rejects the qualified B2R16 head `ac9f7ce`, because `885307…` is not its ancestor. The old control accepted it.
  - Negative fixtures are missing for these rejecting branches:
    - not descended from `FROZEN_MERGE`;
    - zero or more than one `CHECKER_SHA256` literal;
    - digest literal not equal to the checker hash;
    - wrong `ls-tree` kind or name;
    - historical-proof failure;
    - the workflow's fetch and HEAD-drift checks.
  - Needs the A7 patch, or a reviewer ruling that `test_historical_stdout_unchanged` satisfies item 3.
- **B3. Non-concealment evidence is over-broad.** The neutralization in `c1_gate_evidence.sh` returns early after the reconciliation branch. That skips the forbidden decode and scoring call checks, the publish-authority check, and the delete and binding checks for C1's three paths. Those must be run separately and shown to pass.
- **B4. The evidence is not pinned.** The harness and its outputs are linked by branch name (`planning/wispral-world-class-master-plan-20261108`). Cite the commit SHA and the SHA-256 of `run_gate_steps.py`, `c1_gate_evidence.sh` and each output file.

### Non-blocking

- **B5. Skipped checks.** The four Trusted Materialization jobs are skipped. Record why their `if:` conditions do not apply, because transitional condition 2 says a skipped check "is not satisfied".
- **B6. The new files are unprotected.** `verify_b2r16_preservation.py` and `test_b2r16_preservation.py` are not in `FROZEN_PATHS`. A later pull request could gut either one. The result fails closed, but recreates the deadlock. Reject candidate changes to both files.
- **B7. Post-merge work is still pending.** Items 8–10 depend on A4.

## Recommended order

1. **A patch amendment (0.3.1) to Principle XVII**, with a qualifying non-Anthropic or owner review. It should address A1–A4 and ratify the waived #129 review (A9).
2. **#130 completes B2–B4**, then obtains a qualifying review (B1).
3. **The merges proceed** under the plan's W0 sequence.
