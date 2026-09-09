# Voice Capture Product and Architecture References

**Status:** product / architecture / donor-qualification reference only  
**Source class:** external public repositories and public product documentation; no executable authority  
**Accessed:** 2026-09-07  
**Companions:** `SOURCE_ADOPTION_STRATEGY.md`, `SOURCE_DONOR_REGISTRY.md`, `source-donor-registry.json`

## Permission posture

The Founder reports separate permission to use the source code of all previously discussed source projects for Wispral.

That statement allows the project to treat otherwise useful implementation as a donor candidate instead of automatically limiting it to architecture study. Repository provenance remains mandatory: whenever an import relies on permission beyond the upstream public license, the exact permission/rights basis must be recorded in the responsible import evidence before canonical adoption.

This is especially important because Wispral has not yet selected its own repository license. The project must remain able to explain how every copied implementation may be redistributed under the eventual canonical license.

Public product documentation is different from source-code permission. A commercial product reference may inform UX, architecture questions, and threat modeling, but it does not create source-code rights or establish Wispral benchmark claims.

## Source snapshots

### OpenWhispr

- Repository: `OpenWhispr/openwhispr`
- Reviewed revision: `a9cf27b49bdcc9069922641ec39ac06d3483a125`
- Application license: MIT
- Public positioning observed at this revision: cross-platform desktop dictation, meeting transcription, local/cloud STT routing, local diarization, notes, API, and MCP.

**Donor classification:** `CODE_DONOR_CANDIDATE`, subject to exact per-file dependency/provenance review before adaptation. MIT licensing makes direct reuse comparatively straightforward, but does not waive review of bundled dependencies, model terms, native helpers, or platform-specific code.

### VoiceStudio

- Repository: `debpalash/VoiceStudio`
- Reviewed revision: `53ff367c1fdde695f17673707cd46e2b27d41546`
- Public application license: `AGPL-3.0-only`
- Public license notice states that the Tauri shell, React frontend, FastAPI backend, build/packaging scripts, and related application code are covered by AGPL-3.0-only; downloaded model weights retain upstream terms.
- Founder statement: separate permission is reported to exist for Wispral source use.

**Donor classification:** `PERMISSION_REPORTED_DONOR_CANDIDATE`. Architecture and product patterns may be used immediately as research input. Direct code adaptation becomes eligible when the responsible task records the exact separate permission/rights basis relied upon, required attribution/notices, source revision/paths, and any model/dependency terms separately.

### Superwhisper commercial product

- Product: `https://superwhisper.com`
- Source posture: commercial product/public documentation reference; no source-code relationship is assumed.
- Public product behavior reviewed on 2026-09-07 includes system-wide push-to-talk dictation, on-device and cloud speech models, an optional language-model rewrite stage, custom modes, context-aware formatting, file/meeting transcription, and cross-app text delivery.
- Public documentation describes context classes including active-application text, selected text, and recent clipboard content, with different capture times.

**Reference classification:** `PRODUCT_REFERENCE` / `ARCHITECTURE_REFERENCE`. Superwhisper is useful for product and boundary lessons only. Its published model speed/error numbers, privacy/compliance statements, and product claims are external claims and are not Wispral evidence.

### OpenSuperWhisper

- Repository: `Starmel/OpenSuperWhisper`
- Reviewed revision: `bef6bc0421d0c010e8f2fb4288c0d74978c8b964`
- License: MIT
- Platform at the reviewed revision: macOS Apple Silicon.
- The repository describes two transcription engines: Whisper and Parakeet via FluidAudio, global shortcuts including modifier-only keys, mouse-button triggers, hold-to-record behavior, microphone selection, drag/drop audio queueing, and multiple-language support.
- Relevant source seams inspected include `TranscriptionEngine.swift`, `TranscriptionService.swift`, `TranscriptionQueue.swift`, `ModifierKeyMonitor.swift`, `MouseButtonMonitor.swift`, `MicrophoneService.swift`, `FileDropHandler.swift`, `WhisperEngine.swift`, and `FluidAudioEngine.swift`.
- The repository contains upstream submodules for `whisper.cpp` and Asian autocorrect; those remain separately licensed/provenanced dependencies.

