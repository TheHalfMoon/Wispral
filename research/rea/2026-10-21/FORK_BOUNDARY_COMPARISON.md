# Pinned fork boundaries: internal source comparison

Date: 2026-10-21. Scope: Opus review PR #125, `INDEPENDENT_REVIEW.md` S1, reviewing the reuse boundary proposed for PR #124. This is a fresh same-mission source review. It does **not** satisfy an independent external security, release, merge or governance review gate.

**Recommendation:** use pinned Handy and VoiceStudio forks as conditional product leads, retaining narrow pure-module transplants and shared contract fixtures. Preserve each donor's existing integration until a measured incompatibility justifies extracting it. Accept S1 as a planning direction, with the qualifications below; do not treat it as a completed baseline, proven effort saving, runtime acceptance or permission to install/build product code.

## Evidence and limits

Only existing captured bytes and pinned trees were read. No REA restart, network acquisition, newer donor revision, package install, model load, donor edit, native app launch, commit or publication occurred. `fork-boundary-evidence.json` records local paths, SHA-256, git blob identities, dependency manifests, inventory predicates, test entry points and explicit `NOT_RUN` fields.

| Donor | Immutable pin | Pinned tree blobs | Unique captured source files | Local captured bytes matching pinned tree |
| --- | --- | ---: | ---: | --- |
| cjpais/Handy | `93c9ee05efe294cf2a56bd534b77ea1079f21b77` | 397 | 27 | 27/27 |
| debpalash/VoiceStudio | `28bf2c7a83b8a64836297340c52a45d716684aed` | 3,601 | 66 | 66/66 |

The trees are not truncated. Matching these captured bytes to the previously captured tree is a reproduced local integrity check, not a fresh remote attestation or whole-repository audit. Tree-only paths establish presence, not behavior. Donor README descriptions establish documented functionality, not observed quality, offline behavior or compatibility. Existing pure mechanism probes remain separate evidence and are not donor suite baselines.

Capture roots, relative to the REA workspace above `work/Wispral`:

- `work/donors/cjpais__Handy/{snapshot.json,tree.json,files/}` and `work/ink-scratch/cjpais__Handy/`.
- `work/donors/debpalash__VoiceStudio/{snapshot.json,tree.json,files/}` and `work/studio-scratch/debpalash__VoiceStudio/`.

## Actual reuse boundaries

| Dimension | Retain the pinned fork | Selective transplantation | Assessment |
| --- | --- | --- | --- |
| WisprSide functionality | Handy capture includes application entry/wiring, settings, audio/transcription managers, transcription coordinator, shortcut and paste implementations, supervisor and protocol. Tree includes CLI, portable support, secure input, model/history managers, frontend and packaging paths. | Extracting the coordinator/paste/supervisor leaves application wiring, settings/history, microphone/shortcut integration, UI and installer assembly to Wispral. | Fork lead has the better supported integration boundary for a desktop dictation surface. It is not proof that the full product meets the proposed target-authority contract. |
| WisprStudio functionality | Captured source includes fit/duration planning, long-form render/resume, dubbing pipeline, consent migration/profile routes, watermarking, model acceptance/lifecycle and subprocess engine infrastructure. Tree includes Electron application, fake `_echo` engine and packaging infrastructure. | Pure planning or policy modules can stay small, but transplanting dubbing or engine management crosses job persistence, media tools, lifecycle, API and frontend dependencies. | Fork lead preserves more relevant integration. Keep pure modules available for contract/fixture reuse; avoid rebuilding the captured sidecar infrastructure. |
| Dependency cost | Inherits the complete app, optional providers, updater/install machinery, native libraries and security maintenance scope. | Can exclude unused UI/providers/engine dependencies when the chosen module is genuinely pure. Integration-heavy modules can quietly recreate much of the closure. | Neither choice is dependency-free. Qualify the retained feature set and resolved closure before product acceptance. |
| Supervisor ownership | Preserves donor ownership relationships; contracts adapt at their public boundary. | Pulling several supervisors into one shared runtime risks two owners for the same child, contradictory cancellation and early lease release. | Share states/fixtures; do not install another process owner around the same worker merely to make the code look shared. Nested ownership of distinct process subtrees is valid. |
| Upstream maintenance | Preserve a clean upstream pin and a reviewable delta branch/register. Security fixes can be rebased into retained context. Larger retained surface needs monitoring. | Smaller copied surface, but fixes to omitted integration/tests may never reach the transplant. A changed donor module can require manual semantic reconstruction. | Track provenance and security updates in either approach; fork retention favors integrated features, transplantation favors pure leaf functions. |
| Recovery | Revert one delta when schema, settings, installed files and artifacts remain compatible. A binary revert alone cannot reverse a database migration or model deletion. | A leaf module can be replaced/reverted cheaply. Reassembled app/runtime glue has no single upstream baseline to restore. | Define rollback per delta, including data and model state, rather than promise a universal git revert. |

