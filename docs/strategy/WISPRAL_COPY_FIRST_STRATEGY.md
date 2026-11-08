# Wispral copy-first strategy

**Status:** CANDIDATE PLAN. Part of the [World-Class Master Plan](WISPRAL_WORLD_CLASS_MASTER_PLAN.md). Exact repositories, commit SHAs, paths, licenses and evidence are in [SOURCE_DECISION_MATRIX.md](../../research/wispral-world-class/SOURCE_DECISION_MATRIX.md). The PR #124 [transplant matrix](../../research/rea/2026-10-21/SOURCE_TRANSPLANT_MATRIX.md) (75 mechanisms, 96/96 source anchors re-verified by Opus in PR #125) remains the mechanism-level evidence base.

```text
COPY → ADAPT → INTEGRATE → TEST → IMPROVE
```

## 1. Rights posture

- `FOUNDER_SOURCE_AUTHORIZATION=YES_CONFIRMED_BY_FOUNDER` · `CONFIDENTIAL_GRANTS=HELD_PRIVATELY_BY_FOUNDER_NOT_SHARED` ([founder record](FOUNDER_SOURCE_REUSE_AND_PRODUCT_IDENTITY.md)). The documents are not requested and were not inspected. Their confidentiality is not treated as missing permission.
- Founder-confirmed rights and independently inspected public licenses are recorded in **separate columns**. Copied files keep their copyright headers, LICENSE and NOTICE files; renaming the product does not change authorship.
- Separately licensed items are qualified on their own: model weights, tokenizers, datasets, fonts, voices, media, trademarks. An unclear item is isolated and does not block unrelated code work.
- Closed competitors are studied only through public documentation and lawful observation. No proprietary implementation is copied.

## 2. Decision framework

For every subsystem the options are evaluated in this order, and the first option that meets the requirement at the lowest total cost wins:

| Rank | Mode | Use when | Example in this plan |
| --- | --- | --- | --- |
| 1 | **FORK** an authorized application | The donor already *is* most of the product, with tests, UI, packaging and a coherent ownership graph | Handy → WisprSide; VoiceStudio → WisprStudio |
| 2 | **COPY** a qualified subsystem or file unchanged | A pure, well-tested mechanism fits as is | VoiceStudio `fit_planner.py` byte-for-byte behind a separate guard |
| 3 | **ADAPT** a module | Small mismatch with Wispral contracts | Sentrdel narrowing lattice → `wispral-policy` |
| 4 | **WRAP** a package or service | Stable library or service boundary | Parlant service; whisper.cpp / sherpa-onnx; ACP Rust SDK |
| 5 | **API_INTEGRATION** | A product is best run unmodified | Chatwoot via Agent Bot API and webhooks |
| 6 | **FORK_DELTA** | Change inside a retained fork, tied to a finding | Target-identity check in the Handy paste path |
| 7 | **BUILD_NEW** | Only after the five questions in §4 are answered | Klaint deterministic broker |

**Cost dimensions compared** (estimated, never presented as measured): engineering to integrate; security exposure; upstream sync and rebase cost; dependency closure size; existing test coverage retained; runtime isolation; cross-platform packaging; maintenance ownership.

**Anti-patterns rejected:** clean-room rewrites for elegance; assembling three incompatible apps into one; copying a whole platform to use one module; a second engine, queue, supervisor or inventory beside the donor's.

## 3. Per-product strategy

### 3.1 WisprSide — fork Handy