**Donor classification:** `CODE_DONOR_CANDIDATE`, subject to exact per-file dependency/provenance review before adaptation. No affiliation with, derivation from, or source relationship to the commercial Superwhisper product is inferred from the similar name. Treat them as independent references unless independent evidence establishes otherwise.

## Why these references matter to Wispral

Wispral's mission is trustworthy, low-friction voice control for independent AI coding agents. These projects are useful because they contain mature desktop voice-capture mechanics or product lessons that can inform later Wispral qualification without changing the founding product boundary.

They are **not** templates for turning Wispral into a generic dictation suite, meeting-notes product, voice-cloning studio, hosted memory service, or Electron IDE.

## OpenWhispr patterns worth qualifying

### Cross-platform hotkey abstraction

OpenWhispr does not treat Electron `globalShortcut` as a universal solution. Its hotkey layer includes platform-specific paths for GNOME, KDE, Hyprland, Windows modifier-only/right-side keys, and fallback accelerators.

**Wispral lesson:** H1/H9 push-to-talk and later hands-free controls need a platform abstraction that fails visibly and degrades deterministically. Shortcut registration success must be testable rather than assumed.

### Background and launch-at-login behavior

OpenWhispr includes launch-at-login policy, hidden startup into the tray, and repair logic for stale executable paths after updates or AppImage renames.

**Wispral lesson:** H12 distribution should treat background availability, tray state, login-item repair, and user-disabled autostart as explicit lifecycle semantics, not packaging trivia.

### Dual-stream microphone and system-audio capture

OpenWhispr's meeting recording path separates microphone and system-audio streams, requests a system-audio display stream where supported, converts audio through an `AudioWorklet` into bounded PCM chunks, and keeps the recording pipeline outside view-local React state so it survives view changes/remounts.

**Wispral lesson:** if H10 or later research ever qualifies duplex/system-audio-aware control, capture lifetimes should be independent from UI component lifetimes and source identity must remain explicit (`mic` versus `system`). No such capture is authorized now.

### Echo/bleed analysis as a pure seam

OpenWhispr isolates render-bleed/echo analysis and microphone gating into testable helpers rather than embedding the policy inside IPC plumbing. Its echo detector correlates recent system-audio history against microphone chunks and preserves distinct clean, awaiting-reference, bleed, and double-talk behavior.

**Wispral lesson:** any future AEC/duplex work under H10 should separate measurement, classification, and action policy. Suppressing or mutating speech input must be inspectable and evidence-driven.

### Meeting/session recording state machine

The meeting pipeline includes explicit start coordination, stop barriers, serial event handling, mic recovery, partial/final segment state, and source-tagged transcript segments.

**Wispral lesson:** later long-lived capture should use explicit session identity, start/stop coordination, bounded teardown, and monotonic state transitions. The reusable lesson is lifecycle design, not meeting-note functionality.

### Permission onboarding

OpenWhispr exposes microphone, system-audio, accessibility, and screen-recording permissions as explicit product states and handles platform differences rather than silently assuming permission availability.

**Wispral lesson:** H0 platform feasibility and H1 microphone state should model permission state as first-class evidence. Later context capture must remain opt-in and visibly attributable.

## VoiceStudio patterns worth qualifying

### Rust/Tauri desktop control boundary

VoiceStudio uses a Rust Tauri shell around a web UI and Python backend. Its dictation flow routes global shortcut state through Rust commands/events rather than relying only on renderer state.

**Wispral lesson:** this is architecturally adjacent to Wispral's H1 Rust-runtime direction. The preferred transplant is the native control mechanism or an independently testable equivalent, not VoiceStudio's complete application architecture.

### Dictation delivery readiness and race handling

VoiceStudio's dictation path includes explicit capture registration/readiness/acknowledgement commands and tests for setup races, stranded widgets, and shortcut delivery timing.

