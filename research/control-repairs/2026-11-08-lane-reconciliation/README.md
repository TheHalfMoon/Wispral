# Evidence for Reconciliation 002 (B2R16/ATTEMPT-003 lane)

This directory holds the evidence for the combined lane reconciliation under Constitution 0.4.0, Principle XVII item 10. The record itself is "Reconciliation 002" in [`docs/canonical/TRUSTED_CONTROL_REPAIRS.md`](../../../docs/canonical/TRUSTED_CONTROL_REPAIRS.md).

| File | What it shows |
| --- | --- |
| [`r_field_diff.py`](r_field_diff.py) | The deterministic records-only proof. Run it from the repository root: `python -I research/control-repairs/2026-11-08-lane-reconciliation/r_field_diff.py 8d52a4579a0b1c6555cbe8443027c1950493b326 d78ecb540d97ff07b6788339177e9d63ed4dfca3 HEAD`. |
| [`runs/field_diff.txt`](runs/field_diff.txt) | Its output at the commit named in the file. |
| [`runs/recovery_dispatch_42508548479.txt`](runs/recovery_dispatch_42508548479.txt) | Key output lines of the ATTEMPT-003 recovery gate `workflow_dispatch` run on `main` at `d78ecb5`: success. |
| [`runs/pr118_trusted_checker.txt`](runs/pr118_trusted_checker.txt) | C1's trusted checker, from `main` at `d78ecb5`, run on #118's head `b7824b3` and its merge `edacdf7`: PASS on both. |
| [`review-118/`](review-118/) | The prompt and verbatim output of the qualifying retrospective review of #118 (NVIDIA Nemotron 3.5 Super through OpenCode): APPROVE, 0 blocking. The output's header mislabels the reviewer as an Anthropic model. The reviewer's identity is the route. |

Local paths are redacted.