## Test entry points and honest counts

Counts were recomputed from the existing trees. These are **files or source definitions, never collected/passing tests or coverage**. No donor suite was run.

| Inventory | Handy | VoiceStudio |
| --- | ---: | ---: |
| Snapshot's broad test-path heuristic | 7 entries | 1,425 entries |
| Python basename `test_*.py` or `*_test.py` | 0 files | 696 files |
| JS/TS suffix `.test` or `.spec` before a JS/TS extension | 4 files | 640 files |
| Captured Rust `#[test]` / `#[tokio::test]` attributes | 141 definitions across 12 captured files | Not inventoried as a donor-wide Rust suite |
| Captured Python `def test_` / `async def test_` definitions | 0 under this capture | 182 definitions across 10 captured files |

S1's “696 test files” is reproducible as the Python filename inventory, not the complete application test inventory. The broad heuristic includes workflows, helper files, fixtures and other non-test entries; these numbers must not be added together as case counts. Parameterization and platform conditions change collected cases.

Handy's captured `package.json` defines `bun run test:keyboard` and `bun run test:playwright`; the captured Rust manifest provides the `cargo test --locked --manifest-path src-tauri/Cargo.toml` entry point. The tree contains `.github/workflows/test.yml`, but its body was not captured; the exact CI suite partition and native setup remain unverified. Captured coordinator, paste state and protocol tests can travel with their surrounding implementation instead of being silently discarded.

VoiceStudio's captured `pyproject.toml` defaults pytest discovery to `tests`, excludes vendored research, and explicitly notes `backend/tests` runs separately. Capture-derived entry points are `python -m pytest tests`, `python -m pytest backend/tests`, `bun run test:frontend`, `bun run test` and `bun run check:electron`. The root `test` script delegates to the Electron package; `check:electron` additionally invokes typecheck/build/web build and a packaging contract. The tree has `.github/workflows/ci.yml` and `electron/package.json`, but their bodies are unavailable in this capture. Do not infer that a root pytest run covers all suites or that every suite is model-free.

**Baseline status: `NOT_RUN` for both donors; pass/fail/skipped/collected counts are unknown.** These are sparse captures, not installable checkouts. No `node_modules`, `.venv` or Rust target exists under the inspected donor roots. A read-only host module-spec probe found pytest/numpy, but not torch/fastapi. VoiceStudio's captured fit test imports unavailable `services.incremental` and an API router, so calling its planner pure does not make the complete donor test module runnable from this capture. No test was substituted for an unmodified donor baseline. Full fork build/install and suite baselines remain gated product work after canonical authority opens.

## Direct dependencies and native closure

Handy's captured frontend manifest declares 27 runtime dependencies, including React, Tauri plugins, model catalog, internationalization and state/UI packages. Its Rust manifest has 44 base runtime dependency names plus platform-specific tables and development/build dependencies. Notable native boundaries are `transcribe-cpp`/ggml, `handy-recorder`, `handy-keys`, rdev/enigo, bundled SQLite, Tauri/WebView2 on Windows, Metal/Objective-C frameworks on macOS and GTK/Vulkan on Linux. Windows x86_64 enables dynamic backends and Vulkan; Windows ARM is statically linked CPU-only at this pin. rdev, hf-hub, tauri-nspanel and patched tao introduce Git dependency provenance. The captured Cargo lock is retained, but frontend lock/build script bodies and shipped native artifact validation are absent from this comparison. Do not equate a manifest inventory with a resolved SBOM or ABI-compatible package.

