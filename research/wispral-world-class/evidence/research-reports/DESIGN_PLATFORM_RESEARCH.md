# Wispral master plan: design direction and desktop-platform research

Prepared 2026-11-08 for the Wispral master-plan mission (umbrella voice-intelligence platform: **WisprSide** dictation companion, Tauri/Rust + React, Windows first; **WisprStudio** voice production studio, Electron + Python; **Klaint** operations console for customer-facing AI voice/chat agents; Arabic RTL and English are both first-class). Read-only research: no sign-ins, no purchases, no downloads of third-party software. English output.

## How to read this report

- Tags: `DOCUMENTED (url)` means the claim is stated on that page, which was fetched or read through search results on 2026-11-08. `NOT_VERIFIED` means no primary source confirmed it (forum reports, vendor material, inference). `PROPOSAL` is my recommendation, not a fact. `COMPUTED` is a number I calculated with a script (the contrast ratios in 4.4).
- In sections 8 and 9 the tags were originally written as `DOCUMENTED(Sn)`; every `Sn` has been expanded inline to its URL, and the full list is in Appendix A.
- Sources are Microsoft Learn, Apple Developer and Support, W3C, MDN, Tauri, Electron, electron-builder, Flatpak/freedesktop, Wayland protocol registry, and the products' own docs. Where only a search-result summary was read, the item says so.
- Source hygiene: one fetched page (Linear docs) contained text addressed to AI agents asking to connect to an MCP server; it was treated as data and ignored. Apple HIG and Material 2/3 pages are JavaScript-rendered and return titles only to a plain fetch; Apple text was recovered from Apple's own JSON endpoint, and Material 2/3 statements are NOT_VERIFIED. The Windows 7-era Win32 tray and notification guides are marked "not updated" by Microsoft; they are used as principles only.
- Time-sensitive: prices, country lists, Insider features and release versions can change. Re-check before committing money or architecture.

## Executive summary

### Ten findings most likely to change the plan

