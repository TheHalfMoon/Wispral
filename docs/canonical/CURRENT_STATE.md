# Wispral Current State

**Repository:** `TheHalfMoon/Wispral`  
**Canonical branch:** `main`  
**Bootstrap commit:** `894644c102a77b65bf53bfab21a3fdd258272ac9`  
**Founding authority merge:** `3cbe212bf7202c37ec322f114c0e5486e5218d9b`  
**ACP qualification merge:** `354695c9f4d406147cbdc425d8f59e841a2f96a3`  
**ACP closeout merge:** `99dd6290ee01ce566d32b92df6d469b66b56520a`  
**000B refinement merge:** `6b5696a6becc360948282712cc9339df9cb3a67c`  
**000B1 evidence merge:** `8df69835349f85d5ae6af9d6a62ef3af24f65f43`  
**000B2 entry-preparation evidence merge:** `49d0f31408ab36f285f5e61228b54a72ca0aec07`  
**000B2 authority-intake merge:** `f71df132f963056b3321fe38b94ed88d6a0dfd89`  
**000B2 trusted authority-structure merge:** `8cc8b1a22edd9268a49b3ad16c4d3ee8c0d6d586`  
**000B2 external-authority runbook merge:** `9e66115a3e17631e7e658b276779d05240fa647b`  
**000B2 trusted participant-policy merge:** `4048ba97471c0d94046cff0625b7f2fe2e2c8f3a`  
**000B2 participant-policy freeze merge:** `ee8a579093c35a93650a8b13f0bac02cecd3f1e8`  
**000B2 trusted participant-materials merge:** `c753635d29deca180af85dfd2f8914bef3ee0ec8`  
**000B2 participant-material identity amendment merge:** `fe8496e5e45160a09e55a6f967dd62e46c0bf47f`  
**000B2 participant-material freeze merge:** `66cca406e69eda33dfd6e0a2adf59ea328eda1c6`  
**Program status:** `SPEC_000_RESEARCH_ACTIVE`  
**Active product implementation:** none  
**Active parent specification:** `000-founding-research` — `REFINING`  
**Verified ACP child:** `000A-acp-qualification` — `VERIFIED`, recommendation `PARTIAL`, confidence `MODERATE`  
**Active research parent:** `000B-stt-entity-bakeoff` — `REFINING`  
**Verified speech child:** `000B1-benchmark-candidate-qualification` — `VERIFIED`  
**000B2 entry preparation:** `CLOSED_CANONICAL`  
**000B2 authority structure:** `CANONICAL`, participant authority still `EXTERNAL`  
**000B2 participant policy:** `CANONICAL_FROZEN`, participant consent `EXTERNAL_NOT_OBTAINED`  
**000B2 participant materials:** `CANONICAL_FROZEN`, participant consent `EXTERNAL_NOT_OBTAINED`  
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
- recommendation: `PARTIAL`, confidence: `MODERATE`;
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

The historical B1 closeout record remains `research/000b1/canonical-closeout.json`.

## Canonical 000B2 entry-preparation proof

PR #10 completed the bounded non-primary B2 entry-preparation unit and merged by guarded expected-head merge from exact head `69b66bc433a146c2146e2b7fec264a8f4ed50ae9` as canonical commit `49d0f31408ab36f285f5e61228b54a72ca0aec07`.

Before that merge, PR #11 canonicalized the trusted-base artifact-identity verifier at `32135294675a372653843560623067d9ad3822d6`, and PR #12 corrected live-base refresh semantics at `248208cffa666a485fe58b7467fdbb2ec7e8b820`.

The decisive trusted runtime proof is workflow `000B2 Trusted Materialization Authority` run `33537242680`, job `99954441750`. It:

