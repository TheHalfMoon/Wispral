# Wispral Current State

**Repository:** `TheHalfMoon/Wispral`  
**Canonical branch:** `main`  
**Bootstrap commit:** `894644c102a77b65bf53bfab21a3fdd258272ac9`  
**Founding authority merge:** `3cbe212bf7202c37ec322f114c0e5486e5218d9b`  
**ACP qualification merge:** `354695c9f4d406147cbdc425d8f59e841a2f96a3`  
**ACP closeout merge:** `99dd6290ee01ce566d32b92df6d469b66b56520a`  
**Program status:** `SPEC_000_RESEARCH_ACTIVE`  
**Active product implementation:** none  
**Active parent specification:** `000-founding-research` — `REFINING`  
**Verified child:** `000A-acp-qualification` — `VERIFIED`, recommendation `PARTIAL`, confidence `MODERATE`  
**Active research parent:** `000B-stt-entity-bakeoff` — `REFINING`  
**Near frontier:** `000B1-benchmark-candidate-qualification` — `GRAIN`; readiness recheck required before execution  
**Published release:** none

Live GitHub and repository truth override this document.

## Canonical founding proof

PR #1 merged by guarded squash with exact expected head `9a8e014cb1693058e03e43b59ea1c3a4eb068a4b` into canonical merge `3cbe212bf7202c37ec322f114c0e5486e5218d9b`.

The founding PR changed exactly 20 documentation/research/governance paths and added no product code, dependency manifest, workflow, release artifact, package metadata, speech engine, or agent adapter.

At the final pre-merge reconciliation:

- GitHub reported the PR mergeable;
- canonical `main` remained at bootstrap commit `894644c102a77b65bf53bfab21a3fdd258272ac9`;
- the exact head was unchanged;
- there were no submitted reviews and no inline review threads;
- Qodo was billing-blocked;
- CodeRabbit automatic review was skipped by repository-star policy; a manual review was requested but no submitted review was present at the merge gate;
- CodeRabbit status existed but was not treated as independent review evidence;
- product tests were not applicable because no product code existed;
- the repository had no configured required CI checks or branch protection.

No unavailable/skipped review system was represented as PASS. The merge commit is GitHub-signature verified.

## Canonical ACP qualification proof

PR #3 executed Specification 000A against pinned Gemini CLI `0.57.0 --acp` and Codex ACP `1.7.0` using a synthetic fixture and a no-secret GitHub-hosted probe.

The final exact qualified head was `6882bc8fac6925e068d40b2b68d46a18e8b03f2f`. Workflow `33502915021` completed successfully across:

- `Committed evidence verifier`;
- `ACP v1 probe (gemini)`;
- `ACP v1 probe (codex-acp)`.

The guarded merge produced canonical commit `354695c9f4d406147cbdc425d8f59e841a2f96a3`, which is GitHub-signature verified. PR #4 then reconciled the canonical 000A closeout at `99dd6290ee01ce566d32b92df6d469b66b56520a`.

The verified result is intentionally bounded:

- both representatives completed real ACP v1 initialization;
- both exposed structured capability/authentication metadata;
- Gemini returned `session/new=AUTH_REQUIRED` and `session/list=METHOD_NOT_FOUND`;
- Codex ACP returned `session/new=AUTH_REQUIRED` and `session/list=AUTH_REQUIRED`;
- authenticated prompt execution, streaming, active cancellation, structured permission behavior, Codex steering behavior, and representative ACP v2 runtime interoperability were not observed;
- the recommendation is therefore `PARTIAL`, not `PRIMARY`, with `MODERATE` confidence.

The repository preserves raw sanitized evidence, package integrity, a capability matrix, an evidence review, and an independent deterministic verifier under `docs/research/acp/` and `research/000a/`.

## Local speech research refinement

000B is now shaped from current WispralBench authority and current external STT truth rather than from the original candidate list alone.

The current candidate families for qualification are:

- Moonshine Voice streaming STT;
- `whisper.cpp` with an exact Whisper model artifact;
- `sherpa-onnx` with an exact online English model artifact.

These are candidate families only. No runtime/model configuration has won a Wispral benchmark and no permanent dependency is selected.

Current upstream research materially affects the benchmark design:

- Moonshine exposes current streaming models plus native keyterms/context biasing;
- whisper.cpp documents its microphone `whisper-stream` example as naive periodic/sliding-window re-decode behavior and exposes decoder prompt context;
- sherpa-onnx exposes online recognizers/streaming model families and hotword mechanisms.

Therefore 000B separates:

1. **C0 unbiased local STT** — no repository/test-specific decoder context;
2. **C1 deterministic engine-agnostic repository resolution** — applied to frozen C0 transcripts;
3. **C2 backend-native context/bias** — reported only as within-backend uplift/degradation relative to the same backend's C0.