1. **Windows signing depends on where the publishing entity is.** Azure Artifact Signing (formerly Trusted Signing) is Microsoft's recommended non-Store route at about USD 9.99/month (Basic) but only for organizations in 12 listed regions and individuals in the US or Canada; it never issues EV. Outside those regions the fallback is an OV certificate (USD 150-300/year, hardware key) or the Store. DOCUMENTED (https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart, https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options). Section 6.1.
2. **EV no longer buys SmartScreen trust; nothing does instantly.** Reputation builds per file hash and publisher over "several weeks and hundreds of clean installs"; unsigned installers show "Windows protected your PC" and are blocked outright by Smart App Control on Windows 11. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation). Section 6.2.
3. **Tauri cannot produce MSIX.** It makes NSIS and MSI only; a Store listing is a link to your own signed offline installer. Electron's MSIX targets exist but are beta/experimental. DOCUMENTED (https://v2.tauri.app/distribute/microsoft-store/, https://www.electron.build/docs/msix/). Section 6.3.
4. **Microsoft Store developer accounts are free for new sign-ups, but a commercial product belongs on a Company account.** DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/publish/partner-center/open-a-developer-account). Section 6.4.
5. **Install scope and the elevated-window strategy are coupled.** `uiAccess` (the only way to type into administrator windows) needs a trusted-root signature plus a Program Files install, while Tauri's default per-user install lives under `%LOCALAPPDATA%`. DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-securityoverview). Sections 7.4 and 6.3.
6. **Windows text insertion has no single best method.** `SendInput` Unicode, clipboard paste (with the history-exclusion formats), UI Automation (a sensor, not a writer) and a TSF text service each fail differently; UIPI makes injection fail silently for elevated targets. DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput). Section 7.3.
7. **Windows 11 is moving to per-app microphone prompts for desktop apps (Insider only today),** and apps without a verifiable signature show as "Unsigned" there. DOCUMENTED (https://learn.microsoft.com/en-us/windows-insider/release-notes/beta/preview-build-26220-9836). Sections 7.1 and 2.1.
8. **macOS means Developer ID, not the Mac App Store, for a dictation app:** the $99/year program is not waivable for a commercial product, and Accessibility APIs are unavailable in the sandbox; Input Monitoring covers listen-only key taps, Post-Event covers synthetic paste. DOCUMENTED (https://developer.apple.com/support/fee-waiver/, https://developer.apple.com/forums/thread/749494). Section 8.
9. **Linux is fragmented.** Wayland global shortcuts work through the GlobalShortcuts portal on GNOME and KDE, not on COSMIC; Tauri's global-shortcut plugin is still X11-only; text injection differs per compositor. DOCUMENTED (https://github.com/tauri-apps/tauri/issues/3578, https://github.com/pop-os/xdg-desktop-portal-cosmic/issues/4). Sections 8.4 and 8.5.
10. **Updates: signatures are mandatory in Tauri, rollout is DIY, and an update must never interrupt a live dictation.** DOCUMENTED (https://v2.tauri.app/plugin/updater/); the never-interrupt rule and state machine are PROPOSAL (section 9).

### Flags on the already-adopted design direction (full table in section 4.13)

The main session adopted the "Quiet Signal" system (IBM Plex Sans + Plex Sans Arabic, Plex Mono, Lucide, paper/graphite tokens). No license blocker was found, but:
- **Reserved Font Name "Plex":** all Plex OFL files declare it; subsetting or re-encoding the fonts makes a Modified Version that must be renamed, so ship upstream files unmodified or rename the build. DOCUMENTED (https://openfontlicense.org/ofl-faq/).
- **Contrast "PASS 44/44" is true for the declared pairs but incomplete:** light tertiary text on `bg.sunken` is 4.49:1, light `accent.wisp` text on `bg.sunken` is 4.25:1, dark `border.strong` on `bg.sunken` is 2.97:1. COMPUTED.
- **"Designed together as one superfamily" is not supported by any source read;** Arabic tashkeel and Arabic-Indic digit coverage of Plex Sans Arabic, and Arabic coverage of Plex Mono, are NOT_VERIFIED. Plex Sans (Latin) has no Arabic subset, Segoe UI Variable has none locally, so the fallback chain must name "Segoe UI" explicitly.
- **Lucide is ISC (plus MIT for Feather-derived icons) but has no official RTL mirror metadata;** the mirror list must be authored in-house.

### Decisions the master plan must make

| # | Decision | Recommendation (PROPOSAL) | Why |
|---|---|---|---|
| D1 | Legal entity country, which sets the Windows signing route | Pick the entity first; if it is outside the Artifact Signing list, budget an OV certificate and ship on the Store as a second channel | 6.1, 6.2 |
| D2 | Windows install scope | Per-user NSIS for WisprSide MVP; revisit per-machine only if an "Accessibility mode" (`uiAccess`) build is wanted | 6.3, 7.4 |
| D3 | Dictation hotkey model | `RegisterHotKey` toggle by default; opt-in hold-to-talk via a narrowly scoped low-level hook; never default to Win-key chords (Win+H is voice typing) | 7.2 |
| D4 | Insertion policy | `SendInput` Unicode for short text, clipboard paste with history-exclusion formats for long text, read-back where UIA allows, "Not inserted" recovery chip always | 7.3 |
| D5 | macOS distribution | Developer ID + hardened runtime + notarization, non-sandboxed | 8.1-8.3 |
| D6 | Linux scope | Tier 1: X11 and GNOME/KDE portals; Tier 2: wlroots-family via virtual keyboard; mark COSMIC unsupported for global shortcuts | 8.4, 8.5 |
| D7 | Update architecture | Self-hosted static feeds, decile-ring staged rollout for Tauri, `stagingPercentage` for Electron, crash-loop watchdog, no third-party update service | 9 |
| D8 | Color of "listening" | Product accent plus shape and text, not red; test against a red variant | 4.4, 5.6 |
| D9 | Digits and direction | Digits "Auto" from the full locale with override; waveform, transport and timeline stay LTR in RTL UI | 3.1, 3.2 |
| D10 | Store channel | Company developer account; MSIX only after the build pipeline exists | 6.4 |

### Where sources disagree (resolved or flagged)

- Artifact Signing geography differs between the quickstart (12 organization regions, updated 2026-10-08) and the Windows "Code signing options" page (shorter list, 2026-08-29): quickstart treated as authoritative. A Microsoft Q&A answer claims individual onboarding is paused; it is AI-generated and contradicts itself: NOT_VERIFIED.
- Electron's code-signing page (as fetched) says EV is required and OV "no longer helps", and that Artifact Signing removes SmartScreen warnings; Microsoft Learn says the opposite on EV and that reputation still builds over time. Microsoft treated as authoritative.
- The Artifact Signing pricing-details page rendered "$-" for all prices; USD 9.99 and 99.99 come from the product page. Verify in the Azure calculator.
- Apple/Windows disagree on disabling vs removing inapplicable menu items (see 1.6 and 1.7); Wispral applies "disable, do not hide" in main windows and "remove, do not disable" in tray menus and tests both.
- Reference-product churn: Arc sunsets on 2026-12-22 (successor Dia) and ElevenLabs Voiceover Studio sunset on 2026-05-15 with Dubbing Studio in maintenance mode, so treat them as lessons, not live benchmarks (section 1).

### Biggest NOT_VERIFIED items to close with empirical tests before build

`RegisterEventHotKey` needing no TCC prompt on macOS 15/26; whether an LL hook sees keystrokes for elevated windows and its time-out behavior; how ARIA live regions from WebView2/Tauri reach Narrator and NVDA; Mica/forced-colors behavior inside WebView2; surrogate-pair and `VK_PACKET` handling in target apps (terminals, games, Citrix); Arabic tashkeel coverage and line-height in the chosen fonts; Bluetooth headset behavior when capture opens; Tauri updater behavior with pre-2.12 signatures when `requireSignedVersion` is on; Flathub policy on in-app updaters. Full lists are at the end of sections 2, 3 and 9.

### Contents

PART A: 1 Interaction-design principles by reference product; 2 Recording-state and privacy-indicator practice (OS indicators, WCAG 2.2, screen-reader announcements, indicator state machine); 3 Arabic/RTL (mirroring, numerals, mixed-direction text, caret, open-licensed fonts); 4 Wispral design identity (tokens, color, type, motion, icons, sound, components, states, onboarding); 5 Design-review method (capture matrix, heuristics, accessibility tooling, latency budgets, usability protocol).
PART B: 6 Windows signing, installers, Store, winget, updaters; 7 Windows desktop integration (microphone permission, hotkeys, text insertion, UIPI, window identity, tray/materials/high contrast); 8 macOS and Linux; 9 Installer/update UX, rollout and rollback. Appendix A: source index for sections 8-9.

---

# PART A: Design research

## 1. Interaction-design principles by reference product

Research date 2026-11-08. Read-only; official/primary sources only. Paraphrased; no long quotes.
Tags (legacy shorthand from the sub-researcher; URLs were normalized to https:// in this report): DOCUMENTED(url) = stated on that page. NOT_VERIFIED = could not confirm from a primary source. PROPOSAL = my recommendation, not documented.
Surfaces: WS = WisprSide, ST = WisprStudio, KL = Klaint.

Source-hygiene notes
- linear.app/docs/conceptual-model contained text addressed to AI agents (connect to an MCP server); treated as data, not acted on.
- Apple HIG pages are JS-rendered; a plain fetch returned only titles, so text came from Apple's docc JSON endpoint (developer.apple.com/tutorials/data/design/human-interface-guidelines/PAGE.json).
- Status: Arc sunsets 2026-12-22, successor Dia DOCUMENTED(https://arc.net). ElevenLabs Voiceover Studio sunset 2026-05-15; Dubbing Studio in maintenance mode DOCUMENTED(https://elevenlabs.io/docs/eleven-creative/audio-tools/voiceover-studio; https://elevenlabs.io/docs/eleven-creative/products/dubbing/dubbing-studio). Win32 notification-area and notification guides are Windows 7-era and "not updated" DOCUMENTED(https://learn.microsoft.com/en-us/windows/win32/uxguide/winenv-notification); treat as principles only.
- Items marked "(search summary)" rest on search-result summaries, not a fully fetched page.


### 1.1 Linear (speed, keyboard, opinionated defaults, restraint)

L1. Keyboard-first through one context-aware command menu. Cmd/Ctrl+K acts on the current selection, and also covers settings navigation. DOCUMENTED(https://linear.app/docs/select-issues) (search summary). A pointer-disabling "keyboard practice" mode: NOT_VERIFIED (search summary only).
 Apply: WS: every action (start/stop, language, mode, history) reachable from a global hotkey plus one command surface. ST: block/track actions on selection. KL: assign, pause, escalate on selected conversations.

L2. Be opinionated for the job. The Method argues purpose-built software beats unlimited flexibility, which lets each team invent chaotic workflows. DOCUMENTED(https://linear.app/method/introduction).
 Apply: WS ships one dictation flow (hold-to-talk plus hands-free), not a mode zoo. KL ships one triage-to-resolution path for voice agents.

L3. Rule for settings versus defaults: commit to a default for core behavior; offer settings for taste or habit; add cheap toggles for repeated irritants; use settings to teach; let observed user changes guide what becomes a setting. DOCUMENTED(https://linear.app/now/settings-are-not-a-design-failure).
 Apply: Wispral settings policy. Core (insertion semantics, what "listening" means) = no setting. Taste (indicator position, sounds, theme) = setting.

L4. Few inputs, many outputs for theming: base color, accent, contrast instead of dozens of variables; perceptually uniform color; restrained accent; a high-contrast option. DOCUMENTED(https://linear.app/now/how-we-redesigned-the-linear-ui).
 Apply: one token model for all three products (base, accent, contrast) with RTL-neutral layout tokens.

L5. Calmer chrome: matching headers, nav and view controls across areas, dimmer sidebars so content leads, scannability. DOCUMENTED(https://linear.app/changelog/2026-03-12-ui-refresh). An explicit statement about motion restraint was not found (NOT_VERIFIED).
 Apply: KL console dims chrome behind live data. ST is content-first.

### 1.2 Raycast (launcher UX, instant feedback, extensions)

R1. Summon latency comes from preparation. Keep a window rendered but hidden; avoid blank WebView flashes; disable web-view throttling when hidden; let the native host own hotkeys, windows and tray; trade hidden-window memory against cold start with grace periods. Windows host is C#/.NET 8/WPF around system WebView2. DOCUMENTED(https://www.raycast.com/blog/a-technical-deep-dive-into-the-new-raycast).
 Apply: WS indicator and command window are prewarmed; WebView2 hosted in a thin native shell.

R2. Feedback mirrors operation stage. One animated toast morphs to success or failure instead of stacking; fall back to a HUD when the main window is closed; short title, detail in message; attach a few helpful actions. DOCUMENTED(https://developers.raycast.com/api-reference/feedback/toast).
 Apply: WS has one indicator that morphs listening, processing, inserted/failed, with Retry and Copy transcript on failure. KL uses in-place result toasts.

R3. Render first, fill later; no misleading empty states; cached data beats an error. DOCUMENTED(https://developers.raycast.com/information/best-practices; https://developers.raycast.com/basics/prepare-an-extension-for-store).
 Apply: KL lists, ST project open.

R4. Position encodes priority. First action is primary (Return), second is secondary (Cmd+Return); sections group related actions; submenus replace panel content. DOCUMENTED(https://developers.raycast.com/api-reference/user-interface/action-panel).
 Apply: one consistent primary/secondary shortcut map across ST block menus and KL row actions.

R5. Keyboard-first details: the hotkey recorder supports single-modifier shortcuts, left/right modifiers and international keyboards; desktop UIs drop web cues (pointer cursors, hover highlights). DOCUMENTED(https://www.raycast.com/blog/the-new-raycast; https://www.raycast.com/blog/a-technical-deep-dive-into-the-new-raycast).
 Apply: WS hotkey recorder; WebView2 UI must feel native.

### 1.3 Obsidian (local-first, plugins, files you own)

O1. Plain, open, human-readable files are the source of truth. Indexes and caches must be rebuildable; keep content and configuration separate; sync stays optional and pluggable; avoid nested containers. DOCUMENTED(https://obsidian.md/help/data-storage; https://obsidian.md/about). The "file over app" essay (apps are ephemeral, files can last) is on a personal site; authorship/role NOT_VERIFIED. DOCUMENTED(https://stephango.com/file-over-app).
 Also local-first: notes stay on the device; online services use end-to-end encryption. DOCUMENTED(https://obsidian.md/about).
 Apply: ST project = folder of open audio plus JSON/Markdown timeline with a rebuildable waveform cache. WS history is opt-in local files with export and a local-processing option. KL transcripts export with a documented schema.

O2. Plugin trust model: third-party code off by default (restricted mode), disabled plugins remain visible but inert, honest statement that fine-grained permissions cannot be enforced, per-version automated scans with a public scorecard, layered reporting paths. DOCUMENTED(https://obsidian.md/help/plugin-security).
 Apply: Wispral extensions/connectors: opt-in, scoped permissions where possible, plain statement of risk where not.

### 1.4 Arc / The Browser Company (spaces, calm chrome)

A1. Budget novelty: be familiar by default; spend users' limited learning effort only where the product is genuinely new, borrowing familiar gestures (for example @-mention). DOCUMENTED(https://browsercompany.substack.com/p/the-strategy-behind-dias-design).
 Apply: WS keeps hotkey and indicator conventional; novelty budget goes to bilingual (Arabic/English) controls.

A2. One obvious path per task; reveal secondary controls when the user signals interest (for example on hover). DOCUMENTED(https://browsercompany.substack.com/p/the-strategy-behind-dias-design).
 Apply: WS indicator compact until needed. KL console avoids duplicate controls.

A3. Power features carry learning cost: Spaces and pins created new decisions, and removing one feature weakened others. DOCUMENTED(https://browsercompany.substack.com/p/there-and-back-again-the-product).
 Apply: add no new organizing concept (workspace, queue, collection) to ST or KL without usage evidence.

A4. Context grouping with scoped identity: Arc Spaces become Profiles in Dia, Folders become Tab Groups, with import of tabs, history, extensions. DOCUMENTED(https://arc.net).
 Apply: KL workspaces per client or brand as a real boundary; day-one import/export.

"Calm chrome" as an explicit Arc principle: NOT_VERIFIED. The closest primary statement is the simplicity principle in A2.

### 1.5 Figma (multiplayer, properties panel)

F1. Show presence and keep one live version: cursors/avatars visible, no save step, no stale copy; sharing is opt-in and files start private. DOCUMENTED(https://www.figma.com/blog/multiplayer-editing-in-figma/).
 Apply: KL shows who is watching or handling a conversation to prevent double intervention. ST and KL are private by default.

F2. Predictable conflicts: edits to different properties merge; the same property resolves last-write-wins; local edits show immediately and stale server echoes are ignored to prevent flicker. DOCUMENTED(https://www.figma.com/blog/how-figmas-multiplayer-technology-works/) (search summary).
 Apply: ST block properties (voice, speed) and KL agent configuration merge per property.

F3. A contextual properties panel: file-level options when nothing is selected, object-level when something is; grouped by task; permission-tailored tabs; optional property labels. DOCUMENTED(https://help.figma.com/hc/en-us/articles/360039832014-Design-prototype-and-explore-layer-properties-in-the-right-sidebar).
 Apply: ST inspector (project vs block/track/clip). KL detail pane for the selected conversation or agent.

F4. Reduce chrome, but prefer fixed resizable panels over floating ones (floating crowded the canvas); reveal controls progressively; treat speed as a feature; offer an opt-out during beta with gradual rollout. DOCUMENTED(https://www.figma.com/blog/our-approach-to-designing-ui3/).
 Apply: floating only for the WS indicator. ST and KL use docked, resizable panels.

### 1.6 Apple Human Interface Guidelines (macOS; transfer to Windows analogs)

H1. Menu bar extras: the user, not the app, decides whether the icon appears (offer it during setup); do not rely on its presence, since the system hides extras; expose functionality elsewhere (for example a Dock menu); open a menu, not a popover, unless the content is too complex. DOCUMENTED(https://developer.apple.com/design/human-interface-guidelines/the-menu-bar).
 Apply: WS tray icon is user-controlled; the app stays reachable if Windows hides the icon in overflow.

H2. Keep menu items visible; disable instead of hiding; list all commands in menus for discoverability and full keyboard access. DOCUMENTED(https://developer.apple.com/design/human-interface-guidelines/the-menu-bar). Tension: the Win32 tray-menu guide says remove inapplicable items rather than disable them. DOCUMENTED(https://learn.microsoft.com/en-us/windows/win32/uxguide/winenv-notification).
 Apply: ST/KL main windows disable-not-hide; tray menu remove-not-disable. Test both.

H3. Match feedback to significance: passive status near its subject; alerts only for critical, ideally actionable information; warn only about unexpected irreversible loss; confirm only significant completions; say why a command cannot run; deliver in several modalities (color, text, sound, haptics). DOCUMENTED(https://developer.apple.com/design/human-interface-guidelines/feedback).
 Apply: WS indicator never uses color alone. ST: delete block (undo) vs delete project (confirm).

H4. Accessibility: allow text enlargement of at least 200 percent; meet WCAG AA contrast and offer higher contrast when the system setting is on; never color alone; avoid auto-dismiss timers (prefer explicit dismissal); under Reduce Motion replace transitions with fades; do not override system shortcuts. DOCUMENTED(https://developer.apple.com/design/human-interface-guidelines/accessibility).
 Apply: WS error messages must persist until dismissed or resolved, not only auto-hide.

H5. RTL rules: flip progress and ordered-navigation controls; keep digits inside a number in order; keep controls that name a real direction; do not flip photos, logos or universal marks; align a paragraph (3+ lines) by its own language; align list items consistently; consider about +2 pt Arabic size beside all-caps Latin; Arabic may use Western or Eastern Arabic numerals by region. DOCUMENTED(https://developer.apple.com/design/human-interface-guidelines/right-to-left).
 Icons: flip those implying reading direction or forward motion (speaker waves), keep real-world objects (clock), localize icons containing text. DOCUMENTED(https://developer.apple.com/design/human-interface-guidelines/right-to-left).
 Apply: all surfaces, with RTL icon variants. Media-timeline direction in ST is not addressed by that page (NOT_VERIFIED); decide through Arabic-user testing (PROPOSAL).

### 1.7 Microsoft Fluent 2 / Windows 11 guidance

W1. System tray and flyout. Use the notification area only for status/notifications and features with no desktop presence; keep users in control (remove icon, choose notification types, suspend, quit); one icon per component; 16/20/24 px versions; one status overlay; no flashing or long animations; left-click shows something (a flyout), on mouse-up; right-click opens the context menu; apps cannot auto-promote an icon out of overflow. DOCUMENTED(https://learn.microsoft.com/en-us/windows/win32/uxguide/winenv-notification) (Win7-era). Flyouts light-dismiss on outside click or Esc, and the first outside tap is absorbed. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/controls/dialogs-and-flyouts/flyouts).
 Apply: WS tray icon states; flyout with status, common actions, settings link.

W2. Notifications must be ignorable. No success notices unless users are waiting, after a recent failure, or for security; delay a failure that may self-resolve; escalate to a modal only when action is mandatory; not for rapidly changing data. DOCUMENTED(https://learn.microsoft.com/en-gb/windows/win32/uxguide/mess-notif). Current guidance: avoid noise, respect Focus Sessions (FocusSessionManager), launch in the notification's context. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/develop/notifications/app-notifications/app-notifications-ux-guidance).
 Apply: WS shows success in the indicator, not a toast. KL alert ladder: icon, notification, modal.

W3. Materials. Mica is the base layer of long-lived windows with a content layer above; Acrylic is for transient surfaces; apply Mica once, not to elements; it falls back to solid when transparency is off, in Battery Saver, on low-end hardware, when the window is inactive, below build 22000, and in high contrast. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/style/mica).
 Apply: ST/KL main windows use Mica (Alt). The transient WS indicator must stay legible on the solid fallback.

W4. Contrast themes and accessibility. Four contrast themes (Aquatic, Desert, Dusk, Night sky), toggled with Left Alt+Left Shift+Print Screen; never hard-code colors; use paired system colors; GrayText only for disabled; Hotlight only for links; 2 px borders on transient surfaces. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/accessibility/high-contrast-themes). Fluent 2: 4.5:1 text, 3:1 large text and non-text, predictable focus order and restoration after dialogs, reflow at 400 percent zoom (320 px), readable at 200 percent text zoom. DOCUMENTED(https://fluent2.microsoft.design/accessibility).
 Apply: explicit contrast-theme token mapping; how WebView2 content maps to system colors is NOT_VERIFIED, so test it.

W5. Motion is direct and consistent: surfaces sharing an entry point enter and exit alike; fade 83 ms, entrances 167/250/333 ms, exits 167 ms. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/motion). UISettings.AnimationsEnabled reports the system animation setting. DOCUMENTED(https://learn.microsoft.com/en-us/uwp/api/windows.ui.viewmanagement.uisettings.animationsenabled).
 Apply: indicator transitions 83-167 ms; honor the setting.

W6. RTL on Windows. Set FlowDirection on the root; it is not set automatically from the display language; avoid fixed widths; pseudo-localize; use LanguageFont mapping. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/globalizing/adjust-layout-and-fonts--and-support-rtl).
 Apply: UI direction follows UI language. Per-run direction for dictated text is PROPOSAL.

### 1.8 ElevenLabs (studio, dubbing, projects)

E1. Structure mirrors production: project, chapters, paragraphs, plus a multi-track timeline for narration, music, effects, video. DOCUMENTED(https://elevenlabs.io/docs/eleven-creative/products/studio).
 Apply: ST information architecture.

E2. Bind voice and settings to the smallest unit, with layered overrides (track default, clip override, an inherit toggle). DOCUMENTED(https://elevenlabs.io/docs/eleven-creative/products/studio; https://elevenlabs.io/docs/eleven-creative/products/dubbing/dubbing-studio).
 Apply: ST per-block voice and delivery settings.

E3. Regeneration is explicit and reversible: edits mark audio stale rather than silently rewriting; generation history can be restored; fixed versus dynamic duration exposes the sync-versus-naturalness trade-off; finished paragraphs can be locked. DOCUMENTED(https://elevenlabs.io/docs/eleven-creative/products/dubbing/dubbing-studio; https://elevenlabs.io/docs/eleven-creative/audio-tools/voiceover-studio; https://elevenlabs.io/docs/eleven-creative/products/studio).
 Apply: ST stale badge, take history, lock.

E4. Text, timing and audio are separate (speaker cards versus timeline), and costs tie to visible work (per-character generation, flat per sound effect). DOCUMENTED(https://elevenlabs.io/docs/eleven-creative/products/dubbing/dubbing-studio; https://elevenlabs.io/docs/eleven-creative/audio-tools/voiceover-studio).
 Apply: ST script edits do not move clips; show cost before regenerate.

E5. In-tool review: read-only share links with timestamped comments; versioned exports retained. DOCUMENTED(https://elevenlabs.io/docs/eleven-creative/products/studio).
 Apply: ST review links.

### 1.9 Wispr Flow (Flow Bar, onboarding, hotkey)

WF1. Floating bar: shown by default; click to start/stop; a persistent "show at all times" setting versus a one-hour hide from the right-click menu; on Windows it recovers from update relaunch, sleep, lock and full-screen apps, deferring recovery during dictation, backing off up to an hour, and retrying sooner on a hotkey press. DOCUMENTED(https://docs.wisprflow.ai/articles/5002934560-why-is-the-wispr-bar-is-not-appearing-or-disappearing). Shrink-when-idle sizing is NOT_VERIFIED.
 Apply: WS indicator recovery plan and a tray fallback.

WF2. Hotkey rules: most bindings need a modifier; max three keys; per-OS blocklist; conflicts rejected; no left+right of the same modifier; Caps Lock alone only for push-to-talk/hands-free; overlap warning for hands-free versus push-to-talk; last binding of a core action cannot be deleted. DOCUMENTED(https://docs.wisprflow.ai/articles/2612050838-supported-unsupported-keyboard-hotkey-shortcuts). Windows defaults (Caps Lock or Ctrl+Win) are NOT_VERIFIED (search summary only).
 Apply: adopt the validation model; add RTL-keyboard and non-US layout tests.

WF3. Interaction model: text lands in whichever field has focus at release; a very short tap inserts nothing; hands-free toggles; cancel via Esc or on-screen control; clipboard used briefly then restored; if insertion fails the transcript stays on the clipboard; desktop sessions capped near 20 minutes. DOCUMENTED(https://docs.wisprflow.ai/articles/6409258247-starting-your-first-dictation).
 Apply: WS failure-safe insertion; evaluate clipboard side effects (PROPOSAL).

WF4. Onboarding: permissions requested in context (granted ones skipped), in-place mic test, hotkey and mode with platform defaults, languages, skippable practice demos, resumable progress, separate data-consent step, honest warning when an optional permission is declined. DOCUMENTED(https://docs.wisprflow.ai/articles/3152211871-setup-guide).
 Apply: WS first run; track time to first successful dictation (PROPOSAL).

WF5. Accessibility tested and gaps disclosed (VoiceOver, NVDA, JAWS, TalkBack). Toasts do not take focus; errors interrupt while success/info wait politely; timeout dismissal is not explicit dismissal; known gap: the bar's menu is not keyboard-operable. DOCUMENTED(https://docs.wisprflow.ai/articles/3941699399-keyboard-and-screen-reader-accessibility-in-wispr-flow).
 Apply: WS can differentiate with a fully keyboard-operable indicator menu. Wispr Flow's Arabic/RTL support: NOT_VERIFIED (not checked).

## 2. Recording-state and privacy-indicator best practice

### 2.1 OS microphone indicators

#### Windows
- A microphone icon appears in the taskbar notification area whenever an app is using the microphone. DOCUMENTED(https://support.microsoft.com/en-us/windows/privacy/windows-camera-microphone-and-privacy)
- When an app is listening for spoken keywords (voice activation), a mic indicator also appears on the taskbar. DOCUMENTED(https://support.microsoft.com/en-us/windows/privacy/speech-voice-activation-inking-typing-and-privacy)
- Stable-Windows privacy model: mic access can be toggled for the device, for apps overall, and per Microsoft Store app. Classic desktop apps are NOT individually togglable; one shared "Let desktop apps access your microphone" switch governs all of them. Turning it off can disable some Windows features such as dictation, and some desktop apps may not be listed yet can still reach the mic. DOCUMENTED(https://support.microsoft.com/en-us/windows/privacy/windows-camera-microphone-and-privacy)
- NEW (Insider only): Windows 11 Insider Beta build 26220.9836 (2026-10-30) adds per-desktop-app allow/deny for camera, microphone, location under Settings > Privacy & security; apps prompt on first request; existing decisions carry over; some apps may show under an unexpected name or as "Unsigned". Insider features may never ship. DOCUMENTED(https://learn.microsoft.com/en-us/windows-insider/release-notes/beta/preview-build-26220-9836)
- "Recent activity" list (7-day window) and whether users can hide the mic tray icon: community Q&A only, answers conflict. NOT_VERIFIED. Implication: don't assume the OS icon is visible or hidden; the app's own indicator must stand alone.
- Packaged (MSIX) apps declare the Microphone capability; unpackaged apps rely on runtime consent (search summary of Learn pages only). NOT_VERIFIED.

#### macOS
- Orange dot to the right of Control Center in the menu bar = microphone in use; green = camera; purple = system audio recording; arrow = location. Only ONE dot shows at a time (camera/green outranks mic/orange). Control Center's top area can list which apps use mic/camera/location and clicking opens the Privacy window (macOS 13.3+). DOCUMENTED(https://support.apple.com/guide/mac-help/quickly-change-settings-mchl50f94f8f/mac)
- Sonoma 14.4+: indicators can be hidden on an EXTERNAL display only while an app is full screen there; main display still shows them; setup needs macOS Recovery + a Terminal command. DOCUMENTED(https://support.apple.com/en-us/118449)
- Apple privacy guidance (WWDC21 "Apple's privacy pillars in focus"): the orange dot shows whenever the built-in mic (or W1/H1 audio device) is listening; run the mic only when it makes sense to people; if your app has a mute control, actually stop receiving audio from the system when muted (don't just discard samples). DOCUMENTED(https://developer.apple.com/videos/play/wwdc2021/10085/) (transcript on page)
- No public API to suppress the dot: developer-forum replies only. NOT_VERIFIED.
- App Store Review Guideline 2.5.14: explicit consent plus a clear visual and/or audible indication when recording (camera, mic, screen, other input). DOCUMENTED(https://developer.apple.com/app-store/review/guidelines/) — a useful benchmark even outside the App Store.
- Apple HIG HTML pages are JavaScript-rendered; WebFetch returned titles only, so HIG wording on privacy indicators/color/motion is NOT_VERIFIED here.

#### Implications for an app's OWN indicator (PROPOSAL, derived from the DOCUMENTED facts above)
1. DO show your own indicator. The OS dot/icon only says "some app uses the mic"; users need to know "Wispral is listening, to what end, and how to stop it". Apple requires a clear visual/audible indication (2.5.14) and Windows guidance wants status shown by the app.
2. Never contradict the OS indicator: keep the app's state truthful to the actual capture stream. When idle/muted/privacy-blocked, CLOSE the capture stream so the OS indicator disappears (Windows icon = "app is using the mic"; Apple = stop receiving audio on mute). A "muted" label while the OS dot stays lit erodes trust.
3. Never imitate the OS indicator (orange dot, Windows mic glyph); use a distinct Wispral mark. (Analogy only: Apple 5.2.5 bars App Store apps that look confusingly like Apple interface, DOCUMENTED(https://developer.apple.com/app-store/review/guidelines/); applying it here is PROPOSAL.)
4. Don't try to hide or suppress the OS indicator (no documented Windows way; macOS only external-display fullscreen).
5. Windows tray guidance (Win32 UX guide; banner says written for Windows 7 and not updated): icon is a temporary source of status; show only while relevant; don't flash; no long-running animation for continuous activity; brief subtle animation OK for transient states; one overlay (bottom-right) for Warning/Error/Disabled/Blocked; avoid big swaths of pure red/yellow/green in base icons; don't change icon rapidly; tooltip = name + status; one icon per component; 16/20/24 px; let users remove the icon; only users promote icons out of overflow. DOCUMENTED(https://learn.microsoft.com/en-us/windows/win32/uxguide/winenv-notification)
6. Shell API: use NOTIFYICON_VERSION_4 (GUID identity, better accessibility); balloon timeout is superseded by the system accessibility timeout; ask permission before adding a non-transient icon; not for critical info needing immediate action. DOCUMENTED(https://learn.microsoft.com/en-us/windows/win32/shell/notification-area)

### 2.2 WCAG 2.2 criteria relevant to indicators (levels verified on w3.org)
Normative text: https://www.w3.org/TR/WCAG22/  | Understanding: https://www.w3.org/WAI/WCAG22/Understanding/<slug>.html
| SC | Level | What it means for an indicator | Source |
|---|---|---|---|
| 1.1.1 Non-text Content | A | Icon-only states need a text alternative/accessible name; sound cues used as sensory content need a descriptive text label | DOCUMENTED(https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html) |
| 1.4.1 Use of Color | A | Never color alone; add text, icon, shape/pattern, labels; if colors must differ, differ in lightness (>=3:1) too | DOCUMENTED(https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) |
| 1.4.3 Contrast (Minimum) | AA | Text 4.5:1 (3:1 large: >=18pt or >=14pt bold); inactive components exempt | DOCUMENTED(https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) |
| 1.4.11 Non-text Contrast | AA | UI components + graphics needed to understand state need 3:1 vs adjacent colors; icon-only status indicators included; state visuals (selected/focused) must meet 3:1; disabled exempt | DOCUMENTED(https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) |
| 1.4.12 Text Spacing | AA | No loss of content/function when user sets line-height 1.5x, paragraph 2x, letter 0.12x, word 0.16x font size. Understanding page notes scripts that don't use a property may conform with those that apply (example given is Japanese; Arabic not mentioned) | DOCUMENTED(https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html) |
| 1.3.4 Orientation | AA | Don't lock portrait/landscape unless essential (mobile/tablet; low relevance to a Windows tray companion) | DOCUMENTED(https://www.w3.org/WAI/WCAG22/Understanding/orientation.html) |
| 2.2.2 Pause, Stop, Hide | A | Auto-starting moving/blinking/scrolling content that lasts >5 s next to other content needs pause/stop/hide; auto-updating content has NO 5 s grace; a loading animation that is the only thing shown is exempt; short blink <5 s ok | DOCUMENTED(https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html) |
| 2.3.1 Three Flashes or Below Threshold | A | <=3 flashes in any 1 s unless below general/red flash thresholds (area threshold ~341x256 CSS px) | DOCUMENTED(https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html). For non-web software only display-based flashes count, not hardware LEDs: DOCUMENTED(https://www.w3.org/TR/wcag2ict-22/) |
| 2.3.3 Animation from Interactions | AAA | Users can disable interaction-triggered motion; technique C39 = CSS prefers-reduced-motion; color/opacity changes are not "motion"; (not required for AA but cheap) | DOCUMENTED(https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html) |
| 2.4.7 Focus Visible | AA | Visible keyboard focus indicator; must not vanish on a timer; indicator subject to 1.4.11 | DOCUMENTED(https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html) |
| 2.4.11 Focus Not Obscured (Minimum) | AA | Focused item not entirely hidden by author-created content (sticky/non-modal overlays; a floating pill/HUD is exactly such content) | DOCUMENTED(https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html) |
| 2.5.8 Target Size (Minimum) | AA | Pointer targets >=24x24 CSS px, or spacing exception (24px circle around each small target doesn't hit another), equivalent control, inline, user-agent-controlled, essential; zoom can't be used to claim compliance. WCAG2ICT gives non-web density-independent units (pt Apple, dp Android, epx Windows) | DOCUMENTED(https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html; https://www.w3.org/TR/wcag2ict-22/) |
| 3.2.1 On Focus / 3.2.2 On Input | A | Focus or changing a setting must not trigger unexpected context change (e.g., focusing the indicator must not start recording) | DOCUMENTED(https://www.w3.org/TR/WCAG22/) |
| 4.1.3 Status Messages | AA | State changes that don't take focus must be programmatically exposed to AT (role=status/alert/live region); "busy", progress, errors, results qualify; removal of a message may need its own message. Applies to non-web software too: expose via platform accessibility services | DOCUMENTED(https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html; https://www.w3.org/TR/wcag2ict-22/) |
| 1.4.13 Content on Hover or Focus | AA | Tooltips dismissible, hoverable, persistent | DOCUMENTED(https://www.w3.org/TR/WCAG22/) |
| 1.4.2 Audio Control | A | Audio auto-playing >3 s needs pause/stop/volume control (don't loop a "listening" tone) | DOCUMENTED(https://www.w3.org/TR/WCAG22/) |
Notes: AAA among the above: 2.3.3 (and 2.4.12 Focus Not Obscured Enhanced); all others are A or AA. PROPOSAL: use 32-40 px targets for the HUD for comfort (24 is the minimum).

### 2.3 Screen-reader announcements for state changes

#### Web content (ARIA live regions)
- aria-live: polite = announce when user pauses (normal choice); assertive = interrupts, reserve for critical/time-sensitive; off = generally announced only when focus is in the element. DOCUMENTED(https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions)
- role=status: implicit aria-live=polite + aria-atomic=true; don't move focus to it; for info that shouldn't interrupt. DOCUMENTED(https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/status_role)
- role=alert: implicit aria-live=assertive + aria-atomic=true; use sparingly; no focus management; no interactive content inside; if the user must respond use alertdialog; not announced if present at page load (must change dynamically); container must exist in DOM first, clear then inject text (identical text re-inserted is typically not a change); don't hide with display:none. DOCUMENTED(https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/alert_role)
- Register the live region BEFORE changing it (most reliable: in initial HTML; if created by JS, defer the first update); timing varies by browser/SR; content is read as plain text; don't combine role=alert with aria-live=assertive (double announcement in iOS VoiceOver); aria-atomic default false, aria-relevant default "additions text". DOCUMENTED(https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions)
- W3C: ARIA22 (role=status) is the main technique for 4.1.3; ARIA19 (role=alert) for errors where focus doesn't move; ARIA23 role=log; overusing assertive on minor content is a listed failure. DOCUMENTED(https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)

#### Native Windows (UI Automation)
- UiaRaiseNotificationEvent(provider, NotificationKind, NotificationProcessing, displayString, activityId): provider-side API that raises a notification event (UIA_NotificationEventId 20035 per search summary only); min Windows 10 1709; popup-style windows need Window Pattern + WM_GETOBJECT. DOCUMENTED(https://learn.microsoft.com/en-us/windows/win32/api/uiautomationcoreapi/nf-uiautomationcoreapi-uiaraisenotificationevent)
- NotificationProcessing values: ImportantAll(0, may flood), ImportantMostRecent(1), All(2), MostRecent(3), CurrentThenMostRecent(4), ImportantCurrentThenMostRecent(5; introduced in Windows build 26100). MostRecent = supersede earlier; CurrentThenMostRecent = don't interrupt current speech. DOCUMENTED(https://learn.microsoft.com/en-us/windows/win32/api/uiautomationcore/ne-uiautomationcore-notificationprocessing)
- AutomationProperties.LiveSetting = Off / Polite / Assertive (UWP + WinUI; Win32 enum LiveSetting 0/1/2). Microsoft sample: after setting the text you must also raise LiveRegionChanged via the automation peer; Assertive = announce immediately, Polite = finish current announcement first; use Assertive sparingly. DOCUMENTED(https://learn.microsoft.com/en-us/accessibility-tools-docs/items/uwpxaml/text_livesetting) ; (enum description from search snippet of https://learn.microsoft.com/en-us/uwp/api/windows.ui.xaml.automation.automationproperties.livesetting — NOT_VERIFIED by direct read)
- WinForms AccessibleObject.RaiseAutomationNotification (search snippet only) and Narrator announcement personalization (Narrator key+Alt+P, Jan 2026; search summary only): NOT_VERIFIED. Implication: don't encode meaning only in an announcement; keep state in the accessible name/value too.

#### Do WebView2 / Tauri / Electron bridge ARIA live regions to UIA?
- Chromium itself: native UIA provider is on by default in Chromium-based browsers on Windows starting Chrome 138 (rollout began 126); enterprise policy UiAutomationProviderEnabled can revert (supported through Chrome 146); MSAA/IA2 still supported; Narrator, Magnifier and Voice Access are UIA clients. The post does NOT mention WebView2, Electron, or live regions. DOCUMENTED(https://developer.chrome.com/blog/windows-uia-support-update)
- Chromium source (a historical commit, content/browser/accessibility/browser_accessibility_manager_win.cc): LIVE_REGION_CHANGED fires EVENT_OBJECT_LIVEREGIONCHANGED and UIA_LiveRegionChangedEventId; LIVE_REGION_CREATED fires the UIA live region event; ALERT fires EVENT_SYSTEM_ALERT (MSAA) plus UIA live-region-changed (a comment says role=alert should be treated as a normal live-region change rather than a system-wide alert). DOCUMENTED(https://chromium.googlesource.com/chromium/src/+/59edafe2ab2a3c5acb237af7ab5e24ed59c63a29/content/browser/accessibility/browser_accessibility_manager_win.cc) — code may have changed since that commit.
- Therefore web ARIA live regions DO reach Windows AT as live-region events in Chromium-based content. Whether a specific host (WebView2 / Tauri-wry / Electron) enables the accessibility tree, and how NVDA/Narrator voice it, is host-dependent:
  * Electron: accessibility auto-enables when AT such as JAWS/VoiceOver runs; app.setAccessibilitySupportEnabled(bool) can force it; system AT overrides the app setting; doc does not mention NVDA/Narrator or live regions. DOCUMENTED(https://www.electronjs.org/docs/latest/tutorial/accessibility)
  * WebView2: no official WebView2 accessibility/live-region documentation found; behavior is inferred from Chromium/Edge UIA. NOT_VERIFIED (no official WebView2 statement).
  * Tauri: no official docs page on screen reader/ARIA support found (uses WebView2 on Windows). Open issue tauri-apps/tauri#15624 reportedly shows WebView2 content becoming unreadable to screen readers after the host window loses/regains activation; seen only in a search summary: NOT_VERIFIED (https://github.com/tauri-apps/tauri/issues/15624). Long-running a11y tracker: https://github.com/tauri-apps/tauri/issues/207. A community plugin (https://github.com/cartertemm/tauri-plugin-prism) sends text straight to the native screen reader instead of relying on live regions: NOT_VERIFIED.
- PROPOSAL: put the state in BOTH places — (a) a visually-hidden-but-present role=status region in the web UI, and (b) a native UIA notification (UiaRaiseNotificationEvent / UWP LiveSetting) or tray tooltip/accessible name from the host process — then test with Narrator + NVDA + JAWS on target builds. Never rely on a single path.

#### Narrator / NVDA behavior for tray/flyout content
- No official Microsoft page found that documents how Narrator speaks custom tray icon state or flyouts; the Win32 UX guide says infotip text should be feature name + status, and flyout "Summary" should repeat the tooltip text because tooltips are not reachable by touch. DOCUMENTED(https://learn.microsoft.com/en-us/windows/win32/uxguide/winenv-notification)
- Win+B focuses the notification area — only a community Q&A claim. NOT_VERIFIED.
- NVDA's "Report notifications" option (Object Presentation) covers help balloons and toasts; whether it also silences UIA notification events is disputed in community threads (nvaccess/nvda#10956): option documented in https://download.nvaccess.org/releases/2026.3/documentation/userGuide.html (seen via search summary); UIA linkage NOT_VERIFIED. A user could therefore suppress UIA notifications.
- Implication (PROPOSAL): always mirror important state in a persistent, focusable/readable element (tray tooltip, HUD accessible name/value) so a missed or suppressed announcement is recoverable.

### 2.4 Redundant cues (not color alone)
- Sources: WCAG 1.4.1 (text, icons, shape/pattern, labels, lightness difference; see table above); WCAG 1.1.1 (sound/sensory cues get a descriptive text label); Windows UX guide (icon shape/overlay changes, standard overlays, progressive emphasis, subtle changes because peripheral vision is motion-sensitive); Apple 2.5.14 ("visual and/or audible"). All DOCUMENTED above.
- prefers-reduced-motion maps to Windows 11 Settings > Accessibility > Visual effects > Animation effects (Windows 10: "Show animations") and macOS Reduce motion. DOCUMENTED(https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion)
- Haptics: no desktop source gathered; NOT_VERIFIED / out of scope.

### 2.5 PROPOSAL — Indicator state machine (WisprSide)
Principles: (1) visible only when relevant ("disappears when not needed"); (2) truthful to real mic capture; (3) every state carries >=3 non-color channels; (4) no blinking >3 Hz, no looping animation >5 s without a stop path; with reduced-motion, swap animation for a static change; (5) sound optional, short, off-by-default or user-set; (6) announcements: polite for routine, assertive/alert only for errors/privacy-blocked.
| State | Shape/icon (non-color) | Text label (tooltip + accessible name) | Color (supporting only; >=3:1 non-text) | Motion | Sound (optional) | SR announcement | Mic stream open? |
|---|---|---|---|---|---|---|---|
| idle | HUD hidden; tray icon = outline mic (or absent) | "Wispral, ready" | neutral grey | none | none | none (no live update) | NO |
| listening | solid filled mic + level bars | "Listening" | accent (e.g., teal/blue; not red) | level bars respond to input; reduced-motion = static bars/steady ring | short start earcon (user-set) | role=status polite: "Listening" | YES |
| processing | mic + spinner/ellipsis glyph | "Transcribing" | accent muted | subtle spinner; reduced-motion = static "..." | none | polite: "Transcribing" (only if >~1 s to avoid chatter) | NO (capture closed) |
| inserting | check/arrow-into-text glyph | "Inserting text" / "Inserted" | success tint | single short fade; reduced-motion none | optional soft tick | polite: "Text inserted" (or suppress; text appearing in field is already announced by AT) | NO |
| error | triangle/exclamation overlay | specific text "Couldn't transcribe — tap to retry" | warning tint + text | one-time, no flash | distinct error earcon | assertive/role=alert once (error needs attention) | NO |
| muted | mic with slash glyph | "Muted — microphone off" | neutral/desaturated | none | optional mute tone | polite: "Microphone muted" | NO (must really close stream — Apple WWDC21) |
| privacy-blocked | mic with lock/shield + "blocked" overlay | "Microphone blocked by Windows privacy settings — open settings" | warning tint | none | error earcon | alert once; provide link/button to Settings > Privacy & security > Microphone | NO |
Transitions: idle->listening (hotkey/PTT) ; listening->processing (end of speech/release) ; processing->inserting ; inserting->idle (auto-hide after ~1-2 s, no focus steal) ; any->error ; listening/idle->muted (user) ; any->privacy-blocked (OS denies/policy) ; privacy-blocked->idle on permission restored (poll/consent-store event; mechanism NOT_VERIFIED).
Guardrails: HUD must not steal focus (3.2.1/2.4.11), must be dismissible, targets >=24 px (2.5.8) with Esc to cancel, and must keep working when text spacing/zoom changes (1.4.12).

## 3. Arabic and RTL

### 3.1 Mirroring rules (bidi UI)
Foundations
- Set base direction with the HTML `dir` attribute (on <html>, tight inline wrappers); W3C prefers markup over CSS or Unicode control characters for text/html. DOCUMENTED(https://www.w3.org/International/articles/inline-bidi-markup/) and (https://www.w3.org/International/geo/html-tech/tech-bidi.html, from search summary only; NOT_VERIFIED by direct read)
- CSS logical properties describe layout via inline/block axes; start/end follow `direction`/`writing-mode` (margin-inline-start, padding-inline, inset-inline-start, text-align:start/end, float:inline-start, border-start-start-radius). DOCUMENTED(https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_logical_properties_and_values). Browser-support status not read: NOT_VERIFIED.
- Native Windows (XAML): FlowDirection is NOT set automatically from the display language and does not change when the user switches language; set it on the root panel from the language's LayoutDirection. Images can mirror via FlowDirection or per-layout-direction resource files (`file.layoutdir-rtl.png`). Avoid fixed widths/heights/absolute positions; pseudo-localize. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/globalizing/adjust-layout-and-fonts--and-support-rtl)
- Microsoft BiDi design rationale: mirror the UI, consistent direction, mixed-text support; text blocks of 3+ lines (5+ words per line) may align opposite to the app direction for readability. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/globalizing/design-for-bidi-text)
- Material 2/3 and Apple HIG HTML pages are JS-rendered (title only). Readable: Material 1 (static) and Apple HIG via its JSON endpoint (https://developer.apple.com/tutorials/data/design/human-interface-guidelines/right-to-left.json). Material 3 statements below come from a search summary only: NOT_VERIFIED.

What mirrors / what doesn't
| Element | Mirror in RTL? | Source |
|---|---|---|
| Back/forward/next/previous, navigation order, direction arrows | YES | DOCUMENTED(https://m1.material.io/usability/bidirectionality.html; https://developer.apple.com/tutorials/data/design/human-interface-guidelines/right-to-left.json) |
| Layout order of panes/lists/grids, text alignment (start), icons in text fields, checkbox side | YES | DOCUMENTED(https://m1.material.io/usability/bidirectionality.html; https://learn.microsoft.com/en-us/windows/apps/design/globalizing/design-for-bidi-text) |
| Progress bars / sliders (linear value progress) | YES (fill right-to-left; swap end glyphs e.g. quiet/loud speaker) | DOCUMENTED(https://m1.material.io/usability/bidirectionality.html; https://developer.apple.com/tutorials/data/design/human-interface-guidelines/right-to-left.json) |
| Volume slider incl. speaker icon with waves | YES | DOCUMENTED(https://m1.material.io/usability/bidirectionality.html; https://developer.apple.com/tutorials/data/design/human-interface-guidelines/right-to-left.json "speaker with sound waves") |
| Icons showing text/reading direction (text-line, alignment icons), forward-motion figures (walking person) | YES | DOCUMENTED(https://m1.material.io/usability/bidirectionality.html; https://developer.apple.com/tutorials/data/design/human-interface-guidelines/right-to-left.json) |
| Media playback controls (play/rewind/ff) and MEDIA progress bar/timeline | NO (they reflect tape/media direction, not reading direction) | DOCUMENTED(https://m1.material.io/usability/bidirectionality.html). Microsoft's BiDi music-app case study says media controls are generally expected LTR (DOCUMENTED, design-for-bidi-text). Apple HIG JSON does not mention media controls/timelines (explicitly absent). Material 3 reportedly says media controls always LTR with a Hebrew-specific timeline note: NOT_VERIFIED |
| Audio waveform | Not addressed by any source read; follows media-timeline logic (time runs left to right). PROPOSAL: keep waveform + scrubber LTR with explicit dir="ltr". | NOT_VERIFIED |
| Numbers (incl. digits in clocks, phone numbers) | Don't reverse digit order; may need localized numerals | DOCUMENTED(https://m1.material.io/usability/bidirectionality.html; https://developer.apple.com/tutorials/data/design/human-interface-guidelines/right-to-left.json "never reverse digits within a number") |
| Sequence numerals/ratings (1..5), ordered image sets | Reverse the ORDER of items | DOCUMENTED(https://developer.apple.com/tutorials/data/design/human-interface-guidelines/right-to-left.json) |
| Clocks, circular refresh/history icons (clockwise stays clockwise) | NO | DOCUMENTED(https://m1.material.io/usability/bidirectionality.html; https://developer.apple.com/tutorials/data/design/human-interface-guidelines/right-to-left.json: clock icon unchanged) |
| Checkmarks, logos, universal marks, real-world objects (pencil, controller, keyboard, headset), non-directional icons (camera), photos, fixed-direction "move right" controls | NO | DOCUMENTED(https://developer.apple.com/tutorials/data/design/human-interface-guidelines/right-to-left.json; https://m1.material.io/usability/bidirectionality.html) |
| Charts and graphs | NO | DOCUMENTED(https://m1.material.io/usability/bidirectionality.html) |
| Search/magnifier (angle reflects right-handedness) | NO | DOCUMENTED(https://m1.material.io/usability/bidirectionality.html; Apple WWDC22 https://developer.apple.com/videos/play/wwdc2022/10034/) |
| Slashes for "off" state (e.g., muted mic) | Keep slash direction | DOCUMENTED(https://m1.material.io/usability/bidirectionality.html; https://developer.apple.com/videos/play/wwdc2022/10034/: Apple kept slash direction consistent) |
Apple: icons are not auto-mirrored; decide case by case (pen flipped, magnifier kept); for complex icons flip only the parts that need it; icons containing text need localized variants. DOCUMENTED(https://developer.apple.com/videos/play/wwdc2022/10034/ page; https://developer.apple.com/tutorials/data/design/human-interface-guidelines/right-to-left.json).
PROPOSAL (Wispral icon set): tag each icon `mirror: true|false|variant`; mic glyph = false; mute slash = false; back/next = true; transport + waveform = false (explicit dir="ltr" container); "processing" progress bar = true; text-alignment / insert-into-text arrows = true.

### 3.2 Numerals
- Regional digit families: European 0-9 (Western Arabic-speaking regions e.g., Algeria, Morocco), Arabic-Indic ٠-٩ (Egypt, Saudi Arabia, Iraq), Eastern Arabic-Indic ۰-۹ (Iran, Afghanistan); Arabic-Indic digits come with their own decimal (٫) and thousands (٬) separators; choose by audience region. DOCUMENTED(https://www.w3.org/TR/alreq/ sec 6.1.2)
- Apple: system picks Western vs Eastern numerals by country or user setting; Western in Morocco/Algeria/Tunisia; apps should support both or check the target country. DOCUMENTED(https://developer.apple.com/videos/play/wwdc2022/10034/)
- CLDR source files (main branch): ar_SA and ar_EG set default numbering system `arab`. DOCUMENTED(https://raw.githubusercontent.com/unicode-org/cldr/main/common/main/ar_SA.xml; .../ar_EG.xml). ar_MA.xml sets "↑↑↑" (inherit; value not visible in the file).
- Runtime check on this PC (Node v24.19.0, ICU 78.3, CLDR 48.0; Intl.NumberFormat resolvedOptions; locally observed, not a URL): arab = ar-SA, ar-EG, ar-IQ, ar-JO, ar-LB, ar-SY, ar-KW, ar-QA, ar-OM, ar-BH, ar-YE, ar-SD, ar-PS; latn = bare `ar`, ar-001, ar-AE, ar-MA, ar-DZ, ar-TN, ar-LY; `fa` = arabext. Maghreb output 1.234.567,89 (dot grouping, comma decimal); arab locales ١٬٢٣٤٬٥٦٧٫٨٩. IMPORTANT: bare `ar` gives Latin digits under CLDR 48, so keep the region subtag (or the user's explicit choice). Other platforms/ICU versions: NOT_VERIFIED.
- API: Intl.NumberFormat takes a `numberingSystem` option or `-u-nu-` extension (options wins); default is locale dependent; verify with `resolvedOptions().numberingSystem`. DOCUMENTED(https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat/NumberFormat)
- Microsoft: use Globalization APIs for number formats; don't infer region from language or vice versa. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/globalizing/guidelines-and-checklist-for-globalizing-your-app)
- PROPOSAL: Default digits = "Auto" from the user's full locale (OS region + language), plus a Settings override: Auto / Western 0-9 / Arabic-Indic ٠-٩ (/ Persian ۰-۹ if fa is added). In dense data (Klaint tables, timestamps, IDs, durations, phone numbers, file sizes) default to Western tabular digits for alignment/copy-paste and make search normalize both digit sets; apply the override uniformly to all numbers incl. in icons/badges.

### 3.3 Mixed-direction text
- Neutrals (spaces/punctuation) take direction from context; at a boundary they follow the base direction, so trailing "!" or ")" can jump sides; numbers are weak (display LTR but don't break a run) and can attach to the wrong run. DOCUMENTED(https://www.w3.org/International/articles/inline-bidi-markup/uba-basics; https://learn.microsoft.com/en-us/globalization/fonts-layout/text-directionality)
- Known-direction fragment: tight wrapper with `dir` (e.g., `<span dir="ltr">`); unknown/user-generated: `<bdi>` or `dir="auto"` (first strong character decides, isolates the element). `bdo` overrides the algorithm; rarely needed. DOCUMENTED(https://www.w3.org/International/articles/inline-bidi-markup/)
- Pitfall: first-strong detection can pick the wrong direction (e.g., Arabic text starting with a Latin word): set an explicit dir when known; deriving direction from `lang` is generally a bad idea; marks inserted into stored strings change the content, so prefer direction metadata or render-time isolation. DOCUMENTED(https://www.w3.org/International/articles/strings-and-bidi/)
- CSS `unicode-bidi: isolate` computes direction without the element's content (acts like a single object); `isolate-override` and `plaintext` exist; MDN says authors should not override unicode-bidi in HTML (use `dir`). DOCUMENTED(https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/unicode-bidi)
- Unicode: isolates LRI U+2066, RLI U+2067, FSI U+2068, PDI U+2069 (since Unicode 6.3) behave as neutrals and don't affect surrounding order (embeddings do); LRM U+200E, RLM U+200F, ALM U+061C are invisible strong characters; prefer isolates over embeddings; on the web prefer HTML/CSS. UAX #9 is Revision 52 for Unicode 18.0.0 (2026-09-01). DOCUMENTED(https://unicode.org/reports/tr9/)
- Use control characters only where markup is impossible (title attributes, plain text); isolate+PDI mirror `span dir`/`bdi`; RLM/LRM for small punctuation/number fixes; avoid RLE/LRE/PDF. DOCUMENTED(https://www.w3.org/International/articles/inline-bidi-markup/). Example: LRM before and RLM after the digit in "one two ثلاثة 4 خمسة" makes "4" its own LTR run. DOCUMENTED(https://learn.microsoft.com/en-us/globalization/fonts-layout/text-directionality)
- Windows: the BiDi Parenthesis Algorithm fixes paired brackets; Microsoft's media-app sample adds zero-width LRM/RLM when a string whose direction opposes the app's starts or ends with neutrals. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/globalizing/design-for-bidi-text)
- PROPOSAL (Wispral): (1) every screen sets `<html lang dir>` from the UI language; (2) wrap user-generated strings (agent names, file names, transcripts snippets, contact names) in `<bdi>`; (3) wrap code, URLs, file paths, emails, phone numbers, IDs, hashes in `dir="ltr"` + `unicode-bidi: isolate` (`<code dir="ltr">`, `<bdi dir="ltr">`); keep `text-align:start`; (4) in native surfaces without markup (tray tooltip, toasts, window titles, clipboard, logs) wrap dynamic strings as U+2068 ... U+2069 (FSI/PDI); (5) never auto-insert RLM/LRM into text the user dictates or that is inserted into other apps unless a test shows a boundary bug; (6) paragraphs of 3+ lines align by their own language, shorter text follows UI direction, list items stay consistent (Apple HIG JSON; Microsoft page above, both DOCUMENTED).

#### Caret / selection
- Logical order (storage/typing) differs from visual order; arrow keys can change visual direction mid-line (mixed Latin/Hebrew example). DOCUMENTED(https://learn.microsoft.com/en-us/globalization/fonts-layout/text-directionality)
- Caret position at a direction boundary is ambiguous; Uniscribe convention: typing/pasting/advancing -> trailing edge of the last character; retiring -> leading edge of last character passed; Home = leading edge of line, End = trailing edge. DOCUMENTED(https://learn.microsoft.com/en-us/windows/win32/intl/displaying-the-caret-in-bidirectional-strings)
- Selection: contiguous in storage is NOT contiguous on screen across a boundary. Apple iOS/iPadOS 26 "Natural Selection" follows the cursor visually; UITextView gets `selectedRanges` (array of non-contiguous ranges); delete/format must act on all ranges (delete in reverse order); NSTextView already worked this way; staying on TextKit 2 is required. DOCUMENTED(https://developer.apple.com/videos/play/wwdc2025/222/)
- W3C editing mailing-list discussion (not a standard; search summary only, NOT_VERIFIED): one visual caret position can map to two logical offsets, so selection state should record the bidi level; browsers differ on logical vs visual caret movement. https://lists.w3.org/Archives/Public/public-editing-tf/2014Dec/0057.html
- PROPOSAL: don't hand-roll a text editor for WisprStudio; use a platform/mature text engine, support multi-range selections for cut/delete/format, test caret behavior at LTR/RTL boundaries and with isolates, and keep dictated-text insertion as plain Unicode.

### 3.4 Fonts (OFL unless noted)
Method: google/fonts repo `ofl/<dir>/METADATA.pb` (license, subsets, axes, files) + `DESCRIPTION.en_us.html`; each directory below was listed via the GitHub contents API and contains `OFL.txt`. License URL for all: https://github.com/google/fonts/blob/main/ofl/<dir>/OFL.txt. "Latin?" = Google Fonts subset lists, not full glyph inventories. Per-glyph facts (tashkeel coverage, digit style, x-height) were not verified (no font downloads were made): NOT_VERIFIED unless stated. Descriptions quoted are the designers' own claims.
| Font (dir) | Latin? | Weights / variable | What is documented | Role |
|---|---|---|---|---|
| IBM Plex Sans Arabic (ibmplexsansarabic) | yes (latin, latin-ext, cyrillic-ext) | 7 static, 100-700; NOT variable on Google Fonts | OFL; IBM/plex README confirms OFL-1.1 and lists the package; family built to read clearly in print/web/mobile (DESCRIPTION) | UI sans, pairs with Inter |
| Noto Sans Arabic (notosansarabic) | yes (latin, latin-ext, symbols, math) | variable wdth 62.5-100, wght 100-900 | OFL-1.1 (notofonts/arabic); 1,642 glyphs; unmodulated sans | dense/compact UI (width axis) |
| Noto Naskh Arabic (notonaskharabic) | yes (latin subsets) | variable wght 400-700 | OFL; 1,598 glyphs; serif-like Naskh with stroke contrast; W3C alreq: Naskh is the default basis for continuous reading | long-form/transcript |
| Readex Pro (readexpro) | yes (latin, latin-ext, vietnamese) | variable HEXP 0-100, wght 160-700 | OFL-1.1; Arabic by Nadine Chahine derived from Lexend's Latin; designed to ease reading (Google Fonts article). Lexend's reading-fluency claim is stated for Lexend, not claimed for Readex Pro. Tashkeel/digits: README+article silent | single-family body text |
| Rubik (rubik) | yes (+cyrillic, hebrew) | variable wght 300-900 + italic | OFL; Arabic designer credited (Omaima Dajani) | friendly UI/marketing |
| Cairo (cairo) | yes (Latin extended from Titillium Web) | variable wght 200-1000, slnt | OFL; Kufi-influenced; "open interiors, compact ascenders/descenders"; Arabic/Persian/Urdu; light weights for body, heavy for headlines (DESCRIPTION) | display/marketing; usable UI |
| Tajawal (tajawal) | yes | 7 static 200-900 | OFL; geometric, honors calligraphy rules | UI/brand |
| Almarai (almarai) | yes | 4 static 300/400/700/800 | OFL; "especially legible on screens" (designer claim) | UI/body |
| Harmattan (harmattan) | yes | 4 static 400-700 | OFL (SIL); Warsh-style for West-African Arabic-script languages | not a default MSA UI font |
| Vazirmatn (vazirmatn) | yes (Latin from Roboto per README) | variable wght 100-900 | OFL-1.1; Persian focus | only if Persian is added |
| Lexend (lexend) | Latin only (no Arabic subset) | variable wght 100-900 | OFL; Readex Pro is its Arabic extension | n/a |
| Alexandria (alexandria) | yes | variable wght 100-900 | OFL; Arabic drawn to pair with Montserrat; light weights for long body, heavy for short headlines | display/headlines |
| El Messiri (elmessiri) | yes (Latin from Philosopher) | variable wght 400-700 | OFL; brush-like Naskh cues; "open interior spaces help legibility at small sizes" (self-description); covers Farsi/Urdu | headlines/editorial |
| Amiri (amiri) | yes (latin, latin-ext) | static R/I/B/BI | OFL; classical Naskh for book typesetting; description silent on Latin/digits/diacritics | long-form reading only |
| Inter (inter) | Latin/Greek/Cyrillic; NO Arabic | variable opsz 14-32, wght 100-900 (+ italic) | OFL; tall x-height, tabular numbers, slashed zero, contextual alternates (DESCRIPTION) | Latin side of every pairing |
| Segoe UI Variable / Segoe UI (system) | Segoe UI Variable: Latin, Greek, Cyrillic only; Segoe UI: Arabic, Armenian, Cyrillic, Georgian, Greek, Hebrew, Latin | SegUI Var: wght+opsz | NOT OFL (Microsoft system fonts; do not bundle; exact redistribution terms NOT_VERIFIED). Microsoft names Segoe UI as the UI font for Arabic. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/typography; https://learn.microsoft.com/en-us/windows/apps/design/globalizing/loc-international-fonts). LOCAL CHECK (fontTools on this Windows PC): SegUIVar.ttf v2.03 has 0/256 glyphs in U+0600-06FF; Segoe UI v5.72 has 256/256, all 8 tashkeel U+064B-0652, Arabic-Indic digits U+0660-0669 and Extended U+06F0-06F9, plus ALM/LRM/RLM | zero-bundle Windows UI |
Also: Selawik = open-source font metric-compatible with Segoe UI for apps that don't bundle Segoe (DOCUMENTED, typography page above); its Arabic coverage NOT_VERIFIED.

#### Recommended pairings (PROPOSAL)
Mixed-script stacks work through per-glyph fallback: list the Latin font first (Inter has no Arabic, so Arabic falls through to the next family).
(a) WisprSide compact UI
 1. Windows-native, zero bundle: `font-family: "Segoe UI Variable", "Segoe UI", system-ui, sans-serif` -> Latin from Segoe UI Variable, Arabic falls to Segoe UI (exact CSS family-name strings NOT_VERIFIED). 
 2. Brand-consistent bundle: Inter (var) + IBM Plex Sans Arabic (static 400/500/600). Alt: Inter + Noto Sans Arabic variable using the wdth axis (down to 62.5) to fit narrow HUD/tray widths.
(b) WisprStudio editor
 1. UI chrome: Inter + IBM Plex Sans Arabic.
 2. Transcript/script body: Readex Pro (one variable family for both scripts; consistent rhythm) OR Noto Naskh Arabic + Inter (traditional long-form look). Amiri only for classical/literary content.
 3. Display/branding accents: Alexandria or Cairo for headlines only.
(c) Klaint dense console
 1. Inter (tabular nums via `font-variant-numeric: tabular-nums`) + Noto Sans Arabic (variable, condensed widths for tables).
 2. Alt: Inter + IBM Plex Sans Arabic (static, fewer variants to load).
 Digits: Western tabular default for data columns with user override (see A3.2); whether these Arabic fonts provide tabular Arabic-Indic digits: NOT_VERIFIED.

#### Size / line-height guidance for Arabic
Evidence:
- Apple WWDC22: digital Arabic fonts are matched to lowercase Latin, so beside uppercase Latin they look smaller; suggested ~+10% Arabic size, which also helps small-size legibility; Arabic is taller (dots/diacritics) so allow more vertical space where vocalization marks are used. DOCUMENTED(https://developer.apple.com/videos/play/wwdc2022/10034/) (the "extra leading" remark appeared only in a search summary: NOT_VERIFIED).
- Apple HIG JSON: raise RTL font ~2 pt when it sits beside all-caps Latin. DOCUMENTED.
- W3C ALReq: Arabic ascenders/descenders extend much further than Latin's; mixed-script lines need careful vertical alignment; marks' height varies by font. DOCUMENTED(https://www.w3.org/TR/alreq/) (no numeric line-height there). Do not letter-space joined Arabic; emphasis stretching uses the baseline (kashida/tatweel), not tracking (implied by 4.3.7.1/7.3). DOCUMENTED(https://www.w3.org/TR/alreq/).
- Microsoft: fonts for other languages may need larger minimum sizes; design for different text lengths; no fixed heights. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/globalizing/guidelines-and-checklist-for-globalizing-your-app). Windows type ramp: caption 12/16, body 14/20, large body 18/24, subtitle 20/28 epx; minimum 12px Regular / 14px Semibold "illegible in some languages" below that. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/typography).
- Material (m2 language-support page; search summary only, NOT_VERIFIED): Arabic is a "tall" script needing extra line height and can look smaller than Latin at the same size; Latin baselines ~1.5x body, ~1.2x display.
- WCAG 1.4.12: layout must survive line-height 1.5x, letter 0.12x, word 0.16x (see A2).
Starting values (PROPOSAL; validate with real tashkeel text in each chosen font; no numeric Arabic standard found):
| Surface | Latin | Arabic |
|---|---|---|
| WisprSide HUD/tray text | 12-13px / 16-18px (never <12px) | 13-14px / 20-22px (>=1.55) |
| WisprStudio chrome / labels | 13-14px / 20px | 14-15px / 22-24px |
| WisprStudio transcript editor | 15-16px / 24px | 17-18px / 28-32px (~1.7) |
| Klaint dense tables | 12-13px / 16-18px | 13-14px / 20px; row min-height from Arabic, not fixed |
Rules: use `:lang(ar)` overrides; `letter-spacing: 0` for Arabic; no uppercase transforms; no synthetic italics; leave extra vertical padding for tashkeel/dots; use min-height instead of fixed heights; scale Arabic ~+10% when beside uppercase Latin labels; text-spacing override test (1.5/0.12/0.16) must not clip.

### 3.5 Open items and NOT_VERIFIED summary (sections 2 and 3)
- Windows "recent activity" list and hiding the mic icon (community-only); WebView2/Tauri/Electron live-region bridging to Narrator/NVDA (Chromium fires UIA live-region events, no official host statement: test it); NVDA "Report notifications" vs UIA notifications.
- Material 2/3 and Apple HIG HTML text (JS-rendered); numeric Arabic line-height standard; glyph-level font facts (no downloads); CLDR numbering beyond the Node/ICU CLDR 48.0 observation.


## 4. Wispral design identity direction (PROPOSAL, built on documented constraints)

**Direction note (read first).** After this research was drafted, the main session adopted the "Quiet Signal" design system (`docs/design/WISPRAL_DESIGN_SYSTEM.md` and `docs/design/tokens/wispral.tokens.json`: IBM Plex Sans + IBM Plex Sans Arabic, IBM Plex Mono, Noto Naskh Arabic for long-form reading, Lucide icons, paper/graphite neutrals). That adopted direction wins wherever it differs from sections 4.1 to 4.12 below. Those sections are kept as an independently derived alternative and as the carrier of the documented constraints (contrast math, Windows geometry and motion values, sound and RTL rules). Section 4.13 is a factual check of the adopted choices (licenses, Arabic coverage, contrast) and is the part to act on.

Everything in this section is my design proposal. Where a value rests on a documented source, the source is cited and tagged. Contrast ratios are COMPUTED by me with the WCAG relative-luminance formula (https://www.w3.org/TR/WCAG22/#dfn-contrast-ratio) using `_contrast.py` in the research folder; every text pair below is at least 4.5:1 and every non-text pair at least 3:1.

### 4.1 Idea: "Quiet instrument, one living line"

Wispral's name carries *wisp* (breath, a thin trace) and *oral*. The identity is a **quiet instrument**: neutral, calm chrome that stays out of the way, with exactly one expressive element, **the wisp**, a single continuous line that is the voice made visible. It appears as the live level indicator, the caret trail, the waveform stroke, the loader and the empty-state drawing, always with the same geometry: 1.5 px stroke, round caps, a sinusoid whose amplitude decays from "spoken" to "whisper".

Umbrella principles (each is a testable rule):
1. **Disappear by default, surface on intent.** Nothing animates, glows, or badges while the user is not dictating or acting. (Source for the product promise: the mission brief; no external citation needed.)
2. **State is never color alone.** Every state has shape + text/icon + (optionally) sound; color is the fourth channel. Rationale and criteria: WCAG 1.4.1 and 4.1.3 (see section 2 of this report).
3. **One saturated thing per view.** The live element (recording indicator, playhead, live-session marker) is the only saturated element; the rest of the chrome sits within 2 steps of the background.
4. **Honest privacy surface.** Where audio goes (device, local model, cloud) is always one click away and shown in the indicator's tooltip text, not only in settings.
5. **Bilingual by construction.** Logical properties, mirrored layout, Arabic-tuned type scale, locale-correct numerals; the Arabic UI is a first-class build, not a translation pass.
6. **Keyboard-first, mouse-fluent.** Every action reachable from a command surface; no animation on keyboard-triggered, high-frequency actions (principle drawn from Linear/Raycast research; see section 1).
7. **Local-first, files you own.** Projects, transcripts, dictionaries and policies are plain, exportable files (principle drawn from Obsidian; see section 1).

### 4.2 Umbrella plus three personalities

| | **Wispral (umbrella)** | **WisprSide** | **WisprStudio** | **Klaint** |
|---|---|---|---|---|
| Personality | Calm, precise, bilingual | **The breath**: ephemeral, instant, nearly invisible | **The tape and the paper**: warm, tactile, craft-minded | **The control room**: dense, legible, accountable |
| Metaphor | Instrument + line | Pill that appears and dissolves | Timeline as the hero, paper-and-tape | Flight-strip board, hairline grid |
| Density | n/a | Airy (settings), micro (indicator) | Comfortable | Compact |
| Accent (hue family) | Neutral only (ink and paper) | Breath teal (hue about 190) | Tape magenta (hue about 335) | Signal ultramarine (hue about 255) |
| Radius character | 4 / 8 (Windows 11 parity) | Pill (full) for the bar, 4/8 elsewhere | 4 controls, 6 clips | 2 for strips/tables, 4 controls |
| Signature device | The wisp line | The wisp bar (indicator pill) | Waveform stroke + warm paper canvas | Status glyph set + ticker bar |
| Default theme | follows OS | follows OS; indicator is always dark-on-light-safe | dark | light (paper), dark available |
| Motion temperament | Restrained | Almost none; one breath cycle while listening | Playhead and scrub are the only continuous motion | Near zero; live data updates in place |

Why these hues: product accents must never encode state (a hard rule). State uses the semantic status tokens plus shape. The accents sit away from the status hues (red about 25, amber about 85, green about 150), so teal (190), ultramarine (255) and magenta (335) stay distinguishable from success, warning and danger even for users with some color-vision difference; this hue-spacing rationale is my reasoning, not a tested result. NOT_VERIFIED for color-blind legibility until simulated (see section 5 tooling).

### 4.3 Token architecture: primitive, semantic, component

**Format.** Author tokens in the W3C Design Tokens Community Group JSON format (`$value`, `$type`, `{group.token}` aliases, `$ref` JSON Pointer). The spec is still a draft: the page says "Do not attempt to implement this version", the latest published version is 2025.10, and the working draft is dated 2026-09-08. DOCUMENTED (https://www.designtokens.org/tr/drafts/format/). PROPOSAL: use the 2025.10 shape and a small build step (Style Dictionary or a 100-line script) that emits CSS custom properties for the web shells (Tauri/React, Electron/React) and a Rust `const` module for native bits (tray icon colors, overlay window clear color). Pin the token spec version in the repo.

Three tiers, strict one-way references:

1. **Primitive** (`color.teal.700`, `space.4`, `radius.2`, `duration.167`): raw values, no meaning, never used in components.
2. **Semantic** (`color.fg.default`, `color.bg.surface`, `color.accent.default`, `color.status.recording`, `motion.enter`): meaning by role; these are what themes override.
3. **Component** (`wispbar.bg`, `wispbar.radius`, `strip.row.height`, `timeline.playhead.color`): per-component decisions that alias semantic tokens only.

Theme switching = remap semantic tokens under selectors; components never change:

```css
:root { color-scheme: light dark; }
[data-theme="light"] { /* semantic -> light primitives */ }
[data-theme="dark"]  { /* semantic -> dark primitives  */ }
[data-product="side"]   { --color-accent: var(--teal-700); }
[data-product="studio"] { --color-accent: var(--magenta-700); }
[data-product="klaint"] { --color-accent: var(--blue-700); }
[data-theme="dark"][data-product="side"] { --color-accent: var(--teal-300); }
@media (forced-colors: active) { /* map to system colors, see 4.4 */ }
@media (prefers-reduced-motion: reduce) { :root { --motion-scale: 0; } }
```

RTL is not a theme: it is `dir="rtl"` on the root plus logical properties everywhere (`margin-inline-start`, `inset-inline-end`, `padding-block`), and tokens named `inline-start/end`, never `left/right`. Density is a second axis: `[data-density="compact|default|comfortable"]` changes `control.height` and `space.row` only.

Starter token file (DTCG-style, trimmed to the load-bearing set):

```json
{
  "color": {
    "paper": { "0": {"$type":"color","$value":"#FFFFFF"}, "100":{"$value":"#F6F5F0"}, "200":{"$value":"#ECEAE2"}, "300":{"$value":"#D8D5CA"} },
    "ink":   { "500":{"$value":"#7D8890"}, "600":{"$value":"#5F6B73"}, "700":{"$value":"#47525A"}, "900":{"$value":"#14191C"} },
    "night": { "950":{"$value":"#090C0E"}, "900":{"$value":"#0C1013"}, "850":{"$value":"#141A1E"}, "800":{"$value":"#1B232A"},
              "700":{"$value":"#2A353C"}, "500":{"$value":"#76858D"}, "400":{"$value":"#8D999F"}, "300":{"$value":"#A5B0B6"}, "100":{"$value":"#ECEFF0"} },
    "teal":    { "700":{"$value":"#0A766E"}, "300":{"$value":"#3FD6C6"} },
    "magenta": { "700":{"$value":"#B0206B"}, "300":{"$value":"#FF7DB8"} },
    "blue":    { "700":{"$value":"#2E4BCB"}, "300":{"$value":"#8CA5FF"} },
    "green":   { "700":{"$value":"#17703A"}, "300":{"$value":"#4FD18B"} },
    "amber":   { "700":{"$value":"#8A5A00"}, "300":{"$value":"#F2B84B"} },
    "red":     { "700":{"$value":"#B3261E"}, "300":{"$value":"#FF8D84"} },
    "rec":     { "700":{"$value":"#C0201C"}, "300":{"$value":"#FF6A61"} }
  },
  "semantic": {
    "light": {
      "bg": {"canvas":{"$value":"{color.paper.100}"}, "surface":{"$value":"{color.paper.0}"}, "sunken":{"$value":"{color.paper.200}"}},
      "fg": {"default":{"$value":"{color.ink.900}"}, "muted":{"$value":"{color.ink.700}"}, "subtle":{"$value":"{color.ink.600}"}},
      "border": {"default":{"$value":"{color.paper.300}"}, "strong":{"$value":"{color.ink.500}"}},
      "status": {"success":{"$value":"{color.green.700}"}, "warning":{"$value":"{color.amber.700}"}, "danger":{"$value":"{color.red.700}"}, "recording":{"$value":"{color.rec.700}"}}
    },
    "dark": {
      "bg": {"canvas":{"$value":"{color.night.900}"}, "surface":{"$value":"{color.night.850}"}, "raised":{"$value":"{color.night.800}"}, "sunken":{"$value":"{color.night.950}"}},
      "fg": {"default":{"$value":"{color.night.100}"}, "muted":{"$value":"{color.night.300}"}, "subtle":{"$value":"{color.night.400}"}},
      "border": {"default":{"$value":"{color.night.700}"}, "strong":{"$value":"{color.night.500}"}},
      "status": {"success":{"$value":"{color.green.300}"}, "warning":{"$value":"{color.amber.300}"}, "danger":{"$value":"{color.red.300}"}, "recording":{"$value":"{color.rec.300}"}}
    }
  },
  "duration": {"instant":{"$type":"duration","$value":"0ms"}, "fast":{"$value":"83ms"}, "base":{"$value":"167ms"}, "moderate":{"$value":"250ms"}, "slow":{"$value":"333ms"}, "breath":{"$value":"2400ms"}},
  "easing": {"enter":{"$type":"cubicBezier","$value":[0,0,0,1]}, "exit":{"$value":[1,0,1,1]}, "standard":{"$value":[0.2,0,0,1]}}
}
```

### 4.4 Color strategy (light, dark, high contrast) with computed contrast

Light = warm "paper" (not pure white canvas: `#F6F5F0` canvas, `#FFFFFF` surface). Dark = cool "ink-night" (`#0C1013` canvas). Accents are chosen per theme (700-step in light, 300-step in dark) so the same semantic token passes in both.

COMPUTED contrast (WCAG 2.x ratios):

| Pair (light) | Ratio | Pair (dark) | Ratio |
|---|---|---|---|
| fg.default on canvas | 16.23 | fg.default on canvas | 16.53 |
| fg.muted on canvas | 7.34 | fg.muted on surface | 7.93 |
| fg.subtle on canvas | 5.01 (on surface 5.47) | fg.subtle on raised | 5.44 |
| accent teal / magenta / blue on canvas | 5.02 / 5.89 / 6.44 | accent teal / magenta / blue on surface | 9.73 / 7.42 / 7.47 |
| success / warning / danger / recording on surface | 6.15 / 5.93 / 6.54 / 6.06 | same on surface | 9.05 / 9.81 / 7.85 / 6.26 |
| border.strong on canvas (non-text, needs 3) | 3.32 | border.strong on raised (non-text, needs 3) | 4.17 |
| label (#FFFFFF) on filled accent teal / magenta / blue | 5.48 / 6.43 / 7.04 | label (#06100F) on filled accent teal / magenta / blue | 10.70 / 8.15 / 8.21 |

Rules:
- Text needs 4.5:1 (large text 3:1); UI component boundaries and state graphics need 3:1: WCAG 1.4.3 and 1.4.11, both AA. DOCUMENTED (https://www.w3.org/TR/WCAG22/; levels confirmed in the section 2.2 of this report).
- Accent colors are for brand, primary buttons, selection and focus only. Status colors are fixed across products.
- **Open design decision, "what color is listening?"** The state-machine research in section 2.5 recommends the product accent (teal) for WisprSide's *listening* state and not red, because red reads as error and a loud pill contradicts "disappears when not needed". `color.status.recording` (red) is therefore reserved for audio that is being stored or leaves the device: Studio record-arm, Klaint call recording, and (an idea to test, not a decision) a 6 px dot on the wisp bar while cloud recognition is active. Listening is carried by shape (filled mic + level wisp) and the word "Listening", with color as the fourth channel. Test both variants in the section 5.6 usability protocol (task WS-T1) before locking.
- Focus ring (WCAG 2.4.7 focus visible, AA): two-tone, 2 px `fg.default` outline plus 2 px `bg.surface` halo, so it reads on any backdrop; never removed, never the only cue of selection.
- **High contrast:** under `forced-colors: active` the browser overrides authored colors with system colors; map by role rather than fighting it: text `CanvasText` on `Canvas`, interactive `ButtonText`/`ButtonFace`, selected `Highlight`/`HighlightText`, disabled `GrayText`, links `LinkText`. Replace shadows and fills that carry meaning with borders; keep icons `currentColor`; use `forced-color-adjust: none` only for the waveform canvas, where the line color must stay legible (use `CanvasText`). `box-shadow` and `text-shadow` are forced to none, so the wisp bar needs a real 1 px border. DOCUMENTED (https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/forced-colors, https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/forced-color-adjust). Legacy `-ms-high-contrast` is removed from Edge 138+. DOCUMENTED (https://blogs.windows.com/msedgedev/2025/06/30/removing-ms-high-contrast-and-embracing-standards-based-forced-colors-in-microsoft-edge/).
- Windows 11 materials: main windows may use Mica (falls back to solid when unfocused or when transparency is off), transient flyouts may use Acrylic; do not paint opaque backgrounds over a backdrop. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/design/style/mica). Both shells expose it (see 7.6). PROPOSAL: Mica only on the WisprSide settings window and WisprStudio shell (never Klaint, where flat paper reduces glare in long sessions: a design judgment, not a documented finding); the tokens must work when the backdrop is absent.
- Windows contrast themes, Windows 11 test path: Settings > Accessibility > Contrast themes. DOCUMENTED per the Microsoft Edge blog (https://blogs.windows.com/msedgedev/2020/09/17/styling-for-windows-high-contrast-with-new-standards-for-forced-colors/; read via search summary, not fetched in full); verify on a real device.

### 4.5 Type scale, spacing, radius, elevation

**Type (px / line-height).** Windows 11's own ramp is Caption 12/16, Body 14/20, Body Large 18/24, Subtitle 20/28, Title 28/36, Title Large 40/52, Display 68/92 in effective pixels, with Segoe UI Variable as the system font. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/typography). Wispral uses the same anchors so it feels native on Windows, with a script-aware second column:

| Role | Latin | Arabic (PROPOSAL) | Use |
|---|---|---|---|
| `text.micro` | 11/14, uppercase tracking +0.04em, only for 3-letter units (REC, ms) | not used (no uppercase in Arabic; floor 12) | meters, units |
| `text.caption` | 12/16 | 13/22 | helper text, timestamps |
| `text.body-sm` | 13/20 | 14/24 | dense tables (Klaint) |
| `text.body` | 14/20 | 15/26 | default UI |
| `text.body-lg` | 16/24 | 17/28 | onboarding, editor body |
| `text.subtitle` | 20/28 | 21/34 | section titles |
| `text.title` | 28/36 | 29/44 | page titles |
| `text.display` | 40/52 | 41/60 | onboarding hero only |

- Arabic needs more height than Latin at the same nominal size, so the Arabic column is one px larger with a looser line-height: PROPOSAL, to be confirmed by a reading test in section 5; see the section 3 for font-specific metrics and any documented guidance.
- **Never apply `letter-spacing` to Arabic text.** The current CSS Text draft says user agents may not be able to space cursive scripts without breaking connections and tells authors to avoid it; MDN says spaced Arabic "may lead to the text looking broken". DOCUMENTED (https://www.w3.org/TR/2026/CRD-css-text-3-20260814/, https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/letter-spacing). Token rule: `letter-spacing` tokens are Latin-only and are zeroed under `:lang(ar)`.
- Numerals: `font-variant-numeric: tabular-nums` for timers, timecodes, counters (Studio timecode and Klaint durations also in a monospace face).
- Font families: see the font-pairing recommendations in the section 3 of this report; the token names are `font.family.ui`, `font.family.mono`, `font.family.arabic-ui`, `font.family.arabic-editor`.

**Spacing.** 4 px base. Scale: `space.0` 0, `1` 2, `2` 4, `3` 6, `4` 8, `5` 12, `6` 16, `7` 20, `8` 24, `9` 32, `10` 40, `11` 48, `12` 64. Control heights: compact 28, default 32, comfortable 40, touch 44. No interactive target below 24x24 CSS px (WCAG 2.5.8, AA, with its spacing exception); the compact density floor is 28 so there is margin. DOCUMENTED for the 24 px criterion (https://www.w3.org/TR/WCAG22/#target-size-minimum; confirmed in the section 2.2).

**Radius.** Windows 11 geometry: 8 px top-level containers and overlays (`OverlayCornerRadius`), 4 px in-page controls (`ControlCornerRadius`), tooltips 4 px, bars (progress, scroll, slider) 4 px, straight joins square, snapped or maximized windows square. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/geometry). Tokens: `radius.0` 0, `radius.1` 2 (Klaint strips), `radius.2` 4, `radius.3` 8, `radius.4` 12 (Studio panels), `radius.pill` 9999 (wisp bar only). The OS rounds top-level windows; Win32 opt-in is via DWM. DOCUMENTED (same page).

**Elevation.** Flat-first: hierarchy comes from tone steps and 1 px borders, not shadows.
| Level | Use | Light | Dark |
|---|---|---|---|
| `elev.0` | canvas, tables | border `border.default` | border `border.default` |
| `elev.1` | cards, panels (rare) | `bg.surface` + border | `bg.surface` + border |
| `elev.2` | menus, popovers, wisp bar | shadow `0 4px 16px rgb(20 25 28 / .14)` + 1 px border | `bg.raised` + 1 px `border.strong`, shadow `0 4px 16px rgb(0 0 0 / .5)` |
| `elev.3` | modal dialogs | shadow `0 12px 40px rgb(20 25 28 / .22)` + scrim | `bg.raised` + scrim 60% |
Shadows are disabled under forced colors, so every elevated surface also carries a border (see above).

### 4.6 Motion language

Principle: motion explains state change; it never decorates and never delays feedback. Durations and curves are borrowed from documented systems so they feel at home on Windows:
- Fluent/Windows reference durations: 167, 250 and 333 ms for entrances and point-to-point moves, 167 ms for exits, 83 ms for opacity fades. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/design/motion/timing-and-easing).
- Fluent curves: Fast Out Slow In `cubic-bezier(0,0,0,1)` for entering, Slow Out Fast In `cubic-bezier(1,0,1,1)` for exiting; Material 3 standard `cubic-bezier(0.2,0,0,1)`, standard decelerate `(0,0,0,1)`, standard accelerate `(0.3,0,1,1)`; M3's own note says its easing-and-duration system is the legacy system, still used for transitions. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/design/motion/timing-and-easing, https://m3.material.io/styles/motion/easing-and-duration/tokens-specs).

| Token | Value | Use |
|---|---|---|
| `duration.instant` | 0 ms | any keyboard-triggered or high-frequency action; the first frame of every state change |
| `duration.fast` | 83 ms | opacity fades, hover/press feedback |
| `duration.base` | 167 ms | small transforms, popover enter/exit, wisp bar appear |
| `duration.moderate` | 250 ms | panel slide, inspector open |
| `duration.slow` | 333 ms | onboarding step change; the longest anything gets in WisprSide and Klaint |
| `duration.breath` | 2400 ms | the one ambient cycle: the listening halo (opacity 0.55 to 1, scale 1 to 1.04) |
| `easing.enter` | `cubic-bezier(0,0,0,1)` | enter, expand |
| `easing.exit` | `cubic-bezier(0.3,0,1,1)` (M3 accelerate; gentler than Fluent's `(1,0,1,1)`) | exit, collapse; use Fluent's value if you want the stricter Windows feel |
| `easing.standard` | `cubic-bezier(0.2,0,0,1)` | transitions between steady states |
| `easing.linear` | linear | progress fills, level meters only |

Rules:
1. **State first, motion second.** The recording indicator's state change is painted on the first frame (`duration.instant`); only halo and fade are animated. This keeps the indicator inside the latency budget in section 5.
2. **Waveform/level motion is data, not animation:** it follows the audio level at display rate while a session is live; it is absent when idle.
3. **Reduced motion:** honor `prefers-reduced-motion: reduce` (on Windows 11 this is driven by Settings > Accessibility > Visual effects > Animation effects, inverted: off means reduce) plus an in-app "Reduce motion" override. DOCUMENTED (https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion, https://web.dev/articles/prefers-reduced-motion). Under reduce: all transforms to 0 ms; keep an opacity crossfade of at most 83 ms; replace the breathing halo with a static ring plus the text "Listening"; render the waveform as a stepped level meter updated at 4 Hz or less. (Exact mapping from the OS toggle to the media query inside WebView2 is NOT_VERIFIED; test it.)
4. No flashing: nothing flashes more than three times per second (WCAG 2.3.1, Level A). The breath cycle is about 0.4 Hz. The criterion level is from the section 2.2 (https://www.w3.org/TR/WCAG22/).
5. Moving content that auto-starts and lasts over five seconds needs a pause/stop/hide mechanism (WCAG 2.2.2, Level A) unless it is essential; whether a live level meter counts as essential is a judgment call. PROPOSAL: treat it as essential while a session is live, and provide a "Static indicator" setting anyway.
6. No parallax, no spring overshoot on utility surfaces, no animated number counters, no skeleton shimmer (use a static placeholder after 300 ms).

### 4.7 Iconography

- **Primary UI set: Lucide**, ISC license (Feather-derived icons also carry MIT). DOCUMENTED (https://github.com/lucide-icons/lucide/blob/main/LICENSE). Consistent 24 px / 2 px-stroke grid, tree-shakeable React package; its stroke weight matches the wisp line (set stroke to 1.5 px at 16-20 px sizes).
- **Windows-native feel and RTL metadata: Fluent System Icons**, MIT. The repo's README documents a per-icon direction property: `unique` (separate LTR and RTL versions) or `mirror` (can be mirrored). DOCUMENTED (https://github.com/microsoft/fluentui-system-icons). Use it as the reference list for which glyphs mirror (see the section 3) and as a fallback where Lucide lacks a glyph.
- **Onboarding and empty states: Phosphor** (six weights including duotone), MIT. DOCUMENTED for the license (https://github.com/phosphor-icons/core/blob/main/LICENSE); weight inventory NOT_VERIFIED here.
- **Custom "wisp" glyph family (about 24 icons):** mic states (idle, listening, muted, blocked), insert-caret, handoff, whisper/barge-in, policy-hit, take-over, plus tray icon variants. Drawn on the same 24 px grid so they sit with Lucide. Tray icons ship 16 and 32 px with a monochrome-safe silhouette because the notification area expects both sizes. DOCUMENTED for sizes (https://learn.microsoft.com/en-us/windows/win32/shell/notification-area).
- Material Symbols (Apache 2.0) is not adopted, to avoid a second visual dialect. (License claim not fetched: NOT_VERIFIED.)
- Rules: icon + text label for every destructive or mode-changing action; icon-only buttons need an accessible name and a tooltip; directional icons mirror under RTL, media transport and timelines do not (see the section 3 for the cited rule); status icons are shape-distinct (circle, triangle, square, diamond), never recolored copies of one shape.

### 4.8 Sound design for start/stop cues (accessibility-first)

All cues are non-verbal (language- and direction-neutral), short, and optional; the visual and assistive-technology channels always exist, so a Deaf or hard-of-hearing user loses nothing, and the audio channel exists for blind and low-vision users and for anyone looking away from the screen.

| Cue | Contour | Length (PROPOSAL) | Notes |
|---|---|---|---|
| start | two rising soft sine/triangle notes | about 140 ms | played before capture opens |
| stop | two falling notes | about 110 ms | played after capture closes |
| cancel | single low soft tick | about 60 ms | distinct from stop by contour AND length, never by pitch alone |
| error / not-inserted | two short low pulses with a duller timbre | about 90 ms each | pairs with the "Not inserted" chip |

- Cues must not be recorded into the dictation: play the start cue before opening the capture stream and the stop cue after closing it, or subtract it. PROPOSAL. Whether Bluetooth headsets add latency or switch profiles when capture opens is a known practical issue that I did not verify against a primary source: NOT_VERIFIED. Test with a real headset in section 5.
- Short cues are outside WCAG 1.4.2 (Audio Control, Level A), which concerns audio that plays automatically for more than 3 seconds. DOCUMENTED (https://www.w3.org/WAI/WCAG22/Understanding/audio-control.html). Do not add ambient or "thinking" audio.
- Settings: cue set on/off, volume (never above the system alert level by default), "also vibrate" is n/a on desktop. Screen-reader users should hear the assistive-technology announcement (see section 2) rather than depending on the cue.
- The default is ON at low volume during the first week, then a one-time prompt "Keep sounds?" (PROPOSAL). Rationale: an audible confirmation that the microphone is open or closed is a privacy aid, and the OS microphone indicators are not always visible.

### 4.9 Component inventory

**WisprSide (companion):** tray icon with five state variants; tray flyout (quick toggles: microphone, language, mode, last result); **wisp bar** (floating, non-activating indicator: state glyph, level line, timer, cancel, undo-last); hotkey recorder with live conflict check; microphone picker with live level test; language and dialect picker with numerals option; insertion-mode control (type / paste / clipboard-only) with per-app rules table; vocabulary and snippets editor; local history list (search, copy, delete, retention setting); model manager (size, source, local vs cloud, progress, cancel); permission checklist cards; "Not inserted" recovery chip; onboarding stepper with practice field; update banner; diagnostics export.
**WisprStudio (production):** project library; **timeline** (tracks, clips, ruler, playhead, markers, zoom, snap, waveform lanes); script/transcript editor with word-level sync and speaker labels (bidi-aware); voice browser with preview chips; generation panel (engine, voice, style, speed, pronunciation dictionary); dubbing view (source vs target lanes, alignment handles, duration-fit indicator); properties inspector (right panel, selection-driven); asset bin; mixer (level, mute, solo); render queue and export dialog; engine manager (Python sidecar status, model downloads, GPU/CPU); version snapshots; command palette; rights/consent badge for cloned voices.
**Klaint (operations):** agent fleet board; **policy editor** (rules, tone, guardrails, versioned with side-by-side diff and approval); live sessions wall (state, elapsed, last utterance, policy hits); session detail with turn timeline and tool-call trace; takeover/handoff controls (listen, whisper, barge-in, transfer, return to agent); test lab (scenario library, simulated calls, assertions, regression runs); handoff queue; audit log (append-only view, filters, export); knowledge sources; channels (voice, chat); roles and permissions; alert center and incident banner; quality metrics as strips and sparklines, not tile grids.

Shared: command palette, toast/status region, empty/loading/error templates, settings shell, keyboard-shortcut sheet, locale switcher, density switcher.

### 4.10 Empty, loading, error and disabled states

| State | Rule | Wispral pattern |
|---|---|---|
| Empty | teach, don't decorate: one sentence of what appears here, one primary action, one example | WisprSide history: "Dictations appear here. Hold the shortcut and speak." plus the wisp line drawing; Klaint empty policy list: a template picker, not a blank table |
| Loading | under 100 ms no indicator; 100 ms to 1 s keep layout still (reserved space, no spinner); over 1 s show determinate progress with what is happening; over 10 s offer cancel and keep working | model download = determinate bar with size, rate, and "Cancel" and "Continue in background"; Studio render = queue entry with percent |
| Error | state what happened, the likely cause, one next action; keep user content; announce blocking errors with `role="alert"`, non-blocking with `role="status"` | "Not inserted: Notepad lost focus. [Copy] [Retry in Notepad]"; never a dead end |
| Disabled | keep visible, say why (inline text, not only a tooltip), keep it discoverable by keyboard via `aria-disabled` | "Dub this clip: choose a target language first" |
| Offline / blocked | name the blocker and the fix: `privacy-blocked` indicator + `ms-settings:privacy-microphone` link | see 7.1 |
(Response-time thresholds 0.1 s / 1 s / 10 s are from Nielsen's response-time limits; they are cited in section 5. Inactive components are exempt from the contrast minimum in WCAG 1.4.3 but should still be legible: the exemption is from the WCAG text, not re-fetched here, NOT_VERIFIED beyond the section 2.2.)

### 4.11 Onboarding and permissions education

Patterns (PROPOSAL), one screen per decision, each skippable and resumable, each ends in a *test*, not a lecture:
1. **Promise and privacy in one screen:** what the app does, where audio goes (local model vs cloud), what is stored. No account wall.
2. **Microphone access check (before any OS dialog or settings jump):** on Windows 11 today the toggle is the single "Let desktop apps access your microphone" switch with no per-app prompt (per-app prompts exist only in Insider builds; see 7.1). So the screen performs a live mic probe, shows a level line moving, and if blocked shows "Windows is blocking microphone access for desktop apps" with a button that opens `ms-settings:privacy-microphone`. On macOS the same screen precedes the system prompt (see section 8).
3. **Shortcut:** record the hotkey, run the conflict check, offer the safe default; practice field: "Hold and say hello".
4. **Insert test:** a built-in text field first, then "now try it in Notepad" with a visible success/failure; explain in one line that administrator windows cannot receive text (see 7.4).
5. **Language and numerals:** Arabic, English, mixed; digit style by locale with an override (see the section 3).
6. **Done:** show the tray icon location and how to find it again (Windows 11 may place a new icon in the overflow; no documented API promotes it, so the screen must say where to look). Source for the overflow behavior: community only, NOT_VERIFIED; for the rule that the user chooses which icons show: https://learn.microsoft.com/en-us/windows/win32/shell/notification-area.
Education principles: ask for a permission at the moment of need, with the reason; show the benefit before the ask; never block the whole app behind a denied permission, degrade to "copy to clipboard" mode; make the denied state recoverable from Settings > Permissions with the same probe UI.

### 4.12 How this avoids the generic dashboard look

Anti-patterns banned by rule: gradient hero cards, giant rounded KPI tiles, purple-to-blue gradients, glassmorphism on content, identical card grids, decorative blurs, emoji as icons, centered 3-column marketing layouts inside the app.
Replaced by signature devices: the wisp line; typography-first hierarchy (size, weight, space instead of boxes); tabular **strips** for operational data (Klaint rows: shape glyph, monospace ID, status text, elapsed timer, in a hairline grid with 2 px radius); a timeline-first Studio with the waveform as the largest visual; a Side bar that is a single pill and nothing else; one saturated element per view; a **status glyph set** (live, attention, stopped, handoff) that is shape-coded and mirrors correctly in RTL (symmetric shapes).

### 4.13 Factual check of the adopted direction (Quiet Signal tokens, Plex fonts, Lucide icons)

Scope: facts only (licenses, Arabic coverage, contrast, RTL metadata). The direction itself is not re-derived. Inputs read: `docs/design/WISPRAL_DESIGN_SYSTEM.md`, `docs/design/tokens/wispral.tokens.json`, `docs/design/tokens/check_contrast.mjs`. Findings are ordered by how likely they are to bite.

| # | Claim in the adopted design | Finding | Status |
|---|---|---|---|
| F1 | "Contrast verified, PASS 44/44" | I recomputed with an independent script (WCAG formula, https://www.w3.org/TR/WCAG22/#dfn-contrast-ratio). Every pair the checker declares passes. But the checker tests mostly against `bg.canvas`, so some legal uses fail: **light `text.tertiary` (#6F6B65) on `bg.sunken` (#EEECE8) = 4.49:1** (needs 4.5); **light `accent.wisp` as text on `bg.sunken` = 4.25:1**; **dark `border.strong` (#6F6B65) on `bg.sunken` (#242320) = 2.97:1** (needs 3:1 for a control boundary). Fix: check every text token and every UI token against every background token (cross product), or restrict those tokens to canvas/surface and darken `graphite.500`/`wisp.500` one step. The script's sRGB threshold 0.04045 vs WCAG's 0.03928 makes no practical difference. | COMPUTED (this report) |
| F2 | `border.default` as a quiet divider | #E3E0DA on #FBFAF8 is 1.26:1 (light) and 1.34:1 (dark). That is fine for decoration, but WCAG 1.4.11 needs 3:1 for the boundary of an input or any control that is not otherwise identifiable, so inputs and buttons must use `border.strong` (5.07:1 light, 3.51:1 dark on canvas). Encode this as a rule in the token docs. | COMPUTED; rule from https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html |
| F3 | State colors carry meaning (live, danger, attention, Studio accent) | `state.live.solid` (coral) vs `state.danger.solid` (red) differ by only 1.33:1 (light) and 1.08:1 (dark); `state.attention.solid` (amber) vs the Studio accent differ by 1.49:1. They cannot be told apart by color, so shape plus text must always accompany them (WCAG 1.4.1, see section 2.2 and the state machine in 2.5). | COMPUTED; criterion DOCUMENTED (https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) |
| F4 | IBM Plex Sans, Plex Sans Arabic, Plex Mono are SIL OFL | Confirmed: Google Fonts mirrors carry `OFL.txt` for all three and the IBM/plex README says the family follows the Open Font License. DOCUMENTED (https://github.com/IBM/plex, https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexsansarabic/OFL.txt, https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexmono/OFL.txt). | DOCUMENTED |
| F5 | (not mentioned) **Reserved Font Name "Plex"** | The `OFL.txt` of Plex Sans Arabic and Plex Mono both begin "Copyright 2017 IBM Corp. with Reserved Font Name 'Plex'" (the same file pattern applies to Plex Sans; not fetched separately). Under the OFL FAQ, removing glyphs when delivering a font (subsetting) counts as a modification, and WOFF2 conversion is in most cases treated as a modification too; a Modified Version may not use the Reserved Font Name. Practical rule: bundle the upstream files exactly as published, with `OFL.txt` and copyright intact; if the build pipeline subsets or re-encodes them, rename the result (for example "Wispral Sans") and do not call it "IBM Plex ..." in CSS or UI. Not legal advice; confirm with SIL guidance before release. DOCUMENTED (https://openfontlicense.org/ofl-faq/, https://openfontlicense.org/webfonts-and-reserved-font-names/). | DOCUMENTED |
| F6 | "Plex Sans + Plex Sans Arabic were designed together as one superfamily, so weights, x-height and rhythm match across scripts" | **Not confirmed by any source I could read.** The IBM/plex README lists "IBM Plex Sans Arabic" as one of the packages but says nothing about cross-script x-height or rhythm matching; Google Fonts' description only claims readability. Glyph-level metrics were not measured. The planned rendering harness (DS-01) is the right gate; do not repeat the superfamily claim in docs until measured. DOCUMENTED for the listing (https://github.com/IBM/plex); the harmonization claim is NOT_VERIFIED. | NOT_VERIFIED |
| F7 | Arabic coverage of the stack `IBM Plex Sans, IBM Plex Sans Arabic, ...` | Plex Sans (Latin) on Google Fonts has **no Arabic subset** (subsets: cyrillic, cyrillic-ext, greek, latin, latin-ext, vietnamese), so Arabic comes only from Plex Sans Arabic by per-glyph fallback, which is what the stack does. DOCUMENTED (https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexsans/METADATA.pb). Plex Sans Arabic lists Latin subsets (latin, latin-ext, cyrillic-ext), so Latin runs inside Arabic-only strings still render. Tashkeel (U+064B-0652) coverage and Arabic-Indic digit glyphs (U+0660-0669) in Plex Sans Arabic: NOT_VERIFIED; test with real vocalized text in DS-01. For comparison my local check found Segoe UI has all of them. | DOCUMENTED / NOT_VERIFIED as marked |
| F8 | Font formats and weights | Plex Sans on Google Fonts is a variable font (axes `wdth` 75-100 and `wght` 100-700); Plex Sans Arabic is 7 static weights 100-700 (not variable). Weight steps will not be continuous across scripts, and bundle weight grows with static files (size not measured). DOCUMENTED (https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexsans/METADATA.pb; static weights per section 3.4). | DOCUMENTED; size NOT_VERIFIED |
| F9 | Mono stack `IBM Plex Mono, Cascadia Mono, ui-monospace, monospace` for transcripts, logs, ids | No source states that Plex Mono covers Arabic (README silent), and the stack contains no Arabic-capable family, so Arabic inside a mono context falls back to whatever the OS picks. Add "IBM Plex Sans Arabic" (or Noto Sans Arabic) before the generic `monospace`, and keep code, ids and URLs in an LTR isolate (section 3.3). Cascadia Mono Arabic coverage: NOT_VERIFIED. | NOT_VERIFIED |
| F10 | `Segoe UI Variable` listed as the platform fallback | Segoe UI Variable has no Arabic glyphs (my local fontTools check: 0 of 256 code points in U+0600-06FF); Windows would fall through to Segoe UI, which does cover Arabic and Microsoft names as the Arabic UI font. List "Segoe UI" explicitly after "Segoe UI Variable" so the fallback is deterministic. LOCAL CHECK in section 3.4; Microsoft's note: https://learn.microsoft.com/en-us/windows/apps/design/globalizing/loc-international-fonts. | LOCAL CHECK |
| F11 | Lucide, ISC license | Confirmed: Lucide is ISC; icons derived from Feather also carry the MIT license (Cole Bemis), so the third-party notice file must include both texts. DOCUMENTED (https://github.com/lucide-icons/lucide/blob/main/LICENSE). | DOCUMENTED |
| F12 | DS-03 "icon set with mirror metadata" | I found **no official Lucide RTL or mirror metadata**; third-party projects flip icons themselves with CSS, and a Lucide issue asks for logical (start/end) icons with unknown status. Wispral will have to author the `mirror: true/false/variant` list. A usable starting reference is the per-icon `directionType` (`unique` or `mirror`) in Microsoft's Fluent System Icons (MIT). DOCUMENTED (https://github.com/lucide-icons/lucide/issues/3415, https://github.com/microsoft/fluentui-system-icons). Media transport and waveform stay unmirrored (section 3.1). | NOT_VERIFIED (no official Lucide RTL support found) |
| F13 | Custom glyphs drawn "with 1.5 px strokes" beside Lucide | Lucide's default stroke width is not stated on the pages I read; I believe it is 2 px on a 24 px grid. If so, 1.5 px custom glyphs will look lighter than Lucide next to them unless Lucide is rendered at stroke width 1.5 globally. | NOT_VERIFIED |
| F14 | Arabic gets "+2 px line-height at body sizes" | Within the range other sources suggest (Arabic needs more vertical room for dots and tashkeel; Apple advises roughly +10% size or +2 pt beside all-caps Latin; WCAG 1.4.12 requires layouts to survive 1.5x line-height). No numeric Arabic standard exists in the sources I read, so +2 px stays a starting value for DS-01. | NOT_VERIFIED as a numeric rule |
| F15 | Studio timeline does not mirror | Consistent with documented guidance: Material 1 and Microsoft's bidi guidance treat media controls and media timelines as non-mirrored; Apple HIG is silent on timelines. DOCUMENTED (https://m1.material.io/usability/bidirectionality.html, https://learn.microsoft.com/en-us/windows/apps/design/globalizing/design-for-bidi-text). | DOCUMENTED |
| F16 | Numerals "default by locale" | Correct approach, with one trap: under CLDR 48 (observed through Node/ICU on this PC) bare `ar` resolves to **Latin** digits while `ar-SA` and `ar-EG` resolve to Arabic-Indic, so the default must key off the full locale (language plus region), not the language alone. Local observation; other ICU/CLDR versions NOT_VERIFIED. See section 3.2. | LOCAL CHECK |
| F17 | Windows contrast-theme mapping includes `Mark` | The adopted token file maps `state.danger.solid` to the CSS system color `Mark` under forced colors. I did not verify that `Mark`/`MarkText` are honored as intended in WebView2/Chromium forced-colors mode; test in a real Windows contrast theme. | NOT_VERIFIED |

Overall: no license blocker found. The two items that need action before release are the Reserved Font Name handling (F5) and the missing cross-surface contrast checks (F1, F2); the two claims to drop or measure are the "superfamily" harmonization (F6) and the assumption of official Lucide RTL metadata (F12).

## 5. Design-review method


Pipeline (PROPOSAL): capture matrix, independent heuristic review, accessibility audit, latency measurement, moderated usability test; defects go to one severity-rated backlog.

### 5.1 Screenshot capture across OS/theme/locale

Documented facts
- Snipping Tool: Win+Shift+S (image), Win+Shift+R (video); rectangle, window, full-screen, freeform; a 1-5 s delay captures menus, tooltips and flyouts; Windows 11 auto-saves to a Screenshots folder; Print Screen copies the full screen. DOCUMENTED(https://support.microsoft.com/en-us/windows/use-snipping-tool-to-capture-screenshots-00246869-1843-655f-f220-97299b865f6b).
- Contrast themes toggle with Left Alt+Left Shift+Print Screen; test all four. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/accessibility/high-contrast-themes). Also verify DPI/scale changes. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-testing).
- Playwright emulates locale, timezoneId, colorScheme, forcedColors, reducedMotion, contrast, viewport, deviceScaleFactor. DOCUMENTED(https://playwright.dev/docs/emulation). Baselines are per browser and platform and rendering varies with OS, browser version, hardware and headless mode, so compare in the environment that made the baseline. DOCUMENTED(https://playwright.dev/docs/test-snapshots).
- Playwright drives WebView2 via CDP (remote-debugging port in WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS, connectOverCDP, one WEBVIEW2_USER_DATA_FOLDER per parallel test). DOCUMENTED(https://playwright.dev/docs/webview2). Edge WebDriver can launch or attach, must match the WebView2 runtime version, and does not automate native UI. DOCUMENTED(https://learn.microsoft.com/en-us/microsoft-edge/webview2/how-to/webdriver).
- Tauri: use WebdriverIO with @wdio/tauri-service; embedded server covers macOS; direct tauri-driver is Windows and Linux only. DOCUMENTED(https://v2.tauri.app/develop/tests/webdriver/).
- WebView2 CapturePreview captures the WebView's content and fails before the first ContentLoading event. DOCUMENTED(https://learn.microsoft.com/en-us/microsoft-edge/webview2/reference/win32/icorewebview2).
- WebView2 hosting: windowed hosting can hit DPI issues when apps with different DPI awareness share a user-data folder; Window-to-Visual hosting improves DPI/input; Visual hosting needs manual scaling and input routing. DOCUMENTED(https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/windowed-vs-visual-hosting). Default background supports only opaque or fully transparent, with a startup white-flash caveat. DOCUMENTED(https://learn.microsoft.com/en-us/microsoft-edge/webview2/reference/win32/icorewebview2controller2) (search summary).

Inference (NOT_VERIFIED): page-level screenshots (Playwright/CapturePreview) show web content, not shell surfaces (tray, Mica, notifications, title bar). Use OS-level capture for those.

PROPOSAL: capture matrix
- Axes: theme (light, dark, 4 contrast themes); locale (en-US LTR, ar RTL, plus a second Arabic region for numeral choice); scale (100, 125, 150, 200 percent; one mixed-DPI dual-monitor rig); transparency off; animations off; text scale 200 percent.
- Surfaces/states: WS indicator (idle, listening, processing, inserted, error, permission denied, offline), tray icon and flyout, settings; ST editor with stale/locked/regenerating blocks; KL live list, detail, alert.
- Full factorial is too big: all states at default theme/locale/scale, then pairwise combinations, plus corners (dark+ar+200 percent, each contrast theme+ar, mixed DPI).
- File name surface_state_osbuild_theme_locale_scale.png. WebView content via Playwright; shell surfaces via Snipping Tool with delay or a debug hotkey that freezes indicator state. Review each shot against the 10 heuristics and H5/H6.

### 5.2 Heuristic review rubric

Documented: NN/g's 10 heuristics are broad rules of thumb, not specific guidelines (1994, reviewed 2024): visibility of system status; match with the real world; user control and freedom; consistency and standards; error prevention; recognition over recall; flexibility and efficiency; aesthetic and minimalist design; help recognize, diagnose and recover from errors; help and documentation. DOCUMENTED(https://www.nngroup.com/articles/ten-usability-heuristics/). Method: 3-5 independent evaluators, about 1-2 hours each, consolidate afterward; it complements but cannot replace user research. DOCUMENTED(https://www.nngroup.com/articles/how-to-conduct-a-heuristic-evaluation/). Severity 0-4 (cosmetic, minor, major, catastrophe) rated independently; averaging about three raters is practical. DOCUMENTED(https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/).

PROPOSAL: Wispral probes per heuristic
1 Status: mic-live state always visible and truthful; processing visible by 1 s.
2 Real world: Arabic and English terms reviewed by native speakers.
3 Control: Esc cancels; every state has an exit; undo for block regeneration.
4 Consistency: one shortcut map; same state names in tray, indicator, screen-reader text.
5 Prevention: hotkey conflict validation; confirm only unexpected irreversible loss.
6 Recognition: shortcuts shown in menus and the tray flyout.
7 Efficiency: command menu, per-block overrides, expert shortcuts that do not hide the beginner path.
8 Minimalism: WS "disappears when not needed" yet stays discoverable.
9 Errors: plain-language cause plus next action (Retry, Open mic settings).
10 Help: in-context, searchable, bilingual.
Add two criteria: RTL/bidi correctness; calm non-interruption (W2).

### 5.3 Accessibility audit tools

- Accessibility Insights for Windows: FastPass (under 5 minutes; automated checks for 60+ requirements; guided tab-stops test), Live Inspect (UIA properties on hover or focus), Troubleshooting (control patterns, event recording, contrast checker). DOCUMENTED(https://accessibilityinsights.io/docs/windows/overview/). Microsoft prefers it over the legacy SDK tools and recommends CI automation plus manual screen-reader checks, failing builds on critical issues with tracked exemptions. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-testing).
- axe-core (Deque): finds about 57 percent of WCAG issues automatically on average; flags uncertain items "incomplete" for human review; covers WCAG 2.0/2.1/2.2; color-contrast fails under JSDOM. DOCUMENTED(https://github.com/dequelabs/axe-core). Run it via @axe-core/playwright (AxeBuilder); automation cannot catch everything. DOCUMENTED(https://playwright.dev/docs/accessibility-testing). It sees only DOM inside the WebView; native shell surfaces need Accessibility Insights/UIA.
- Status without focus: WCAG 4.1.3 (AA) requires status messages (results, busy state, progress, errors) to be programmatically determinable without moving focus. DOCUMENTED(https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html). For a native floating window, UiaRaiseNotificationEvent (Windows 10 1709+) raises announcements, and a WS_POPUP window must implement the Window pattern and handle WM_GETOBJECT. DOCUMENTED(https://learn.microsoft.com/en-us/windows/win32/api/uiautomationcoreapi/nf-uiautomationcoreapi-uiaraisenotificationevent). How ARIA live regions inside WebView2 map to Narrator/NVDA speech: NOT_VERIFIED; test both.
- Narrator: start Win+Ctrl+Enter; check name, state and type per control; Caps Lock+Enter invokes; Caps Lock+Shift+Enter searches the app's controls; Ctrl+Caps Lock+F12 developer mode masks the screen and highlights exposed objects. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-testing). Narrator key is Caps Lock or Insert; +X repeats the last phrase; +Alt+X opens speech recap (last 500 strings). DOCUMENTED(https://support.microsoft.com/en-us/windows/complete-guide-to-narrator-e4397a0d-ef4f-b386-d8ae-c172f109bdb1).
- NVDA: modifier Insert (or Caps Lock); Ctrl+Alt+N starts; NVDA+Tab reports focus; NVDA+T title; NVDA+S cycles speech modes; NVDA+X repeats last speech. DOCUMENTED(https://download.nvaccess.org/documentation/userGuide.html). Navigator object: NVDA+numpad5 (laptop NVDA+Shift+O) reports current; numpad4/6 previous/next. DOCUMENTED(https://www.nvaccess.org/files/nvda/documentation/keyCommands.html) (search summary). Speech Viewer is enabled from the Tools item of the NVDA menu. DOCUMENTED(https://download.nvaccess.org/releases/2026.2/documentation/userGuide.html) (search summary).

#### PROPOSAL: manual NVDA + Narrator script for a dictation-state indicator
Run once with NVDA and once with Narrator (never both). Targets: Notepad and a WebView text field; UI language English then Arabic. Log speech via NVDA Speech Viewer and Narrator speech recap.
1. Idle: reach the tray icon by keyboard (a shortcut for this is NOT_VERIFIED; use the mouse if needed). Expect name plus state, for example "app name, idle". Enter opens the flyout; Esc closes it and returns focus.
2. Hold the dictation hotkey in the target field. Expect "listening" (or an earcon) announced once; focus stays in the target (NVDA+Tab / Narrator reading focus). Record announcement delay.
3. Speak 10+ s. Expect no repeated announcements (no level-meter chatter) and no screen-reader speech picked up by the mic (risk is my hypothesis; use headphones or earcons and verify).
4. Release. Expect "processing" once, politely, then inserted text readable by caret navigation; no double reading; focus unchanged.
5. Repeat, press Esc while listening. Expect "cancelled", indicator gone, nothing inserted.
6. Cause an error (block mic or go offline). Expect an interrupting plain-language error with keyboard-reachable Retry/Open settings; no auto-dismiss before it can be read.
7. Reach the indicator through NVDA navigator keys or Narrator Caps Lock+arrows. Expect correct name, role, state, Arabic text, sensible RTL order.
8. Enable a contrast theme and disable animations. States stay distinguishable without color.
9. Pass: each state change announced once; focus never stolen; every action keyboard-reachable; strings correct in both languages.

### 5.4 Latency budgets: documented references

- Nielsen response times: about 0.1 s feels instantaneous; about 1 s keeps the train of thought, and beyond it a working indicator is needed; about 10 s is the attention limit and needs progress plus cancel; 2-10 s favors subtle indicators over a percent-done bar. DOCUMENTED(https://www.nngroup.com/articles/response-times-3-important-limits/) (1993 excerpt, 2014 update).
- RAIL: visible response within about 100 ms, input handlers under 50 ms; frame work about 10 ms (16 ms total at 60 fps); idle chunks of 50 ms or less; load targets 5 s and 2 s. The page now recommends Core Web Vitals over RAIL. DOCUMENTED(https://web.dev/articles/rail).
- INP: good is 200 ms or less, poor above 500 ms, at the 75th percentile of field loads; covers click, tap, key press, not hover or scroll; web-specific. DOCUMENTED(https://web.dev/articles/inp).
- Doherty threshold: a 400 ms response target from Doherty and Thadani (IBM Systems Journal, 1982), per a secondary summary; original paper not fetched. DOCUMENTED(https://lawsofux.com/doherty-threshold/).
- Windows motion durations: 83 ms fade, 167/250/333 ms entrances, 167 ms exits. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/motion).
- Wispr Flow: a quick second press right after starting cancels instead of inserting DOCUMENTED(https://docs.wisprflow.ai/articles/6409258247-starting-your-first-dictation); the exact half-second figure is NOT_VERIFIED (search summary, page unconfirmed).
- Gap: none of these defines a dictation-specific threshold. Any such norm is NOT_VERIFIED.

### 5.5 PROPOSAL: Wispral latency budgets (not documented)

Measure p50/p95 on reference mid-range hardware, warm and cold, using in-app timestamps plus high-speed camera for hotkey-to-pixel. Fail the build when p95 exceeds the hard limit.

WisprSide
- WS-1 Hotkey down to mic capturing and "listening" painted: p50 60 ms, p95 100 ms, fail above 150 ms. Why: 0.1 s feels instant (NN/g); RAIL 100 ms with 50 ms handlers; users speak immediately, and the indicator must not claim live before the mic is.
- WS-2 Stop (key up or end of speech) to "processing" painted: p95 100 ms. Why: same; NN/g wants a working indicator by 1 s.
- WS-3 Esc to idle, capture stopped, nothing inserted: p95 100 ms.
- WS-4 End of speech to text in field (speech up to 10 s, warm): p50 1.0 s, p95 2.5 s. Past 10 s show progress, cancel, and keep the transcript. Why: 1 s preserves flow, 10 s is the attention limit (NN/g). Doherty's 400 ms is aspirational, likely unreachable with cloud recognition plus cleanup.
- WS-5 Text ready to inserted (clipboard restore or UIA path): p95 150 ms. Why: RAIL 100 ms, INP 200 ms ceiling.
- WS-6 State animation 83-167 ms; suppress states shorter than 150 ms rather than flashing. Why: Windows motion durations; Win32 guide says do not flash or change status too often.
- WS-7 UIA notification within 100 ms of the visual change; screen-reader speech starts within 500 ms (no source).
- WS-8 Login to hotkey active 2 s (weak analog: RAIL repeat load); prewarmed window opens in 100 ms (Raycast documents prewarming; number is mine).

WisprStudio
- ST-1 Play/pause/seek on cached audio: 100 ms. ST-2 Keystroke to paint in the script editor: p95 50 ms (RAIL handler budget; INP 200 ms ceiling).
- ST-3 Edit marks the block stale: 100 ms (stale marking is documented in Dubbing/Voiceover Studio; budget is mine).
- ST-4 Regenerate: busy state 100 ms; per-block progress after 2 s; percent/ETA plus cancel after 10 s (NN/g).
- ST-5 Timeline pan, zoom, scrub: 60 fps, about 10 ms script work per frame (RAIL, with its status caveat).

Klaint
- KL-1 Command menu open and filter-as-you-type: 100 ms each.
- KL-2 Control action (pause, take over): optimistic acknowledgement 100 ms, authoritative confirmation within 1 s, else visible pending state, timeout error by 10 s.
- KL-3 Live transcript row appears within 1 s of the event; show "stale since" when no data for 5 s (5 s is mine).
- KL-4 Filter/sort on 10k rows: 200 ms (INP "good"). KL-5 Alert visible within 2 s of trigger (no source).

### 5.6 PROPOSAL: usability test protocol

Participants (documented): test about 5 per distinct user group, minimum 3 per group; iterate in rounds (three rounds of 5 beat one of 15); the 5-user model (31 percent of problems per user, about 85 percent with five) assumes a typical L and is qualitative; use at least 20 for metrics studies. DOCUMENTED(https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/; https://www.nngroup.com/articles/how-many-test-users/). Caveats: five users find problems, they do not give statistics; multiple distinct groups need more (documented); whether product complexity lowers the 31 percent figure is NOT_VERIFIED.
PROPOSAL: WS groups = Arabic-primary, English-primary, bilingual code-switchers, screen-reader users (round 1: 3 each, then 5 each after fixes). ST = solo creators and audio professionals (5 each). KL = support/ops leads (5) plus configuration admins (3-5). Include an NVDA user in every WS round.

Method. Moderated, one participant at a time. Scenario tasks state a goal and context, ask for action not explanation, and avoid interface labels. DOCUMENTED(https://www.nngroup.com/articles/task-scenarios-usability-testing/). Think-aloud is highly valuable but unnatural, slows tasks, invites facilitator bias and is not statistical; keep the facilitator quiet, prompt "keep talking", avoid leading, note biased moments. DOCUMENTED(https://www.nngroup.com/articles/thinking-aloud-the-1-usability-tool/; https://www.nngroup.com/articles/success-rate-the-simplest-usability-metric/). NN/g suggests retrospective techniques when think-aloud fails for experts. DOCUMENTED(https://www.nngroup.com/videos/when-thinking-aloud-fails/) (search summary). Ask permission before recording. DOCUMENTED(https://www.nngroup.com/articles/usability-checklist/) (search summary).
PROPOSAL: dictation uses the participant's voice, so run WS tasks with retrospective think-aloud (narrate a screen recording afterward) and take timings only from runs without narration.

Metrics: task success in four levels (complete, minor issue, major issue, failure), reported with word labels, not averaged numbers; small tests rarely give tight confidence intervals. DOCUMENTED(https://www.nngroup.com/articles/success-rate-the-simplest-usability-metric/). Add error counts by type, NN/g 0-4 severity (about three independent raters), time-on-task only without narration, and a 1-7 confidence rating per task. That article gives no pass benchmark, so any release gate is mine, for example no open severity 3-4 problems and 4 of 5 unaided completions per task.

Tasks (8)
WS-T1 First run. "You just installed the app. Get to where you can dictate a two-sentence reply in Arabic into the message box you have open." Watch permissions, hotkey, mic test, where they look for status. Success: first insertion unaided.
WS-T2 Mixed language. "Dictate a note in Arabic that includes an English product name and a phone number." Success: correct direction, digits intact, no cursor jumps, in an RTL and an LTR field.
WS-T3 Recovery. "Partway through dictating you realize it is the wrong window. Stop without inserting anything, then dictate in the right window. Later the indicator is gone; get it back." Success: no stray insertion; finds cancel and restore.
ST-T1 Per-block voices. "Make a three-paragraph voiceover with a narrator and a character; change only the character's voice afterward." Success: per-block binding and stale/regenerate understood.
ST-T2 Arabic correction and takes. "Import this Arabic script, fix one word's pronunciation, keep the version you like, and be able to return to an earlier attempt." Tests RTL editing, take history.
ST-T3 Mix and review. "Add music, start the voice two seconds later, export a final WAV and a no-music version, and share a link for comments." Tests arrangement versus generation, export, review.
KL-T1 Live intervention. "A customer call is going badly. Find it in the live list, tell me what the agent last said, and take over." Tests triage, presence, control acknowledgement.
KL-T2 View and alert. "Find yesterday's conversations where the Arabic voice agent failed to understand the caller, save that view for your team, and get alerted if it recurs." Tests filters, saved views, alerts, RTL tables.

Session (45-60 min): consent and recording permission; warm-up; one scenario card at a time; minimal prompts; post-task rating; debrief; pilot first. Log screen, audio and app latency traces to match perceived to measured delay.


---


# PART B — Platform and distribution facts

Conventions: `DOCUMENTED (url)` = stated on that primary source when fetched on 2026-11-08. `NOT_VERIFIED` = could not confirm from a primary source (often inference, forum reports, or vendor material). `PROPOSAL` = my recommendation, not a documented fact. `COMPUTED` = I calculated it locally with a reproducible script. Microsoft Learn pages carry `updated_at` stamps in their front matter; those dates are quoted where they matter.

---

## 6. Windows code signing, installers and distribution in 2026

### 6.1 Azure Artifact Signing (formerly Trusted Signing)

| Fact | Status |
|---|---|
| The service was renamed. Microsoft's current docs say "Artifact Signing (formerly Trusted Signing)". | DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation) |
| It is a managed signing service. The certificate is never given to you; keys stay in FIPS 140-3 Level 3 HSMs; "digest signing" means the file never leaves your endpoint. No USB token needed; works from CI (GitHub Actions, Azure DevOps, SignTool). | DOCUMENTED (https://learn.microsoft.com/en-us/azure/artifact-signing/overview, https://learn.microsoft.com/en-us/azure/artifact-signing/faq) |
| Two SKUs: Basic (5,000 signatures/month, 1 profile of each type) and Premium (100,000 signatures/month, 10 of each type). | DOCUMENTED (https://azure.microsoft.com/en-us/pricing/details/artifact-signing/) |
| Price: Basic $9.99/month incl. 5,000 signatures, $0.005 per extra signature; Premium $99.99/month incl. 100,000 signatures. The Windows docs say "~$9.99/month". Billing starts when the account is created, is not pro-rated, and is a full month for the SKU. Note: the pricing-details page rendered "$-" for every price in my fetch (prices load dynamically), so the figures come from the product page; re-check in the Azure pricing calculator before budgeting. | DOCUMENTED (https://azure.microsoft.com/en-us/products/artifact-signing, https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options, https://learn.microsoft.com/en-us/azure/artifact-signing/faq) |
| Requires a paid Azure subscription. Free, trial and sponsored subscriptions are not supported. | DOCUMENTED (https://learn.microsoft.com/en-us/azure/artifact-signing/faq) |
| Eligibility for Public Trust certificates (quickstart, updated 2026-10-08): **organizations** in the US, Canada, EU, UK, Australia, New Zealand, Japan, South Korea, Singapore, Switzerland, Norway and Israel; **individual developers must be located in the US or Canada**. Private Trust is not geo-restricted. | DOCUMENTED (https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart) |
| Discrepancy: the "Code signing options" page (updated 2026-08-29) lists the shorter set "organizations: USA, Canada, EU, UK; individuals: USA and Canada". The quickstart is newer and more specific, so treat it as authoritative and confirm in the portal's country drop-down. | DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options) |
| A Microsoft Q&A answer (2026-03-06, labelled AI-generated, no Microsoft staff reply) claims individual onboarding is "paused" and org onboarding needs "3 years of verifiable history". The answer contradicts itself and no primary source backs it. Treat as unverified; ask Azure Support before planning around it. | NOT_VERIFIED (source of the claim: https://learn.microsoft.com/en-us/answers/questions/5810735/cant-create-a-new-trusted-signing-individual-ident) |
| Individual identity validation: billing account of type "Individual"; legal name and sold-to address must match a government ID; Microsoft Entra Verified ID with Face Check via AU10TIX (phone + browser). The certificate shows city, state/province and country; street and email are not included. | DOCUMENTED (https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart) |
| Organization identity validation: 1 to 20 business days (longer if documents requested); three attempts to supply documents; documents must be dated within 12 months; primary email must be on a domain the entity owns. | DOCUMENTED (https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart) |
| No custom CN/O: the certificate subject is the validated legal name. For individuals that means your legal name is the publisher name users see. | DOCUMENTED (https://learn.microsoft.com/en-us/azure/artifact-signing/faq) |
| It does not issue EV certificates and has no plan to. | DOCUMENTED (https://learn.microsoft.com/en-us/azure/artifact-signing/faq) |
| Timestamping: Microsoft runs `timestamp.acs.microsoft.com`; external timestamp services are supported. Certificates are short-lived: the FAQ states three days for anti-malware binaries; the general lifetime is not stated on the pages I read, so timestamping every signature is mandatory in practice. | DOCUMENTED for the endpoint and the 3-day AM case (https://learn.microsoft.com/en-us/azure/artifact-signing/faq); general lifetime NOT_VERIFIED |
| Tauri integration: `signCommand` with `artifact-signing-cli`, env vars `AZURE_CLIENT_ID/SECRET/TENANT_ID`. | DOCUMENTED (https://v2.tauri.app/distribute/sign/windows/) |
| Account regions today include Central US, East US, West Europe, North Europe, Japan East, Korea Central, Brazil South, Poland Central, Switzerland North and several more US regions. | DOCUMENTED (https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart) |

**Implication for Wispral (PROPOSAL):** the publishing legal entity's country decides everything. If the entity (or the individual) sits outside the lists above (the Gulf states, for example, are not on the organization list), Artifact Signing is not available and the options become: an OV certificate from a commercial CA (https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options says USD 150-300/year, HSM or token required since June 2023); Microsoft Store distribution (Store re-signs MSIX for free); or SignPath Foundation if the project is open source. I do not know where the publishing entity will be registered, so this is flagged as an open decision for the master plan.

### 6.2 EV vs OV certificates and SmartScreen

- EV certificates no longer bypass SmartScreen; the behavior was removed in 2024. EV and OV build reputation the same way. Microsoft's own wording: paying the EV premium "solely to avoid SmartScreen warnings is no longer justified". DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation, https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options, https://v2.tauri.app/distribute/sign/windows/).
- Price bands in Microsoft's table: OV about USD 150-300/year, EV USD 400+/year, Artifact Signing about USD 9.99/month. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options).
- SmartScreen weighs two signals: publisher (signing certificate) reputation and file-hash reputation. There is no exact threshold; it can take "several weeks and hundreds of clean installs from a wide audience". A new signed version inherits publisher reputation only if signed with the same publisher identity; changing certificates resets the publisher signal. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).
- There is no mechanism to manually request SmartScreen reputation for consumer endpoints; enterprise admins can submit files to Microsoft Security Intelligence. Tauri's docs say manual review submission "may" grant reputation but is not guaranteed. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation, https://v2.tauri.app/distribute/sign/windows/).
- **What an unsigned installer experiences:** "Windows protected your PC"; the user must click "Run anyway"; enterprise policy can block continuation entirely; self-signed behaves the same. On Windows 11 with Smart App Control, unsigned files are blocked unless they have positive reputation, and the user cannot allow a single app. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation, https://v2.tauri.app/distribute/sign/windows/).
- Microsoft Store apps are never subject to SmartScreen download warnings. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).
- **Source conflict to note:** Electron's code-signing page (as returned by my fetch) says EV has been required since June 2023, that OV "no longer helps", and that Artifact Signing "removes SmartScreen warnings". That conflicts with Microsoft's own pages above. I treat Microsoft Learn as authoritative and mark the Electron phrasing NOT_VERIFIED (https://www.electronjs.org/docs/latest/tutorial/code-signing).
- OV private keys must be on an HSM or hardware token since June 2023. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options). Tauri's OV guide applies only to OV certificates acquired before 1 June 2023. DOCUMENTED (https://v2.tauri.app/distribute/sign/windows/).

### 6.3 Installer formats: NSIS vs MSI vs MSIX

| Topic | Tauri (WisprSide) | Electron (WisprStudio) |
|---|---|---|
| Formats produced | EXE (NSIS `-setup.exe`) and MSI (WiX v3). "Currently Tauri only generates EXE and MSI installers" - no MSIX. DOCUMENTED (https://v2.tauri.app/distribute/microsoft-store/, https://v2.tauri.app/distribute/windows-installer/) | electron-builder has an `msix` target (documented as beta) plus older `appx`; Electron Forge has `@electron-forge/maker-msix` (added in Forge 7.10, experimental, Windows 10/11 + Windows SDK required); Microsoft documents a `winapp` CLI route. DOCUMENTED (https://www.electron.build/docs/msix/, https://www.electronforge.io/config/makers/msix, https://learn.microsoft.com/en-us/windows/apps/dev-tools/winapp-cli/guides/electron-packaging) |
| Install scope | NSIS `installMode`: `currentUser` (default, no admin, installs under `%LOCALAPPDATA%`), `perMachine` (Program Files, admin), `both`. DOCUMENTED (https://v2.tauri.app/distribute/windows-installer/) | NSIS per-user/per-machine via electron-builder (details not fetched). NOT_VERIFIED |
| Build host | MSI only on Windows; NSIS can cross-compile from Linux/macOS but Tauri calls it untested/last resort, and signing then needs an external tool (`signCommand`). DOCUMENTED (https://v2.tauri.app/distribute/windows-installer/, https://v2.tauri.app/distribute/sign/windows/) | MSIX target needs Windows (electron-builder can drive a Windows VM via Parallels from macOS). DOCUMENTED (https://www.electron.build/docs/msix/) |
| Languages | NSIS: one multi-language installer with optional language picker. WiX: one installer per language, default en-US only. DOCUMENTED (https://v2.tauri.app/distribute/windows-installer/) | not fetched. NOT_VERIFIED |
| WebView2 | Five modes; `downloadBootstrapper` default (needs internet), `offlineInstaller` ~127 MB, `fixedVersion` ~180 MB. DOCUMENTED (https://v2.tauri.app/distribute/windows-installer/) | n/a (Electron bundles Chromium) |
| Silent install | NSIS `/S` (uppercase), MSI `/quiet`; the Store rejects installers that do not install silently. DOCUMENTED (https://v2.tauri.app/distribute/microsoft-store/) | n/a |

MSIX facts from Microsoft: if you publish an MSIX through the Store, signing is free and automatic (Microsoft re-signs after certification). If you submit an MSI/EXE to the Store, Microsoft does not re-sign it: you must sign it with a certificate chaining to the Trusted Root Program, and self-signed certificates are rejected. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options).

**PROPOSAL:**
- WisprSide: signed NSIS per-user installer + Tauri updater as the primary channel (fits "disappears when not needed": no admin prompt, silent-capable). Offer a signed MSI later for enterprise (Intune/GPO). Treat the Store as an optional second channel via the "link to your own offline installer" path; native MSIX needs a third-party pipeline (NOT_VERIFIED maturity).
- WisprStudio: NSIS via electron-builder + electron-updater (differential downloads, see 6.6). Add MSIX/Store only after the beta `msix` target stabilizes.
- Important coupling with section 7.4: a per-user install under `%LOCALAPPDATA%` can never obtain `uiAccess` (secure-location rule); a per-machine install can. Decide the install scope together with the elevated-window strategy.

### 6.4 Microsoft Store as a distribution path

- No registration fee for new developers who enter through https://storedeveloper.microsoft.com ("no registration fees for either account type"); individual accounts need a Microsoft account and government ID + selfie verification. Other entry points show the legacy flow. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/publish/partner-center/open-a-developer-account, page updated 2026-10-29).
- Eligibility trap: an **Individual** account is for apps "not in relation to their business, trade, or profession" (hobbyists, non-commercial). A commercial product, even by one freelancer, should use a **Company** account (DUNS number or official business documents; work email on the company's domain; personal Gmail/Yahoo addresses are not supported). Individual-to-Company conversion is not supported. DOCUMENTED (same URL).
- Company account manual review typically 2-5 business days (3-5 for documents). DOCUMENTED (same URL).
- Store benefits for MSIX: no SmartScreen warning; gradual package rollout (a percentage of installed customers; update-only; can be raised or halted, halting does not roll back); package flights for named tester groups. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/publish/gradual-package-rollout, https://learn.microsoft.com/en-us/windows/apps/publish/package-flights).
- Tauri via Store = link to an installer you host (offline WebView2, signed, silent, self-updating, publisher name different from product name). DOCUMENTED (https://v2.tauri.app/distribute/microsoft-store/).

### 6.5 winget

- WinGet ships as part of App Installer on Windows 11, modern Windows 10 (1809+), and Windows Server 2025. Supported installer formats include EXE, MSI, WIX, INNO, NULLSOFT, BURN, MSIX/APPX, ZIP, PORTABLE, FONT. DOCUMENTED (https://learn.microsoft.com/en-us/windows/package-manager/winget/).
- Community repo: `microsoft/winget-pkgs` via manifest PRs (`wingetcreate` automates). Manifests need `InstallerUrl` + `InstallerSha256`; "All tools must support a silent install"; one PR per package version. DOCUMENTED (https://learn.microsoft.com/en-us/windows/package-manager/package/manifest).
- Whether winget-pkgs requires a signed installer: not an official rule I could find. Contributor reports say unsigned installers are accepted but face stricter Defender/URL-reputation validation and may go to manual review. NOT_VERIFIED (contributor PR threads in https://github.com/microsoft/winget-pkgs).
- PROPOSAL: publish both installers to winget after the first signed release; use the stable `PackageName`/`Publisher` that matches Add/Remove Programs so `upgrade` correlates (documented tip in the manifest page).

### 6.6 Updaters

**Tauri updater** (https://v2.tauri.app/plugin/updater/): signatures are mandatory ("cannot be disabled"); keypair via `tauri signer generate`; private key via `TAURI_SIGNING_PRIVATE_KEY` env var (`.env` files do not work); losing the key means you cannot update existing installs; public key goes into `tauri.conf.json`. Static JSON (`version`, per-platform `url` + `signature`; whole file validated, every platform must be complete) or dynamic server (204 when no update). `{{target}}`, `{{arch}}`, `{{current_version}}` URL variables let a dynamic endpoint implement staged rollout. Windows `installMode`: `passive` (default), `basicUi`, `quiet` (only for per-user installs or already-elevated apps). The app exits during install on Windows; use `on_before_exit`. Default rule: install only when version is greater; override `version_comparator` to allow downgrade/rollback with a dynamic server. All DOCUMENTED at that URL. Tauri has no built-in staged rollout (the page documents none); a dynamic server can implement it (inference: NOT_VERIFIED as an official pattern).

**Electron:**
- Built-in `autoUpdater`: macOS (Squirrel.Mac) and Windows only; no Linux support; on Windows it uses the MSIX updater for MSIX packages or Squirrel.Windows otherwise; app must be signed on macOS. DOCUMENTED (https://www.electronjs.org/docs/latest/api/auto-updater).
- `update.electronjs.org` is free but needs a public GitHub repo and GitHub Releases. DOCUMENTED (https://www.electronjs.org/docs/latest/tutorial/updates).
- `electron-updater` (electron-builder): `allowDowngrade` (default false; only meaningful when the channel differs), `disableDifferentialDownload` (NSIS differential downloads exist and use the old blockmap; GitHub hosting needs `previousBlockmapBaseUrlOverride`), staged rollout via a percentage compared to a user ID, overridable with `isUserWithinRollout`. DOCUMENTED (https://www.electron.build/docs/api/electron-updater.Class.AppUpdater).
- See the macOS/Linux/updater notes in section 9 for rollback and release-channel patterns.

---

## 7. Windows desktop integration for a dictation app

### 7.1 Microphone privacy permission for Win32 apps

- Desktop (Win32) apps cannot be toggled individually today: one switch, "Let desktop apps access your microphone", under Settings > Privacy & security > Microphone, with a list of desktop apps Windows detected using the mic. Microsoft warns desktop apps may not appear in the list or may still reach the mic when the setting is off. DOCUMENTED (https://support.microsoft.com/en-us/windows/privacy/windows-camera-microphone-and-privacy).
- Windows Insider Beta build 26220.9836 (released 2026-10-30, Windows 11 25H2 enablement) adds per-app camera/microphone/location control for desktop apps: apps that never accessed the resource prompt on first request; existing decisions are preserved; some apps show as "Unsigned" when Windows cannot verify publisher information. Insider features "might never get released". DOCUMENTED (https://learn.microsoft.com/en-us/windows-insider/release-notes/beta/preview-build-26220-9836). Design consequence (PROPOSAL): code signing now also shapes how trustworthy our app looks inside the privacy UI, and the first-run flow must handle a "denied" state without crashing the capture pipeline.
- Deep link to the page: `ms-settings:privacy-microphone`; Microsoft recommends giving the user a link when your app cannot access a sensitive resource. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/develop/launch/launch-settings).
- Detecting "mic blocked" reliably from a Win32 app (specific error codes from WASAPI when blocked) is not documented in what I read. NOT_VERIFIED. PROPOSAL: run a 200-300 ms "mic probe" at first run and on each "listening failed" event, and show a dedicated `privacy-blocked` indicator state with the settings link.

### 7.2 Global hotkeys: RegisterHotKey vs low-level hooks

| | `RegisterHotKey` | `WH_KEYBOARD_LL` hook |
|---|---|---|
| What it is | System-wide hotkey; `WM_HOTKEY` posted to the registering thread's queue (or a window). DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey) | Intercepts keyboard events before they reach thread input queues. DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/winmsg/about-hooks) |
| Conflicts | Fails if the same keystroke is already registered by another hotkey; some OS default hotkeys (e.g. PrintScreen) may be overridden when your window is foreground. Win-key combinations are "reserved for use by the operating system". F12 is reserved for the debugger. DOCUMENTED (same page) | No conflict check; can swallow keys. Microsoft: hooks slow the system; global hooks cause conflicts with other apps that use the same hook type; use "only when necessary". DOCUMENTED (about-hooks page) |
| Auto-repeat | `MOD_NOREPEAT` suppresses repeat notifications. DOCUMENTED | App must filter repeats itself. NOT_VERIFIED |
| Key-up event | Docs describe only a press notification (`WM_HOTKEY`). Hold-to-talk therefore needs a key-up source (hook or polling `GetAsyncKeyState`). This is my inference from the docs. NOT_VERIFIED | Sees both down and up. NOT_VERIFIED here |
| Callback time limit | n/a | Windows silently drops slow low-level hooks (the `LowLevelHooksTimeout` behavior). I did not fetch the documentation page for this. NOT_VERIFIED |
| Elevated target windows | n/a | Whether a non-elevated LL hook sees keystrokes typed into an elevated window is governed by UIPI; Microsoft states lower-privilege processes cannot install hooks into higher-privilege processes. Exact LL-hook behavior NOT_VERIFIED. |

- Reserved by Windows: `Win+H` opens voice typing; if Voice access is running, `Win+H` does not start a second session. Do not default to Win+H; also avoid `Win+Ctrl+V` (Voice access) style conflicts. DOCUMENTED (https://support.microsoft.com/en-us/accessibility/windows/use-voice-typing-to-talk-instead-of-type-on-your-pc).
- Donor app: Handy (Tauri 2.x) lists `rdev` for global shortcuts and has a `shortcut.rs` module; it pastes through the system clipboard. DOCUMENTED (https://github.com/cjpais/Handy/blob/main/AGENTS.md, https://github.com/cjpais/handy/blob/main/README.md). Which Windows API `rdev` uses (a low-level hook) and whether `tauri-plugin-global-shortcut` maps to `RegisterHotKey` on Windows: NOT_VERIFIED.
- **PROPOSAL:** primary path = `RegisterHotKey` + `MOD_NOREPEAT` for toggle mode (no hook, no antivirus heuristics, no UIPI surprises); an opt-in "hold to talk" mode that adds a narrowly scoped LL hook only while the chord is held; conflict detection at registration time with a clear "this shortcut is taken by X" message; never default to Win-key chords; allow a single-modifier or mouse-button trigger only through the opt-in hook path.

### 7.3 Text insertion methods

| Method | How it works | Strengths | Hazards |
|---|---|---|---|
| `SendInput` + `KEYEVENTF_UNICODE` | Each UTF-16 unit goes in `wScan`, `wVk` = 0, one down + one up event; it synthesizes `VK_PACKET`, translated to `WM_CHAR` for the foreground thread. Events in one call are not interleaved with other input. DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-keybdinput, https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput) | No clipboard side effects; works with Arabic and any BMP text; goes to whatever has focus. | Subject to UIPI. Return value does not reveal a UIPI block. "Does not reset the keyboard's current state": keys still held (our own hotkey modifiers) can corrupt the output, so release/wait first. DOCUMENTED (SendInput page). Surrogate pairs (emoji): docs silent; sending the two surrogate units as separate events is the usual approach. NOT_VERIFIED. Apps that ignore `VK_PACKET`: NOT_VERIFIED. Slow for long text. |
| Clipboard + synthesized Ctrl+V | Put text on clipboard, `SendInput` Ctrl+V, restore the old clipboard. | Fast for long text; works where Unicode events do not. | Clobbers user clipboard unless restored; leaks into Windows clipboard history and cloud clipboard. Mitigation: register and set the formats `ExcludeClipboardContentFromMonitorProcessing` (blocks history and sync), or `CanIncludeInClipboardHistory` = 0, or `CanUploadToCloudClipboard` = 0. DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/dataxchg/clipboard-formats). Paste shortcut differs in some terminals (inference) NOT_VERIFIED. Race: target reads clipboard late. Still UIPI-limited because Ctrl+V is synthesized input. |
| UI Automation `ValuePattern.SetValue` | Sets the control's value through the provider. | No keystrokes; works without focus games when supported. | Requires `IsEnabled` and not `IsReadOnly`. Multi-line edit controls do not support ValuePattern; TextPattern cannot set text. DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationvaluepattern-setvalue, https://learn.microsoft.com/en-us/dotnet/framework/ui-automation/ui-automation-support-for-the-edit-control-type). Provider-specific behavior is undocumented: test per framework. Not a general insertion path; best used for detection and verification. |
| Text Services Framework (TSF) text service | Register as a text input processor; use `ITfInsertAtSelection::InsertTextAtSelection` inside an edit session. Windows Speech Recognition used TSF to insert, select and correct dictated text. DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/tsf/text-services-framework, https://learn.microsoft.com/en-us/windows/win32/api/msctf/nf-msctf-itfinsertatselection-inserttextatselection, https://learn.microsoft.com/en-us/archive/msdn-magazine/2007/july/speak-up-support-dictation-with-text-services-framework; the article dates from 2007) | The native-grade path: composition, undo integration, correct caret handling, IME-aware. | Heavy: COM registration, per-app compatibility testing. Not evaluated beyond docs. PROPOSAL: a research spike for v2, not MVP. |

**UI Automation as sensor, not actuator (important):**
- Edit controls holding passwords must set `IsPassword` = true; reading the Value of such a control must fail. DOCUMENTED (https://learn.microsoft.com/en-us/dotnet/framework/ui-automation/ui-automation-support-for-the-edit-control-type).
- Chromium on Windows enables native UIA by default since Chrome 138. DOCUMENTED (https://developer.chrome.com/blog/windows-uia-support-update). Electron keeps accessibility off until it detects assistive technology (Windows) or the app turns it on, so a UIA probe of an Electron/Chromium target (VS Code, Slack, Teams, Discord) may see little unless accessibility is active. DOCUMENTED (https://www.electronjs.org/docs/latest/tutorial/accessibility). Whether our own UIA probe counts as "assistive technology" that switches it on: NOT_VERIFIED.

**PROPOSAL (insertion policy):**
1. At hotkey press: snapshot target identity (7.5) and, when available, UIA focused element (`IsPassword`, `IsEnabled`, `ValuePattern.IsReadOnly`, control type).
2. If `IsPassword` is true or the target is on the secure desktop: do not capture audio into that context; show the `privacy-blocked` state.
3. Short results (under about 200 characters): `SendInput` Unicode, after waiting for modifier release. Long results: clipboard paste with the history-exclusion formats and clipboard restore.
4. After insertion, if a TextPattern is available, read back to verify; on mismatch or UIPI suspicion, keep the text in a "Not inserted: copy / retry" chip rather than silently dropping it.
5. Per-app overrides (terminal, remote desktop, games) stored locally and editable by the user.

### 7.4 UIPI, elevated windows, secure desktop, password fields

- UIPI: input injection is allowed only into windows at equal or lower integrity level. `SendInput` fails when blocked and neither `GetLastError` nor the return value says UIPI was the cause. DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput).
- Same rule for messages and hooks: lower-integrity processes cannot send messages to, or install hooks in, higher-integrity processes. DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-securityoverview).
- `uiAccess="true"` in the manifest lets an app drive higher-integrity windows. Microsoft says to use it only for accessibility applications. It takes effect only when the binary is signed with a certificate chaining to a trusted root, is installed in a secure location (Program Files, Program Files (x86), Windows\System32; the list is not configurable), and the policy "Only elevate UIAccess applications that are installed in secure locations" (on by default) is satisfied. DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-securityoverview, https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/security-policy-settings/user-account-control-only-elevate-uiaccess-applications-that-are-installed-in-secure-locations).
- Secure desktop: UAC prompts default to the secure (Winlogon) desktop so non-SYSTEM processes cannot observe typed input; Windows 10 blocks clipboard access from that desktop. DOCUMENTED (https://learn.microsoft.com/en-us/troubleshoot/windows-client/windows-security/file-system-error-when-pasting-password, https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-gpsb/9ad50fd3-4d8d-4870-9f5b-978ce292b9d8). Forum reports that `OpenInputDesktop` fails with access denied and simulated input has no effect there are consistent with this but are not official documentation. NOT_VERIFIED.
- **PROPOSAL:** (a) before injecting, compare the target process's token integrity level with ours; if higher, do not attempt injection, show "Cannot type into an administrator window" and put the text on the clipboard with a toast. (b) Do not ship `uiAccess` in the MVP: it forces a per-machine, Program Files install and a trusted-root signature, and Microsoft limits it to accessibility apps; revisit as an optional "Accessibility mode" build after the first signed release. (c) Never try to type into UAC, lock screen, or credential dialogs; treat a foreground window on another desktop as `privacy-blocked`.

### 7.5 Target window identity (HWND + PID + process start time)

- Window handles are recycled; `IsWindow` on a handle you did not create can be wrong because the handle could point to a different window. DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-iswindow).
- A process ID is valid until all handles to the process are closed, after which it may be reused. DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/ns-processthreadsapi-process_information).
- The Restart Manager identifies a process uniquely by the pair (process ID, process creation time from `GetProcessTimes`); Raymond Chen explains that opening by ID and then confirming the start times match detects a recycled ID. DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/api/restartmanager/ns-restartmanager-rm_unique_process, https://devblogs.microsoft.com/oldnewthing/20120217-00/).
- **PROPOSAL (identity record captured at hotkey press, verified before insertion):** `{hwnd, threadId, pid, processStartTime(FILETIME), exePath, integrityLevel, uiaRuntimeId?}`; keep the process handle open for the whole dictation so the PID cannot be reused; before inserting require `GetForegroundWindow() == hwnd`, `GetWindowThreadProcessId` still returns the same pid, and `GetProcessTimes` matches. If focus moved, do not type; offer "Insert into <original app>" (re-focus) or "Copy". Whether `uiaRuntimeId` is stable enough is NOT_VERIFIED.
- The floating indicator must not take focus, or the target identity changes under the user. Handy's README reports that its recording overlay can interfere with pasting on Linux/X11 (DOCUMENTED, https://github.com/cjpais/handy/blob/main/README.md). PROPOSAL: Windows overlay windows created non-activating and click-through while idle (`WS_EX_NOACTIVATE`, `WS_EX_TOOLWINDOW`); I did not fetch the Win32 docs for those styles, so treat the flag names as NOT_VERIFIED until checked.

### 7.6 Notification area, materials and high contrast (WisprSide shell)

- Notification-area icons: identify the icon by a registered GUID (preferred since Windows 7); the GUID registration stores the binary's full path, and moving the binary breaks re-adding the icon, so keep the install path stable across updates. Use `NOTIFYICON_VERSION_4` ("better accessibility"); supply 16x16 and 32x32 icons. The user should have the final say on which icons show, be asked before a persistent icon is installed, and be able to remove it from the shortcut menu. DOCUMENTED (https://learn.microsoft.com/en-us/windows/win32/shell/notification-area). Windows 11 overflow ("promotion" of icons) has no documented app API; forum answers only. NOT_VERIFIED. Per-user NSIS installs under `%LOCALAPPDATA%` keep a stable path across Tauri updates (same directory), which supports the GUID rule (inference).
- Mica: base layer for long-lived windows, falls back to a solid color when the window is unfocused or "Transparency effects" is off; never apply a backdrop twice; do not paint opaque backgrounds on top of it. Acrylic is for transient surfaces (flyouts, menus) and is disabled in Battery Saver, Mica is not. DOCUMENTED (https://learn.microsoft.com/en-us/windows/apps/design/style/mica). Both shells expose it: Electron `backgroundMaterial` (`auto`/`none`/`mica`/`acrylic`/`tabbed`, Windows 11 22H2+) DOCUMENTED (https://www.electronjs.org/docs/latest/api/structures/base-window-options); Tauri 2 `windowEffects` with `mica`/`tabbed`/`acrylic` requires a transparent window, first supported effect wins, and Acrylic has poor resize/drag performance on recent Windows 10/11 builds, DOCUMENTED (https://v2.tauri.app/reference/config/, https://docs.rs/tauri/latest/tauri/window/enum.Effect.html).
- High contrast: Windows contrast themes map to the CSS `forced-colors` media feature; use system color keywords; `-ms-high-contrast` is removed from Edge 138+. DOCUMENTED (https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/forced-colors, https://blogs.windows.com/msedgedev/2025/06/30/removing-ms-high-contrast-and-embracing-standards-based-forced-colors-in-microsoft-edge/). No WebView2-specific forced-colors statement found: test in a real contrast theme. NOT_VERIFIED.

## 8. macOS and Linux platform constraints

### 8.1 macOS: notarization and distribution

#### Fee
- Programs page shows "$99 annual membership"; Enterprise Program is $299/year (internal use, irrelevant). The page has no fee-waiver text. DOCUMENTED(https://developer.apple.com/programs/)
- Waiver: only nonprofits, accredited educational institutions, government entities; individuals, sole proprietors and single-person businesses are excluded, as are entities that signed the Paid Applications Agreement or sell digital goods in apps. Otherwise standard fee "99 USD or local equivalent". DOCUMENTED(https://developer.apple.com/support/fee-waiver/)
- Conclusion: a commercial product budgets $99/yr; prices in other regions NOT_VERIFIED. A free Apple account cannot notarize. DOCUMENTED(https://v2.tauri.app/distribute/sign/macos/)

#### Notarization requirements
- Automated scan, not App Review; returns a ticket and publishes it online for Gatekeeper. DOCUMENTED(https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)
- Required: valid signatures on all executables; "Developer ID Application" (or Installer for pkg) certificate, not Mac Distribution/ad hoc/dev certs; Hardened Runtime; secure timestamp; no `get-task-allow`=true; macOS 10.9+ SDK; well-formed entitlements. DOCUMENTED(https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)
- Hardened Runtime must be on to upload; exceptions via entitlements (JIT, unsigned executable memory, DYLD vars, library-validation off). Resource entitlements include audio input, camera, location, contacts, Apple events. DOCUMENTED(https://developer.apple.com/documentation/security/hardened-runtime)
- Account Holder signs with Developer ID; Tauri docs say only the Account Holder can create Developer ID Application certs. DOCUMENTED(https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution, https://v2.tauri.app/distribute/sign/macos/)
- Upload formats: ZIP, UDIF disk image, signed flat pkg (nested items each get a ticket). Tools: `xcrun notarytool submit --wait`, `store-credentials` (app-specific password because of 2FA), `notarytool log`. `altool` rejected since 2023-11-01. DOCUMENTED(https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution, https://developer.apple.com/documentation/security/customizing-the-notarization-workflow)
- CI auth: App Store Connect API key, or Apple ID + app-specific password + team ID. DOCUMENTED(https://v2.tauri.app/distribute/sign/macos/, https://www.electron.build/v26/docs/api/electron-builder.Interface.MacConfiguration)
- Stapling (`xcrun stapler staple`): works on .app, bundle, .dmg, flat .pkg; not on ZIP (staple contents, re-zip) or standalone binaries. Unstapled software works only if Gatekeeper can fetch the ticket online. DOCUMENTED(https://developer.apple.com/documentation/security/customizing-the-notarization-workflow)
- Typical time: most within 5 min, 98% within 15 min; suggested cap 75 notarizations/day. DOCUMENTED(https://developer.apple.com/documentation/security/customizing-the-notarization-workflow)

#### Gatekeeper
- macOS 10.14.5+: software signed with a new Developer ID cert must be notarized; macOS 10.15+: all Developer-ID software built after 2019-06-01. DOCUMENTED(https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)
- Gatekeeper checks the Developer ID signature and, by default in Catalina+, notarization; online checks exclude Apple Account/device identity per Apple. DOCUMENTED(https://support.apple.com/en-us/102445)
- macOS 15 Sequoia: Control-click "Open" override removed for improperly signed/un-notarized software; users must use System Settings > Privacy & Security > "Open Anyway" (Apple news 2024-08-06). DOCUMENTED(https://developer.apple.com/news/?id=saqachfa, https://support.apple.com/en-us/102445). "About an hour" availability and password prompt: search extract only.
- macOS 26 Tahoe: no documented change to notarization/Gatekeeper policy found; Tahoe security notes list Gatekeeper-bypass fixes only. NOT_VERIFIED for Tahoe-specific policy. An unanswered forum report claims notarized .pkg downloads are rejected on 26.3 while .app passes. NOT_VERIFIED
- PROPOSAL: treat un-notarized distribution as a launch blocker for consumers.

#### Tauri v2
- Cert types: "Apple Distribution" (App Store) or "Developer ID Application" (outside); identity in `bundle.macOS.signingIdentity` or `APPLE_SIGNING_IDENTITY`; CI via `APPLE_CERTIFICATE` (base64 .p12) + `APPLE_CERTIFICATE_PASSWORD`. Notarization runs in `tauri build` with API-key vars (`APPLE_API_ISSUER`, `APPLE_API_KEY`, `APPLE_API_KEY_PATH`) or `APPLE_ID`/`APPLE_PASSWORD`/`APPLE_TEAM_ID`; `--skip-stapling` exists; ad-hoc `"-"` identity may still require user approval. DOCUMENTED(https://v2.tauri.app/distribute/sign/macos/)
- Config: `hardenedRuntime` defaults true; `entitlements` path; `infoPlist` merge (also auto-picks `Info.plist` next to config); `minimumSystemVersion` default 10.13. DOCUMENTED(https://v2.tauri.app/reference/config/)
- Put `NSMicrophoneUsageDescription` in `src-tauri/Info.plist`; entitlements in `src-tauri/Entitlements.plist` via `bundle.macOS.entitlements`; localized strings via `<lang>.lproj/InfoPlist.strings`. DOCUMENTED(https://v2.tauri.app/distribute/macos-application-bundle/)
- Signing page does not cover entitlements/hardened runtime; whether a WKWebView app needs any hardened-runtime exception: NOT_VERIFIED.

#### Electron
- Forge uses @electron/osx-sign + @electron/notarize; Squirrel.Mac `autoUpdater`, `safeStorage`, `setLoginItemSettings` need a signed app. DOCUMENTED(https://www.electronjs.org/docs/latest/tutorial/code-signing)
- electron-builder v26: `hardenedRuntime` default true; auto-detects `build/entitlements.mac.plist` and `.inherit.plist`; notarization env sets (API key trio recommended); `extendInfo` for Info.plist keys. DOCUMENTED(https://www.electron.build/v26/docs/api/electron-builder.Interface.MacConfiguration). Exact Electron entitlement set under hardened runtime: NOT_VERIFIED.

### 8.2 macOS: TCC permissions for a dictation app

| Capability | TCC service / Settings pane | Used for | Sandbox-OK? |
|---|---|---|---|
| Microphone | Microphone | recording | yes (+entitlement) |
| Input Monitoring | ListenEvent | listen-only CGEventTap (global/modifier-only keys) | yes (DTS) |
| Post events | PostEvent, shown under Accessibility | CGEvent.post (synthetic Cmd+V/typing) | yes (DTS) |
| Accessibility (AX) | Accessibility | AXUIElement: read focused element, set value | NO |
| Screen Recording | ScreenCapture | only to read other apps' windows | n/a |
| Speech Recognition | SpeechRecognition | only for Apple Speech | n/a |

#### Microphone
- `NSMicrophoneUsageDescription` is required when using microphone APIs. DOCUMENTED(https://developer.apple.com/documentation/bundleresources/information-property-list/nsmicrophoneusagedescription)
- Flow: `AVCaptureDevice.authorizationStatus(for:)`, then `requestAccess(for:)` if `.notDetermined`; the system remembers the answer; user changes it in Settings. DOCUMENTED(https://developer.apple.com/documentation/avfoundation/requesting-authorization-to-capture-and-save-media)
- Plist key AND (on macOS) the audio-input entitlement must exist before requesting access or capturing, otherwise the system terminates the app. DOCUMENTED(https://developer.apple.com/documentation/avfoundation/requesting-authorization-to-capture-and-save-media)
- `com.apple.security.device.audio-input` sits under Hardened Runtime > Resource Access. DOCUMENTED(https://developer.apple.com/documentation/security/hardened-runtime, https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.device.audio-input). A second Apple page, `com.apple.security.device.microphone`, describes the Audio Input checkbox under App Sandbox. DOCUMENTED(https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.device.microphone). Why two names exist: NOT_VERIFIED. PROPOSAL: sign with `…device.audio-input` (named by the AVFoundation article) and test on clean macOS 15/26.
- Electron: `systemPreferences.getMediaAccessStatus('microphone')`, `askForMediaAccess('microphone')` (no dialog if already denied; Settings change needs app restart); Info.plist must define `NSMicrophoneUsageDescription`. DOCUMENTED(https://www.electronjs.org/docs/latest/api/system-preferences)

#### Accessibility
- Apple's AXIsProcessTrusted symbol page was not retrievable; exact semantics (`AXIsProcessTrustedWithOptions` + `kAXTrustedCheckOptionPrompt`) NOT_VERIFIED from Apple docs. Electron wraps it: `isTrustedAccessibilityClient(prompt)`. DOCUMENTED(https://www.electronjs.org/docs/latest/api/system-preferences)
- (DTS) Listening for events does not need "full" Accessibility; ListenEvent and PostEvent are separate TCC services with `CGRequest{Listen,Post}EventAccess` helpers, both sandbox-compatible. PostEvent is displayed under Accessibility (DTS: "super confusing"); service names don't map 1:1 to Settings items. DOCUMENTED(https://developer.apple.com/forums/thread/735204)
- `NSEvent.addGlobalMonitorForEvents` needs Accessibility; `CGEventTap` needs Input Monitoring. DOCUMENTED(https://developer.apple.com/forums/thread/707680)

#### Input Monitoring vs Carbon hotkeys
- (DTS) Three ways to watch keys: CGEventTap, AppKit global monitor, `RegisterEventHotKey`; DTS likes RegisterEventHotKey but can't recommend it (legacy Carbon) and prefers CGEventTap partly for TCC behaviour. CGEventTap: needs Input Monitoring (`CGPreflightListenEventAccess`/`CGRequestListenEventAccess`), sandbox-compatible since 10.15. DOCUMENTED(https://developer.apple.com/forums/thread/735223)
- WWDC19 701 (search extract): listen-only tap needs Input Monitoring, modifying (default) tap needs Accessibility; `IOHIDCheckAccess`/`IOHIDRequestAccess` check/request without a tap. DOCUMENTED(https://developer.apple.com/videos/play/wwdc2019/701/)
- Default-tap creation returns NULL without permission (used by a poster as revocation probe); a user report says revoking Accessibility during an active default tap can hang input and listenOnly avoids it. NOT_VERIFIED (user reports in S17)
- RegisterEventHotKey needs NO TCC permission: no Apple doc/DTS reply states this; DTS only attaches TCC privileges to taps, monitors and PostEvent. NOT_VERIFIED. PROPOSAL: expect no prompt but test on clean macOS 15 and 26 before promising it in onboarding copy.
- Sequoia: hotkeys with only Option or Option+Shift failed with `-9868`; an Apple frameworks engineer said (Sept 2024) it was intentional (anti-keylogging) and (Nov 2024) that macOS 15.2 beta 2 allows them again. DOCUMENTED(https://developer.apple.com/forums/thread/763878). Later user reports of recurrence after unlock: NOT_VERIFIED.
- Tauri `global-hotkey` registers normal keys with Carbon `RegisterEventHotKey` and uses a `CGEventTap` only for media keys. DOCUMENTED(https://raw.githubusercontent.com/tauri-apps/global-hotkey/dev/src/platform_impl/macos/mod.rs). Electron: media keys only register for a trusted accessibility client on macOS. DOCUMENTED(https://www.electronjs.org/docs/latest/api/global-shortcut)
- Plugin handler reports Pressed/Released (needed for push-to-talk). DOCUMENTED(https://v2.tauri.app/plugin/global-shortcut/)
- Inference: modifier-only keys (Fn, right-Option alone) can't be a Carbon hotkey (key+modifiers) and would need a listen-only tap + Input Monitoring. NOT_VERIFIED. PROPOSAL: default to key+modifier combo (Carbon); optional "advanced push-to-talk key" mode requests Input Monitoring just-in-time.

#### Inserting text
- (DTS) `CGEvent.post` uses its own PostEvent privilege (shown under Accessibility), is sandbox-compatible; posting triggers the TCC alert; `CGPreflightPostEventAccess`/`CGRequestPostEventAccess` exist. DOCUMENTED(https://developer.apple.com/forums/thread/789896)
- AXUIElement read/set needs real Accessibility and doesn't work in a sandbox (below). DOCUMENTED(https://developer.apple.com/documentation/security/protecting-user-data-with-app-sandbox, https://developer.apple.com/forums/thread/749494)
- PROPOSAL ladder: (1) AX insert at caret when trusted; (2) pasteboard + synthetic Cmd+V (PostEvent only), restore clipboard; (3) synthetic typing for short text.

#### Screen Recording / Speech Recognition
- `CGPreflightScreenCaptureAccess`/`CGRequestScreenCaptureAccess` exist (macOS 10.15+). DOCUMENTED(https://developer.apple.com/documentation/coregraphics/cgrequestscreencaptureaccess(). Electron `getMediaAccessStatus('screen')`. DOCUMENTED(https://www.electronjs.org/docs/latest/api/system-preferences). A forum answer (search extract) says window titles (`kCGWindowName`) need Screen Recording. NOT_VERIFIED. PROPOSAL: don't request it in v1.
- Using the Speech framework requires `NSSpeechRecognitionUsageDescription` even for on-device mode; omission crashes at `requestAuthorization`. DOCUMENTED(https://developer.apple.com/documentation/bundleresources/information-property-list/nsspeechrecognitionusagedescription). PROPOSAL: don't link Speech.framework unless used.

#### Settings deep links and reset
- `x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility` / `?Privacy_ListenEvent` are used by developers via `NSWorkspace.shared.open`; some panes moved in Sequoia. Only community usage found; Apple's "Supported URL Schemes" page not retrieved. NOT_VERIFIED (S24). `Privacy_Microphone`: NOT_VERIFIED.
- `tccutil reset <SERVICE> [BUNDLE_ID]`; names case-sensitive (`Microphone`); DTS-posted list: Microphone, Accessibility, ListenEvent, PostEvent, ScreenCapture (+AddressBook, AppleEvents, Calendar, Camera, Photos, Reminders…); SpeechRecognition from another list. No official enumeration; DTS warns against reading tcc.db or shipping extraction tricks. DOCUMENTED(https://developer.apple.com/forums/thread/679303, https://developer.apple.com/forums/thread/735204). Omitting bundle ID resets all apps: search extract.
- A helper/child process may not inherit the parent's grant (one user report). NOT_VERIFIED (S23). PROPOSAL: do audio + input in the signed main process; test any helper's TCC identity.
- Permission changes may need relaunch. DOCUMENTED(https://developer.apple.com/forums/thread/735204, https://www.electronjs.org/docs/latest/api/system-preferences)

### 8.3 macOS sandbox implications
- App Sandbox is mandatory for the Mac App Store. DOCUMENTED(https://developer.apple.com/documentation/security/protecting-user-data-with-app-sandbox, https://developer.apple.com/documentation/security/app-sandbox)
- Forbidden in the sandbox: "use of accessibility APIs in assistive apps", Apple Events to arbitrary apps. DOCUMENTED(https://developer.apple.com/documentation/security/protecting-user-data-with-app-sandbox)
- Apple staff: Accessibility API from a sandboxed app is not possible even if the user grants it manually. DOCUMENTED(https://developer.apple.com/forums/thread/749494); DTS: sandbox generally blocks AX APIs. DOCUMENTED(https://developer.apple.com/forums/thread/789896)
- Works in sandbox: CGEventTap (Input Monitoring) and CGEvent.post (PostEvent). DOCUMENTED(https://developer.apple.com/forums/thread/735223, https://developer.apple.com/forums/thread/707680, https://developer.apple.com/forums/thread/789896)
- Sandbox mic: Audio Input under App Sandbox hardware. DOCUMENTED(https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.device.microphone); non-sandboxed notarized apps still need the hardened-runtime audio-input entitlement. DOCUMENTED(https://developer.apple.com/documentation/security/hardened-runtime, https://developer.apple.com/documentation/avfoundation/requesting-authorization-to-capture-and-save-media)
- PROPOSAL: ship WisprSide via Developer ID (non-sandboxed, hardened, notarized) to keep AX focused-element reading and direct insertion. A Mac App Store edition would be reduced (clipboard + synthetic paste, no AX); App Review acceptance of that behaviour NOT_VERIFIED.

### 8.4 Linux: global shortcuts (X11 vs Wayland)
- X11: apps grab keys directly (Electron; Tauri `global-hotkey` uses `XGrabKey` with exact modifier matching, so also grabs with NumLock/CapsLock variants). `global-hotkey` README: Linux "X11 only". DOCUMENTED(https://www.electronjs.org/docs/latest/api/global-shortcut, https://raw.githubusercontent.com/tauri-apps/global-hotkey/dev/src/platform_impl/x11/mod.rs, https://github.com/tauri-apps/global-hotkey)
- Wayland: compositors don't let apps grab keys; Electron uses the `org.freedesktop.portal.GlobalShortcuts` portal. DOCUMENTED(https://www.electronjs.org/docs/latest/api/global-shortcut)
- Portal (v2 documented): `CreateSession`, `BindShortcuts` (id, description, optional preferred trigger; one bind attempt per session), `ListShortcuts`, `ConfigureShortcuts` (v2); signals `Activated`, `Deactivated`, `ShortcutsChanged`; BindShortcuts typically shows a dialog to view/configure. DOCUMENTED(https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.GlobalShortcuts.html). Activated+Deactivated suit push-to-talk (inference). Preferred trigger is only a suggestion; read back the real trigger. DOCUMENTED(https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.GlobalShortcuts.html, https://github.com/tauri-apps/global-hotkey/pull/172)

Status per desktop (late 2026):
- GNOME: GNOME 48 notes: system-wide shortcuts "fully supported", user can edit/revoke. DOCUMENTED(https://release.gnome.org/48/developers/). A GNOME 48 rebind bug fixed in 49, backported to 48.x (PR author text). DOCUMENTED(https://github.com/tauri-apps/global-hotkey/pull/162). Electron: consent dialog on first bind; on GNOME 50.0/50.1 an invalid `desktopName` makes binds silently denied. DOCUMENTED(https://www.electronjs.org/docs/latest/api/global-shortcut)
- KDE Plasma: binds silently, reviewable in System Settings, persisted per portal identity. DOCUMENTED(https://www.electronjs.org/docs/latest/api/global-shortcut). PR #172 text lists Plasma 5.27+; first-supported version NOT_VERIFIED. Older Plasma (<6.4) reportedly re-prompts on each BindShortcuts, fix cherry-picked to Plasma 6.7 branch July 2026 (search extract of KDE bug 523063). NOT_VERIFIED
- Hyprland: supported via xdg-desktop-portal-hyprland; also its own `hyprland_global_shortcuts_v1`. DOCUMENTED(https://github.com/tauri-apps/global-hotkey/pull/172, https://github.com/emersion/xdg-desktop-portal-wlr/issues/240)
- COSMIC: NOT supported. Issue open; 2026-10-24 comment confirms; COSMIC 1.2.0 user got "No such interface"; portal-cosmic 1.6.0 lacked it (2026-09-07); blocked on internal design (2026-03-17). DOCUMENTED(https://github.com/pop-os/xdg-desktop-portal-cosmic/issues/4)
- wlroots/Sway: xdg-desktop-portal-wlr issue #240 still open; an 2026-10-08 comment says a wayland-protocols MR "has been merged" (unnamed) and asks if wlroots must implement it. Which protocol/adoption: NOT_VERIFIED. DOCUMENTED(https://github.com/emersion/xdg-desktop-portal-wlr/issues/240) for issue state.

Tauri global-shortcut on Wayland:
- Plugin docs list Linux but have no Wayland note. DOCUMENTED(https://v2.tauri.app/plugin/global-shortcut/). Crate README: X11 only. DOCUMENTED(https://github.com/tauri-apps/global-hotkey)
- Tauri issue #3578 open, label "status: upstream", last activity Apr 2025, no maintainer reply. DOCUMENTED(https://github.com/tauri-apps/tauri/issues/3578)
- global-hotkey PR #162 (portal via `wl_register_all()`, opened 2025-09-14) open/unmerged; testers: KDE Plasma 6.x, GNOME 49, Flatpak. DOCUMENTED(https://github.com/tauri-apps/global-hotkey/pull/162)
- PR #172 ("Unified Wayland support via XDG GlobalShortcuts portal", opened 2026-03-27) open, no reviews; runtime backend detection with X11 fallback, portal-restart recovery, `trigger_description()`; use `register_all` because on KDE each `register()` rebinds the whole set and re-prompts; limits: curated key table, no left/right modifier distinction, stale UI after user rebinds; COSMIC and wlroots unsupported; maintainer OK with MSRV raise. DOCUMENTED(https://github.com/tauri-apps/global-hotkey/pull/172)
- Conclusion (inference): no released `tauri-plugin-global-shortcut` supports Wayland as of 2026-11-08. NOT_VERIFIED for unreleased branches; third-party apps (Warp) reportedly pin a PR commit. DOCUMENTED(https://github.com/tauri-apps/global-hotkey/pull/172, secondary)
- Prior art, Handy (Tauri dictation app): on Wayland the compositor must own the shortcut; users bind a key to `handy --toggle-transcription` (GNOME/KDE custom shortcuts, Sway/Hyprland bindings) or `pkill -USR2 -n handy`; SIGUSR1 unhandled because WebKitGTK uses it. DOCUMENTED(https://github.com/cjpais/Handy). Issue #949: shortcuts failed on COSMIC/Sway/Hyprland (Mar 2026), closed as known; PR #1560 "add xdg-desktop-portal GlobalShortcuts backend for Wayland" referenced (merge status NOT_VERIFIED). DOCUMENTED(https://github.com/cjpais/Handy/issues/949)
- Electron has native Wayland support via the portal (feature flags `GlobalShortcutsPortal`, `GlobalShortcutsPortalPreferredTrigger` on by default); set `desktopName`/`app.setDesktopName()` to the reverse-DNS ID matching the installed .desktop file; `register()` returns false if taken. DOCUMENTED(https://www.electronjs.org/docs/latest/api/global-shortcut)

### 8.5 Linux: text injection into other apps

| Mechanism | GNOME | KDE | wlroots-family / niri / Hyprland / COSMIC | Needs |
|---|---|---|---|---|
| RemoteDesktop portal (keyboard) | yes (search extract) | yes (search extract) | NOT_VERIFIED | consent dialog, persistable |
| zwp_virtual_keyboard_v1 | NO | NO | yes | compositor-gated |
| zwp_input_method_v2 (IME role) | NO | NO | yes | being the active IME |
| IBus/Fcitx engine | native path | via fcitx/ibus | varies | user activates engine |
| uinput (ydotool/dotool) | works | works | works | /dev/uinput access |
| X11 XTest/xdotool | XWayland only (NOT_VERIFIED) | same | same | X11/XWayland |

- RemoteDesktop portal: CreateSession → SelectDevices → Start; device types keyboard(1)/pointer(2)/touch(4); `NotifyKeyboardKeycode`/`NotifyKeyboardKeysym`; Start shows a consent dialog; v2 adds `persist_mode` (0/1/2, 2 = until revoked) and single-use `restore_token`; `ConnectToEIS` returns a libei fd (recommended; afterwards Notify* calls error). DOCUMENTED(https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html)
- libei: compositor runs the EIS side, can distinguish emulated from real input for access control; clients can't tell them apart once in the input stack; supported-compositor list not on that page. DOCUMENTED(https://libinput.pages.freedesktop.org/libei/). GNOME portal EIS merge and KWin libeis-behind-portal: search extract; first versions NOT_VERIFIED.
- InputCapture portal is not suited: capture only via pointer barriers; "no way … to activate immediate input capture". DOCUMENTED(https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.InputCapture.html)
- `zwp_virtual_keyboard_v1`: supported by Cage, COSMIC, Hyprland, Jay, Labwc, Mango, Mir, niri, phoc, Qtile, river, Sway, Treeland, Wayfire; not by GameScope, KWin, Louvre, Muffin, Mutter, Weston ("wlroots-only" is slightly off, but GNOME and KDE are excluded). Viewer is a community aggregator of protocol XML. DOCUMENTED(https://wayland.app/protocols/virtual-keyboard-unstable-v1)
- `wtype`: "xdotool type for wayland"; keys released on exit because the compositor destroys the virtual keyboard object; README names no protocol/compositors. DOCUMENTED(https://github.com/atx/wtype). Handy README: X11 → xdotool; Wayland → wtype or dotool (`input` group); on Ubuntu 26.04 wtype doesn't work, use ydotool + systemd; fallback enigo (limited on Wayland). DOCUMENTED(https://github.com/cjpais/Handy)
- `ydotool`: kernel uinput; `ydotoold` required since v1.0.0; `/dev/uinput` access "usually requires root"; no layout detection (raw keycodes). DOCUMENTED(https://github.com/ReimuNotMoe/ydotool). Flatpak reaching uinput: NOT_VERIFIED.
- `zwp_input_method_v2`: client acts as IME; `commit_string` inserts at cursor (≤4000 bytes, double-buffered); at most one input method per seat; supported by COSMIC, Hyprland, Jay, Labwc, Mango, Mir, niri, phoc, river, Sway, Treeland; not KWin, Mutter, Muffin, Wayfire, Weston. DOCUMENTED(https://wayland.app/protocols/input-method-unstable-v2). `text-input-v3` (app side): shown for most incl. Mutter and KWin (higher version number); not Cage/GameScope/Louvre/Qtile/Wayfire/Weston; meaning of per-row numbers undefined on page. DOCUMENTED(https://wayland.app/protocols/text-input-unstable-v3)
- Inference: being the IME collides with the user's real IME (one per seat). PROPOSAL: IME route only as optional later phase.
- Fcitx5 wiki: GNOME uses the IBus D-Bus protocol (Fcitx needs its IBus frontend); text-input-v3 used by GTK 3/4 and Qt 6.7+; KWin uses text-input-v1 and input_method_v1; Sway 1.10+ uses input-method-v2; IM state is global under zwp_input_method. DOCUMENTED(https://fcitx-im.org/wiki/Using_Fcitx_5_on_Wayland)
- IBus: engines are separate executables; `ibus_engine_commit_text` sends engine output to the client; surrounding-text get/delete APIs exist. DOCUMENTED(https://ibus.github.io/docs/ibus-1.5/IBusEngine.html). An IBus/Fcitx engine is the "proper" route (compositor routes text to the focused field) but requires it to be the active input source; coexistence with another IME NOT_VERIFIED.
- AT-SPI `EditableText`: `insert_text`, `paste_text`, `set_text_contents` (character offsets). DOCUMENTED(https://docs.gtk.org/atspi2/iface.EditableText.html). Cross-toolkit/Wayland reliability NOT_VERIFIED.
- Clipboard + synthetic paste still needs a key channel; Handy warns paste "might fail or end up in the wrong window" when its overlay holds focus. DOCUMENTED(https://github.com/cjpais/Handy)
- PROPOSAL ladder: X11 → xdotool/XTest; Wayland GNOME/KDE → RemoteDesktop portal (`persist_mode=2`, store `restore_token`, ConnectToEIS), fallback user-configured ydotool; Wayland wlroots-family → wtype/virtual keyboard; optional IBus engine later; last fallback "copy to clipboard + notify".

#### Flatpak
- Mic: `--socket=pulseaudio` (audio incl. mic, /dev/snd; flagged sensitive). Also `--socket=wayland|fallback-x11|x11`, `--device=dri`, `--share=network`, `--device=input|usb|all` (all = wide). Default D-Bus policy lets apps own their namespace and talk to the bus and `org.freedesktop.portal.*`; extra names via `--talk-name`; avoid session/system bus sockets. DOCUMENTED(https://docs.flatpak.org/en/latest/sandbox-permissions.html). Portals (GlobalShortcuts/RemoteDesktop) therefore reachable by default (inference); PR author reports shortcuts working in Flatpak. DOCUMENTED(https://github.com/tauri-apps/global-hotkey/pull/162, secondary)
- Tauri → Flatpak: build a `.deb` and repackage in a manifest on `org.gnome.Platform`/`Sdk`; finish-args `--socket=wayland`, `--socket=fallback-x11`, optional `--device=dri`, `--share=ipc`; tray needs `--talk-name=org.kde.StatusNotifierWatcher`; offline builds need flatpak-node-generator/flatpak-cargo-generator; AppStream metainfo recommended; Flathub PR to `new-pr`. The sample args omit `--socket=pulseaudio` and `--share=network` (PROPOSAL: add both). DOCUMENTED(https://v2.tauri.app/distribute/flatpak/)
- Electron → Flatpak: Freedesktop runtime 24.08, `org.electronjs.Electron2.BaseApp`, `zypak-wrapper`; default permissions include `--socket=x11 --socket=pulseaudio --share=network --device=dri --share=ipc`; X11 default since Electron Wayland is "still experimental" per that page (page freshness NOT_VERIFIED); `desktopName` = Flatpak ID + `.desktop`. DOCUMENTED(https://docs.flatpak.org/en/latest/electron.html)
- Flathub policy on in-app updaters: NOT_VERIFIED.


## 9. Installer/update UX, rollout, rollback

### Delta updates
- electron-updater (docs labelled "next (v27)"): NSIS and macOS zip publish `<artifact>.blockmap`; updater diffs against the installed map and fetches changed ranges via HTTP Range; AppImage embeds its map; map format follows `electronUpdaterCompatibility` (default `>=7` → "v3"); tips `nsis.differentialPackage: "store-asar"`, `asar.contentAlignment: 512`. DOCUMENTED(https://www.electron.build/docs/features/auto-update). v26: `disableDifferentialDownload` (NSIS only, default false). DOCUMENTED(https://www.electron.build/v26/docs/api/electron-updater.Class.AppUpdater)
- Squirrel.Windows: downloads `RELEASES`, picks deltas vs full package (whichever smaller), verifies SHA1, rebuilds the full package from deltas. DOCUMENTED(https://github.com/Squirrel/Squirrel.Windows/blob/develop/docs/using/update-process.md). electron-updater does not support Squirrel.Windows (NSIS only). DOCUMENTED(https://www.electron.build/v26/docs/features/auto-update)
- Electron's built-in `autoUpdater` on macOS supports a `delta` object (Sparkle BinaryDelta); no Windows delta described. DOCUMENTED(https://www.electronjs.org/docs/latest/api/auto-updater)
- MSIX: `AppxBlockMap.xml` has SHA2-256 per 64 KB block; Windows downloads only changed blocks and reuses unchanged files; works between any two versions including older ones. DOCUMENTED(https://learn.microsoft.com/en-us/windows/msix/desktop/managing-your-msix-deployment-update)
- Tauri updater: no delta mechanism on the docs page (full artifact per update). DOCUMENTED(https://v2.tauri.app/plugin/updater/) (absence); absolute "no delta" NOT_VERIFIED.

### Staged rollout
- electron-updater: hand-edit `stagingPercentage` (0-100) into `latest.yml`/`latest-mac.yml`; to withdraw a bad staged release publish a higher version. DOCUMENTED(https://www.electron.build/docs/features/auto-update, https://www.electron.build/v26/docs/features/auto-update). Client stickiness via a locally stored random ID: third-party write-up only (search extract). NOT_VERIFIED
- Electron docs: custom update servers enable percentage rollouts and channels; no built-in mechanism. DOCUMENTED(https://www.electronjs.org/docs/latest/tutorial/updates)
- Microsoft Store: gradual package rollout is for updates, MSIX apps only; set % (e.g., 5), change from Overview without a new submission; Finalize pushes to all, Halt stops distribution but does NOT roll back customers who already got it; OS builds below 10586 get nothing until finalized; 100% alone isn't finalization; must finalize/halt before a new submission; flights target named groups and can combine with rollout. DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/publish/gradual-package-rollout)
- Tauri: updater docs don't mention staged rollout; dynamic server can return 204 or 200 JSON; endpoints/pubkey/target settable at runtime; custom placeholder variables unsupported (custom `target` OK). DOCUMENTED(https://v2.tauri.app/plugin/updater/) → implement server/endpoint-side.
- MSIX App Installer self-hosting: no percentage rollout documented in pages read. NOT_VERIFIED.

### Rollback and downgrade
- Squirrel.Windows: one `app-x.y.z` folder per version; after an update the next startup keeps current + immediately previous; "no built-in support for rolling back". DOCUMENTED(https://github.com/Squirrel/Squirrel.Windows/blob/develop/docs/using/update-process.md, https://github.com/Squirrel/Squirrel.Windows/blob/develop/docs/using/install-process.md)
- electron-updater: `allowDowngrade` (default false) applies only when the channel differs (e.g., beta→stable); setting `channel` in code sets it true; `allowPrerelease` (GitHub only) also enables downgrade. DOCUMENTED(https://www.electron.build/v26/docs/api/electron-updater.Class.AppUpdater). Documented remedy otherwise: publish a higher version. DOCUMENTED(https://www.electron.build/v26/docs/features/auto-update)
- Electron built-in MSIX updater: `allowAnyVersion` permits downgrade. DOCUMENTED(https://www.electronjs.org/docs/latest/api/auto-updater)
- MSIX App Installer: `ForceUpdateFromAnyVersion` allows lower versions (Win10 1903+); downgrade also differential. DOCUMENTED(https://learn.microsoft.com/en-us/windows/msix/app-installer/update-settings; https://learn.microsoft.com/en-us/windows/msix/app-installer/auto-update-and-repair--overview, https://learn.microsoft.com/en-us/windows/msix/desktop/managing-your-msix-deployment-update). Whether MSIX keeps previous files for instant local rollback: NOT_VERIFIED.
- Tauri: default accepts only strictly newer; Rust `version_comparator` overrides (docs example accepts any different version, "useful for rolling back"). DOCUMENTED(https://v2.tauri.app/plugin/updater/). JS `check({allowDowngrades})` (added 2.8.0, 2025-06-16) was moved to plugin config in 2.12.0 (2026-09-20, breaking) because webview code could relax the check. DOCUMENTED(https://v2.tauri.app/release/updater/all-versions/)
- Tauri macOS: updater 2.13.2 (2026-10-07): failed install no longer deletes the installed app (atomic swap or restore). DOCUMENTED(https://v2.tauri.app/release/updater/all-versions/)
- Tauri `requireSignedVersion` (CLI 2.12.0, 2026-09-26): signed trusted comment records the version, so an announced version can't be paired with an older signed artifact; `tauri build` fills it; `tauri plugin add updater` enables it; `signer sign --app-version` for manual signing. DOCUMENTED(https://v2.tauri.app/release/tauri-cli/). It constrains rollback design: a rollback artifact must carry a valid signed version.

### Signature verification
- Tauri: updates must be signed, "cannot be disabled"; `tauri signer generate`; pubkey in `tauri.conf.json`; private key via `TAURI_SIGNING_PRIVATE_KEY`/`_PATH` (+`_PASSWORD`; `.env` not read); losing the private key blocks updates for installed users; TLS enforced (`dangerousInsecureTransportProtocol` overrides). DOCUMENTED(https://v2.tauri.app/plugin/updater/). Scheme is minisign: plugin depends on `minisign-verify` (0.3 since 2.13.3, 2026-10-10, rejects non-canonical Ed25519 S). DOCUMENTED(https://raw.githubusercontent.com/tauri-apps/plugins-workspace/v2/plugins/updater/Cargo.toml, https://v2.tauri.app/release/updater/all-versions/). The docs page itself doesn't name minisign. DOCUMENTED(https://v2.tauri.app/plugin/updater/)
- Keys generated between CLI 2.9.3 and 2.10.0 with empty password were broken; fixed in 2.10.1 (2026-03-04): regenerate. DOCUMENTED(https://v2.tauri.app/release/tauri-cli/)
- electron-updater validates code signatures on macOS and Windows. DOCUMENTED(https://www.electron.build/v26/docs/features/auto-update). NSIS: `verifyUpdateCodeSignature` default true, uses the publisher name; custom verifier `(publisherName: string[], path) => Promise<string|null>`; failure behaviour not stated. DOCUMENTED(https://www.electron.build/v26/docs/api/electron-builder.Interface.WindowsConfiguration, https://www.electron.build/v26/docs/api/electron-updater.Class.NsisUpdater)
- electron-builder v27 NOT released (stable 26.17.0 on 2026-09-25; newest 27.0.0-alpha.14 on 2026-10-28). It adds Ed25519 signed manifests (`updateManifest`, `npx electron-builder create-update-key`, `ELECTRON_BUILDER_UPDATE_SIGN_KEY`); publishing fails without a key unless `updateManifest: false`; apps built before a key existed skip verification; rotation needs a bridge release signed with both keys. DOCUMENTED(https://www.electron.build/docs/features/signed-update-manifests/, https://www.electron.build/changelog, https://www.electron.build/docs/features/auto-update). Alpha notes on stricter `publisherName` checks: search extract. NOT_VERIFIED
- Windows signing options per Electron: Azure Artifact Signing (cheapest, limited country availability), jsign, DigiCert KeyLocker; EV certs need FIPS 140 L2 hardware/cloud since June 2023. DOCUMENTED(https://www.electronjs.org/docs/latest/tutorial/code-signing)

### Install timing
- electron-updater v26: `autoDownload` true; `autoInstallOnAppQuit` true. DOCUMENTED(https://www.electron.build/v26/docs/api/electron-updater.Class.AppUpdater). Next: `autoInstallEvent` = `onQuit` (default) | `onNextLaunch` | `manual`; `onNextLaunch` planned default in v28. DOCUMENTED(https://www.electron.build/docs/features/auto-update, https://www.electron.build/docs/api/electron-updater.Class.AppUpdater)
- Electron `autoUpdater`: `update-downloaded` handling optional (applies next launch); `quitAndInstall()` closes windows then quits; `before-quit-for-update` for cleanup. DOCUMENTED(https://www.electronjs.org/docs/latest/api/auto-updater)
- `update-electron-app` default: check at startup and every ten minutes, background download, restart prompt, update.electronjs.org. DOCUMENTED(https://www.electronjs.org/docs/latest/tutorial/updates)
- Tauri: `check()`, then `download()` and `install()` separately; on Windows the app exits automatically when install starts (`on_before_exit` hook); `installMode` `passive` (default) / `basicUi` / `quiet` (only per-user installs or already elevated; not recommended); macOS/Linux need manual relaunch. DOCUMENTED(https://v2.tauri.app/plugin/updater/, https://v2.tauri.app/reference/javascript/updater/)
- MSIX App Installer: `OnLaunch` (with `ShowPrompt`, `UpdateBlocksActivation`), `AutomaticBackgroundTask` every 8 h without UI, `HoursBetweenUpdateChecks` default 24; non-blocking updates apply silently at an opportune time; in-use packages can fail, force shutdown or defer registration. DOCUMENTED(https://learn.microsoft.com/en-us/windows/msix/app-installer/update-settings; https://learn.microsoft.com/en-us/windows/msix/app-installer/auto-update-and-repair--overview, https://learn.microsoft.com/en-us/windows/msix/desktop/managing-your-msix-deployment-update)
- Detecting an active dictation session before restart: documented nowhere I read; all of it below is PROPOSAL.

### Channels and privacy
- Tauri: runtime `.endpoints()`/`.pubkey()`/`.target()` → channels by URL. DOCUMENTED(https://v2.tauri.app/plugin/updater/). electron-updater: `channel` setter (forces allowDowngrade), `allowPrerelease`; "Release Using Channels" tutorial not read. DOCUMENTED(https://www.electron.build/v26/docs/api/electron-updater.Class.AppUpdater, https://www.electron.build/v26/docs/features/auto-update)
- Tauri check URL can carry `{{current_version}}`, `{{target}}`, `{{arch}}`; custom headers/proxy/timeout configurable; other request content (User-Agent etc.) NOT_VERIFIED. DOCUMENTED(https://v2.tauri.app/plugin/updater/)
- `update-electron-app` defaults to the third-party update.electronjs.org service. DOCUMENTED(https://www.electronjs.org/docs/latest/tutorial/updates). What electron-updater providers log/send: NOT_VERIFIED.
- PROPOSAL: self-hosted static manifests on a CDN with logs off or IP-truncated; no install/account/machine ID in requests; visible "check automatically" toggle + "Check now"; publish exactly what the request contains (version, OS, arch).

### Reference update design (PROPOSAL; documented capabilities only)

### Shared rules
1. Never interrupt a session. State machine IDLE → CHECKING → DOWNLOADING (background) → READY → INSTALLING; INSTALLING only when `dictation_active == false` and audio buffers are flushed. Otherwise stay READY with a passive tray badge.
2. Install moments: user "Restart to update", app quit, next launch before main window, optional idle-N-minutes.
3. Check at launch (after UI ready) + ~24 h with jitter + "Check now"; "pause updates" switch; no 10-minute polling.
4. Channels `stable` (default), `beta` (opt-in), hidden `rollback` used only by the watchdog.
5. Store builds (MSIX/Store, Mac App Store if ever, Flathub): disable in-app updater; use Store gradual rollout/halt for risk (DOCUMENTED(https://learn.microsoft.com/en-us/windows/apps/publish/gradual-package-rollout)).
6. Crash-loop watchdog: on each launch write `{version, started_at, healthy:false}`; set `healthy:true` after health gates (main window ready, audio enumeration OK, hotkey registered or portal bound, ASR backend started) or N stable minutes. After 3 consecutive unhealthy launches of an updater-installed version: pause auto-update, show "Roll back / Send crash report (opt-in) / Continue", fetch the `rollback` target, add the bad version to local `blocked_versions` (no rollback loops).
7. Server kill switch: signed `channel.json` with `min_safe_version` and `blocked_versions`, read in the same request as the update check (no extra telemetry).
8. Default recovery is roll-forward (fixed vX.Y.Z+1); true downgrade is exceptional because of version binding (Tauri `requireSignedVersion`, electron-updater higher-version rule).

### WisprSide (Tauri)
- `tauri-plugin-updater` ≥ 2.13.2 (atomic macOS swap), `createUpdaterArtifacts: true`, `requireSignedVersion` on, `allowDowngrades` off in plugin config; signing key offline/HSM with backup.
- Endpoints per channel, e.g. `https://updates.<domain>/wisprside/{channel}/{{target}}-{{arch}}/{{current_version}}`, returning 204 or signed JSON; channel chosen by runtime `.endpoints()`.
- Staged rollout without telemetry: client draws a random decile 0-9 once, stores it locally, never sends an ID; URL includes the decile (`r0..r9`). Promote = publish the JSON under more deciles; halt = revert those paths to 204. Server learns only "decile".
- Download in background; hold the `Update` handle; call `install()` only in INSTALLING (Windows exits the app: flush audio/log in `on_before_exit`). Windows NSIS `currentUser` (default) + `passive`.
- macOS: notarized + stapled app in a notarized dmg; updater uses `.app.tar.gz` + `.sig`.
- Rollback: `rollback.json` points to the previous good signed artifact; Rust `version_comparator` accepts exactly that version only when `rollback_requested` is true. Behaviour of pre-2.12 signatures (no signed version) when `requireSignedVersion` is on: NOT_VERIFIED.
- Linux: updater supports AppImage/deb/rpm since plugin 2.10.0 (DOCUMENTED(https://v2.tauri.app/release/updater/all-versions/)); deb/rpm updates go through a privileged prompt and manifests need per-format keys (search extract; NOT_VERIFIED); Flatpak/Flathub builds disable updater.

### WisprStudio (Electron)
- electron-builder 26.x + electron-updater; Windows NSIS only; macOS dmg+zip signed + notarized; Linux AppImage (embedded blockmap) ± deb/rpm; Flatpak/Store editions disable updater. DOCUMENTED(https://www.electron.build/docs/features/auto-update, https://www.electron.build/v26/docs/features/auto-update)
- Do not adopt the v27 alpha for production; prepare: generate the Ed25519 update key, plan rotation/bridge release, enable signed manifests when v27 is stable. DOCUMENTED(https://www.electron.build/docs/features/signed-update-manifests/)
- Differential: keep default; trial `nsis.differentialPackage: "store-asar"` + `asar.contentAlignment: 512` (documented on "next" page; v26 NOT_VERIFIED).
- Staged rollout: publish `latest.yml` with `stagingPercentage` 5 → 25 → 50 → 100; withdraw via a higher version containing the revert. DOCUMENTED(https://www.electron.build/docs/features/auto-update, https://www.electron.build/v26/docs/features/auto-update)
- Timing: `autoDownload` true; never `quitAndInstall()` during dictation/export/transcription jobs; rely on `autoInstallOnAppQuit` (v26) / `autoInstallEvent: 'onQuit'` (v27 name) plus a user "Restart to update"; stop the Python sidecar cleanly on `before-quit` (installer file-lock behaviour NOT_VERIFIED).
- Signature: keep `verifyUpdateCodeSignature` true with the exact Authenticode `publisherName`; evaluate Azure Artifact Signing vs EV/KeyLocker. DOCUMENTED(https://www.electronjs.org/docs/latest/tutorial/code-signing, https://www.electron.build/v26/docs/api/electron-builder.Interface.WindowsConfiguration)
- Channels: `beta` via `channel` setter (forces allowDowngrade; use only for beta→stable). DOCUMENTED(https://www.electron.build/v26/docs/api/electron-updater.Class.AppUpdater)
- Rollback: roll-forward; emergency downgrade via a dedicated "stable-rollback" channel feed pointing at the previous binary, relying on channel-change semantics (allowDowngrade applies only when channel differs). DOCUMENTED(https://www.electron.build/v26/docs/api/electron-updater.Class.AppUpdater, https://www.electron.build/v26/docs/features/auto-update) for the semantics; the trick itself is PROPOSAL and needs testing on all three OSes. Re-publishing the same version number leaves users on the broken build. DOCUMENTED(https://www.electron.build/v26/docs/features/auto-update)
- Privacy: generic static host on own CDN; avoid GitHub provider and `update.electronjs.org`; provider list not read. NOT_VERIFIED

### Open items (unresolved)
1. RegisterEventHotKey needs no TCC prompt on clean macOS 15/26 (empirical test).
2. `device.microphone` vs `device.audio-input` for non-sandboxed hardened apps.
3. Tauri updater with pre-2.12 signatures under `requireSignedVersion`; rollback design under it.
4. Electron v26: `differentialPackage`/`contentAlignment`; provider list and request contents.
5. First GNOME/KWin versions with EIS RemoteDesktop keyboard; consent UX with `persist_mode=2`.
6. Which wayland-protocols MR merged ~Oct 2026 (may be a global-shortcut protocol).
7. KDE Plasma minimum version for GlobalShortcuts; COSMIC roadmap.
8. Flathub updater policy; Flatpak access to uinput/keyboard injection.


# Appendix A: Source index for sections 8 and 9

---------------------------------------------------------------------------
S1 https://developer.apple.com/programs/
S2 https://developer.apple.com/support/fee-waiver/
S3 https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution
S4 https://developer.apple.com/documentation/security/customizing-the-notarization-workflow
S5 https://developer.apple.com/documentation/security/hardened-runtime
S6 https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.device.audio-input
S7 https://developer.apple.com/documentation/avfoundation/requesting-authorization-to-capture-and-save-media
S8 https://developer.apple.com/documentation/bundleresources/information-property-list/nsmicrophoneusagedescription
S9 https://developer.apple.com/documentation/bundleresources/information-property-list/nsspeechrecognitionusagedescription
S10 https://developer.apple.com/news/?id=saqachfa
S11 https://support.apple.com/en-us/102445
S12 https://developer.apple.com/documentation/security/protecting-user-data-with-app-sandbox
S13 https://developer.apple.com/documentation/security/app-sandbox
S14 https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.device.microphone
S15 https://developer.apple.com/forums/thread/735223
S16 https://developer.apple.com/forums/thread/707680
S17 https://developer.apple.com/forums/thread/735204
S18 https://developer.apple.com/forums/thread/789896
S19 https://developer.apple.com/forums/thread/749494
S20 https://developer.apple.com/forums/thread/763878
S21 https://developer.apple.com/forums/thread/679303
S22 https://developer.apple.com/videos/play/wwdc2019/701/
S23 https://developer.apple.com/forums/thread/805245
S24 https://developer.apple.com/forums/thread/709289 ; https://developer.apple.com/forums/thread/761193
S25 https://v2.tauri.app/distribute/sign/macos/
S26 https://v2.tauri.app/reference/config/
S27 https://v2.tauri.app/distribute/macos-application-bundle/
S28 https://www.electronjs.org/docs/latest/tutorial/code-signing
S29 https://www.electronjs.org/docs/latest/api/system-preferences
S30 https://www.electron.build/v26/docs/api/electron-builder.Interface.MacConfiguration
S31 https://github.com/tauri-apps/global-hotkey
S32 https://raw.githubusercontent.com/tauri-apps/global-hotkey/dev/src/platform_impl/macos/mod.rs
S33 https://raw.githubusercontent.com/tauri-apps/global-hotkey/dev/src/platform_impl/x11/mod.rs
S34 https://v2.tauri.app/plugin/global-shortcut/
S35 https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.GlobalShortcuts.html
S36 https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html
S36a https://developer.apple.com/documentation/coregraphics/cgrequestscreencaptureaccess()
S37 https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.InputCapture.html
S38 https://release.gnome.org/48/developers/
S39 https://www.electronjs.org/docs/latest/api/global-shortcut
S40 https://github.com/tauri-apps/tauri/issues/3578
S41 https://github.com/tauri-apps/global-hotkey/pull/162
S42 https://github.com/tauri-apps/global-hotkey/pull/172
S43 https://github.com/pop-os/xdg-desktop-portal-cosmic/issues/4
S44 https://github.com/emersion/xdg-desktop-portal-wlr/issues/240
S45 https://wayland.app/protocols/virtual-keyboard-unstable-v1
S46 https://wayland.app/protocols/text-input-unstable-v3
S47 https://wayland.app/protocols/input-method-unstable-v2
S48 https://github.com/atx/wtype
S49 https://github.com/ReimuNotMoe/ydotool
S50 https://libinput.pages.freedesktop.org/libei/
S51 https://docs.flatpak.org/en/latest/sandbox-permissions.html
S52 https://docs.flatpak.org/en/latest/electron.html
S53 https://v2.tauri.app/distribute/flatpak/
S54 https://fcitx-im.org/wiki/Using_Fcitx_5_on_Wayland
S55 https://ibus.github.io/docs/ibus-1.5/IBusEngine.html
S56 https://docs.gtk.org/atspi2/iface.EditableText.html
S57 https://github.com/cjpais/Handy
S58 https://github.com/cjpais/Handy/issues/949
S60 https://www.electron.build/docs/features/auto-update   (labelled "next (v27)")
S61 https://www.electron.build/v26/docs/features/auto-update
S62 https://www.electron.build/v26/docs/api/electron-updater.Class.AppUpdater
S63 https://www.electron.build/docs/api/electron-updater.Class.AppUpdater   (next v27)
S64 https://www.electron.build/v26/docs/api/electron-builder.Interface.WindowsConfiguration
S65 https://www.electron.build/v26/docs/api/electron-updater.Class.NsisUpdater
S66 https://www.electron.build/docs/features/signed-update-manifests/
S67 https://www.electron.build/changelog
S68 https://www.electronjs.org/docs/latest/api/auto-updater
S69 https://www.electronjs.org/docs/latest/tutorial/updates
S70 https://github.com/Squirrel/Squirrel.Windows/blob/develop/docs/using/update-process.md
S71 https://github.com/Squirrel/Squirrel.Windows/blob/develop/docs/using/install-process.md
S72 https://learn.microsoft.com/en-us/windows/msix/desktop/managing-your-msix-deployment-update
S73 https://learn.microsoft.com/en-us/windows/msix/app-installer/update-settings ; https://learn.microsoft.com/en-us/windows/msix/app-installer/auto-update-and-repair--overview
S75 https://learn.microsoft.com/en-us/windows/apps/publish/gradual-package-rollout
S76 https://v2.tauri.app/plugin/updater/
S77 https://v2.tauri.app/release/tauri-cli/
S78 https://v2.tauri.app/release/updater/all-versions/
S79 https://raw.githubusercontent.com/tauri-apps/plugins-workspace/v2/plugins/updater/Cargo.toml
S80 https://v2.tauri.app/reference/javascript/updater/