- checked out live canonical `main` and resolved `TRUSTED_BASE_SHA=248208cffa666a485fe58b7467fdbb2ec7e8b820`;
- checked out exact candidate head `69b66bc433a146c2146e2b7fec264a8f4ed50ae9` as data only;
- reproduced all 18 pending artifact identities;
- emitted `TRUSTED_000B2_ARTIFACT_IDENTITY=PASS`;
- explicitly emitted `PROCESS_ATTESTATION=NOT_PROVIDED_BY_THIS_GATE`.

The entry-preparation unit canonically establishes:

- all B1-pending Moonshine and sherpa-onnx artifact SHA-256 identities are materialized;
- all six selected candidate cells have bounded deterministic synthetic non-speech `SMOKE_PASS` evidence;
- the deterministic B2 scorer implementation, configuration, and verifier are canonical at merge `49d0f31408ab36f285f5e61228b54a72ca0aec07`;
- FFmpeg `9.0.1` qualification and attempt-state-bound preprocessing capture tooling are prepared;
- attempt-state-bound execution-environment capture tooling is prepared.

This does not create participant/media authority, primary human-speech evidence, independent process chronology, controlled-environment attestation, comparative ranking, or a frozen final B2 attempt.

The historical entry-preparation closeout record is `research/000b2-entry/canonical-closeout.json`; current readiness is `research/000b2-entry/readiness.json`.

## Canonical B2 human-authority structure proof

PR #14 added the fail-closed, non-identifying authority-intake contract and merged from exact head `20961174b5b4603806a6d79963e3bc9e624f5995` as canonical commit `f71df132f963056b3321fe38b94ed88d6a0dfd89`. Exact-head `000B2 Entry Contracts` run `33541279600` passed; post-merge run `33541475726` passed. The canonical authority package and template remain `NOT_AUTHORIZED`.

PR #15 added the trusted structural authority gate and merged from exact head `1516f65cb763a7b50e3f2fa9ebd98ea53d253771` as canonical commit `8cc8b1a22edd9268a49b3ad16c4d3ee8c0d6d586`. Exact-head bootstrap run `33542254408` passed. Post-merge trusted run `33542411499` passed, verified the canonical blocked state, and reverified open main-targeting PRs against the refreshed base.

The trusted structural gate:

- executes verifier code only from live canonical `main`;
- does not check out or execute candidate code;
- reads fixed authority/readiness/state files from immutable candidate head SHAs through the GitHub Contents API;
- validates structural authority metadata without claiming that underlying private consent evidence is genuine;
- emits `PARTICIPANT_CONSENT_ATTESTATION=NOT_PROVIDED_BY_THIS_GATE` and `PRIMARY_MEDIA_ACCEPTANCE=NO`;
- preserves B2 as `BLOCKED_EXTERNAL`.

Durable proof is `research/000b2-entry/authority/canonical-structural-gate.json`.

This is trust-boundary preparation, not participant/media authority. No participant consent was created or verified, no human recording was accepted, and no primary decoding was authorized.

## Canonical B2 participant policy and participant-material proof

PR #19 added the external authority runbook and policy-fingerprint helper, then merged as `9e66115a3e17631e7e658b276779d05240fa647b`. The runbook keeps identity-bearing consent artifacts, identity mappings, signatures, contact data, withdrawal evidence, and raw authority-review notes outside the public repository and explicitly does not attest consent or authorize recording.

PR #21 established the trusted participant-policy gate at `4048ba97471c0d94046cff0625b7f2fe2e2c8f3a`; PR #20 then froze the project-controlled participant policy at `ee8a579093c35a93650a8b13f0bac02cecd3f1e8`. The frozen policy fixes consent scope, recording purpose, public raw-audio redistribution as prohibited, repository storage boundaries, retention, pre-freeze withdrawal, derivative-artifact scope, privacy constraints, and prohibited-content controls. Its policy SHA-256 is `454b208884211f83fc3ed62c22844d2a72d37dafbaa001793d791e91faecc811`.

