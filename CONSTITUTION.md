# Wispral Constitution

**Version:** 0.4.0  
**Status:** Active  
**Ratified:** 2026-09-01  
**Amended:** 2026-11-08  
**Canonical ratification merge:** `3cbe212bf7202c37ec322f114c0e5486e5218d9b`

## Preamble

Wispral exists to make speaking to AI coding agents a trustworthy control interface rather than a transcription shortcut. The product should let a developer speak, think aloud, interrupt, steer, inspect, approve, and recover while preserving the authority boundaries of the underlying agent and repository.

The project optimizes for durable usefulness, interoperability, trust, speed, and open evidence. Popularity is a desired consequence of exceptional utility, not a substitute for it.

## Principle I — Control plane, not another agent

Wispral MUST remain primarily an interface and control plane around independent agents. It MUST NOT require users to adopt a Wispral-owned foundation model, coding agent, IDE, or hosted reasoning service for the core product to work.

Agent-specific adapters MAY improve compatibility but MUST remain outside the portable core contract.

## Principle II — Speech is evidence, not authority by default

Raw audio, transcripts, interpreted intent, resolved repository entities, and authorized actions are distinct states.

Wispral MUST NOT silently transform ambiguous or tentative speech into consequential authority. The system MUST preserve enough provenance to explain what was heard, what was resolved, what was interpreted, and what was sent to an agent.

## Principle III — Interruptibility is a first-class primitive

A voice interface that cannot be interrupted cannot be a trustworthy control plane.

Cancellation, barge-in, steering, pause, denial, and recovery MUST be designed as core runtime semantics rather than UI conveniences added after execution.

## Principle IV — Command and context are different

Wispral MUST support the product distinction between speech intended to cause action and speech intended to provide context, exploration, preference, or tentative reasoning.

The project MAY evolve the exact interaction mechanism, but it MUST NOT assume that every spoken utterance is an executable command.

## Principle V — Repository-aware meaning outranks generic dictation

Wispral SHOULD use bounded repository context to improve interpretation of paths, symbols, package names, flags, branches, tests, and other developer entities.

Context resolution MUST remain inspectable, confidence-aware, bounded, and reversible. A low-confidence entity binding MUST NOT be hidden behind polished text.

## Principle VI — Agent and protocol neutrality

No single commercial agent, model vendor, editor, speech provider, or proprietary protocol may become necessary for the core workflow.

Open protocols SHOULD be preferred when they provide the required semantics. Compatibility fallbacks MAY exist, but protocol-specific behavior MUST not leak into the portable product contract without explicit justification.

## Principle VII — Local-first, cloud-optional

A useful core path MUST be possible without a Wispral account or mandatory Wispral-hosted service.

Cloud speech, model, synchronization, or enterprise services MAY be supported as optional adapters. Their failure MUST NOT silently weaken privacy, authorization, or evidence guarantees.

## Principle VIII — Deterministic trust boundaries

Speech recognition, language models, entity resolution, and ranking may be probabilistic. Authorization, policy evaluation, state transitions, evidence binding, safety escalation, and destructive-action gates MUST be deterministic and testable.

Probabilistic confidence MAY inform a deterministic rule; it MUST NOT itself become the sole authority for a high-risk action.

## Principle IX — Risk changes rigor

Verification and user confirmation MUST scale with blast radius.

Read-only inspection, reversible edits, repository writes, external side effects, credential use, spending, destructive operations, and publication actions MUST NOT share one undifferentiated approval policy.

High-risk paths require explicit negative-path, cancellation, provenance, and recovery evidence.

## Principle X — Rust owns the runtime, not the ideology

The product runtime SHOULD be Rust-first for latency, concurrency, cancellation, portability, memory safety, and single-binary distribution.

Other languages and native libraries MAY be used when evidence demonstrates a better engineering boundary. Language purity MUST NOT outrank product correctness, accessibility, portability, or maintainability.

## Principle XI — Open benchmarks before comparative claims

Wispral MUST NOT claim superiority in latency, accuracy, developer speech recognition, interruption, privacy, compatibility, or productivity without a reproducible public method and artifacts sufficient for independent challenge.

Benchmarks MUST include adverse and losing results where material. Hidden scorer knowledge, cherry-picked devices, or undocumented prompt/model changes invalidate a general comparative claim.

## Principle XII — Progressive refinement over speculative scale

Program ambition may be large, but executable work MUST remain small enough to understand and prove.

Distant roadmap horizons MUST remain intentionally coarse. Near-term work is recursively refined until it satisfies the Definition of Grain. Evidence, not enthusiasm, selects the next implementation frontier.

## Principle XIII — Accessibility is a product contract

