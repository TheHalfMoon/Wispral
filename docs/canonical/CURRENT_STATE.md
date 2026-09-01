# Wispral Current State

**Repository:** `TheHalfMoon/Wispral`  
**Canonical branch:** `main`  
**Bootstrap commit:** `894644c102a77b65bf53bfab21a3fdd258272ac9`  
**Founding authority merge:** `3cbe212bf7202c37ec322f114c0e5486e5218d9b`  
**ACP qualification merge:** `354695c9f4d406147cbdc425d8f59e841a2f96a3`  
**ACP closeout merge:** `99dd6290ee01ce566d32b92df6d469b66b56520a`  
**000B refinement merge:** `6b5696a6becc360948282712cc9339df9cb3a67c`  
**000B1 evidence merge:** `8df69835349f85d5ae6af9d6a62ef3af24f65f43`  
**Program status:** `SPEC_000_RESEARCH_ACTIVE`  
**Active product implementation:** none  
**Active parent specification:** `000-founding-research` — `REFINING`  
**Verified ACP child:** `000A-acp-qualification` — `VERIFIED`, recommendation `PARTIAL`, confidence `MODERATE`  
**Active research parent:** `000B-stt-entity-bakeoff` — `REFINING`  
**Verified speech child:** `000B1-benchmark-candidate-qualification` — `VERIFIED`  
**Blocked successor:** `000B2-unbiased-stt-bakeoff` — `BLOCKED_EXTERNAL`  
**Published release:** none

Live GitHub and repository truth override this document.

## Canonical founding proof

PR #1 merged by guarded squash with exact expected head `9a8e014cb1693058e03e43b59ea1c3a4eb068a4b` into canonical merge `3cbe212bf7202c37ec322f114c0e5486e5218d9b`.

The founding authority established the Wispral Constitution, architecture invariants, research roadmap, benchmark/threat-model foundations, and Specification 000 without adding product code or selecting permanent agent/speech dependencies.

## Canonical ACP qualification proof

PR #3 executed Specification 000A against pinned Gemini CLI `0.57.0 --acp` and Codex ACP `1.7.0` using a synthetic fixture and a no-secret GitHub-hosted probe.

The final exact qualified head was `6882bc8fac6925e068d40b2b68d46a18e8b03f2f`. Workflow `33502915021` completed successfully. The guarded merge produced canonical commit `354695c9f4d406147cbdc425d8f59e841a2f96a3`; PR #4 reconciled the canonical 000A closeout at `99dd6290ee01ce566d32b92df6d469b66b56520a`.

The verified result remains intentionally bounded:

- both representatives completed real ACP v1 initialization;
- both exposed structured capability/authentication metadata;
- authenticated prompt execution, streaming, active cancellation, structured permission behavior, Codex steering behavior, and representative ACP v2 runtime interoperability were not observed;
- recommendation: `PARTIAL`, confidence `MODERATE`;
- ACP remains a structured-path candidate, not an unconditional production selection.

## Canonical local-speech refinement

PR #5 refined 000B into sequential evidence children and merged as `6b5696a6becc360948282712cc9339df9cb3a67c`.

000B separates:

1. **C0 unbiased local STT** — repository/test-specific decoder context OFF;
2. **C1 deterministic engine-agnostic repository resolution** — applied to frozen C0 transcripts;
3. **C2 backend-native context/bias** — reported only as within-backend uplift/degradation relative to the same backend's C0.

It also distinguishes observed `NATIVE_INCREMENTAL`, `CHUNKED_REDECODE`, `BATCH_ONLY`, and `UNKNOWN` streaming semantics instead of treating every upstream `streaming` label as equivalent.

## Canonical 000B1 preregistration proof

PR #7 completed B101–B119 and merged by guarded expected-head squash from exact head `262c8cc6dd6fadfcd782ce5beee2f3ca443c77b5` as canonical commit `8df69835349f85d5ae6af9d6a62ef3af24f65f43`.

The exact premerge head passed `000B1 Preregistration` workflow run `33514521301` (run number `58`). The final gate included deterministic verification for:

- exact candidate family/cell allowlists, runtimes, model/source provenance, tier limits, artifact identities, and pinned/pending digests;
- immutable whisper.cpp model-source revision;
- frozen 20-speaker / 720-utterance human-panel design without authorizing recording;
- FFmpeg `9.0.1` / `n9.0.1` / source commit `bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa`, PCM-WAV preprocessing, and C0 configuration invariants;
- attempt-manifest binding to the frozen six-cell registry/methodology;
- allowed pre-freeze exclusions and per-candidate smoke-PASS/canonical-waiver readiness evidence;
- entity-annotation cross-field span invariants;
- schema semantic constraints rather than schema headers alone;
- exact adversarial-review authority labels and B2 readiness blockers.

