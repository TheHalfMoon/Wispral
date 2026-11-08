# WisprSide source investigation

> V3 repair selection (Opus #125): current reuse modes/owners are in [SOURCE_TRANSPLANT_MATRIX.md](SOURCE_TRANSPLANT_MATRIX.md) and the [repair traceability](OPUS_REPAIR_TRACEABILITY.md). The original pinned source observations below remain valid; extraction-first selection/estimates are superseded where the current fork/API/contract boundary differs. No source identity or runtime result was discarded.

**Mission:** [Issue #122](https://github.com/TheHalfMoon/Wispral/issues/122). **Disposition:** research and proposed transplants only; implementation authority remains closed. **Evidence date:** 2026-10-21. **Observed host:** Windows x64, Node.js 24.19.0. Hardware microphone, native insertion, packaged applications, paid APIs, Arabic recognition and macOS/Linux execution were **NOT_RUN** in this study.

`FOUNDER_SOURCE_AUTHORIZATION=YES_CONFIRMED_BY_FOUNDER`
`CONFIDENTIAL_GRANTS=HELD_PRIVATELY_BY_FOUNDER_NOT_SHARED`

The founder's existing permission covers identified supplied/authorized source code. Agreements were not requested or independently inspected. Notices and separate model, voice, dataset and asset rights remain distinct. Final product names are **Wispral / WisprStudio / WisprSide / Klaint**.

## Contents

1. [Decision](#decision)
2. [Pinned source scope](#pinned-source-scope)
3. [Concrete execution paths](#concrete-execution-paths)
4. [Published dependency archives](#published-dependency-archives)
5. [Transplant seams](#transplant-seams)
6. [Tests actually executed](#tests-actually-executed)
7. [Required behavioral trials](#required-behavioral-trials)
8. [Risk and acceptance register](#risk-and-acceptance-register)

Machine-readable file identities, SHA-256 hashes, decisions, dependency origins and trial results are in [ink-source-evidence.json](ink-source-evidence.json). This file records inspected seams; fetched file inventory is not a claim that every line in every repository was audited. Browser REA and proprietary documentation coverage are consolidated separately in the [methodology](REA_METHODOLOGY.md) and [feature matrix](FEATURE_PARITY_AND_GAP_MATRIX.md).

## Decision

**Lead donor for native dictation mechanisms: Handy, selectively, with its separately published `handy-recorder` and `handy-keys` crates considered before extracting application managers.** The captured source provides Rust microphone lifetime/error handling, keyboard edge/state handling, cancel generations, explicit committed/tentative text, native process isolation and clipboard transactions. These align more closely with Wispral's existing Rust boundary than importing OpenWhispr's entire Electron/React application or the macOS-only FreeFlow/VoiceInk applications. This is a source-fit recommendation; no speed, recognition-quality or native reliability winner has been measured.

**Complementary donors:** OpenWhispr's native target detection, terminal paste selection, recovery classifications and negative fixtures; FreeFlow's small selection snapshot and shortcut state-machine fixtures; VoiceInk's explicit partial-delivery result and Unicode chunking for a later native macOS adapter. Use one capture service, one STT router and one insertion transaction in Wispral Core. WisprSide consumes those services; WisprStudio and Klaint must not acquire duplicate microphone engines.

**Do not select a production STT backend from this report.** Live Handy uses `transcribe-cpp 0.4.0`; it is a newly investigated candidate, not a replacement for the frozen Wispral B2 experiment. OpenWhispr's application code exposes local Whisper/sherpa-style and optional network routes; their availability in source does not establish Wispral support.

| Candidate | Reuse position | Rejection/qualification boundary |
| --- | --- | --- |
| Handy + published crates | Lead capture/hotkey/transaction donor; ADAPT/WRAP | Tauri state/settings/UI coupling must be removed at typed boundaries. Receipt paste is debug-gated, not a proven default. Its cancellation shortcut is unregistered when recording stops. |
| OpenWhispr | Narrow native helpers and failure fixtures | Reject whole application inheritance: one clipboard helper is 2,532 lines and `ipcHandlers.js` is 13,330 lines at this pin; cloud/auth/UI/module coupling is substantial. Failed focus restoration currently falls through to the current foreground. |
| FreeFlow | Small native macOS context/shortcut mechanisms | Reject as platform shell or offline baseline: direct source uses configurable HTTP speech/context services and macOS frameworks. Desktop screenshot fallback defaults to enabled; Wispral must not inherit that policy. |
| VoiceInk | Later macOS partial-delivery/Unicode seam | Reject as cross-platform shell: SwiftUI/AppKit/SwiftData and numerous Swift packages. `LICENSE` is GPLv3 text despite GitHub metadata `NOASSERTION`; retain founder-confirmed grant and accurate upstream notice. |

## Pinned source scope

| Source identity | Immutable revision | Inspected source surface | State |
| --- | --- | --- | --- |
| [OpenWhispr/openwhispr](https://github.com/OpenWhispr/openwhispr/tree/e4280ada144f04f20dad0bd32eaf22272f9c77b8) | `e4280ada144f04f20dad0bd32eaf22272f9c77b8` | Capture/processing cancellation, clipboard queue, Windows native target/paste, empty-recording guard, repeat gate, IPC imports, manifests and selected tests | SOURCE_VERIFIED; 17 isolated pure tests REPRODUCED |
| [cjpais/Handy](https://github.com/cjpais/Handy/tree/93c9ee05efe294cf2a56bd534b77ea1079f21b77) | `93c9ee05efe294cf2a56bd534b77ea1079f21b77` | Audio/shortcut managers, coordinator, stream policy, worker protocol/supervisor, clipboard and native transaction modules, manifests/lock and inline tests | SOURCE_VERIFIED; native/Rust tests NOT_RUN |
| [zachlatta/freeflow](https://github.com/zachlatta/freeflow/tree/797a3f32e6b525b8d942512db2801466d3a651f7) | `797a3f32e6b525b8d942512db2801466d3a651f7` | AVFoundation capture, selection/context service, HTTP speech client, postprocessing, shortcut session controller, Makefile and selected tests | SOURCE_VERIFIED; Swift tests NOT_RUN |
| [Beingpax/VoiceInk](https://github.com/Beingpax/VoiceInk/tree/22e5ec5479b712797c3b338fcb875961e58800b6) | `22e5ec5479b712797c3b338fcb875961e58800b6` | Transcription pipeline/delivery, context snapshot, selected-text dependency, streaming states, clipboard/session restore, direct Unicode typer, license and Swift lock | SOURCE_VERIFIED; native/Swift tests NOT_RUN |

The parent inventory includes complete GitHub tree responses at each pin. This study captured 66 selected files: 20 OpenWhispr, 23 Handy, 11 FreeFlow and 12 VoiceInk. A mistaken guess at `engine_supervisor.rs` was corrected by reading the tree: the real module is `engine_supervisor/{mod,protocol,supervisor,worker}.rs`. No invented path is selected for transplant.

## Concrete execution paths

### Handy: reuse capture and lifecycle, separate from the application

1. [`shortcut/handler.rs:29`](https://github.com/cjpais/Handy/blob/93c9ee05efe294cf2a56bd534b77ea1079f21b77/src-tauri/src/shortcut/handler.rs#L29) routes transcription edges to `TranscriptionCoordinator::send_input`. The handler feeds activation mode and hold threshold; `shortcut/handy_keys.rs` owns a dedicated manager thread with register/unregister commands rather than sharing a mutable keyboard hook across threads.
2. [`transcription_coordinator.rs:97`](https://github.com/cjpais/Handy/blob/93c9ee05efe294cf2a56bd534b77ea1079f21b77/src-tauri/src/transcription_coordinator.rs#L97) separates pure `classify_busy_input`, `Stage`, `Effect` and `CoordinatorState` decisions from side effects. It preserves toggle parity while a previous transcription is busy; release grace handles X11 autorepeat. Inline tests include `toggle_presses_during_processing_net_noop_after_drain`, `cancel_during_processing_drops_remembered_press`, and `hold_or_toggle_autorepeat_burst_straddling_drain_measures_from_first_press`. Extract this reducer and its actual tests, not Tauri's whole action map.
3. [`managers/audio.rs:998`](https://github.com/cjpais/Handy/blob/93c9ee05efe294cf2a56bd534b77ea1079f21b77/src-tauri/src/managers/audio.rs#L998) `try_start_recording` rejects non-idle state, acquires a `CaptureSink`, retries one failed recorder open, and returns first-sample readiness bound to a capture generation. `invalidate_recording_readiness`, `cancel_generation`, `was_cancelled_since`, `stop_recording` and `cancel_recording` prevent late output from a cancelled generation. `stop_recording` may pad very short audio and permits configured trailing capture; those are transformations that must be explicit in Wispral evidence, not inherited into frozen C0.
4. [`actions.rs:565`](https://github.com/cjpais/Handy/blob/93c9ee05efe294cf2a56bd534b77ea1079f21b77/src-tauri/src/actions.rs#L565) unregisters the cancel shortcut when recording stops. Later code checks the cancel generation before postprocessing and again inside the scheduled paste closure, but that does not by itself supply a visible cancellation control throughout transcription. Wispral must expose capture, inference and delivery cancellation independently.
5. [`managers/transcription.rs:56`](https://github.com/cjpais/Handy/blob/93c9ee05efe294cf2a56bd534b77ea1079f21b77/src-tauri/src/managers/transcription.rs#L56) defines `StreamTextEvent { committed, tentative }`; `StreamCmd::Feed/Finalize/Cancel` preserve ordering. [`policy.rs:51`](https://github.com/cjpais/Handy/blob/93c9ee05efe294cf2a56bd534b77ea1079f21b77/src-tauri/src/managers/transcription/policy.rs#L51) distinguishes native streaming, pause-delimited chunking and batch-only decoding. Preserve that distinction in the STT contract.
6. [`engine_supervisor/mod.rs`](https://github.com/cjpais/Handy/blob/93c9ee05efe294cf2a56bd534b77ea1079f21b77/src-tauri/src/engine_supervisor/mod.rs) describes and source-traces a re-launched executable worker, model-lifetime ownership and CPU-only recovery. `protocol.rs::encode_message/read_message` frame JSON and f32 PCM; `supervisor.rs::EngineSupervisor::cancel` and `Worker` lifecycle isolate native failures. The frame section cap is **1 GiB** at this pin; a Wispral IPC contract requires much smaller per-frame bounds, total/session budgets and sequence identities. Source tests cover hung finalize/feed, GPU crash and cancellation, but many are ignored/model-dependent and were not executed here.

**Clipboard path:** [`clipboard.rs:774`](https://github.com/cjpais/Handy/blob/93c9ee05efe294cf2a56bd534b77ea1079f21b77/src-tauri/src/clipboard.rs#L774) dispatches None, direct, clipboard-chord and external-script methods. `reliable_paste` is a debug setting with fallback to the legacy timer-based path. [`paste_tx/mod.rs`](https://github.com/cjpais/Handy/blob/93c9ee05efe294cf2a56bd534b77ea1079f21b77/src-tauri/src/paste_tx/mod.rs) provides `TxState`, `record_receipt`, `last_receipt_after_injection` and pure `evaluate`. A receipt before injection is ignored; ownership loss/new copy ends restoration. Quiet period is 200 ms; timeout 8 s; failed-injection timeout 500 ms. These are source constants, not latency measurements.

Windows uses `WM_RENDERFORMAT` on a message-only window, sequence-guards restoration and publishes clipboard-history/cloud-exclusion conventions. macOS uses a promised `NSPasteboard` owner, `changeCount`, and concealment marker conventions. **Neither receipt proves that the intended editor accepted the text, and third-party clipboard readers remain possible.** Do not elevate `Ok(())`, a read receipt, or a queued input event to `INSERTED`. Disable donor auto-submit until a separate exact-target authority contract is approved. Legacy restoration saves text/image incompletely compared with arbitrary rich clipboard formats; receipt-module macOS snapshots also do not promise every type. Retain manual-copy recovery when safe restoration cannot be promised.

**Dependencies:** Handy `Cargo.toml` version is 0.9.8; Tauri 2.11.5, enigo 0.6.1, handy-recorder 0.1, handy-keys 0.3.4, transcribe-cpp 0.4.0, serde, channels/atomics and platform Win32/ObjC APIs. `Cargo.lock` pins registry checksums and git origins: rdev at `a90dbe1172f8832f54c97c62e823c5a34af5fdfe`; hf-hub at `9918f11ab3473135eb7865aa4a5d79d597e6e810`; tao at `c3bee28c1d446d95f08c95c3b6f8d4bde052b876`. Do not import updater, storage, model downloads, tray, shell or patched window manager merely to acquire capture.

### OpenWhispr: useful observable outcomes, unsafe target fallback to remove

`package.json` declares version 1.10.3, Node >=24, Electron main `main.js`, React/Zustand UI, AI-provider SDKs, better-sqlite3, ONNX Runtime, ffmpeg-static, native keyring, archives and updater. This has materially more dependency and native-binary surface than the selected pure helpers; no install or dependency safety approval was performed.

[`audioManager.js:2134`](https://github.com/OpenWhispr/openwhispr/blob/e4280ada144f04f20dad0bd32eaf22272f9c77b8/src/helpers/audioManager.js#L2134) binds a processing pipeline to a cancellation generation. `cancelProcessing` does not advertise idle while a stop promise still awaits an unabortable provider; `_requestStreamingCancellation` aborts available provider requests, clears pending selection/context, and increments generation. `cancelStreamingRecording` clears capture resources, awaits provider/start settlement and closes the specific session. Preserve these failure fixtures and lifecycle distinctions as independent tests against the Wispral contract rather than copying the 6,577-line audio manager wholesale.

[`clipboard.js:951`](https://github.com/OpenWhispr/openwhispr/blob/e4280ada144f04f20dad0bd32eaf22272f9c77b8/src/helpers/clipboard.js#L951) serializes paste operations through restoration completion. `_restoreClipboardAfterDelay` skips restoring when clipboard text changed. `_saveClipboard` retains text/HTML/RTF/image when present; KDE/Wayland primary-selection handling is separate. macOS permission failure returns copied-only guidance when allowed, instead of equating copy with insertion; [`AudioManager::safePaste`](https://github.com/OpenWhispr/openwhispr/blob/e4280ada144f04f20dad0bd32eaf22272f9c77b8/src/helpers/audioManager.js#L4427) preserves a `pasted` boolean and errors.

[`windowsPasteTarget.js:23`](https://github.com/OpenWhispr/openwhispr/blob/e4280ada144f04f20dad0bd32eaf22272f9c77b8/src/helpers/windowsPasteTarget.js#L23) deliberately permits an unreadable executable identity, while rejecting an unparseable own-window handle. [`windows-fast-paste.c:281`](https://github.com/OpenWhispr/openwhispr/blob/e4280ada144f04f20dad0bd32eaf22272f9c77b8/resources/windows-fast-paste.c#L281) explicitly falls through to whatever is foreground when a captured target disappeared or could not be restored. This is incompatible with an exact-target fail-closed Wispral insertion rule. **ADAPT the detector/terminal-chord helper; remove fallback-to-other-window before enabling insertion.** A reused HWND alone also needs process/start-time and focus freshness checks to address handle reuse.

`screenContextCapture.js` contains bounded image encoding and platform permission checks; its existence is not authorization to capture the screen. `recordingGuard.js` uses a 256-byte container-size heuristic; `hotkeyRepeatGate.js` uses a 600-ms renew-on-repeat window. They are narrow, source-tested candidates with caveats: compressed-container size is not acoustic silence detection, and the repeat window intentionally suppresses a quick second tap.

### FreeFlow: source-level contextual-editing reference, macOS and HTTP boundaries

[`AppContextService.swift:96`](https://github.com/zachlatta/freeflow/blob/797a3f32e6b525b8d942512db2801466d3a651f7/Sources/AppContextService.swift#L96) `collectSelectionSnapshot` gathers bundle ID/window/selected text using `NSWorkspace` and AX. `collectContext` also takes a screenshot and calls a configured `chat/completions` endpoint when a key exists. `DesktopScreenshotFallbackPreference.load` defaults **true**; tests explicitly preserve that default. Do not inherit its default screen policy or cloud-routing policy. Reuse a bounded selection snapshot only with explicit per-application consent, sensitive-field exclusion and freshness identity.

`inferActivityWithLLM` retries image-less after some image-request failures but immediately stops retrying 401/403/404/429. `ContextInferenceFailure` provides typed user-facing failures. `TranscriptionService` defaults to a configurable Groq-compatible OpenAI API endpoint, validates API configuration and races transcription against cancellation/timeout. This source path does not establish an offline path.

[`DictationShortcutSessionController.swift`](https://github.com/zachlatta/freeflow/blob/797a3f32e6b525b8d942512db2801466d3a651f7/Sources/ShortcutCore/DictationShortcutSessionController.swift) is an 86-line reducer for hold/toggle/hold-to-toggle, ignores copy-again events and prevents new starts during transcription. `Tests/ShortcutCoreTests.swift` exercises lifecycle and repeat/modifier boundaries. `AudioRecorder.swift` uses AVFoundation, a buffer watchdog, format conversion and interruption recovery. The Makefile builds macOS 13 targets with swiftc/xcrun; its tests cannot be run as native macOS tests on this Windows host. Reuse reducers/error cases without acquiring the complete 3,451-line AppState.

### VoiceInk: partial delivery and Unicode matter more than success-shaped APIs

[`CursorPaster.swift:44`](https://github.com/Beingpax/VoiceInk/blob/22e5ec5479b712797c3b338fcb875961e58800b6/VoiceInk/Infrastructure/SystemIntegration/Paste/CursorPaster.swift#L44) queues paste sessions through restoration completion. Results distinguish `commandPosted`, `commandNotPosted` and `commandPartiallyPosted`; a posted event is explicitly weaker than accepted editor text. Restoration checks both expected text and a per-session marker before replacing the clipboard. Direct partial typing is not automatically retried, preventing duplicate text. This is a useful failure vocabulary for Wispral on all platforms.

[`DirectTextTyper.swift:25`](https://github.com/Beingpax/VoiceInk/blob/22e5ec5479b712797c3b338fcb875961e58800b6/VoiceInk/Infrastructure/SystemIntegration/Paste/DirectTextTyper.swift#L25) requires AX trust, waits for held modifiers with a deadline, aborts on cancellation/new modifiers, chunks UTF-16 without splitting surrogate pairs, preserves combining marks and rejects controls other than tab/newline. It yields during long inputs and returns partial status. It routes to the current keyboard recipient, so Wispral still needs an intended-target guard; Arabic correctness and grapheme behavior are NOT_MEASURED.

[`TranscriptionPipeline.swift:51`](https://github.com/Beingpax/VoiceInk/blob/22e5ec5479b712797c3b338fcb875961e58800b6/VoiceInk/Features/Recording/Workflows/TranscriptionPipeline.swift#L51) separates transcription, cancellation checks, formatting, replacement, enhancement and delivery; it writes a cleaned text field after filtering. Wispral must retain immutable raw transcript separately. `TranscriptionDelivery::deliver` gates completed status but also supports custom commands and auto-send. Do not transplant shell/custom-command authority or billing restrictions into Wispral Core.

`RecordingContextCaptureService::startCapture` reads clipboard/selection and optionally screen OCR into a snapshot; only OS permission is visible at this seam, not Wispral's per-purpose consent. `SelectedTextService` delegates to `SelectedTextKit` through accessibility/menu-action/AppleScript strategies; its pinned dependency is `Beingpax/SelectedTextKit@05a3e5177300d800c2785be83ba2ba7fa775e41a`. Swift dependencies also include FluidAudio, AXSwift, Transcribe-cpp-swift, MLX, Sparkle and others. These dependencies are source-discovered, not fully audited/transplant-approved.

## Published dependency archives

All three source archives were fetched directly from `static.crates.io`, decompressed as data, and matched against the exact published archive SHA-256 in Handy's captured Cargo.lock. No crate build scripts, compiler or native library was run. The archive inventory/hashes and publisher-supplied `.cargo_vcs_info.json` are recorded in the JSON; VCS declarations are provenance assertions, while archive checksum equality was independently reproduced.

| Candidate and archive identity | Source seam inspected | Qualified use and limitations |
| --- | --- | --- |
| `handy-recorder 0.1.0`, SHA-256 `4a734d6d16eb8eb485548d75f383fa0c09d65b037a20e648c19730860f7a8a3f` | `src/lib.rs::Recorder::{open_with_failure_handler,start,stop,close}`, `Stopped::is_complete`; `src/sink.rs::{Sink,AudioChunk}`; `src/capture/transport.rs::write_input_to_ring`; failure tests | Prefer WRAP over extracting Tauri's manager. Reports dropped frames/end reason; callbacks deliver through ring/off-RT sink; Rust >=1.88, handy-cpal 0.18.2, rtrb, rubato =5.0.0. Permission and hardware behavior NOT_RUN. |
| `handy-keys 0.3.4`, SHA-256 `1a007b6c921d3273fd88aac45b516eee01e5a9dc2d76bb6f1a981500cc0d818a` | `src/manager.rs::HotkeyManager`, `ManagerState::process_event`; `src/platform/windows/listener.rs`; synthetic-input tests | WRAP for platform-qualified shortcut input. Windows LL hooks, macOS AX, Linux evdev; blocking grabs/reinjects through uinput. Linux broad keyboard-read rights and sandbox restrictions require a narrower portal alternative. Synthetic integration tests are ignored by default and NOT_RUN here. |
| `transcribe-cpp 0.4.0`, SHA-256 `f6cad85eeb846a7064891c8b49b92a57a0f2d4dd089104cb199608b23043555e` | `src/lib.rs` model/session contract; `src/cancel.rs::{CancelToken,abort_trampoline}`; cancellation/no-model tests | Evaluation candidate, not selected STT. Native `transcribe-cpp-sys 0.4.0` and checkpoint rights remain to qualify. Cooperative callback runs between decode steps; source warns model-level compute is serialized and an active stream leases the model. |

All three archive LICENSE files declare MIT and retain 2026 handy-computer/transcribe.cpp author notices. The recorder's archive declares upstream repo `handy-computer/handy-recorder`, VCS SHA `1d975fe8c10f9a69d778cf16955c7e0699b4b8e1`, subpath `crates/handy-recorder`. Keys declares `handy-computer/handy-keys@e7d1b8e6de8258f21ee1d60608d16f8d195157bf`. Bindings declare `handy-computer/transcribe.cpp@f1dcd15858c4bbba87ca97862b4e448b2cf15b8f`, subpath `bindings/rust/transcribe-cpp`. The nonempty recorder subpath should be reconciled with its repo metadata before source-to-archive equivalence is claimed.

An important test limitation: `transcribe-cpp/tests/cancel.rs` returns early when fixtures are unavailable or capability is missing; its race permits completion before the timer fires. A green upstream test process therefore does not prove that cancellation actually occurred. Wispral's cancellation gate must require observed request, acknowledgement/stopped state and rejection of late generation output, with fixture presence enforced.

`transcribe-cpp/tests/streaming.rs:74` makes another boundary explicit: `text.full` is the authoritative raw hypothesis, while its best-effort append-only `committed` prefix can diverge for re-attending models such as Moonshine. `CommitPolicy::OnFinalize` has a separate contract. Preserve raw/full/final provider semantics and revision identity; an event named committed is not universally irrevocable truth.

## Transplant seams

All destinations below are **proposed**. Exact SHA/path/symbol/hash/test maps and effort bands are in the JSON for consolidation into the master work packets. Estimates are engineering planning estimates, not measured throughput.

| Order | Mechanism and selected source | Destination / mode | Acceptance and rollback |
| --- | --- | --- | --- |
| I1 | handy-recorder published API and failure fixture pattern | Core audio capture adapter / WRAP | Fake backend exact frames, dropped-frame signal, unplug/no-audio/permission, close releases capture; disable adapter back to text-only on failure. |
| I2 | handy-keys HotkeyManager + Handy coordinator reducer | Core platform activation / WRAP + ADAPT | Hold/toggle autorepeat, focus/lock/resume, registration collision, busy parity and cancel clearing; keyboard-button fallback. |
| I3 | Handy `paste_tx::TxState/evaluate` and inline tests | Core insertion transaction / ADAPT | Pre-injection reader, multi-read quiet period, timeout, cancel, external copy, crash and overlapping sessions; manual copy with visible outcome. |
| I4 | Handy `paste_tx/windows.rs` | Windows insertion adapter / ADAPT | Dedicated test target and independent clipboard reader; no wrong-window fallback, no auto-submit, bounds/cleanup; manual copy. |
| I5 | OpenWhispr `windows-fast-paste.c::{GetExeName,GetWindowTitleUtf8,RestoreForegroundWindow}` | Windows target identity helper / ADAPT | Fail closed when restore/identity/focus freshness fails, HWND reuse, elevated target/UIPI, terminal chord; refuse injection. |
| I6 | Handy Linux insertion tool dispatch and OpenWhispr negative fixtures | Linux insertion adapter / ADAPT | Separate X11, GNOME/KDE/Hyprland/other Wayland matrix; no root blanket grants, known tool failures; manual copy. |
| I7 | Handy stream text/policy and worker isolation | Core STT adapter candidate / ADAPT, qualification pending | Never conflate tentative with final or chunking with streaming; crash/hang/cancel/IPC bounds and zero silent cloud fallback; retain existing qualified backend selection process. |
| I8 | FreeFlow selection snapshot; VoiceInk partial/Unicode seam | Later macOS native adapter / ADAPT | Explicit AX/context consent, fresh selection snapshot, no screen default, Arabic/emoji/control characters, partial typing never retried; manual copy. |
| I9 | OpenWhispr empty-container/repeat guards and upstream cases | Regression fixtures / COPY where language fits, ADAPT otherwise | Retain byte threshold/repeat tradeoffs and false-drop tests; no new silence/accuracy claims. |
| I10 | Donor output pipelines plus Wispral immutable provenance contract | Core transcript/result envelope / ADAPT | Raw→normalized→rewrite lineage, meaning/negation/numbers preserved; proposed rewrite shown before replacing high-risk text. |

**BUILD_NEW exception I11:** implement only the missing **cross-donor exact-target authorization and context-consent binding**, using Wispral's existing trust model. The inspected donors have pieces (HWND/bundle ID, session marker, cancellation generation), but none supplies one contract binding original audio/session, target process/start identity, purpose/expiry, selected-text digest, approved routing and insertion generation. First reuse those pieces; the minimal new glue is justified by this concrete contract gap. Do not write another capture or ASR engine.

## Tests actually executed

`INK-UNIT-02`: exact upstream `windowsPasteTarget.test.js` (6), `recordingGuard.test.js` (8), `hotkeyRepeatGate.test.js` (3), with unchanged exact helper bytes at the OpenWhispr pin. **17/17 pure unit tests passed**, exit 0, Windows x64, Node 24.19.0. No npm install, lifecycle hook, Electron, native injector, microphone, model inference, cloud endpoint or private audio was executed. The earlier `INK-UNIT-01` was the six target tests alone; it overlaps and is not 6 additional unique tests. The final run's ESM package-type warning is retained in raw output.

These results prove the exercised pure decisions, including intentionally permitting unknown executable identity and suppressing taps inside a repeat window. They do not prove that those choices are secure or right for Wispral. Test names referring to real speech are upstream labels; inputs here are byte counts only. Timings printed by Node are diagnostic test-run data, not latency benchmarks.

Run the committed [reproduction helper](reproduce_ink_pure_units.mjs) against a new disposable directory; it downloads exact public blobs, verifies the recorded hashes and runs only these three builtin-Node test files. All native Handy/FreeFlow/VoiceInk tests remain NOT_RUN. Native test plans require an isolated editor fixture, model presence where applicable and the exact platform permissions; a missing fixture must fail/incomplete, not silently count as a pass.

## Required behavioral trials

For each Wispr Flow, Aqua Voice, Superwhisper, Willow, OpenWhispr, Handy, FreeFlow and VoiceInk application, reserve three independent captures: success, failure/recovery, and permission/platform boundary. This document does not claim those product workflows ran. Parent REA artifacts state which public browser observations were actually possible; a homepage observation is not a dictation trial.

| Trial | Reproducible setup and action | Required evidence / blocker handling |
| --- | --- | --- |
| Successful dictation | Dedicated test editor, explicit microphone, fixed consented or synthetic fixture, English then Arabic/Gulf separately; PTT release→final→insertion | App/version/OS/backend digests, capture/partial/final/delivery timestamps, actual editor text, raw and rewritten results. Synthetic material remains diagnostic. |
| Recovery | Revoke mic/AX or disconnect input during capture; close target before finalization; cancel during STT/rewrite; copy new clipboard content during pending restore | No stale/duplicate insertion, explicit error and recoverable transcript, mic released, new clipboard preserved, late provider result rejected. Unknown recipient means refused insertion. |
| Permission/platform | Fresh standard user, protected/password/elevated target, non-Latin layout, desktop lock/resume; Windows versus native macOS and supported Linux sessions | Explicit capability outcome. No unavailable OS/device is represented as supported. No additional account/subscription/voice consent is assumed. |
| Spoken editing | Select a known sentence, speak correction containing negation/amount/date/name; switch focus before result | Digest-bound selection and preview; refuse stale replacement, unchanged meaning outside requested edit, explicit undo. Context text is untrusted data. |
| Offline/privacy | Disconnect networking before capture with local model preinstalled; optional cloud disabled; inspect permitted network telemetry | No silent provider switch; observable model/storage/routing; no clipboard/screen/context collection without per-purpose consent. Offline status NOT_MEASURED until this completes. |

Do not adopt a vendor's advertised languages, retention or latency as independent evidence. User-facing claims require measured WER/CER, semantic-distortion rate, exact-target error rate, cancellation state/latency and controlled p50/p95; all are **NOT_MEASURED** here. Saudi/Gulf dialect, code-switching and developer entities require consented human fixtures before population claims.

## Risk and acceptance register

| Risk | Source evidence | Required control before release |
| --- | --- | --- |
| Wrong-window insertion | OpenWhispr failed restore falls through; other injectors post to current recipient | Fail-closed target/process/start/focus/selection identity, expiration and final pre-injection recheck; test handle reuse and target death. |
| False insertion success | Receipt/keystroke APIs establish reads/posts rather than accepted text | Distinct `COPIED`, `INPUT_POSTED`, `PARTIAL`, `INSERTION_CONFIRMED`, `REFUSED`, `UNKNOWN`; confirmation only where supported by editor evidence. |
| Cancel UI vanishes too soon | Handy cancel shortcut unregistered on stop; OpenWhispr awaits provider stop | Separate capture/inference/rewrite/delivery stop controls and observed lifecycle; late generation result never inserts. |
| Clipboard data loss/privacy | Timer restoration, incomplete format snapshots, third-party readers | Ownership token/sequence + session, rich-format tests, budget and timeout, explicit privacy limitation. Clipboard concealment flags are conventions. |
| Broad context capture | FreeFlow desktop default enabled; VoiceInk snapshot reads clipboard and permitted screen | Screen/clipboard context off by default, purpose-bound consent, sensitive-app exclusion and scoped deletion. |
| Broad keyboard rights | handy-keys Linux evdev/uinput and Windows low-level hooks | Visible permission/scope, no raw key retention, isolated platform module; prefer narrow portal capability where adequate, report sandbox incompatibility. |
| Silent text distortion | Donor filtering, fillers/replacements/cleanup, newlines/auto-send | Keep raw immutable; tests for negation, Arabic diacritics, numbers, filenames and quoted commands; no default auto-send. |
| Native worker resource/supply-chain | 1-GiB protocol cap, C++/GPU drivers, model downloads | Smaller bounded frames, process policy/resource budget, exact worker/model digest, corrupt-input/crash/hang tests, notices/SBOM and dependency review. |

The first eligible implementation Grain after governance/000G qualification is **one native capture adapter into a deterministic test sink**, with keyboard/text fallback and no production insertion. The shortest subsequent dictation Grain adds exactly one qualified STT path and **copy/manual-paste** output; native automatic insertion opens only after the I3–I5 negative tests pass. This preserves user value while preventing unsafe donor defaults from becoming Wispral authority.
