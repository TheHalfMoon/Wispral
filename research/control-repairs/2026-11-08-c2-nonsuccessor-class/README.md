# C2 evidence: non-successor class for the B2 scope gates

**Correction C2** of the B2R16/ATTEMPT-003 lane, under Constitution 0.4.0, Principle XVII (annex items 3 and 4).

- Authority base: `main` = `76fe651a41eaf73e12f6ac85d7f159427ada1447`.
- Control commit: `d5bb5bea53fe7c20bfaba705040443a8154cfa69`. The evidence directory is added on top of it and changes no control byte.
- Harness: [`tools/run_gate_steps.py`](tools/run_gate_steps.py) (SHA-256 `4198c25b…`). It runs every `run:` step of a gate job, as defined at a fixed Git ref, separately on a detached candidate checkout.
- Drivers: [`tools/c2_evidence.py`](tools/c2_evidence.py), [`tools/c2_neutral.py`](tools/c2_neutral.py), [`tools/c2_a3_boundary.py`](tools/c2_a3_boundary.py), [`tools/c2_corpus.py`](tools/c2_corpus.py) and [`tools/b3_checks_base.py`](tools/b3_checks_base.py).
- Synthetic candidates are reproducible: fixed author, committer and date (`Synthetic fixture`, `2026-11-08T00:00:00Z`), built by `c2_evidence.py`.

Step codes below are `step:exit`.

## 1. After merge: gate definitions and authority base = the C2 control commit

| Candidate | trusted-pr | recovery | Expected |
| --- | --- | --- | --- |
| `ns_ok`: edits allowlisted sections in both frontier files and appends `## Platform frontier` | 2:0 3:0 4:0 5:0 | 2:0 3:0 4:0 5:0 6:0 7:0 | **pass** |
| `task_pr120`: #120's B2R17 task changes | 2:0 3:0 4:0 5:0 | 2:0 3:0 4:0 5:0 6:0 7:0 | pass (in-class verdict unchanged) |
| `neg_task_extra_path`: #120 plus an extra path | 2:1 3:1 4:0 5:1 | 2:0 3:0 4:1 5:1 6:1 7:0 | reject (in-class verdict unchanged) |
| `neg_b2_path`, `neg_github_path`, `neg_readiness`, `neg_outside_allowlist`, `neg_reordered`, `neg_duplicate_heading`, `neg_confusable_heading`, `neg_marker_in_allowlisted`, `neg_marker_in_appended`, `neg_preamble` | 2:1 3:1 4:0 5:1 | 2:0 3:0 4:1 5:1 6:1 7:0 | reject (10 negative fixtures) |
| `neg_c1_checker`: changes C1's freeze checker | 2:1 3:1 4:0 5:1 | 2:0 3:0 4:1 5:1 6:1 7:0 | reject (item 3a for #130's checker and tests) |
| canonical self-check: the C2 commit itself, empty diff | n/a | 2:0 3:0 4:0 5:0 6:0 7:0 | pass (R can show the recovery gate green on `main`) |

The classifier rejects each negative for its intended reason; the outputs are in [`runs/`](runs/). Examples: `B2-owned path changed`, `existing sections removed, renamed or reordered`, `duplicate section heading`, `confusable or duplicate allowlisted heading`, `B2 marker inside allowlisted section`, `text before the first section changed`.

## 2. C2's own pull request: gate definitions and authority base = `main` `76fe651`

### Cause (item 5(a))

| Candidate | trusted-pr | recovery |
| --- | --- | --- |
| #120's changes on `main` | 2:0 3:0 4:0 5:0 | 2:0 3:0 4:0 5:0 6:0 7:0 |
| the same + exactly C2's three blobs | 2:**1** 3:**1** 4:0 5:**1** | 2:0 3:0 4:**1** 5:**1** 6:**1** 7:0 |
| C2 control commit | 2:**1** 3:**1** 4:0 5:**1** | 2:0 3:0 4:**1** 5:**1** 6:**1** 7:0 |

The preserved failures:

- trusted-pr step 2: `immutable execution control changed`. This is the immutable-boundary case of item 5 (A3).
- trusted-pr steps 3 and 5: the common verifier's byte-equality test against the base. The same A3 boundary.
- recovery step 4: `B2R17 task-candidate path scope violation`.
- recovery steps 5 and 6: `B2R17 candidate must match the exact canonical task path set`.

### A3 immutable boundary (item 5)

- **Bytes outside the annexed parts.** [`runs/a3_boundary.txt`](runs/a3_boundary.txt): every changed line of the three blobs lies inside the annexed scope-classification step or function. `A3_BOUNDARY=PASS`.
- **Reverting one blob clears the boundary.** #120 plus exactly **one** C2 blob fails the boundary naming exactly that path (`runs/perblob_trusted_*.txt`). #120 alone passes, so reverting only that blob makes the boundary pass.
- **The immutable list is unchanged.** The readiness file is not touched.

### Non-concealment (item 5(b))

- **Neutralized run.** C2 was run again with only the preserved checks neutralized. In the gate steps (harness `--patch`, printed in the outputs), the immutable-boundary `raise` statements, the scope `raise` and the byte-equality `test` were neutralized. In the verifier, a working-tree-only early return was added ([`runs/neutralization_verifier.diff`](runs/neutralization_verifier.diff)). Result: **every step of both gates passes** (trusted-pr 2:0 3:0 4:0 5:0; recovery 2:0 to 7:0).
- **Skipped checks, run separately.** The task-content checks that the verifier neutralization skips were run separately ([`runs/b3_c2.txt`](runs/b3_c2.txt)). Deletion, decode and scoring pass. The future-task-token and authority-string hits are identical on the base bytes of the same three control files, which enumerate every task. C2 adds no task token.

## 3. In-class corpus (item 3)

- **Coverage.** [`c2_in_class_corpus_manifest.json`](c2_in_class_corpus_manifest.json) (SHA-256 `867c0b9fa00462d6825d02be47be9d4c3aa3804c956efccd1e37018ef427b716`) lists all **114** candidates that either scope gate ever evaluated on a pull request, from the GitHub run history.
- **Result.** C2's `nonsuccessor_violations` is non-empty for every one of them. C2 changes a gate's behavior only when it is empty, so **every historical verdict is preserved**.
- **Present-day check.** The live B2R17 candidate (#120) and a malformed variant keep their verdicts under the C2 definitions (section 1).

## 4. Not in this correction

The trusted-coverage extension in plan §4.2 item 4 changes the trusted-pr workflow's path filter, outside the annexed step. Constitution 0.4.0 item 5 (A3) does not allow that in a XVII correction, so it is a separate follow-up.
