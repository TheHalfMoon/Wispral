# Wispral Constitution

**Version:** 0.3.0  
**Status:** Active  
**Ratified:** 2026-09-01  
**Amended:** 2026-11-08  
**Canonical ratification merge:** `3cbe212bf7202c37ec322f114c0e5486e5218d9b`  
**Canonical 0.3.0 amendment merge:** pending; recorded in the Principle XVII item 8 reconciliation and replaced with the merge SHA by the next patch release

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

## Principle XVII — Fail-closed control deadlocks are resolved explicitly and narrowly

A repository control is **over-applied** when it is fail-closed and its applicability predicate selects and rejects a candidate that lies outside the control's governed scope. The governed scope MUST be quoted verbatim from the canonical text that introduced the control, cited by commit SHA and path, and MUST be the complete recorded scope, not a subset. Where sources conflict, the control's own declaration controls; absent one, the introducing specification, task, or reconciliation controls. A control that rejects a candidate because the candidate lies outside an active task or candidate scope the control was chartered to enforce is applying as intended, not over-applied.

When one or more over-applied controls, alone or together with fail-closed controls applying as intended, make every ordinary candidate unadmittable, the controls are in **deadlock**. This includes the repair of each over-applied control and any canonical reconciliation that would authorize or record that repair. All dependent execution MUST freeze until the deadlock is resolved under this principle.

Principle XVI remains the sole lane for fail-open defects. This principle MUST NOT be used while any reviewer or evidence identifies an unresolved fail-open defect in a control path within the declared repair scope; such a defect MUST first be resolved under Principle XVI. This principle MUST NOT be used as a substitute for an ordinary gate that the repair candidate or its reconciliation can satisfy.

A deadlock repair is authorized only when all of the following hold:

1. **Declared cycle.** Before merge, the repair pull request MUST declare the deadlock cycle. The declaration identifies:
   - the ordered set of over-applied control identities (canonical path plus required-check context);
   - the intended-scope controls participating in the cycle;
   - the canonical authority base.

   The declaration MUST be recorded in the pull request and in the item 8 reconciliation. Renaming, splitting, or relocating a control does not create a new control or a new cycle.
2. **Exact scope.**
   - The repair MUST repair every over-applied control in the declared cycle and nothing else.
   - Its changed paths are limited to the implementations of those controls, plus new or modified deterministic test fixtures or verifier scripts located within each repaired control's verification location.
   - It MUST NOT add or modify any workflow trigger, branch-protection or ruleset required-check mapping, or other control. The implementation of a repaired control is not a required-check mapping.
   - The declared changed-path scope MUST equal exactly the set of paths changed by the pull request, verified mechanically against the diff.
   - The pull request MUST enumerate every assertion it removes or weakens. No assertion may be removed or weakened for a candidate within the governed scope.
3. **Preserved guarantees.** The repair MUST preserve every guarantee the original control provides for candidates within its governed scope:
   - frozen-object identity;
   - every commit recorded as PASS under the original control still passes the repaired control, or is recorded as out of scope with the authority cited;
   - fail-closed rejection of each malformed class the original control rejected.

   The repair MUST NOT broaden task scope, reconciliation scope, execution authority, evidence authority, decode authority, scoring authority, comparative-claim authority, product authority, or completion state.
4. **Disclosure and evidence.** The repair pull request MUST describe:
   - the declared cycle, with exact pull requests, workflow names, job identifiers and failure strings;
   - the canonical authority base and the changed-path scope;
   - compatibility impact, security and privacy impact, and affected specifications.

   It MUST include deterministic evidence that the repaired control:
   - accepts its valid candidate class;
   - for each enumerated malformed class, rejects at least one in-scope malformed candidate;
   - still selects every candidate within its governed scope;
   - now passes on canonical main at the authority base.

   That evidence MUST be generated by the original control at the authority base, or independently by a reviewer using pinned tooling. Evidence produced solely by scripts introduced in the repair is insufficient.