- **Lead:** pinned fork of `cjpais/Handy` (MIT, Rust/Tauri 2 + React). Keep the recorder, hotkeys, coordinator, engine supervisor, model manager, paste path, overlay, settings, history, tray, packaging and updater. ([decision D-01](../../research/wispral-world-class/DECISION_LEDGER.md))
- **Re-pin:** `cjpais/Handy@73cc8579cff74e97e08de9d86035a92e4335ff7f` (2026-11-06; v0.10.0 plus TLS-advisory dependency bumps), replacing the 2026-10-21 pin `93c9ee05`. The newer revision includes three security fixes the fork would otherwise need to backport, and all nine of its CI check runs succeeded (`REPRODUCED` via the GitHub API on 2026-11-08). The modules the plan depends on (`paste_tx/*`, `engine_supervisor/*`, `secure_input.rs`) are unchanged since the old pin.
- **Narrow donors:** FreeFlow's MIT `AppTextInsertionCore` (`zachlatta/freeflow@37786464`) as the **algorithm** donor for fail-closed insertion (double re-verification before and after clipboard preparation; `inserted / notInserted / unverified / unavailable`); OpenWhispr's Windows UIA editable-field probe and `GetExeName` as ADAPT references (its fall-through to the current foreground window and its nircmd/PowerShell fallback are **rejected**); VoiceInk's outcome vocabulary (GPLv3) as concept only.
- **Deltas (each tied to a finding and a fixture):** egress lockdown (Handy's update check is on by default today); compile out the transcription hook and external-script paste; non-null webview CSP; target-identity binding and fail-closed delivery; make Handy's existing receipt-based clipboard transaction the Windows default; elevated/password/secure-desktop refusal; `DeliveryOutcome` with partial reporting; Arabic match-key normalization; cancellation completeness; Windows CI test job; Wispral-owned signing and updater keys; design system.
- **Branches:** `upstream/handy` (tracks the pin), `wisprside/main` (deltas), plus `DELTA_REGISTER.md` (finding → file → fixture → upstream status → rollback).

### 3.2 WisprStudio — fork VoiceStudio

- **Lead:** pinned fork of `debpalash/VoiceStudio@200286ccff6f28faaf51bb08b2a5b54c460b39f4` (v0.5.8; AGPL-3.0 publicly; reuse covered by founder-confirmed grants, recorded per file). Keep projects, timeline, script editor, engine registry with per-engine subprocess environments, model acceptance, consent capture, watermark, long-form resume, dubbing pipeline, export and its test suites (869 Python and 753 Electron test files counted, not run). Upstream moves about 118 commits a day and is drifting toward open-core, so the fork rebases in scheduled windows driven by the delta register. ([decision D-02](../../research/wispral-world-class/DECISION_LEDGER.md))
- **Deltas (from the 2026-11-08 source audit):** remove or disable the upstream update check (on by default, 10 s after launch), cloud account and sync, the Hugging Face race against the third-party `hf-mirror.com`, third-party runtime mirrors (`gh-proxy.com`, `ghproxy.net`, `mirrors.aliyun.com`), the committed analytics key, and yt-dlp URL and YouTube search; replace the **non-commercial OmniVoice default engine**; enforce consent on every synthesis, dubbing, conversion and cloning path (today **none checks it**) with revocation that cancels queued work; force watermarking on cloned output; a `fit_inputs` guard before the unchanged `plan_fit` that rejects NaN, Inf, negative and inverted input but **allows overlapping segments** (upstream supports them deliberately); Arabic proclitic-aware pronunciation matching; truthful cancel states; an offline staging manifest; a Chatterbox Multilingual subprocess engine adapter (it is not a native engine on Windows or Linux); design system and RTL script editing.
- **Engines:** benchmark VoiceStudio's built-in Arabic-listed engines with permissive records (VoxCPM2, MOSS-TTS-Nano; cards to verify) **before** building any new adapter; the Chatterbox Multilingual adapter (ST-D06) is built only if they fail the rights or quality gate. Non-commercial engines may remain for clearly labelled personal evaluation where the license allows and are blocked in commercial profiles. **Timeline:** the MVP uses VoiceStudio's existing segment timeline; a DAW-style multitrack editor is tier L with Voicebox (MIT) as the donor candidate. **Lead check:** packet ST-D00b compares Voicebox and VoiceStudio on MVP-tier capabilities, delta count and dependency size before the fork is committed.

### 3.3 Klaint — wrap Parlant, integrate Chatwoot, build only the broker

- **Lead:** `emcie-co/parlant` (Apache-2.0) v4.0.2 `2a463ccd`, conditional on compatibility spike KT-01, with v3.3.2 `61bba3b2` as the documented fallback; one Parlant process per tenant. **Parlant 4 is a breaking rewrite:** strict canned responses, journeys, the evaluations API and the Plan hook were removed. Wispral therefore uses v4's rules and policies, retrievers, the `on_reviewing_tool_calls` review hook and an `on_message_generated` commitment guard, and adopts tau2-bench (MIT) for simulation and deterministic scoring. ([decision D-04](../../research/wispral-world-class/DECISION_LEDGER.md))
- **Integration:** Chatwoot v4.19.1 (MIT outside `enterprise/`) run unmodified through its Agent Bot API and webhooks, one account and bot per tenant (bot tokens are account-wide; webhooks are at-least-once). standard-webhooks (Apache-2.0) for signature, timestamp and replay checks. Pipecat v1.15.0 (BSD-2-Clause) inside the same tenant process for voice later, with **no mutating tools registered in Pipecat** (barge-in cancels in-flight function calls by default). Botpress schemas are references for thin Python connectors.
- **Build new (justified):** the deterministic tool broker with its Python policy module (allowlist, argument schema, scope checks and the ASK/UNDECIDABLE resolution, adapted from Sentrdel's concepts) and outcome ledger, the commitment guard, the ownership-epoch bridge to Chatwoot, and later (tier S) the operations console. The MVP is **one hardened Parlant process** (production mode, loopback only, dashboard and plugin tool server off); the multi-tenant host and gateway (KT-02, ADAPT of Parlant's authentication modules) and real connectors are tier S.

### 3.4 Wispral platform — adapt founder modules into contracts

- **Contracts first, crates later.** The eight contracts are language-neutral JSON Schemas with fixtures (CORE-01). The Rust `wispral-policy` (Sentrdel lattice and bounded JSON) and `wispral-journal` (orcel-journal, copied unchanged) crates are deferred until a second Rust consumer exists (A-01); Klaint's policy lives in its Python broker and its ledger is a database table with the same state table. Orcel's audit record and Ascout's engine descriptor shaped the provenance and manifest contracts. Ninerr's network policy stays a reference for later Klaint connectors. ACP rust-sdk 5.0 is wrapped later for the developer-agent module.
- Founder repositories are not merged wholesale into Wispral. Only named modules with tests are adapted.

## 4. Build-new register

Each entry answers the five mandatory questions. Anything not listed here must not be built new.

| ID | Component | Inspected sources | Why they cannot be used as is | Smallest missing capability | Confined to | Test and maintenance cost (estimate) |
| --- | --- | --- | --- | --- | --- | --- |
| BN-01 | **Windows target binding + fail-closed verdict** (WisprSide) | Handy `actions.rs`, `clipboard.rs`, `paste_tx/windows.rs` (no target identity); OpenWhispr `windows-fast-paste.c` (HWND only, falls through to current foreground); FreeFlow `AppTextInsertionCore.swift` (correct algorithm, macOS AX only); VoiceInk (macOS) | No donor has a Windows binding of HWND + PID + process start time + focused control + UIA element that refuses on mismatch | Pure `verdict()` function + one Windows capture module; checks before clipboard mutation and again right before injection | New `paste_tx/target.rs` (pure, testable on Linux CI) + `paste_tx/target_windows.rs`; ~20 lines at two call sites | Small upstream-conflict surface (new files); needs a Windows fixture app and a `windows-latest` test job |
| BN-01b | **Password / elevated / secure-desktop refusal** (WisprSide) | Handy `secure_input.rs` (macOS hotkey resilience only); OpenWhispr UIA `IsPassword`/editable probe (no integrity check) | UIPI blocking is silent per Microsoft's `SendInput` documentation; no donor compares integrity levels | Token integrity comparison + UIA predicate port + `ES_PASSWORD` check | Inside BN-01's module | Elevated and password-box fixtures (GitHub Windows runners run as administrator) |
| BN-01c | **`DeliveryOutcome` envelope with partial reporting** (WisprSide) | Handy `Result<(), String>` + `TranscriptionOutcome::Typed`; VoiceInk / FreeFlow vocabularies | Handy reports "Typed" at chord time, before any receipt, and has no partial state | One enum; receipt channel from `paste_tx`; chunked `SendInput` typer that never splits surrogate pairs | `clipboard.rs`, `input.rs`, `actions.rs`, history migration | Mapping unit tests, receipt fixtures, migration up/down test |
| BN-01d | **Egress observation harness** (all desktop products) | Handy CI (none); Opus S5 requirement | No donor proves offline behaviour | CI job: fresh profile, preinstalled model, full push-to-talk session on fixture audio, OS connection log must be empty for the process tree | Test-only | Windows runner with firewall/pktmon logging; OS-noise allowlist scoped to the process tree |
| BN-02 | **Deterministic tool broker + outcome ledger** (Klaint) | Parlant ToolService and Plan hook; Botpress connectors; Chatwoot handoff; Rasa action server | Parlant has an alternate tool path past the Plan hook; no donor resolves tenant credentials server-side, assigns idempotency keys and reconciles unknown outcomes | Brokered ToolService implementation + ledger table + reconciliation loop | One Python package inside the Klaint service | ~800–1,500 LOC plus adversarial fixture suites (estimate); medium churn as connectors grow |
| BN-03 | **Consent enforcement points** (WisprStudio) | VoiceStudio `record_consent` and profile consent tests; Chatterbox watermark | Consent is recorded but not re-checked at render, resume and cache reuse, and revocation semantics are not a single contract | Consent-epoch checks at four points + revocation cascade | VoiceStudio job registry and profile service (fork delta) | ~200–500 LOC plus revocation fixtures (estimate) |
| BN-04 | **Rights manifest enforcement** (WisprStudio, WisprSide) | VoiceStudio model acceptance; Handy model manager | Donors record terms acceptance but not a weight-license field with commercial-profile blocking | `model_manifest` rows + a profile check at load | Model managers (fork delta) | ~150–300 LOC (estimate) |
| BN-05 | **Ownership-epoch bridge to Chatwoot** (Klaint) | Chatwoot `conversation.rb` handoff ("best-effort, not a lock") | Not race-safe for AI-versus-human sends | Epoch on Klaint side; stale-epoch sends rejected | Klaint service | ~200–400 LOC plus race fixtures (estimate) |
| BN-06 | **Klaint operations console views** (why panel, Test Lab runner UI, audit search) | Parlant APIs and evaluations; Chatwoot UI; Botpress Studio (cloud components not in the public repo) | No inspected open-source console presents policy verdicts, ledger outcomes and evaluations together for non-experts | Web views over existing APIs | Klaint console app | Largest new UI surface; mitigated by design-system components (estimate: several weeks of UI work) |
| BN-07 | **Shared contracts + fixtures** (platform) | Sentrdel, Orcel, Ascout, ACP SDK types | Each donor uses its own types and lifetimes | Eight small schemas with shape, runtime, sequence and bundle fixtures | `docs/engineering/contracts/` → `contracts/v1/` | Drafted and passing (114 cases, 10 sequences, 6 bundles) |
| BN-08 | **Arabic text tooling**: evaluation normalization, segmentation, meaning-distortion rubric, and WisprSide's custom-word match-key normalizer (SD-R7) | Existing WispralBench scorer; public ASR normalizers; Handy `text.rs` (ASCII-only fuzzy keys); VoiceInk, OpenWhispr, FreeFlow | No inspected scorer or donor normalizes Arabic script for matching or implements the WB-AR rules | Normalizer + segment tags + rubric; matching keys only, never rewriting output | Benchmark tooling and `audio_toolkit/text.rs` | Small (estimate ~300 LOC each), plus the consented panel effort |
| BN-09 | **Windows selection reading** (SD-R3, tier S) | OpenWhispr synthetic Ctrl+C selection (mutates the clipboard); VoiceInk and FreeFlow (macOS AX) | No donor reads a Windows selection without touching the clipboard | UIA `TextPattern.GetSelection` bound into the target binding | One new module in `paste_tx` | Fixture editors; refusal when TextPattern is absent |
| BN-10 | **First real Klaint connector** (KT-10, tier S) | Botpress zendesk integration (TypeScript, cloud runtime); HubSpot HITL signature code | Node runtime; missing replay and timestamp checks | Thin Python client using the Botpress schema as reference | One connector package behind the broker | Fake-API fixtures per connector |
| BN-11 | **Studio contract bridge** (ST-D10, tier L) | VoiceStudio REST and MCP routes | No Wispral job, consent or cancel message contract | Thin mapping adapter | `adapters/studio/` outside the fork | Contract fixtures; low |
| BN-12 | **SDKs** (PL-SDK, tier L) | VoiceStudio REST/MCP, Handy CLI, Orcel app API (FSL, reference only) | No donor SDK spans products or uses the Wispral contracts | Thin generated clients | `sdk/` | Generated; low |

Explicitly **not** built new: ASR/TTS models, a duration-fit algorithm, a generic policy framework, a timeline editor, a model hub, a dialogue engine, a CRM inbox, a workflow engine, a coding agent, a realtime voice framework.

## 5. Copy-first acceptance rules

1. **Baseline before edit:** each fork packet first builds and runs the donor's own test suite at the pin, recording collected/passed/failed/skipped counts and missing cells. No delta lands before its baseline is recorded.
2. **Delta register:** every fork change records the finding that motivated it, the files touched, the fixture that proves it, upstream status (upstreamable / Wispral-only), and rollback.
3. **Unchanged-copy proof:** a file declared "COPY unchanged" is verified by SHA-256 against the pinned donor blob in CI.
4. **Notices:** LICENSE/NOTICE and third-party notices travel with the code and appear in the app's About screen.
5. **No silent widening:** a fork may not gain network calls, telemetry or auto-downloads through a rebase without a reviewed delta.