**Wispral lesson:** PTT capture must not lose a press because the UI/runtime listener is not ready. H1 should eventually qualify an explicit event-delivery contract with replay/ack semantics or an equivalent deterministic mechanism.

### Capability-style host-path authorization

VoiceStudio's Rust/Tauri layer uses one-shot host-path authorization tokens, validates path kinds, protects authorization files, and keeps path capability decisions separate from renderer input.

**Wispral lesson:** future native file/tool access should use explicit capability-style boundaries rather than treating renderer-provided paths as authority. Any direct transplant remains subject to exact permission/provenance qualification.

### Engine acceptance by user job

VoiceStudio's engine policy requires every ASR/TTS engine to own a specific user job, clear license/platform/adapter/test/steward/demand gates, and be deprecated when stewardship and smoke coverage disappear.

**Wispral lesson:** this is a strong governance model for H11 speech-engine extensibility. Wispral should avoid accumulating backends merely because they benchmark well. A backend should enter the product only when it wins a defined job under Wispral evidence and does not weaken portability or provenance.

### Isolation for dependency-conflicting engines

VoiceStudio uses subprocess/sidecar boundaries when an engine does not fit the core dependency profile.

**Wispral lesson:** if later STT providers require conflicting native/runtime dependencies, isolate them behind a stable adapter rather than contaminating the core runtime. No plugin system is authorized solely by this observation.

### Diagnostics and support bundles

VoiceStudio exposes self-check/diagnose paths, persistent error journaling, and scrubbed support bundles.

**Wispral lesson:** H12 should include deterministic self-diagnosis for microphone access, shortcut registration, model/runtime availability, agent transport, and local dependency state. Diagnostics should be safe to share and must not leak repository secrets or captured speech by default.

### Interface convergence

VoiceStudio exposes desktop, local REST/SSE/WebSocket, OpenAI-compatible audio, and MCP surfaces over a common backend.

**Wispral lesson:** H11 may later benefit from multiple interfaces over one semantic control model, but CLI/MCP/API surfaces must not become independent authority systems. Current roadmap gates remain unchanged.

## Superwhisper product patterns worth carrying forward

### Separate speech recognition from rewrite/interpretation

Superwhisper publicly describes a two-stage pipeline: a speech-recognition model produces text, followed optionally by a language model that rewrites or formats the result.

**Wispral lesson:** keep raw STT evidence and downstream interpretation/transformation as separate typed stages with separate provider identity, timing, provenance, cancellation, and failure semantics. A language-model rewrite must never silently replace the transcript used for audit or benchmark evidence.

### Explicit local/cloud provider posture

Superwhisper exposes local and cloud speech/language choices rather than presenting them as one opaque engine.

**Wispral lesson:** any future remote provider must be explicit in current state, credentials, network path, fallback policy, and evidence. Local failure must not silently route speech to cloud. Provider choice belongs to policy/configuration, not hidden adapter behavior.

### Context-aware modes are policy surfaces

Superwhisper uses modes to control which model and context classes are used and how text is transformed.

**Wispral lesson:** if Wispral later supports context-enriched voice instructions, the enabled context classes and transformation policy should be explicit, inspectable, and tied to a named user job. Do not build a generic prompt-mode system merely because a dictation product has one.

### Context capture timing is part of provenance

Superwhisper documentation describes selected text as captured at recording start, clipboard context in a bounded time window around dictation, and application context after voice processing. It also documents that changing windows before application-context capture can change what is observed.

**Wispral lesson:** context must carry capture time, source identity, focus/window identity where applicable, and the turn/session it belongs to. A later focus change must not silently rebind a spoken instruction to a different repository/app/window context. Context capture should be minimized to the classes needed by the active job.

### Visible capture and cancellation state

Superwhisper exposes recording, context-capture, stop, and cancel states in its recording UI.

**Wispral lesson:** every consequential capture/context stage should have a non-voice observable state, including terminal-visible state during founding horizons. Cancellation semantics still require backend evidence that execution actually stopped.

