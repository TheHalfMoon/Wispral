# Specification 000 Tasks

This file tracks child-spec progression, not a speculative implementation backlog.

## Parent state

- [x] `000A` ACP qualification — `VERIFIED` at canonical merge `354695c9f4d406147cbdc425d8f59e841a2f96a3`; recommendation `PARTIAL`, confidence `MODERATE`.
- [ ] `000B` local STT/entity evidence — refined as a recursive research parent; only B1 is task-refined.
- [ ] `000C` turn/interruption measurement — intentionally coarse.
- [ ] `000D` PTY fallback boundary — intentionally coarse.
- [ ] `000E` platform audio/privacy feasibility — intentionally coarse.
- [ ] `000F` dependency/license/provenance synthesis — intentionally coarse.
- [ ] `000G` founding synthesis / first product Grain selection — intentionally coarse.

## Immediate authorized refinement/execution frontier

`000B-stt-entity-bakeoff` is refined as the current speech-research parent.

Its only task-level child is:

`000B1-benchmark-candidate-qualification`

State after the refinement authority becomes canonical: `GRAIN`.

B1 must independently recheck readiness before it may become `READY` or execute. B1 freezes benchmark/candidate/corpus/scoring/environment/attempt rules before any primary developer benchmark test decoding.

B1 specifically does **not** authorize:

- primary comparative STT decoding;
- a model/backend winner;
- repository-context uplift execution;
- performance-superiority claims;
- a permanent speech dependency;
- production Rust/Cargo speech code.

Do not create detailed 000C–000G task lists before prior canonical evidence can materially shape them.

## 000B child ordering

- [ ] `000B1` benchmark/candidate qualification — task-refined.
- [ ] `000B2` unbiased local STT bakeoff — coarse until B1 is canonical.
- [ ] `000B3` repository-context uplift — coarse until B2 is canonical.
- [ ] `000B4` STT synthesis — coarse until preceding evidence stabilizes its inputs.

## Parent closeout tasks

These become eligible only after the required children complete:

- [ ] Reconcile all child dispositions and exact evidence references.
- [ ] Produce the 000G architecture/product decision matrix.
- [ ] Select one first implementation Grain or explicitly select no implementation.
- [ ] Create only the ADRs supported by settled evidence.
- [ ] Reconcile README, current state, roadmap, security notes, and benchmark claims.
- [ ] Verify no founding non-claim has silently become an unsupported public claim.
- [ ] Close Specification 000 only after canonical post-merge verification of its final authority update.

## Product-code gate

No production Rust/Cargo workspace, permanent speech engine, ACP runtime, PTY adapter, TUI, installer, or release is authorized until 000G selects a bounded first product Grain and that Grain independently satisfies readiness.