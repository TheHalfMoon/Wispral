# Wispral Current State

**Repository:** `TheHalfMoon/Wispral`  
**Canonical branch:** `main`  
**Bootstrap commit:** `894644c102a77b65bf53bfab21a3fdd258272ac9`  
**Founding authority merge:** `3cbe212bf7202c37ec322f114c0e5486e5218d9b`  
**ACP qualification merge:** `354695c9f4d406147cbdc425d8f59e841a2f96a3`  
**ACP qualification PR:** `#3`  
**Program status:** `SPEC_000_RESEARCH_ACTIVE`  
**Active product implementation:** none  
**Active parent specification:** `000-founding-research` — `REFINING`  
**Verified child:** `000A-acp-qualification` — `VERIFIED`, recommendation `PARTIAL`, confidence `MODERATE`  
**Next refinement candidate:** `000B` — local streaming STT and developer-entity benchmark bakeoff; not `READY`  
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

The guarded merge produced canonical commit `354695c9f4d406147cbdc425d8f59e841a2f96a3`, which is GitHub-signature verified.

The verified result is intentionally bounded:

- both representatives completed real ACP v1 initialization;
- both exposed structured capability/authentication metadata;
- Gemini returned `session/new=AUTH_REQUIRED` and `session/list=METHOD_NOT_FOUND`;
- Codex ACP returned `session/new=AUTH_REQUIRED` and `session/list=AUTH_REQUIRED`;
- authenticated prompt execution, streaming, active cancellation, structured permission behavior, Codex steering behavior, and representative ACP v2 runtime interoperability were not observed;
- the recommendation is therefore `PARTIAL`, not `PRIMARY`, with `MODERATE` confidence.

The repository preserves raw sanitized evidence, package integrity, a capability matrix, an evidence review, and an independent deterministic verifier under `docs/research/acp/` and `research/000a/`.

## What is established

Canonical `main` contains:

- the active Wispral Constitution v0.1.0;
- repository operating discipline derived from proof-before-done and progressive SpecGrain principles;
- architecture invariants without premature dependency selection;
- a progressive H0–H15 program roadmap;
- a source-backed founding research register;
- the WispralBench methodology contract with zero qualifying speech benchmark results so far;
- a founding voice/agent threat model;
- category/adoption strategy with 200k+ stars recorded as ambition rather than engineering evidence;
- Specification 000 as the active research parent;
- Specification 000A as a verified ACP qualification child;
- evidence that ACP is a credible structured-control candidate but still requires authenticated semantic qualification before an unconditional production selection.

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
- Local streaming speech recognition should be a first-class option, but no engine is selected yet.
- Repository-aware entity resolution may materially improve developer speech quality, but the improvement must be measured.
- `COMMAND` and `ASIDE` should be separate semantic classes, but the exact user interaction and classification contract remain unselected.
- Push-to-talk remains the preferred first reliable capture hypothesis; hands-free and full duplex require separate evidence.

## Explicit non-claims

Until further evidence exists, Wispral does NOT claim:

- production support for Codex, Claude Code, Gemini CLI, OpenCode, Goose, Copilot CLI, or any other named agent;
- broad ACP compatibility beyond the exact 000A observations;
- authenticated ACP prompt/session portability;
- ACP streaming, active cancellation, permission, steering, or v2 runtime portability;
- sub-second latency;
- a particular interruption latency;
- better transcription than Wispr Flow, Superwhisper, Aqua, Claude Code voice, or any other product;
- better local STT performance from Moonshine, Whisper, sherpa-onnx, or another engine;
- repository-context accuracy uplift;
- full-duplex audio or acoustic echo cancellation;
- offline operation on any named platform;
- production security, accessibility, or privacy qualification;
- macOS, Linux, or Windows product support;
- any release-readiness state;
- any GitHub growth outcome.

## Immediate research gate

000A is complete and verified.

The next child eligible for bounded refinement is `000B` — local streaming STT and developer-entity benchmark bakeoff.

000B is not automatically `READY`. Before any comparative benchmark execution, its refinement must define a reproducible benchmark/scoring contract, pin current candidate engines and provenance, define fixture/corpus licensing, isolate engine-quality evidence from repository-context uplift evidence, and establish environment/readiness constraints.

No product code is authorized. Product implementation remains blocked until Specification 000 synthesis selects a bounded first implementation Grain from reproducible evidence.

## Next canonical action

After this 000A closeout becomes canonical, refine 000B from current live speech-engine and WispralBench truth. Do not run a bakeoff or select an engine until the resulting 000B Grain independently satisfies readiness. After every completed research child, merge exact evidence first, re-read canonical authority, and only then refine the next child.