Independent CodeRabbit and Cubic reviews produced actionable findings. Valid findings were verified, fixed, regression-gated, and all review threads were resolved before the guarded merge. No stale review or unavailable reviewer was represented as a fresh approval.

The verified B1 result is a preregistration/qualification contract, not a benchmark result:

- primary developer-speech decoding performed: `NO`;
- comparative ranking present: `NO`;
- production speech dependency selected: `NO`;
- product Rust/Cargo implementation added: `NO`;
- human recording authorization created: `NO`;
- B2 authorization created: `NO`.

The canonical closeout record is `research/000b1/canonical-closeout.json`.

## B2 blocked successor

`000B2-unbiased-stt-bakeoff` is `BLOCKED_EXTERNAL`, not `READY`.

Primary developer-speech decoding must not begin until all required gates are satisfied. Current blockers are:

- explicit human developer-speech consent, retention, redistribution, withdrawal, and frozen-corpus authority are absent;
- Moonshine payload SHA-256 values remain pending attempt-time materialization;
- sherpa-onnx `tokens.txt` SHA-256 remains pending attempt-time materialization;
- each selected candidate still requires bounded non-primary operational smoke PASS or an explicit canonical waiver;
- exact scorer implementation/revision/configuration is not frozen;
- attempt-time FFmpeg binary/version-output identity and preprocessing execution evidence are not frozen;
- execution environment and hardware fingerprint are not frozen;
- no final B2 attempt manifest exists with `frozen=true` and a matching freeze digest.

Synthetic/TTS audio may support smoke/harness/regression only. It cannot satisfy the human developer-speech authority gate and cannot enter the primary human ranking.

## What is established

Canonical research authority now contains:

- the active Wispral Constitution v0.1.0;
- proof-before-done and progressive SpecGrain repository discipline;
- architecture invariants without premature dependency selection;
- a progressive H0–H15 program roadmap;
- a source-backed founding research register;
- WispralBench methodology with no speech winner selected;
- a founding voice/agent threat model;
- verified 000A ACP evidence (`PARTIAL` / `MODERATE`);
- verified 000B1 local-STT preregistration/candidate qualification;
- explicit B2 external/material readiness blockers.

## Current product thesis

Wispral is a voice-native control plane for AI coding agents.

> A developer should be able to speak to an agent, think aloud without accidentally authorizing action, resolve developer-specific entities against repository context, interrupt and steer execution immediately, and preserve visible authority boundaries across multiple independent agents.

This thesis is a program direction, not a benchmark result or compatibility claim.

## Current architecture posture

- Rust remains the preferred product runtime; no production Cargo workspace is authorized yet.
- ACP is the leading structured integration candidate, classified `PARTIAL` / `MODERATE` by 000A rather than selected as unconditional `PRIMARY`.
- A PTY compatibility path may still be required for agents without sufficient structured semantics.
- Local streaming speech recognition remains first-class, but no engine/model configuration is selected.
- Repository-aware entity resolution remains a hypothesis to be measured after unbiased STT evidence exists.
- `COMMAND` and `ASIDE` remain separate semantic concepts; the exact interaction/classification contract remains unselected.
- Push-to-talk remains the preferred first reliable capture hypothesis; hands-free/full-duplex behavior requires later evidence.

## Explicit non-claims

Wispral does NOT currently claim:

- production support for Codex, Claude Code, Gemini CLI, OpenCode, Goose, Copilot CLI, or another named agent;
- broad ACP compatibility beyond exact 000A observations;
- authenticated ACP prompt/session portability, streaming, active cancellation, permissions, steering, or v2 portability;
- a winning or production-ready Moonshine, Whisper, sherpa-onnx, or other STT configuration;
- developer-entity accuracy for any STT candidate;
- repository-context accuracy uplift;
- sub-second voice latency or comparative performance superiority;
- better transcription than Wispr Flow, Superwhisper, Aqua, Claude Code voice, or another product;
- Arabic or English product support;
- full-duplex audio or acoustic echo cancellation;
- production security, accessibility, privacy, platform, or release qualification;
- any GitHub growth outcome.

## Product-code gate

No Rust product implementation, Cargo workspace, permanent speech-engine integration, ACP production client, PTY adapter, TUI, installer, or release is authorized until Specification 000 synthesis reaches `000G`, selects a bounded first implementation Grain from reproducible evidence, and that Grain independently satisfies readiness.

Verified 000A and verified 000B1 do not weaken this gate.

## Next canonical action

Do not execute B2 while it is `BLOCKED_EXTERNAL`. Establish the missing human-speech authority and satisfy the remaining materialization, operational, scoring, preprocessing, environment, and final manifest-freeze gates without weakening the verified B1 contract. If those gates cannot be satisfied, preserve the block rather than substitute synthetic primary evidence or prematurely advance B3/B4.