PR #22 established the trusted participant-material gate at `c753635d29deca180af85dfd2f8914bef3ee0ec8`. Independent review on PR #23 then identified an exact-template binding defect; PR #24 corrected the trusted identities and merged as `fe8496e5e45160a09e55a6f967dd62e46c0bf47f`. PR #23 subsequently froze the corrected participant-facing material set at `66cca406e69eda33dfd6e0a2adf59ea328eda1c6` after exact-head CI and independent CodeRabbit review `5090599306`.

The frozen participant-material identities are:

- participant information/consent template SHA-256 `dd4143145674473ea56122a7e7e23cfc95c08cb99840b451b190bc92fb3d93b6`;
- recording-entry checklist SHA-256 `b4e9f8fdf54c0809bb5f44d004c61c6e621506fef64888b92cec407ca05d0a55`;
- deterministic material-set SHA-256 `5f96a7ff1ab63371c0396a93ccaa140b4d82bf567e62e64c9b0ed7520997034c`.

Post-merge verification at `66cca406e69eda33dfd6e0a2adf59ea328eda1c6` completed successfully in:

- `000B2 Trusted Materialization Authority` run `33639022112`;
- `000B2 Trusted Human Authority Structure` run `33639022068`;
- `000B2 Entry Contracts` run `33639022116`;
- `000B2 Trusted Participant Materials` run `33639022133`;
- `000B2 Trusted Participant Policy` run `33639022138`.

These controls make the project-controlled policy and participant-facing material exact and reviewable. They do not make consent self-authenticating. The authority package remains `NOT_AUTHORIZED`, `participant_count=0`, `consent_records_sha256=null`, and `authority_effective_before_recording=false`. No participant identity, signature, consent chronology, human recording, or corpus has been accepted by these repository-side units.

## B2 blocked successor

`000B2-unbiased-stt-bakeoff` remains `BLOCKED_EXTERNAL`, not `READY`.

Primary developer-speech decoding must not begin until all remaining gates are satisfied. Current blockers are:

- real human developer-speech participant/media authority is absent: the project-controlled policy and participant-facing materials are frozen, but no real participant consent has been obtained or independently verified, the authority package remains `NOT_AUTHORIZED`, `participant_count=0`, and no consent-bundle digest is bound;
- authorized human recordings, consent records, speaker-disjoint split manifests, and a frozen primary test manifest are absent;
- accepted attempt-bound FFmpeg `9.0.1` binary/version/config identity and preprocessing execution evidence under separately reviewable execution chronology is absent;
- accepted attempt-bound execution-environment and hardware-fingerprint evidence under separately reviewable chronology/control evidence is absent;
- no final B2 attempt manifest exists with `frozen=true` and a matching freeze digest.

Synthetic/TTS audio may support smoke/harness/regression only. It cannot satisfy the human developer-speech authority gate and cannot enter the primary human ranking. Repository-owner approval, structural authority metadata, frozen project policy, frozen participant-facing materials, or a consent-record digest cannot substitute for real participant/media authority.

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
- canonical B2 entry-preparation evidence for artifact identities, bounded smoke qualification, and scorer revision;
- canonical fail-closed B2 authority-intake and trusted structural verification surfaces;
- canonical frozen participant policy and exact participant-facing/operator-entry materials, without real participant consent;
- explicit remaining B2 external/attempt-time readiness blockers.

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

Verified 000A, verified 000B1, canonical B2 entry preparation, canonical B2 authority structure, and canonical participant policy/materials do not weaken this gate.

## Next canonical action

Preserve B2 as `BLOCKED_EXTERNAL`. Use the exact frozen participant policy and participant-facing materials in the real external consent process, establish independently genuine participant/media authority, and collect the authorized frozen human developer-speech corpus under that authority. Repository structure, policy, and templates are prepared, but none is consent. Only then prepare a separately reviewable B2 attempt that captures preprocessing and execution-environment evidence before primary decoding, freezes the final manifest, and rechecks readiness from canonical `main`. If those gates cannot be satisfied, preserve the block rather than substitute synthetic primary evidence or prematurely advance B3/B4.
