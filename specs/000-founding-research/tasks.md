# Specification 000 Tasks

This file tracks child-spec progression, not a speculative implementation backlog.

## Parent state

- [x] `000A` ACP qualification — `VERIFIED` at canonical evidence merge `354695c9f4d406147cbdc425d8f59e841a2f96a3` and closeout merge `99dd6290ee01ce566d32b92df6d469b66b56520a`; recommendation `PARTIAL`, confidence `MODERATE`.
- [ ] `000B` local STT/entity evidence — active recursive research parent; `000B1` remains historical `VERIFIED`, and the active B2 execution path is the public-corpus supersession defined by `000B2-public-corpus-bakeoff` once canonical.
- [ ] `000C` turn/interruption measurement — intentionally coarse.
- [ ] `000D` PTY fallback boundary — intentionally coarse.
- [ ] `000E` platform audio/privacy feasibility — intentionally coarse.
- [ ] `000F` dependency/license/provenance synthesis — intentionally coarse.
- [ ] `000G` founding synthesis / first product Grain selection — intentionally coarse.

## Immediate authorized refinement/execution frontier

`000B-stt-entity-bakeoff` remains the current speech-research parent.

Canonical historical speech evidence includes:

- `000B1-benchmark-candidate-qualification` — `VERIFIED`;
- B1 evidence merge `8df69835349f85d5ae6af9d6a62ef3af24f65f43`;
- B1 canonical closeout merge `ed05ad9b0ef80ae4f6838e783188cf306c20391a`;
- the unstarted private 20-speaker B2 collection path and its readiness/authority preparation.

The private participant-collection path is preserved as historical preregistration and preparation evidence but is prospectively superseded for active execution by `000B2-public-corpus-bakeoff` once that specification is canonical.

This supersession is allowed because no old-path primary decode occurred and the parent `000B` acceptance contract permits closure with human developer-speech evidence absent when that absence is explicit enough to prevent false ranking.

After canonicalization, B2 is authorized to execute only the bounded public-corpus plan:

- public human ordinary-speech baseline from the exact frozen OpenSLR LibriSpeech source/subset;
- identical C0 audio across candidate cells;
- exact provenance, preprocessing, environment, scorer, and attempt freeze before comparative decoding;
- optional deterministic synthetic developer-term stress as `DIAGNOSTIC_ONLY`;
- explicit `HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT` in all synthesis.

The following remain prohibited during B2:

- representing public audiobook speech as developer speech;
- representing synthetic/TTS speech as human evidence;
- a general STT superiority claim;
- a model/backend production winner;
- permanent speech dependency selection;
- production Rust/Cargo speech code;
- premature B3/B4 execution before B2 evidence is canonical.

## 000B child ordering

- [x] `000B1` benchmark/candidate qualification — `VERIFIED`.
- [ ] `000B2` unbiased local STT bakeoff — `BLOCKED_EXTERNAL`; entry-preparation only until all attempt-time gates pass.
- [ ] `000B2-public-corpus-bakeoff` — `READY` candidate; becomes the executable B2 lane only after its authority update is canonical on `main`.
- [ ] `000B3` repository-context uplift — coarse until amended B2 evidence is canonical.
- [ ] `000B4` STT synthesis — coarse until preceding evidence stabilizes its inputs.

The first two B-chain markers above are preserved canonical history. The old private-collection B2 path is not deleted, rewritten, or reported as completed; it remains `BLOCKED_EXTERNAL`. The public-corpus successor is a separate prospective active route because the private external dependency is unnecessary for the narrower founding shortlist decision permitted by the parent acceptance contract.

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
