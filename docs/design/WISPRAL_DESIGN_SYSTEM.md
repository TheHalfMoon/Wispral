# Wispral design system — "Quiet Signal"

**Status:** CANDIDATE DESIGN DIRECTION. No interface has been built, rendered or reviewed; every quality statement here is a requirement, not an observation. Part of the [World-Class Master Plan](../strategy/WISPRAL_WORLD_CLASS_MASTER_PLAN.md). Machine-readable tokens: [tokens/wispral.tokens.json](tokens/wispral.tokens.json). Product specs: [WisprSide](WISPRSIDE_UX_SPEC.md) · [WisprStudio](WISPRSTUDIO_UX_SPEC.md) · [Klaint](KLAINT_UX_SPEC.md).

Design is a first-class requirement. The donors' interfaces are a starting point to *re-skin and re-structure*, not a ceiling. The design system is delivered as tokens and components applied to the retained donor UIs (Handy's React/Tauri frontend, VoiceStudio's Electron renderer, Klaint's web console), not as a new UI framework.

---

## 1. Identity

### 1.1 Concept

**Quiet Signal.** Voice is invisible until it matters. Wispral interfaces stay calm and nearly silent, then become unmistakably clear at the moments that carry risk or meaning: recording is live, text was delivered *here*, a voice needs consent, an agent is about to act.

Three rules follow from the concept:

1. **Calm by default, loud when it matters.** Most surfaces are neutral and low-contrast in chrome, high-contrast in content. Saturated color is reserved for state: live capture, a pending decision, a failure.
2. **State is never ambiguous.** Every consequential state is shown three ways — shape or icon, text label, and color — and announced to assistive technology. Color alone never carries meaning.
3. **Show the evidence.** Where a decision was made (what was heard, where text went, which policy allowed an action, which consent covers a voice), the interface offers a one-step path to the evidence.

### 1.2 What we take from design leaders (principles, not visuals)

| Source | Principle Wispral adopts | Where it applies |
| --- | --- | --- |
| Linear | Speed as a feature; keyboard-first; a command menu for everything; opinionated defaults; restrained motion | All products; Klaint console; Studio |
| Raycast | Instant, summonable surface that disappears; results before chrome | WisprSide quick panel |
| Obsidian | Local files you own; transparent storage; extensibility without lock-in | Studio projects; Side history export |
| Arc | Calm chrome that recedes behind content | Studio editor |
| Figma | Properties inspector bound to selection; direct manipulation | Studio inspector and timeline |
| Apple HIG / Windows Fluent 2 | Native conventions for menus, tray/menu-bar, notifications, focus, high contrast and accessibility; respect platform materials | Platform shells |
| ElevenLabs | Script-first production flow with voice selection close to the text | Studio |
| Wispr Flow | A small, persistent, low-distraction capture indicator | WisprSide capsule |

Wispral does **not** copy any of these products' logos, color palettes, illustrations, icons, or proprietary visual assets.

### 1.3 Umbrella and product personalities

| Product | Personality | Default theme | Signature accent (token) | Density |
| --- | --- | --- | --- | --- |
| **Wispral** (umbrella, docs, installer) | Precise, warm, trustworthy | Light | `wisp` — orchid | Comfortable |
| **WisprSide** | Invisible until summoned; calm, immediate | Follows OS | `side` — ink indigo; `live` coral for capture | Compact |
| **WisprStudio** | Creative, focused, tactile | Dark (studio) | `studio` — plum violet | Comfortable, canvas-first |
| **Klaint** | Operational, legible, accountable | Light | `klaint` — ledger blue | Dense, data-first |

All four share neutrals, typography, spacing, radius, motion and state colors. Product accent tokens are the only color that differs. The family resemblance comes from the shared "signal line" motif (§8) and type.

---

## 2. Token architecture

Three layers, exported from one JSON source in the W3C Design Tokens Community Group format ([tokens/wispral.tokens.json](tokens/wispral.tokens.json)) to CSS custom properties (Tauri and Electron renderers, Klaint web), with Tailwind theme mappings where a donor already uses Tailwind.

1. **Primitive** — raw values: `color.graphite.900`, `space.4`, `radius.2`, `duration.200`.
2. **Semantic** — intent: `color.bg.canvas`, `color.text.primary`, `color.state.live`, `color.border.focus`, `motion.enter`.
3. **Component** — scoped: `capsule.bg.live`, `timeline.clip.selected.border`, `verdict.deny.fg`.

