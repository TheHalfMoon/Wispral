# Trusted-Control Repair Reconciliations

**Status:** canonical append-only governance/evidence ledger
**Authority:** `CONSTITUTION.md` Principle XVI
**Successor-state effect:** none unless a later independently authorized successor reconciliation changes successor state

This ledger records completed trusted-control repair sequences required by Constitution Principle XVI. A record here is not a successor task reconciliation, does not complete a B2 recovery task, does not mutate successor readiness, and cannot authorize decode, scoring, comparative claims, production selection, product code, or project completion.

Each repair record must preserve exact repository identities, failed-boundary evidence without relabeling it as success, deterministic positive/negative proof, independent review disposition, canonical merge ancestry, canonical-state exercise evidence, and the exact execution authority that remains after reconciliation.

## Repair 001 — ATTEMPT-003 successor exact-scope and deletion hardening

### Defect

The canonical common successor verifier in `research/000b2-public/verify_attempt_002_invalidation.py` had two related fail-open scope defects:

1. trusted task/reconciliation validation rejected paths outside an allowlist but accepted strict subsets instead of requiring exact canonical path-set equality;
2. trusted scope-derived Git diff queries used `--diff-filter=ACMRTUXB`, excluding deleted paths from the candidate scope input.

The second defect was found by fresh independent review after the first repair was already prepared. It was repaired forward-only before merge. The final verifier uses exact path-set equality and deletion-aware `--diff-filter=ACDMRTUXB` in the B2R13, B2R14, and general active-task/reconciliation scope queries.

### Canonical repair identity

- repair authority base: `a7b2179ade9825e4f280c5cf28aa72a3e361e970`
- exact independently reviewed repair head: `51891f584be26639e3cda427e4f61d46fe524b1a`
- repaired verifier blob: `b8ed65776c6d9b5ae313c34d91c221b13a25197e`
- repair PR: `#106`
- guarded normal repair merge: `003ed3a44b89779ff51df45cd1d015ef6da98370`
- canonical repair merge tree: `0e9e17fc1396971bd4e172a14bc2f82c67f1dadc`
- canonical repair merge first parent: `a7b2179ade9825e4f280c5cf28aa72a3e361e970`
- canonical repair merge second parent: `51891f584be26639e3cda427e4f61d46fe524b1a`
- GitHub commit verification: `verified=true`, reason `valid`

The final repair changed only `research/000b2-public/verify_attempt_002_invalidation.py` relative to its canonical authority base.

### Preserved pre-merge boundary evidence

The following exact-head non-successes are preserved as Principle XVI boundary evidence and are not counted as successful gates:

- `000B2 Public Corpus ATTEMPT-003 Trusted PR Gate` run `34402893952` failed only because the declared immutable trusted-control verifier bytes changed. Candidate common-verifier execution, pinned-source verification, and runtime-contract execution were skipped.
- `000B2 Public Corpus ATTEMPT-003 Recovery` run `34402895472` failed at the trusted pre-candidate boundary with `B2R16 task-candidate path scope violation` because the same trusted-control path is outside ordinary B2R16 task scope. Dependent candidate execution, material-drift verification, and transition-proof steps were skipped.

Other applicable exact-head repair checks succeeded:

- `000B2 Public Corpus Attempt Recovery` run `34402895470` — `success`;
- `000B2 Public Corpus Methodology` run `34402895445` — `success`.

`000B2 Trusted Materialization Authority` run `34402894009` was skipped and was not applicable to the repair candidate; it is not counted as success.

### Pre-merge deterministic proof

Evidence-only PR `#113` was closed unmerged after capture. Run `34403473885`, job `102640722781`, bound exact repair head `51891f584be26639e3cda427e4f61d46fe524b1a`, verifier blob `b8ed65776c6d9b5ae313c34d91c221b13a25197e`, and B2R16 source head `ee3b419bc2b5c32bc72ced1c777a07ebfc6f85f4`.

The run proved:

