# WisprSide UX specification

**Status:** CANDIDATE SPEC — nothing built or tested. Applies the [design system](WISPRAL_DESIGN_SYSTEM.md) to the retained Handy fork ([source decision](../../research/wispral-world-class/SOURCE_DECISION_MATRIX.md#wisprside)). Capability IDs (SD-xx) refer to the [product capability catalog](../strategy/WISPRAL_PRODUCT_VISION.md#21-wisprside--intelligent-voice-companion).

**Design priority:** the interface disappears when not needed. Microphone state, privacy, recording status and delivery outcome are unmistakable.

## 1. Surfaces

| Surface | Purpose | Donor starting point | Change |
| --- | --- | --- | --- |
| **Capsule** | The only thing visible during dictation | Handy recording overlay | Re-skin; add the delivery receipt and refusal states; anchored placement rules; screen-reader announcements |
| **Tray icon** | Ambient state + menu | Handy tray | State-specific icon glyphs (idle / live / working / attention); menu: Start dictation, Open panel, Pause WisprSide, Settings, Quit |
| **Quick panel** | Raycast-style surface for history, retry, model and language switching | Handy history window (re-structured) | Summon via shortcut; keyboard-first list; search |
| **Settings** | Configure capture, language and models, output, privacy, shortcuts | Handy settings | Reorganized by intent; searchable; network badges |
| **Onboarding** | First-run setup with live tests | Handy onboarding/permissions | Rewritten flow (§4) |

## 2. The capsule

A pill (`radius.pill`) about 220 × 40 px at 100% scale, placed bottom-center of the active monitor by default, 48 px above the taskbar. Users may pin it near the text caret where the OS exposes caret position, or to any corner. It never takes focus and never covers the caret.

| State | Visual | Text label | Screen reader (UIA notification) | Earcon | Exit |
| --- | --- | --- | --- | --- | --- |
| Hidden (idle) | Nothing on screen; tray glyph idle | — | — | — | Activation |
| **Arming** (model loading) | Capsule appears at once; audio is already captured from key-down into a bounded buffer, so the mic glyph is filled coral and the level meter moves; a working shimmer shows the model is loading | "Listening" (sub-label "getting ready") | "Listening" | Start cue | Model ready → buffered audio is transcribed; Esc → Cancelled. If buffering is impossible (device busy), the capsule shows "Wait…" with an outlined mic and a distinct wait cue, and speech is not accepted until it turns coral |
| **Listening** | Coral `state.live` mic glyph + live level meter driven by input level; elapsed time | "Listening" (PTT: "Release to finish") | "Listening" | Start cue | Release / toggle → Transcribing; Esc → Cancelled |
| **Transcribing** | Lagoon `state.working` progress; mic glyph off | "Transcribing" | — (avoid chatter) | Stop cue | Result → Delivering; error → Error |
| **Delivering** | Brief; target app icon appears | "Inserting into Notepad" | — | — | Outcome |
| **Delivered** (receipt) | Green check + target app icon + window title (direction-isolated, then truncated); shown for at least 3 s plus 0.5 s per 20 title characters (max 8 s); stays while hovered or while a screen reader is running | "Inserted into ‹Notepad — notes.txt›" + **Undo insert** while the target is unchanged and the method supports verified reversal (UI Automation value restore); otherwise **Show where it went** | "Inserted into Notepad. Press the last-outcome shortcut to undo or review." | — | Fade; tray tooltip and accessible name keep "Last: inserted into Notepad" until the next dictation |
| **Refused** | Amber `state.attention`; capsule **expands** to the action layout (§2.1); text kept | "Window changed — text kept" + **Insert into Notepad** · **Copy** · **Discard** | "Not inserted. Window changed. Text kept. Press the last-outcome shortcut to choose." | Refusal cue | No timeout while hovered or while assistive technology is running; otherwise collapses after 8 s into the tray **Needs attention** item and the quick panel's Needs-attention section until handled |
| **Partial** | Amber; expanded layout; shows the inserted character count | "Partly inserted (42 of 120 characters)" + **Copy rest** · **Show where it went** | Announced with the counts | Refusal cue | Same persistence rules as Refused |
| **Cancelled** | Neutral; brief | "Cancelled" (or "Already inserted — cancel had no effect" when delivery had committed) | Announced | Cancel cue | Fade |
| **Error** | Red `state.danger` | Specific reason + one action ("Microphone disconnected — Choose microphone") | Announced | — | Action |
| **Mic blocked by Windows privacy** | Red; mic-off glyph | "Windows is blocking the microphone" + **Open privacy settings** | Announced | — | Unpackaged desktop apps may get no per-app prompt; the capsule deep-links to "Let desktop apps access your microphone" |
| **No microphone** | Red; mic-off glyph | "No microphone found" + **Choose microphone** | Announced | — | Device list refreshes on plug-in |
| **Paused** | Tray glyph paused; pressing the shortcut shows a brief neutral capsule | "WisprSide is paused" + **Resume** | Announced | — | Nothing is captured while paused |
| **Target not allowed** | Amber; shield glyph; expanded layout | "This window is protected (administrator or password field) — text kept" + **Copy** | Announced | Refusal cue | Never attempts insertion |
| **Model missing** | Amber | "No speech model installed" + **Choose model** | Announced | — | Opens the model card list |

Rules:

- Coral appears **only** while the microphone is actually capturing. When capture stops, coral disappears in the same frame.
- The receipt always names the destination. This is the primary defense users can *see* against wrong-target insertion (SD-04).
- No modal dialogs during dictation. Everything happens in the capsule.
- Mirrored in Arabic UI: icon order and text alignment flip; the level meter grows from the **centre outward** so it reads the same in both directions; window titles are direction-isolated **before** truncation so the ellipsis lands correctly.

### 2.1 Expanded capsule and keyboard recovery

- **Expanded layout:** 360 × 88 px at 100% scale with up to three buttons, each at least 24 × 24 px (WCAG 2.2 SC 2.5.8), placed above the collapsed position.
- **The capsule still never takes focus.** Keyboard and screen-reader users act through a global **last-outcome shortcut** (configurable; validated by SD-UX-01) that opens the quick panel focused on the pending item, where Enter, Esc and Tab behave normally. Enter and Esc are never intercepted from the target application.
- Every pending outcome also appears in the tray menu under **Needs attention** and in the quick panel's Needs-attention section until the user handles or dismisses it. This is the recovery buffer; it survives an app restart and respects history-retention settings.

## 3. Interaction model

| Action | Default (Windows) | Notes |
| --- | --- | --- |
| Push-to-talk | Keep the donor's `HoldOrToggle` activation model and its default chord unless SD-UX-01 finds a conflict | Never default to a `Win`-key chord (`Win`+`H` is Windows voice typing). Toggle via `RegisterHotKey` is the robust baseline; hold-to-talk needs a low-level hook, scoped narrowly. Onboarding detects conflicts |
| Toggle | Double-tap the PTT chord, or a separate shortcut | — |
| Cancel | `Esc` while capsule is active | Never sends text |
| Re-insert last | Shortcut (configurable) | Re-binds to the *current* target only after showing which app will receive it |
| Open quick panel | Shortcut (configurable) | — |
| Edit selection by voice (SD-14, S tier) | Separate shortcut while text is selected | The preview opens in the quick panel, which takes focus explicitly; Enter applies there and Esc discards, so no key reaches the target app |

Spoken commands inside dictation (S tier): "new line", "new paragraph", "scratch that", "no, I mean…" — applied as visible, reversible edits on top of the immutable raw transcript.

## 4. Onboarding (target: first successful delivery in under 2 minutes, to be measured)

1. **Welcome** — one sentence: "Speak anywhere you can type. Nothing leaves this computer unless you choose." Language choice (English / العربية) sets UI language and the default dictation languages. Every step has **Skip** and onboarding can be resumed from the tray.
2. **Microphone** — explanation, then the OS permission request; live level meter test ("Say something — the line should move").
3. **Shortcut** — choose push-to-talk or toggle; press it to test; conflict detection message if another app owns it.
4. **Model** — recommended model card for this machine (size, languages, offline ✓, license, download size). The download starts in the background **as soon as the user consents** (it runs while steps 2–3 continue); a tiny starter model is bundled instead only if its license permits redistribution. A "fully offline" badge explains there is no network after download.
5. **Privacy first, then practice** — history on/off and retention (off / 24 h / 7 days / 30 days) are chosen **before** any practice dictation is recorded. Then a built-in sandbox field: the user dictates and sees the capsule, the receipt and the raw/formatted toggle. Refusal is demonstrated with a **"Simulate a window switch"** button, so no simultaneous key-hold and window switch is required.
6. **Try it for real** — "Now try it in Notepad" (or any app the user picks), confirming the first real delivery receipt.
7. **Done** — tray location shown; a cheat sheet of shortcuts.

## 5. Quick panel

- Opens centered, 640 px wide, list-first. Each entry: time, target app icon, first line, language badge (AR / EN / Mixed), delivery outcome icon.
- Enter = copy; `Ctrl+Enter` = insert into the current target (after a confirmation line naming it); `Ctrl+R` toggles raw/formatted (Tab keeps normal focus movement); `Delete` removes an entry only when the list has focus and shows an **Undo** toast; shortcuts bind by physical key code so they work on Arabic keyboard layouts.
- Header: current model and language with a one-key switcher; offline/online badge.
- Mixed Arabic/English entries render each entry in its own isolated direction (`dir="auto"`).

## 6. Settings information architecture

- **Capture:** microphone, input level, noise suppression (if the selected route supports it), activation mode, shortcuts.
- **Language & models:** dictation languages, code-switching on/off, model list with capability cards (size, languages, offline, license, measured performance once available), download/remove.
- **Output & formatting:** punctuation style, numerals (Western / Arabic-Indic / keep as spoken), filler removal, self-correction handling, optional local LLM rewrite (shows "Not configured" until the user points it at a local endpoint; network badge if the endpoint is remote).
- **Per-app profiles (S tier):** app identity → language default, formatting, LLM on/off.
- **Privacy & data:** history retention, delete all, export, view data folder, network activity log (every outbound request with time, host and purpose).
- **Advanced:** delivery method preference (paste / typing simulation / UI Automation where qualified), clipboard restore, refusal behaviour, diagnostics export.

## 7. Core journeys and acceptance

| Journey | Steps | Acceptance (measured in G-E2E) |
| --- | --- | --- |
| J1 Dictate an email | Focus mail compose → hold PTT → speak 15 s → release | Receipt names the mail app; text correct within route WER; ≤ 2 s p95 key-up → text (*target*) |
| J2 Focus steal | Start dictation in Notepad → a notification window takes focus → release | Refused state; text kept; nothing inserted elsewhere |
| J3 Arabic/English mixed message | Dictate "ارسل لي الـ report قبل الساعة ٥" in a chat app | Correct logical order; digits per setting; receipt shown |
| J4 Cancel | Hold PTT → speak → Esc | Nothing inserted; "Cancelled" announced |
| J5 Recover after refusal | J2 → click "Insert into Notepad" | Inserted only after Notepad is confirmed as the target |
| J6 Change model offline | Disconnect network → switch to a downloaded model → dictate | Works; network log shows nothing |
| J7 Screen-reader user | Complete J1 with NVDA only | Every state announced; no mouse needed |
| J8 Mic unplugged mid-dictation | Pull USB mic | Error state with "Choose microphone"; captured audio so far is transcribed or explicitly discarded, never silently lost |
| J9 Recover from a refusal with NVDA only | J2 with a screen reader; use the last-outcome shortcut | Refusal announced with the shortcut name; quick panel opens focused on the item; "Insert into Notepad" succeeds after re-confirmation; no mouse used |
| J10 Microphone blocked by Windows privacy settings | Turn off desktop-app microphone access, then dictate | "Windows is blocking the microphone" with a working deep link; nothing silently fails |

## 8. Accessibility specifics

- All capsule states are exposed through UI Automation notifications (Windows) and `aria-live="polite"` equivalents in the webview, with assertive priority only for errors and refusals.
- Capsule text meets 4.5:1 on its background in every theme; the live state is distinguishable without color (level meter shape).
- Non-voice fallback for everything: every action available from the tray, quick panel and settings by keyboard (Constitution XIII, invariant A14).
- Users can lengthen receipt and refusal display time; earcons can be turned on independently of visual cues.