Rules: components may reference only semantic tokens. Semantic tokens have light, dark and high-contrast values. Windows high-contrast mode maps semantic tokens to system colors (`Canvas`, `CanvasText`, `Highlight`, `HighlightText`, `ButtonFace`, `ButtonText`) via `forced-colors` media queries.

## 3. Color

### 3.1 Neutrals ("graphite" and "paper")

Slightly warm grays avoid the clinical blue-gray dashboard look. Thirteen steps from `paper.0` (#FBFAF8) to `graphite.950` (#131312). Text on canvas meets WCAG 2.2 AA (4.5:1 body, 3:1 large text and UI components) in every theme. The token file lists exact values; contrast is verified by a script in the token build (packet DS-02).

### 3.2 State colors (shared, never product-tinted)

| Semantic token | Meaning | Light solid / text-safe | Dark | Always paired with |
| --- | --- | --- | --- | --- |
| `state.live` | Microphone capturing | coral #E5484D / #B3262C | #FF7A7F | Live level meter shape + "Listening" label |
| `state.working` | Transcribing / rendering / thinking | lagoon #0E9384 / #0B6E64 | #3FD0BA | Progress shape + label |
| `state.success` | Delivered / rendered / allowed | green #2B9A66 / #1B6E48 | #4ADE9B | Check icon + destination label |
| `state.attention` | Needs a decision / consent / ASK | amber #C46A05 / #8F4C00 | #FFC14D | Question/shield icon + action label |
| `state.danger` | Refused / failed / DENY | red #CE2C31 / #A61E24 | #FF8589 | Cross/stop icon + reason |
| `state.neutral` | Idle / disabled | graphite #6F6B65 | #A19D96 | Label |

"Solid" values are for icons, fills and borders (WCAG 2.2 SC 1.4.11, 3:1); "text-safe" values are for state-colored text (SC 1.4.3, 4.5:1). `node docs/design/tokens/check_contrast.mjs` checks 76 light/dark pairs across canvas, surface and sunken backgrounds: `PASS 76/76` on 2026-11-08 (`REPRODUCED`). Two earlier runs failed and were fixed forward: three primitives failed the first run, and the design-platform research pass found three more failures against `bg.sunken` that the original pair list did not cover (graphite.500, wisp.500 and the dark `border.strong` mapping were adjusted). Coral `live` and red `danger` solids differ from each other by only about 1.1–1.3:1, so shape and text, not color, must distinguish them. Whether "listening" should use coral or the product accent is an open A/B question for packet DS-04 (the research report recommends testing a non-red variant).

Coral (`live`) and red (`danger`) are close in hue on purpose (both mean "pay attention"), but they are never shown without their distinct shape: a live level meter versus a stop/cross glyph.

### 3.3 Product accents

`wisp` orchid #A3317B (dark #F07CC0), `side` ink indigo #3E4BC9, `studio` plum #6340D0 as text on light (#A98BFF on dark), `klaint` ledger blue #1A64D6. Accents mark primary actions and brand moments, never status. A hue-separation lint in `check_contrast.mjs` requires every accent to sit at least 30° of hue away from every state colour in both themes (the earlier amber Studio accent was 1.46:1 from the attention amber and read as a warning).

### 3.4 Focus, selection, disabled and input

- **Focus indicator:** every focusable control gets a 2 px `focus.ring` outline with a 2 px `bg.canvas` gap (`outline-offset: 2px`). The ring is graphite.900 in light and paper.0 in dark, reaches at least 3:1 against canvas, surface and sunken (checked), and never reuses an accent, so focus is never confused with selection.
- **Selection:** `bg.selected` (indigo tint) with text contrast checked; selection is also shown by a check or bar, not colour alone.
- **Disabled:** `text.disabled`; disabled controls explain why (§10).
- **Inputs:** `border.input` (≥ 3:1); `border.default` is for dividers only and is never used as an input boundary.
- **High contrast:** every semantic token maps to a CSS system colour, and live and focus never share a mapping (tokens file `highContrast`).

`check_contrast.mjs` result on 2026-11-08: `PASS` — 94 contrast pairs and 40 hue-separation checks (`REPRODUCED`).

## 4. Typography

Bilingual typography is a core requirement: Arabic and Latin must feel like one family, at UI sizes, on Windows ClearType rendering.

| Role | Family (license) | Rationale |
| --- | --- | --- |
| UI sans (Latin + Arabic) | **IBM Plex Sans** + **IBM Plex Sans Arabic** (SIL OFL 1.1) | Both belong to the IBM Plex project, which makes a consistent bilingual pairing plausible; strong Latin legibility at 12–14 px. Arabic diacritic (tashkeel) and Arabic-Indic digit coverage are `NOT_VERIFIED` and are checked in DS-01 before adoption |
| Monospace (transcripts, logs, ids) | **IBM Plex Mono** (SIL OFL 1.1) | Clear 0/O and 1/l/I. Plex Mono's Arabic coverage is `NOT_VERIFIED`, so the mono stack falls back to Plex Sans Arabic and Segoe UI for Arabic runs |
| Fallback Arabic (long-form reading, script editor option) | **Noto Naskh Arabic** (SIL OFL 1.1) | Traditional Naskh for long Arabic scripts in Studio |
| Platform fallback | Segoe UI Variable, then **Segoe UI** (Windows; named explicitly because Segoe UI Variable lacks Arabic) / SF Pro (macOS) / system-ui | When the bundled fonts fail to load |

**Font licensing note:** every IBM Plex OFL file declares the Reserved Font Name "Plex". Subsetting or re-encoding the fonts creates a Modified Version that must be renamed under the OFL, so Wispral ships the upstream font files unmodified (or renames any subset build). Lucide is ISC-licensed (Feather-derived icons MIT).

Final selection is confirmed in packet DS-01 by rendering test strings (Arabic with diacritics, mixed Arabic/English with code tokens, Arabic-Indic and Western digits) at 12, 13, 14 and 16 px on Windows at 100% and 150% scaling, and reviewing them with native Arabic readers. If Plex Sans Arabic fails that review, the documented alternatives are Readex Pro and Noto Sans Arabic UI (both OFL), compared in the same harness.

**Type scale (px / line-height):** 11/16 caption · 12/18 small · 13/20 body-compact (Klaint, Side) · 14/22 body · 16/24 body-large · 20/28 title-3 · 24/32 title-2 · 32/40 title-1. Arabic text gets +2 px line-height at body sizes so ascenders, descenders and diacritics do not collide, and **Arabic is never set below 13 px** (dense Klaint and WisprSide surfaces use 13/22 for Arabic, with a font `size-adjust` so Arabic and Latin read at the same visual size). Arabic is never letter-spaced and never set in faux italics.

## 5. Space, layout, radius, elevation

- **Spacing:** 4 px base; tokens `space.1`–`space.12` = 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96.
- **Radius:** 4 (inputs), 6 (buttons), 10 (cards, panels), 999 (capsule, pills).
- **Elevation:** three levels via borders and a subtle shadow in light theme; in dark theme elevation uses surface lightness, not shadows.
- **Layout logical properties only:** `margin-inline-start`, `padding-inline-end`, `inset-inline-*`, so RTL mirroring is automatic (§9).
- **Windows materials:** WisprSide settings and quick panel may use Mica/acrylic backgrounds where the Tauri window API supports them, with a solid fallback and a reduced-transparency setting.

## 6. Iconography

- **Base set:** Lucide (ISC license) for product UI, extended with a small Wispral set for domain glyphs (capsule states, consent shield, verdict marks, waveform, target-window) drawn on the same 24 px grid with 1.5 px strokes.
- **Directional icons mirror in RTL** (back/forward, undo/redo arrows, list indentation, send). **Non-directional icons do not mirror** (media play, clocks, checkmarks, microphone, brand marks). Lucide ships no official RTL mirror metadata, so Wispral maintains its own mirror list as part of the icon set (DS-03).
- **Logo system (direction):** a single continuous "signal line" — a breath-like stroke that rises into a gentle spiral — as the Wispral mark. Product marks reuse the line with one distinct terminal: WisprSide (a caret), WisprStudio (a tape reel loop), Klaint (a speech-bubble tail). The logo is designed and trademark-searched in packet DS-06; nothing here is a final mark.

## 7. Motion and feedback budgets

| Token | Duration | Easing | Use |
| --- | --- | --- | --- |
| `motion.instant` | 0–80 ms | none | Press feedback, toggles |
| `motion.quick` | 120 ms | `cubic-bezier(0.2, 0, 0, 1)` | Capsule appear, hover, menus |
| `motion.standard` | 200 ms | `cubic-bezier(0.2, 0, 0, 1)` | Panels, popovers |
| `motion.exit` | 150 ms | `cubic-bezier(0.4, 0, 1, 1)` | Dismissals (exit durations are shorter than entry durations) |
| `motion.emphasis` | 320 ms | `cubic-bezier(0.3, 0, 0, 1.2)` | Rare success moments (first delivery in onboarding) |

- **Meaningful motion only:** the live level meter moves with the actual input level; there is no decorative pulsing. Under `prefers-reduced-motion`, the meter becomes discrete static bars updated at a lower rate, and transitions become instant crossfades.
- **Feedback latency budgets (targets for measurement):** visible response to a key or click ≤ 100 ms; capsule visible ≤ 100 ms after activation key-down; delivery receipt shown within one frame of the delivery outcome.
- **Earcons (WisprSide, optional, on by default during onboarding):** start = short rising two-note cue; stop = falling cue; cancel = low double tick; refusal = soft distinct triad. Each ≤ 150 ms, mastered quietly, never played into the microphone path, with independent volume and a mute.

## 8. The signal line motif

**Component tokens:** stroke 1.5 px; amplitude mapped from the measured input level (0–100%) to 0–8 px; colour per state (`state.live` when capturing, `text.tertiary` idle, `state.attention` on refusal); under reduced motion it becomes discrete bars updated at 4 Hz. In WisprStudio it carries clip waveforms; in Klaint it shows conversation activity on the live list. Its shape is specified once and reused, so the products are recognisable without a logo.

**Banned patterns:** purple-to-blue "AI" gradients, sparkle or robot icons for AI features, glassmorphism cards, stock illustrations, confetti, vanity KPI tiles, decorative pulsing that is not driven by real input, and dashboards whose first screen is a chart rather than the task.

One reusable visual element ties the products together: a thin horizontal line that is flat when idle, becomes a live waveform when capturing (WisprSide capsule), carries clip waveforms on the Studio timeline, and shows conversation activity in Klaint live sessions. It is the brand's main graphic device, which keeps marketing art, onboarding illustration and product UI consistent without stock "AI" imagery.

## 9. Arabic, RTL and localization

- **Full mirroring** of layout for Arabic UI: navigation, panels, progress direction, sliders, back/forward. The Studio **timeline does not mirror**: time flows left to right in audio and video tooling regardless of UI language, and the playhead convention stays universal. This exception is documented in the Studio spec.
- **Bidi isolation for user content:** every user-provided or transcribed string is rendered inside a direction-isolated element (`dir="auto"` / `<bdi>` / Unicode FSI…PDI), so a Latin token (URL, code, product name) inside Arabic text, or an Arabic name inside English text, never reorders surrounding UI.
- **Numerals:** a per-user setting (Western 0–9 or Arabic-Indic ٠–٩) with an "Auto" default keyed off the **full** locale (for example `ar-SA` versus `ar-EG`), not the bare `ar` tag, which resolves to Latin digits under current CLDR data. Wispral never silently converts digits in *transcribed or inserted text*; that is a formatting rule the user controls.
- **Inserted text:** WisprSide inserts Unicode text in logical order and never adds directional control characters unless the user enables the option for the target app.
- **Copy:** Arabic UI copy is written by native speakers (Gulf-neutral MSA for UI), not machine-translated. String externalization via the donors' existing i18n frameworks; pseudo-localization and RTL screenshot tests in CI.
- **Locales at first stable release:** English and Arabic. More locales only with native review.

## 10. States, onboarding and permissions

| State | Pattern |
| --- | --- |
| Empty | A single sentence of purpose, one primary action, an optional sample ("Try a sample project"); no illustrations that imply features that do not exist |
| Loading | Skeletons for known layouts; a determinate progress bar with a reason ("Loading Whisper base · 142 MB") for anything over one second; a cancel button for anything that may exceed five seconds |
| Disabled | Explains why and how to enable ("Arabic voice requires a model that supports Arabic — Choose model") |
| Error | What happened, what was preserved, what to do next. Never a raw stack trace; a "Copy details" button for support |
| Refusal (Wispral-specific) | Treated as a *success of safety*, not an error: neutral-attention styling, the reason, and the recovery ("Window changed — text kept. Insert into Notepad again · Copy") |

**Permissions education.** Ask for a permission only at the moment it is needed, after showing what it enables. Each request screen states what is accessed, when, where data goes ("Nothing leaves this computer in offline mode"), and how to revoke it. A live test follows every grant (speak and see the level meter; press the hotkey and see the capsule).

**Settings.** Organized by intent (Capture, Language & models, Output & formatting, Privacy & data, Shortcuts, Advanced), searchable, with every setting reachable from the command menu. Network-using settings carry a visible network badge.

**Installer and update.** Signed installer; a one-screen install for per-user installs without administrator rights where the packaging allows; first launch goes straight into onboarding. Updates are announced in-app with release notes and a "Later" option; the previous version is retained for rollback.

## 11. Design review method

Interfaces are verified, not assumed excellent.

1. **Native screenshot and state-sequence capture:** each key screen × {light, dark, all four Windows contrast themes} × {English, Arabic} × {100%, 125%, 150%, 200% scale} × {text size 100% and 200%} × {reduced motion on/off}. A debug-only **state-freeze** hotkey holds each transient state (capsule states, refusals, takeover) for capture, and scripted state sequences are recorded as short videos so timeouts, focus order, announcements and motion are reviewable, not just still frames.
2. **Heuristic rubric** scored per screen with written anchors: 0 = missing or misleading; 1 = present but ambiguous or mouse-only; 2 = clear and keyboard-reachable; 3 = clear, keyboard-reachable, announced to screen readers and correct in RTL. Criteria: state clarity; evidence reachable; hierarchy (one primary action); keyboard path; RTL correctness; copy clarity; empty, loading and error states present; consistency with tokens; performance feel. Scored by someone **other than the builder**. Release gate: **3 on state clarity and keyboard path**, at least 2 on everything else.
3. **Accessibility audit:** Accessibility Insights for Windows (automated + assessment), axe-core for web surfaces, scripted NVDA and Narrator passes, keyboard-only completion of each core journey, contrast check from tokens.
4. **Interaction latency measurement:** instrumented timestamps for key-down → capsule visible and click → response, reported p50/p95 against the budgets in §7.
5. **Usability tests:** 5–8 consented participants per round, including bilingual Arabic/English users, at least one screen-reader user, one keyboard-only user and (for Klaint) operations staff without AI experience; tasks from each UX spec; success, time and errors recorded; an **unbranded screenshot recognition test** checks that each product is identifiable without its logo; findings classified BLOCKER / MUST FIX / SHOULD IMPROVE / OPTIONAL. Accessibility passes include an Arabic NVDA and Narrator pass.
6. **Design tooling:** design exploration may use available tools (for example Claude Design, Paper or Figma when accessible). Every design artifact is judged by the same rubric and by screenshots of the *running* product — a mockup is never accepted as evidence of the shipped interface.

## 12. Design-system work packets

| ID | Output | Acceptance |
| --- | --- | --- |
| DS-01 | Font harness and bilingual type selection | Rendered strings at four sizes and two scales reviewed by native Arabic readers; decision recorded |
| DS-02 | Token source + build to CSS variables, Tailwind map, and a contrast check script | All semantic pairs meet WCAG 2.2 AA in light/dark; high-contrast maps to system colors |
| DS-03 | Icon set (Lucide subset + Wispral glyphs) with mirror metadata | RTL screenshot test shows correct mirroring |
| DS-04 | Component kit for capsule, receipt, verdict chip, consent badge, model capability card, job row | Storybook-style or static HTML gallery with states; keyboard and screen-reader checks |
| DS-05 | Apply tokens to the Handy fork (WisprSide) and build the component kit there (capsule, receipt, refusal, quick panel, onboarding) | Screenshot and state-sequence matrix; rubric 3 on state clarity and keyboard path, ≥ 2 elsewhere, scored by a non-builder |
| DS-06 | Logo and product marks + trademark search | Marks delivered in SVG; search results recorded; founder approval |
| DS-07 | Apply tokens to the VoiceStudio fork (WisprStudio) | Screenshot matrix + rubric |
| DS-08 | Klaint console shell on tokens | Screenshot matrix + rubric |
