# C1 Principle XVII item 5 evidence

Evidence for correction C1 (B2R16 freeze preservation from a base-defined job). It covers the two B2 trusted scope gates that fail on C1 and are preserved under Constitution Principle XVII item 5.

- **Gate definitions:** `main` at `edacdf7504302cc91ff7138bc6ac2d391e4df1f4` (`.github/workflows/000b2-public-attempt-003-trusted-pr.yml`, job `verify-successor-pr-from-canonical-base`; `.github/workflows/000b2-public-attempt-003-recovery.yml`, job `verify-successor-recovery`). C1 changes neither file.
- **Harness:** [`run_gate_steps.py`](run_gate_steps.py) (successor of `../run_inline_gate.py`).
  - It runs every `run:` step of the job, as defined at that ref, separately under `bash --noprofile --norc -eo pipefail`. A failing step therefore does not hide later steps.
  - `uses:` steps (checkout) are performed by the driver, which uses a detached worktree at the exact candidate.
- **Driver:** [`c1_gate_evidence.sh`](c1_gate_evidence.sh). `GH_TOKEN` is read from the local `gh` session for the recovery gate's public transition-proof API reads. It is never printed or stored.
- **Host:** Windows 11, Git Bash, CPython 3.14, PyYAML 6.0.3.
- **Pinned source:** sherpa-onnx `917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e`, fetched exactly as the workflows fetch it.

## Candidates

| Name | Commit | Meaning |
| --- | --- | --- |
| `c1` | `a909024a49b746fa19b5654a01288cd460d544ae` | C1 head |
| `base` | `edacdf7504302cc91ff7138bc6ac2d391e4df1f4` | C1 with every declared path reverted (the authority base) |
| `pr120` | `85fe810267eda7ce1be8b76fd4cd769d3a39003d` | #120 head, an in-scope B2R17 candidate on the same authority base |
| `pr120c1` | `6f023cde56722ccea7b659906f1591b6e17916c0` | synthetic: `pr120` plus exactly C1's three declared blobs |

`pr120c1` is reproducible: the tree is `85fe810`'s tree with the three C1 blobs from `a909024` overlaid; parent `85fe810`; author and committer `Synthetic fixture <fixture@example.invalid>` at `2026-11-08T00:00:00Z`; message `Synthetic: #120 head plus C1 declared control bytes`.

## Results

Step exit codes per run. The `run:` steps are numbered as in each workflow; step 1 is the checkout.

### `verify-successor-pr-from-canonical-base`

| Candidate | Step 2 inline boundary | Step 3 common verifier `--static-only` | Step 4 sherpa fetch | Step 5 common verifier `--sherpa-source` |
| --- | --- | --- | --- | --- |
| `pr120` | 0 `TRUSTED_PR_GATE_CONTROL_BYTES=PASS` | 0 | 0 | 0 `TRUSTED_PR_GATE=PASS` |
| `pr120c1` | **1** `B2R17 candidate path scope violation` | **1** `must match the exact canonical task path set` | 0 | **1** same |
| `c1` | **1** `B2R17 candidate path scope violation` | **1** `must match the exact canonical task path set` | 0 | **1** same |
| `base` | 1 `empty successor candidate` | 1 `B2R17 candidate must not be empty` | 0 | 1 same |
| `c1`, classification neutralized | 0 `TRUSTED_PR_GATE_CONTROL_BYTES=PASS` | 0 | 0 | 0 `TRUSTED_PR_GATE=PASS` |

### `verify-successor-recovery`

| Candidate | Step 2 revision | Step 3 sherpa fetch | Step 4 inline boundary | Step 5 common verifier `--static-only` | Step 6 common verifier `--sherpa-source` | Step 7 transition proofs |
| --- | --- | --- | --- | --- | --- | --- |
| `pr120` | 0 | 0 | 0 | 0 | 0 | 0 |
| `pr120c1` | 0 | 0 | **1** `B2R17 task-candidate path scope violation` | **1** `must match the exact canonical task path set` | **1** same | 0 |
| `c1` | 0 | 0 | **1** `B2R17 task-candidate path scope violation` | **1** `must match the exact canonical task path set` | **1** same | 0 |
| `base` | 0 | 0 | 0 | 1 `B2R17 candidate must not be empty` | 1 same | 0 |
| `c1`, classification neutralized | 0 | 0 | 0 | 0 | 0 | 0 |

## Reading (Principle XVII item 5, #129 revision 3)

- **Cause.**
  - `pr120` passes every step of both gates. `pr120c1` is `pr120` plus exactly C1's three declared blobs, and it fails at exactly the classification checks. So the declared control bytes alone cause each preserved failure, and both gates are evaluated in both runs.
  - Reverting every declared path of `c1` yields `base`, a zero-delta candidate. There the scope failures do not occur, and the gates stop at their empty-candidate rule instead. This is weaker evidence and is shown only for completeness.
- **Preserved failures.** Six, each individually evidenced above:
  - trusted-pr steps 2, 3 and 5;
  - recovery steps 4, 5 and 6.

  All come from the same over-applied task-candidate classification: annex items 3 and 4, corrected in C2. Each occurs before any candidate execution or state transition.
- **Non-concealment.**
  - Every later step was executed separately. Each passed or failed only with one of the preserved failures; recovery step 7 passes unchanged.
  - With only the classification neutralized, every step of both gates passes on `c1`. The neutralization is printed in the outputs:
    - both inline scope `raise` statements become `print`;
    - a working-tree-only early return follows the reconciliation branch of `verify_active_task_candidate_content`. The committed verifier bytes, which the gates compare as Git objects, are unchanged.
- **Post-merge.** A normal merge of C1 into `edacdf7` has the same three-path diff. The push-triggered recovery gate on `main` is therefore expected to fail at steps 4 to 6 in the same way. It must be recorded by the item 10 reconciliation and not rerun to green.
- **Rebase.** These results bind authority base `edacdf7`. After #129 merges, C1 is rebased and this evidence is regenerated against the new base before C1's qualifying review.
