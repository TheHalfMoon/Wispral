# WisprSide: source, fork-qualification and competitor research

**Date:** 2026-11-08. **Mission:** Wispral master plan, WisprSide (voice dictation companion). **Mode:** read-only research. Nothing was pushed, commented, starred, forked, purchased, signed into or installed. No donor build or donor test was run.

**Builds on:** `pr124:research/rea/2026-10-21/{WISPRSIDE_DEEP_DIVE.md, FORK_BOUNDARY_COMPARISON.md, source-transplants.json (INK-I1..I13), FEATURE_PARITY_AND_GAP_MATRIX.md}` and the Opus review `pr125:.../INDEPENDENT_REVIEW.md`, whose S1 recommends forking Handy at `93c9ee05`. Prior observations are not repeated here unless the pinned source has changed or a new decision depends on them.

## Contents

0. [Method, evidence tags and limits](#0-method-evidence-tags-and-limits)
1. [Drift since the 2026-10-21 pins, and the Handy re-pin](#1-drift-since-the-2026-10-21-pins-and-the-handy-re-pin)
2. [Handy fork qualification at the recommended SHA](#2-handy-fork-qualification-at-73cc857)
3. [Windows text-insertion safety](#3-windows-text-insertion-safety)
4. [Feature capability inventory](#4-feature-capability-inventory)
5. [Competitors, parity matrix and differentiation](#5-competitors-parity-matrix-and-differentiation)
6. [What must be built new](#6-what-must-be-built-new)
7. [Work packets (MVP and RC)](#7-work-packets-mvp-and-rc)
8. [Open decisions and residual risks](#8-open-decisions-and-residual-risks)
9. [Appendix: reproduction](#9-appendix-reproduction)

---

## 0. Method, evidence tags and limits

### Evidence tags

| Tag | Meaning in this report |
| --- | --- |
| `SOURCE_VERIFIED (repo@sha:path:line)` | I read the line in the stated revision. It proves what the code says, not how it behaves at runtime. |
| `DOCUMENTED (URL)` | An official vendor or platform page states it. All pages were accessed 2026-11-08. It proves a claim was made, not that it is true. |
| `REPRODUCED` | A deterministic local command over pinned bytes produced the number (git counts, grep counts, JSON parses). The commands are in §9. |
| `RUNTIME_OBSERVED` | Not used. No donor or competitor app was launched. |
| `NOT_RUN` | The behaviour needs a build, device, microphone, account or OS that was not exercised. |
| `BLOCKED_EXTERNAL` | A source could not be fetched. |
| `REJECTED` | Considered and ruled out, with the reason. |

### Revision identities

| Short form | Repository | Revision (full SHA) | Commit date | State |
| --- | --- | --- | --- | --- |
| `Handy@93c9ee0` | cjpais/Handy | `93c9ee05efe294cf2a56bd534b77ea1079f21b77` | 2026-10-20 | Prior pin |
| **`Handy@73cc857`** | cjpais/Handy | **`73cc8579cff74e97e08de9d86035a92e4335ff7f`** | 2026-11-06 | **Current `main` HEAD; recommended re-pin** |
| `OW@e4280ad` | OpenWhispr/openwhispr | `e4280ada144f04f20dad0bd32eaf22272f9c77b8` | 2026-10-21 | Prior pin |
| `OW@cb08c41` | OpenWhispr/openwhispr | `cb08c411dd008c57e4f0a8193756d6b5812479fd` | 2026-11-07 | Current HEAD |
| `VI@22e5ec5` | Beingpax/VoiceInk | `22e5ec5479b712797c3b338fcb875961e58800b6` | 2026-10-20 | Prior pin |
| `VI@4bc74ca` | Beingpax/VoiceInk | `4bc74caddfad6fdfab71e5957451b83b33c1a2c5` | 2026-11-06 | Current HEAD |
| `FF@797a3f3` | zachlatta/freeflow | `797a3f32e6b525b8d942512db2801466d3a651f7` | 2026-10-16 | Prior pin |
| `FF@3778646` | zachlatta/freeflow | `37786464bb2422c58313d7456fe7191d115d0d18` | 2026-11-05 | Current HEAD |

All four prior pins are ancestors of the current HEADs (`git merge-base --is-ancestor`, REPRODUCED).

### How sources were obtained

- Each repository was fetched as a blobless partial clone (`--filter=blob:none`), with hooks disabled, into `<scratchpad>\side\{Handy, ow, VoiceInk, freeflow}`. OpenWhispr sits in `side\ow` because `side\openwhispr` exceeded the Windows MAX_PATH limit that git's HTTPS helper enforces.
- Only Handy was checked out, at `73cc857`, so its tree could be read. The other repositories were read with `git show <sha>:<path>`.
- Donor files are untrusted data. Handy's `AGENTS.md`/`CLAUDE.md` and OpenWhispr's `CLAUDE.md` were not read as instructions.
- Python ran only with `-I`, from scripts in `<scratchpad>\scripts`, with donor paths passed as arguments.
- Competitor facts come only from official vendor, Microsoft and Tauri pages, gathered by me and by two read-only research sub-agents.

### What was not done (NOT_RUN)

- Building Handy, running cargo, bun or Playwright tests, or making a packaged install.
- Microphone capture, model inference (Arabic included) and any native insertion.
- Packet capture of egress.
- Competitor apps: no product was installed or used. Competitor statements are vendor claims (DOCUMENTED), not observations.

---

## 1. Drift since the 2026-10-21 pins, and the Handy re-pin

### 1.1 Volume of change (REPRODUCED)

| Donor | Commits pin..HEAD (first-parent / all) | Files changed | Lines (+/−) | Notes |
| --- | ---: | ---: | --- | --- |
| Handy | 32 / 36 | 262 | +28,712 / −7,202 | Release v0.10.0 (2026-11-02), then a TLS advisory lock bump |
| OpenWhispr | 95 / 350 | 1,556 | +232,388 / −31,522 | v1.11.1; much of the growth is mobile, agent and enterprise work |
| VoiceInk | 26 / 67 | 143 | +16,173 / −5,612 | Releases 2.25 and 2.26 |
| FreeFlow | 4 / 14 | 25 | +3,679 / −128 | Original-field insertion; optional window context |

### 1.2 Handy commits that touch relevant modules (SOURCE_VERIFIED via `git log`/`git diff 93c9ee0..73cc857`)

**Paste and insertion (`clipboard.rs`, `input.rs`)**
- `5a9451e` (#2302): paste now runs on a worker thread. Input injection hops to the main thread through `with_enigo`.
- A process-wide `PASTE_LOCK` serialises pastes. Its comment says overlapping pastes "would restore each other's transcript as the user's clipboard": a clipboard-leak class fixed after the pin (`Handy@73cc857:src-tauri/src/clipboard.rs:18-20,823`).
- **Security fix:** the Linux `dotool` typing path used to write `type <text>` on one stdin line. A transcript containing a newline could therefore run dotool commands such as `key super+l`. It now emits one `type` command per line plus `key enter` (`Handy@73cc857:src-tauri/src/clipboard.rs:497-518`), with tests `dotool_script_does_not_run_lines_of_text_as_commands` (`:1012-1021`).
- The Windows paths in `paste_tx/` did not change.

**Coordinator (`transcription_coordinator.rs`)**
- Adds `RecordingPhase {Started, Locked, Stopped, Cancelled}` events (`:17-41`).
- A cancel while transcribing now ends the take (`:613-622`).
- Existing busy-parity and autorepeat logic is unchanged.

**Hotkeys (`shortcut/handy_keys.rs`, `shortcut/mod.rs`)**
- `8020c87` (#2327): `HotkeyManager::new_with_blocking()` now runs before the manager thread starts. A startup failure (for example a missing permission) therefore reaches the caller, which falls back to the Tauri implementation (`handy_keys.rs:95-101`).
- `298653c`: Linux ibus default changed.

**Engine supervisor (`engine_supervisor/*`): no change** (empty diff, REPRODUCED). The 1 GiB frame-section cap and "model loads are never cancelled" still apply (`protocol.rs:19`, `supervisor.rs:471-475`).

**Models and transcription**
- `126bed7` (#2331) adds language detection: `language_detection/{mod,policy,detector,speech}.rs` plus a downloadable VoxLingua107 ECAPA detector.
- `73c0958` (#2315) adds transcription of audio files into history: `audio/decode.rs`, using symphonia for AAC/ALAC/MP4/AIFF. **This is a new media-parsing attack surface.**
- Catalog sync (`@handy-computer/models` 0.2.2→0.2.3), a reworked model manager (+581/−?), and download progress with a rate meter.
- `889fca0` (#2290): a blank post-processing reply now falls back to the raw transcript, through a new `PostProcessOutcome` (`actions.rs:183-191`).

**Windows**
- `f81e7e7`: chip label centring.
- WebView2 accelerator handling is unchanged.
- No Windows-specific insertion change.

**New surfaces with security relevance**
- `transcription_hook.rs`: an optional executable at `<app data>/hooks/transcription` receives the transcript on stdin, and its stdout is pasted instead (30 s timeout; `Handy@73cc857:src-tauri/src/transcription_hook.rs:1-31`; called at `actions.rs:831-843`). Any process able to write the app data directory gets code execution with the transcript as input. **WisprSide must compile it out** (§7, WS-M2).
- `notices.rs`: an error-notice framework adding `NoticeCode::PasteFailed` and `PostProcessFailed`.

**Dependencies**
- `73cc857` (#2432) moves `openssl` 0.10.75→0.10.82, `openssl-sys` 0.9.111→0.9.118, `rustls` 0.23.36→0.23.46 and `rustls-webpki` 0.103.9→0.103.16. The commit is titled "address TLS dependency security advisories".
- Lock-only: Cargo.lock, 8+/9−.

**UI**
- New onboarding (`0e5e9ca`), a tray language submenu, an error-notice panel.
- Accessibility fixes: Escape dismisses menus and tooltips; reset buttons and the playback control are named (`a537ec4`, `77ad955`, `3b60fc7`, `8fd85aa`).

### 1.3 Other donors: relevant drift

**OpenWhispr (`OW@cb08c41`)**
- **`resources/windows-fast-paste.c` is byte-identical to the pin** (blob `e542c122…` at both revisions, REPRODUCED). The fall-through-to-current-foreground defect is still present (`OW@cb08c41:resources/windows-fast-paste.c:281-291`).
- `src/helpers/windowsPasteTarget.js` is also unchanged (blob `f6ad812a…`). It still treats an unreadable exe name as a valid foreign target (`:25-28`).
- `clipboard.js` changed (+204 lines); the Windows fast-paste path still falls back to nircmd/PowerShell on failure or timeout (`clipboard.js:1477-1498`).
- Relevant new commits:
  - `f1b1aa19`: AltGr no longer triggers Ctrl+Alt hotkeys on Windows.
  - `3164664b`/`4be52ca0`/`999a9e23`: selection-edit fixes.
  - `88d6e360`: local model allow-lists.
  - `315ee2de`: model catalog read from a signed registry.
  - Linux and macOS paste fixes.
- Version is 1.11.1. Most growth is mobile, agent and enterprise (`openwhispr-mobile/`, assistant skills, Azure gateway). That raises the cost of inheriting the whole app; it does not change the narrow-helper decision.

**VoiceInk (`VI@4bc74ca`)**
- The `CursorPaster` outcome vocabulary is unchanged: `commandPosted / commandNotPosted / commandPartiallyPosted` (`VI@4bc74ca:VoiceInk/Infrastructure/SystemIntegration/Paste/CursorPaster.swift:11-14`). Restore still checks expected text plus session marker before replacing the clipboard (`:231-235`).
- New: `PasteFocusDiagnostics.swift`, `RemoteTextTyper.swift` (typing for remote desktops), `SmartPunctuation.swift`, filler-removal capitalisation repair (`9b2dd5a`), in-house selected-text service (`3e31732`), and auto-learn dictionary rework.
- Licence is still GPLv3 (`LICENSE`); GitHub reports NOASSERTION.

**FreeFlow (`FF@3778646`)**
- **New, highly relevant:** opt-in "original field insertion" (`0fe9b2f`). A pure `AppTextInsertionCore` has result type `AppTextInsertionResult {inserted, notInserted, unverified, unavailable}` (`FF@3778646:Sources/AppTextInsertionCore.swift:3-9`).
  - Secure-text-field exclusion (`:28-35`).
  - Range-local write with readback classification (`:44-104`).
  - `pasteIfTargetMatches`, which re-verifies focus, value and selection before and after clipboard preparation (`:106-137`).
  - Tests: `Tests/AppTextInsertionCoreTests.swift` (692 lines) and `AppTextInsertionDispatchTests.swift` (888 lines), NOT_RUN (macOS).
  - The preference defaults off (`Sources/OriginalFieldInsertionPreference.swift`).
  - This is the best available fail-closed **algorithm** donor (MIT). Its platform calls are macOS AX.
- Context capture still defaults on, and the desktop screenshot fallback still defaults to `true` (`FF@3778646:Sources/AppContextService.swift:35-42`; `Sources/AppState.swift:731-733`). The prior rejection of FreeFlow's context policy stands.

### 1.4 Re-pin recommendation

**Re-pin the WisprSide fork lead to `Handy@73cc857` (`73cc8579cff74e97e08de9d86035a92e4335ff7f`).** Reasons:

1. **Security fixes landed after `93c9ee0`:**
   - TLS dependency advisories (openssl/rustls/webpki).
   - A transcript-to-command injection on the Linux dotool path.
   - A clipboard cross-restore race fixed by `PASTE_LOCK`.

   A fork at `93c9ee0` would have to backport all three on day one.
2. **CI on this exact SHA is green:**
   - 9 check runs, all `completed/success`: 7 platform builds (windows-latest x64, windows-11-arm, macos ×2, ubuntu ×3), `rust-tests` and `nix-build`. Source: `gh api repos/cjpais/Handy/commits/73cc857/check-runs`, REPRODUCED 2026-11-08.
   - Caveat: the combined *status* API reported `pending`. Check runs are what this repository uses; the status may come from an unrelated status context.
3. **Release proximity:** the SHA is the v0.10.0 release (tag commit `82dfab9`, 2026-11-02) plus one lock-only security commit.
4. **WisprSide-relevant capability gained:**
   - Per-utterance language detection, which matters for Arabic/English.
   - Structured paste and post-process failure notices, which are the seed of a delivery-outcome UI.
   - Main-thread-safe paste.
5. **The modules the prior plan depends on are unchanged:** `paste_tx/*`, `engine_supervisor/*`, `secure_input.rs`, `portable.rs`, `cli.rs`, `managers/transcription/policy.rs` all have empty diffs. Prior INK-I3/I4/I5/I10/I13 seam analysis carries over without rework.

**What the re-pin costs:**
- New surfaces to gate:
  - The transcription hook, to compile out.
  - File-decode media parsing (symphonia), to disable or fuzz.
  - The language-detector download, a new user-initiated egress.
- The onboarding rewrite enlarges the UI to rebrand.

`OW`, `VI` and `FF` stay **reference/narrow donors**. Cite their current HEADs above for any ADAPT, and re-check the specific file blob before porting. No donor is to be tracked at a moving branch.

---

## 2. Handy fork qualification at `73cc857`

### 2.1 Licence and stack

| Item | Finding | Evidence |
| --- | --- | --- |
| Licence | MIT, "Copyright (c) 2025 CJ Pais"; Cargo `license = "MIT"` | SOURCE_VERIFIED `Handy@73cc857:LICENSE:1-3`, `src-tauri/Cargo.toml:7` |
| App version | 0.10.0 (Cargo, package.json, tauri.conf.json) | `Cargo.toml:3`, `package.json:4`, `tauri.conf.json:4` |
| Shell | Tauri **2.11.5** (locked), plugins: log, opener, store, os, clipboard-manager 2.3.2, macos-permissions, process, fs, dialog, autostart, global-shortcut, single-instance, updater 2.10.1 | `Cargo.toml:32-46,96-100`; `Cargo.lock` (tauri 2.11.5) |
| Frontend | React 18.3, Vite 6.4, TypeScript 5.6, Tailwind 4, zustand 5, i18next 25/react-i18next 16, zod, react-markdown, lucide | `package.json:28-71` |
| Package manager | **bun** (`bun.lock`; scripts use `bun`), Nix flake also maintained | `package.json:17-26`, `flake.nix` |
| Speech engine | `transcribe-cpp 0.4.0` (+ `transcribe-cpp-sys 0.4.0`, ggml/GGUF). Windows x64 builds `dynamic-backends` + `vulkan`; Windows ARM64 static, CPU-only | `Cargo.toml:83-86,123-129` |
| Audio capture | `handy-recorder 0.1.0` (MIT crate; prior archive hash `4a734d6d…` verified 2026-10-21) | `Cargo.toml:61`; Cargo.lock |
| Hotkeys | `handy-keys 0.3.4` (default on Windows/macOS); `tauri-plugin-global-shortcut` fallback; `rdev` (git `a90dbe11…`) | `Cargo.toml:87,51`; `settings.rs:241-248` |
| Input injection | `enigo 0.6.1`; Windows clipboard transaction via `windows 0.61.3` Win32 APIs | `Cargo.toml:57,108-123` |
| VAD | Silero (`audio_toolkit/vad/silero.rs`), earshot (`vad/earshot.rs`), smoothing (`vad/smoothed.rs`) | tree |
| Storage | SQLite (`rusqlite 0.37` bundled, `rusqlite_migration`), tauri-plugin-store settings | `Cargo.toml:47,76` |
| Network clients | `reqwest 0.12.28` (+0.13.2 transitively), `hf-hub` (git fork `cjpais/hf-hub@9918f11a`, cancellable downloads) | `Cargo.toml:62,93-95`; Cargo.lock |
| Scale | 47 base `[dependencies]` names; 852 locked packages; 4 git-sourced crates (tauri-nspanel, hf-hub fork, tao fork `c3bee28c`, rdev); 36,662 Rust lines across `src-tauri/src`; 216 TS/TSX files | REPRODUCED |

### 2.2 Complete module map (`src-tauri/src/` unless stated)

| Capability | Path(s) | Notes |
| --- | --- | --- |
| Recorder | `managers/audio.rs` (`try_start_recording`, cancel generations, `stop_recording`), `audio_toolkit/audio/{device,sink,utils,visualizer}.rs`, crate `handy-recorder` | Prior INK-I1 analysis holds; `last_input_silent()` added (digital-silence detection) |
| VAD | `audio_toolkit/vad/{mod,silero,earshot,smoothed}.rs`; `default_vad_enabled() = true` (`settings.rs:635`) | Silero model is a catalog entry (`silero-vad-v6.2`) |
| Hotkeys / activation | `shortcut/{mod,handler,handy_keys,tauri_impl}.rs`; `ShortcutActivation {Toggle, PushToTalk, HoldOrToggle(default)}` (`settings.rs:173-186`), `hold_threshold_ms = 300` (`settings.rs:584-586`); `KeyboardImplementation::None` allows CLI/signal-only triggering | Cancel shortcut registered at record start, **unregistered at stop** (`actions.rs:634,662`; `shortcut/mod.rs:73-89`) |
| Transcription coordinator | `transcription_coordinator.rs` (pure `CoordinatorState`, `Stage`, `Effect`; 36 tests) | `DEBOUNCE 30 ms`, `RELEASE_GRACE 50 ms` (`:15-16`) |
| Transcription pipeline | `actions.rs` (`TranscribeAction::start` `:478`, `stop` `:655`), `managers/transcription.rs`, `managers/transcription/{policy,live,chunked,job}.rs`, `managers/transcription_jobs.rs` | Streaming `committed/tentative` preserved |
| Engine supervisor | `engine_supervisor/{mod,protocol,supervisor,worker}.rs` | Unchanged since prior pin |
| Model manager / download | `managers/model.rs` (`download_model` `:2264`; HF via `ApiBuilder::from_env()` `:2033`), `managers/model/download.rs` (resumable HTTP, size cap, SHA-256 verify), `catalog/{mod.rs,catalog.json}` (bundled offline catalog, 76 models; `MIRRORS = ["https://blob.handy.computer"]` `catalog/mod.rs:36`), `managers/{gguf_meta,model_capabilities}.rs`, `commands/models.rs` | Downloads are user-triggered (onboarding pick or model table) |
| Language handling | `language_detection/*` (picks between the user's `spoken_languages`), `languages.rs`, `system_languages.rs`, `audio_toolkit/lang_id.rs`, `chinese_script.rs` | One language per utterance (`language_detection/mod.rs:1-3`) |
| Text post-processing | `audio_toolkit/text.rs` (`apply_custom_words` `:151`, `remove_filler_words` `:429`), `llm_client.rs` (OpenAI-compatible + Anthropic format), `apple_intelligence.rs` (macOS ARM only) | Custom-word fuzzy keys are ASCII-only (`text.rs:58-64`) |
| Paste / insertion (all OS) | `clipboard.rs` (`paste` `:822`, `paste_via_clipboard` `:74`, `paste_direct`, Linux tool dispatch), `input.rs` (chords; `paste_text_direct` via `enigo.text` `:268-274`) | Default method Ctrl+V on Windows/macOS, Direct on Linux (`settings.rs:250-258`) |
| Paste / insertion (Windows) | Legacy: `clipboard.rs:74-138` + `input.rs:179-206`. Receipt transaction: `paste_tx/windows.rs` (message-only window, delayed render, `WM_RENDERFORMAT` receipts, full-format snapshot, sequence-guarded restore) gated by `reliable_paste` (default **false**, `settings.rs:1055`) | See §3 |
| Clipboard handling | `ClipboardHandling {DontModify(default), CopyToClipboard}` (`settings.rs:188-194`); history-page copy (`src/components/settings/history/clipboard.test.ts`) | |
| Secure input detection | `secure_input.rs` (**macOS-only**: `IsSecureEventInputEnabled` polling for hotkey resilience; non-macOS stub at `:668`) | Not a paste-refusal guard; nothing equivalent on Windows |
| Overlay / indicator | `overlay.rs` (topmost, non-activating; Windows `SetWindowPos HWND_TOPMOST` `:175-188`), `src/overlay/RecordingOverlay.tsx` (cancel button `:296-299`), `OverlayStyle::Live` default on Windows/macOS (`settings.rs:626-633`) | |
| Settings | `settings.rs` (schema v2, migrations), `src/components/settings/*` (≈50 setting components) | |
| History | `managers/history.rs` (SQLite `transcription_history`, raw `transcription_text` + `post_processed_text` + prompt; audio file per entry; migrations `:23-35`), `commands/history.rs`, `RecordingRetentionPeriod {Never, PreserveLimit(default), Days3, Weeks2, Months3}` (`settings.rs:221-229`), `history_limit = 5` (`settings.rs:684-686`) | Raw transcript kept separately from post-processed text |
| Tray | `tray.rs` (Cancel item during Recording/Transcribing `:696-702`; new language submenu), `tray_i18n.rs` | |
| Onboarding / permissions | `src/components/onboarding/*` (Welcome, Permissions, Model, TryIt, Demo screens; `usePermissions.ts`; `downloadPick.ts`), `tauri-plugin-macos-permissions` | Windows needs no permission step for hooks; mic privacy prompt is OS-level |
| Updater | `tauri-plugin-updater` (`lib.rs:932`), `src/components/update-checker/UpdateChecker.tsx`, portable fallback `portableInstaller.ts` | **Default on**; see §2.6 |
| CLI | `cli.rs` (`--start-hidden`, `--no-tray`, `--toggle-transcription`, `--toggle-post-process`, `--cancel`, `--debug`, `-f/--transcribe-file`, `--model`, `--list-devices`, `--list-models`, `--json`, repeat) | |
| Portable mode | `portable.rs` (marker file `portable` next to exe → `Data/`), NSIS custom page | |
| Autostart / single instance | `autostart.rs` (default off, `settings.rs:600-602`), `tauri-plugin-single-instance` | |
| i18n | `src/i18n/{index.ts,languages.ts}`, 26 locales incl. **`ar`** (`direction: "rtl"`, `languages.ts:35`) and `he`; `src/lib/utils/rtl.ts`; root container `dir={direction}` (`src/App.tsx:319`); `scripts/check-translations.ts` in CI | Arabic locale: 664/664 keys present, 20 values identical to English (REPRODUCED) |
| Accessibility | 133 `aria-*` and 26 `role=` attributes in TSX; `role="status"` notice live region (`components/notices/NoticePanel.tsx:155`); `prefers-reduced-motion` CSS (`App.css:167`) | Overlay cancel `aria-label="cancel"` is not localised (`RecordingOverlay.tsx:299`); no live announcement of recording state in the overlay |
| Error notices | `notices.rs` (`NoticeCode::PasteFailed`, `PostProcessFailed`, recording codes), `src/components/notices/*` | |
| Hook / script exec | `transcription_hook.rs`; `PasteMethod::ExternalScript` (`clipboard.rs:895-901`) | Both must be disabled for WisprSide |

### 2.3 Test inventory (counts are definitions or files, not collected or passing tests; REPRODUCED)

| Kind | Count | Notes |
| --- | ---: | --- |
| Rust `#[test]` / `#[tokio::test]` definitions | **368** in **43** files | Largest: `audio_toolkit/text.rs` 44, `transcription_coordinator.rs` 36, `settings.rs` 30, `managers/model.rs` 22, `managers/transcription.rs` 20, `managers/model/download/tests.rs` 19, `llm_client.rs` 18, `engine_supervisor/supervisor.rs` 18, `actions.rs` 13, `clipboard.rs` 12, `paste_tx/mod.rs` 7 |
| `#[ignore]` attributes | 18 | Many supervisor/model tests need models or GPUs |
| **Windows insertion tests** | **0** | `paste_tx/windows.rs` 0, `input.rs` 0. `clipboard.rs` tests are all Linux-, unix- or platform-neutral (`clipboard.rs:944-1053`). Only the platform-neutral `paste_tx::evaluate` (7 tests) covers receipt logic. |
| Frontend unit tests | 3 files: `src/lib/utils/keyboard.test.ts`, `src/components/update-checker/portableInstaller.test.ts`, `src/components/settings/history/clipboard.test.ts` | Only `test:keyboard` is wired into CI (`code-quality.yml:59`) |
| E2E | `tests/app.spec.ts` (Playwright, Chromium, web build) | `playwright.yml` on PRs |

**Baseline status: NOT_RUN.** The prior figure (141 tests in 12 captured files) covered a partial capture. 368 is the whole-tree definition count at `73cc857`.

### 2.4 CI workflows (`.github/workflows/`)

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `test.yml` | push to main / PR touching `src-tauri/**` | **`cargo test` on `ubuntu-24.04` only** (installs webkit, gtk, vulkan) |
| `code-quality.yml` | push / PR | translations, model-language coverage, catalog sync, `test:keyboard`, eslint, prettier, cargo fmt |
| `playwright.yml` | PR / dispatch | Playwright Chromium E2E |
| `nix-check.yml` | push / PR | `nix build .#handy` |
| `build.yml` (reusable) | called by main-build, pr-test-build, release, build-test | Multi-platform Tauri builds; Windows signing via `trusted-signing-cli` (Azure); macOS notarisation; deb package audit |
| `main-build.yml`, `pr-test-build.yml`, `release.yml`, `build-test.yml` | push / dispatch | Wrappers around `build.yml` |

**Gap for WisprSide:** no Windows Rust test job runs anywhere, and Windows insertion code has no tests. A WisprSide fork must add a `windows-latest` `cargo test` job before any insertion delta is accepted (WS-M9).

### 2.5 Packaging and signing

- **Windows installers:** `bundle.targets = "all"` produces NSIS `-setup.exe` and MSI. The NSIS build uses a **custom template with a Normal vs Portable page** (`src-tauri/nsis/installer.nsi`, 1,085 lines; portable sections marked). `portableInstaller.test.ts` references both `_x64-setup.exe` and `_x64_en-US.msi` assets.
- **Install mode:** not set in `tauri.conf.json`. Tauri's NSIS default is `currentUser`, which needs no admin. DOCUMENTED (https://v2.tauri.app/distribute/windows-installer/).
- **WebView2:** `webviewInstallMode` is not set. Tauri's default is `downloadBootstrapper`: it "Requires an internet connection" when the runtime is missing. DOCUMENTED (same URL). Windows 11 ships WebView2, so this is normally a no-op, but it is **install-time egress** on machines without the runtime.
- **Signing:** `signCommand: trusted-signing-cli -e https://eus.codesigning.azure.net/ -a CJ-Signing -c cjpais-dev -d Handy %1` (`tauri.conf.json:77`). It is upstream-owned and must be replaced.
- **Updater:** minisign `pubkey` and `endpoints: ["https://github.com/cjpais/Handy/releases/latest/download/latest.json"]` (`tauri.conf.json:85-90`); `createUpdaterArtifacts: true` (`:28`). Both are upstream-owned and must be replaced or removed.
- **Webview security:** `"csp": null` (`tauri.conf.json:16`) and `assetProtocol.scope.allow: ["**"]` (`:17-22`). The fs capability is scoped to `$APPDATA/**` (`capabilities/default.json:17-21`). A null CSP plus an unrestricted asset scope is a hardening gap (WS-M2).

### 2.6 Default network egress inventory (critical for "no hidden network transmission")

Method: grep of `src-tauri/src`, `src/`, `index.html` and the manifests for URLs, `reqwest`, `hf_hub`, `fetch(` and updater calls, then reading every hit (SOURCE_VERIFIED). Telemetry search (`posthog|sentry|analytics|telemetry|mixpanel|amplitude|segment.io|plausible|aptabase`) returned **no hits** (REPRODUCED). The frontend loads no remote fonts or images. Release notes are bundled (`components/whats-new/releaseNotes.ts:17` uses a local glob).

| # | Egress path | Default? | Destination | Trigger / gate | Evidence |
| --- | --- | --- | --- | --- | --- |
| E1 | **Update check** | **ON by default** | `https://github.com/cjpais/Handy/releases/latest/download/latest.json`, which redirects to GitHub asset hosting | Fires when the hidden main webview mounts the footer after onboarding. The main window is always built, hidden or not (`lib.rs:1000-1006`). Gated by `update_checks_enabled` (default `true`) and the `HANDY_DISABLE_UPDATER` env var | `settings.rs:604-606`, `settings.rs:1385-1398`, `UpdateChecker.tsx:37-43,64,85`, `Footer.tsx:41`, `App.tsx:353`, `tauri.conf.json:85-90` |
| E2 | Update download/install | User click | Same release assets | `installUpdate` | `UpdateChecker.tsx:122-160` |
| E3 | Transcription model download | User-initiated (onboarding pick starts it; model table) | `huggingface.co` via `hf-hub` (honours `HF_ENDPOINT`), fallback `https://blob.handy.computer/{repo}/{rev}/{file}`; legacy whisper `.bin` URLs on `blob.handy.computer` | `downloadPick.ts:10-31`, `commands/models.rs:42`. SHA-256-verified, pinned revisions | `managers/model.rs:2033,2264`, `catalog/mod.rs:36`, `managers/model.rs:916-1038` |
| E4 | Language-detector download | User-initiated | Same as E3 | `commands/models.rs:77` | `language_detection/mod.rs:185-199` |
| E5 | LLM post-processing | **Off by default** | User-selected provider base URL. Defaults offered: OpenAI, z.ai, OpenRouter, Anthropic, Groq, Cerebras, AWS Bedrock mantle, and "custom" `http://localhost:11434/v1` (Ollama) | `post_process_enabled = false`; also a separate hotkey `transcribe_with_post_process` | `settings.rs:704-706,722-812`, `llm_client.rs:239-251` |
| E6 | LLM model-list fetch | When a provider is selected **and** a key (or a custom base URL) is set | `GET {base_url}/models` | `usePostProcessProviderState.ts:107-114,186` | `llm_client.rs:624-636` |
| E7 | External links | User click | handy.computer docs/donate, GitHub | `openUrl` (system browser) | `AboutSettings.tsx:34,74`, `LinuxGuide.tsx:7`, `SecureInputWarning.tsx:10` |
| E8 | Installer WebView2 bootstrapper | Only if WebView2 is missing | Microsoft | Tauri default | DOCUMENTED (Tauri page above) |
| L1 | Local exec (not network, but an exfiltration path) | Present when the user places a hook file | `<app data>/hooks/transcription` | File existence | `transcription_hook.rs:18-31` |
| L2 | Local exec | Opt-in paste method | User-configured script | `PasteMethod::ExternalScript` | `clipboard.rs:895-901` |

**Verdict:**
- With defaults, a post-onboarding launch performs **one silent network request (E1)**. The UI does show update state, but the user never consented to the request.
- Everything else is user-initiated or opt-in. No telemetry or analytics was found in application source.
- Native crates (transcribe-cpp-sys, handy-recorder, handy-keys, WebView2 itself) were not audited for egress.
- **Offline behaviour is NOT_MEASURED.** Acceptance needs the observed-egress test in WS-M1, as Opus S5 requires.

### 2.7 Fork verdict

**Qualified as fork lead, conditionally.**
- Licence (MIT), stack fit (Rust core, Windows x64/ARM builds in CI), module completeness and an active upstream (37.9k stars; releases every 2–4 weeks) support forking at `73cc857`.
- Conditions:
  - The unmodified suite baseline (WS-M0).
  - Egress lockdown (WS-M1).
  - Removal of exec surfaces and webview hardening (WS-M2).
  - The Windows insertion deltas in §3 (WS-M3..M6).
  - A Windows CI test job (WS-M9).
- Native build, install, runtime, Arabic quality and the effort saved are all **NOT_ESTABLISHED**.

---

## 3. Windows text-insertion safety

### 3.1 How Handy delivers text on Windows today (SOURCE_VERIFIED `Handy@73cc857`)

1. **Activation (`actions.rs:478-640`):**
   - `TranscribeAction::start` kicks off the model load, bumps `RECORDING_SESSION` (`:514`), registers the cancel shortcut (`:634`) and starts capture.
   - **No target window, process or focused-control identity is captured** (grep for `GetForegroundWindow|hwnd|foreground` finds only overlay and clipboard-owner code).
2. **Stop (`:655-662`):**
   - Readiness is invalidated and **the cancel shortcut is unregistered**.
   - Transcription, custom words, fillers, optional LLM and the optional hook (`:831-843`) run under `was_cancelled_since(cancel_generation)` checks.
3. **Paste thread (`:858-930`):**
   - A dedicated thread re-checks cancellation (`:867`), then calls `utils::paste(final_text)` (`:881`).
   - `Ok(())` maps to `TranscriptionOutcome::Typed` (`:885-901`); `Err` maps to `Failed` + `NoticeCode::PasteFailed` (`:902-913`).
4. **`clipboard::paste` (`clipboard.rs:822-921`):**
   - Takes `PASTE_LOCK` and optionally appends a trailing space.
   - **Default method Ctrl+V → legacy `paste_via_clipboard`**, unless the debug setting `reliable_paste` is on, in which case it uses `paste_tx` and falls back to legacy only if the transaction could not *start* (`:860-893`).
   - After the paste, `auto_submit` (default off) presses Enter on the legacy path **without any receipt** (`:905-913`).
5. **Legacy `paste_via_clipboard` (`:74-138`):**
   - Saves clipboard **text, or an image only if there was no text** (`:81-90`). HTML, RTF and file lists are not saved.
   - Writes the transcript through tauri-plugin-clipboard-manager. **No history or cloud exclusion markers are set**, so the transcript can enter Windows clipboard history and Cloud Clipboard; the absence of markers is SOURCE_VERIFIED, the history behaviour itself is NOT_RUN.
   - Sleeps `paste_delay_ms` (60), sends Ctrl+V via enigo `SendInput` into **whatever window is foreground**, sleeps `paste_delay_after_ms` (60), then **restores unconditionally** (`:123-137`). There is no check that the clipboard is still Handy's, so a copy the user makes in that window is overwritten.
6. **Receipt path `paste_tx/windows.rs` (opt-in):**
   - Snapshots all global-memory formats up to 64 MiB, plus CF_BITMAP (`:298-352`).
   - Publishes a delayed-render CF_UNICODETEXT plus the three Microsoft exclusion formats (`:370-411`).
   - Restores only if `GetClipboardSequenceNumber()` is unchanged and ownership was not lost (`:463-469`).
   - Auto-submits only after a post-injection receipt (`:457-461`).
   - Timing: 200 ms quiet period, 8 s timeout, 500 ms on failed injection (`paste_tx/mod.rs:53-63`).
   - `try_reliable_paste` returns `Ok` once publishing and the chord are done (`mod.rs:188-213`), so the caller reports `Typed` **before any receipt exists**.
7. **Direct method (`input.rs:268-274`):** `enigo.text(text)` reports one error or success for the whole string. There is no count of characters sent and no partial outcome.

**Consequences:**
- The paste lands in whatever has focus when the paste thread runs. That is seconds after release for slow models or LLM post-processing.
- A focus change during transcription (a notification, an app stealing focus, the user clicking elsewhere) silently redirects the transcript.
- Password fields, elevated (higher-integrity) windows and the secure desktop are not detected on Windows.
- Microsoft documents that SendInput "fails when it is blocked by UIPI", and that neither GetLastError "nor the return value will indicate the failure was caused by UIPI blocking". Applications may inject only into targets "at an equal or lesser integrity level". DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput).
- So Handy reports `Typed` for a paste into an elevated window that never received it. (Inference from the documented API plus the code path; NOT_RUN.)

### 3.2 Comparison with narrow donors

| Concern | Handy `73cc857` | OpenWhispr `cb08c41` | VoiceInk `4bc74ca` (macOS) | FreeFlow `3778646` (macOS) |
| --- | --- | --- | --- | --- |
| Target captured at activation | No | HWND via `windows-fast-paste --detect-only` (`TARGET %p`, class, exe, title; `windows-fast-paste.c:313-327`) | Active window/app snapshot (`ActiveWindowService.swift`) | AX focused element, window, PID, value, selection (`AppTextInsertionTarget.swift:22-42`) |
| Verified before paste | No | Tries `RestoreForegroundWindow`; **on failure falls through to current foreground** (`windows-fast-paste.c:281-291`). JS predicate treats an unreadable exe as foreign (`windowsPasteTarget.js:25-28`). Fast-paste failure or timeout **falls back to nircmd/PowerShell** paste (`clipboard.js:1477-1498`) | Focus diagnostics only (`PasteFocusDiagnostics.swift`); typer goes to the current recipient | **Yes.** `pasteIfTargetMatches` checks focus, value equality (UTF-16) and selection, before **and** after clipboard preparation (`AppTextInsertionCore.swift:106-137`) |
| Fail-closed refusal | No | **No** (fall-through by design, "pre-#859 behavior") | Partial (does not post when AX trust is missing) | **Yes** (returns `false` / `.unavailable` / `.notInserted`) |
| Password / secure field | No (macOS-only hotkey module) | **UIA probe**: `IsPassword` (defaults TRUE if unread), enabled, keyboard-focusable, `ValuePattern.IsReadOnly`, no live selection, Edit/Document control type → `EDITABLE`/`NOT_EDITABLE` (`windows-text-monitor.c:226-293`, `--probe-editable`) | AX checks in typer | Excludes `AXSecureTextField` at capture and focus time (`AppTextInsertionTarget.swift:24-26,55-56`; `Core:30`) |
| Elevated / UIPI | No | No (only an NSIS netsh comment) | n/a | n/a |
| Clipboard restore only if unchanged | Legacy: **no**. Receipt path: **yes** (sequence number) | Yes, by text compare or session tag after a fixed delay (`clipboard.js:921-958`); saves text/HTML/RTF/image (`:859-904`) | Yes, expected text + per-session marker (`CursorPaster.swift:231-235`) | n/a (writes through AX first) |
| Clipboard history exclusion | Receipt path only (`paste_tx/windows.rs:373-377`) | Not inspected | macOS concealment markers (prior study) | n/a |
| Partial-delivery reporting | No | `pasted` boolean (prior study) | `commandPosted/NotPosted/PartiallyPosted`; partial never retried | `inserted / notInserted / unverified / unavailable`; only `notInserted` permits fallback |
| Licence | MIT | MIT | GPLv3 (founder grant recorded privately) | MIT |

**REJECTED for WisprSide:**
- OpenWhispr's fall-through at `windows-fast-paste.c:281-291`.
- OpenWhispr's nircmd/PowerShell fallback paste.
- OpenWhispr's "unknown exe is foreign" predicate.
- Any `SetForegroundWindow` / `AttachThreadInput` focus stealing at paste time (`windows-fast-paste.c:182-213`). Restoring focus moves the user's context and does not prove the right field.

### 3.3 Smallest delta to add (specification)

Everything below lives in Handy's existing seams.
- **New Windows module:** `src-tauri/src/paste_tx/target_windows.rs`.
- **New platform-neutral pure module:** `src-tauri/src/paste_tx/target.rs`.
- **Call-site edits:** `actions.rs` (start and paste thread), `clipboard.rs` (`paste`), `settings.rs` (defaults), `notices.rs`, `managers/history.rs` (outcome column).
- **New `windows` crate features:** `Win32_UI_Accessibility` (UIA), `Win32_Security` (token integrity) and `Win32_System_ProcessStatus` if needed; the existing ones stay.

#### D-A Target identity binding (at activation)

In `TranscribeAction::start` (`actions.rs:478`, beside `RECORDING_SESSION.fetch_add` at `:514`), capture a `TargetBinding` and store it with the session generation:

| Field | Source API | Purpose |
| --- | --- | --- |
| `hwnd_top` | `GetForegroundWindow()` | Top-level target |
| `pid`, `tid` | `GetWindowThreadProcessId` | Owner |
| `process_start` | `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)` + `GetProcessTimes` creation FILETIME | Defeats PID and HWND reuse |
| `exe_path` | `QueryFullProcessImageNameW` (idea ADAPTed from OpenWhispr `GetExeName`, `windows-fast-paste.c:64-85`) | Profiles and display. **Unreadable means unknown, never "foreign-ok"** |
| `hwnd_focus` | `GetGUIThreadInfo(tid).hwndFocus` | Focused child control |
| `uia_runtime_id`, `control_type`, `is_password`, `is_enabled`, `is_keyboard_focusable`, `is_read_only` | `IUIAutomation::GetFocusedElement` + properties `UIA_RuntimeIdPropertyId`, `UIA_ControlTypePropertyId`, `UIA_IsPasswordPropertyId` (30019), ValuePattern `IsReadOnly` | Editable-field predicate, ported from OpenWhispr `--probe-editable` (`windows-text-monitor.c:226-293`), with **`is_password` defaulting to true when unreadable** as upstream does |
| `target_integrity`, `self_integrity` | `OpenProcessToken` + `GetTokenInformation(TokenIntegrityLevel)` | UIPI pre-check |
| `captured_at` | monotonic clock | Expiry |
| `session_generation` | existing `RECORDING_SESSION` / cancel generation | Late-result rejection |

Microsoft documents that `UIA_RuntimeIdPropertyId` "Identifiers can be reused over time", and that `IsPassword` marks "protected content or a password". DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-automation-element-propids). Hence RuntimeId is combined with HWND, PID and process start time; it is never used alone.

**Privacy rule:**
- The binding stores **no field text**. OpenWhispr's monitor prints the full field value (`INITIAL_VALUE`, `windows-text-monitor.c:262-268`); WisprSide does not.
- An optional value digest exists only for the later selected-text feature (RC), and needs explicit consent.

#### D-B Fail-closed verification (before any clipboard mutation, and again right before `SendInput`)

Add a pure function `verdict(captured: &TargetBinding, now: &TargetBinding, policy) -> Verdict`, with unit tests on any OS using fake snapshots. Following FreeFlow's double-check (`AppTextInsertionCore.swift:117-135`):

1. **Check #1** at the top of `clipboard::paste` (Windows), before `write_text_to_clipboard` or snapshotting.
2. **Check #2** after the clipboard is published and immediately before the chord or `SendInput`.
3. Mismatch on any field among {hwnd_top, pid, process_start, hwnd_focus, uia_runtime_id}, a NULL foreground (secure desktop or lock), or an expired binding gives `Refused(TargetChanged|TargetGone|Expired|SecureDesktop)`.
4. On refusal:
   - **Inject nothing.** Do not call `SetForegroundWindow`.
   - If check #2 fails after publishing, cancel the transaction so the receipt path restores the snapshot (`ownership_lost`/`cancelled` handling exists).
   - Keep the transcript in history and raise a notice whose action copies it **on explicit user click**.
5. Expiry is a policy constant to be chosen by the founder. No value is asserted here.

#### D-C Secure, password and elevated refusal

| Condition | Detection | Outcome |
| --- | --- | --- |
| Password field | `is_password == true`; classic Edit `GetWindowLongPtrW(hwnd_focus, GWL_STYLE) & ES_PASSWORD` | `Refused(PasswordField)` |
| Not editable or read-only | the editable predicate fails | `Refused(NotEditable)`. Optional, policy-gated: some editors expose no UIA patterns, so start as **warn and refuse**, with a per-app allow override recorded in settings |
| Higher-integrity target | `target_integrity > self_integrity` (or the token is unreadable) | `Refused(ElevatedTarget)` with guidance. Never auto-elevate. Wispr Flow's documented answer is to run Flow as administrator (DOCUMENTED, https://docs.wisprflow.ai/articles/7971211038-fix-text-not-pasting-after-dictation); WisprSide should refuse and explain instead |
| Secure desktop / lock / UAC | `GetForegroundWindow()` NULL, or `OpenInputDesktop` is not the user's desktop | `Refused(SecureDesktop)` |

#### D-D Clipboard: restore only if unchanged

1. Make the receipt transaction the **default** on Windows for WisprSide (`reliable_paste: true` at `settings.rs:1055`). It already snapshots full format fidelity, restores only on an unchanged sequence number, and sets the exclusion formats.
2. Delete the legacy fallback *after* a refused or failed transaction start on Windows. Fall back to `CopiedOnly`/manual instead of `paste_via_clipboard`. Where legacy remains (non-Windows), record `GetClipboardSequenceNumber()`/`changeCount` after writing, and restore only if it is unchanged.
3. Keep the three Microsoft formats on every transcript write. Their semantics are DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/dataxchg/clipboard-formats): `ExcludeClipboardContentFromMonitorProcessing` prevents history and sync; `CanIncludeInClipboardHistory` = 0; `CanUploadToCloudClipboard` = 0.
4. Document the residual risk: third-party clipboard readers can still read the delayed-render data. A receipt is not proof of insertion.

#### D-E Delivery outcome and partial-delivery reporting

Replace `Result<(), String>` from `clipboard::paste` with:

```rust
enum DeliveryOutcome {
    Refused(RefusalReason),        // nothing injected; transcript retained
    NotPosted(String),             // injection API failed before any event
    Posted,                        // chord/text events accepted by SendInput; no receipt
    PostedAndRead,                 // WM_RENDERFORMAT receipt observed after injection (paste_tx)
    PartiallyPosted { sent_utf16: usize, total_utf16: usize }, // direct typing stopped mid-way
    CopiedOnly,                    // user-initiated copy, no injection
    Unknown,                       // e.g. transaction timed out without receipt
}
```

- **Names** follow VoiceInk's vocabulary (`CursorPaster.swift:11-14`) and FreeFlow's semantics (`AppTextInsertionCore.swift:3-9`). This is a concept transplant, so no GPL code is copied.
- **Receipt mapping:** `paste_tx` already computes `any_receipt_after_injection()` and `injection_failed` (`paste_tx/windows.rs:436-446`). Send them back to the paste thread over a channel so `TranscriptionOutcome` is emitted **after** settling rather than at chord time.
- **Direct typing:** replace `enigo.text` (`input.rs:268-274`) with WisprSide's own chunked `SendInput(KEYEVENTF_UNICODE)`. Chunks never split surrogate pairs (concept from VoiceInk `DirectTextTyper`), and a count `sent < expected` gives `PartiallyPosted`. **Partial is never retried** (VoiceInk rule).
- **Downstream:** extend `TranscriptionOutcome` and notices; add an `outcome` column to history (migration). Auto-submit is allowed **only** on `PostedAndRead`; remove the legacy auto-submit at `clipboard.rs:905-913`.
- **UI wording:** "Typed" becomes "Sent" for `Posted` and "Delivered" for `PostedAndRead`. Neither claims the editor accepted the text.

---

## 4. Feature capability inventory

Legend: **HAS** = present in `Handy@73cc857` (path given); **PARTIAL**; **MISSING**. "Donor" is the best narrow donor at its current HEAD. All runtime quality is NOT_MEASURED.

| # | WisprSide capability | Handy status (path) | Best narrow donor if gap | Notes |
| --- | --- | --- | --- | --- |
| 1 | Instant activation | **HAS**: global hotkeys via handy-keys (`shortcut/handy_keys.rs`); model load kicked off at press (`actions.rs:488`); optional `always_on_microphone` (default off, `settings.rs:588`) | — | Latency NOT_MEASURED |
| 2 | Push-to-talk | **HAS**: `ShortcutActivation::PushToTalk` (`settings.rs:180-181`) | — | |
| 3 | Toggle | **HAS**: `Toggle` and default `HoldOrToggle` (`settings.rs:177-185`); coordinator parity tests | FreeFlow double-tap-to-lock (`1546427`) for reference only | |
| 4 | Natural punctuation | **PARTIAL**: model output plus the opt-in LLM prompt rule "Replace spoken punctuation with symbols" (`settings.rs:852`); no deterministic spoken-punctuation pass | VoiceInk `SmartPunctuation.swift` (GPL, concept only); OpenWhispr cleanup (MIT) | |
| 5 | Context-aware formatting | **MISSING** (no app or window context) | App identity from D-A `exe_path` (OpenWhispr `GetExeName`, MIT); VoiceInk Modes triggers (`Features/Modes/Models/ModeTriggerModels.swift`, GPL, concept) | **REJECTED:** screenshots or field-text reading by default (FreeFlow default-on fallback; Aqua/Monologue screenshot designs) |
| 6 | Smart correction / backtrack ("no wait, I meant…") | **MISSING** deterministically; **PARTIAL** through a custom LLM prompt | Prompt patterns: VoiceInk `Core/Enhancement/AIPrompts.swift:14` (GPL, wording reference), FreeFlow `PostProcessingService.swift:67` (MIT). Output guard: OpenWhispr `src/utils/cleanupOutput.ts` + `test/utils/cleanupOutput.test.js` (MIT; includes `"Send it Thursday no wait Friday" → "Send it Friday."`) | Raw transcript must stay immutable (history already stores it, `history.rs:23-35`) |
| 7 | Filler removal | **HAS** for en/de/fr plus universal tokens (`audio_toolkit/text.rs:300-330,429`); `custom_filler_words` (`settings.rs:534`) | VoiceInk `FillerWordManager.swift` + capitalisation repair `9b2dd5a` (GPL, concept) | **Arabic fillers: MISSING** (no `ar` gated list, `text.rs:318-326`) |
| 8 | Personal vocabulary / dictionary | **HAS**: `custom_words` used as a model prompt when supported, otherwise fuzzy replacement (`managers/transcription.rs:1252-1271,1681`; `text.rs:151`) | Learned dictionary: VoiceInk AutoLearn (GPL; AX-observes edits, privacy-heavy, REJECTED as default) | **Arabic-script fuzzy matching MISSING**: keys must be ASCII (`text.rs:58-64`) |
| 9 | Technical terminology | **PARTIAL**: custom words only | None qualified | Code identifiers and casing are BUILD_NEW (RC) or done through an LLM prompt |
| 10 | Voice commands for editing | **MISSING** | FreeFlow command mode (`AppState.swift:144,392`, macOS, MIT); Windows Voice Access as the benchmark | RC; requires D-A/D-E |
| 11 | Selected-text rewrite | **MISSING** | OpenWhispr selection edit (Windows selection via `windows-fast-paste --copy`, which mutates the clipboard). Its own qualification doc reports **26/36 exact** for local Qwen 3.5 2B and "model-quality objective is not met" (`OW@cb08c41:docs/validation/local-selection-edit/README.md`; upstream claim, not reproduced) | RC; preview and confirm are mandatory |
| 12 | Snippets | **MISSING** | OpenWhispr `src/components/SnippetsView.tsx`, `openwhispr-mobile/src/lib/snippets.ts` (MIT) | RC |
| 13 | Multilingual | **HAS**: 76-model bundled catalog (`catalog/catalog.json`), `selected_language`, `spoken_languages`, detector | — | 17 catalog models list `ar` (REPRODUCED) |
| 14 | Arabic/English code-switching | **PARTIAL**: one language per utterance (`language_detection/mod.rs:1-3`; detection window default 5 s, `settings.rs:643`). The catalog describes `cohere-transcribe-arabic-07-2026` (ar+en, Apache-2.0 per catalog) as "Best for Arabic and Arabic/English speakers" | — | Catalog FLEURS-ar "error" claims: 11.06 (cohere-arabic), 13.6 (cohere-03), 14.53 (Voxtral-Mini-4B-Realtime), 14.92 (whisper-large-v3). These are **upstream catalog claims** (`catalog.json` `results`), metric undefined, read speech; Gulf dialect and code-switch performance **NOT_MEASURED** |
| 15 | App-aware profiles | **MISSING** | Exe/class matching (OpenWhispr `windows-fast-paste.c:31-53` terminal lists, MIT → COPY the list); VoiceInk Modes (concept) | RC |
| 16 | Local / offline | **HAS** for transcription (transcribe-cpp local); **default egress E1** (§2.6) | — | Offline NOT_MEASURED |
| 17 | Transparent model selection | **HAS**: bundled catalog with pinned revisions, per-quant SHA-256 and benchmark fields (`catalog/mod.rs:1-18`); model table UI | — | Show licence and rights per model (WS-M7) |
| 18 | LLM post-processing (local) | **PARTIAL**: opt-in; OpenAI-compatible "custom" provider defaulting to `http://localhost:11434/v1` (Ollama) (`settings.rs:812`); no bundled local LLM | OpenWhispr bundled llama-server + model manager (MIT; heavy, REJECTED for MVP) | Structured output and injection-resistant prompt exist (`settings.rs:852`) |
| 19 | History with privacy controls | **PARTIAL**: raw + post-processed text, audio retention options, limit 5, deletion with error reporting (`0685192`) | — | Missing: text-retention control, per-app exclusion, encryption at rest (DPAPI) |
| 20 | Accessibility | **PARTIAL**: aria attributes, notice live region, reduced motion, recent a11y fixes | — | Overlay cancel label not localised; overlay state not announced; keyboard cancel unregistered during processing |
| 21 | Low resource usage | **PARTIAL**: model unload timeout (`ModelUnloadTimeout`), CPU-only ARM64, Vulkan x64, no Electron | — | RAM/CPU NOT_MEASURED |
| 22 | Cancellation / recovery | **PARTIAL**: cancel generations; tray/overlay cancel through transcription (`tray.rs:696-702`, `RecordingOverlay.tsx:296`); history retains the transcript; `PasteFailed` notice | Handy's own coordinator | Keyboard cancel dropped at stop (`actions.rs:662`); "Model loads are never cancelled" (`engine_supervisor/supervisor.rs:471-475`) |
| 23 | Streaming preview | **HAS** for streaming-capable models: `OverlayStyle::Live` (`settings.rs:626-633`), `StreamTextEvent {committed, tentative}` | — | Catalog streaming models with `ar`: only `Voxtral-Mini-4B-Realtime-2602` (REPRODUCED) |

---

## 5. Competitors, parity matrix and differentiation

*(Filled from official sources; see §5.1–§5.3.)*

<!-- COMPETITORS -->

---

## 6. What must be built new

Each item says: what was inspected, why it is insufficient, the smallest missing capability, whether it fits in an adapter, and the test/maintenance cost. All other WisprSide v1 capability is **FORK_DELTA on Handy** or a narrow **ADAPT**.

| ID | Build-new item | Inspected sources | Why insufficient | Smallest missing capability | Confined to an adapter? | Test / maintenance cost |
| --- | --- | --- | --- | --- | --- | --- |
| BN-1 | **Windows target binding + verdict** (D-A/D-B) | Handy `actions.rs`, `clipboard.rs`, `paste_tx/windows.rs` (no target identity); OpenWhispr `windows-fast-paste.c` (HWND only, fall-through, no PID/start time, no focus control); FreeFlow `AppTextInsertionCore/Target.swift` (correct algorithm, macOS AX only); VoiceInk (macOS) | None has a Windows fail-closed binding of HWND + PID + process start + focused control + UIA element | ~1 pure Rust module (`verdict`) + 1 Windows capture module | **Yes**: `paste_tx/target.rs` (pure) + `paste_tx/target_windows.rs`; two call sites | Pure verdict: platform-neutral unit tests on Linux CI. Capture: Windows CI plus a fixture app. Upstream conflict surface is small (new files + ~20 lines in `actions.rs`/`clipboard.rs`) |
| BN-2 | **Windows password / elevated / secure-desktop refusal** (D-C) | Handy `secure_input.rs` (macOS hotkey resilience only); OpenWhispr `windows-text-monitor.c --probe-editable` (UIA IsPassword/editable; no integrity check); none check UIPI | UIPI blocking is silent per Microsoft docs; no donor checks integrity | Token integrity compare + UIA predicate port + `ES_PASSWORD` | **Yes**, inside BN-1's module | Needs an elevated fixture (GitHub Windows runners are admin) and a password-box fixture |
| BN-3 | **DeliveryOutcome envelope** (D-E) | Handy `Result<(),String>` + `TranscriptionOutcome{Typed,Empty,Silent,Failed}`; VoiceInk/FreeFlow vocabularies (Swift) | Handy conflates Posted with Delivered and has no partial state; donors are other languages and OSes | One enum, receipt channel from `paste_tx`, chunked `SendInput` typer | Mostly (`clipboard.rs`, `input.rs`, `actions.rs`, history migration) | Unit tests for mapping; fixture tests for receipt vs no receipt; history migration needs a rollback plan |
| BN-4 | **Arabic text layer** | Handy `text.rs` (ASCII-only fuzzy keys, no Arabic fillers); VoiceInk/OpenWhispr/FreeFlow (no Arabic normalisation found by grep for tatweel/alef/hamza/tashkeel) | No donor normalises Arabic script for matching | Match-key normaliser (strip tatweel U+0640 and harakat; unify alef forms; ta marbuta/ha; alef maqsura/ya) used **only for matching keys**, never to rewrite output; optional user-editable Arabic filler list (default empty until validated) | **Yes**: `audio_toolkit/text.rs` | Unit fixtures; must prove no change to raw transcript. Linguistic review needed; the default filler list must not delete meaningful words (e.g. "يعني" is often meaningful) |
| BN-5 | **Egress observation harness** | Handy CI (none); prior Opus S5 requirement | No donor proves offline behaviour | CI job: fresh profile, model preinstalled, full PTT on a fixture audio source, OS-level connection log must be empty | Test-only | A Windows runner with pktmon/firewall logging. False positives from the OS itself need an allowlist scoped to the WisprSide process tree |
| BN-6 (RC) | **Non-destructive selection capture on Windows** | OpenWhispr uses synthetic Ctrl+C (`windows-fast-paste.c` `SendCopy*`), which mutates the clipboard; VoiceInk/FreeFlow are AX | No donor reads the selection on Windows without touching the clipboard | UIA `TextPattern.GetSelection()` read + digest bound into TargetBinding | **Yes** | Many editors lack TextPattern, so refuse when it is absent |

**Not to be built:** another capture engine, ASR runtime, hotkey layer, supervisor, model downloader, settings or history store, installer, or tray. Handy has them all.

---

## 7. Work packets (MVP and RC)

Common rules:
- Fork base `Handy@73cc857`, with an immutable upstream-tracking branch and a `DELTA_REGISTER.md` row per packet (finding, files, fixture, upstream status).
- Implementation authority remains closed until governance opens the grain.
- Licence notices are preserved (MIT for Handy, OpenWhispr and FreeFlow). VoiceInk (GPLv3) contributes **vocabulary and concepts only**, unless the founder's private grant is invoked explicitly per file.
- Estimates are intentionally omitted (not measured).

### 7.1 MVP packets (Windows x64, local-only, safe delivery)

| ID | Depends on | Donor + SHA + path | Decision | Files affected | Acceptance criteria | Tests | Security risks | Rollback |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **WS-M0** Fork baseline | Governance opens grain | Handy `73cc8579…` whole tree | **FORK** | none (baseline) | Exact pin materialised; notices and locks preserved; unmodified `cargo test --locked` on Windows **and** Linux, `bun run lint`, `test:keyboard`, Playwright run, with collected/pass/fail/ignored counts recorded; unsigned NSIS + MSI built on Windows; bundled DLL list recorded | Donor suites as-is; failures recorded, not fixed | Native toolchain supply chain (Vulkan SDK, LLVM, ggml); git-sourced crates (4) | Delete fork branch |
| **WS-M1** Egress lockdown | M0 | Handy `settings.rs:604-606`, `lib.rs:932`, `capabilities/*.json`, `UpdateChecker.tsx`, `tauri.conf.json:85-90` | **FORK_DELTA** | same | Fresh install + onboarding + PTT session with model preinstalled shows **zero outbound connections** from the WisprSide process tree (BN-5); update check default **off**, behind an explicit "Check for updates" action that discloses the destination; remote LLM providers hidden unless a "Cloud services" switch is on; model download UI shows the host before download | BN-5 harness; unit test on default settings JSON (`settings.rs:1455+` pattern) | Users miss security updates (mitigate with signed release notes and an opt-in prompt) | Flip defaults back |
| **WS-M2** Exec surface removal + webview hardening | M0 | Handy `transcription_hook.rs`, `actions.rs:831-843`, `clipboard.rs:895-901`, `tauri.conf.json:16-22`; also gate `audio_toolkit/audio/decode.rs` file transcription | **FORK_DELTA** | same + `settings.rs` (`PasteMethod::ExternalScript` hidden on WisprSide) | Hook file present → never executed (test); ExternalScript unreachable from UI and settings import; CSP non-null with app UI working; asset scope narrowed to the recordings dir; file-decode either disabled or behind explicit import with format allowlist | Unit + Playwright; malformed-media fuzz corpus if decode is kept | CSP breakage; media parser CVEs if kept | Revert commit |
| **WS-M3** Target binding capture (D-A) | M0, M9 | Concepts: OpenWhispr `OW@cb08c41:resources/windows-fast-paste.c:64-85` (`GetExeName`), `resources/windows-text-monitor.c:226-293` (editable predicate); FreeFlow `FF@3778646:Sources/AppTextInsertionTarget.swift:22-57` (shape) | **BUILD_NEW (BN-1) + ADAPT** | new `paste_tx/target.rs`, `paste_tx/target_windows.rs`; `actions.rs:478-520`; `Cargo.toml` windows features | Binding captured within the start path for every session; contains no field text; unreadable fields recorded as unknown; PID-reuse and HWND-reuse fixtures distinguish targets via process start time | Pure snapshot tests; Windows fixture (two edit windows, kill/relaunch same exe) | UIA calls can block on hung targets, so time-bound them and treat timeout as unknown | Feature flag off → current behaviour (insertion disabled, copy-only) |
| **WS-M4** Fail-closed verification + refusal (D-B, D-C) | M3 | FreeFlow `AppTextInsertionCore.swift:106-137` algorithm (MIT) | **BUILD_NEW (BN-1/BN-2) + ADAPT** | `clipboard.rs:822-893`, `paste_tx/windows.rs` (cancel on check #2), `notices.rs` | 0 injections when target changed, gone, expired, password, read-only, elevated or secure desktop across the fixture matrix; no `SetForegroundWindow` calls (static grep test); transcript retrievable from history and notice "Copy" in 100% of refusals | Pure verdict table tests (all branches); Windows integration: focus switch mid-transcription, password box, elevated Notepad, lock-screen simulation (`LockWorkStation` on runner may be unavailable; record BLOCKED if so) | False refusals in apps without UIA, so per-app override with an audit entry | Policy switch "warn only" (still never redirect) |
| **WS-M5** Clipboard transaction default (D-D) | M4 | Handy `paste_tx/windows.rs` (own code), `settings.rs:1055` | **FORK_DELTA** | `settings.rs`, `clipboard.rs:74-138,860-893` | External copy during pending restore preserved; text+HTML+image snapshot restored byte-equal; transcript write carries the three exclusion formats; no legacy fallback after a failed transaction start on Windows | Windows test with an independent clipboard reader process; sequence-number race test; 8 s timeout path | Delayed-render data still readable by clipboard monitors (documented limitation) | Re-enable legacy path behind a flag |
| **WS-M6** DeliveryOutcome + partial reporting (D-E) | M4, M5 | Vocabulary: VoiceInk `VI@4bc74ca:.../CursorPaster.swift:11-14`; FreeFlow `AppTextInsertionCore.swift:3-9`; Handy `paste_tx/windows.rs:436-446` | **BUILD_NEW (BN-3)** | `clipboard.rs`, `input.rs:268-274`, `actions.rs:858-930`, `notices.rs`, `managers/history.rs` (migration), `src/components/notices/*` | Fixture matrix yields correct outcome 100%: app reads paste → `PostedAndRead`; app ignores → `Unknown` after timeout; injection error → `NotPosted`; typed text stopped mid-way → `PartiallyPosted{sent,total}` with no retry; auto-submit only on `PostedAndRead` | Unit mapping tests; Windows fixtures; history migration up/down test | Migration rollback on downgrade | Down-migration + flag |
| **WS-M7** Arabic baseline | M0 | Handy `audio_toolkit/text.rs`; catalog entries | **BUILD_NEW (BN-4) + FORK_DELTA** | `text.rs`, onboarding model suggestions, model table (licence column) | Arabic custom words match across alef/hamza/tatweel/harakat variants; raw transcript byte-identical in history; RTL text inserted with bidi controls preserved; Arabic model suggested when OS/UI language is `ar`, **after** model rights review; no Arabic quality claim until measured | Unit fixtures; consented held-out Gulf + code-switch set **before** any accuracy claim (NOT_MEASURED today) | Over-normalisation changing meaning (keys only, never output) | Disable normaliser |
| **WS-M8** Cancellation completeness | M0 | Handy `actions.rs:634,662`, `shortcut/mod.rs:73-89`, `engine_supervisor/supervisor.rs:471-485` | **FORK_DELTA** | same | Keyboard cancel works through transcription, post-processing and paste wait; late result after cancel never injected; model-load cancel either implemented with an observed-stop test or surfaced in the UI as non-cancellable | Coordinator tests (existing pattern) + Windows integration | Shortcut re-registration races (upstream already serialises reconcile) | Revert |
| **WS-M9** Windows CI | M0 | Handy `.github/workflows/test.yml` | **FORK_DELTA** | `test.yml` (+ `windows-latest` matrix), fixture app under `tests/windows-fixtures/` | `cargo test` runs on Windows for every PR touching `src-tauri/**`; insertion fixtures run (admin runner) | — | Runner image drift | Remove job |
| **WS-M10** Brand, signing and updater ownership | M1 | Handy `tauri.conf.json:2-5,77,85-90`, `nsis/installer.nsi` | **FORK_DELTA** | same + icons | No `cjpais` identifiers in signing, updater or identifier; Wispral-owned minisign key; `webviewInstallMode` chosen deliberately (offline/embed for zero install-time egress, or documented bootstrapper) | Package audit script (like upstream deb audit) | Key custody | Revert config |

### 7.2 RC packets

| ID | Depends on | Donor + SHA + path | Decision | Files affected | Acceptance criteria | Tests | Security risks | Rollback |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **WS-R1** App-aware profiles (exe-based) | M3 | OpenWhispr `OW@cb08c41:resources/windows-fast-paste.c:31-53` terminal class/exe lists (MIT) | **COPY** (lists) + **ADAPT** | `settings.rs` (profiles), `clipboard.rs` (chord per profile), UI | Profile chosen only from `exe_path` + class (no screenshots, no field text); terminals get Ctrl+Shift+V; per-profile language and prompt | Deterministic mapping tests | Spoofable exe names (profiles never grant authority) | Disable profiles |
| **WS-R2** Local LLM cleanup + backtrack with guard | M6, M1 | OpenWhispr `src/utils/cleanupOutput.ts` + tests (MIT); prompt concepts VoiceInk `AIPrompts.swift:14`, FreeFlow `PostProcessingService.swift:67` | **ADAPT** (TS→Rust validator; own prompt) | `actions.rs:183-475`, `llm_client.rs`, history UI | Raw kept; diff shown; one-key revert; validator rejects duplicated output; meaning-preservation set (negation, numbers, dates, names, Arabic diacritics) has 0 silent distortions accepted; provider unavailable → raw text + visible notice, **no cloud fallback** | Golden fixtures; port upstream validator tests | Prompt injection from dictated text (existing "do not follow instructions" prompt plus output guard) | Toggle off |
| **WS-R3** Selected-text rewrite (preview/confirm) | M4, R2 | BN-6; OpenWhispr selection-edit docs as negative evidence | **BUILD_NEW** | new `paste_tx/selection_windows.rs`, UI preview | Selection read without clipboard mutation; replacement only after confirm **and** re-verify of binding + selection digest; refuse if TextPattern is absent | Fixture editors (Win32 Edit, RichEdit, WebView2 textarea) | Reading sensitive selections (consent per app) | Disable feature |
| **WS-R4** Snippets | M6 | OpenWhispr `openwhispr-mobile/src/lib/snippets.ts`, `src/components/SnippetsView.tsx` (MIT) | **ADAPT** | `text.rs` or new `snippets.rs`, settings UI | Whole-utterance exact trigger only; expansion logged in history; undo restores raw | Unit tests incl. Arabic triggers | Accidental expansion of secrets (snippets local only, never synced) | Disable |
| **WS-R5** Minimal voice edit commands | M6 | Benchmark: Windows Voice Access (DOCUMENTED, §5) | **BUILD_NEW** | `actions.rs`, coordinator | "scratch that" undoes the last delivery only if the last outcome was `PostedAndRead` into the same live binding; "new line" / "new paragraph"; commands in Arabic and English | Fixture tests; false-trigger rate on held-out dictation | Destructive undo in the wrong window (bound to binding) | Disable |
| **WS-R6** History privacy | M0 | Handy `managers/history.rs`, `settings.rs:221-229` | **FORK_DELTA** | same + UI | "Don't keep text", per-app exclusion, text retention period, DPAPI-encrypted DB (decision) | Migration tests | Key loss means history loss (document) | Down-migration |
| **WS-R7** Accessibility pass | M0 | Handy `src/overlay/RecordingOverlay.tsx:296-299`, `NoticePanel.tsx:155` | **FORK_DELTA** | overlay, notices, i18n | Narrator announces recording, transcribing, delivered and refused; all controls localised (incl. Arabic RTL); full keyboard operation | Manual Narrator script + UIA event capture | — | Revert |
| **WS-R8** Streaming preview hardening | M6 | Handy `managers/transcription/policy.rs`, `StreamTextEvent` | **FORK_DELTA** | overlay | Tentative text visually distinct; only final text inserted; preview never written to the target | Unit + overlay snapshot | — | `OverlayStyle::Minimal` |
| **WS-R9** Arabic/Gulf/code-switch measurement | M7 | consented fixtures (none yet) | **MEASURE** | eval scripts | WER/CER per model with disclosed denominators; false language-switch rate; latency p50/p95 on reference hardware | — | Consent and retention of voice data | n/a |

---

<!-- SECTION8 -->
