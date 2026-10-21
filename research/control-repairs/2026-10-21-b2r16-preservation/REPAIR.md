# B2R16 historical verification and frozen-object preservation

Status: dedicated draft control repair; no merge or successor authority. Canonical base: `edacdf7504302cc91ff7138bc6ac2d391e4df1f4`. Finding: external Opus [PR #125](https://github.com/TheHalfMoon/Wispral/pull/125), M1, reviewed original planning head `f36338138f4b4a872b05393b5cab03856dd7bf8e`.

## Defect and minimal correction

The original task verifier diffs the historical B2R16 authority base against current HEAD and requires exactly four task paths. It therefore fails on canonical main and #124 even though frozen task bytes are preserved. It still passes on qualified head `ac9f7ce993aec33e6c6436cce4efd85394a97f35`. This is **fail-closed over-application**, not a fail-open defect and not a Constitution XVI repair.

Keep `verify_b2r16.py`, the preexecution state and manifest unchanged. Keep the same always-on pull_request/workflow_dispatch event and `verify-b2r16-freeze` job; no paths filter, skip, continue-on-error or suppression. Replace the job invocation with:

1. Verify exact checkout SHA and SHA-256 of the new preservation checker and its fixtures **before candidate code executes**, using isolated Python `-I` so candidate-root modules cannot shadow hashlib/pathlib.
2. Check 16 frozen path identities against canonical task merge `885307429ec8b1aa0fe173169a8c2918714c06b0`: payloads, original verifier, workflow and the immutable candidate/subset/methodology/preprocessing/environment/harness/scorer inputs it binds. Require regular 100644 blob mode, exact paths, bytes and historical ancestry.
3. Run the unchanged original verifier at the exact qualified head in a fresh detached local snapshot with its historical readiness/authority context. Retain its original PASS output. Current readiness and successor ledgers intentionally evolve; they are not rewritten to pretend B2R16 remains active.
4. Run tamper fixtures: byte mutation for all 16 frozen paths; deletion, executable mode and symlink mode for each; invalid ref/commit input; exact replacement workflow plus mutation; forged checker/test scripts and candidate-root hashlib shadowing. Mode fixtures preserve the blob bytes to isolate mode rejection.

## Explicit control-workflow migration

The review's four-path immutable set includes the workflow being repaired. Requiring that path to remain byte-identical to 8853074 while also changing its invocation is impossible. This PR declares exactly one migration, not a wildcard exception: the original historical workflow or the exact reviewed replacement template is admissible. The replacement's checker digest literal is normalized solely to break a digest cycle; its value must still equal the exact checker file SHA-256. The fixture digest and every other workflow byte remain bound by the template hash. A byte change to either admissible workflow is rejected, including a changed checker digest. Historical verifier and evidence files have no exception.

The workflow also checks the checker/fixture hashes inline before executing them; replacing both Python scripts with exit-zero stubs fails. The mutation tests themselves are pinned by that preflight. This does not claim a workflow can independently trust its own arbitrarily changed entry code: canonical trusted bootstrap/review and repository governance must protect workflow changes. Required trusted-head jobs that are skipped on a draft are not satisfied. Do not merge until their applicability and fresh independent final-range review are resolved.

## Evidence and status

[local-results.json](local-results.json) preserves the original main/#124 failures and exact historical PASS plus final local control/test identities. Intermediate research harness failures (partial-clone missing historical blobs; a test running across active edits) were corrected forward: materialize the exact historical tree before a shared snapshot and freeze source identities before final execution. No GitHub failure is rerun or relabelled as success.

External review records #118 run `34416457849` as a failed freeze check on a merge that became canonical. Preserve that fact; it is not a waiver or a canonical reconciliation made by this PR. A separate legitimate reconciliation must record applicable authority after any control merge. Original #124 failure run `39588472485` remains failure. Logs may expire; local deterministic reproduction and metadata are distinguished from unavailable historical log bodies.

[settings-access.json](settings-access.json) records fresh API responses. Earlier study observations were 403. This repair's recheck returns main `protected=false`, classic protection 404 “Branch not protected”, and no repository/parent rulesets. No classic required-check list is exposed. This does not cancel governance-required exact-head checks. Recheck at merge; record UNKNOWN if access becomes unavailable.

This PR changes only the control workflow, adds the preservation checker/fixtures and bounded repair evidence. It does not modify frozen benchmark files, canonical state, constitution, active task readiness, scoring, decoding, production selection or product code. No existing PR is merged. Rollback is a governed control change, not deletion of failed evidence. Fresh-context patch review found and repaired mutable-script and import-shadowing bypasses; it does not replace any required external merge/security approval.

Reproduce with an existing Python interpreter from repository root:

```text
python -I research/000b2-public/test_b2r16_preservation.py
python -I research/000b2-public/verify_b2r16_preservation.py --candidate FULL_COMMIT_SHA
```

The checker needs complete commit/tree identities; missing objects/history fail closed. On a partial clone, historical tree materialization may fetch Git objects from the already configured repository remote. No model/audio/corpus or paid service is used.