It also distinguishes observed `NATIVE_INCREMENTAL`, `CHUNKED_REDECODE`, `BATCH_ONLY`, and `UNKNOWN` streaming semantics instead of treating every upstream `streaming` label as equivalent.

000B is recursively divided into B1 benchmark/candidate qualification, B2 unbiased bakeoff, B3 context uplift, and B4 synthesis. Only B1 is task-refined.

B1 freezes methodology before the primary comparison. It may perform bounded non-comparative qualification smoke, but it does not decode or rank the primary developer-speech test split.

Primary human developer-speech ranking requires explicit consent/retention/redistribution authority. Synthetic/TTS audio may support smoke/regression only. If suitable human audio is unavailable, later primary execution must remain blocked rather than produce a human-speech ranking from synthetic voices.

Shared GitHub-hosted runner timing is diagnostic by default and is not sufficient evidence for general latency/resource superiority.

## What is established

Canonical research authority now contains:

- the active Wispral Constitution v0.1.0;
- proof-before-done and progressive SpecGrain repository discipline;
- architecture invariants without premature dependency selection;
- a progressive H0–H15 program roadmap;
- a source-backed founding research register;
- the WispralBench methodology contract with zero qualifying speech benchmark results so far;
- a founding voice/agent threat model;
- category/adoption strategy with 200k+ stars recorded as ambition rather than engineering evidence;
- Specification 000 as the active research parent;
- verified 000A ACP evidence;
- refined 000B local speech evidence methodology with B1 as the next bounded Grain.

## Current product thesis

Wispral is a voice-native control plane for AI coding agents.

The current thesis is intentionally stronger and narrower than generic dictation:

> A developer should be able to speak to an agent, think aloud without accidentally authorizing action, resolve developer-specific entities against repository context, interrupt and steer execution immediately, and preserve visible authority boundaries across multiple independent agents.

This thesis is a program direction, not a benchmark result or compatibility claim.

## Current architecture posture

The following are the current evidence-aware hypotheses:

- Rust remains the preferred product runtime; no production Cargo workspace is authorized yet.
- ACP is the leading structured integration candidate, classified `PARTIAL` / `MODERATE` by 000A rather than selected as unconditional `PRIMARY`.
- Any future ACP product boundary must be version-aware because current authority contains materially different v1/v2 surfaces while the tested representatives negotiated v1.
- A PTY-based compatibility path may still be required for agents that do not expose sufficient structured semantics.
- Local streaming speech recognition remains a first-class requirement, but no engine/model configuration is selected yet.
- Repository-aware entity resolution may materially improve developer speech quality; 000B now requires raw STT and context uplift to be measured separately.
- `COMMAND` and `ASIDE` remain distinct semantic concepts, but their interaction/classification contract is unselected.
- Push-to-talk remains the preferred first reliable capture hypothesis; hands-free and full duplex require separate evidence.

## Explicit non-claims

Until further evidence exists, Wispral does NOT claim:

- production support for Codex, Claude Code, Gemini CLI, OpenCode, Goose, Copilot CLI, or any other named agent;
- broad ACP compatibility beyond exact 000A observations;
- authenticated ACP prompt/session portability;
- ACP streaming, active cancellation, permission, steering, or v2 runtime portability;
- a winning or production-ready Moonshine, Whisper, sherpa-onnx, or other STT configuration;
- developer entity accuracy for any STT candidate;
- repository-context accuracy uplift;
- sub-second voice latency or any particular STT/finalization latency;
- better transcription than Wispr Flow, Superwhisper, Aqua, Claude Code voice, or any other product;
- Arabic or English product support;
- full-duplex audio or acoustic echo cancellation;
- offline product operation on any named platform merely because candidate runtimes advertise local support;
- production security, accessibility, or privacy qualification;
- macOS, Linux, or Windows product support;
- any release-readiness state;
- any GitHub growth outcome.

## Immediate research gate

The next bounded unit is `000B1-benchmark-candidate-qualification`.

B1 is `GRAIN`, not automatically `READY`. Before execution, re-read the current candidate repositories/releases/model/license truth and the readiness gate in `specs/000B1-benchmark-candidate-qualification/tasks.md`.

No primary benchmark decoding is authorized by B1 readiness alone; B1 itself exists to preregister the later B2 comparison.

No product code is authorized. Product implementation remains blocked until Specification 000 synthesis and 000G select a bounded first implementation Grain from reproducible evidence.

## Next canonical action

After this refinement becomes canonical, recheck B1 readiness. If readiness passes, execute only B1's candidate/methodology qualification tasks and preserve exact evidence. Merge and close B1 before refining B2. Do not run the primary developer-speech bakeoff early.