VoiceStudio's captured Python manifest declares 54 base dependencies, plus `eval`, `ui`, `supertonic` and `pockettts` extras and cpu/cuda/dev groups. Core closure already includes torch/torchaudio/torchvision, transformers, ASR/diarization, FFmpeg integration, audio/media libraries, FastAPI, model downloading, `yt-dlp`, posthog and optional provider clients. Its uv constraints couple torch 2.8.0, torchaudio 2.8.0 and torchvision 0.23.0; groups choose CPU/CUDA indices and default groups include CUDA. Platform markers gate MLX and other Apple-specific packages. Direct GitHub wheel URLs exist for KittenTTS and the spaCy model. Separate per-engine environments are an existing compatibility mechanism, not proof their requirements or native ABIs were resolved here. `uv.lock`, the Electron dependency manifest, per-engine requirements bodies and native desktop bridge manifest bodies were not captured. Retaining a full fork inherits those closures; narrowing the enabled feature set does not automatically remove their installed dependencies.

MIT Handy and AGPL-3.0-only VoiceStudio notices remain distinct. Founder grant authorization is already recorded in the bundle and is not questioned here. Retain per-file notices and private grant-scope flags; app rights do not establish third-party package, media codec or model-weight rights.

## Supervisor and cancellation qualifications

Handy's `src-tauri/src/engine_supervisor/supervisor.rs:1-10` names `EngineSupervisor` as the single model-worker owner, serializing work and permitting separate model-less device probes. `cancel()` at lines 471-485 advances the cancel epoch and kills the in-flight transcription worker. **The same source explicitly says “Model loads are never cancelled.”** Keeping the fork does not satisfy a shared cancel-during-load criterion. A future delta must establish the required load cancellation behavior with an observed-stop test, or the authority must explicitly define a narrower contract. Returning cancellation or changing an epoch does not itself prove process exit or resource release.

VoiceStudio is **not** uniformly per-engine subprocess isolated. `backend/services/model_lifecycle.py:1-6` describes in-process TTS/ASR, diarization and subprocess sidecars; lines 164-190 separately inventory further in-process engines. `subprocess_backend.py:1-37` already owns isolated interpreter spawn, framing, accounting and teardown for engines that use that base. `backend/core/contained_subprocess.py:1-16` defines nested POSIX groups / Windows kill-on-close Jobs under the desktop-owned backend. `dub_pipeline.py:15-17,60-70` preserves a distinct media-job process registry. These are compatible ownership levels for different subtrees, not interchangeable second supervisors.

The product contract should see one Studio runtime boundary with explicit cancellation mapping. Inside it, retain the donor's defined ownership hierarchy: desktop/backend containment; each owned engine subtree; job media-process ownership; in-process inference lifecycle. Do not claim a sidecar kill proves cancellation of an in-process model. The existing request allowlist, frame cap and teardown code are source observations, not a security assurance. Conformance must cover each reachable path, including load, generation, timeout, backend death and post-commit cancellation.

## Telemetry, URL ingest and retained surfaces

VoiceStudio's `pyproject.toml:156-159` already describes PostHog as inert without both a project token and user opt-in, “default OFF”; its README also says analytics is opt-in. The captured renderer `analytics-consent.test.tsx` asserts explicit choice persistence and retry after a failed write, but has not been executed here. `backend/core/analytics.py` is tree-only. Accordingly, revise S1 to **verify and preserve default-off behavior**, including clean install, upgrades, opt-out and packaged builds; do not report a confirmed default-on defect. If the approved Wispral policy requires telemetry disabled entirely, enforce that as a separately recorded delta and verify observed egress.

