# Wispral Current State

**Repository:** `TheHalfMoon/Wispral`  
**Canonical branch:** `main`  
**Bootstrap commit:** `894644c102a77b65bf53bfab21a3fdd258272ac9`  
**Program status:** `FOUNDING_AUTHORITY_CANDIDATE`  
**Active product implementation:** none  
**Active specification:** `000-founding-research` once this authority becomes canonical  
**Published release:** none

Live GitHub and repository truth override this document.

## What is established

The repository exists and has a minimal bootstrap README. No product implementation, compatibility matrix, speech engine, ACP integration, PTY integration, benchmark result, latency claim, accuracy claim, release, package, installer, security qualification, or supported-platform claim exists yet.

The founding authority branch is intended to establish:

- project constitution and operating discipline;
- architecture invariants and explicit hypotheses;
- a progressive program roadmap;
- the first research specification;
- benchmark and security contracts;
- a truthful category and adoption strategy.

None of those candidate documents become canonical merely because they exist on a branch.

## Current product thesis

Wispral is a voice-native control plane for AI coding agents.

The current thesis is intentionally stronger and narrower than generic dictation:

> A developer should be able to speak to an agent, think aloud without accidentally authorizing action, resolve developer-specific entities against repository context, interrupt and steer execution immediately, and preserve visible authority boundaries across multiple independent agents.

This thesis is a program direction, not a benchmark result or compatibility claim.

## Current architecture posture

The following are hypotheses pending Specification 000 evidence:

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

## Execution gate

No product code is authorized before the founding authority is canonical and Specification 000 selects a bounded first implementation unit from reproducible research evidence.

The immediate frontier is research, protocol qualification, benchmark design, threat modeling, licensing/provenance, and architecture decision preparation.

## Completion condition for founding authority

This founding authority becomes canonical only when:

1. the exact candidate diff is reviewed for internal consistency;
2. the branch head and changed paths are reconciled;
3. any configured repository checks for the exact head succeed, or their absence is recorded truthfully;
4. no unresolved review finding blocks merge;
5. the candidate merges without overwriting a moved head; and
6. canonical `main` is re-read after merge.

After that, `specs/CURRENT.md` governs the executable frontier.