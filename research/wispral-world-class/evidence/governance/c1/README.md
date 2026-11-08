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

## Regenerated on the final authority base `8d52a45` (after #129 merged)

#129 merged as `8d52a4579a0b1c6555cbe8443027c1950493b326`, with first parent `edacdf7`. Its only change is `CONSTITUTION.md`. C1 was rebased onto it as head `de095ea3260698a84332ffd6cf708e336c645d51`; the three declared blobs are unchanged. The whole run set was repeated with `BASE=8d52a45` and gate definitions at `8d52a45`. Outputs are in [`base-8d52a45/`](base-8d52a45/).

| Name | Commit | Meaning |
| --- | --- | --- |
| `c1` | `de095ea3260698a84332ffd6cf708e336c645d51` | rebased C1 head |
| `base` | `8d52a4579a0b1c6555cbe8443027c1950493b326` | C1 with every declared path reverted |
| `pr120` | `1705b4f2ba4d7261bb6df32c5bf431e60181ef1e` | synthetic: #120's five changed paths (`edacdf7..85fe810`) overlaid on `8d52a45` |
| `pr120c1` | `0141ef59c402e6961c2d7a58fcef533eee8d763b` | synthetic: `pr120` plus exactly C1's three declared blobs from `de095ea` |

Both synthetic commits use the same fixed author, committer and date as above. Their messages are `Synthetic: #120 changes overlaid on 8d52a45` and `Synthetic: rebased #120 plus C1 declared control bytes`.

Step exit codes (step:exit):

| Run | trusted-pr | recovery |
| --- | --- | --- |
| `pr120` | 2:0 3:0 4:0 5:0 | 2:0 3:0 4:0 5:0 6:0 7:0 |
| `pr120c1` | 2:**1** 3:**1** 4:0 5:**1** | 2:0 3:0 4:**1** 5:**1** 6:**1** 7:0 |
| `c1` | 2:**1** 3:**1** 4:0 5:**1** | 2:0 3:0 4:**1** 5:**1** 6:**1** 7:0 |
| `base` | 2:1 3:1 4:0 5:1 (empty candidate) | 2:0 3:0 4:0 5:1 6:1 (empty candidate) 7:0 |
| `c1`, classification neutralized | 2:0 3:0 4:0 5:0 (`TRUSTED_PR_GATE=PASS`) | 2:0 3:0 4:0 5:0 6:0 7:0 |

The failure texts are the same as on `edacdf7`, and the reading above holds unchanged on the final base.

## Final head `cabf4e5` (after the qualifying review's blocking findings)

The different-vendor review of `de095ea` returned four blocking findings. Commit `cabf4e5d96ab03d38a74ee4e5986be17a26f5e74` resolves them. Because the three declared blobs changed, the whole item 5 run set was repeated on base `8d52a45` (outputs in [`head-cabf4e5/`](head-cabf4e5/)).

| Name | Commit |
| --- | --- |
| `c1` | `cabf4e5d96ab03d38a74ee4e5986be17a26f5e74` |
| `pr120c1` | `c0eac928db00c1af30ff998b15ef7dc49e1a694c`: `pr120` (`1705b4f`) plus exactly the three `cabf4e5` blobs; same fixed fixture identity and message as before |

The exit-code pattern is identical to the `de095ea` and `edacdf7` runs in both gates: `pr120` passes every step; `pr120c1` and `c1` fail only at the classification steps; with the classification neutralized, `c1` passes every step.

### Pre-correction freeze gate (review finding 4)

[`freeze_gate_evidence.sh`](freeze_gate_evidence.sh) ran the freeze gate as defined at `8d52a45` (`verify_b2r16.py --require-git` from the candidate checkout) on `cabf4e5` and on `8d52a45`. Outputs are in [`freeze-gate-cabf4e5/`](freeze-gate-cabf4e5/).

| Run | C1 `cabf4e5` | base `8d52a45` |
| --- | --- | --- |
| plain | `FAIL: B2R16 actual candidate range scope drift` | the same |
| range classification neutralized | `FAIL: canonical recovery prefix drift` | the same |
| range and B2R16 task-time authority neutralized | `B2R16_ATTEMPT_003_FREEZE=PASS` | the same |

- **Cause.** The failure is the defect's own reproduction. It occurs without C1, and the transitional clause preserves it on C1.
- **Non-concealment.** The checks it masked pass on C1: frozen source identities, preexecution state, manifest, and primary-output surface.

### Harness and driver digests (SHA-256)

| File | SHA-256 |
| --- | --- |
| `run_gate_steps.py` | `4198c25becfd81d98086bb4ac85566bad81276c7c7ac5e2216be47c42e661a6f` |
| `c1_gate_evidence.sh` | `a5825c17106b77aa31bc95f5ac18fa42e67604a229573644d4629523eca52413` |
| `freeze_gate_evidence.sh` | `136939c0fa1be2ffcd75aa8afaf16996beb07863d82620e041d63b18d554ea40` |
