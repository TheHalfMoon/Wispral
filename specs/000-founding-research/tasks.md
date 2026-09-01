# Specification 000 Tasks

This file tracks child-spec progression, not a speculative implementation backlog.

## Parent state

- [x] `000A` ACP qualification — `VERIFIED` at canonical evidence merge `354695c9f4d406147cbdc425d8f59e841a2f96a3` and closeout merge `99dd6290ee01ce566d32b92df6d469b66b56520a`; recommendation `PARTIAL`, confidence `MODERATE`.
- [ ] `000B` local STT/entity evidence — active recursive research parent; `000B1` is `VERIFIED`, while `000B2` is `BLOCKED_EXTERNAL`.
- [ ] `000C` turn/interruption measurement — intentionally coarse.
- [ ] `000D` PTY fallback boundary — intentionally coarse.
- [ ] `000E` platform audio/privacy feasibility — intentionally coarse.
- [ ] `000F` dependency/license/provenance synthesis — intentionally coarse.
- [ ] `000G` founding synthesis / first product Grain selection — intentionally coarse.

## Immediate authorized refinement/execution frontier

`000B-stt-entity-bakeoff` remains the current speech-research parent.

Canonical speech evidence now includes:

- `000B1-benchmark-candidate-qualification` — `VERIFIED`;
- B1 evidence merge `8df69835349f85d5ae6af9d6a62ef3af24f65f43`;
- B1 canonical closeout merge `ed05ad9b0ef80ae4f6838e783188cf306c20391a`;
- successor `000B2-unbiased-stt-bakeoff` — `BLOCKED_EXTERNAL`, not `READY`.

The only work permitted at the B2 frontier while it remains blocked is bounded entry-preparation that removes non-primary readiness blockers without decoding the primary developer-speech test split, weakening the B1 preregistration, or substituting synthetic/TTS media for human primary evidence.

B2 specifically does **not** currently authorize:

- primary comparative STT decoding;
- a model/backend winner;
- repository-context uplift execution;
- performance-superiority claims;
- a permanent speech dependency;
- production Rust/Cargo speech code.

Do not create detailed 000C–000G task lists before prior canonical evidence can materially shape them.

## 000B child ordering

- [x] `000B1` benchmark/candidate qualification — `VERIFIED`.
- [ ] `000B2` unbiased local STT bakeoff — `BLOCKED_EXTERNAL`; entry-preparation only until all attempt-time gates pass.
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