5. **Preserved non-successes.** A non-success may be preserved only if its sole failing condition is one of the following:
   - (a) an over-applied control in the declared cycle rejecting the repair, with the exact failure string recorded under item 4, solely because of the declared over-application;
   - (b) an intended-scope control in the declared cycle rejecting the repair's declared paths, solely because they lie outside the active candidate scope.

   A rejection of canonical main is defect evidence, not a preserved non-success.

   Each preserved non-success MUST:
   - be recorded individually with its job identifier and failure string;
   - be shown to contain no other failing condition, by its full log or by an independent run of every remaining step and condition of that check;
   - occur before any dependent candidate execution or state transition.

   It MUST NOT be relabeled, suppressed, rerun-to-green, or counted as a successful gate. No other non-success category is permitted.
6. **All other gates.** Every other exact-head gate required by canonical repository authority and applicable to the repair candidate MUST conclude successfully on the exact final repair head. A required gate that is absent, skipped, pending, cancelled, or failed is not satisfied.
7. **Review and merge.**
   - A fresh independent substantive review MUST cover the exact final repair range.
   - The review MUST verify the governed-scope citation, the over-application determination and the equality of the diff with the declared scope.
   - All blocking findings MUST be resolved before merge.
   - The repair MUST use a guarded normal merge bound to the exact reviewed head.
8. **Verification and reconciliation.**
   - After merge, the actual canonical merge SHA and ancestry MUST be verified.
   - Each repaired control MUST be exercised against that exact canonical state by a deterministic verifier or canonical workflow.
   - A separate canonical reconciliation MUST record the repair and the declared cycle before dependent execution resumes.
   - The reconciliation MUST satisfy every required gate, including the repaired controls. The only exception is a non-success preserved on the same conditions as item 5(b), where an intended-scope control rejects the reconciliation solely because its paths lie outside the active candidate scope.
   - If the reconciliation cannot be admitted under these conditions, the cycle is incomplete and no dependent execution may resume.
9. **Single use.**
   - Per declared cycle, exactly one repair pull request may merge with preserved non-successes, together with that cycle's single reconciliation under item 8. No other candidate may rely on them.
   - A control already repaired under this principle MUST NOT be repaired under it again. Any further defect in that control requires Principle XVI or a constitutional amendment.
   - Each use MUST be recorded in canonical reconciliation with references to all prior uses.

This principle grants no authority to merge any candidate with an unpreserved or unrelated non-success. If strict preservation cannot be demonstrated under these conditions, the project remains blocked.

**Transitional provision (0.3.0).** This provision is self-executing and takes effect upon the merge it authorizes. The pull request adopting this principle is itself rejected by the deadlock it addresses and cannot satisfy this principle. It may merge only if:

- it changes `CONSTITUTION.md` alone and satisfies Governance item 3;
- each non-success is preserved individually under the conditions of item 5, and is shown to fail solely on the over-applied B2R16 freeze verification or on B2R17 intended-scope rejection of `CONSTITUTION.md`;
- every other required exact-head gate succeeds;
- a fresh independent substantive review covers the exact final range with no unresolved blocking finding;
- it uses a guarded normal merge bound to the reviewed head.

This merge is not a use of item 9 and does not consume the single repair pull request of the cycle it addresses. That cycle closes only when the item 8 reconciliation records its repair. This provision authorizes no other merge, is not precedent, and expires on that merge. The merge SHA MUST be recorded in the item 8 reconciliation of the first use of this principle.

## Governance

1. This constitution is the highest product-governance document in the repository.
2. An implementation that violates a principle requires an explicit constitution amendment, not a hidden exception.
3. Amendments require a dedicated pull request describing motivation, compatibility impact, security/privacy impact, and affected specifications.
4. Semantic versioning applies to this constitution: major for incompatible principle changes, minor for new or materially stronger principles, patch for clarification.
5. ADRs govern durable architectural decisions. Specs govern bounded outcomes. Tasks govern execution order. Evidence governs verified state.
6. When these authorities conflict, the conflict must be resolved explicitly before dependent work proceeds.