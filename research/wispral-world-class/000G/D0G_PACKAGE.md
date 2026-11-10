# D0G decision package: after the 000E evidence (2026-11-10)

**Status:** a decision package and recommendation for the founder. It is not itself the D0G decision. It updates [`DECISION_PACKAGE.md`](DECISION_PACKAGE.md) (2026-11-09) with the 000E evidence merged since.

- **Authority:**
  - `D0G` in `research/wispral-world-class/packets.json` ("000G decision: select capability-specific Grains from P1 evidence"), readiness authority `DECISION_000G`.
  - Constitution 1.0.0, Governance item 8: product code needs a 000G decision and a Grain that satisfies readiness.
  - Governance item 7: a qualifying independent review.
- **Canonical base:** `main` = `246283f59dcdfa945ef9d49d0cc2fa5b9deb8b09`. PR #153 (000E Grain states) is approved but not yet merged. The states below are those it records.

## Recommendation

**NO-GO on D0G as the packet is written.** `D0G` depends on `F`, `CORE-00`, `SD-M0`, `ST-D00`, `ST-D00b` and `KT-01`. Three of these are not `VERIFIED`, and two are `BLOCKED` for reasons that a decision alone cannot clear.

The smallest safe first Grain is still **`CORE-01`**: the eight candidate contracts as a language-neutral package, with the gap-probe corpus. Its own work does not depend on any blocked evidence, because it uses no STT, no donor runtime and no model. It is reachable only through `D0G`, though. Section 4 gives the founder two paths.

## 1. D0G dependencies

