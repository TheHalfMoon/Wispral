# Wispral Specification Frontier

**Status:** founding research — ACP verified; STT preregistration verified; B2 externally blocked

## Active parent specification

`000-founding-research`

State: `REFINING`

Purpose: replace founding technical assumptions with reproducible evidence sufficient to select the first product implementation Grain.

## Verified ACP child

`000A-acp-qualification`

State: `VERIFIED`

Canonical evidence merge: `354695c9f4d406147cbdc425d8f59e841a2f96a3`

Canonical closeout merge: `99dd6290ee01ce566d32b92df6d469b66b56520a`

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

## Verified speech preregistration child

`000B1-benchmark-candidate-qualification`

State: `VERIFIED`

Canonical 000B refinement/base merge: `6b5696a6becc360948282712cc9339df9cb3a67c`

Canonical evidence merge: `8df69835349f85d5ae6af9d6a62ef3af24f65f43` from PR #7.

Disposition:

- exact candidate/runtime/model/provenance and COMPACT/BALANCED selection rules are preregistered;
- canonical FFmpeg `9.0.1` PCM-WAV preprocessing and C0/C1/C2 boundaries are frozen;
- the human panel design is frozen at 20 speakers / 720 utterances without authorizing recording;
- a fail-closed B2 manifest/registry/annotation validation surface is canonical;
- primary developer-speech decoding: `NO`;
- comparative ranking: `NO`;
- STT winner/product dependency selection: `NO`.

See `research/000b1/canonical-closeout.json` for the canonical B1 closeout proof and B2 blocker set.

## Blocked successor

`000B2-unbiased-stt-bakeoff`

State: `BLOCKED_EXTERNAL`

B2 is not `READY` and primary decoding is not authorized. Current blockers include:

- human developer-speech consent, retention, redistribution, withdrawal, and frozen-corpus authority are absent;
- Moonshine payload SHA-256 materialization remains incomplete;
- sherpa-onnx `tokens.txt` SHA-256 materialization remains incomplete;
- each selected candidate still needs bounded non-primary operational smoke PASS or an explicit canonical waiver;
- scorer implementation/revision/configuration is not frozen;
- attempt-time FFmpeg binary/version-output identity and preprocessing execution evidence are not frozen;
- execution environment and hardware fingerprint are not frozen;
- no final `frozen=true` B2 attempt manifest with a matching freeze digest exists.

Synthetic/TTS media cannot satisfy the human developer-speech authority gate or enter the primary ranking.

## Evidence boundaries established by 000B1

- C0: unbiased local STT, with repository/test-specific decoder context disabled;
- C1: one engine-agnostic deterministic repository resolver applied to frozen C0 transcripts;
- C2: backend-native keyterm/prompt/hotword/context features, reported only as within-backend uplift/degradation relative to that backend's C0.

Native context features do not replace C0 in cross-backend comparison.

The benchmark distinguishes observed streaming semantics such as `NATIVE_INCREMENTAL` versus `CHUNKED_REDECODE` rather than treating every upstream `streaming` label as equivalent behavior.

Primary developer-speech evidence requires suitable human recordings under explicit consent/retention/redistribution rules. Shared hosted-runner timings remain diagnostic by default and do not establish general latency/resource superiority.

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

Neither verified 000A nor verified 000B1 weakens this gate.

## Live-truth rule

Live canonical GitHub/repository truth overrides this file. After each merged research/refinement unit, re-read current authority before refining or starting the next child.

## Next canonical action

Do not execute B2 while it is `BLOCKED_EXTERNAL`. The next legitimate action is to obtain or formally establish the missing external human-speech authority and satisfy the remaining material/operational/freeze gates without weakening the verified 000B1 contract. If those gates cannot be satisfied, preserve the block rather than substituting synthetic primary evidence or prematurely advancing B3/B4.
