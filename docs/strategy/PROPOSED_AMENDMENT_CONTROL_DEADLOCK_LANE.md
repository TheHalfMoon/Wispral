# Proposed constitutional amendment: fail-closed control deadlock lane

**Status: SUPERSEDED — NOT ADOPTED.** Canonical `main` adopted a different Principle XVII through #129 (merge `8d52a45`). Draft PR #127 was returned to draft. This file is retained as review history only.

**Original status: PROPOSED DRAFT — NOT RATIFIED.** This is the exact text for the preferred N1 option in the [governance proposal](WISPRAL_GOVERNANCE_AMENDMENT_PROPOSAL.md#control-lane-deadlock-opus-re-review-n1). Adopting it requires a dedicated amendment PR and the founder's explicit decision.

Nothing in this file changes `CONSTITUTION.md`.

## Amendment metadata

- **Proposed version:** 0.3.0 (MINOR). The amendment adds a narrowly bounded procedure. It does not weaken any existing principle.
- **Canonical base to target:** current `main`. At drafting time this was `edacdf7504302cc91ff7138bc6ac2d391e4df1f4`; re-read `main` before opening the PR.
- **Changed path:** `CONSTITUTION.md` only. The change is a new Principle XVII plus the version and amendment-date lines.

## Motivation

Two kinds of repository control currently block each other:

- The B2R16 freeze verifier over-applies: it fails on canonical `main` and on every later pull request.
- The ATTEMPT-003 B2R17 scope gates reject any change outside B2R17's candidate scope.

The only authorized execution unit, #120, fails the first control. The repair for that control, #126, fails the second. A readiness reconciliation that authorized #126 would fail both.

Principle XVI covers only fail-open defects, and none is demonstrated here. The constitution therefore has no lane that resolves the conflict. Every option currently available is a hidden exception, which Governance clause 2 forbids.

## Compatibility impact

- No principle is removed or weakened.
- Principle XVI keeps sole authority over fail-open repairs.
- Frozen benchmark evidence, task scopes, scoring authority and product authority are unchanged.

## Security and privacy impact

None. The lane only admits changes that preserve or strengthen fail-closed verification.

## Affected specifications

- No specification is affected by the amendment itself.
- The admitted repair (#126) touches only `.github/workflows/000b2-public-b2r16-freeze.yml` and new verifier files under `research/000b2-public/`.

## Proposed text

> ## Principle XVII — Fail-closed control deadlocks are resolved explicitly and narrowly
>
> A repository control MAY be shown to be fail-closed but over-applied: it rejects candidates it was never intended to govern, while preserving every guarantee for the candidates it does govern. When two or more such controls make every ordinary candidate unadmittable, including the repair of either control and any canonical reconciliation that would authorize that repair, the controls are in a deadlock. All dependent execution MUST freeze until the deadlock is resolved under this principle.
>
> Principle XVI remains the sole lane for fail-open defects. This principle MUST NOT be used where a fail-open defect is alleged, nor as a substitute for an ordinary gate that a candidate can satisfy.
>
> A deadlock repair is authorized only when all of the following hold:
>
> 1. The repair is limited to the exact control paths whose over-application causes the deadlock, plus new verification files the repair requires.
> 2. The repair MUST preserve every guarantee the original control provides for its intended candidates. That includes frozen-object identity, historical PASS reproducibility and fail-closed rejection of the malformed classes the original control rejected. The repair MUST NOT broaden task scope, reconciliation scope, execution, evidence, decode, scoring, comparative-claim or product authority, or completion state.
> 3. The repair PR MUST describe:
>    - the deadlock cycle, with exact PRs, workflow names, job IDs and failure strings;
>    - the exact canonical base;
>    - the exact changed-path scope;
>    - deterministic positive and negative evidence that the repaired control accepts its intended valid candidate class and rejects the malformed class.
> 4. Each pre-repair failure caused solely by the declared over-application MUST be preserved individually as conflict evidence. Such a failure MUST NOT be relabelled, suppressed, rerun-to-green or counted as a successful gate.
> 5. Every other gate required by canonical repository authority and applicable to the repair MUST conclude successfully on the exact final repair head. Absent, skipped, pending, cancelled or failed results do not satisfy a gate. The only permitted non-successes are the preserved results from item 4.
> 6. A fresh, independent, substantive review MUST cover the exact final repair range and resolve all blocking findings before merge.
> 7. The repair MUST use a guarded normal merge bound to the exact reviewed head.
> 8. After merge:
>    - the actual canonical merge SHA and its ancestry MUST be verified;
>    - each repaired control MUST be exercised against that exact canonical state;
>    - a separate canonical reconciliation MUST record the repair before dependent execution resumes.
>    The reconciliation is itself an ordinary candidate and MUST pass the repaired controls.
> 9. Each deadlock repair is a single use for its declared cycle. A new deadlock requires a new, separately evidenced repair PR.

## Required evidence for the first use (#126)

Run all of this against #126's exact final head:

1. The preserved red results:
   - #124 run `39588472485` (`verify-b2r16-freeze`);
   - #120 `verify-b2r16-freeze`;
   - #126 job `119240340129`, `TRUSTED_PR_GATE=FAIL: B2R17 candidate path scope violation`;
   - #126 job `119240337239`, `TRUSTED_BOUNDARY=FAIL: B2R17 task-candidate path scope violation`.
2. #126's own preservation tests:
   - the historical verifier still reports PASS at `ac9f7ce993aec33e6c6436cce4efd85394a97f35`;
   - the 16 frozen-path mutation cases reject;
   - the 48 deletion, mode and symlink cases reject;
   - forged-script and import-shadowing cases reject.
3. All other applicable checks green at #126's final head.
4. A fresh independent review of #126's exact range.

## Acceptance after adoption

- A no-op pull request against the new canonical `main` passes `verify-b2r16-freeze`.
- #120 re-runs `verify-b2r16-freeze` to success with no byte change to its frozen B2R17 evidence. Every check that previously passed on #120 still passes.
- The red results listed above remain visible in the canonical reconciliation record.

## Rejected alternatives

| Alternative | Reason rejected |
| --- | --- |
| Merge with red gates, as #118 did | Hidden exception; violates Governance clause 2 and AGENTS §3 |
| Add a paths filter, a skip or `continue-on-error` | Suppression; fails Principle XVI item 4 by analogy and AGENTS §3 |
| Use Principle XVI | Requires a demonstrated fail-open defect; none exists |
| Declare #126 a second B2R17-scope candidate | Workable, but widens a task scope, which this amendment avoids. It remains the fallback option if the founder declines this text |
