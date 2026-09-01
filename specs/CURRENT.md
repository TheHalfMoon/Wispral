# Wispral Specification Frontier

**Status:** founding research — ACP verified; local speech evidence refining

## Active parent specification

`000-founding-research`

State: `REFINING`

Purpose: replace founding technical assumptions with reproducible evidence sufficient to select the first product implementation Grain.

## Verified child

`000A-acp-qualification`

State: `VERIFIED`

Canonical evidence merge: `354695c9f4d406147cbdc425d8f59e841a2f96a3`

Disposition:

- ACP recommendation: `PARTIAL`
- confidence: `MODERATE`
- ACP remains the leading structured-path candidate, not an unconditional production selection;
- authenticated prompt/stream/cancellation/permission behavior and representative ACP v2 runtime behavior remain unverified;
- no broad named-agent support claim is authorized.

See `docs/research/acp/qualification-report.md` and `docs/research/acp/capability-matrix.json` for the bounded evidence.

## Active research parent

`000B-stt-entity-bakeoff`

State: `REFINING`

Purpose: produce reproducible local STT and developer-entity/context evidence without preselecting a speech engine or conflating raw recognition with repository-context uplift.

000B is recursively refined into:

- `000B1` — benchmark and candidate qualification;
- `000B2` — unbiased local STT bakeoff;
- `000B3` — repository-context uplift;
- `000B4` — STT synthesis.

Only 000B1 is task-refined by current authority.

## Near executable frontier

`000B1-benchmark-candidate-qualification`

State after this refinement is canonical: `GRAIN`

Readiness: must be rechecked against canonical Wispral authority and current Moonshine/whisper.cpp/sherpa-onnx runtime/model/license truth before transitioning to `READY`.

B1 freezes the benchmark contract **before** primary comparative decoding. It may qualify exact runtime/model provenance and use bounded non-comparative smoke media if needed, but it does not run the primary developer-speech ranking.

Mandatory candidate families for qualification, subject to live revalidation:

- Moonshine Voice streaming STT;
- `whisper.cpp` with an exact Whisper model artifact;
- `sherpa-onnx` with an exact online English model artifact.

These are candidates, not support claims or selected dependencies.

## Evidence boundaries established by 000B refinement

- C0: unbiased local STT, with repository/test-specific decoder context disabled;
- C1: one engine-agnostic deterministic repository resolver applied to frozen C0 transcripts;
- C2: backend-native keyterm/prompt/hotword/context features, reported only as within-backend uplift/degradation relative to that backend's C0.

Native context features do not replace C0 in cross-backend comparison.

The benchmark also distinguishes observed streaming semantics such as `NATIVE_INCREMENTAL` versus `CHUNKED_REDECODE` rather than treating every upstream `streaming` label as equivalent behavior.

Synthetic/TTS audio may validate the harness but may not be the sole evidence for ranking human developer-speech accuracy. Primary developer-speech evidence requires suitable human recordings under explicit consent/retention/redistribution rules; otherwise later primary execution must remain blocked.

Shared hosted-runner timings are diagnostic by default and do not establish general latency/resource superiority.

## Remaining planned research children

After the evidence-selected 000B children complete, the parent currently anticipates:

- `000C` — turn-taking, pause, and interruption measurement design;
- `000D` — PTY compatibility and fallback threat/maintenance boundary;
- `000E` — platform audio feasibility and privacy/permission observations;
- `000F` — dependency, licensing, provenance, and distribution decision inputs;
- `000G` — founding synthesis and first product-Grain selection.

000C–000G remain intentionally coarse until preceding canonical evidence can materially shape them.

## Global evidence gate

Before any child is marked `VERIFIED`:

- exact artifacts and source revisions must be recorded;
- failures and unsupported behavior must remain visible;
- unavailable systems must be recorded as unavailable, not PASS;
- evidence claims must remain narrower than the raw observations;
- benchmark attempts must preserve frozen material inputs and invalidate/restart after material drift;
- the evidence must be sufficient to challenge the resulting recommendation.

## Product-code gate

No Rust product implementation, Cargo workspace, permanent speech engine integration, ACP production client, PTY adapter, TUI, installer, or release is authorized until `000G` selects a bounded first implementation Grain and that Grain independently satisfies readiness.

Neither verified 000A nor refined 000B weakens this gate.

## Live-truth rule

Live canonical GitHub/repository truth overrides this file. After each merged research/refinement unit, re-read current authority before refining or starting the next child.