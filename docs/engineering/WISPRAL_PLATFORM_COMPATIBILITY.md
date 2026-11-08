# Wispral platform, packaging and distribution strategy

**Status:** CANDIDATE PLAN. No Wispral platform support is claimed; every cell below is `NOT_RUN` until a clean-machine journey passes ([release gates](../strategy/WISPRAL_RELEASE_QUALITY.md)). Facts are `DOCUMENTED` in the [design and platform research report](../../research/wispral-world-class/evidence/research-reports/DESIGN_PLATFORM_RESEARCH.md) (sections 6–9, fetched 2026-11-08, each with its primary-source URL) and in the [WisprSide source research](../../research/wispral-world-class/evidence/research-reports/WISPRSIDE_SOURCE_RESEARCH.md). Prices and eligibility rules change; re-check them before any purchase decision.

## 1. Platform order

| Order | Platform | Products | Why |
| --- | --- | --- | --- |
| 1 | **Windows 11 x64** | WisprSide, WisprStudio | The founder's primary machine (HW-A); the largest desktop share; Handy already builds for `windows-latest` x64 and ARM64 in CI |
| 2 | Linux server (container) | Klaint | Operator-hosted service; WSL2 is available for local development |
| 3 | macOS (Apple Silicon) | WisprSide, WisprStudio | Donors already support it (Handy macOS paths, VoiceStudio Electron); needs a paid Apple Developer membership and notarization |
| 4 | Linux desktop | WisprSide, WisprStudio | Fragmented input stack (X11 versus Wayland compositors) |
| 5 | Mobile | — | Separate research cell; not planned |

## 2. Windows

### 2.1 Packaging

