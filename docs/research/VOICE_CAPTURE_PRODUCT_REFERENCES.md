# Voice Capture Product and Architecture References

**Status:** product / architecture / donor-qualification reference only  
**Source class:** external public repositories; no executable authority  
**Accessed:** 2026-09-06  
**Companions:** `SOURCE_ADOPTION_STRATEGY.md`, `SOURCE_DONOR_REGISTRY.md`, `source-donor-registry.json`

## Permission posture

The Founder reports separate permission to use the source code of all previously discussed source projects for Wispral.

That statement allows the project to treat otherwise useful implementation as a donor candidate instead of automatically limiting it to architecture study. Repository provenance remains mandatory: whenever an import relies on permission beyond the upstream public license, the exact permission/rights basis must be recorded in the responsible import evidence before canonical adoption.

This is especially important because Wispral has not yet selected its own repository license. The project must remain able to explain how every copied implementation may be redistributed under the eventual canonical license.

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

## Why these references matter to Wispral

Wispral's mission is trustworthy, low-friction voice control for independent AI coding agents. These projects are useful because they contain mature desktop voice-capture mechanics that can inform later Wispral qualification without changing the founding product boundary.

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

## Legal and provenance rules

1. Founder-reported source-use permission expands donor eligibility; it does not remove the need to record the rights basis relied upon for each incompatible/copyright-sensitive import.
2. Treat model/tokenizer/data/binary assets as separately licensed unless exact permission evidence includes them.
3. For OpenWhispr, preserve required MIT notices for substantial copied portions and still inspect dependency/native-helper terms.
4. For VoiceStudio, record exact separate permission terms before copying AGPL-covered implementation into a Wispral tree whose canonical license may differ.
5. Do not import external workflows, dependency lockfiles, native binaries, model weights, telemetry, cloud services, or generated artifacts merely because source code is eligible for use.
6. External benchmark claims remain experiment-design inputs, not Wispral qualification evidence.
7. Any adopted donor code must be tied to an authorized Wispral task and independently tested against Wispral's own acceptance criteria.

## Explicit non-goals created by this reference

This research reference does not authorize:

- a generic meeting recorder or meeting-notes product;
- always-on or invisible microphone/system-audio capture;
- screen capture by default;
- voice cloning, dubbing, audiobook production, or broad TTS studio functionality;
- an Electron IDE;
- a hosted note/memory platform;
- cloud transcription as a requirement;
- a plugin marketplace;
- any change to the active `000B2` recovery frontier, candidate set, C0 methodology, scorer, or claim guards.

## Relationship to the active frontier

The active public-corpus recovery sequence remains authoritative. This note is intentionally non-executable and must not alter B2R07/B2R08+ authorization, ATTEMPT-002 identities, or benchmark comparability.

If these references are later used to shape implementation, the responsible specification must re-verify the source revision, rights basis, dependencies, platform behavior, and exact adopted files at that time.