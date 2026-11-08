# Master plan completion and governance execution: final report (2026-11-09)

This report covers the ten items requested in the founder's brief. Canonical `main` is `04d12e2134dc19df7635dd0ffc1df5a2ca07443d`.

Every merge listed below:

- was a guarded normal merge bound to the reviewed head (`--match-head-commit`), recorded as an owner act quoting the founder's instruction verbatim;
- was verified after merge, including that its tree equals the reviewed head.

## 1. #133 — Constitution 0.4.0

| Item | Value |
| --- | --- |
| Reviewed head | `73fcfd8` |
| Merge | `76fe651` |
| Reconciliation with 0.3.0 | The transitional clause was marked expired at #130; #130 was not reopened; the lane was declared |
| Qualifying review | NVIDIA Nemotron 3.5 Super: APPROVE, 0 blocking. A DeepSeek attempt that hit the 429 free-usage limit is disclosed. |
| Ratification | The review ratified 0.3.0's waived review |

## 2. C2 — #135

| Item | Value |
| --- | --- |
| Change | Non-successor class for the B2 scope gates (annex items 3 and 4) |
| Reviewed head | `64a7bb7`; merge `d78ecb5` |
| Evidence | A3 boundary `PASS`; 114-candidate in-class corpus with verdicts preserved; neutralized run; skipped checks run separately |
| Review | Nemotron, 2 rounds, APPROVE |
| Lane | Confirmed complete: #130 and #135 |

## 3. Reconciliation R — #136

| Item | Value |
| --- | --- |
| Reviewed head | `ba73499`; merge `bedf376` |
| What it records | Reconciliation 002: the G1 waivers, C1, C2, and #118 as an exception, with fresh evidence |
| Owner decision | The B2R17 frontier stands |
| Records only | `r_field_diff.py` `PASS` |
| Review | Nemotron, APPROVE |

**NOOP:**

- probes #137 and #138 were closed unmerged, and the frontier probe passed both B2 gates;
- the recovery gate's push run on F's merge passed (run 42519309297), closing the last criterion.

## 4. Exact-head CI and review evidence

| PR | Exact-head checks | Qualifying or fresh review |
| --- | --- | --- |
| #133 | freeze pass | Nemotron APPROVE |
| #135 | freeze, methodology and legacy pass; trusted-PR and recovery fail only as preserved (runs 42498837525, 42498837653) | Nemotron R1 REQUEST_CHANGES → R2 APPROVE |
| #136 | freeze pass | Nemotron APPROVE (26 tool calls, disclosed) |
| #139 (G2) | freeze pass (run 42513314652) | Nemotron R1–R4 APPROVE; author mistake in round 3 disclosed |
| #140 (F) | 19 pass, 0 fail, including both B2 gates (runs 42515395288, 42515395284) | Nemotron APPROVE (37 tool calls, disclosed) |
| #141 (CORE-00) | freeze pass (run 42523357874) | Nemotron R1–R2 APPROVE |
| #142 (ST-D00b) | freeze pass (run 42524669345) | Nemotron APPROVE |
| #143, #144 | freeze pass | fresh-context review, APPROVE (#143 after one REQUEST_CHANGES round) |

Each review is recorded on its pull request with the reviewer identity, prompts, verbatim output and exact head SHA. Every reviewer side-effect scan found no write to GitHub.

## 5. G2 — Constitution 1.0.0 (#139)

| Item | Value |
| --- | --- |
| Reviewed head | `a97b95b`; merge `4c16b7e`; founder ratification "Merge #139" |
| What it establishes | The platform thesis (WisprSide, WisprStudio, Klaint); Principles XVIII (consent), XIX (tenant and action authority) and XX (copy first) |
| Frontier designation | The frontier sections are designated by exact heading |
| Governance item 8 | `product_code_authorized` scopes the B2 lane only |
| Subordinate documents | The A12 and anti-roadmap dispositions; the 000C–000G re-scope |

