# 000B2 Public-Corpus ATTEMPT-003 Recovery

## Status

`READY` for the single active unit named by `research/000b2-public/recovery-attempt-003-readiness.json` after this recovery authority becomes canonical.

This file is a forward-only successor to `recovery.md`. It does not rewrite, erase, or reinterpret the evidence that was canonical before the material ATTEMPT-002 execution defect was discovered.

## Trigger

Canonical B2R09 used pinned `sherpa-onnx==1.13.7` at source revision `917bed95c8e5c7c18aa4d69fea42e9ef8ef0a60e`. The pinned Python API defines:

```python
def get_result(self, s: OnlineStream) -> str:
    return self.recognizer.get_result(s).text.strip()
```

The canonical B2R09 decoder instead extracts:

```python
str(getattr(recognizer.get_result(stream), "text", "") or "")
```

That expression requests `.text` from the plain string returned by the pinned API and therefore falls back to the empty-string default. This is material execution drift because raw candidate output was not preserved faithfully under the frozen ATTEMPT-002 C0 contract.

The active 000B2 recovery rule is therefore controlling: material drift discovered after attempt freeze invalidates the attempt; preserve the old attempt and start a new pinned attempt.

## Authority precedence

For new execution decisions after this recovery becomes canonical:

1. `specs/CURRENT.md` remains the executable frontier owner.
2. `research/000b2-public/recovery-attempt-003-readiness.json` is the machine-readable successor recovery authority.
3. `research/000b2-public/recovery-readiness.json` remains a historical ATTEMPT-002 transition snapshot and MUST NOT authorize new execution.
4. `research/000b2-public/readiness.json` remains the older historical ATTEMPT-001/post-B2E02 snapshot.
5. `recovery.md` and the B2R01-B2R12 ledger remain immutable historical recovery chronology except for explicit forward-only supersession notes in this successor chain.

No lower-precedence state may reopen ATTEMPT-001 or ATTEMPT-002 primary execution.

## Immutable historical boundary

The exact bytes of ATTEMPT-002 execution artifacts that were canonical at discovery main `dc70fac9eddb6cda2dc4cabc4aec2df5f0beb9ff` MUST remain unchanged. At minimum this includes:

- `research/000b2-public/attempt-002-manifest.json`;
- `research/000b2-public/attempt-002-preexecution-state.json`;
- `research/000b2-public/b2r03-preexecution-rebinding.json`;
- all canonical B2R05-B2R09 decoder, evidence, provenance, and task-verifier files.

Closed noncanonical PR #89/#90 bytes are not promoted into canonical ATTEMPT-002 evidence.

ATTEMPT-002 is permanently ineligible for comparative scoring, candidate-superiority claims, or production selection.

## Frozen methodology boundary

The recovery corrects execution plumbing only. It does not authorize result-driven methodology changes.

The following remain fixed across ATTEMPT-003 unless a separately reviewed canonical methodology amendment is selected before the new attempt freeze:

- the six candidate cells and their order;
- the frozen P0 subset membership and exact source/preprocessed identities;
- C0 repository context `OFF`;
- C0 test-specific context `OFF`;
- candidate-specific audio transforms `OFF`;
- scorer implementation and configuration;
- public P0 normalization;
- ordinary read-English claim scope;
- diagnostic-only hosted-runner timing semantics;
- `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`;
- `production_stt_selected=false`;
- `product_code_authorized=false`.

## Successor task order

The successor chain is strict and dependency ordered:

1. `B2R13` — qualify ATTEMPT-002 material invalidation against canonical B2R09 bytes and exact pinned sherpa-onnx upstream source. No primary decode.
2. `B2R14` — qualify a corrected sherpa-onnx result-extraction harness against non-primary material only. The qualification must prove plain-string result preservation against the exact pinned runtime and fail closed on object/string API confusion. No primary decode.
3. `B2R15` — capture or cryptographically rebind attempt-bound preprocessing and execution-environment evidence for `000B2-PUBLIC-ATTEMPT-003`, preserving frozen subset/candidate/scorer/normalization identities. No primary decode.
4. `B2R16` — freeze `000B2-PUBLIC-ATTEMPT-003` before any new primary candidate decode. No primary decode may occur in the freeze unit.
5. `B2R17` — execute candidate cell 1 (`moonshine-compact`) under ATTEMPT-003.
6. `B2R18` — execute candidate cell 2 (`moonshine-balanced`) under ATTEMPT-003.
7. `B2R19` — execute candidate cell 3 (`whispercpp-compact`) under ATTEMPT-003.
8. `B2R20` — execute candidate cell 4 (`whispercpp-balanced`) under ATTEMPT-003.
9. `B2R21` — execute candidate cell 5 (`sherpa-onnx-compact`) under ATTEMPT-003 using the qualified result-extraction harness.
10. `B2R22` — execute candidate cell 6 (`sherpa-onnx-balanced`) under ATTEMPT-003 using the same qualified result-extraction harness.
11. `B2R23` — preserve the complete ATTEMPT-003 raw transcript/failure/runtime/run-identity evidence set and prove all six cells bind the same frozen attempt. No scoring and no further primary decode.
12. `B2R24` — score ATTEMPT-003 under the already-frozen scorer and normalization contract. No primary decode. Comparative result availability may become true only in terminal reconciliation after every predecessor is canonical, all required evidence verifies, and B2R24 itself satisfies the normal qualification/merge/post-merge gates.

B2R10, B2R11, and B2R12 remain historical pending units of the invalidated ATTEMPT-002 chain and are superseded for execution. They MUST NOT be checked as completed merely to advance this successor chain.

## Transition discipline

Each successor task must satisfy all of the following before the next task becomes executable:

- the task was the exact active unit on its canonical first parent;
- implementation/evidence scope is bounded to that task;
- focused checks and all applicable repository CI pass on the exact final head;
- fresh independent substantive semantic review covers the exact final task range;
- every actionable finding is repaired forward-only and review threads are reconciled;
- guarded merge uses the exact qualified head;
- the successor recovery workflow succeeds on the exact canonical task merge;
- a separate canonical reconciliation records the task merge, successful post-merge recovery run, completed task, and sole successor.

Each reconciliation may advance exactly one recovery task relative to its canonical authority base. Existing transition proofs are append-only. Every completed-task proof must use a unique canonical task merge and a unique successful post-merge recovery run. The proof must bind the canonical task base, the exact qualified task head, the normal merge commit whose first and second parents are those exact SHAs, the successful `main` push recovery run for that merge SHA, the completed task, and its sole successor. Reusing a merge/run proof, bulk-advancing multiple tasks, replacing an earlier proof, or accepting a squash/rebase commit as a task merge is prohibited.

Stale CI or review evidence never transfers to a changed head.

## Active-task content boundary

Path scope alone is not execution authority. The exact `task_candidate_scopes` and `task_content_policies` maps in the successor readiness state are frozen governance contracts established by B2R13 and MUST remain byte-semantically equivalent in every later authority state.

For B2R14 through B2R24, every non-reconciliation task candidate MUST:

- change only paths in the exact active-task allowlist;
- include the task's exact required verifier as a reviewable evidence artifact; the common trusted control MUST NOT execute candidate-supplied verifier code and instead validates the candidate diff itself;
- bind every changed artifact explicitly to the exact active B2R task;
- contain no reference to a future successor B2R task; references to already-canonical predecessor tasks are allowed only when they bind required evidence or qualified predecessor artifacts for the active task;
- bind each changed JSON evidence object with top-level `task` equal to the exact active task;
- contain no positive comparative-publication, production-selection, product-code, or primary-decode-authority declaration;
- contain no decode-runtime calls unless the active task is B2R17 through B2R22, except that B2R14 may exercise the pinned sherpa runtime API solely against explicitly non-primary qualification material while primary-decode entry authority remains `false`;
- contain no scoring calls unless the active task is B2R24.

In the v1 machine policy, `foreign_successor_task_references_allowed=false` is interpreted fail-closed as prohibiting future or otherwise unqualified successor-task material; it does not prohibit an exact canonical predecessor evidence binding that the active task contract requires. The common verifier computes the future-task set from `task_order` and rejects those references directly.

