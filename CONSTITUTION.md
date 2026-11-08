# Wispral Constitution

**Version:** 1.0.0
**Status:** Active  
**Ratified:** 2026-09-01  
**Amended:** 2026-11-08  
**Canonical ratification merge:** `3cbe212bf7202c37ec322f114c0e5486e5218d9b`

## Preamble

Wispral makes voice a trustworthy interface for writing, audio production, and interaction with independent agents. It is one platform with three products that share one authority, provenance, and resource core:

- **WisprSide**: cross-application dictation, spoken writing and editing, and optional control of independent developer agents;
- **WisprStudio**: voice production, including authorized voice cloning, synthesis, editing, and dubbing;
- **Klaint**: customer dialogue agents with bounded tools, channels, and human handoff.

These names are final founder selections; trademark, domain, and store clearance is not asserted. Each product should let a person speak, think aloud, interrupt, steer, inspect, correct, approve, and recover while preserving the authority boundaries of the systems it acts on.

The project optimizes for durable usefulness, interoperability, trust, speed, and open evidence. Popularity is a desired consequence of exceptional utility, not a substitute for it.

## Principle I — Platform and control plane, not compulsory proprietary intelligence

Wispral MUST remain a modular platform around replaceable speech, model, dialogue, and agent implementations. A useful local core MUST NOT require a Wispral-owned foundation model, coding agent, IDE, or hosted reasoning service.

Control of independent coding agents remains a supported direction of WisprSide, as an optional capability; it is neither removed nor required by any product.

Product-, agent-, engine-, and vendor-specific adapters MAY improve compatibility but MUST remain outside the portable core contracts.

## Principle II — Speech is evidence, not authority by default

Raw audio, transcripts, interpreted intent, resolved repository entities, and authorized actions are distinct states.

Wispral MUST NOT silently transform ambiguous or tentative speech into consequential authority. The system MUST preserve enough provenance to explain what was heard, what was resolved, what was interpreted, and what was sent to an agent.

## Principle III — Interruptibility is a first-class primitive

A voice interface that cannot be interrupted cannot be a trustworthy control plane.

Cancellation, barge-in, steering, pause, denial, and recovery MUST be designed as core runtime semantics rather than UI conveniences added after execution.

## Principle IV — Command and context are different

Wispral MUST support the product distinction between speech intended to cause action and speech intended to provide context, exploration, preference, or tentative reasoning.

The project MAY evolve the exact interaction mechanism, but it MUST NOT assume that every spoken utterance is an executable command.

## Principle V — Bounded domain context improves meaning

Wispral SHOULD use bounded, explicitly scoped context to improve interpretation. Repository context (paths, symbols, package names, flags, branches, tests, and other developer entities) is one domain; the target application, script or project metadata, and tenant-authorized knowledge are others. Each domain is scoped and authorized separately.

Raw text, selected context, and interpretation MUST remain distinct. Context resolution MUST remain inspectable, confidence-aware, bounded, and reversible, and MUST NOT become a hidden exfiltration channel. A low-confidence binding MUST NOT be hidden behind polished text.

## Principle VI — Agent and protocol neutrality

No single commercial agent, model vendor, editor, speech provider, or proprietary protocol may become necessary for the core workflow.

Open protocols SHOULD be preferred when they provide the required semantics. Compatibility fallbacks MAY exist, but protocol-specific behavior MUST not leak into the portable product contract without explicit justification.

## Principle VII — Local-first, cloud-optional

A useful core path MUST be possible without a Wispral account or mandatory Wispral-hosted service.

Cloud speech, model, synchronization, or enterprise services MAY be supported as optional adapters. Their failure MUST NOT silently weaken privacy, authorization, or evidence guarantees.