| Dependency | State | Evidence on `main` | What clears it |
| --- | --- | --- | --- |
| `F` | `VERIFIED` | #140, `b6c8507` | — |
| `CORE-00` | `VERIFIED` | #141, `81b2de6` | — |
| `ST-D00b` | `VERIFIED` | #142, `5c2663f` | — |
| `SD-M0` | `VERIFYING` (#153) | Linux in #148 (`48fb9c0`); Windows in #150 (`131a2bf`). All suites pass. Debug and release builds succeed. Acceptance item 3 (bundled DLLs) is recorded only in the narrowed form the #150 review required: no VC++ runtime staged, installer contents NOT RUN. | **The founder confirms the narrowed item 3 satisfies the packet**, or amends the item |
| `ST-D00` | `BLOCKED` (#153) | Linux #148; Windows #149 (`f29f5f5`); attribution #151 (`c407288`). The test suite reaches Hugging Face despite `HF_HUB_OFFLINE=1`: the AudioSeal watermark download through `torch.hub`. On Windows, a test also clones from GitHub and a runtime download is attempted. 82 failures and 21 errors on Windows. | A remediation decision, **and** a rerun on both platforms showing zero model-hub connections and no runtime download |
| `KT-01` | `BLOCKED` (#153) | #152 (`246283f`). Hooks fire in order on Parlant v4.0.2. BAIL works only in BLOCK mode. **The integrated tool server cannot be disabled and accepts a forged `customer_id` (v4 and v3).** The local CPU model is NOT RUN. | Item 3: a packet amendment, or an implemented and evidenced gate. Item 4: the founder names a model, and it is measured. |

## 2. Capability dispositions D0G must cite (000B, 000C, 000D)

| Child | State on `main` | Effect on Grains |
| --- | --- | --- |
| 000B STT / entity | Active. B2R17 is the active recovery unit; ATTEMPT-003 is frozen and scoring is closed (`specs/CURRENT.md`). There is no STT selection, and human developer-speech evidence is absent. | Blocks any speech-bearing Grain, including `GRAIN_SIDE` product work, until accepted backend evidence exists or an explicit insufficient-evidence synthesis is recorded |
| 000C turn / interruption | Coarse; re-scoped into `000C-AGENT` and `000C-VOICE` | No Grain depends on it yet |
| 000D PTY boundary | Coarse; blocks only optional developer-agent compatibility | Does not block the Grains below |
| 000A ACP | `VERIFIED` `PARTIAL` / `MODERATE` | Citable for interoperability |
| Licence (Q-01) | **Decided:** Apache-2.0 (#146, `53d32b5`) | No longer a blocker |

## 3. Recalculated matrix

The ratings for value, reversibility and blast radius are unchanged from [`DECISION_PACKAGE.md`](DECISION_PACKAGE.md) §3. Only the evidence and blocker rows change.

| | `GRAIN_CORE` (`CORE-01`, `CORE-07`) | `GRAIN_DESIGN` (`DS-01`) | `GRAIN_BENCH` (`BM-00` preregistration) | `GRAIN_SIDE` | `GRAIN_STUDIO` | `GRAIN_KLAINT_TEXT` |
| --- | --- | --- | --- | --- | --- | --- |
| Depends on (packets) | `D0G` | `D0G` | `BM-00`: `D0G`. `BM-01`: `SD-M0`, `ST-D00`, `CORE-07`. | `SD-M0`, plus `D0G` or `CORE-01` (first packets); the STT condition comes from Specification 000, not `packets.json` | `ST-D00`, `D0G` | `KT-01`, `D0G` |
| Blocked P1 evidence it relies on | none in its own work | none in its own work | `BM-00` none; `BM-01` needs `ST-D00` | `SD-M0` (VERIFYING); 000B | **`ST-D00` (BLOCKED)** | **`KT-01` (BLOCKED)** |
| Uses STT, donor runtime or a model | no | no | `BM-00` no | yes (STT) | yes (TTS donor) | yes (LLM) |
| Ready to open if `D0G` passed today | **yes** | yes | `BM-00` yes | **no** (000B) | **no** | **no** |

## 4. Paths for the founder

**Path A: clear the dependencies, then decide D0G as written.**

1. Confirm `SD-M0`'s narrowed item 3. This makes it `VERIFIED`.
2. Remediate `ST-D00`. For example, provide the AudioSeal checkpoint locally or stub it in tests, and fix the Windows `git` and `PATH` handling. Then rerun on both platforms with zero model-hub connections.
3. Resolve `KT-01`: authorize a local CPU model and measure it. Then either amend item 3, or implement and evidence a tool gate.
4. Re-run D0G with a qualifying review.

This is the slowest path. Steps 2 and 3 are substantial work, and step 2 means deciding how far a research baseline may diverge from the donor.

**Path B: amend D0G's dependencies so each blocked baseline gates only its own product Grain.** *(This is the recommended path, if the founder accepts the amendment.)*

- Change `D0G.depends_on` to `F`, `CORE-00` and `ST-D00b`, plus `SD-M0` once it is confirmed.
- Move `ST-D00` to the dependencies of `GRAIN_STUDIO`, and `KT-01` to those of `GRAIN_KLAINT_TEXT`. They already depend on them in `packets.json`.
- D0G can then open `GRAIN_CORE`, `GRAIN_DESIGN` and `GRAIN_BENCH` (`BM-00` preregistration) with **no product Grain**. Each product Grain stays closed: `GRAIN_SIDE` on 000B, `GRAIN_STUDIO` on `ST-D00`, and `GRAIN_KLAINT_TEXT` on `KT-01`.
- `CORE-01` becomes the first `READY` Grain.
- This is a governance amendment to `packets.json`. It needs its own reviewed PR and the founder's approval, followed by the D0G decision PR, which also needs a qualifying review.

**Why B is safe:**

- No Grain it opens touches the blocked evidence, STT, a donor runtime or a model.
- The blocked baselines still gate the product Grains that would use them.
- Nothing is reported as verified that is not.

**What B gives up:** D0G no longer waits for all of P1. The founder should decide whether that ordering mattered for its own sake.

## 5. What this package does not do

- It decides nothing and authorizes no product code. `CORE-01` is not `READY` until a D0G decision is merged.
- It does not amend `packets.json`.
- It does not remediate any donor.
- It does not change any 000B state.
- It does not count the approved-but-unmerged #153 as canonical. If #153 changes, this package must be reread.