B2R14's runtime-call exception is not primary-decode authority. The only accepted harness entry point is exactly `extract_result(recognizer, stream)`. The trusted common recovery control—not candidate-supplied verifier execution and not a candidate-workflow mention—must require the harness to expose exactly one top-level function with that exact two-argument interface, no defaults, varargs, keyword-only arguments, or alternate entry points, and a body consisting only of `return recognizer.get_result(stream)`. The harness may contain no alternate `get_result` call, `.text` extraction, or `getattr` result coercion. The trusted common verifier compiles only that fixed function with empty builtins and independently invokes it on a trusted recognizer and trusted synthetic stream, requiring one and only one `get_result` call, identity-preserving passage of the exact stream object, and unchanged return of the trusted plain string. Candidate-workflow behavior is orchestration evidence only and cannot create qualification by merely naming the harness or entry point.

The same trusted control separately exercises the exact pinned sherpa API against the frozen synthetic fixture to prove the pinned runtime itself returns a plain string. A B2R14 task candidate is ineligible unless both the fixed candidate-harness entry-point contract and the pinned-runtime contract pass independently under the trusted common control.

The canonical B2R14 qualification fixture is frozen before B2R14 begins: `DETERMINISTIC_SYNTHETIC_NON_PRIMARY_FIXTURE_ONLY`, fixture id `b2r14-sherpa-result-string-contract-v1`, mono PCM S16LE at 16 kHz, 16000 frames, with exact PCM SHA-256 `0c92bddb4e96f3ea9ec9f0f64a668255a6c15527ac09f6f119cafde60c7c4a39`. The common successor verifier—not the B2R14-supplied verifier—must bind this contract and reject frozen P0, ATTEMPT-003 primary evidence, transcript, or successor decode artifact access from the B2R14 harness/workflow.

The common successor verifier enforces these rules from the exact authority-base-to-head diff. A task-specific verifier cannot replace or weaken the common content policy. A reconciliation cannot modify either task-scope or task-content policy because the common workflow and static verifier compare both maps against the canonical expected policy and the authority-base copy.

Primary-decode entry authority is `false` for B2R13 through B2R16, `true` only for B2R17 through B2R22, and `false` again for B2R23, B2R24, and terminal recovery state. ATTEMPT-003 must remain frozen from B2R17 onward, including B2R23, B2R24, and terminal state.

## B2R13 activation exception

B2R13 is the recovery-activation/invalidation unit required to remove execution authority from the already-invalid B2R10 frontier. Its task candidate may establish this successor specification, successor machine state, pinned invalidation evidence, and the successor proof workflow while leaving `B2R13` incomplete and `primary_decode_entry_open=false`.

After that task candidate is independently qualified and merged, the exact canonical post-merge successor-recovery run is required before a separate reconciliation may mark B2R13 complete and authorize B2R14.

This exception cannot be reused for B2R14 or later tasks.

## Evidence and provenance requirements

B2R13 must bind at least:

- discovery canonical main SHA;
- exact ATTEMPT-002 manifest blob and SHA-256;
- ATTEMPT-002 freeze digest;
- exact canonical B2R09 task merge and post-merge recovery run;
- exact B2R09 decoder/evidence/provenance blob identities;
- exact pinned `sherpa-onnx` distribution version and source revision;
- exact upstream `online_recognizer.py` path and Git blob identity;
- exact upstream `get_result(...) -> str` signature and return semantics;
- closed/nonmerged disposition of PR #89 and PR #90;
- explicit closure of ATTEMPT-002 scoring, ranking, synthesis, production selection, and product authority.

No reviewer, scanner, LLM, benchmark, or runtime can self-authorize execution. Deterministic repository policy remains the authority boundary.

## Merge gates

No B2R13 or later successor task may merge without:

- exact-head applicable CI success;
- fresh substantive independent semantic review of the exact final head/range;
- no unresolved actionable review findings;
- mergeability and base/head reconciliation against live GitHub truth;
- guarded exact-head merge;
- post-merge exact-SHA verification.

If no independent reviewer is available, the PR remains blocked. Rate-limit, billing, status-only, or self-review output is not independent review evidence.

## Closed surfaces

Until separately authorized after successful ATTEMPT-003 scoring and canonical synthesis:

- comparative ranking is closed;
- candidate superiority claims are closed;
- production STT selection is false;
- product-code authority is false;
- Rust/Cargo product implementation remains unauthorized;
- B3/B4 synthesis does not become executable merely because recovery work exists.
