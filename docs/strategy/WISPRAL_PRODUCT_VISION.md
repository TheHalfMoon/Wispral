# Wispral product vision and capability specification

**Status:** CANDIDATE PLAN — not ratified governance, not implementation authority. Part of the [World-Class Master Plan](WISPRAL_WORLD_CLASS_MASTER_PLAN.md).
**Date:** 2026-11-08 · **Canonical base observed:** `main` = `edacdf7504302cc91ff7138bc6ac2d391e4df1f4`
**Names (founder-final, not trademark-cleared):** Wispral · WisprStudio · WisprSide · Klaint ([founder record](FOUNDER_SOURCE_REUSE_AND_PRODUCT_IDENTITY.md)).

Every capability below is **PLANNED**. Nothing in this document claims that a Wispral capability exists, works, or outperforms a competitor. Tier labels set build order only. Moving any row into execution requires the readiness authority described in [WISPRAL_GOVERNANCE_RECONCILIATION.md](WISPRAL_GOVERNANCE_RECONCILIATION.md).

---

## 1. Vision

> **Voice you can trust, in the languages you actually speak.**

Wispral turns speech into writing, audio and customer conversations. It treats three properties as product features rather than compliance work: knowing what the system heard, knowing where the output went, and knowing who authorized each action. It works usefully offline, treats Arabic and English as first-class languages including code-switching, and reuses proven open-source software instead of rebuilding it.

### 1.1 Strategic thesis

