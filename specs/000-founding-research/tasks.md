# Specification 000 Tasks

This file tracks child-spec progression, not a speculative implementation backlog.

## Parent state

- [x] `000A` ACP qualification — `VERIFIED` at canonical merge `354695c9f4d406147cbdc425d8f59e841a2f96a3`; recommendation `PARTIAL`, confidence `MODERATE`.
- [ ] `000B` local STT/entity bakeoff — intentionally coarse; next child eligible for bounded refinement.
- [ ] `000C` turn/interruption measurement — intentionally coarse.
- [ ] `000D` PTY fallback boundary — intentionally coarse.
- [ ] `000E` platform audio/privacy feasibility — intentionally coarse.
- [ ] `000F` dependency/license/provenance synthesis — intentionally coarse.
- [ ] `000G` founding synthesis / first product Grain selection — intentionally coarse.

## Immediate authorized refinement

The next child eligible for bounded refinement is `000B`.

000B is **not** automatically `READY` and no STT experiment is authorized merely by this task file. Refinement must:

- re-read current canonical WispralBench and research authority;
- use current external/local-STT truth rather than founding assumptions;
- define a reproducible developer-speech benchmark contract before comparative execution;
- preserve licensing/provenance and environment constraints;
- separate local STT quality evidence from repository-context uplift evidence;
- establish a readiness gate before any benchmark run.

Do not create detailed 000C–000G task lists before prior canonical evidence can materially shape them.

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