Voice interaction can materially improve or harm accessibility. Wispral MUST treat configurable input behavior, speech pacing, visible state, non-voice fallback, keyboard control, captions/transcripts, and failure recovery as product requirements rather than polish.

The product MUST NOT assume one accent, speaking cadence, language, microphone setup, hearing ability, or motor interaction pattern.

## Principle XIV — Privacy is observable behavior

Microphone state, recording state, network use, transcript persistence, telemetry, model routing, and credential access MUST be observable and documented.

Core behavior MUST NOT depend on hidden background recording or undisclosed content telemetry. Telemetry, when introduced, MUST be opt-in or otherwise governed by an explicit approved privacy contract.

## Principle XV — Adoption claims are separate from engineering truth

GitHub stars, trending position, press, social reach, downloads, and community size are meaningful distribution signals but do not establish product correctness or technical superiority.

The project MAY pursue ambitious adoption goals, including category leadership, while keeping engineering acceptance criteria evidence-based and independently verifiable.

## Principle XVI — Trusted-control repair is fail-closed and exceptional

Repository controls designated as immutable for ordinary task or reconciliation candidates MUST remain immutable for those candidates. Their immutability is a trust boundary, not a reason to preserve a proven fail-open defect.

If fresh independent evidence demonstrates that an immutable trusted control is materially fail-open, and the existing immutable-control gate prevents the defect from being corrected through the ordinary execution lane, all dependent execution MUST freeze until the authority conflict is resolved explicitly.

A trusted-control repair is authorized only through a dedicated governance-control repair sequence that satisfies all of the following:

1. the repair is limited to the exact trusted-control path or paths required to remove the demonstrated fail-open defect;
2. the repair MUST strictly strengthen or restore fail-closed behavior and MUST NOT broaden task scope, reconciliation scope, execution authority, evidence authority, decode authority, scoring authority, comparative-claim authority, product authority, or completion state;
3. the repair PR MUST describe the defect, exact canonical authority base, exact changed-path scope, expected conflict with the pre-repair immutable-control gate, compatibility impact, security/privacy impact, affected specifications, and the deterministic evidence required to prove the correction;
4. the pre-repair immutable-control gate failure caused solely by the declared trusted-control byte change MUST be preserved as conflict evidence and MUST NOT be relabeled, suppressed, rerun-to-green, or counted as a successful gate;
5. every exact-head gate required by canonical repository authority and applicable to the repair candidate MUST conclude successfully on the exact final repair head; a required gate that is absent, skipped, pending, cancelled, or failed is not satisfied. The sole permitted non-successes are preserved pre-repair trusted-boundary results whose only failing condition is the declared trusted-control byte change described in item 4. Such preserved results MAY include both the immutable-control boundary and an ordinary task- or reconciliation-scope boundary when that scope boundary necessarily rejects the same trusted-control path because it is outside the ordinary candidate scope. Each preserved non-success MUST be individually evidenced, MUST occur before any dependent candidate execution or state transition, and MUST NOT conceal any unrelated failure. No other non-success category is permitted;
6. deterministic positive and negative evidence MUST show that the repaired control accepts an exact valid candidate while rejecting the demonstrated malformed or incomplete candidate class;
7. a fresh independent substantive review MUST cover the exact final repair range and resolve all blocking findings before merge;
8. the repair MUST use a guarded normal merge bound to the exact reviewed head;
9. after merge, the actual canonical merge SHA and ancestry MUST be verified, the repaired control MUST be exercised against that exact canonical state by a deterministic verifier or canonical workflow, and a separate canonical reconciliation MUST record the repair before dependent execution resumes.

This repair authority MUST NOT be used as a substitute for an ordinary required gate. If strict strengthening cannot be demonstrated under these conditions, the project remains blocked.

## Principle XVII — Correcting an over-applied benchmark control is explicit, narrow, and proven

**Scope.** This principle applies only to the controls listed in the annex below. Adding a control to the annex requires a constitutional amendment. It never applies to a control, or to any step of a control, whose purpose is security, consent, tenant isolation, network egress, credential handling, release, or signing; such a control or step changes only through an ordinary reviewed change that strengthens it, or through Principle XVI. Where an annexed file also contains such a step, that step MUST remain unchanged in effect, proven by its existing negative fixtures.

**Annex.** The initial annexed controls are:

1. `.github/workflows/000b2-public-b2r16-freeze.yml`;
2. `research/000b2-public/verify_b2r16.py`;
3. the scope-classification steps of `.github/workflows/000b2-public-attempt-003-recovery.yml` and `.github/workflows/000b2-public-attempt-003-trusted-pr.yml` (the immutable-control-blob boundary of the latter is not annexed);
4. the scope-classification functions of `research/000b2-public/verify_attempt_002_invalidation.py`.