1. **Trust is the moat that open-source donors and closed competitors leave open.** Inspected donors already provide capture, transcription, generation and dialogue. None of them binds output to its intended target, its consent, or its tenant, and fails closed when that binding breaks (see the [build-new register](WISPRAL_COPY_FIRST_STRATEGY.md#4-build-new-register)). Closed competitors ask users to trust a cloud they cannot inspect. Wispral competes on verifiable behavior.
2. **Arabic is a quality requirement, not a checkbox.** Gulf and Saudi users code-switch constantly. A product measured on segmented, consented Arabic/English evidence is a defensible position — but only once that evidence exists ([benchmarks](../engineering/WISPRAL_BENCHMARKS.md)).
3. **Copy-first is how a small team ships world-class breadth.** Each product starts from a pinned donor application that already works (Handy, VoiceStudio, Parlant). Wispral spends its engineering on the narrow boundaries where donors are unsafe or incomplete ([copy-first strategy](WISPRAL_COPY_FIRST_STRATEGY.md)).
4. **Small, excellent, independent products beat a monolith.** Each product installs and ships alone. Wispral the platform is shared contracts, a small policy library, conformance fixtures and design tokens, not a daemon every product must run ([architecture](WISPRAL_PRODUCT_ARCHITECTURE.md)).

### 1.2 Product boundaries

| Product | Is | Is not |
| --- | --- | --- |
| **Wispral** (platform) | Versioned contracts (envelope, cancellation, inventory, consent, verdict, provenance, delivery outcome); a small Rust policy library with a Python binding or fixture-equivalent port; conformance fixtures; model capability manifests; design tokens; later SDKs | A mandatory background service, a cloud account, a hosted model, a monorepo that forces co-installation |
| **WisprSide** | A fast, calm, application-aware dictation and spoken-editing companion. Windows first. Optional developer-agent voice control as a later module | A meeting recorder, an always-listening assistant by default, a screen-capture tool, an IDE |
| **WisprStudio** | A desktop voice and audio production studio: scripts, generation, consented cloning, timeline, long-form, dubbing, export | A generic DAW replacement, a voice marketplace, a tool for cloning voices without consent |
| **Klaint** | A self-hostable platform to build, test, supervise and audit customer voice/chat agents with deterministic action authority | A generic chatbot builder without authority controls, a CRM, a replacement for a human support team's inbox |

### 1.3 Target users

| Product | Primary users (first release) | Secondary users (later) |
| --- | --- | --- |
| WisprSide | Bilingual Arabic/English knowledge workers and developers on Windows; users with RSI or motor constraints who need reliable dictation | macOS and Linux users; mobile; enterprise fleets |
| WisprStudio | Independent creators, educators and small localization teams producing Arabic/English narration and dubbing on their own hardware | Studios with GPU farms, audiobook publishers, broadcasters |
| Klaint | Support-operations leads at small and mid-size businesses, especially Gulf-region teams that serve Arabic and English customers and need self-hosting and audit | Regulated enterprises, BPOs, contact centers with telephony |

### 1.4 Positioning hypotheses (each needs a measurable test before any public claim)

| Hypothesis | Measurable test that would support it | Where specified |
| --- | --- | --- |
| WisprSide never inserts text into the wrong application | Zero wrong-target insertions across the preregistered focus-steal / window-close / PID-reuse / elevated-window fixture suite on the shipped binary | [Benchmarks §WB-DELIVERY](../engineering/WISPRAL_BENCHMARKS.md#wb-delivery--safe-text-insertion) |
| WisprSide in offline mode sends nothing over the network | OS firewall / packet capture during a full session shows zero outbound connections | [Benchmarks §WB-EGRESS](../engineering/WISPRAL_BENCHMARKS.md#wb-egress--observed-network-behavior) |
| Wispral's Gulf Arabic / code-switch dictation is competitive | Segmented WER/CER, meaning-distortion and negation-flip rates on a held-out consented set, reported with confidence intervals against named alternatives | [Benchmarks §WB-AR](../engineering/WISPRAL_BENCHMARKS.md#wb-ar--arabic-and-english-language-quality) |
| WisprStudio never renders with a revoked or unconsented voice | Revocation fixtures block queued, resumed and cached renders, with zero leaks | [Security §Studio](../engineering/WISPRAL_SECURITY_ARCHITECTURE.md#4-wisprstudio-threat-model) |
| Klaint never lets conversation text grant itself authority | Preregistered adversarial set: zero unauthorized tool commits and zero unapproved commitment phrases | [Benchmarks §WB-KLAINT](../engineering/WISPRAL_BENCHMARKS.md#wb-klaint--agent-safety-and-quality) |

---

## 2. Capability catalog

**Tier legend.** `M` = MVP (first internally usable build). `S` = first stable release candidate. `L` = later expansion. `R` = long-term research. **Class:** `P` = parity (needed to be credible), `X` = differentiator (where Wispral aims to lead, once measured). **Source:** the donor that already provides it (`HAS`), provides it partly (`PARTIAL`), or not at all (`NEW`, justified in the [build-new register](WISPRAL_COPY_FIRST_STRATEGY.md#4-build-new-register)). Exact paths and pins are in [SOURCE_DECISION_MATRIX.md](../../research/wispral-world-class/SOURCE_DECISION_MATRIX.md).

### 2.1 WisprSide — intelligent voice companion

| # | Capability | Tier | Class | Source | Acceptance anchor |
| --- | --- | --- | --- | --- | --- |
| SD-01 | Global push-to-talk and toggle activation with configurable shortcuts | M | P | Handy HAS | Hold / toggle / repeat / lock-screen fixtures |
| SD-02 | Visible, unambiguous microphone and recording state (capsule, tray, earcon, screen-reader announcement) | M | P | Handy PARTIAL (overlay) + design delta | Indicator within the latency budget in the [design system](../design/WISPRAL_DESIGN_SYSTEM.md#7-motion-and-feedback-budgets); never color-only |
| SD-03 | Local offline transcription with a transparent model picker (size, languages, offline, license) | M | P | Handy HAS (model manager) | Offline egress test; capability manifest shown |
| SD-04 | Target-bound, fail-closed text insertion with an explicit delivery outcome (delivered / refused / partial / unconfirmed) | M | X | Handy PARTIAL + NEW envelope | WB-DELIVERY suite: zero wrong-target |
| SD-05 | Clipboard preservation: restore only if the clipboard is unchanged since Wispral wrote it | M | P | Handy PARTIAL | Clipboard-interference fixtures |
| SD-06 | Refusal for password, secure-desktop and elevated windows, with a copy fallback | M | X | NEW (small) | UIPI/elevated and password-field fixtures |
| SD-07 | Reliable cancel (Esc / release-cancel) with truthful state; never "cancelled" when text was already delivered | M | P | Handy PARTIAL | Cancel-at-load / mid / after-delivery fixtures |
| SD-08 | History with privacy controls: retention chosen in onboarding including keeping no text (M); per-app exclusion and encrypted store (S) | M | P | Handy HAS (history) + retention delta | Retention and deletion tests |
| SD-09 | Raw transcript always preserved next to formatted text, viewable in one click | M | X | Handy PARTIAL | Provenance test: raw never overwritten |
| SD-10 | Natural punctuation and capitalization (model-native first) | M | P | Model-dependent | WB-AR / WB-EN punctuation metrics |
| SD-11 | Personal vocabulary (names, technical terms) applied as recognition bias or post-correction | S | P | Handy PARTIAL (custom words) | Entity accuracy uplift on held-out set |
| SD-12 | Self-correction / backtrack ("no, I mean…") and filler removal as a reversible edit layer | S | P | NEW rule layer or optional local LLM | Meaning-distortion and negation tests |
| SD-13 | Optional local LLM rewrite (tone, formatting, per-app style); visibly "unavailable" when not configured | S | P | Handy/OpenWhispr PARTIAL | Provider-unavailable test; no silent cloud |
| SD-14 | Voice editing commands on selected text ("make this shorter", "translate to Arabic") with preview and confirm | S | P | FreeFlow/OpenWhispr reference + NEW Windows selection adapter | Selection-identity + wrong-target fixtures |
| SD-15 | Snippets / reusable phrases triggered by voice | S | P | NEW (small) | Collision and undo tests |
| SD-16 | Arabic and English with automatic code-switch handling | S | X | Model-dependent | WB-AR code-switch false-switch rate |
| SD-17 | RTL-correct preview, history and insertion of mixed Arabic/English text (bidi isolation) | M | X | Design delta | RTL fixtures incl. numerals and Latin code tokens |
| SD-18 | Per-application profiles (formatting, language default, LLM on/off) using app identity only (no screenshots) | S | P | NEW (small) | Profile selection on app identity |
| SD-19 | Streaming preview while speaking (Handy already ships it; hardening only) | S | P | Handy HAS | Stale preview never committed |
| SD-20 | Opt-in app context (selected text, field metadata) with explicit consent | L | P | FreeFlow reference (screenshot path rejected) | Consent epoch and sensitive-app deny list |
| SD-21 | Developer-agent voice control (ACP) with risk-tiered approvals | L | X | ACP rust-sdk WRAP, Orcel reference | 000A/000C/000D-dependent fixtures |
| SD-22 | macOS release (accessibility + input monitoring + notarization) | L | P | Handy HAS (macOS paths) | Platform cell evidence |
| SD-23 | Linux release (X11 first; Wayland via portals) | L | P | Handy PARTIAL | Platform cell evidence |
| SD-24 | Hands-free / wake mode with explicit visible state | R | P | NEW | H9-style turn evidence |
| SD-25 | Mobile keyboard | R | P | — | Separate platform research |

### 2.2 WisprStudio — creative voice production

| # | Capability | Tier | Class | Source | Acceptance anchor |
| --- | --- | --- | --- | --- | --- |
| ST-01 | Projects with durable, versioned, migratable format; autosave; crash recovery | M | P | VoiceStudio HAS | Kill-during-render resume fixture |
| ST-02 | Script editor → multi-speaker TTS generation with explicit per-project engine and voice | M | P | VoiceStudio HAS | Engine never auto-switches on resume |
| ST-03 | Engine/model manager showing code license, **weight license**, languages, size, offline, consent need | M | X | VoiceStudio PARTIAL (model acceptance) + manifest delta | Non-commercial weights blocked in commercial builds |
| ST-04 | Consent ledger for cloned voices (subject, purpose, scope, expiry, revocation) enforced at enqueue, render, resume and cache | M | X | VoiceStudio PARTIAL (`record_consent`) + enforcement delta | Revocation blocks queued, resumed and cached work |
| ST-05 | Synthetic-audio watermark on exports where the engine supports it, stated honestly | M | P | VoiceStudio/Chatterbox HAS | Encode/decode fixture; no robustness claim |
| ST-06 | Segment timeline for long-form and dubbing (VoiceStudio's existing timeline); DAW-style multitrack later (tier L, Voicebox donor candidate) | M | P | VoiceStudio HAS (segment timeline) | Edit/undo/export parity |
| ST-07 | Long-form generation (chapters, audiobook) with segment-level resume after failure | M | P | VoiceStudio HAS (`longform_resume`) | Resume identity checks |
| ST-08 | Export / render (WAV, MP3, stems, subtitles) with provenance sidecar | M | P | VoiceStudio HAS | Zero-volume export regression fixture |
| ST-09 | Local-only operation: analytics off, URL media ingest off, no auto-download | M | X | VoiceStudio PARTIAL → delta | WB-EGRESS for Studio |
| ST-10 | Pronunciation control (lexicon, phoneme or respelling, numbers and names) | S | P | NEW cross-engine lexicon layer (engine-native where available) | Name/number panel |
| ST-11 | Dubbing: ASR → translate → align → duration fit → TTS → mix, with a review gate at each stage | S | P | VoiceStudio HAS (+ fit guard) | Fit-guard fixtures; stage provenance |
| ST-12 | Speaker diarization and voice mapping for dubbing | S | P | VoiceStudio PARTIAL | Speaker mapping review |
| ST-13 | Batch workflows (queue, priorities, cancel, retry with identity checks) | S | P | VoiceStudio HAS | Cancel truthfulness |
| ST-14 | Voice conversion (speech-to-speech) for consented voices | S | P | VoiceStudio/OpenVoice/Chatterbox VC | Consent enforcement |
| ST-15 | Voice design from a text description (model-qualified only) | L | P | Qwen3-TTS voice design | Model rights + quality trial |
| ST-16 | Voice isolation / denoise / stems | L | P | Demucs (archived) or successor | Maintenance risk accepted explicitly |
| ST-17 | Local authenticated API and MCP for automation | L | P | VoiceStudio PARTIAL | Auth, origin and rate limits |
| ST-18 | Arabic dubbing quality with dialect-appropriate voices | L | X | Model-dependent | WB-AR TTS panel |
| ST-19 | Cross-engine A/B listening with blinded comparison | L | X | NEW (small, evaluation tool) | Blinded MOS protocol |
| ST-20 | Collaborative review / comments | R | P | — | — |

### 2.3 Klaint — conversational AI agents

| # | Capability | Tier | Class | Source | Acceptance anchor |
| --- | --- | --- | --- | --- | --- |
| KL-01 | Agent definition: rules and step-by-step policies (Parlant v4; guidelines and journeys on the v3.3.2 fallback), glossary, tone; versioned and diffable | M | P | Parlant HAS (code-first SDK in v4) | Version diff + rollback |
| KL-02 | Approved responses required for any action, price or policy commitment: a commitment guard suppresses unbacked commitments and substitutes an approved template or handoff | M | X | Parlant PARTIAL (v4 `on_message_generated` BAIL hook in BLOCK mode; v3.3.2 `CANNED_STRICT`) + NEW guard | 100 adversarial prompts x 3 seeds x EN/AR: zero unbacked commitments |
| KL-03 | Tenant-scoped knowledge retrieval with citations and source versions | M | P | Parlant HAS (retrievers) + tenant binding delta | Cross-tenant retrieval denial |
| KL-04 | Deterministic tool broker: tenant/credential resolved server-side, policy verdict, idempotency key, outcome ledger, unknown-outcome reconciliation | M | X | NEW (justified) around Parlant ToolService | Zero duplicate commits after uncertain outcome |
| KL-05 | Tool review gate plus closure of every bypass path (context-variable refresh, unauthenticated local tool server, lowest effort level) so the broker is the sole executor | M | X | Parlant PARTIAL (`on_reviewing_tool_calls`) + delta | One fixture per bypass path |
| KL-06 | Human handoff and takeover with an ownership epoch (no AI sends after takeover) | M | P | Chatwoot via API + NEW epoch | Takeover race fixtures |
| KL-07 | Session history and an append-only audit trail of guideline matches, tool proposals, verdicts and outcomes | M | X | Parlant PARTIAL + Core audit contract | Audit completeness check |
| KL-08 | Test Lab: scripted and simulated conversations, regression suites, deterministic outcome scoring | M | P | tau2-bench (MIT) harness; Parlant v4 removed its evaluations API | Suite runs in CI with identical verdicts on recorded replays |
| KL-09 | Text channels: web chat widget and Chatwoot inbox | M | P | Chatwoot API | Channel fixtures |
| KL-10 | Authentication, roles and permissions for operators | S | P | Parlant/host PARTIAL | RBAC tests |
| KL-11 | Multi-tenant isolation (one service instance per tenant first; shared later only with proof) | S | P | NEW deployment rule | Isolation fixtures |
| KL-12 | CRM / helpdesk connectors (HubSpot, Zendesk, Shopify-class) via thin Python adapters | S | P | Botpress schemas reference | Webhook signature/replay fixtures |
| KL-13 | Analytics: containment, handoff rate, resolution, policy-block rate, cost per conversation | S | P | NEW (small) on audit data | Metric definitions frozen |
| KL-14 | Multilingual conversations incl. Arabic dialects and code-switching | S | X | LLM-dependent | WB-AR dialogue panel |
| KL-15 | Real-time voice (WebRTC) with barge-in, using Pipecat inside the same service | L | P | Pipecat HAS | Barge-in and stale-frame fixtures |
| KL-16 | Telephony (SIP/Twilio-class) with recording disclosure and transfer recovery | L | P | Pipecat serializers | Authorized test number trials |
| KL-17 | Conversation QA: sampled review, rubric scoring, disagreement tracking | L | P | NEW (small) | Inter-rater agreement |
| KL-18 | Outbound contact with consent and rate controls | R | P | — | Legal review |
| KL-19 | On-prem / air-gapped enterprise deployment | L | X | Host packaging | Clean-install evidence |

### 2.4 Wispral platform

| # | Capability | Tier | Source | Acceptance anchor |
| --- | --- | --- | --- | --- |
| PL-01 | Versioned JSON Schemas for the eight core contracts, with fixtures | M | NEW (thin) informed by Sentrdel/Orcel/Ascout | Schema + fixture CI |
| PL-02 | Policy narrowing in Klaint's Python broker now; Rust `wispral-policy` crate once a second Rust consumer exists | M / L | Sentrdel ADAPT | Policy fixtures |
| PL-03 | Model capability manifest and rights record | M | NEW (thin) | Manifest validation |
| PL-04 | Shared design tokens and icon set | M | NEW | Token build to Tauri, Electron and web |
| PL-05 | Conformance fixture corpus runnable from Rust, Python and TypeScript | M | NEW | CI matrix |
| PL-06 | Developer SDKs (TypeScript, Python) over each product's local authenticated API | L | NEW | Semver policy |
| PL-07 | Public WispralBench extended to Arabic/English dictation, TTS and agent safety | L | Existing WispralBench + NEW families | Reproducible public artifacts |

---

## 3. What Wispral deliberately will not build first

- A Wispral foundation model or fine-tuned model (only after the measurable triggers in the [model strategy](../engineering/WISPRAL_MODEL_STRATEGY.md#7-when-a-wispral-owned-model-becomes-justified) fire).
- A new timeline editor, model hub, dialogue engine, inbox, workflow engine, or coding agent while a donor boundary exists.
- Always-listening capture, screen capture, telephony, outbound calling, or mobile before their dedicated research cells.
- Any cloud dependency for a capability that runs acceptably on the user's machine.