Local dictation and local project workflows MUST have useful account-free paths. Enterprise channels and cloud services are optional, separately declared deployments; this principle does not imply that telephone, messaging, or CRM channels can operate offline, and no hidden fallback between deployments is permitted.

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
3. deterministic evidence executed from trusted code (base-pinned, hash-verified, run under an isolated interpreter) MUST show that detection on the authorized class is preserved in full: identical verdicts on an in-class corpus that includes every previously rejected malformed candidate, plus at least one negative fixture for every rejecting branch of the corrected control. The in-class corpus MUST be listed in a manifest pinned by SHA-256. For a candidate class whose task has already merged, identical verdicts MAY instead be shown by a pinned re-run of the original control at that task's qualified head with byte-identical output, together with item 3a and negative fixtures showing that the corrected control rejects every new candidate of that closed class;
3a. every invariant the pre-correction control enforced other than the over-applied classification, including frozen-object identity, MUST remain enforced on every later candidate of every class, proven by negative fixtures on at least one out-of-class candidate. Any new verifier or test file that the corrected control invokes MUST itself be protected by that control against later change;
4. the correction MUST NOT broaden task scope, reconciliation scope, execution authority, evidence authority, decode authority, scoring authority, comparative-claim authority, product authority, or completion state, and a newly accepted candidate class carries no execution authority. Changing a gate's trigger, trust root, or permissions is permitted only when it moves execution to base-defined code, does not widen token permissions, does not expose secrets, and does not execute candidate-supplied code in a privileged context;
5. each pre-correction gate failure MUST be preserved as conflict evidence and MUST NOT be relabeled, suppressed, or rerun-to-green. For each preserved failure the correction MUST prove (a) cause: a deterministic harness evaluates the gate's base-defined program on the candidate and on the same candidate with the declared control bytes reverted, the failure occurs on the former and not on the latter, and the gate is actually evaluated in both runs, because an absent or untriggered gate proves nothing; and (b) non-concealment: because a failing gate stops at its first failing check, every later step of that gate is executed separately from base-pinned code on the candidate and either concludes successfully or fails only with a failure that is itself preserved and proven under this item, and every failing step is executed again on the candidate with only the over-applied classification, and any immutable-control boundary failure preserved under this item, neutralized, and then concludes successfully. The neutralization diff MUST be published byte-exact and pinned by commit SHA. It MAY change only statements whose failure line is a failure preserved under this item. Every check that the resulting control flow skips MUST be executed separately on the candidate and conclude successfully. A failure is the same failure only when the gate, the step, and the exact failure line are identical. Where an annexed path is also an immutable control under Principle XVI, the immutable-control boundary failure whose only failing condition is the declared annexed byte change MAY be preserved under this item, provided that a deterministic diff shows every byte of that blob outside the annexed scope-classification steps or functions is identical to base, that reverting only that blob makes the boundary pass, and that the list of immutable controls is not changed; Principle XVI is not otherwise invoked. Each preserved failure MUST be individually evidenced and MUST occur before any dependent candidate execution or state transition. A preserved failure that recurs on the post-merge run of the same gate on canonical `main` remains preserved conflict evidence only until the earlier of the next correction in the same declared lane or that lane's reconciliation merges; the reconciliation MUST show that gate passing on canonical `main`. It MUST be recorded by the reconciliation in item 10;
6. every exact-head gate required by canonical repository authority and applicable to the correction candidate MUST conclude successfully on the exact final head. A job is required and applicable when the base branch's workflow definitions trigger its workflow for the candidate's event and changed paths and its base-defined job condition evaluates true for that event, or when it actually runs on the exact head. A job skipped because its base-defined trigger, path filter, or job condition does not select the candidate is not applicable, and that trigger, filter, or condition MUST be quoted in the evidence. This definition also governs the transitional conditions; a required gate that is absent, skipped, pending, cancelled, or failed is not satisfied, except the failures preserved under item 5;
7. a qualifying independent substantive review (Governance item 7) MUST cover the exact final range and resolve all blocking findings before merge;
8. the correction MUST use a guarded normal merge bound to the exact reviewed head, recorded as an explicit owner act;
9. after merge, the actual canonical merge SHA and ancestry MUST be verified, and the corrected control MUST be exercised against that exact canonical state by a deterministic verifier or a dispatched canonical workflow;
10. a separate canonical reconciliation MUST record the correction before dependent work other than a later correction in the same declared lane relies on it. The reconciliation changes only records of the correction (merge SHA, preserved failures, and verifier outputs) and MUST NOT change any authority, freeze, decode, scoring, readiness, task-scope, or completion field, proven by a deterministic diff of those fields against the pre-correction base. It requires a qualifying review. Reconciliations of corrections in one declared lane MAY be combined into a single reconciliation after the lane's last correction. Until that reconciliation merges, no work other than a later correction in the same declared lane and that reconciliation itself may rely on any of those corrections. A declared lane is a closed list of correction pull requests and their annexed paths, stated by number in the first correction's description and confirmed by the owner on that pull request, or declared by a constitutional amendment. Constitution 0.4.0 declared the B2R16/ATTEMPT-003 lane: #130, which merged under 0.3.0 as `5879c43` and corrected annex item 1, and one further correction covering annex items 3 and 4, which the owner confirmed as #135 (merged as `d78ecb5`). That lane is complete and was reconciled as Reconciliation 002 (`bedf376`). Extending a lane or declaring a new one requires a constitutional amendment.