## 6. F — frontier reconciliation (#140)

| Item | Value |
| --- | --- |
| Reviewed head | `067cba1`; merge `b6c8507` |
| What it opens | The 000E and 000F research parents, with exactly five Grains named: `CORE-00`, `SD-M0`, `ST-D00`, `ST-D00b`, `KT-01` |
| Platform thesis | Now in the designated sections |
| Product code | Still closed |

**Research completed after F:**

- `CORE-00` (#141, `81b2de6`): 57 of 57 anchors pass; rights register; licence gate **CLOSED**.
- `ST-D00b` (#142, `5c2663f`): VoiceStudio stays the WisprStudio lead.
- Research forks `TheHalfMoon/wisprside` and `TheHalfMoon/wisprstudio` were created and made public (#143, #144). Actions are disabled, with 0 runs.

## 7. 000G

The decision package is [`DECISION_PACKAGE.md`](DECISION_PACKAGE.md).

**Recommendation: NO-GO on any product Grain today.** The evidence is insufficient:

- the licence gate is closed;
- three of the four 000E Grains have not run;
- STT is not settled.

The package gives a provisional order for the next 000G review:

1. a pure non-STT contract Grain;
2. WisprStudio or Klaint text-only;
3. WisprSide.

## 8. Document index (canonical on `main`)

**Constitution and canonical documents:**

- `CONSTITUTION.md` (1.0.0);
- `AGENTS.md`;
- `docs/canonical/{CURRENT_STATE,ARCHITECTURE_INVARIANTS,PROGRAM_ROADMAP,TRUSTED_CONTROL_REPAIRS}.md`;
- `specs/CURRENT.md`.

**Specifications:**

- `specs/000-founding-research/{spec,plan,tasks}.md`;
- `specs/000E-platform-feasibility/{spec,plan,tasks}.md`;
- `specs/000F-provenance-intake/{spec,plan,tasks}.md`.

**Plan:**

- `docs/strategy/WISPRAL_WORLD_CLASS_MASTER_PLAN.md`;
- `docs/strategy/WISPRAL_GOVERNANCE_RECONCILIATION.md`;
- `docs/strategy/WISPRAL_PRODUCT_VISION.md`;
- `research/wispral-world-class/packets.json`.

**Evidence:**

- `research/control-repairs/2026-11-08-{c2-nonsuccessor-class,lane-reconciliation}/`;
- `research/wispral-world-class/{RIGHTS_REGISTER,CATALOG_ERRATA,SOURCE_DECISION_MATRIX}.md`;
- `research/wispral-world-class/evidence/{core-00,baselines}/`;
- `research/wispral-world-class/000G/`.

## 9. Blockers

| Blocker | Owner |
| --- | --- |
| **Outbound licence (Q-01).** Wispral has no LICENSE, so no `COPY` or `ADAPT` code can land. | founder decision |
| **HW-A go-ahead.** Needed for the Windows halves of `SD-M0` and `ST-D00`, and for `KT-01`. | founder |
| **000B.** B2R17 active; #120 needs requalification at a new head; no STT selection. | B2 lane |
| **Ruleset.** Do not enable a ruleset until a single always-run aggregator check exists. | founder decision, with a governance PR |
| **Housekeeping.** Open #124 and #127 are superseded per the plan (close as carried or superseded); #121 and #73 are independent. | founder |
| **Small follow-ups.** The `SD-M0` packet text still cites private minutes; confusables folding of B2 marker text; trusted-coverage extension (plan §4.2 item 4). | later pull requests |

## 10. Exact next step to implementation

**The founder records Wispral's outbound licence (Q-01).** That single decision opens the gate for the first-ranked 000G candidate, a pure non-STT contract Grain. It is the only candidate with no outstanding 000E dependency.

In parallel, with the founder's go-ahead for HW-A, run `SD-M0`, `ST-D00` and `KT-01`. Then re-run 000G with a qualifying review, select exactly one Grain, and take it through readiness. Product code starts only after that.