**Defect.** An annexed control is over-applied only when (a) canonical authority text assigns it to a named candidate class, and (b) reproduction on canonical `main` or on a minimal synthetic candidate outside that class shows that it rejects candidates outside that class, or `main` itself. Argument alone is not evidence.

A correction of an over-applied annexed control is authorized only through a dedicated control-correction pull request that satisfies all of the following:

1. the pull request MUST describe the defect, the exact canonical authority base, the exact changed paths, the expected conflict with the pre-correction controls, the compatibility impact, the security and privacy impact, and the affected specifications;
2. the correction MUST change only the exact annexed control paths required, any new verifier or test files those controls invoke, and its evidence directory;
3. deterministic evidence executed from trusted code (base-pinned, hash-verified, run under an isolated interpreter) MUST show that detection on the authorized class is preserved in full: identical verdicts on an in-class corpus that includes every previously rejected malformed candidate, plus at least one negative fixture for every rejecting branch of the corrected control. The in-class corpus MUST be listed in a manifest pinned by SHA-256. For a candidate class whose task has already merged, identical verdicts MAY instead be shown by a pinned re-run of the original control at that task's qualified head with byte-identical output, together with item 3a;
3a. every invariant the pre-correction control enforced other than the over-applied classification, including frozen-object identity, MUST remain enforced on every later candidate of every class, proven by negative fixtures on at least one out-of-class candidate. Any new verifier or test file that the corrected control invokes MUST itself be protected by that control against later change;
4. the correction MUST NOT broaden task scope, reconciliation scope, execution authority, evidence authority, decode authority, scoring authority, comparative-claim authority, product authority, or completion state, and a newly accepted candidate class carries no execution authority. Changing a gate's trigger, trust root, or permissions is permitted only when it moves execution to base-defined code and does not widen token permissions;
5. each pre-correction gate failure MUST be preserved as conflict evidence and MUST NOT be relabeled, suppressed, or rerun-to-green. For each preserved failure the correction MUST prove (a) cause: a deterministic harness evaluates the gate's base-defined program on the candidate and on the same candidate with the declared control bytes reverted, the failure occurs on the former and not on the latter, and the gate is actually evaluated in both runs, because an absent or untriggered gate proves nothing; and (b) non-concealment: because a failing gate stops at its first failing check, every later step of that gate is executed separately from base-pinned code on the candidate and either concludes successfully or fails only with a failure that is itself preserved and proven under this item, and every failing step is executed again on the candidate with only the over-applied classification neutralized and then concludes successfully. The neutralization diff MUST be published byte-exact and pinned by commit SHA. It MAY change only statements whose failure line is a preserved failure. Every check that the resulting control flow skips MUST be executed separately on the candidate and conclude successfully. A failure is the same failure only when the gate, the step, and the exact failure line are identical. Where an annexed path is also an immutable control under Principle XVI, the immutable-control boundary failure whose only failing condition is the declared annexed byte change MAY be preserved under this item, provided that reverting only that blob makes the boundary pass and the list of immutable controls is not changed; Principle XVI is not otherwise invoked. Each preserved failure MUST be individually evidenced and MUST occur before any dependent candidate execution or state transition. A preserved failure that recurs on the post-merge run of the same gate on canonical `main` remains preserved conflict evidence only until the next correction in the same declared lane merges, and MUST be recorded by the reconciliation in item 10;
6. every exact-head gate required by canonical repository authority and applicable to the correction candidate MUST conclude successfully on the exact final head. A gate is required and applicable when the base branch's workflow definitions trigger it for the candidate's event and changed paths, or when it actually runs on the exact head; a required gate that is absent, skipped, pending, cancelled, or failed is not satisfied, except the failures preserved under item 5;
7. a qualifying independent substantive review (Governance item 7) MUST cover the exact final range and resolve all blocking findings before merge;
8. the correction MUST use a guarded normal merge bound to the exact reviewed head, recorded as an explicit owner act;
9. after merge, the actual canonical merge SHA and ancestry MUST be verified, and the corrected control MUST be exercised against that exact canonical state by a deterministic verifier or a dispatched canonical workflow;
10. a separate canonical reconciliation MUST record the correction before dependent work other than a later correction in the same declared lane relies on it. The reconciliation changes only records of the correction (merge SHA, preserved failures, and verifier outputs) and MUST NOT change any authority, freeze, decode, scoring, readiness, task-scope, or completion field, proven by a deterministic diff of those fields against the pre-correction base. It requires a qualifying review. Reconciliations of corrections in one declared lane MAY be combined into a single reconciliation after the lane's last correction. Until that reconciliation merges, no non-correction work may rely on any of those corrections.

