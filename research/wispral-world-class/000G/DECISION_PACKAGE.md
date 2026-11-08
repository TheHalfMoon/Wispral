# 000G decision package: founding synthesis (2026-11-09)

**Status:** decision package and recommendation for the founder. It is not itself a 000G decision.

- **Authority.** Specification 000 (`specs/000-founding-research/spec.md`): 000G "selects exactly one bounded first product Grain, or records that evidence is insufficient to implement product code". Constitution 1.0.0, Governance item 8: product code is authorized only when a 000G decision selects a bounded Grain and that Grain satisfies readiness. Governance item 7: a 000G decision needs a qualifying review.
- **Canonical base:** `main` = `04d12e2134dc19df7635dd0ffc1df5a2ca07443d`.

## Recommendation

**NO-GO on any product Grain today.** The evidence is insufficient. This package records that, as Specification 000 requires, and names the shortest path to a GO.

Four blocking reasons, each verified on `main`:

1. **Licence gate Q-01 is CLOSED** (`RIGHTS_REGISTER.md` §1). Wispral has no LICENSE, so no `COPY` or `ADAPT` code may land. Every candidate below lands adapted or copied code.
2. **000E is incomplete.** Of its four Grains, only `ST-D00b` is `VERIFIED`. The fork baselines `SD-M0` and `ST-D00` and the Klaint spike `KT-01` are `NOT RUN`. No donor has been built or tested here.
3. **000B has not settled STT.** B2R17 is the active unit. The readiness claim guards record no selected STT engine and absent human developer-speech accuracy evidence. Any speech-bearing Grain requires accepted backend evidence, or an explicit insufficient-evidence synthesis (spec.md, 000B row).
4. **Several Specification 000 acceptance conditions are open** (section 2).

## 1. Child dispositions

| Child | State on `main` | Evidence that 000G can cite |
| --- | --- | --- |
| 000A ACP | `VERIFIED`: `PARTIAL` / `MODERATE` (merge `354695c9`) | ACP v1 initialization and discovery for two representatives. Authenticated lifecycle, permissions and cancellation are unverified. |
| 000B STT / entity | Active. B2R13–B2R16 complete; B2R17 active (#120 open, requalification pending); ATTEMPT-003 frozen and unscored | No STT selection. No comparative result. Human developer-speech evidence absent. |
| 000C turn / interruption | Coarse; re-scoped into `000C-AGENT` and `000C-VOICE` by Constitution 1.0.0 | none |
| 000D PTY boundary | Coarse; blocks only optional developer-agent compatibility | none |
| 000E platform feasibility | Open. `ST-D00b` `VERIFIED` (#142, `5c2663f`). `SD-M0`, `ST-D00` and `KT-01` are `GRAIN`, `NOT RUN`. | VoiceStudio stays the WisprStudio lead (capability 10 vs 7). Public research forks exist with Actions disabled and 0 runs. |
| 000F provenance intake | Open. `CORE-00` `VERIFIED` (#141, `81b2de6`). | 57 of 57 anchors re-verified; per-donor rights register; reference-only files; licence gate **CLOSED** |

## 2. Specification 000 acceptance conditions

| Condition (spec.md) | Status |
| --- | --- |
| Required children `VERIFIED`, `SUPERSEDED` or `CANCELLED` with rationale | **Open.** 000B, 000C, 000D, 000E and 000F are unfinished. |
| ACP and PTY recommendations state supported and unsupported semantics | ACP: met (000A). PTY: **open** (000D). |
| STT recommendation backed by a reproducible bakeoff, or an explicit record of why none is justified | **Open** (B2 active) |
| WispralBench founding scoring contract for the metrics used | **Open**. The B2 lane has a scorer, but nothing is scored yet. |
| Security and privacy analysis identifies first-product constraints | **Partial.** Constitution 1.0.0 Principles XVIII and XIX, and `docs/engineering/WISPRAL_SECURITY_ARCHITECTURE.md`, exist. There is no per-candidate analysis. |
| Dependency, licence and provenance decisions sufficient for a first production dependency baseline | **Open.** CORE-00 is done, but the outbound licence is unrecorded and the donor closures are unbuilt. |
| Platform scope for the first implementation explicit | **Open** (pending 000E) |
| 000G records a decision matrix and selects one Grain, or records that evidence is insufficient | **Met by this package:** evidence insufficient |
| No README or roadmap claim exceeds the evidence | Met. The non-claims were updated by F (#140). |

## 3. Decision matrix (capability-specific candidates, Specification 000)

Criteria from `specs/000-founding-research/plan.md`. The ratings are this package's judgement from the evidence above; they are not measurements.

| Criterion | Pure non-STT contract Grain (e.g. `CORE-01` / `CORE-02`) | WisprStudio first Grain | Klaint text-only first Grain | WisprSide first Grain |
| --- | --- | --- | --- | --- |
| Direct proof of the thesis | low | medium | medium | high |
| User-visible value | low | high | medium | high |
| Interoperability learning | medium | low | medium | high |
| Reversibility | high | medium | medium | medium |
| Measurable acceptance | high (fixtures, conformance) | medium | medium (tau2-style tasks) | medium |
| Narrow blast radius | high | low (large AGPL donor, consent surface) | medium (tenant surface) | medium |
| Low dependency lock-in | high | low (heavy closure) | medium | medium |
| Falsifies a bad architecture early | medium | medium | medium | high |
| STT dependency | none | none (TTS only) | none | **yes** |
| Code that would land | `ADAPT` / `COPY` from founder donors | the fork plus deltas | a `WRAP` of Parlant plus a broker | the fork plus deltas |
| **Evidence still missing** | the outbound licence (Q-01) | Q-01; the `ST-D00` baseline; `ST-D02` default-engine change; consent ledger | Q-01; the `KT-01` spike (v4 vs v3.3.2 decision) | Q-01; the `SD-M0` baseline; STT evidence or an explicit insufficient-evidence synthesis |
| **Could become GO after** | Q-01 alone | Q-01 + `ST-D00` | Q-01 + `KT-01` | Q-01 + `SD-M0` + a 000B disposition |

**Provisional order for the next 000G review.** This is not a selection: 000G still selects exactly one Grain, from the evidence available at that time.

1. **Pure non-STT contract Grain.** It is the only candidate with no outstanding 000E dependency. It is gated by Q-01 alone, and it has the narrowest blast radius and the most measurable acceptance.
2. **WisprStudio** or **Klaint text-only**, whichever baseline (`ST-D00` or `KT-01`) qualifies first.
3. **WisprSide.** It has the highest thesis value, but it also has the most open dependencies, including STT.

## 4. Shortest path to a GO

| Step | Owner | Unblocks |
| --- | --- | --- |
| Record Wispral's outbound licence (Q-01) in `RIGHTS_REGISTER.md` | founder decision; Claude records it | every candidate |
| Go-ahead for runs on HW-A (the founder's laptop) | founder | the Windows halves of `SD-M0` and `ST-D00`; all of `KT-01` |
| Run `SD-M0` and `ST-D00` on hosted Linux in the public forks, after disabling the donor release, signing and updater workflows on a baseline branch | Claude | 000E baselines |
| Run `KT-01` | Claude, with HW-A | the Klaint candidate |
| Re-run 000G with the new evidence, with a qualifying review | Claude, then founder ratification | product code for exactly one Grain |

## 5. What this package does not do

- It authorizes no product code, release or installer.
- It does not open the licence gate or decide any model or voice right.
- It does not change any B2 state.
- It selects no Grain.