This correction authority MUST NOT be used as a substitute for an ordinary required gate. If preservation, cause, non-concealment, or strict non-broadening cannot be demonstrated, the project remains blocked.

**Transitional preservation.** Until the first correction of the B2R16 freeze control under this principle merges, the failure `B2R16_ATTEMPT_003_FREEZE=FAIL: B2R16 actual candidate range scope drift`, reproduced on canonical `edacdf7504302cc91ff7138bc6ac2d391e4df1f4`, MAY be preserved as evidence on exactly two pull requests: the amendment that adopts this principle, and that first freeze correction. Conditions:

1. the amendment changes only `CONSTITUTION.md`, and the freeze correction changes only its declared annexed paths, its new verifier and test files, and its evidence directory;
2. every other applicable check on that pull request concludes successfully; a check that is absent, skipped, pending, cancelled, or failed is not satisfied, except, on the freeze correction only, scope-gate failures preserved under item 5 above;
3. on the amendment, the B2R16 preservation checker `research/000b2-public/verify_b2r16_preservation.py` with SHA-256 `b4ad0f3ef02394e28c982100acb68a719acde0d9a137b62be662871756eefe16`, as published at `a97d596bfc9a027bc6c71747b11d94de14f3e838`, reports `B2R16_FROZEN_OBJECT_PRESERVATION=PASS` on the amendment's head under an isolated interpreter, and its test suite `research/000b2-public/test_b2r16_preservation.py` with SHA-256 `3b144f15d9870877e891d7847384aa058acd73a5c1fc1ab648bb6d1c04c4aae2`, as published at the same commit, passes when run in a checkout of that commit; the checker and test bytes are part of this amendment's qualifying review. On the freeze correction: (a) every path that this pinned checker lists as frozen, other than `.github/workflows/000b2-public-b2r16-freeze.yml`, has the same blob and mode as at canonical merge `885307429ec8b1aa0fe173169a8c2918714c06b0`; (b) the preservation checker and test suite that the correction introduces, whose bytes are part of the correction's qualifying review, report `B2R16_FROZEN_OBJECT_PRESERVATION=PASS` and pass on the correction's head under an isolated interpreter; and (c) a `workflow_dispatch` run of the corrected workflow on the correction's exact head concludes successfully, since a trigger defined by the base branch does not run on the correction itself. The qualifying reviewer of each pull request runs or reproduces its checks.

The first freeze correction is pull request #130. It merged as `5879c43c7a389bd460955f2e181e8bd70f0ecee5` on 2026-11-08, and this transitional preservation expired then; the text above is retained as the record of what applied to #129 and #130.

**Frontier sections.** Non-B2 governance pull requests MAY edit only those sections of `specs/CURRENT.md` and `docs/canonical/CURRENT_STATE.md` that a constitutional amendment designates by exact heading as non-B2 sections, plus newly appended sections whose headings that amendment designates; all other bytes of those files remain under benchmark-lane authority, both while ATTEMPT-003 is active and after it completes.

**Designation (1.0.0).** This amendment designates exactly these non-B2 sections:

- in `docs/canonical/CURRENT_STATE.md`, the sections headed exactly `## Current product thesis`, `## Current architecture posture`, `## Explicit non-claims`, and `## Product-code gate`;
- in `specs/CURRENT.md`, the sections headed exactly `## Remaining founding children` and `## Product-code gate`;
- in either file, new sections that a pull request appends at the end of the file, after every section of its base, each with a heading line that begins `## Platform frontier`. Once merged, an appended section is an existing section: it is not editable unless an amendment designates it.