## OpenSuperWhisper patterns worth qualifying

### Minimal transcription-engine protocol

`TranscriptionEngine.swift` defines a small provider surface around initialization, transcription, cancellation, model-loaded state, engine identity, and supported languages. `TranscriptionService.swift` owns engine selection and serializes access so a shared engine context is not used concurrently.

**Wispral lesson:** H11 provider replaceability benefits from a small Wispral-owned contract. However, do not copy the current special-casing of concrete engine classes for progress reporting; a Wispral provider contract should expose progress/events generically if required.

### Modifier-only and left/right-specific activation

`ModifierKeyMonitor.swift` distinguishes left/right Command, Option, Shift, Control, and Fn using a `CGEvent` tap. It observes press/release transitions and attempts to re-enable the event tap after timeout/user-input disablement.

**Wispral lesson:** macOS PTT feasibility should explicitly test modifier-only and side-specific shortcuts, tap disable/re-enable behavior, accessibility permission loss, repeated transitions, and teardown. A failed event tap must become typed state/diagnostics, not only a console print.

### Mouse-button activation with event consumption

`MouseButtonMonitor.swift` can bind middle/extra mouse buttons and consume the matched event so the focused app does not also execute its normal action.

**Wispral lesson:** alternate PTT controls can materially reduce keyboard friction, but event consumption is an authority-bearing behavior. Any future mouse-button binding must be explicit, reversible, observable, and tested so unbound events pass through unchanged.

### Microphone identity, hot-plug, and fallback

`MicrophoneService.swift` enumerates audio devices, observes connect/disconnect events, persists a selected microphone, detects Bluetooth/Continuity characteristics, and falls back when the selected device disappears.

**Wispral lesson:** H1 should treat input-device identity and device-change events as part of capture state. Fallback must be visible; the runtime must not silently switch from a selected external microphone to another device during a consequential turn.

### Queue, cancellation, and source-file ownership

`TranscriptionQueue.swift` serializes queued work, tracks the current recording, propagates cancellation to the provider task, rejects missing source files, and differentiates temporary microphone recordings from user-provided imported files when moving/copying/deleting data.

**Wispral lesson:** later queued/offline jobs should make ownership/retention explicit, preserve user-owned sources, and keep cancellation semantics independent of UI state. The founding PTT path does not require importing a file-transcription product surface.

### Multiple local engines without monolithic inheritance

At the reviewed revision, OpenSuperWhisper supports Whisper and Parakeet/FluidAudio behind the same application-level engine protocol.

**Wispral lesson:** the useful donor seam is provider isolation and switching mechanics, not the particular engine ranking. Wispral's canonical bakeoff remains the only authority for current STT selection.

## Candidate carry-forward matrix