```text
TASK_EXACT_SCOPE_POSITIVE=PASS
TASK_INCOMPLETE_SCOPE_REJECTION=PASS
TASK_EXTRA_SCOPE_REJECTION=PASS
TASK_UNRELATED_DELETION_REJECTION=PASS
B2R13_UNRELATED_DELETION_REJECTION=PASS
RECONCILIATION_EXACT_SCOPE_POSITIVE=PASS
RECONCILIATION_INCOMPLETE_SCOPE_REJECTION=PASS
RECONCILIATION_EXTRA_SCOPE_REJECTION=PASS
RECONCILIATION_UNRELATED_DELETION_REJECTION=PASS
```

It also preserved:

```text
ATTEMPT_002_INVALIDATION=PASS
ATTEMPT_002_HISTORICAL_BYTES=PASS
ACTIVE_SUCCESSOR_RECOVERY_UNIT=B2R16
COMPARATIVE_RESULT_AVAILABLE=NO
PRODUCTION_STT_SELECTED=NO
PRODUCT_CODE_AUTHORIZED=NO
HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT
```

### Independent review

Review-only PR `#114` pointed to the exact same canonical base and final repair head and was closed unmerged after review. Fresh independent CodeRabbit review inspected exact range `a7b2179ade9825e4f280c5cf28aa72a3e361e970..51891f584be26639e3cda427e4f61d46fe524b1a`, the full one-file repair, Principle XVI authority, exact workflow evidence, and the repaired deletion-bypass finding. It reported no blocking governance, security, correctness, compatibility, historical-state, scope, or authority-expansion issue.

Earlier review-only PR `#112` is preserved as the source of the deletion-filter finding on stale head `70aa5e91d9f1b3e1cab7e97b32e61d9a7d3107a5`; that finding was repaired forward-only and resolved before the final review.

### Canonical merge and push observation

Guarded normal merge `003ed3a44b89779ff51df45cd1d015ef6da98370` preserved the exact canonical base and independently reviewed repair head as its two parents.

Exact-merge push workflows succeeded for:

- `000B2 Trusted Participant Policy` run `34404010596`;
- `000B2 Public Corpus Methodology` run `34404010647`;
- `000B2 Trusted Human Authority Structure` run `34404010595`;
- `000B2 Trusted Materialization Authority` run `34404010722`;
- `000B2 Trusted Participant Materials` run `34404010572`;
- `000B2 Public Corpus Attempt Recovery` run `34404010576`;
- `000B2 Public Corpus Candidate Revalidation` run `34404010579`, with both static and live jobs successful.

`000B2 Public Corpus ATTEMPT-003 Recovery` run `34404010547` failed at `Trusted pre-candidate execution boundary` with `B2R16 task-candidate path scope violation`. The repair merge is not a B2R16 task candidate. The failure occurred before successor candidate verification, material-drift verification, or transition-proof execution. It is preserved as observed post-merge behavior, was not rerun-to-green, and is not counted as success.

### Canonical-state repaired-control exercise

Evidence-only PR `#115` was closed unmerged after capture. `Trusted Control Repair 003ED Canonical State Evidence` run `34404224592`, job `102643205076`, completed successfully.

The workflow bound and exercised the verifier from exact canonical repair merge `003ed3a44b89779ff51df45cd1d015ef6da98370` and exact verifier blob `b8ed65776c6d9b5ae313c34d91c221b13a25197e`. It reset each deterministic candidate sandbox to that exact canonical merge and reproduced all nine pre-merge exact/missing/extra/deletion positive/negative results, including B2R16 task deletion rejection, B2R13 activation deletion rejection, and reconciliation deletion rejection.

This satisfies the Principle XVI requirement to exercise the repaired control against the exact canonical state after merge.

### Reconciled authority

This repair reconciliation does not change `research/000b2-public/recovery-attempt-003-readiness.json`, does not append a successor transition proof, and does not complete or advance any B2 recovery task.

After this reconciliation becomes canonical:

- the trusted-control repair dependency freeze is closed;
- `B2R16` remains the sole active successor recovery unit;
- ATTEMPT-003 remains required and unfrozen;
- primary decode and scoring remain closed;
- B2R17 and every later successor remain unauthorized;
- comparative publication/ranking, production selection, product code, and project completion remain closed;
- any B2R16 candidate must be freshly qualified against the then-current canonical base; evidence from a pre-repair base or earlier candidate head is stale.

This record authorizes only resumption of fresh B2R16 qualification under the ordinary successor gates. It does not authorize B2R16 merge, primary decode, B2R17, scoring, or any later project state.