URL download is a confirmed retained source surface: `backend/services/dub_pipeline.py:1136-1168` defines `yt_download_sync`, imports `yt_dlp`, and rechecks URL safety; lines 1259-1261 and 1333-1336 call the downloader behind outbound guards. This is more than a hidden UI field. An initial local-only product can reject URL ingest at backend entry points and every desktop/CLI/plugin route reaching them, with negative fixtures proving no downloader/network invocation. Preserve local-file workflows. Do not remove unrelated model-download functionality under an ambiguous “URL off” label. URL-safety implementation bodies are not captured, and this report makes no SSRF-safety finding.

Handy's network-capable downloader/updater/post-processing dependencies and VoiceStudio's account/provider/model-download paths also require explicit feature/egress inventory. Fork retention alone does not prove offline or telemetry-free operation. S1's OpenWhispr focus-fallback defect applies to that donor's helper; it is not proof Handy contains the same bug. Qualify Handy's own paste paths and add target-identity/expiry/focus-loss deltas against actual findings. If importing the OpenWhispr helper, keep its unsafe fallback excluded.

## Effort, rebase and rollback decision

The source supports reduced reassembly work for existing app flows; it does not measure saved engineer-days. Fork qualification adds full build, dependency, packaging, update and retained-feature obligations. Selective extraction remains attractive for pure `fit_planner` plus a separate validating guard, deterministic policy, schemas and fixtures. It is less persuasive for lifecycle/dubbing/app modules that import persistent stores, native tools, API routes and UI state. The current comparison supports this hybrid boundary without proving either fork is installable on the target machine.

Estimate the first baseline separately from deltas. Baseline uncertainty includes sparse-source completion from the **same pin** when authorized, native toolchains/ABI packaging, dependency availability, test setup, platform signing and rights notices. Delta uncertainty includes target-safe paste, load cancellation, retained in-process engines, telemetry/URL denial and data migrations. Review/CI and governance latency remain separate unknowns. Do not replace them with an unmeasured fixed duration.

For each delta, record finding/authority, changed paths, fixture, upstream status and expected conflict surface. Keep the unmodified pin and upstream-tracking branch immutable; apply small commits on a product branch. Rebase qualification reruns the affected fixtures plus original baseline partitions and any packaging/native/egress checks touched by the upstream update. Preserve failed results. Define rollback of binary, settings/database schema and model artifacts before executing a migration; backup compatibility and recovery tests are required where a delta changes persistent state.

## Acceptance evidence required before adopting the product runtime

1. Canonical governance opens the named fork-baseline grain. Research recommendation alone leaves it `NOT_READY` for implementation.
2. Materialize the exact pin, preserve notices/locks, inventory enabled and disabled surfaces, and record interpreter/toolchain/native dependencies. No implicit latest-version upgrade.
3. Run the unmodified donor suites first, with commands, exact pin, environment, collected/pass/fail/skip counts, logs and a declared model-free versus model/native partition. Record failures honestly. A failing baseline is a triage result, not an automatic fork rejection or successful gate.
4. Produce the separately authorized first installable artifact and bounded launch/exit evidence. Record target OS/architecture, bundled native DLLs/libraries, update destinations and rollback behavior. This work has not happened in this review.
5. Create a delta register before edits. Test Handy target identity and cancellation through load/inference/commit; test Studio sidecar and in-process paths separately, descendant cleanup, late replies, lease release only after observed stop and backend death. Keep one owner at each defined subtree boundary.
6. Prove telemetry default/opt-out and URL-ingest denial at all entry points with egress observations and no-download negative fixtures. Inventory retained optional cloud/account/provider/model download paths.
7. Run exact-range independent external reviews and all project gates required by authority. This same-mission comparison and any local advisory classifier cannot satisfy them.

Planning acceptance: **conditional fork leads supported; runtime/build/security/effort acceptance `NOT_ESTABLISHED`.** No canonical text or implementation was changed by this comparison.

panel: source-boundary combined review (session model); correctness, parsimony and product bars applied to S1; security concerns recorded as qualification inputs, independent external security/release gates not satisfied; browser/native/runtime checks NOT_RUN.