| Pattern | Primary source | Wispral horizon | Current disposition |
| --- | --- | --- | --- |
| Cross-platform shortcut abstraction | OpenWhispr | H1, H9, H12 | `DONOR_CANDIDATE` |
| Hidden tray + launch-at-login repair | OpenWhispr | H12 | `DONOR_CANDIDATE` |
| Source-separated mic/system audio | OpenWhispr | H10, H15 | `DEFERRED_DONOR_CANDIDATE`; no current capture authority |
| Echo/bleed detector + mic gate seams | OpenWhispr | H10 | `DEFERRED_DONOR_CANDIDATE` |
| Long-lived capture session lifecycle | OpenWhispr | H9, H10 | `DONOR_CANDIDATE` |
| Permission-state modeling | OpenWhispr | H0E, H1 | `DONOR_CANDIDATE` |
| Native Rust shortcut/capture boundary | VoiceStudio | H1, H12 | `PERMISSION_REPORTED_DONOR_CANDIDATE` |
| Capture readiness/ack race handling | VoiceStudio | H1 | `PERMISSION_REPORTED_DONOR_CANDIDATE` |
| Capability-style host-path authorization | VoiceStudio | H7, H12 | `PERMISSION_REPORTED_DONOR_CANDIDATE` |
| Job-based engine acceptance | VoiceStudio | H11 | `GOVERNANCE_REFERENCE` |
| Engine subprocess isolation | VoiceStudio | H11 | `ARCHITECTURE/DONOR_CANDIDATE` |
| Self-check and scrubbed diagnostics | VoiceStudio | H12 | `PERMISSION_REPORTED_DONOR_CANDIDATE` |
| REST/WebSocket/MCP convergence | VoiceStudio | H11 | `DEFERRED_RESEARCH` |
| STT -> optional LM rewrite separation | Superwhisper | H5, H6, H11 | `PRODUCT/ARCHITECTURE_REFERENCE` |
| Explicit local/cloud model posture | Superwhisper | H11, H12 | `PRODUCT/SECURITY_REFERENCE` |
| Context-mode visibility and minimization | Superwhisper | H4, H5, H6 | `PRODUCT/ARCHITECTURE_REFERENCE` |
| Context capture timing/focus provenance | Superwhisper | H4, H5, H6 | `SECURITY/ARCHITECTURE_REFERENCE` |
| Modifier-only / side-specific macOS PTT | OpenSuperWhisper | H1, H9 | `DONOR_CANDIDATE` |
| Mouse-button PTT with explicit consumption | OpenSuperWhisper | H1, H9 | `DONOR_CANDIDATE` |
| Microphone hot-plug/selection state | OpenSuperWhisper | H1, H12 | `DONOR_CANDIDATE` |
| Minimal local transcription provider protocol | OpenSuperWhisper | H11 | `DONOR_CANDIDATE` |
| Queued cancellation/source ownership | OpenSuperWhisper | H11, H12 | `DONOR_CANDIDATE`; file-transcription UI remains out of founding scope |

## Legal and provenance rules

1. Founder-reported source-use permission expands donor eligibility; it does not remove the need to record the rights basis relied upon for each incompatible/copyright-sensitive import.
2. Treat model/tokenizer/data/binary assets as separately licensed unless exact permission evidence includes them.
3. For OpenWhispr, preserve required MIT notices for substantial copied portions and still inspect dependency/native-helper terms.
4. For VoiceStudio, record exact separate permission terms before copying AGPL-covered implementation into a Wispral tree whose canonical license may differ.
5. For OpenSuperWhisper, preserve required MIT notices for substantial copied portions and separately qualify `whisper.cpp`, FluidAudio/Parakeet assets, Asian autocorrect, models, binaries, and any other transitive dependency before adoption.
6. Do not infer that OpenSuperWhisper is an official/open-source version of the commercial Superwhisper product from naming similarity.
7. Do not import external workflows, dependency lockfiles, native binaries, model weights, telemetry, cloud services, or generated artifacts merely because source code is eligible for use.
8. External benchmark claims remain experiment-design inputs, not Wispral qualification evidence.
9. Any adopted donor code must be tied to an authorized Wispral task and independently tested against Wispral's own acceptance criteria.

## Explicit non-goals created by this reference

This research reference does not authorize:

- a generic meeting recorder or meeting-notes product;
- always-on or invisible microphone/system-audio capture;
- screen/application/clipboard context capture by default;
- screen capture by default;
- voice cloning, dubbing, audiobook production, or broad TTS studio functionality;
- an Electron IDE;
- a hosted note/memory platform;
- cloud transcription as a requirement or silent fallback;
- a generic prompt/mode marketplace;
- a plugin marketplace;
- macOS-only product architecture merely because OpenSuperWhisper is macOS-native;
- any change to the active `000B2` recovery frontier, candidate set, C0 methodology, scorer, or claim guards.

## Relationship to the active frontier

The active public-corpus recovery sequence remains authoritative. This note is intentionally non-executable and must not alter B2R07/B2R08+ authorization, ATTEMPT-002 identities, or benchmark comparability.

If these references are later used to shape implementation, the responsible specification must re-verify the source revision, rights basis, dependencies, platform behavior, and exact adopted files at that time.