A section runs from its `## ` heading line to the line before the next `## ` heading, or to the end of the file. Text before the first heading, the order of existing headings, and every other section remain under benchmark-lane authority. A designated section MUST NOT contain the B2 lane markers that the B2 scope gates reject there. Designation lets non-B2 governance pull requests edit these sections; it grants no authority beyond what this constitution and the active specification grant. In particular, editing a `## Product-code gate` section cannot open product code, which requires a founding-synthesis (000G) decision.

**Ratification of 0.3.0.** The 0.3.0 adoption of this principle merged with its qualifying review waived by the owner. The qualifying review of the 0.4.0 amendment covers the full text of this principle as amended, together with the transitional checker and test bytes named above, and ratifies them. That review MUST be recorded on the exact merged head before merge and MUST NOT be waived. #130 merged under 0.3.0 before this amendment, with its own qualifying review recorded on #130, and is not reopened. Item 3a applies to the B2R16 freeze checker and tests that #130 introduced from the merge of this amendment, and the lane's further correction MUST bring them under it.

## Principle XVIII — Voice and asset consent is bound, visible, and revocable

Personal voice recordings, voice references, and cloned or synthesized voices MUST be bound to a subject, a purpose, the artifacts produced, and a revocation state. Work queued under a consent that has since been revoked or has expired MUST NOT run. Recording and retention MUST be visible to the subject.

Rights in models, tokenizers, datasets, and voice or media assets are qualified separately from source-code grants; a code grant never implies them. Wispral MUST NOT promise that outputs already delivered to third parties can be recalled after revocation.

The founder's confidential source-code grants remain confirmed and private; no confidential document upload is required by this principle.

## Principle XIX — Tenant and action authority is server-derived and deterministic

Customer, tenant, account, channel, and credential authority MUST derive from authenticated server context and deterministic policy, never from identifiers supplied by a model or by customer text.

External side effects MUST use scoped credentials and idempotency, and an action whose outcome is unknown MUST be reconciled explicitly rather than blindly retried. Guidelines, model confidence, and scanners are evidence, not authority (Principle VIII).

## Principle XX — Copy first, qualify always

Qualified reuse of authorized source precedes new implementation. Every adopted source MUST record its immutable provenance (upstream, revision, and paths), its actual dependency closure, its required notices and attribution, its mismatches with Wispral contracts, and its tests. Smaller modules or services are preferred to duplicating complete applications, and a decision to build something new MUST be justified against the qualified donor options.

Reuse MUST NOT weaken any correctness, security, consent, tenant, or rights gate, and renaming adopted code never removes original authorship or notices.

## Governance

1. This constitution is the highest product-governance document in the repository.
2. An implementation that violates a principle requires an explicit constitution amendment, not a hidden exception.
3. Amendments require a dedicated pull request describing motivation, compatibility impact, security/privacy impact, and affected specifications.
4. Semantic versioning applies to this constitution: major for incompatible principle changes, minor for new or materially stronger principles, patch for clarification.
5. ADRs govern durable architectural decisions. Specs govern bounded outcomes. Tasks govern execution order. Evidence governs verified state.
6. When these authorities conflict, the conflict must be resolved explicitly before dependent work proceeds.
7. A review is a qualifying independent review only when the reviewer did not author the change, the review is substantive (it examines the exact final range and states any blocking findings), every blocking finding is resolved before merge, and the review is recorded on the pull request with the exact reviewed head SHA. Qualifying reviewers are: (a) the repository owner personally; (b) a human the owner names for that pull request; or (c) an automated reviewer whose model comes from a different vendor than the model that authored the change, with its model identity, prompt, and output recorded. Local classifiers and reviewers from the author's model vendor may assist but never qualify. Reviews required by Principles XVI and XVII, constitutional amendments, founding-synthesis (000G) decisions, and benchmark-lane merges require a qualifying review; other pull requests require a fresh-context review and the owner's merge approval.
8. The `claim_guards` of the B2 benchmark lane's readiness file, including `product_code_authorized=false`, are claims of that lane only. They neither grant nor withhold product-code authority outside that lane. Product-code authority is governed by the product-code gate and the founding synthesis (000G): until a 000G decision selects a bounded implementation Grain and that Grain satisfies readiness, no product code is authorized.