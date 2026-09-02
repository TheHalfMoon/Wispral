# Wispral Specification Frontier

**Status:** founding research — ACP verified; STT preregistration verified; B2 entry preparation, authority structure, participant policy, and participant materials canonical; B2 externally blocked

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

See `research/000b1/canonical-closeout.json` for the historical B1 closeout proof. Current B2 readiness is owned by `research/000b2-entry/readiness.json`; historical entry-preparation closeout remains `research/000b2-entry/canonical-closeout.json`.

## B2 entry preparation — canonical

Entry-preparation evidence merged as `49d0f31408ab36f285f5e61228b54a72ca0aec07` from exact qualified head `69b66bc433a146c2146e2b7fec264a8f4ed50ae9`.

The bounded preparation unit canonically establishes:

- all 18 B1-pending candidate artifact SHA-256 identities are materialized;
- canonical-base trusted artifact reproduction passed in run `33537242680` against live canonical base `248208cffa666a485fe58b7467fdbb2ec7e8b820` and exact candidate head `69b66bc433a146c2146e2b7fec264a8f4ed50ae9`;
- all six selected candidate cells have bounded deterministic synthetic non-speech `SMOKE_PASS` evidence;
- the deterministic B2 scorer implementation, configuration, and verifier are canonical at the entry-preparation evidence merge;
- FFmpeg `9.0.1` qualification plus attempt-state-bound preprocessing capture tooling are prepared;
- attempt-state-bound execution-environment capture tooling is prepared.

These preparation results do **not** provide process chronology attestation, participant/media authority, primary human-speech evidence, a controlled performance-environment attestation, or a frozen B2 attempt.

## B2 human-authority structure — canonical, authority still external

PR #14 canonicalized fail-closed authority-intake structure at merge `f71df132f963056b3321fe38b94ed88d6a0dfd89` from exact head `20961174b5b4603806a6d79963e3bc9e624f5995`. Exact-head `000B2 Entry Contracts` run `33541279600` passed, and post-merge run `33541475726` passed. The canonical authority package and template remain `NOT_AUTHORIZED`.

PR #15 canonicalized the trusted structural gate at merge `8cc8b1a22edd9268a49b3ad16c4d3ee8c0d6d586` from exact head `1516f65cb763a7b50e3f2fa9ebd98ea53d253771`. Exact-head bootstrap run `33542254408` passed; post-merge trusted run `33542411499` passed and rechecked the canonical blocked state plus open main-targeting PRs against the refreshed base.

The trusted gate:

- executes verifier code from live canonical `main` only;
- does not check out or execute candidate code;
- reads only non-executable candidate authority/readiness/state data from an immutable exact head SHA;
- structurally validates `AUTHORIZED` or `NOT_AUTHORIZED` metadata without claiming that the underlying consent is genuine;
- always preserves `PARTICIPANT_CONSENT_ATTESTATION=NOT_PROVIDED_BY_THIS_GATE`, `PRIMARY_MEDIA_ACCEPTANCE=NO`, and `B2_READY=NO`.

Durable proof is `research/000b2-entry/authority/canonical-structural-gate.json`.

This structure reduces accidental or candidate-controlled self-authorization. It does **not** create participant consent, verify a private consent artifact, authorize recording, accept primary media, or satisfy the external human-authority blocker.

## B2 participant policy and materials — canonical, participant consent still external

Readiness-only follow-up work removed repository-controlled ambiguity without converting project policy into participant authority:

- PR #19 merged the external human-authority runbook as `9e66115a3e17631e7e658b276779d05240fa647b`;
- PR #21 merged the trusted participant-policy gate as `4048ba97471c0d94046cff0625b7f2fe2e2c8f3a`;
- PR #20 froze the project-controlled participant policy as `ee8a579093c35a93650a8b13f0bac02cecd3f1e8`;
- PR #22 merged the trusted participant-material gate as `c753635d29deca180af85dfd2f8914bef3ee0ec8`;
- PR #24 amended the trusted participant-material identities after independent review as `fe8496e5e45160a09e55a6f967dd62e46c0bf47f`;
- PR #23 froze the participant-facing information/consent template, operator recording-entry checklist, and material-set record as `66cca406e69eda33dfd6e0a2adf59ea328eda1c6`.

