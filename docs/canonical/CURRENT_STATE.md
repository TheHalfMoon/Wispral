# Wispral Current State

**Repository:** `TheHalfMoon/Wispral`  
**Canonical branch:** `main`  
**Bootstrap commit:** `894644c102a77b65bf53bfab21a3fdd258272ac9`  
**Founding authority merge:** `3cbe212bf7202c37ec322f114c0e5486e5218d9b`  
**Founding authority PR:** `#1`  
**Program status:** `SPEC_000_RESEARCH_ACTIVE`  
**Active product implementation:** none  
**Active parent specification:** `000-founding-research` — `REFINING`  
**Near frontier:** `000A-acp-qualification` — `GRAIN`, readiness recheck required before execution  
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

## What is established

Canonical `main` now contains:

- the active Wispral Constitution v0.1.0;
- repository operating discipline derived from proof-before-done and progressive SpecGrain principles;
- architecture invariants without premature dependency selection;
- a progressive H0–H15 program roadmap;
- a source-backed founding research register;
- the WispralBench methodology contract with zero qualifying results;
- a founding voice/agent threat model;
- category/adoption strategy with 200k+ stars recorded as ambition rather than engineering evidence;
- Specification 000 as the active research parent;
- Specification 000A as the only task-refined near-term Grain.

## Current product thesis

Wispral is a voice-native control plane for AI coding agents.

The current thesis is intentionally stronger and narrower than generic dictation:

> A developer should be able to speak to an agent, think aloud without accidentally authorizing action, resolve developer-specific entities against repository context, interrupt and steer execution immediately, and preserve visible authority boundaries across multiple independent agents.

This thesis is a program direction, not a benchmark result or compatibility claim.

## Current architecture posture

The following remain hypotheses pending Specification 000 evidence:

- Rust is the preferred product runtime.
- ACP is the preferred structured agent integration path when it exposes sufficient lifecycle, streaming, permission, and cancellation semantics.
- A PTY-based compatibility path may be required for agents that do not expose a suitable protocol.
- Local streaming speech recognition should be a first-class option, but no engine is selected yet.
- Repository-aware entity resolution may materially improve developer speech quality, but the improvement must be measured.
- `COMMAND` and `ASIDE` should be separate semantic classes, but the exact user interaction and classification contract remain unselected.
- Push-to-talk should be the first reliable capture mode; hands-free and full duplex require separate evidence.

## Explicit non-claims

Until evidence exists, Wispral does NOT claim:

- support for Codex, Claude Code, Gemini CLI, OpenCode, Goose, Copilot CLI, or any other agent;
- ACP compatibility;
- sub-second latency;
- a particular interruption latency;
- better transcription than Wispr Flow, Superwhisper, Aqua, Claude Code voice, or any other product;
- better local STT performance from Moonshine, Whisper, sherpa-onnx, or another engine;
- full-duplex audio or acoustic echo cancellation;
- offline operation on any named platform;
- production security, accessibility, or privacy qualification;
- macOS, Linux, or Windows support;
- any release-readiness state;
- any GitHub growth outcome.

## Immediate execution gate

The next research unit is `000A-acp-qualification`.

It is `GRAIN`, not automatically `READY`. Before execution, re-read current ACP specification/SDK/registry truth and recheck the readiness conditions in `specs/000A-acp-qualification/tasks.md`.

No product code is authorized. Product implementation remains blocked until Specification 000 synthesis selects a bounded first implementation Grain from reproducible evidence.

## Next canonical action

Execute or further refine 000A only after its readiness recheck. After each completed research child, merge exact evidence first, re-read canonical authority, and only then refine the next child.