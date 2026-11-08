# Re-review of PR #124 at `e7064c78`

- Date: 2026-11-08.
- Reviewer: Claude Opus 5.5, independent of the Codex mission.
- Scope: the repair commits `0dc99fe` and `e7064c7` made in response to [INDEPENDENT_REVIEW.md](INDEPENDENT_REVIEW.md), plus PR #126.
- Status: this is a planning review only. It is not a merge, security or release approval.

## Verdict

**APPROVE FOR PLANNING**, conditional on N1 below, which this branch adds to the plan text.

The governance sequence cannot execute until the founder makes the N1 decision. N1 is a decision the founder must make, not a defect in the plan content.

## Disposition of earlier findings

Labels used in the "Method" column:

- **REPRODUCED**: I re-ran the check on this machine.
- **SOURCE/DOC_READ**: I read the source or document.
- **GH_READ**: I read the result from GitHub.

### MUST FIX

| ID | Status | Method | Evidence |
| --- | --- | --- | --- |
| M1 | Repaired in #126 (draft, not merged) | GH_READ | `verify-b2r16-freeze` passes on #126 head `a97d596b`. However, see N1. |
| M2 | Resolved as a proposal | REPRODUCED | `packet-authorities.json` has 26 packets. All `requires` references resolve, the graph is acyclic, and 0 packets are READY. The founding-chain table covers 000A–000G and B2R17. |
| M3 | Resolved as a proposal | DOC_READ | The governance proposal handles the AGENTS mission negation, all 14 anti-roadmap items (grouped into 11 rows) and A12 per product. |
| M4 | Resolved | REPRODUCED | `fit_input_boundary_probe.py` returns PASS against the pinned `fit_planner.py` and its four donor golden fixtures. |
| M5 | Resolved as a proposal | DOC_READ | The architecture now has a "One owner per responsibility" table. Q-07 names INK-I10 as the sole owner and avoids wrapping it in Sentrdel. |

### SHOULD IMPROVE

| ID | Status | Method | Evidence |
| --- | --- | --- | --- |
| S1 | Adopted | DOC_READ | Adopted as conditional fork leads with F-SIDE-0 and F-STUDIO-0 baselines. Fork baselines are honestly NOT_RUN. |
| S2–S6 | Adopted | DOC_READ | The architecture, Klaint K-00 and K13–K15, and `WISPRAL_MODEL_ROUTING_CONTRACTS.md` are present. |
| S7 | Adopted | DOC_READ | The feature matrix now carries a coarse backlog. |
| S8 | Adopted | DOC_READ | The review file was renamed to `INTERNAL_CONSISTENCY_REVIEW.md`. |

### OPTIONAL

| ID | Status | Method | Evidence |
| --- | --- | --- | --- |
| O1–O4 | Adopted | REPRODUCED | `validate_research.mjs` reports `failures: []`, and `test_research_schema.mjs` reports 3 PASS. |

## N1 (MUST FIX, new): the control lanes are deadlocked

Status: GH_READ. Observed on 2026-11-08 and undocumented in both #124 and #126.

### What GitHub shows

- **#120 (B2R17).** This is the sole authorized execution unit. Its head is `85fe8102`. `verify-b2r16-freeze` fails there; its other 6 checks pass.
- **#126, Trusted PR Gate.** Job `119240340129` of `000B2 Public Corpus ATTEMPT-003 Trusted PR Gate` reports `TRUSTED_PR_GATE=FAIL: B2R17 candidate path scope violation`.
- **#126, Recovery boundary.** Job `119240337239` of `000B2 Public Corpus ATTEMPT-003 Recovery` reports `TRUSTED_BOUNDARY=FAIL: B2R17 task-candidate path scope violation`.
- **Paths covered by those gates.** They watch `.github/workflows/000b2-public-*.yml`, `research/000b2-public/**`, `specs/CURRENT.md` and `docs/canonical/CURRENT_STATE.md`. So a canonical readiness PR that authorizes #126 would be rejected the same way.

### Why this is a deadlock

- B2R17 cannot pass while the freeze check over-applies.
- The fix for that over-application (#126) cannot pass while B2R17's single-candidate scope gates stand.
- No ordinary lane exists. Principle XVI requires a fail-open defect, and none is demonstrated.

### Affected work packets

G-00, G-01, and everything downstream of them.

### Remedy

This branch adds the remedy to the plan text:

- [WISPRAL_GOVERNANCE_AMENDMENT_PROPOSAL.md](../../../docs/strategy/WISPRAL_GOVERNANCE_AMENDMENT_PROPOSAL.md), section "Control-lane deadlock".
- The W0 section of [WISPRAL_MASTER_PLAN_REBUILT.md](../../../docs/strategy/WISPRAL_MASTER_PLAN_REBUILT.md).

The founder chooses one of two options:

1. **Preferred:** a narrow deadlock lane that mirrors Principle XVI's rigor.
2. **Alternative:** a declared second B2R17-scope candidate.

The proposed order is:

1. Lane amendment.
2. #126.
3. #120 re-run and reconciliation.
4. Scope amendment.
5. #124.

### Acceptance test

- The lane amendment preserves the listed red results individually.
- #126 then merges with every other applicable gate green.
- On canonical `main`, `verify-b2r16-freeze` passes on a no-op PR.
- #120's freeze check passes on re-run without any byte change to the frozen B2R17 evidence.

## Checks run

| Check | Result |
| --- | --- |
| `validate_research.mjs` | PASS after refreshing the index with the bundle's own `refresh_evidence_index.mjs` (only the two edited strategy docs' hashes changed) |
| `test_research_schema.mjs` | PASS |
| Packet-graph integrity check | PASS |
| `fit_input_boundary_probe.py` | PASS |
| GitHub check states for #120, #124 and #126 | Read from GitHub |

## Checks not run

- The #126 local test suite.
- Donor builds, fork baselines, and all audio, native, provider, tenant and telephony tests.
