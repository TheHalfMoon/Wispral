# B3: task-content guards skipped by the item 5(b) neutralization

The neutralization of `verify_active_task_candidate_content` in the common verifier (an early return after the reconciliation branch) also skips the per-path task-content checks that follow it. An assisting audit (#130 comment, finding B3) asked for those checks to be run separately.

[`b3_checks.py`](b3_checks.py) (SHA-256 `22172ffcbfc3bbc431bff26a9b45daea6556a0bfb84f9ddee3a5a79e6c700320`) runs them from the authority-base verifier bytes (blob-identical in the candidate) on every path the candidate changes relative to `8d52a45`.

| Check | C1 `cabf4e5` (3 paths) | #120 on `8d52a45` (`1705b4f`, 5 paths) |
| --- | --- | --- |
| not deleted | PASS | PASS |
| no future successor tokens | PASS | PASS |
| no positive authority publication | PASS | PASS |
| no forbidden decode-runtime calls (`.py`) | PASS | PASS |
| no forbidden scoring calls (`.py`) | PASS | PASS |
| active-task binding token `B2R17` (classification) | absent | present |
| required verifier `verify_b2r17.py` changed (classification) | no | yes |
| JSON `task` binding (classification) | no JSON | present |

- Every generic guard passes on C1: `B3_GENERIC_TASK_CONTENT_GUARDS=PASS`.
- The only checks C1 does not satisfy are those that exist to identify a B2R17 task candidate. That is the over-applied classification itself, which C2 corrects.
- #120 satisfies all of them, which shows they function.

Outputs: [`b3_c1_cabf4e5.txt`](b3_c1_cabf4e5.txt), [`b3_pr120_1705b4f.txt`](b3_pr120_1705b4f.txt).