| Product | Format | Notes |
| --- | --- | --- |
| WisprSide | **Per-user NSIS installer** (Tauri default `currentUser`, no admin), plus MSI for managed deployment | Tauri builds NSIS and MSI only; **it cannot produce MSIX**. A Microsoft Store listing would point to the signed installer. Set `webviewInstallMode` deliberately: the Tauri default download bootstrapper needs network access when WebView2 is missing (normally present on Windows 11) |
| WisprStudio | NSIS via electron-builder (donor's existing packaging), with Python engine environments created by the app's per-engine mechanism | Electron MSIX targets are beta/experimental; not used |
| Portable builds | Handy's portable mode (marker file → `Data/`) retained for evaluation builds | — |

### 2.2 Code signing and SmartScreen (honest expectations)

- **Unsigned** installers show "Windows protected your PC", and Smart App Control on Windows 11 can block them outright. No UI design avoids this.
- **EV certificates no longer bypass SmartScreen.** Reputation accrues per file and publisher over time ("several weeks and hundreds of clean installs" in Microsoft's guidance), whatever the certificate type.
- **Azure Artifact Signing** (formerly Trusted Signing) is Microsoft's recommended non-Store route: about USD 9.99/month (Basic), managed HSM keys, works from CI. It requires a **paid** Azure subscription and is available only to organizations in a listed set of regions and to individuals in the US or Canada. Whether the founder's entity qualifies is a **founder decision with cost (R-10)**.
- **Fallbacks:** an OV certificate (roughly USD 150–300/year with a hardware key), or Microsoft Store distribution (free developer account for new sign-ups; a Company account for a commercial product).
- **Private beta (R2)** may ship with a documented warning for invited testers only if the founder accepts that; R3+ requires a signed build (gate G-SIGN).
- Handy's upstream signing command (`trusted-signing-cli … CJ-Signing …`) and updater key/endpoints belong to the upstream author and **must be replaced** (packet WS-M10).

### 2.3 Microphone, hotkeys, insertion

| Topic | Rule |
| --- | --- |
| Microphone permission | Win32 apps follow the Windows privacy setting "Let desktop apps access your microphone". Windows 11 Insider builds are introducing per-app prompts for desktop apps, where unsigned apps show as "Unsigned". Onboarding detects a blocked microphone and deep-links to the setting |
| Hotkeys | `RegisterHotKey` (key-down only) is the robust baseline for toggle; hold-to-talk needs a narrowly scoped low-level hook. Never default to a `Win`-key chord (`Win`+`H` is Windows voice typing) |
| Insertion methods | `SendInput` with `KEYEVENTF_UNICODE` (short text; chunk without splitting surrogate pairs), clipboard paste with the three clipboard-history exclusion formats (long text), UI Automation as a *sensor* for target identity and read-back, not a general writer |
| Elevated targets | UIPI blocks injection into higher-integrity windows **silently**. WisprSide refuses with an explanation. Typing into admin windows would need a `uiAccess` build installed under Program Files with a trusted signature, which conflicts with the per-user install; deferred as an optional "accessibility build" |
| Target identity | `HWND` + PID + process creation time + image path + focused control + UIA runtime ID (runtime IDs can be reused, so never used alone) |
| Tray and materials | Notification-area icon with state glyphs; Mica where available with a solid fallback; forced-colors (high contrast) mapping from tokens |

### 2.4 Updates and rollback

- Tauri updater signatures are mandatory; Wispral generates its own minisign key (custody documented, never in the repo).
- Update checks are **off by default** in WisprSide (Handy's default is on; packet WS-M1) and offered as an explicit action that names the destination.
- Self-hosted static update feeds (GitHub Releases of the Wispral repository, after the founder's green light), staged rollout by cohort, crash-loop watchdog that offers rollback to N-1.
- **An update never interrupts a live dictation, render or session.**

## 3. macOS (later tier)

- Developer ID signing, hardened runtime and notarization; Apple Developer Program at USD 99/year (founder cost). Not the Mac App Store: Accessibility APIs are unavailable in the sandbox.
- Permissions: Microphone; Accessibility (for synthetic paste/typing via posted events); Input Monitoring (for listen-only key taps). Whether `RegisterEventHotKey` avoids a permission prompt is `NOT_VERIFIED`.
- Donor support: Handy and VoiceInk/FreeFlow macOS paths; FreeFlow's `AppTextInsertionCore` is the closest fail-closed macOS insertion design.

## 4. Linux (later tier)

- **Global shortcuts:** X11 works; on Wayland, the `GlobalShortcuts` portal works on GNOME and KDE (and Hyprland per the report), not on COSMIC. Tauri's global-shortcut plugin is still X11-only.
- **Text injection** differs per compositor (portal-based remote desktop, virtual-keyboard protocols, `ydotool`/`wtype`, or an input-method approach). Handy's Linux paths (including its now-fixed `dotool` newline injection issue) are the starting point.
- Support tiers: Tier 1 X11 and GNOME/KDE portals; Tier 2 wlroots family; COSMIC marked unsupported for global shortcuts until its portal exists.
- Packaging: AppImage/deb from the donor pipelines; Flatpak later (in-app updater policy `NOT_VERIFIED`).

## 5. Klaint deployment

- One container stack per tenant on an operator-managed Linux host: Klaint service (Parlant + broker + console), database, optional Chatwoot.
- Images pinned by digest; SBOM per release; migrations reversible or snapshot-guarded; backup/restore tested (gate G-INSTALL for Klaint).
- No public deployment until the founder's explicit green light.

## 6. Model artifact distribution

- Models are downloaded on explicit user action from pinned revisions with SHA-256 verification (Handy already does this, with a bundled offline catalog of 76 models). WisprSide shows the host before download.
- Offline installs: an "offline bundle" (installer plus one permissively licensed default model) is a later packaging option, gated on the model's redistribution terms.
- No model with an unresolved weight license is bundled or offered by default (gate G-RIGHTS).

## 7. Platform qualification cells

| Cell | Evidence required before a support claim |
| --- | --- |
| Windows 11 x64 (Home and Pro), per-user install | G-INSTALL + G-E2E + G-SHOTS + WB-DELIVERY + WB-EGRESS on a clean VM |
| Windows 11 ARM64 | Same, on ARM hardware or a qualified VM (CPU-only build) |
| Windows 10 | Not planned; claim nothing |
| macOS 15+ Apple Silicon | Notarized build + TCC journey + insertion fixtures |
| Ubuntu LTS X11 / GNOME Wayland / KDE Wayland | Per-session-type journey |
| Klaint on Ubuntu LTS (container) | Clean install + backup/restore + tenant isolation suite |