This correction authority MUST NOT be used as a substitute for an ordinary required gate. If preservation, cause, non-concealment, or strict non-broadening cannot be demonstrated, the project remains blocked.

**Transitional preservation.** Until the first correction of the B2R16 freeze control under this principle merges, the failure `B2R16_ATTEMPT_003_FREEZE=FAIL: B2R16 actual candidate range scope drift`, reproduced on canonical `edacdf7504302cc91ff7138bc6ac2d391e4df1f4`, MAY be preserved as evidence on exactly two pull requests: the amendment that adopts this principle, and that first freeze correction. Conditions:

1. the amendment changes only `CONSTITUTION.md`, and the freeze correction changes only its declared annexed paths, its new verifier and test files, and its evidence directory;
2. every other applicable check on that pull request concludes successfully; a check that is absent, skipped, pending, cancelled, or failed is not satisfied, except, on the freeze correction only, scope-gate failures preserved under item 5 above;
3. on the amendment, the B2R16 preservation checker `research/000b2-public/verify_b2r16_preservation.py` with SHA-256 `b4ad0f3ef02394e28c982100acb68a719acde0d9a137b62be662871756eefe16`, as published at `a97d596bfc9a027bc6c71747b11d94de14f3e838`, reports `B2R16_FROZEN_OBJECT_PRESERVATION=PASS` on the amendment's head under an isolated interpreter, and its test suite `research/000b2-public/test_b2r16_preservation.py` with SHA-256 `3b144f15d9870877e891d7847384aa058acd73a5c1fc1ab648bb6d1c04c4aae2`, as published at the same commit, passes there; the checker and test bytes are part of this amendment's qualifying review. On the freeze correction: (a) every path that this pinned checker lists as frozen, other than `.github/workflows/000b2-public-b2r16-freeze.yml`, has the same blob and mode as at canonical merge `885307429ec8b1aa0fe173169a8c2918714c06b0`; (b) the preservation checker and test suite that the correction introduces, whose bytes are part of the correction's qualifying review, report `B2R16_FROZEN_OBJECT_PRESERVATION=PASS` and pass on the correction's head under an isolated interpreter; and (c) a `workflow_dispatch` run of the corrected workflow on the correction's exact head concludes successfully, since a trigger defined by the base branch does not run on the correction itself. The qualifying reviewer of each pull request runs or reproduces its checks.

The first freeze correction is pull request #130 or its declared successor. This transitional preservation expires when that first freeze correction merges.

**Frontier sections.** Non-B2 governance pull requests MAY edit only those sections of `specs/CURRENT.md` and `docs/canonical/CURRENT_STATE.md` that a constitutional amendment designates by exact heading as non-B2 sections, plus newly appended sections whose headings that amendment designates; all other bytes of those files remain under benchmark-lane authority, both while ATTEMPT-003 is active and after it completes.

**Ratification of 0.3.0.** The 0.3.0 adoption of this principle merged with its qualifying review waived by the owner. The qualifying review of the 0.4.0 amendment covers the full text of this principle as amended, together with the transitional checker and test bytes named above, and ratifies them. Until that review is recorded on the 0.4.0 pull request, no correction under this principle may merge.

## Governance

1. This constitution is the highest product-governance document in the repository.
2. An implementation that violates a principle requires an explicit constitution amendment, not a hidden exception.
3. Amendments require a dedicated pull request describing motivation, compatibility impact, security/privacy impact, and affected specifications.
4. Semantic versioning applies to this constitution: major for incompatible principle changes, minor for new or materially stronger principles, patch for clarification.
5. ADRs govern durable architectural decisions. Specs govern bounded outcomes. Tasks govern execution order. Evidence governs verified state.
6. When these authorities conflict, the conflict must be resolved explicitly before dependent work proceeds.
7. A review is a qualifying independent review only when the reviewer did not author the change, the review is substantive (it examines the exact final range and states any blocking findings), every blocking finding is resolved before merge, and the review is recorded on the pull request with the exact reviewed head SHA. Qualifying reviewers are: (a) the repository owner personally; (b) a human the owner names for that pull request; or (c) an automated reviewer whose model comes from a different vendor than the model that authored the change, with its model identity, prompt, and output recorded. Local classifiers and reviewers from the author's model vendor may assist but never qualify. Reviews required by Principles XVI and XVII, constitutional amendments, founding-synthesis (000G) decisions, and benchmark-lane merges require a qualifying review; other pull requests require a fresh-context review and the owner's merge approval.