The canonical frozen identities are:

- participant policy SHA-256: `454b208884211f83fc3ed62c22844d2a72d37dafbaa001793d791e91faecc811`;
- participant information/consent template SHA-256: `dd4143145674473ea56122a7e7e23cfc95c08cb99840b451b190bc92fb3d93b6`;
- recording-entry checklist SHA-256: `b4e9f8fdf54c0809bb5f44d004c61c6e621506fef64888b92cec407ca05d0a55`;
- deterministic participant-material set SHA-256: `5f96a7ff1ab63371c0396a93ccaa140b4d82bf567e62e64c9b0ed7520997034c`.

Post-merge verification on `66cca406e69eda33dfd6e0a2adf59ea328eda1c6` passed `000B2 Trusted Materialization Authority` run `33639022112`, `000B2 Trusted Human Authority Structure` run `33639022068`, `000B2 Entry Contracts` run `33639022116`, `000B2 Trusted Participant Materials` run `33639022133`, and `000B2 Trusted Participant Policy` run `33639022138`.

The owner-controlled policy now fixes consent scope, recording purpose, raw-audio public redistribution as prohibited, repository storage boundaries, retention, pre-freeze withdrawal, derivative-artifact scope, privacy constraints, and prohibited-content controls. The participant-facing materials bind that exact policy and remain fail-closed.

This does **not** establish real participant consent or participant/media authority. The canonical authority package remains `NOT_AUTHORIZED`, with `participant_count=0`, `consent_records_sha256=null`, and `authority_effective_before_recording=false`. No participant identity, signature, consent chronology, human recording, or corpus evidence has been accepted by these repository-side controls.

## Blocked successor

`000B2-unbiased-stt-bakeoff`

State: `BLOCKED_EXTERNAL`

B2 is not `READY` and primary decoding is not authorized. Current blockers are now limited to:

- real human developer-speech participant/media authority is absent: the project-controlled policy and participant-facing materials are frozen, but no real participant consent has been obtained or independently verified, the authority package remains `NOT_AUTHORIZED`, `participant_count=0`, and no consent-bundle digest is bound;
- authorized human recordings, consent records, speaker-disjoint split manifests, and a frozen primary test manifest are absent;
- accepted attempt-bound FFmpeg `9.0.1` binary/version/config identity and preprocessing execution evidence under separately reviewable execution chronology is absent;
- accepted attempt-bound execution-environment and hardware-fingerprint evidence under separately reviewable chronology/control evidence is absent;
- no final `frozen=true` B2 attempt manifest with a matching freeze digest exists.

Synthetic/TTS media cannot satisfy the human developer-speech authority gate or enter the primary ranking. Repository-owner approval cannot substitute for participant/media authority. A structurally valid authority package, frozen project policy, frozen participant-facing material, or consent digest also cannot substitute for independently real participant authority.

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

Neither verified 000A, verified 000B1, canonical B2 entry preparation, canonical B2 authority structure, nor the frozen participant policy/materials weakens this gate.

## Live-truth rule

Live canonical GitHub/repository truth overrides this file. After each merged research/refinement unit, re-read current authority before refining or starting the next child.

## Next canonical action

Preserve B2 as `BLOCKED_EXTERNAL`. Use the exact frozen participant policy and participant-facing materials in the real external consent process, establish independently genuine participant/media authority, and collect the authorized frozen human developer-speech corpus under that authority. Repository structure, policy, and templates are prepared, but none is consent. Only after real external evidence exists may a separately reviewable attempt be prepared to capture preprocessing and execution-environment evidence before any primary decode, freeze the final attempt manifest, and recheck readiness from canonical `main`. Do not substitute synthetic primary evidence or prematurely advance B3/B4.
